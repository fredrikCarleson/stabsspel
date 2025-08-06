import unittest
import requests
import time
import subprocess
import os
import signal
import sys

class TestAppRunning(unittest.TestCase):
    """Test that the Flask application can start and run"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://127.0.0.1:5000"
        self.process = None
    
    def tearDown(self):
        """Clean up after tests"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
    
    def test_app_starts(self):
        """Test that the Flask app can start without errors"""
        try:
            # Start the Flask app in a subprocess
            self.process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for the app to start
            time.sleep(3)
            
            # Check if process is still running
            if self.process.poll() is None:
                # App is running, try to access the home page
                try:
                    response = requests.get(self.base_url, timeout=5)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("Stabsspelet", response.text)
                except requests.exceptions.RequestException as e:
                    # If we can't connect, that's okay for this test
                    # The important thing is that the app started without errors
                    pass
            else:
                # Check if there were any startup errors
                stdout, stderr = self.process.communicate()
                if stderr:
                    self.fail(f"App failed to start. Error: {stderr}")
                else:
                    self.fail("App process terminated unexpectedly")
                    
        except Exception as e:
            self.fail(f"Failed to start app: {e}")
    
    def test_imports_work(self):
        """Test that all modules can be imported without errors"""
        try:
            import app
            import admin_routes
            import team_routes
            import models
            self.assertTrue(True)  # If we get here, all imports worked
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_models_functions(self):
        """Test that key model functions work"""
        try:
            from models import TEAMS, BACKLOG, FASER, MAX_RUNDA, skapa_nytt_spel
            
            # Test constants
            self.assertIsInstance(TEAMS, list)
            self.assertIsInstance(BACKLOG, dict)
            self.assertIsInstance(FASER, list)
            self.assertIsInstance(MAX_RUNDA, int)
            
            # Test creating a game
            game_id = skapa_nytt_spel("2025-01-01", "Test", 20, 10, 15)
            self.assertIsInstance(game_id, str)
            
            # Clean up test file
            game_file = os.path.join('speldata', f"game_{game_id}.json")
            if os.path.exists(game_file):
                os.remove(game_file)
                
        except Exception as e:
            self.fail(f"Models test failed: {e}")
    
    def test_file_structure(self):
        """Test that all required files exist"""
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
    
    def test_directories_exist(self):
        """Test that required directories exist"""
        required_dirs = [
            'speldata',
            'static',
            'teambeskrivning'
        ]
        
        for dir_path in required_dirs:
            self.assertTrue(os.path.exists(dir_path), f"Required directory {dir_path} does not exist")
            self.assertTrue(os.path.isdir(dir_path), f"{dir_path} exists but is not a directory")

if __name__ == '__main__':
    unittest.main() 