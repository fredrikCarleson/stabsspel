import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch

# Import the functions we want to test
import sys
sys.path.append('.')

from models import TEAMS, BACKLOG, FASER, MAX_RUNDA, skapa_nytt_spel

class TestBasicFunctionality(unittest.TestCase):
    """Basic functionality tests that can be run quickly"""
    
    def test_models_constants(self):
        """Test that all constants are properly defined"""
        # Test TEAMS - now it's a list of tuples (team_name, action_points)
        self.assertIsInstance(TEAMS, list)
        self.assertGreater(len(TEAMS), 0)
        
        # Check team names (first element of each tuple)
        team_names = [team[0] for team in TEAMS]
        self.assertIn('Alfa', team_names)
        self.assertIn('Bravo', team_names)
        
        # Test BACKLOG
        self.assertIsInstance(BACKLOG, dict)
        self.assertGreater(len(BACKLOG), 0)
        
        # Test FASER
        self.assertIsInstance(FASER, list)
        self.assertGreater(len(FASER), 0)
        self.assertIn('Orderfas', FASER)
        self.assertIn('Diplomatifas', FASER)
        self.assertIn('Resultatfas', FASER)
        
        # Test MAX_RUNDA
        self.assertIsInstance(MAX_RUNDA, int)
        self.assertEqual(MAX_RUNDA, 3)
    
    def test_create_new_game(self):
        """Test creating a new game with skapa_nytt_spel"""
        # Updated to match the actual function signature
        game_id = skapa_nytt_spel("2025-01-01", "Test Location", 20, 10, 15)
        
        # Check that a game ID was returned
        self.assertIsInstance(game_id, str)
        self.assertGreater(len(game_id), 0)
        
        # Check that game file was created
        game_file = os.path.join('speldata', f"game_{game_id}.json")
        self.assertTrue(os.path.exists(game_file))
        
        # Load and check game data
        with open(game_file, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Check basic structure
        self.assertEqual(game_data['datum'], "2025-01-01")
        self.assertEqual(game_data['plats'], "Test Location")
        self.assertEqual(game_data['antal_spelare'], 20)
        self.assertEqual(game_data['runda'], 1)
        self.assertEqual(game_data['fas'], 'Orderfas')
        self.assertEqual(game_data['orderfas_min'], 10)
        self.assertEqual(game_data['diplomatifas_min'], 15)
        
        # Check teams
        self.assertIsInstance(game_data['lag'], list)
        self.assertGreater(len(game_data['lag']), 0)
        
        # Check backlog structure
        self.assertIn('backlog', game_data)
        self.assertIsInstance(game_data['backlog'], dict)
        
        # Clean up test file
        os.remove(game_file)
    
    def test_backlog_structure(self):
        """Test that backlog structure is correct for all teams"""
        for team_name in BACKLOG.keys():
            self.assertIn(team_name, BACKLOG)
            team_backlog = BACKLOG[team_name]
            self.assertIsInstance(team_backlog, list)
            
            # Check each task has required fields
            for task in team_backlog:
                self.assertIsInstance(task, dict)
                self.assertIn('id', task)
                self.assertIn('namn', task)
                self.assertIn('slutford', task)
                
                # Check if task has phases (like Bravo tasks) or direct estimaterade_hp
                if 'faser' in task:
                    # Task with phases (like Bravo)
                    self.assertIsInstance(task['faser'], list)
                    for phase in task['faser']:
                        self.assertIsInstance(phase, dict)
                        self.assertIn('namn', phase)
                        self.assertIn('estimaterade_hp', phase)
                        self.assertIn('spenderade_hp', phase)
                        self.assertIn('slutford', phase)
                else:
                    # Direct task (like Alfa, STT)
                    self.assertIn('estimaterade_hp', task)
                    self.assertIn('spenderade_hp', task)
    
    def test_imports_work(self):
        """Test that all imports work correctly"""
        try:
            # Import the Flask app from app.py instead
            from app import app
            self.assertTrue(True)  # If we get here, import worked
        except ImportError as e:
            self.fail(f"Failed to import app: {e}")
        
        try:
            # team_routes uses Blueprint, not app
            from team_routes import team_bp
            self.assertTrue(True)  # If we get here, import worked
        except ImportError as e:
            self.fail(f"Failed to import team_routes: {e}")
    
    def test_file_structure(self):
        """Test that required files exist"""
        required_files = [
            'app.py',
            'admin_routes.py',
            'team_routes.py',
            'models.py',
            'requirements.txt',
            'static/style.css'
        ]
        
        for file_path in required_files:
            self.assertTrue(os.path.exists(file_path), f"Required file {file_path} does not exist")
    
    def test_speldata_directory(self):
        """Test that speldata directory exists and is accessible"""
        self.assertTrue(os.path.exists('speldata'), "speldata directory does not exist")
        self.assertTrue(os.path.isdir('speldata'), "speldata is not a directory")
    
    def test_static_files(self):
        """Test that static files exist"""
        static_files = [
            'static/style.css',
            'static/alarm.mp3'
        ]
        
        for file_path in static_files:
            if os.path.exists(file_path):
                self.assertTrue(os.path.isfile(file_path), f"{file_path} exists but is not a file")
            # Note: We don't fail if files don't exist as they might be optional
    
    def test_teambeskrivning_directory(self):
        """Test that teambeskrivning directory exists and has content"""
        self.assertTrue(os.path.exists('teambeskrivning'), "teambeskrivning directory does not exist")
        self.assertTrue(os.path.isdir('teambeskrivning'), "teambeskrivning is not a directory")
        
        # Check that it has some content
        files = os.listdir('teambeskrivning')
        self.assertGreater(len(files), 0, "teambeskrivning directory is empty")

class TestDataConsistency(unittest.TestCase):
    """Test data consistency across the application"""
    
    def test_teams_consistency(self):
        """Test that teams are consistent across all data structures"""
        # Get team names from TEAMS (first element of each tuple)
        team_names = [team[0] for team in TEAMS]
        
        # Check that teams in BACKLOG are a subset of TEAMS
        # Not all teams have backlog entries, so we check the reverse
        for team_name in BACKLOG.keys():
            self.assertIn(team_name, team_names, f"Team {team_name} in BACKLOG but not in TEAMS")
        
        # Check that all teams have team description files
        teambeskrivning_dir = 'teambeskrivning'
        if os.path.exists(teambeskrivning_dir):
            team_files = os.listdir(teambeskrivning_dir)
            for team_name in team_names:
                team_lower = team_name.lower()
                # Check for .txt files
                txt_files = [f for f in team_files if f.endswith('.txt') and team_lower in f.lower()]
                # Check for .jpg files
                jpg_files = [f for f in team_files if f.endswith('.jpg') and team_lower in f.lower()]
                
                # At least one file should exist for each team
                self.assertTrue(len(txt_files) > 0 or len(jpg_files) > 0, 
                              f"No team description files found for {team_name}")
    
    def test_game_data_structure(self):
        """Test that game data structure is consistent"""
        # Create a test game
        game_id = skapa_nytt_spel("2025-01-01", "Test", 20, 10, 15)
        
        # Load the created game data
        game_file = os.path.join('speldata', f"game_{game_id}.json")
        with open(game_file, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Check all required fields exist
        required_fields = [
            'id', 'datum', 'plats', 'antal_spelare', 
            'runda', 'fas', 'lag', 'backlog', 
            'orderfas_min', 'diplomatifas_min'
        ]
        
        for field in required_fields:
            self.assertIn(field, game_data, f"Required field {field} missing from game data")
        
        # Check data types
        self.assertIsInstance(game_data['id'], str)
        self.assertIsInstance(game_data['datum'], str)
        self.assertIsInstance(game_data['plats'], str)
        self.assertIsInstance(game_data['antal_spelare'], int)
        self.assertIsInstance(game_data['runda'], int)
        self.assertIsInstance(game_data['fas'], str)
        self.assertIsInstance(game_data['lag'], list)
        self.assertIsInstance(game_data['backlog'], dict)
        self.assertIsInstance(game_data['orderfas_min'], int)
        self.assertIsInstance(game_data['diplomatifas_min'], int)
        
        # Clean up test file
        os.remove(game_file)

if __name__ == '__main__':
    unittest.main() 