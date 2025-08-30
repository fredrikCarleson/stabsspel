from flask import Blueprint, send_from_directory
from markupsafe import Markup
import os
from models import DATA_DIR
from orderkort import generate_team_orderkort_html

team_bp = Blueprint('team', __name__)

@team_bp.route("/team/<spel_id>/<lag_namn>")
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
        <link rel="stylesheet" href="/static/style.css">
        <div class="container">
        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <button onclick="window.print()">Skriv ut</button>
            <a href="/team/{spel_id}/{lag_namn}/orderkort" target="_blank">
                <button>Skriv ut orderkort</button>
            </a>
        </div>
        <h1>{lag_namn}</h1>
        <div>{Markup(text_html)}</div>
        {img_html}
        </div>
    '''

@team_bp.route("/team/<spel_id>/<lag_namn>/orderkort")
def team_orderkort(spel_id, lag_namn):
    """
    Generera orderkort för ett specifikt team för alla rundor.
    """
    return generate_team_orderkort_html(spel_id, lag_namn)

@team_bp.route("/teambeskrivning/<filename>")
def team_bild(filename):
    return send_from_directory("teambeskrivning", filename) 