#!/usr/bin/env python3
"""
RUSSIAN REVIEW LOBBY REQUIREMENTS TESTING
Проверить бэкенд на соответствие новым правкам лобби:

1) /api/bots/active-games — creator_username должен быть "Bot" для всех; статус только WAITING; is_regular_bot=true; нет реальных имён.
2) /api/bots/ongoing-games — creator_username "Bot"; статус только ACTIVE; opponent.username реальный игрок (не Bot/Unknown); нет смешивания с human-bot или живыми игроками.
3) /api/games/available и /api/games/active-human-bots — обычные боты не попадают; ставки обычных ботов не возвращаются ни под какими именами. В частности, /games/active-human-bots больше не должен возвращать ACTIVE игры с регулярными ботами из-за фильтра по opponent_id без [None].

Использовать admin@gemplay.com / Admin123! для авторизации
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://russian-writing-4.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
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

def test_bots_active_games():
    """Test 1: /api/bots/active-games — creator_username должен быть "Bot" для всех; статус только WAITING; is_regular_bot=true; нет реальных имён."""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Testing /api/bots/active-games Requirements{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bots Active Games Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/bots/active-games endpoint...")
    
    # Test bots active games endpoint
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not response_data:
        record_test("Bots Active Games Test", False, f"Failed to get active games: {details}")
        return
    
    # Parse response data
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} active bot games")
    
    # Check requirements
    issues = []
    valid_games = 0
    
    for i, game in enumerate(games):
        game_issues = []
        
        # Check creator_username should be "Bot"
        creator_username = game.get("creator_username", "")
        if creator_username != "Bot":
            game_issues.append(f"creator_username is '{creator_username}' instead of 'Bot'")
        
        # Check status should be WAITING only
        status = game.get("status", "")
        if status != "WAITING":
            game_issues.append(f"status is '{status}' instead of 'WAITING'")
        
        # Check is_regular_bot should be true
        is_regular_bot = game.get("is_regular_bot", False)
        if not is_regular_bot:
            game_issues.append(f"is_regular_bot is {is_regular_bot} instead of true")
        
        # Check no real names (should not contain common real name patterns)
        real_name_patterns = ["Alex", "Anna", "Dmitry", "Elena", "Sergey", "Natalia", "Oleg", "Irina", "Player"]
        if any(pattern in creator_username for pattern in real_name_patterns):
            game_issues.append(f"creator_username '{creator_username}' contains real name pattern")
        
        if not game_issues:
            valid_games += 1
        else:
            issues.extend([f"Game {i+1}: {issue}" for issue in game_issues])
    
    # Evaluate results
    if len(games) == 0:
        record_test("Bots Active Games Test", True, "No active bot games found (acceptable)")
    elif len(issues) == 0:
        record_test(
            "Bots Active Games Test", 
            True, 
            f"All {len(games)} games comply: creator_username='Bot', status='WAITING', is_regular_bot=true"
        )
    else:
        record_test(
            "Bots Active Games Test", 
            False, 
            f"{len(issues)} compliance issues found in {len(games)} games: {'; '.join(issues[:3])}..."
        )

def test_bots_ongoing_games():
    """Test 2: /api/bots/ongoing-games — creator_username "Bot"; статус только ACTIVE; opponent.username реальный игрок (не Bot/Unknown); нет смешивания с human-bot или живыми игроками."""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Testing /api/bots/ongoing-games Requirements{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bots Ongoing Games Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/bots/ongoing-games endpoint...")
    
    # Test bots ongoing games endpoint
    success, response_data, details = make_request(
        "GET",
        "/bots/ongoing-games",
        headers=headers
    )
    
    if not success or not response_data:
        record_test("Bots Ongoing Games Test", False, f"Failed to get ongoing games: {details}")
        return
    
    # Parse response data
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} ongoing bot games")
    
    # Check requirements
    issues = []
    valid_games = 0
    
    for i, game in enumerate(games):
        game_issues = []
        
        # Check creator_username should be "Bot"
        creator_username = game.get("creator_username", "")
        if creator_username != "Bot":
            game_issues.append(f"creator_username is '{creator_username}' instead of 'Bot'")
        
        # Check status should be ACTIVE only
        status = game.get("status", "")
        if status != "ACTIVE":
            game_issues.append(f"status is '{status}' instead of 'ACTIVE'")
        
        # Check opponent.username should be real player (not Bot/Unknown)
        opponent = game.get("opponent", {})
        opponent_username = opponent.get("username", "") if isinstance(opponent, dict) else ""
        
        if opponent_username in ["Bot", "Unknown", "Unknown Player", ""]:
            game_issues.append(f"opponent.username is '{opponent_username}' (should be real player)")
        
        # Check no mixing with human-bot or live players (should be regular bot games only)
        bot_type = game.get("bot_type", "")
        creator_type = game.get("creator_type", "")
        
        if bot_type != "REGULAR" and creator_type != "bot":
            game_issues.append(f"bot_type is '{bot_type}', creator_type is '{creator_type}' (should be REGULAR bot)")
        
        if not game_issues:
            valid_games += 1
        else:
            issues.extend([f"Game {i+1}: {issue}" for issue in game_issues])
    
    # Evaluate results
    if len(games) == 0:
        record_test("Bots Ongoing Games Test", True, "No ongoing bot games found (acceptable)")
    elif len(issues) == 0:
        record_test(
            "Bots Ongoing Games Test", 
            True, 
            f"All {len(games)} games comply: creator_username='Bot', status='ACTIVE', real opponent usernames"
        )
    else:
        record_test(
            "Bots Ongoing Games Test", 
            False, 
            f"{len(issues)} compliance issues found in {len(games)} games: {'; '.join(issues[:3])}..."
        )

def test_games_available():
    """Test 3a: /api/games/available — обычные боты не попадают; ставки обычных ботов не возвращаются ни под какими именами."""
    print(f"\n{Colors.MAGENTA}🧪 Test 3a: Testing /api/games/available Requirements{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Games Available Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/games/available endpoint...")
    
    # Test games available endpoint
    success, response_data, details = make_request(
        "GET",
        "/games/available",
        headers=headers
    )
    
    if not success or not response_data:
        record_test("Games Available Test", False, f"Failed to get available games: {details}")
        return
    
    # Parse response data
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} available games")
    
    # Check requirements - no regular bots should appear
    issues = []
    regular_bot_games = 0
    
    for i, game in enumerate(games):
        # Check if this is a regular bot game
        is_regular_bot = game.get("is_regular_bot", False)
        bot_type = game.get("bot_type", "")
        creator_type = game.get("creator_type", "")
        creator_username = game.get("creator_username", "")
        
        # Multiple ways to identify regular bot games
        is_regular_bot_game = (
            is_regular_bot or 
            bot_type == "REGULAR" or 
            (creator_type == "bot" and creator_username == "Bot") or
            creator_username == "Bot"
        )
        
        if is_regular_bot_game:
            regular_bot_games += 1
            issues.append(f"Game {i+1}: Regular bot game found (creator: '{creator_username}', bot_type: '{bot_type}', is_regular_bot: {is_regular_bot})")
    
    # Evaluate results
    if regular_bot_games == 0:
        record_test(
            "Games Available Test", 
            True, 
            f"No regular bot games found in {len(games)} available games (correct exclusion)"
        )
    else:
        record_test(
            "Games Available Test", 
            False, 
            f"{regular_bot_games} regular bot games found in available games: {'; '.join(issues[:3])}..."
        )

def test_games_active_human_bots():
    """Test 3b: /api/games/active-human-bots — обычные боты не попадают; больше не должен возвращать ACTIVE игры с регулярными ботами из-за фильтра по opponent_id без [None]."""
    print(f"\n{Colors.MAGENTA}🧪 Test 3b: Testing /api/games/active-human-bots Requirements{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Games Active Human Bots Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/games/active-human-bots endpoint...")
    
    # Test games active human bots endpoint
    success, response_data, details = make_request(
        "GET",
        "/games/active-human-bots",
        headers=headers
    )
    
    if not success or not response_data:
        record_test("Games Active Human Bots Test", False, f"Failed to get active human bot games: {details}")
        return
    
    # Parse response data
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} active human bot games")
    
    # Check requirements - no regular bots should appear
    issues = []
    regular_bot_games = 0
    
    for i, game in enumerate(games):
        # Check if this is a regular bot game
        is_regular_bot = game.get("is_regular_bot", False)
        bot_type = game.get("bot_type", "")
        creator_type = game.get("creator_type", "")
        creator_username = game.get("creator_username", "")
        opponent_id = game.get("opponent_id")
        
        # Multiple ways to identify regular bot games
        is_regular_bot_game = (
            is_regular_bot or 
            bot_type == "REGULAR" or 
            (creator_type == "bot" and creator_username == "Bot") or
            creator_username == "Bot"
        )
        
        # Also check for ACTIVE games with regular bots (should be filtered out)
        status = game.get("status", "")
        if is_regular_bot_game and status == "ACTIVE":
            regular_bot_games += 1
            issues.append(f"Game {i+1}: ACTIVE regular bot game found (creator: '{creator_username}', status: '{status}', opponent_id: {opponent_id})")
        elif is_regular_bot_game:
            regular_bot_games += 1
            issues.append(f"Game {i+1}: Regular bot game found (creator: '{creator_username}', bot_type: '{bot_type}')")
    
    # Evaluate results
    if regular_bot_games == 0:
        record_test(
            "Games Active Human Bots Test", 
            True, 
            f"No regular bot games found in {len(games)} active human bot games (correct exclusion)"
        )
    else:
        record_test(
            "Games Active Human Bots Test", 
            False, 
            f"{regular_bot_games} regular bot games found in active human bot games: {'; '.join(issues[:3])}..."
        )

def print_lobby_requirements_summary():
    """Print Russian Review Lobby Requirements testing summary"""
    print_header("RUSSIAN REVIEW LOBBY REQUIREMENTS TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 LOBBY REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each requirement
    active_games_test = next((test for test in test_results["tests"] if "active games" in test["name"].lower() and "bots" in test["name"].lower()), None)
    ongoing_games_test = next((test for test in test_results["tests"] if "ongoing games" in test["name"].lower()), None)
    available_games_test = next((test for test in test_results["tests"] if "available" in test["name"].lower()), None)
    human_bots_test = next((test for test in test_results["tests"] if "human bots" in test["name"].lower()), None)
    
    requirements = [
        ("1. /api/bots/active-games (creator_username='Bot', WAITING, is_regular_bot=true)", active_games_test),
        ("2. /api/bots/ongoing-games (creator_username='Bot', ACTIVE, real opponents)", ongoing_games_test),
        ("3a. /api/games/available (no regular bots)", available_games_test),
        ("3b. /api/games/active-human-bots (no regular bots, no ACTIVE regular bot games)", human_bots_test)
    ]
    
    for req_name, test in requirements:
        if test:
            status = f"{Colors.GREEN}✅ COMPLIANT{Colors.END}" if test["success"] else f"{Colors.RED}❌ NON-COMPLIANT{Colors.END}"
            print(f"   {req_name}: {status}")
            if test["details"]:
                print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
        else:
            print(f"   {req_name}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: ALL LOBBY REQUIREMENTS ARE COMPLIANT!{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/bots/active-games shows only 'Bot' creators with WAITING status{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/bots/ongoing-games shows only 'Bot' creators with ACTIVE status and real opponents{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/games/available excludes all regular bot games{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/games/active-human-bots excludes all regular bot games{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOST REQUIREMENTS MET ({success_rate:.1f}% compliant){Colors.END}")
        print(f"{Colors.YELLOW}Большинство требований лобби выполнены, но есть минорные несоответствия.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL COMPLIANCE ({success_rate:.1f}% compliant){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые требования лобби выполнены, но требуется дополнительная работа.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: MAJOR NON-COMPLIANCE ({success_rate:.1f}% compliant){Colors.END}")
        print(f"{Colors.RED}Большинство требований лобби НЕ выполнены. Требуется срочное исправление.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    if active_games_test and not active_games_test["success"]:
        print(f"   🔴 Fix /api/bots/active-games: ensure creator_username='Bot', status='WAITING', is_regular_bot=true")
    if ongoing_games_test and not ongoing_games_test["success"]:
        print(f"   🔴 Fix /api/bots/ongoing-games: ensure creator_username='Bot', status='ACTIVE', real opponent usernames")
    if available_games_test and not available_games_test["success"]:
        print(f"   🔴 Fix /api/games/available: exclude all regular bot games")
    if human_bots_test and not human_bots_test["success"]:
        print(f"   🔴 Fix /api/games/active-human-bots: exclude all regular bot games and ACTIVE regular bot games")
    
    if success_rate == 100:
        print(f"   🟢 All lobby requirements are compliant - system ready for production")
        print(f"   ✅ Main agent can summarize and finish")
    else:
        print(f"   🔧 Fix remaining lobby compliance issues before considering system complete")

def main():
    """Main test execution for Russian Review Lobby Requirements"""
    print_header("RUSSIAN REVIEW LOBBY REQUIREMENTS TESTING")
    print(f"{Colors.BLUE}🎯 Testing новые правки лобби для соответствия требованиям{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: /api/bots/active-games requirements
        test_bots_active_games()
        
        # Test 2: /api/bots/ongoing-games requirements
        test_bots_ongoing_games()
        
        # Test 3a: /api/games/available requirements
        test_games_available()
        
        # Test 3b: /api/games/active-human-bots requirements
        test_games_active_human_bots()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_lobby_requirements_summary()

if __name__ == "__main__":
    main()