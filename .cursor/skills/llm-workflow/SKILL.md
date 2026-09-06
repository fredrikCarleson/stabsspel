---
name: llm-workflow
description: >-
  Guides Stabsspel LLM copy/import: prompt.md, frozen D100, utfall, nyheter,
  HP queue, milstolpar, projector secrecy. Use when editing Docs/prompt.md,
  LLM_WORKFLOW.md, llm_import/llm_apply, rolls, utfall, llm_forslag,
  Kopiera till LLM, Tillämpa HP, or news that must stay off the projector.
---

# Stabsspel LLM workflow

The app never calls a model. The GM copies a filled prompt, pastes **JSON only** back, then confirms HP and milestones.

Contract: [Docs/LLM_WORKFLOW.md](../../../Docs/LLM_WORKFLOW.md).
External instructions: [Docs/prompt.md](../../../Docs/prompt.md).
Python layering: [python](../python/SKILL.md). Room rules: [game-rules](../game-rules/SKILL.md).

## Do not

- Call an LLM from the server or invent an in-app news CMS.
- Put live rolls in `Docs/prompt.md` (it is a template; placeholders are filled at copy time).
- Treat `utfall` as wallet HP or backlog progress.
- Auto-apply `hp[]` or `milstolpar[]` on import.
- Send `llm_forslag`, `llm_resolution`, rolls, probabilities, `utfall`, orders, or inbox to `build_public_state`.
- Reroll frozen dice on undo or re-export.
- Invent `order_ref` values or dice the app did not freeze.

## Copy → import → apply

```
Diplomatifas / Resultatfas
  Kopiera till LLM  →  GET /admin/<id>/order_summary
                       fills Docs/prompt.md, freezes 1–100 per submitted order
  GM pastes JSON    →  POST /admin/<id>/llm_import
                       stores llm_forslag + optional utfall (GM-only)
  Confirm           →  POST /admin/<id>/llm_apply
                       Tillämpa HP → hp_pending (next round)
                       Tillämpa milstolpar → backlog now
```

News go to paper for the studio. They never appear on the projector.

## Three HP meanings

| Name | Meaning | When the wallet changes |
|------|---------|-------------------------|
| **Satsad HP** | Stake vs resistance in `utfall` | Never |
| **Kassa-HP** | `bas + varaktigt + tillfalligt` | LLM: after **Tillämpa HP**, then **Starta nästa runda** (temporary next round, or **Avsluta spelet** after round 4). GM ± in Orderfas: immediately |
| **Backlog-HP** | `spenderade_hp` on Teamens arbete | After **Tillämpa milstolpar** or Inkorg. Not wallet |

A successful `utfall` does **not** create an `hp[]` row. Empty `hp` means no wallet change. LLM `hp[]` is temporary next-round kassa. Lasting income is GM-only on Lag.

## Dice

- `ensure_round_rolls` freezes one D100 per submitted `order_ref` in `llm_resolution.<runda>.rolls`.
- Drafts get no `order_ref` and no roll.
- Unused rolls are valid for ordinary backlog work. Import does not reject a reply that omits `utfall` for a custom order; the GM tab lists those gaps.
- Import rejects `utfall.slump` that does not match the frozen value.
- Ordinary undo must not create new rolls.

## Import rules

Expected top-level: `runda`, `utfall`, `nyheter`, `hp`, `milstolpar`. Schema lives in `Docs/prompt.md`.

- Strip a wrapping ` ```json ` fence. Extra prose around the object is an error.
- `utfall`: empty is allowed; if present, **every** item must be valid or the whole import fails.
- `nyheter` / `hp` / `milstolpar`: unknown teams skipped; `delta` 0 skipped; negative milestone HP dropped.
- Re-import must not re-enable HP or milestones already applied this round. Undo first.

## Code map

| Change | Where |
|--------|--------|
| Export text / placeholders / dice | `gm_console.build_llm_export_text`, `ensure_round_rolls` |
| Parse / import | `parse_llm_forslag`, `parse_utfall_items`, `import_llm_forslag` |
| Apply | `apply_llm_hp`, `apply_llm_milestones` |
| Projector forecast | `build_public_state`, `next_round_hp_view` |
| HTTP | `GET /admin/<id>/order_summary`, `POST .../llm_import`, `POST .../llm_apply` |
| GM cards | `gm_console_ui.py` tab **LLM-resultat** |
| Prompt wording | `Docs/prompt.md` |
| Example JSON | `testdata/llm-svar-exempel.json`, `testdata/llm-svar-utfall-exempel.json` |

Tests: `tests/test_domain.py` for parse/queue/secrecy. Authored four-round JSON: [scenario-playthrough](../scenario-playthrough/SKILL.md).

## When changing this area

1. Read the current functions above before editing.
2. Preserve the copy-paste contract unless the user explicitly wants an in-app model call.
3. Update `Docs/LLM_WORKFLOW.md` in the same change. Update `Docs/prompt.md` only when the **external** LLM should think differently.
4. Add or extend a domain test for rolls, import rejection, HP queue, apply-once, undo-without-reroll, or projector secrecy.
5. Do not put headlines on the projector to "make the room see news".
