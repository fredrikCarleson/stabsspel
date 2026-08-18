"""
Helper functions for admin routes
Extracted from admin_routes.py for better code organization
"""

def add_no_cache_headers(response):
    """Lägg till headers för att förhindra caching"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def create_team_info_js():
    """Skapa JavaScript för team-information"""
    return '''
    <script>
    function updateTeamInfo() {
        const select = document.getElementById('players_interval');
        const teamInfo = document.getElementById('team-info');
        const numPlayers = parseInt(select.value);
        
        if (numPlayers >= 27) {
            teamInfo.innerHTML = `
                <h3>Team som kommer vara med (9 st):</h3>
                <div class="team-info">
                    <h4>🧩 Grundteam (5 st):</h4>
                    <ul>
                        <li>Team Alfa</li>
                        <li>Team Bravo</li>
                        <li>STT</li>
                        <li>Främmande Makt (FM)</li>
                        <li>Brottssyndikatet (BS)</li>
                    </ul>
                    <h4>➕ Extra team (4 st):</h4>
                    <ul>
                        <li>Media</li>
                        <li>SÄPO</li>
                        <li>Regeringen</li>
                        <li>USA</li>
                    </ul>
                </div>
            `;
        } else {
            teamInfo.innerHTML = `
                <h3>Team som kommer vara med (5 st):</h3>
                <div class="team-info">
                    <h4>🧩 Grundteam:</h4>
                    <ul>
                        <li>Team Alfa</li>
                        <li>Team Bravo</li>
                        <li>STT</li>
                        <li>Främmande Makt (FM)</li>
                        <li>Brottssyndikatet (BS)</li>
                    </ul>
                    <p><em>Extra team (Media, SÄPO, Regeringen, USA) aktiveras vid 27+ spelare</em></p>
                </div>
            `;
        }
    }
    
    // Uppdatera när sidan laddas
    window.onload = function() {
        updateTeamInfo();
    };
    </script>
    '''

def create_compact_header(data, lag_html):
    """Skapa kompakt header med spelinformation"""
    return f'''
    <div class="compact-header">
        <div class="compact-header-content">
            <div class="compact-header-info">
                <p><b>Datum:</b> {data["datum"]} <b>Plats:</b> {data["plats"]} <b>Antal spelare:</b> {data["antal_spelare"]}</p>
                <p><b>Orderfas:</b> {data.get("orderfas_min", "-")} min | <b>Diplomatifas:</b> {data.get("diplomatifas_min", "-")} min</p>
            </div>
            <div class="compact-header-info">
                <p><b>Lag:</b> {lag_html}</p>
                <p>(Klicka på laget för att se dess mål)</p>
            </div>
        </div>
    </div>
    '''

def create_action_buttons(spel_id):
    """Skapa knappar för åtgärder med modern gaming-inspired design system"""
    poang_lank = f'<a href="/admin/{spel_id}/poang" class="primary">📊 Visa/ändra handlingspoäng</a>'
    aktivitetskort_lank = f'<a href="/admin/{spel_id}/aktivitetskort" target="_blank" class="info">🖨️ Skriv ut aktivitetskort</a>'
    reset_lank = f'<form method="post" action="/admin/{spel_id}/reset" class="d-inline"><button type="submit" class="warning" onclick="return confirm(\'Är du säker på att du vill återställa spelet? Detta går inte att ångra.\')">🔄 Återställ spel</button></form>'
    back_lank = f'<a href="/admin" class="secondary">← Tillbaka till adminstart</a>'
    
    return f'''
    <div class="admin-panel-actions">
        {poang_lank}
        {aktivitetskort_lank}
        {reset_lank}
        {back_lank}
    </div>
    '''

def create_script_references():
    """Skapa referenser till externa JavaScript-filer"""
    return '''
    <script src="/static/admin.js"></script>
    <script src="/static/gm-console.js?v=11"></script>
    '''

def create_delete_game_button(spel_id, label, css_class="danger sm"):
    """Button that opens the shared delete-password modal."""
    import html
    return (
        f'<button type="button" class="{css_class}" '
        f'data-delete-game-id="{html.escape(str(spel_id), quote=True)}" '
        f'data-delete-game-label="{html.escape(str(label), quote=True)}">'
        f'Ta bort</button>'
    )

def create_delete_game_modal():
    """Password modal for deleting a game. Uses existing .modal styles."""
    return '''
    <div id="deleteGameSuccess" class="notification success" style="display: none; position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 2000; max-width: 480px;">
        Spelet har tagits bort.
    </div>
    <div id="deleteGameModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Ta bort spel</h3>
                <span class="close" onclick="closeDeleteGameModal()">&times;</span>
            </div>
            <div class="modal-body">
                <p id="deleteGameLabel" class="mb-3"></p>
                <div id="deleteGameError" class="notification error" style="display: none;">
                    Felaktigt lösenord. Spelet togs inte bort.
                </div>
                <form id="deleteGameForm" method="post" action="/admin/delete_game/" autocomplete="off">
                    <input type="hidden" name="next" id="deleteGameNext" value="/">
                    <div class="form-group">
                        <label for="deleteGamePassword">Spellösenord</label>
                        <input type="password" id="deleteGamePassword" name="password" required placeholder="Ange lösenord" autocomplete="new-password">
                    </div>
                    <div class="form-actions">
                        <button type="button" onclick="closeDeleteGameModal()" class="secondary">Avbryt</button>
                        <button type="submit" class="danger">Ta bort spelet</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    <script src="/static/admin.js?v=5"></script>
    '''

def create_time_adjustment_modal(spel_id, orderfas_min, diplomatifas_min):
    """Skapa modal för att ändra fas-tider"""
    return f'''
    <!-- Time Adjustment Modal -->
    <div id="timeAdjustmentModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>⚙️ Ändra fas-tider</h3>
                <span class="close" onclick="closeTimeAdjustmentModal()">&times;</span>
            </div>
            <div class="modal-body">
                <form id="timeAdjustmentForm" method="post" action="/admin/{spel_id}/adjust_times">
                    <div class="form-group">
                        <label for="orderfas_min">⏱️ Orderfas (minuter):</label>
                        <input type="number" id="orderfas_min" name="orderfas_min" 
                               min="1" max="60" value="{orderfas_min}" required>
                    </div>
                    <div class="form-group">
                        <label for="diplomatifas_min">🤝 Diplomatifas (minuter):</label>
                        <input type="number" id="diplomatifas_min" name="diplomatifas_min" 
                               min="1" max="60" value="{diplomatifas_min}" required>
                    </div>
                    <div class="form-actions">
                        <button type="button" onclick="closeTimeAdjustmentModal()" class="secondary">Avbryt</button>
                        <button type="submit" class="success">💾 Spara ändringar</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    '''

def create_timer_controls(spel_id, remaining, timer_status):
    """Skapa timer-kontroller med design-systemets klasser"""
    return f'''
    <div class="timer-wrap">
        <div class="margin-bottom-25">
            <h2>⏰ TID KVAR</h2>
            <div id="timer" class="timer">{remaining//60:02d}:{remaining%60:02d}</div>
        </div>
        
        <div class="margin-20-0">
            <form method="post" action="/admin/{spel_id}/timer" class="form-inline">
                <button name="action" value="start" class="success">▶️ Starta</button>
                <button name="action" value="pause" class="warning">⏸️ Pausa</button>
                <button name="action" value="reset" class="danger">🔄 Återställ</button>
                <button type="button" onclick="openTimeAdjustmentModal('{spel_id}')" class="info">⚙️ Ändra tid</button>
            </form>
        </div>
        
        <div class="timer-status">
            <span class="badge {timer_status}">Status: {timer_status.capitalize()}</span>
        </div>
        
        <!-- Öppna timer i nytt fönster -->
        <div class="margin-top-15">
            <button type="button" onclick="openTimerWindow('{spel_id}')" class="secondary">🖥️ Öppna i nytt fönster</button>
        </div>
    </div>
    '''
