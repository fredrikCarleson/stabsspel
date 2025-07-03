from flask import Flask, request, redirect, url_for, send_from_directory
from markupsafe import Markup
import os
import json
from datetime import datetime
import time
# Testkommentar: AI har skrivrättigheter

# Lägg till detta högst upp i din fil, efter importerna
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

def suggest_teams(num_players):
    """
    Returnerar en lista med lag baserat på antal spelare enligt tabellen.
    """
    teams = []
    for team, min_players in TEAMS:
        if num_players >= min_players:
            teams.append(team)
    return teams

app = Flask(__name__)

# Katalog för att lagra speldata
DATA_DIR = "speldata"
os.makedirs(DATA_DIR, exist_ok=True)

# Hjälpfunktioner för fas och timer
FASER = ["Orderfas", "Diplomatifas", "Resultatfas"]

def get_next_fas(current_fas, runda):
    if runda < MAX_RUNDA:
        idx = FASER.index(current_fas)
        return FASER[(idx + 1) % len(FASER)]
    else:
        # Sista rundan: Orderfas -> Resultatfas -> (ingen diplomati)
        if current_fas == "Orderfas":
            return "Resultatfas"
        elif current_fas == "Resultatfas":
            return "Orderfas"  # Om man skulle gå vidare, men spelet avslutas normalt
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

# Hjälpfunktion för att skapa nytt spel och spara till fil
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

@app.route("/delete_game/<spel_id>", methods=["POST"])
def delete_game(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if os.path.exists(filnamn):
        os.remove(filnamn)
    return redirect(url_for("startsida"))

@app.route("/", methods=["GET"])
def startsida():
    # Lista befintliga spel
    spel = []
    for fil in os.listdir(DATA_DIR):
        if fil.startswith("game_") and fil.endswith(".json"):
            with open(os.path.join(DATA_DIR, fil), encoding="utf-8") as f:
                data = json.load(f)
                spel.append({"id": data["id"], "datum": data["datum"], "plats": data["plats"]})
    spel_html = ''
    for s in spel:
        spel_html += f'<li><a href="/admin/{s["id"]}">{s["datum"]} – {s["plats"]} (ID: {s["id"]})</a> '
        spel_html += f'<form method="post" action="/delete_game/{s["id"]}" style="display:inline;" onsubmit="return confirm(\'Ta bort spelet permanent?\');">'
        spel_html += '<button type="submit">Ta bort</button></form></li>'
    return f'''
        <h1>Stabsspelet</h1>
        <a href="/admin"><button>Skapa nytt spel</button></a>
        <h2>Befintliga spel</h2>
        <ul>
            {spel_html}
        </ul>
    '''

@app.route("/teams/<int:num_players>")
def get_teams(num_players):
    teams = suggest_teams(num_players)
    return f"Antal spelare: {num_players}<br>Föreslagna lag: {', '.join(teams)}"

# Visa startsida: skapa nytt spel eller välj befintligt
@app.route("/admin", methods=["GET", "POST"])
def admin_start():
    if request.method == "POST":
        datum = request.form.get("datum")
        plats = request.form.get("plats")
        intervall = request.form.get("players_interval")
        antal_spelare = int(intervall) if intervall else 20
        orderfas_min = int(request.form.get("orderfas_min") or 10)
        diplomatifas_min = int(request.form.get("diplomatifas_min") or 10)
        spel_id = skapa_nytt_spel(datum, plats, antal_spelare, orderfas_min, diplomatifas_min)
        return redirect(url_for("admin_panel", spel_id=spel_id))
    # Lista befintliga spel
    spel = []
    for fil in os.listdir(DATA_DIR):
        if fil.startswith("game_") and fil.endswith(".json"):
            with open(os.path.join(DATA_DIR, fil), encoding="utf-8") as f:
                data = json.load(f)
                spel.append({"id": data["id"], "datum": data["datum"], "plats": data["plats"]})
    intervals = [
        ("20-29", 20),
        ("30-39", 30),
        ("40-49", 40),
        ("50-59", 50),
        ("60+", 60)
    ]
    return f'''
        <h1>Adminpanel – Starta nytt spel</h1>
        <form method="post">
            <label for="datum">Datum:</label>
            <input type="date" name="datum" id="datum" required><br>
            <label for="plats">Plats:</label>
            <input type="text" name="plats" id="plats" required><br>
            <label for="players_interval">Antal spelare:</label>
            <select name="players_interval" id="players_interval">
                {''.join([f'<option value="{val}">{label}</option>' for label, val in intervals])}
            </select><br>
            <label for="orderfas_min">Orderfas (minuter):</label>
            <input type="number" name="orderfas_min" id="orderfas_min" min="1" value="10" required><br>
            <label for="diplomatifas_min">Diplomatifas (minuter):</label>
            <input type="number" name="diplomatifas_min" id="diplomatifas_min" min="1" value="10" required><br>
            <input type="submit" value="Starta nytt spel">
        </form>
        <h2>Befintliga spel</h2>
        <ul>
            {''.join([f'<li><a href="/admin/{s["id"]}">{s["datum"]} – {s["plats"]} (ID: {s["id"]})</a></li>' for s in spel])}
        </ul>
    '''

def init_fashistorik_v2():
    # Startar med runda 1, Orderfas, pågående
    return [{"runda": 1, "fas": "Orderfas", "status": "pågående"}]

def add_fashistorik_entry(data, runda, fas, status):
    if "fashistorik" not in data or not isinstance(data["fashistorik"], list):
        data["fashistorik"] = init_fashistorik_v2()
    data["fashistorik"].append({"runda": runda, "fas": fas, "status": status})
    return data

def avsluta_aktuell_fas(data):
    # Sätt status på senaste pågående till avklarad
    if "fashistorik" in data and data["fashistorik"]:
        for entry in reversed(data["fashistorik"]):
            if entry["status"] == "pågående":
                entry["status"] = "avklarad"
                break
    return data

@app.route("/admin/<spel_id>/timer", methods=["POST"])
def admin_timer_action(spel_id):
    action = request.form.get("action")
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return "Spelet hittades inte.", 404
    with open(filnamn, encoding="utf-8") as f:
        data = json.load(f)
    now = int(time.time())
    if action == "start":
        data["timer_status"] = "running"
        data["timer_start"] = now
    elif action == "pause":
        if data.get("timer_status") == "running":
            elapsed = now - data.get("timer_start", now)
            data["timer_status"] = "paused"
            data["timer_elapsed"] = elapsed + data.get("timer_elapsed", 0)
    elif action == "reset":
        data["timer_status"] = "stopped"
        data["timer_start"] = None
        data["timer_elapsed"] = 0
    elif action == "next_fas":
        # Avsluta aktuell fas i historiken
        data = avsluta_aktuell_fas(data)
        # Byt fas och nollställ timer
        nuvarande_fas = data["fas"]
        nuvarande_runda = data.get("runda", 1)
        next_fas = get_next_fas(nuvarande_fas, nuvarande_runda)
        data["fas"] = next_fas
        data["timer_status"] = "stopped"
        data["timer_start"] = None
        data["timer_elapsed"] = 0
        # Lägg till ny fas i historiken
        if next_fas == "Orderfas":
            # Om vi går från Resultatfas till Orderfas, öka runda
            data["runda"] = nuvarande_runda + 1
            add_fashistorik_entry(data, data["runda"], "Orderfas", "pågående")
        else:
            add_fashistorik_entry(data, nuvarande_runda, next_fas, "pågående")
    save_game_data(spel_id, data)
    return redirect(url_for("admin_panel", spel_id=spel_id))

MAX_RUNDA = 3

def avsluta_spel(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if os.path.exists(filnamn):
        with open(filnamn, encoding="utf-8") as f:
            data = json.load(f)
        data["avslutat"] = True
        save_game_data(spel_id, data)

@app.route("/admin/<spel_id>/slut", methods=["POST"])
def admin_slut(spel_id):
    avsluta_spel(spel_id)
    return redirect(url_for("admin_panel", spel_id=spel_id))

@app.route("/admin/<spel_id>/ny_runda", methods=["POST"])
def admin_ny_runda(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return "Spelet hittades inte.", 404
    with open(filnamn, encoding="utf-8") as f:
        data = json.load(f)
    # Avsluta aktuell fas
    data = avsluta_aktuell_fas(data)
    # Starta ny runda med Orderfas
    data["runda"] = data.get("runda", 1) + 1
    data["fas"] = "Orderfas"
    data["timer_status"] = "stopped"
    data["timer_start"] = None
    data["timer_elapsed"] = 0
    add_fashistorik_entry(data, data["runda"], "Orderfas", "pågående")
    save_game_data(spel_id, data)
    return redirect(url_for("admin_panel", spel_id=spel_id))

@app.route("/admin/<spel_id>/reset", methods=["POST"])
def admin_reset(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return "Spelet hittades inte.", 404
    with open(filnamn, encoding="utf-8") as f:
        data = json.load(f)
    data["runda"] = 1
    data["fas"] = "Orderfas"
    data["timer_status"] = "stopped"
    data["timer_start"] = None
    data["timer_elapsed"] = 0
    data["avslutat"] = False
    data["fashistorik"] = init_fashistorik_v2()
    save_game_data(spel_id, data)
    return redirect(url_for("admin_panel", spel_id=spel_id))

@app.route("/team/<spel_id>/<lag_namn>")
def team_beskrivning(spel_id, lag_namn):
    # Sökväg till beskrivning och bild
    desc_dir = os.path.join("teambeskrivning")
    txt_path = os.path.join(desc_dir, f"{lag_namn.lower()}.txt")
    img_path = os.path.join(desc_dir, f"{lag_namn.lower()}.jpg")
    # Läs beskrivningstext
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            text = f.read()
        # Enkel formattering: radbrytningar till <br>, rubriker (rad som slutar med ":") till <b>
        lines = text.splitlines()
        html_lines = []
        for line in lines:
            if line.strip().endswith(":"):
                html_lines.append(f'<b>{line.strip()}</b>')
            else:
                html_lines.append(line)
        text_html = "<br>".join(html_lines)
    else:
        text_html = "<i>Ingen beskrivning hittades för detta lag.</i>"
    # Bild om den finns, placeras längst ner och på egen sida vid utskrift
    img_html = ""
    if os.path.exists(img_path):
        img_html = f'''
        <div class="bildsida">
            <img src="/teambeskrivning/{lag_namn.lower()}.jpg" alt="{lag_namn}" style="width:100%;max-width:100vw;max-height:29.7cm;object-fit:contain;">
        </div>
        '''
    # Förbättrad utskriftsvänlig och lättläst CSS
    return f'''
        <html>
        <head>
            <title>{lag_namn} – Lagbeskrivning</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 40px;
                    color: #222;
                    background: #fff;
                    line-height: 1.3;
                    font-size: 1.1em;
                }}
                h1 {{ font-size: 2.2em; margin-bottom: 0.3em; }}
                b {{ font-size: 1.1em; display: block; margin-top: 1.2em; margin-bottom: 0.2em; }}
                ul, ol {{ margin-left: 2em; margin-bottom: 1em; }}
                table {{ border-collapse: collapse; margin: 1.5em 0; width: 100%; }}
                th, td {{ border: 1px solid #bbb; padding: 0.5em 0.8em; }}
                th {{ background: #f3f3f3; }}
                img {{ margin: 1.5em 0; border-radius: 6px; box-shadow: 0 2px 8px #0001; }}
                .bildsida {{ margin-top: 2em; }}
                button {{ font-size: 1em; padding: 0.5em 1.2em; margin-bottom: 1.5em; border-radius: 5px; border: 1px solid #bbb; background: #f3f3f3; cursor: pointer; }}
                button:hover {{ background: #e0e0e0; }}
                @media print {{
                    button {{ display: none; }}
                    .bildsida {{ page-break-before: always; break-before: page; }}
                    .bildsida img {{ width: 100vw; max-width: 100vw; max-height: 29.7cm; object-fit: contain; }}
                    body {{ background: #fff; color: #000; }}
                }}
            </style>
        </head>
        <body>
            <button onclick="window.print()">Skriv ut</button>
            <h1>{lag_namn}</h1>
            <div>{Markup(text_html)}</div>
            {img_html}
        </body>
        </html>
    '''

@app.route("/teambeskrivning/<filename>")
def team_bild(filename):
    return send_from_directory("teambeskrivning", filename)

@app.route("/admin/<spel_id>")
def admin_panel(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return "Spelet hittades inte.", 404
    with open(filnamn, encoding="utf-8") as f:
        data = json.load(f)
    # Timerberäkning
    fas_min = get_fas_minutes(data)
    total_sec = fas_min * 60
    now = int(time.time())
    timer_status = data.get("timer_status", "stopped")
    timer_start = data.get("timer_start")
    timer_elapsed = data.get("timer_elapsed", 0)
    if timer_status == "running" and timer_start:
        elapsed = now - timer_start + timer_elapsed
    else:
        elapsed = timer_elapsed
    remaining = max(0, total_sec - elapsed)
    avslutat = data.get("avslutat", False)
    runda = data.get("runda", 1)
    fas = data.get("fas", "Orderfas")
    # Historik grupperad per runda
    historik = data.get("fashistorik", [])
    rundor = {}
    for entry in historik:
        rundnr = entry["runda"]
        if rundnr not in rundor:
            rundor[rundnr] = []
        rundor[rundnr].append(entry)
    historik_html = "<h3>Historik</h3>"
    for rundnr in sorted(rundor.keys()):
        historik_html += f'<h2>Runda {rundnr}</h2><ul>'
        for entry in rundor[rundnr]:
            status = "<b>(pågående)</b>" if entry["status"] == "pågående" else "(avklarad)"
            historik_html += f'<li>{entry["fas"]} {status}</li>'
        historik_html += "</ul>"
    # Rubrik för runda och fas
    rubrik = f"Runda {runda} av {MAX_RUNDA} – {fas}"
    # Gör lagnamn klickbara
    lag_html = ', '.join([
        f'<a href="/team/{spel_id}/{lag}" target="_blank">{lag}</a>' for lag in data['lag']
    ])
    # Timer och knappar endast för Orderfas/Diplomatifas
    timer_html = ""
    if not avslutat:
        if fas in ["Orderfas", "Diplomatifas"]:
            timer_html = f'''
            <h1>{rubrik}</h1>
            <div>
                <span id="timer">{remaining//60:02d}:{remaining%60:02d}</span>
                <form method="post" action="/admin/{spel_id}/timer" style="display:inline;">
                    <button name="action" value="start">Starta</button>
                    <button name="action" value="pause">Pausa</button>
                    <button name="action" value="reset">Återställ</button>
                    <button name="action" value="next_fas">Nästa fas</button>
                </form>
                <p>Status: {timer_status.capitalize()}</p>
            </div>
            <script>
            var remaining = {remaining};
            var timerElem = document.getElementById('timer');
            var running = "{timer_status}" === "running";
            function updateTimer() {{
                if (remaining > 0 && running) {{
                    remaining--;
                    var min = Math.floor(remaining/60);
                    var sec = remaining%60;
                    timerElem.textContent = (min<10?'0':'')+min+":"+(sec<10?'0':'')+sec;
                }}
            }}
            setInterval(updateTimer, 1000);
            </script>
            '''
        elif fas == "Resultatfas":
            timer_html = f'<h1>{rubrik}</h1>'
            if runda == MAX_RUNDA and fas == "Resultatfas":
                timer_html += f'''
                <form method="post" action="/admin/{spel_id}/ny_runda" style="display:inline;">
                    <button type="submit">Starta ny runda</button>
                </form>
                '''
            if runda > MAX_RUNDA and fas == "Resultatfas":
                timer_html += f'''
                <form method="post" action="/admin/{spel_id}/slut" style="display:inline;">
                    <button type="submit">Avsluta spelet</button>
                </form>
                '''
    else:
        timer_html = f'<h2>Spelet är avslutat</h2>'
    # HTML
    return f'''
        <h1>Adminpanel för spel {spel_id}</h1>
        <p><b>Datum:</b> {data["datum"]} <b>Plats:</b> {data["plats"]} <b>Antal spelare:</b> {data["antal_spelare"]}</p>
        <p><b>Orderfas:</b> {data.get("orderfas_min", "-")} min | <b>Diplomatifas:</b> {data.get("diplomatifas_min", "-")} min</p>
        <p><b>Lag:</b> {lag_html}</p>
        <hr>
        {historik_html}
        <hr>
        {timer_html}
        <hr>
        <form method="post" action="/admin/{spel_id}/reset">
            <button type="submit">Återställ spel</button>
        </form>
        <p>Här kommer funktioner för order, poäng, resultat, backlog m.m.</p>
        <a href="/admin">Tillbaka till adminstart</a>
    '''

if __name__ == "__main__":
    app.run(debug=True)