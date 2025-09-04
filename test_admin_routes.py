import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from flask import Flask
from werkzeug.test import Client

# Import the functions we want to test
import sys
sys.path.append('.')

from app import app
from models import TEAMS, BACKLOG, FASER, MAX_RUNDA, skapa_nytt_spel

class TestAdminRoutes(unittest.TestCase):
    """Test cases for admin_routes.py functions"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the actual Flask app with all blueprints registered
        self.app = app.test_client()
        self.app.testing = True
        
        # Create temporary directory for test data
        self.test_data_dir = tempfile.mkdtemp()
        self.original_speldata_dir = 'speldata'
        
        # Backup original speldata if it exists
        if os.path.exists(self.original_speldata_dir):
            self.speldata_backup = tempfile.mkdtemp()
            shutil.copytree(self.original_speldata_dir, self.speldata_backup, dirs_exist_ok=True)
        
        # Create test speldata directory
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Mock the DATA_DIR from models
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    self.test_spel_id = "test_20250101"
                    self.test_game_data = self.create_test_game_data()
                    self.save_test_game_data()
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original speldata if it existed
        if hasattr(self, 'speldata_backup'):
            shutil.rmtree(self.original_speldata_dir, ignore_errors=True)
            shutil.move(self.speldata_backup, self.original_speldata_dir)
        
        # Clean up test directory
        shutil.rmtree(self.test_data_dir, ignore_errors=True)
    
    def create_test_game_data(self):
        """Create test game data"""
        # Extract team names from TEAMS tuples
        team_names = [team[0] for team in TEAMS]
        
        return {
            "id": self.test_spel_id,
            "spel_id": self.test_spel_id,
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
    
    def save_test_game_data(self):
        """Save test game data to file"""
        test_file = os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_game_data, f, ensure_ascii=False, indent=2)
    
    def test_admin_start_page(self):
        """Test admin start page loads correctly"""
        response = self.app.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Stabsspel Admin', response.data)
    
    def test_create_new_game(self):
        """Test creating a new game"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            response = self.app.post('/admin', data={
                'datum': '2025-01-01',
                'plats': 'Test Location',
                'players_interval': '20',
                'orderfas_min': '10',
                'diplomatifas_min': '10'
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            # Check if game file was created
            game_files = [f for f in os.listdir(self.test_data_dir) if f.endswith('.json')]
            self.assertGreater(len(game_files), 0)
    
    def test_admin_panel_loads(self):
        """Test admin panel loads for existing game"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    response = self.app.get(f'/admin/{self.test_spel_id}')
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(b'Adminpanel', response.data)
    
    def test_game_not_found(self):
        """Test handling of non-existent game"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            response = self.app.get('/admin/nonexistent_game')
            self.assertEqual(response.status_code, 404)
    
    def test_next_phase_transition(self):
        """Test transitioning to next phase"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    # Start with Orderfas
                    self.test_game_data['fas'] = 'Orderfas'
                    self.save_test_game_data()
                    
                    response = self.app.post(f'/admin/{self.test_spel_id}/timer', data={'action': 'next_fas'})
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Check if phase changed to Diplomatifas
                    with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                        updated_data = json.load(f)
                        self.assertEqual(updated_data['fas'], 'Diplomatifas')
    
    def test_new_round_creation(self):
        """Test creating a new round"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    # Set up game in final phase of round 1
                    self.test_game_data['fas'] = 'Resultatfas'
                    self.test_game_data['runda'] = 1
                    self.save_test_game_data()
                    
                    response = self.app.post(f'/admin/{self.test_spel_id}/ny_runda')
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Check if new round was created
                    with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                        updated_data = json.load(f)
                        self.assertEqual(updated_data['runda'], 2)
                        self.assertEqual(updated_data['fas'], 'Orderfas')
    
    def test_reset_game(self):
        """Test resetting a game"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    # Set up game with some progress
                    self.test_game_data['runda'] = 2
                    self.test_game_data['fas'] = 'Diplomatifas'
                    team_names = [team[0] for team in TEAMS]
                    self.test_game_data['handlingspoang'] = {team: 15 for team in team_names}
                    self.save_test_game_data()
                    
                    response = self.app.post(f'/admin/{self.test_spel_id}/reset')
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Check if game was reset
                    with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                        updated_data = json.load(f)
                        self.assertEqual(updated_data['runda'], 1)
                        self.assertEqual(updated_data['fas'], 'Orderfas')
                        # Check that poang structure was reset correctly
                        team_names = [team[0] for team in TEAMS]
                        for team in team_names:
                            # Get the correct base value from TEAMS
                            expected_bas = next((minp for namn, minp in TEAMS if namn == team), 20)
                            self.assertEqual(updated_data['poang'][team]['aktuell'], expected_bas)
                            self.assertEqual(updated_data['poang'][team]['bas'], expected_bas)
                            self.assertFalse(updated_data['poang'][team]['regeringsstod'])
    
    def test_update_backlog(self):
        """Test updating team backlog"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    test_team = 'Alfa'
                    test_task_id = 'alfa_1'  # ID for "Inloggning val"
                    test_hp = 5
                    
                    response = self.app.post(f'/admin/{self.test_spel_id}/backlog', data={
                        f'spenderade_{test_task_id}': str(test_hp)
                    }, follow_redirects=True)
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Check if backlog was updated
                    with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                        updated_data = json.load(f)
                        backlog = updated_data['backlog'][test_team]
                        # Find the task by ID
                        task = None
                        for t in backlog:
                            if t['id'] == test_task_id:
                                task = t
                                break
                        self.assertIsNotNone(task, f"Task with ID '{test_task_id}' not found in backlog")
                        # Simple task without phases
                        self.assertEqual(task['spenderade_hp'], test_hp)
    
    def test_update_action_points(self):
        """Test updating team action points"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    test_team = 'Bravo'
                    new_points = 15
                    
                    response = self.app.post(f'/admin/{self.test_spel_id}/poang', data={
                        f'poang_{test_team}': str(new_points)
                    }, follow_redirects=True)
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Check if action points were updated
                    with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                        updated_data = json.load(f)
                        self.assertEqual(updated_data['poang'][test_team]['aktuell'], new_points)
    
    def test_checkbox_state_persistence(self):
        """Test checkbox state persistence"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    # Save test game data first
                    self.save_test_game_data()
                    
                    checkbox_id = 'test_checkbox'
                    checked_state = True
                    
                    # Set checkbox state
                    response = self.app.post(f'/admin/{self.test_spel_id}/save_checkbox', 
                                           json={'checkbox_id': checkbox_id, 'checked': checked_state})
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Check if state was saved
                    with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                        updated_data = json.load(f)
                        self.assertEqual(updated_data['checkbox_states'].get(checkbox_id), checked_state)
    
    def test_timer_controls(self):
        """Test timer start/stop functionality"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    # Test start timer
                    response = self.app.post(f'/admin/{self.test_spel_id}/timer', data={'action': 'start'})
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Test stop timer
                    response = self.app.post(f'/admin/{self.test_spel_id}/timer', data={'action': 'pause'})
                    self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_activity_cards_page(self):
        """Test activity cards page loads"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    response = self.app.get(f'/admin/{self.test_spel_id}/aktivitetskort')
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(b'Aktivitetskort', response.data)
    
    def test_team_routes(self):
        """Test team-specific routes"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    test_team = 'Alfa'
                    response = self.app.get(f'/team/{self.test_spel_id}/{test_team}')
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(test_team.encode(), response.data)
    
    def test_game_end_condition(self):
        """Test game end after 3 rounds"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    # Set up game in final phase of round 3
                    self.test_game_data['runda'] = 3
                    self.test_game_data['fas'] = 'Resultatfas'
                    self.save_test_game_data()
                    
                    response = self.app.get(f'/admin/{self.test_spel_id}')
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(b'Avsluta spelet', response.data)
    
    def test_data_consistency(self):
        """Test that game data structure is consistent"""
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('admin_routes.DATA_DIR', self.test_data_dir):
                with patch('game_management.DATA_DIR', self.test_data_dir):
                    # Test that game data has all required fields
                    game_file = os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json")
                    with open(game_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    required_fields = ['spel_id', 'datum', 'plats', 'antal_spelare', 'runda', 'fas', 'lag']
                    for field in required_fields:
                        self.assertIn(field, data)
                    
                    # Test that teams are properly structured
                    self.assertIsInstance(data['lag'], list)
                    self.assertGreater(len(data['lag']), 0)
                    
                    # Test that backlog exists for teams that should have it
                    if 'backlog' in data:
                        # Only Alfa, Bravo, and STT have backlog entries
                        expected_backlog_teams = ['Alfa', 'Bravo', 'STT']
                        for team_name in expected_backlog_teams:
                            self.assertIn(team_name, data['backlog'])

    def test_delete_game_functionality(self):
        """Test the delete_game function works correctly"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            with patch('game_management.DATA_DIR', self.test_data_dir):
                # Verify game file exists before deletion
                game_file = os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json")
                self.assertTrue(os.path.exists(game_file))
                
                # Test POST request to delete game
                response = self.app.post(f'/admin/delete_game/{self.test_spel_id}', follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                
                # Verify game file was deleted
                self.assertFalse(os.path.exists(game_file))
    
    def test_delete_game_nonexistent(self):
        """Test delete_game with non-existent game ID"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            nonexistent_id = "nonexistent_game_12345"
            
            # Test POST request to delete non-existent game
            response = self.app.post(f'/admin/delete_game/{nonexistent_id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Should redirect to admin start page without error
            self.assertIn(b'Stabsspel Admin', response.data)
    
    def test_delete_game_route_accessible(self):
        """Test that delete game route is accessible"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            # Test that the route exists and responds
            response = self.app.post(f'/admin/delete_game/{self.test_spel_id}')
            self.assertEqual(response.status_code, 302)  # Redirect status
            
            # Test with non-existent game
            response = self.app.post('/admin/delete_game/nonexistent')
            self.assertEqual(response.status_code, 302)  # Should still redirect

    def test_nollstall_regeringsstod_functionality(self):
        """Test the nollstall_regeringsstod function"""
        # Create test data with some teams having regeringsstod = True
        test_data = {
            "poang": {
                "Alfa": {"bas": 25, "aktuell": 25, "regeringsstod": True},
                "Bravo": {"bas": 25, "aktuell": 30, "regeringsstod": True},
                "STT": {"bas": 25, "aktuell": 20, "regeringsstod": False}
            }
        }
        
        # Import the function from game_management
        from game_management import nollstall_regeringsstod
        
        # Call the function
        result = nollstall_regeringsstod(test_data)
        
        # Verify all regeringsstod values are now False
        for team in result["poang"]:
            self.assertFalse(result["poang"][team]["regeringsstod"])
        
        # Verify other data is unchanged
        self.assertEqual(result["poang"]["Alfa"]["aktuell"], 25)
        self.assertEqual(result["poang"]["Bravo"]["aktuell"], 30)
        self.assertEqual(result["poang"]["STT"]["aktuell"], 20)

    def test_nollstall_regeringsstod_in_route(self):
        """Test that nollstall_regeringsstod is used in the ny_runda route"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            with patch('game_management.DATA_DIR', self.test_data_dir):
                with patch('models.DATA_DIR', self.test_data_dir):
                    # Create a copy of test data to avoid modifying the original
                    test_data_copy = self.test_game_data.copy()
                    test_data_copy["poang"] = self.test_game_data["poang"].copy()
                    test_data_copy["poang"]["Alfa"] = self.test_game_data["poang"]["Alfa"].copy()
                    test_data_copy["poang"]["Bravo"] = self.test_game_data["poang"]["Bravo"].copy()
                    
                    # Set up game data with some teams having regeringsstod = True
                    test_data_copy["poang"]["Alfa"]["regeringsstod"] = True
                    test_data_copy["poang"]["Bravo"]["regeringsstod"] = True
                    
                    # Save the modified test data
                    test_file = os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json")
                    with open(test_file, 'w', encoding='utf-8') as f:
                        json.dump(test_data_copy, f, ensure_ascii=False, indent=2)
                    
                    # Call the ny_runda route
                    response = self.app.post(f'/admin/{self.test_spel_id}/ny_runda')
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Check that regeringsstod was reset to False
                    with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                        updated_data = json.load(f)
                        for team in updated_data["poang"]:
                            self.assertFalse(updated_data["poang"][team]["regeringsstod"])

    def test_load_game_data_functionality(self):
        """Test that load_game_data function can load game data correctly"""
        from game_management import load_game_data
        
        # Test loading existing game data with patched DATA_DIR
        with patch('game_management.DATA_DIR', self.test_data_dir):
            result = load_game_data(self.test_spel_id)
            self.assertIsNotNone(result)
            self.assertEqual(result["spel_id"], self.test_spel_id)
            self.assertEqual(result["datum"], "2025-01-01")
            
            # Test loading non-existent game data
            result = load_game_data("non_existent_game")
            self.assertIsNone(result)

    def test_load_game_data_import(self):
        """Test that load_game_data function can be imported"""
        from game_management import load_game_data
        self.assertTrue(callable(load_game_data))

    def test_save_checkbox_state_functionality(self):
        """Test that save_checkbox_state function works correctly"""
        from game_management import save_checkbox_state, get_checkbox_state
        
        # Test with patched DATA_DIR
        with patch('models.DATA_DIR', self.test_data_dir):
            with patch('game_management.DATA_DIR', self.test_data_dir):
                # Initially no checkbox states
                result = get_checkbox_state(self.test_game_data, "test_checkbox")
                self.assertFalse(result)
                
                # Save a checkbox state
                save_checkbox_state(self.test_spel_id, "test_checkbox", True)
                
                # Reload data and check
                with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                    updated_data = json.load(f)
                    result = get_checkbox_state(updated_data, "test_checkbox")
                    self.assertTrue(result)
                
                # Save another checkbox state
                save_checkbox_state(self.test_spel_id, "another_checkbox", False)
                
                # Reload and check both
                with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                    updated_data = json.load(f)
                    result1 = get_checkbox_state(updated_data, "test_checkbox")
                    result2 = get_checkbox_state(updated_data, "another_checkbox")
                    self.assertTrue(result1)
                    self.assertFalse(result2)

    def test_get_checkbox_state_functionality(self):
        """Test that get_checkbox_state function works correctly"""
        from game_management import get_checkbox_state
        
        # Test with data that has no checkbox_states
        data_without_checkboxes = {"id": "test"}
        result = get_checkbox_state(data_without_checkboxes, "any_checkbox")
        self.assertFalse(result)
        
        # Test with data that has checkbox_states
        data_with_checkboxes = {
            "id": "test",
            "checkbox_states": {
                "checkbox1": True,
                "checkbox2": False,
                "checkbox3": True
            }
        }
        
        result1 = get_checkbox_state(data_with_checkboxes, "checkbox1")
        result2 = get_checkbox_state(data_with_checkboxes, "checkbox2")
        result3 = get_checkbox_state(data_with_checkboxes, "checkbox3")
        result4 = get_checkbox_state(data_with_checkboxes, "nonexistent")
        
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertTrue(result3)
        self.assertFalse(result4)

    def test_checkbox_functions_import(self):
        """Test that checkbox functions can be imported"""
        from game_management import save_checkbox_state, get_checkbox_state
        self.assertTrue(callable(save_checkbox_state))
        self.assertTrue(callable(get_checkbox_state))

class TestModels(unittest.TestCase):
    """Test cases for models.py functions"""
    
    def test_create_new_game(self):
        """Test skapa_nytt_spel function"""
        spel_id = skapa_nytt_spel("2025-01-01", "Test Location", 20, 10, 10)
        
        # Check that a spel_id was returned
        self.assertIsInstance(spel_id, str)
        self.assertGreater(len(spel_id), 0)
    
    def test_constants(self):
        """Test that constants are properly defined"""
        self.assertIsInstance(TEAMS, list)
        self.assertGreater(len(TEAMS), 0)
        
        self.assertIsInstance(BACKLOG, dict)
        self.assertGreater(len(BACKLOG), 0)
        
        self.assertIsInstance(FASER, list)
        self.assertGreater(len(FASER), 0)
        
        self.assertIsInstance(MAX_RUNDA, int)
        self.assertEqual(MAX_RUNDA, 4)

if __name__ == '__main__':
    unittest.main() 
