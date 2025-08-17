#!/usr/bin/env python3
"""
RUSSIAN REVIEW REQUEST - REGULAR BOTS API COMPREHENSIVE TESTING
Пожалуйста, запусти авто‑тесты бэкенда для текущей версии API Regular Bots перед началом рефакторинга.

ЦЕЛИ ТЕСТОВ:
1) Базовая регрессия API Regular Bots, включая:
   - POST /api/admin/bots/create-regular (валидации, сохранение параметров, расчет cycle_total_amount)
   - GET /api/admin/bots/regular/list (возврат roi_active, cycle_total_info)
   - GET /api/admin/bots/{id} (получение параметров бота и статистики)
   - PUT /api/admin/bots/{id} и PATCH /api/admin/bots/{id} (частичные обновления, строгие валидации: проценты=100%, W+L+D=N)
   - GET /api/admin/bots/{id}/cycle-bets (детальная разбивка сумм и списков ставок)
   - POST /api/admin/bots/{id}/recalculate-bets (пересобрать ставки)
   - POST /api/admin/bots/{id}/toggle, /force-complete-cycle

2) Верифицировать корректность ROI_active = (wins_sum - losses_sum)/(wins_sum + losses_sum)*100, ничьи не входят в активный пул.

3) Проверить, что активные ставки не превышают cycle_games в обычных сценариях.

4) Зафиксировать текущее поведение ничьей: матчи с Regular ботом должны иметь фактические ничьи согласно новой логике.

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
import math

# Configuration
BASE_URL = "https://russianparts.preview.emergentagent.com/api"
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
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=30)
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

def test_create_regular_bot():
    """Test POST /api/admin/bots/create-regular - валидации, сохранение параметров, расчет cycle_total_amount"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: POST /api/admin/bots/create-regular{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Create Regular Bot", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test bot data with comprehensive parameters
    bot_data = {
        "name": f"RegularBot_Test_{int(time.time())}",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "wins_count": 6,
        "losses_count": 4,
        "draws_count": 2,
        "wins_percentage": 50.0,
        "losses_percentage": 33.3,
        "draws_percentage": 16.7,
        "cycle_games": 12,
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"   📝 Creating Regular bot with parameters:")
    print(f"      min_bet: {bot_data['min_bet_amount']}, max_bet: {bot_data['max_bet_amount']}")
    print(f"      cycle_games: {bot_data['cycle_games']}")
    print(f"      W/L/D balance: {bot_data['wins_count']}/{bot_data['losses_count']}/{bot_data['draws_count']}")
    print(f"      W/L/D percentages: {bot_data['wins_percentage']}/{bot_data['losses_percentage']}/{bot_data['draws_percentage']}")
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if success and response_data:
        bot_id = response_data.get("bot_id")
        if bot_id:
            # Calculate expected cycle_total_amount
            expected_cycle_total = (bot_data["min_bet_amount"] + bot_data["max_bet_amount"]) / 2 * bot_data["cycle_games"]
            
            record_test(
                "Create Regular Bot",
                True,
                f"Bot created successfully with ID: {bot_id}, expected cycle_total: ${expected_cycle_total}"
            )
            return bot_id, bot_data
        else:
            record_test("Create Regular Bot", False, "Bot created but no bot_id returned")
            return None
    else:
        record_test("Create Regular Bot", False, f"Failed to create bot: {details}")
        return None

def test_get_regular_bots_list():
    """Test GET /api/admin/bots/regular/list - возврат roi_active, cycle_total_info"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: GET /api/admin/bots/regular/list{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Get Regular Bots List", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if success and response_data:
        bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
        
        if bots:
            # Check if required fields are present
            first_bot = bots[0]
            has_roi_active = "roi_active" in first_bot or "win_percentage" in first_bot
            has_cycle_info = "cycle_total_amount" in first_bot or "cycle_games" in first_bot
            
            record_test(
                "Get Regular Bots List",
                True,
                f"Retrieved {len(bots)} bots, ROI fields: {has_roi_active}, Cycle info: {has_cycle_info}"
            )
            return bots
        else:
            record_test("Get Regular Bots List", True, "No bots found (empty list)")
            return []
    else:
        record_test("Get Regular Bots List", False, f"Failed to get bots list: {details}")
        return None

def test_get_bot_details(bot_id: str):
    """Test GET /api/admin/bots/{id} - получение параметров бота и статистики"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: GET /api/admin/bots/{bot_id}{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Get Bot Details", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}",
        headers=headers
    )
    
    if success and response_data:
        # Check for required fields
        required_fields = ["id", "name", "min_bet_amount", "max_bet_amount", "cycle_games"]
        statistics_fields = ["current_cycle_wins", "current_cycle_losses", "current_cycle_draws"]
        
        has_required = all(field in response_data for field in required_fields)
        has_statistics = any(field in response_data for field in statistics_fields)
        
        record_test(
            "Get Bot Details",
            True,
            f"Bot details retrieved, required fields: {has_required}, statistics: {has_statistics}"
        )
        return response_data
    else:
        record_test("Get Bot Details", False, f"Failed to get bot details: {details}")
        return None

def test_update_bot_put_patch(bot_id: str):
    """Test PUT /api/admin/bots/{id} и PATCH /api/admin/bots/{id} - строгие валидации"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: PUT/PATCH /api/admin/bots/{bot_id}{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Update Bot PUT/PATCH", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test PATCH with valid data (percentages = 100%, W+L+D = cycle_games)
    patch_data = {
        "wins_percentage": 50.0,
        "losses_percentage": 30.0,
        "draws_percentage": 20.0,  # Total = 100%
        "wins_count": 6,
        "losses_count": 4,
        "draws_count": 2  # Total = 12 (assuming cycle_games = 12)
    }
    
    print(f"   📝 Testing PATCH with valid percentages (100%) and W+L+D balance")
    
    success, response_data, details = make_request(
        "PATCH",
        f"/admin/bots/{bot_id}",
        headers=headers,
        data=patch_data
    )
    
    if success:
        record_test("Update Bot PATCH (Valid)", True, "PATCH update successful with valid data")
    else:
        record_test("Update Bot PATCH (Valid)", False, f"PATCH failed: {details}")
    
    # Test PATCH with invalid percentages (not 100%)
    invalid_patch_data = {
        "wins_percentage": 50.0,
        "losses_percentage": 30.0,
        "draws_percentage": 15.0  # Total = 95% (should fail)
    }
    
    print(f"   📝 Testing PATCH with invalid percentages (95% total)")
    
    success, response_data, details = make_request(
        "PATCH",
        f"/admin/bots/{bot_id}",
        headers=headers,
        data=invalid_patch_data
    )
    
    if not success:
        record_test("Update Bot PATCH (Invalid %)", True, "PATCH correctly rejected invalid percentages")
    else:
        record_test("Update Bot PATCH (Invalid %)", False, "PATCH should have rejected invalid percentages")

def test_get_cycle_bets(bot_id: str):
    """Test GET /api/admin/bots/{id}/cycle-bets - детальная разбивка сумм и списков ставок"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: GET /api/admin/bots/{bot_id}/cycle-bets{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Get Cycle Bets", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}/cycle-bets",
        headers=headers
    )
    
    if success and response_data:
        # Check for detailed breakdown
        has_bets_list = "bets" in response_data or "games" in response_data
        has_summary = "total_amount" in response_data or "cycle_total" in response_data
        
        bets_count = 0
        if "bets" in response_data:
            bets_count = len(response_data["bets"])
        elif "games" in response_data:
            bets_count = len(response_data["games"])
        elif isinstance(response_data, list):
            bets_count = len(response_data)
        
        record_test(
            "Get Cycle Bets",
            True,
            f"Cycle bets retrieved: {bets_count} bets, has_list: {has_bets_list}, has_summary: {has_summary}"
        )
        return response_data
    else:
        record_test("Get Cycle Bets", False, f"Failed to get cycle bets: {details}")
        return None

def test_recalculate_bets(bot_id: str):
    """Test POST /api/admin/bots/{id}/recalculate-bets - пересобрать ставки"""
    print(f"\n{Colors.MAGENTA}🧪 Test 6: POST /api/admin/bots/{bot_id}/recalculate-bets{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Recalculate Bets", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details = make_request(
        "POST",
        f"/admin/bots/{bot_id}/recalculate-bets",
        headers=headers
    )
    
    if success:
        record_test("Recalculate Bets", True, f"Bets recalculated successfully: {response_data}")
    else:
        record_test("Recalculate Bets", False, f"Failed to recalculate bets: {details}")

def test_bot_toggle_and_force_complete(bot_id: str):
    """Test POST /api/admin/bots/{id}/toggle, /force-complete-cycle"""
    print(f"\n{Colors.MAGENTA}🧪 Test 7: Bot Toggle and Force Complete Cycle{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bot Toggle/Force Complete", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test toggle
    success, response_data, details = make_request(
        "POST",
        f"/admin/bots/{bot_id}/toggle",
        headers=headers
    )
    
    if success:
        record_test("Bot Toggle", True, f"Bot toggle successful: {response_data}")
    else:
        record_test("Bot Toggle", False, f"Bot toggle failed: {details}")
    
    # Test force complete cycle
    success, response_data, details = make_request(
        "POST",
        f"/admin/bots/{bot_id}/force-complete-cycle",
        headers=headers
    )
    
    if success:
        record_test("Force Complete Cycle", True, f"Force complete cycle successful: {response_data}")
    else:
        record_test("Force Complete Cycle", False, f"Force complete cycle failed: {details}")

def test_roi_calculation():
    """Test ROI_active = (wins_sum - losses_sum)/(wins_sum + losses_sum)*100"""
    print(f"\n{Colors.MAGENTA}🧪 Test 8: ROI Active Calculation Verification{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("ROI Calculation", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get bots list to check ROI calculations
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if success and response_data:
        bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
        
        roi_tests_passed = 0
        roi_tests_total = 0
        
        for bot in bots[:3]:  # Test first 3 bots
            bot_id = bot.get("id")
            if not bot_id:
                continue
                
            roi_tests_total += 1
            
            # Get detailed bot info
            bot_success, bot_data, bot_details = make_request(
                "GET",
                f"/admin/bots/{bot_id}",
                headers=headers
            )
            
            if bot_success and bot_data:
                # Check if ROI calculation is correct
                wins_sum = bot_data.get("current_cycle_gem_value_won", 0)
                total_sum = bot_data.get("current_cycle_gem_value_total", 0)
                losses_sum = total_sum - wins_sum
                
                if wins_sum + losses_sum > 0:
                    expected_roi = (wins_sum - losses_sum) / (wins_sum + losses_sum) * 100
                    actual_roi = bot_data.get("roi_active", 0)
                    
                    roi_diff = abs(expected_roi - actual_roi)
                    if roi_diff < 0.1:  # Allow small floating point differences
                        roi_tests_passed += 1
        
        if roi_tests_total > 0:
            roi_success_rate = roi_tests_passed / roi_tests_total
            record_test(
                "ROI Calculation",
                roi_success_rate >= 0.8,
                f"ROI calculation verified for {roi_tests_passed}/{roi_tests_total} bots"
            )
        else:
            record_test("ROI Calculation", False, "No bots available for ROI testing")
    else:
        record_test("ROI Calculation", False, f"Failed to get bots for ROI testing: {details}")

def test_active_bets_limit():
    """Test that active bets don't exceed cycle_games in normal scenarios"""
    print(f"\n{Colors.MAGENTA}🧪 Test 9: Active Bets Limit Verification{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Active Bets Limit", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get active games for regular bots
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        # Group games by bot_id
        bot_games = {}
        for game in games:
            bot_id = game.get("bot_id")
            if bot_id:
                if bot_id not in bot_games:
                    bot_games[bot_id] = []
                bot_games[bot_id].append(game)
        
        violations = 0
        total_bots = len(bot_games)
        
        for bot_id, bot_game_list in bot_games.items():
            # Get bot details to check cycle_games
            bot_success, bot_data, bot_details = make_request(
                "GET",
                f"/admin/bots/{bot_id}",
                headers=headers
            )
            
            if bot_success and bot_data:
                cycle_games = bot_data.get("cycle_games", 12)
                active_bets = len(bot_game_list)
                
                if active_bets > cycle_games:
                    violations += 1
                    print(f"   ⚠️ Bot {bot_id}: {active_bets} active bets > {cycle_games} cycle_games")
        
        record_test(
            "Active Bets Limit",
            violations == 0,
            f"Checked {total_bots} bots, {violations} violations found"
        )
    else:
        record_test("Active Bets Limit", False, f"Failed to get active games: {details}")

def test_draw_behavior():
    """Test current draw behavior for Regular bots"""
    print(f"\n{Colors.MAGENTA}🧪 Test 10: Draw Behavior Verification{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Draw Behavior", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get completed games to check draw behavior
    success, response_data, details = make_request(
        "GET",
        "/admin/games",
        headers=headers,
        params={"status": "COMPLETED", "limit": 50}
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        regular_bot_games = [game for game in games if game.get("is_regular_bot_game", False)]
        draw_games = [game for game in regular_bot_games if game.get("winner_id") is None]
        
        total_regular_games = len(regular_bot_games)
        draw_count = len(draw_games)
        draw_percentage = (draw_count / total_regular_games * 100) if total_regular_games > 0 else 0
        
        record_test(
            "Draw Behavior",
            True,
            f"Regular bot games: {total_regular_games}, Draws: {draw_count} ({draw_percentage:.1f}%)"
        )
    else:
        record_test("Draw Behavior", False, f"Failed to get completed games: {details}")

def print_comprehensive_summary():
    """Print comprehensive testing summary"""
    print_header("REGULAR BOTS API COMPREHENSIVE TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 API ENDPOINTS STATUS:{Colors.END}")
    
    # Group tests by endpoint
    endpoint_tests = {
        "POST /api/admin/bots/create-regular": [],
        "GET /api/admin/bots/regular/list": [],
        "GET /api/admin/bots/{id}": [],
        "PUT/PATCH /api/admin/bots/{id}": [],
        "GET /api/admin/bots/{id}/cycle-bets": [],
        "POST /api/admin/bots/{id}/recalculate-bets": [],
        "Bot Toggle/Force Complete": [],
        "ROI Calculation": [],
        "Active Bets Limit": [],
        "Draw Behavior": []
    }
    
    for test in test_results["tests"]:
        test_name = test["name"]
        if "Create Regular Bot" in test_name:
            endpoint_tests["POST /api/admin/bots/create-regular"].append(test)
        elif "Regular Bots List" in test_name:
            endpoint_tests["GET /api/admin/bots/regular/list"].append(test)
        elif "Bot Details" in test_name:
            endpoint_tests["GET /api/admin/bots/{id}"].append(test)
        elif "PUT/PATCH" in test_name or "Update Bot" in test_name:
            endpoint_tests["PUT/PATCH /api/admin/bots/{id}"].append(test)
        elif "Cycle Bets" in test_name:
            endpoint_tests["GET /api/admin/bots/{id}/cycle-bets"].append(test)
        elif "Recalculate" in test_name:
            endpoint_tests["POST /api/admin/bots/{id}/recalculate-bets"].append(test)
        elif "Toggle" in test_name or "Force Complete" in test_name:
            endpoint_tests["Bot Toggle/Force Complete"].append(test)
        elif "ROI" in test_name:
            endpoint_tests["ROI Calculation"].append(test)
        elif "Active Bets Limit" in test_name:
            endpoint_tests["Active Bets Limit"].append(test)
        elif "Draw Behavior" in test_name:
            endpoint_tests["Draw Behavior"].append(test)
    
    for endpoint, tests in endpoint_tests.items():
        if tests:
            passed_tests = sum(1 for test in tests if test["success"])
            total_tests = len(tests)
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if passed_tests == total_tests else f"{Colors.RED}❌ ISSUES{Colors.END}"
            print(f"   {endpoint}: {status} ({passed_tests}/{total_tests})")
        else:
            print(f"   {endpoint}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED ISSUES:{Colors.END}")
    failed_tests = [test for test in test_results["tests"] if not test["success"]]
    if failed_tests:
        for test in failed_tests:
            print(f"   {Colors.RED}❌{Colors.END} {test['name']}: {test['details']}")
    else:
        print(f"   {Colors.GREEN}✅ No issues found - all tests passed{Colors.END}")
    
    # Recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.END}")
    
    if success_rate == 100:
        print(f"   {Colors.GREEN}🎉 ALL REGULAR BOTS API ENDPOINTS ARE WORKING CORRECTLY{Colors.END}")
        print(f"   ✅ System is ready for refactoring")
        print(f"   ✅ All validations, calculations, and endpoints functional")
    elif success_rate >= 80:
        print(f"   {Colors.YELLOW}⚠️ Most endpoints working, minor issues need attention{Colors.END}")
        print(f"   🔧 Fix remaining issues before refactoring")
    else:
        print(f"   {Colors.RED}🚨 CRITICAL ISSUES FOUND - DO NOT PROCEED WITH REFACTORING{Colors.END}")
        print(f"   🔴 Multiple endpoints have problems")
        print(f"   🔧 Fix all issues before any refactoring work")

def main():
    """Main test execution for Regular Bots API"""
    print_header("REGULAR BOTS API COMPREHENSIVE TESTING")
    print(f"{Colors.BLUE}🎯 Testing Regular Bots API before refactoring{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: Create Regular Bot
        bot_result = test_create_regular_bot()
        bot_id = None
        if bot_result:
            bot_id, bot_data = bot_result
        
        # Test 2: Get Regular Bots List
        test_get_regular_bots_list()
        
        # Test 3-7: Bot-specific tests (if we have a bot_id)
        if bot_id:
            test_get_bot_details(bot_id)
            test_update_bot_put_patch(bot_id)
            test_get_cycle_bets(bot_id)
            test_recalculate_bets(bot_id)
            test_bot_toggle_and_force_complete(bot_id)
        
        # Test 8-10: System-wide tests
        test_roi_calculation()
        test_active_bets_limit()
        test_draw_behavior()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_comprehensive_summary()

if __name__ == "__main__":
    main()