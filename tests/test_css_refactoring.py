"""
Test CSS refactoring - verify that inline styles have been replaced with CSS classes
"""
import unittest
from admin_helpers import create_timer_controls, create_compact_header, create_action_buttons

class TestCSSRefactoring(unittest.TestCase):
    
    def test_create_timer_controls_uses_css_classes(self):
        """Test that create_timer_controls uses CSS classes instead of inline styles"""
        html = create_timer_controls("test_id", 600, "running")
        
        # Should use CSS classes instead of inline styles
        self.assertIn('class="margin-bottom-25"', html)
        self.assertIn('class="margin-20-0"', html)
        self.assertIn('class="margin-top-20"', html)
        self.assertIn('class="margin-top-15"', html)
        self.assertIn('class="form-inline"', html)
        self.assertIn('class="btn btn-primary"', html)
        self.assertIn('class="btn btn-warning"', html)
        self.assertIn('class="btn btn-danger"', html)
        self.assertIn('class="btn btn-secondary"', html)
        
        # Should NOT contain inline styles
        self.assertNotIn('style="margin-bottom: 25px;"', html)
        self.assertNotIn('style="margin: 20px 0;"', html)
        self.assertNotIn('style="display:inline;"', html)
    
    def test_create_compact_header_uses_css_classes(self):
        """Test that create_compact_header uses CSS classes"""
        data = {
            "datum": "2025-01-01",
            "plats": "Test Location",
            "antal_spelare": 20,
            "orderfas_min": 10,
            "diplomatifas_min": 5
        }
        lag_html = "<a href='#'>Test Team</a>"
        
        html = create_compact_header(data, lag_html)
        
        # Should use CSS classes
        self.assertIn('class="compact-header"', html)
        self.assertIn('class="compact-header-content"', html)
        self.assertIn('class="compact-header-info"', html)
        
        # Should contain the data
        self.assertIn("2025-01-01", html)
        self.assertIn("Test Location", html)
        self.assertIn("20", html)
    
    def test_create_action_buttons_uses_css_classes(self):
        """Test that create_action_buttons uses CSS classes"""
        html = create_action_buttons("test_id")
        
        # Should use CSS classes
        self.assertIn('class="action-buttons"', html)
        self.assertIn('class="action-button"', html)
        
        # Should contain the expected links
        self.assertIn('/admin/test_id/poang', html)
        self.assertIn('/admin/test_id/aktivitetskort', html)
        self.assertIn('/admin/test_id/reset', html)
        self.assertIn('/admin', html)

if __name__ == '__main__':
    unittest.main()
