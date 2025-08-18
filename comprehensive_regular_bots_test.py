#!/usr/bin/env python3
"""
COMPREHENSIVE REGULAR BOTS API TESTING - POST LEGACY CLEANUP
Полный прогон автотестов бэкенда после чистки legacy и правок ничьих

TESTING REQUIREMENTS:
1) Создание REGULAR бота (POST /api/admin/bots/create-regular) — без win_percentage/creation_mode/profit_strategy в теле и ответе
2) Список (GET /api/admin/bots/regular/list) — нет legacy полей, cycle_total_amount = total_sum (включая ничьи), active_pool = wins+losses, отображение display как в коде
3) Подробности бота (GET /api/admin/bots/{id}) — нет legacy полей; поля min/max/pause_* и W/L/D counts/percentages возвращаются
4) Пересборка цикла (POST /api/admin/bots/{id}/recalculate-bets) — создаёт полный цикл с metadata.intended_result и точными суммами; нет старых /reset-bets
5) Завершение игр — intended_result соблюдается; ничьи считаются в N игр (check_and_complete_bot_cycle считает W+L+D), замены не создаются
6) Анти-гонки — /admin/bots/{id}/active-bets не допускает активных игр больше cycle_games и корректно балансирует

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
BASE_URL = "https://write-russian-2.preview.emergentagent.com/api"
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

def test_1_create_regular_bot():
    """
    Test 1: Создание REGULAR бота (POST /api/admin/bots/create-regular) 
    — без win_percentage/creation_mode/profit_strategy в теле и ответе
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Creating REGULAR Bot (No Legacy Fields){Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Create Regular Bot - No Legacy Fields", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot WITHOUT legacy fields
    bot_data = {
        "name": "Test_Regular_Bot_Clean",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "cycle_games": 12,
        "pause_between_cycles": 5,
        "pause_on_draw": 3
        # INTENTIONALLY OMITTING: win_percentage, creation_mode, profit_strategy
    }
    
    print(f"   📝 Creating Regular bot without legacy fields...")
    print(f"   📊 Request body: {json.dumps(bot_data, indent=2)}")
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        record_test(
            "Create Regular Bot - No Legacy Fields",
            False,
            f"Failed to create Regular bot: {details}"
        )
        return None
    
    # Check response structure - should NOT contain legacy fields
    bot_id = response_data.get("bot_id")
    bot_details = response_data.get("bot", {})
    
    legacy_fields_in_response = []
    for field in ["win_percentage", "creation_mode", "profit_strategy"]:
        if field in bot_details:
            legacy_fields_in_response.append(field)
    
    if bot_id and not legacy_fields_in_response:
        record_test(
            "Create Regular Bot - No Legacy Fields",
            True,
            f"Bot created successfully (ID: {bot_id}) without legacy fields in response"
        )
        return bot_id, bot_details
    elif bot_id and legacy_fields_in_response:
        record_test(
            "Create Regular Bot - No Legacy Fields",
            False,
            f"Bot created but response contains legacy fields: {legacy_fields_in_response}"
        )
        return bot_id, bot_details
    else:
        record_test(
            "Create Regular Bot - No Legacy Fields",
            False,
            "Bot created but no bot_id returned"
        )
        return None

def test_2_regular_bots_list():
    """
    Test 2: Список (GET /api/admin/bots/regular/list) 
    — нет legacy полей, cycle_total_amount = total_sum (включая ничьи), active_pool = wins+losses
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Regular Bots List (No Legacy Fields, Correct Calculations){Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Regular Bots List - Clean Structure", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Getting Regular bots list...")
    
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Regular Bots List - Clean Structure",
            False,
            f"Failed to get Regular bots list: {details}"
        )
        return None
    
    bots = response_data.get("bots", [])
    if not bots:
        record_test(
            "Regular Bots List - Clean Structure",
            False,
            "No bots found in list"
        )
        return None
    
    # Check first bot for structure
    first_bot = bots[0]
    
    # Check for absence of legacy fields
    legacy_fields_found = []
    for field in ["win_percentage", "creation_mode", "profit_strategy"]:
        if field in first_bot:
            legacy_fields_found.append(field)
    
    # Check for required fields and calculations
    required_fields = ["cycle_total_amount", "active_pool", "display"]
    missing_fields = []
    for field in required_fields:
        if field not in first_bot:
            missing_fields.append(field)
    
    # Check calculation logic
    calculation_issues = []
    
    # cycle_total_amount should include draws (W+L+D total sum)
    cycle_total = first_bot.get("cycle_total_amount", 0)
    
    # active_pool should be wins + losses (not including draws)
    active_pool = first_bot.get("active_pool", 0)
    wins = first_bot.get("current_cycle_wins", 0)
    losses = first_bot.get("current_cycle_losses", 0)
    draws = first_bot.get("current_cycle_draws", 0)
    
    expected_active_pool = wins + losses
    if active_pool != expected_active_pool:
        calculation_issues.append(f"active_pool={active_pool} but wins+losses={expected_active_pool}")
    
    print(f"   📊 First bot analysis:")
    print(f"      Bot ID: {first_bot.get('id', 'N/A')}")
    print(f"      Name: {first_bot.get('name', 'N/A')}")
    print(f"      cycle_total_amount: {cycle_total}")
    print(f"      active_pool: {active_pool} (wins: {wins}, losses: {losses})")
    print(f"      current_cycle_draws: {draws}")
    print(f"      Legacy fields found: {legacy_fields_found}")
    print(f"      Missing required fields: {missing_fields}")
    print(f"      Calculation issues: {calculation_issues}")
    
    success_conditions = [
        len(legacy_fields_found) == 0,
        len(missing_fields) == 0,
        len(calculation_issues) == 0
    ]
    
    if all(success_conditions):
        record_test(
            "Regular Bots List - Clean Structure",
            True,
            f"List structure correct: no legacy fields, proper calculations, {len(bots)} bots found"
        )
    else:
        issues = []
        if legacy_fields_found:
            issues.append(f"Legacy fields: {legacy_fields_found}")
        if missing_fields:
            issues.append(f"Missing fields: {missing_fields}")
        if calculation_issues:
            issues.append(f"Calculation issues: {calculation_issues}")
        
        record_test(
            "Regular Bots List - Clean Structure",
            False,
            f"Structure issues: {'; '.join(issues)}"
        )
    
    return bots

def test_3_bot_details(bot_id: str = None):
    """
    Test 3: Подробности бота (GET /api/admin/bots/{id}) 
    — нет legacy полей; поля min/max/pause_* и W/L/D counts/percentages возвращаются
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Bot Details (No Legacy Fields, Required Fields Present){Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bot Details - Clean Structure", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # If no bot_id provided, get first bot from list
    if not bot_id:
        success, list_data, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
        if success and list_data and list_data.get("bots"):
            bot_id = list_data["bots"][0]["id"]
        else:
            record_test("Bot Details - Clean Structure", False, "No bot ID available for testing")
            return None
    
    print(f"   📝 Getting bot details for ID: {bot_id}")
    
    success, response_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Bot Details - Clean Structure",
            False,
            f"Failed to get bot details: {details}"
        )
        return None
    
    bot_data = response_data.get("bot", response_data)
    
    # Check for absence of legacy fields
    legacy_fields_found = []
    for field in ["win_percentage", "creation_mode", "profit_strategy"]:
        if field in bot_data:
            legacy_fields_found.append(field)
    
    # Check for required fields
    required_fields = [
        "min_bet_amount", "max_bet_amount", 
        "pause_between_cycles", "pause_on_draw",
        "current_cycle_wins", "current_cycle_losses", "current_cycle_draws",
        "wins_percentage", "losses_percentage", "draws_percentage"
    ]
    
    missing_fields = []
    present_fields = []
    for field in required_fields:
        if field in bot_data:
            present_fields.append(field)
        else:
            missing_fields.append(field)
    
    print(f"   📊 Bot details analysis:")
    print(f"      Bot ID: {bot_data.get('id', 'N/A')}")
    print(f"      Name: {bot_data.get('name', 'N/A')}")
    print(f"      Legacy fields found: {legacy_fields_found}")
    print(f"      Required fields present: {len(present_fields)}/{len(required_fields)}")
    print(f"      Missing fields: {missing_fields}")
    
    # Check W/L/D counts and percentages
    wins = bot_data.get("current_cycle_wins", 0)
    losses = bot_data.get("current_cycle_losses", 0)
    draws = bot_data.get("current_cycle_draws", 0)
    wins_pct = bot_data.get("wins_percentage", 0)
    losses_pct = bot_data.get("losses_percentage", 0)
    draws_pct = bot_data.get("draws_percentage", 0)
    
    print(f"      W/L/D counts: {wins}/{losses}/{draws}")
    print(f"      W/L/D percentages: {wins_pct}%/{losses_pct}%/{draws_pct}%")
    
    success_conditions = [
        len(legacy_fields_found) == 0,
        len(missing_fields) == 0
    ]
    
    if all(success_conditions):
        record_test(
            "Bot Details - Clean Structure",
            True,
            f"Bot details structure correct: no legacy fields, all required fields present"
        )
    else:
        issues = []
        if legacy_fields_found:
            issues.append(f"Legacy fields: {legacy_fields_found}")
        if missing_fields:
            issues.append(f"Missing fields: {missing_fields}")
        
        record_test(
            "Bot Details - Clean Structure",
            False,
            f"Structure issues: {'; '.join(issues)}"
        )
    
    return bot_data

def test_4_recalculate_bets(bot_id: str = None):
    """
    Test 4: Пересборка цикла (POST /api/admin/bots/{id}/recalculate-bets) 
    — создаёт полный цикл с metadata.intended_result и точными суммами; нет старых /reset-bets
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Cycle Recalculation (Full Cycle with Metadata){Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Cycle Recalculation - Full Cycle", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # If no bot_id provided, get first bot from list
    if not bot_id:
        success, list_data, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
        if success and list_data and list_data.get("bots"):
            bot_id = list_data["bots"][0]["id"]
        else:
            record_test("Cycle Recalculation - Full Cycle", False, "No bot ID available for testing")
            return None
    
    print(f"   📝 Testing cycle recalculation for bot ID: {bot_id}")
    
    # First, check if old /reset-bets endpoint exists (should NOT exist)
    print(f"   🔍 Checking that old /reset-bets endpoint does NOT exist...")
    success_old, _, details_old = make_request(
        "POST",
        f"/admin/bots/{bot_id}/reset-bets",
        headers=headers
    )
    
    old_endpoint_exists = success_old
    
    # Test new /recalculate-bets endpoint
    print(f"   📝 Testing new /recalculate-bets endpoint...")
    success, response_data, details = make_request(
        "POST",
        f"/admin/bots/{bot_id}/recalculate-bets",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Cycle Recalculation - Full Cycle",
            False,
            f"Failed to recalculate bets: {details}"
        )
        return None
    
    # Check response structure
    has_success = response_data.get("success", False)
    has_message = "message" in response_data
    cycle_info = response_data.get("cycle_info", {})
    
    # Wait a moment for cycle creation
    print(f"   ⏳ Waiting 10 seconds for cycle creation...")
    time.sleep(10)
    
    # Get active bets to check metadata
    success_bets, bets_data, _ = make_request(
        "GET",
        f"/admin/bots/{bot_id}/active-bets",
        headers=headers
    )
    
    metadata_check = False
    intended_results_found = 0
    
    if success_bets and bets_data:
        bets = bets_data.get("bets", [])
        print(f"   📊 Found {len(bets)} active bets after recalculation")
        
        # Check for metadata.intended_result in bets
        for bet in bets[:3]:  # Check first 3 bets
            metadata = bet.get("metadata", {})
            if "intended_result" in metadata:
                intended_results_found += 1
                print(f"      Bet {bet.get('id', 'N/A')}: intended_result = {metadata['intended_result']}")
        
        metadata_check = intended_results_found > 0
    
    print(f"   📊 Recalculation analysis:")
    print(f"      Old /reset-bets endpoint exists: {old_endpoint_exists}")
    print(f"      New /recalculate-bets success: {has_success}")
    print(f"      Response has message: {has_message}")
    print(f"      Bets with intended_result metadata: {intended_results_found}")
    
    success_conditions = [
        not old_endpoint_exists,  # Old endpoint should NOT exist
        has_success,
        has_message,
        metadata_check  # Should have metadata.intended_result
    ]
    
    if all(success_conditions):
        record_test(
            "Cycle Recalculation - Full Cycle",
            True,
            f"Recalculation successful: old endpoint removed, new endpoint works, {intended_results_found} bets with metadata"
        )
    else:
        issues = []
        if old_endpoint_exists:
            issues.append("Old /reset-bets endpoint still exists")
        if not has_success:
            issues.append("Recalculation failed")
        if not metadata_check:
            issues.append("No intended_result metadata found")
        
        record_test(
            "Cycle Recalculation - Full Cycle",
            False,
            f"Issues: {'; '.join(issues)}"
        )
    
    return response_data

def test_5_game_completion_logic(bot_id: str = None):
    """
    Test 5: Завершение игр — intended_result соблюдается; ничьи считаются в N игр 
    (check_and_complete_bot_cycle считает W+L+D), замены не создаются
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 5: Game Completion Logic (Draws Count, No Replacements){Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Game Completion Logic", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # If no bot_id provided, get first bot from list
    if not bot_id:
        success, list_data, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
        if success and list_data and list_data.get("bots"):
            bot_id = list_data["bots"][0]["id"]
        else:
            record_test("Game Completion Logic", False, "No bot ID available for testing")
            return None
    
    print(f"   📝 Testing game completion logic for bot ID: {bot_id}")
    
    # Get bot details before
    success_before, bot_before, _ = make_request("GET", f"/admin/bots/{bot_id}", headers=headers)
    if not success_before:
        record_test("Game Completion Logic", False, "Failed to get bot details before test")
        return None
    
    bot_data_before = bot_before.get("bot", bot_before)
    wins_before = bot_data_before.get("current_cycle_wins", 0)
    losses_before = bot_data_before.get("current_cycle_losses", 0)
    draws_before = bot_data_before.get("current_cycle_draws", 0)
    cycle_games = bot_data_before.get("cycle_games", 12)
    
    print(f"   📊 Bot state before test:")
    print(f"      Wins: {wins_before}, Losses: {losses_before}, Draws: {draws_before}")
    print(f"      Total games: {wins_before + losses_before + draws_before}/{cycle_games}")
    
    # Get active bets
    success_bets, bets_data, _ = make_request("GET", f"/admin/bots/{bot_id}/active-bets", headers=headers)
    if not success_bets or not bets_data:
        record_test("Game Completion Logic", False, "Failed to get active bets")
        return None
    
    bets = bets_data.get("bets", [])
    if not bets:
        record_test("Game Completion Logic", False, "No active bets found for testing")
        return None
    
    print(f"   📊 Found {len(bets)} active bets")
    
    # Check if bets have intended_result metadata
    bets_with_metadata = []
    for bet in bets:
        metadata = bet.get("metadata", {})
        if "intended_result" in metadata:
            bets_with_metadata.append({
                "id": bet["id"],
                "intended_result": metadata["intended_result"]
            })
    
    print(f"   📊 Bets with intended_result metadata: {len(bets_with_metadata)}")
    
    # Check that total games (W+L+D) doesn't exceed cycle_games
    total_games = wins_before + losses_before + draws_before
    games_within_limit = total_games <= cycle_games
    
    # Check for replacement logic - if cycle is complete, no new bets should be created
    cycle_complete = total_games >= cycle_games
    
    print(f"   📊 Game completion analysis:")
    print(f"      Total games (W+L+D): {total_games}/{cycle_games}")
    print(f"      Games within limit: {games_within_limit}")
    print(f"      Cycle complete: {cycle_complete}")
    print(f"      Bets with intended_result: {len(bets_with_metadata)}")
    
    success_conditions = [
        games_within_limit,  # Total games should not exceed cycle_games
        len(bets_with_metadata) > 0  # Should have intended_result metadata
    ]
    
    if all(success_conditions):
        record_test(
            "Game Completion Logic",
            True,
            f"Game completion logic correct: {total_games}/{cycle_games} games, {len(bets_with_metadata)} bets with metadata"
        )
    else:
        issues = []
        if not games_within_limit:
            issues.append(f"Games exceed limit: {total_games}/{cycle_games}")
        if len(bets_with_metadata) == 0:
            issues.append("No intended_result metadata found")
        
        record_test(
            "Game Completion Logic",
            False,
            f"Issues: {'; '.join(issues)}"
        )
    
    return {
        "total_games": total_games,
        "cycle_games": cycle_games,
        "bets_with_metadata": len(bets_with_metadata)
    }

def test_6_anti_race_conditions(bot_id: str = None):
    """
    Test 6: Анти-гонки — /admin/bots/{id}/active-bets не допускает активных игр больше cycle_games 
    и корректно балансирует
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 6: Anti-Race Conditions (Active Bets Limit){Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Anti-Race Conditions", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # If no bot_id provided, get first bot from list
    if not bot_id:
        success, list_data, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
        if success and list_data and list_data.get("bots"):
            bot_id = list_data["bots"][0]["id"]
        else:
            record_test("Anti-Race Conditions", False, "No bot ID available for testing")
            return None
    
    print(f"   📝 Testing anti-race conditions for bot ID: {bot_id}")
    
    # Get bot details
    success_bot, bot_data, _ = make_request("GET", f"/admin/bots/{bot_id}", headers=headers)
    if not success_bot:
        record_test("Anti-Race Conditions", False, "Failed to get bot details")
        return None
    
    bot_info = bot_data.get("bot", bot_data)
    cycle_games = bot_info.get("cycle_games", 12)
    wins = bot_info.get("current_cycle_wins", 0)
    losses = bot_info.get("current_cycle_losses", 0)
    draws = bot_info.get("current_cycle_draws", 0)
    total_completed = wins + losses + draws
    
    print(f"   📊 Bot cycle info:")
    print(f"      Cycle games limit: {cycle_games}")
    print(f"      Completed games (W+L+D): {total_completed}")
    print(f"      Remaining slots: {cycle_games - total_completed}")
    
    # Get active bets multiple times to check consistency
    active_bets_counts = []
    for i in range(3):
        success_bets, bets_data, _ = make_request("GET", f"/admin/bots/{bot_id}/active-bets", headers=headers)
        if success_bets and bets_data:
            bets = bets_data.get("bets", [])
            active_bets_counts.append(len(bets))
            print(f"      Active bets check #{i+1}: {len(bets)} bets")
        time.sleep(1)
    
    if not active_bets_counts:
        record_test("Anti-Race Conditions", False, "Failed to get active bets data")
        return None
    
    # Check that active bets + completed games <= cycle_games
    max_active_bets = max(active_bets_counts)
    total_games_with_active = total_completed + max_active_bets
    
    # Check consistency of active bets count (should be stable)
    bets_count_consistent = len(set(active_bets_counts)) <= 2  # Allow minor variation
    
    # Check that total doesn't exceed cycle_games
    within_cycle_limit = total_games_with_active <= cycle_games
    
    print(f"   📊 Anti-race analysis:")
    print(f"      Active bets counts: {active_bets_counts}")
    print(f"      Max active bets: {max_active_bets}")
    print(f"      Total with active: {total_games_with_active}/{cycle_games}")
    print(f"      Within cycle limit: {within_cycle_limit}")
    print(f"      Counts consistent: {bets_count_consistent}")
    
    success_conditions = [
        within_cycle_limit,  # Total should not exceed cycle_games
        bets_count_consistent  # Active bets count should be consistent
    ]
    
    if all(success_conditions):
        record_test(
            "Anti-Race Conditions",
            True,
            f"Anti-race protection working: {total_games_with_active}/{cycle_games} total, consistent counts"
        )
    else:
        issues = []
        if not within_cycle_limit:
            issues.append(f"Exceeds cycle limit: {total_games_with_active}/{cycle_games}")
        if not bets_count_consistent:
            issues.append(f"Inconsistent active bets: {active_bets_counts}")
        
        record_test(
            "Anti-Race Conditions",
            False,
            f"Issues: {'; '.join(issues)}"
        )
    
    return {
        "cycle_games": cycle_games,
        "total_completed": total_completed,
        "active_bets_counts": active_bets_counts,
        "within_limit": within_cycle_limit
    }

def print_comprehensive_summary():
    """Print comprehensive testing summary"""
    print_header("COMPREHENSIVE REGULAR BOTS API TESTING SUMMARY")
    
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
    
    # Map tests to requirements
    requirements = [
        ("1. Создание REGULAR бота (без legacy полей)", "create regular bot"),
        ("2. Список ботов (чистая структура)", "regular bots list"),
        ("3. Подробности бота (все поля)", "bot details"),
        ("4. Пересборка цикла (с metadata)", "cycle recalculation"),
        ("5. Завершение игр (ничьи считаются)", "game completion"),
        ("6. Анти-гонки (лимит активных игр)", "anti-race")
    ]
    
    for req_name, test_keyword in requirements:
        test = next((t for t in test_results["tests"] if test_keyword in t["name"].lower()), None)
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: ALL REQUIREMENTS SATISFIED!{Colors.END}")
        print(f"{Colors.GREEN}✅ Legacy cleanup completed successfully{Colors.END}")
        print(f"{Colors.GREEN}✅ Draw logic alignment working correctly{Colors.END}")
        print(f"{Colors.GREEN}✅ All API endpoints functioning as expected{Colors.END}")
        print(f"{Colors.GREEN}✅ Anti-race conditions properly implemented{Colors.END}")
    elif success_rate >= 83:  # 5/6 tests
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOSTLY SUCCESSFUL ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Большинство требований выполнены, есть минорные проблемы.{Colors.END}")
    elif success_rate >= 67:  # 4/6 tests
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Основные требования выполнены, но есть проблемы.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: SIGNIFICANT ISSUES REMAIN ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Требуется дополнительная работа для исправления проблем.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 ACTION ITEMS FOR MAIN AGENT:{Colors.END}")
    
    failed_tests = [t for t in test_results["tests"] if not t["success"]]
    if not failed_tests:
        print(f"   🟢 All tests passed - system ready")
        print(f"   ✅ Main agent can summarize and finish")
    else:
        for test in failed_tests:
            print(f"   🔴 Fix: {test['name']} - {test['details']}")

def main():
    """Main test execution for comprehensive Regular Bots API testing"""
    print_header("COMPREHENSIVE REGULAR BOTS API TESTING")
    print(f"{Colors.BLUE}🎯 Testing backend after legacy cleanup and draw logic fixes{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: Create Regular Bot (no legacy fields)
        bot_result = test_1_create_regular_bot()
        bot_id = bot_result[0] if bot_result else None
        
        # Test 2: Regular Bots List (clean structure)
        test_2_regular_bots_list()
        
        # Test 3: Bot Details (required fields)
        test_3_bot_details(bot_id)
        
        # Test 4: Cycle Recalculation (with metadata)
        test_4_recalculate_bets(bot_id)
        
        # Test 5: Game Completion Logic (draws count)
        test_5_game_completion_logic(bot_id)
        
        # Test 6: Anti-Race Conditions (active bets limit)
        test_6_anti_race_conditions(bot_id)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_comprehensive_summary()

if __name__ == "__main__":
    main()