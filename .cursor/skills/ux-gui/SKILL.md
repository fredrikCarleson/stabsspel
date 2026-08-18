---

name: ux-gui
description: >-
Design and change Stabsspel UI: GM console, room projector, team order form,
homepage, app.css tokens, Swedish labels, no SPA. Use when reviewing or editing
HTML, CSS, JS, gm_console_ui.py, visual layout, buttons, projector, or backgrounds.
-----------------------------------------------------------------------------------

# Stabsspel UX / GUI

Stabsspel is a live staff-exercise runner for a Swedish room of 20–60 people.

It is not a CRUD admin product.

The GM runs the clock and operates the live console. The projector shows shared public state to the room. Teams submit orders from phones.

Software map: [Docs/architecture.md](../../../Docs/architecture.md).
Python layering: [python](../python/SKILL.md) skill.
Design tokens and UI classes live in `static/app.css`.

## UX principle

Design for a live exercise under time pressure.

The interface should help the user answer quickly:

* Where are we?
* What is happening?
* What needs my attention?
* What is the likely next action?
* What can safely wait?

Prioritize situational awareness and error prevention over feature visibility.

A screen where everything is emphasized has no hierarchy.

## Before changing a screen

Before editing UI code:

1. Identify who uses the screen.
2. Identify what they are trying to accomplish at this moment in the game.
3. Identify the 1–3 most important actions or pieces of information.
4. Look for friction, ambiguity, competing controls and unnecessary information.
5. Separate UX problems from purely visual polish.
6. Inspect the relevant existing HTML, CSS, JS and tests before proposing changes.

If the user asks for review, critique or suggestions, **do not implement immediately**.

First provide:

* the biggest UX/UI problems,
* their impact during live use,
* a proposed hierarchy or layout,
* what should become primary, secondary or hidden.

Wait for approval before coding.

## Surfaces

| Surface            | Audience               | Files                                          | Rule                                                                          |
| ------------------ | ---------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------- |
| Spelledarpanel     | GM, laptop             | `gm_console_ui.py`, `static/gm-console.js`     | Live operational console: clock, attention, HP, inbox, backlog, log           |
| Spelarskärm        | Room projector         | `create_projector_html`, `static/projector.js` | Round, phase, time, public HP only. No buttons, orders, log or GM information |
| Team order form    | Players, usually phone | `team_order_routes.py`                         | Token URL. Draft autosave, submit, withdraw only in Orderfas                  |
| Home / create game | GM before start        | `app.py`, `admin_routes.py`                    | List, open, download, delete, create/upload                                   |
| Print              | Paper                  | `orderkort.py`, `static/print.css`             | Separate from live UI                                                         |

There is no SPA framework and no `templates/` directory. HTML is built in Python.

Prefer extending the existing live console over adding another full page.

**Leftover chrome** such as the old quarter bar, checklists and extra timer widgets below the console is not the live GM UI. Do not add new workflows there.

News stay on paper for the studio:

**copy orders → LLM JSON (with app dice) → paste suggestions → paper → studio**

Keep `Kopiera ordrar till LLM` as the export step. Pasted JSON may suggest headlines, HP, milestones, and GM-only `utfall`. Do not add an in-app headline editor. Rolls, probabilities and motivering stay off the projector.

## Design for the current task

Do not treat every available control as equally important.

The hierarchy should reflect what the user needs to do **right now**.

For example, during Orderfas the GM primarily needs to:

* see current round and phase,
* start or monitor the timer,
* see which teams have submitted,
* notice exceptions requiring attention,
* advance to the next phase when appropriate.

Controls unrelated to the immediate task should be visually secondary.

Do not make every feature permanently prominent simply because it exists.

## Prevent live-operation mistakes

Assume the GM is:

* under time pressure,
* interrupted by players,
* scanning rather than reading,
* using the application for several hours,
* occasionally operating while speaking to the room.

Avoid:

* several equally prominent primary actions,
* dangerous and routine buttons mixed together,
* neighbouring controls with very different consequences,
* unclear active/inactive states,
* labels whose effect is ambiguous,
* state the GM must remember instead of seeing,
* important information available only on hover.

Phase changes, destructive actions and irreversible actions must be visually distinct from routine controls.

Use confirmation only where it reduces meaningful risk. Do not interrupt routine live operation with unnecessary modal dialogs.

## Progressive disclosure

Keep frequent live actions visible.

Move infrequent, administrative, debug or risky controls behind:

* `Mer`,
* expandable sections,
* contextual menus,
* or visually secondary controls.

Typical secondary candidates include:

* reset actions,
* Testläge,
* setup functions,
* maintenance/debug controls,
* rarely used timer actions.

Do not hide information required for situational awareness.

## Visual hierarchy

For every screen ask:

1. What must the user notice first?
2. What must they notice second?
3. What is the likely next action?
4. What only needs to be available, not prominent?

Use:

* placement,
* grouping,
* whitespace,
* size,
* typography,
* contrast

before adding more colour.

Do not use colour as the only way to communicate state.

## Laptop vs projector

The GM console and projector are different products sharing game state.

### GM console

Optimize for:

* fast operation,
* moderate information density,
* obvious next actions,
* exceptions and attention states,
* safe interaction.

### Projector

Optimize for:

* viewing from several metres away,
* extremely fast comprehension,
* very low information density,
* strong contrast,
* large typography.

Projector rules:

* no operational controls,
* no inbox,
* no log,
* no secret information,
* no Testläge,
* no hover-only information.

Never solve a projector problem by adding GM detail.

Never solve a GM workflow problem by making the console projector-like.

## Team order form

Assume players may use phones and may be moving around the room.

Prioritize:

* clear current round/phase,
* obvious draft/submitted state,
* large touch targets,
* readable inputs,
* clear HP/order relationship,
* confidence that an order has actually been saved/submitted.

Do not add unnecessary controls or dense desktop-style layouts.

Submission state must never be visually ambiguous.

## Language and density

Visible UI labels are Swedish.

Examples:

* `Nästa fas`
* `Ångra`
* `Spelarskärm`
* `Ta bort`

Match existing wording where possible. Do not introduce parallel English terminology.

The room is noisy and time-pressured.

Prefer:

* concise labels,
* large enough type,
* clear spacing,
* few competing actions,
* scannable status.

Avoid explanatory paragraphs where a short label or status is enough.

Keyboard on the GM console:

* **Space** = pause/resume
* **N** = next phase with existing confirmation

Do not steal these shortcuts for new features without a clear reason.

## Visual direction

The visual identity should support a serious live crisis simulation.

Aim for:

* professional,
* calm,
* strategic,
* modern,
* authoritative,
* slightly dramatic where appropriate.

Avoid:

* generic SaaS appearance,
* unnecessary cyberpunk styling,
* excessive neon,
* arcade-game UI,
* decorative complexity that reduces readability.

Atmosphere must never compete with operational information.

## Visual system

Main stylesheet: `static/app.css`
Print stylesheet: `static/print.css`

Bump the relevant `?v=` cache-bust when CSS or JS changes so live browsers do not keep stale assets.

### Fonts

* `--font-ui` — Inter for body and controls
* `--font-display` — Bebas Neue for headings/display information

Prefer the existing typography. Do not introduce new fonts without a strong reason.

### Existing tokens

Use existing tokens before introducing new values.

Surfaces:

* `--c-bg`
* `--c-surface`
* `--c-border`
* `--c-text`
* `--c-muted`

Status:

* `--c-primary`
* `--c-success`
* `--c-warning`
* `--c-danger`
* `--c-secondary`
* `--c-info`

Teams:

* `--t-alfa`
* `--t-bravo`
* `--t-stt`
* `--t-fm`
* `--t-bs`
* `--t-media`
* `--t-sapo`
* `--t-reger`
* `--t-usa`

Radius/shadow:

* `--radius-6`
* `--radius-8`
* `--radius-12`
* `--shadow-sm`
* `--shadow-md`
* `--shadow-lg`

Prefer spacing, grouping and typography changes over adding a new palette.

## Buttons

Buttons are not BEM.

Use element + modifier classes:

```html
<button class="primary">Öppna</button>
<button class="danger sm">Ta bort</button>
<a class="secondary" href="…">Tillbaka</a>
```

Existing modifiers:

* `primary`
* `success`
* `warning`
* `danger`
* `info`
* `secondary`
* `sm`
* `lg`
* `ghost`

The same classes may be used on `<a>` elements.

Primary actions should be genuinely primary in the current workflow.

Do not solve hierarchy problems by turning several buttons into different bright colours.

## Existing UI classes

Notifications:

* `.notification.success`
* `.notification.error`

Modals:

* `.modal`
* `.modal-content`
* `.is-open`

GM clock:

* `.gm-clock.is-warning`
* `.gm-clock.is-danger`

Order status:

* `gm-status-empty`
* `gm-status-draft`
* `gm-status-submitted`
* `gm-status-changed`

Reuse existing patterns before creating parallel classes.

## Backgrounds and imagery

Background images belong in:

`static/backgrounds/`

and are served from:

`/static/backgrounds/<filename>`

Prefer clean filenames such as existing `bg-*.png`.

Do not commit generated assets with long export names or spaces unless there is a clear reason.

When using backgrounds:

* preserve text contrast,
* use overlays/gradients when needed,
* avoid busy imagery behind live information,
* do not stretch source images,
* choose sensible focal positioning,
* test common 16:9 displays.

Background imagery is atmosphere, not information.

## HTML and JS patterns

* Escape every dynamic string with `markupsafe.escape` when interpolating into HTML.
* Live regions replaced by polling must keep stable IDs such as `gm-clock`, `gm-state`, `projector-state`.
* JS reads initial JSON from `<script type="application/json">` and updates from `/live` payloads.
* `gm-console.js` and `projector.js` are IIFEs with no build step.
* Match the existing plain-JS style rather than introducing a framework or bundler.
* Destructive or phase-changing actions use existing POST/fetch patterns and Swedish confirmation.
* Delete-game remains handled through the password modal in `admin.js`.
* Clock warning thresholds (do not treat them as identical):

  * GM console: ≤5 min warning, ≤1 min danger
  * Projector: ≤5 min warning, ≤1 min danger, ≤30s critical
  * Projector audio (room): chime at 5 min, chime at 1 min, repeating alarm at ≤30s while the timer is running
  * Browsers often block sound until the projector window is clicked once
* `:focus-visible` outlines already exist globally.
* Do not use `outline: none` without an equally visible replacement.
* Keep `aria-label` on compact icon-only and stepper controls.
* Testläge remains hidden unless explicitly enabled.
* Never expose Testläge on the projector.

## Change discipline

Prefer the smallest coherent UX improvement.

Do not redesign neighbouring screens unless:

* a shared component must change,
* or the user explicitly asks for a broader redesign.

Do not introduce new workflows or functionality merely because they would make a mock-up look cleaner.

If solving a UX problem requires behavioural changes, explain that separately before implementing.

Preserve working interaction patterns unless there is a clear usability reason to change them.

If you notice adjacent UX debt, report it separately instead of silently expanding scope.

## Responsive design

Do not treat responsive behaviour as shrinking the desktop layout.

Check the actual task for each viewport.

### GM laptop

Ensure:

* primary controls remain visible,
* important state is not pushed below low-value controls,
* cards do not become unnecessarily tall,
* live workflow still scans quickly.

### Phones

For team-facing forms:

* stack content logically,
* use practical touch targets,
* avoid horizontal scrolling,
* keep submit/save state visible.

### Projector

Design explicitly for common 16:9 screens.

Important room-facing content should remain readable on a 1920×1080 projector from several metres away.

## UX completion check

Before considering a UI change complete, ask:

* Can the primary state be understood in 2–3 seconds?
* Is the likely next action obvious?
* Are dangerous and routine actions clearly separated?
* Have secondary controls been visually demoted where appropriate?
* Has unnecessary information been removed or reduced?
* Can the GM use the screen while distracted?
* Does the screen work at common laptop widths?
* Does the team form work comfortably on a phone?
* If room-facing, is it readable from several metres away?
* Has cognitive load decreased rather than merely making the page prettier?

## Technical checklist for UI changes

* [ ] Swedish labels use existing terminology
* [ ] Existing button classes and design tokens reused where possible
* [ ] GM work landed on the live console, not leftover admin chrome
* [ ] Projector still contains no inbox, log, Testläge, orders or controls
* [ ] Dynamic HTML remains escaped
* [ ] Poller IDs and JS hooks still match
* [ ] Keyboard shortcuts still work
* [ ] Focus states remain visible
* [ ] Relevant CSS/JS cache-bust version was bumped
* [ ] Existing behaviour was not changed unintentionally
* [ ] Relevant tests still pass
