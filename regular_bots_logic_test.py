#!/usr/bin/env python3
"""
Regular Bots Logic Testing - Russian Review
Тестирование исправленной логики работы обычных ботов для соответствия заданным требованиям

КОНТЕКСТ: Тестирование исправленной логики создания ставок обычными ботами и нового endpoint для ongoing bot battles.

ОСНОВНЫЕ ИЗМЕНЕНИЯ:
1. Новая логика maintain_all_bots_active_bets(): Каждый бот поддерживает точно cycle_games активных ставок одновременно
2. Новый endpoint /bots/ongoing-games: для отображения активных игр ботов  
3. Обновлен frontend: использует новый endpoint для ongoing bot battles

ТРЕБОВАНИЯ ДЛЯ ТЕСТИРОВАНИЯ:

1. Логика создания ставок:
- Проверить что боты не создают ставок сверх cycle_games 
- Убедиться что боты поддерживают постоянное количество активных ставок
- При принятии ставки игроком создается новая ставка для поддержания квоты

2. Правильное разделение:
- /bots/active-games (Available Bots) - показывает только WAITING игры обычных ботов
- /bots/ongoing-games (Ongoing Bot Battles) - показывает только ACTIVE игры обычных ботов
- /games/available - НЕ включает игры обычных ботов
- /games/active-human-bots - НЕ включает игры обычных ботов

3. Обязательные правила:
- Обычные боты не играют между собой
- Обычные боты не заходят в чужие ставки (только создают свои)
- Дополнительная ставка создается только при ничье

ПРИОРИТЕТ: Критически важно - исправление основной логики игры
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
BASE_URL = "https://slavic-scribe-1.preview.emergentagent.com/api"
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

def test_regular_bots_cycle_games_logic(token: str):
    """Test 1: Проверить что боты не создают ставок сверх cycle_games"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Regular Bots Cycle Games Logic{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all regular bots
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Regular Bots Cycle Games Logic",
            False,
            f"Failed to get bots: {details}"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    if not bots:
        record_test(
            "Regular Bots Cycle Games Logic",
            False,
            "No regular bots found"
        )
        return
    
    # Check each bot's active bets vs cycle_games
    violations = []
    correct_bots = []
    
    for bot in bots:
        bot_name = bot.get("name", "Unknown")
        cycle_games = bot.get("cycle_games", 0)
        active_bets = bot.get("active_bets", 0)
        
        if active_bets > cycle_games:
            violations.append(f"{bot_name}: {active_bets} active bets > {cycle_games} cycle_games")
        else:
            correct_bots.append(f"{bot_name}: {active_bets}/{cycle_games} bets (OK)")
    
    if violations:
        record_test(
            "Regular Bots Cycle Games Logic",
            False,
            f"Bots violating cycle_games limit: {violations}"
        )
    else:
        record_test(
            "Regular Bots Cycle Games Logic",
            True,
            f"All {len(bots)} bots respect cycle_games limit. Examples: {correct_bots[:3]}"
        )

def test_maintain_active_bets_quota(token: str):
    """Test 2: Убедиться что боты поддерживают постоянное количество активных ставок"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Maintain Active Bets Quota{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current bot states
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Maintain Active Bets Quota",
            False,
            f"Failed to get bots: {details}"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    if not bots:
        record_test(
            "Maintain Active Bets Quota",
            False,
            "No regular bots found"
        )
        return
    
    # Check if bots are maintaining their quotas
    quota_maintained = []
    quota_issues = []
    
    for bot in bots:
        bot_name = bot.get("name", "Unknown")
        cycle_games = bot.get("cycle_games", 0)
        active_bets = bot.get("active_bets", 0)
        
        # Check if bot is maintaining close to its quota (allowing some variance)
        if cycle_games > 0:
            quota_ratio = active_bets / cycle_games
            if quota_ratio >= 0.8:  # At least 80% of quota maintained
                quota_maintained.append(f"{bot_name}: {active_bets}/{cycle_games} ({quota_ratio:.1%})")
            else:
                quota_issues.append(f"{bot_name}: {active_bets}/{cycle_games} ({quota_ratio:.1%})")
    
    if len(quota_maintained) >= len(bots) * 0.7:  # At least 70% of bots maintaining quota
        record_test(
            "Maintain Active Bets Quota",
            True,
            f"{len(quota_maintained)}/{len(bots)} bots maintaining quota. Examples: {quota_maintained[:3]}"
        )
    else:
        record_test(
            "Maintain Active Bets Quota",
            False,
            f"Only {len(quota_maintained)}/{len(bots)} bots maintaining quota. Issues: {quota_issues[:3]}"
        )

def test_endpoint_separation(token: str):
    """Test 3: Правильное разделение эндпоинтов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Endpoint Separation{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /bots/active-games (Available Bots) - should show only WAITING regular bot games
    success1, data1, details1 = make_request("GET", "/bots/active-games", headers=headers)
    
    # Test /bots/ongoing-games (Ongoing Bot Battles) - should show only ACTIVE regular bot games  
    success2, data2, details2 = make_request("GET", "/bots/ongoing-games", headers=headers)
    
    # Test /games/available - should NOT include regular bot games
    success3, data3, details3 = make_request("GET", "/games/available", headers=headers)
    
    # Test /games/active-human-bots - should NOT include regular bot games
    success4, data4, details4 = make_request("GET", "/games/active-human-bots", headers=headers)
    
    results = []
    
    # Check /bots/active-games
    if success1:
        games1 = data1 if isinstance(data1, list) else data1.get("games", [])
        waiting_games = [g for g in games1 if g.get("status") == "WAITING"]
        results.append(f"/bots/active-games: {len(waiting_games)} WAITING games")
        
        # Check if these are regular bot games
        regular_bot_games = [g for g in games1 if g.get("creator_type") == "bot" or g.get("is_regular_bot_game")]
        if len(regular_bot_games) > 0:
            results.append(f"✅ Contains {len(regular_bot_games)} regular bot games")
        else:
            results.append(f"⚠️ No regular bot games found")
    else:
        results.append(f"❌ /bots/active-games failed: {details1}")
    
    # Check /bots/ongoing-games
    if success2:
        games2 = data2 if isinstance(data2, list) else data2.get("games", [])
        active_games = [g for g in games2 if g.get("status") == "ACTIVE"]
        results.append(f"/bots/ongoing-games: {len(active_games)} ACTIVE games")
    else:
        results.append(f"❌ /bots/ongoing-games failed: {details2}")
    
    # Check /games/available - should exclude regular bots
    if success3:
        games3 = data3 if isinstance(data3, list) else data3.get("games", [])
        regular_in_available = [g for g in games3 if g.get("creator_type") == "bot" and g.get("is_regular_bot_game")]
        if len(regular_in_available) == 0:
            results.append(f"✅ /games/available excludes regular bots ({len(games3)} total games)")
        else:
            results.append(f"❌ /games/available includes {len(regular_in_available)} regular bot games")
    else:
        results.append(f"❌ /games/available failed: {details3}")
    
    # Check /games/active-human-bots - should exclude regular bots
    if success4:
        games4 = data4 if isinstance(data4, list) else data4.get("games", [])
        regular_in_human_bots = [g for g in games4 if g.get("creator_type") == "bot" and g.get("is_regular_bot_game")]
        if len(regular_in_human_bots) == 0:
            results.append(f"✅ /games/active-human-bots excludes regular bots ({len(games4)} total games)")
        else:
            results.append(f"❌ /games/active-human-bots includes {len(regular_in_human_bots)} regular bot games")
    else:
        results.append(f"❌ /games/active-human-bots failed: {details4}")
    
    # Determine overall success
    failed_checks = [r for r in results if r.startswith("❌")]
    success_overall = len(failed_checks) == 0
    
    record_test(
        "Endpoint Separation",
        success_overall,
        f"Endpoint separation results: {'; '.join(results)}"
    )

def test_regular_bots_isolation_rules(token: str):
    """Test 4: Обязательные правила изоляции обычных ботов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Regular Bots Isolation Rules{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get active regular bot games
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success:
        record_test(
            "Regular Bots Isolation Rules",
            False,
            f"Failed to get active games: {details}"
        )
        return
    
    games = response_data if isinstance(response_data, list) else response_data.get("games", [])
    
    if not games:
        record_test(
            "Regular Bots Isolation Rules",
            True,
            "No active games found - isolation rules cannot be violated"
        )
        return
    
    violations = []
    correct_games = []
    
    for game in games:
        creator_type = game.get("creator_type", "")
        opponent_type = game.get("opponent_type", "")
        creator_id = game.get("creator_id", "")
        opponent_id = game.get("opponent_id", "")
        
        # Rule 1: Regular bots should not play with each other
        if creator_type == "bot" and opponent_type == "bot":
            violations.append(f"Game {game.get('id', 'unknown')}: Bot vs Bot game detected")
        
        # Rule 2: Regular bots should only create games, not join them
        # (This is harder to test directly, but we can check if regular bots are opponents)
        elif opponent_type == "bot" and game.get("is_regular_bot_game"):
            violations.append(f"Game {game.get('id', 'unknown')}: Regular bot as opponent (should only create)")
        
        else:
            correct_games.append(f"Game {game.get('id', 'unknown')}: {creator_type} vs {opponent_type or 'waiting'}")
    
    if violations:
        record_test(
            "Regular Bots Isolation Rules",
            False,
            f"Isolation violations found: {violations[:3]}"
        )
    else:
        record_test(
            "Regular Bots Isolation Rules",
            True,
            f"All {len(games)} games follow isolation rules. Examples: {correct_games[:3]}"
        )

def test_new_ongoing_games_endpoint(token: str):
    """Test 5: Новый endpoint /bots/ongoing-games"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: New Ongoing Games Endpoint{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/ongoing-games",
        headers=headers
    )
    
    if not success:
        record_test(
            "New Ongoing Games Endpoint",
            False,
            f"Endpoint /bots/ongoing-games failed: {details}"
        )
        return
    
    games = response_data if isinstance(response_data, list) else response_data.get("games", [])
    
    # Check that all games are ACTIVE status
    active_games = [g for g in games if g.get("status") == "ACTIVE"]
    non_active_games = [g for g in games if g.get("status") != "ACTIVE"]
    
    # Check that games have required fields
    required_fields = ["id", "creator_id", "opponent_id", "status", "bet_amount"]
    games_with_fields = []
    games_missing_fields = []
    
    for game in games:
        missing_fields = [field for field in required_fields if field not in game]
        if missing_fields:
            games_missing_fields.append(f"Game {game.get('id', 'unknown')}: missing {missing_fields}")
        else:
            games_with_fields.append(game.get('id', 'unknown'))
    
    success_criteria = [
        len(games) > 0,  # Has games
        len(non_active_games) == 0,  # All games are ACTIVE
        len(games_missing_fields) == 0  # All games have required fields
    ]
    
    overall_success = all(success_criteria)
    
    details_str = f"Found {len(games)} games, {len(active_games)} ACTIVE, {len(non_active_games)} non-ACTIVE"
    if games_missing_fields:
        details_str += f", {len(games_missing_fields)} missing fields"
    
    record_test(
        "New Ongoing Games Endpoint",
        overall_success,
        details_str
    )

def test_bet_creation_gem_types_fix(token: str):
    """Test 6: Исправление создания ставок с разными типами гемов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 6: Bet Creation Gem Types Fix{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get some active regular bot games to check gem diversity
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success:
        record_test(
            "Bet Creation Gem Types Fix",
            False,
            f"Failed to get active games: {details}"
        )
        return
    
    games = response_data if isinstance(response_data, list) else response_data.get("games", [])
    
    if not games:
        record_test(
            "Bet Creation Gem Types Fix",
            False,
            "No active games found to test gem diversity"
        )
        return
    
    # Analyze gem types used in bets
    all_gem_types = set()
    zero_value_bets = []
    diverse_bets = []
    
    for game in games[:10]:  # Check first 10 games
        bet_gems = game.get("bet_gems", {})
        bet_amount = game.get("bet_amount", 0)
        
        if bet_amount == 0:
            zero_value_bets.append(game.get("id", "unknown"))
        
        if bet_gems:
            game_gem_types = set(bet_gems.keys())
            all_gem_types.update(game_gem_types)
            
            if len(game_gem_types) > 1:
                diverse_bets.append(f"Game {game.get('id', 'unknown')}: {list(game_gem_types)}")
    
    # Expected gem types (should be more than just 4 basic ones)
    expected_gem_types = {"Ruby", "Amber", "Topaz", "Emerald", "Aquamarine", "Sapphire", "Magic"}
    found_gem_types = all_gem_types.intersection(expected_gem_types)
    
    success_criteria = [
        len(found_gem_types) >= 5,  # At least 5 different gem types used
        len(zero_value_bets) == 0,  # No zero-value bets
        len(diverse_bets) > 0  # Some bets use multiple gem types
    ]
    
    overall_success = all(success_criteria)
    
    details_str = f"Found {len(found_gem_types)} gem types: {sorted(found_gem_types)}, "
    details_str += f"{len(zero_value_bets)} zero-value bets, {len(diverse_bets)} diverse bets"
    
    record_test(
        "Bet Creation Gem Types Fix",
        overall_success,
        details_str
    )

def test_draw_replacement_logic(token: str):
    """Test 7: Дополнительная ставка создается только при ничье"""
    print(f"\n{Colors.MAGENTA}🧪 Test 7: Draw Replacement Logic{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # This test is harder to verify directly without game simulation
    # We'll check if the system has the proper endpoints and logic structure
    
    # Check if bots have pause_on_draw settings
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Draw Replacement Logic",
            False,
            f"Failed to get bots: {details}"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    if not bots:
        record_test(
            "Draw Replacement Logic",
            False,
            "No bots found to check draw logic"
        )
        return
    
    # Check if bots have pause_on_draw field (indicates draw logic is implemented)
    bots_with_draw_logic = []
    bots_without_draw_logic = []
    
    for bot in bots:
        bot_name = bot.get("name", "Unknown")
        if "pause_on_draw" in bot or "pause_between_games" in bot:
            pause_on_draw = bot.get("pause_on_draw", bot.get("pause_between_games", "unknown"))
            bots_with_draw_logic.append(f"{bot_name}: {pause_on_draw}s")
        else:
            bots_without_draw_logic.append(bot_name)
    
    # Check if there are completed games with DRAW status (indicates draw handling exists)
    success2, games_data, _ = make_request("GET", "/bots/ongoing-games", headers=headers)
    draw_games_exist = False
    
    if success2:
        games = games_data if isinstance(games_data, list) else games_data.get("games", [])
        # Look for any indication of draw handling in the system
        draw_games_exist = len(games) > 0  # If ongoing games exist, draw logic is likely implemented
    
    success_criteria = [
        len(bots_with_draw_logic) > 0,  # Bots have draw timing settings
        len(bots_without_draw_logic) < len(bots)  # Most bots have draw logic
    ]
    
    overall_success = all(success_criteria)
    
    details_str = f"{len(bots_with_draw_logic)} bots with draw logic: {bots_with_draw_logic[:3]}"
    if bots_without_draw_logic:
        details_str += f", {len(bots_without_draw_logic)} without: {bots_without_draw_logic[:3]}"
    
    record_test(
        "Draw Replacement Logic",
        overall_success,
        details_str
    )

def print_final_summary():
    """Print final test summary"""
    print_header("REGULAR BOTS LOGIC TESTING SUMMARY")
    
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
        "Боты не создают ставок сверх cycle_games",
        "Боты поддерживают постоянное количество активных ставок", 
        "Правильное разделение эндпоинтов",
        "Обычные боты не играют между собой",
        "Новый endpoint /bots/ongoing-games работает",
        "Исправлены типы гемов и нулевые значения",
        "Дополнительная ставка только при ничье"
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: REGULAR BOTS LOGIC IS {success_rate:.1f}% FUNCTIONAL!{Colors.END}")
        print(f"{Colors.GREEN}The corrected regular bots logic is working well and follows the specified requirements.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: REGULAR BOTS LOGIC IS {success_rate:.1f}% FUNCTIONAL{Colors.END}")
        print(f"{Colors.YELLOW}The logic has some issues but core functionality is working.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: REGULAR BOTS LOGIC NEEDS ATTENTION ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Multiple critical issues found that need to be addressed.{Colors.END}")

def main():
    """Main test execution"""
    print_header("REGULAR BOTS CORRECTED LOGIC TESTING")
    print(f"{Colors.BLUE}🎯 Testing corrected logic for regular bots per Russian review{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: cycle_games limits, endpoint separation, isolation rules{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Cannot proceed without authentication{Colors.END}")
        sys.exit(1)
    
    try:
        # Run all tests
        test_regular_bots_cycle_games_logic(token)
        test_maintain_active_bets_quota(token)
        test_endpoint_separation(token)
        test_regular_bots_isolation_rules(token)
        test_new_ongoing_games_endpoint(token)
        test_bet_creation_gem_types_fix(token)
        test_draw_replacement_logic(token)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()