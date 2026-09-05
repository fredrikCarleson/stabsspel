"""
Team order entry routes for Stabsspel
Handles team-specific order entry with authorization and mobile-responsive design
"""

from flask import Blueprint, request, render_template_string, redirect, url_for, jsonify, make_response, g
from models import (
    validate_team_token,
    get_team_by_token,
    load_game_data,
    save_game_data,
    get_phase_timer,
    BACKLOG,
    game_lock_for,
    active_teams,
)
from admin_routes import create_team_overview, check_admin_session
from gm_console import (
    can_submit_orders,
    can_withdraw_orders,
    validate_order_hp,
    withdraw_order,
    sync_regeringen_fordelning,
    effective_hp,
    _fordelning_items,
)
import json
import time

team_order_bp = Blueprint('team_order', __name__)


@team_order_bp.before_request
def lock_team_game_mutation():
    """Keep team order read-modify-write operations atomic per game."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    spel_id = (request.view_args or {}).get("spel_id")
    if not spel_id:
        return None
    lock = game_lock_for(spel_id)
    lock.acquire()
    g._team_game_mutation_lock = lock
    return None


@team_order_bp.teardown_request
def unlock_team_game_mutation(_error=None):
    lock = getattr(g, "_team_game_mutation_lock", None)
    if lock is not None:
        del g._team_game_mutation_lock
        lock.release()


def _merge_server_activity_fields(existing_record, order_data):
    """Preserve server-owned apply/ref metadata when a browser saves again."""
    previous = ((existing_record or {}).get("orders") or {}).get("activities") or []
    by_id = {
        str(item.get("id")): item
        for item in previous
        if isinstance(item, dict) and item.get("id") is not None
    }
    for item in (order_data or {}).get("activities") or []:
        if not isinstance(item, dict):
            continue
        item.pop("_order_ref", None)
        item.pop("backlog_applied", None)
        old = by_id.get(str(item.get("id"))) if item.get("id") is not None else None
        if not old:
            continue
        for key in ("_order_ref", "backlog_applied"):
            if key in old:
                item[key] = old[key]
    return order_data


def _has_meaningful_activity(order_data, team_name=None, data=None):
    if any(
        isinstance(item, dict) and str(item.get("aktivitet") or "").strip()
        for item in (order_data or {}).get("activities") or []
    ):
        return True
    if team_name == "Regeringen" and data is not None:
        return bool(_fordelning_items(order_data, active_teams(data), team_name))
    return False


def format_time(seconds):
    """Format seconds to MM:SS"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def generate_backlog_options():
    """Generate HTML options for backlog dropdown"""
    options = ['<option value="">Välj backlog-uppgift...</option>']
    
    for team_name, tasks in BACKLOG.items():
        options.append(f'<optgroup label="Team {team_name}">')
        
        for task in tasks:
            if 'faser' in task:  # Bravo tasks with phases
                for phase in task['faser']:
                    option_text = f"{task['namn']} - {phase['namn']} ({phase['estimaterade_hp']} HP)"
                    option_value = f"{task['id']}_{phase['namn']}"
                    options.append(f'<option value="{option_value}">{option_text}</option>')
            else:  # Regular tasks (Alfa, STT)
                option_text = f"{task['namn']} ({task['estimaterade_hp']} HP)"
                option_value = task['id']
                options.append(f'<option value="{option_value}">{option_text}</option>')
        
        options.append('</optgroup>')
    
    options.append('<option value="custom">Annat (egen beskrivning)</option>')
    return '\n'.join(options)


def backlog_choice_meta():
    """Dropdown value → team, name and estimated HP for order-form prefill."""
    meta = {}
    for team_name, tasks in BACKLOG.items():
        for task in tasks:
            if "faser" in task:
                for phase in task["faser"]:
                    namn = f"{task['namn']} - {phase['namn']}"
                    meta[f"{task['id']}_{phase['namn']}"] = {
                        "team": team_name,
                        "namn": namn,
                        "hp": int(phase["estimaterade_hp"]),
                        "syfte": f"Driva {namn} vidare i backlog",
                    }
            else:
                namn = task["namn"]
                meta[task["id"]] = {
                    "team": team_name,
                    "namn": namn,
                    "hp": int(task["estimaterade_hp"]),
                    "syfte": f"Driva {namn} vidare i backlog",
                }
    return meta


@team_order_bp.route("/team/<spel_id>/<token>/enter_order")
def team_enter_order(spel_id, token):
    """Team order entry page with authorization"""
    
    # Validate token and get team
    team_name = get_team_by_token(spel_id, token)
    if not team_name:
        return "Ogiltig eller utgången länk.", 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return "Spelet hittades inte.", 404
    
    # Check if game is active
    if data.get("avslutat", False):
        return "Spelet är avslutat.", 403
    
    # Check if orders can be submitted
    if not can_submit_orders(data):
        return f"Order kan bara lämnas under Orderfas eller Diplomatifas. Nuvarande fas: {data['fas']}", 403
    
    # Get remaining time
    remaining_time = get_phase_timer(data)
    
    # Check if team has already submitted orders for this round
    orders_key = f"orders_round_{data['runda']}"
    team_orders = data.get("team_orders", {}).get(orders_key, {}).get(team_name)
    
    # Orders loading logic (debug removed)
    
    # Check if this is admin edit mode
    is_admin_session = check_admin_session(spel_id)
    is_admin_edit = request.args.get('admin_edit') == 'true' and is_admin_session
    
    # Check if order is already submitted (final) - but allow admin editing
    is_submitted = team_orders and team_orders.get("final", False) and not is_admin_edit
    
    # Get team's max HP
    team_entry = (data.get("poang") or {}).get(team_name) or {}
    team_max_hp = effective_hp(team_entry) if team_entry else 25
    roster = active_teams(data)
    
    # Generate team overview HTML
    team_overview_html = create_team_overview(data)
    
    # Create response with anti-caching headers
    html_content = render_template_string(TEAM_ORDER_TEMPLATE, 
                                         spel_id=spel_id, 
                                         team_name=team_name, 
                                         token=token,
                                         data=data,
                                         is_admin_edit=is_admin_edit,
                                         show_gm_back=is_admin_edit,
                                         remaining_time=remaining_time,
                                         team_max_hp=team_max_hp,
                                         existing_orders=team_orders,
                                         is_submitted=is_submitted,
                                         format_time=format_time,
                                         backlog_options=generate_backlog_options(),
                                         backlog_meta=backlog_choice_meta(),
                                         team_overview_html=team_overview_html,
                                         is_regeringen=team_name == "Regeringen",
                                         active_team_names=roster,
                                         fordelning_teams=[name for name in roster if name != team_name],
                                         existing_fordelning=((team_orders or {}).get("orders") or {}).get("hp_fordelning") or ((team_orders or {}).get("hp_fordelning_applied") or []))
    
    response = make_response(html_content)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@team_order_bp.route("/team/<spel_id>/<token>/save_order", methods=["POST"])
def team_save_order(spel_id, token):
    """Save team order (auto-save)"""
    
    # Validate token and get team
    team_name = get_team_by_token(spel_id, token)
    if not team_name:
        return jsonify({"success": False, "error": "Ogiltig länk."}), 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Spelet hittades inte."}), 404
    
    # Check if orders can be submitted
    if not can_submit_orders(data):
        return jsonify({"success": False, "error": "Order kan inte lämnas i den här fasen."}), 403
    
    # Get order data from request
    order_data = request.get_json()
    if not order_data:
        return jsonify({"success": False, "error": "Ingen orderdata togs emot."}), 400
    
    # Validate HP usage
    validation_result = validate_order_hp(data, team_name, order_data)
    if not validation_result["valid"]:
        return jsonify({"success": False, "error": validation_result["error"]}), 400
    
    # Initialize team_orders structure if it doesn't exist
    if "team_orders" not in data:
        data["team_orders"] = {}
    
    orders_key = f"orders_round_{data['runda']}"
    if orders_key not in data["team_orders"]:
        data["team_orders"][orders_key] = {}

    existing = data["team_orders"][orders_key].get(team_name, {})
    admin_edit = request.args.get("admin_edit") == "true" and check_admin_session(spel_id)
    if existing.get("final") and not admin_edit:
        return jsonify({"success": False, "error": "Ordern är redan skickad."}), 403
    order_data = _merge_server_activity_fields(existing, order_data)

    # Save order data
    saved = {
        "submitted_at": existing.get("submitted_at") or time.time(),
        "updated_at": time.time(),
        "phase": data["fas"],
        "round": data["runda"],
        "orders": order_data
    }
    if existing.get("final") and admin_edit:
        saved["final"] = True
        saved["edited_by_gm"] = True
        saved["submitted_at"] = existing.get("submitted_at") or time.time()
    data["team_orders"][orders_key][team_name] = saved
    
    # Save to file
    try:
        save_game_data(spel_id, data)
        return jsonify({"success": True, "message": "Order saved successfully"})
    except PermissionError:
        return jsonify({"success": False, "error": "File temporarily locked, please try again"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save order: {str(e)}"}), 500

@team_order_bp.route("/team/<spel_id>/<token>/submit_order", methods=["POST"])
def team_submit_order(spel_id, token):
    """Submit final team order"""
    
    # Validate token and get team
    team_name = get_team_by_token(spel_id, token)
    if not team_name:
        return jsonify({"success": False, "error": "Ogiltig länk."}), 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Spelet hittades inte."}), 404
    
    # Check if orders can be submitted
    if not can_submit_orders(data):
        return jsonify({"success": False, "error": "Order kan inte lämnas i den här fasen."}), 403
    
    # Get order data from request
    order_data = request.get_json()
    if not order_data:
        return jsonify({"success": False, "error": "Ingen orderdata togs emot."}), 400
    
    # Validate HP usage
    validation_result = validate_order_hp(data, team_name, order_data)
    if not validation_result["valid"]:
        return jsonify({"success": False, "error": validation_result["error"]}), 400
    
    # Initialize team_orders structure if it doesn't exist
    if "team_orders" not in data:
        data["team_orders"] = {}
    
    orders_key = f"orders_round_{data['runda']}"
    if orders_key not in data["team_orders"]:
        data["team_orders"][orders_key] = {}
    
    existing = data["team_orders"][orders_key].get(team_name, {})
    admin_edit = request.args.get("admin_edit") == "true" and check_admin_session(spel_id)
    if existing.get("final") and not admin_edit:
        return jsonify({"success": False, "error": "Ordern är redan skickad."}), 403
    if not _has_meaningful_activity(order_data, team_name, data):
        return jsonify({"success": False, "error": "Order must contain an activity"}), 400
    order_data = _merge_server_activity_fields(existing, order_data)

    # Save final order data
    saved = {
        "submitted_at": existing.get("submitted_at") or time.time(),
        "updated_at": time.time(),
        "phase": data["fas"],
        "round": data["runda"],
        "orders": order_data,
        "final": True
    }
    if admin_edit:
        saved["edited_by_gm"] = True
    data["team_orders"][orders_key][team_name] = saved
    if team_name == "Regeringen":
        sync_regeringen_fordelning(data, team_name)
    
    # Save to file
    try:
        save_game_data(spel_id, data)
        return jsonify({"success": True, "message": "Order submitted successfully"})
    except PermissionError:
        return jsonify({"success": False, "error": "File temporarily locked, please try again"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to submit order: {str(e)}"}), 500


@team_order_bp.route("/team/<spel_id>/<token>/withdraw_order", methods=["POST"])
def team_withdraw_order(spel_id, token):
    """Let a team reopen a submitted order during Orderfas."""
    team_name = get_team_by_token(spel_id, token)
    if not team_name:
        return jsonify({"success": False, "error": "Ogiltig länk."}), 403
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Spelet hittades inte."}), 404
    if not can_withdraw_orders(data):
        return jsonify({"success": False, "error": "Order kan bara återtas under Orderfas."}), 403
    try:
        withdraw_order(data, team_name)
        save_game_data(spel_id, data)
        return jsonify({"success": True, "message": "Order reopened"})
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except PermissionError:
        return jsonify({"success": False, "error": "File temporarily locked, please try again"}), 503

@team_order_bp.route("/team/<spel_id>/<token>/timer")
def team_timer(spel_id, token):
    """Get remaining time for current phase"""
    
    # Validate token
    team_name = get_team_by_token(spel_id, token)
    if not team_name:
        return jsonify({"error": "Ogiltig länk."}), 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"error": "Spelet hittades inte."}), 404
    
    remaining_time = get_phase_timer(data)
    
    return jsonify({
        "remaining_time": remaining_time,
        "formatted_time": format_time(remaining_time),
        "phase": data["fas"],
        "round": data["runda"]
    })

# HTML Template for the team order entry page
TEAM_ORDER_TEMPLATE = """
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Ange order – {{ team_name }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/app.css?v=44">
</head>
<body class="order-page">
    <div class="order-wrap">
        <header class="order-head">
            {% if show_gm_back %}
            <p class="order-gm-back no-print">
                <a href="/admin/{{ spel_id }}" class="secondary sm">Tillbaka till spelledarpanel</a>
            </p>
            {% endif %}
            {% if is_admin_edit %}
            <div class="order-admin-banner">
                Du redigerar {{ team_name }}s order. Gå tillbaka till spelledarpanelen när du är klar.
            </div>
            {% endif %}
            <p class="order-kicker">Ange order</p>
            <h1>{{ team_name }}</h1>
            <p class="order-meta">Runda {{ data.runda }} · {{ data.fas }}</p>
            {% if is_submitted and not is_admin_edit %}
            <p class="order-state is-submitted">Order skickad</p>
            {% else %}
            <p class="order-state is-draft">Utkast — inte skickad</p>
            {% endif %}
        </header>
        
        <div class="order-sticky">
        <div class="timer" id="timer">
            Tid kvar: <span id="timer-display">{{ "00:00" if remaining_time <= 0 else format_time(remaining_time) }}</span>
        </div>
        
        <div class="hp-summary" id="hp-summary">
            <h4>Handlingspoäng</h4>
            <div class="hp-display">
                <span class="hp-stat"><small>Max</small><strong id="max-hp">{{ team_max_hp }}</strong></span>
                <span class="hp-stat"><small>Använt</small><strong id="used-hp">0</strong></span>
                <span class="hp-stat is-primary"><small>Kvar</small><strong id="remaining-hp" class="hp-remaining">{{ team_max_hp }}</strong></span>
            </div>
        </div>
        </div>
        
        <div class="order-form">
            <form id="orderForm">
                <div class="form-section">
                    <h3>Aktiviteter</h3>
                    <p class="text-muted mb-2">
                        Upp till 6 aktiviteter. Spara utkast när ni vill.
                        Skicka innan tiden tar slut — därefter kan ni inte ändra själva.
                    </p>
                    {% if is_regeringen %}
                    <div class="hp-grant-box" id="hp-grant-box">
                        <h4>Fördela HP till andra lag</h4>
                        <p class="text-muted mb-2">Politiska resurser. Fördelad HP lämnar kassan och kan inte också läggas på en order.</p>
                        <div id="hp-grant-rows"></div>
                        <button type="button" class="secondary sm" onclick="addGrantRow()">+ Lägg till fördelning</button>
                    </div>
                    {% endif %}
                    
                    <div id="activities-container">
                        <!-- Activities will be added here -->
                    </div>
                    
                    <button type="button" class="secondary add-activity" onclick="addActivity()">
                        Lägg till aktivitet
                    </button>
                </div>
                
                <div class="submit-section">
                    <p class="submit-help">
                        Utkast syns hos spelledaren men räknas inte förrän ni skickar.
                    </p>
                    <button type="submit" class="primary submit-btn" id="submitBtn" {% if is_submitted %}disabled{% endif %}>
                        {% if is_submitted and not is_admin_edit %}
                            Order skickad
                        {% else %}
                            Skicka slutgiltig order
                        {% endif %}
                    </button>
                    <button type="button" class="secondary save-btn" onclick="saveOrder(false)" {% if is_submitted %}disabled{% endif %}>
                        {% if is_submitted and not is_admin_edit %}
                            Order skickad
                        {% else %}
                            Spara utkast
                        {% endif %}
                    </button>
                    {% if is_submitted and not is_admin_edit and data.fas == "Orderfas" %}
                    <button type="button" class="secondary withdraw-btn" onclick="withdrawOrder()">
                        Återta order
                    </button>
                    {% endif %}
                </div>
            </form>
        </div>
        
        <!-- Team Overview Section - Moved to bottom -->
        {% if team_overview_html %}
        <details class="order-overview">
            <summary>Andra lags arbete</summary>
            <div class="team-overview-section">
                {{ team_overview_html | safe }}
            </div>
        </details>
        {% endif %}
        
        <div id="status-message" aria-live="polite" aria-atomic="true"></div>
    </div>
    
    <script>
        let activities = [];
        let autoSaveInterval;
        let timerInterval;
        const BACKLOG_META = {{ backlog_meta | tojson }};
        const TEAM_MAX_HP = {{ team_max_hp }};
        const ACTIVE_TEAMS = {{ active_team_names | tojson }};
        const GRANT_TEAMS = {{ fordelning_teams | tojson }};
        const IS_REGERINGEN = {{ 'true' if is_regeringen else 'false' }};
        let hpGrants = {{ existing_fordelning | tojson }};
        
        // Initialize form
        document.addEventListener('DOMContentLoaded', function() {
            initializeForm();
            startTimer();
            // Removed auto-save functionality
            
            // Check if order is already submitted
            {% if is_submitted %}
                // Disable form if order is already submitted (but not in admin edit mode)
                {% if not is_admin_edit %}
                disableForm();
                {% endif %}
            {% endif %}
        });
        
        function initializeForm() {
            // Load existing orders if any
            try {
                {% if existing_orders %}
                    console.log('Existing orders found:', {{ existing_orders | tojson }});
                    const existingOrdersData = {{ existing_orders | tojson }};
                    if (existingOrdersData && existingOrdersData.orders) {
                        activities = existingOrdersData.orders.activities || [];
                        if (existingOrdersData.orders.hp_fordelning) {
                            hpGrants = existingOrdersData.orders.hp_fordelning;
                        }
                        console.log('Loaded activities:', activities);
                    } else {
                        console.log('No activities in existing orders');
                        activities = [];
                    }
                {% else %}
                    console.log('No existing orders found');
                    activities = [];
                {% endif %}
            } catch (error) {
                console.error('Error loading existing orders:', error);
                activities = [];
            }
            
            renderActivities();
            renderGrantRows();
            updateHPSummary();
        }
        
        function addActivity() {
            if (activities.length >= 6) {
                showStatus('Du kan bara ha 6 aktiviteter', 'error');
                return;
            }
            
            const activity = {
                id: Date.now(),
                aktivitet: '',
                syfte: '',
                malomrade: 'eget',
                paverkar: [],
                typ: 'bygga',
                hp: 0,
                backlog_selected: 'custom',
                backlog_item: ''
            };
            
            activities.push(activity);
            renderActivities();
        }
        
        function removeActivity(id) {
            activities = activities.filter(a => a.id !== id);
            renderActivities();
            updateHPSummary();
        }
        
        function renderActivities() {
            const container = document.getElementById('activities-container');
            container.innerHTML = '';
            
            activities.forEach((activity, index) => {
                const activityHtml = `
                    <div class="activity-row" data-activity-id="${activity.id}">
                        <div class="activity-header">
                            <div class="activity-number">${index + 1}</div>
                            <button type="button" class="remove-activity" onclick="removeActivity(${activity.id})">
                                Ta bort
                            </button>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Aktivitet (Vad?)</label>
                                <select 
                                    id="backlog-select-${activity.id}"
                                    onchange="handleBacklogSelection(${activity.id}, this.value)"
                                    style="margin-bottom: 10px;"
                                >
                                    {{ backlog_options | safe }}
                                </select>
                                <textarea 
                                    id="activity-text-${activity.id}"
                                    placeholder="Beskriv aktiviteten..."
                                    onchange="updateActivity(${activity.id}, 'aktivitet', this.value)"
                                >${activity.aktivitet || ""}</textarea>
                            </div>
                            
                            <div class="form-group">
                                <label>Syfte/Mål (Varför?)</label>
                                <textarea 
                                    placeholder="Beskriv syftet..."
                                    onchange="updateActivity(${activity.id}, 'syfte', this.value)"
                                >${activity.syfte}</textarea>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Målområde</label>
                                <div class="radio-group">
                                    <label>
                                        <input type="radio" name="malomrade_${activity.id}" value="eget" 
                                               ${activity.malomrade === 'eget' ? 'checked' : ''}
                                               onchange="updateActivity(${activity.id}, 'malomrade', this.value)">
                                        Eget mål
                                    </label>
                                    <label>
                                        <input type="radio" name="malomrade_${activity.id}" value="annat" 
                                               ${activity.malomrade === 'annat' ? 'checked' : ''}
                                               onchange="updateActivity(${activity.id}, 'malomrade', this.value)">
                                        Annat mål
                                    </label>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label>Typ av handling</label>
                                <div class="radio-group">
                                    <label>
                                        <input type="radio" name="typ_${activity.id}" value="bygga" 
                                               ${activity.typ === 'bygga' ? 'checked' : ''}
                                               onchange="updateActivity(${activity.id}, 'typ', this.value)">
                                        Bygga/Förstärka
                                    </label>
                                    <label>
                                        <input type="radio" name="typ_${activity.id}" value="forstora" 
                                               ${activity.typ === 'forstora' ? 'checked' : ''}
                                               onchange="updateActivity(${activity.id}, 'typ', this.value)">
                                        Förstöra/Störa
                                    </label>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Påverkar/Vem</label>
                                <div class="checkbox-group">
                                    ${ACTIVE_TEAMS.map(function (team) {
                                        return '<label><input type="checkbox" value="' + team + '" onchange="updatePaverkar(' + activity.id + ', this.value, this.checked)">' + team + '</label>';
                                    }).join('')}
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label>Handlingspoäng (HP)</label>
                                <input type="number" min="0" class="hp-input"
                                       value="${activity.hp}"
                                       oninput="updateActivity(${activity.id}, 'hp', parseInt(this.value, 10) || 0)">
                            </div>
                        </div>
                    </div>
                `;
                container.innerHTML += activityHtml;
            });
            
            // Restore checkbox states
            activities.forEach(activity => {
                activity.paverkar.forEach(team => {
                    // Find checkbox within this specific activity's container
                    const activityContainer = document.querySelector(`[data-activity-id="${activity.id}"]`);
                    if (activityContainer) {
                        const checkbox = activityContainer.querySelector(`input[value="${team}"]`);
                        if (checkbox) checkbox.checked = true;
                    }
                });
                
                // Restore backlog selection state
                const select = document.getElementById(`backlog-select-${activity.id}`);
                if (select && activity.backlog_selected) {
                    select.value = activity.backlog_selected;
                }
            });
        }
        
        function updateActivity(id, field, value) {
            const activity = activities.find(a => a.id === id);
            if (activity) {
                activity[field] = value;
                updateHPSummary();
            }
        }
        
        function handleBacklogSelection(id, value) {
            const activity = activities.find(a => a.id === id);
            if (!activity) return;

            if (value === 'custom' || value === '') {
                activity.backlog_selected = value === 'custom' ? 'custom' : '';
                activity.backlog_item = '';
                if (value === '') {
                    activity.aktivitet = '';
                    activity.syfte = '';
                    activity.hp = 0;
                    activity.paverkar = [];
                }
            } else {
                const meta = BACKLOG_META[value];
                if (!meta) return;
                activity.aktivitet = meta.namn;
                activity.syfte = meta.syfte;
                activity.hp = meta.hp;
                activity.typ = 'bygga';
                activity.malomrade = 'eget';
                activity.paverkar = [meta.team];
                activity.backlog_selected = value;
                activity.backlog_item = value;
            }
            renderActivities();
            updateHPSummary();
        }
        
        function updatePaverkar(id, team, checked) {
            const activity = activities.find(a => a.id === id);
            if (activity) {
                if (checked && !activity.paverkar.includes(team)) {
                    activity.paverkar.push(team);
                } else if (!checked && activity.paverkar.includes(team)) {
                    activity.paverkar = activity.paverkar.filter(t => t !== team);
                }
            }
        }
        
        function grantHPTotal() {
            if (!IS_REGERINGEN || !Array.isArray(hpGrants)) return 0;
            return hpGrants.reduce(function (sum, row) {
                return sum + (parseInt(row && row.hp, 10) || 0);
            }, 0);
        }

        function usedOrderHP() {
            const activityHP = activities.reduce((sum, activity) => sum + (parseInt(activity.hp, 10) || 0), 0);
            return activityHP + grantHPTotal();
        }

        function addGrantRow() {
            if (!Array.isArray(hpGrants)) hpGrants = [];
            hpGrants.push({ lag: GRANT_TEAMS[0] || '', hp: 0 });
            renderGrantRows();
            updateHPSummary();
        }

        function removeGrantRow(index) {
            hpGrants.splice(index, 1);
            renderGrantRows();
            updateHPSummary();
        }

        function updateGrantRow(index, field, value) {
            if (!hpGrants[index]) return;
            if (field === 'hp') hpGrants[index].hp = parseInt(value, 10) || 0;
            else hpGrants[index][field] = value;
            updateHPSummary();
        }

        function renderGrantRows() {
            const root = document.getElementById('hp-grant-rows');
            if (!root) return;
            if (!Array.isArray(hpGrants) || !hpGrants.length) {
                hpGrants = [];
                root.innerHTML = '<p class="text-muted">Ingen fördelning ännu.</p>';
                return;
            }
            root.innerHTML = hpGrants.map(function (row, index) {
                const options = GRANT_TEAMS.map(function (team) {
                    const selected = team === row.lag ? ' selected' : '';
                    return '<option value="' + team + '"' + selected + '>' + team + '</option>';
                }).join('');
                return '<div class="hp-grant-row">' +
                    '<select data-field="lag" onchange="updateGrantRow(' + index + ', this.dataset.field, this.value)">' + options + '</select>' +
                    '<input type="number" min="0" data-field="hp" value="' + (parseInt(row.hp, 10) || 0) + '" oninput="updateGrantRow(' + index + ', this.dataset.field, this.value)">' +
                    '<button type="button" class="secondary sm" onclick="removeGrantRow(' + index + ')">Ta bort</button>' +
                    '</div>';
            }).join('');
        }

        function updateHPSummary() {
            const usedHP = usedOrderHP();
            const remainingHP = TEAM_MAX_HP - usedHP;
            const remainingElement = document.getElementById("remaining-hp");
            const summary = document.getElementById("hp-summary");
            document.getElementById("used-hp").textContent = usedHP;
            remainingElement.textContent = remainingHP;
            remainingElement.className = remainingHP < 0 ? "hp-over" : "hp-remaining";
            if (summary) summary.classList.toggle("is-over", remainingHP < 0);
            document.querySelectorAll(".hp-input").forEach(function (el) {
                el.classList.toggle("is-over", remainingHP < 0);
            });
            const submitBtn = document.getElementById("submitBtn");
            {% if not is_submitted %}
            if (submitBtn) submitBtn.disabled = remainingHP < 0;
            {% endif %}
        }
        
        function startTimer() {
            timerInterval = setInterval(() => {
                fetch('/team/{{ spel_id }}/{{ token }}/timer')
                    .then(response => response.json())
                    .then(data => {
                        if (data.remaining_time <= 0) {
                            // Time's up - just play sound and show warning
                            playAlarmSound();
                            showStatus('Tiden är ute! Ordern kommer att skickas automatiskt när fasen ändras.', 'warning');
                        } else {
                            document.getElementById('timer-display').textContent = data.formatted_time;
                        }
                    })
                    .catch(error => {
                        console.error('Timer error:', error);
                    });
            }, 1000);
        }
        
        function withdrawOrder() {
            if (!confirm('Återta ordern? Du kan ändra och skicka igen under orderfasen.')) {
                return;
            }
            fetch('/team/{{ spel_id }}/{{ token }}/withdraw_order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    showStatus('Fel: ' + (data.error || 'Kunde inte återta ordern'), 'error');
                }
            })
            .catch(() => {
                showStatus('Fel: Kunde inte återta ordern', 'error');
            });
        }

        function playAlarmSound() {
            const audio = new Audio('/static/alarm.mp3');
            audio.play().catch(error => {
                console.error('Could not play alarm sound:', error);
            });
        }
        
        // Auto-save functionality removed
        
        function saveOrder(isFinal = false, retryCount = 0) {
            const usedHP = usedOrderHP();
            if (usedHP > TEAM_MAX_HP) {
                showStatus(`Du har använt ${usedHP} HP men har bara ${TEAM_MAX_HP} HP tillgängliga!`, 'error');
                return;
            }
            
            const orderData = {
                activities: activities,
                hp_fordelning: IS_REGERINGEN ? hpGrants.filter(function (row) {
                    return row && row.lag && (parseInt(row.hp, 10) || 0) > 0;
                }) : [],
                timestamp: new Date().toISOString()
            };
            
            const url = (isFinal ? '/team/{{ spel_id }}/{{ token }}/submit_order' : '/team/{{ spel_id }}/{{ token }}/save_order'){% if is_admin_edit %} + '?admin_edit=true'{% endif %};
            const maxRetries = 3;
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (isFinal) {
                        {% if is_admin_edit %}
                        showStatus('Slutgiltig order skickad. Du kan gå tillbaka till spelledarpanelen.', 'success');
                        {% else %}
                        showStatus('Slutgiltig order skickad.', 'success');
                        document.getElementById('submitBtn').disabled = true;
                        document.getElementById('submitBtn').textContent = 'Order skickad';
                        // Hide save button when order is submitted
                        const saveBtn = document.querySelector('.save-btn');
                        if (saveBtn) {
                            saveBtn.style.display = 'none';
                        }
                        {% endif %}
                    } else {
                        {% if is_admin_edit %}
                        showStatus('Utkast sparat.', 'success');
                        {% else %}
                        showStatus('Utkast sparat.', 'success');
                        {% endif %}
                    }
                } else {
                    // Om filen är låst, försök igen
                    if (data.error && data.error.includes('temporarily locked') && retryCount < maxRetries) {
                        setTimeout(() => {
                            saveOrder(isFinal, retryCount + 1);
                        }, 500 * (retryCount + 1)); // Exponential backoff
                        showStatus('Försöker spara igen...', 'info');
                    } else {
                        showStatus('Fel: ' + data.error, 'error');
                    }
                }
            })
            .catch(error => {
                console.error('Save error:', error);
                showStatus('Fel vid sparande av order', 'error');
            });
        }
        
        function submitOrder(isAutoSubmit = false) {
            const usedHP = usedOrderHP();
            
            if (usedHP > TEAM_MAX_HP) {
                showStatus(`Du har använt ${usedHP} HP men har bara ${TEAM_MAX_HP} HP tillgängliga!`, 'error');
                return;
            }
            
            if (activities.length === 0 && grantHPTotal() <= 0) {
                showStatus('Du måste lägga till minst en aktivitet eller fördela HP!', 'error');
                return;
            }
            
            if (!isAutoSubmit) {
                const remainingHP = TEAM_MAX_HP - usedHP;
                const leftover = remainingHP > 0
                    ? `Ni har ${remainingHP} HP kvar. `
                    : "";
                if (!confirm(leftover + "Skicka den slutgiltiga ordern nu? Efter det kan ni inte ändra den själva.")) {
                    return;
                }
            }
            
            saveOrder(true);
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status-message');
            
            // Create modern status message
            const statusClass = type === 'success' ? 'status-success' : 
                               type === 'error' ? 'status-error' : 'status-info';
            
            statusDiv.innerHTML = `
                <div class="status-message ${statusClass}">
                    <div class="status-icon">
                        ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
                    </div>
                    <div class="status-text">${message}</div>
                </div>
            `;
            
            // Auto-hide after 2 seconds for success messages
            if (type === 'success') {
                setTimeout(() => {
                    statusDiv.innerHTML = '';
                }, 2000);
            }
        }
        
        function disableForm() {
            // Disable all form inputs
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.disabled = true;
            });
            
            // Disable buttons
            const buttons = document.querySelectorAll('button');
            buttons.forEach(button => {
                if (button.classList.contains('withdraw-btn')) return;
                button.disabled = true;
            });
            
            // Hide save button and update submit button
            const saveBtn = document.querySelector('.save-btn');
            const submitBtn = document.getElementById('submitBtn');
            if (saveBtn) {
                saveBtn.style.display = 'none';
            }
            if (submitBtn) {
                submitBtn.textContent = 'Order skickad';
            }
        }
        
        // Form submission
        document.getElementById('orderForm').addEventListener('submit', function(e) {
            e.preventDefault();
            submitOrder();
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (timerInterval) clearInterval(timerInterval);
        });
    </script>
</body>
</html>
"""
