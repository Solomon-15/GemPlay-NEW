#!/usr/bin/env python3
"""
Simple Regular Bot Move Data Fix Test
Quick test to verify the "Missing move data for regular bot game" fix
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://5a0f72db-7197-4535-89b4-f85be852ec00.preview.emergentagent.com/api"
ADMIN_USER = {"email": "admin@gemplay.com", "password": "Admin123!"}

def authenticate():
    """Get admin token"""
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER, timeout=10)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_regular_bot_move_data_fix():
    """Test the move data fix for regular bots"""
    print("🎯 Testing Regular Bot Move Data Fix")
    print("=" * 50)
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Check for active regular bot games
    print("\n1. Checking for active regular bot games...")
    response = requests.get(f"{BASE_URL}/bots/active-games", headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to get active games: {response.status_code}")
        return
    
    games = response.json()
    regular_bot_games = [g for g in games if g.get("is_regular_bot") or g.get("bot_type") == "REGULAR"]
    
    print(f"✅ Found {len(regular_bot_games)} regular bot games")
    
    if not regular_bot_games:
        print("❌ No regular bot games found to test")
        return
    
    # Step 2: Find a suitable game to join
    test_game = None
    for game in regular_bot_games:
        if game.get("status") == "WAITING" and game.get("bet_amount", 0) <= 20:
            test_game = game
            break
    
    if not test_game:
        print("❌ No suitable WAITING game found")
        return
    
    print(f"✅ Found test game: {test_game['id']} (${test_game['bet_amount']})")
    
    # Step 3: Join the game
    print("\n2. Joining the regular bot game...")
    game_id = test_game["id"]
    bet_amount = test_game["bet_amount"]
    
    # Simple gem combination that matches the bet amount
    join_data = {
        "move": "rock",
        "gems": {"Ruby": int(bet_amount)}  # Use Ruby gems to match bet amount
    }
    
    response = requests.post(f"{BASE_URL}/games/{game_id}/join", headers=headers, json=join_data, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to join game: {response.status_code} - {response.text}")
        return
    
    print("✅ Successfully joined the game")
    
    # Step 4: Wait and check game completion
    print("\n3. Waiting for game completion...")
    
    for attempt in range(10):  # Wait up to 20 seconds
        time.sleep(2)
        
        # Try to get game status
        try:
            response = requests.get(f"{BASE_URL}/games/{game_id}", headers=headers, timeout=5)
            if response.status_code == 200:
                game_data = response.json()
                status = game_data.get("status")
                creator_move = game_data.get("creator_move")
                opponent_move = game_data.get("opponent_move")
                winner_id = game_data.get("winner_id")
                
                print(f"   Attempt {attempt + 1}: Status={status}, Creator={creator_move}, Opponent={opponent_move}")
                
                if status == "COMPLETED":
                    if creator_move and opponent_move:
                        print(f"🎉 SUCCESS: Game completed with both moves!")
                        print(f"   Creator move: {creator_move}")
                        print(f"   Opponent move: {opponent_move}")
                        print(f"   Winner: {winner_id}")
                        print(f"   ✅ NO 'Missing move data' error occurred!")
                        return True
                    else:
                        print(f"❌ FAILURE: Game completed but missing move data")
                        print(f"   Creator move: {creator_move}")
                        print(f"   Opponent move: {opponent_move}")
                        return False
                        
                elif status == "ACTIVE":
                    print(f"   Game is ACTIVE - both players joined, waiting for completion...")
                    
        except Exception as e:
            print(f"   Attempt {attempt + 1}: Error checking game - {e}")
    
    print("❌ Game did not complete within expected time")
    return False

if __name__ == "__main__":
    success = test_regular_bot_move_data_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CONCLUSION: Regular Bot Move Data Fix is WORKING!")
        print("   The 'Missing move data for regular bot game' error has been resolved.")
    else:
        print("❌ CONCLUSION: Move Data Fix needs attention")
        print("   The issue may still be present or games are not completing properly.")