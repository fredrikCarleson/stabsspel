#!/usr/bin/env python3
"""
Test script to verify the Flask app works correctly before deployment
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import app
        print("✅ app.py imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import app.py: {e}")
        return False
    
    try:
        from models import DATA_DIR, TEAMS, BACKLOG
        print("✅ models.py imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import models.py: {e}")
        return False
    
    try:
        from admin_routes import admin_bp
        print("✅ admin_routes.py imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import admin_routes.py: {e}")
        return False
    
    try:
        from team_routes import team_bp
        print("✅ team_routes.py imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import team_routes.py: {e}")
        return False
    
    return True

def test_required_files():
    """Test that all required files exist"""
    print("\n📋 Testing required files...")
    
    required_files = [
        "requirements.txt",
        "Procfile", 
        "runtime.txt",
        "app.py",
        "models.py",
        "admin_routes.py",
        "team_routes.py"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_static_files():
    """Test that static files exist"""
    print("\n🎨 Testing static files...")
    
    static_files = [
        "static/style.css",
        "static/alarm.mp3"
    ]
    
    missing_files = []
    for file in static_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_app_creation():
    """Test that the Flask app can be created"""
    print("\n🚀 Testing Flask app creation...")
    
    try:
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the DATA_DIR to use temp directory
            with patch('models.DATA_DIR', temp_dir):
                with patch('app.DATA_DIR', temp_dir):
                    # Import and test app creation
                    import app
                    from app import app as flask_app
                    
                    print("✅ Flask app created successfully")
                    
                    # Test basic route
                    with flask_app.test_client() as client:
                        response = client.get('/')
                        if response.status_code == 200:
                            print("✅ Home route works")
                        else:
                            print(f"❌ Home route failed: {response.status_code}")
                            return False
                    
                    return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running deployment tests for Stabsspelet...\n")
    
    tests = [
        ("Required Files", test_required_files),
        ("Static Files", test_static_files),
        ("Imports", test_imports),
        ("Flask App", test_app_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"\n✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! Your app is ready for deployment.")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Create a Render account at https://render.com")
        print("3. Create a new Web Service and connect your repository")
        print("4. Set environment variables (SECRET_KEY, FLASK_ENV)")
        print("5. Deploy!")
        return True
    else:
        print("⚠️  Some tests failed. Please fix the issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
