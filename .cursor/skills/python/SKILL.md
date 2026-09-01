---

name: python
description: >-
Write and change Python in Stabsspel (Flask 3, Python 3.12, JSON game state,
live domain in gm_console.py, unittest). Use when editing .py files, adding
routes, HP/phase/order/backlog rules, persistence, authentication, or tests.
----------------------------------------------------------------------------

# Stabsspel Python

Single Flask process. No database, no `templates/` tree, no ORM. Each game is one JSON dict on disk.

Map of the repo: [Docs/architecture.md](../../../Docs/architecture.md).
Game rules: [Docs/Stabsspel Traineeprogrammet.md](../../../Docs/Stabsspel%20Traineeprogrammet.md).
LLM copy/import, HP queue, projector secrecy: [Docs/LLM_WORKFLOW.md](../../../Docs/LLM_WORKFLOW.md).
Agent doc hierarchy and conflict handling: `Docs/architecture.md` § For coding agents.

## Before changing code

Before implementing a change:

1. Read the relevant existing functions, routes, rendering code, JavaScript and tests.
2. Trace the full flow where relevant: HTTP → domain → persistence → UI.
3. Reuse existing helpers and conventions before creating new ones.
4. Do not introduce a second implementation of an existing rule.
5. Prefer the smallest coherent change that solves the requested problem.
6. Do not refactor unrelated code while implementing a feature or fix.
7. If you notice adjacent technical debt, report it separately instead of silently fixing it.
8. Active domain code (`gm_console.py`) shows runtime behaviour. The docs describe intended mechanics. If they disagree, do not silently pick one and do not follow leftover or unused code. Decide whether the difference is stale documentation or a code defect, then report it before changing game mechanics. Leftover routes, unused HTML builders and root-level `test_*.py` are never the game spec. The standard test suite is `tests/`.

## Where code goes

| Change                                                            | Put it in                                        | Test in                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| Live rules: phase, HP, orders, backlog, undo, LLM rolls/`utfall`, public/live payload | `gm_console.py`                                  | `tests/test_domain.py`                                         |
| GM / projector HTML                                               | `gm_console_ui.py`                               | `tests/test_gm_console.py`                                     |
| GM HTTP: auth, mutations, print/export                            | `admin_routes.py`, helpers in `admin_helpers.py` | `tests/test_admin_helpers.py`, `test_admin_routes.py` for HTTP |
| LLM prompt text (export instructions)                             | `Docs/prompt.md`                                 | domain tests that the filled export contains expected placeholders |
| Team briefs / QR                                                  | `team_routes.py`                                 | existing relevant tests                                        |
| Order save / submit / withdraw                                    | `team_order_routes.py`                           | domain tests for rules, route tests where needed               |
| JSON load/save, teams, passwords, backlog templates               | `models.py`                                      | `tests/test_domain.py`                                         |
| Delete game, stöd reset                                           | `game_management.py`                             | existing relevant tests                                        |
| App entry, home, health, projector routes                         | `app.py`                                         | existing relevant tests                                        |

Do not implement new live-event rules inside route handlers. Routes should load state, validate request-level input, call domain logic, persist, and return.

Do not grow leftover admin chrome (old quarter bar, checklists, extra timer widgets in `admin_routes.py`). Those builders are unused; they are not injected under the live console. Put new live GM work on the console.

## Domain model

The game dict **is** the model.

Important keys include:

* `runda` — 1–4
* `fas` — `Orderfas` / `Diplomatifas` / `Resultatfas`
* `poang.<lag>.aktuell`
* `regeringsstod`
* `team_orders`
* `backlog`
* `hp_pending` — queued wallet deltas applied when a new round starts
* `gm_log`
* `gm_undo`
* `test_mode`
* `llm_forslag` — per-round LLM suggestions; optional on older saves
* `llm_resolution` — per-round frozen rolls and imported `utfall`; optional on older saves

Important rules:

* Spendable HP is `aktuell`, plus +10 when `regeringsstod` applies.
* **Transfers use stored `aktuell` only. Government support is not transferable.**
* LLM **Tillämpa HP** and GM ± after Orderfas queue into `hp_pending` (next round's wallet). GM ± in Orderfas changes this round immediately.
* `build_live_state` is the GM payload.
* `build_public_state` is the projector payload. Never send inbox, `gm_log`, test mode, secret orders, `llm_forslag`, `llm_resolution`, rolls or `utfall` to the projector.
* News headlines stay on paper for the studio. LLM export fills `Docs/prompt.md` and freezes 1–100 rolls in `llm_resolution`. Paste/upload stores suggestions (`llm_forslag`) and GM-only `utfall`. HP and milestones apply only after GM confirm. A successful `utfall` does not create wallet HP by itself. Ordinary undo must not reroll frozen dice. Details: [Docs/LLM_WORKFLOW.md](../../../Docs/LLM_WORKFLOW.md).
* Code identifiers keep the existing mix such as `fas`, `runda`, `poang`, `regeringsstod`.
* UI strings are Swedish. See the [ux-gui](../ux-gui/SKILL.md) skill.

## State mutation discipline

For every state mutation, verify that:

1. validation happens before mutation,
2. an undo snapshot is created when the action is meant to be undoable,
3. the domain layer performs the rule-changing mutation,
4. the state is persisted exactly once,
5. returned live/public state reflects the persisted result.

Use the existing undo path (`push_undo` / `apply_undo`) rather than creating separate undo mechanisms.

Do not partially mutate game state and then fail validation.

Raise `ValueError` for illegal live actions where that is the existing domain convention. Routes should convert domain errors into appropriate user-visible or JSON responses.

## Persistence and saved-game compatibility

Persist game state through the existing `save_game_data` path.

Persistence uses atomic temp-file replacement and per-game locking. Do not write files under `speldata/` directly.

Existing JSON files may have been created by older versions.

Therefore:

* prefer additive changes to the game-state schema,
* use safe defaults when newly introduced keys are absent,
* do not assume old saved games contain new fields,
* do not rename or remove persisted keys without an explicit migration plan,
* loading an older valid game must not fail merely because a newer feature introduced additional state.

Do not use real files from `speldata/` in automated tests.

## HTTP and HTML-in-Python

Blueprints already exist:

* `admin`
* `team`
* `team_order`

Register routes in the appropriate existing blueprint.

Only put process-level routes directly in `app.py`, such as:

* home
* health
* projector

Pages are mostly f-strings or `render_template_string`.

Escape untrusted values with `markupsafe.escape`.

JSON mutations requiring a GM session must remain protected and return **401** when unauthenticated where that is the current API behaviour.

The projector endpoint remains public and deliberately small.

Team order URLs use `team_tokens`, not team names.

Do not weaken authentication, session validation or team-token checks to make implementation easier.

## Trust boundaries

Treat route input and persisted JSON as untrusted input.

Validate where relevant:

* game IDs
* team names
* numeric values
* HP adjustments
* requested actions
* phase transitions
* order data

Never expose GM-only information through projector or team-facing payloads.

Never move secret game information into a public endpoint for convenience.

Escape user-controlled values before rendering them into HTML.

## Tests

The authoritative suite is `tests/` (`test_domain.py`, `test_gm_console.py`, `test_admin_helpers.py`). Prefer those.

Root-level `test_*.py` and `debug_*.py` are legacy. Do not treat them as the game specification. `test_admin_routes.py` still covers delete-game HTTP; other root tests are archaeology.

Typical fast test run:

```bash
python -m unittest tests.test_domain tests.test_gm_console tests.test_admin_helpers
```

Use `tests/game_fixtures.py` for state builders such as:

* `create_game_state`
* `order_record`
* `activity`

Do not create automated tests that depend on live files in `speldata/`.

### Test placement

* Domain behaviour → `tests/test_domain.py`
* GM/projector HTML hooks → `tests/test_gm_console.py`
* Admin helpers → `tests/test_admin_helpers.py`
* Route/auth behaviour → relevant HTTP tests

Domain tests should assert on state and behaviour, not rendered HTML.

Visual-only CSS changes normally do not require new domain tests unless behaviour changes.

### Regression-test rule

Any behavioural change to:

* phases
* HP
* transfers
* government support
* orders
* backlog
* undo
* timers
* authentication
* visibility/public payloads
* persisted game state

should have a regression test.

Bug fixes should normally include a test that fails before the fix and passes after it.

Do not add new tests to root-level legacy `test_*.py` or `debug_*.py` unless maintaining an existing test there is specifically required.

## Local and production execution

Local development entry point:

```bash
python app.py
```

Production entry point:

```bash
gunicorn wsgi:app
```

Do not invent alternative startup or deployment entry points unless the user explicitly asks for an architectural change.

## Style

* Python 3.12.
* Match the style of the file being edited.
* Some modules use `from __future__ import annotations`; many do not. Do not introduce it broadly without reason.
* Keep functions small and named after the live action, for example:

  * `apply_next_phase`
  * `transfer_hp`
  * `withdraw_order`
* Prefer existing helpers and data structures over new abstractions.
* Avoid speculative frameworks, repositories, service layers or ORM-style abstractions that do not fit this codebase.
* No new dependencies unless explicitly justified or requested.
* Current stack includes Flask 3, Gunicorn, qrcode and Pillow.

## Documentation

Update the relevant docs in the **same change** as the code. Do not leave documentation stale for a later cleanup.

| Change | Also update |
|--------|-------------|
| Live rules, routes, tests, console structure | `Docs/architecture.md` |
| LLM export/import, HP queue, `utfall`, projector secrecy | `Docs/LLM_WORKFLOW.md` |
| External LLM instructions | `Docs/prompt.md` (this file is loaded at copy time) |
| Room rules (teams, spy, paper news) | `Docs/Stabsspel Traineeprogrammet.md` |
| UX working notes | `Docs/UX_CONSOLE_REWORK.md` (log only, not the UI spec) |

Do not rewrite unrelated docs. Do not treat the UX working log as current specification.

## Completion check

Before considering a Python change complete:

1. Confirm the requested behaviour works.
2. Confirm relevant existing behaviour still works.
3. Run the smallest relevant test set.
4. Run broader fast tests when the change touches shared domain logic.
5. Check saved-game compatibility when persisted state changed.
6. Check GM/public data separation when payloads changed.
7. Update the docs that describe what you changed.
8. Report any remaining risk or adjacent issue separately rather than silently expanding scope.
