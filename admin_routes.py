from flask import Blueprint, request, redirect, url_for
from markupsafe import Markup
import os
import json
import time
from models import (
    skapa_nytt_spel, suggest_teams, get_fas_minutes, save_game_data, get_next_fas,
    avsluta_aktuell_fas, add_fashistorik_entry, avsluta_spel, init_fashistorik_v2, MAX_RUNDA, DATA_DIR, TEAMS, AKTIVITETSKORT, BACKLOG
)

admin_bp = Blueprint('admin', __name__)

# ============================================================================
# HJÄLPFUNKTIONER
# ============================================================================

def load_game_data(spel_id):
    """Ladda speldatan från fil"""
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return None
    with open(filnamn, encoding="utf-8") as f:
        return json.load(f)

def create_team_info_js():
    """Skapa JavaScript för team-information"""
    return '''
    <script>
    function updateTeamInfo() {
        const select = document.getElementById('players_interval');
        const teamInfo = document.getElementById('team-info');
        const numPlayers = parseInt(select.value);
        
        if (numPlayers >= 27) {
            teamInfo.innerHTML = `
                <h3>Team som kommer vara med (9 st):</h3>
                <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <h4>🧩 Grundteam (5 st):</h4>
                    <ul>
                        <li>Team Alfa</li>
                        <li>Team Bravo</li>
                        <li>STT</li>
                        <li>Främmande Makt (FM)</li>
                        <li>Brottssyndikatet (BS)</li>
                    </ul>
                    <h4>➕ Extra team (4 st):</h4>
                    <ul>
                        <li>Media</li>
                        <li>SÄPO</li>
                        <li>Regeringen</li>
                        <li>USA</li>
                    </ul>
                </div>
            `;
        } else {
            teamInfo.innerHTML = `
                <h3>Team som kommer vara med (5 st):</h3>
                <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <h4>🧩 Grundteam:</h4>
                    <ul>
                        <li>Team Alfa</li>
                        <li>Team Bravo</li>
                        <li>STT</li>
                        <li>Främmande Makt (FM)</li>
                        <li>Brottssyndikatet (BS)</li>
                    </ul>
                    <p><em>Extra team (Media, SÄPO, Regeringen, USA) aktiveras vid 27+ spelare</em></p>
                </div>
            `;
        }
    }
    
    // Uppdatera när sidan laddas
    window.onload = function() {
        updateTeamInfo();
    };
    </script>
    '''

def create_compact_header(data, lag_html):
    """Skapa kompakt header med spelinformation"""
    return f'''
    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #007bff;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div style="flex: 1; min-width: 300px;">
                <p style="margin: 0; font-size: 14px;"><b>Datum:</b> {data["datum"]} <b>Plats:</b> {data["plats"]} <b>Antal spelare:</b> {data["antal_spelare"]}</p>
                <p style="margin: 5px 0 0 0; font-size: 14px;"><b>Orderfas:</b> {data.get("orderfas_min", "-")} min | <b>Diplomatifas:</b> {data.get("diplomatifas_min", "-")} min</p>
            </div>
            <div style="flex: 1; min-width: 300px;">
                <p style="margin: 0; font-size: 14px;"><b>Lag:</b> {lag_html}</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">(Klicka på laget för att se dess mål)</p>
            </div>
        </div>
    </div>
    '''

def create_action_buttons(spel_id):
    """Skapa knappar för åtgärder"""
    poang_lank = f'<a href="/admin/{spel_id}/poang" style="display: block; text-decoration: none;"><button style="width: 100%; height: 40px;">Visa/ändra handlingspoäng</button></a>'
    aktivitetskort_lank = f'<a href="/admin/{spel_id}/aktivitetskort" target="_blank" style="display: block; text-decoration: none;"><button style="width: 100%; height: 40px;">Skriv ut aktivitetskort</button></a>'
    reset_lank = f'<form method="post" action="/admin/{spel_id}/reset" style="display: block; text-decoration: none;"><button type="submit" style="width: 100%; height: 40px;">Återställ spel</button></form>'
    back_lank = f'<a href="/admin" style="display: block; text-decoration: none;"><button style="width: 100%; height: 40px;">Tillbaka till adminstart</button></a>'
    
    return f'''
    <div style="display: flex; flex-direction: row; gap: 10px; margin: 15px 0; flex-wrap: wrap;">
        {poang_lank}
        {aktivitetskort_lank}
        {reset_lank}
        {back_lank}
    </div>
    '''

def create_timer_controls(spel_id, remaining, timer_status):
    """Skapa timer-kontroller"""
    return f'''
    <div>
        <span id="timer">{remaining//60:02d}:{remaining%60:02d}</span>
        <form method="post" action="/admin/{spel_id}/timer" style="display:inline;">
            <button name="action" value="start">Starta</button>
            <button name="action" value="pause">Pausa</button>
            <button name="action" value="reset">Återställ</button>
        </form>
        <p class="status {timer_status}">Status: {timer_status.capitalize()}</p>
    </div>
    '''

def create_orderfas_checklist(spel_id, data):
    """Skapa checklista för Orderfas"""
    checklist_html = f'''
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #28a745;">
        <h3>📋 Checklista: Ordrar från alla team</h3>
        <div style="margin: 10px 0;">
    '''
    
    # Skapa checkbox för varje lag
    for i, lag in enumerate(data["lag"], 1):
        checklist_html += f'''
            <label style="display: flex; align-items: center; margin: 8px 0;">
                <input type="checkbox" id="order_check{i}" style="margin-right: 10px;" onchange="updateNextFasButton()">
                <span>Ordrar från {lag}</span>
            </label>
        '''
    
    checklist_html += f'''
        </div>
    </div>
    
    <form method="post" action="/admin/{spel_id}/timer" style="display:inline;">
        <button name="action" value="next_fas" id="next-fas-btn" disabled style="opacity: 0.5; cursor: not-allowed;">Nästa fas</button>
    </form>
    
    <script>
    function updateNextFasButton() {{
        const totalTeams = {len(data["lag"])};
        let checkedCount = 0;
        
        for (let i = 1; i <= totalTeams; i++) {{
            const checkbox = document.getElementById('order_check' + i);
            if (checkbox && checkbox.checked) {{
                checkedCount++;
            }}
        }}
        
        const nextFasButton = document.getElementById('next-fas-btn');
        
        if (checkedCount === totalTeams) {{
            nextFasButton.disabled = false;
            nextFasButton.style.opacity = '1';
            nextFasButton.style.cursor = 'pointer';
        }} else {{
            nextFasButton.disabled = true;
            nextFasButton.style.opacity = '0.5';
            nextFasButton.style.cursor = 'not-allowed';
        }}
    }}
    
    // Initiera knappen som inaktiverad när sidan laddas
    window.onload = function() {{
        updateNextFasButton();
    }};
    </script>
    '''
    
    return checklist_html

def create_diplomatifas_checklist(spel_id):
    """Skapa checklista för Diplomatifas"""
    return f'''
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #17a2b8;">
        <h3>📋 Checklista: Diplomatifas</h3>
        <div style="margin: 10px 0;">
            <label style="display: flex; align-items: center; margin: 8px 0;">
                <input type="checkbox" id="diplo_check1" style="margin-right: 10px;" onchange="updateDiploNextFasButton()">
                <span>Läs igenom alla orders</span>
            </label>
            <label style="display: flex; align-items: center; margin: 8px 0;">
                <input type="checkbox" id="diplo_check2" style="margin-right: 10px;" onchange="updateDiploNextFasButton()">
                <span>Besluta om konsekvenser gällande handlingspoäng</span>
            </label>
            <label style="display: flex; align-items: center; margin: 8px 0;">
                <input type="checkbox" id="diplo_check3" style="margin-right: 10px;" onchange="updateDiploNextFasButton()">
                <span>Skapa nyheter</span>
            </label>
        </div>
    </div>
    
    <form method="post" action="/admin/{spel_id}/timer" style="display:inline;">
        <button name="action" value="next_fas" id="diplo-next-fas-btn" disabled style="opacity: 0.5; cursor: not-allowed;">Nästa fas</button>
    </form>
    
    <script>
    function updateDiploNextFasButton() {{
        const check1 = document.getElementById('diplo_check1').checked;
        const check2 = document.getElementById('diplo_check2').checked;
        const check3 = document.getElementById('diplo_check3').checked;
        const nextFasButton = document.getElementById('diplo-next-fas-btn');
        
        if (check1 && check2 && check3) {{
            nextFasButton.disabled = false;
            nextFasButton.style.opacity = '1';
            nextFasButton.style.cursor = 'pointer';
        }} else {{
            nextFasButton.disabled = true;
            nextFasButton.style.opacity = '0.5';
            nextFasButton.style.cursor = 'not-allowed';
        }}
    }}
    
    // Initiera knappen som inaktiverad när sidan laddas
    window.onload = function() {{
        updateDiploNextFasButton();
    }};
    </script>
    '''

def create_resultatfas_checklist(spel_id):
    """Skapa checklista för Resultatfas"""
    return f'''
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #007bff;">
        <h3>✅ Checklista innan ny runda</h3>
        <div style="margin: 10px 0;">
            <label style="display: flex; align-items: center; margin: 8px 0;">
                <input type="checkbox" id="check1" style="margin-right: 10px;" onchange="updateStartButton()">
                <span>Uppdatera progress för teamens arbete</span>                
            </label>
            <a href="/admin/{spel_id}/backlog"><button>Uppdatera teamens arbete</button></a>
            <label style="display: flex; align-items: center; margin: 8px 0;">
                <input type="checkbox" id="check2" style="margin-right: 10px;" onchange="updateStartButton()">
                <span>Läsa upp nyheter</span>
            </label>
            <label style="display: flex; align-items: center; margin: 8px 0;">
                <input type="checkbox" id="check3" style="margin-right: 10px;" onchange="updateStartButton()">
                <span>Redigera handlingspoäng för varje team</span>
            </label>
            <a href="/admin/{spel_id}/poang"><button>Visa/ändra handlingspoäng</button></a>
        </div>
    </div>
    
    <script>
    function updateStartButton() {{
        const check1 = document.getElementById('check1').checked;
        const check2 = document.getElementById('check2').checked;
        const check3 = document.getElementById('check3').checked;
        const startButton = document.getElementById('start-ny-runda-btn');
        
        if (check1 && check2 && check3) {{
            startButton.disabled = false;
            startButton.style.opacity = '1';
            startButton.style.cursor = 'pointer';
        }} else {{
            startButton.disabled = true;
            startButton.style.opacity = '0.5';
            startButton.style.cursor = 'not-allowed';
        }}
    }}
    
    // Initiera knappen som inaktiverad när sidan laddas
    window.onload = function() {{
        updateStartButton();
    }};
    </script>
    '''

def create_timer_script(remaining, timer_status):
    """Skapa timer-script"""
    return f'''
    <script>
    var remaining = {remaining};
    var timerElem = document.getElementById('timer');
    var running = "{timer_status}" === "running";
    var alarmPlayed = false;
    
    // Skapa audio-element för alarmet
    var alarm = new Audio('/static/alarm.mp3');
    alarm.volume = 0.7; // Sätt volym till 70%
    
    function updateTimer() {{
        if (remaining > 0 && running) {{
            remaining--;
            var min = Math.floor(remaining/60);
            var sec = remaining%60;
            timerElem.textContent = (min<10?'0':'')+min+":"+(sec<10?'0':'')+sec;
            
            // Spela alarm när tiden går ut
            if (remaining <= 0 && !alarmPlayed) {{
                alarm.play().catch(function(error) {{
                    console.log('Kunde inte spela alarm:', error);
                }});
                alarmPlayed = true;
                
                // Visa varning
                alert('Tiden är ute!');
            }}
        }}
    }}
    setInterval(updateTimer, 1000);
    </script>
    '''

def create_historik_html(rundor):
    """Skapa snygg historik HTML"""
    if not rundor:
        return ""
    
    historik_html = '''
    <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin: 20px 0; border-left: 4px solid #6c757d;">
        <h3 style="margin-top: 0; color: #495057; font-size: 1.4em;">📊 Spelhistorik</h3>
    '''
    
    for rundnr in sorted(rundor.keys()):
        historik_html += f'''
        <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid #e9ecef;">
            <h4 style="margin: 0 0 10px 0; color: #495057; font-size: 1.2em;">🎯 Runda {rundnr}</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        '''
        
        for entry in rundor[rundnr]:
            if entry["status"] == "pågående":
                status_icon = "🔄"
                status_class = "background: #fff3cd; color: #856404; border: 1px solid #ffeaa7;"
            else:
                status_icon = "✅"
                status_class = "background: #d4edda; color: #155724; border: 1px solid #c3e6cb;"
            
            historik_html += f'''
            <div style="{status_class} padding: 8px 12px; border-radius: 6px; font-size: 0.9em; font-weight: 500;">
                {status_icon} {entry["fas"]}
            </div>
            '''
        
        historik_html += '''
            </div>
        </div>
        '''
    
    historik_html += '</div>'
    return historik_html

# ============================================================================
# ROUTES
# ============================================================================

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_start():
    if request.method == "POST":
        datum = request.form.get("datum")
        plats = request.form.get("plats")
        intervall = request.form.get("players_interval")
        antal_spelare = int(intervall) if intervall else 20
        orderfas_min = int(request.form.get("orderfas_min") or 10)
        diplomatifas_min = int(request.form.get("diplomatifas_min") or 10)
        spel_id = skapa_nytt_spel(datum, plats, antal_spelare, orderfas_min, diplomatifas_min)
        return redirect(url_for("admin.admin_panel", spel_id=spel_id))
    # Lista befintliga spel
    spel = []
    for fil in os.listdir(DATA_DIR):
        if fil.startswith("game_") and fil.endswith(".json"):
            with open(os.path.join(DATA_DIR, fil), encoding="utf-8") as f:
                data = json.load(f)
                spel.append({"id": data["id"], "datum": data["datum"], "plats": data["plats"]})
    intervals = [
        ("15-26 (5 team)", 20),
        ("27-60 (9 team)", 27)
    ]
    
    # Skapa JavaScript för att visa vilka team som kommer vara med
    team_info_js = create_team_info_js()
    
    return f'''
        <link rel="stylesheet" href="/static/style.css">
        <div class="container">
        <h1>Adminpanel – Starta nytt spel</h1>
        <form method="post">
            <label for="datum">Datum:</label>
            <input type="date" name="datum" id="datum" required><br>
            <label for="plats">Plats:</label>
            <input type="text" name="plats" id="plats" required><br>
            <label for="players_interval">Antal spelare:</label>
            <select name="players_interval" id="players_interval" onchange="updateTeamInfo()">
                {''.join([f'<option value="{val}">{label}</option>' for label, val in intervals])}
            </select><br>
            <label for="orderfas_min">Orderfas (minuter):</label>
            <input type="number" name="orderfas_min" id="orderfas_min" min="1" value="10" required><br>
            <label for="diplomatifas_min">Diplomatifas (minuter):</label>
            <input type="number" name="diplomatifas_min" id="diplomatifas_min" min="1" value="10" required><br>
            <input type="submit" value="Starta nytt spel">
        </form>
        
        <div id="team-info"></div>
        
        {team_info_js}
        <h2>Befintliga spel</h2>
        <ul>
            {''.join([f'<li><a href="/admin/{s["id"]}">{s["datum"]} – {s["plats"]} (ID: {s["id"]})</a></li> <form method="post" action="/admin/delete_game/{s["id"]}" style="display:inline;" onsubmit="return confirm(\'Är du säker på att du vill ta bort spelet {s["datum"]} – {s["plats"]}? Detta går inte att ångra.\')"><button type="submit" style="background: #e53e3e; margin-left: 10px;">Ta bort</button></form>' for s in spel])}
        </ul>
        </div>
    '''

@admin_bp.route("/admin/<spel_id>")
def admin_panel(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    # Beräkna timer-värden
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
    
    # Hämta spelstatus
    avslutat = data.get("avslutat", False)
    runda = data.get("runda", 1)
    fas = data.get("fas", "Orderfas")
    
    # Skapa historik
    historik = data.get("fashistorik", [])
    rundor = {}
    for entry in historik:
        rundnr = entry["runda"]
        if rundnr not in rundor:
            rundor[rundnr] = []
        rundor[rundnr].append(entry)
    
    historik_html = create_historik_html(rundor)
    rubrik = f"Runda {runda} av {MAX_RUNDA} – {fas}"
    
    # Skapa klickbara lagnamn
    lag_html = ', '.join([
        f'<a href="/team/{spel_id}/{lag}" target="_blank">{lag}</a>' for lag in data['lag']
    ])
    
    # Skapa timer HTML baserat på fas
    timer_html = create_timer_html(spel_id, data, fas, avslutat, remaining, timer_status, rubrik, runda)
    
    # Returnera komplett HTML
    return f'''
        <link rel="stylesheet" href="/static/style.css">
        <div class="container">
        <h1>Adminpanel för spel {spel_id}</h1>
        
        {create_compact_header(data, lag_html)}
        {create_action_buttons(spel_id)}
        
        <hr>
        {timer_html}
        <hr>
        
        
        
        {historik_html}
        </div>
    '''

def create_timer_html(spel_id, data, fas, avslutat, remaining, timer_status, rubrik, runda):
    """Skapa timer HTML baserat på fas"""
    if avslutat:
        return '<h2>Spelet är avslutat</h2>'
    
    if fas in ["Orderfas", "Diplomatifas"]:
        timer_html = f'<h1>{rubrik}</h1>'
        timer_html += create_timer_controls(spel_id, remaining, timer_status)
        
        if fas == "Orderfas":
            timer_html += create_orderfas_checklist(spel_id, data)
        elif fas == "Diplomatifas":
            timer_html += create_diplomatifas_checklist(spel_id)
        
        timer_html += create_timer_script(remaining, timer_status)
        return timer_html
    
    elif fas == "Resultatfas":
        timer_html = f'<h1>{rubrik}</h1>'
        timer_html += create_resultatfas_checklist(spel_id)
        
        # Starta ny runda knapp
        timer_html += f'''
        <form method="post" action="/admin/{spel_id}/ny_runda" style="display:inline;">
            <button type="submit" id="start-ny-runda-btn" disabled style="opacity: 0.5; cursor: not-allowed;">Starta ny runda</button>
        </form>
        '''
        
        # Avsluta spel om max runder nått
        if runda > MAX_RUNDA:
            timer_html += f'''
            <form method="post" action="/admin/{spel_id}/slut" style="display:inline;">
                <button type="submit">Avsluta spelet</button>
            </form>
            '''
        
        return timer_html
    
    return ""

@admin_bp.route("/admin/<spel_id>/timer", methods=["POST"])
def admin_timer_action(spel_id):
    action = request.form.get("action")
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
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
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))

@admin_bp.route("/admin/<spel_id>/slut", methods=["POST"])
def admin_slut(spel_id):
    avsluta_spel(spel_id)
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))

@admin_bp.route("/admin/<spel_id>/poang", methods=["GET", "POST"])
def admin_poang(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    laglista = data["lag"]
    runda = data.get("runda", 1)
    # Initiera poängstruktur om den saknas eller om lag saknas
    if "poang" not in data:
        data["poang"] = {}
    changed = False
    for lag in laglista:
        if lag not in data["poang"]:
            bas = next((minp for namn, minp in TEAMS if namn == lag), 20)
            data["poang"][lag] = {"bas": bas, "aktuell": bas, "regeringsstod": False}
            changed = True
    if changed:
        save_game_data(spel_id, data)
    # POST: uppdatera poäng och regeringsstöd
    if request.method == "POST":
        for lag in laglista:
            aktuell = int(request.form.get(f"poang_{lag}", data["poang"][lag]["aktuell"]))
            regeringsstod = request.form.get(f"regeringsstod_{lag}") == "on"
            data["poang"][lag]["aktuell"] = aktuell
            data["poang"][lag]["regeringsstod"] = regeringsstod
        save_game_data(spel_id, data)
    # Bygg tabell
    tabell = "<form method='post'><table border='1' cellpadding='6' style='border-collapse:collapse;'>"
    tabell += "<tr><th>Lag</th><th>Ursprung</th><th>Aktuell</th><th>Skillnad</th><th>Regeringsstöd</th><th>Formel</th></tr>"
    for lag in laglista:
        p = data["poang"][lag]
        bas = p["bas"]
        aktuell = p["aktuell"]
        diff = aktuell - bas
        diff_farg = "green" if diff > 0 else ("red" if diff < 0 else "black")
        regeringsstod = p.get("regeringsstod", False)
        # Formel: t.ex. 25 + 10 om regeringsstöd
        formel = str(aktuell)
        if regeringsstod:
            formel += " + 10"
        # Inputfält och checkbox
        tabell += f"<tr>"
        tabell += f"<td>{lag}</td>"
        tabell += f"<td>{bas}</td>"
        tabell += f"<td><input type='number' name='poang_{lag}' value='{aktuell}'></td>"
        tabell += f"<td style='color:{diff_farg};text-align:center;'>{'+' if diff>0 else ''}{diff}</td>"
        tabell += f"<td style='text-align:center;'><input type='checkbox' name='regeringsstod_{lag}' {'checked' if regeringsstod else ''}></td>"
        tabell += f"<td>{formel}</td>"
        tabell += f"</tr>"
    tabell += "</table><br><button type='submit'>Spara ändringar</button></form>"
    # Visa aktuell runda
    html = f"""
    <link rel='stylesheet' href='/static/style.css'>
    <div class='container'>
    <h1>Handlingspoäng – Runda {runda}</h1>
    {tabell}
    <br><a href='/admin/{spel_id}'>Tillbaka till adminpanelen</a>
    </div>
    """
    return Markup(html)

# Vid ny runda: nollställ regeringsstöd
def nollstall_regeringsstod(data):
    if "poang" in data:
        for lag in data["poang"]:
            data["poang"][lag]["regeringsstod"] = False
    return data

# Modifiera admin_ny_runda så att regeringsstöd nollställs
@admin_bp.route("/admin/<spel_id>/ny_runda", methods=["POST"])
def admin_ny_runda(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    # Avsluta aktuell fas
    data = avsluta_aktuell_fas(data)
    # Starta ny runda med Orderfas
    data["runda"] = data.get("runda", 1) + 1
    data["fas"] = "Orderfas"
    data["timer_status"] = "stopped"
    data["timer_start"] = None
    data["timer_elapsed"] = 0
    add_fashistorik_entry(data, data["runda"], "Orderfas", "pågående")
    # Nollställ regeringsstöd
    data = nollstall_regeringsstod(data)
    save_game_data(spel_id, data)
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))

@admin_bp.route("/admin/<spel_id>/reset", methods=["POST"])
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
    # Nollställ handlingspoäng och regeringsstöd, sätt rätt basvärde från TEAMS
    if "poang" in data:
        from models import TEAMS
        for lag in data["poang"]:
            bas = next((minp for namn, minp in TEAMS if namn.lower() == lag.lower()), 20)
            data["poang"][lag]["bas"] = bas
            data["poang"][lag]["aktuell"] = bas
            data["poang"][lag]["regeringsstod"] = False
    save_game_data(spel_id, data)
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))

@admin_bp.route("/admin/<spel_id>/aktivitetskort")
def admin_aktivitetskort(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    laglista = data["lag"]
    html = f'''
    <link rel="stylesheet" href="/static/style.css">
    <div class="container">
    <h1>Aktivitetskort för spel {spel_id}</h1>
    <p><b>Datum:</b> {data["datum"]} <b>Plats:</b> {data["plats"]}</p>
    <p><b>Antal spelare:</b> {data["antal_spelare"]}</p>
    
    <hr>
    '''
    
    for lag in laglista:
        if lag in AKTIVITETSKORT:
            html += f'<h2>🟢 Team {lag} – Aktivitetskort</h2>'
            html += '<div style="page-break-after: always;">'
            
            # Skapa kort för alla spelare i laget (2 med uppdrag, resten blanka)
            kort = AKTIVITETSKORT[lag]
            
            # Kort 1 med uppdrag
            html += f'''
            <div class="kort">
                <div class="kort-header">
                    <h3>{lag} Kort 1: {kort[0]["titel"]}</h3>
                </div>
                <div class="kort-innehall">
                    <p><strong>Uppdrag:</strong> {kort[0]["uppdrag"]}</p>
                    <p><strong>Mål:</strong> {kort[0]["mål"]}</p>
                    <p><strong>Belöning:</strong> {kort[0]["belöning"]}</p>
                    {f'<p><strong>Risk:</strong> {kort[0]["risk"]}</p>' if "risk" in kort[0] else ''}
                    {f'<p><strong>Bonus:</strong> {kort[0]["bonus"]}</p>' if "bonus" in kort[0] else ''}
                </div>
            </div>
            '''
            
            # Kort 2 med uppdrag
            html += f'''
            <div class="kort">
                <div class="kort-header">
                    <h3>{lag} Kort 2: {kort[1]["titel"]}</h3>
                </div>
                <div class="kort-innehall">
                    <p><strong>Uppdrag:</strong> {kort[1]["uppdrag"]}</p>
                    <p><strong>Mål:</strong> {kort[1]["mål"]}</p>
                    <p><strong>Belöning:</strong> {kort[1]["belöning"]}</p>
                    {f'<p><strong>Risk:</strong> {kort[1]["risk"]}</p>' if "risk" in kort[1] else ''}
                    {f'<p><strong>Bonus:</strong> {kort[1]["bonus"]}</p>' if "bonus" in kort[1] else ''}
                </div>
            </div>
            '''
            
            # Lägg till blanka kort för resten av spelarna
            for i in range(3, 11):  # Upp till 10 spelare per lag
                html += f'''
                <div class="kort">
                    <div class="kort-header">
                        <h3>{lag} Kort {i}: Blankt</h3>
                    </div>
                    <div class="kort-innehall">
                        <p><em>Du har inget särskilt uppdrag. Fokusera på ditt teams mål.</em></p>
                    </div>
                </div>
                '''
            
            html += '</div>'
        else:
            # Om laget inte har aktivitetskort, skapa blanka kort för alla spelare
            html += f'<h2>🟢 Team {lag} – Aktivitetskort</h2>'
            html += '<div style="page-break-after: always;">'
            
            # Skapa blanka kort för alla spelare i laget
            for i in range(1, 11):  # Upp till 10 spelare per lag
                html += f'''
                <div class="kort">
                    <div class="kort-header">
                        <h3>{lag} Kort {i}: Blankt</h3>
                    </div>
                    <div class="kort-innehall">
                        <p><em>Du har inget särskilt uppdrag. Fokusera på ditt teams mål.</em></p>
                    </div>
                </div>
                '''
            
            html += '</div>'
    
    html += f'''
    <br><br>
    <a href="/admin/{spel_id}">Tillbaka till adminpanelen</a>
    </div>
    '''
    return Markup(html)

@admin_bp.route("/admin/<spel_id>/backlog", methods=["GET", "POST"])
def admin_backlog(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    # Initiera backlog om den saknas eller är fel typ
    if "backlog" not in data or not isinstance(data["backlog"], dict):
        data["backlog"] = {}
    
    # Initiera backlog för varje lag som finns i spelet
    for lag in data["lag"]:
        if lag in BACKLOG and lag not in data["backlog"]:
            data["backlog"][lag] = BACKLOG[lag].copy()
    
    # Hantera POST-requests (uppdateringar)
    if request.method == "POST":
        for lag in data["lag"]:
            if lag in data["backlog"]:
                for uppgift in data["backlog"][lag]:
                    if lag == "Bravo":
                        # Bravo har faser
                        for fas in uppgift["faser"]:
                            fas_id = f"{uppgift['id']}_{fas['namn']}"
                            estimaterade = int(request.form.get(f"estimaterade_{fas_id}", fas["estimaterade_hp"]))
                            spenderade = int(request.form.get(f"spenderade_{fas_id}", fas["spenderade_hp"]))
                            fas["estimaterade_hp"] = estimaterade
                            fas["spenderade_hp"] = spenderade
                            fas["slutford"] = spenderade >= estimaterade
                        # Kontrollera om alla faser är slutforda
                        uppgift["slutford"] = all(fas["slutford"] for fas in uppgift["faser"])
                    else:
                        # Alfa och STT har enkla uppgifter
                        uppgift_id = uppgift["id"]
                        estimaterade = int(request.form.get(f"estimaterade_{uppgift_id}", uppgift["estimaterade_hp"]))
                        spenderade = int(request.form.get(f"spenderade_{uppgift_id}", uppgift["spenderade_hp"]))
                        uppgift["estimaterade_hp"] = estimaterade
                        uppgift["spenderade_hp"] = spenderade
                        uppgift["slutford"] = spenderade >= estimaterade
        
        save_game_data(spel_id, data)
        return redirect(url_for("admin.admin_backlog", spel_id=spel_id))
    
    # Bygg HTML för varje lag
    html_parts = []
    for lag in data["lag"]:
        if lag in data["backlog"]:
            html_parts.append(f'<h2>✅ Team {lag} – Uppgifter & handlingspoäng</h2>')
            
            if lag == "Bravo":
                # Bravo - GANTT-stil med faser
                html_parts.append('''
                <table>
                    <tr>
                        <th>Uppgift</th>
                        <th>Krav</th>
                        <th>Design</th>
                        <th>Utveckling</th>
                        <th>Test</th>
                        <th>Totalt</th>
                    </tr>
                ''')
                
                for uppgift in data["backlog"][lag]:
                    krav = uppgift["faser"][0]
                    design = uppgift["faser"][1]
                    utveckling = uppgift["faser"][2]
                    test = uppgift["faser"][3]
                    
                    total_estimaterade = sum(fas["estimaterade_hp"] for fas in uppgift["faser"])
                    total_spenderade = sum(fas["spenderade_hp"] for fas in uppgift["faser"])
                    
                    status_class = "slutford" if uppgift["slutford"] else "pa_gang"
                    task_class = "task-completed" if uppgift["slutford"] else ""
                    
                    html_parts.append(f'''
                    <tr class="{status_class}">
                        <td class="{task_class}"><strong>{uppgift["namn"]}</strong></td>
                        <td>
                            <input type="number" name="estimaterade_{uppgift['id']}_Krav" value="{krav['estimaterade_hp']}" min="0">
                            / <input type="number" name="spenderade_{uppgift['id']}_Krav" value="{krav['spenderade_hp']}" min="0">
                        </td>
                        <td>
                            <input type="number" name="estimaterade_{uppgift['id']}_Design" value="{design['estimaterade_hp']}" min="0">
                            / <input type="number" name="spenderade_{uppgift['id']}_Design" value="{design['spenderade_hp']}" min="0">
                        </td>
                        <td>
                            <input type="number" name="estimaterade_{uppgift['id']}_Utveckling" value="{utveckling['estimaterade_hp']}" min="0">
                            / <input type="number" name="spenderade_{uppgift['id']}_Utveckling" value="{utveckling['spenderade_hp']}" min="0">
                        </td>
                        <td>
                            <input type="number" name="estimaterade_{uppgift['id']}_Test" value="{test['estimaterade_hp']}" min="0">
                            / <input type="number" name="spenderade_{uppgift['id']}_Test" value="{test['spenderade_hp']}" min="0">
                        </td>
                        <td><strong>{total_spenderade}/{total_estimaterade} HP</strong></td>
                    </tr>
                    ''')
                
                html_parts.append('</table>')
                
            else:
                # Alfa och STT - enkel tabell
                html_parts.append('''
                <table>
                    <tr>
                        <th>Uppgift</th>
                        <th>Handlingspoäng</th>
                    </tr>
                ''')
                
                for uppgift in data["backlog"][lag]:
                    is_aterkommande = "typ" in uppgift and uppgift["typ"] == "aterkommande"
                    status_class = "slutford" if uppgift["slutford"] and not is_aterkommande else "pa_gang"
                    if is_aterkommande:
                        status_class = "aterkommande"
                    typ_text = f" ({uppgift['typ']})" if "typ" in uppgift else ""
                    
                    # Only show checkmark for completed non-recurring tasks
                    task_class = "task-completed" if uppgift["slutford"] and not is_aterkommande else ""
                    
                    html_parts.append(f'''
                    <tr class="{status_class}">
                        <td class="{task_class}"><strong>{uppgift["namn"]}{typ_text}</strong></td>
                        <td>
                            <input type="number" name="estimaterade_{uppgift['id']}" value="{uppgift['estimaterade_hp']}" min="0">
                            / <input type="number" name="spenderade_{uppgift['id']}" value="{uppgift['spenderade_hp']}" min="0">
                            <span class="progress">({uppgift['spenderade_hp']}/{uppgift['estimaterade_hp']} HP)</span>
                        </td>
                    </tr>
                    ''')
                
                html_parts.append('</table>')
            
            # Beräkna totala HP för laget
            if lag == "Bravo":
                total_estimaterade = sum(sum(fas["estimaterade_hp"] for fas in uppgift["faser"]) for uppgift in data["backlog"][lag])
                total_spenderade = sum(sum(fas["spenderade_hp"] for fas in uppgift["faser"]) for uppgift in data["backlog"][lag])
            else:
                total_estimaterade = sum(uppgift["estimaterade_hp"] for uppgift in data["backlog"][lag])
                total_spenderade = sum(uppgift["spenderade_hp"] for uppgift in data["backlog"][lag])
            
            html_parts.append(f'<p><strong>🔁 Totalt: {total_spenderade}/{total_estimaterade} HP</strong></p>')
            html_parts.append('<hr>')
    
    # Bygg komplett HTML
    html = f'''
    <link rel="stylesheet" href="/static/style.css">
    <div class="container">
        <h1>Team Backlogs – Runda {data.get("runda", 1)}</h1>
        <form method="post">
            {''.join(html_parts)}
            <button type="submit">Spara ändringar</button>
        </form>
        <br>
        <a href="/admin/{spel_id}">Tillbaka till adminpanelen</a>
    </div>
    '''
    
    return Markup(html)

@admin_bp.route("/admin/delete_game/<spel_id>", methods=["POST"])
def delete_game(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if os.path.exists(filnamn):
        os.remove(filnamn)
        return redirect(url_for("admin.admin_start"))
    return redirect(url_for("admin.admin_start")) 