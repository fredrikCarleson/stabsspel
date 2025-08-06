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
        # Use the actual Flask app
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
            "lag": team_names,
            "handlingspoang": {team: 10 for team in team_names},
            "regeringsstod": {team: 5 for team in team_names},
            "backlog": BACKLOG.copy(),
            "checkbox_states": {},
            "fashistorik": [],
            "rundor": {}
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
            response = self.app.post('/admin/skapa_spel', data={
                'datum': '2025-01-01',
                'plats': 'Test Location',
                'antal_spelare': '20'
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            # Check if game file was created
            game_files = [f for f in os.listdir(self.test_data_dir) if f.endswith('.json')]
            self.assertGreater(len(game_files), 0)
    
    def test_admin_panel_loads(self):
        """Test admin panel loads for existing game"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            response = self.app.get(f'/admin/{self.test_spel_id}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Stabsspel Admin', response.data)
    
    def test_game_not_found(self):
        """Test handling of non-existent game"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            response = self.app.get('/admin/nonexistent_game')
            self.assertEqual(response.status_code, 404)
    
    def test_next_phase_transition(self):
        """Test transitioning to next phase"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            # Start with Orderfas
            self.test_game_data['fas'] = 'Orderfas'
            self.save_test_game_data()
            
            response = self.app.post(f'/admin/{self.test_spel_id}/nasta_fas')
            self.assertEqual(response.status_code, 302)  # Redirect
            
            # Check if phase changed to Diplomatifas
            with open(os.path.join(self.test_data_dir, f"game_{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                updated_data = json.load(f)
                self.assertEqual(updated_data['fas'], 'Diplomatifas')
    
    def test_new_round_creation(self):
        """Test creating a new round"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
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
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
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
                team_names = [team[0] for team in TEAMS]
                self.assertEqual(updated_data['handlingspoang'], {team: 10 for team in team_names})
    
    def test_update_backlog(self):
        """Test updating team backlog"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            test_team = 'Alfa'
            test_task = 'Uppgift 1'
            test_phase = 'Orderfas'
            test_hp = 5
            
            response = self.app.post(f'/admin/{self.test_spel_id}/backlog', data={
                'lag': test_team,
                'uppgift': test_task,
                'fas': test_phase,
                'handlingspoang': str(test_hp)
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            
            # Check if backlog was updated
            with open(os.path.join(self.test_data_dir, f"{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                updated_data = json.load(f)
                backlog = updated_data['backlog'][test_team]
                task = backlog[test_task]
                phase = task['faser'][test_phase]
                self.assertEqual(phase['spenderade_hp'], test_hp)
    
    def test_update_action_points(self):
        """Test updating team action points"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            test_team = 'Bravo'
            new_points = 15
            
            response = self.app.post(f'/admin/{self.test_spel_id}/poang', data={
                'lag': test_team,
                'handlingspoang': str(new_points)
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            
            # Check if action points were updated
            with open(os.path.join(self.test_data_dir, f"{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                updated_data = json.load(f)
                self.assertEqual(updated_data['handlingspoang'][test_team], new_points)
    
    def test_checkbox_state_persistence(self):
        """Test checkbox state persistence"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            checkbox_id = 'test_checkbox'
            checked_state = True
            
            # Set checkbox state
            response = self.app.post(f'/admin/{self.test_spel_id}/checkbox', data={
                'checkbox_id': checkbox_id,
                'checked': str(checked_state)
            })
            
            self.assertEqual(response.status_code, 200)
            
            # Check if state was saved
            with open(os.path.join(self.test_data_dir, f"{self.test_spel_id}.json"), 'r', encoding='utf-8') as f:
                updated_data = json.load(f)
                self.assertEqual(updated_data['checkbox_states'].get(checkbox_id), checked_state)
    
    def test_timer_controls(self):
        """Test timer start/stop functionality"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            # Test start timer
            response = self.app.post(f'/admin/{self.test_spel_id}/start_timer')
            self.assertEqual(response.status_code, 200)
            
            # Test stop timer
            response = self.app.post(f'/admin/{self.test_spel_id}/stop_timer')
            self.assertEqual(response.status_code, 200)
    
    def test_activity_cards_page(self):
        """Test activity cards page loads"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            response = self.app.get(f'/admin/{self.test_spel_id}/aktivitetskort')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Aktivitetskort', response.data)
    
    def test_team_routes(self):
        """Test team-specific routes"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            test_team = 'Alfa'
            response = self.app.get(f'/admin/{self.test_spel_id}/lag/{test_team}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(test_team.encode(), response.data)
    
    def test_game_end_condition(self):
        """Test game end after 3 rounds"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            # Set up game in final phase of round 3
            self.test_game_data['runda'] = 3
            self.test_game_data['fas'] = 'Resultatfas'
            self.save_test_game_data()
            
            response = self.app.get(f'/admin/{self.test_spel_id}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Avsluta spelet', response.data)
    
    def test_data_consistency(self):
        """Test that game data structure is consistent"""
        with patch('admin_routes.DATA_DIR', self.test_data_dir):
            # Test that game data has all required fields
            game_file = os.path.join(self.test_data_dir, f"{self.test_spel_id}.json")
            with open(game_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            required_fields = ['spel_id', 'datum', 'plats', 'antal_spelare', 'runda', 'fas', 'lag']
            for field in required_fields:
                self.assertIn(field, data)
            
            # Test that teams are properly structured
            self.assertIsInstance(data['lag'], list)
            self.assertGreater(len(data['lag']), 0)
            
            # Test that backlog exists for all teams
            if 'backlog' in data:
                for team in data['lag']:
                    if isinstance(team, tuple):
                        team_name = team[0]
                    else:
                        team_name = team
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

class TestModels(unittest.TestCase):
    """Test cases for models.py functions"""
    
    def test_create_new_game(self):
        """Test skapa_nytt_spel function"""
        game_data = skapa_nytt_spel("test_20250101", "2025-01-01", "Test Location", 20)
        
        # Check basic structure
        self.assertEqual(game_data['spel_id'], "test_20250101")
        self.assertEqual(game_data['datum'], "2025-01-01")
        self.assertEqual(game_data['plats'], "Test Location")
        self.assertEqual(game_data['antal_spelare'], 20)
        self.assertEqual(game_data['runda'], 1)
        self.assertEqual(game_data['fas'], 'Orderfas')
        
        # Check teams
        self.assertEqual(set(game_data['lag']), set(TEAMS))
        
        # Check action points initialization
        for team in TEAMS:
            self.assertEqual(game_data['handlingspoang'][team], 10)
            self.assertEqual(game_data['regeringsstod'][team], 5)
        
        # Check backlog structure
        for team in TEAMS:
            self.assertIn(team, game_data['backlog'])
            team_backlog = game_data['backlog'][team]
            self.assertIsInstance(team_backlog, dict)
            
            # Check that spenderade_hp is initialized to 0
            for task_name, task_data in team_backlog.items():
                self.assertIn('faser', task_data)
                for phase_name, phase_data in task_data['faser'].items():
                    self.assertEqual(phase_data['spenderade_hp'], 0)
                    self.assertEqual(phase_data['slutford'], False)
    
    def test_constants(self):
        """Test that constants are properly defined"""
        self.assertIsInstance(TEAMS, list)
        self.assertGreater(len(TEAMS), 0)
        
        self.assertIsInstance(BACKLOG, dict)
        self.assertGreater(len(BACKLOG), 0)
        
        self.assertIsInstance(FASER, list)
        self.assertGreater(len(FASER), 0)
        
        self.assertIsInstance(MAX_RUNDA, int)
        self.assertEqual(MAX_RUNDA, 3)

if __name__ == '__main__':
    unittest.main() 
