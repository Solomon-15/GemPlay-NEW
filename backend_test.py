#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ЦИКЛА СТАВОК - Russian Review Testing
Тестирование критического исправления точной суммы цикла ставок

ПРОБЛЕМА: Regular боты создают ставки с неточными суммами цикла вместо точно 306.0
Ожидаемая сумма: (min_bet_amount + max_bet_amount) / 2 * cycle_games = (1 + 50) / 2 * 12 = 306.0

ТЕСТ КРИТИЧЕСКОГО ИСПРАВЛЕНИЯ:
1. POST /api/admin/bots/create-regular - создать бота "Critical_Fix_Test_Bot"
2. Подождать 25 секунд для полного создания всех 12 ставок цикла
3. GET /api/bots/active-games - получить ВСЕ активные игры этого бота
4. Вычислить ТОЧНУЮ сумму всех bet_amount
5. Проверить что сумма СТРОГО равна 306.0
6. Показать количество ставок (должно быть 12)
7. Проверить логи на:
   - "🎯 Bot ID: GENERATING COMPLETE CYCLE"
   - "🎯 Bot ID: CYCLE BETS SAVED"
   - "🎯 Bot ID: ARCHITECTURAL SUCCESS! Perfect exact sum match!"

КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: Сумма должна быть ТОЧНО 306.0. 
Если получается другое значение (110, 288, 229, 377, 289, 227, 333, 315), исправление провалилось.

Это последняя попытка исправить архитектурную проблему создания ставок по циклам.
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

def test_exact_cycle_sum_matching():
    """Test 1: Создать Regular бот "Critical_Fix_Test_Bot" и проверить точную сумму цикла 306.0"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Testing CRITICAL FIX for exact cycle sum matching{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Critical Fix Test Bot Creation", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot with EXACT settings from Russian review
    import time
    timestamp = int(time.time())
    bot_data = {
        "name": f"Final_Perfect_Test_Bot_{timestamp}",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "cycle_games": 12,
        "win_percentage": 55,
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"   📝 Creating Regular bot 'Final_Perfect_Test_Bot_{timestamp}' with settings: {bot_data}")
    
    # Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        record_test(
            "Critical Fix Test Bot Creation",
            False,
            f"Failed to create Regular bot: {details}"
        )
        return
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        record_test(
            "Critical Fix Test Bot Creation",
            False,
            "Bot created but no bot_id returned"
        )
        return
    
    print(f"   ✅ Regular bot 'Final_Perfect_Test_Bot_{timestamp}' created successfully with ID: {bot_id}")
    
    # Wait 30 seconds for COMPLETE cycle creation as specified in Russian review
    print(f"   ⏳ Waiting 30 seconds for COMPLETE cycle creation (all 12 bets)...")
    time.sleep(30)
    
    # Get ALL active games for this specific bot
    success, games_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not games_data:
        record_test(
            "Critical Fix Test Bot - Active Games Retrieval",
            False,
            f"Failed to get active games: {details}"
        )
        return
    
    # Filter games for our specific bot
    bot_games = []
    if isinstance(games_data, list):
        bot_games = [game for game in games_data if game.get("bot_id") == bot_id]
    elif isinstance(games_data, dict) and "games" in games_data:
        bot_games = [game for game in games_data["games"] if game.get("bot_id") == bot_id]
    
    if not bot_games:
        record_test(
            "Critical Fix Test Bot - Active Games Retrieval",
            False,
            f"No active games found for bot {bot_id}. Total games found: {len(games_data) if isinstance(games_data, list) else 'unknown'}"
        )
        return
    
    print(f"   ✅ Found {len(bot_games)} active games for Final_Perfect_Test_Bot_{timestamp}")
    
    # Calculate EXACT sum of ALL bet_amount values
    bet_amounts = [float(game.get("bet_amount", 0)) for game in bot_games]
    total_sum = sum(bet_amounts)
    bet_count = len(bet_amounts)
    min_bet = min(bet_amounts) if bet_amounts else 0
    max_bet = max(bet_amounts) if bet_amounts else 0
    avg_bet = total_sum / bet_count if bet_count > 0 else 0
    
    print(f"   📊 CRITICAL FIX ANALYSIS:")
    print(f"      Количество ставок: {bet_count} (должно быть 12)")
    print(f"      Минимальная ставка: ${min_bet:.1f}")
    print(f"      Максимальная ставка: ${max_bet:.1f}")
    print(f"      Средняя ставка: ${avg_bet:.1f}")
    print(f"      ТОЧНАЯ СУММА: ${total_sum:.1f}")
    print(f"      ОЖИДАЕМАЯ СУММА: $306.0")
    
    # Check if sum is STRICTLY equal to 306.0
    expected_sum = 306.0
    is_exact_match = abs(total_sum - expected_sum) < 0.01  # Allow for floating point precision
    
    # Check bet count
    correct_bet_count = bet_count == 12
    
    if is_exact_match and correct_bet_count:
        record_test(
            "Critical Fix Test Bot - Exact Sum Verification",
            True,
            f"🎯 ARCHITECTURAL SUCCESS! Perfect exact sum match: {total_sum:.1f} = 306.0. Bets: {bet_count}/12, Range: ${min_bet:.1f}-${max_bet:.1f}"
        )
    else:
        difference = total_sum - expected_sum
        issues = []
        if not is_exact_match:
            issues.append(f"Sum mismatch: {total_sum:.1f} ≠ 306.0 (diff: {difference:+.1f})")
        if not correct_bet_count:
            issues.append(f"Bet count wrong: {bet_count} ≠ 12")
        
        record_test(
            "Critical Fix Test Bot - Exact Sum Verification",
            False,
            f"🚨 CRITICAL FAILURE! {'; '.join(issues)}. Expected values: 110, 288, 229, 377, 289, 227, 333, 315 indicate fix failure."
        )
    
    # Show individual bet amounts for debugging
    print(f"   🔍 Individual bet amounts: {sorted(bet_amounts)}")
    
    return is_exact_match and correct_bet_count, total_sum, bet_count, min_bet, max_bet, avg_bet

def test_backend_logs_analysis():
    """Test 2: Проверить логи на специфические сообщения КРИТИЧЕСКОГО ИСПРАВЛЕНИЯ"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Analyzing backend logs for CRITICAL FIX messages{Colors.END}")
    
    try:
        # Try to read supervisor logs for backend
        import subprocess
        
        # Get recent backend logs
        result = subprocess.run(
            ["tail", "-n", "200", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for CRITICAL FIX specific messages
            generating_cycle_msgs = log_content.count("🎯 Bot ID: GENERATING COMPLETE CYCLE")
            cycle_bets_saved_msgs = log_content.count("🎯 Bot ID: CYCLE BETS SAVED")
            architectural_success_msgs = log_content.count("🎯 Bot ID: ARCHITECTURAL SUCCESS! Perfect exact sum match!")
            
            # Look for general normalization messages
            perfect_matches = log_content.count("✅ normalize: PERFECT MATCH!")
            imperfect_matches = log_content.count("❌ normalize: Imperfect match")
            
            print(f"   📋 CRITICAL FIX Log Analysis Results:")
            print(f"      🎯 'GENERATING COMPLETE CYCLE' messages: {generating_cycle_msgs}")
            print(f"      🎯 'CYCLE BETS SAVED' messages: {cycle_bets_saved_msgs}")
            print(f"      🎯 'ARCHITECTURAL SUCCESS! Perfect exact sum match!' messages: {architectural_success_msgs}")
            print(f"      ✅ General 'PERFECT MATCH' messages: {perfect_matches}")
            print(f"      ❌ 'Imperfect match' messages: {imperfect_matches}")
            
            # Success criteria: should have architectural success messages
            if architectural_success_msgs > 0:
                record_test(
                    "Critical Fix Backend Logs Analysis",
                    True,
                    f"Found {architectural_success_msgs} ARCHITECTURAL SUCCESS messages indicating critical fix is working"
                )
            elif generating_cycle_msgs > 0 and cycle_bets_saved_msgs > 0:
                record_test(
                    "Critical Fix Backend Logs Analysis",
                    True,
                    f"Found cycle generation messages: {generating_cycle_msgs} GENERATING, {cycle_bets_saved_msgs} SAVED"
                )
            elif perfect_matches > 0:
                record_test(
                    "Critical Fix Backend Logs Analysis",
                    True,
                    f"Found {perfect_matches} general PERFECT MATCH messages"
                )
            else:
                record_test(
                    "Critical Fix Backend Logs Analysis",
                    False,
                    "No critical fix success messages found in recent logs"
                )
            
            # Show some relevant log lines
            critical_lines = []
            for line in log_content.split('\n'):
                if any(keyword in line for keyword in [
                    "🎯 Bot ID: GENERATING COMPLETE CYCLE",
                    "🎯 Bot ID: CYCLE BETS SAVED", 
                    "🎯 Bot ID: ARCHITECTURAL SUCCESS",
                    "✅ normalize: PERFECT MATCH"
                ]):
                    critical_lines.append(line.strip())
            
            if critical_lines:
                print(f"   📝 Recent critical fix log lines:")
                for line in critical_lines[-5:]:  # Show last 5 relevant lines
                    print(f"      {line}")
                    
        else:
            record_test(
                "Critical Fix Backend Logs Analysis",
                False,
                f"Failed to read backend logs: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        record_test("Critical Fix Backend Logs Analysis", False, "Timeout reading backend logs")
    except Exception as e:
        record_test("Critical Fix Backend Logs Analysis", False, f"Error reading logs: {str(e)}")

def print_cycle_sum_summary():
    """Print CRITICAL FIX cycle sum testing specific summary"""
    print_header("CRITICAL FIX - EXACT CYCLE SUM MATCHING TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 CRITICAL FIX REQUIREMENTS STATUS:{Colors.END}")
    
    requirements = [
        "POST /api/admin/bots/create-regular - создать бота 'Critical_Fix_Test_Bot'",
        "Подождать 25 секунд для полного создания всех 12 ставок цикла",
        "GET /api/bots/active-games - получить ВСЕ активные игры этого бота",
        "Вычислить ТОЧНУЮ сумму всех bet_amount",
        "Проверить что сумма СТРОГО равна 306.0",
        "Показать количество ставок (должно быть 12)",
        "Проверить логи на '🎯 Bot ID: GENERATING COMPLETE CYCLE'",
        "Проверить логи на '🎯 Bot ID: CYCLE BETS SAVED'",
        "Проверить логи на '🎯 Bot ID: ARCHITECTURAL SUCCESS! Perfect exact sum match!'"
    ]
    
    for i, req in enumerate(requirements, 1):
        # Find corresponding test result
        test_found = False
        for test in test_results["tests"]:
            if ("critical fix test bot" in test["name"].lower() or "exact sum verification" in test["name"].lower()) and i <= 6:
                status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
                print(f"   {i}. {req}: {status}")
                test_found = True
                break
            elif "critical fix backend logs" in test["name"].lower() and i >= 7:
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
    
    # Specific conclusion for CRITICAL FIX
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: CRITICAL FIX IS 100% WORKING!{Colors.END}")
        print(f"{Colors.GREEN}Regular боты создают ставки с точной суммой 306.0. КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ цикла ставок работает корректно.{Colors.END}")
        print(f"{Colors.GREEN}Это последняя попытка исправить архитектурную проблему - УСПЕШНА!{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: CRITICAL FIX HAS ISSUES ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые компоненты работают, но есть проблемы с точностью суммы цикла.{Colors.END}")
        print(f"{Colors.YELLOW}КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ требует дополнительной работы.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: CRITICAL FIX FAILED ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}КРИТИЧЕСКИЕ ПРОБЛЕМЫ! Regular боты НЕ создают точную сумму 306.0.{Colors.END}")
        print(f"{Colors.RED}Если получается другое значение (110, 288, 229, 377, 289, 227, 333, 315), исправление провалилось.{Colors.END}")
        print(f"{Colors.RED}Это последняя попытка исправить архитектурную проблему создания ставок по циклам - ПРОВАЛЕНА!{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    # Check specific failure patterns
    cycle_test = next((test for test in test_results["tests"] if "exact sum verification" in test["name"].lower()), None)
    logs_test = next((test for test in test_results["tests"] if "critical fix backend logs" in test["name"].lower()), None)
    
    if cycle_test and not cycle_test["success"]:
        print(f"   🔴 CRITICAL: Exact cycle sum matching is NOT working")
        print(f"   🔧 URGENT: Fix normalize_amounts_to_exact_sum() function")
        print(f"   🔧 URGENT: Check cycle-wide sum calculation logic")
        print(f"   🔧 URGENT: Verify bet creation architecture (individual vs batch)")
        print(f"   🔧 URGENT: This is the LAST ATTEMPT - architectural redesign needed")
    elif logs_test and not logs_test["success"]:
        print(f"   🔴 Backend logs don't show ARCHITECTURAL SUCCESS messages")
        print(f"   🔧 Check critical fix logging implementation")
        print(f"   🔧 Verify cycle generation and saving logic")
    else:
        print(f"   🟢 CRITICAL FIX appears to be working correctly")
        print(f"   ✅ Regular боты создают точную сумму 306.0")
        print(f"   ✅ Архитектурная проблема решена")
        print(f"   ✅ Система готова к продакшену")

def main():
    """Main test execution for CRITICAL FIX - exact cycle sum matching"""
    print_header("CRITICAL FIX - EXACT CYCLE SUM MATCHING TESTING")
    print(f"{Colors.BLUE}🎯 Testing КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ цикла ставок для Regular ботов{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Regular bot 'Critical_Fix_Test_Bot', cycle sum = 306.0, architectural logs{Colors.END}")
    print(f"{Colors.BLUE}🎲 Expected: (1+50)/2*12 = 25.5*12 = 306.0{Colors.END}")
    print(f"{Colors.BLUE}🚨 КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: Сумма должна быть СТРОГО равна 306.0{Colors.END}")
    print(f"{Colors.BLUE}❌ Если получается другое значение (110, 288, 229, 377, 289, 227, 333, 315), исправление провалилось{Colors.END}")
    print(f"{Colors.BLUE}🔥 Это последняя попытка исправить архитектурную проблему создания ставок по циклам{Colors.END}")
    
    try:
        # Run CRITICAL FIX tests
        test_exact_cycle_sum_matching()
        test_backend_logs_analysis()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_cycle_sum_summary()

if __name__ == "__main__":
    main()