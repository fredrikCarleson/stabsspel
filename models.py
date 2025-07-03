import os
import json
from datetime import datetime
import time

TEAMS = [
    ("Alfa", 20),
    ("Bravo", 20),
    ("STT", 20),
    ("FM", 20),  # Främmande Makt
    ("BS", 20),  # Brottssyndikat
    ("Media", 40),
    ("SÄPO", 50),
    ("Regeringen", 50),
    ("USA", 50)
]

DATA_DIR = "speldata"
os.makedirs(DATA_DIR, exist_ok=True)

FASER = ["Orderfas", "Diplomatifas", "Resultatfas"]
MAX_RUNDA = 3

def suggest_teams(num_players):
    teams = []
    for team, min_players in TEAMS:
        if num_players >= min_players:
            teams.append(team)
    return teams

def get_next_fas(current_fas, runda):
    if runda < MAX_RUNDA:
        idx = FASER.index(current_fas)
        return FASER[(idx + 1) % len(FASER)]
    else:
        if current_fas == "Orderfas":
            return "Resultatfas"
        elif current_fas == "Resultatfas":
            return "Orderfas"
        else:
            return "Resultatfas"

def get_fas_minutes(data):
    if data["fas"] == "Orderfas":
        return int(data.get("orderfas_min", 10))
    elif data["fas"] == "Diplomatifas":
        return int(data.get("diplomatifas_min", 10))
    else:
        return 0

def save_game_data(spel_id, data):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    with open(filnamn, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def skapa_nytt_spel(datum, plats, antal_spelare, orderfas_min, diplomatifas_min):
    spel_id = datetime.now().strftime("%Y%m%d%H%M%S")
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    data = {
        "id": spel_id,
        "datum": datum,
        "plats": plats,
        "antal_spelare": antal_spelare,
        "skapad": datetime.now().isoformat(),
        "fas": "Orderfas",
        "runda": 1,
        "lag": suggest_teams(antal_spelare),
        "order": {},
        "poang": {},
        "resultat": [],
        "backlog": [],
        "orderfas_min": orderfas_min,
        "diplomatifas_min": diplomatifas_min,
    }
    with open(filnamn, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return spel_id

def init_fashistorik_v2():
    return [{"runda": 1, "fas": "Orderfas", "status": "pågående"}]

def add_fashistorik_entry(data, runda, fas, status):
    if "fashistorik" not in data or not isinstance(data["fashistorik"], list):
        data["fashistorik"] = init_fashistorik_v2()
    data["fashistorik"].append({"runda": runda, "fas": fas, "status": status})
    return data

def avsluta_aktuell_fas(data):
    if "fashistorik" in data and data["fashistorik"]:
        for entry in reversed(data["fashistorik"]):
            if entry["status"] == "pågående":
                entry["status"] = "avklarad"
                break
    return data

def avsluta_spel(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if os.path.exists(filnamn):
        with open(filnamn, encoding="utf-8") as f:
            data = json.load(f)
        data["avslutat"] = True
        save_game_data(spel_id, data) 