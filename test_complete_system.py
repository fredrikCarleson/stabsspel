#!/usr/bin/env python3
"""
Comprehensive test for the complete team order system
"""

import requests
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import skapa_nytt_spel, load_game_data

def test_complete_system():
    """Test the complete team order system"""
    print("🧪 Testing Complete Team Order System")
    print("=" * 60)
    
    # Create a test game
    print("1️⃣ Creating test game...")
    try:
        spel_id = skapa_nytt_spel("2024-12-01", "Test Location", 15, 10, 10)
        print(f"   Created game: {spel_id}")
        
        # Load game data to get tokens
        data = load_game_data(spel_id)
        team_tokens = data.get("team_tokens", {})
        first_team = list(team_tokens.keys())[0]
        first_token = team_tokens[first_team]
        
        print(f"   Using team: {first_team}")
        print(f"   Token: {first_token[:20]}...")
        
    except Exception as e:
        print(f"   ❌ Error creating test game: {e}")
        return
    
    # Test team order entry page
    print("\n2️⃣ Testing team order entry page...")
    url = f"http://localhost:5000/team/{spel_id}/{first_token}/enter_order"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Team order page loads successfully")
            if "Ange Order" in response.text and first_team in response.text:
                print("   ✅ Page contains expected content")
            else:
                print("   ⚠️ Page content may be incomplete")
        else:
            print(f"   ❌ Page returned status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test submitting an order
    print("\n3️⃣ Testing order submission...")
    test_order = {
        "activities": [
            {
                "id": 1234567890,
                "aktivitet": "Test aktivitet för systemtest",
                "syfte": "Testa att systemet fungerar",
                "malomrade": "eget",
                "paverkar": ["Alfa", "Bravo"],
                "typ": "bygga",
                "hp": 5
            },
            {
                "id": 1234567891,
                "aktivitet": "Andra test aktivitet",
                "syfte": "Fortsätt testa systemet",
                "malomrade": "annat",
                "paverkar": ["STT"],
                "typ": "forstora",
                "hp": 3
            }
        ],
        "timestamp": "2024-12-01T12:00:00Z"
    }
    
    submit_url = f"http://localhost:5000/team/{spel_id}/{first_token}/submit_order"
    try:
        response = requests.post(submit_url, json=test_order, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✅ Order submitted successfully")
            else:
                print(f"   ❌ Order submission failed: {result.get('error')}")
        else:
            print(f"   ❌ Submit endpoint returned status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error submitting order: {e}")
    
    # Test admin order viewing
    print("\n4️⃣ Testing admin order viewing...")
    admin_url = f"http://localhost:5000/admin/{spel_id}"
    try:
        response = requests.get(admin_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Admin page loads successfully")
            if "Checklista: Ordrar från alla team" in response.text:
                print("   ✅ Admin page contains order checklist")
                
                # Check if the submitted order is visible
                if first_team in response.text and "Inskickad" in response.text:
                    print("   ✅ Submitted order is visible in admin")
                else:
                    print("   ⚠️ Submitted order may not be visible yet")
            else:
                print("   ⚠️ Admin page may not contain expected content")
        else:
            print(f"   ❌ Admin page returned status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error loading admin page: {e}")
    
    # Test order view page
    print("\n5️⃣ Testing order view page...")
    view_url = f"http://localhost:5000/admin/{spel_id}/view_order/{first_team}"
    try:
        response = requests.get(view_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Order view page loads successfully")
            if "Order från" in response.text and first_team in response.text:
                print("   ✅ Order view page contains expected content")
                if "Test aktivitet för systemtest" in response.text:
                    print("   ✅ Submitted order content is visible")
                else:
                    print("   ⚠️ Order content may not be visible")
            else:
                print("   ⚠️ Order view page may not contain expected content")
        else:
            print(f"   ❌ Order view page returned status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error loading order view page: {e}")
    
    # Test timer functionality
    print("\n6️⃣ Testing timer functionality...")
    timer_url = f"http://localhost:5000/team/{spel_id}/{first_token}/timer"
    try:
        response = requests.get(timer_url, timeout=5)
        if response.status_code == 200:
            timer_data = response.json()
            print(f"   ✅ Timer endpoint works: {timer_data}")
            if "remaining_time" in timer_data and "phase" in timer_data:
                print("   ✅ Timer data contains expected fields")
            else:
                print("   ⚠️ Timer data may be incomplete")
        else:
            print(f"   ❌ Timer endpoint returned status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error with timer: {e}")
    
    # Test security (invalid token)
    print("\n7️⃣ Testing security...")
    invalid_url = f"http://localhost:5000/team/{spel_id}/invalid_token/enter_order"
    try:
        response = requests.get(invalid_url, timeout=5)
        if response.status_code == 403:
            print("   ✅ Invalid token correctly rejected")
        else:
            print(f"   ⚠️ Invalid token returned status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing security: {e}")
    
    print("\n🎉 Complete system test finished!")
    print(f"📁 Test game file: game_{spel_id}.json")
    
    # Clean up
    try:
        os.remove(os.path.join("speldata", f"game_{spel_id}.json"))
        print(f"🧹 Cleaned up test file: game_{spel_id}.json")
    except:
        print("⚠️ Could not clean up test file")

if __name__ == "__main__":
    test_complete_system()
