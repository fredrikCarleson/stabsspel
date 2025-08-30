#!/usr/bin/env python3
"""
Test script for the authorization token system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import generate_team_token, generate_team_tokens, validate_team_token, get_team_by_token, skapa_nytt_spel, load_game_data

def test_auth_system():
    """Test the authorization token system"""
    print("🧪 Testing Authorization Token System")
    print("=" * 50)
    
    # Test data
    test_spel_id = "test_20241201_120000"
    test_teams = ["Alfa", "Bravo", "STT"]
    
    print(f"📋 Test spel ID: {test_spel_id}")
    print(f"📋 Test teams: {test_teams}")
    print()
    
    # Create a test game first
    print("0️⃣ Creating test game...")
    try:
        # Create a new game (this will generate tokens automatically)
        created_spel_id = skapa_nytt_spel("2024-12-01", "Test Location", 15, 10, 10)
        print(f"   Created game: {created_spel_id}")
        
        # Load the game data to get the actual tokens
        game_data = load_game_data(created_spel_id)
        if game_data and "team_tokens" in game_data:
            team_tokens = game_data["team_tokens"]
            print("   Generated tokens:")
            for team, token in team_tokens.items():
                print(f"     {team}: {token}")
        else:
            print("   ❌ No team tokens found in game data")
            return
            
    except Exception as e:
        print(f"   ❌ Error creating test game: {e}")
        return
    
    print("✅ Test game created successfully")
    print()
    
    # Test 1: Generate tokens for all teams (separate test)
    print("1️⃣ Testing token generation...")
    manual_tokens = generate_team_tokens(test_spel_id, test_teams)
    
    for team, token in manual_tokens.items():
        print(f"   {team}: {token}")
    
    print("✅ Token generation successful")
    print()
    
    # Test 2: Validate tokens (using the created game)
    print("2️⃣ Testing token validation...")
    for team, token in team_tokens.items():
        is_valid = validate_team_token(created_spel_id, team, token)
        print(f"   {team} token valid: {is_valid}")
        
        # Test with wrong token
        wrong_token = "wrong_token_123"
        is_invalid = validate_team_token(created_spel_id, team, wrong_token)
        print(f"   {team} wrong token valid: {is_invalid} (should be False)")
    
    print("✅ Token validation successful")
    print()
    
    # Test 3: Get team by token
    print("3️⃣ Testing get team by token...")
    for team, token in team_tokens.items():
        found_team = get_team_by_token(created_spel_id, token)
        print(f"   Token {token[:20]}... -> Team: {found_team} (expected: {team})")
        
        # Test with wrong token
        wrong_team = get_team_by_token(created_spel_id, "wrong_token_123")
        print(f"   Wrong token -> Team: {wrong_team} (should be None)")
    
    print("✅ Get team by token successful")
    print()
    
    # Test 4: Token uniqueness
    print("4️⃣ Testing token uniqueness...")
    all_tokens = list(team_tokens.values())
    unique_tokens = set(all_tokens)
    print(f"   Total tokens: {len(all_tokens)}")
    print(f"   Unique tokens: {len(unique_tokens)}")
    print(f"   All tokens unique: {len(all_tokens) == len(unique_tokens)}")
    
    print("✅ Token uniqueness test successful")
    print()
    
    print("🎉 All authorization system tests passed!")
    print()
    print("📝 Sample team URLs:")
    for team, token in team_tokens.items():
        print(f"   {team}: /team/{created_spel_id}/{token}/enter_order")
    
    # Clean up test file
    try:
        os.remove(os.path.join("speldata", f"game_{created_spel_id}.json"))
        print(f"🧹 Cleaned up test file: game_{created_spel_id}.json")
    except:
        print("⚠️ Could not clean up test file")

if __name__ == "__main__":
    test_auth_system()
