#!/usr/bin/env python3
"""
Test script to debug the delete game functionality
"""

import requests
import time
import os
from models import skapa_nytt_spel, load_game_data

def test_delete_game():
    """Test the delete game functionality"""
    print("🧪 Testing Delete Game Functionality")
    print("=" * 50)
    
    # Create a test game
    print("📝 Creating test game...")
    spel_id = skapa_nytt_spel(
        datum="2024-01-01",
        plats="Test Location",
        antal_spelare=15,
        orderfas_min=10,
        diplomatifas_min=5
    )
    print(f"   ✅ Test game created: {spel_id}")
    
    # Verify the game file exists
    game_file = f"speldata/game_{spel_id}.json"
    if os.path.exists(game_file):
        print(f"   ✅ Game file exists: {game_file}")
    else:
        print(f"   ❌ Game file not found: {game_file}")
        return False
    
    # Test the delete game endpoint
    print("🗑️ Testing delete game endpoint...")
    try:
        response = requests.post(f"http://localhost:5000/admin/delete_game/{spel_id}", timeout=10)
        print(f"   Status code: {response.status_code}")
        print(f"   Response URL: {response.url}")
        
        if response.status_code == 200:
            print("   ✅ Delete request successful")
        elif response.status_code == 302:
            print("   ✅ Delete request redirected (expected)")
            print(f"   Redirect URL: {response.headers.get('Location', 'No location header')}")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response content: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False
    
    # Check if the game file was actually deleted
    if not os.path.exists(game_file):
        print("   ✅ Game file was successfully deleted")
    else:
        print("   ❌ Game file still exists after delete request")
        return False
    
    print("\n🎉 Delete game test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_delete_game()
        if success:
            print("\n✅ Delete game functionality test passed!")
        else:
            print("\n❌ Delete game functionality test failed!")
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
