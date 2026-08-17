# UX rework — live console and start screen

Working log for the GM/projector UX pass started 2026-08-17.
**Read this before continuing the work.** It is the source of truth for what was agreed, what shipped, and what is still open.

Related: [architecture.md](architecture.md), skills `.cursor/skills/ux-gui/SKILL.md` and `.cursor/skills/python/SKILL.md`.

## Goal

A live crisis exercise. The GM should see **where we are, what needs attention, and the next action** in a few seconds. Phase screens focus on **that phase’s job**. Reference tools stay available but are not all unfolded at once.

Do not add features unless they fix a clear UX problem. Do not redesign the whole app. No SPA. Swedish labels. News stay outside the app (copy orders → LLM → paper → studio).

## Agreed slices

| Slice | Status | What |
| ----- | ------ | ---- |
| Start screen | **Done** | Launch list, not a marketing landing page. No background images (deferred). |
| 1. Orderfas job | **Done** | Readiness chips, quieter attention, Start/Pause vs Nästa, extra controls under Mer, HP folded. |
| Projector audio | **Done** | Room warnings at 5 min, 1 min, repeating alarm at 30 s. |
| 3. Diplomatifas job | **Done** | Inbox + conflicts + LLM copy first. HP / backlog / log folded. |
| Resultatfas job | **Done** | Körschema first, in-console quarter strip, HP / inbox / backlog / log folded. |
| 2. Tab shell | **Not done** | Sticky bar + four always-available views: Inkorg, Lag, Arbete, Historik. Changing phase lands on the phase job, not the last tab. |
| 4. One console | **Not done** | Fold leftover **Kvartalsförlopp / Team översikt / Spelhistorik** (under the console in `admin_routes.py`) into Arbete / Historik / Resultatfas. Do not add new workflows to that leftover chrome. |
| Background images | **Deferred** | Assets in `static/backgrounds/`. Do not put `bg-sverige.png` under controls. `bg-stabsrum.png` only as dimmed atmosphere; banners as marks, not 16:9 fills. |

## What shipped (so a new session does not redo it)

### Start screen (`app.py` `startsida`, `static/app.css` `.home-*`)

- Compact header: Stabsspelet, **Ladda upp**, **Starta nytt spel**
- Main surface: **Öppna spel** as rows (date/place, round/phase, **Öppna**)
- Active games first; finished muted
- **Ladda ner** / **Ta bort** under per-row **Mer** (delete still uses password modal)
- No hero, no feature cards, no background images

### Orderfas (`gm_console_ui.py`)

- Sticky bar: clock, **Starta** XOR **Pausa**, ±1 min, Spelarskärm, **Nästa** as `primary` (not a second green), **Ångra**
- Under **Mer**: Nollställ timer, Föregående fas, Testläge, exports, reset
- Readiness chips: Saknas / Utkast / Inne + HP. Completeness notes (saknar HP, inte låst)
- Yellow **Kräver uppmärksamhet** hidden unless there is a real exception (not a repeat of the missing-team list)
- **Lag och handlingspoäng** collapsed in `<details class="gm-fold">`
- GM clock: ≤5 min warning, ≤1 min danger (`gm-console.js`)

### Diplomatifas

- Order: attention (missing teams + conflicts) → **Kopiera ordrar till LLM** → **Orderinkorg** → folded HP / Teamens arbete / Händelselogg
- Conflict rows: `gm-conflict` + visible **Konflikt** label (not colour alone)
- **Nästa: Resultatfas**

### Resultatfas

- Job is the körschema: open projector, news on paper, point at HP, point at quarters, next round / end
- Compact quarter strip (Okt–Dec … Jul–Sep) lives **in the console**, current round marked. Körschema no longer points at leftover chrome below the panel
- Folded: Orderinkorg, Lag och handlingspoäng, Teamens arbete, Händelselogg
- LLM copy still available under the körschema
- Ended game shows **Spelet är slut** instead of the rundown

### Projector (`static/projector.js`, `create_projector_html`)

- Visual: ≤5 min warning, ≤1 min danger, ≤30 s critical pulse
- Audio: one chime at 5 min, one at 1 min, repeating alarm while running and ≤30 s
- Browsers often need **one click** on the projector window (`Klicka för ljudvarningar`)
- Projector still has no GM controls, inbox, log, or Testläge

## Still to do (priority)

1. **Tab shell (slice 2)** — only if unfolding `<details>` is not enough. Four tabs across all phases; clock never lives in a tab. No new URLs, no SPA.
2. **Retire leftover chrome (slice 4)** — `Kvartalsförlopp`, `Team översikt`, `Spelhistorik` below the console in `admin_routes.py` duplicate live data. Move or delete; do not grow them. Resultatfas no longer depends on that quarter bar.
3. **Backgrounds** — only after the operational layout is stable, and only as chrome (not under live numbers).

## Explicit non-goals

- Auto-open last game
- Auto-advance when the timer hits 0
- In-app headlines / news editor
- Dark C2 restyle of the whole app
- Separate page per phase
- Using `bg-sverige.png` as a functional background (fake HP/clock)

## Files to touch next

| Job | Files |
| --- | ----- |
| Tabs | `gm_console_ui.py`, `static/gm-console.js`, `static/app.css` — keep poller ids (`gm-clock`, `gm-inbox-root`, `gm-backlog-root`, `gm-log-root`, `gm-attention`, `gm-readiness-root`) |
| Leftover chrome | `admin_routes.py` (quarter bar / historik injected **under** `create_gm_console_html`) |
| Cache-bust | Console CSS is `app.css?v=15` (as of Resultatfas). Bump when CSS/JS changes. |

## How to continue in a new chat

1. Read this file and the ux-gui skill.
2. Ask for a screendump of the phase you will change, or implement the next slice in the table above.
3. Mark the slice **Done** here when it ships.
4. Do not implement leftover chrome workflows. Do not reopen Orderfas/Diplomacy unless the user reports a live-play bug.
