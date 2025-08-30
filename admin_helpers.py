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
                <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
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
                <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
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
