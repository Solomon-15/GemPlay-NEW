#!/usr/bin/env python3
"""
RUSSIAN REVIEW LOBBY TESTING - Four Critical Endpoints
Протестировать все четыре критических эндпоинта лобби по требованиям русского обзора

1. /api/games/available — НЕ должен возвращать игры обычных ботов (REGULAR). 
   Должен возвращать только живых игроков и Human-ботов. 
   Имя создателя НЕ должно быть "Unknown Player"; для Human-ботов возвращается их реальное имя.

2. /api/bots/active-games — возвращает только WAITING игры обычных ботов для блока "Available Bots", 
   имя бота теперь должно быть реальным (bot.name), гендер из avatar_gender.

3. /api/bots/ongoing-games — возвращает только ACTIVE игры обычных ботов для блока "Ongoing Bot Battles" 
   с реальными именами ботов и именами оппонентов (реальные пользователи), не "Unknown Player".

4. /api/games/active-human-bots — не должен включать обычных ботов и должен возвращать реальные имена 
   (не Unknown Player) для создателя/оппонента, если это игрок или Human-бот.

Использовать admin@gemplay.com / Admin123! для авторизации
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
BASE_URL = "https://ac189324-9922-4d54-b6a3-50cded9a8e9f.preview.emergentagent.com/api"
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

def test_games_available_endpoint():
    """Test 1: /api/games/available - НЕ должен возвращать игры обычных ботов (REGULAR)"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Testing /api/games/available endpoint{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Games Available Endpoint Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/games/available endpoint...")
    
    # Test games/available endpoint
    success, response_data, details = make_request(
        "GET",
        "/games/available",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Games Available Endpoint Test",
            False,
            f"Failed to get available games: {details}"
        )
        return
    
    # Analyze response structure
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} available games")
    
    # Check requirements
    regular_bot_games = 0
    unknown_player_names = 0
    human_bot_games = 0
    live_player_games = 0
    
    for game in games:
        creator_type = game.get("creator_type", "")
        creator_name = game.get("creator_name", "")
        bot_type = game.get("bot_type", "")
        
        # Count regular bot games (should be 0)
        if creator_type == "bot" and bot_type == "REGULAR":
            regular_bot_games += 1
        
        # Count "Unknown Player" names (should be 0)
        if creator_name == "Unknown Player":
            unknown_player_names += 1
        
        # Count Human-bot games
        if creator_type == "human_bot" or bot_type == "HUMAN":
            human_bot_games += 1
        
        # Count live player games
        if creator_type == "user":
            live_player_games += 1
    
    print(f"   📋 Analysis Results:")
    print(f"      Regular bot games: {regular_bot_games} (should be 0)")
    print(f"      'Unknown Player' names: {unknown_player_names} (should be 0)")
    print(f"      Human-bot games: {human_bot_games}")
    print(f"      Live player games: {live_player_games}")
    
    # Success criteria: no regular bot games and no "Unknown Player" names
    no_regular_bots = regular_bot_games == 0
    no_unknown_players = unknown_player_names == 0
    has_valid_games = human_bot_games > 0 or live_player_games > 0
    
    if no_regular_bots and no_unknown_players:
        record_test(
            "Games Available Endpoint Test",
            True,
            f"✅ REQUIREMENT 1 PASSED: No regular bot games ({regular_bot_games}), no 'Unknown Player' names ({unknown_player_names}), {human_bot_games} Human-bot + {live_player_games} live player games"
        )
    else:
        issues = []
        if not no_regular_bots:
            issues.append(f"Found {regular_bot_games} regular bot games")
        if not no_unknown_players:
            issues.append(f"Found {unknown_player_names} 'Unknown Player' names")
        
        record_test(
            "Games Available Endpoint Test",
            False,
            f"❌ REQUIREMENT 1 FAILED: {'; '.join(issues)}"
        )

def test_bots_active_games_endpoint():
    """Test 2: /api/bots/active-games - возвращает только WAITING игры обычных ботов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Testing /api/bots/active-games endpoint{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bots Active Games Endpoint Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/bots/active-games endpoint...")
    
    # Test bots/active-games endpoint
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Bots Active Games Endpoint Test",
            False,
            f"Failed to get bot active games: {details}"
        )
        return
    
    # Analyze response structure
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} bot active games")
    
    # Check requirements
    waiting_games = 0
    non_waiting_games = 0
    regular_bot_games = 0
    non_regular_bot_games = 0
    real_bot_names = 0
    missing_bot_names = 0
    has_avatar_gender = 0
    missing_avatar_gender = 0
    
    for game in games:
        status = game.get("status", "")
        bot_type = game.get("bot_type", "")
        creator_type = game.get("creator_type", "")
        bot_name = game.get("bot_name", "") or game.get("creator_name", "")
        avatar_gender = game.get("avatar_gender", "") or game.get("gender", "")
        
        # Count WAITING vs non-WAITING games
        if status == "WAITING":
            waiting_games += 1
        else:
            non_waiting_games += 1
        
        # Count REGULAR vs non-REGULAR bot games
        if bot_type == "REGULAR" or creator_type == "bot":
            regular_bot_games += 1
        else:
            non_regular_bot_games += 1
        
        # Check for real bot names (look in creator_username and creator.username)
        creator_username = game.get("creator_username", "")
        creator_obj = game.get("creator", {})
        creator_name_from_obj = creator_obj.get("username", "") if creator_obj else ""
        
        actual_bot_name = creator_username or creator_name_from_obj or bot_name
        
        if actual_bot_name and actual_bot_name != "Unknown Player" and actual_bot_name.strip():
            real_bot_names += 1
        else:
            missing_bot_names += 1
        
        # Check for avatar_gender (look in creator.gender)
        creator_gender = creator_obj.get("gender", "") if creator_obj else ""
        actual_gender = creator_gender or avatar_gender
        
        if actual_gender and actual_gender.strip():
            has_avatar_gender += 1
        else:
            missing_avatar_gender += 1
    
    print(f"   📋 Analysis Results:")
    print(f"      WAITING games: {waiting_games} (should be all)")
    print(f"      Non-WAITING games: {non_waiting_games} (should be 0)")
    print(f"      Regular bot games: {regular_bot_games} (should be all)")
    print(f"      Non-regular bot games: {non_regular_bot_games} (should be 0)")
    print(f"      Real bot names: {real_bot_names}")
    print(f"      Missing/invalid bot names: {missing_bot_names} (should be 0)")
    print(f"      Has avatar_gender: {has_avatar_gender}")
    print(f"      Missing avatar_gender: {missing_avatar_gender} (should be 0)")
    
    # Success criteria: only WAITING games of REGULAR bots with real names and gender
    only_waiting = non_waiting_games == 0
    only_regular_bots = non_regular_bot_games == 0
    all_have_real_names = missing_bot_names == 0
    all_have_gender = missing_avatar_gender == 0
    
    if only_waiting and only_regular_bots and all_have_real_names and all_have_gender:
        record_test(
            "Bots Active Games Endpoint Test",
            True,
            f"✅ REQUIREMENT 2 PASSED: {waiting_games} WAITING regular bot games, all with real names and gender"
        )
    else:
        issues = []
        if not only_waiting:
            issues.append(f"{non_waiting_games} non-WAITING games")
        if not only_regular_bots:
            issues.append(f"{non_regular_bot_games} non-regular bot games")
        if not all_have_real_names:
            issues.append(f"{missing_bot_names} games with missing/invalid bot names")
        if not all_have_gender:
            issues.append(f"{missing_avatar_gender} games with missing avatar_gender")
        
        record_test(
            "Bots Active Games Endpoint Test",
            False,
            f"❌ REQUIREMENT 2 FAILED: {'; '.join(issues)}"
        )

def test_bots_ongoing_games_endpoint():
    """Test 3: /api/bots/ongoing-games - возвращает только ACTIVE игры обычных ботов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Testing /api/bots/ongoing-games endpoint{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bots Ongoing Games Endpoint Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/bots/ongoing-games endpoint...")
    
    # Test bots/ongoing-games endpoint
    success, response_data, details = make_request(
        "GET",
        "/bots/ongoing-games",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Bots Ongoing Games Endpoint Test",
            False,
            f"Failed to get bot ongoing games: {details}"
        )
        return
    
    # Analyze response structure
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} bot ongoing games")
    
    # Check requirements
    active_games = 0
    non_active_games = 0
    regular_bot_games = 0
    non_regular_bot_games = 0
    real_bot_names = 0
    missing_bot_names = 0
    real_opponent_names = 0
    unknown_opponent_names = 0
    
    for game in games:
        status = game.get("status", "")
        bot_type = game.get("bot_type", "")
        creator_type = game.get("creator_type", "")
        bot_name = game.get("bot_name", "") or game.get("creator_name", "")
        opponent_name = game.get("opponent_name", "")
        
        # Count ACTIVE vs non-ACTIVE games
        if status == "ACTIVE":
            active_games += 1
        else:
            non_active_games += 1
        
        # Count REGULAR vs non-REGULAR bot games
        if bot_type == "REGULAR" or creator_type == "bot":
            regular_bot_games += 1
        else:
            non_regular_bot_games += 1
        
        # Check for real bot names (not empty, not "Unknown Player")
        if bot_name and bot_name != "Unknown Player" and bot_name.strip():
            real_bot_names += 1
        else:
            missing_bot_names += 1
        
        # Check for real opponent names (not "Unknown Player")
        if opponent_name and opponent_name != "Unknown Player" and opponent_name.strip():
            real_opponent_names += 1
        else:
            unknown_opponent_names += 1
    
    print(f"   📋 Analysis Results:")
    print(f"      ACTIVE games: {active_games} (should be all)")
    print(f"      Non-ACTIVE games: {non_active_games} (should be 0)")
    print(f"      Regular bot games: {regular_bot_games} (should be all)")
    print(f"      Non-regular bot games: {non_regular_bot_games} (should be 0)")
    print(f"      Real bot names: {real_bot_names}")
    print(f"      Missing/invalid bot names: {missing_bot_names} (should be 0)")
    print(f"      Real opponent names: {real_opponent_names}")
    print(f"      'Unknown Player' opponent names: {unknown_opponent_names} (should be 0)")
    
    # Success criteria: only ACTIVE games of REGULAR bots with real names for both bot and opponent
    only_active = non_active_games == 0
    only_regular_bots = non_regular_bot_games == 0
    all_have_real_bot_names = missing_bot_names == 0
    all_have_real_opponent_names = unknown_opponent_names == 0
    
    if only_active and only_regular_bots and all_have_real_bot_names and all_have_real_opponent_names:
        record_test(
            "Bots Ongoing Games Endpoint Test",
            True,
            f"✅ REQUIREMENT 3 PASSED: {active_games} ACTIVE regular bot games, all with real bot and opponent names"
        )
    else:
        issues = []
        if not only_active:
            issues.append(f"{non_active_games} non-ACTIVE games")
        if not only_regular_bots:
            issues.append(f"{non_regular_bot_games} non-regular bot games")
        if not all_have_real_bot_names:
            issues.append(f"{missing_bot_names} games with missing/invalid bot names")
        if not all_have_real_opponent_names:
            issues.append(f"{unknown_opponent_names} games with 'Unknown Player' opponent names")
        
        record_test(
            "Bots Ongoing Games Endpoint Test",
            False,
            f"❌ REQUIREMENT 3 FAILED: {'; '.join(issues)}"
        )

def test_games_active_human_bots_endpoint():
    """Test 4: /api/games/active-human-bots - не должен включать обычных ботов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Testing /api/games/active-human-bots endpoint{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Games Active Human Bots Endpoint Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/games/active-human-bots endpoint...")
    
    # Test games/active-human-bots endpoint
    success, response_data, details = make_request(
        "GET",
        "/games/active-human-bots",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Games Active Human Bots Endpoint Test",
            False,
            f"Failed to get active human bot games: {details}"
        )
        return
    
    # Analyze response structure
    games = []
    if isinstance(response_data, list):
        games = response_data
    elif isinstance(response_data, dict) and "games" in response_data:
        games = response_data["games"]
    elif isinstance(response_data, dict) and "data" in response_data:
        games = response_data["data"]
    
    print(f"   📊 Found {len(games)} active human bot games")
    
    # Check requirements
    regular_bot_games = 0
    human_bot_games = 0
    live_player_games = 0
    unknown_creator_names = 0
    unknown_opponent_names = 0
    real_creator_names = 0
    real_opponent_names = 0
    
    for game in games:
        creator_type = game.get("creator_type", "")
        opponent_type = game.get("opponent_type", "")
        bot_type = game.get("bot_type", "")
        creator_name = game.get("creator_name", "")
        opponent_name = game.get("opponent_name", "")
        
        # Count regular bot games (should be 0)
        if creator_type == "bot" and bot_type == "REGULAR":
            regular_bot_games += 1
        if opponent_type == "bot" and bot_type == "REGULAR":
            regular_bot_games += 1
        
        # Count Human-bot games
        if creator_type == "human_bot" or bot_type == "HUMAN":
            human_bot_games += 1
        
        # Count live player games
        if creator_type == "user" or opponent_type == "user":
            live_player_games += 1
        
        # Check creator names
        if creator_name == "Unknown Player":
            unknown_creator_names += 1
        elif creator_name and creator_name.strip():
            real_creator_names += 1
        
        # Check opponent names
        if opponent_name == "Unknown Player":
            unknown_opponent_names += 1
        elif opponent_name and opponent_name.strip():
            real_opponent_names += 1
    
    print(f"   📋 Analysis Results:")
    print(f"      Regular bot games: {regular_bot_games} (should be 0)")
    print(f"      Human-bot games: {human_bot_games}")
    print(f"      Live player games: {live_player_games}")
    print(f"      'Unknown Player' creator names: {unknown_creator_names} (should be 0)")
    print(f"      'Unknown Player' opponent names: {unknown_opponent_names} (should be 0)")
    print(f"      Real creator names: {real_creator_names}")
    print(f"      Real opponent names: {real_opponent_names}")
    
    # Success criteria: no regular bots and no "Unknown Player" names
    no_regular_bots = regular_bot_games == 0
    no_unknown_creators = unknown_creator_names == 0
    no_unknown_opponents = unknown_opponent_names == 0
    has_valid_games = human_bot_games > 0 or live_player_games > 0
    
    if no_regular_bots and no_unknown_creators and no_unknown_opponents:
        record_test(
            "Games Active Human Bots Endpoint Test",
            True,
            f"✅ REQUIREMENT 4 PASSED: No regular bot games ({regular_bot_games}), no 'Unknown Player' names (creators: {unknown_creator_names}, opponents: {unknown_opponent_names}), {human_bot_games} Human-bot + {live_player_games} live player games"
        )
    else:
        issues = []
        if not no_regular_bots:
            issues.append(f"Found {regular_bot_games} regular bot games")
        if not no_unknown_creators:
            issues.append(f"Found {unknown_creator_names} 'Unknown Player' creator names")
        if not no_unknown_opponents:
            issues.append(f"Found {unknown_opponent_names} 'Unknown Player' opponent names")
        
        record_test(
            "Games Active Human Bots Endpoint Test",
            False,
            f"❌ REQUIREMENT 4 FAILED: {'; '.join(issues)}"
        )

def print_russian_lobby_summary():
    """Print Russian Lobby testing specific summary"""
    print_header("RUSSIAN REVIEW LOBBY TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 RUSSIAN LOBBY REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each requirement
    req1_test = next((test for test in test_results["tests"] if "games available" in test["name"].lower()), None)
    req2_test = next((test for test in test_results["tests"] if "bots active games" in test["name"].lower()), None)
    req3_test = next((test for test in test_results["tests"] if "bots ongoing games" in test["name"].lower()), None)
    req4_test = next((test for test in test_results["tests"] if "games active human bots" in test["name"].lower()), None)
    
    requirements = [
        ("1. /api/games/available (No REGULAR bots, real names)", req1_test),
        ("2. /api/bots/active-games (WAITING REGULAR bots, real names)", req2_test),
        ("3. /api/bots/ongoing-games (ACTIVE REGULAR bots, real names)", req3_test),
        ("4. /api/games/active-human-bots (No REGULAR bots, real names)", req4_test)
    ]
    
    for req_name, test in requirements:
        if test:
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: ALL LOBBY REQUIREMENTS ARE WORKING!{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/games/available excludes REGULAR bots and shows real names{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/bots/active-games shows only WAITING REGULAR bots with real names{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/bots/ongoing-games shows only ACTIVE REGULAR bots with real names{Colors.END}")
        print(f"{Colors.GREEN}✅ /api/games/active-human-bots excludes REGULAR bots and shows real names{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOST LOBBY REQUIREMENTS WORKING ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Большинство требований лобби выполнены, но есть минорные проблемы.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые требования лобби выполнены, но требуется дополнительная работа.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: CRITICAL LOBBY ISSUES REMAIN ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Большинство требований лобби НЕ выполнены. Требуется срочное исправление.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    if req1_test and not req1_test["success"]:
        print(f"   🔴 /api/games/available needs fixing - still showing REGULAR bots or 'Unknown Player' names")
    if req2_test and not req2_test["success"]:
        print(f"   🔴 /api/bots/active-games needs fixing - not showing only WAITING REGULAR bots with real names")
    if req3_test and not req3_test["success"]:
        print(f"   🔴 /api/bots/ongoing-games needs fixing - not showing only ACTIVE REGULAR bots with real names")
    if req4_test and not req4_test["success"]:
        print(f"   🔴 /api/games/active-human-bots needs fixing - still showing REGULAR bots or 'Unknown Player' names")
    
    if success_rate == 100:
        print(f"   🟢 All lobby requirements are met - system ready for production")
        print(f"   ✅ Main agent can summarize and finish")
    else:
        print(f"   🔧 Fix remaining lobby issues before considering system complete")

def main():
    """Main test execution for Russian Review Lobby Requirements"""
    print_header("RUSSIAN REVIEW LOBBY REQUIREMENTS TESTING")
    print(f"{Colors.BLUE}🎯 Testing четыре критических эндпоинта лобби по требованиям русского обзора{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: /api/games/available
        test_games_available_endpoint()
        
        # Test 2: /api/bots/active-games
        test_bots_active_games_endpoint()
        
        # Test 3: /api/bots/ongoing-games
        test_bots_ongoing_games_endpoint()
        
        # Test 4: /api/games/active-human-bots
        test_games_active_human_bots_endpoint()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_russian_lobby_summary()

if __name__ == "__main__":
    main()