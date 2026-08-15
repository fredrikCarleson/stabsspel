"""
Game Master live-console helpers.

News and plot-twist headlines are created outside this app (copy orders into
an LLM, then paper + news studio). This module supports running the room:
phase/time, orders, HP, undo, and an operational log — not a news CMS.
"""

from __future__ import annotations

import copy
import time
from models import (
    FASER,
    MAX_RUNDA,
    add_fashistorik_entry,
    avsluta_aktuell_fas,
    get_next_fas,
    get_phase_timer,
    get_team_base_hp,
)
from game_management import nollstall_regeringsstod

UNDO_LIMIT = 20
LOG_LIMIT = 50
STATUS_LABELS = {
    "empty": "Tom",
    "draft": "Utkast",
    "submitted": "Inskickad",
    "changed": "Ändrad",
}


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


def push_undo(data, action):
    """Snapshot current state (except the undo stack itself) before a mutation."""
    snapshot = {k: copy.deepcopy(v) for k, v in data.items() if k != "gm_undo"}
    stack = data.setdefault("gm_undo", [])
    stack.append({"action": action, "at": time.time(), "state": snapshot})
    data["gm_undo"] = stack[-UNDO_LIMIT:]
    return data


def apply_undo(data):
    """Restore the latest snapshot. Returns (data, action_label) or (data, None)."""
    stack = data.get("gm_undo") or []
    if not stack:
        return data, None
    entry = stack.pop()
    restored = copy.deepcopy(entry.get("state") or {})
    restored["gm_undo"] = stack
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


def ensure_poang(data):
    if "poang" not in data:
        data["poang"] = {}
    for lag in data.get("lag") or []:
        if lag not in data["poang"]:
            bas = get_team_base_hp(lag, data)
            data["poang"][lag] = {"bas": bas, "aktuell": bas, "regeringsstod": False}
    return data


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
        raise ValueError(f"{from_team} har bara {source} HP")
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
    if auto_submit_fn:
        auto_submit_fn(data, runda)
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
        })
    return strip


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
        "conflict_count": len({row["conflict_key"] for row in conflicts}),
        "missing_teams": missing,
        "log": log,
        "undo_available": bool(undo_stack),
        "undo_label": (undo_stack[-1].get("action") if undo_stack else None),
        "can_go_back": previous is not None,
        "previous_label": f"{previous[0]} (runda {previous[1]})" if previous else None,
        "faser": FASER,
        "test_mode": bool(data.get("test_mode")),
    }
