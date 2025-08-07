import json
import os
import tempfile
import shutil
from unittest.mock import patch
from app import app
from models import DATA_DIR, TEAMS, BACKLOG

# Create test environment exactly like the test
test_data_dir = tempfile.mkdtemp()
test_spel_id = "test_20250101"

# Create test game data exactly like the test
team_names = [team[0] for team in TEAMS]
test_game_data = {
    "id": test_spel_id,
    "spel_id": test_spel_id,
    "datum": "2025-01-01",
    "plats": "Test Location",
    "antal_spelare": 20,
    "runda": 1,
    "fas": "Orderfas",
    "timer": 600,
    "orderfas_min": 15,
    "diplomatifas_min": 10,
    "lag": team_names,
    "handlingspoang": {team: 10 for team in team_names},
    "regeringsstod": {team: 5 for team in team_names},
    "backlog": BACKLOG.copy(),
    "checkbox_states": {},
    "fashistorik": [],
    "rundor": {},
    "poang": {team: {"bas": 25, "aktuell": 25, "regeringsstod": False} for team in team_names}
}

# Save test game data
test_file = os.path.join(test_data_dir, f"game_{test_spel_id}.json")
with open(test_file, 'w', encoding='utf-8') as f:
    json.dump(test_game_data, f, ensure_ascii=False, indent=2)

print("Test file created:", test_file)
print("Initial checkbox_states:", test_game_data.get('checkbox_states', {}))

# Test the route with the exact same patching as the test, plus models.DATA_DIR
with patch('models.DATA_DIR', test_data_dir):
    with patch('admin_routes.DATA_DIR', test_data_dir):
        with patch('game_management.DATA_DIR', test_data_dir):
            client = app.test_client()
            response = client.post(f'/admin/{test_spel_id}/save_checkbox', 
                                 json={'checkbox_id': 'test_checkbox', 'checked': True})
            
            print("Response status:", response.status_code)
            print("Response data:", response.data)
            
            # Check if state was saved
            with open(test_file, 'r', encoding='utf-8') as f:
                updated_data = json.load(f)
                print("Updated checkbox_states:", updated_data.get('checkbox_states', {}))
                print("test_checkbox value:", updated_data.get('checkbox_states', {}).get('test_checkbox'))

# Clean up
shutil.rmtree(test_data_dir, ignore_errors=True) 