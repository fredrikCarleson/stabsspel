# UX rework — live console and start screen

Working log for the GM/projector UX pass started 2026-08-17.
**Read this before continuing the work.** It is the source of truth for what was agreed, what shipped, and what is still open.

Related: [architecture.md](architecture.md), skills `.cursor/skills/ux-gui/SKILL.md` and `.cursor/skills/python/SKILL.md`.

## Goal

A live crisis exercise. The GM should see **where we are, what needs attention, and the next action** in a few seconds. Phase screens focus on **that phase’s job**. Reference tools stay available but are not all unfolded at once.

Do not add features unless they fix a clear UX problem. Do not redesign the whole app. No SPA. Swedish labels. News stay on paper for the studio (copy orders → LLM JSON with app dice → paste suggestions → paper → studio). GM-only `utfall` (probability, roll, result) stays on the console.

## Agreed slices

| Slice | Status | What |
| ----- | ------ | ---- |
| Start screen | **Done** | Launch list, not a marketing landing page. Light `bf-frontpage.png` behind opaque rows. |
| 1. Orderfas job | **Done** | Readiness chips, quieter attention, Start/Pause vs Nästa, extra controls under Mer, HP folded. |
| Projector audio | **Done** | Room warnings at 5 min, 1 min, repeating alarm at 30 s. |
| 3. Diplomatifas job | **Done** | Inbox + conflicts + LLM copy/import first (rolls + utfall). HP / backlog / log folded. |
| Resultatfas job | **Done** | Körschema first, in-console quarter strip, HP / inbox / backlog / log folded. Utfall visible if imported. |
| 2. Tab shell | **Done** | Sticky bar + four always-available views: Inkorg, Lag, Arbete, Historik. Changing phase lands on the phase job (Order/Diplo → Inkorg, Resultatfas → Lag with körschema above). Clock never lives in a tab. |
| 4. One console | **Done** | Leftover **Kvartalsförlopp / Team översikt / Spelhistorik** no longer render under the console. Quarters stay in Resultatfas. Phase history sits in **Händelselogg**. Teamens arbete remains the backlog. |
| Background images | **Trial** | Spelledarpanel: dimmed `bg-stabsrum.png`, no side banners. Startsida: `bf-frontpage.png`. Projector and team form stay plain. `bg-sverige.png` unused. |

## What shipped (so a new session does not redo it)

### Start screen (`app.py` `startsida`, `static/app.css` `.home-*`)

- Compact header: Stabsspelet, **Ladda upp**, **Starta nytt spel**
- Main surface: **Öppna spel** as rows (date/place, round/phase, **Öppna**)
- Active games first; finished muted
- **Ladda ner** / **Ta bort** under per-row **Mer** (delete still uses password modal)
- No hero, no feature cards
- Light `bf-frontpage.png` behind the page (map/hexes in the margins). Header and game rows stay opaque.

### Orderfas (`gm_console_ui.py`)

- Sticky bar: clock, **Starta** XOR **Pausa**, ±1 min, **Nollställ timer**, Spelarskärm, **Nästa** as `primary` (not a second green), **Föregående** next to it, **Ångra**. **Meny** sits top-left in the panel header (hamburger + label, Heroicons on items).
- Readiness chips: Saknas / Utkast / Inne + HP. Completeness notes (saknar HP, inte låst)
- Yellow **Kräver uppmärksamhet** hidden unless there is a real exception (not a repeat of the missing-team list)
- **Lag och handlingspoäng** collapsed in `<details class="gm-fold">`
- GM clock: ≤5 min warning, ≤1 min danger (`gm-console.js`)

### Diplomatifas

- Order: attention (missing teams + conflicts) → **Kopiera ordrar till LLM** + paste JSON → **Utfall och sannolikhet** (after import) → **Orderinkorg** → folded HP / Teamens arbete / Händelselogg
- Conflict rows: `gm-conflict` + visible **Konflikt** label (not colour alone)
- **Nästa: Resultatfas**

### Resultatfas

- Job is the körschema: open projector, news on paper (from LLM-förslag), point at HP, point at quarters, next round / end
- Compact quarter strip (Okt–Dec … Jul–Sep) lives **in the console**, current round marked. Körschema no longer points at leftover chrome below the panel
- Folded: Orderinkorg, Lag och handlingspoäng, Teamens arbete, Händelselogg
- LLM copy/import and utfall still available under the körschema
- Ended game shows **Spelet är slut** instead of the rundown

### Projector (`static/projector.js`, `create_projector_html`)

- Visual: ≤5 min warning, ≤1 min danger, ≤30 s critical pulse
- Audio: one chime at 5 min, one at 1 min, repeating alarm while running and ≤30 s
- Browsers often need **one click** on the projector window (`Klicka för ljudvarningar`)
- Projector still has no GM controls, inbox, log, or Testläge

### Testläge, order edit, Meny (2026-08-17)

- **Testläge** is saved on the server (form POST + JSON). The checkbox is no longer a client-only lie; testdataåtgärden stays behind Testläge in **Meny** instead of occupying the order inbox.
- **Fyll med testdata** loads `testdata/testdataroundN.json` for the current round. When orders already exist, the menu action is labelled **Ersätt med testdata…**. Round 1 is the old built-in set; rounds 2–4 follow each team’s goals (declaration freeze in round 3, production/election in round 4).
- **Redigera order** is always available in Orderfas and Diplomatifas (team cards + inbox). It opens the team form so the GM can revise before LLM. **Ändra** remains the inline HP/text edit.
- Overflow control is a classic **Meny** in the top-left of the dark panel header, with Heroicons on each item. **Nollställ timer** sits with +1/−1 min.
- **Föregående** sits beside **Nästa**. No confirm that claims you cannot go back. Confirm remains for missing orders, next round, and end game.

### One console (slice 4)

- The spelledarpanel is header + declaration warning + live console. No KVARTALSFÖRLOPP / Team översikt / Spelhistorik under it.
- Resultatfas still has the named quarter strip in the körschema.
- **Händelselogg** starts with a compact phase timeline (runda + klar/pågår), then GM actions.
- `create_team_overview` still exists for the team order form. Old checklist/timer HTML builders in `admin_routes.py` are unused on the panel.

### Tab shell (slice 2)

- Under the sticky clock: **Inkorg**, **Lag**, **Arbete**, **Historik**. No new URLs.
- Orderfas and Diplomatifas open on **Inkorg**. Resultatfas keeps the körschema above the tabs and opens **Lag**.
- Readiness chips, attention and LLM copy stay outside the tabs.
- Phase change reloads the console, so the last tab is not kept.

### Orderinkorg (grouped)

- Rows are grouped by lag. Team actions (**Öppna för laget**, **Redigera**) sit on a team header, once.
- Activity rows: name, Bygga/Förstöra tag, HP. **Ändra** is a quiet pencil.
- **Lägg +HP** is green and only in Diplomatifas/Resultatfas. Orderfas hides it.
- HP shows spent / backlog estimate when they differ (e.g. 10 / 15).

### Backgrounds (trial)

- Spelledarpanel `body.gm-page`: dimmed `bg-stabsrum.png`. Console column stays almost opaque. No side banners.
- Startsida: `bf-frontpage.png` as atmosphere. Header and game rows stay opaque.
- Projector and team order form stay plain.
- `bg-sverige.png` is not used.

### LLM-export and suggestions (2026-08-18)

- Copy text is `Docs/prompt.md` filled with round, teams, backlog, orders (`order_ref` like `Alfa-1`), frozen 1–100 rolls, and previous `utfall`.
- First copy for a round creates `llm_resolution.<runda>.rolls` and saves them. Copy/refresh/undo does not reroll. A new activity gets a new ref/roll only.
- Paste or upload JSON on the export page. Stored as `llm_forslag` plus `llm_resolution.<runda>.result.utfall`, then shown in Diplomatifas/Resultatfas. Not sent to the projector.
- GM sees **Utfall och sannolikhet** only for probabilistically resolved outcomes (optional `delmal` when just part of an order was rolled). Ordinary backlog work belongs under milstolpar, not as a dice card. News are copied to paper for the studio. **Tillämpa HP** and **Tillämpa milstolpar** are confirm + undo.
- Old JSON without `utfall` still imports. Example files: `testdata/llm-svar-exempel.json`, `testdata/llm-svar-utfall-exempel.json`.
- Invalid JSON still fails on `json.loads` (no auto-repair). The LLM export/import page shows line/column, a snippet with a marker, and a short hint (citationstecken, kommatecken, text utanför JSON). One outer markdown fence around the whole payload is stripped. Pasted text stays in the textarea. **Kopiera fel** copies the message for pasting back to the LLM. Domain/`utfall` errors stay separate.

### One-window LLM flow (2026-08-19)

- **Kopiera till LLM** and Meny → **LLM-export** now open in the current browser tab.
- The paste/upload form lives only on the export page. Import errors stay on that page with the pasted JSON preserved; a successful import returns to the spelledarpanel.
- Diplomatifas/Resultatfas keeps a compact LLM status/action row. Imported output lives in the ordinary **LLM-resultat** console tab, without a second competing paste form or nested result tabs.
- The export page is now a focused two-tab workspace: **1. Kopiera till LLM** and **2. Klistra in LLM-svar**. Normal visits open tab 1; import errors reopen tab 2.
- The legacy **Detaljerad översikt** with repeated team/activity cards was removed from this page. Orders remain in the console inbox and still feed the generated LLM prompt.

### Focused polish pass (2026-08-18)

- Timerstatus is Swedish and pairs text with a status dot: **Inte startad / Pågår / Pausad**.
- Team cards make **Kvar att använda** the primary HP value; available, spent, base and transferable HP remain subordinate.
- LLM work reads as **Kopiera → Skicka → Klistra in**. After a successful import, the paste field folds under **Ersätt LLM-svar** instead of occupying the result view.
- `utfall` cards emphasize **Chans → Slag → Utfall** with text and symbols as well as colour. News, HP consequences and milestones are separate quiet sections rather than one long blue block.
- Resultatfas keeps the whole LLM result available in the same **LLM-resultat** console tab as Diplomatifas, while Lag remains the default view.
- LLM output has a four-part count summary. Utfall stays visible; Nyheter, HP and Milstolpar are expandable sections. Pending HP/milestone actions open automatically and mark the main LLM tab with **Att göra**.
- HP and milestone suggestions are single-apply operations: the submit button disables immediately, the server rejects/reconciles repeated POSTs, re-import cannot re-arm an applied consequence, and the applied tab shows a persistent **✓ … är tillämpade** state. Undo is the explicit revision path.
- Backlog rows show `spenderat / totalt HP`, remaining effort, and a compact progress bar split into **förra rundan** / **tillagt** / **draget**. Repeating work does not get a completion bar. Klar is written as text, not as a green bar.
- Console and the focused LLM export/import workspace use the same shared tab component: blue selected state, selected underline, uniform counts, focus state and keyboard navigation. Tabs that need a GM action show the word **Att göra**, not only a color.
- **Tillämpa HP** schedules wallet changes for the next round. The Lag card shows **Nästa runda ±N** until **Starta nästa runda**.
- The start list explicitly marks active games as **Pågår**. The mobile team form gives **Kvar** visual priority and stacks save/submit actions into full-width touch targets.
- Milstolpar har nu en väg: när LLM-förslag finns ligger den samlade åtgärden högst upp i **LLM-resultat** och Inkorg hänvisar dit. Tillämpning i endera vyn synkas till den andra i live-uppdateringen, så **Att göra** och knappar försvinner när arbetet är klart och samma progress inte kan räknas två gånger.
- Spelledarpanelens tidigare stora titelblock är ersatt av en kompakt tvådelad kontrollheader. Runda, fas, timer, spelmetadata och spelarskärm ligger överst; fas- och timeråtgärder samt den fullständiga **Meny**-dropdownen ligger på en smal åtgärdsrad under.

## Still to do (priority)

1. Optional later: delete unused checklist / `create_timer_html` builders in `admin_routes.py`.

## Explicit non-goals

- Auto-open last game
- Auto-advance when the timer hits 0
- In-app headline editor (suggestions from LLM JSON are not an editor)
- Dark C2 restyle of the whole app
- Separate page per phase
- Using `bg-sverige.png` as a functional background under live HP/clock

## Files to touch next

| Job | Files |
| --- | ----- |
| Cache-bust | Console CSS is `app.css?v=35`, JS `gm-console.js?v=14`. Bump when CSS/JS changes. |

## How to continue in a new chat

1. Read this file and the ux-gui skill.
2. Ask for a screendump of the phase you will change, or implement the next slice in the table above.
3. Mark the slice **Done** here when it ships.
4. Do not implement leftover chrome workflows. Do not reopen Orderfas/Diplomacy unless the user reports a live-play bug.
