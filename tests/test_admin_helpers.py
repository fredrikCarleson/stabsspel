"""
Unit tests for admin_helpers module
"""
import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_helpers import add_no_cache_headers, create_team_info_js, create_compact_header, create_action_buttons, create_script_references, create_timer_controls

class TestAdminHelpers(unittest.TestCase):
    """Test cases for admin_helpers functionality"""
    
    def test_add_no_cache_headers(self):
        """Test add_no_cache_headers function"""
        from flask import Response
        
        # Create a mock response
        response = Response("test")
        
        # Add headers
        result = add_no_cache_headers(response)
        
        # Check that headers were added
        self.assertEqual(result.headers['Cache-Control'], 'no-cache, no-store, must-revalidate')
        self.assertEqual(result.headers['Pragma'], 'no-cache')
        self.assertEqual(result.headers['Expires'], '0')
        
        # Check that it returns the same response object
        self.assertIs(result, response)
    
    def test_create_team_info_js(self):
        """Test create_team_info_js function"""
        js_code = create_team_info_js()
        
        # Check that it returns a string
        self.assertIsInstance(js_code, str)
        
        # Check that it contains expected JavaScript
        self.assertIn('function updateTeamInfo()', js_code)
        self.assertIn('document.getElementById', js_code)
        self.assertIn('Team Alfa', js_code)
        self.assertIn('Team Bravo', js_code)
        self.assertIn('STT', js_code)
        self.assertIn('Media', js_code)
        self.assertIn('SÄPO', js_code)
        self.assertIn('Regeringen', js_code)
        self.assertIn('USA', js_code)
    
    def test_create_compact_header(self):
        """Test create_compact_header function"""
        data = {
            "datum": "2025-01-01",
            "plats": "Stockholm",
            "antal_spelare": 25,
            "orderfas_min": 15,
            "diplomatifas_min": 10
        }
        lag_html = "Team Alfa, Team Bravo"
        
        header_html = create_compact_header(data, lag_html)
        
        # Check that it returns a string
        self.assertIsInstance(header_html, str)
        
        # Check that it contains expected content
        self.assertIn('<div class="compact-header">', header_html)
        self.assertIn('compact-header-content', header_html)
        self.assertIn('2025-01-01', header_html)
        self.assertIn('Stockholm', header_html)
        self.assertIn('25', header_html)
        self.assertIn('Team Alfa, Team Bravo', header_html)
    
    def test_create_action_buttons(self):
        """Test create_action_buttons function"""
        spel_id = "test123"
        
        buttons_html = create_action_buttons(spel_id)
        
        # Check that it returns a string
        self.assertIsInstance(buttons_html, str)
        
        # Check that it contains expected content
        self.assertIn('<div class="action-buttons">', buttons_html)
        self.assertIn('action-button', buttons_html)
        self.assertIn('test123', buttons_html)
        self.assertIn('Visa/ändra handlingspoäng', buttons_html)
        self.assertIn('Skriv ut aktivitetskort', buttons_html)
        self.assertIn('Återställ spel', buttons_html)
        self.assertIn('Tillbaka till adminstart', buttons_html)
    
    def test_create_script_references(self):
        """Test create_script_references function"""
        script_refs = create_script_references()
        
        # Check that it returns a string
        self.assertIsInstance(script_refs, str)
        
        # Check that it contains expected script reference
        self.assertIn('<script src="/static/admin.js"></script>', script_refs)
    
    def test_create_timer_controls(self):
        """Test create_timer_controls function"""
        spel_id = "test123"
        remaining = 600  # 10 minutes
        timer_status = "running"
        
        timer_html = create_timer_controls(spel_id, remaining, timer_status)
        
        # Check that it returns a string
        self.assertIsInstance(timer_html, str)
        
        # Check that it contains expected content
        self.assertIn('<div class="timer-container">', timer_html)
        self.assertIn('10:00', timer_html)  # 600 seconds = 10:00
        self.assertIn('test123', timer_html)
        self.assertIn('running', timer_html)
        self.assertIn('openTimerWindow', timer_html)

if __name__ == '__main__':
    unittest.main()
