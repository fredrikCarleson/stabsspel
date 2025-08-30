#!/usr/bin/env python3
"""
Test script for the team order entry system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import skapa_nytt_spel, load_game_data
import json

def test_team_order_system():
    """Test the team order entry system"""
    print("🧪 Testing Team Order Entry System")
    print("=" * 50)
    
    # Create a test game
    print("1️⃣ Creating test game...")
    try:
        spel_id = skapa_nytt_spel("2024-12-01", "Test Location", 15, 10, 10)
        print(f"   Created game: {spel_id}")
        
        # Load game data
        data = load_game_data(spel_id)
        if not data:
            print("   ❌ Could not load game data")
            return
        
        # Check if team tokens were generated
        team_tokens = data.get("team_tokens", {})
        if not team_tokens:
            print("   ❌ No team tokens found")
            return
        
        print(f"   ✅ Team tokens generated for {len(team_tokens)} teams")
        
        # Display sample URLs
        print("\n2️⃣ Sample team URLs:")
        for team, token in team_tokens.items():
            print(f"   {team}: /team/{spel_id}/{token}/enter_order")
        
        # Test order data structure
        print("\n3️⃣ Testing order data structure...")
        test_order = {
            "activities": [
                {
                    "id": 1234567890,
                    "aktivitet": "Test aktivitet",
                    "syfte": "Test syfte",
                    "malomrade": "eget",
                    "paverkar": ["Alfa", "Bravo"],
                    "typ": "bygga",
                    "hp": 5
                }
            ],
            "timestamp": "2024-12-01T12:00:00Z"
        }
        
        # Initialize team_orders structure
        if "team_orders" not in data:
            data["team_orders"] = {}
        
        orders_key = f"orders_round_{data['runda']}"
        if orders_key not in data["team_orders"]:
            data["team_orders"][orders_key] = {}
        
        # Save test order for first team
        first_team = list(team_tokens.keys())[0]
        data["team_orders"][orders_key][first_team] = {
            "submitted_at": 1234567890,
            "phase": data["fas"],
            "round": data["runda"],
            "orders": test_order,
            "final": True
        }
        
        # Save back to file
        from models import save_game_data
        save_game_data(spel_id, data)
        
        print(f"   ✅ Test order saved for {first_team}")
        
        # Verify order was saved
        data_after = load_game_data(spel_id)
        saved_order = data_after.get("team_orders", {}).get(orders_key, {}).get(first_team)
        if saved_order:
            print("   ✅ Order verification successful")
            print(f"   📝 Order details: {len(saved_order['orders']['activities'])} activities")
        else:
            print("   ❌ Order verification failed")
        
        print("\n🎉 Team order system test completed!")
        print(f"📁 Test game file: game_{spel_id}.json")
        
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
    test_team_order_system()
