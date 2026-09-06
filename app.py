import os
import json
import time
import sys

# Windows consoles often use cp1252; avoid UnicodeEncodeError on startup logs
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from flask import Flask, send_from_directory, make_response, jsonify, request, session
from markupsafe import escape
from admin_routes import admin_bp
from team_routes import team_bp
from team_order_routes import team_order_bp
from models import suggest_teams, DATA_DIR, check_game_password, list_saved_games
from game_management import load_game_data
from gm_console import build_public_state
from admin_helpers import create_delete_game_modal, create_delete_game_button
from gm_console_ui import create_projector_html

app = Flask(__name__)
app.register_blueprint(admin_bp)
app.register_blueprint(team_bp)
app.register_blueprint(team_order_bp)

# Configure for production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
# Disable static file caching during development and force template reloads
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = 6 * 60 * 60  # Cover a full live event

# Add cache-busting headers for static files
@app.after_request
def after_request(response):
    # Add cache-busting headers for static files
    if request.endpoint and 'static' in request.endpoint:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Removed old demo timer maximize route with inline styles

@app.route("/health")
def health_check():
    """Health check endpoint for production monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "Stabsspel",
        "version": "1.1",
        "timestamp": time.time()
    })

@app.route("/test_css")
def test_css():
    return '''
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS Refaktorering Test</title>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/app.css">
    <link rel="stylesheet" href="/static/print.css" media="print">
</head>
<body>
    <div class="container">
        <div class="page-header">
            <h1>CSS Refaktorering Test</h1>
            <p class="page-subtitle">Testar den nya konsoliderade CSS-strukturen</p>
        </div>

        <div class="section-header">
            <h3>Knappar</h3>
        </div>
        
        <div class="card">
            <h4>Knappvarianter</h4>
            <div class="flex-wrap">
                <button class="primary">Primär</button>
                <button class="success">Framgång</button>
                <button class="warning">Varning</button>
                <button class="danger">Farlig</button>
                <button class="secondary">Sekundär</button>
                <button class="info">Info</button>
                <button class="ghost">Transparent</button>
            </div>
            
            <h4 class="mt-4">Knappstorlekar</h4>
            <div class="flex-wrap">
                <button class="primary sm">Liten</button>
                <button class="primary">Normal</button>
                <button class="primary lg">Stor</button>
            </div>
        </div>

        <div class="section-header">
            <h3>Badges</h3>
        </div>
        
        <div class="card">
            <div class="flex-wrap">
                <button class="success sm">Framgång</button>
                <button class="warning sm">Varning</button>
                <button class="danger sm">Farlig</button>
                <button class="secondary sm">Dämpad</button>
            </div>
        </div>

        <div class="section-header">
            <h3>Team-komponenter</h3>
        </div>
        
        <div class="card">
            <div class="flex-wrap">
                <div class="team alfa">
                    <span class="team-indicator alfa"></span>
                    Alfa
                </div>
                <div class="team bravo">
                    <span class="team-indicator bravo"></span>
                    Bravo
                </div>
                <div class="team stt">
                    <span class="team-indicator stt"></span>
                    STT
                </div>
                <div class="team fm">
                    <span class="team-indicator fm"></span>
                    FM
                </div>
            </div>
        </div>

        <div class="section-header">
            <h3>Timer</h3>
        </div>
        
        <div class="timer">
            <h2>Tid kvar</h2>
            <div class="timer-display">12:34:56</div>
        </div>

        <div class="section-header">
            <h3>Formulär</h3>
        </div>
        
        <div class="card">
            <form>
                <div>
                    <label>Namn</label>
                    <input type="text" placeholder="Ange namn">
                </div>
                
                <div>
                    <label>E-post</label>
                    <input type="email" placeholder="ange@email.se">
                </div>
                
                <div>
                    <label>Meddelande</label>
                    <textarea rows="4" placeholder="Skriv ditt meddelande"></textarea>
                </div>
            </form>
        </div>

        <div class="section-header">
            <h3>Notifikationer</h3>
        </div>
        
        <div class="notification success">
            Detta är en framgångsnotifikation
        </div>
        
        <div class="notification warning">
            Detta är en varningsnotifikation
        </div>
        
        <div class="notification error">
            Detta är en felnotifikation
        </div>
        
        <div class="notification info">
            Detta är en informationsnotifikation
        </div>

        <div class="section-header">
            <h3>Tabeller</h3>
        </div>
        
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Team</th>
                        <th>Poäng</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <div class="team alfa">
                                <span class="team-indicator alfa"></span>
                                Alfa
                            </div>
                        </td>
                        <td>150</td>
                        <td><button class="success sm">Aktiv</button></td>
                    </tr>
                    <tr>
                        <td>
                            <div class="team bravo">
                                <span class="team-indicator bravo"></span>
                                Bravo
                            </div>
                        </td>
                        <td>120</td>
                        <td><button class="warning sm">Väntar</button></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="section-header">
            <h3>Utility klasser</h3>
        </div>
        
        <div class="card">
            <h4>Text alignment</h4>
            <p class="text-left">Vänsterjusterad text</p>
            <p class="text-center">Centrerad text</p>
            <p class="text-right">Högerjusterad text</p>
            
            <h4 class="mt-4">Text colors</h4>
            <p class="text-success">Grön text</p>
            <p class="text-danger">Röd text</p>
            <p class="text-warning">Gul text</p>
            <p class="text-info">Blå text</p>
            <p class="text-muted">Dämpad text</p>
            
            <h4 class="mt-4">Spacing</h4>
            <div class="mb-1">Margin bottom 1</div>
            <div class="mb-2">Margin bottom 2</div>
            <div class="mb-3">Margin bottom 3</div>
            <div class="mt-4">Margin top 4</div>
        </div>

        <div class="section-header">
            <h3>Kortvarianter</h3>
        </div>
        
        <div class="card elevated">
            <h4>Upphöjt kort</h4>
            <p>Detta kort har en större skugga.</p>
        </div>
        
        <div class="card interactive">
            <h4>Interaktivt kort</h4>
            <p>Detta kort har hover-effekter.</p>
        </div>

        <div class="section-header">
            <h3>Print test</h3>
        </div>
        
        <div class="card">
            <p>Tryck Ctrl+P för att testa utskriftsstilarna.</p>
            <p>Alla knappar och interaktiva element ska döljas vid utskrift.</p>
        </div>
    </div>
</body>
</html>
    '''

def _home_game_row(game_data):
    spel_id = str(game_data.get("id", "") or "")
    datum = str(game_data.get("datum", "") or "")
    plats = str(game_data.get("plats", "") or "")
    label = f"{datum} – {plats}".strip(" –")
    runda = game_data.get("runda", 1)
    fas = str(game_data.get("fas", "Orderfas") or "Orderfas")
    avslutat = bool(game_data.get("avslutat", False))
    teams = [str(name) for name in game_data.get("lag", []) if name]
    if avslutat:
        status = '<span class="home-game-state">Avslutat</span>'
    else:
        status = (
            '<span class="home-game-state is-active">Pågår</span>'
            f'<span>Runda {escape(str(runda))} · {escape(fas)}</span>'
        )
    finished_class = " is-finished" if avslutat else ""
    teams_html = ""
    if teams:
        teams_html = (
            f'<p class="home-game-teams">{escape(", ".join(teams))}</p>'
        )
    return f'''
        <article class="home-game{finished_class}" data-game-card-id="{escape(spel_id)}">
            <div class="home-game-info">
                <h3 class="home-game-title">{escape(label)}</h3>
                {teams_html}
            </div>
            <p class="home-game-status">{status}</p>
            <div class="home-game-actions">
                <a href="/admin/{escape(spel_id)}" class="primary">Öppna</a>
                <details class="home-mer">
                    <summary aria-label="Fler åtgärder för {escape(label)}">Mer</summary>
                    <div class="home-mer-menu">
                        <a href="/admin/download_game/{escape(spel_id)}" class="secondary sm">Ladda ner</a>
                        {create_delete_game_button(spel_id, label, "danger sm")}
                    </div>
                </details>
            </div>
        </article>
        '''


@app.route("/")
def startsida():
    games = list(list_saved_games())
    games.sort(key=lambda g: 1 if g.get("avslutat") else 0)
    spel_html = "".join(_home_game_row(game) for game in games)
    empty_hidden = " hidden" if spel_html else ""
    list_hidden = "" if spel_html else " hidden"

    return f'''
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stabsspelet - Krisledningssimulation</title>
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/app.css?v=29">
        <link rel="stylesheet" href="/static/print.css" media="print">
    </head>
    <body class="home-page">
        <header class="home-bar">
            <h1>Stabsspelet</h1>
            <div class="home-bar-actions">
                <a href="/admin?tab=upload" class="secondary">Ladda upp</a>
                <a href="/admin" class="primary">Starta nytt spel</a>
            </div>
        </header>
        <main class="home-main">
            <h2 class="home-heading">Öppna spel</h2>
            <div class="home-game-list"{list_hidden}>{spel_html}</div>
            <div class="home-empty"{empty_hidden}>
                <p>Inga sparade spel.</p>
                <a href="/admin" class="primary">Starta nytt spel</a>
            </div>
        </main>
        {create_delete_game_modal()}
    </body>
    </html>
    '''

@app.route("/teams/<int:num_players>")
def get_teams(num_players):
    teams = suggest_teams(num_players)
    return f"Antal spelare: {num_players}<br>Föreslagna lag: {', '.join(teams)}"

@app.route("/timer_window/<spel_id>")
def timer_window(spel_id):
    # Läs speldata
    try:
        with open(os.path.join(DATA_DIR, f"game_{spel_id}.json"), encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "Spel hittades inte", 404
    
    # Hämta URL-parametrar för tid och status
    from flask import request
    time_param = request.args.get('time', None)
    status_param = request.args.get('status', 'paused')
    
    # Konvertera tid från sekunder tillbaka till MM:SS format
    if time_param:
        try:
            total_seconds = int(time_param)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            initial_time = f"{minutes:02d}:{seconds:02d}"
            initial_seconds = total_seconds
        except ValueError:
            initial_time = "10:00"
            initial_seconds = 600
    else:
        initial_time = "10:00"
        initial_seconds = 600
    
    # Skapa timer HTML baserat på aktuell fas
    current_phase = data.get("current_phase", "order")
    if current_phase == "order":
        timer_html = f'''
            <div class="timer">
                <div class="margin-bottom-25">
                    <h2>⏰ ORDERFAS</h2>
                    <div id="timer" class="timer-display">{initial_time}</div>
                </div>
                <div class="timer-controls">
                    <button onclick="startTimer()" class="success">▶️ Starta</button>
                    <button onclick="pauseTimer()" class="warning">⏸️ Pausa</button>
                    <button onclick="resetTimer()" class="danger">🔄 Återställ</button>
                </div>
                <div class="timer-status">
                    <span id="status" class="status-badge">Status: {status_param.capitalize()}</span>
                </div>
            </div>
        '''
    elif current_phase == "diplomati":
        timer_html = f'''
            <div class="timer">
                <div class="margin-bottom-25">
                    <h2>⏰ DIPLOMATIFAS</h2>
                    <div id="timer" class="timer-display">{data.get("diplomatifas_min", 10)}:00</div>
                </div>
                <div class="timer-controls">
                    <button onclick="startTimer()" class="success">▶️ Starta</button>
                    <button onclick="pauseTimer()" class="warning">⏸️ Pausa</button>
                    <button onclick="resetTimer()" class="danger">🔄 Återställ</button>
                </div>
                <div class="timer-status">
                    <span id="status" class="status-badge">Status: {status_param.capitalize()}</span>
                </div>
            </div>
        '''
    else:
        timer_html = f'''
            <div class="timer">
                <div class="margin-bottom-25">
                    <h2>⏰ RESULTATFAS</h2>
                    <div id="timer" class="timer-display">05:00</div>
                </div>
                <div class="timer-controls">
                    <button onclick="startTimer()" class="success">▶️ Starta</button>
                    <button onclick="pauseTimer()" class="warning">⏸️ Pausa</button>
                    <button onclick="resetTimer()" class="danger">🔄 Återställ</button>
                </div>
                <div class="timer-status">
                    <span id="status" class="status-badge">Status: {status_param.capitalize()}</span>
                </div>
            </div>
        '''
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Timer - Spel {spel_id}</title>
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="0">
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/app.css?v=6">
    </head>
    <body class="timer-window">
        <div class="timer-container">
            {timer_html}
            
            <div class="margin-top-15">
                <button type="button" class="maximize-btn" onclick="toggleTimerMaximize()">⛶ Maximera</button>
                <button type="button" class="minimize-btn d-none" onclick="toggleTimerMaximize()">⛶ Minimera</button>
            </div>
        </div>

        <script>
            // Timer maximization functionality
            function toggleTimerMaximize() {{
                var timerContainer = document.querySelector('.timer-container');
                var maximizeBtn = document.querySelector('.maximize-btn');
                var minimizeBtn = document.querySelector('.minimize-btn');
                
                if (timerContainer.classList.contains('maximized')) {{
                    // Minimize timer
                    timerContainer.classList.remove('maximized');
                    maximizeBtn.style.display = 'inline-block';
                    minimizeBtn.style.display = 'none';
                }} else {{
                    // Maximize timer
                    timerContainer.classList.add('maximized');
                    maximizeBtn.style.display = 'none';
                    minimizeBtn.style.display = 'inline-block';
                }}
            }}
            
            // Keyboard shortcut for maximizing/minimizing timer (F11 key)
            document.addEventListener('keydown', function(event) {{
                if (event.key === 'F11') {{
                    event.preventDefault(); // Prevent browser fullscreen
                    event.stopPropagation();
                    toggleTimerMaximize();
                    return false;
                }}
            }});
            
            // Simple timer functionality
            let timeLeft = {initial_seconds};
            let timerId = null;
            let isRunning = {str(status_param == 'running').lower()};
            
            function startTimer() {{
                if (!isRunning) {{
                    isRunning = true;
                    timerId = setInterval(updateTimer, 1000);
                    document.getElementById('status').textContent = 'Status: Kör';
                    document.getElementById('status').className = 'status-badge';
                    document.getElementById('status').style.background = 'var(--c-success)';
                }}
            }}
            
            function pauseTimer() {{
                if (isRunning) {{
                    isRunning = false;
                    clearInterval(timerId);
                    document.getElementById('status').textContent = 'Status: Pausad';
                    document.getElementById('status').className = 'status-badge';
                    document.getElementById('status').style.background = 'var(--c-secondary)';
                }}
            }}
            
            function resetTimer() {{
                pauseTimer();
                timeLeft = {data.get("orderfas_min", 15) if current_phase == "order" else data.get("diplomatifas_min", 10) if current_phase == "diplomati" else 5} * 60;
                updateDisplay();
                document.getElementById('status').textContent = 'Status: Pausad';
                document.getElementById('status').className = 'status-badge';
                document.getElementById('status').style.background = 'var(--c-secondary)';
            }}
            
            function updateTimer() {{
                if (timeLeft > 0) {{
                    timeLeft--;
                    updateDisplay();
                }} else {{
                    pauseTimer();
                    document.getElementById('status').textContent = 'Status: Slut';
                    document.getElementById('status').className = 'status-badge';
                    document.getElementById('status').style.background = 'var(--c-danger)';
                    // Spela ljud om det finns
                    var audio = new Audio('/static/alarm.mp3');
                    audio.play().catch(e => console.log('Kunde inte spela ljud:', e));
                }}
            }}
            
            function updateDisplay() {{
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                document.getElementById('timer').textContent = `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
            }}
            
            // Initiera display
            updateDisplay();
            
            // Starta timer automatiskt om den var igång
            if (isRunning) {{
                // Sätt status till "Kör" och grön färg
                document.getElementById('status').textContent = 'Status: Kör';
                document.getElementById('status').style.background = '#27ae60';
                // Starta timern direkt (utan att kolla isRunning)
                timerId = setInterval(updateTimer, 1000);
            }}
            
            // Automatiskt maximera timern när fönstret öppnas
            window.addEventListener('load', function() {{
                setTimeout(function() {{
                    toggleTimerMaximize();
                }}, 100);
            }});
        </script>
    </body>
    </html>
    '''
    
    # Skapa response med anti-caching headers
    response = make_response(html_content)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/spelarskarm/<spel_id>")
def player_display(spel_id):
    """Room projector: round, phase, time, public HP. No GM chrome."""
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    response = make_response(create_projector_html(spel_id, data))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/spelarskarm/<spel_id>/live")
def player_display_live(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Spelet hittades inte"}), 404
    return jsonify({"success": True, "state": build_public_state(data)})


if __name__ == "__main__":
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    # Force debug True locally to enable auto-reload unless explicitly disabled
    debug_env = os.environ.get('FLASK_DEBUG') or os.environ.get('FLASK_ENV')
    debug = True if (debug_env is None or debug_env in ['1', 'true', 'development']) else False
    
    # Ensure secret key is set for production
    if not app.config['SECRET_KEY'] or app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
        if os.environ.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
        else:
            print("⚠️  WARNING: No SECRET_KEY set. Using development key.")
    
    print(f"🚀 Starting Stabsspelet on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'production')}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
