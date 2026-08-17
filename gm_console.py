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
    clone_backlog_for_teams,
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
        "undo_available": bool(undo_stack),
        "undo_label": (undo_stack[-1].get("action") if undo_stack else None),
        "can_go_back": previous is not None,
        "previous_label": f"{previous[0]} (runda {previous[1]})" if previous else None,
        "faser": FASER,
        "test_mode": bool(data.get("test_mode")),
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
