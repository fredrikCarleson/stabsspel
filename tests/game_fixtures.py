"""Small, explicit game-state builders for domain tests."""


def create_game_state(**overrides):
    state = {
        "id": "g1",
        "fas": "Orderfas",
        "runda": 1,
        "lag": ["Alfa", "Bravo", "STT"],
        "poang": {
            "Alfa": {"bas": 25, "aktuell": 25, "regeringsstod": False},
            "Bravo": {"bas": 25, "aktuell": 25, "regeringsstod": False},
            "STT": {"bas": 25, "aktuell": 25, "regeringsstod": False},
        },
        "orderfas_min": 10,
        "diplomatifas_min": 10,
        "resultatfas_min": 10,
        "timer_status": "stopped",
        "timer_start": None,
        "timer_elapsed": 0,
        "timer_bonus": 0,
        "fashistorik": [{"runda": 1, "fas": "Orderfas", "status": "pågående"}],
        "team_orders": {},
        "gm_log": [],
        "gm_undo": [],
        "avslutat": False,
    }
    state.update(overrides)
    return state


def order_record(activities, final=False, **extra):
    record = {
        "final": final,
        "submitted_at": extra.pop("submitted_at", 1 if final else 0),
        "updated_at": extra.pop("updated_at", 0),
        "orders": {"activities": activities},
    }
    record.update(extra)
    return record


def activity(name="API", hp=10, typ="bygga", paverkar=None, **extra):
    item = {
        "aktivitet": name,
        "syfte": extra.pop("syfte", "test"),
        "hp": hp,
        "typ": typ,
        "paverkar": paverkar or [],
    }
    item.update(extra)
    return item
