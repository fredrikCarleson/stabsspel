"""
Team order entry routes for Stabsspel
Handles team-specific order entry with authorization and mobile-responsive design
"""

from flask import Blueprint, request, render_template_string, redirect, url_for, jsonify, make_response
from models import validate_team_token, get_team_by_token, load_game_data, save_game_data
import json
import time

team_order_bp = Blueprint('team_order', __name__)

def get_phase_timer(data):
    """Get remaining time for current phase"""
    # Use admin timer system instead of fas_start_time
    fas_minutes = 0
    if data["fas"] == "Orderfas":
        fas_minutes = data.get("orderfas_min", 10)
    elif data["fas"] == "Diplomatifas":
        fas_minutes = data.get("diplomatifas_min", 10)
    
    # Use admin timer system
    total_sec = fas_minutes * 60
    now = int(time.time())
    timer_status = data.get("timer_status", "stopped")
    timer_start = data.get("timer_start")
    timer_elapsed = data.get("timer_elapsed", 0)
    
    if timer_status == "running" and timer_start:
        elapsed = now - timer_start + timer_elapsed
    else:
        elapsed = timer_elapsed
    
    remaining_seconds = max(0, total_sec - elapsed)
    
    return int(remaining_seconds)

def format_time(seconds):
    """Format seconds to MM:SS"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def can_submit_orders(data):
    """Check if orders can be submitted in current phase"""
    # Orders can be submitted during Orderfas and Diplomatifas
    # regardless of timer status - timer only affects auto-submission
    return data["fas"] in ["Orderfas", "Diplomatifas"]

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
    
    # Check if order is already submitted (final)
    is_submitted = team_orders and team_orders.get("final", False)
    
    # Get team's max HP
    team_max_hp = 25  # Default
    for team, hp in data.get("poang", {}).items():
        if team == team_name:
            team_max_hp = hp.get("max_hp", 25)
            break
    
    # Create response with anti-caching headers
    html_content = render_template_string(TEAM_ORDER_TEMPLATE, 
                                         spel_id=spel_id, 
                                         team_name=team_name, 
                                         token=token,
                                         data=data,
                                         remaining_time=remaining_time,
                                         team_max_hp=team_max_hp,
                                         existing_orders=team_orders,
                                         is_submitted=is_submitted,
                                         format_time=format_time)
    
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
    
    # Initialize team_orders structure if it doesn't exist
    if "team_orders" not in data:
        data["team_orders"] = {}
    
    orders_key = f"orders_round_{data['runda']}"
    if orders_key not in data["team_orders"]:
        data["team_orders"][orders_key] = {}
    
    # Save order data
    data["team_orders"][orders_key][team_name] = {
        "submitted_at": time.time(),
        "phase": data["fas"],
        "round": data["runda"],
        "orders": order_data
    }
    
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
    
    # Initialize team_orders structure if it doesn't exist
    if "team_orders" not in data:
        data["team_orders"] = {}
    
    orders_key = f"orders_round_{data['runda']}"
    if orders_key not in data["team_orders"]:
        data["team_orders"][orders_key] = {}
    
    # Save final order data
    data["team_orders"][orders_key][team_name] = {
        "submitted_at": time.time(),
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
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 20px;
        }
        
        .submit-section {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
        
        .save-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-right: 15px;
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
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Ange Order - {{ team_name }}</h1>
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
                    <p style="color: #6c757d; margin-bottom: 20px;">
                        Fyll i dina order för denna runda. Du kan lägga till upp till 6 aktiviteter.
                    </p>
                    
                    <div id="activities-container">
                        <!-- Activities will be added here -->
                    </div>
                    
                    <button type="button" class="add-activity" onclick="addActivity()">
                        ➕ Lägg till aktivitet
                    </button>
                </div>
                
                <div class="submit-section">
                    <button type="button" class="save-btn" onclick="saveOrder(false)" {% if is_submitted %}disabled{% endif %}>
                        {% if is_submitted %}✅ Order Skickad{% else %}💾 Spara Order{% endif %}
                    </button>
                    <button type="submit" class="submit-btn" id="submitBtn" {% if is_submitted %}disabled{% endif %}>
                        {% if is_submitted %}✅ Order Skickad{% else %}📤 Slutför Order{% endif %}
                    </button>
                </div>
            </form>
        </div>
        
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
                // Disable form if order is already submitted
                disableForm();
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
                hp: 0
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
                    <div class="activity-row">
                        <div class="activity-header">
                            <div class="activity-number">${index + 1}</div>
                            <button type="button" class="remove-activity" onclick="removeActivity(${activity.id})">
                                🗑️ Ta bort
                            </button>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Aktivitet (Vad?)</label>
                                <textarea 
                                    placeholder="Beskriv aktiviteten..."
                                    onchange="updateActivity(${activity.id}, 'aktivitet', this.value)"
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
                    const checkbox = document.querySelector(`input[value="${team}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            });
        }
        
        function updateActivity(id, field, value) {
            const activity = activities.find(a => a.id === id);
            if (activity) {
                activity[field] = value;
                updateHPSummary();
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
                        showStatus('Order skickad framgångsrikt!', 'success');
                        document.getElementById('submitBtn').disabled = true;
                        document.getElementById('submitBtn').textContent = '✅ Order Skickad';
                        // Hide save button when order is submitted
                        const saveBtn = document.querySelector('.save-btn');
                        if (saveBtn) {
                            saveBtn.style.display = 'none';
                        }
                    } else {
                        showStatus('Order sparad framgångsrikt!', 'success');
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
                if (!confirm('Är du säker på att du vill skicka ordern? Du kan inte ändra den efter skickning.')) {
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
