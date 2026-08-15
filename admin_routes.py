from flask import Blueprint, request, redirect, url_for, jsonify, render_template_string, make_response, session
from markupsafe import Markup
import os
import json
import time
from models import (
    skapa_nytt_spel, suggest_teams, get_fas_minutes, save_game_data, get_next_fas,
    avsluta_aktuell_fas, add_fashistorik_entry, avsluta_spel, init_fashistorik_v2, MAX_RUNDA, DATA_DIR, TEAMS, AKTIVITETSKORT, BACKLOG,
    check_game_password, is_game_session_valid, create_game_session, refresh_game_session, get_phase_timer, is_declaration_period,
    list_saved_games, clone_backlog_for_teams
)
from game_management import delete_game, nollstall_regeringsstod, load_game_data, save_checkbox_state, get_checkbox_state
from orderkort import generate_orderkort_html, get_available_rounds
from admin_helpers import add_no_cache_headers, create_team_info_js, create_compact_header, create_action_buttons, create_script_references, create_timer_controls, create_time_adjustment_modal
from gm_console import (
    add_timer_seconds,
    adjust_hp,
    apply_new_round,
    apply_next_phase,
    apply_previous_phase,
    apply_undo,
    auto_submit_unsaved_orders,
    end_game,
    push_undo,
    reset_timer_fields,
    set_regeringsstod,
    transfer_hp,
)
from gm_console_ui import create_gm_console_html

admin_bp = Blueprint('admin', __name__)

PUBLIC_ADMIN_ENDPOINTS = {
    "admin.admin_start",
    "admin.admin_panel",
    "admin.upload_game",
}

def check_admin_session(spel_id):
    """Kontrollera om admin har giltig session för spelet"""
    session_key = f"game_session_{spel_id}"
    return is_game_session_valid(spel_id, session.get(session_key))


@admin_bp.before_request
def require_admin_session_for_game_routes():
    """Block unauthenticated mutations and data leaks for a specific game."""
    if request.endpoint in PUBLIC_ADMIN_ENDPOINTS or request.endpoint is None:
        return None
    spel_id = (request.view_args or {}).get("spel_id")
    if not spel_id:
        return None
    if load_game_data(spel_id) is None:
        return None
    if check_admin_session(spel_id):
        session_key = f"game_session_{spel_id}"
        session[session_key] = refresh_game_session(session.get(session_key))
        session.permanent = True
        return None
    wants_json = (
        request.is_json
        or request.path.endswith("/save_checkbox")
        or request.path.endswith("/checklist_status")
    )
    if wants_json:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))

def create_declaration_warning(runda):
    """Create warning HTML for declaration period (runda 3)"""
    if is_declaration_period(runda):
        return f'''
        <div class="notification warning">
            <div class="notification-icon">⚠️</div>
            <div class="notification-content">
                <strong>Deklarationstider (April-Juni)</strong>
                <p>Under denna runda är det <strong>absolut förbjudet</strong> för STT att produktionssätta något nytt. 
                Informera STT om denna begränsning och att de måste planera sina leveranser därefter.</p>
            </div>
        </div>
        '''
    return ""

# ============================================================================
# HJÄLPFUNKTIONER
# ============================================================================

def generate_order_view_html(spel_id, team_name, team_orders, data):
    """Generera HTML för att visa en inskickad order"""
    from datetime import datetime
    
    order_data = team_orders.get("orders", {})
    activities = order_data.get("activities", [])
    submitted_at = team_orders.get("submitted_at", 0)
    submitted_time = datetime.fromtimestamp(submitted_at).strftime("%Y-%m-%d %H:%M:%S") if submitted_at > 0 else "Okänd"
    
    activities_html = ""
    total_hp = 0
    
    for i, activity in enumerate(activities, 1):
        hp = activity.get("hp", 0)
        total_hp += hp
        
        # Get affected teams
        paverkar = activity.get('paverkar', [])
        paverkar_text = ', '.join(paverkar) if paverkar else 'Ingen'
        
        # Determine activity type icon and color
        typ = activity.get('typ', 'bygga')
        typ_icon = '🔨' if typ == 'bygga' else '💥'
        typ_color = '#28a745' if typ == 'bygga' else '#dc3545'
        
        # Determine target area
        malomrade = activity.get('malomrade', 'eget')
        malomrade_text = 'Eget mål' if malomrade == 'eget' else 'Annat mål'
        malomrade_icon = '🎯' if malomrade == 'eget' else '🌐'
        
        activities_html += f'''
        <div class="activity-card">
            <div class="activity-card-header">
                <div class="activity-number">
                    <span class="activity-badge">{i}</span>
                </div>
                <div class="activity-hp">
                    <span class="hp-badge">{hp} HP</span>
                </div>
            </div>
            
            <div class="activity-card-body">
                <div class="activity-main">
                    <h4 class="activity-title">{activity.get('aktivitet', 'Ingen aktivitet angiven')}</h4>
                    <p class="activity-purpose">{activity.get('syfte', 'Inget syfte angivet')}</p>
                </div>
                
                <div class="activity-details">
                    <div class="detail-item">
                        <div class="detail-icon">{malomrade_icon}</div>
                        <div class="detail-content">
                            <div class="detail-label">Målområde</div>
                            <div class="detail-value">{malomrade_text}</div>
                        </div>
                    </div>
                    
                    <div class="detail-item">
                        <div class="detail-icon" style="color: {typ_color}">{typ_icon}</div>
                        <div class="detail-content">
                            <div class="detail-label">Typ</div>
                            <div class="detail-value">{'Bygga/Förstärka' if typ == 'bygga' else 'Förstöra/Störa'}</div>
                        </div>
                    </div>
                    
                    <div class="detail-item">
                        <div class="detail-icon">👥</div>
                        <div class="detail-content">
                            <div class="detail-label">Påverkar</div>
                            <div class="detail-value">{paverkar_text}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Order - {team_name}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                color: #333;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 2rem;
            }}
            .order-info {{
                background: #e9ecef;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .order-info h3 {{
                margin: 0 0 10px 0;
                color: #2c3e50;
            }}
            .hp-summary {{
                background: #d4edda;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                border: 1px solid #c3e6cb;
            }}
            .hp-summary h4 {{
                margin: 0 0 10px 0;
                color: #155724;
            }}
            .back-button {{
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            .back-button:hover {{
                background: #5a6268;
            }}
            .activities-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .activity-card {{
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}
            .activity-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            }}
            .activity-card-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .activity-badge {{
                background: rgba(255,255,255,0.2);
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 14px;
            }}
            .hp-badge {{
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }}
            .activity-card-body {{
                padding: 20px;
            }}
            .activity-main {{
                margin-bottom: 20px;
            }}
            .activity-title {{
                margin: 0 0 10px 0;
                font-size: 18px;
                font-weight: 600;
                color: #2c3e50;
                line-height: 1.4;
            }}
            .activity-purpose {{
                margin: 0;
                color: #6c757d;
                font-size: 14px;
                line-height: 1.5;
            }}
            .activity-details {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 12px;
            }}
            .detail-item {{
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 0;
            }}
            .detail-icon {{
                font-size: 16px;
                width: 24px;
                text-align: center;
            }}
            .detail-content {{
                flex: 1;
            }}
            .detail-label {{
                font-size: 12px;
                color: #6c757d;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 2px;
            }}
            .detail-value {{
                font-size: 14px;
                color: #2c3e50;
                font-weight: 500;
            }}
            @media (max-width: 768px) {{
                .activities-grid {{
                    grid-template-columns: 1fr;
                }}
                .activity-card {{
                    margin-bottom: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/admin/{spel_id}" class="back-button">← Tillbaka till admin</a>
            
            <div class="header">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div>
                        <h1>📋 Order från {team_name}</h1>
                        <p>Spel: {data.get('id', 'Okänt')} | Runda: {data.get('runda', 'Okänt')} | Fas: {data.get('fas', 'Okänt')}</p>
                    </div>
                    {f'''
                    <div style="text-align: right;">
                        <button onclick="unlockForEditing()" class="unlock-button" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;">
                            🔓 Unlock for Editing
                        </button>
                        <small style="display: block; margin-top: 5px; color: rgba(255,255,255,0.8); font-size: 12px;">Available during Diplomacy phase</small>
                    </div>
                    ''' if data.get('fas') == 'Diplomatifas' else ''}
                </div>
            </div>
            
            <div class="order-info">
                <h3>📅 Orderinformation</h3>
                <p><strong>Inskickad:</strong> {submitted_time}</p>
                <p><strong>Antal aktiviteter:</strong> {len(activities)}</p>
            </div>
            
            <div class="hp-summary">
                <h4>💪 Handlingspoäng</h4>
                <p><strong>Totalt använt:</strong> {total_hp} HP</p>
            </div>
            
            <div class="activities">
                <h3 class="card-title mb-3">📝 Aktiviteter</h3>
                <div class="activities-grid">
                    {activities_html if activities_html else '<p class="text-muted text-center">Inga aktiviteter hittades</p>'}
                </div>
            </div>
        </div>
        
        <!-- Password Modal -->
        <div id="passwordModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); max-width: 400px; width: 90%;">
                <h3 style="margin: 0 0 20px 0; color: #2c3e50;">🔒 Unlock for Editing</h3>
                <p style="margin: 0 0 20px 0; color: #6c757d;">Enter the game password to edit this order:</p>
                <input type="password" id="gamePassword" placeholder="Game password" style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 20px; font-size: 16px;">
                <div style="text-align: right;">
                    <button onclick="closePasswordModal()" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 6px; margin-right: 10px; cursor: pointer;">Cancel</button>
                    <button onclick="verifyPasswordAndEdit()" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Unlock</button>
                </div>
                <div id="passwordError" style="color: #dc3545; margin-top: 10px; display: none;">❌ Incorrect password</div>
            </div>
        </div>
        
        <script>
            function unlockForEditing() {{
                document.getElementById('passwordModal').style.display = 'block';
                document.getElementById('gamePassword').focus();
            }}
            
            function closePasswordModal() {{
                document.getElementById('passwordModal').style.display = 'none';
                document.getElementById('gamePassword').value = '';
                document.getElementById('passwordError').style.display = 'none';
            }}
            
            function verifyPasswordAndEdit() {{
                const password = document.getElementById('gamePassword').value;
                if (!password) {{
                    document.getElementById('passwordError').style.display = 'block';
                    return;
                }}
                
                // Redirect to edit page with password
                window.location.href = `/admin/{spel_id}/edit_order/{team_name}?password=${{encodeURIComponent(password)}}`;
            }}
            
            // Close modal on Escape key
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    closePasswordModal();
                }}
            }});
            
            // Submit on Enter key
            document.getElementById('gamePassword').addEventListener('keydown', function(e) {{
                if (e.key === 'Enter') {{
                    verifyPasswordAndEdit();
                }}
            }});
        </script>
    </body>
    </html>
    '''





def create_orderfas_checklist(spel_id, data):
    """Skapa checklista för Orderfas (per-team orders med test-läge)"""
    checklist_html = f'''
    <div class="checklist-container border-left-success">
        <h3 class="checklist-title">📋 Checklista: Ordrar från alla team</h3>

        <!-- Auto-fill Orders utility -->
        <div class="test-mode-container">
            <div id="auto_fill_section" class="test-mode-section">
                <h4 class="test-mode-title">🚀 Auto-fyll Test Data</h4>
                <p class="test-mode-description">Fyll automatiskt alla teams order med test data för att prova ChatGPT-funktionen</p>
                <button onclick="autoFillOrders()" class="warning sm">🚀 Auto-fyll Alla Orders</button>
            </div>
        </div>

        <div class="checklist-content">
    '''

    # Check for submitted orders
    orders_key = f"orders_round_{data['runda']}"
    team_orders = data.get("team_orders", {}).get(orders_key, {})

    # Get team tokens for admin cheat links
    team_tokens = data.get("team_tokens", {})

    # Skapa rad för varje lag
    for i, lag in enumerate(data["lag"], 1):
        checkbox_id = f"order_check{i}"
        is_checked = get_checkbox_state(data, checkbox_id)
        checked_attr = "checked" if is_checked else ""

        # Finns det inskickade ordrar?
        has_submitted = lag in team_orders and team_orders[lag].get("final", False)
        submitted_text = " (Inskickad)" if has_submitted else " (Väntar)"

        view_order_link = f'''<a href="/admin/{spel_id}/view_order/{lag}" target="_blank" class="status-indicator">👁️ Visa order</a>''' if has_submitted else ""

        admin_cheat_link = ""
        if lag in team_tokens:
            token = team_tokens[lag]
            admin_cheat_link = f'''<a href="/team/{spel_id}/{token}/enter_order" target="_blank" class="admin-cheat-link">🔗 Admin: Ange order</a>'''

        checklist_html += f'''
            <div class="team-order-row">
                <div class="checklist-item">
                    <input type="checkbox" id="{checkbox_id}" name="{checkbox_id}" {checked_attr} class="checkbox-large" onchange="updateNextFasButton(); saveCheckboxState('{checkbox_id}', this.checked);">
                    <span class="team-status">Ordrar från {lag}{submitted_text}</span>
                </div>
                <div class="team-actions">
                    {view_order_link}
                    {admin_cheat_link}
                </div>
            </div>
        '''

    checklist_html += f'''
        </div>
    </div>

    <div class="margin-20-0">
        <form method="post" action="/admin/{spel_id}/timer" class="form-inline">
            <button name="action" value="next_fas" id="next-fas-btn" disabled class="secondary">Nästa fas</button>
        </form>
    </div>

    <script>
    function saveCheckboxState(checkboxId, checked) {{
        fetch('/admin/{spel_id}/save_checkbox', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ checkbox_id: checkboxId, checked: checked }})
        }});
    }}

    function updateNextFasButton() {{
        const totalTeams = {len(data["lag"])};
        let checkedCount = 0;
        for (let i = 1; i <= totalTeams; i++) {{
            const checkbox = document.getElementById('order_check' + i);
            if (checkbox && checkbox.checked) {{ checkedCount++; }}
        }}
        const nextFasButton = document.getElementById('next-fas-btn');
        if (checkedCount === totalTeams) {{
            nextFasButton.disabled = false;
            nextFasButton.className = 'btn btn--success';
        }} else {{
            nextFasButton.disabled = true;
            nextFasButton.className = 'btn btn--secondary';
        }}
    }}

    // (Test Mode borttagen) Admin-länkar visas alltid nu

    function autoFillOrders() {{
        if (!confirm('Är du säker på att du vill auto-fylla alla teams order med test data? Detta kommer att ersätta eventuella befintliga order.')) return;
        fetch('/admin/{spel_id}/auto_fill_orders', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }} }})
            .then(r => r.json())
            .then(d => {{
                if (d.success) {{ alert('✅ ' + d.message); location.reload(); }}
                else {{ alert('❌ Fel: ' + d.error); }}
            }})
            .catch(() => alert('❌ Ett fel uppstod vid auto-fyllning av orders'));
    }}

    function refreshChecklist() {{
        fetch('/admin/{spel_id}/checklist_status')
            .then(r => r.json())
            .then(data => {{
                data.team_status.forEach((status, index) => {{
                    const checkbox = document.getElementById('order_check' + (index + 1));
                    if (checkbox) {{
                        checkbox.checked = status.submitted;
                        const statusSpan = checkbox.parentElement.querySelector('span');
                        if (statusSpan) {{ statusSpan.innerHTML = status.status_text; }}
                        const viewLink = checkbox.parentElement.parentElement.querySelector('a[href*="/view_order/"]');
                        if (viewLink) {{ viewLink.style.display = status.submitted ? 'inline' : 'none'; }}
                    }}
                }});
                updateNextFasButton();
            }})
            .catch(() => {{}});
    }}

    setInterval(refreshChecklist, 5000);
    window.onload = function() {{ updateNextFasButton(); }};
    </script>
    '''

    return checklist_html

def create_diplomatifas_checklist(spel_id):
    """Skapa checklista för Diplomatifas"""
    data = load_game_data(spel_id)
    
    checklist_html = f'''
    <div class="checklist-container border-left-info">
        <h3 class="checklist-title">📋 Checklista: Diplomatifas</h3>
        <div class="checklist-content">
    '''
    
    # Skapa checkboxar med persistent states (4 steg i korrekt ordning)
    checkbox_items = [
        ("diplo_check1", "Kopiera alla teams order för att få ChatGPT-förslag på konsekvenser"),
        ("diplo_check2", "Klistra in i chatgpt och läs resultatet"),
        ("diplo_check3", "Redigera handlingspoäng för varje team"),
        ("diplo_check4", "Uppdatera progress för teamens arbete")
    ]
    
    for checkbox_id, label in checkbox_items:
        is_checked = get_checkbox_state(data, checkbox_id)
        checked_attr = "checked" if is_checked else ""
        
        checklist_html += f'''
            <div class="checklist-item">
                <input type="checkbox" id="{checkbox_id}" name="{checkbox_id}" {checked_attr} class="checkbox-large" onchange="updateDiploNextFasButton(); saveCheckboxState('{checkbox_id}', this.checked);">
                <span class="font-size-14 text-muted">{label}</span>
            </div>
        '''

        # Lägg till relaterat innehåll direkt under respektive steg
        if checkbox_id == "diplo_check1":
            checklist_html += f'''
            <div class="chatgpt-container substep">
                <h4 class="chatgpt-title">📋 ChatGPT Order Sammanfattning</h4>
                <p class="chatgpt-description">Kopiera alla teams order för att få ChatGPT-förslag på konsekvenser</p>
                <a href="/admin/{spel_id}/order_summary" target="_blank" class="info sm btn-equal">
                    📋 Visa Order Sammanfattning
                </a>
            </div>
            '''
        elif checkbox_id == "diplo_check3":
            checklist_html += f'''
            <div class="substep">
                <a href="/admin/{spel_id}/poang" class="primary sm btn-equal">Visa/ändra handlingspoäng</a>
            </div>
            '''
        elif checkbox_id == "diplo_check4":
            checklist_html += f'''
            <div class="substep">
                <a href="/admin/{spel_id}/backlog" class="success sm btn-equal">Uppdatera teamens arbete</a>
            </div>
            '''
    
    checklist_html += f'''
        </div>
    </div>
    
    <div class="margin-20-0">
        <form method="post" action="/admin/{spel_id}/timer" class="form-inline">
            <button name="action" value="next_fas" id="diplo-next-fas-btn" disabled class="secondary">Nästa fas</button>
        </form>
    </div>
    
    <script>
    function saveCheckboxState(checkboxId, checked) {{
        fetch('/admin/{spel_id}/save_checkbox', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                checkbox_id: checkboxId,
                checked: checked
            }})
        }});
    }}
    
    function updateDiploNextFasButton() {{
        const check1 = document.getElementById('diplo_check1').checked;
        const check2 = document.getElementById('diplo_check2').checked;
        const check3 = document.getElementById('diplo_check3').checked;
        const check4 = document.getElementById('diplo_check4').checked;
        const nextFasButton = document.getElementById('diplo-next-fas-btn');

        if (check1 && check2 && check3 && check4) {{
            nextFasButton.disabled = false;
            nextFasButton.className = 'btn btn--info';
        }} else {{
            nextFasButton.disabled = true;
            nextFasButton.className = 'btn btn--secondary';
        }}
    }}
    
    // Initiera knappen när sidan laddas
    window.onload = function() {{
        updateDiploNextFasButton();
    }};
    </script>
    '''
    
    return checklist_html

def create_resultatfas_checklist(spel_id):
    """Skapa checklista för Resultatfas"""
    data = load_game_data(spel_id)
    
    checklist_html = f'''
    <div class="checklist-container border-left-info">
        <h3 class="checklist-title">✅ Checklista innan ny runda</h3>
        <div class="checklist-content">
    '''
    
    # Skapa checkboxar med persistent states (endast textpunkter)
    checkbox_items = [
        ("result_check1", "Läsa upp nyheter"),
        ("result_check2", "Visa Team Översikt"),
        ("result_check3", "Visa teamens nya handlingspoäng"),
        ("result_check4", "Visa Order Sammanfattning")
    ]
    
    for i, (checkbox_id, label) in enumerate(checkbox_items, 1):
        is_checked = get_checkbox_state(data, checkbox_id)
        checked_attr = "checked" if is_checked else ""
        
        checklist_html += f'''
            <div class="checklist-item">
                <input type="checkbox" id="{checkbox_id}" name="{checkbox_id}" {checked_attr} class="checkbox-large" onchange="updateStartButton(); saveCheckboxState('{checkbox_id}', this.checked);">
                <span class="team-status">{label}</span>
            </div>
        '''
        
        # Lägg till relaterat innehåll direkt under respektive steg
        if checkbox_id == "result_check4":
            checklist_html += f'''
            <div class="chatgpt-container substep">
                <h4 class="chatgpt-title">📋 ChatGPT Order Sammanfattning</h4>
                <p class="chatgpt-description">Kopiera alla teams order för att få ChatGPT-förslag på konsekvenser</p>
                <a href="/admin/{spel_id}/order_summary" target="_blank" class="info sm btn-equal">
                    📋 Visa Order Sammanfattning
                </a>
            </div>
            '''
        
    
    checklist_html += f'''
        </div>
    </div>
    
    <script>
    function saveCheckboxState(checkboxId, checked) {{
        fetch('/admin/{spel_id}/save_checkbox', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                checkbox_id: checkboxId,
                checked: checked
            }})
        }});
    }}
    
    function updateStartButton() {{
        const check1 = document.getElementById('result_check1').checked;
        const check2 = document.getElementById('result_check2').checked;
        const check3 = document.getElementById('result_check3').checked;
        const check4 = document.getElementById('result_check4').checked;
        const startButton = document.getElementById('start-ny-runda-btn');
        
        if (check1 && check2 && check3 && check4) {{
            startButton.disabled = false;
            startButton.className = 'primary lg';
        }} else {{
            startButton.disabled = true;
            startButton.className = 'secondary lg';
        }}
    }}
    
    // Initiera knappen när sidan laddas
    window.onload = function() {{
        updateStartButton();
    }};
    </script>
    '''
    
    return checklist_html

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
            
            // Lägg till visuella varningar baserat på återstående tid
            timerElem.classList.remove('warning', 'danger');
            if (remaining <= 60 && remaining > 30) {{
                // Varning: 1 minut kvar
                timerElem.classList.add('warning');
            }} else if (remaining <= 30) {{
                // Fara: 30 sekunder eller mindre
                timerElem.classList.add('danger');
            }}
            
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
    
    // Timer maximization functionality
    function toggleTimerMaximize() {{
        var timerContainer = document.querySelector('.timer-container');
        var maximizeBtn = document.querySelector('.maximize-btn');
        var minimizeBtn = document.querySelector('.minimize-btn');
        var body = document.body;
        
        if (timerContainer.classList.contains('maximized')) {{
            // Minimize timer
            timerContainer.classList.remove('maximized');
            body.classList.remove('timer-maximized');
            maximizeBtn.style.display = 'inline-block';
            minimizeBtn.style.display = 'none';
        }} else {{
            // Maximize timer
            timerContainer.classList.add('maximized');
            body.classList.add('timer-maximized');
            maximizeBtn.style.display = 'none';
            minimizeBtn.style.display = 'inline-block';
        }}
    }}
    
    // Keyboard shortcut for maximizing/minimizing timer (F11 key)
    document.addEventListener('keydown', function(event) {{
        if (event.key === 'F11') {{
            event.preventDefault(); // Prevent browser fullscreen
            event.stopPropagation(); // Stop event from bubbling up
            toggleTimerMaximize();
            return false; // Prevent default behavior
        }}
    }});
    
    // Also prevent F11 on keyup to be extra sure
    document.addEventListener('keyup', function(event) {{
        if (event.key === 'F11') {{
            event.preventDefault();
            event.stopPropagation();
            return false;
        }}
    }});
    </script>
    '''

def create_historik_html(rundor):
    """Skapa snygg historik HTML"""
    if not rundor:
        return ""
    
    historik_html = '''
    <div class="section-header">
        <h3>📊 Spelhistorik</h3>
    '''
    
    for rundnr in sorted(rundor.keys()):
        historik_html += f'''
        <div class="card">
            <h4 class="card-title">🎯 Runda {rundnr}</h4>
            <div class="flex-wrap">
        '''
        
        for entry in rundor[rundnr]:
            if entry["status"] == "pågående":
                status_icon = "🔄"
                status_class = "ongoing"
            else:
                status_icon = "✅"
                status_class = "done"
            
            historik_html += f'''
            <div class="status-badge {status_class}">{status_icon} {entry["fas"]}</div>
            '''
        
        historik_html += '</div></div>'
    
    historik_html += '</div>'
    return historik_html

def create_team_overview(data):
    """Skapa kompakt översikt för alla team med card-baserad layout"""
    if "backlog" not in data or not isinstance(data["backlog"], dict):
        return ""
    
    overview_html = '''
    <div class="section-header">
        <h3>📊 Team Översikt</h3>
    </div>
    
    <div class="team-overview-grid">
    '''
    
    # Skapa färgskala funktion
    def get_progress_color(percent):
        if percent >= 80:
            return "#28a745"  # Grön
        elif percent >= 60:
            return "#ffc107"  # Gul
        elif percent >= 40:
            return "#fd7e14"  # Orange
        elif percent >= 20:
            return "#e83e8c"  # Rosa
        else:
            return "#dc3545"  # Röd
    
    # Skapa team-kort för varje lag
    for lag in data["lag"]:
        if lag in data["backlog"]:
            team_tasks = []
            total_estimaterade = 0
            total_spenderade = 0
            
            for uppgift in data["backlog"][lag]:
                # Filtrera bort återkommande uppgifter
                is_aterkommande = "typ" in uppgift and uppgift["typ"] == "aterkommande"
                if not is_aterkommande:
                    if lag == "Bravo":
                        # Bravo har faser - beräkna total progress
                        task_estimaterade = sum(fas["estimaterade_hp"] for fas in uppgift["faser"])
                        task_spenderade = sum(fas["spenderade_hp"] for fas in uppgift["faser"])
                        progress_percent = min(100, (task_spenderade / task_estimaterade * 100) if task_estimaterade > 0 else 0)
                    else:
                        # Enkla uppgifter
                        task_estimaterade = uppgift["estimaterade_hp"]
                        task_spenderade = uppgift["spenderade_hp"]
                        progress_percent = min(100, (task_spenderade / task_estimaterade * 100) if task_estimaterade > 0 else 0)
                    
                    team_tasks.append({
                        "namn": uppgift["namn"],
                        "progress": progress_percent,
                        "spenderade": task_spenderade,
                        "estimaterade": task_estimaterade
                    })
                    
                    total_estimaterade += task_estimaterade
                    total_spenderade += task_spenderade
            
            # Beräkna team-total progress
            team_progress = min(100, (total_spenderade / total_estimaterade * 100) if total_estimaterade > 0 else 0)
            team_color = get_progress_color(team_progress)
            
            # Team-färg baserat på lag
            team_bg_colors = {
                "Alfa": "linear-gradient(135deg, #5ba3e8 0%, #4a8ce8 100%)",
                "Bravo": "linear-gradient(135deg, #5dd085 0%, #4ac870 100%)",
                "STT": "linear-gradient(135deg, #f5d547 0%, #f0c040 100%)",
                "FM": "linear-gradient(135deg, #f08a82 0%, #e67a73 100%)",
                "BS": "linear-gradient(135deg, #4a5a6c 0%, #3a4a5c 100%)",
                "Media": "linear-gradient(135deg, #b07cc6 0%, #a06bb8 100%)",
                "Säpo": "linear-gradient(135deg, #4a6bb8 0%, #3a5ba8 100%)",
                "Regeringen": "linear-gradient(135deg, #8a9ba8 0%, #7a8b98 100%)",
                "USA": "linear-gradient(135deg, #4ac5d8 0%, #3ab5c8 100%)"
            }
            
            team_bg = team_bg_colors.get(lag, "linear-gradient(135deg, #6ba3f5 0%, #4a8ce8 100%)")
            
            overview_html += f'''
            <div class="team-overview-card">
                <div class="team-overview-header" style="background: {team_bg};">
                    <div class="team-overview-title">
                        <h4>🟢 {lag}</h4>
                        <div class="team-overview-progress">
                            <span class="team-progress-percent">{team_progress:.0f}%</span>
                            <span class="team-progress-hp">{total_spenderade}/{total_estimaterade} HP</span>
                        </div>
                    </div>
                    <div class="team-overview-bar">
                        <div class="team-progress-fill" style="width: {team_progress}%; background: {team_color};"></div>
                    </div>
                </div>
                
                <div class="team-overview-content">
            '''
            
            # Visa alla uppgifter
            for task in team_tasks:  # Visa alla uppgifter per team
                task_color = get_progress_color(task["progress"])
                overview_html += f'''
                    <div class="team-task-item">
                        <div class="team-task-info">
                            <span class="team-task-name">{task["namn"]}</span>
                            <span class="team-task-hp">{task["spenderade"]}/{task["estimaterade"]} HP</span>
                        </div>
                        <div class="team-task-bar">
                            <div class="team-task-fill" style="width: {task["progress"]}%; background: {task_color};"></div>
                        </div>
                    </div>
                '''
            
            overview_html += '''
                </div>
            </div>
            '''
    
    if not any(lag in data["backlog"] for lag in data["lag"]):
        overview_html += '''
        <div class="team-overview-empty">
            <div class="text-center text-muted">
                <p>Inga uppgifter att visa ännu.</p>
            </div>
        </div>
        '''
    
    overview_html += '''
    </div>
    '''
    
    return overview_html

def create_phase_progress_html(runda, fas):
    """Skapa visuell fas-progress för aktuell runda med design-system färger"""
    phases = ["Orderfas", "Diplomatifas", "Resultatfas"]
    
    progress_html = f'''
    <div class="card">
        <h3 class="card-title">🎯 RUNDA {runda} AV 4</h3>
        <div class="flex-wrap">
    '''
    
    for phase in phases:
        if phase == fas:
            status_icon = "🔄"
            status_class = "phase-current"
        elif phases.index(phase) < phases.index(fas):
            status_icon = "✅"
            status_class = "phase-done"
        else:
            status_icon = "⏳"
            status_class = "phase-future"
        
        progress_html += f'''
        <div class="phase-pill {status_class}">{status_icon} {phase}</div>
        '''
    
    progress_html += '''
        </div>
    </div>
    '''
    return progress_html

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
        password = request.form.get("password", "").strip()
        spel_id = skapa_nytt_spel(datum, plats, antal_spelare, orderfas_min, diplomatifas_min, password)
        return redirect(url_for("admin.admin_panel", spel_id=spel_id))
    
    # Lista befintliga spel
    spel = []
    for game in list_saved_games():
        spel.append({
            "id": game["id"],
            "datum": game.get("datum", ""),
            "plats": game.get("plats", ""),
            "runda": game.get("runda", 1),
            "fas": game.get("fas", ""),
        })
    
    intervals = [
        ("15-26 (5 team)", 20),
        ("27-60 (9 team)", 27)
    ]
    
    # Skapa JavaScript för att visa vilka team som kommer vara med
    team_info_js = create_team_info_js()
    
    return f'''
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/app.css?v=5">
        <link rel="stylesheet" href="/static/print.css" media="print">
        <div class="container">
            <!-- Header Section -->
            <div class="page-header">
                <h1>Stabsspel Admin</h1>
                <p class="page-subtitle">Spelhantering och kontrollpanel</p>
            </div>
            
            <!-- Main Content Grid -->
            <div class="admin-form-grid">
                
                <!-- New Game Form -->
                <div class="admin-form-section">
                    <h2>
                        <span class="admin-form-section-icon">➕</span>
                        Starta nytt spel
                    </h2>
                    
                    <form method="post">
                        <div class="admin-form-grid">
                            <div>
                                <label for="datum">📅 Datum</label>
                                <input type="date" name="datum" id="datum" required>
                            </div>
                            <div>
                                <label for="plats">📍 Plats</label>
                                <input type="text" name="plats" id="plats" required placeholder="T.ex. Stockholm">
                            </div>
                        </div>
                        
                        <div class="admin-form-grid-single">
                            <div>
                                <label for="players_interval">👥 Antal spelare</label>
                                <select name="players_interval" id="players_interval" onchange="updateTeamInfo()">
                                    {''.join([f'<option value="{val}">{label}</option>' for label, val in intervals])}
                                </select>
                            </div>
                        </div>
                        
                        <div class="admin-form-grid">
                            <div>
                                <label for="orderfas_min">⏱️ Orderfas (min)</label>
                                <input type="number" name="orderfas_min" id="orderfas_min" min="1" value="10" required>
                            </div>
                            <div>
                                <label for="diplomatifas_min">🤝 Diplomatifas (min)</label>
                                <input type="number" name="diplomatifas_min" id="diplomatifas_min" min="1" value="10" required>
                            </div>
                        </div>
                        
                        <div class="admin-form-grid-single">
                            <div>
                                <label for="password">🔒 Spellösenord</label>
                                <input type="password" name="password" id="password" placeholder="Lämna tomt för standardlösenord" maxlength="50">
                                <small class="text-muted">Skyddar spelledarpanelen. Lämna tomt för standardlösenord.</small>
                            </div>
                        </div>
                        
                        <button type="submit" class="primary lg">
                            🚀 Starta nytt spel
                        </button>
                    </form>
                    
                    <div id="team-info" class="mt-4"></div>
                </div>
                
                <!-- Upload Game -->
                <div class="admin-form-section info">
                    <h2>
                        <span class="admin-form-section-icon">📁</span>
                        Ladda upp spel
                    </h2>
                    <p class="text-muted mb-3">Återställ ett spel från en tidigare nedladdad JSON-fil</p>
                    <a href="/admin/upload_game" class="secondary lg">
                        📤 Ladda upp JSON-fil
                    </a>
                </div>
                
                <!-- Existing Games -->
                <div class="admin-form-section success">
                    <h2>
                        <span class="admin-form-section-icon">📋</span>
                        Befintliga spel ({len(spel)})
                    </h2>
                    
                    {f'''
                    <div class="scroll-y-400">
                        {''.join([f'''
                        <div class="list-card border-left-success">
                            <div class="flex-between">
                                <div class="flex-1">
                                    <h3 class="h3-compact">{s["datum"]}</h3>
                                    <p class="mb-0 text-muted">📍 {s["plats"]}</p>
                                    <p class="mt-5px text-xs text-muted-light">Runda {s.get("runda", "?")} · {s.get("fas", "")} · ID: {s["id"]}</p>
                                </div>
                                <div class="flex gap-2">
                                    <a href="/admin/{s["id"]}" class="primary sm link-light">▶️ Öppna</a>
                                    <a href="/admin/download_game/{s["id"]}" class="secondary sm link-light">💾 Ladda ner</a>
                                    <form method="post" action="/admin/delete_game/{s["id"]}" class="d-inline" onsubmit="return confirm('Är du säker på att du vill ta bort spelet {s["datum"]} – {s["plats"]}? Detta går inte att ångra.')">
                                        <button type="submit" class="danger sm">🗑️ Ta bort</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                        ''' for s in spel])}
                    </div>
                    ''' if spel else '''
                    <div class="text-center empty-box text-muted">
                        <div class="emoji-xl">📭</div>
                        <h3 class="mb-0">Inga spel ännu</h3>
                        <p class="text-sm">Skapa ditt första spel genom att fylla i formuläret till vänster.</p>
                    </div>
                    '''}
                </div>
            </div>
            
            <!-- Quick Stats -->
            <div class="stats-card">
                <h2 class="title-row">
                    <span class="title-icon">📊</span>
                    Snabbstatistik
                </h2>
                <div class="grid-auto-200">
                    <div class="stat-box">
                        <div class="emoji-lg">🎮</div>
                        <h3 class="mb-0">{len(spel)}</h3>
                        <p class="mt-5px text-sm text-muted">Totalt antal spel</p>
                    </div>
                    <div class="stat-box">
                        <div class="emoji-lg">👥</div>
                        <h3 class="mb-0">5-9</h3>
                        <p class="mt-5px text-sm text-muted">Team per spel</p>
                    </div>
                    <div class="stat-box">
                        <div class="emoji-lg">⏱️</div>
                        <h3 class="mb-0">10-15</h3>
                        <p class="mt-5px text-sm text-muted">Minuter per fas</p>
                    </div>
                    <div class="stat-box">
                        <div class="emoji-lg">🔄</div>
                        <h3 class="mb-0">3</h3>
                        <p class="mt-5px text-sm text-muted">Faser per runda</p>
                    </div>
                </div>
            </div>
            
            {team_info_js}
        </div>
        
        <style>
        input:focus, select:focus {{
            outline: none;
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .container > div:hover {{
            transform: translateY(-2px);
            transition: transform 0.3s ease;
        }}
        </style>
    '''

@admin_bp.route("/admin/<spel_id>", methods=["GET", "POST"])
def admin_panel(spel_id):
    # Kontrollera session först
    session_key = f"game_session_{spel_id}"
    if request.method == "GET" and is_game_session_valid(spel_id, session.get(session_key)):
        # Session är giltig, fortsätt till admin-panelen
        pass
    elif request.method == "POST":
        # Kontrollera lösenord
        provided_password = request.form.get("password", "").strip()
        if not check_game_password(spel_id, provided_password):
            return f'''
            <!DOCTYPE html>
            <html lang="sv">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Lösenord krävs - Stabsspel</title>
                <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
                <link rel="stylesheet" href="/static/app.css">
            </head>
            <body>
                <div class="container">
                    <div class="page-header">
                        <h1>🔒 Lösenord krävs</h1>
                        <p class="page-subtitle">Spelet är skyddat med lösenord</p>
                    </div>
                    
                    <div class="card">
                        <div class="notification error">
                            ❌ Felaktigt lösenord. Försök igen.
                        </div>
                        
                        <form method="post">
                            <div>
                                <label for="password">Spellösenord</label>
                                <input type="password" name="password" id="password" required placeholder="Ange lösenord">
                                <small class="text-muted">Ange spelledarlösenordet för spelet</small>
                            </div>
                            <button type="submit" class="primary">Öppna spel</button>
                        </form>
                        
                        <div class="mt-4">
                            <a href="/admin" class="secondary">← Tillbaka till admin</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            ''', 401
        else:
            # Lösenord korrekt, skapa session
            session[session_key] = create_game_session(spel_id)
            session.permanent = True
    
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    # Kontrollera om lösenord behövs (för GET-requests utan giltig session)
    stored_password = data.get("password")
    # Om det är en GET-request utan giltig session, visa lösenordsprompt
    if request.method == "GET" and not is_game_session_valid(spel_id, session.get(session_key)):
        return f'''<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lösenord krävs - Stabsspel</title>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/app.css">
</head>
<body>
    <div class="container">
        <div class="page-header">
            <h1>🔒 Lösenord krävs</h1>
            <p class="page-subtitle">Spelet är skyddat med lösenord</p>
        </div>
        
        <div class="card">
            <form method="post">
                <div>
                    <label for="password">Spellösenord</label>
                    <input type="password" name="password" id="password" required placeholder="Ange lösenord">
                    <small class="text-muted">Ange spelledarlösenordet för spelet</small>
                </div>
                <button type="submit" class="primary">Öppna spel</button>
            </form>
            
            <div class="mt-4">
                <a href="/admin" class="secondary">← Tillbaka till admin</a>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    # Beräkna timer-värden med centraliserad funktion
    remaining = get_phase_timer(data)
    
    # Hämta spelstatus
    avslutat = data.get("avslutat", False)
    runda = data.get("runda", 1)
    fas = data.get("fas", "Orderfas")
    timer_status = data.get("timer_status", "stopped")
    
    # Skapa historik
    historik = data.get("fashistorik", [])
    rundor = {}
    for entry in historik:
        rundnr = entry["runda"]
        if rundnr not in rundor:
            rundor[rundnr] = []
        rundor[rundnr].append(entry)
    
    historik_html = create_historik_html(rundor)
    
    # Skapa visuell fas-progress för aktuell runda
    phase_progress_html = create_phase_progress_html(runda, fas)
    
    # Skapa kvartalsvisualisering
    quarters = [
        {"name": "Okt-Dec", "active": runda >= 1},
        {"name": "Jan-Mar", "active": runda >= 2},
        {"name": "Apr-Jun", "active": runda >= 3},
        {"name": "Jul-Sep", "active": runda >= 4}
    ]
    
    quarter_bar_html = create_quarter_bar_html(quarters, runda)
    
    # Skapa klickbara lagnamn
    lag_html = ', '.join([
        f'<a href="/team/{spel_id}/{lag}" target="_blank" class="link-light underline fw-semibold">{lag}</a>' for lag in data['lag']
    ])
    
    console_html = create_gm_console_html(spel_id, data)
    
    # Returnera komplett HTML med förbättrad layout
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
            <link rel="stylesheet" href="/static/app.css?v=5">
            <link rel="stylesheet" href="/static/print.css" media="print">
            <script>
                // Force cache refresh for JavaScript
                if (window.performance && window.performance.navigation.type === window.performance.navigation.TYPE_BACK_FORWARD) {{
                    window.location.reload();
                }}
                
                // Prevent caching of dynamic content
                window.addEventListener('load', function() {{
                    // Clear any cached data
                    if ('caches' in window) {{
                        caches.keys().then(function(names) {{
                            for (let name of names) {{
                                caches.delete(name);
                            }}
                        }});
                    }}
                }});
            </script>
        </head>
        <body>
            <div class="container">
            <!-- Header Section -->
            <div class="admin-panel-header">
                <h1>Spelledarpanel</h1>
                <p class="gm-meta">{data["datum"]} · {data["plats"]} · {data["antal_spelare"]} spelare · {lag_html}</p>
            </div>
            
            {create_declaration_warning(runda)}
            
            {console_html}
            
            {quarter_bar_html}
            
            {create_team_overview(data)}
            
            {historik_html}
        </div>
        
        <!-- Include admin JavaScript -->
        {create_script_references()}
        
        <style>
        /* Team Overview Grid Layout */
        .team-overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .team-overview-card {{
            background: white;
            border: 1px solid #e8e9ea;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .team-overview-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        .team-overview-header {{
            color: white;
            padding: 16px 20px;
            position: relative;
        }}
        
        .team-overview-title {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .team-overview-title h4 {{
            margin: 0;
            font-size: 1.1em;
            font-weight: 600;
        }}
        
        .team-overview-progress {{
            text-align: right;
        }}
        
        .team-progress-percent {{
            display: block;
            font-size: 1.2em;
            font-weight: bold;
        }}
        
        .team-progress-hp {{
            display: block;
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .team-overview-bar {{
            height: 6px;
            background: rgba(255,255,255,0.3);
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .team-progress-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.3s ease;
        }}
        
        .team-overview-content {{
            padding: 16px 20px;
        }}
        
        .team-task-item {{
            margin-bottom: 12px;
        }}
        
        .team-task-item:last-child {{
            margin-bottom: 0;
        }}
        
        .team-task-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }}
        
        .team-task-name {{
            font-size: 0.9em;
            color: #2c3e50;
            font-weight: 500;
        }}
        
        .team-task-hp {{
            font-size: 0.8em;
            color: #6c757d;
        }}
        
        .team-task-bar {{
            height: 4px;
            background: #e9ecef;
            border-radius: 2px;
            overflow: hidden;
        }}
        
        .team-task-fill {{
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }}
        
        .team-task-more {{
            text-align: center;
            padding: 8px 0;
            border-top: 1px solid #e9ecef;
            margin-top: 8px;
        }}
        
        .team-overview-empty {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 40px 20px;
            color: #6c757d;
        }}
        
        /* Reduce overall spacing in admin panel */
        .admin-content-card {{
            margin-bottom: 16px;
        }}
        
        .card {{
            margin-bottom: 16px;
        }}
        
        .section-header {{
            margin-bottom: 16px;
        }}
        
        .section-header h3 {{
            margin-bottom: 8px;
        }}
        
        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .team-overview-grid {{
                grid-template-columns: 1fr;
                gap: 16px;
            }}
            
            .team-overview-card {{
                margin-bottom: 0;
            }}
        }}
        </style>
        </body>
        </html>
    '''
    
    # Skapa response med anti-caching headers
    response = make_response(html_content)
    return add_no_cache_headers(response)

def create_quarter_bar_html(quarters, current_round):
    """Skapa kvartalsvisualisering med design-system färger"""
    quarter_html = '<div class="card">'
    quarter_html += '<h3 class="card-title">KVARTALSFÖRLOPP</h3>'
    quarter_html += '<div class="flex gap-2 flex-center">'
    
    for i, quarter in enumerate(quarters):
        is_active = quarter["active"]
        is_current = current_round == i + 1
        
        if is_current:
            # Current quarter - use softer blue
            bg_color = "#6ba3f5"
            text_color = "white"
            border = "2px solid #4a8ce8"
        elif is_active:
            # Completed quarter - use softer green
            bg_color = "#7bc96f"
            text_color = "white"
            border = "1px solid #6bb85f"
        else:
            # Future quarter - use light gray
            bg_color = "#f5f6f7"
            text_color = "#7a8a9c"
            border = "1px solid #e8e9ea"
        
        quarter_html += f'''
        <div class="quarter-pill flex-1" data-bg="{bg_color}" data-fg="{text_color}" data-border="{border}">
            {quarter["name"]}
        </div>
        '''
    
    quarter_html += '</div></div>'
    return quarter_html

def create_timer_html(spel_id, data, fas, avslutat, remaining, timer_status, rubrik, runda):
    """Skapa timer HTML baserat på fas"""
    if avslutat:
        return '<h2 class="section-title text-danger mt-4">Spelet är avslutat</h2>'
    
    if fas in ["Orderfas", "Diplomatifas"]:
        timer_html = ''
        
        # Visa rubrik endast om den inte är tom (för bakåtkompatibilitet)
        if rubrik:
            timer_html += f'<h2 class="section-title">{rubrik}</h2>'
        
        timer_html += create_timer_controls(spel_id, remaining, timer_status)
        
        # Add time adjustment modal
        timer_html += create_time_adjustment_modal(spel_id, data.get("orderfas_min", 10), data.get("diplomatifas_min", 10))
        
        if fas == "Orderfas":
            timer_html += create_orderfas_checklist(spel_id, data)
        elif fas == "Diplomatifas":
            timer_html += create_diplomatifas_checklist(spel_id)
        
        timer_html += create_timer_script(remaining, timer_status)
        return timer_html
    
    elif fas == "Resultatfas":
        # Visa rubrik endast om den inte är tom (för bakåtkompatibilitet)
        timer_html = ''
        if rubrik:
            timer_html += f'<h2 class="section-title">{rubrik}</h2>'
        timer_html += create_resultatfas_checklist(spel_id)
        
        # Starta ny runda knapp - inaktivera om runda 4
        if runda >= MAX_RUNDA:
            timer_html += f'''
            <div class="text-center margin-20-0">
                <form method="post" action="/admin/{spel_id}/ny_runda" class="d-inline">
                    <button type="submit" id="start-ny-runda-btn" disabled class="secondary lg">Starta ny runda</button>
                </form>
            </div>
            '''
        else:
            timer_html += f'''
            <div class="text-center margin-20-0">
                <form method="post" action="/admin/{spel_id}/ny_runda" class="d-inline">
                    <button type="submit" id="start-ny-runda-btn" class="primary lg">Starta ny runda</button>
                </form>
            </div>
            '''
        
        # Avsluta spel om max runder nått
        if runda >= MAX_RUNDA:
            timer_html += f'''
            <div class="text-center margin-20-0">
                <form method="post" action="/admin/{spel_id}/slut" class="d-inline">
                    <button type="submit" class="danger lg">Avsluta spelet</button>
                </form>
            </div>
            '''
    
    return timer_html

@admin_bp.route("/admin/<spel_id>/save_checkbox", methods=["POST"])
def save_checkbox_state_route(spel_id):
    """Spara checkbox-tillstånd via AJAX"""
    try:
        data = request.get_json()
        checkbox_id = data.get("checkbox_id")
        checked = data.get("checked")
        
        if checkbox_id is not None and checked is not None:
            save_checkbox_state(spel_id, checkbox_id, checked)
            return {"success": True}, 200
        else:
            return {"success": False, "error": "Missing checkbox_id or checked"}, 400
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@admin_bp.route("/admin/<spel_id>/checklist_status")
def checklist_status(spel_id):
    """Get current status of team orders for auto-refresh"""
    try:
        data = load_game_data(spel_id)
        if not data:
            return {"error": "Game not found"}, 404
        
        orders_key = f"orders_round_{data['runda']}"
        team_orders = data.get("team_orders", {}).get(orders_key, {})
        
        team_status = []
        for lag in data["lag"]:
            has_submitted = lag in team_orders and team_orders[lag].get("final", False)
            submitted_status = ""  # Removed emoji to prevent visual duplication
            submitted_text = " (Inskickad)" if has_submitted else " (Väntar)"
            
            team_status.append({
                "team": lag,
                "submitted": has_submitted,
                "status_text": f"Ordrar från {lag}{submitted_text}"
            })
        
        return {"team_status": team_status}
    except Exception as e:
        return {"error": str(e)}, 500

@admin_bp.route("/admin/<spel_id>/timer", methods=["POST"])
def admin_timer_action(spel_id):
    try:
        action = request.form.get("action")
        data = load_game_data(spel_id)
        if not data:
            return "Spelet hittades inte.", 404
        now = int(time.time())
        if action == "start":
            data["timer_status"] = "running"
            data["timer_start"] = now
            data["fas_start_time"] = now
        elif action == "pause":
            if data.get("timer_status") == "running":
                elapsed = now - data.get("timer_start", now)
                data["timer_status"] = "paused"
                data["timer_elapsed"] = elapsed + data.get("timer_elapsed", 0)
        elif action == "reset":
            push_undo(data, "Nollställ timer")
            reset_timer_fields(data)
        elif action == "add_min":
            add_timer_seconds(data, 60)
        elif action == "sub_min":
            add_timer_seconds(data, -60)
        elif action == "next_fas":
            push_undo(data, "Nästa fas")
            data = apply_next_phase(data)
        elif action == "prev_fas":
            push_undo(data, "Föregående fas")
            data = apply_previous_phase(data)
        elif action == "ny_runda":
            push_undo(data, "Ny runda")
            data = apply_new_round(data)
        elif action == "end_game":
            push_undo(data, "Avsluta spel")
            data = end_game(data)
        save_game_data(spel_id, data)
        return redirect(url_for("admin.admin_panel", spel_id=spel_id))
    except Exception as e:
        print(f"Error in admin_timer_action: {e}")
        return f"Ett fel uppstod: {str(e)}", 500


@admin_bp.route("/admin/<spel_id>/undo", methods=["POST"])
def admin_undo(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    data, label = apply_undo(data)
    if label:
        log = data.setdefault("gm_log", [])
        log.append({"at": time.time(), "kind": "undo", "message": f"Ångrade: {label}"})
        data["gm_log"] = log[-50:]
    save_game_data(spel_id, data)
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))


@admin_bp.route("/admin/<spel_id>/hp", methods=["POST"])
def admin_hp_live(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    op = request.form.get("op")
    reason = request.form.get("reason", "")
    try:
        if op == "plus5":
            push_undo(data, "HP +5")
            adjust_hp(data, request.form.get("team"), 5, reason)
        elif op == "minus5":
            push_undo(data, "HP -5")
            adjust_hp(data, request.form.get("team"), -5, reason)
        elif op == "transfer":
            push_undo(data, "HP-överföring")
            transfer_hp(
                data,
                request.form.get("from_team"),
                request.form.get("to_team"),
                int(request.form.get("amount") or 0),
                reason,
            )
        elif op == "support":
            push_undo(data, "Regeringsstöd")
            set_regeringsstod(
                data,
                request.form.get("team"),
                request.form.get("regeringsstod") == "on",
                reason,
            )
        else:
            return "Okänd HP-åtgärd", 400
    except (ValueError, TypeError) as exc:
        return str(exc), 400
    save_game_data(spel_id, data)
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))


@admin_bp.route("/admin/<spel_id>/test_mode", methods=["POST"])
def admin_test_mode(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Spelet hittades inte"}), 404
    payload = request.get_json(silent=True) or {}
    data["test_mode"] = bool(payload.get("enabled"))
    save_game_data(spel_id, data)
    return jsonify({"success": True, "test_mode": data["test_mode"]})

@admin_bp.route("/admin/<spel_id>/adjust_times", methods=["POST"])
def admin_adjust_times(spel_id):
    """Handle time adjustments for Order and Diplomacy phases"""
    try:
        data = load_game_data(spel_id)
        if not data:
            return "Spelet hittades inte.", 404
        
        # Get new times from form
        orderfas_min = int(request.form.get("orderfas_min", data.get("orderfas_min", 10)))
        diplomatifas_min = int(request.form.get("diplomatifas_min", data.get("diplomatifas_min", 10)))
        
        # Validate times (1-60 minutes)
        if not (1 <= orderfas_min <= 60 and 1 <= diplomatifas_min <= 60):
            return "Tiderna måste vara mellan 1 och 60 minuter.", 400
        
        # Update the game data
        data["orderfas_min"] = orderfas_min
        data["diplomatifas_min"] = diplomatifas_min
        save_game_data(spel_id, data)
        
        # Redirect back to admin panel with success message
        return redirect(url_for("admin.admin_panel", spel_id=spel_id))
        
    except Exception as e:
        print(f"Error in admin_adjust_times: {e}")
        return f"Ett fel uppstod: {str(e)}", 500

@admin_bp.route("/admin/<spel_id>/slut", methods=["POST"])
def admin_slut(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    push_undo(data, "Avsluta spel")
    data = end_game(data)
    save_game_data(spel_id, data)
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
            from models import get_team_base_hp
            bas = get_team_base_hp(lag, data)
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
    # Bygg tabell med moderna CSS-klasser
    tabell = "<form method='post'><table>"
    tabell += "<tr><th>Lag</th><th>Ursprung</th><th>Aktuell</th><th>Skillnad</th><th>Regeringsstöd</th><th>Formel</th></tr>"
    for lag in laglista:
        p = data["poang"][lag]
        bas = p["bas"]
        aktuell = p["aktuell"]
        diff = aktuell - bas
        diff_class = "text-success" if diff > 0 else ("text-danger" if diff < 0 else "text-muted")
        regeringsstod = p.get("regeringsstod", False)
        # Formel: t.ex. 25 + 10 om regeringsstöd
        formel = str(aktuell)
        if regeringsstod:
            formel += " + 10"
        # Inputfält och checkbox
        tabell += f"<tr>"
        tabell += f"<td><strong>{lag}</strong></td>"
        tabell += f"<td>{bas}</td>"
        tabell += f"<td><input type='number' name='poang_{lag}' value='{aktuell}' min='0'></td>"
        tabell += f"<td class='text-center {diff_class}'>{'+' if diff>0 else ''}{diff}</td>"
        tabell += f"<td class='text-center'><input type='checkbox' name='regeringsstod_{lag}' {'checked' if regeringsstod else ''}></td>"
        tabell += f"<td><code>{formel}</code></td>"
        tabell += f"</tr>"
    tabell += "</table><br><button type='submit' class='success'>💾 Spara ändringar</button></form>"
    # Visa aktuell runda med konsistent header
    html = f"""
    <link rel='stylesheet' href='/static/app.css?v=5'>
    <div class='container'>
        <div class='page-header'>
            <h1>Handlingspoäng – Runda {runda}</h1>
            <p class='page-subtitle'>Hantera teamens handlingspoäng och regeringsstöd</p>
        </div>
        {tabell}
        <br><a href='/admin/{spel_id}' class='secondary'>← Tillbaka till adminpanelen</a>
    </div>
    """
    return Markup(html)



# Modifiera admin_ny_runda så att regeringsstöd nollställs
@admin_bp.route("/admin/<spel_id>/ny_runda", methods=["POST"])
def admin_ny_runda(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    push_undo(data, "Ny runda")
    data = apply_new_round(data)
    save_game_data(spel_id, data)
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))

@admin_bp.route("/admin/<spel_id>/reset", methods=["POST"])
def admin_reset(spel_id):
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return "Spelet hittades inte.", 404
    with open(filnamn, encoding="utf-8") as f:
        data = json.load(f)
    push_undo(data, "Återställ spel")
    data["runda"] = 1
    data["fas"] = "Orderfas"
    data["timer_status"] = "stopped"
    data["timer_start"] = None
    data["timer_elapsed"] = 0
    data["avslutat"] = False
    data["fashistorik"] = init_fashistorik_v2()
    # Nollställ handlingspoäng och regeringsstöd, sätt rätt basvärde från TEAMS
    if "poang" in data:
        from models import get_team_base_hp
        for lag in data["poang"]:
            bas = get_team_base_hp(lag, data)
            data["poang"][lag]["bas"] = bas
            data["poang"][lag]["aktuell"] = bas
            data["poang"][lag]["regeringsstod"] = False
    # Nollställ checkbox-tillstånd
    if "checkbox_states" in data:
        data["checkbox_states"] = {}
    
    # Nollställ team orders
    if "team_orders" in data:
        data["team_orders"] = {}
    
    # Rensa fas_start_time
    if "fas_start_time" in data:
        del data["fas_start_time"]
    
    # Nollställ teamens arbete (backlog)
    if "backlog" in data:
        data["backlog"] = clone_backlog_for_teams(data.get("lag", []))
    
    save_game_data(spel_id, data)
    return redirect(url_for("admin.admin_panel", spel_id=spel_id))

@admin_bp.route("/admin/<spel_id>/aktivitetskort")
def admin_aktivitetskort(spel_id):
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    laglista = data["lag"]
    html = f'''
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/app.css?v=5">
    <link rel="stylesheet" href="/static/print.css" media="print">
    <div class="container">
    <h1>Aktivitetskort för spel {spel_id}</h1>
    <p><b>Datum:</b> {data["datum"]} <b>Plats:</b> {data["plats"]}</p>
    <p><b>Antal spelare:</b> {data["antal_spelare"]}</p>
    
    <hr>
    '''
    
    for lag in laglista:
        if lag in AKTIVITETSKORT:
            html += f'<h2>🟢 Team {lag} – Aktivitetskort</h2>'
            html += '<div class="cards-container force-break">'
            
            # Skapa kort för alla spelare i laget (2 med uppdrag, resten blanka)
            kort = AKTIVITETSKORT[lag]
            
            # Kort 1 med uppdrag
            html += f'''
            <div class="activity-card">
                <div class="card-header">
                    <h3>{lag} Kort 1: {kort[0]["titel"]}</h3>
                </div>
                <div class="card-content">
                    <div class="card-section">
                        <h4>Uppdrag</h4>
                        <p>{kort[0]["uppdrag"]}</p>
                    </div>
                    <div class="card-section">
                        <h4>Mål</h4>
                        <p>{kort[0]["mål"]}</p>
                    </div>
                    <div class="card-section">
                        <h4>Belöning</h4>
                        <p>{kort[0]["belöning"]}</p>
                    </div>
                    {f'<div class="card-section"><h4>Risk</h4><p>{kort[0]["risk"]}</p></div>' if "risk" in kort[0] else ''}
                    {f'<div class="card-section"><h4>Bonus</h4><p>{kort[0]["bonus"]}</p></div>' if "bonus" in kort[0] else ''}
                </div>
            </div>
            '''
            
            # Kort 2 med uppdrag
            html += f'''
            <div class="activity-card">
                <div class="card-header">
                    <h3>{lag} Kort 2: {kort[1]["titel"]}</h3>
                </div>
                <div class="card-content">
                    <div class="card-section">
                        <h4>Uppdrag</h4>
                        <p>{kort[1]["uppdrag"]}</p>
                    </div>
                    <div class="card-section">
                        <h4>Mål</h4>
                        <p>{kort[1]["mål"]}</p>
                    </div>
                    <div class="card-section">
                        <h4>Belöning</h4>
                        <p>{kort[1]["belöning"]}</p>
                    </div>
                    {f'<div class="card-section"><h4>Risk</h4><p>{kort[1]["risk"]}</p></div>' if "risk" in kort[1] else ''}
                    {f'<div class="card-section"><h4>Bonus</h4><p>{kort[1]["bonus"]}</p></div>' if "bonus" in kort[1] else ''}
                </div>
            </div>
            '''
            
            # Lägg till blanka kort för resten av spelarna
            for i in range(3, 11):  # Upp till 10 spelare per lag
                html += f'''
                <div class="activity-card">
                    <div class="card-header">
                        <h3>{lag} Kort {i}: Blankt</h3>
                    </div>
                    <div class="card-content">
                        <div class="card-section">
                            <h4>Uppdrag</h4>
                            <p><em>Du har inget särskilt uppdrag. Fokusera på ditt teams mål.</em></p>
                        </div>
                        <div class="card-section">
                            <h4>Mål</h4>
                            <p><em>Arbeta med ditt team för att slutföra era uppgifter.</em></p>
                        </div>
                        <div class="card-section">
                            <h4>Belöning</h4>
                            <p><em>Din belöning kommer från teamets framgång.</em></p>
                        </div>
                    </div>
                </div>
                '''
            
            html += '</div>'
        else:
            # Om laget inte har aktivitetskort, skapa blanka kort för alla spelare
            html += f'<h2>🟢 Team {lag} – Aktivitetskort</h2>'
            html += '<div class="cards-container force-break">'
            
            # Skapa blanka kort för alla spelare i laget
            for i in range(1, 11):  # Upp till 10 spelare per lag
                html += f'''
                <div class="activity-card">
                    <div class="card-header">
                        <h3>{lag} Kort {i}: Blankt</h3>
                    </div>
                    <div class="card-content">
                        <div class="card-section">
                            <h4>Uppdrag</h4>
                            <p><em>Du har inget särskilt uppdrag. Fokusera på ditt teams mål.</em></p>
                        </div>
                        <div class="card-section">
                            <h4>Mål</h4>
                            <p><em>Arbeta med ditt team för att slutföra era uppgifter.</em></p>
                        </div>
                        <div class="card-section">
                            <h4>Belöning</h4>
                            <p><em>Din belöning kommer från teamets framgång.</em></p>
                        </div>
                    </div>
                </div>
                '''
            
            html += '</div>'
    
    html += '''
    <div class="text-center margin-top-15">
        <button onclick="window.print()">Skriv ut aktivitetskort</button>
        <a href="/admin/''' + spel_id + '''"><button type="button">Tillbaka till adminpanel</button></a>
    </div>
    </div>
    '''
    
    return html

@admin_bp.route("/admin/<spel_id>/orderkort")
def admin_orderkort(spel_id):
    """Visa orderkort för alla team för en specifik runda"""
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    # Hämta tillgängliga rundor
    available_rounds = get_available_rounds(spel_id)
    current_round = data.get("runda", 1)
    
    # Skapa HTML för runda-väljare
    round_selector = f'''
    <div class="card p-20 mt-3">
        <h3>Välj runda för orderkort</h3>
        <div class="flex-wrap">
    '''
    
    for runda in available_rounds:
        round_selector += f'''
            <a href="/admin/{spel_id}/orderkort/{runda}" class="btn {'is-primary' if runda == current_round else 'is-secondary'}">
                Runda {runda}
            </a>
        '''
    
    round_selector += '''
        </div>
        <p class="mt-3 text-sm text-muted">
            Klicka på en runda för att skriva ut orderkort för alla team.
        </p>
    </div>
    '''
    
    html = f'''
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/app.css?v=5">
    <div class="container">
        <h1>Orderkort för spel {spel_id}</h1>
        <p><b>Datum:</b> {data["datum"]} <b>Plats:</b> {data["plats"]}</p>
        <p><b>Antal spelare:</b> {data["antal_spelare"]}</p>
        <p><b>Aktuell runda:</b> {current_round}</p>
        
        {round_selector}
        
        <div class="text-center mt-4">
            <a href="/admin/{spel_id}" class="secondary ghost">Tillbaka till adminpanel</a>
        </div>
    </div>
    '''
    
    return html

@admin_bp.route("/admin/<spel_id>/orderkort/<int:runda>")
def admin_orderkort_runda(spel_id, runda):
    """Visa orderkort för en specifik runda"""
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    # Kontrollera att rundan är giltig
    available_rounds = get_available_rounds(spel_id)
    if runda not in available_rounds:
        return f"Runda {runda} är inte tillgänglig för detta spel.", 404
    
    # Generera orderkort HTML
    orderkort_html = generate_orderkort_html(spel_id, runda)
    
    return orderkort_html

@admin_bp.route("/admin/<spel_id>/view_order/<team_name>")
def admin_view_order(spel_id, team_name):
    """Visa inskickad order för ett specifikt team"""
    try:
        # Ladda speldata
        data = load_game_data(spel_id)
        if not data:
            return "Spel hittades inte", 404
        
        # Kontrollera att teamet finns
        if team_name not in data.get("lag", []):
            return "Team hittades inte", 404
        
        # Hämta order för aktuell runda
        orders_key = f"orders_round_{data['runda']}"
        team_orders = data.get("team_orders", {}).get(orders_key, {}).get(team_name)
        
        if not team_orders:
            return "Ingen order hittad för detta team", 404
        
        # Generera HTML för att visa ordern
        order_html = generate_order_view_html(spel_id, team_name, team_orders, data)
        
        return order_html
    except Exception as e:
        return f"Fel: {str(e)}", 500

@admin_bp.route("/admin/<spel_id>/edit_order/<team_name>")
def admin_edit_order(spel_id, team_name):
    """Edit a team order using the existing admin session."""
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    if team_name not in data.get("lag", []):
        return "Teamet hittades inte.", 404
    if data.get("fas") not in ("Orderfas", "Diplomatifas"):
        return (
            f"Orderredigering är tillgänglig under order- och diplomatifas. "
            f"Nuvarande fas: {data.get('fas', 'okänd')}"
        ), 403
    team_token = (data.get("team_tokens") or {}).get(team_name)
    if not team_token:
        return "Team-token saknas.", 404
    return redirect(f"/team/{spel_id}/{team_token}/enter_order?admin_edit=true")

def format_orders_for_chatgpt(data, all_orders):
    """Formatera order för ChatGPT enligt den nya standarden"""
    try:
        team_codes = {
            'Alfa': 'AL', 'Bravo': 'BR', 'STT': 'ST', 'FM': 'FM', 
            'BS': 'BS', 'SÄPO': 'SE', 'Regeringen': 'RG', 'USA': 'US', 'Media': 'ME'
        }
        
        formatted_lines = []
        formatted_lines.append(f"SPEL: {data['id']} | RUNDA: {data['runda']} | FAS: {data['fas']} | DATUM: {data['datum']}")
        formatted_lines.append("")
        
        for team_name, team_orders in all_orders.items():
            if team_orders and team_orders.get('orders') and team_orders['orders'].get('activities'):
                team_code = team_codes.get(team_name, team_name)
                total_hp = 0
                
                for i, activity in enumerate(team_orders['orders']['activities'], 1):
                    # Beräkna total HP
                    total_hp += activity['hp']
                    
                    # Bestäm typ
                    activity_typ = 'BYGGA' if activity['typ'] == 'bygga' else 'STÖRA'
                    
                    # Bestäm mål
                    activity_mal = 'EGET' if activity['malomrade'] == 'eget' else 'ANNAT'
                    
                    # Bestäm miljö baserat på aktivitet
                    aktivitet_lower = activity['aktivitet'].lower()
                    if any(word in aktivitet_lower for word in ['utveckling', 'bygga', 'implementera', 'pipeline', 'api']):
                        miljo = 'DEV'
                    elif 'test' in aktivitet_lower:
                        miljo = 'TEST'
                    elif any(word in aktivitet_lower for word in ['produktion', 'server', 'valservern']):
                        miljo = 'PROD'
                    else:
                        miljo = '-'
                    
                    # Prioritet baserat på ordning
                    priority = i
                    
                    # Formatera påverkar
                    paverkar_codes = []
                    for paverkar_team in activity.get('paverkar', []):
                        if paverkar_team in team_codes:
                            paverkar_codes.append(team_codes[paverkar_team])
                    paverkar_text = ','.join(paverkar_codes) if paverkar_codes else '-'
                    
                    # Use exact backlog item name if available, otherwise use custom description
                    activity_name = activity.get('aktivitet', '')
                    if activity.get('backlog_item') and activity.get('backlog_selected') != 'custom':
                        # Extract the exact backlog item name from the dropdown text
                        # The activity['aktivitet'] contains the full dropdown text like "Back-end API för inskickade röster (25 HP)"
                        # We want just the task name part
                        activity_name = activity_name.split(' (')[0] if ' (' in activity_name else activity_name
                    
                    # Skapa raden
                    line = f"TEAM: {team_code} | AKT: {activity_name[:120]} | SYFTE: {activity['syfte'][:160]} | HP: {activity['hp']} | PÅVERKAR: {paverkar_text} | TYP: {activity_typ} | MÅL: {activity_mal} | PRIO: {priority} | MILJÖ: {miljo}"
                    formatted_lines.append(line)
                
                # Lägg till summa för teamet
                formatted_lines.append(f"SUM HP TEAM {team_code} = {total_hp}")
                formatted_lines.append("")
        
        result = '\n'.join(formatted_lines)
        return result
    except Exception as e:
        print(f"Error in format_orders_for_chatgpt: {e}")
        return "Fel vid formatering av order"

@admin_bp.route("/admin/<spel_id>/order_summary")
def order_summary(spel_id):
    """Visa sammanfattning av alla teams order för ChatGPT"""
    try:
        data = load_game_data(spel_id)
        if not data:
            return "Spelet hittades inte.", 404
        
        orders_key = f"orders_round_{data['runda']}"
        all_orders = data.get("team_orders", {}).get(orders_key, {})
        
        # Formatera order för ChatGPT
        formatted_text = format_orders_for_chatgpt(data, all_orders)
        
        return render_template_string(ORDER_SUMMARY_TEMPLATE, 
                                      spel_id=spel_id,
                                      data=data,
                                      all_orders=all_orders,
                                      formatted_text=formatted_text)
    except Exception as e:
        return f"Fel: {str(e)}", 500

@admin_bp.route("/admin/<spel_id>/auto_fill_orders", methods=["POST"])
def auto_fill_orders(spel_id):
    """Auto-fyll alla teams order med test data"""
    try:
        data = load_game_data(spel_id)
        if not data:
            return jsonify({"success": False, "error": "Spelet hittades inte"}), 404
        if not data.get("test_mode"):
            error = "Auto-fyll kräver testläge"
            if request.is_json:
                return jsonify({"success": False, "error": error}), 403
            return error, 403
        push_undo(data, "Auto-fyll testdata")
        
        orders_key = f"orders_round_{data['runda']}"
        if "team_orders" not in data:
            data["team_orders"] = {}
        if orders_key not in data["team_orders"]:
            data["team_orders"][orders_key] = {}
        
        # Test data för varje team
        test_orders = {
            "Alfa": [
                {
                    "id": int(time.time() * 1000) + 1,
                    "aktivitet": "Inloggning val (15 HP)",
                    "syfte": "Genom att bygga en automatisk kedja för test och leverans hoppas teamet frigöra resurser och snabbare få ut funktionalitet i produktion. De satsar på att visa att agilt arbetssätt ger snabba resultat.",
                    "malomrade": "eget",
                    "paverkar": ["Alfa", "STT"],
                    "typ": "bygga",
                    "hp": 10,
                    "backlog_selected": "alfa_1",
                    "backlog_item": "Inloggning val"
                },
                {
                    "id": int(time.time() * 1000) + 2,
                    "aktivitet": "Back-end API för inskickade röster (25 HP)",
                    "syfte": "Säkerställa att röster kan skickas in digitalt. Målet är att kunna köra end-to-end-test med hjälp av STT:s testmiljö. Om detta lyckas stärker det Alfas position gentemot Bravo.",
                    "malomrade": "eget",
                    "paverkar": ["Alfa", "STT"],
                    "typ": "bygga",
                    "hp": 9,
                    "backlog_selected": "alfa_2",
                    "backlog_item": "Back-end API för inskickade röster"
                },
                {
                    "id": int(time.time() * 1000) + 3,
                    "aktivitet": "Kampanja mot Bravo i korridorerna",
                    "syfte": "Alfa försöker påverka Media genom att sprida berättelser om Bravos långsamma process och överdrivna dokumentation. De hoppas framstå som mer moderna och nyskapande.",
                    "malomrade": "eget",
                    "paverkar": ["Media", "Bravo"],
                    "typ": "bygga",
                    "hp": 6,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                }
            ],
            "Bravo": [
                {
                    "id": int(time.time() * 1000) + 4,
                    "aktivitet": "Grafisk visning valet - Krav (10 HP)",
                    "syfte": "Dokumentera samtliga krav för grafisk visning och sökfunktion. Teamet är övertygat om att planering i detalj är nyckeln för att hinna i tid.",
                    "malomrade": "eget",
                    "paverkar": ["Bravo"],
                    "typ": "bygga",
                    "hp": 12,
                    "backlog_selected": "bravo_1_Krav",
                    "backlog_item": "Grafisk visning valet - Krav"
                },
                {
                    "id": int(time.time() * 1000) + 5,
                    "aktivitet": "Kontakta regeringen för extra resurser",
                    "syfte": "Bravo presenterar en detaljerad kostnadsplan och argumenterar för att deras strukturerade metod ger störst chans att leverera stabilt system. De vill få resurser flyttade från Alfa.",
                    "malomrade": "eget",
                    "paverkar": ["Regeringen", "Alfa"],
                    "typ": "bygga",
                    "hp": 7,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                },
                {
                    "id": int(time.time() * 1000) + 6,
                    "aktivitet": "Sprida rykten om Alfa",
                    "syfte": "Teamet sprider via Media att Alfas experimentella metoder kan leda till säkerhetshaveri. Målet är att vinna tid genom att andra aktörer pressar Alfa.",
                    "malomrade": "eget",
                    "paverkar": ["Media", "Alfa"],
                    "typ": "bygga",
                    "hp": 6,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                }
            ],
            "STT": [
                {
                    "id": int(time.time() * 1000) + 7,
                    "aktivitet": "Infrastruktur för val (setup, hardening, konfig) (20 HP)",
                    "syfte": "STT förstärker brandväggar, loggning och övervakning för att stå emot cyberattacker. Detta är resurskrävande men viktigt.",
                    "malomrade": "eget",
                    "paverkar": ["STT"],
                    "typ": "bygga",
                    "hp": 12,
                    "backlog_selected": "stt_1",
                    "backlog_item": "Infrastruktur för val (setup, hardening, konfig)"
                },
                {
                    "id": int(time.time() * 1000) + 8,
                    "aktivitet": "Infrastruktur för deklaration (20 HP)",
                    "syfte": "Planera inför april–juni, då det är absolut förbjudet att släppa nytt i produktion. STT vill förankra reglerna hos Alfa och Bravo för att undvika konflikter senare.",
                    "malomrade": "eget",
                    "paverkar": ["Alfa", "Bravo"],
                    "typ": "bygga",
                    "hp": 7,
                    "backlog_selected": "stt_2",
                    "backlog_item": "Infrastruktur för deklaration"
                },
                {
                    "id": int(time.time() * 1000) + 9,
                    "aktivitet": "Förhandla om prioritet",
                    "syfte": "STT pressar Alfa och Bravo på extra resurser i utbyte mot att deras leveranser får gå ut i produktion. \"Den som betalar mest får företräde.\"",
                    "malomrade": "eget",
                    "paverkar": ["Alfa", "Bravo"],
                    "typ": "bygga",
                    "hp": 6,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                }
            ],
            "FM": [
                {
                    "id": int(time.time() * 1000) + 10,
                    "aktivitet": "Massiv DDOS-attack mot valservern",
                    "syfte": "Genom att koordinera botnät i Östeuropa vill FM slå ut valets front-end. Angreppet syftar till att skapa misstro hos väljarna.",
                    "malomrade": "eget",
                    "paverkar": ["STT"],
                    "typ": "forstora",
                    "hp": 8,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                },
                {
                    "id": int(time.time() * 1000) + 11,
                    "aktivitet": "Desinformationskampanj på sociala medier",
                    "syfte": "Sprida rykten om att röster kan manipuleras. FM använder trollkonton för att skapa oro och tryck på regeringen.",
                    "malomrade": "eget",
                    "paverkar": ["Regeringen", "Media"],
                    "typ": "forstora",
                    "hp": 4,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                }
            ],
            "BS": [
                {
                    "id": int(time.time() * 1000) + 12,
                    "aktivitet": "Utpressa en STT-medlem",
                    "syfte": "BS hotar en utvecklare i STT med att läcka komprometterande bilder. Om personen går med får BS insiderinformation om STT:s prioriteringar.",
                    "malomrade": "eget",
                    "paverkar": ["STT"],
                    "typ": "forstora",
                    "hp": 7,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                },
                {
                    "id": int(time.time() * 1000) + 13,
                    "aktivitet": "Manipulera databasen",
                    "syfte": "Försöker placera en backdoor i röstdatabasen för att kunna sälja resultat i efterhand.",
                    "malomrade": "eget",
                    "paverkar": ["Alfa", "Bravo"],
                    "typ": "forstora",
                    "hp": 5,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                }
            ],
            "SÄPO": [
                {
                    "id": int(time.time() * 1000) + 14,
                    "aktivitet": "Spaning på Alfa",
                    "syfte": "Misstänker infiltration i Team Alfa. SÄPO skickar underrättelsepersonal för att övervaka deras aktiviteter och identifiera spioner.",
                    "malomrade": "eget",
                    "paverkar": ["Alfa"],
                    "typ": "bygga",
                    "hp": 7,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                },
                {
                    "id": int(time.time() * 1000) + 15,
                    "aktivitet": "Samarbete med Media",
                    "syfte": "Läckor planeras där SÄPO framstår som garant för säkerheten. De vill bygga narrativ om att myndigheten är nödvändig.",
                    "malomrade": "eget",
                    "paverkar": ["Media"],
                    "typ": "bygga",
                    "hp": 5,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                }
            ],
            "Regeringen": [
                {
                    "id": int(time.time() * 1000) + 16,
                    "aktivitet": "Fördela extra resurser till Bravo",
                    "syfte": "Regeringen vill stödja det mest strukturerade teamet för att minska risken för kaos. De hoppas på ett lugnare narrativ i media.",
                    "malomrade": "eget",
                    "paverkar": ["Bravo"],
                    "typ": "bygga",
                    "hp": 6,
                    "backlog_selected": "custom",
                    "backlog_item": ""
                },
                {
                    "id": int(time.time() * 1000) + 17,
                    "aktivitet": "Mörka säkerhetsbrister",
                    "syfte": "I samråd med PR-konsulter beslutar regeringen att tona ned problem med valets IT-system för att inte väcka panik.",
                    "malomrade": "eget",
                    "paverkar": ["Media", "STT"],
                    "typ": "bygga",
                    "hp": 4
                }
            ],
            "USA": [
                {
                    "id": int(time.time() * 1000) + 18,
                    "aktivitet": "Pressa regeringen att gynna ett extremparti",
                    "syfte": "USA kopplar bistånd och IT-stöd till politiska krav. Hotar att strypa tillgången till Office 365-licenser om regeringen inte samarbetar.",
                    "malomrade": "eget",
                    "paverkar": ["Regeringen"],
                    "typ": "bygga",
                    "hp": 8
                },
                {
                    "id": int(time.time() * 1000) + 19,
                    "aktivitet": "Erbjuda säkerhetsinformation till STT",
                    "syfte": "Lämna \"strategiska tips\" om FM:s metoder, men med syfte att skapa beroende av amerikansk teknologi.",
                    "malomrade": "eget",
                    "paverkar": ["STT"],
                    "typ": "bygga",
                    "hp": 4
                }
            ],
            "Media": [
                {
                    "id": int(time.time() * 1000) + 20,
                    "aktivitet": "Publicera artikel om misstänkt sabotage i Alfa",
                    "syfte": "Skapa rubriker om att utvecklingen är saboterad. Oavsett fakta får detta klick och skadar Alfas rykte.",
                    "malomrade": "eget",
                    "paverkar": ["Alfa"],
                    "typ": "bygga",
                    "hp": 7
                },
                {
                    "id": int(time.time() * 1000) + 21,
                    "aktivitet": "Granskning av regeringens mörkläggning",
                    "syfte": "Publicera uppgifter om att regeringen undanhåller allvarliga säkerhetsproblem. Detta ger stort genomslag internationellt.",
                    "malomrade": "eget",
                    "paverkar": ["Regeringen"],
                    "typ": "bygga",
                    "hp": 5
                }
            ]
        }
        
        # Fyll i order för varje team
        base_time = int(time.time() * 1000)
        for i, team_name in enumerate(data["lag"]):
            if team_name in test_orders:
                # Skapa unika ID:n för varje aktivitet
                team_orders = []
                for j, activity in enumerate(test_orders[team_name]):
                    activity_copy = activity.copy()
                    activity_copy["id"] = base_time + (i * 100) + j
                    team_orders.append(activity_copy)
                
                data["team_orders"][orders_key][team_name] = {
                    "submitted_at": time.time(),
                    "phase": data["fas"],
                    "round": data["runda"],
                    "orders": {
                        "activities": team_orders,
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    },
                    "final": True
                }
        
        save_game_data(spel_id, data)
        
        # Return info about which teams were processed
        processed_teams = [team for team in data["lag"] if team in test_orders]
        if request.is_json:
            return jsonify({
                "success": True,
                "message": f"Auto-fyllde order för {len(processed_teams)} team: {', '.join(processed_teams)}",
                "processed_teams": processed_teams,
                "total_teams": len(data["lag"])
            })
        return redirect(url_for("admin.admin_panel", spel_id=spel_id))
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Fel: {str(e)}"}), 500

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
    
    # Bygg HTML för varje lag med förbättrad layout
    html_parts = []
    for lag in data["lag"]:
        if lag in data["backlog"]:
            # Beräkna totala HP för laget först
            if lag == "Bravo":
                total_estimaterade = sum(sum(fas["estimaterade_hp"] for fas in uppgift["faser"]) for uppgift in data["backlog"][lag])
                total_spenderade = sum(sum(fas["spenderade_hp"] for fas in uppgift["faser"]) for uppgift in data["backlog"][lag])
            else:
                total_estimaterade = sum(uppgift["estimaterade_hp"] for uppgift in data["backlog"][lag])
                total_spenderade = sum(uppgift["spenderade_hp"] for uppgift in data["backlog"][lag])
            
            # Skapa team-kort header
            progress_percent = (total_spenderade / total_estimaterade * 100) if total_estimaterade > 0 else 0
            progress_color = "#28a745" if progress_percent >= 100 else "#ffc107" if progress_percent > 50 else "#dc3545"
            
            html_parts.append(f'''
            <div class="team-backlog-card">
                <div class="team-header">
                    <div class="team-info">
                        <h3>✅ Team {lag}</h3>
                        <div class="team-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" data-width="{min(progress_percent, 100)}" data-color="{progress_color}"></div>
                            </div>
                            <span class="progress-text">{total_spenderade}/{total_estimaterade} HP ({progress_percent:.0f}%)</span>
                        </div>
                    </div>
                </div>
                <div class="team-content">
            ''')
            
            if lag == "Bravo":
                # Bravo - GANTT-stil med faser - Explicit layout utan CSS-beroende
                html_parts.append('''
                <div class="backlog-table-container">
                    <table class="backlog-table table-fixed" data-team="Bravo">
                        <thead>
                            <tr>
                                <th class="w-35">Uppgift</th>
                                <th class="w-15 text-center">Krav</th>
                                <th class="w-15 text-center">Design</th>
                                <th class="w-15 text-center">Utveckling</th>
                                <th class="w-15 text-center">Test</th>
                                <th class="w-5 text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>
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
                    status_icon = "✅" if uppgift["slutford"] else "🔄"
                    
                    html_parts.append(f'''
                    <tr class="{status_class}">
                        <td class="{task_class} w-35"><strong>{uppgift["namn"]}</strong></td>
                        <td class="w-15 text-center">
                            <input type="number" name="spenderade_{uppgift['id']}_Krav" value="{krav['spenderade_hp']}" min="0" class="compact-input">
                            <span>/</span>
                            <input type="number" name="estimaterade_{uppgift['id']}_Krav" value="{krav['estimaterade_hp']}" min="0" class="compact-input" readonly>
                        </td>
                        <td class="w-15 text-center">
                            <input type="number" name="spenderade_{uppgift['id']}_Design" value="{design['spenderade_hp']}" min="0" class="compact-input">
                            <span>/</span>
                            <input type="number" name="estimaterade_{uppgift['id']}_Design" value="{design['estimaterade_hp']}" min="0" class="compact-input" readonly>
                        </td>
                        <td class="w-15 text-center">
                            <input type="number" name="spenderade_{uppgift['id']}_Utveckling" value="{utveckling['spenderade_hp']}" min="0" class="compact-input">
                            <span>/</span>
                            <input type="number" name="estimaterade_{uppgift['id']}_Utveckling" value="{utveckling['estimaterade_hp']}" min="0" class="compact-input" readonly>
                        </td>
                        <td class="w-15 text-center">
                            <input type="number" name="spenderade_{uppgift['id']}_Test" value="{test['spenderade_hp']}" min="0" class="compact-input">
                            <span>/</span>
                            <input type="number" name="estimaterade_{uppgift['id']}_Test" value="{test['estimaterade_hp']}" min="0" class="compact-input" readonly>
                        </td>
                        <td class="status-cell w-5 text-center">
                            <span class="status-badge">{status_icon} {total_spenderade}/{total_estimaterade}</span>
                        </td>
                    </tr>
                    ''')
                
                html_parts.append('''
                        </tbody>
                    </table>
                </div>
                ''')
                
            else:
                # Alfa och STT - enkel tabell
                html_parts.append('''
                <div class="backlog-table-container">
                    <table class="backlog-table">
                        <thead>
                            <tr>
                                <th>Uppgift</th>
                                <th>Handlingspoäng</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                ''')
                
                for uppgift in data["backlog"][lag]:
                    is_aterkommande = "typ" in uppgift and uppgift["typ"] == "aterkommande"
                    status_class = "slutford" if uppgift["slutford"] and not is_aterkommande else "pa_gang"
                    if is_aterkommande:
                        status_class = "aterkommande"
                    typ_text = f" ({uppgift['typ']})" if "typ" in uppgift else ""
                    
                    # Only show checkmark for completed non-recurring tasks
                    task_class = "task-completed" if uppgift["slutford"] and not is_aterkommande else ""
                    status_icon = "✅" if uppgift["slutford"] and not is_aterkommande else "🔄" if not is_aterkommande else "🔄"
                    
                    html_parts.append(f'''
                    <tr class="{status_class}">
                        <td class="{task_class}"><strong>{uppgift["namn"]}{typ_text}</strong></td>
                        <td class="hp-inputs">
                            <input type="number" name="spenderade_{uppgift['id']}" value="{uppgift['spenderade_hp']}" min="0" class="compact-input">
                            <span>/</span>
                            <input type="number" name="estimaterade_{uppgift['id']}" value="{uppgift['estimaterade_hp']}" min="0" class="compact-input" readonly>
                        </td>
                        <td class="status-cell">
                            <span class="status-badge">{status_icon} {uppgift['spenderade_hp']}/{uppgift['estimaterade_hp']}</span>
                        </td>
                    </tr>
                    ''')
                
                html_parts.append('''
                        </tbody>
                    </table>
                </div>
                ''')
            
            html_parts.append('''
                </div>
            </div>
            ''')
    
    # Bygg komplett HTML med förbättrad layout
    html = f'''
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/app.css?v=5">
    <link rel="stylesheet" href="/static/print.css" media="print">
    
    <style>
    /* Enhanced input fields for backlog page only */
    .compact-input {{
        width: 60px !important;
        height: 36px !important;
        padding: 6px 8px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        text-align: center !important;
        border: 2px solid #e8e9ea !important;
        border-radius: 6px !important;
        background: white !important;
        transition: all 0.2s ease !important;
    }}
    
    .compact-input:focus {{
        outline: none !important;
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        transform: scale(1.05) !important;
    }}
    
    .compact-input[readonly] {{
        background: #f8f9fa !important;
        color: #6c757d !important;
        border-color: #e8e9ea !important;
        cursor: not-allowed !important;
    }}
    
    /* Remove the tiny spinner arrows */
    .compact-input::-webkit-outer-spin-button,
    .compact-input::-webkit-inner-spin-button {{
        -webkit-appearance: none !important;
        margin: 0 !important;
    }}
    
    .compact-input[type=number] {{
        -moz-appearance: textfield !important;
    }}
    </style>
    
    <div class="container">
        <div class="backlog-header">
            <h1>Team Backlogs – Runda {data.get("runda", 1)}</h1>
            <p class="backlog-subtitle">Uppdatera teamens arbete och handlingspoäng</p>
        </div>
        
        <form method="post" class="backlog-form">
            <div class="backlog-grid">
                {''.join(html_parts)}
            </div>
            
            <div class="backlog-actions">
                <button type="submit" class="success">💾 Spara ändringar</button>
                <a href="/admin/{spel_id}" class="secondary ghost">← Tillbaka till adminpanelen</a>
            </div>
        </form>
    </div>
    '''
    
    return Markup(html)

@admin_bp.route("/admin/delete_game/<spel_id>", methods=["POST"])
def delete_game_route(spel_id):
    """Route handler for deleting a game - delegates to game_management.delete_game"""
    try:
        result = delete_game(spel_id)
        # If delete_game returns a redirect, follow it
        if hasattr(result, 'status_code') and result.status_code == 302:
            return result
        # Otherwise, redirect to admin start page
        return redirect(url_for("admin.admin_start"))
    except Exception as e:
        print(f"Error deleting game {spel_id}: {e}")
        return redirect(url_for("admin.admin_start"))

@admin_bp.route("/admin/download_game/<spel_id>")
def download_game(spel_id):
    """Download game data as JSON file"""
    try:
        data = load_game_data(spel_id)
        if not data:
            return "Game not found", 404
        
        # Create filename with game info
        filename = f"stabsspel_{data.get('datum', 'unknown')}_{data.get('plats', 'unknown')}_{spel_id}.json"
        
        # Create response with JSON data
        from flask import Response
        response = Response(
            json.dumps(data, ensure_ascii=False, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/json; charset=utf-8'
            }
        )
        return response
        
    except Exception as e:
        print(f"Error downloading game {spel_id}: {e}")
        return f"Error downloading game: {e}", 500

@admin_bp.route("/admin/upload_game", methods=["GET", "POST"])
def upload_game():
    """Upload and restore game from JSON file"""
    if request.method == "GET":
        # Show upload form
        return '''
        <!DOCTYPE html>
        <html lang="sv">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ladda upp spel - Stabsspel Admin</title>
            <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="/static/app.css?v=5">
            <style>
                .upload-container {
                    max-width: 600px;
                    margin: 2rem auto;
                    padding: 2rem;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .upload-form {
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                }
                .file-input {
                    padding: 1rem;
                    border: 2px dashed #ddd;
                    border-radius: 8px;
                    text-align: center;
                    cursor: pointer;
                    transition: border-color 0.3s;
                }
                .file-input:hover {
                    border-color: #007bff;
                }
                .file-input input[type="file"] {
                    display: none;
                }
                .btn {
                    padding: 0.75rem 1.5rem;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    text-decoration: none;
                    display: inline-block;
                    text-align: center;
                }
                .btn-primary {
                    background: #007bff;
                    color: white;
                }
                .btn-secondary {
                    background: #6c757d;
                    color: white;
                }
                .btn:hover {
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="page-header">
                    <h1>📁 Ladda upp spel</h1>
                    <p class="page-subtitle">Återställ spel från JSON-fil</p>
                </div>
                
                <div class="upload-container">
                    <form method="post" enctype="multipart/form-data" class="upload-form">
                        <div class="file-input" onclick="document.getElementById('gameFile').click()">
                            <input type="file" id="gameFile" name="gameFile" accept=".json" required>
                            <p>📄 Klicka här för att välja JSON-fil</p>
                            <small>Välj en .json-fil som tidigare laddats ner från Stabsspel</small>
                        </div>
                        
                        <div style="display: flex; gap: 1rem; justify-content: center;">
                            <button type="submit" class="btn btn-primary">📤 Ladda upp spel</button>
                            <a href="/admin" class="btn btn-secondary">🔙 Tillbaka till admin</a>
                        </div>
                    </form>
                </div>
            </div>
            
            <script>
                document.getElementById('gameFile').addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        const label = document.querySelector('.file-input p');
                        label.textContent = `📄 Vald fil: ${file.name}`;
                    }
                });
            </script>
        </body>
        </html>
        '''
    
    elif request.method == "POST":
        try:
            # Check if file was uploaded
            if 'gameFile' not in request.files:
                return "No file uploaded", 400
            
            file = request.files['gameFile']
            if file.filename == '':
                return "No file selected", 400
            
            if not file.filename.endswith('.json'):
                return "File must be a JSON file", 400
            
            # Read and parse JSON
            try:
                game_data = json.load(file)
            except json.JSONDecodeError as e:
                return f"Invalid JSON file: {e}", 400
            
            # Validate game data structure
            required_fields = ['id', 'datum', 'plats', 'runda', 'fas']
            for field in required_fields:
                if field not in game_data:
                    return f"Invalid game file: missing field '{field}'", 400
            
            # Generate new ID to avoid conflicts
            import time
            new_id = f"{int(time.time())}"
            game_data['id'] = new_id
            game_data['spel_id'] = new_id
            
            # Save the game
            save_game_data(new_id, game_data)
            
            return f'''
            <!DOCTYPE html>
            <html lang="sv">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Spel uppladdat - Stabsspel Admin</title>
                <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
                <link rel="stylesheet" href="/static/app.css?v=5">
            </head>
            <body>
                <div class="container">
                    <div class="page-header">
                        <h1>✅ Spel uppladdat!</h1>
                        <p class="page-subtitle">Spelet har återställts framgångsrikt</p>
                    </div>
                    
                    <div style="max-width: 600px; margin: 2rem auto; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <h3>📋 Spelinformation:</h3>
                        <ul>
                            <li><strong>Datum:</strong> {game_data.get('datum', 'Okänt')}</li>
                            <li><strong>Plats:</strong> {game_data.get('plats', 'Okänt')}</li>
                            <li><strong>Runda:</strong> {game_data.get('runda', 'Okänt')}</li>
                            <li><strong>Fas:</strong> {game_data.get('fas', 'Okänt')}</li>
                            <li><strong>Nytt ID:</strong> {new_id}</li>
                        </ul>
                        
                        <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;">
                            <a href="/admin/{new_id}" class="btn btn-primary">🎮 Öppna spel</a>
                            <a href="/admin" class="btn btn-secondary">🔙 Tillbaka till admin</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
            
        except Exception as e:
            print(f"Error uploading game: {e}")
            return f"Error uploading game: {e}", 500

# HTML Template för order sammanfattning för ChatGPT
ORDER_SUMMARY_TEMPLATE = """
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Sammanfattning - LLM</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #2c3e50;
            line-height: 1.6;
            padding: 20px;
        }7371
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            overflow: hidden;
            border: 1px solid #e8e9ea;
        }
        
        .header {
            background: linear-gradient(135deg, #4a5a6c 0%, #5a6a7c 100%);
            color: white;
            padding: 36px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute; inset: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
            pointer-events: none;
        }
        
        .header h1 {
            font-size: clamp(24px, 4vw, 36px);
            margin-bottom: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.95;
            font-weight: 500;
            position: relative;
            z-index: 1;
        }
        
        .game-info {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 24px 28px;
            border-bottom: 1px solid #e8e9ea;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        
        .game-info span {
            background: white;
            padding: 10px 18px;
            border-radius: 20px;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border: 1px solid #e8e9ea;
            color: #2c3e50;
            font-size: 14px;
        }
        
        .content {
            padding: 32px;
        }
        
        .copy-section {
            background: #f8f9fa;
            border: 1px solid #e8e9ea;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 32px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        
        .copy-section h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .copy-text {
            background: white;
            border: 1px solid #e8e9ea;
            border-radius: 8px;
            padding: 24px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            position: relative;
            color: #2c3e50;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        
        .team-section {
            margin-bottom: 32px;
            border: 1px solid #e8e9ea;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            background: white;
        }
        
        .team-header {
            background: linear-gradient(135deg, #4a5a6c 0%, #5a6a7c 100%);
            color: white;
            padding: 24px 28px;
            font-size: 1.3em;
            font-weight: 600;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .team-header.alfa { background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); }
        .team-header.bravo { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }
        .team-header.stt { background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); }
        .team-header.fm { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
        .team-header.bs { background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); }
        .team-header.sapo { background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); }
        .team-header.regeringen { background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%); }
        .team-header.usa { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }
        .team-header.media { background: linear-gradient(135deg, #e67e22 0%, #d35400 100%); }
        
        .team-content {
            padding: 28px;
        }
        
        .team-activities-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .activity-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .activity-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }
        
        .activity-card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .activity-badge {
            background: rgba(255,255,255,0.2);
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
        }
        
        .hp-badge {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        
        .activity-card-body {
            padding: 20px;
        }
        
        .activity-main {
            margin-bottom: 20px;
        }
        
        .activity-title {
            margin: 0 0 10px 0;
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            line-height: 1.4;
        }
        
        .activity-purpose {
            margin: 0;
            color: #6c757d;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .activity-details {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }
        
        .detail-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0;
        }
        
        .detail-icon {
            font-size: 16px;
            width: 24px;
            text-align: center;
        }
        
        .detail-content {
            flex: 1;
        }
        
        .detail-label {
            font-size: 12px;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
        }
        
        .detail-value {
            font-size: 14px;
            color: #2c3e50;
            font-weight: 500;
        }
        
        @media (max-width: 768px) {
            .team-activities-grid {
                grid-template-columns: 1fr;
            }
            .activity-card {
                margin-bottom: 15px;
            }
        }
        
        .no-orders {
            text-align: center;
            padding: 48px;
            color: #5a6a7c;
            font-style: italic;
            background: #f8f9fa;
            border-radius: 12px;
            border: 1px solid #e8e9ea;
        }
        
        .back-button {
            display: inline-block;
            background: #5a6a7c;
            color: white;
            padding: 14px 28px;
            text-decoration: none;
            border-radius: 8px;
            margin-top: 24px;
            transition: all 0.3s ease;
            font-weight: 600;
            border: 1px solid #4a5a6c;
        }
        
        .back-button:hover {
            background: #4a5a6c;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .team-order-link {
            background: #4a5a6c;
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: all 0.3s ease;
            border: 1px solid #4a5a6c;
        }
        
        .team-order-link:hover {
            background: #3a4a5c;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            color: white;
            text-decoration: none;
        }
        
        .team-header a:hover {
            background: rgba(255,255,255,0.3) !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Order Sammanfattning</h1>
            <p>Kopiera texten nedan och klistra in i Grok, Gemini eller ChatGPT. Nyhetsrubriker skrivs på papper och läses i studion — de lagras inte här.</p>
        </div>
        
        <div class="game-info">
            <span>🎮 Spel: {{ data.id }}</span>
            <span>🔄 Runda: {{ data.runda }}</span>
            <span>⏱️ Fas: {{ data.fas }}</span>
            <span>📅 Datum: {{ data.datum }}</span>
        </div>
        
        <div class="content">
            <div class="copy-section">
                <h3>Kopiera till LLM</h3>
                <div class="copy-text" id="copyText">
{% if formatted_text %}
{{ formatted_text }}

Baserat på dessa order, ge förslag på:
1. Uppdaterad backlogstatus: hur många fler (eller färre) poäng varje team har på sina arbetsuppgifter. Använd EXAKTA namnen från backlog-uppgifterna (t.ex. "Back-end API för inskickade röster", "Grafisk visning valet - Krav", "Infrastruktur för val").
2. Plus/minus poäng för varje team inför nästa runda.
3. Konsekvenser av teamens handlingar.
4. Eventuella konflikter mellan team.
5. Samlad resultatrapport i tidningsformat.

VIKTIGT: När du refererar till backlog-uppgifter, använd alltid de EXAKTA namnen som visas i ordern (t.ex. "Back-end API för inskickade röster" istället för "Röst-API").
{% else %}
Inga order har skickats in ännu.
{% endif %}
                </div>
                <button class="copy-button" onclick="copyToClipboard()" style="background: #4a5a6c; color: white; border: 1px solid #4a5a6c; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s ease;">📋 Kopiera</button>
            </div>
            
            <h2>📊 Detaljerad Översikt</h2>
            
            {% if all_orders %}
                {% for team_name, team_orders in all_orders.items() %}
                    {% if team_orders and team_orders.orders and team_orders.orders.activities %}
                    <div class="team-section">
                        <div class="team-header {{ team_name.lower() }}" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>🟢 Team {{ team_name }}</span>
                            <a href="/admin/{{ spel_id }}/view_order/{{ team_name }}" target="_blank" style="background: rgba(255,255,255,0.2); color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px; border: 1px solid rgba(255,255,255,0.3); transition: all 0.3s ease;">
                                👁️ View {{ team_name }} Order
                            </a>
                        </div>
                        <div class="team-content">
                            <div class="team-activities-grid">
                                {% for activity in team_orders.orders.activities %}
                                <div class="activity-card">
                                    <div class="activity-card-header">
                                        <div class="activity-number">
                                            <span class="activity-badge">{{ loop.index }}</span>
                                        </div>
                                        <div class="activity-hp">
                                            <span class="hp-badge">{{ activity.hp }} HP</span>
                                        </div>
                                    </div>
                                    
                                    <div class="activity-card-body">
                                        <div class="activity-main">
                                            <h4 class="activity-title">{{ activity.aktivitet }}</h4>
                                            <p class="activity-purpose">{{ activity.syfte }}</p>
                                        </div>
                                        
                                        <div class="activity-details">
                                            <div class="detail-item">
                                                <div class="detail-icon">🎯</div>
                                                <div class="detail-content">
                                                    <div class="detail-label">Målområde</div>
                                                    <div class="detail-value">{{ 'Eget mål' if activity.malomrade == 'eget' else 'Annat mål' }}</div>
                                                </div>
                                            </div>
                                            
                                            <div class="detail-item">
                                                <div class="detail-icon" style="color: {{ '#28a745' if activity.typ == 'bygga' else '#dc3545' }}">{{ '🔨' if activity.typ == 'bygga' else '💥' }}</div>
                                                <div class="detail-content">
                                                    <div class="detail-label">Typ</div>
                                                    <div class="detail-value">{{ 'Bygga/Förstärka' if activity.typ == 'bygga' else 'Förstöra/Störa' }}</div>
                                                </div>
                                            </div>
                                            
                                            <div class="detail-item">
                                                <div class="detail-icon">👥</div>
                                                <div class="detail-content">
                                                    <div class="detail-label">Påverkar</div>
                                                    <div class="detail-value">{{ ', '.join(activity.paverkar) if activity.paverkar else 'Ingen' }}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    {% endif %}
                {% endfor %}
            {% else %}
                <div class="no-orders">
                    <h3>Inga order har skickats in ännu</h3>
                    <p>När teamen skickar in sina order kommer de att visas här.</p>
                </div>
            {% endif %}
            
            <a href="/admin/{{ spel_id }}" class="secondary ghost">← Tillbaka till Admin Panel</a>
        </div>
    </div>
    
    <script>
        function copyToClipboard() {
            const textElement = document.getElementById('copyText');
            const text = textElement.textContent || textElement.innerText;
            
            // Try modern clipboard API first
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(function() {
                    showCopySuccess();
                }).catch(function(err) {
                    console.error('Modern clipboard failed: ', err);
                    fallbackCopyTextToClipboard(text);
                });
            } else {
                // Use fallback method
                fallbackCopyTextToClipboard(text);
            }
        }
        
        function fallbackCopyTextToClipboard(text) {
            // Create a temporary textarea element
            const textArea = document.createElement("textarea");
            textArea.value = text;
            
            // Make it invisible but still selectable
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            textArea.style.opacity = "0";
            textArea.style.pointerEvents = "none";
            textArea.setAttribute('readonly', '');
            
            document.body.appendChild(textArea);
            
            // Select and copy
            textArea.focus();
            textArea.select();
            textArea.setSelectionRange(0, 99999); // For mobile devices
            
            try {
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (successful) {
                    showCopySuccess();
                } else {
                    showCopyError();
                }
            } catch (err) {
                console.error('Fallback copy failed: ', err);
                document.body.removeChild(textArea);
                showCopyError();
            }
        }
        
        function showCopySuccess() {
            const button = document.querySelector('.copy-button');
            if (button) {
                const originalText = button.textContent;
                const originalStyle = button.style.cssText;
                
                button.textContent = '✅ Kopierat!';
                button.style.background = '#28a745';
                button.style.borderColor = '#28a745';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.cssText = originalStyle;
                }, 2000);
            }
        }
        
        function showCopyError() {
            const button = document.querySelector('.copy-button');
            if (button) {
                const originalText = button.textContent;
                const originalStyle = button.style.cssText;
                
                button.textContent = '❌ Kopiera manuellt';
                button.style.background = '#dc3545';
                button.style.borderColor = '#dc3545';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.cssText = originalStyle;
                }, 3000);
            }
            
            // Also show a more helpful message
            alert('Automatisk kopiering misslyckades. Markera texten i rutan ovan och kopiera manuellt (Ctrl+C eller Cmd+C).');
        }
    </script>
</body>
</html>
"""