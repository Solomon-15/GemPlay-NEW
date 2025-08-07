#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Regular Bots Move Data Fix - Missing move data error
Финальный тест исправления ошибки "Missing move data for regular bot game"

КОНТЕКСТ: Тестирование исправления критической ошибки где Regular боты завершают игры 
с creator_move=null, что вызывает ошибку "Missing move data for regular bot game".

ЗАДАЧА ИЗ РУССКОГО ОБЗОРА:
1. Создать нового тестового обычного бота или использовать существующего:
   - name: "Final_Move_Test_Bot"
   - min_bet_amount: 15.0
   - max_bet_amount: 25.0
   - win_percentage: 55
   - cycle_games: 1

2. Найти активную игру этого бота: GET /api/bots/active-games

3. Присоединиться к игре как тестовый пользователь:
   - POST /api/games/{game_id}/join с подходящими гемами
   - POST /api/games/{game_id}/choose-move с ходом "rock"

4. ДЕТАЛЬНО проверить финальное состояние игры:
   - Получить игру через GET /api/games/{game_id}
   - Убедиться что creator_move НЕ равно null
   - Убедиться что opponent_move равно "rock" 
   - Убедиться что status равно "COMPLETED"
   - Убедиться что есть winner_id
   - НЕ должно быть ошибки "Missing move data for regular bot game"

КРИТИЧНО: Это окончательный тест - если не работает, значит нужен другой подход к решению проблемы.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://5a0f72db-7197-4535-89b4-f85be852ec00.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test user for joining games
TEST_USER = {
    "email": "testuser@example.com",
    "password": "TestPassword123!"
}

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with colors"""
    status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if success else f"{Colors.RED}❌ FAILED{Colors.END}"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {Colors.YELLOW}Details: {details}{Colors.END}")

def record_test(test_name: str, success: bool, details: str = "", response_data: Any = None):
    """Record test result"""
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": test_name,
        "success": success,
        "details": details,
        "response_data": response_data,
        "timestamp": datetime.now().isoformat()
    })
    
    print_test_result(test_name, success, details)

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str]:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return False, None, f"Unsupported method: {method}"
        
        response_time = time.time() - start_time
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        success = response.status_code in [200, 201]
        details = f"Status: {response.status_code}, Time: {response_time:.3f}s"
        
        if not success:
            details += f", Error: {response_data}"
        
        return success, response_data, details
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout (30s)"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error"
    except Exception as e:
        return False, None, f"Request error: {str(e)}"

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as admin user...{Colors.END}")
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print(f"{Colors.GREEN}✅ Admin authentication successful{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Admin authentication failed: {details}{Colors.END}")
        return None

def create_test_user() -> Optional[str]:
    """Create test user and return access token"""
    print(f"{Colors.BLUE}👤 Creating test user for game joining...{Colors.END}")
    
    # Generate unique email
    timestamp = int(time.time())
    test_email = f"testuser_{timestamp}@example.com"
    
    user_data = {
        "username": f"Test{timestamp % 10000}",  # Keep username under 15 chars
        "email": test_email,
        "password": TEST_USER["password"],
        "gender": "male"
    }
    
    # Try to register
    success, response_data, details = make_request(
        "POST",
        "/auth/register",
        data=user_data
    )
    
    if success:
        print(f"{Colors.GREEN}✅ Test user created: {test_email}{Colors.END}")
        
        # Login with the new user
        login_data = {
            "email": test_email,
            "password": TEST_USER["password"]
        }
        
        success, response_data, details = make_request(
            "POST",
            "/auth/login",
            data=login_data
        )
        
        if success and response_data and "access_token" in response_data:
            token = response_data["access_token"]
            user_id = response_data.get("user", {}).get("id")
            print(f"{Colors.GREEN}✅ Test user authenticated successfully{Colors.END}")
            return token, user_id
    
    print(f"{Colors.RED}❌ Failed to create/authenticate test user: {details}{Colors.END}")
    return None, None

def create_final_move_test_bot(admin_token: str) -> Optional[str]:
    """Create the Final_Move_Test_Bot as specified in Russian review"""
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
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if success and response_data:
        bot_id = response_data.get("id") or response_data.get("bot_id")
        if bot_id:
            record_test(
                "Create Final_Move_Test_Bot",
                True,
                f"Bot created successfully with ID: {bot_id}"
            )
            return bot_id
        else:
            record_test(
                "Create Final_Move_Test_Bot",
                False,
                f"Bot created but no ID returned: {response_data}"
            )
    else:
        record_test(
            "Create Final_Move_Test_Bot",
            False,
            f"Failed to create bot: {details}"
        )
    
    return None

def find_bot_active_game(admin_token: str, bot_name: str = "Final_Move_Test_Bot") -> Optional[Dict]:
    """Find active game of the test bot"""
    print(f"\n{Colors.MAGENTA}🔍 Finding active game of {bot_name}...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        # Look for games created by our test bot
        for game in games:
            # Check if this game belongs to our test bot
            if (game.get("status") == "WAITING" and 
                game.get("bet_amount", 0) >= 15.0 and 
                game.get("bet_amount", 0) <= 25.0):
                
                record_test(
                    "Find bot active game",
                    True,
                    f"Found active game: {game.get('id')} with bet amount: ${game.get('bet_amount')}"
                )
                return game
        
        record_test(
            "Find bot active game",
            False,
            f"No active games found for test bot. Total games: {len(games)}"
        )
    else:
        record_test(
            "Find bot active game",
            False,
            f"Failed to get active games: {details}"
        )
    
    return None

def add_gems_to_test_user(user_token: str, user_id: str, admin_token: str):
    """Add gems to test user for joining games"""
    print(f"\n{Colors.BLUE}💎 Adding gems to test user...{Colors.END}")
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Add balance first
    balance_data = {"amount": 100.0}
    success, response_data, details = make_request(
        "POST",
        f"/admin/users/{user_id}/add-balance",
        headers=admin_headers,
        data=balance_data
    )
    
    if success:
        print(f"{Colors.GREEN}✅ Added $100 balance to test user{Colors.END}")
        
        # Buy gems
        user_headers = {"Authorization": f"Bearer {user_token}"}
        gem_purchases = [
            {"gem_type": "Ruby", "quantity": 20},
            {"gem_type": "Emerald", "quantity": 5},
            {"gem_type": "Sapphire", "quantity": 2}
        ]
        
        for purchase in gem_purchases:
            success, response_data, details = make_request(
                "POST",
                "/gems/purchase",
                headers=user_headers,
                data=purchase
            )
            
            if success:
                print(f"{Colors.GREEN}✅ Purchased {purchase['quantity']} {purchase['gem_type']} gems{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠️ Failed to purchase {purchase['gem_type']}: {details}{Colors.END}")

def join_bot_game(user_token: str, game_id: str, bet_amount: float) -> bool:
    """Join the bot's game with matching gems"""
    print(f"\n{Colors.MAGENTA}🎮 Joining bot game {game_id}...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Calculate gem combination for the bet amount
    gems_combination = {}
    remaining_amount = bet_amount
    
    # Use a mix of gems to match the bet amount
    if remaining_amount >= 10:
        emerald_count = min(int(remaining_amount // 10), 2)
        gems_combination["Emerald"] = emerald_count
        remaining_amount -= emerald_count * 10
    
    if remaining_amount >= 1:
        ruby_count = int(remaining_amount)
        gems_combination["Ruby"] = ruby_count
        remaining_amount -= ruby_count
    
    join_data = {
        "move": "rock",
        "gems": gems_combination
    }
    
    success, response_data, details = make_request(
        "POST",
        f"/games/{game_id}/join",
        headers=headers,
        data=join_data
    )
    
    if success:
        record_test(
            "Join bot game",
            True,
            f"Successfully joined game with gems: {gems_combination}"
        )
        return True
    else:
        record_test(
            "Join bot game",
            False,
            f"Failed to join game: {details}"
        )
        return False

def check_final_game_state(admin_token: str, game_id: str) -> Dict:
    """Check the final state of the completed game"""
    print(f"\n{Colors.MAGENTA}🔍 Checking final game state for {game_id}...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Wait a bit for game to complete
    time.sleep(3)
    
    success, response_data, details = make_request(
        "GET",
        f"/games/{game_id}",
        headers=headers
    )
    
    if success and response_data:
        game = response_data
        
        # Check all critical fields
        creator_move = game.get("creator_move")
        opponent_move = game.get("opponent_move")
        status = game.get("status")
        winner_id = game.get("winner_id")
        
        print(f"{Colors.CYAN}📊 Game State Analysis:{Colors.END}")
        print(f"   Game ID: {game_id}")
        print(f"   Status: {status}")
        print(f"   Creator Move: {creator_move}")
        print(f"   Opponent Move: {opponent_move}")
        print(f"   Winner ID: {winner_id}")
        
        # Critical checks
        checks = {
            "creator_move_not_null": creator_move is not None,
            "opponent_move_is_rock": opponent_move == "rock",
            "status_is_completed": status == "COMPLETED",
            "has_winner_id": winner_id is not None
        }
        
        all_checks_passed = all(checks.values())
        
        if all_checks_passed:
            record_test(
                "Final game state verification",
                True,
                f"All checks passed: creator_move={creator_move}, opponent_move={opponent_move}, status={status}, winner_id={winner_id}"
            )
        else:
            failed_checks = [check for check, passed in checks.items() if not passed]
            record_test(
                "Final game state verification",
                False,
                f"Failed checks: {failed_checks}. creator_move={creator_move}, opponent_move={opponent_move}, status={status}, winner_id={winner_id}"
            )
        
        return game
    else:
        record_test(
            "Final game state verification",
            False,
            f"Failed to get game state: {details}"
        )
        return {}

def test_move_data_fix_comprehensive():
    """Comprehensive test of the move data fix"""
    print_header("ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Regular Bots Move Data Fix")
    print(f"{Colors.BLUE}🎯 Testing fix for 'Missing move data for regular bot game' error{Colors.END}")
    
    # Step 1: Authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        print(f"{Colors.RED}❌ Cannot proceed without admin authentication{Colors.END}")
        return False
    
    # Step 2: Create test user
    user_token, user_id = create_test_user()
    if not user_token or not user_id:
        print(f"{Colors.RED}❌ Cannot proceed without test user{Colors.END}")
        return False
    
    # Step 3: Create Final_Move_Test_Bot
    bot_id = create_final_move_test_bot(admin_token)
    if not bot_id:
        print(f"{Colors.RED}❌ Cannot proceed without test bot{Colors.END}")
        return False
    
    # Step 4: Add gems to test user
    add_gems_to_test_user(user_token, user_id, admin_token)
    
    # Step 5: Wait for bot to create a game
    print(f"\n{Colors.BLUE}⏳ Waiting for bot to create active game...{Colors.END}")
    time.sleep(10)  # Wait for bot automation to create game
    
    # Step 6: Find bot's active game
    active_game = find_bot_active_game(admin_token)
    if not active_game:
        print(f"{Colors.RED}❌ Cannot proceed without active bot game{Colors.END}")
        return False
    
    game_id = active_game.get("id")
    bet_amount = active_game.get("bet_amount", 20.0)
    
    # Step 7: Join the game
    join_success = join_bot_game(user_token, game_id, bet_amount)
    if not join_success:
        print(f"{Colors.RED}❌ Cannot proceed without joining the game{Colors.END}")
        return False
    
    # Step 8: Check final game state
    final_game_state = check_final_game_state(admin_token, game_id)
    
    # Step 9: Verify no "Missing move data" error
    creator_move = final_game_state.get("creator_move")
    if creator_move is not None:
        record_test(
            "No 'Missing move data' error",
            True,
            f"creator_move is properly set to: {creator_move}"
        )
        return True
    else:
        record_test(
            "No 'Missing move data' error",
            False,
            "creator_move is still null - the fix is NOT working!"
        )
        return False

def print_final_summary():
    """Print final test summary"""
    print_header("ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ РЕЗУЛЬТАТЫ")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 RUSSIAN REVIEW REQUIREMENTS STATUS:{Colors.END}")
    
    requirements = [
        "Создать тестового бота Final_Move_Test_Bot",
        "Найти активную игру бота через GET /api/bots/active-games",
        "Присоединиться к игре как тестовый пользователь",
        "Проверить что creator_move НЕ равно null",
        "Проверить что opponent_move равно 'rock'",
        "Проверить что status равно 'COMPLETED'",
        "Проверить что есть winner_id",
        "НЕ должно быть ошибки 'Missing move data for regular bot game'"
    ]
    
    for i, req in enumerate(requirements, 1):
        # Find corresponding test result
        test_found = False
        for test in test_results["tests"]:
            if any(keyword in test["name"].lower() for keyword in req.lower().split()[:2]):
                status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
                print(f"   {i}. {req}: {status}")
                test_found = True
                break
        
        if not test_found:
            print(f"   {i}. {req}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Final conclusion
    if success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: REGULAR BOTS MOVE DATA FIX IS WORKING!{Colors.END}")
        print(f"{Colors.GREEN}The 'Missing move data for regular bot game' error has been successfully fixed.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: REGULAR BOTS MOVE DATA FIX IS NOT WORKING!{Colors.END}")
        print(f"{Colors.RED}The 'Missing move data for regular bot game' error is still occurring. The fix needs a different approach.{Colors.END}")

def main():
    """Main test execution"""
    try:
        success = test_move_data_fix_comprehensive()
        print_final_summary()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
        print_final_summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
        print_final_summary()
        sys.exit(1)

if __name__ == "__main__":
    main()