#!/usr/bin/env python3
"""
EXACT CYCLE SUM MATCHING FIX TESTING - Russian Review
Тестирование исправленной логики точного совпадения суммы ставок цикла

ПРОБЛЕМА: Regular боты создают ставки с неточной суммой цикла.
Ожидается: min_bet_amount=1.0, max_bet_amount=50.0, cycle_games=12 → сумма = 306.0
Фактически: получаются суммы 227.0, 333.0, 315.0 вместо точных 306.0

ТЕСТИРОВАТЬ:
1. POST /api/admin/bots/create-regular - создать бота Direct_Fix_Test_Bot
2. Подождать 15 секунд для создания ставок
3. GET /api/bots/active-games - получить игры этого бота
4. Вычислить точную сумму всех bet_amount
5. Проверить что сумма == 306.0 (не 305, 281, 325, 227, 333, 315)
6. Показать детали: количество ставок, мин/макс/среднюю сумму
7. Проверить логи на наличие "🔧 Direct adjustment" и "✅ PERFECT MATCH!"

КРИТИЧЕСКИЙ ТЕСТ: Если сумма не равна точно 306.0, исправление все еще не работает.
ПРИОРИТЕТ: Критически важно - основная логика создания ставок ботов
ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ: Сумма всех ставок должна быть точно 306.0
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
BASE_URL = "https://modalni-dialogi.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test configuration for exact sum matching
TEST_BOT_CONFIG = {
    "min_bet_amount": 1.0,
    "max_bet_amount": 50.0,
    "cycle_games": 12,
    "win_percentage": 55
}

EXPECTED_CYCLE_SUM = 306.0  # (1+50)/2 * 12 = 25.5 * 12 = 306.0

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

def generate_unique_bot_name() -> str:
    """Generate unique bot name for testing"""
    timestamp = int(time.time())
    return f"Direct_Fix_Test_Bot_{timestamp}"

def test_create_regular_bot_for_exact_sum(token: str) -> Optional[str]:
    """Test 1: Create Regular bot with exact sum test configuration"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Creating Regular bot for exact sum testing{Colors.END}")
    
    if not token:
        record_test("Create Regular bot for exact sum", False, "No admin token available")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    bot_name = generate_unique_bot_name()
    
    bot_data = {
        "name": bot_name,
        "min_bet_amount": TEST_BOT_CONFIG["min_bet_amount"],
        "max_bet_amount": TEST_BOT_CONFIG["max_bet_amount"],
        "cycle_games": TEST_BOT_CONFIG["cycle_games"],
        "win_percentage": TEST_BOT_CONFIG["win_percentage"],
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if success and response_data:
        bot_id = response_data.get("bot_id")
        if bot_id:
            record_test(
                "Create Regular bot for exact sum",
                True,
                f"Successfully created bot '{bot_name}' with ID: {bot_id}, config: min={TEST_BOT_CONFIG['min_bet_amount']}, max={TEST_BOT_CONFIG['max_bet_amount']}, cycle={TEST_BOT_CONFIG['cycle_games']}"
            )
            return bot_id
        else:
            record_test(
                "Create Regular bot for exact sum",
                False,
                f"Bot created but no bot_id in response: {response_data}"
            )
    else:
        record_test(
            "Create Regular bot for exact sum",
            False,
            f"Failed to create bot: {details}"
        )
    
    return None

def test_wait_for_bet_creation(bot_id: str):
    """Test 2: Wait for bot to create initial cycle bets"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Waiting for bot to create initial cycle bets{Colors.END}")
    
    if not bot_id:
        record_test("Wait for bet creation", False, "No bot ID available")
        return
    
    print(f"{Colors.BLUE}⏳ Waiting 15 seconds for bot to create initial cycle bets...{Colors.END}")
    
    # Wait for bot automation to create bets
    for i in range(15):
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"{Colors.BLUE}   {15 - (i + 1)} seconds remaining...{Colors.END}")
    
    record_test(
        "Wait for bet creation",
        True,
        "Completed 15-second wait for bot automation to create initial cycle bets"
    )

def test_get_bot_active_games(token: str, bot_id: str) -> List[Dict]:
    """Test 3: Get active games for the created bot"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Getting active games for the bot{Colors.END}")
    
    if not token or not bot_id:
        record_test("Get bot active games", False, "Missing token or bot_id")
        return []
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        # Filter games for our specific bot
        all_games = response_data if isinstance(response_data, list) else []
        bot_games = [game for game in all_games if game.get("bot_id") == bot_id]
        
        if bot_games:
            record_test(
                "Get bot active games",
                True,
                f"Successfully retrieved {len(bot_games)} active games for bot {bot_id}"
            )
            return bot_games
        else:
            record_test(
                "Get bot active games",
                False,
                f"No active games found for bot {bot_id}. Total games in system: {len(all_games)}"
            )
    else:
        record_test(
            "Get bot active games",
            False,
            f"Failed to get active games: {details}"
        )
    
    return []

def test_calculate_exact_cycle_sum(bot_games: List[Dict]) -> float:
    """Test 4: Calculate exact sum of all bet amounts"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Calculating exact sum of all bet amounts{Colors.END}")
    
    if not bot_games:
        record_test("Calculate exact cycle sum", False, "No bot games available for calculation")
        return 0.0
    
    # Extract bet amounts
    bet_amounts = []
    for game in bot_games:
        bet_amount = game.get("bet_amount", 0)
        if bet_amount > 0:
            bet_amounts.append(bet_amount)
    
    if not bet_amounts:
        record_test("Calculate exact cycle sum", False, "No valid bet amounts found in games")
        return 0.0
    
    # Calculate statistics
    total_sum = sum(bet_amounts)
    min_bet = min(bet_amounts)
    max_bet = max(bet_amounts)
    avg_bet = total_sum / len(bet_amounts)
    
    # Check if sum matches expected
    sum_matches = abs(total_sum - EXPECTED_CYCLE_SUM) < 0.01  # Allow for small floating point differences
    
    details = f"Games: {len(bet_amounts)}, Sum: ${total_sum}, Min: ${min_bet}, Max: ${max_bet}, Avg: ${avg_bet:.2f}, Expected: ${EXPECTED_CYCLE_SUM}"
    
    record_test(
        "Calculate exact cycle sum",
        sum_matches,
        details
    )
    
    # Print detailed breakdown
    print(f"{Colors.CYAN}📊 DETAILED BET BREAKDOWN:{Colors.END}")
    print(f"   Total Games: {len(bet_amounts)}")
    print(f"   Expected Games: {TEST_BOT_CONFIG['cycle_games']}")
    print(f"   Bet Amounts: {sorted(bet_amounts)}")
    print(f"   Total Sum: ${total_sum}")
    print(f"   Expected Sum: ${EXPECTED_CYCLE_SUM}")
    print(f"   Difference: ${abs(total_sum - EXPECTED_CYCLE_SUM):.2f}")
    print(f"   Min Bet: ${min_bet} (Expected: ${TEST_BOT_CONFIG['min_bet_amount']})")
    print(f"   Max Bet: ${max_bet} (Expected: ${TEST_BOT_CONFIG['max_bet_amount']})")
    print(f"   Average Bet: ${avg_bet:.2f} (Expected: ${(TEST_BOT_CONFIG['min_bet_amount'] + TEST_BOT_CONFIG['max_bet_amount']) / 2})")
    
    return total_sum

def test_verify_exact_sum_match(actual_sum: float):
    """Test 5: Verify that sum matches exactly 306.0"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: Verifying exact sum match (306.0){Colors.END}")
    
    if actual_sum == 0.0:
        record_test("Verify exact sum match", False, "No actual sum available for verification")
        return
    
    # Check for exact match (allowing minimal floating point tolerance)
    exact_match = abs(actual_sum - EXPECTED_CYCLE_SUM) < 0.01
    difference = actual_sum - EXPECTED_CYCLE_SUM
    
    if exact_match:
        record_test(
            "Verify exact sum match",
            True,
            f"✅ PERFECT MATCH! Actual sum ${actual_sum} matches expected ${EXPECTED_CYCLE_SUM} (difference: ${difference:.2f})"
        )
    else:
        # Check if it's one of the known incorrect values
        known_incorrect_values = [305, 281, 325, 227, 333, 315]
        is_known_incorrect = any(abs(actual_sum - val) < 0.01 for val in known_incorrect_values)
        
        if is_known_incorrect:
            record_test(
                "Verify exact sum match",
                False,
                f"❌ KNOWN INCORRECT VALUE! Actual sum ${actual_sum} is one of the previously failing values. Expected: ${EXPECTED_CYCLE_SUM}, Difference: ${difference:.2f}"
            )
        else:
            record_test(
                "Verify exact sum match",
                False,
                f"❌ SUM MISMATCH! Actual sum ${actual_sum} does not match expected ${EXPECTED_CYCLE_SUM}. Difference: ${difference:.2f}"
            )

def test_check_cycle_games_count(bot_games: List[Dict]):
    """Test 6: Verify that number of games matches cycle_games setting"""
    print(f"\n{Colors.MAGENTA}🧪 Test 6: Verifying cycle games count{Colors.END}")
    
    actual_count = len(bot_games)
    expected_count = TEST_BOT_CONFIG["cycle_games"]
    
    count_matches = actual_count == expected_count
    
    record_test(
        "Verify cycle games count",
        count_matches,
        f"Actual games: {actual_count}, Expected: {expected_count}, Match: {count_matches}"
    )

def test_check_bet_range_compliance(bot_games: List[Dict]):
    """Test 7: Verify that all bets are within min/max range"""
    print(f"\n{Colors.MAGENTA}🧪 Test 7: Verifying bet range compliance{Colors.END}")
    
    if not bot_games:
        record_test("Verify bet range compliance", False, "No bot games available")
        return
    
    min_allowed = TEST_BOT_CONFIG["min_bet_amount"]
    max_allowed = TEST_BOT_CONFIG["max_bet_amount"]
    
    out_of_range_bets = []
    in_range_bets = []
    
    for game in bot_games:
        bet_amount = game.get("bet_amount", 0)
        if bet_amount < min_allowed or bet_amount > max_allowed:
            out_of_range_bets.append(bet_amount)
        else:
            in_range_bets.append(bet_amount)
    
    all_in_range = len(out_of_range_bets) == 0
    
    details = f"In range: {len(in_range_bets)}, Out of range: {len(out_of_range_bets)}"
    if out_of_range_bets:
        details += f", Out of range values: {out_of_range_bets}"
    
    record_test(
        "Verify bet range compliance",
        all_in_range,
        details
    )

def print_exact_sum_summary():
    """Print exact sum testing summary"""
    print_header("EXACT CYCLE SUM MATCHING FIX TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 EXACT SUM MATCHING REQUIREMENTS STATUS:{Colors.END}")
    
    requirements = [
        "Regular bot creation with test config",
        "Bot automation creates initial bets",
        "Active games retrieval",
        "Exact sum calculation",
        "Sum matches 306.0 exactly",
        "Cycle games count matches setting",
        "All bets within min/max range"
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
    
    # Critical conclusion for exact sum matching
    exact_sum_test = next((test for test in test_results["tests"] if "exact sum match" in test["name"].lower()), None)
    
    if exact_sum_test and exact_sum_test["success"]:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: EXACT CYCLE SUM MATCHING FIX IS WORKING!{Colors.END}")
        print(f"{Colors.GREEN}The fix successfully ensures that Regular bot cycle sums equal exactly 306.0 as expected.{Colors.END}")
    elif exact_sum_test and not exact_sum_test["success"]:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: EXACT CYCLE SUM MATCHING FIX IS NOT WORKING!{Colors.END}")
        print(f"{Colors.RED}The fix is still failing to produce the exact expected sum of 306.0.{Colors.END}")
        print(f"{Colors.RED}The normalize_amounts_to_exact_sum function needs further debugging.{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: EXACT SUM MATCHING COULD NOT BE TESTED{Colors.END}")
        print(f"{Colors.YELLOW}Unable to complete the critical exact sum verification test.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.END}")
    
    if success_rate < 100:
        print(f"   🔴 The exact cycle sum matching fix requires immediate attention")
        print(f"   🔍 Check backend logs for '🔧 Direct adjustment' and '✅ PERFECT MATCH!' messages")
        print(f"   🔍 Verify normalize_amounts_to_exact_sum function is being called correctly")
        print(f"   🔍 Ensure the function handles the total cycle sum, not just individual components")
    else:
        print(f"   🟢 Exact cycle sum matching is working correctly")
        print(f"   🎯 The fix successfully produces sums of exactly 306.0")

def main():
    """Main test execution for exact cycle sum matching"""
    print_header("EXACT CYCLE SUM MATCHING FIX TESTING")
    print(f"{Colors.BLUE}🎯 Testing exact sum matching for Regular bot cycles{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 Config: min={TEST_BOT_CONFIG['min_bet_amount']}, max={TEST_BOT_CONFIG['max_bet_amount']}, cycle={TEST_BOT_CONFIG['cycle_games']}{Colors.END}")
    print(f"{Colors.BLUE}🎯 Expected Sum: ${EXPECTED_CYCLE_SUM}{Colors.END}")
    
    # Store data for subsequent tests
    admin_token = None
    bot_id = None
    bot_games = []
    actual_sum = 0.0
    
    try:
        # Authenticate
        admin_token = authenticate_admin()
        if not admin_token:
            print(f"{Colors.RED}❌ Cannot proceed without admin authentication{Colors.END}")
            return
        
        # Run exact sum matching tests
        bot_id = test_create_regular_bot_for_exact_sum(admin_token)
        test_wait_for_bet_creation(bot_id)
        bot_games = test_get_bot_active_games(admin_token, bot_id)
        actual_sum = test_calculate_exact_cycle_sum(bot_games)
        test_verify_exact_sum_match(actual_sum)
        test_check_cycle_games_count(bot_games)
        test_check_bet_range_compliance(bot_games)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_exact_sum_summary()

if __name__ == "__main__":
    main()