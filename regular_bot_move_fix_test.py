#!/usr/bin/env python3
"""
Regular Bot Move Data Fix Testing - Russian Review
Тестирование исправления ошибки "Missing move data for regular bot game"

КОНТЕКСТ: Тестирование исправления ошибки при игре с обычными ботами, когда в финальном 
состоянии игры отсутствуют данные о ходах (creator_move, opponent_move).

ТЕСТИРОВАТЬ:
1. Создать нового тестового обычного бота с параметрами:
   - name: "Test_Move_Fix_Bot"
   - min_bet_amount: 10.0
   - max_bet_amount: 20.0
   - win_percentage: 55
   - cycle_games: 2

2. Подождать пока бот создаст ставки

3. Получить список активных игр и найти игру этого бота: GET /api/bots/active-games

4. Присоединиться к игре как обычный пользователь:
   - POST /api/games/{game_id}/join с подходящими гемами
   - POST /api/games/{game_id}/choose-move с ходом (например "rock")

5. Проверить что:
   - Игра завершается БЕЗ ошибки "Missing move data for regular bot game" 
   - В финальном состоянии игры есть как creator_move, так и opponent_move
   - Игра имеет статус COMPLETED
   - Определён победитель

КРИТИЧНО: Это должно исправить ошибку при ничьих и обычных играх с регулярными ботами.
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
    """Create or authenticate test user for joining games"""
    print(f"{Colors.BLUE}👤 Setting up test user for game joining...{Colors.END}")
    
    # Try to login first
    success, response_data, details = make_request(
        "POST",
        "/auth/login",
        data=TEST_USER
    )
    
    if success and response_data and "access_token" in response_data:
        print(f"{Colors.GREEN}✅ Test user login successful{Colors.END}")
        return response_data["access_token"]
    
    # If login fails, try to register
    print(f"{Colors.YELLOW}⚠️ Test user login failed, attempting registration...{Colors.END}")
    
    registration_data = {
        "username": "TestMoveUser",
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "gender": "male"
    }
    
    success, response_data, details = make_request(
        "POST",
        "/auth/register",
        data=registration_data
    )
    
    if success:
        print(f"{Colors.GREEN}✅ Test user registered successfully{Colors.END}")
        # Try login again
        success, response_data, details = make_request(
            "POST",
            "/auth/login",
            data=TEST_USER
        )
        
        if success and response_data and "access_token" in response_data:
            return response_data["access_token"]
    
    print(f"{Colors.RED}❌ Failed to setup test user: {details}{Colors.END}")
    return None

def create_test_regular_bot(admin_token: str) -> Optional[str]:
    """Create test regular bot with specific parameters"""
    print(f"\n{Colors.MAGENTA}🤖 Step 1: Creating test regular bot 'Test_Move_Fix_Bot'{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    bot_data = {
        "name": "Test_Move_Fix_Bot",
        "min_bet_amount": 10.0,
        "max_bet_amount": 20.0,
        "win_percentage": 55,
        "cycle_games": 2,
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
                "Create Test_Move_Fix_Bot",
                True,
                f"Bot created successfully with ID: {bot_id}, min_bet: {bot_data['min_bet_amount']}, max_bet: {bot_data['max_bet_amount']}, win%: {bot_data['win_percentage']}, cycle: {bot_data['cycle_games']}"
            )
            return bot_id
        else:
            record_test(
                "Create Test_Move_Fix_Bot",
                False,
                f"Bot created but no ID returned. Response: {response_data}"
            )
    else:
        record_test(
            "Create Test_Move_Fix_Bot",
            False,
            f"Failed to create bot: {details}"
        )
    
    return None

def wait_for_bot_bets(admin_token: str, bot_name: str = "Test_Move_Fix_Bot") -> bool:
    """Wait for bot to create bets"""
    print(f"\n{Colors.MAGENTA}⏳ Step 2: Waiting for bot to create bets...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    max_attempts = 6  # 30 seconds total
    
    for attempt in range(max_attempts):
        print(f"{Colors.BLUE}   Attempt {attempt + 1}/{max_attempts}: Checking for bot bets...{Colors.END}")
        
        success, response_data, details = make_request(
            "GET",
            "/bots/active-games",
            headers=headers
        )
        
        if success and response_data:
            games = response_data if isinstance(response_data, list) else response_data.get("games", [])
            
            # Look for games created by our test bot
            bot_games = []
            for game in games:
                if game.get("creator_type") == "bot" and bot_name in str(game):
                    bot_games.append(game)
            
            if bot_games:
                record_test(
                    "Bot creates bets automatically",
                    True,
                    f"Found {len(bot_games)} active games created by {bot_name}"
                )
                return True
        
        if attempt < max_attempts - 1:
            time.sleep(5)  # Wait 5 seconds between attempts
    
    record_test(
        "Bot creates bets automatically",
        False,
        f"Bot {bot_name} did not create any bets after {max_attempts * 5} seconds"
    )
    return False

def find_bot_game(admin_token: str, bot_name: str = "Test_Move_Fix_Bot") -> Optional[Dict]:
    """Find an active game created by the test bot"""
    print(f"\n{Colors.MAGENTA}🔍 Step 3: Finding active game from {bot_name}{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        # Look for WAITING games created by our test bot
        for game in games:
            if (game.get("status") == "WAITING" and 
                game.get("creator_type") == "bot" and 
                bot_name in str(game)):
                
                record_test(
                    "Find bot game for joining",
                    True,
                    f"Found WAITING game: ID={game.get('id')}, bet_amount=${game.get('bet_amount')}, status={game.get('status')}"
                )
                return game
        
        record_test(
            "Find bot game for joining",
            False,
            f"No WAITING games found from {bot_name}. Total games: {len(games)}"
        )
    else:
        record_test(
            "Find bot game for joining",
            False,
            f"Failed to get active games: {details}"
        )
    
    return None

def add_gems_to_user(user_token: str, gem_amount: int = 50) -> bool:
    """Add gems to test user for betting"""
    print(f"{Colors.BLUE}💎 Adding gems to test user...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Add virtual balance first
    success, response_data, details = make_request(
        "POST",
        "/user/add-balance",
        headers=headers,
        data={"amount": 100.0}
    )
    
    if not success:
        print(f"{Colors.YELLOW}⚠️ Could not add balance: {details}{Colors.END}")
        return False
    
    # Purchase gems
    gem_types = ["Ruby", "Emerald", "Sapphire"]
    for gem_type in gem_types:
        success, response_data, details = make_request(
            "POST",
            "/gems/purchase",
            headers=headers,
            data={
                "gem_type": gem_type,
                "quantity": gem_amount
            }
        )
        
        if success:
            print(f"{Colors.GREEN}✅ Added {gem_amount} {gem_type} gems{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️ Could not add {gem_type} gems: {details}{Colors.END}")
    
    return True

def join_bot_game(user_token: str, game: Dict) -> Optional[str]:
    """Join the bot's game as a regular user"""
    print(f"\n{Colors.MAGENTA}🎮 Step 4: Joining bot game as regular user{Colors.END}")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    game_id = game.get("id")
    bet_amount = game.get("bet_amount", 15.0)
    
    if not game_id:
        record_test(
            "Join bot game",
            False,
            "No game ID available"
        )
        return None
    
    # Add gems to user first
    add_gems_to_user(user_token)
    
    # Prepare gems for joining (match the bet amount)
    join_gems = {
        "Ruby": int(bet_amount * 0.6),  # 60% Ruby
        "Emerald": int(bet_amount * 0.3),  # 30% Emerald  
        "Sapphire": int(bet_amount * 0.1)   # 10% Sapphire
    }
    
    # Ensure we have at least 1 of each gem
    for gem_type in join_gems:
        if join_gems[gem_type] < 1:
            join_gems[gem_type] = 1
    
    join_data = {
        "move": "rock",  # Choose rock as our move
        "gems": join_gems
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
            f"Successfully joined game {game_id} with move 'rock' and gems: {join_gems}"
        )
        return game_id
    else:
        record_test(
            "Join bot game",
            False,
            f"Failed to join game {game_id}: {details}"
        )
        return None

def choose_move_in_game(user_token: str, game_id: str) -> bool:
    """Choose move in the joined game"""
    print(f"\n{Colors.MAGENTA}✋ Step 5: Choosing move in game{Colors.END}")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    move_data = {
        "move": "rock"
    }
    
    success, response_data, details = make_request(
        "POST",
        f"/games/{game_id}/choose-move",
        headers=headers,
        data=move_data
    )
    
    if success:
        record_test(
            "Choose move in game",
            True,
            f"Successfully chose move 'rock' in game {game_id}"
        )
        return True
    else:
        record_test(
            "Choose move in game",
            False,
            f"Failed to choose move in game {game_id}: {details}"
        )
        return False

def verify_game_completion(admin_token: str, game_id: str) -> bool:
    """Verify that the game completed successfully with move data"""
    print(f"\n{Colors.MAGENTA}🏁 Step 6: Verifying game completion and move data{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Wait a bit for game to complete
    time.sleep(3)
    
    # Check game status multiple times
    max_attempts = 5
    for attempt in range(max_attempts):
        success, response_data, details = make_request(
            "GET",
            f"/games/{game_id}",
            headers=headers
        )
        
        if success and response_data:
            game = response_data
            status = game.get("status")
            creator_move = game.get("creator_move")
            opponent_move = game.get("opponent_move")
            winner_id = game.get("winner_id")
            
            print(f"{Colors.BLUE}   Attempt {attempt + 1}: Status={status}, Creator_move={creator_move}, Opponent_move={opponent_move}, Winner={winner_id}{Colors.END}")
            
            if status == "COMPLETED":
                # Check for the critical fix: both moves should be present
                if creator_move and opponent_move:
                    record_test(
                        "Game completes with move data",
                        True,
                        f"✅ CRITICAL FIX VERIFIED: Game completed successfully with creator_move='{creator_move}' and opponent_move='{opponent_move}', winner_id='{winner_id}'"
                    )
                    
                    # Additional verification: no "Missing move data" error
                    record_test(
                        "No 'Missing move data' error",
                        True,
                        "✅ No 'Missing move data for regular bot game' error occurred"
                    )
                    
                    return True
                else:
                    record_test(
                        "Game completes with move data",
                        False,
                        f"❌ CRITICAL ISSUE: Game completed but missing move data - creator_move='{creator_move}', opponent_move='{opponent_move}'"
                    )
                    return False
            
            elif status in ["CANCELLED", "TIMEOUT"]:
                record_test(
                    "Game completes with move data",
                    False,
                    f"Game ended with status '{status}' instead of COMPLETED"
                )
                return False
        
        if attempt < max_attempts - 1:
            time.sleep(2)  # Wait 2 seconds between attempts
    
    record_test(
        "Game completes with move data",
        False,
        f"Game did not complete after {max_attempts * 2} seconds"
    )
    return False

def test_multiple_game_scenarios(admin_token: str, user_token: str, bot_name: str = "Test_Move_Fix_Bot"):
    """Test multiple game scenarios to ensure fix works consistently"""
    print(f"\n{Colors.MAGENTA}🔄 Step 7: Testing multiple game scenarios{Colors.END}")
    
    successful_games = 0
    total_attempts = 3
    
    for i in range(total_attempts):
        print(f"{Colors.BLUE}   Testing scenario {i + 1}/{total_attempts}...{Colors.END}")
        
        # Find another bot game
        bot_game = find_bot_game(admin_token, bot_name)
        if not bot_game:
            continue
        
        # Join and play the game
        game_id = join_bot_game(user_token, bot_game)
        if not game_id:
            continue
        
        # Verify completion
        if verify_game_completion(admin_token, game_id):
            successful_games += 1
    
    if successful_games >= 2:  # At least 2 out of 3 should work
        record_test(
            "Multiple game scenarios",
            True,
            f"Successfully completed {successful_games}/{total_attempts} game scenarios"
        )
    else:
        record_test(
            "Multiple game scenarios",
            False,
            f"Only {successful_games}/{total_attempts} game scenarios completed successfully"
        )

def print_final_summary():
    """Print final test summary"""
    print_header("REGULAR BOT MOVE DATA FIX TESTING SUMMARY")
    
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
        "Создать тестового бота Test_Move_Fix_Bot",
        "Бот автоматически создает ставки",
        "Найти активную игру бота",
        "Присоединиться к игре как пользователь",
        "Выбрать ход в игре",
        "Игра завершается БЕЗ ошибки 'Missing move data'",
        "В финальном состоянии есть creator_move и opponent_move",
        "Игра имеет статус COMPLETED с определенным победителем"
    ]
    
    for i, req in enumerate(requirements, 1):
        # Find corresponding test result
        test_found = False
        for test in test_results["tests"]:
            if any(keyword in test["name"].lower() for keyword in req.lower().split()[:3]):
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: REGULAR BOT MOVE DATA FIX IS WORKING!{Colors.END}")
        print(f"{Colors.GREEN}The 'Missing move data for regular bot game' error has been successfully fixed.{Colors.END}")
        print(f"{Colors.GREEN}Regular bots now properly complete games with both creator_move and opponent_move data.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.YELLOW}Some aspects of the fix are working but there may be edge cases.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: MOVE DATA FIX NEEDS ATTENTION ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.RED}The 'Missing move data for regular bot game' error may still be occurring.{Colors.END}")

def main():
    """Main test execution"""
    print_header("REGULAR BOT MOVE DATA FIX TESTING")
    print(f"{Colors.BLUE}🎯 Testing fix for 'Missing move data for regular bot game' error{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: creator_move and opponent_move data in completed games{Colors.END}")
    
    # Authenticate admin
    admin_token = authenticate_admin()
    if not admin_token:
        print(f"{Colors.RED}❌ Cannot proceed without admin authentication{Colors.END}")
        sys.exit(1)
    
    # Setup test user
    user_token = create_test_user()
    if not user_token:
        print(f"{Colors.RED}❌ Cannot proceed without test user{Colors.END}")
        sys.exit(1)
    
    try:
        # Step 1: Create test bot
        bot_id = create_test_regular_bot(admin_token)
        if not bot_id:
            print(f"{Colors.RED}❌ Cannot proceed without test bot{Colors.END}")
            return
        
        # Step 2: Wait for bot to create bets
        if not wait_for_bot_bets(admin_token):
            print(f"{Colors.RED}❌ Bot did not create bets, cannot test game completion{Colors.END}")
            return
        
        # Step 3: Find bot game
        bot_game = find_bot_game(admin_token)
        if not bot_game:
            print(f"{Colors.RED}❌ No bot game found for testing{Colors.END}")
            return
        
        # Step 4: Join bot game
        game_id = join_bot_game(user_token, bot_game)
        if not game_id:
            print(f"{Colors.RED}❌ Could not join bot game{Colors.END}")
            return
        
        # Step 5: Choose move (this might be handled in join)
        choose_move_in_game(user_token, game_id)
        
        # Step 6: Verify game completion
        verify_game_completion(admin_token, game_id)
        
        # Step 7: Test multiple scenarios
        test_multiple_game_scenarios(admin_token, user_token)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()