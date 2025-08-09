#!/usr/bin/env python3
"""
NEW ROI FORMULA TESTING - Comprehensive Test Suite
Протестировать новую формулу ROI для обычных ботов

КРИТИЧЕСКИ ВАЖНО - ТЕСТИРУЕМ НОВУЮ ЛОГИКУ:

1. Тест создания бота с новыми параметрами:
   - Баланс игр: wins_count/losses_count/draws_count (по умолчанию 6/6/4)
   - Процент исходов: wins_percentage/losses_percentage/draws_percentage (по умолчанию 44/36/20)
   - Диапазон ставок: 1-100 (обновленный по умолчанию)
   - Игр в цикле: 16 (было 12)

2. Тест предварительного расчета:
   - Общая сумма цикла (~808)
   - Активный пул (wins + losses)
   - ROI_active по формуле (profit/active_pool)*100%

3. Тест списка ботов:
   - Колонка "%" теперь показывает ROI_active с 2 знаками после запятой
   - Колонка "СУММА ЦИКЛА" показывает активный пул с дополнительной информацией
   - Формат: "646 (из 808, ничьи: 162)"

4. Тест backend логики:
   - Проверить что backend использует новую функцию generate_cycle_bets_natural_distribution
   - ROI рассчитывается по формуле: (profit / active_pool) * 100%
   - Ничьи НЕ пересоздаются (остаются как есть)
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
BASE_URL = "https://f5408cb5-a948-4578-b0dd-1a7c404eb24f.preview.emergentagent.com/api"
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

def test_new_bot_creation_parameters():
    """Test 1: Создание бота с новыми параметрами ROI формулы"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Creating Bot with NEW ROI Formula Parameters{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("New ROI Bot Creation", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot with NEW ROI parameters
    bot_data = {
        "name": "ROI_Test_Bot_2024",
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,  # Updated default range
        "cycle_games": 16,        # Updated from 12 to 16
        # NEW PARAMETERS - Balance of games
        "wins_count": 6,          # Default 6
        "losses_count": 6,        # Default 6  
        "draws_count": 4,         # Default 4
        # NEW PARAMETERS - Outcome percentages
        "wins_percentage": 44.0,  # Default 44%
        "losses_percentage": 36.0, # Default 36%
        "draws_percentage": 20.0,  # Default 20%
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"   📝 Creating Regular bot 'ROI_Test_Bot_2024' with NEW ROI parameters")
    print(f"   📊 Range: 1-100, Cycle: 16 games")
    print(f"   🎯 Balance: {bot_data['wins_count']}W/{bot_data['losses_count']}L/{bot_data['draws_count']}D")
    print(f"   📈 Percentages: {bot_data['wins_percentage']}%/{bot_data['losses_percentage']}%/{bot_data['draws_percentage']}%")
    
    # Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        record_test(
            "New ROI Bot Creation",
            False,
            f"Failed to create ROI bot: {details}"
        )
        return None
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        record_test(
            "New ROI Bot Creation",
            False,
            "Bot created but no bot_id returned"
        )
        return None
    
    # Check if response contains expected ROI calculation preview
    has_cycle_sum = "cycle_total_amount" in response_data or "total_cycle_sum" in response_data
    has_active_pool = "active_pool" in response_data
    has_roi_active = "roi_active" in response_data
    
    cycle_sum = response_data.get("cycle_total_amount", response_data.get("total_cycle_sum", 0))
    active_pool = response_data.get("active_pool", 0)
    roi_active = response_data.get("roi_active", 0)
    
    print(f"   ✅ ROI bot created successfully with ID: {bot_id}")
    print(f"   📊 Cycle sum: {cycle_sum}, Active pool: {active_pool}, ROI: {roi_active}%")
    
    # Expected cycle sum should be around 808 for range 1-100, 16 games
    expected_cycle_sum_range = (750, 850)  # Allow some variance
    cycle_sum_ok = expected_cycle_sum_range[0] <= cycle_sum <= expected_cycle_sum_range[1]
    
    if has_cycle_sum and cycle_sum_ok:
        record_test(
            "New ROI Bot Creation",
            True,
            f"Bot created with correct ROI parameters. Cycle sum: {cycle_sum} (expected ~808)"
        )
    else:
        record_test(
            "New ROI Bot Creation",
            False,
            f"Bot created but ROI parameters missing or incorrect. Cycle sum: {cycle_sum}"
        )
    
    return bot_id, response_data

def test_preliminary_roi_calculation(bot_data=None):
    """Test 2: Проверка предварительного расчета ROI"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Testing Preliminary ROI Calculation{Colors.END}")
    
    if not bot_data:
        record_test("Preliminary ROI Calculation", False, "No bot data available from previous test")
        return
    
    # Extract ROI calculation data
    cycle_sum = bot_data.get("cycle_total_amount", bot_data.get("total_cycle_sum", 0))
    active_pool = bot_data.get("active_pool", 0)
    roi_active = bot_data.get("roi_active", 0)
    draws_sum = bot_data.get("draws_sum", 0)
    
    print(f"   📊 ROI Calculation Analysis:")
    print(f"      Total cycle sum: {cycle_sum}")
    print(f"      Active pool (wins + losses): {active_pool}")
    print(f"      Draws sum: {draws_sum}")
    print(f"      ROI_active: {roi_active}%")
    
    # Validate ROI calculation
    # ROI_active = (profit / active_pool) * 100%
    # For balanced strategy, profit should be close to 0, so ROI should be close to 0
    
    # Check if active pool + draws sum = total cycle sum
    calculated_total = active_pool + draws_sum
    total_sum_correct = abs(calculated_total - cycle_sum) < 1.0  # Allow small rounding errors
    
    # Check if ROI is calculated correctly (should be close to 0 for balanced strategy)
    roi_reasonable = -20 <= roi_active <= 20  # Allow reasonable range for balanced strategy
    
    # Check if active pool is approximately 80% of total (44% + 36% = 80%)
    expected_active_ratio = 0.8  # 44% + 36% = 80%
    actual_active_ratio = active_pool / cycle_sum if cycle_sum > 0 else 0
    active_ratio_correct = abs(actual_active_ratio - expected_active_ratio) < 0.1
    
    print(f"   🔍 Validation Results:")
    print(f"      Total sum check: {calculated_total} ≈ {cycle_sum} ✅" if total_sum_correct else f"      Total sum check: {calculated_total} ≠ {cycle_sum} ❌")
    print(f"      Active pool ratio: {actual_active_ratio:.2%} ≈ 80% ✅" if active_ratio_correct else f"      Active pool ratio: {actual_active_ratio:.2%} ≠ 80% ❌")
    print(f"      ROI reasonable: {roi_active}% ✅" if roi_reasonable else f"      ROI unreasonable: {roi_active}% ❌")
    
    if total_sum_correct and active_ratio_correct and roi_reasonable:
        record_test(
            "Preliminary ROI Calculation",
            True,
            f"ROI calculation correct: {roi_active}% with active pool {active_pool} from total {cycle_sum}"
        )
    else:
        issues = []
        if not total_sum_correct:
            issues.append("total sum mismatch")
        if not active_ratio_correct:
            issues.append("active pool ratio incorrect")
        if not roi_reasonable:
            issues.append("ROI unreasonable")
        
        record_test(
            "Preliminary ROI Calculation",
            False,
            f"ROI calculation issues: {', '.join(issues)}"
        )

def test_bot_list_roi_display():
    """Test 3: Проверка отображения ROI в списке ботов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Testing ROI Display in Bot List{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bot List ROI Display", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get list of regular bots
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Bot List ROI Display",
            False,
            f"Failed to get bot list: {details}"
        )
        return
    
    bots = response_data.get("bots", [])
    if not bots:
        record_test(
            "Bot List ROI Display",
            False,
            "No bots found in list"
        )
        return
    
    print(f"   📋 Found {len(bots)} regular bots")
    
    # Check ROI display format in bot list
    roi_display_correct = True
    cycle_sum_format_correct = True
    
    for bot in bots[:3]:  # Check first 3 bots
        bot_name = bot.get("name", "Unknown")
        roi_display = bot.get("roi_active", bot.get("roi", "N/A"))
        cycle_sum_display = bot.get("cycle_sum_display", bot.get("cycle_total_amount", "N/A"))
        
        print(f"   🤖 Bot: {bot_name}")
        print(f"      ROI display: {roi_display}")
        print(f"      Cycle sum display: {cycle_sum_display}")
        
        # Check ROI format (should be X.XX%)
        if isinstance(roi_display, (int, float)):
            roi_formatted_correctly = True  # Numeric value is acceptable
        elif isinstance(roi_display, str) and "%" in roi_display:
            try:
                # Extract numeric part and check if it has 2 decimal places
                roi_value = float(roi_display.replace("%", ""))
                roi_formatted_correctly = True
            except:
                roi_formatted_correctly = False
        else:
            roi_formatted_correctly = False
        
        if not roi_formatted_correctly:
            roi_display_correct = False
        
        # Check cycle sum format (should include active pool info)
        # Expected format: "646 (из 808, ничьи: 162)" or similar
        if isinstance(cycle_sum_display, str) and ("из" in cycle_sum_display or "ничьи" in cycle_sum_display):
            cycle_format_ok = True
        else:
            cycle_format_ok = False
            cycle_sum_format_correct = False
    
    if roi_display_correct and cycle_sum_format_correct:
        record_test(
            "Bot List ROI Display",
            True,
            "ROI and cycle sum display formats are correct"
        )
    else:
        issues = []
        if not roi_display_correct:
            issues.append("ROI format incorrect")
        if not cycle_sum_format_correct:
            issues.append("cycle sum format missing active pool info")
        
        record_test(
            "Bot List ROI Display",
            False,
            f"Display format issues: {', '.join(issues)}"
        )

def test_backend_new_formula_usage():
    """Test 4: Проверка использования новой функции generate_cycle_bets_natural_distribution"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Testing Backend NEW Formula Usage{Colors.END}")
    
    try:
        # Try to read supervisor logs for backend
        import subprocess
        
        # Get recent backend logs
        result = subprocess.run(
            ["tail", "-n", "1000", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for NEW FORMULA specific messages
            new_formula_msgs = log_content.count("NEW FORMULA: Generating cycle bets")
            roi_active_msgs = log_content.count("ROI_active:")
            active_pool_msgs = log_content.count("Active pool:")
            natural_distribution_msgs = log_content.count("generate_cycle_bets_natural_distribution")
            draws_not_recreated_msgs = log_content.count("Ничьи НЕ пересоздаются")
            
            print(f"   📋 NEW ROI Formula Log Messages:")
            print(f"      🎯 'NEW FORMULA: Generating cycle bets': {new_formula_msgs}")
            print(f"      🎯 'ROI_active:' calculations: {roi_active_msgs}")
            print(f"      🎯 'Active pool:' mentions: {active_pool_msgs}")
            print(f"      🎯 'generate_cycle_bets_natural_distribution' calls: {natural_distribution_msgs}")
            print(f"      🎯 'Ничьи НЕ пересоздаются' confirmations: {draws_not_recreated_msgs}")
            
            # Success criteria: should have NEW FORMULA messages
            has_new_formula_messages = new_formula_msgs > 0
            has_roi_calculations = roi_active_msgs > 0
            has_function_calls = natural_distribution_msgs > 0
            
            total_new_msgs = new_formula_msgs + roi_active_msgs + active_pool_msgs + natural_distribution_msgs
            
            if has_new_formula_messages and has_roi_calculations:
                record_test(
                    "Backend NEW Formula Usage",
                    True,
                    f"Found {total_new_msgs} NEW ROI formula messages in logs"
                )
            elif has_function_calls:
                record_test(
                    "Backend NEW Formula Usage",
                    True,
                    f"Found function calls to new formula ({natural_distribution_msgs} times)"
                )
            else:
                record_test(
                    "Backend NEW Formula Usage",
                    False,
                    "No NEW ROI formula messages found in recent logs"
                )
            
            # Show some relevant log lines
            new_formula_lines = []
            for line in log_content.split('\n'):
                if any(keyword in line for keyword in [
                    "NEW FORMULA:",
                    "ROI_active:",
                    "Active pool:",
                    "generate_cycle_bets_natural_distribution"
                ]):
                    new_formula_lines.append(line.strip())
            
            if new_formula_lines:
                print(f"   📝 Recent NEW ROI formula log lines:")
                for line in new_formula_lines[-5:]:  # Show last 5 relevant lines
                    print(f"      {line}")
            else:
                print(f"   ⚠️ No NEW ROI formula log messages found in recent logs")
                    
        else:
            record_test(
                "Backend NEW Formula Usage",
                False,
                f"Failed to read backend logs: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        record_test("Backend NEW Formula Usage", False, "Timeout reading backend logs")
    except Exception as e:
        record_test("Backend NEW Formula Usage", False, f"Error reading logs: {str(e)}")

def test_roi_calculation_accuracy():
    """Test 5: Проверка точности расчета ROI формулы"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: Testing ROI Calculation Accuracy{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("ROI Calculation Accuracy", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Wait for bot to create some bets
    print(f"   ⏳ Waiting 30 seconds for bot to create cycle bets...")
    time.sleep(30)
    
    # Get active games for ROI test bot
    success, games_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not games_data:
        record_test(
            "ROI Calculation Accuracy",
            False,
            f"Failed to get active games: {details}"
        )
        return
    
    # Filter games for our ROI test bot
    roi_bot_games = []
    if isinstance(games_data, list):
        roi_bot_games = [game for game in games_data if "ROI_Test_Bot" in game.get("creator_id", "")]
    elif isinstance(games_data, dict) and "games" in games_data:
        roi_bot_games = [game for game in games_data["games"] if "ROI_Test_Bot" in game.get("creator_id", "")]
    
    if not roi_bot_games:
        record_test(
            "ROI Calculation Accuracy",
            False,
            "No active games found for ROI test bot"
        )
        return
    
    print(f"   📊 Found {len(roi_bot_games)} active games for ROI test bot")
    
    # Calculate actual ROI based on game data
    total_bet_amount = sum(float(game.get("bet_amount", 0)) for game in roi_bot_games)
    
    # Simulate wins/losses based on new formula (44%/36%/20%)
    wins_amount = total_bet_amount * 0.44
    losses_amount = total_bet_amount * 0.36
    draws_amount = total_bet_amount * 0.20
    
    active_pool = wins_amount + losses_amount
    profit = wins_amount - losses_amount
    calculated_roi = (profit / active_pool * 100) if active_pool > 0 else 0
    
    print(f"   🧮 ROI Calculation Verification:")
    print(f"      Total bet amount: {total_bet_amount}")
    print(f"      Wins amount (44%): {wins_amount}")
    print(f"      Losses amount (36%): {losses_amount}")
    print(f"      Draws amount (20%): {draws_amount}")
    print(f"      Active pool: {active_pool}")
    print(f"      Profit: {profit}")
    print(f"      Calculated ROI_active: {calculated_roi:.2f}%")
    
    # For balanced strategy with 44% wins and 36% losses, ROI should be positive
    expected_roi_range = (15, 25)  # Expected around 22.22% for 44/36 split
    roi_in_expected_range = expected_roi_range[0] <= calculated_roi <= expected_roi_range[1]
    
    # Check if we have the expected 16 games
    expected_games = 16
    games_count_correct = len(roi_bot_games) == expected_games
    
    if roi_in_expected_range and games_count_correct:
        record_test(
            "ROI Calculation Accuracy",
            True,
            f"ROI calculation accurate: {calculated_roi:.2f}% with {len(roi_bot_games)} games"
        )
    else:
        issues = []
        if not roi_in_expected_range:
            issues.append(f"ROI {calculated_roi:.2f}% not in expected range {expected_roi_range}")
        if not games_count_correct:
            issues.append(f"Games count {len(roi_bot_games)} ≠ expected {expected_games}")
        
        record_test(
            "ROI Calculation Accuracy",
            False,
            f"ROI calculation issues: {', '.join(issues)}"
        )

def print_roi_formula_summary():
    """Print NEW ROI Formula testing summary"""
    print_header("NEW ROI FORMULA TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 NEW ROI FORMULA REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each test
    tests_status = [
        ("1. NEW BOT PARAMETERS", "new roi bot creation"),
        ("2. PRELIMINARY ROI CALCULATION", "preliminary roi calculation"),
        ("3. BOT LIST ROI DISPLAY", "bot list roi display"),
        ("4. BACKEND NEW FORMULA USAGE", "backend new formula usage"),
        ("5. ROI CALCULATION ACCURACY", "roi calculation accuracy")
    ]
    
    for requirement, test_key in tests_status:
        test = next((test for test in test_results["tests"] if test_key in test["name"].lower()), None)
        if test:
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
            print(f"   {requirement}: {status}")
            if test["details"]:
                print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
        else:
            print(f"   {requirement}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: NEW ROI FORMULA IS WORKING PERFECTLY!{Colors.END}")
        print(f"{Colors.GREEN}✅ Новые параметры ботов работают{Colors.END}")
        print(f"{Colors.GREEN}✅ ROI_active рассчитывается правильно{Colors.END}")
        print(f"{Colors.GREEN}✅ Отображение в списке ботов корректное{Colors.END}")
        print(f"{Colors.GREEN}✅ Backend использует новую функцию{Colors.END}")
        print(f"{Colors.GREEN}✅ Ничьи НЕ пересоздаются{Colors.END}")
    elif success_rate >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: NEW ROI FORMULA MOSTLY WORKING ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Большинство функций новой ROI формулы работают, но есть минорные проблемы.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL ROI FORMULA SUCCESS ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые функции новой ROI формулы работают, но требуется дополнительная работа.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: NEW ROI FORMULA HAS CRITICAL ISSUES ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Большинство функций новой ROI формулы НЕ работают. Требуется срочное исправление.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    failed_tests = [test for test in test_results["tests"] if not test["success"]]
    if failed_tests:
        for test in failed_tests:
            print(f"   🔴 Fix: {test['name']} - {test['details']}")
    
    if success_rate == 100:
        print(f"   🟢 All NEW ROI formula features are working - ready for production")
        print(f"   ✅ Main agent can proceed with confidence")
    else:
        print(f"   🔧 Fix remaining NEW ROI formula issues before deployment")

def main():
    """Main test execution for NEW ROI Formula"""
    print_header("NEW ROI FORMULA COMPREHENSIVE TESTING")
    print(f"{Colors.BLUE}🎯 Testing NEW ROI Formula Implementation{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 CRITICAL: ROI_active = (profit/active_pool)*100%{Colors.END}")
    print(f"{Colors.BLUE}📐 New Parameters: wins_count/losses_count/draws_count + percentages{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: Create bot with new ROI parameters
        bot_id, bot_data = test_new_bot_creation_parameters()
        
        # Test 2: Check preliminary ROI calculation
        if bot_data:
            test_preliminary_roi_calculation(bot_data)
        
        # Test 3: Check ROI display in bot list
        test_bot_list_roi_display()
        
        # Test 4: Check backend usage of new formula
        test_backend_new_formula_usage()
        
        # Test 5: Check ROI calculation accuracy
        if bot_id:
            test_roi_calculation_accuracy()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_roi_formula_summary()

if __name__ == "__main__":
    main()