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
from admin_routes import admin_bp
from team_routes import team_bp
from team_order_routes import team_order_bp
from models import suggest_teams, DATA_DIR, check_game_password, list_saved_games

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

@app.route("/")
def startsida():
    spel_html = ''
    for game_data in list_saved_games():
        runda = game_data.get("runda", 1)
        fas = game_data.get("fas", "Orderfas")
        avslutat = game_data.get("avslutat", False)

        if avslutat:
            status = "Avslutat"
            status_class = "status-finished"
        else:
            status = f"Runda {runda} – {fas}"
            status_class = "status-active"

        team_indicators = ""
        for team_name in game_data.get("lag", [])[:4]:
            slug = str(team_name).lower()
            team_indicators += f'<span class="team-indicator team-{slug}"></span>'

        spel_html += f'''
        <div class="game-card">
            <div class="game-info">
                <h3>{game_data.get("datum", "")} – {game_data.get("plats", "")}</h3>
                <p class="game-id">ID: {game_data.get("id", "")}</p>
                <div class="game-status">
                    <span class="status-badge {status_class}">{status}</span>
                    <div class="team-indicators">{team_indicators}</div>
                </div>
            </div>
            <div class="game-actions">
                <a href="/admin/{game_data.get("id", "")}" class="primary">Öppna (kräver lösenord)</a>
                <a href="/admin/download_game/{game_data.get("id", "")}" class="secondary">💾 Ladda ner</a>
                <form method="post" action="/admin/delete_game/{game_data.get("id", "")}" class="d-inline" onsubmit="return confirm('Är du säker på att du vill ta bort detta spel permanent?');">
                    <button type="submit" class="danger">Ta bort</button>
                </form>
            </div>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stabsspelet - Krisledningssimulation</title>
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/app.css">
        <link rel="stylesheet" href="/static/print.css" media="print">
        <style>
            /* Hero section with enhanced background */
            .hero-section {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 100px 20px;
                text-align: center;
                position: relative;
                overflow: hidden;
                min-height: 60vh;
                display: flex;
                align-items: center;
            }}
            
            /* Subtle background illustration */
            .hero-section::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/><rect width="100" height="100" fill="url(%23dots)"/></svg>');
                opacity: 0.4;
            }}
            
            /* Game pieces illustration */
            .hero-section::after {{
                content: '';
                position: absolute;
                top: 20%;
                right: 10%;
                width: 200px;
                height: 200px;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="2"/><circle cx="50" cy="50" r="25" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/><circle cx="50" cy="50" r="10" fill="rgba(255,255,255,0.1)"/></svg>');
                opacity: 0.6;
                animation: float 6s ease-in-out infinite;
            }}
            
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
                50% {{ transform: translateY(-20px) rotate(180deg); }}
            }}
            
            .hero-content {{
                position: relative;
                z-index: 2;
                max-width: 800px;
                margin: 0 auto;
            }}
            
            .hero-title {{
                font-size: 4rem;
                font-weight: 700;
                margin-bottom: 20px;
                text-shadow: 0 4px 8px rgba(0,0,0,0.3);
                letter-spacing: -1px;
            }}
            
            .hero-subtitle {{
                font-size: 1.4rem;
                font-weight: 300;
                margin-bottom: 50px;
                opacity: 0.9;
                line-height: 1.6;
            }}
            
            
            .description-section {{
                padding: 80px 20px;
                background: #f8f9fa;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            
            .features-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin: 60px 0;
            }}
            
            .feature-card {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                border-left: 4px solid #667eea;
            }}
            
            .feature-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.15);
            }}
            
            .feature-icon {{
                font-size: 3rem;
                margin-bottom: 20px;
                color: #667eea;
            }}
            
            .feature-title {{
                font-size: 1.4rem;
                font-weight: 600;
                margin-bottom: 15px;
                color: #2c3e50;
            }}
            
            .feature-description {{
                color: #6c757d;
                line-height: 1.6;
            }}
            
            .games-section {{
                padding: 80px 20px;
                background: white;
            }}
            
            .section-title {{
                text-align: center;
                font-size: 2.5rem;
                font-weight: 600;
                margin-bottom: 50px;
                color: #2c3e50;
            }}
            
            .games-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 25px;
                margin-top: 40px;
            }}
            
            /* Enhanced game cards with team colors */
            .game-card {{
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 15px;
                padding: 25px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                position: relative;
                overflow: hidden;
            }}
            
            .game-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #3498db, #2ecc71, #e74c3c, #f39c12);
                opacity: 0.8;
            }}
            
            .game-card:hover {{
                border-color: #667eea;
                box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
                transform: translateY(-3px);
            }}
            
            .game-info h3 {{
                margin: 0 0 10px 0;
                color: #2c3e50;
                font-size: 1.3rem;
                font-weight: 600;
            }}
            
            .game-id {{
                color: #6c757d;
                font-size: 0.9rem;
                margin: 0 0 15px 0;
                font-family: 'Courier New', monospace;
                background: #f8f9fa;
                padding: 5px 10px;
                border-radius: 5px;
                display: inline-block;
            }}
            
            .game-actions {{
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }}
            
            .btn {{
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                font-size: 0.9rem;
            }}
            
            .btn-primary {{
                background: #667eea;
                color: white;
            }}
            
            .btn-primary:hover {{
                background: #5a6fd8;
                transform: translateY(-1px);
            }}
            
            .btn-danger {{
                background: #e74c3c;
                color: white;
            }}
            
            .btn-danger:hover {{
                background: #c0392b;
                transform: translateY(-1px);
            }}
            
            .no-games {{
                text-align: center;
                padding: 60px 20px;
                color: #6c757d;
                font-size: 1.1rem;
                background: #f8f9fa;
                border-radius: 15px;
                border: 2px dashed #dee2e6;
            }}
            
            /* Game status and team indicators */
            .game-status {{
                margin-top: 15px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 10px;
            }}
            
            .status-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .status-active {{
                background: #27ae60;
                color: white;
            }}
            
            .status-finished {{
                background: #6c757d;
                color: white;
            }}
            
            .team-indicators {{
                display: flex;
                gap: 6px;
                align-items: center;
            }}
            
            .team-indicator {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            }}
            
            /* Team color indicators */
            .team-alfa {{ background: #3498db; }}
            .team-bravo {{ background: #2ecc71; }}
            .team-charlie {{ background: #e74c3c; }}
            .team-delta {{ background: #f39c12; }}
            .team-echo {{ background: #9b59b6; }}
            .team-foxtrot {{ background: #1abc9c; }}
            .team-golf {{ background: #34495e; }}
            .team-hotel {{ background: #e67e22; }}
            .team-india {{ background: #16a085; }}
            .team-juliett {{ background: #8e44ad; }}
            .team-kilo {{ background: #27ae60; }}
            .team-lima {{ background: #d35400; }}
            .team-mike {{ background: #c0392b; }}
            .team-november {{ background: #2980b9; }}
            .team-oscar {{ background: #f1c40f; }}
            .team-papa {{ background: #e91e63; }}
            .team-quebec {{ background: #00bcd4; }}
            .team-romeo {{ background: #795548; }}
            .team-sierra {{ background: #607d8b; }}
            .team-tango {{ background: #ff9800; }}
            .team-uniform {{ background: #4caf50; }}
            .team-victor {{ background: #2196f3; }}
            .team-whiskey {{ background: #ff5722; }}
            .team-xray {{ background: #9c27b0; }}
            .team-yankee {{ background: #00bcd4; }}
            .team-zulu {{ background: #ffc107; }}
            
            @media (max-width: 768px) {{
                .hero-title {{
                    font-size: 2.5rem;
                }}
                
                .hero-subtitle {{
                    font-size: 1.1rem;
                }}
                
                
                .features-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .games-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .hero-section::after {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="hero-section">
            <div class="hero-content">
                <h1 class="hero-title">Stabsspelet v1</h1>
                <p class="hero-subtitle">En avancerad krisledningssimulation för att träna beslutsfattande under press</p>
                <a href="/admin" class="primary lg">🎮 Starta nytt spel</a>
            </div>
        </div>
        
        <div class="description-section">
            <div class="container">
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">⚡</div>
                        <h3 class="feature-title">Snabb beslutsfattande</h3>
                        <p class="feature-description">Träna dig på att fatta kritiska beslut under tidspress och med begränsad information. Varje runda representerar en kvartal med nya utmaningar.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">👥</div>
                        <h3 class="feature-title">Team-samarbete</h3>
                        <p class="feature-description">Spela som olika team med unika roller och ansvarsområden. Koordinera era insatser för att hantera krisen effektivt.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <h3 class="feature-title">Handlingspoäng-system</h3>
                        <p class="feature-description">Hantera era handlingspoäng strategiskt. Varje beslut kostar poäng - välj klokt för att maximera er påverkan.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">⏰</div>
                        <h3 class="feature-title">Tidsbegränsade faser</h3>
                        <p class="feature-description">Arbeta under press med tidsbegränsade faser: Orderfas, Diplomatifas och Resultatfas. Varje fas har sina egna utmaningar.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🎯</div>
                        <h3 class="feature-title">Målbaserat spel</h3>
                        <p class="feature-description">Varje team har specifika mål och uppgifter att slutföra. Samarbeta eller konkurrera för att uppnå era objektiv.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📈</div>
                        <h3 class="feature-title">Progressiv svårighet</h3>
                        <p class="feature-description">Spelet blir allt mer utmanande över fyra rundor. Hantera ökande komplexitet och oförutsägbara händelser.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="games-section">
            <div class="container">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                    <h2 class="section-title">Befintliga spel</h2>
                    <a href="/admin/upload_game" class="secondary" style="padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 6px;">
                        📤 Ladda upp spel
                    </a>
                </div>
                {f'<div class="games-grid">{spel_html}</div>' if spel_html else '<div class="no-games">Inga aktiva spel hittades. Skapa ditt första spel för att komma igång!</div>'}
            </div>
        </div>
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
