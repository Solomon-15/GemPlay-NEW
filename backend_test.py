#!/usr/bin/env python3
"""
RUSSIAN REVIEW TESTING - Three Critical Issues
Протестировать все три критические проблемы которые были исправлены

1. **КНОПКА ОЧИСТКИ КЭША** - УЖЕ ПРОТЕСТИРОВАНО И РАБОТАЕТ
   - Кратко проверить что POST /api/admin/cache/clear все еще работает

2. **ЛОГИКА REGULAR БОТОВ - ЦИКЛЫ**
   - Создать тестовый Regular бот с параметрами: min_bet=1.0, max_bet=50.0, cycle_games=12
   - Подождать чтобы бот создал ставки
   - ПРОВЕРИТЬ что бот создает РОВНО 12 активных ставок (не больше, не меньше)
   - ПРОВЕРИТЬ что ставки НЕ превышают лимит cycle_games

3. **ТОЧНОЕ СОВПАДЕНИЕ СУММЫ ЦИКЛА**
   - Для того же бота проверить что общая сумма всех 12 ставок = ровно 306.0
   - Расчет: (min_bet + max_bet) / 2 * cycle_games = (1+50)/2 * 12 = 25.5 * 12 = 306.0
   - КРИТИЧЕСКИ ВАЖНО: сумма должна быть ТОЧНО 306.0, не 305, не 307

4. **ЛОГИ BACKEND**
   - Проверить что в логах есть сообщения вида:
     - "✅ ARCHITECTURAL SUCCESS! Perfect exact sum match!"
     - "PERFECT MATCH! Final sum = 306"
     - Никаких ошибок типа HTTP 500

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
BASE_URL = "https://f772daa6-fb15-4f46-808e-f02104f088ba.preview.emergentagent.com/api"
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

def test_clear_cache_button():
    """Test 1: Кратко проверить что POST /api/admin/cache/clear все еще работает"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Testing Clear Cache Button (Brief Check){Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Clear Cache Button Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing POST /api/admin/cache/clear endpoint...")
    
    # Test clear cache endpoint
    success, response_data, details = make_request(
        "POST",
        "/admin/cache/clear",
        headers=headers
    )
    
    if success and response_data:
        # Check response structure
        has_success = response_data.get("success", False)
        has_message = "message" in response_data
        has_cache_types = "cache_types_cleared" in response_data
        
        if has_success and has_message and has_cache_types:
            cache_types = response_data.get("cache_types_cleared", [])
            cleared_count = response_data.get("cleared_count", 0)
            
            record_test(
                "Clear Cache Button Test",
                True,
                f"Cache cleared successfully: {cleared_count} types cleared ({', '.join(cache_types[:3])}...)"
            )
        else:
            record_test(
                "Clear Cache Button Test",
                False,
                f"Invalid response structure: {response_data}"
            )
    else:
        record_test(
            "Clear Cache Button Test",
            False,
            f"Cache clear failed: {details}"
        )

def test_regular_bot_cycle_logic():
    """Test 2: Создать тестовый REGULAR БОТ с точными параметрами из русского обзора"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Creating FINAL ARCHITECTURE TEST BOT{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Final Architecture Test Bot Creation", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot with EXACT settings from Russian review
    bot_data = {
        "name": "Final_Architecture_Test_Bot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "cycle_games": 12,
        "win_percentage": 55,
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"   📝 Creating Regular bot 'Final_Architecture_Test_Bot'")
    print(f"   📊 Parameters: min_bet=1.0, max_bet=50.0, cycle_games=12, win_percentage=55")
    
    # Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        record_test(
            "Final Architecture Test Bot Creation",
            False,
            f"Failed to create Regular bot: {details}"
        )
        return None
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        record_test(
            "Final Architecture Test Bot Creation",
            False,
            "Bot created but no bot_id returned"
        )
        return None
    
    print(f"   ✅ Regular bot created successfully with ID: {bot_id}")
    
    # Wait 25 seconds as specified in Russian review
    print(f"   ⏳ Waiting 25 seconds for complete cycle creation (as per Russian review)...")
    time.sleep(25)
    
    # Get ALL active games for this specific bot
    success, games_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not games_data:
        record_test(
            "Regular Bot Active Games Retrieval",
            False,
            f"Failed to get active games: {details}"
        )
        return None
    
    # Filter games for our specific bot
    bot_games = []
    if isinstance(games_data, list):
        bot_games = [game for game in games_data if game.get("bot_id") == bot_id]
    elif isinstance(games_data, dict) and "games" in games_data:
        bot_games = [game for game in games_data["games"] if game.get("bot_id") == bot_id]
    
    bet_count = len(bot_games)
    print(f"   📊 Found {bet_count} active games for Final_Architecture_Test_Bot")
    
    # Check if bot creates EXACTLY 12 active bets
    correct_bet_count = bet_count == 12
    
    if correct_bet_count:
        record_test(
            "Final Architecture Test Bot - Bet Count",
            True,
            f"Bot created exactly 12 active bets as expected (cycle_games=12)"
        )
    else:
        record_test(
            "Final Architecture Test Bot - Bet Count",
            False,
            f"Bot created {bet_count} bets instead of 12 (cycle_games limit violation)"
        )
    
    return bot_id, bot_games

def test_exact_cycle_sum_matching(bot_id=None, bot_games=None):
    """Test 3: КРИТИЧЕСКАЯ ПРОВЕРКА - Сумма ДОЛЖНА быть ТОЧНО 306.0"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: CRITICAL - Exact Cycle Sum Must Equal 306.0{Colors.END}")
    
    if not bot_id or not bot_games:
        record_test("CRITICAL Exact Cycle Sum Test", False, "No bot data available from previous test")
        return
    
    # Calculate EXACT sum of ALL bet_amount values
    bet_amounts = [float(game.get("bet_amount", 0)) for game in bot_games]
    total_sum = sum(bet_amounts)
    bet_count = len(bet_amounts)
    min_bet = min(bet_amounts) if bet_amounts else 0
    max_bet = max(bet_amounts) if bet_amounts else 0
    avg_bet = total_sum / bet_count if bet_count > 0 else 0
    
    print(f"   📊 FINAL ARCHITECTURE TEST RESULTS:")
    print(f"      Количество ставок: {bet_count}")
    print(f"      Минимальная ставка: ${min_bet:.1f}")
    print(f"      Максимальная ставка: ${max_bet:.1f}")
    print(f"      Средняя ставка: ${avg_bet:.1f}")
    print(f"      🎯 ФАКТИЧЕСКАЯ СУММА: ${total_sum:.1f}")
    print(f"      🎯 ОЖИДАЕМАЯ СУММА: $306.0")
    print(f"      📐 Расчет: (1+50)/2 * 12 = 25.5 * 12 = 306.0")
    
    # Check if sum is EXACTLY equal to 306.0
    expected_sum = 306.0
    is_exact_match = abs(total_sum - expected_sum) < 0.01  # Allow for floating point precision
    difference = total_sum - expected_sum
    
    # Check bet diversity - should have DIFFERENT amounts, not all the same
    unique_amounts = len(set(bet_amounts))
    has_diversity = unique_amounts > 1
    
    print(f"   🔍 BET DIVERSITY CHECK:")
    print(f"      Уникальных сумм ставок: {unique_amounts} из {bet_count}")
    print(f"      Individual bet amounts: {sorted(bet_amounts)}")
    
    if is_exact_match and has_diversity:
        record_test(
            "CRITICAL Exact Cycle Sum Test",
            True,
            f"✅ ARCHITECTURAL SUCCESS! Perfect exact sum match: {total_sum:.1f} = 306.0, {unique_amounts} different bet amounts"
        )
    elif is_exact_match and not has_diversity:
        record_test(
            "CRITICAL Exact Cycle Sum Test",
            False,
            f"⚠️ Sum correct ({total_sum:.1f}) but no bet diversity - all bets same amount"
        )
    elif not is_exact_match and has_diversity:
        record_test(
            "CRITICAL Exact Cycle Sum Test",
            False,
            f"🚨 ARCHITECTURAL FAILURE! Sum mismatch: Got ${total_sum:.1f} instead of $306.0 (diff: {difference:+.1f})"
        )
    else:
        record_test(
            "CRITICAL Exact Cycle Sum Test",
            False,
            f"🚨 DOUBLE FAILURE! Wrong sum (${total_sum:.1f}) AND no bet diversity"
        )
    
    return is_exact_match, total_sum

def test_backend_logs_analysis():
    """Test 4: Искать специфические сообщения из русского обзора"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Searching for Specific Russian Review Log Messages{Colors.END}")
    
    try:
        # Try to read supervisor logs for backend
        import subprocess
        
        # Get recent backend logs
        result = subprocess.run(
            ["tail", "-n", "500", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for SPECIFIC messages from Russian review
            creating_complete_cycle_msgs = log_content.count("Creating complete cycle - 12 bets with exact total 306")
            architectural_success_msgs = log_content.count("ARCHITECTURAL SUCCESS! Perfect exact sum match!")
            created_complete_cycle_msgs = log_content.count("Created complete cycle - 12/12 bets")
            total_bet_amounts_306_msgs = log_content.count("Total bet amounts = 306")
            general_perfect_matches = log_content.count("✅ PERFECT MATCH!")
            http_500_errors = log_content.count("HTTP 500")
            
            print(f"   📋 Russian Review Specific Log Messages:")
            print(f"      🎯 'Creating complete cycle - 12 bets with exact total 306': {creating_complete_cycle_msgs}")
            print(f"      🎯 'ARCHITECTURAL SUCCESS! Perfect exact sum match!': {architectural_success_msgs}")
            print(f"      🎯 'Created complete cycle - 12/12 bets': {created_complete_cycle_msgs}")
            print(f"      🎯 'Total bet amounts = 306': {total_bet_amounts_306_msgs}")
            print(f"      ✅ General 'PERFECT MATCH!' messages: {general_perfect_matches}")
            print(f"      ❌ HTTP 500 errors: {http_500_errors}")
            
            # Success criteria: should have specific Russian review messages and no HTTP 500 errors
            has_specific_messages = (creating_complete_cycle_msgs > 0 or 
                                   architectural_success_msgs > 0 or 
                                   created_complete_cycle_msgs > 0 or
                                   total_bet_amounts_306_msgs > 0)
            has_any_success_messages = has_specific_messages or general_perfect_matches > 0
            no_http_errors = http_500_errors == 0
            
            total_specific_msgs = (creating_complete_cycle_msgs + architectural_success_msgs + 
                                 created_complete_cycle_msgs + total_bet_amounts_306_msgs)
            
            if has_specific_messages and no_http_errors:
                record_test(
                    "Russian Review Backend Logs Analysis",
                    True,
                    f"Found {total_specific_msgs} specific Russian review messages and no HTTP 500 errors"
                )
            elif has_any_success_messages and no_http_errors:
                record_test(
                    "Russian Review Backend Logs Analysis",
                    False,
                    f"Found general success messages ({general_perfect_matches}) but no specific Russian review messages"
                )
            elif has_specific_messages and not no_http_errors:
                record_test(
                    "Russian Review Backend Logs Analysis",
                    False,
                    f"Found specific messages but also {http_500_errors} HTTP 500 errors"
                )
            else:
                record_test(
                    "Russian Review Backend Logs Analysis",
                    False,
                    f"No specific Russian review messages found and {http_500_errors} HTTP 500 errors detected"
                )
            
            # Show some relevant log lines
            success_lines = []
            for line in log_content.split('\n'):
                if any(keyword in line for keyword in [
                    "Creating complete cycle - 12 bets with exact total 306",
                    "ARCHITECTURAL SUCCESS! Perfect exact sum match!",
                    "Created complete cycle - 12/12 bets",
                    "Total bet amounts = 306"
                ]):
                    success_lines.append(line.strip())
            
            if success_lines:
                print(f"   📝 Recent Russian review specific log lines:")
                for line in success_lines[-5:]:  # Show last 5 relevant lines
                    print(f"      {line}")
            else:
                print(f"   ⚠️ No specific Russian review log messages found in recent logs")
                    
        else:
            record_test(
                "Russian Review Backend Logs Analysis",
                False,
                f"Failed to read backend logs: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        record_test("Russian Review Backend Logs Analysis", False, "Timeout reading backend logs")
    except Exception as e:
        record_test("Russian Review Backend Logs Analysis", False, f"Error reading logs: {str(e)}")

def print_russian_review_summary():
    """Print Russian Review testing specific summary"""
    print_header("RUSSIAN REVIEW - THREE CRITICAL ISSUES TESTING SUMMARY")
    
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
    
    # Check each critical issue
    cache_test = next((test for test in test_results["tests"] if "clear cache" in test["name"].lower()), None)
    cycle_test = next((test for test in test_results["tests"] if "cycle logic" in test["name"].lower()), None)
    sum_test = next((test for test in test_results["tests"] if "exact cycle sum" in test["name"].lower()), None)
    logs_test = next((test for test in test_results["tests"] if "backend logs" in test["name"].lower()), None)
    
    issues = [
        ("1. КНОПКА ОЧИСТКИ КЭША", cache_test),
        ("2. ЛОГИКА REGULAR БОТОВ - ЦИКЛЫ", cycle_test),
        ("3. ТОЧНОЕ СОВПАДЕНИЕ СУММЫ ЦИКЛА", sum_test),
        ("4. ЛОГИ BACKEND", logs_test)
    ]
    
    for issue_name, test in issues:
        if test:
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
            print(f"   {issue_name}: {status}")
            if test["details"]:
                print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
        else:
            print(f"   {issue_name}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: ALL THREE CRITICAL ISSUES ARE WORKING!{Colors.END}")
        print(f"{Colors.GREEN}✅ Кнопка очистки кэша работает{Colors.END}")
        print(f"{Colors.GREEN}✅ Regular боты создают ровно 12 ставок{Colors.END}")
        print(f"{Colors.GREEN}✅ Сумма цикла точно равна 306.0{Colors.END}")
        print(f"{Colors.GREEN}✅ Логи показывают успешные сообщения{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOST ISSUES FIXED ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Большинство критических проблем решены, но есть минорные проблемы.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые критические проблемы решены, но требуется дополнительная работа.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: CRITICAL ISSUES REMAIN ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Большинство критических проблем НЕ решены. Требуется срочное исправление.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    if cache_test and not cache_test["success"]:
        print(f"   🔴 Clear cache button needs fixing")
    if cycle_test and not cycle_test["success"]:
        print(f"   🔴 Regular bot cycle logic needs fixing - bots not creating exactly 12 bets")
    if sum_test and not sum_test["success"]:
        print(f"   🔴 CRITICAL: Exact cycle sum matching is NOT working - sum ≠ 306.0")
    if logs_test and not logs_test["success"]:
        print(f"   🔴 Backend logs don't show success messages")
    
    if success_rate == 100:
        print(f"   🟢 All critical issues are resolved - system ready for production")
        print(f"   ✅ Main agent can summarize and finish")
    else:
        print(f"   🔧 Fix remaining issues before considering system complete")

def main():
    """Main test execution for Russian Review - Final Architecture Test"""
    print_header("RUSSIAN REVIEW - FINAL ARCHITECTURE TEST")
    print(f"{Colors.BLUE}🎯 Testing ИСПРАВЛЕННУЮ систему создания полных циклов ставок{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 CRITICAL REQUIREMENT: Sum of all bet_amount MUST = EXACTLY 306.0{Colors.END}")
    print(f"{Colors.BLUE}📐 Calculation: (1+50)/2 * 12 = 25.5 * 12 = 306.0{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: Clear Cache Button (brief check)
        test_clear_cache_button()
        
        # Test 2: Create Final_Architecture_Test_Bot + Test 3: Exact Sum Matching
        bot_id, bot_games = test_regular_bot_cycle_logic()
        if bot_id and bot_games:
            test_exact_cycle_sum_matching(bot_id, bot_games)
        
        # Test 4: Backend Logs Analysis for specific Russian review messages
        test_backend_logs_analysis()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_russian_review_summary()

if __name__ == "__main__":
    main()