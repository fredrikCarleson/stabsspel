from flask import Blueprint, send_from_directory, request, make_response
from markupsafe import Markup
import os
import qrcode
import io
import base64
from models import DATA_DIR, load_game_data, get_team_by_token
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
    # Sökväg till beskrivning och bild
    desc_dir = os.path.join("teambeskrivning")
    txt_path = os.path.join(desc_dir, f"{lag_namn.lower()}.txt")
    img_path = os.path.join(desc_dir, f"{lag_namn.lower()}.jpg")
    
    # Load game data to get team token
    data = load_game_data(spel_id)
    team_token = None
    team_order_url = None
    qr_code_html = ""
    
    if data and "team_tokens" in data:
        team_token = data["team_tokens"].get(lag_namn)
        if team_token:
            team_order_url = f"/team/{spel_id}/{team_token}/enter_order"
            # Generate QR code for the team order URL
            full_url = request.url_root.rstrip('/') + team_order_url
            qr_code_data = generate_qr_code(full_url)
            qr_code_html = f'''
            <div style="text-align: center; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3 style="margin-bottom: 15px; color: #2c3e50;">📱 Ange Order</h3>
                <div style="display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;">
                    <div>
                        <img src="{qr_code_data}" alt="QR Code" style="width: 120px; height: 120px; border: 1px solid #ddd; border-radius: 8px;">
                    </div>
                    <div style="text-align: left;">
                        <p style="margin: 0 0 10px 0; font-weight: 600; color: #2c3e50;">Skanna QR-koden eller gå till:</p>
                        <p style="margin: 0; font-family: monospace; font-size: 14px; color: #2c3e50; word-break: break-all; background: white; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            {full_url}
                        </p>
                    </div>
                </div>
            </div>
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
    html_content = f'''
        <!DOCTYPE html>
        <html lang="sv">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
            <meta http-equiv="Pragma" content="no-cache">
            <meta http-equiv="Expires" content="0">
            <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="/static/design-system.css">
            <link rel="stylesheet" href="/static/style.css">
            <link rel="stylesheet" href="/static/admin.css">
        </head>
        <body>
        <div class="container">
        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <button onclick="window.print()" class="btn is-secondary">Skriv ut</button>
            <a href="/team/{spel_id}/{lag_namn}/orderkort" target="_blank" class="btn is-info">
                Skriv ut orderkort
            </a>
        </div>
        <h1>{lag_namn}</h1>
        {qr_code_html}
        <div>{Markup(text_html)}</div>
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