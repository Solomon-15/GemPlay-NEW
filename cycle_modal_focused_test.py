#!/usr/bin/env python3
"""
Focused Bot Cycle History Modal Test
Directly test the cycle history endpoint that's working
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://df28b502-4a8b-41a3-806f-4aea5b27dbbf.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Known bot IDs from the logs
KNOWN_BOT_IDS = [
    "22bcb333-6260-4f30-80c0-db6aebd8ab65",
    "400f42d6-8169-442f-8d29-5925ca53c80e"
]

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
    return None

def test_cycle_history_endpoint(bot_id: str, token: str):
    """Test the cycle history endpoint for a specific bot"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"\n🧪 Testing cycle history for bot: {bot_id[:8]}...")
        
        response = requests.get(
            f"{BASE_URL}/admin/bots/{bot_id}/cycle-history",
            headers=headers,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analyze the response structure
            print(f"   📊 Response structure:")
            print(f"      Keys: {list(data.keys())}")
            
            # Check cycle_stats (financial indicators)
            cycle_stats = data.get("cycle_stats", {})
            if cycle_stats:
                print(f"   💰 Financial indicators:")
                print(f"      Поставлено (total_bet_amount): ${cycle_stats.get('total_bet_amount', 0)}")
                print(f"      Выиграно (total_winnings): ${cycle_stats.get('total_winnings', 0)}")
                print(f"      Проиграно (total_losses): ${cycle_stats.get('total_losses', 0)}")
                print(f"      Итого (net_profit): ${cycle_stats.get('net_profit', 0)}")
                
                # Check if financial data is real (not $0)
                total_bet = cycle_stats.get('total_bet_amount', 0)
                if total_bet > 0:
                    print(f"   ✅ Financial data looks good - total bet: ${total_bet}")
                else:
                    print(f"   ⚠️ Financial data shows $0 - may need real game data")
            
            # Check games data (table content)
            games = data.get("games", [])
            print(f"   🎮 Games data: {len(games)} games found")
            
            if games:
                sample_game = games[0]
                print(f"   📋 Sample game structure:")
                print(f"      Keys: {list(sample_game.keys())}")
                
                # Check required fields for the modal table
                bet_amount = sample_game.get("bet_amount", 0)
                bet_gems = sample_game.get("bet_gems", {})
                creator_move = sample_game.get("creator_move", "")
                opponent_move = sample_game.get("opponent_move", "")
                opponent = sample_game.get("opponent", "")
                winner = sample_game.get("winner", "")
                
                print(f"   🔍 Table data validation:")
                print(f"      СТАВКА (bet_amount): ${bet_amount} {'✅' if bet_amount > 0 else '❌'}")
                print(f"      ГЕМЫ (bet_gems): {bet_gems} {'✅' if bet_gems else '❌'}")
                print(f"      ХОДЫ (moves): Bot={creator_move}, Opponent={opponent_move} {'✅' if creator_move and opponent_move else '❌'}")
                print(f"      СОПЕРНИК (opponent): '{opponent}' {'✅' if opponent and opponent != 'N/A' else '❌'}")
                print(f"      РЕЗУЛЬТАТ (winner): '{winner}' {'✅' if winner in ['Победа', 'Поражение', 'Ничья'] else '❌'}")
                
                return True
            else:
                print(f"   ⚠️ No games data found")
                return False
                
        else:
            print(f"   ❌ Failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing cycle history: {e}")
        return False

def main():
    print("🎯 Focused Bot Cycle History Modal Test")
    print("=" * 60)
    
    # Authenticate
    print("🔐 Authenticating...")
    token = authenticate_admin()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    print("✅ Authentication successful")
    
    # Test known bot IDs
    success_count = 0
    for bot_id in KNOWN_BOT_IDS:
        if test_cycle_history_endpoint(bot_id, token):
            success_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Tested: {len(KNOWN_BOT_IDS)} bots")
    print(f"   Successful: {success_count}")
    print(f"   Success rate: {(success_count/len(KNOWN_BOT_IDS)*100):.1f}%")
    
    if success_count > 0:
        print("\n✅ Bot cycle history API is working!")
        print("   Ready for frontend testing with browser automation")
    else:
        print("\n❌ Bot cycle history API has issues")
        print("   Backend needs fixing before frontend testing")

if __name__ == "__main__":
    main()