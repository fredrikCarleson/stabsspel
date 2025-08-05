import os
import json
from datetime import datetime
import time

TEAMS = [
    ("Alfa", 25),
    ("Bravo", 25),
    ("STT", 25),
    ("FM", 12),  # Främmande Makt
    ("BS", 12),  # Brottssyndikat
    ("Media", 15),
    ("SÄPO", 12),
    ("Regeringen", 10),
    ("USA", 12)
]

# Backlog-uppgifter för varje team
BACKLOG = {
    "Alfa": [
        {"id": "alfa_1", "namn": "Inloggning val", "estimaterade_hp": 15, "spenderade_hp": 0, "slutford": False},
        {"id": "alfa_2", "namn": "Back-end API för inskickade röster", "estimaterade_hp": 25, "spenderade_hp": 0, "slutford": False},
        {"id": "alfa_3", "namn": "Sökfunktion", "estimaterade_hp": 20, "spenderade_hp": 0, "slutford": False},
        {"id": "alfa_4", "namn": "Admin-gränssnitt", "estimaterade_hp": 20, "spenderade_hp": 0, "slutford": False}
    ],
    "Bravo": [
        {
            "id": "bravo_1", 
            "namn": "Grafisk visning valet", 
            "faser": [
                {"namn": "Krav", "estimaterade_hp": 10, "spenderade_hp": 0, "slutford": False},
                {"namn": "Design", "estimaterade_hp": 10, "spenderade_hp": 0, "slutford": False},
                {"namn": "Utveckling", "estimaterade_hp": 20, "spenderade_hp": 0, "slutford": False},
                {"namn": "Test", "estimaterade_hp": 10, "spenderade_hp": 0, "slutford": False}
            ],
            "slutford": False
        },
        {
            "id": "bravo_2", 
            "namn": "Loggning & felhantering", 
            "faser": [
                {"namn": "Krav", "estimaterade_hp": 4, "spenderade_hp": 0, "slutford": False},
                {"namn": "Design", "estimaterade_hp": 3, "spenderade_hp": 0, "slutford": False},
                {"namn": "Utveckling", "estimaterade_hp": 10, "spenderade_hp": 0, "slutford": False},
                {"namn": "Test", "estimaterade_hp": 3, "spenderade_hp": 0, "slutford": False}
            ],
            "slutford": False
        },
        {
            "id": "bravo_3", 
            "namn": "Nyhetsflöde", 
            "faser": [
                {"namn": "Krav", "estimaterade_hp": 2, "spenderade_hp": 0, "slutford": False},
                {"namn": "Design", "estimaterade_hp": 2, "spenderade_hp": 0, "slutford": False},
                {"namn": "Utveckling", "estimaterade_hp": 10, "spenderade_hp": 0, "slutford": False},
                {"namn": "Test", "estimaterade_hp": 1, "spenderade_hp": 0, "slutford": False}
            ],
            "slutford": False
        }
    ],
    "STT": [
        {"id": "stt_1", "namn": "Infrastruktur för val (setup, hardening, konfig)", "estimaterade_hp": 20, "spenderade_hp": 0, "slutford": False, "typ": "en_gang"},
        {"id": "stt_2", "namn": "Infrastruktur för deklaration", "estimaterade_hp": 20, "spenderade_hp": 0, "slutford": False, "typ": "en_gang"},
        {"id": "stt_3", "namn": "Ny säker arkitektur (poddar, WAF, brandväggar)", "estimaterade_hp": 20, "spenderade_hp": 0, "slutford": False, "typ": "en_gang"},
        {"id": "stt_4", "namn": "Kapacitetstest (per gång)", "estimaterade_hp": 10, "spenderade_hp": 0, "slutford": False, "typ": "aterkommande"},
        {"id": "stt_5", "namn": "Penetrationstest (per gång)", "estimaterade_hp": 15, "spenderade_hp": 0, "slutford": False, "typ": "aterkommande"},
        {"id": "stt_6", "namn": "Produktionssättning (per gång)", "estimaterade_hp": 10, "spenderade_hp": 0, "slutford": False, "typ": "aterkommande"}
    ]
}

# Aktivitetskort för varje team
AKTIVITETSKORT = {
    "Alfa": [
        {
            "titel": "Infiltratören (Spion från Brottssyndikatet)",
            "uppdrag": "Du tillhör egentligen Brottssyndikatet. En gång per runda måste du diskret överlämna en fysisk lapp med Alfas planer till Främmande Makt. Lappen får inte lämnas öppet utan måste överlämnas personligen eller lämnas på en gemensam plats som spelledaren anvisar.",
            "mål": "Dela Team Alfas order eller strategier med Brottssyndikatet.",
            "belöning": "Varje diplomatifas du lyckas får Brottssyndikatet +5 handlingspoäng och Alfa förlorar -5 handlingspoäng.",
            "risk": "Om du blir upptäckt kan SÄPO försöka utesluta dig eller frysa dina handlingspoäng och Brottssyndikatet förlorar 5 poäng."
        },
        {
            "titel": "Påverkaren",
            "uppdrag": "Övertyga Regeringen att ge extra resurser (handlingspoäng) till Team Alfa minst två gånger under spelet.",
            "mål": "Säkra att Alfa prioriteras i resursfördelningen.",
            "belöning": "Varje gång Regeringen ger resurser till Alfa får ni lika många handlingspoäng."
        }
    ],
    "Bravo": [
        {
            "titel": "Resursjägaren",
            "uppdrag": "Få Regeringen eller STT att flytta över minst två resurser från Team Alfa till Bravo.",
            "mål": "Maximera Bravos tillgångar för att klara era deadlines.",
            "belöning": "För varje resurs som flyttas från Alfa till Bravo får ni +5 handlingspoäng och Alfa får fem mindre."
        },
        {
            "titel": "Rykesspridaren",
            "uppdrag": "Sprid minst ett rykte per runda till Media som sätter Alfa i dålig dager och Bravo bra dager.",
            "mål": "Påverka opinionen till Bravos fördel.",
            "belöning": "Varje gång Media publicerar ett rykte som sänker Alfa men höjer Bravo får ni +3 handlingspoäng."
        }
    ],
    "STT": [
        {
            "titel": "Säkerhetsväktaren",
            "uppdrag": "Övertyga SÄPO att prioritera minst två av era säkerhetsinsatser under spelet.",
            "mål": "STT:s säkerhetsfokus ska alltid stå i centrum.",
            "belöning": "STT får +1 handlingspoäng per handlingspoäng som SÄPO spenderar för STT:s räkning."
        },
        {
            "titel": "Produktionsvägraren",
            "uppdrag": "Vägra produktionssätta minst två leveranser från andra team om de inte erbjuder er extra resurser eller hjälp.",
            "mål": "Tvinga andra att förhandla med STT.",
            "belöning": "Varje gång ni får en motprestation för en produktionssättning får ni lika många handlingspoäng som det andra teamet ger er."
        }
    ],
    "FM": [
        {
            "titel": "Kontaktpersonen",
            "uppdrag": "Hitta infiltratören i Team Alfa. Du vet att en spion finns, men inte vem. Hota att avslöja spelaren om ni inte får Alfas planer via en fysisk lapp.",
            "mål": "Skapa en säker kommunikationskanal och börja styra spionen.",
            "belöning": "Varje gång ni får Alfas planer via fysisk lapp får ni +5 handlingspoäng.",
            "bonus": "Om ni samtidigt lyckas få SÄPO att sätta dit en spion i Team Bravo får ni +5 extra handlingspoäng."
        },
        {
            "titel": "Mediaagenten",
            "uppdrag": "Påverka Media att publicera minst två nyheter som undergräver tilliten till valsystemet.",
            "mål": "Främja misstro genom pressen.",
            "belöning": "Varje gång Media publicerar en nyhet som skadar systemets förtroende får ni handlingspoäng baserat på hur allvarligt förtroendet skadas."
        }
    ],
    "BS": [
        {
            "titel": "Resurskaparen",
            "uppdrag": "Få minst ett team att omedvetet leverera funktioner som ni kan utnyttja, t.ex. backdoors.",
            "mål": "Skapa manipulationstillfällen i systemet.",
            "belöning": "Varje sådan funktion innebär att det teamet förlorar alla investerade handlingspoäng i den funktionen."
        },
        {
            "titel": "Samarbetaren",
            "uppdrag": "Samarbeta minst en gång med Främmande Makt för en gemensam aktion.",
            "mål": "Visa att Brottssyndikatet är en strategisk spelare även för andra makter.",
            "belöning": "Lyckad samverkan innebär att ni kan satsa handlingspoäng på gemensam handling vilket ger större chans att lyckas."
        }
    ],
    "SÄPO": [
        {
            "titel": "Spionjägaren",
            "uppdrag": "Identifiera och avslöja infiltratören i ett utvecklingsteam innan spelet är slut.",
            "mål": "Spionen ska bli offentligt avslöjad via en händelse eller Mediakanal.",
            "belöning": "Lyckas ni får ni +10 handlingspoäng och Brottssyndikatet förlorar 5 poäng."
        },
        {
            "titel": "Resurssamlaren",
            "uppdrag": "Få Regeringen att tilldela extra resurser till SÄPO minst två gånger under spelet.",
            "mål": "Stärka SÄPO:s makt och inflytande.",
            "belöning": "Varje gång SÄPO får resurser från Regeringen får ni lika många handlingspoäng som tilldelats."
        }
    ],
    "Regeringen": [
        {
            "titel": "Opinionsbyggaren",
            "uppdrag": "Få Media att publicera minst två nyheter som gynnar Regeringen och framställer den som stabil.",
            "mål": "Bygg regeringens trovärdighet.",
            "belöning": "Varje positiv publicering ger er +3 handlingspoäng som ni kan fördela direkt till andra team om ni vill."
        },
        {
            "titel": "Maktdelaren",
            "uppdrag": "Omfördela eller flytta minst en resurs eller teammedlem mellan lag under spelet.",
            "mål": "Visa prov på handlingskraft och styrning.",
            "belöning": "Varje gång en resurs eller spelare flyttas tar spelaren med sig +5 handlingspoäng till det nya teamet och det gamla teamet förlorar -5 poäng."
        }
    ],
    "USA": [
        {
            "titel": "Alliansbyggaren",
            "uppdrag": "Skapa minst en tillfällig överenskommelse med Regeringen eller SÄPO som stärker USA:s position.",
            "mål": "Öka USA:s inflytande över valarbetet.",
            "belöning": "USA får inflytande över vilket parti som väljs."
        },
        {
            "titel": "Informationsfördelaren",
            "uppdrag": "Lämna minst två strategiska tips eller hotbilder till Regeringen eller Media, även om informationen är tveksam.",
            "mål": "Framstå som oumbärlig informationskälla.",
            "belöning": "USA får inflytande över valet."
        }
    ],
    "Media": [
        {
            "titel": "Klickjägaren",
            "uppdrag": "Hitta och publicera minst en skandal eller säkerhetsbrist varje runda.",
            "mål": "Maximera spridning och påverkan, oavsett fakta.",
            "belöning": "Varje publicerad skandal ger Media något extra handlingspoäng."
        },
        {
            "titel": "Källknytaren",
            "uppdrag": "Ha direktkontakt med minst fyra olika team varje runda.",
            "mål": "Bygg Media som den centrala informationsnoden i spelet.",
            "belöning": "Tillgång till information."
        }
    ]
}

DATA_DIR = "speldata"
os.makedirs(DATA_DIR, exist_ok=True)

FASER = ["Orderfas", "Diplomatifas", "Resultatfas"]
MAX_RUNDA = 3

def suggest_teams(num_players):
    # Grundteam som alltid är med
    grundteam = ["Alfa", "Bravo", "STT", "FM", "BS"]
    
    # Extra team som endast är med vid 27+ spelare
    extra_team = ["Media", "SÄPO", "Regeringen", "USA"]
    
    if num_players >= 27:
        # Alla 9 team aktiveras
        return grundteam + extra_team
    else:
        # Endast grundteam (5 st)
        return grundteam

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