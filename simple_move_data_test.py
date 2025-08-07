#!/usr/bin/env python3
"""
SIMPLIFIED FINAL TEST: Regular Bots Move Data Fix
Упрощенный финальный тест исправления ошибки "Missing move data for regular bot game"
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://f772daa6-fb15-4f46-808e-f02104f088ba.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None) -> tuple:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        else:
            return False, None, f"Unsupported method: {method}"
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        success = response.status_code in [200, 201]
        return success, response_data, response.status_code
        
    except Exception as e:
        return False, None, f"Error: {str(e)}"

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as admin...{Colors.END}")
    
    success, response_data, status = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print(f"{Colors.GREEN}✅ Admin authentication successful{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Admin authentication failed: {status}{Colors.END}")
        return None

def create_test_bot(admin_token: str) -> Optional[str]:
    """Create Final_Move_Test_Bot"""
    print(f"\n{Colors.MAGENTA}🤖 Creating Final_Move_Test_Bot...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    bot_data = {
        "name": "Final_Move_Test_Bot",
        "min_bet_amount": 15.0,
        "max_bet_amount": 25.0,
        "win_percentage": 55,
        "cycle_games": 1,
        "pause_between_games": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced"
    }
    
    success, response_data, status = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if success and response_data:
        bot_id = response_data.get("id") or response_data.get("bot_id")
        if bot_id:
            print(f"{Colors.GREEN}✅ Bot created successfully with ID: {bot_id}{Colors.END}")
            return bot_id
        else:
            print(f"{Colors.YELLOW}⚠️ Bot created but no ID returned: {response_data}{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Failed to create bot: {status} - {response_data}{Colors.END}")
    
    return None

def find_active_regular_bot_games(admin_token: str):
    """Find active regular bot games"""
    print(f"\n{Colors.MAGENTA}🔍 Finding active regular bot games...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, status = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        print(f"{Colors.CYAN}📊 Found {len(games)} active regular bot games{Colors.END}")
        
        # Look for games in the expected bet range
        suitable_games = []
        for game in games:
            bet_amount = game.get("bet_amount", 0)
            status = game.get("status", "")
            if 15.0 <= bet_amount <= 25.0 and status == "WAITING":
                suitable_games.append(game)
                print(f"   Game {game.get('id', 'N/A')[:8]}... - ${bet_amount} - {status}")
        
        if suitable_games:
            print(f"{Colors.GREEN}✅ Found {len(suitable_games)} suitable games for testing{Colors.END}")
            return suitable_games[0]  # Return first suitable game
        else:
            print(f"{Colors.YELLOW}⚠️ No suitable games found in bet range $15-25{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Failed to get active games: {status} - {response_data}{Colors.END}")
    
    return None

def check_completed_regular_bot_games(admin_token: str):
    """Check completed regular bot games for move data issues"""
    print(f"\n{Colors.MAGENTA}🔍 Checking completed regular bot games for move data...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get all games
    success, response_data, status = make_request(
        "GET",
        "/admin/games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        print(f"{Colors.CYAN}📊 Analyzing {len(games)} total games{Colors.END}")
        
        # Filter for completed regular bot games
        regular_bot_games = []
        move_data_issues = []
        
        for game in games:
            if (game.get("is_regular_bot_game") or 
                game.get("creator_type") == "bot" or 
                game.get("bot_type") == "REGULAR"):
                
                regular_bot_games.append(game)
                
                # Check for move data issues
                creator_move = game.get("creator_move")
                opponent_move = game.get("opponent_move")
                status = game.get("status")
                
                if status == "COMPLETED" and creator_move is None:
                    move_data_issues.append({
                        "game_id": game.get("id"),
                        "creator_move": creator_move,
                        "opponent_move": opponent_move,
                        "status": status,
                        "winner_id": game.get("winner_id")
                    })
        
        print(f"{Colors.CYAN}📊 Found {len(regular_bot_games)} regular bot games{Colors.END}")
        
        if move_data_issues:
            print(f"{Colors.RED}🚨 CRITICAL: Found {len(move_data_issues)} games with missing move data!{Colors.END}")
            for issue in move_data_issues[:3]:  # Show first 3 issues
                print(f"   Game {issue['game_id'][:8]}... - creator_move: {issue['creator_move']}, opponent_move: {issue['opponent_move']}, status: {issue['status']}")
            
            return False, move_data_issues
        else:
            print(f"{Colors.GREEN}✅ No move data issues found in completed games{Colors.END}")
            return True, []
    else:
        print(f"{Colors.RED}❌ Failed to get games: {status} - {response_data}{Colors.END}")
        return False, []

def main():
    """Main test execution"""
    print_header("SIMPLIFIED FINAL TEST: Regular Bots Move Data Fix")
    print(f"{Colors.BLUE}🎯 Testing for 'Missing move data for regular bot game' error{Colors.END}")
    
    # Step 1: Authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        print(f"{Colors.RED}❌ Cannot proceed without admin authentication{Colors.END}")
        sys.exit(1)
    
    # Step 2: Create test bot (or use existing)
    bot_id = create_test_bot(admin_token)
    
    # Step 3: Wait for bot to create games
    print(f"\n{Colors.BLUE}⏳ Waiting 15 seconds for bot automation to create games...{Colors.END}")
    time.sleep(15)
    
    # Step 4: Find active games
    active_game = find_active_regular_bot_games(admin_token)
    
    # Step 5: Check for existing move data issues
    no_issues, issues = check_completed_regular_bot_games(admin_token)
    
    # Final assessment
    print_header("FINAL ASSESSMENT")
    
    if no_issues:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 SUCCESS: No 'Missing move data' issues found!{Colors.END}")
        print(f"{Colors.GREEN}The Regular Bots Move Data Fix appears to be working correctly.{Colors.END}")
        
        if active_game:
            print(f"{Colors.GREEN}✅ Regular bots are creating games properly{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️ No active games found, but no move data issues detected{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}🚨 CRITICAL FAILURE: 'Missing move data' issues still exist!{Colors.END}")
        print(f"{Colors.RED}Found {len(issues)} games with creator_move=null in completed regular bot games.{Colors.END}")
        print(f"{Colors.RED}The fix is NOT working and needs a different approach.{Colors.END}")
        
        # Show details of issues
        print(f"\n{Colors.YELLOW}🔍 Issue Details:{Colors.END}")
        for i, issue in enumerate(issues[:5], 1):
            print(f"   {i}. Game {issue['game_id'][:12]}...")
            print(f"      creator_move: {issue['creator_move']}")
            print(f"      opponent_move: {issue['opponent_move']}")
            print(f"      status: {issue['status']}")
            print(f"      winner_id: {issue['winner_id']}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()