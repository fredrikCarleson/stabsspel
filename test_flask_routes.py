#!/usr/bin/env python3
"""
Test Flask routes for team order system
"""

import requests
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import skapa_nytt_spel, load_game_data

def test_flask_routes():
    """Test the Flask routes"""
    print("🧪 Testing Flask Routes")
    print("=" * 50)
    
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
        
        # Test the team order entry page
        print("\n2️⃣ Testing team order entry page...")
        url = f"http://localhost:5000/team/{spel_id}/{first_token}/enter_order"
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("   ✅ Team order page loads successfully")
                if "Ange Order" in response.text:
                    print("   ✅ Page contains expected content")
                else:
                    print("   ⚠️ Page content may be incomplete")
            else:
                print(f"   ❌ Page returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ❌ Could not connect to Flask app (is it running?)")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test timer endpoint
        print("\n3️⃣ Testing timer endpoint...")
        timer_url = f"http://localhost:5000/team/{spel_id}/{first_token}/timer"
        try:
            response = requests.get(timer_url, timeout=5)
            if response.status_code == 200:
                timer_data = response.json()
                print(f"   ✅ Timer endpoint works: {timer_data}")
            else:
                print(f"   ❌ Timer endpoint returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ❌ Could not connect to Flask app")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test invalid token
        print("\n4️⃣ Testing invalid token...")
        invalid_url = f"http://localhost:5000/team/{spel_id}/invalid_token/enter_order"
        try:
            response = requests.get(invalid_url, timeout=5)
            if response.status_code == 403:
                print("   ✅ Invalid token correctly rejected")
            else:
                print(f"   ⚠️ Invalid token returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ❌ Could not connect to Flask app")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n🎉 Flask routes test completed!")
        
        # Clean up
        try:
            os.remove(os.path.join("speldata", f"game_{spel_id}.json"))
            print(f"🧹 Cleaned up test file: game_{spel_id}.json")
        except:
            print("⚠️ Could not clean up test file")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

if __name__ == "__main__":
    test_flask_routes()
