"""
Team order entry routes for Stabsspel
Handles team-specific order entry with authorization and mobile-responsive design
"""

from flask import Blueprint, request, render_template_string, redirect, url_for, jsonify, make_response
from models import validate_team_token, get_team_by_token, load_game_data, save_game_data, get_phase_timer, BACKLOG
from admin_routes import create_team_overview, check_admin_session
from gm_console import can_submit_orders, can_withdraw_orders, validate_order_hp, withdraw_order
import json
import time

team_order_bp = Blueprint('team_order', __name__)


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


@team_order_bp.route("/team/<spel_id>/<token>/enter_order")
def team_enter_order(spel_id, token):
    """Team order entry page with authorization"""
    
    # Validate token and get team
    team_name = get_team_by_token(spel_id, token)
    if not team_name:
        return "❌ Invalid or expired access token", 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return "❌ Game not found or corrupted", 404
    
    # Check if game is active
    if data.get("avslutat", False):
        return "❌ This game has ended", 403
    
    # Check if orders can be submitted
    if not can_submit_orders(data):
        return f"❌ Orders can only be submitted during Orderfas or Diplomatifas. Current phase: {data['fas']}", 403
    
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
    team_max_hp = 25  # Default
    for team, hp in data.get("poang", {}).items():
        if team == team_name:
            team_max_hp = hp.get("aktuell", 25)
            # Add regeringsstöd bonus if applicable
            if hp.get("regeringsstod", False):
                team_max_hp += 10
            break
    
    # Generate team overview HTML
    team_overview_html = create_team_overview(data)
    
    # Create response with anti-caching headers
    html_content = render_template_string(TEAM_ORDER_TEMPLATE, 
                                         spel_id=spel_id, 
                                         team_name=team_name, 
                                         token=token,
                                         data=data,
                                         is_admin_edit=is_admin_edit,
                                         show_gm_back=is_admin_session,
                                         remaining_time=remaining_time,
                                         team_max_hp=team_max_hp,
                                         existing_orders=team_orders,
                                         is_submitted=is_submitted,
                                         format_time=format_time,
                                         backlog_options=generate_backlog_options(),
                                         team_overview_html=team_overview_html)
    
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
        return jsonify({"success": False, "error": "Invalid token"}), 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Game not found or corrupted"}), 404
    
    # Check if orders can be submitted
    if not can_submit_orders(data):
        return jsonify({"success": False, "error": "Orders not allowed in current phase"}), 403
    
    # Get order data from request
    order_data = request.get_json()
    if not order_data:
        return jsonify({"success": False, "error": "No order data received"}), 400
    
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
        return jsonify({"success": False, "error": "Order already submitted"}), 403

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
        return jsonify({"success": False, "error": "Invalid token"}), 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Game not found or corrupted"}), 404
    
    # Check if orders can be submitted
    if not can_submit_orders(data):
        return jsonify({"success": False, "error": "Orders not allowed in current phase"}), 403
    
    # Get order data from request
    order_data = request.get_json()
    if not order_data:
        return jsonify({"success": False, "error": "No order data received"}), 400
    
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
    
    # Save final order data
    data["team_orders"][orders_key][team_name] = {
        "submitted_at": time.time(),
        "updated_at": time.time(),
        "phase": data["fas"],
        "round": data["runda"],
        "orders": order_data,
        "final": True
    }
    
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
        return jsonify({"success": False, "error": "Invalid token"}), 403
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"success": False, "error": "Game not found or corrupted"}), 404
    if not can_withdraw_orders(data):
        return jsonify({"success": False, "error": "Orders can only be withdrawn during Orderfas"}), 403
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
        return jsonify({"error": "Invalid token"}), 403
    
    # Load game data
    data = load_game_data(spel_id)
    if not data:
        return jsonify({"error": "Game not found or corrupted"}), 404
    
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
    <title>Ange Order - {{ team_name }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 1.8rem;
            margin-bottom: 10px;
        }
        
        .game-info {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .timer {
            background: #ff6b6b;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .order-form {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .form-section {
            margin-bottom: 30px;
        }
        
        .form-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        @media (min-width: 768px) {
            .form-row {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            font-weight: 600;
            margin-bottom: 5px;
            color: #2c3e50;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        .radio-group {
            display: flex;
            gap: 20px;
            margin-top: 5px;
        }
        
        .radio-group label {
            display: flex;
            align-items: center;
            font-weight: normal;
            cursor: pointer;
        }
        
        .radio-group input[type="radio"] {
            margin-right: 8px;
        }
        
        .checkbox-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 5px;
        }
        
        .checkbox-group label {
            display: flex;
            align-items: center;
            font-weight: normal;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .checkbox-group input[type="checkbox"] {
            margin-right: 8px;
        }
        
        .activity-row {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .activity-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .activity-number {
            background: #667eea;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .remove-activity {
            background: #dc3545;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .add-activity {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 18px;
            min-height: 44px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 20px;
            white-space: nowrap;
        }
        
        .submit-section {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
        
        .submit-help {
            flex: 1 0 100%;
            margin: 0 0 4px;
            color: #6c757d;
            font-size: 0.95rem;
            text-align: left;
            line-height: 1.4;
        }
        
        .save-btn,
        .submit-btn,
        .withdraw-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            border: none;
            padding: 12px 20px;
            min-height: 44px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
        }
        
        .save-btn {
            background: #6c757d;
            color: white;
        }
        
        .save-btn:hover {
            background: #5a6268;
        }
        
        .save-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        .submit-btn {
            background: #28a745;
            color: white;
        }
        
        .submit-btn:hover {
            background: #218838;
        }
        
        .submit-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        .status-message {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px 24px;
            border-radius: 12px;
            margin: 16px 0;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            animation: slideIn 0.3s ease-out;
        }
        
        .status-icon {
            margin-right: 12px;
            font-size: 1.2rem;
        }
        
        .status-text {
            font-size: 1rem;
        }
        
        .status-success {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
            border: 2px solid #28a745;
        }
        
        .status-error {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24;
            border: 2px solid #dc3545;
        }
        
        .status-info {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            color: #0c5460;
            border: 2px solid #17a2b8;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .hp-summary {
            background: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .hp-summary h4 {
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .hp-display {
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        .hp-remaining {
            color: #28a745;
        }
        
        .hp-over {
            color: #dc3545;
        }
        
        /* Team Overview Styles */
        .team-overview-section {
            margin-bottom: 20px;
        }
        
        .team-overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        
        .team-overview-card {
            background: white;
            border: 1px solid #e8e9ea;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .team-overview-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }
        
        .team-overview-header {
            color: white;
            padding: 12px 16px;
            position: relative;
        }
        
        .team-overview-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .team-overview-title h4 {
            margin: 0;
            font-size: 1em;
            font-weight: 600;
        }
        
        .team-overview-progress {
            text-align: right;
        }
        
        .team-progress-percent {
            display: block;
            font-size: 1.1em;
            font-weight: bold;
        }
        
        .team-progress-hp {
            display: block;
            font-size: 0.85em;
            opacity: 0.9;
        }
        
        .team-overview-bar {
            height: 4px;
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .team-progress-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }
        
        .team-overview-content {
            padding: 12px 16px;
        }
        
        .team-task-item {
            margin-bottom: 8px;
        }
        
        .team-task-item:last-child {
            margin-bottom: 0;
        }
        
        .team-task-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }
        
        .team-task-name {
            font-size: 0.85em;
            font-weight: 500;
            color: #2c3e50;
        }
        
        .team-task-hp {
            font-size: 0.8em;
            color: #6c757d;
            font-weight: 600;
        }
        
        .team-task-bar {
            height: 3px;
            background: #f1f3f4;
            border-radius: 2px;
            overflow: hidden;
        }
        
        .team-task-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }
        
        .team-task-more {
            text-align: center;
            padding: 8px 0;
            border-top: 1px solid #f1f3f4;
            margin-top: 8px;
        }
        
        .team-overview-empty {
            grid-column: 1 / -1;
            text-align: center;
            padding: 20px;
            color: #6c757d;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        /* Responsive adjustments for team overview */
        @media (max-width: 768px) {
            .team-overview-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            
            .team-overview-card {
                margin-bottom: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Ange Order - {{ team_name }}</h1>
            {% if show_gm_back %}
            <p class="no-print" style="margin: 0 0 12px;">
                <a href="/admin/{{ spel_id }}" style="display:inline-block; background:#e9ecef; color:#1a1a1a; padding:8px 14px; border-radius:6px; text-decoration:none; font-weight:600;">← Tillbaka till spelledarpanel</a>
            </p>
            {% endif %}
            {% if is_admin_edit %}
            <div style="background: #ffc107; color: #000; padding: 8px 16px; border-radius: 6px; margin: 10px 0; font-weight: bold; font-size: 0.9rem;">
                🔓 ADMIN — du redigerar {{ team_name }}s order. Gå tillbaka till spelledarpanelen när du är klar.
            </div>
            {% endif %}
            <div class="game-info">
                <span>🎮 Spel: {{ data.id }}</span>
                <span>🔄 Runda: {{ data.runda }}</span>
                <span>⏱️ Fas: {{ data.fas }}</span>
            </div>
        </div>
        
        <div class="timer" id="timer">
            ⏰ Tid kvar: <span id="timer-display">{{ "00:00" if remaining_time <= 0 else format_time(remaining_time) }}</span>
        </div>
        
        <div class="hp-summary">
            <h4>💪 Handlingspoäng</h4>
            <div class="hp-display">
                Max: <span id="max-hp">{{ team_max_hp }}</span> | 
                Använt: <span id="used-hp">0</span> | 
                Kvar: <span id="remaining-hp" class="hp-remaining">{{ team_max_hp }}</span>
            </div>
        </div>
        
        <div class="order-form">
            <form id="orderForm">
                <div class="form-section">
                    <h3>📝 Orderformulär</h3>
                    <p class="text-muted mb-2">
                        Fyll i orderna för denna runda (upp till 6 aktiviteter). Spara utkast när ni vill.
                        Skicka den slutgiltiga ordern innan tiden tar slut — därefter kan ni inte ändra den själva.
                    </p>
                    
                    <div id="activities-container">
                        <!-- Activities will be added here -->
                    </div>
                    
                    <button type="button" class="add-activity" onclick="addActivity()">
                        ➕ Lägg till aktivitet
                    </button>
                </div>
                
                <div class="submit-section">
                    <p class="submit-help">
                        Utkast syns hos spelledaren men räknas inte. Den gröna knappen skickar den slutgiltiga ordern.
                    </p>
                    <button type="button" class="save-btn" onclick="saveOrder(false)" {% if is_submitted %}disabled{% endif %}>
                        {% if is_submitted and not is_admin_edit %}
                            Order skickad
                        {% else %}
                            Spara utkast
                        {% endif %}
                    </button>
                    <button type="submit" class="submit-btn" id="submitBtn" {% if is_submitted %}disabled{% endif %}>
                        {% if is_submitted and not is_admin_edit %}
                            Order skickad
                        {% else %}
                            Skicka slutgiltig order
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
        <div class="team-overview-section">
            {{ team_overview_html | safe }}
        </div>
        {% endif %}
        
        <div id="status-message"></div>
    </div>
    
    <script>
        let activities = [];
        let autoSaveInterval;
        let timerInterval;
        
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
                                🗑️ Ta bort
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
                                    style="display: ${activity.backlog_selected === 'custom' || !activity.backlog_selected ? 'block' : 'none'};"
                                >${activity.aktivitet}</textarea>
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
                                <label>Målområde 🎯</label>
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
                                <label>Typ av handling ⚔️</label>
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
                                    <label><input type="checkbox" value="Alfa" onchange="updatePaverkar(${activity.id}, 'Alfa', this.checked)">Alfa</label>
                                    <label><input type="checkbox" value="Bravo" onchange="updatePaverkar(${activity.id}, 'Bravo', this.checked)">Bravo</label>
                                    <label><input type="checkbox" value="STT" onchange="updatePaverkar(${activity.id}, 'STT', this.checked)">STT</label>
                                    <label><input type="checkbox" value="FM" onchange="updatePaverkar(${activity.id}, 'FM', this.checked)">FM</label>
                                    <label><input type="checkbox" value="BS" onchange="updatePaverkar(${activity.id}, 'BS', this.checked)">BS</label>
                                    <label><input type="checkbox" value="Media" onchange="updatePaverkar(${activity.id}, 'Media', this.checked)">Media</label>
                                    <label><input type="checkbox" value="SÄPO" onchange="updatePaverkar(${activity.id}, 'SÄPO', this.checked)">SÄPO</label>
                                    <label><input type="checkbox" value="Regeringen" onchange="updatePaverkar(${activity.id}, 'Regeringen', this.checked)">Regeringen</label>
                                    <label><input type="checkbox" value="USA" onchange="updatePaverkar(${activity.id}, 'USA', this.checked)">USA</label>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label>Handlingspoäng (HP)</label>
                                <input type="number" min="0" max="{{ team_max_hp }}" 
                                       value="${activity.hp}"
                                       onchange="updateActivity(${activity.id}, 'hp', parseInt(this.value) || 0)">
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
                if (activity.backlog_selected && activity.backlog_selected !== 'custom') {
                    const select = document.getElementById(`backlog-select-${activity.id}`);
                    if (select) {
                        select.value = activity.backlog_selected;
                    }
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
            
            const textarea = document.getElementById(`activity-text-${id}`);
            const select = document.getElementById(`backlog-select-${id}`);
            
            if (value === 'custom') {
                // Show textarea for custom input
                textarea.style.display = 'block';
                activity.backlog_selected = 'custom';
                activity.backlog_item = '';
            } else if (value === '') {
                // No selection
                textarea.style.display = 'none';
                textarea.value = '';
                activity.aktivitet = '';
                activity.backlog_selected = '';
                activity.backlog_item = '';
            } else {
                // Backlog item selected
                textarea.style.display = 'none';
                const selectedOption = select.options[select.selectedIndex];
                const backlogText = selectedOption.text;
                activity.aktivitet = backlogText;
                activity.backlog_selected = value;
                activity.backlog_item = value;
            }
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
        
        function updateHPSummary() {
            const maxHP = {{ team_max_hp }};
            const usedHP = activities.reduce((sum, activity) => sum + (parseInt(activity.hp) || 0), 0);
            const remainingHP = maxHP - usedHP;
            
            document.getElementById('used-hp').textContent = usedHP;
            document.getElementById('remaining-hp').textContent = remainingHP;
            
            const remainingElement = document.getElementById('remaining-hp');
            if (remainingHP < 0) {
                remainingElement.className = 'hp-over';
            } else {
                remainingElement.className = 'hp-remaining';
            }
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
            // Validate HP before saving
            const maxHP = {{ team_max_hp }};
            const usedHP = activities.reduce((sum, activity) => sum + (parseInt(activity.hp) || 0), 0);
            
            if (usedHP > maxHP) {
                showStatus(`Du har använt ${usedHP} HP men har bara ${maxHP} HP tillgängliga!`, 'error');
                return;
            }
            
            const orderData = {
                activities: activities,
                timestamp: new Date().toISOString()
            };
            
            const url = isFinal ? '/team/{{ spel_id }}/{{ token }}/submit_order' : '/team/{{ spel_id }}/{{ token }}/save_order';
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
            const maxHP = {{ team_max_hp }};
            const usedHP = activities.reduce((sum, activity) => sum + (parseInt(activity.hp) || 0), 0);
            
            if (usedHP > maxHP) {
                showStatus(`Du har använt ${usedHP} HP men har bara ${maxHP} HP tillgängliga!`, 'error');
                return;
            }
            
            if (activities.length === 0) {
                showStatus('Du måste lägga till minst en aktivitet!', 'error');
                return;
            }
            
            // Only show confirmation dialog if not auto-submitting
            if (!isAutoSubmit) {
                if (!confirm('Skicka den slutgiltiga ordern nu? Efter det kan ni inte ändra den själva.')) {
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
                submitBtn.textContent = '✅ Order Skickad';
                submitBtn.style.background = '#28a745';
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
