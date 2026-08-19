import os
import json
import copy
import shutil
import threading
import uuid
from datetime import datetime
import time
import secrets
import hashlib
import base64

_save_locks_guard = threading.Lock()
_save_locks = {}

SESSION_TIMEOUT_SECONDS = 6 * 60 * 60  # Cover a full live event


def _save_lock_for(spel_id):
    with _save_locks_guard:
        lock = _save_locks.get(spel_id)
        if lock is None:
            # Request handlers hold this lock across load -> mutate -> save.
            # save_game_data also takes it, so it must be re-entrant.
            lock = threading.RLock()
            _save_locks[spel_id] = lock
        return lock


def game_lock_for(spel_id):
    """Return the per-game lock used to serialize read-modify-write mutations."""
    return _save_lock_for(str(spel_id))

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

# Lösenordskryptering
def encrypt_password(password):
    """Kryptera lösenord med salt och hash"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(stored_password, provided_password):
    """Verifiera lösenord mot lagrat hash"""
    try:
        salt, password_hash = stored_password.split(':')
        password_hash_bytes = bytes.fromhex(password_hash)
        new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000)
        return password_hash_bytes == new_hash
    except:
        return False

def get_default_password():
    """Returnera standardlösenord för befintliga spel"""
    return "apa123"

def check_game_password(spel_id, provided_password):
    """Kontrollera om angivet lösenord stämmer för spelet"""
    data = load_game_data(spel_id)
    if not data:
        return False
    
    stored_password = data.get("password")
    
    # Om inget lösenord finns lagrat, använd standardlösenord
    if not stored_password:
        return provided_password == get_default_password()
    
    # Verifiera mot lagrat lösenord
    return verify_password(stored_password, provided_password)

def is_game_session_valid(spel_id, session_data):
    """Kontrollera om session är giltig för spelet"""
    if not session_data:
        return False
    
    # Kontrollera att sessionen är för rätt spel
    if session_data.get('spel_id') != spel_id:
        return False
    
    # Kontrollera att sessionen inte är utgången
    import time
    session_time = session_data.get('timestamp', 0)
    current_time = time.time()
    session_timeout = SESSION_TIMEOUT_SECONDS
    
    if current_time - session_time > session_timeout:
        return False
    
    return True

def create_game_session(spel_id):
    """Skapa session för spel"""
    return {
        'spel_id': spel_id,
        'timestamp': time.time(),
        'authenticated': True
    }


def refresh_game_session(session_data):
    """Sliding expiry so a live GM is not kicked during play."""
    if not session_data:
        return session_data
    session_data["timestamp"] = time.time()
    return session_data

def get_phase_timer(data):
    """Get remaining time for current phase - unified timer logic"""
    import time
    
    # Use admin timer system instead of fas_start_time
    fas_minutes = 0
    if data["fas"] == "Orderfas":
        fas_minutes = data.get("orderfas_min", 10)
    elif data["fas"] == "Diplomatifas":
        fas_minutes = data.get("diplomatifas_min", 10)
    elif data["fas"] == "Resultatfas":
        fas_minutes = data.get("resultatfas_min", 10)
    
    # Use admin timer system
    total_sec = fas_minutes * 60
    bonus = int(data.get("timer_bonus") or 0)
    now = int(time.time())
    timer_status = data.get("timer_status", "stopped")
    timer_start = data.get("timer_start")
    timer_elapsed = data.get("timer_elapsed", 0)
    
    if timer_status == "running" and timer_start:
        elapsed = now - timer_start + timer_elapsed
    else:
        elapsed = timer_elapsed
    
    remaining_seconds = max(0, total_sec + bonus - elapsed)
    
    return int(remaining_seconds)

def is_declaration_period(runda):
    """Check if current round is during declaration period (runda 3 = april-juni)"""
    return runda == 3

# Bas-HP-tabell som dictionary för enklare uppslag
DEFAULT_HP = {namn: hp for namn, hp in TEAMS}

# För stora spel (alla aktörer aktiva) justeras några basvärden
LARGE_GAME_OVERRIDES = {
    "STT": 30,          # +5
    "FM": 10,          # -2
    "BS": 10,          # -2
    "Media": 12,       # -3
    "Regeringen": 12,  # +2
    "SÄPO": 15,        # +3
}

def is_large_game(data: dict) -> bool:
    """Returnerar True om spelet kör med samtliga 9 lag (stort spel)."""
    try:
        lag = data.get("lag", [])
        return isinstance(lag, list) and len(lag) >= 9
    except Exception:
        return False

def get_team_base_hp(team_name: str, data: dict) -> int:
    """Hämta bas-HP för ett lag givet spelets storlek.

    - Litet spel (grundteam): använd DEFAULT_HP
    - Stort spel (alla 9 lag): använd overrides där de finns
    """
    base = DEFAULT_HP.get(team_name, 20)
    if is_large_game(data):
        return LARGE_GAME_OVERRIDES.get(team_name, base)
    return base

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
            "uppdrag": "Du tillhör egentligen Brottssyndikatet. En gång per runda måste du diskret överlämna en fysisk lapp med Alfas planer till Brottssyndikatet. Lappen får inte lämnas öppet utan måste överlämnas personligen eller lämnas på en gemensam plats som spelledaren anvisar.",
            "mål": "Dela Team Alfas order eller strategier med Brottssyndikatet.",
            "belöning": "Varje diplomatifas du lyckas får Brottssyndikatet +5 handlingspoäng och Alfa förlorar -5 handlingspoäng.",
            "risk": "Om du blir upptäckt stoppas framtida överlämningar och Brottssyndikatet kan inte längre få bonusen på 5 HP. SÄPO kan också försöka utesluta dig eller frysa dina handlingspoäng."
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
            "uppdrag": "Ni vet att Brottssyndikatet har en spion i Team Alfa, men inte vem. Förhandla med Brottssyndikatet för att få tillgång till information från spionen.",
            "mål": "Få del av Alfas planer genom en överenskommelse med Brottssyndikatet.",
            "belöning": "Information från spionen kan ge er ett övertag, men spionens bonus på 5 HP tillhör Brottssyndikatet.",
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
MAX_RUNDA = 4

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
    """Return the next phase. Last round stays on Resultatfas instead of opening round 5."""
    if current_fas not in FASER:
        return "Orderfas"
    if runda >= MAX_RUNDA and current_fas == "Resultatfas":
        return "Resultatfas"
    idx = FASER.index(current_fas)
    return FASER[(idx + 1) % len(FASER)]


def clone_backlog_for_teams(lag):
    """Deep-copy backlog templates so one game cannot mutate another."""
    backlog_data = {}
    for lag_namn in lag:
        if lag_namn not in BACKLOG:
            continue
        cloned = copy.deepcopy(BACKLOG[lag_namn])
        for uppgift in cloned:
            if not isinstance(uppgift, dict):
                continue
            uppgift["spenderade_hp"] = 0
            uppgift["slutford"] = False
            for fas in uppgift.get("faser", []):
                fas["spenderade_hp"] = 0
                fas["slutford"] = False
        backlog_data[lag_namn] = cloned
    return backlog_data


def list_saved_games():
    """Load all valid game files, skipping corrupt or incomplete JSON."""
    games = []
    if not os.path.isdir(DATA_DIR):
        return games
    for fil in os.listdir(DATA_DIR):
        if not fil.startswith("game_") or not fil.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, fil)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get("id"):
                games.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    games.sort(key=lambda g: str(g.get("skapad") or g.get("datum") or ""), reverse=True)
    return games

def get_fas_minutes(data):
    if data["fas"] == "Orderfas":
        return int(data.get("orderfas_min", 10))
    elif data["fas"] == "Diplomatifas":
        return int(data.get("diplomatifas_min", 10))
    elif data["fas"] == "Resultatfas":
        return int(data.get("resultatfas_min", 10))
    else:
        return 0

def load_game_data(spel_id):
    """Ladda speldata från fil med felhantering"""
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return None
    
    try:
        with open(filnamn, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in {filnamn}: {e}")
        # Försök läsa backup om den finns
        backup_filnamn = filnamn + ".backup"
        if os.path.exists(backup_filnamn):
            try:
                with open(backup_filnamn, encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None
    except Exception as e:
        print(f"Error loading game data from {filnamn}: {e}")
        return None

def save_game_data(spel_id, data):
    """Spara speldata till fil med atomisk skrivning för att undvika korruption"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    backup_filnamn = filnamn + ".backup"
    # Unique tmp per write so concurrent requests cannot delete each other's file
    temp_filnamn = f"{filnamn}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    max_retries = 5
    retry_delay = 0.1

    with _save_lock_for(spel_id):
        last_error = None
        for attempt in range(max_retries):
            try:
                if os.path.exists(filnamn):
                    try:
                        shutil.copy2(filnamn, backup_filnamn)
                    except OSError:
                        pass

                with open(temp_filnamn, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())

                os.replace(temp_filnamn, filnamn)
                return
            except (PermissionError, FileNotFoundError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                break

        if os.path.exists(temp_filnamn):
            try:
                os.remove(temp_filnamn)
            except OSError:
                pass
        print(f"Error saving game data for {spel_id}: {last_error}")
        raise last_error

def generate_game_id():
    """Return a readable ID with enough entropy to avoid same-second collisions."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}-{secrets.token_hex(8)}"


def skapa_nytt_spel(datum, plats, antal_spelare, orderfas_min, diplomatifas_min, password=None):
    spel_id = generate_game_id()
    
    lag = suggest_teams(antal_spelare)
    backlog_data = clone_backlog_for_teams(lag)
    
    # Generera tokens för alla team
    team_tokens = generate_team_tokens(spel_id, lag)
    
    # Kryptera lösenord om det finns
    encrypted_password = None
    if password:
        encrypted_password = encrypt_password(password)
    
    data = {
        "id": spel_id,
        "datum": datum,
        "plats": plats,
        "antal_spelare": antal_spelare,
        "skapad": datetime.now().isoformat(),
        "fas": "Orderfas",
        "runda": 1,
        "lag": lag,
        "order": {},
        "poang": {},
        "resultat": [],
        "backlog": backlog_data,
        "orderfas_min": orderfas_min,
        "diplomatifas_min": diplomatifas_min,
        "resultatfas_min": 10,
        "timer_bonus": 0,
        "gm_log": [],
        "gm_undo": [],
        "test_mode": False,
        "fashistorik": init_fashistorik_v2(),
        "team_tokens": team_tokens,
        "password": encrypted_password,
    }
    # Initiera poäng baserat på spelstorlek
    data["poang"] = {}
    for lag_namn in lag:
        bas_hp = get_team_base_hp(lag_namn, data)
        data["poang"][lag_namn] = {"bas": bas_hp, "aktuell": bas_hp, "regeringsstod": False}
    save_game_data(spel_id, data)
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

def generate_team_token(team_name, spel_id):
    """Generera en unik token för ett team"""
    # Skapa en unik sträng baserad på team namn, spel ID och tid
    unique_string = f"{team_name}_{spel_id}_{datetime.now().isoformat()}"
    # Generera en säker token
    token = secrets.token_urlsafe(16)
    # Skapa en hash för extra säkerhet
    token_hash = hashlib.sha256(f"{unique_string}_{token}".encode()).hexdigest()[:12]
    return f"{token}_{token_hash}"

def generate_team_tokens(spel_id, teams):
    """Generera tokens för alla team i ett spel"""
    tokens = {}
    for team in teams:
        tokens[team] = generate_team_token(team, spel_id)
    return tokens

def validate_team_token(spel_id, team_name, token):
    """Validera att en token tillhör rätt team och spel"""
    try:
        # Ladda speldata för att hämta tokens
        data = load_game_data(spel_id)
        if not data:
            return False
        
        team_tokens = data.get("team_tokens", {})
        return team_tokens.get(team_name) == token
    except:
        return False

def get_team_by_token(spel_id, token):
    """Hitta team baserat på token"""
    try:
        data = load_game_data(spel_id)
        if not data:
            return None
        
        team_tokens = data.get("team_tokens", {})
        for team_name, team_token in team_tokens.items():
            if team_token == token:
                return team_name
        return None
    except:
        return None
