"""
Unit tests for admin_helpers module
"""
import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_helpers import add_no_cache_headers, create_team_info_js

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

if __name__ == '__main__':
    unittest.main()
