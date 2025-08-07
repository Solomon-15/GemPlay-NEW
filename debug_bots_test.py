#!/usr/bin/env python3
"""
Debug Regular Bots - Detailed Analysis
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://5a0f72db-7197-4535-89b4-f85be852ec00.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def authenticate_admin():
    """Authenticate as admin and return access token"""
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER, timeout=30)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def main():
    print("🔍 DEBUGGING REGULAR BOTS LOGIC")
    
    token = authenticate_admin()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get bot details
    print("\n📊 REGULAR BOTS ANALYSIS:")
    response = requests.get(f"{BASE_URL}/admin/bots", headers=headers, timeout=30)
    if response.status_code == 200:
        bots_data = response.json()
        bots = bots_data if isinstance(bots_data, list) else bots_data.get("bots", [])
        for bot in bots[:3]:  # First 3 bots
            bot_id = bot["id"]
            bot_name = bot["name"]
            cycle_games = bot.get("cycle_games", 0)
            active_bets = bot.get("active_bets", 0)
            
            print(f"\n🤖 Bot: {bot_name}")
            print(f"   ID: {bot_id}")
            print(f"   Cycle Games: {cycle_games}")
            print(f"   Active Bets (API): {active_bets}")
            
            # Check actual games in database
            # WAITING games created by this bot
            waiting_response = requests.get(
                f"{BASE_URL}/games/available", 
                headers=headers, 
                timeout=30
            )
            
            if waiting_response.status_code == 200:
                all_games = waiting_response.json()
                bot_waiting_games = [g for g in all_games if g.get("creator_id") == bot_id]
                print(f"   WAITING games created: {len(bot_waiting_games)}")
            
            # Check active games
            active_response = requests.get(
                f"{BASE_URL}/bots/ongoing-games", 
                headers=headers, 
                timeout=30
            )
            
            if active_response.status_code == 200:
                active_games = active_response.json()
                bot_active_games = [g for g in active_games if g.get("creator_id") == bot_id]
                print(f"   ACTIVE games created: {len(bot_active_games)}")
            
            # Check if bot appears as opponent anywhere (should be 0)
            all_games_response = requests.get(
                f"{BASE_URL}/bots/active-games", 
                headers=headers, 
                timeout=30
            )
            
            if all_games_response.status_code == 200:
                all_bot_games = all_games_response.json()
                bot_as_opponent = [g for g in all_bot_games if g.get("opponent_id") == bot_id]
                print(f"   Games as opponent: {len(bot_as_opponent)} (should be 0)")
                
                bot_as_creator = [g for g in all_bot_games if g.get("creator_id") == bot_id]
                print(f"   Games as creator: {len(bot_as_creator)}")
    
    # Check endpoint separation
    print("\n🔗 ENDPOINT SEPARATION ANALYSIS:")
    
    # /bots/active-games
    response1 = requests.get(f"{BASE_URL}/bots/active-games", headers=headers, timeout=30)
    if response1.status_code == 200:
        games1 = response1.json()
        print(f"   /bots/active-games: {len(games1)} games")
        waiting_count = len([g for g in games1 if g.get("status") == "WAITING"])
        active_count = len([g for g in games1 if g.get("status") == "ACTIVE"])
        print(f"     - WAITING: {waiting_count}")
        print(f"     - ACTIVE: {active_count}")
    
    # /bots/ongoing-games
    response2 = requests.get(f"{BASE_URL}/bots/ongoing-games", headers=headers, timeout=30)
    if response2.status_code == 200:
        games2 = response2.json()
        print(f"   /bots/ongoing-games: {len(games2)} games")
        if games2:
            print(f"     - Sample game: {games2[0].get('status', 'unknown')}")
    
    # /games/available
    response3 = requests.get(f"{BASE_URL}/games/available", headers=headers, timeout=30)
    if response3.status_code == 200:
        games3 = response3.json()
        print(f"   /games/available: {len(games3)} games")
        regular_bot_games = [g for g in games3 if g.get("creator_type") == "bot" and g.get("is_regular_bot_game")]
        print(f"     - Regular bot games: {len(regular_bot_games)} (should be 0)")
    
    # /games/active-human-bots
    response4 = requests.get(f"{BASE_URL}/games/active-human-bots", headers=headers, timeout=30)
    if response4.status_code == 200:
        games4 = response4.json()
        print(f"   /games/active-human-bots: {len(games4)} games")
        regular_bot_games = [g for g in games4 if g.get("creator_type") == "bot" and g.get("is_regular_bot_game")]
        print(f"     - Regular bot games: {len(regular_bot_games)} (should be 0)")

if __name__ == "__main__":
    main()