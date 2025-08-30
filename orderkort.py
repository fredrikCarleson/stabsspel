"""
Orderkort generator för Stabsspelet.
Skapar utskrivbara orderkort för alla team för varje runda.
"""

import os
from datetime import datetime
from models import TEAMS
from game_management import load_game_data

def generate_orderkort_html(spel_id, runda):
    """
    Generera HTML för orderkort för alla team för en specifik runda.
    
    Args:
        spel_id (str): Spel-ID
        runda (int): Rundanummer
        
    Returns:
        str: HTML-kod för orderkorten
    """
    data = load_game_data(spel_id)
    if not data:
        return "<p>Spel hittades inte.</p>"
    
    # Hämta team från spelet
    teams = data.get("lag", [])
    if not teams:
        return "<p>Inga team hittades i spelet.</p>"
    
    # Hämta poängdata för att visa max handlingspoäng
    poang = data.get("poang", {})
    
    # Skapa HTML för varje team
    orderkort_html = ""
    
    for team in teams:
        # Hämta teamets max handlingspoäng
        max_hp = poang.get(team, {}).get("max_hp", 25)  # Standard 25 om inte satt
        
        orderkort_html += f"""
        <div class="orderkort-page">
            <div class="orderkort-header">
                <h1>Förslag: Strukturerat Orderkort</h1>
                <div class="identity-section">
                    <div class="identity-row">
                        <span class="label">Team:</span>
                        <span class="value">{team}</span>
                    </div>
                    <div class="identity-row">
                        <span class="label">Runda:</span>
                        <span class="value">{runda}</span>
                    </div>
                    <div class="identity-row">
                        <span class="label">Max handlingspoäng:</span>
                        <span class="value">{max_hp}</span>
                    </div>
                    <div class="identity-row">
                        <span class="label">Totalt satsade HP:</span>
                        <span class="value">_____</span>
                    </div>
                </div>
            </div>
            
            <div class="order-table-section">
                <h2>Ordertabell (max 6 rader)</h2>
                <table class="order-table">
                    <thead>
                        <tr>
                            <th>Nr</th>
                            <th>Aktivitet (Vad?)</th>
                            <th>Syfte/Mål (Varför?)</th>
                            <th>Målområde 🎯</th>
                            <th>Påverkar/Vem</th>
                            <th>Typ av handling ⚔️</th>
                            <th>HP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_order_rows()}
                    </tbody>
                </table>
            </div>
            
            <div class="field-explanations">
                <h3>Fältens funktion</h3>
                <ul>
                    <li><strong>Aktivitet (Vad?)</strong> → kort text, t.ex. "DDOS-attack mot valservern" eller "Utveckla loggning".</li>
                    <li><strong>Syfte/Mål (Varför?)</strong> → varför teamet satsar på detta (ger kontext).</li>
                    <li><strong>Målområde 🎯</strong> → kryssruta om satsningen direkt stöder teamets uttalade mål eller om den är riktad mot andras.</li>
                    <li><strong>Påverkar/Vem</strong> → vilken aktör/funktion detta riktas mot (för att undvika tvetydighet).</li>
                    <li><strong>Typ av handling ⚔️</strong> → kryss: Bygga/Förstärka eller Förstöra/Störa.</li>
                    <li><strong>HP</strong> → antal satsade handlingspoäng.</li>
                </ul>
            </div>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Orderkort - Runda {runda}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .orderkort-page {{ 
                    page-break-after: always; 
                    margin: 0;
                    padding: 20px;
                }}
                .no-print {{ display: none; }}
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }}
            
            .print-button {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                z-index: 1000;
            }}
            
            .print-button:hover {{
                background: #0056b3;
            }}
            
            .orderkort-page {{
                background: white;
                margin: 20px auto;
                padding: 30px;
                max-width: 21cm;
                min-height: 29.7cm;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
            }}
            
            .orderkort-header {{
                border-bottom: 3px solid #333;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            
            .orderkort-header h1 {{
                text-align: center;
                color: #333;
                margin: 0 0 20px 0;
                font-size: 24px;
                font-weight: bold;
            }}
            
            .identity-section {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}
            
            .identity-row {{
                display: flex;
                align-items: center;
                padding: 8px 0;
            }}
            
            .label {{
                font-weight: bold;
                margin-right: 10px;
                min-width: 150px;
            }}
            
            .value {{
                border-bottom: 1px solid #ccc;
                padding: 4px 8px;
                min-width: 100px;
                font-weight: 500;
            }}
            
            .order-table-section {{
                margin-bottom: 30px;
            }}
            
            .order-table-section h2 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 18px;
            }}
            
            .order-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            
            .order-table th,
            .order-table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                vertical-align: top;
            }}
            
            .order-table th {{
                background: #f8f9fa;
                font-weight: bold;
                font-size: 12px;
            }}
            
            .order-table td {{
                font-size: 11px;
                min-height: 60px;
            }}
            
            .activity-cell,
            .purpose-cell {{
                width: 20%;
            }}
            
            .target-cell,
            .affects-cell,
            .action-type-cell {{
                width: 15%;
            }}
            
            .hp-cell {{
                width: 8%;
                text-align: center;
            }}
            
            .checkbox-group {{
                display: flex;
                flex-direction: column;
                gap: 4px;
            }}
            
            .checkbox-item {{
                display: flex;
                align-items: center;
                font-size: 10px;
            }}
            
            .checkbox-item input[type="checkbox"] {{
                margin-right: 4px;
            }}
            
            .affects-options {{
                font-size: 9px;
                line-height: 1.2;
            }}
            
            .field-explanations {{
                border-top: 2px solid #333;
                padding-top: 20px;
                margin-top: 20px;
            }}
            
            .field-explanations h3 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 16px;
            }}
            
            .field-explanations ul {{
                margin: 0;
                padding-left: 20px;
            }}
            
            .field-explanations li {{
                margin-bottom: 8px;
                font-size: 12px;
                line-height: 1.4;
            }}
            
            .field-explanations strong {{
                color: #333;
            }}
        </style>
    </head>
    <body>
        <button class="print-button no-print" onclick="window.print()">🖨️ Skriv ut Orderkort</button>
        {orderkort_html}
    </body>
    </html>
    """

def generate_order_rows(teams=None):
    """
    Generera HTML för orderraderna i tabellen.
    
    Args:
        teams (list): Lista med teamnamn för att generera checkboxes för "Påverkar/Vem"
    
    Returns:
        str: HTML för orderraderna
    """
    if teams is None:
        teams = [team[0] for team in TEAMS]  # Använd standardteam om inga angivna
    
    rows_html = ""
    
    for i in range(1, 7):  # 6 rader som i mallen
        # Generera checkboxes för "Påverkar/Vem"
        affects_checkboxes = ""
        for team in teams:
            affects_checkboxes += f"""
                    <div class="checkbox-item">
                        <input type="checkbox" id="affects_{team}_{i}">
                        <label for="affects_{team}_{i}">{team}</label>
                    </div>"""
        
        rows_html += f"""
        <tr>
            <td style="text-align: center; font-weight: bold;">{i}</td>
            <td class="activity-cell">
                <div style="min-height: 60px; border: 1px solid #ccc; padding: 4px; background: #fafafa;">
                    <textarea style="width: 100%; height: 50px; border: none; resize: none; background: transparent; font-size: 10px;" placeholder="Beskriv aktiviteten..."></textarea>
                </div>
            </td>
            <td class="purpose-cell">
                <div style="min-height: 60px; border: 1px solid #ccc; padding: 4px; background: #fafafa;">
                    <textarea style="width: 100%; height: 50px; border: none; resize: none; background: transparent; font-size: 10px;" placeholder="Beskriv syftet..."></textarea>
                </div>
            </td>
            <td class="target-cell">
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="target_own_{i}">
                        <label for="target_own_{i}">Eget mål</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="target_other_{i}">
                        <label for="target_other_{i}">Annat mål</label>
                    </div>
                </div>
            </td>
            <td class="affects-cell">
                <div class="checkbox-group">
{affects_checkboxes}
                </div>
            </td>
            <td class="action-type-cell">
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="action_build_{i}">
                        <label for="action_build_{i}">Bygga/Förstärka</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="action_destroy_{i}">
                        <label for="action_destroy_{i}">Förstöra/Störa</label>
                    </div>
                </div>
            </td>
            <td class="hp-cell">
                <input type="number" style="width: 100%; text-align: center; font-size: 12px; padding: 4px;" min="0" placeholder="HP">
            </td>
        </tr>
        """
    
    return rows_html

def get_available_rounds(spel_id):
    """
    Hämta tillgängliga rundor för ett spel.
    
    Args:
        spel_id (str): Spel-ID
        
    Returns:
        list: Lista med rundonummer
    """
    data = load_game_data(spel_id)
    if not data:
        return []
    
    current_round = data.get("runda", 1)
    return list(range(1, current_round + 1))

def generate_team_orderkort_html(spel_id, team_name):
    """
    Generera HTML för orderkort för ett specifikt team för alla tillgängliga rundor.
    
    Args:
        spel_id (str): Spel-ID
        team_name (str): Teamnamn
        
    Returns:
        str: HTML-kod för orderkorten
    """
    data = load_game_data(spel_id)
    if not data:
        return "<p>Spel hittades inte.</p>"
    
    # Kontrollera att teamet finns i spelet
    teams = data.get("lag", [])
    if team_name not in teams:
        return f"<p>Team '{team_name}' hittades inte i spelet.</p>"
    
    # Hämta tillgängliga rundor
    available_rounds = get_available_rounds(spel_id)
    if not available_rounds:
        return "<p>Inga rundor hittades för spelet.</p>"
    
    # Hämta poängdata för att visa max handlingspoäng
    poang = data.get("poang", {})
    max_hp = poang.get(team_name, {}).get("max_hp", 25)  # Standard 25 om inte satt
    
    # Skapa HTML för varje runda
    orderkort_html = ""
    
    for runda in available_rounds:
        orderkort_html += f"""
        <div class="orderkort-page">
            <div class="orderkort-header">
                <h1>Förslag: Strukturerat Orderkort</h1>
                <div class="identity-section">
                    <div class="identity-row">
                        <span class="label">Team:</span>
                        <span class="value">{team_name}</span>
                    </div>
                    <div class="identity-row">
                        <span class="label">Runda:</span>
                        <span class="value">{runda}</span>
                    </div>
                    <div class="identity-row">
                        <span class="label">Max handlingspoäng:</span>
                        <span class="value">{max_hp}</span>
                    </div>
                    <div class="identity-row">
                        <span class="label">Totalt satsade HP:</span>
                        <span class="value">_____</span>
                    </div>
                </div>
            </div>
            
                   <div class="order-table-section">
                       <h2>Ordertabell (max 6 rader)</h2>
                       <table class="order-table">
                           <thead>
                               <tr>
                                   <th>Nr</th>
                                   <th>Aktivitet (Vad?)</th>
                                   <th>Syfte/Mål (Varför?)</th>
                                   <th>Målområde 🎯</th>
                                   <th>Påverkar/Vem</th>
                                   <th>Typ av handling ⚔️</th>
                                   <th>HP</th>
                               </tr>
                           </thead>
                           <tbody>
                               {generate_order_rows()}
                           </tbody>
                       </table>
                   </div>
            
            <div class="field-explanations">
                <h3>Fältens funktion</h3>
                <ul>
                    <li><strong>Aktivitet (Vad?)</strong> → kort text, t.ex. "DDOS-attack mot valservern" eller "Utveckla loggning".</li>
                    <li><strong>Syfte/Mål (Varför?)</strong> → varför teamet satsar på detta (ger kontext).</li>
                    <li><strong>Målområde 🎯</strong> → kryssruta om satsningen direkt stöder teamets uttalade mål eller om den är riktad mot andras.</li>
                    <li><strong>Påverkar/Vem</strong> → vilken aktör/funktion detta riktas mot (för att undvika tvetydighet).</li>
                    <li><strong>Typ av handling ⚔️</strong> → kryss: Bygga/Förstärka eller Förstöra/Störa.</li>
                    <li><strong>HP</strong> → antal satsade handlingspoäng.</li>
                </ul>
            </div>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Orderkort - {team_name}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .orderkort-page {{ 
                    page-break-after: always; 
                    margin: 0;
                    padding: 20px;
                }}
                .no-print {{ display: none; }}
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }}
            
            .print-button {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                z-index: 1000;
            }}
            
            .print-button:hover {{
                background: #0056b3;
            }}
            
            .orderkort-page {{
                background: white;
                margin: 20px auto;
                padding: 30px;
                max-width: 21cm;
                min-height: 29.7cm;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
            }}
            
            .orderkort-header {{
                border-bottom: 3px solid #333;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            
            .orderkort-header h1 {{
                text-align: center;
                color: #333;
                margin: 0 0 20px 0;
                font-size: 24px;
                font-weight: bold;
            }}
            
            .identity-section {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}
            
            .identity-row {{
                display: flex;
                align-items: center;
                padding: 8px 0;
            }}
            
            .label {{
                font-weight: bold;
                margin-right: 10px;
                min-width: 150px;
            }}
            
            .value {{
                border-bottom: 1px solid #ccc;
                padding: 4px 8px;
                min-width: 100px;
                font-weight: 500;
            }}
            
            .order-table-section {{
                margin-bottom: 30px;
            }}
            
            .order-table-section h2 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 18px;
            }}
            
            .order-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            
            .order-table th,
            .order-table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                vertical-align: top;
            }}
            
            .order-table th {{
                background: #f8f9fa;
                font-weight: bold;
                font-size: 12px;
            }}
            
            .order-table td {{
                font-size: 11px;
                min-height: 60px;
            }}
            
            .activity-cell,
            .purpose-cell {{
                width: 20%;
            }}
            
            .target-cell,
            .affects-cell,
            .action-type-cell {{
                width: 15%;
            }}
            
            .hp-cell {{
                width: 8%;
                text-align: center;
            }}
            
            .checkbox-group {{
                display: flex;
                flex-direction: column;
                gap: 4px;
            }}
            
            .checkbox-item {{
                display: flex;
                align-items: center;
                font-size: 10px;
            }}
            
            .checkbox-item input[type="checkbox"] {{
                margin-right: 4px;
            }}
            
            .affects-options {{
                font-size: 9px;
                line-height: 1.2;
            }}
            
            .field-explanations {{
                border-top: 2px solid #333;
                padding-top: 20px;
                margin-top: 20px;
            }}
            
            .field-explanations h3 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 16px;
            }}
            
            .field-explanations ul {{
                margin: 0;
                padding-left: 20px;
            }}
            
            .field-explanations li {{
                margin-bottom: 8px;
                font-size: 12px;
                line-height: 1.4;
            }}
            
            .field-explanations strong {{
                color: #333;
            }}
        </style>
    </head>
    <body>
        <button class="print-button no-print" onclick="window.print()">🖨️ Skriv ut Orderkort</button>
        {orderkort_html}
    </body>
    </html>
    """
