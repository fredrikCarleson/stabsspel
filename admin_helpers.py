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
    """Skapa knappar för åtgärder"""
    poang_lank = f'<a href="/admin/{spel_id}/poang" class="action-button"><button>Visa/ändra handlingspoäng</button></a>'
    aktivitetskort_lank = f'<a href="/admin/{spel_id}/aktivitetskort" target="_blank" class="action-button"><button>Skriv ut aktivitetskort</button></a>'
    reset_lank = f'<form method="post" action="/admin/{spel_id}/reset" class="action-button"><button type="submit">Återställ spel</button></form>'
    back_lank = f'<a href="/admin" class="action-button"><button>Tillbaka till adminstart</button></a>'
    
    return f'''
    <div class="action-buttons">
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
    '''

def create_timer_controls(spel_id, remaining, timer_status):
    """Skapa timer-kontroller med externa referenser"""
    return f'''
    <div class="timer-container">
        <div style="margin-bottom: 25px;">
            <h2>⏰ TID KVAR</h2>
            <div id="timer">{remaining//60:02d}:{remaining%60:02d}</div>
        </div>
        
        <div style="margin: 20px 0;">
            <form method="post" action="/admin/{spel_id}/timer" style="display:inline;">
                <button name="action" value="start">▶️ Starta</button>
                <button name="action" value="pause">⏸️ Pausa</button>
                <button name="action" value="reset">🔄 Återställ</button>
            </form>
        </div>
        
        <div style="margin-top: 20px;">
            <span class="status {timer_status}">Status: {timer_status.capitalize()}</span>
        </div>
        
        <!-- Öppna timer i nytt fönster -->
        <div style="margin-top: 15px;">
            <button type="button" onclick="openTimerWindow('{spel_id}')">🖥️ Öppna i nytt fönster</button>
        </div>
    </div>
    '''
