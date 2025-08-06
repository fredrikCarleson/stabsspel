from flask import Flask
from admin_routes import admin_bp
from team_routes import team_bp
from models import suggest_teams, DATA_DIR
import os
import json

app = Flask(__name__)
app.register_blueprint(admin_bp)
app.register_blueprint(team_bp)

@app.route("/")
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
        spel_html += f'''
        <div class="game-card">
            <div class="game-info">
                <h3>{s["datum"]} – {s["plats"]}</h3>
                <p class="game-id">ID: {s["id"]}</p>
            </div>
            <div class="game-actions">
                <a href="/admin/{s["id"]}" class="btn btn-primary">Öppna</a>
                <form method="post" action="/delete_game/{s["id"]}" style="display:inline;" onsubmit="return confirm('Är du säker på att du vill ta bort detta spel permanent?');">
                    <button type="submit" class="btn btn-danger">Ta bort</button>
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
        <link rel="stylesheet" href="/static/style.css">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            .hero-section {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 80px 20px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .hero-section::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
                opacity: 0.3;
            }}
            
            .hero-content {{
                position: relative;
                z-index: 2;
                max-width: 800px;
                margin: 0 auto;
            }}
            
            .hero-title {{
                font-size: 3.5rem;
                font-weight: 700;
                margin-bottom: 20px;
                text-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }}
            
            .hero-subtitle {{
                font-size: 1.3rem;
                font-weight: 300;
                margin-bottom: 40px;
                opacity: 0.9;
            }}
            
            .cta-button {{
                display: inline-block;
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                color: white;
                padding: 18px 36px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 600;
                font-size: 1.1rem;
                transition: all 0.3s ease;
                box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
                border: none;
                cursor: pointer;
            }}
            
            .cta-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 12px 35px rgba(255, 107, 107, 0.4);
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
            }}
            
            .feature-card:hover {{
                transform: translateY(-5px);
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
                gap: 20px;
                margin-top: 40px;
            }}
            
            .game-card {{
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 25px;
                transition: all 0.3s ease;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }}
            
            .game-card:hover {{
                border-color: #667eea;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
                transform: translateY(-2px);
            }}
            
            .game-info h3 {{
                margin: 0 0 10px 0;
                color: #2c3e50;
                font-size: 1.2rem;
                font-weight: 600;
            }}
            
            .game-id {{
                color: #6c757d;
                font-size: 0.9rem;
                margin: 0;
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
            }}
            
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
            }}
        </style>
    </head>
    <body>
        <div class="hero-section">
            <div class="hero-content">
                <h1 class="hero-title">Stabsspelet</h1>
                <p class="hero-subtitle">En avancerad krisledningssimulation för att träna beslutsfattande under press</p>
                <a href="/admin" class="cta-button">🎮 Starta nytt spel</a>
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
                <h2 class="section-title">Befintliga spel</h2>
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

if __name__ == "__main__":
    app.run(debug=True)