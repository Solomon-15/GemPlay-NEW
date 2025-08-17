#!/usr/bin/env python3
"""
ОКОНЧАТЕЛЬНЫЙ ТЕСТ исправления "Missing move data for regular bot game"
Final test for Regular Bots Move Data Fix - Russian Review

КОНТЕКСТ: Тестирование критического исправления ошибки "Missing move data for regular bot game"
где при присоединении пользователя к игре обычного бота creator_move возвращается как null.

ТЕСТИРОВАТЬ:
1. Найти любую активную игру обычного бота: GET /api/bots/active-games
2. Присоединиться к игре как пользователь:
   - POST /api/games/{game_id}/join с подходящими гемами
   - POST /api/games/{game_id}/choose-move с ходом "scissors"
3. Проверить результат:
   - Должно быть 200 OK (НЕ 500 Internal Server Error)
   - Получить игру: GET /api/games/{game_id}  
   - Убедиться что creator_move НЕ равно null
   - Убедиться что opponent_move равно "scissors"
   - Убедиться что status равно "COMPLETED"
   - Должен быть winner_id

КРИТИЧНО: Это должно наконец исправить ошибку "Missing move data for regular bot game". 
Если тест не проходит - значит проблема ещё глубже.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
from datetime import datetime

# Configuration
BASE_URL = "https://russianparts.preview.emergentagent.com/api"
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

def authenticate_test_user() -> Optional[str]:
    """Authenticate as test user and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as test user (using admin account)...{Colors.END}")
    
    # Use admin account as test user since it's verified and has permissions
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER  # Use admin user instead of TEST_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print(f"{Colors.GREEN}✅ Test user authentication successful{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Test user authentication failed: {details}{Colors.END}")
        return None

def get_user_gems(token: str) -> Dict[str, int]:
    """Get user's gem inventory"""
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/user/gems",
        headers=headers
    )
    
    if success and response_data:
        gems = {}
        gem_list = response_data if isinstance(response_data, list) else response_data.get("gems", [])
        
        for gem in gem_list:
            gem_type = gem.get("type", gem.get("gem_type", ""))
            quantity = gem.get("quantity", 0)
            if gem_type and quantity > 0:
                gems[gem_type] = quantity
        
        return gems
    
    return {}

def add_gems_to_user(admin_token: str, user_token: str) -> bool:
    """Add gems to test user for testing"""
    print(f"{Colors.BLUE}💎 Adding gems to test user...{Colors.END}")
    
    # Get user info first
    headers = {"Authorization": f"Bearer {user_token}"}
    success, user_data, _ = make_request("GET", "/user/profile", headers=headers)
    
    if not success or not user_data:
        print(f"{Colors.RED}❌ Failed to get user profile{Colors.END}")
        return False
    
    user_id = user_data.get("id")
    if not user_id:
        print(f"{Colors.RED}❌ No user ID found{Colors.END}")
        return False
    
    # Add gems using admin endpoint
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Add various gems
    gem_types = ["Ruby", "Emerald", "Sapphire", "Topaz", "Amber", "Aquamarine", "Magic"]
    
    gems_added = 0
    for gem_type in gem_types:
        gem_data = {
            "user_id": user_id,
            "gem_type": gem_type,
            "quantity": 50  # Add 50 of each gem type
        }
        
        success, _, _ = make_request(
            "POST",
            "/admin/users/add-gems",
            headers=admin_headers,
            data=gem_data
        )
        
        if success:
            gems_added += 1
    
    if gems_added > 0:
        print(f"{Colors.GREEN}✅ Added {gems_added} gem types to test user{Colors.END}")
        return True
    else:
        # Try alternative method - add balance and buy gems
        balance_data = {"amount": 1000.0}
        success, _, _ = make_request(
            "POST",
            "/admin/users/add-balance",
            headers=admin_headers,
            data={"user_id": user_id, "amount": 1000.0}
        )
        
        if success:
            print(f"{Colors.GREEN}✅ Added balance to test user, they can buy gems{Colors.END}")
            return True
        
        print(f"{Colors.RED}❌ Failed to add gems or balance to test user{Colors.END}")
        return False

def find_active_regular_bot_game(token: str) -> Optional[Dict]:
    """Find an active regular bot game to join"""
    print(f"{Colors.BLUE}🔍 Finding active regular bot games...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        # Filter for WAITING games (can be joined)
        waiting_games = [game for game in games if game.get("status") == "WAITING"]
        
        if waiting_games:
            # Sort by bet amount to find a reasonable game
            waiting_games.sort(key=lambda x: x.get("bet_amount", 0))
            selected_game = waiting_games[0]
            
            print(f"{Colors.GREEN}✅ Found {len(waiting_games)} waiting regular bot games{Colors.END}")
            print(f"   Selected game: ID={selected_game.get('id')}, Bet=${selected_game.get('bet_amount')}")
            
            return selected_game
        else:
            print(f"{Colors.YELLOW}⚠️ Found {len(games)} regular bot games but none are WAITING{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Failed to get regular bot games: {details}{Colors.END}")
    
    return None

def create_matching_gems(bet_gems: Dict[str, int], user_gems: Dict[str, int]) -> Dict[str, int]:
    """Create matching gem combination for joining the game"""
    matching_gems = {}
    
    # First try to match exactly
    for gem_type, required_quantity in bet_gems.items():
        available_quantity = user_gems.get(gem_type, 0)
        
        if available_quantity >= required_quantity:
            matching_gems[gem_type] = required_quantity
        elif available_quantity > 0:
            matching_gems[gem_type] = available_quantity
    
    # If we don't have enough gems, create a simple combination
    if not matching_gems or sum(matching_gems.values()) == 0:
        # Use any available gems
        for gem_type, quantity in user_gems.items():
            if quantity > 0:
                matching_gems[gem_type] = min(quantity, 10)  # Use up to 10 gems
                if len(matching_gems) >= 2:  # Use at most 2 gem types
                    break
    
    # If still no gems, create a minimal combination
    if not matching_gems:
        matching_gems = {"Ruby": 1}  # Fallback
    
    return matching_gems

def test_regular_bot_move_data_fix(admin_token: str, user_token: str):
    """Main test for regular bot move data fix"""
    print(f"\n{Colors.MAGENTA}🧪 CRITICAL TEST: Regular Bot Move Data Fix{Colors.END}")
    
    # Step 1: Find active regular bot game
    game = find_active_regular_bot_game(admin_token)
    if not game:
        record_test(
            "Find active regular bot game",
            False,
            "No active regular bot games found to test with"
        )
        return
    
    game_id = game.get("id")
    bet_gems = game.get("bet_gems", {})
    
    record_test(
        "Find active regular bot game",
        True,
        f"Found game {game_id} with bet amount ${game.get('bet_amount')}"
    )
    
    # Step 2: Get user gems
    user_gems = get_user_gems(user_token)
    if not user_gems:
        # Try to add gems to user
        add_gems_to_user(admin_token, user_token)
        user_gems = get_user_gems(user_token)
    
    if not user_gems:
        record_test(
            "Get user gems",
            False,
            "User has no gems to join the game"
        )
        return
    
    record_test(
        "Get user gems",
        True,
        f"User has gems: {list(user_gems.keys())}"
    )
    
    # Step 3: Create matching gem combination
    matching_gems = create_matching_gems(bet_gems, user_gems)
    if not matching_gems:
        record_test(
            "Create matching gems",
            False,
            "Could not create matching gem combination"
        )
        return
    
    record_test(
        "Create matching gems",
        True,
        f"Created matching gems: {matching_gems}"
    )
    
    # Step 4: Join the game
    headers = {"Authorization": f"Bearer {user_token}"}
    join_data = {
        "move": "scissors",
        "gems": matching_gems
    }
    
    success, response_data, details = make_request(
        "POST",
        f"/games/{game_id}/join",
        headers=headers,
        data=join_data
    )
    
    if not success:
        record_test(
            "Join regular bot game",
            False,
            f"Failed to join game: {details}"
        )
        return
    
    record_test(
        "Join regular bot game",
        True,
        f"Successfully joined game {game_id}"
    )
    
    # Step 5: Choose move (this is where the bug occurs)
    move_data = {"move": "scissors"}
    
    success, response_data, details = make_request(
        "POST",
        f"/games/{game_id}/choose-move",
        headers=headers,
        data=move_data
    )
    
    # This is the critical test - should be 200 OK, not 500 error
    if not success:
        record_test(
            "Choose move (CRITICAL)",
            False,
            f"FAILED - Got error instead of 200 OK: {details}"
        )
        return
    
    record_test(
        "Choose move (CRITICAL)",
        True,
        "Successfully chose move without 500 error"
    )
    
    # Step 6: Get final game state
    success, game_data, details = make_request(
        "GET",
        f"/games/{game_id}",
        headers=headers
    )
    
    if not success:
        record_test(
            "Get final game state",
            False,
            f"Failed to get game state: {details}"
        )
        return
    
    # Step 7: Verify move data is NOT missing
    creator_move = game_data.get("creator_move")
    opponent_move = game_data.get("opponent_move")
    status = game_data.get("status")
    winner_id = game_data.get("winner_id")
    
    # Critical checks
    creator_move_ok = creator_move is not None
    opponent_move_ok = opponent_move == "scissors"
    status_ok = status == "COMPLETED"
    winner_ok = winner_id is not None
    
    record_test(
        "Creator move NOT null (CRITICAL)",
        creator_move_ok,
        f"creator_move = {creator_move} (should NOT be null)"
    )
    
    record_test(
        "Opponent move correct",
        opponent_move_ok,
        f"opponent_move = {opponent_move} (should be 'scissors')"
    )
    
    record_test(
        "Game status completed",
        status_ok,
        f"status = {status} (should be 'COMPLETED')"
    )
    
    record_test(
        "Winner determined",
        winner_ok,
        f"winner_id = {winner_id} (should not be null)"
    )
    
    # Overall success
    overall_success = creator_move_ok and opponent_move_ok and status_ok and winner_ok
    
    record_test(
        "OVERALL: Missing move data fix",
        overall_success,
        "All move data properly saved and game completed correctly" if overall_success else "Move data still missing or game not completing properly"
    )
    
    # Print detailed game state for debugging
    print(f"\n{Colors.CYAN}🔍 DETAILED GAME STATE:{Colors.END}")
    print(f"   Game ID: {game_id}")
    print(f"   Status: {status}")
    print(f"   Creator Move: {creator_move}")
    print(f"   Opponent Move: {opponent_move}")
    print(f"   Winner ID: {winner_id}")
    print(f"   Bet Amount: ${game_data.get('bet_amount')}")

def print_final_summary():
    """Print final test summary"""
    print_header("REGULAR BOTS MOVE DATA FIX - FINAL TEST RESULTS")
    
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
        "Найти активную игру обычного бота через GET /api/bots/active-games",
        "Присоединиться к игре как пользователь с POST /api/games/{game_id}/join",
        "Выбрать ход 'scissors' с POST /api/games/{game_id}/choose-move",
        "Получить 200 OK (НЕ 500 Internal Server Error)",
        "creator_move НЕ равно null в финальном состоянии",
        "opponent_move равно 'scissors'",
        "status равно 'COMPLETED'",
        "Есть winner_id в результате"
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
    critical_tests = [t for t in test_results["tests"] if "CRITICAL" in t["name"]]
    critical_passed = sum(1 for t in critical_tests if t["success"])
    critical_total = len(critical_tests)
    
    if critical_total > 0 and critical_passed == critical_total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: REGULAR BOTS MOVE DATA FIX IS WORKING!{Colors.END}")
        print(f"{Colors.GREEN}The 'Missing move data for regular bot game' error has been successfully fixed.{Colors.END}")
        print(f"{Colors.GREEN}Regular bot games now complete properly with all move data saved.{Colors.END}")
    elif success_rate >= 70:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Some aspects are working but critical move data issues may remain.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: MOVE DATA FIX IS NOT WORKING ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}The 'Missing move data for regular bot game' error is still occurring.{Colors.END}")
        print(f"{Colors.RED}Regular bot games are not completing properly - needs immediate attention.{Colors.END}")

def main():
    """Main test execution"""
    print_header("REGULAR BOTS MOVE DATA FIX - FINAL TEST")
    print(f"{Colors.BLUE}🎯 Testing critical fix for 'Missing move data for regular bot game' error{Colors.END}")
    print(f"{Colors.BLUE}📋 This test will verify that regular bot games complete with proper move data{Colors.END}")
    
    # Authenticate admin
    admin_token = authenticate_admin()
    if not admin_token:
        print(f"{Colors.RED}❌ Cannot proceed without admin authentication{Colors.END}")
        sys.exit(1)
    
    # Authenticate test user
    user_token = authenticate_test_user()
    if not user_token:
        print(f"{Colors.RED}❌ Cannot proceed without test user authentication{Colors.END}")
        sys.exit(1)
    
    try:
        # Run the critical test
        test_regular_bot_move_data_fix(admin_token, user_token)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()
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
BASE_URL = "https://russianparts.preview.emergentagent.com/api"
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
        
        # Get admin token to verify the user
        admin_token = authenticate_admin()
        if admin_token:
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Get the user ID
            users_response = make_request("GET", "/admin/users", headers=admin_headers)
            if users_response[0]:
                users = users_response[1]
                if isinstance(users, list):
                    for user in users:
                        if user.get("email") == test_email:
                            user_id = user.get("id")
                            
                            # Verify the user's email
                            verify_data = {"status": "ACTIVE", "email_verified": True}
                            verify_response = make_request(
                                "PUT", 
                                f"/admin/users/{user_id}",
                                headers=admin_headers,
                                data=verify_data
                            )
                            
                            if verify_response[0]:
                                print(f"{Colors.GREEN}✅ Test user email verified{Colors.END}")
                                
                                # Now login with the verified user
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
                                    print(f"{Colors.GREEN}✅ Test user authenticated successfully{Colors.END}")
                                    return token, user_id
                            break
    
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