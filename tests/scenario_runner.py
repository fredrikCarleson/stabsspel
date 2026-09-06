"""In-memory four-round playthrough using testdata orders and frozen LLM JSON.

Does not write under speldata/. Default (nine teams): testdata/scenario_llm/.
Seven teams (no SÄPO/USA): testdata/scenario_llm_7lag/. Same seed; do not
rewrite the nine-team year to match seven.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gm_console import (  # noqa: E402
    apply_llm_hp,
    apply_llm_milestones,
    apply_new_round,
    apply_next_phase,
    apply_test_orders,
    build_backlog_board,
    build_llm_export_text,
    build_public_state,
    end_game,
    ensure_round_rolls,
    get_llm_forslag,
    get_round_rolls,
    get_round_utfall,
    import_llm_forslag,
    iter_submitted_orders,
    pending_hp_totals,
    spent_hp_for_team,
    validate_order_hp,
)
from models import (  # noqa: E402
    clone_backlog_for_teams,
    extra_teams_in,
    get_team_base_hp,
    init_fashistorik_v2,
    resolve_active_teams,
)

SCENARIO_SEED = 20260901
LLM_DIR = ROOT / "testdata" / "scenario_llm"
VARIANTS = {
    "nine": {
        "llm_dir": ROOT / "testdata" / "scenario_llm",
        "label": "Nine teams",
        "spellage": "extended",
        "extra_lag": ["Media", "SÄPO", "Regeringen", "USA"],
        "antal_spelare": 27,
    },
    "seven": {
        "llm_dir": ROOT / "testdata" / "scenario_llm_7lag",
        "label": "Seven teams (no SÄPO, no USA)",
        "spellage": "extended",
        "extra_lag": ["Media", "Regeringen"],
        "antal_spelare": 32,
    },
}
SECRET_PUBLIC_KEYS = (
    "inbox",
    "gm_log",
    "test_mode",
    "llm_forslag",
    "llm_resolution",
    "utfall",
    "rolls",
    "team_orders",
    "hp_pending",
)
NEWS_LEAK_MARKERS = (
    "handlingspoäng",
    " hp",
    "sannolikhet",
    "slumpvärde",
    "order_ref",
    "brottssyndikatet",
    "främmande makt",
)


def variant_config(name="nine"):
    key = str(name or "nine").strip().lower()
    if key not in VARIANTS:
        raise ValueError(f"Okänd scenario-variant: {name}")
    return VARIANTS[key]


def llm_path(runda, llm_dir=None):
    directory = Path(llm_dir) if llm_dir else LLM_DIR
    return directory / f"runda{int(runda)}.json"


def load_llm_json(runda, llm_dir=None):
    path = llm_path(runda, llm_dir)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def create_scenario_state(variant="nine"):
    cfg = variant_config(variant)
    lag = resolve_active_teams(
        cfg["antal_spelare"],
        extra_lag=cfg["extra_lag"],
        spellage=cfg["spellage"],
    )
    data = {
        "id": "scenario-playthrough",
        "datum": "2026-09-01",
        "plats": "scenario",
        "antal_spelare": cfg["antal_spelare"],
        "fas": "Orderfas",
        "runda": 1,
        "lag": lag,
        "extra_lag": extra_teams_in(lag),
        "order": {},
        "poang": {},
        "resultat": [],
        "backlog": clone_backlog_for_teams(lag),
        "orderfas_min": 10,
        "diplomatifas_min": 10,
        "resultatfas_min": 10,
        "timer_status": "stopped",
        "timer_start": None,
        "timer_elapsed": 0,
        "timer_bonus": 0,
        "gm_log": [],
        "gm_undo": [],
        "test_mode": True,
        "fashistorik": init_fashistorik_v2(),
        "team_orders": {},
        "avslutat": False,
    }
    for team in lag:
        bas = get_team_base_hp(team, data)
        data["poang"][team] = {"bas": bas, "aktuell": bas, "regeringsstod": False}
    return data


def make_randint(rng):
    return lambda: rng.randint(1, 100)


def wallet_map(data):
    return {
        team: int((data.get("poang") or {}).get(team, {}).get("aktuell") or 0)
        for team in data.get("lag") or []
    }


def backlog_snapshot(data):
    rows = []
    for group in build_backlog_board(data):
        team = group.get("team")
        for item in group.get("items") or []:
            rows.append({
                "team": team,
                "id": item.get("id"),
                "name": item.get("name"),
                "spent": int(item.get("spent") or 0),
                "estimated": int(item.get("estimated") or 0),
                "done": bool(item.get("done")),
            })
            for phase in item.get("phases") or []:
                rows.append({
                    "team": team,
                    "id": f"{item.get('id')}_{phase.get('name')}",
                    "name": f"{item.get('name')} - {phase.get('name')}",
                    "spent": int(phase.get("spent") or 0),
                    "estimated": int(phase.get("estimated") or 0),
                    "done": bool(phase.get("done")),
                })
    return rows


def submitted_order_brief(data):
    rows = []
    for team, _index, ref, activity in iter_submitted_orders(data):
        rows.append({
            "lag": team,
            "order_ref": ref,
            "aktivitet": activity.get("aktivitet"),
            "syfte": activity.get("syfte"),
            "typ": activity.get("typ"),
            "hp": int(activity.get("hp") or 0),
            "backlog_selected": activity.get("backlog_selected"),
            "paverkar": list(activity.get("paverkar") or []),
        })
    return rows


def order_budget_findings(data):
    findings = []
    for team in data.get("lag") or []:
        record = ((data.get("team_orders") or {}).get(f"orders_round_{data.get('runda')}") or {}).get(team)
        if not record:
            findings.append({
                "kind": "missing_orders",
                "team": team,
                "detail": f"{team} saknar testdata-order i runda {data.get('runda')}.",
            })
            continue
        check = validate_order_hp(data, team, record.get("orders") or {})
        if not check.get("valid"):
            findings.append({
                "kind": "over_budget",
                "team": team,
                "detail": check.get("error"),
                "used_hp": check.get("used_hp", spent_hp_for_team(data, team)),
                "max_hp": check.get("max_hp", wallet_map(data).get(team)),
            })
    return findings


def public_secrecy_findings(data):
    public = build_public_state(data)
    findings = []
    for key in SECRET_PUBLIC_KEYS:
        if key in public:
            findings.append({
                "kind": "public_leak",
                "detail": f"build_public_state innehåller {key}.",
            })
    blob = json.dumps(public, ensure_ascii=False).lower()
    for marker in ("utfall", "sannolikhet", "order_ref", "llm_forslag"):
        if marker in blob:
            findings.append({
                "kind": "public_leak",
                "detail": f"Publikt payload nämner {marker}.",
            })
    return findings, public


def news_leak_findings(nyheter):
    findings = []
    for item in nyheter or []:
        text = f"{item.get('rubrik') or ''} {item.get('upplasning') or ''}".lower()
        for marker in NEWS_LEAK_MARKERS:
            if marker in text:
                findings.append({
                    "kind": "news_leak",
                    "detail": f"Nyheten {item.get('rubrik')!r} innehåller {marker.strip()!r}.",
                })
    return findings


def round_export_brief(data):
    return {
        "runda": int(data.get("runda") or 1),
        "fas": data.get("fas"),
        "wallets": wallet_map(data),
        "rolls": get_round_rolls(data),
        "orders": submitted_order_brief(data),
        "backlog": backlog_snapshot(data),
        "previous_utfall": [
            get_round_utfall(data, runda)
            for runda in range(1, int(data.get("runda") or 1))
        ],
    }


def _apply_suggestions(data, findings):
    forslag = get_llm_forslag(data)
    applied = {"hp": 0, "milestones": 0}
    if forslag and forslag.get("hp"):
        applied["hp"] = apply_llm_hp(data)
    if forslag and forslag.get("milstolpar"):
        applied["milestones"] = apply_llm_milestones(data)
    if forslag:
        for warning in forslag.get("warnings") or []:
            findings.append({"kind": "llm_warning", "detail": warning})
    return applied


def play_one_round(data, rng, llm_raw=None, stop_before_import=False):
    runda = int(data.get("runda") or 1)
    findings = []
    if data.get("fas") != "Orderfas":
        raise ValueError(f"Runda {runda} måste starta i Orderfas, var {data.get('fas')}")

    apply_test_orders(data, now=1_000_000 + runda)
    findings.extend(order_budget_findings(data))
    apply_next_phase(data)
    rolls_fn = make_randint(rng)
    ensure_round_rolls(data, randint=rolls_fn)
    export_text = build_llm_export_text(data, None, randint=rolls_fn)
    brief = round_export_brief(data)

    if stop_before_import or not llm_raw:
        return {
            "runda": runda,
            "stopped": True,
            "brief": brief,
            "export_text": export_text,
            "findings": findings,
        }

    parsed = import_llm_forslag(data, llm_raw)
    findings.extend(news_leak_findings(parsed.get("nyheter")))
    apply_next_phase(data)
    applied = _apply_suggestions(data, findings)
    secrecy, public = public_secrecy_findings(data)
    findings.extend(secrecy)

    report = {
        "runda": runda,
        "stopped": False,
        "wallets_this_round": wallet_map(data),
        "pending_hp": pending_hp_totals(data),
        "rolls": get_round_rolls(data, runda),
        "orders": brief["orders"],
        "utfall": get_round_utfall(data, runda),
        "nyheter": list((get_llm_forslag(data, runda) or {}).get("nyheter") or []),
        "hp": list((get_llm_forslag(data, runda) or {}).get("hp") or []),
        "milstolpar": list((get_llm_forslag(data, runda) or {}).get("milstolpar") or []),
        "backlog": backlog_snapshot(data),
        "applied": applied,
        "public_teams": public.get("teams"),
        "findings": findings,
        "warnings": list(parsed.get("warnings") or []),
    }

    if runda >= 4:
        end_game(data)
        report["wallets_next_round"] = wallet_map(data)
    else:
        apply_new_round(data)
        report["wallets_next_round"] = wallet_map(data)
    return report


def play_scenario(seed=SCENARIO_SEED, stop_after_missing_llm=True, variant="nine"):
    cfg = variant_config(variant)
    rng = random.Random(seed)
    data = create_scenario_state(variant)
    llm_dir = cfg["llm_dir"]
    rounds = []
    missing = None
    for runda in range(1, 5):
        raw = load_llm_json(runda, llm_dir)
        if raw is None and stop_after_missing_llm:
            dump = play_one_round(data, rng, stop_before_import=True)
            rounds.append(dump)
            missing = runda
            break
        if raw is None:
            raise FileNotFoundError(f"Saknar {llm_path(runda, llm_dir)}")
        rounds.append(play_one_round(data, rng, llm_raw=raw))
    return {
        "seed": seed,
        "variant": variant,
        "label": cfg["label"],
        "llm_dir": str(llm_dir.relative_to(ROOT)).replace("\\", "/"),
        "teams": list(data.get("lag") or []),
        "finished": bool(data.get("avslutat")),
        "final_wallets": wallet_map(data),
        "final_backlog": backlog_snapshot(data),
        "missing_llm_round": missing,
        "rounds": rounds,
        "findings": [item for report in rounds for item in report.get("findings") or []],
    }


def format_transcript(result):
    """Human-readable playthrough: wallets, orders, utfall, news, HP, backlog."""
    lines = [
        "# Stabsspel scenario transcript",
        "",
        f"Seed `{result.get('seed')}`. {result.get('label') or 'Nine teams'}. Testdata orders, frozen D100, "
        f"resolutions in `{result.get('llm_dir') or 'testdata/scenario_llm'}/rundaN.json`.",
        "",
        "This is one scripted year, not live diplomacy.",
        "",
    ]
    for report in result.get("rounds") or []:
        if report.get("stopped"):
            continue
        runda = report["runda"]
        lines.append(f"## Runda {runda}")
        lines.append("")
        wallets = report.get("wallets_this_round") or {}
        lines.append("Wallets this round: " + ", ".join(
            f"{team} {wallets[team]}" for team in wallets
        ) + ".")
        pending = report.get("pending_hp") or {}
        if pending:
            parts = [f"{team} {delta:+d}" for team, delta in pending.items()]
            lines.append("Queued HP: " + ", ".join(parts) + ".")
        nxt = report.get("wallets_next_round")
        if nxt:
            lines.append("Wallets after apply: " + ", ".join(
                f"{team} {nxt[team]}" for team in nxt
            ) + ".")
        lines.append("")
        lines.append("### Orders")
        lines.append("")
        for order in report.get("orders") or []:
            ref = order.get("order_ref")
            roll = (report.get("rolls") or {}).get(ref, "—")
            lines.append(
                f"- `{ref}` {order.get('lag')} [{order.get('typ')}] "
                f"{order.get('aktivitet')} ({order.get('hp')} HP, roll {roll})"
            )
        lines.append("")
        lines.append("### Utfall")
        lines.append("")
        for item in report.get("utfall") or []:
            delmal = f" — {item['delmal']}" if item.get("delmal") else ""
            lines.append(
                f"- `{item.get('order_ref')}` {item.get('resultat')} "
                f"({item.get('sannolikhet')}% vs {item.get('slump')}, "
                f"{item.get('satsad_hp')} vs {item.get('motstand_hp')} HP)"
                f"{delmal}: {item.get('motivering')}"
            )
        lines.append("")
        lines.append("### News")
        lines.append("")
        for item in report.get("nyheter") or []:
            lines.append(f"- **{item.get('rubrik')}**")
            if item.get("upplasning"):
                lines.append(f"  {item['upplasning']}")
        lines.append("")
        if report.get("hp"):
            lines.append("### HP deltas")
            lines.append("")
            for item in report["hp"]:
                lines.append(
                    f"- {item.get('lag')} {int(item.get('delta') or 0):+d}: "
                    f"{item.get('orsak')}"
                )
            lines.append("")
        if report.get("milstolpar"):
            lines.append("### Milestones")
            lines.append("")
            for item in report["milstolpar"]:
                lines.append(
                    f"- {item.get('lag')} `{item.get('uppgift')}` "
                    f"+{item.get('delta_hp')}: {item.get('orsak')}"
                )
            lines.append("")
    lines.append("## Final wallets")
    lines.append("")
    final = result.get("final_wallets") or {}
    for team, hp in final.items():
        lines.append(f"- {team}: {hp}")
    lines.append("")
    findings = result.get("findings") or []
    if findings:
        lines.append("## Findings")
        lines.append("")
        for item in findings:
            lines.append(f"- {item.get('kind')}: {item.get('detail')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_transcript(result, path=None):
    cfg = variant_config(result.get("variant") or "nine")
    path = Path(path) if path else cfg["llm_dir"] / "transcript.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_transcript(result), encoding="utf-8")
    return path


def dump_round(runda, seed=SCENARIO_SEED, variant="nine"):
    """Play completed rounds, then write the next round's export brief as JSON."""
    cfg = variant_config(variant)
    llm_dir = cfg["llm_dir"]
    result = play_scenario(seed=seed, stop_after_missing_llm=True, variant=variant)
    current = result["rounds"][-1] if result["rounds"] else None
    if not current or not current.get("stopped"):
        raise SystemExit("Inget round-dump: alla LLM-filer finns redan.")
    if int(current["runda"]) != int(runda):
        raise SystemExit(
            f"Nästa saknade LLM-fil är runda {current['runda']}, inte {runda}."
        )
    llm_dir.mkdir(parents=True, exist_ok=True)
    path = llm_dir / f"_dump_r{int(runda)}.json"
    path.write_text(json.dumps(current["brief"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    args = sys.argv[1:]
    variant = "nine"
    if args and args[-1] in VARIANTS:
        variant = args.pop()
    if args and args[0] == "dump":
        dump_round(int(args[1]) if len(args) > 1 else 1, variant=variant)
    else:
        result = play_scenario(variant=variant)
        transcript = write_transcript(result)
        print(transcript)
        print(json.dumps({
            "finished": result["finished"],
            "variant": result["variant"],
            "teams": result["teams"],
            "findings": result["findings"],
            "final_wallets": result["final_wallets"],
        }, ensure_ascii=False, indent=2))
