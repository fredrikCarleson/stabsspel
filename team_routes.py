from flask import Blueprint, send_from_directory
from markupsafe import Markup
import os
from models import DATA_DIR

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

@team_bp.route("/teambeskrivning/<filename>")
def team_bild(filename):
    return send_from_directory("teambeskrivning", filename) 