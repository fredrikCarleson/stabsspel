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
        spel_html += f'<li><a href="/admin/{s["id"]}">{s["datum"]} – {s["plats"]} (ID: {s["id"]})</a> '
        spel_html += f'<form method="post" action="/delete_game/{s["id"]}" style="display:inline;" onsubmit="return confirm(\'Ta bort spelet permanent?\');">'
        spel_html += '<button type="submit">Ta bort</button></form></li>'
    return f'''
        <link rel="stylesheet" href="/static/style.css">
        <div class="container">
        <h1>Stabsspelet</h1>
        <a href="/admin"><button>Skapa nytt spel</button></a>
        <h2>Befintliga spel</h2>
        <ul>
            {spel_html}
        </ul>
        </div>
    '''

@app.route("/teams/<int:num_players>")
def get_teams(num_players):
    teams = suggest_teams(num_players)
    return f"Antal spelare: {num_players}<br>Föreslagna lag: {', '.join(teams)}"

if __name__ == "__main__":
    app.run(debug=True)