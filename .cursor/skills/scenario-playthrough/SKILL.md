---
name: scenario-playthrough
description: >-
  Runs and authors the four-round Stabsspel scenario (testdata/scenario_llm
  and testdata/scenario_llm_7lag, seeded D100, transcript, design critique).
  Use when writing rundaN.json, updating transcript.md, reviewing LLM
  resolutions as a game designer, or running tests/scenario_runner.py.
---

# Stabsspel scenario playthrough

In-memory four-round run: Auto-fyll orders, seeded dice, imported JSON. It does **not** write `speldata/`.

LLM contract: [llm-workflow](../llm-workflow/SKILL.md).
Room intent: [game-rules](../game-rules/SKILL.md).
External JSON rules: [Docs/prompt.md](../../../Docs/prompt.md).

## Files

| Path | Role |
|------|------|
| `testdata/testdataround1.json`–`runda4` | Auto-fyll orders (HP scaled to the current wallet; absent optional teams skipped and retargeted) |
| `testdata/scenario_llm/rundaN.json` | Frozen nine-team resolution JSON |
| `testdata/scenario_llm/transcript.md` | Nine-team narrative |
| `testdata/scenario_llm_7lag/rundaN.json` | Frozen seven-team resolution JSON (Media + Regeringen; no SÄPO/USA) |
| `testdata/scenario_llm_7lag/transcript.md` | Seven-team narrative |
| `tests/scenario_runner.py` | Runner, variants, seed, leak checks, transcript writer |
| `tests/test_scenario_playthrough.py` | Mechanical invariants for both years |

Default variant is **nine**. Do not rewrite the nine-team JSON to match seven. Same seed, different roster → fewer rolls per round, so dice **diverge from round 2**. Round 1 `Alfa-1` is still 59 in both.

This is scripted years, not live diplomacy.

## Commands

```bash
python -m unittest tests.test_scenario_playthrough
python tests/scenario_runner.py
python tests/scenario_runner.py dump 1
python tests/scenario_runner.py seven
python tests/scenario_runner.py dump 1 seven
```

`dump N` plays completed rounds, then writes `_dump_rN.json` under that variant's LLM dir. Use that to author `rundaN.json`. Do not commit `_dump_r*.json`.

Seed: `SCENARIO_SEED = 20260901`. Do not change it without updating tests that assert specific rolls (round 1 `Alfa-1` is 59).

## Authoring `rundaN.json`

1. Dump the round (or read frozen rolls from a previous run).
2. Follow `Docs/prompt.md`. Return **only** the JSON object.
3. Reuse the app's `slump` per `order_ref`. Do not invent refs or dice.
4. Put **uncertain** opposing actions in `utfall`. Ordinary backlog work → `milstolpar` only.
5. `hp[]` is temporary next-round kassa, and only when the story warrants a wallet change. Success in `utfall` does not imply an `hp` row.
6. `nyheter`: 3–6 studio headlines. No HP, dice, `order_ref`, Brottssyndikatet, or Främmande makt named as such. Seven-team news must not name SÄPO or USA as table teams.
7. Keep `runda` matching the file. Import warns on mismatch but the game round wins.

Schema aliases and strict `utfall` fields: [llm-workflow](../llm-workflow/SKILL.md).

After editing JSON:

```bash
python tests/scenario_runner.py
python tests/scenario_runner.py seven
python -m unittest tests.test_scenario_playthrough
```

The runner writes `transcript.md` next to that variant's `rundaN.json`. Keep the transcript in the same change as the JSON.

## Mechanical checks (tests already cover)

- Four rounds finish; each has ≥1 `utfall` and 3–6 news.
- Replay with the same seed is deterministic.
- Each `utfall.slump` matches the frozen roll; resultat matches slump vs sannolikhet.
- Auto-fyll spends the current wallet (no over-budget).
- Queued HP lands on the next-round wallet; round 4 HP applies on `end_game`.
- Projector payload has no inbox, rolls, `utfall`, `llm_forslag`.
- News text does not contain the leak markers in `NEWS_LEAK_MARKERS`.
- Seven-team year: seven names in `lag`, no SÄPO/USA in news, round 3 STT-3 retargeted onto Regeringen.

Fix mechanical failures in JSON or runner **before** polishing flavour.

## Design critique (when asked to review)

Read `transcript.md` as a live-exercise designer, not as a coverage report.

Check:

- Opposing orders that should collide share one world in `utfall`, news, HP, and milestones.
- Backlog BYGGA work progresses when it was not actually blocked; FÖRSTÖRA does not grant milestone progress.
- Wallet deltas are consequences, not a scoreboard for every success.
- News create paranoia without revealing hidden actors or math.
- Tension should rise across four rounds; round 4 should feel like election week, not a reset.
- Unused rolls on honest backlog work are correct, not a bug.

When reporting, separate **rules/engine bugs** from **story/balance notes**. Do not silently retune HP tables in `models.py` to make a scripted year more exciting.

## Do not

- Point the runner at live files under `speldata/`.
- Put filled live exports into `Docs/prompt.md`.
- Treat example files `testdata/llm-svar-*.json` as this playthrough.
- Add a second playthrough harness. Extend `scenario_runner.py`.
