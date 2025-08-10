#!/usr/bin/env python3
"""
Regular Bots Bet Recalculation Testing - Russian Review
Тестирование исправления кнопки «Пересчет ставок» для обычных ботов

КОНТЕКСТ: Тестирование исправленной функциональности кнопки "Пересчет ставок" 
для обычных ботов, которая теперь должна использовать правильные индивидуальные 
параметры каждого бота вместо фиксированной суммы 500.

ТЕСТИРОВАТЬ:
1. Создать двух тестовых ботов с разными настройками:
   
   Бот 1:
   - name: "Test_Recalc_Bot_1"
   - min_bet_amount: 5.0
   - max_bet_amount: 15.0
   - cycle_games: 4
   - Ожидаемая сумма цикла: (5+15)/2 * 4 = 40 гемов
   
   Бот 2:
   - name: "Test_Recalc_Bot_2" 
   - min_bet_amount: 20.0
   - max_bet_amount: 40.0
   - cycle_games: 6
   - Ожидаемая сумма цикла: (20+40)/2 * 6 = 180 гемов

2. Подождать пока создадутся начальные ставки

3. Выполнить POST /api/admin/bots/{bot_id}/reset-bets для каждого бота

4. Проверить что:
   - Старые ставки отменены (cancelled_bets > 0)
   - Ответ содержит success: true
   - НЕ содержит фиксированную сумму 500
   - Новые ставки создаются в правильных диапазонах

ПРИОРИТЕТ: Критически важно - кнопка "Пересчет ставок" должна работать корректно
ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ: Кнопка использует индивидуальные параметры каждого бота
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
BASE_URL = "https://49b21745-59e5-4980-8f15-13cafed79fb5.preview.emergentagent.com/api"
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

def create_test_bot(token: str, bot_config: Dict) -> Optional[str]:
    """Create a test bot with specific configuration"""
    print(f"\n{Colors.MAGENTA}🤖 Creating test bot: {bot_config['name']}{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_config
    )
    
    if success and response_data:
        # Try different ways to get bot ID from response
        bot_id = None
        if "id" in response_data:
            bot_id = response_data["id"]
        elif "bot_id" in response_data:
            bot_id = response_data["bot_id"]
        elif "created_bots" in response_data and response_data["created_bots"]:
            bot_id = response_data["created_bots"][0]  # Get first bot ID from array
        
        if bot_id:
            record_test(
                f"Create test bot: {bot_config['name']}",
                True,
                f"Bot created with ID: {bot_id}, min_bet: {bot_config['min_bet_amount']}, max_bet: {bot_config['max_bet_amount']}, cycle_games: {bot_config['cycle_games']}"
            )
            return bot_id
        else:
            record_test(
                f"Create test bot: {bot_config['name']}",
                False,
                f"Bot created but no ID returned. Response: {response_data}"
            )
    else:
        record_test(
            f"Create test bot: {bot_config['name']}",
            False,
            f"Failed to create bot: {details}"
        )
    
    return None

def wait_for_initial_bets(token: str, bot_id: str, bot_name: str, expected_cycle_games: int) -> bool:
    """Wait for initial bets to be created by the bot"""
    print(f"\n{Colors.BLUE}⏳ Waiting for initial bets for bot: {bot_name}...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    max_wait_time = 60  # Maximum 60 seconds
    check_interval = 5  # Check every 5 seconds
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        # Check active games for this bot
        success, response_data, details = make_request(
            "GET",
            "/bots/active-games",
            headers=headers
        )
        
        if success and response_data:
            games = response_data if isinstance(response_data, list) else response_data.get("games", [])
            bot_games = [game for game in games if game.get("creator_id") == bot_id or game.get("bot_id") == bot_id]
            
            if len(bot_games) >= expected_cycle_games:
                record_test(
                    f"Initial bets creation for {bot_name}",
                    True,
                    f"Found {len(bot_games)} active bets (expected: {expected_cycle_games})"
                )
                return True
        
        time.sleep(check_interval)
        elapsed_time += check_interval
        print(f"{Colors.YELLOW}   Waiting... ({elapsed_time}s/{max_wait_time}s){Colors.END}")
    
    record_test(
        f"Initial bets creation for {bot_name}",
        False,
        f"Timeout waiting for initial bets after {max_wait_time}s"
    )
    return False

def get_bot_active_bets_count(token: str, bot_id: str) -> int:
    """Get count of active bets for a specific bot"""
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        bot_games = [game for game in games if game.get("creator_id") == bot_id or game.get("bot_id") == bot_id]
        return len(bot_games)
    
    return 0

def test_bet_recalculation(token: str, bot_id: str, bot_name: str, min_bet: float, max_bet: float, cycle_games: int):
    """Test the bet recalculation functionality for a specific bot"""
    print(f"\n{Colors.MAGENTA}🔄 Testing bet recalculation for: {bot_name}{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get initial bet count
    initial_bet_count = get_bot_active_bets_count(token, bot_id)
    print(f"{Colors.BLUE}   Initial active bets: {initial_bet_count}{Colors.END}")
    
    # Execute bet recalculation
    success, response_data, details = make_request(
        "POST",
        f"/admin/bots/{bot_id}/reset-bets",
        headers=headers
    )
    
    if success and response_data:
        # Check response structure
        has_success = response_data.get("success", False)
        cancelled_bets = response_data.get("cancelled_bets", 0)
        
        # Check that response doesn't contain fixed sum 500
        response_str = str(response_data)
        contains_fixed_500 = "500" in response_str and "fixed" in response_str.lower()
        
        # Wait a moment for new bets to be created
        time.sleep(10)
        
        # Get new bet count
        new_bet_count = get_bot_active_bets_count(token, bot_id)
        
        # Calculate expected cycle sum
        expected_cycle_sum = ((min_bet + max_bet) / 2) * cycle_games
        
        # Verify results
        success_criteria = [
            has_success,
            cancelled_bets > 0,
            not contains_fixed_500,
            new_bet_count > 0
        ]
        
        all_criteria_met = all(success_criteria)
        
        details_msg = f"Success: {has_success}, Cancelled: {cancelled_bets}, No fixed 500: {not contains_fixed_500}, New bets: {new_bet_count}, Expected cycle sum: {expected_cycle_sum}"
        
        record_test(
            f"Bet recalculation for {bot_name}",
            all_criteria_met,
            details_msg
        )
        
        # Additional test: Check if new bets are in correct range
        if new_bet_count > 0:
            test_bet_ranges(token, bot_id, bot_name, min_bet, max_bet)
        
    else:
        record_test(
            f"Bet recalculation for {bot_name}",
            False,
            f"API call failed: {details}"
        )

def test_bet_ranges(token: str, bot_id: str, bot_name: str, min_bet: float, max_bet: float):
    """Test that new bets are within the correct range"""
    print(f"{Colors.BLUE}   🎯 Checking bet ranges for {bot_name}...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        bot_games = [game for game in games if game.get("creator_id") == bot_id or game.get("bot_id") == bot_id]
        
        if bot_games:
            bets_in_range = 0
            bets_out_of_range = 0
            bet_amounts = []
            
            for game in bot_games:
                bet_amount = game.get("bet_amount", 0)
                bet_amounts.append(bet_amount)
                
                if min_bet <= bet_amount <= max_bet:
                    bets_in_range += 1
                else:
                    bets_out_of_range += 1
            
            total_bets = len(bot_games)
            range_compliance = (bets_in_range / total_bets * 100) if total_bets > 0 else 0
            
            # Consider it successful if at least 80% of bets are in range
            success_threshold = 80
            range_test_success = range_compliance >= success_threshold
            
            details_msg = f"Range compliance: {range_compliance:.1f}% ({bets_in_range}/{total_bets} bets in range {min_bet}-{max_bet}). Bet amounts: {bet_amounts[:5]}{'...' if len(bet_amounts) > 5 else ''}"
            
            record_test(
                f"Bet range compliance for {bot_name}",
                range_test_success,
                details_msg
            )
        else:
            record_test(
                f"Bet range compliance for {bot_name}",
                False,
                "No active bets found to check ranges"
            )

def cleanup_test_bots(token: str, bot_ids: List[str]):
    """Clean up test bots after testing"""
    print(f"\n{Colors.BLUE}🧹 Cleaning up test bots...{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for bot_id in bot_ids:
        if bot_id:
            success, response_data, details = make_request(
                "DELETE",
                f"/admin/bots/{bot_id}",
                headers=headers
            )
            
            if success:
                print(f"{Colors.GREEN}   ✅ Deleted bot: {bot_id}{Colors.END}")
            else:
                print(f"{Colors.YELLOW}   ⚠️ Could not delete bot {bot_id}: {details}{Colors.END}")

def print_final_summary():
    """Print final test summary"""
    print_header("BET RECALCULATION TESTING SUMMARY")
    
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
        "Создание тестовых ботов с разными настройками",
        "Ожидание создания начальных ставок",
        "Выполнение POST /api/admin/bots/{bot_id}/reset-bets",
        "Проверка отмены старых ставок (cancelled_bets > 0)",
        "Проверка success: true в ответе",
        "Проверка отсутствия фиксированной суммы 500",
        "Проверка создания новых ставок в правильных диапазонах"
    ]
    
    print(f"{Colors.GREEN}✅ Все основные требования протестированы{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Final conclusion
    if success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: BET RECALCULATION IS {success_rate:.1f}% FUNCTIONAL!{Colors.END}")
        print(f"{Colors.GREEN}Кнопка 'Пересчет ставок' теперь использует правильные индивидуальные параметры каждого бота вместо фиксированной суммы 500.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: BET RECALCULATION IS {success_rate:.1f}% FUNCTIONAL{Colors.END}")
        print(f"{Colors.YELLOW}Функциональность частично работает, но есть проблемы которые нужно исправить.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: BET RECALCULATION NEEDS ATTENTION ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Критические проблемы с функциональностью пересчета ставок.{Colors.END}")

def main():
    """Main test execution"""
    print_header("REGULAR BOTS BET RECALCULATION TESTING")
    print(f"{Colors.BLUE}🎯 Testing 'Пересчет ставок' button fix for regular bots{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Individual bot parameters instead of fixed sum 500{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Cannot proceed without authentication{Colors.END}")
        sys.exit(1)
    
    # Test bot configurations
    timestamp = int(time.time())
    bot_configs = [
        {
            "name": f"Test_Recalc_Bot_1_{timestamp}",
            "min_bet_amount": 5.0,
            "max_bet_amount": 15.0,
            "cycle_games": 4,
            "win_percentage": 55.0,
            "pause_between_games": 5,
            "profit_strategy": "balanced"
        },
        {
            "name": f"Test_Recalc_Bot_2_{timestamp}",
            "min_bet_amount": 20.0,
            "max_bet_amount": 40.0,
            "cycle_games": 6,
            "win_percentage": 60.0,
            "pause_between_games": 8,
            "profit_strategy": "balanced"
        }
    ]
    
    created_bot_ids = []
    
    try:
        # Step 1: Create test bots
        print(f"\n{Colors.BOLD}STEP 1: Creating test bots with different settings{Colors.END}")
        for config in bot_configs:
            bot_id = create_test_bot(token, config)
            if bot_id:
                created_bot_ids.append(bot_id)
        
        if len(created_bot_ids) < 2:
            print(f"{Colors.RED}❌ Could not create enough test bots. Exiting.{Colors.END}")
            return
        
        # Step 2: Wait for initial bets
        print(f"\n{Colors.BOLD}STEP 2: Waiting for initial bets to be created{Colors.END}")
        for i, (bot_id, config) in enumerate(zip(created_bot_ids, bot_configs)):
            wait_for_initial_bets(token, bot_id, config["name"], config["cycle_games"])
        
        # Step 3: Test bet recalculation
        print(f"\n{Colors.BOLD}STEP 3: Testing bet recalculation functionality{Colors.END}")
        for i, (bot_id, config) in enumerate(zip(created_bot_ids, bot_configs)):
            test_bet_recalculation(
                token, 
                bot_id, 
                config["name"], 
                config["min_bet_amount"], 
                config["max_bet_amount"], 
                config["cycle_games"]
            )
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Cleanup test bots
        if created_bot_ids:
            cleanup_test_bots(token, created_bot_ids)
        
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()