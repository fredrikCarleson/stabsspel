from flask import Blueprint, send_from_directory, request, make_response
from markupsafe import Markup
import os
import qrcode
import io
import base64
from models import DATA_DIR, load_game_data, get_team_by_token, active_teams, absent_optional_teams_mentioned
from orderkort import generate_team_orderkort_html

team_bp = Blueprint('team', __name__)

def generate_qr_code(data):
    """Generate QR code as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

@team_bp.route("/team/<spel_id>/<lag_namn>")
def team_beskrivning(spel_id, lag_namn):
    # Load game data first so inactive teams cannot be opened.
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    roster = active_teams(data)
    if lag_namn not in roster:
        return "Laget ingår inte i det här spelet.", 404

    desc_dir = os.path.join("teambeskrivning")
    txt_path = os.path.join(desc_dir, f"{lag_namn.lower()}.txt")
    img_path = os.path.join(desc_dir, f"{lag_namn.lower()}.jpg")
    
    team_token = None
    team_order_url = None
    qr_code_html = ""
    
    if "team_tokens" in data:
        team_token = data["team_tokens"].get(lag_namn)
        if team_token:
            team_order_url = f"/team/{spel_id}/{team_token}/enter_order"
            # Generate QR code for the team order URL
            full_url = request.url_root.rstrip('/') + team_order_url
            qr_code_data = generate_qr_code(full_url)
            qr_code_html = f'''
            <section class="brief-qr">
                <h2>Ange order</h2>
                <div class="brief-qr-row">
                    <img src="{qr_code_data}" alt="QR-kod till orderformulär" class="brief-qr-image">
                    <div class="brief-qr-info">
                        <p class="brief-qr-help">Skanna koden eller öppna länken på telefonen.</p>
                        <a class="brief-qr-link" href="{team_order_url}">{full_url}</a>
                    </div>
                </div>
            </section>
            '''
    
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
        missing = absent_optional_teams_mentioned(text, roster)
        if missing:
            names = ", ".join(missing)
            text_html = (
                f'<p class="brief-banner">I det här spelet ingår inte: {names}. '
                "Tolka hänvisningar till dem som aktörer i spelvärlden som spelledaren "
                "kan spela, inte som lag vid ett bord.</p>"
                + text_html
            )
    else:
        text_html = "<i>Ingen beskrivning hittades för detta lag.</i>"
    # Bild om den finns, placeras längst ner och på egen sida vid utskrift
    img_html = ""
    if os.path.exists(img_path):
        img_html = f'''
        <div class="bildsida">
            <img src="/teambeskrivning/{lag_namn.lower()}.jpg" alt="{lag_namn}" class="team-image-print">
        </div>
        '''
    html_content = f'''
        <!DOCTYPE html>
        <html lang="sv">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
            <meta http-equiv="Pragma" content="no-cache">
            <meta http-equiv="Expires" content="0">
            <title>{lag_namn}</title>
            <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="/static/app.css?v=47">
            <link rel="stylesheet" href="/static/print.css">
        </head>
        <body class="brief-page">
        <div class="brief-wrap">
        <div class="brief-toolbar no-print">
            <button type="button" onclick="window.print()" class="secondary">Skriv ut</button>
            <a href="/team/{spel_id}/{lag_namn}/orderkort" target="_blank" class="secondary">
                Skriv ut orderkort
            </a>
        </div>
        <header class="brief-head">
            <p class="brief-kicker">Lagbeskrivning</p>
            <h1>{lag_namn}</h1>
        </header>
        {qr_code_html}
        <div class="brief-body">{Markup(text_html)}</div>
        {img_html}
        </div>
        </body>
        </html>
    '''
    
    # Skapa response med anti-caching headers
    response = make_response(html_content)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@team_bp.route("/team/<spel_id>/<lag_namn>/orderkort")
def team_orderkort(spel_id, lag_namn):
    """
    Generera orderkort för ett specifikt team för alla rundor.
    """
    return generate_team_orderkort_html(spel_id, lag_namn)

@team_bp.route("/teambeskrivning/<filename>")
def team_bild(filename):
    return send_from_directory("teambeskrivning", filename)
