#!/usr/bin/env python3
"""
Check for Human-bot opponent scenarios and joined_at field population
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def admin_login():
    """Login as admin"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    except:
        return None

def get_admin_headers(token):
    """Get headers with admin authorization"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def check_opponent_scenarios():
    """Check for games where Human-bots are opponents"""
    token = admin_login()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = get_admin_headers(token)
    
    print("🔍 CHECKING FOR HUMAN-BOT OPPONENT SCENARIOS")
    print("=" * 60)
    
    # Get all games to find opponent scenarios
    response = requests.get(
        f"{BASE_URL}/admin/games",
        headers=headers,
        params={"page": 1, "per_page": 50}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get games: {response.status_code}")
        return
    
    data = response.json()
    games = data.get("games", [])
    
    print(f"📋 Analyzing {len(games)} games for opponent scenarios")
    
    human_bot_opponents = []
    active_games_with_opponents = []
    games_with_joined_at = []
    
    for game in games:
        opponent_type = game.get("opponent_type")
        status = game.get("status")
        joined_at = game.get("joined_at")
        updated_at = game.get("updated_at")
        
        # Check if Human-bot is opponent
        if opponent_type == "human_bot":
            human_bot_opponents.append({
                "id": game.get("id"),
                "status": status,
                "creator_type": game.get("creator_type"),
                "opponent_type": opponent_type,
                "joined_at": joined_at,
                "updated_at": updated_at,
                "created_at": game.get("created_at")
            })
        
        # Check for active games with opponents
        if status in ["ACTIVE", "REVEAL"] and game.get("opponent_id"):
            active_games_with_opponents.append({
                "id": game.get("id"),
                "status": status,
                "creator_type": game.get("creator_type"),
                "opponent_type": opponent_type,
                "joined_at": joined_at,
                "updated_at": updated_at
            })
        
        # Check for games with joined_at populated
        if joined_at:
            games_with_joined_at.append({
                "id": game.get("id"),
                "status": status,
                "joined_at": joined_at,
                "updated_at": updated_at,
                "creator_type": game.get("creator_type"),
                "opponent_type": opponent_type
            })
    
    print(f"\n📊 RESULTS:")
    print(f"Human-bot opponents found: {len(human_bot_opponents)}")
    print(f"Active games with opponents: {len(active_games_with_opponents)}")
    print(f"Games with joined_at populated: {len(games_with_joined_at)}")
    
    if human_bot_opponents:
        print(f"\n🤖 HUMAN-BOT OPPONENT EXAMPLES:")
        for i, game in enumerate(human_bot_opponents[:3]):
            print(f"  Game #{i+1}: {game['id']}")
            print(f"    Status: {game['status']}")
            print(f"    Creator: {game['creator_type']}")
            print(f"    Opponent: {game['opponent_type']}")
            print(f"    Joined at: {game['joined_at'] or 'Not set'}")
            print(f"    Updated at: {game['updated_at'] or 'Not set'}")
    
    if games_with_joined_at:
        print(f"\n⏰ GAMES WITH JOINED_AT POPULATED:")
        for i, game in enumerate(games_with_joined_at[:3]):
            print(f"  Game #{i+1}: {game['id']}")
            print(f"    Status: {game['status']}")
            print(f"    Creator: {game['creator_type']}")
            print(f"    Opponent: {game['opponent_type']}")
            print(f"    Joined at: {game['joined_at']}")
            print(f"    Updated at: {game['updated_at'] or 'Not set'}")
    
    # Now check if the active bets API would include these fields for opponent scenarios
    if human_bot_opponents:
        print(f"\n🔍 TESTING ACTIVE BETS API FOR OPPONENT SCENARIOS:")
        
        # Get Human-bots list
        response = requests.get(
            f"{BASE_URL}/admin/human-bots",
            headers=headers,
            params={"page": 1, "per_page": 10}
        )
        
        if response.status_code == 200:
            bots_data = response.json()
            human_bots = bots_data.get("bots", [])
            
            for bot in human_bots[:3]:  # Check first 3 bots
                bot_id = bot.get("id")
                bot_name = bot.get("name", "Unknown")
                
                # Check if this bot appears as opponent in any game
                bot_as_opponent = [g for g in human_bot_opponents if g.get("opponent_id") == bot_id]
                
                if bot_as_opponent:
                    print(f"\n  🤖 Bot {bot_name} found as opponent in {len(bot_as_opponent)} games")
                    
                    # Get active bets for this bot
                    response = requests.get(
                        f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        bet_data = response.json()
                        bets = bet_data.get("bets", [])
                        
                        opponent_bets = [bet for bet in bets if not bet.get("is_creator", True)]
                        
                        if opponent_bets:
                            print(f"    Found {len(opponent_bets)} opponent bets in API response")
                            for bet in opponent_bets[:2]:
                                print(f"      Bet {bet.get('id')}: created_at={bet.get('created_at')}")
                                print(f"        Has updated_at: {'updated_at' in bet}")
                                print(f"        Has joined_at: {'joined_at' in bet}")
                        else:
                            print(f"    No opponent bets found in API response")

if __name__ == "__main__":
    check_opponent_scenarios()