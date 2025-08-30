#!/usr/bin/env python3
"""
Demonstration script for admin cheat links functionality
Shows how to access team order pages directly as admin
"""

import requests
import time
import os
from models import skapa_nytt_spel, load_game_data

def demo_admin_cheat_links():
    """Demonstrate the admin cheat links functionality"""
    print("🎭 Admin Cheat Links Demo")
    print("=" * 40)
    
    # Create a demo game
    print("📝 Creating demo game...")
    spel_id = skapa_nytt_spel(
        datum="2024-01-01",
        plats="Demo Location",
        antal_spelare=15,
        orderfas_min=10,
        diplomatifas_min=5
    )
    print(f"   ✅ Demo game created: {spel_id}")
    
    # Load game data
    data = load_game_data(spel_id)
    team_tokens = data.get("team_tokens", {})
    
    print(f"\n🔗 Admin Cheat Links for {spel_id}:")
    print("-" * 40)
    
    for team, token in team_tokens.items():
        cheat_link = f"http://localhost:5000/team/{spel_id}/{token}/enter_order"
        print(f"🧪 {team}: {cheat_link}")
    
    print(f"\n📋 Admin Panel: http://localhost:5000/admin/{spel_id}")
    print("\n💡 Instructions:")
    print("1. Open the admin panel link above")
    print("2. Check the '🧪 Test Mode (Admin Cheat Links)' checkbox")
    print("3. Click any '🔗 Admin: Ange order' link to access team order pages")
    print("4. Test the order entry functionality")
    
    print(f"\n🧹 To clean up, delete: speldata/game_{spel_id}.json")
    
    return spel_id

if __name__ == "__main__":
    demo_admin_cheat_links()
