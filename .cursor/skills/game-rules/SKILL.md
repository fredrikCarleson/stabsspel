---
name: game-rules
description: >-
  Applies Stabsspel room rules versus software: four rounds,
  Orderfas/Diplomatifas/Resultatfas, 5 vs 9 teams, HP, spy as a physical HP
  transfer, paper news, hidden agendas. Use when changing game mechanics,
  teams, HP, spy, backlog, regeringsstöd, or reading
  Docs/Stabsspel Traineeprogrammet.md.
---

# Stabsspel game rules

The exercise is a live Swedish staff game for 20–60 people. The app keeps clock, orders, HP, backlog, and phase. It is not the whole game.

Full room rules: [Docs/Stabsspel Traineeprogrammet.md](../../../Docs/Stabsspel%20Traineeprogrammet.md).
Software map: [Docs/architecture.md](../../../Docs/architecture.md).
LLM contract: [llm-workflow](../llm-workflow/SKILL.md).
Code: [python](../python/SKILL.md).

If the rules doc and `gm_console.py` disagree, do not silently pick one. Decide stale docs vs code defect, then report before changing mechanics.

## What lives in software vs the room

| In the app | In the room (do not encode as first-class state) |
|------------|--------------------------------------------------|
| Round, phase, timer | Whiteboard timeline, seating, shouting |
| Team wallets, transfers | Spy physically walking to BS |
| Orders, inbox, backlog | Hidden-agenda roleplay |
| LLM export/import, GM `utfall` | News studio reading paper headlines |
| Printable briefs, QR, orderkort, aktivitetskort | Who is the spy, who saw the drop |

Do not add spy seating, player roster, or an in-app headline editor unless the user explicitly asks for that product change.

## Structure

- Four rounds (`runda` 1–4). Named year-quarters are flavour; the code uses numbers.
- Each round: **Orderfas** → **Diplomatifas** → **Resultatfas**.
- After round 4 Resultatfas the game ends (`avslutat`). There is no round 5.
- Missed Orderfas submit = no orders that round (HP is not spent).

## Teams and HP

Roster (`models.resolve_active_teams` / persisted `lag`):

- **Core game:** Alfa, Bravo, STT, FM, BS
- **Extended game:** those five plus any selection of Media, Regeringen, SÄPO, USA (at least one extra; 6–9 teams)

Legacy player-count inference remains for old saves without an explicit roster: fewer than 27 players → 5 teams, 27 or more → 9 teams.

Wallet is `poang.<lag>`: spendable this round is `bas + varaktigt + tillfalligt` (`aktuell` is a cache).

**Bas** is table HP. **Varaktigt** is lasting income and survives a new round. **Tillfälligt** is this round only (grants, spy, LLM `hp[]`, GM one-off, transfers) and expires at round change.

**Transfers move tillfällig HP this round.** Next round both sides return to income (bas + varaktigt) plus `hp_pending`.

When Regeringen is active, its 12 HP is the political pool: grant to other active teams or spend on influence. Grants leave the pool immediately on submit. Temporary HP expires at the start of the next round before `hp_pending` is applied.

Base HP (code in `models.DEFAULT_HP` / `LARGE_GAME_OVERRIDES`):

| Team | 5-team game | Extended game |
|------|-------------|---------------|
| Alfa, Bravo | 25 | 25 |
| STT | 25 | 30 |
| FM, BS | 12 | 10 |
| Media | — | 12 |
| SÄPO | — | 15 |
| Regeringen | — | 12 |
| USA | — | 12 |

Lasting income is a GM **varaktigt** total on Lag (the stepper shows the current total; **Verkställ** commits the difference). Not a radio that replaces tillfälligt. LLM HP deltas are temporary next-round kassa; see [llm-workflow](../llm-workflow/SKILL.md).

Backlog templates exist only for **Alfa, Bravo, STT**. Bravo work is phased (Krav, Design, …). Some STT tasks are `aterkommande` and start a new attempt at cap. Round 3 is declaration period (`is_declaration_period`): the console shows a warning; STT must not production-set. That freeze is a room/GM rule, not an order-form lock.

## Spy

BS has a spy in Alfa. **Each round the spy physically visits the BS area**, Alfa loses 5 HP and BS gains 5.

In software this is tillfälligt −5 on Alfa and +5 on BS on the Lag tab. FM knows BS has a spy but not who; they negotiate in the room. If exposed, future drops stop — the GM stops making those two adjustments.

Do not add a `spion` flag, seating chart, or automatic −5/+5 each round.

## News and secrets

- Headlines are written on paper and read in the studio.
- Players must not see which hidden actor caused a negative event, nor dice, probabilities, or `order_ref`.
- Projector payload is public HP, round, phase, time (and Resultatfas this-round → next-round HP). Nothing else.

## Hidden agendas

Printed as aktivitetskort. They motivate players; they are not a rules engine. Do not implement each agenda reward as automatic HP unless the user asks to digitize that card.

## Changing mechanics

1. Read the rules section that matches the request, then the live function in `gm_console.py`.
2. Prefer the smallest change that preserves live-event behaviour.
3. Update `Docs/Stabsspel Traineeprogrammet.md` when the **room** rule changes; `Docs/architecture.md` when only software bookkeeping changes.
4. Add a domain test for HP, transfers, roster size, or phase edges.
5. UI strings stay Swedish: spelledare, handlingspoäng, runda, fas. Code keeps existing identifiers (`fas`, `runda`, `poang`, `tillfalligt`, `varaktigt`).
