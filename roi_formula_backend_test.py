#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ НОВОЙ ФОРМУЛЫ ROI для обычных ботов

Тестирует все новые элементы интерфейса и backend API integration:
1. Создание бота с новыми параметрами (wins_count/losses_count/draws_count)
2. Проверка новых колонок в списке ботов (ROI_active, СУММА ЦИКЛА)
3. Валидация расчетов ROI по формуле (profit/active_pool)*100%
4. Проверка backend API без HTTP 500 ошибок
5. Валидация процентов исходов = 100%
6. Валидация баланса игр = cycle_games

Использует admin@gemplay.com / Admin123! для авторизации
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
BASE_URL = "https://a0c62159-4f54-474f-b3db-88a2c8a14d22.preview.emergentagent.com/api"
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

def test_create_bot_with_new_roi_parameters():
    """Test 1: Создать тестового бота с новыми параметрами ROI"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Creating Bot with New ROI Parameters{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Create Bot with New ROI Parameters", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot with NEW ROI parameters
    bot_data = {
        "name": "ROI_Formula_Test_Bot",
        
        # Новые значения по умолчанию
        "min_bet_amount": 1.0,   # 1-100 (новый диапазон)
        "max_bet_amount": 100.0, # 1-100 (новый диапазон)
        "cycle_games": 16,       # 16 игр по умолчанию (было 12)
        
        # НОВАЯ ЛОГИКА: Баланс игр
        "wins_count": 6,         # Количество побед в цикле
        "losses_count": 6,       # Количество поражений в цикле  
        "draws_count": 4,        # Количество ничьих в цикле
        
        # Процент исходов игр (новые значения по умолчанию)
        "wins_percentage": 44.0,  # 44% побед
        "losses_percentage": 36.0, # 36% поражений
        "draws_percentage": 20.0,  # 20% ничьих
        
        "pause_between_cycles": 5,
        "pause_on_draw": 5,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"   📝 Creating ROI Formula Test Bot with NEW parameters:")
    print(f"   📊 Range: 1-100 (new default)")
    print(f"   📊 Cycle games: 16 (new default, was 12)")
    print(f"   📊 Game balance: 6/6/4 (wins/losses/draws)")
    print(f"   📊 Percentages: 44/36/20 (wins/losses/draws)")
    
    # Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        record_test(
            "Create Bot with New ROI Parameters",
            False,
            f"Failed to create ROI test bot: {details}"
        )
        return None
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        record_test(
            "Create Bot with New ROI Parameters",
            False,
            "Bot created but no bot_id returned"
        )
        return None
    
    print(f"   ✅ ROI Formula Test Bot created successfully with ID: {bot_id}")
    
    # Validate that bot was created with correct parameters
    success, bot_details, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}",
        headers=headers
    )
    
    if success and bot_details:
        # Check new fields are present
        has_wins_count = "wins_count" in bot_details
        has_losses_count = "losses_count" in bot_details
        has_draws_count = "draws_count" in bot_details
        has_wins_percentage = "wins_percentage" in bot_details
        has_losses_percentage = "losses_percentage" in bot_details
        has_draws_percentage = "draws_percentage" in bot_details
        
        correct_values = (
            bot_details.get("wins_count") == 6 and
            bot_details.get("losses_count") == 6 and
            bot_details.get("draws_count") == 4 and
            bot_details.get("wins_percentage") == 44.0 and
            bot_details.get("losses_percentage") == 36.0 and
            bot_details.get("draws_percentage") == 20.0 and
            bot_details.get("cycle_games") == 16 and
            bot_details.get("min_bet_amount") == 1.0 and
            bot_details.get("max_bet_amount") == 100.0
        )
        
        if has_wins_count and has_losses_count and has_draws_count and correct_values:
            record_test(
                "Create Bot with New ROI Parameters",
                True,
                f"Bot created with all new ROI parameters: wins_count=6, losses_count=6, draws_count=4, percentages=44/36/20"
            )
        else:
            record_test(
                "Create Bot with New ROI Parameters",
                False,
                f"Bot created but missing new fields or incorrect values: {bot_details}"
            )
    else:
        record_test(
            "Create Bot with New ROI Parameters",
            False,
            f"Could not retrieve bot details for validation: {details}"
        )
    
    return bot_id

def test_bot_list_new_columns():
    """Test 2: Проверить новые колонки в списке ботов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Testing New Columns in Bot List{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bot List New Columns Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/admin/bots/regular endpoint...")
    
    # Get bot list
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Bot List New Columns Test",
            False,
            f"Failed to get bot list: {details}"
        )
        return
    
    # Check if we have bots
    bots = response_data.get("bots", [])
    if not bots:
        record_test(
            "Bot List New Columns Test",
            False,
            "No bots found in the list"
        )
        return
    
    print(f"   📊 Found {len(bots)} bots in the list")
    
    # Check for new columns/fields in bot data
    test_bot = bots[0]  # Use first bot for testing
    
    # Check for ROI_active field (% column)
    has_roi_active = "bot_profit_percent" in test_bot or "roi_active" in test_bot
    roi_value = test_bot.get("bot_profit_percent", test_bot.get("roi_active", 0))
    
    # Check for cycle total info (СУММА ЦИКЛА column)
    has_cycle_total_info = "cycle_total_info" in test_bot
    cycle_total_info = test_bot.get("cycle_total_info", {})
    
    # Check if cycle_total_info has required fields
    has_active_pool = "active_pool" in cycle_total_info if cycle_total_info else False
    has_total_sum = "total_sum" in cycle_total_info if cycle_total_info else False
    has_draws_sum = "draws_sum" in cycle_total_info if cycle_total_info else False
    
    print(f"   🔍 Checking new columns in bot data:")
    print(f"      ROI_active field present: {has_roi_active}")
    print(f"      ROI_active value: {roi_value}% (should be with 2 decimal precision)")
    print(f"      Cycle total info present: {has_cycle_total_info}")
    if has_cycle_total_info:
        print(f"      Active pool: {cycle_total_info.get('active_pool', 'N/A')}")
        print(f"      Total sum: {cycle_total_info.get('total_sum', 'N/A')}")
        print(f"      Draws sum: {cycle_total_info.get('draws_sum', 'N/A')}")
    
    # Validate ROI calculation
    roi_precision_ok = True
    if has_roi_active and isinstance(roi_value, (int, float)):
        # Check if ROI has proper precision (2 decimal places)
        roi_str = f"{roi_value:.2f}"
        roi_precision_ok = len(roi_str.split('.')[-1]) <= 2
    
    # Check format of cycle total info (should be like "646 (из 808, ничьи: 162)")
    format_ok = has_active_pool and has_total_sum and has_draws_sum
    
    if has_roi_active and has_cycle_total_info and roi_precision_ok and format_ok:
        record_test(
            "Bot List New Columns Test",
            True,
            f"New columns present: ROI_active={roi_value}%, Active pool format correct"
        )
    else:
        missing_fields = []
        if not has_roi_active:
            missing_fields.append("ROI_active field")
        if not has_cycle_total_info:
            missing_fields.append("cycle_total_info field")
        if not roi_precision_ok:
            missing_fields.append("ROI precision issue")
        if not format_ok:
            missing_fields.append("cycle_total_info format issue")
        
        record_test(
            "Bot List New Columns Test",
            False,
            f"Missing or incorrect new columns: {', '.join(missing_fields)}"
        )

def test_roi_calculation_accuracy():
    """Test 3: Проверить точность расчета ROI по формуле (profit/active_pool)*100%"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Testing ROI Calculation Accuracy{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("ROI Calculation Accuracy Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get bot list to test ROI calculations
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "ROI Calculation Accuracy Test",
            False,
            f"Failed to get bot list for ROI testing: {details}"
        )
        return
    
    bots = response_data.get("bots", [])
    if not bots:
        record_test(
            "ROI Calculation Accuracy Test",
            False,
            "No bots available for ROI calculation testing"
        )
        return
    
    print(f"   📊 Testing ROI calculations for {len(bots)} bots")
    
    roi_tests_passed = 0
    roi_tests_total = 0
    
    for bot in bots[:3]:  # Test first 3 bots
        bot_name = bot.get("name", f"Bot#{bot.get('id', 'unknown')[:8]}")
        roi_tests_total += 1
        
        # Get ROI from API
        api_roi = bot.get("bot_profit_percent", bot.get("roi_active", 0))
        
        # Get cycle total info for manual calculation
        cycle_info = bot.get("cycle_total_info", {})
        active_pool = cycle_info.get("active_pool", 0)
        total_sum = cycle_info.get("total_sum", 0)
        draws_sum = cycle_info.get("draws_sum", 0)
        
        # Manual ROI calculation
        if active_pool > 0:
            # Get wins and losses from bot data
            wins_percentage = bot.get("wins_percentage", 44.0)
            losses_percentage = bot.get("losses_percentage", 36.0)
            
            # Calculate expected sums
            wins_sum = total_sum * wins_percentage / 100
            losses_sum = total_sum * losses_percentage / 100
            expected_active_pool = wins_sum + losses_sum
            expected_profit = wins_sum - losses_sum
            expected_roi = (expected_profit / expected_active_pool) * 100 if expected_active_pool > 0 else 0
            
            # Compare with API ROI (allow 0.1% tolerance)
            roi_diff = abs(api_roi - expected_roi)
            roi_accurate = roi_diff <= 0.1
            
            print(f"   🔍 Bot {bot_name}:")
            print(f"      API ROI: {api_roi:.2f}%")
            print(f"      Expected ROI: {expected_roi:.2f}%")
            print(f"      Difference: {roi_diff:.3f}%")
            print(f"      Active pool: {active_pool} (expected: {expected_active_pool:.0f})")
            
            if roi_accurate:
                roi_tests_passed += 1
                print(f"      ✅ ROI calculation accurate")
            else:
                print(f"      ❌ ROI calculation inaccurate")
        else:
            print(f"   ⚠️ Bot {bot_name}: No active pool data for ROI calculation")
    
    success_rate = (roi_tests_passed / roi_tests_total) * 100 if roi_tests_total > 0 else 0
    
    if success_rate >= 80:  # 80% success rate threshold
        record_test(
            "ROI Calculation Accuracy Test",
            True,
            f"ROI calculations accurate: {roi_tests_passed}/{roi_tests_total} bots ({success_rate:.1f}%)"
        )
    else:
        record_test(
            "ROI Calculation Accuracy Test",
            False,
            f"ROI calculations inaccurate: {roi_tests_passed}/{roi_tests_total} bots ({success_rate:.1f}%)"
        )

def test_backend_api_stability():
    """Test 4: Проверить что НЕТ HTTP 500 ошибок при загрузке списка ботов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Testing Backend API Stability (No HTTP 500 Errors){Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Backend API Stability Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test multiple API endpoints for stability
    endpoints_to_test = [
        "/admin/bots/regular",
        "/admin/bots/stats",
        "/admin/dashboard",
        "/bots/active-games"
    ]
    
    http_500_errors = 0
    successful_requests = 0
    total_requests = 0
    
    for endpoint in endpoints_to_test:
        print(f"   📝 Testing {endpoint}...")
        total_requests += 1
        
        success, response_data, details = make_request(
            "GET",
            endpoint,
            headers=headers
        )
        
        if "Status: 500" in details:
            http_500_errors += 1
            print(f"      ❌ HTTP 500 error detected")
        elif success:
            successful_requests += 1
            print(f"      ✅ Request successful")
        else:
            print(f"      ⚠️ Request failed but not HTTP 500: {details}")
    
    print(f"   📊 API Stability Results:")
    print(f"      Total requests: {total_requests}")
    print(f"      Successful requests: {successful_requests}")
    print(f"      HTTP 500 errors: {http_500_errors}")
    
    if http_500_errors == 0:
        record_test(
            "Backend API Stability Test",
            True,
            f"No HTTP 500 errors detected in {total_requests} API requests"
        )
    else:
        record_test(
            "Backend API Stability Test",
            False,
            f"Found {http_500_errors} HTTP 500 errors out of {total_requests} requests"
        )

def test_validation_rules():
    """Test 5: Проверить валидацию процентов исходов = 100% и баланса игр = cycle_games"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: Testing Validation Rules{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Validation Rules Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Invalid percentages (sum != 100%)
    print(f"   📝 Testing invalid percentages validation...")
    
    invalid_percentage_bot = {
        "name": "Invalid_Percentage_Test_Bot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "cycle_games": 16,
        "wins_count": 6,
        "losses_count": 6,
        "draws_count": 4,
        "wins_percentage": 50.0,   # 50 + 40 + 20 = 110% (invalid)
        "losses_percentage": 40.0,
        "draws_percentage": 20.0,
        "pause_between_cycles": 5,
        "pause_on_draw": 5,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=invalid_percentage_bot
    )
    
    percentage_validation_works = not success  # Should fail
    
    # Test 2: Invalid game balance (sum != cycle_games)
    print(f"   📝 Testing invalid game balance validation...")
    
    invalid_balance_bot = {
        "name": "Invalid_Balance_Test_Bot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "cycle_games": 16,
        "wins_count": 5,    # 5 + 5 + 3 = 13 != 16 (invalid)
        "losses_count": 5,
        "draws_count": 3,
        "wins_percentage": 44.0,
        "losses_percentage": 36.0,
        "draws_percentage": 20.0,
        "pause_between_cycles": 5,
        "pause_on_draw": 5,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=invalid_balance_bot
    )
    
    balance_validation_works = not success  # Should fail
    
    # Test 3: Valid bot (should succeed)
    print(f"   📝 Testing valid bot creation...")
    
    valid_bot = {
        "name": "Valid_Test_Bot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "cycle_games": 16,
        "wins_count": 6,
        "losses_count": 6,
        "draws_count": 4,
        "wins_percentage": 44.0,  # 44 + 36 + 20 = 100% (valid)
        "losses_percentage": 36.0,
        "draws_percentage": 20.0,
        "pause_between_cycles": 5,
        "pause_on_draw": 5,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=valid_bot
    )
    
    valid_bot_creation_works = success  # Should succeed
    
    print(f"   📊 Validation Results:")
    print(f"      Invalid percentages rejected: {percentage_validation_works}")
    print(f"      Invalid game balance rejected: {balance_validation_works}")
    print(f"      Valid bot created: {valid_bot_creation_works}")
    
    if percentage_validation_works and balance_validation_works and valid_bot_creation_works:
        record_test(
            "Validation Rules Test",
            True,
            "All validation rules working: percentages=100%, game balance=cycle_games"
        )
    else:
        failed_validations = []
        if not percentage_validation_works:
            failed_validations.append("percentage validation")
        if not balance_validation_works:
            failed_validations.append("game balance validation")
        if not valid_bot_creation_works:
            failed_validations.append("valid bot creation")
        
        record_test(
            "Validation Rules Test",
            False,
            f"Validation issues: {', '.join(failed_validations)}"
        )

def print_roi_formula_summary():
    """Print ROI Formula testing specific summary"""
    print_header("НОВАЯ ФОРМУЛА ROI - ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 ROI FORMULA REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each test
    create_test = next((test for test in test_results["tests"] if "create bot" in test["name"].lower()), None)
    columns_test = next((test for test in test_results["tests"] if "columns" in test["name"].lower()), None)
    roi_test = next((test for test in test_results["tests"] if "roi calculation" in test["name"].lower()), None)
    api_test = next((test for test in test_results["tests"] if "api stability" in test["name"].lower()), None)
    validation_test = next((test for test in test_results["tests"] if "validation" in test["name"].lower()), None)
    
    requirements = [
        ("1. СОЗДАНИЕ БОТА С НОВЫМИ ПАРАМЕТРАМИ", create_test),
        ("2. НОВЫЕ КОЛОНКИ В СПИСКЕ БОТОВ", columns_test),
        ("3. ТОЧНОСТЬ РАСЧЕТА ROI", roi_test),
        ("4. СТАБИЛЬНОСТЬ BACKEND API", api_test),
        ("5. ВАЛИДАЦИЯ ПРАВИЛ", validation_test)
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: НОВАЯ ФОРМУЛА ROI ПОЛНОСТЬЮ РАБОТАЕТ!{Colors.END}")
        print(f"{Colors.GREEN}✅ Создание бота с новыми параметрами работает{Colors.END}")
        print(f"{Colors.GREEN}✅ Новые колонки ROI_active и СУММА ЦИКЛА отображаются{Colors.END}")
        print(f"{Colors.GREEN}✅ ROI рассчитывается по формуле (profit/active_pool)*100%{Colors.END}")
        print(f"{Colors.GREEN}✅ Backend API стабилен без HTTP 500 ошибок{Colors.END}")
        print(f"{Colors.GREEN}✅ Валидация процентов и баланса игр работает{Colors.END}")
    elif success_rate >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: НОВАЯ ФОРМУЛА ROI РАБОТАЕТ ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Большинство функций новой формулы ROI работают, есть минорные проблемы.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: ЧАСТИЧНАЯ РАБОТА ФОРМУЛЫ ROI ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые функции работают, но требуется дополнительная работа.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: НОВАЯ ФОРМУЛА ROI НЕ РАБОТАЕТ ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Большинство функций новой формулы ROI НЕ работают. Требуется срочное исправление.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    if create_test and not create_test["success"]:
        print(f"   🔴 Bot creation with new ROI parameters needs fixing")
    if columns_test and not columns_test["success"]:
        print(f"   🔴 New columns (ROI_active, СУММА ЦИКЛА) not displaying correctly")
    if roi_test and not roi_test["success"]:
        print(f"   🔴 CRITICAL: ROI calculation formula is incorrect")
    if api_test and not api_test["success"]:
        print(f"   🔴 Backend API has HTTP 500 errors - needs stability fixes")
    if validation_test and not validation_test["success"]:
        print(f"   🔴 Validation rules not working properly")
    
    if success_rate == 100:
        print(f"   🟢 Новая формула ROI полностью готова к использованию")
        print(f"   ✅ Main agent can proceed with UI testing")
    else:
        print(f"   🔧 Fix remaining ROI formula issues before UI testing")

def main():
    """Main test execution for ROI Formula Testing"""
    print_header("НОВАЯ ФОРМУЛА ROI - ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ")
    print(f"{Colors.BLUE}🎯 Testing NEW ROI Formula for Regular Bots{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 CRITICAL: Testing wins_count/losses_count/draws_count logic{Colors.END}")
    print(f"{Colors.BLUE}📐 Formula: ROI_active = (profit/active_pool)*100%{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: Create bot with new ROI parameters
        bot_id = test_create_bot_with_new_roi_parameters()
        
        # Test 2: Check new columns in bot list
        test_bot_list_new_columns()
        
        # Test 3: Verify ROI calculation accuracy
        test_roi_calculation_accuracy()
        
        # Test 4: Check backend API stability (no HTTP 500 errors)
        test_backend_api_stability()
        
        # Test 5: Test validation rules
        test_validation_rules()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_roi_formula_summary()

if __name__ == "__main__":
    main()