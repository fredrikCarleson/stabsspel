"""
Game Master live-console helpers.

News is produced outside the app: copy orders into an LLM, paste JSON
suggestions, print headlines for the studio. This module runs the room
(phase/time, orders, HP, undo, log), generates frozen resolution rolls,
and stores LLM suggestions including GM-only utfall.
"""

from __future__ import annotations

import copy
import json
import re
import secrets
import time
from datetime import datetime
from pathlib import Path
from models import (
    FASER,
    MAX_RUNDA,
    add_fashistorik_entry,
    avsluta_aktuell_fas,
    clone_backlog_for_teams,
    get_next_fas,
    get_phase_timer,
    get_team_base_hp,
)
from game_management import nollstall_regeringsstod

UNDO_LIMIT = 20
LOG_LIMIT = 50
TESTDATA_DIR = Path(__file__).resolve().parent / "testdata"
LLM_PROMPT_PATH = Path(__file__).resolve().parent / "Docs" / "prompt.md"
UNDO_KEEP_KEYS = ("gm_undo", "llm_resolution")
UTFALL_RESULTAT = ("framgång", "delvis framgång", "misslyckande")
STATUS_LABELS = {
    "empty": "Tom",
    "draft": "Utkast",
    "submitted": "Inskickad",
    "changed": "Ändrad",
}
BACKLOG_PHASES = ("Krav", "Design", "Utveckling", "Test")
BACKLOG_OWNERS = {"alfa": "Alfa", "bravo": "Bravo", "stt": "STT"}


def effective_hp(entry):
    """Current spendable HP, including government support bonus."""
    if not isinstance(entry, dict):
        return 0
    hp = int(entry.get("aktuell") or 0)
    if entry.get("regeringsstod"):
        hp += 10
    return max(0, hp)


def spent_hp_for_team(data, team_name):
    """HP assigned on the current round's order activities."""
    orders = _team_order_record(data, team_name)
    if not orders:
        return 0
    activities = (orders.get("orders") or {}).get("activities") or []
    total = 0
    for activity in activities:
        try:
            total += int(activity.get("hp") or 0)
        except (TypeError, ValueError):
            continue
    return total


def _team_order_record(data, team_name):
    runda = data.get("runda", 1)
    orders_key = f"orders_round_{runda}"
    return (data.get("team_orders") or {}).get(orders_key, {}).get(team_name)


def team_order_status(data, team_name):
    """empty | draft | submitted | changed"""
    record = _team_order_record(data, team_name)
    if not record:
        return "empty"
    activities = (record.get("orders") or {}).get("activities") or []
    if not activities and not record.get("final"):
        return "empty"
    if record.get("final"):
        updated = float(record.get("updated_at") or 0)
        submitted = float(record.get("submitted_at") or 0)
        if updated > submitted + 0.5 or record.get("edited_by_gm"):
            return "changed"
        return "submitted"
    return "draft"


def get_previous_phase(current_fas, runda):
    """Return (fas, runda) to go back to, or None if already at the start."""
    try:
        runda = int(runda)
    except (TypeError, ValueError):
        runda = 1
    if current_fas == "Diplomatifas":
        return ("Orderfas", runda)
    if current_fas == "Resultatfas":
        return ("Diplomatifas", runda)
    if current_fas == "Orderfas" and runda > 1:
        return ("Resultatfas", runda - 1)
    return None


def can_submit_orders(data):
    """Orders may be saved during Orderfas and Diplomatifas, not Resultatfas."""
    return data.get("fas") in ("Orderfas", "Diplomatifas")


def validate_order_hp(data, team_name, order_data):
    """Reject negative, malformed, or over-budget HP on an order."""
    try:
        entry = (data.get("poang") or {}).get(team_name)
        team_hp = effective_hp(entry) if entry else 25

        used_hp = 0
        for activity in (order_data or {}).get("activities") or []:
            try:
                hp_value = int(activity.get("hp", 0))
                if hp_value < 0:
                    return {"valid": False, "error": "Negativa HP-värden är inte tillåtna"}
                used_hp += hp_value
            except (ValueError, TypeError):
                return {"valid": False, "error": "Ogiltiga HP-värden i order"}

        if used_hp > team_hp:
            return {
                "valid": False,
                "error": f"Du har använt {used_hp} HP men har bara {team_hp} HP tillgängliga!",
            }
        return {"valid": True, "used_hp": used_hp, "max_hp": team_hp}
    except Exception as e:
        return {"valid": False, "error": f"Valideringsfel: {str(e)}"}


def auto_submit_unsaved_orders(data, current_round=None):
    """Mark current-round drafts as final when leaving a timed phase."""
    if current_round is None:
        current_round = data.get("runda", 1)
    orders_key = f"orders_round_{current_round}"
    round_orders = (data.get("team_orders") or {}).get(orders_key)
    if not round_orders:
        return data
    now = time.time()
    for team_orders in round_orders.values():
        if team_orders and not team_orders.get("final", False):
            team_orders["final"] = True
            team_orders["auto_submitted"] = True
            team_orders["submitted_at"] = now
    return data


def push_undo(data, action):
    """Snapshot current state before a mutation.

    Dice in ``llm_resolution`` are excluded so ordinary undo cannot reroll.
    """
    snapshot = {
        k: copy.deepcopy(v) for k, v in data.items() if k not in UNDO_KEEP_KEYS
    }
    stack = data.setdefault("gm_undo", [])
    stack.append({"action": action, "at": time.time(), "state": snapshot})
    data["gm_undo"] = stack[-UNDO_LIMIT:]
    return data


def apply_undo(data):
    """Restore the latest snapshot. Returns (data, action_label) or (data, None)."""
    stack = data.get("gm_undo") or []
    if not stack:
        return data, None
    frozen_resolution = copy.deepcopy(data.get("llm_resolution"))
    entry = stack.pop()
    restored = copy.deepcopy(entry.get("state") or {})
    restored["gm_undo"] = stack
    if frozen_resolution is not None:
        restored["llm_resolution"] = frozen_resolution
    else:
        restored.pop("llm_resolution", None)
    return restored, entry.get("action") or "Ångra"


def append_gm_log(data, kind, message, extra=None):
    log = data.setdefault("gm_log", [])
    item = {
        "at": time.time(),
        "kind": kind,
        "message": message,
    }
    if extra:
        item["extra"] = extra
    log.append(item)
    data["gm_log"] = log[-LOG_LIMIT:]
    return data


def testdata_path_for_round(runda):
    try:
        runda = int(runda)
    except (TypeError, ValueError):
        runda = 1
    return TESTDATA_DIR / f"testdataround{runda}.json"


def load_round_testdata(runda):
    """Load editable testdata/testdataroundN.json. Raises ValueError if missing or invalid."""
    path = testdata_path_for_round(runda)
    if not path.is_file():
        raise ValueError(f"Saknar testdata för runda {runda} ({path.name}).")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ValueError(f"Kunde inte läsa {path.name}: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Ogiltig JSON i {path.name}: {e}") from e
    if not isinstance(payload, dict) or not isinstance(payload.get("orders"), dict):
        raise ValueError(f"{path.name} måste innehålla ett objekt \"orders\" med lag.")
    if not payload["orders"]:
        raise ValueError(f"{path.name} har inga lag under \"orders\".")
    return payload


def _normalize_test_activity(raw, activity_id):
    if not isinstance(raw, dict):
        raise ValueError("Varje aktivitet måste vara ett objekt")
    name = str(raw.get("aktivitet") or "").strip()
    if not name:
        raise ValueError("Aktivitet saknar namn")
    try:
        hp = int(raw.get("hp") or 0)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Ogiltiga HP för {name}") from e
    if hp < 0:
        raise ValueError(f"Negativa HP för {name}")
    paverkar = raw.get("paverkar") or []
    if isinstance(paverkar, str):
        paverkar = [paverkar]
    if not isinstance(paverkar, list):
        paverkar = []
    typ = raw.get("typ") or "bygga"
    if typ not in ("bygga", "forstora"):
        typ = "bygga"
    selected = str(raw.get("backlog_selected") or "custom").strip() or "custom"
    return {
        "id": activity_id,
        "aktivitet": name,
        "syfte": str(raw.get("syfte") or "").strip(),
        "malomrade": str(raw.get("malomrade") or "eget").strip() or "eget",
        "paverkar": [str(item).strip() for item in paverkar if str(item).strip()],
        "typ": typ,
        "hp": hp,
        "backlog_selected": selected,
        "backlog_item": str(raw.get("backlog_item") or "").strip(),
    }


def apply_test_orders(data, now=None):
    """Replace this round's submitted orders from testdata/testdataroundN.json."""
    if not data.get("test_mode"):
        raise ValueError("Auto-fyll kräver testläge")
    runda = data.get("runda", 1)
    payload = load_round_testdata(runda)
    orders = payload["orders"]
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    submitted_at = time.time() if now is None else now
    base_id = int(submitted_at * 1000)
    orders_key = f"orders_round_{runda}"
    data.setdefault("team_orders", {})
    data["team_orders"].setdefault(orders_key, {})
    processed = []
    for i, team_name in enumerate(data.get("lag") or []):
        activities = orders.get(team_name)
        if not isinstance(activities, list) or not activities:
            continue
        team_orders = [
            _normalize_test_activity(activity, base_id + (i * 100) + j)
            for j, activity in enumerate(activities)
        ]
        data["team_orders"][orders_key][team_name] = {
            "submitted_at": submitted_at,
            "phase": data.get("fas"),
            "round": runda,
            "orders": {
                "activities": team_orders,
                "timestamp": stamp,
            },
            "final": True,
        }
        processed.append(team_name)
    if not processed:
        raise ValueError(f"Ingen testdata matchade lagen i runda {runda}.")
    append_gm_log(
        data,
        "order",
        f"Auto-fyllde testdata för runda {runda} ({len(processed)} lag).",
    )
    return data, processed


def ensure_poang(data):
    if "poang" not in data:
        data["poang"] = {}
    for lag in data.get("lag") or []:
        if lag not in data["poang"]:
            bas = get_team_base_hp(lag, data)
            data["poang"][lag] = {"bas": bas, "aktuell": bas, "regeringsstod": False}
    return data


def hp_delta_from_fields(op, amount=None, direction=None):
    """Turn a console HP action into a non-zero integer delta."""
    if op == "plus5":
        return 5
    if op == "minus5":
        return -5
    if op != "adjust":
        return None
    if direction in ("minus", "-", "plus", "+"):
        n = parse_positive_amount(amount, default=1)
        return -n if direction in ("minus", "-") else n
    try:
        n = int(amount)
    except (TypeError, ValueError):
        raise ValueError("Beloppet måste vara ett heltal")
    if n == 0:
        raise ValueError("Beloppet får inte vara 0")
    return n


def parse_positive_amount(raw, default=1):
    """Read a GM amount field. Blank uses default; must be at least 1."""
    if raw in (None, ""):
        return int(default)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        raise ValueError("Beloppet måste vara ett heltal")
    if n < 1:
        raise ValueError("Beloppet måste vara minst 1")
    return n


def adjust_hp(data, team, amount, reason=""):
    ensure_poang(data)
    if team not in data["poang"]:
        raise ValueError(f"Okänt lag: {team}")
    amount = int(amount)
    current = int(data["poang"][team].get("aktuell") or 0)
    data["poang"][team]["aktuell"] = max(0, current + amount)
    sign = "+" if amount >= 0 else ""
    note = reason.strip() or "Justering"
    append_gm_log(
        data,
        "hp",
        f"{team}: {sign}{amount} HP ({note}). Nu {data['poang'][team]['aktuell']}.",
        {"team": team, "amount": amount, "reason": note},
    )
    return data


def transfer_hp(data, from_team, to_team, amount, reason=""):
    ensure_poang(data)
    if from_team not in data["poang"] or to_team not in data["poang"]:
        raise ValueError("Okänt lag i överföring")
    amount = int(amount)
    if amount <= 0:
        raise ValueError("Beloppet måste vara större än 0")
    if from_team == to_team:
        raise ValueError("Kan inte föra över till samma lag")
    source = int(data["poang"][from_team].get("aktuell") or 0)
    if amount > source:
        extra = ""
        if data["poang"][from_team].get("regeringsstod"):
            extra = " (regeringsstöd +10 kan inte flyttas)"
        raise ValueError(f"{from_team} har bara {source} överförbar HP{extra}")
    data["poang"][from_team]["aktuell"] = source - amount
    data["poang"][to_team]["aktuell"] = int(data["poang"][to_team].get("aktuell") or 0) + amount
    note = reason.strip() or "Överföring"
    append_gm_log(
        data,
        "hp",
        f"{amount} HP {from_team} → {to_team} ({note}).",
        {"from": from_team, "to": to_team, "amount": amount, "reason": note},
    )
    return data


def set_regeringsstod(data, team, enabled, reason=""):
    ensure_poang(data)
    if team not in data["poang"]:
        raise ValueError(f"Okänt lag: {team}")
    data["poang"][team]["regeringsstod"] = bool(enabled)
    state = "på" if enabled else "av"
    note = reason.strip()
    suffix = f" ({note})" if note else ""
    append_gm_log(data, "hp", f"Regeringsstöd {state} för {team}{suffix}.")
    return data


def reset_timer_fields(data):
    data["timer_status"] = "stopped"
    data["timer_start"] = None
    data["timer_elapsed"] = 0
    data["timer_bonus"] = 0
    if "fas_start_time" in data:
        del data["fas_start_time"]
    return data


def add_timer_seconds(data, seconds):
    """Shift remaining time without restarting the clock."""
    data["timer_bonus"] = int(data.get("timer_bonus") or 0) + int(seconds)
    return data


def apply_next_phase(data, auto_submit_fn=None):
    """Orderfas → Diplomatifas → Resultatfas. Does not start a new round."""
    runda = data.get("runda", 1)
    fas = data.get("fas", "Orderfas")
    if fas == "Resultatfas":
        raise ValueError("Använd ny runda från resultatfasen")
    submit = auto_submit_fn or auto_submit_unsaved_orders
    submit(data, runda)
    data = avsluta_aktuell_fas(data)
    next_fas = get_next_fas(fas, runda)
    data["fas"] = next_fas
    reset_timer_fields(data)
    add_fashistorik_entry(data, runda, next_fas, "pågående")
    append_gm_log(data, "phase", f"Runda {runda}, {next_fas}.")
    return data


def apply_new_round(data):
    runda = data.get("runda", 1)
    if runda >= MAX_RUNDA:
        raise ValueError("Sista rundan är redan igång")
    data = avsluta_aktuell_fas(data)
    data["runda"] = runda + 1
    data["fas"] = "Orderfas"
    reset_timer_fields(data)
    add_fashistorik_entry(data, data["runda"], "Orderfas", "pågående")
    data = nollstall_regeringsstod(data)
    data["checkbox_states"] = {}
    append_gm_log(data, "phase", f"Runda {data['runda']}, Orderfas.")
    return data


def end_game(data):
    data["avslutat"] = True
    reset_timer_fields(data)
    data = avsluta_aktuell_fas(data)
    append_gm_log(data, "phase", "Spelet avslutades.")
    return data


def apply_previous_phase(data):
    target = get_previous_phase(data.get("fas"), data.get("runda", 1))
    if not target:
        raise ValueError("Redan i första fasen")
    prev_fas, prev_runda = target
    data = avsluta_aktuell_fas(data)
    data["fas"] = prev_fas
    data["runda"] = prev_runda
    reset_timer_fields(data)
    add_fashistorik_entry(data, prev_runda, prev_fas, "pågående")
    append_gm_log(data, "phase", f"Tillbaka till runda {prev_runda}, {prev_fas}.")
    return data


def missing_order_teams(data):
    """Teams with no submitted (final) order this round."""
    missing = []
    for lag in data.get("lag") or []:
        if team_order_status(data, lag) in ("empty", "draft"):
            missing.append(lag)
    return missing


def _conflict_key(activity):
    backlog = (activity.get("backlog_item") or "").strip().lower()
    if backlog:
        return f"backlog:{backlog}"
    targets = ",".join(sorted(activity.get("paverkar") or []))
    if targets:
        return f"target:{targets}"
    name = (activity.get("aktivitet") or "").strip().lower()[:48]
    return f"name:{name}" if name else ""


def ensure_backlog(data):
    """Fill missing team backlogs from the template without resetting spend."""
    if "backlog" not in data or not isinstance(data["backlog"], dict):
        data["backlog"] = {}
    template = clone_backlog_for_teams(data.get("lag") or [])
    for team, tasks in template.items():
        if team not in data["backlog"]:
            data["backlog"][team] = tasks
    return data


def split_task_ref(task_id, phase=None):
    """Return (task_id, phase). Accepts 'alfa_1' or 'bravo_1_Krav'."""
    task_id = (task_id or "").strip()
    if not task_id:
        raise ValueError("Saknar backlog-uppgift")
    if phase:
        return task_id, str(phase)
    for name in BACKLOG_PHASES:
        suffix = "_" + name
        if task_id.endswith(suffix):
            return task_id[: -len(suffix)], name
    return task_id, None


def backlog_owner_for_ref(task_id):
    raw, _phase = split_task_ref(task_id)
    prefix = raw.split("_")[0].lower()
    owner = BACKLOG_OWNERS.get(prefix)
    if not owner:
        raise ValueError("Okänd backlog-uppgift")
    return owner


def _find_backlog_task(data, team, task_id, phase=None):
    ensure_backlog(data)
    task_id, phase = split_task_ref(task_id, phase)
    tasks = (data.get("backlog") or {}).get(team)
    if not tasks:
        raise ValueError(f"{team} har ingen backlog")
    for uppgift in tasks:
        if uppgift.get("id") != task_id:
            continue
        if phase:
            for fas in uppgift.get("faser") or []:
                if fas.get("namn") == phase:
                    return uppgift, fas
            raise ValueError(f"Okänd fas {phase} för {task_id}")
        return uppgift, None
    raise ValueError(f"Okänd backlog-uppgift: {team}/{task_id}")


def _mark_backlog_complete(uppgift, fas=None):
    if fas is not None:
        estimated = int(fas.get("estimaterade_hp") or 0)
        fas["slutford"] = int(fas.get("spenderade_hp") or 0) >= estimated
        faser = uppgift.get("faser") or []
        uppgift["slutford"] = bool(faser) and all(item.get("slutford") for item in faser)
        return
    estimated = int(uppgift.get("estimaterade_hp") or 0)
    done = int(uppgift.get("spenderade_hp") or 0) >= estimated
    if uppgift.get("typ") == "aterkommande":
        uppgift["slutford"] = False
    else:
        uppgift["slutford"] = done


def add_backlog_spend(data, team, task_id, amount, phase=None, log_actor=None):
    """Add (or subtract) spent HP on a backlog task. Never goes below 0."""
    if team not in (data.get("lag") or []):
        raise ValueError(f"Okänt lag: {team}")
    amount = int(amount)
    if amount == 0:
        raise ValueError("Beloppet får inte vara 0")
    uppgift, fas = _find_backlog_task(data, team, task_id, phase)
    target = fas if fas is not None else uppgift
    current = int(target.get("spenderade_hp") or 0)
    target["spenderade_hp"] = max(0, current + amount)
    _mark_backlog_complete(uppgift, fas)
    label = uppgift.get("namn") or task_id
    if fas is not None:
        label = f"{label} ({fas.get('namn')})"
    sign = "+" if amount >= 0 else ""
    actor = log_actor or team
    append_gm_log(
        data,
        "backlog",
        f"{actor}: {sign}{amount} HP på {team} / {label}. Nu {target['spenderade_hp']}.",
        {"team": team, "task_id": uppgift.get("id"), "amount": amount},
    )
    return data


def apply_activity_hp_to_backlog(data, team, activity_index):
    """Move one order activity's HP onto its linked backlog task (once)."""
    record = _team_order_record(data, team)
    if not record:
        raise ValueError("Ingen order för laget")
    activities = (record.get("orders") or {}).get("activities") or []
    try:
        activity_index = int(activity_index)
    except (TypeError, ValueError):
        raise ValueError("Okänd aktivitet") from None
    if activity_index < 0 or activity_index >= len(activities):
        raise ValueError("Okänd aktivitet")
    activity = activities[activity_index]
    if activity.get("backlog_applied"):
        raise ValueError("HP redan lagd på backlog")
    selected = (activity.get("backlog_selected") or "").strip()
    if not selected or selected == "custom":
        raise ValueError("Aktiviteten är inte kopplad till en backlog-uppgift")
    try:
        hp = int(activity.get("hp") or 0)
    except (TypeError, ValueError):
        hp = 0
    if hp <= 0:
        raise ValueError("Aktiviteten har 0 HP")
    owner = backlog_owner_for_ref(selected)
    add_backlog_spend(data, owner, selected, hp, log_actor=team)
    activity["backlog_applied"] = True
    return data


def _task_can_apply(activity):
    selected = (activity.get("backlog_selected") or "").strip()
    if not selected or selected == "custom" or activity.get("backlog_applied"):
        return False
    try:
        return int(activity.get("hp") or 0) > 0
    except (TypeError, ValueError):
        return False


def _backlog_estimated_hp(data, activity):
    selected = (activity.get("backlog_selected") or "").strip()
    if not selected or selected == "custom":
        return None
    try:
        owner = backlog_owner_for_ref(selected)
        uppgift, fas = _find_backlog_task(data, owner, selected)
        if fas is not None:
            return int(fas.get("estimaterade_hp") or 0)
        return int(uppgift.get("estimaterade_hp") or 0)
    except (TypeError, ValueError):
        return None


def build_inbox(data):
    """Flat list of current-round activities plus conflict flags."""
    rows = []
    groups = {}
    for lag in data.get("lag") or []:
        record = _team_order_record(data, lag)
        status = team_order_status(data, lag)
        activities = ((record or {}).get("orders") or {}).get("activities") or []
        for index, activity in enumerate(activities):
            key = _conflict_key(activity)
            selected = (activity.get("backlog_selected") or "").strip()
            row = {
                "team": lag,
                "index": index,
                "aktivitet": activity.get("aktivitet") or "",
                "syfte": activity.get("syfte") or "",
                "hp": int(activity.get("hp") or 0),
                "typ": activity.get("typ") or "bygga",
                "malomrade": activity.get("malomrade") or "eget",
                "paverkar": activity.get("paverkar") or [],
                "status": status,
                "final": bool((record or {}).get("final")),
                "conflict_key": key,
                "conflict": False,
                "backlog_selected": selected,
                "backlog_applied": bool(activity.get("backlog_applied")),
                "can_apply_backlog": _task_can_apply(activity),
                "backlog_estimated": _backlog_estimated_hp(data, activity),
            }
            rows.append(row)
            if key:
                groups.setdefault(key, []).append(row)

    for key, group in groups.items():
        teams = {row["team"] for row in group}
        if len(teams) >= 2:
            for row in group:
                row["conflict"] = True
    return rows


def build_backlog_board(data):
    """Per-team backlog rows for the live console."""
    ensure_backlog(data)
    board = []
    for lag in data.get("lag") or []:
        tasks = (data.get("backlog") or {}).get(lag)
        if not tasks:
            continue
        items = []
        spent_total = 0
        est_total = 0
        for uppgift in tasks:
            faser = uppgift.get("faser") or []
            if faser:
                phases = []
                for fas in faser:
                    estimated = int(fas.get("estimaterade_hp") or 0)
                    spent = int(fas.get("spenderade_hp") or 0)
                    est_total += estimated
                    spent_total += spent
                    phases.append({
                        "name": fas.get("namn") or "",
                        "estimated": estimated,
                        "spent": spent,
                        "done": bool(fas.get("slutford")),
                    })
                items.append({
                    "id": uppgift.get("id") or "",
                    "name": uppgift.get("namn") or "",
                    "kind": "phased",
                    "estimated": sum(p["estimated"] for p in phases),
                    "spent": sum(p["spent"] for p in phases),
                    "done": bool(uppgift.get("slutford")),
                    "recurring": False,
                    "phases": phases,
                })
            else:
                estimated = int(uppgift.get("estimaterade_hp") or 0)
                spent = int(uppgift.get("spenderade_hp") or 0)
                est_total += estimated
                spent_total += spent
                items.append({
                    "id": uppgift.get("id") or "",
                    "name": uppgift.get("namn") or "",
                    "kind": "simple",
                    "estimated": estimated,
                    "spent": spent,
                    "done": bool(uppgift.get("slutford")),
                    "recurring": uppgift.get("typ") == "aterkommande",
                    "phases": [],
                })
        board.append({
            "team": lag,
            "spent": spent_total,
            "estimated": est_total,
            "items": items,
        })
    return board


def _progress_percent(spent, estimated):
    if estimated <= 0:
        return 0
    return min(100, int(round(100.0 * spent / estimated)))


def build_public_progress(data):
    """Roadmap snapshot for the room: names and HP bars, no orders or GM controls."""
    progress = []
    for team in build_backlog_board(data):
        items = []
        spent = 0
        estimated = 0
        for item in team.get("items") or []:
            if item.get("recurring"):
                continue
            spent += int(item.get("spent") or 0)
            estimated += int(item.get("estimated") or 0)
            entry = {
                "name": item.get("name") or "",
                "spent": int(item.get("spent") or 0),
                "estimated": int(item.get("estimated") or 0),
                "percent": _progress_percent(item.get("spent") or 0, item.get("estimated") or 0),
                "done": bool(item.get("done")),
            }
            if item.get("kind") == "phased":
                entry["phases"] = [
                    {"name": phase.get("name") or "", "done": bool(phase.get("done"))}
                    for phase in item.get("phases") or []
                ]
            items.append(entry)
        if not items:
            continue
        progress.append({
            "team": team["team"],
            "spent": spent,
            "estimated": estimated,
            "percent": _progress_percent(spent, estimated),
            "items": items,
        })
    return progress


def build_team_strip(data):
    ensure_poang(data)
    strip = []
    for lag in data.get("lag") or []:
        entry = data["poang"].get(lag) or {}
        spent = spent_hp_for_team(data, lag)
        current = effective_hp(entry)
        status = team_order_status(data, lag)
        strip.append({
            "team": lag,
            "bas": int(entry.get("bas") or 0),
            "aktuell": int(entry.get("aktuell") or 0),
            "regeringsstod": bool(entry.get("regeringsstod")),
            "effective": current,
            "spent": spent,
            "remaining": current - spent,
            "status": status,
            "status_label": STATUS_LABELS.get(status, status),
            "transferable": int(entry.get("aktuell") or 0),
            "can_withdraw": (
                data.get("fas") == "Orderfas"
                and not data.get("avslutat")
                and status in ("submitted", "changed")
            ),
        })
    return strip


_TEAM_ALIASES = {
    "alfa": "Alfa", "lag alfa": "Alfa",
    "bravo": "Bravo", "lag bravo": "Bravo",
    "charlie": "Charlie", "lag charlie": "Charlie",
    "delta": "Delta", "lag delta": "Delta",
    "echo": "Echo", "lag echo": "Echo",
    "stt": "STT", "lag stt": "STT",
    "fm": "FM", "främmande makt": "FM", "lag fm": "FM",
    "bs": "BS", "brottssyndikatet": "BS", "lag bs": "BS",
    "media": "Media", "lag media": "Media",
    "säpo": "SÄPO", "sapo": "SÄPO", "lag säpo": "SÄPO",
    "regeringen": "Regeringen", "lag regeringen": "Regeringen",
    "usa": "USA", "lag usa": "USA",
}


def normalize_team_name(value, teams=None):
    raw = str(value or "").strip()
    if not raw:
        return None
    known = list(teams) if teams is not None else list(_TEAM_ALIASES.values())
    if raw in known:
        return raw
    mapped = _TEAM_ALIASES.get(raw.lower())
    if mapped and mapped in known:
        return mapped
    for team in known:
        if team.lower() == raw.lower():
            return team
    return None


def make_order_ref(team, index):
    """Stable human-readable ref, e.g. Alfa-1 or STT-3."""
    return f"{team}-{int(index)}"


def _round_orders_map(data, all_orders=None):
    if all_orders is not None:
        return all_orders
    runda = data.get("runda") or 1
    return (data.get("team_orders") or {}).get(f"orders_round_{runda}") or {}


def iter_submitted_orders(data, all_orders=None):
    """Yield (team, index, order_ref, activity) for submitted current-round orders."""
    orders = _round_orders_map(data, all_orders)
    teams = list(data.get("lag") or []) or list(orders)
    for team in teams:
        record = orders.get(team) or {}
        if not record.get("final"):
            continue
        activities = (record.get("orders") or {}).get("activities") or []
        for index, activity in enumerate(activities, 1):
            yield team, index, make_order_ref(team, index), activity


def current_order_refs(data, all_orders=None):
    return [ref for _team, _index, ref, _activity in iter_submitted_orders(data, all_orders)]


def _resolution_key(runda=None, data=None):
    if runda is None and data is not None:
        runda = data.get("runda") or 1
    return str(int(runda or 1))


def get_round_resolution(data, runda=None):
    store = data.get("llm_resolution") or {}
    rec = store.get(_resolution_key(runda, data))
    return rec if isinstance(rec, dict) else {}


def get_round_rolls(data, runda=None):
    return dict((get_round_resolution(data, runda) or {}).get("rolls") or {})


def get_round_utfall(data, runda=None):
    result = (get_round_resolution(data, runda) or {}).get("result") or {}
    if isinstance(result, dict):
        return list(result.get("utfall") or [])
    return []


def _ensure_resolution_record(data, runda=None):
    key = _resolution_key(runda, data)
    store = data.setdefault("llm_resolution", {})
    rec = store.get(key)
    if not isinstance(rec, dict):
        rec = {"rolls": {}, "result": None}
    rec.setdefault("rolls", {})
    store[key] = rec
    data["llm_resolution"] = store
    return rec


def _new_roll(randint=None):
    if randint is not None:
        value = int(randint())
    else:
        value = secrets.randbelow(100) + 1
    if not 1 <= value <= 100:
        raise ValueError("Slumpvärde måste vara 1–100")
    return value


def ensure_round_rolls(data, all_orders=None, randint=None):
    """Create missing 1–100 rolls for submitted orders. Never reroll existing refs."""
    rec = _ensure_resolution_record(data)
    rolls = rec.setdefault("rolls", {})
    for _team, _index, ref, _activity in iter_submitted_orders(data, all_orders):
        if ref not in rolls:
            rolls[ref] = _new_roll(randint)
    rec["rolls"] = rolls
    return dict(rolls)


def format_orders_export(data, all_orders):
    """Plain-text order dump used by the LLM export page."""
    lines = []
    poang = data.get("poang") or {}
    current_team = None
    for team, index, ref, activity in iter_submitted_orders(data, all_orders):
        if team != current_team:
            if current_team is not None:
                lines.append("")
            current_team = team
            hp = int((poang.get(team) or {}).get("aktuell") or 0)
            lines.append(f"=== LAG {team.upper()} (HP i kassan: {hp}) ===")
        order_type = activity.get("typ", "bygga")
        typ_label = "BYGGA" if order_type == "bygga" else "FÖRSTÖRA"
        aktivitet = activity.get("aktivitet") or ""
        hp_est = int(activity.get("hp") or 0)
        syfte = (activity.get("syfte") or "").strip()
        malomrade = activity.get("malomrade") or ""
        paverkar = activity.get("paverkar") or []
        backlog_id = activity.get("backlog_selected") or ""
        backlog_item = activity.get("backlog_item") or ""
        lines.append(f"{index}. [{typ_label}] {aktivitet} ({hp_est} HP)")
        lines.append(f"   order_ref: {ref}")
        if syfte:
            lines.append(f"   Syfte: {syfte}")
        if backlog_id and backlog_id != "custom":
            extra = f" ({backlog_item})" if backlog_item else ""
            lines.append(f"   Backlog-id: {backlog_id}{extra}")
        if paverkar:
            lines.append(f"   Påverkar: {', '.join(str(p) for p in paverkar)}")
        if malomrade:
            lines.append(f"   Målområde: {malomrade}")
    return "\n".join(lines) if lines else "(Inga inskickade ordrar ännu)"


def _format_backlog_for_llm(data):
    lines = []
    poang = data.get("poang") or {}
    for group in build_backlog_board(data):
        team = group.get("team")
        hp = int((poang.get(team) or {}).get("aktuell") or 0)
        lines.append(f"=== {team} (HP i kassan: {hp}) ===")
        items = group.get("items") or []
        if not items:
            lines.append("  (tom backlog)")
            lines.append("")
            continue
        for item in items:
            spent = int(item.get("spent") or 0)
            estimated = int(item.get("estimated") or 0)
            status = "klar" if item.get("done") else "pågår"
            lines.append(
                f"  - id={item.get('id')} | {item.get('name')} | "
                f"lagd HP {spent}/{estimated} | status={status}"
            )
            for phase in item.get("phases") or []:
                p_status = "klar" if phase.get("done") else "pågår"
                pname = phase.get("name") or ""
                lines.append(
                    f"      id={item.get('id')}_{pname} | fas={pname} | "
                    f"lagd HP {int(phase.get('spent') or 0)}/"
                    f"{int(phase.get('estimated') or 0)} | status={p_status}"
                )
        lines.append("")
    return "\n".join(lines).strip() or "(ingen backlog)"


def _load_llm_prompt_template():
    try:
        return LLM_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Saknar LLM-prompt ({LLM_PROMPT_PATH.name}).") from exc


def _format_rolls_for_llm(rolls):
    if not rolls:
        return "(Inga slumpvärden. Inga inskickade order.)"
    lines = [f"{ref}: {int(value)}" for ref, value in rolls.items()]
    return "\n".join(lines)


def format_previous_outcomes(data):
    """Compact persisted utfall from earlier rounds. No invented summary."""
    current = int(data.get("runda") or 1)
    store = data.get("llm_resolution") or {}
    lines = []
    for runda in range(1, current):
        rec = store.get(str(runda)) or {}
        result = rec.get("result") or {}
        utfall = result.get("utfall") if isinstance(result, dict) else None
        if not utfall:
            continue
        lines.append(f"Runda {runda}:")
        for item in utfall:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"  - {item.get('order_ref')}: {item.get('lag')} | "
                f"{item.get('order')} | {item.get('resultat')} | "
                f"{item.get('satsad_hp')} HP mot {item.get('motstand_hp')} HP | "
                f"sannolikhet {item.get('sannolikhet')} slump {item.get('slump')} | "
                f"{item.get('motivering')}"
            )
    return "\n".join(lines) if lines else "(Inga tidigare utfall)"


def build_llm_export_text(data, all_orders, randint=None):
    """Fill Docs/prompt.md with live round data. Creates missing rolls."""
    runda = int(data.get("runda") or 1)
    fas = data.get("fas") or ""
    teams = ", ".join(data.get("lag") or []) or "Alfa, Bravo, Charlie, Delta, Echo, STT"
    rolls = ensure_round_rolls(data, all_orders, randint=randint)
    ordered_refs = current_order_refs(data, all_orders)
    ordered_rolls = {ref: rolls[ref] for ref in ordered_refs if ref in rolls}
    template = _load_llm_prompt_template()
    return (
        template
        .replace("{LAGLISTA}", teams)
        .replace("{RUNDA}", str(runda))
        .replace("{FAS}", str(fas))
        .replace("{BACKLOG}", _format_backlog_for_llm(data))
        .replace("{ORDRAR}", format_orders_export(data, all_orders))
        .replace("{SLUMPVARDEN}", _format_rolls_for_llm(ordered_rolls))
        .replace("{TIDIGARE_UTFALL}", format_previous_outcomes(data))
    )


def _strip_llm_fences(raw):
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_llm_forslag(raw, data):
    """Parse pasted LLM JSON into a stored suggestion object. Raises ValueError."""
    text = _strip_llm_fences(raw)
    if not text:
        raise ValueError("Klistra in JSON från LLM.")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ogiltig JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON måste vara ett objekt.")

    ensure_backlog(data)
    teams = list(data.get("lag") or [])
    runda = int(data.get("runda") or 1)
    warnings = []
    payload_runda = payload.get("runda")
    if payload_runda is not None:
        try:
            if int(payload_runda) != runda:
                warnings.append(
                    f"LLM angav runda {payload_runda}, spelet är på runda {runda}."
                )
        except (TypeError, ValueError):
            pass

    nyheter = []
    for item in payload.get("nyheter") or payload.get("news") or []:
        if not isinstance(item, dict):
            continue
        rubrik = str(item.get("rubrik") or item.get("headline") or "").strip()
        uppl = str(item.get("upplasning") or item.get("text") or item.get("lasning") or "").strip()
        if not rubrik and not uppl:
            continue
        lag = []
        for name in item.get("lag") or item.get("teams") or []:
            team = normalize_team_name(name, teams)
            if team:
                lag.append(team)
        nyheter.append({"rubrik": rubrik, "upplasning": uppl, "lag": lag})

    hp = []
    for item in payload.get("hp") or payload.get("hp_justeringar") or []:
        if not isinstance(item, dict):
            continue
        team = normalize_team_name(item.get("lag") or item.get("team"), teams)
        try:
            delta = int(item.get("delta") or 0)
        except (TypeError, ValueError):
            continue
        if not team or delta == 0:
            continue
        hp.append({
            "lag": team,
            "delta": delta,
            "orsak": str(item.get("orsak") or item.get("reason") or "").strip(),
        })

    milstolpar = []
    for item in payload.get("milstolpar") or payload.get("milestones") or payload.get("backlog") or []:
        if not isinstance(item, dict):
            continue
        team = normalize_team_name(item.get("lag") or item.get("team"), teams)
        uppgift = str(item.get("uppgift") or item.get("id") or item.get("task") or "").strip()
        try:
            delta_hp = int(item.get("delta_hp") or item.get("hp") or 0)
        except (TypeError, ValueError):
            continue
        if delta_hp <= 0 or not uppgift:
            continue
        try:
            resolved_team, task_id, fas = _resolve_milestone_ref(data, team, uppgift, item.get("fas"))
        except ValueError as exc:
            warnings.append(str(exc))
            continue
        milstolpar.append({
            "lag": resolved_team,
            "uppgift": task_id,
            "fas": fas,
            "delta_hp": delta_hp,
            "orsak": str(item.get("orsak") or item.get("reason") or "").strip(),
        })

    has_utfall_key = "utfall" in payload
    utfall = parse_utfall_items(payload.get("utfall"), data)

    return {
        "runda": runda,
        "importerad": datetime.now().isoformat(timespec="seconds"),
        "nyheter": nyheter,
        "hp": hp,
        "milstolpar": milstolpar,
        "utfall": utfall,
        "has_utfall_key": has_utfall_key,
        "hp_applied": False,
        "milestones_applied": False,
        "warnings": warnings,
    }


def _require_int(value, field, lo=None, hi=None):
    if isinstance(value, bool) or value is None or value == "":
        raise ValueError(f"{field} måste vara ett heltal.")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} måste vara ett heltal.") from exc
    if lo is not None and number < lo:
        raise ValueError(f"{field} måste vara minst {lo}.")
    if hi is not None and number > hi:
        raise ValueError(f"{field} får vara högst {hi}.")
    return number


def parse_utfall_items(raw_items, data):
    """Validate LLM utfall. Missing/empty is OK. Any invalid object rejects the import."""
    if raw_items is None:
        return []
    if not isinstance(raw_items, list):
        raise ValueError("utfall måste vara en lista.")
    if not raw_items:
        return []
    known_refs = set(current_order_refs(data))
    rolls = get_round_rolls(data)
    teams = list(data.get("lag") or [])
    parsed = []
    required = (
        "lag", "order_ref", "order", "satsad_hp", "motstand_hp",
        "sannolikhet", "slump", "resultat", "motivering",
    )
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("Varje utfall måste vara ett objekt.")
        missing = [key for key in required if item.get(key) in (None, "")]
        if missing:
            raise ValueError(f"Utfall saknar fält: {', '.join(missing)}.")
        team = normalize_team_name(item.get("lag"), teams)
        if not team:
            raise ValueError(f"Okänt lag i utfall: {item.get('lag')}.")
        order_ref = str(item.get("order_ref") or "").strip()
        if order_ref not in known_refs:
            raise ValueError(
                f"Okänd order_ref {order_ref}. Finns inte bland rundans inskickade order."
            )
        sannolikhet = _require_int(item.get("sannolikhet"), f"sannolikhet för {order_ref}", 10, 90)
        slump = _require_int(item.get("slump"), f"slump för {order_ref}", 1, 100)
        expected = rolls.get(order_ref)
        if expected is None:
            raise ValueError(
                f"Ingen slump är sparad för {order_ref}. "
                "Kopiera ordrar till LLM först så att slumpen är låst."
            )
        if slump != int(expected):
            raise ValueError(
                f"Slumpvärdet för {order_ref} är {slump} i LLM-svaret, men spelet har {expected}. "
                "Appen slår tärningen, inte LLM."
            )
        resultat = str(item.get("resultat") or "").strip()
        if resultat not in UTFALL_RESULTAT:
            raise ValueError(
                f"Ogiltigt resultat för {order_ref}: {resultat}. "
                "Använd framgång, delvis framgång eller misslyckande."
            )
        parsed.append({
            "lag": team,
            "order_ref": order_ref,
            "order": str(item.get("order") or "").strip(),
            "satsad_hp": _require_int(item.get("satsad_hp"), f"satsad_hp för {order_ref}", 0),
            "motstand_hp": _require_int(item.get("motstand_hp"), f"motstand_hp för {order_ref}", 0),
            "sannolikhet": sannolikhet,
            "slump": slump,
            "resultat": resultat,
            "motivering": str(item.get("motivering") or "").strip(),
        })
    return parsed


def _resolve_milestone_ref(data, team, uppgift, fas=None):
    raw = str(uppgift or "").strip()
    phase = str(fas).strip() if fas else None
    if team:
        try:
            task_id, phase_name = split_task_ref(raw, phase)
            _find_backlog_task(data, team, task_id, phase_name)
            return team, task_id, phase_name
        except ValueError:
            pass

    needle = raw.lower()
    search_teams = [team] if team else list(data.get("lag") or [])
    matches = []
    for t in search_teams:
        for item in (data.get("backlog") or {}).get(t) or []:
            name = str(item.get("namn") or "").strip()
            if name.lower() == needle or item.get("id") == raw:
                matches.append((t, item["id"], None))
            for p in item.get("faser") or []:
                pname = str(p.get("namn") or "")
                composite = f"{name} - {pname}".lower()
                ref = f"{item['id']}_{pname}"
                if needle in {pname.lower(), composite, ref.lower()} or raw == ref:
                    matches.append((t, item["id"], pname))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Flera milstolpar matchade {raw}")
    raise ValueError(f"Hittade ingen milstolpe för {team or '?'}: {raw}")


def import_llm_forslag(data, raw):
    parsed = parse_llm_forslag(raw, data)
    has_utfall_key = parsed.pop("has_utfall_key", False)
    utfall = list(parsed.get("utfall") or [])
    store = dict(data.get("llm_forslag") or {})
    store[str(parsed["runda"])] = parsed
    data["llm_forslag"] = store
    if has_utfall_key or utfall:
        rec = _ensure_resolution_record(data, parsed["runda"])
        rec["result"] = {"utfall": utfall}
    append_gm_log(
        data,
        "llm",
        f"Importerade LLM-förslag för runda {parsed['runda']}: "
        f"{len(parsed['nyheter'])} nyheter, {len(parsed['hp'])} HP, "
        f"{len(parsed['milstolpar'])} milstolpar, {len(utfall)} utfall",
    )
    return parsed


def get_llm_forslag(data, runda=None):
    store = data.get("llm_forslag") or {}
    key = str(runda if runda is not None else data.get("runda") or 1)
    return store.get(key)


def apply_llm_hp(data):
    forslag = get_llm_forslag(data)
    if not forslag:
        raise ValueError("Inga LLM-förslag för den här rundan.")
    if forslag.get("hp_applied"):
        raise ValueError("HP-förslagen är redan tillämpade.")
    items = list(forslag.get("hp") or [])
    if not items:
        raise ValueError("Inga HP-förslag att tillämpa.")
    applied = 0
    for item in items:
        try:
            if applied == 0:
                push_undo(data, "Tillämpa LLM-HP")
            adjust_hp(data, item["lag"], int(item["delta"]), item.get("orsak") or "LLM-förslag")
            applied += 1
        except ValueError:
            continue
    if applied == 0:
        raise ValueError("Kunde inte tillämpa någon HP-justering.")
    forslag["hp_applied"] = True
    store = dict(data.get("llm_forslag") or {})
    store[str(forslag.get("runda") or data.get("runda") or 1)] = forslag
    data["llm_forslag"] = store
    append_gm_log(data, "llm", f"Tillämpade {applied} HP-justeringar från LLM")
    return applied


def apply_llm_milestones(data):
    forslag = get_llm_forslag(data)
    if not forslag:
        raise ValueError("Inga LLM-förslag för den här rundan.")
    if forslag.get("milestones_applied"):
        raise ValueError("Milstolpeförslagen är redan tillämpade.")
    items = list(forslag.get("milstolpar") or [])
    if not items:
        raise ValueError("Inga milstolpeförslag att tillämpa.")
    applied = 0
    for item in items:
        try:
            if applied == 0:
                push_undo(data, "Tillämpa LLM-milstolpar")
            add_backlog_spend(
                data,
                item["lag"],
                item["uppgift"],
                int(item["delta_hp"]),
                item.get("fas"),
                item.get("orsak") or "LLM-förslag",
            )
            applied += 1
        except ValueError:
            continue
    if applied == 0:
        raise ValueError("Kunde inte tillämpa någon milstolpe.")
    forslag["milestones_applied"] = True
    store = dict(data.get("llm_forslag") or {})
    store[str(forslag.get("runda") or data.get("runda") or 1)] = forslag
    data["llm_forslag"] = store
    append_gm_log(data, "llm", f"Tillämpade {applied} milstolpeförslag från LLM")
    return applied


def _milestone_etikett(data, item):
    try:
        uppgift, fas = _find_backlog_task(
            data, item.get("lag"), item.get("uppgift"), item.get("fas")
        )
        name = uppgift.get("namn") or item.get("uppgift")
        if fas:
            return f"{name} ({fas.get('namn')})"
        return name
    except ValueError:
        return item.get("uppgift") or ""


def llm_forslag_view(data, runda=None):
    """Display-ready LLM suggestions for the current round, or None."""
    forslag = get_llm_forslag(data, runda)
    rolls = get_round_rolls(data, runda)
    utfall = get_round_utfall(data, runda)
    if not utfall and forslag:
        utfall = list(forslag.get("utfall") or [])
    if not forslag and not rolls and not utfall:
        return None
    milstolpar = []
    for item in (forslag or {}).get("milstolpar") or []:
        row = dict(item)
        row["etikett"] = _milestone_etikett(data, item)
        milstolpar.append(row)
    return {
        "runda": (forslag or {}).get("runda") or (runda if runda is not None else data.get("runda")),
        "importerad": (forslag or {}).get("importerad"),
        "nyheter": list((forslag or {}).get("nyheter") or []),
        "hp": list((forslag or {}).get("hp") or []),
        "milstolpar": milstolpar,
        "utfall": utfall,
        "rolls": rolls,
        "hp_applied": bool((forslag or {}).get("hp_applied")),
        "milestones_applied": bool((forslag or {}).get("milestones_applied")),
        "warnings": list((forslag or {}).get("warnings") or []),
    }


def build_live_state(data):
    inbox = build_inbox(data)
    conflicts = [row for row in inbox if row["conflict"]]
    missing = missing_order_teams(data)
    log = list(reversed(data.get("gm_log") or []))[:12]
    undo_stack = data.get("gm_undo") or []
    previous = get_previous_phase(data.get("fas"), data.get("runda", 1))
    return {
        "runda": data.get("runda", 1),
        "max_runda": MAX_RUNDA,
        "fas": data.get("fas", "Orderfas"),
        "avslutat": bool(data.get("avslutat")),
        "timer_status": data.get("timer_status", "stopped"),
        "remaining": get_phase_timer(data),
        "teams": build_team_strip(data),
        "inbox": inbox,
        "backlog": build_backlog_board(data),
        "conflict_count": len({row["conflict_key"] for row in conflicts}),
        "missing_teams": missing,
        "log": log,
        "history": list(data.get("fashistorik") or []),
        "undo_available": bool(undo_stack),
        "undo_label": (undo_stack[-1].get("action") if undo_stack else None),
        "can_go_back": previous is not None,
        "previous_label": f"{previous[0]} (runda {previous[1]})" if previous else None,
        "faser": FASER,
        "test_mode": bool(data.get("test_mode")),
        "llm": llm_forslag_view(data),
    }


def build_public_state(data):
    """Room-safe snapshot: time, phase, public HP. No orders, log, or testläge."""
    ensure_poang(data)
    teams = []
    for lag in data.get("lag") or []:
        entry = data["poang"].get(lag) or {}
        teams.append({
            "team": lag,
            "hp": effective_hp(entry),
            "regeringsstod": bool(entry.get("regeringsstod")),
        })
    return {
        "runda": data.get("runda", 1),
        "max_runda": MAX_RUNDA,
        "fas": data.get("fas", "Orderfas"),
        "avslutat": bool(data.get("avslutat")),
        "timer_status": data.get("timer_status", "stopped"),
        "remaining": get_phase_timer(data),
        "teams": teams,
        "progress": build_public_progress(data),
    }


def can_withdraw_orders(data):
    return data.get("fas") == "Orderfas" and not data.get("avslutat")


def withdraw_order(data, team):
    """Turn a submitted order back into a draft. Orderfas only."""
    if not can_withdraw_orders(data):
        raise ValueError("Order kan bara återtas under orderfasen")
    if team not in (data.get("lag") or []):
        raise ValueError(f"Okänt lag: {team}")
    record = _team_order_record(data, team)
    if not record or not record.get("final"):
        raise ValueError("Ingen inskickad order att återta")
    record["final"] = False
    record["withdrawn_at"] = time.time()
    record["updated_at"] = time.time()
    record.pop("edited_by_gm", None)
    append_gm_log(data, "order", f"{team} återöppnade sin order.")
    return data


def update_activity(data, team, index, fields):
    """Patch one activity on the current-round order. GM stays on the console."""
    if data.get("fas") not in ("Orderfas", "Diplomatifas") or data.get("avslutat"):
        raise ValueError("Kan bara ändra order under order- eller diplomatifas")
    if team not in (data.get("lag") or []):
        raise ValueError(f"Okänt lag: {team}")
    record = _team_order_record(data, team)
    if not record:
        raise ValueError("Ingen order för laget")
    activities = (record.get("orders") or {}).get("activities") or []
    try:
        index = int(index)
    except (TypeError, ValueError):
        raise ValueError("Okänd aktivitet") from None
    if index < 0 or index >= len(activities):
        raise ValueError("Okänd aktivitet")
    orders = copy.deepcopy(record.get("orders") or {"activities": []})
    activity = (orders.get("activities") or [])[index]
    if "hp" in fields and fields["hp"] is not None:
        try:
            hp = int(fields["hp"])
        except (TypeError, ValueError):
            raise ValueError("Ogiltigt HP") from None
        if hp < 0:
            raise ValueError("Negativa HP-värden är inte tillåtna")
        activity["hp"] = hp
    if "aktivitet" in fields and fields["aktivitet"] is not None:
        activity["aktivitet"] = str(fields["aktivitet"]).strip()
    if "syfte" in fields and fields["syfte"] is not None:
        activity["syfte"] = str(fields["syfte"]).strip()
    validation = validate_order_hp(data, team, orders)
    if not validation["valid"]:
        raise ValueError(validation["error"])
    record["orders"] = orders
    record["updated_at"] = time.time()
    record["edited_by_gm"] = True
    label = activity.get("aktivitet") or f"aktivitet {index + 1}"
    append_gm_log(
        data,
        "order",
        f"GM ändrade {team}: {label} ({activity.get('hp') or 0} HP).",
        {"team": team, "index": index},
    )
    return data
