"""
Basic functionality tests for Stabsspel
"""
import unittest
import json
import tempfile
import os
import shutil
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of the application"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_main_page_loads(self):
        """Test that main page loads without errors"""
        response = self.app.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Stabsspelet', response.data)
        self.assertIn(b'Krisledningssimulation', response.data)
    
    def test_admin_page_loads(self):
        """Test that admin page loads without errors"""
        response = self.app.get('/admin')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Stabsspel Admin', response.data)
        self.assertIn(b'data-admin-start-tabs', response.data)
        self.assertIn(b'Starta nytt spel', response.data)
        self.assertIn(b'Ladda upp', response.data)
        self.assertIn(b'id="admin-panel-upload"', response.data)
        self.assertIn(b'id="admin-tab-create"', response.data)
        html = response.get_data(as_text=True)
        self.assertIn('aria-selected="true"', html)
        self.assertIn('id="admin-panel-upload"', html)
        self.assertRegex(html, r'id="admin-panel-upload"[^>]*hidden')
        self.assertNotRegex(html, r'id="admin-panel-create"[^>]*hidden')

    def test_admin_upload_tab_can_open_from_query(self):
        response = self.app.get('/admin?tab=upload')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertRegex(html, r'id="admin-tab-upload"[^>]*aria-selected="true"')
        self.assertRegex(html, r'id="admin-panel-create"[^>]*hidden')
        self.assertNotRegex(html, r'id="admin-panel-upload"[^>]*hidden')
    
    def test_static_files_load(self):
        """Test that static files are accessible"""
        response = self.app.get('/static/app.css')
        self.assertEqual(response.status_code, 200)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'Stabsspel')
        self.assertIn('timestamp', data)

if __name__ == '__main__':
    unittest.main()
