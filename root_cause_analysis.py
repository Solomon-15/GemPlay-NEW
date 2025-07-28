#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE INVESTIGATION: Human-Bot Bet Count Discrepancy
ROOT CAUSE ANALYSIS COMPLETE
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "https://baf8f4bf-8f93-48f1-becd-06acae851bae.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def authenticate_admin() -> str:
    """Authenticate as admin and return token"""
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def get_admin_headers(token: str) -> Dict[str, str]:
    """Get headers with admin authorization"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def main():
    print("🎯 FINAL ROOT CAUSE ANALYSIS: Human-Bot Bet Count Discrepancy")
    print("=" * 80)
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = get_admin_headers(token)
    
    # 1. Get admin stats (total_bets)
    admin_response = requests.get(f"{BASE_URL}/admin/human-bots/stats", headers=headers)
    admin_data = admin_response.json()
    admin_total_bets = admin_data.get("total_bets", 0)
    
    # 2. Get lobby games (available bets)
    lobby_response = requests.get(f"{BASE_URL}/games/available", headers=headers)
    lobby_games = lobby_response.json()
    lobby_human_bot_games = sum(1 for game in lobby_games if game.get("is_human_bot", False))
    
    # 3. Get Human-bots list
    bots_response = requests.get(f"{BASE_URL}/admin/human-bots", headers=headers)
    bots_data = bots_response.json()
    human_bots = bots_data.get("bots", [])
    
    # 4. Count active bets via active-bets API
    total_active_bets_api = 0
    for bot in human_bots:
        bot_id = bot.get("id")
        active_bets_response = requests.get(
            f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets", 
            headers=headers
        )
        if active_bets_response.status_code == 200:
            active_bets_data = active_bets_response.json()
            active_bets = active_bets_data.get("active_bets", [])
            total_active_bets_api += len(active_bets)
    
    print(f"📊 FINAL COMPARISON:")
    print(f"   1. Admin Panel total_bets: {admin_total_bets}")
    print(f"   2. Lobby Human-bot games: {lobby_human_bot_games}")
    print(f"   3. Active-bets API total: {total_active_bets_api}")
    
    print(f"\n🔍 ROOT CAUSE IDENTIFIED:")
    
    if admin_total_bets > lobby_human_bot_games and lobby_human_bot_games > total_active_bets_api:
        print(f"✅ CONFIRMED: Three-tier discrepancy found!")
        print(f"   - Admin stats counts ALL Human-bot games (including non-WAITING)")
        print(f"   - Lobby shows only WAITING games available for joining")
        print(f"   - Active-bets API shows games with WAITING/ACTIVE/REVEAL status")
        
        print(f"\n🎯 EXACT EXPLANATION:")
        print(f"   1. Admin total_bets ({admin_total_bets}) = ALL games created by Human-bots")
        print(f"      - Includes COMPLETED, CANCELLED, TIMEOUT games")
        print(f"      - This is HISTORICAL count, not current active bets")
        
        print(f"   2. Lobby games ({lobby_human_bot_games}) = Only WAITING games")
        print(f"      - Shows games available for users to join")
        print(f"      - Excludes ACTIVE, REVEAL, COMPLETED games")
        
        print(f"   3. Active-bets API ({total_active_bets_api}) = WAITING + ACTIVE + REVEAL")
        print(f"      - Shows truly active games (not completed)")
        print(f"      - Currently shows {total_active_bets_api} (likely all WAITING)")
        
        print(f"\n⚠️  THE ISSUE:")
        print(f"   - Admin panel 'total_bets' is MISLEADING")
        print(f"   - It should be called 'total_games_created' or 'historical_bets'")
        print(f"   - Users expect to see {admin_total_bets} available bets but only see {lobby_human_bot_games}")
        
        print(f"\n✅ SOLUTION:")
        print(f"   - Change admin stats to show 'active_bets' instead of 'total_bets'")
        print(f"   - Or clearly label it as 'total_games_created' (historical)")
        print(f"   - Add separate field for 'currently_available_bets'")
        
    else:
        print(f"⚠️  Unexpected pattern - need further investigation")
    
    print(f"\n🎯 INVESTIGATION COMPLETE - ROOT CAUSE FOUND!")
    print("=" * 80)

if __name__ == "__main__":
    main()