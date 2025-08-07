#!/usr/bin/env python3
"""
Regular Bots Bet Range Generation Testing - Russian Review
Тестирование исправления генерации ставок обычных ботов в диапазоне min_bet_amount и max_bet_amount

КОНТЕКСТ: Тестирование исправления генерации ставок обычных ботов для проверки что ставки 
создаются в правильном диапазоне min_bet_amount и max_bet_amount.

ТЕСТИРОВАТЬ:
1. Создать обычного бота с настройками:
   - name: "Test_Bet_Range_Bot"  
   - min_bet_amount: 10.0
   - max_bet_amount: 30.0
   - win_percentage: 55
   - cycle_games: 5

2. Проверить что бот создался и его активные ставки находятся в диапазоне 10-30 гемов:
   - Получить список активных игр через GET /api/bots/active-games
   - Найти игры созданные этим ботом
   - Проверить что bet_amount каждой игры между 10.0 и 30.0
   - Убедиться что создано 5 активных ставок (cycle_games)

3. Если нашли ставки вне диапазона - показать детали для диагностики

ПРИОРИТЕТ: Критически важно - это исправление генерации ставок ботов
ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ: Все ставки должны быть в диапазоне 10.0-30.0 гемов
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
BASE_URL = "https://5a0f72db-7197-4535-89b4-f85be852ec00.preview.emergentagent.com/api"
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

def test_create_bet_range_bot(token: str) -> Optional[str]:
    """Test 1: Create Regular Bot with specific bet range settings"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Creating Test_Bet_Range_Bot with min_bet=10.0, max_bet=30.0{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Exact bot data as specified in Russian review
    bot_data = {
        "name": "Test_Bet_Range_Bot",
        "min_bet_amount": 10.0,
        "max_bet_amount": 30.0,
        "win_percentage": 55,
        "cycle_games": 5
    }
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if success and response_data:
        bot_id = response_data.get("id") or response_data.get("bot_id")
        if bot_id:
            record_test(
                "Create Test_Bet_Range_Bot",
                True,
                f"Bot created successfully with ID: {bot_id}, min_bet: {bot_data['min_bet_amount']}, max_bet: {bot_data['max_bet_amount']}, cycle_games: {bot_data['cycle_games']}"
            )
            return bot_id
        else:
            record_test(
                "Create Test_Bet_Range_Bot",
                False,
                f"Bot created but no ID returned. Response: {response_data}"
            )
    else:
        record_test(
            "Create Test_Bet_Range_Bot",
            False,
            f"Failed to create bot: {details}"
        )
    
    return None

def test_bot_active_games_range(token: str, bot_id: str = None):
    """Test 2: Check that bot's active games are in the correct bet range (10.0-30.0)"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Checking active games bet amounts are in range 10.0-30.0{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Wait a moment for bot to create initial bets
    print(f"{Colors.BLUE}⏳ Waiting 5 seconds for bot to create initial cycle bets...{Colors.END}")
    time.sleep(5)
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        if games:
            # Find games created by our test bot
            test_bot_games = []
            for game in games:
                # Check if this game was created by our test bot
                creator_name = game.get("creator_name", "")
                if creator_name == "Test_Bet_Range_Bot" or (bot_id and game.get("creator_id") == bot_id):
                    test_bot_games.append(game)
            
            if test_bot_games:
                print(f"{Colors.BLUE}📊 Found {len(test_bot_games)} games created by Test_Bet_Range_Bot{Colors.END}")
                
                # Check bet amounts are in range
                in_range_count = 0
                out_of_range_games = []
                bet_amounts = []
                
                for game in test_bot_games:
                    bet_amount = game.get("bet_amount", 0)
                    bet_amounts.append(bet_amount)
                    
                    if 10.0 <= bet_amount <= 30.0:
                        in_range_count += 1
                    else:
                        out_of_range_games.append({
                            "game_id": game.get("id", "unknown"),
                            "bet_amount": bet_amount,
                            "status": game.get("status", "unknown"),
                            "created_at": game.get("created_at", "unknown")
                        })
                
                # Check if we have expected number of games (5 cycle_games)
                expected_games = 5
                games_count_ok = len(test_bot_games) == expected_games
                
                # Check if all bets are in range
                all_in_range = len(out_of_range_games) == 0
                
                if all_in_range and games_count_ok:
                    record_test(
                        "Bot bet amounts in correct range (10.0-30.0)",
                        True,
                        f"All {len(test_bot_games)} games have bet amounts in range 10.0-30.0. Amounts: {bet_amounts}"
                    )
                elif all_in_range and not games_count_ok:
                    record_test(
                        "Bot bet amounts in correct range (10.0-30.0)",
                        True,
                        f"All {len(test_bot_games)} games in range (expected {expected_games}). Amounts: {bet_amounts}"
                    )
                else:
                    # Critical failure - bets outside range
                    record_test(
                        "Bot bet amounts in correct range (10.0-30.0)",
                        False,
                        f"Found {len(out_of_range_games)} games with bet amounts OUTSIDE range 10.0-30.0. Out of range games: {out_of_range_games}"
                    )
                
                # Additional test for cycle games count
                if games_count_ok:
                    record_test(
                        "Bot created correct number of cycle games (5)",
                        True,
                        f"Bot created exactly {len(test_bot_games)} games as expected (cycle_games=5)"
                    )
                else:
                    record_test(
                        "Bot created correct number of cycle games (5)",
                        False,
                        f"Bot created {len(test_bot_games)} games, expected {expected_games} (cycle_games=5)"
                    )
                
            else:
                record_test(
                    "Bot bet amounts in correct range (10.0-30.0)",
                    False,
                    f"No games found created by Test_Bet_Range_Bot. Total games found: {len(games)}"
                )
        else:
            record_test(
                "Bot bet amounts in correct range (10.0-30.0)",
                False,
                "No active games found in /bots/active-games endpoint"
            )
    else:
        record_test(
            "Bot bet amounts in correct range (10.0-30.0)",
            False,
            f"Failed to get active games: {details}"
        )

def test_detailed_bet_analysis(token: str):
    """Test 3: Detailed analysis of bet generation patterns"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Detailed analysis of bet generation patterns{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        # Find all Test_Bet_Range_Bot games
        test_bot_games = [game for game in games if game.get("creator_name") == "Test_Bet_Range_Bot"]
        
        if test_bot_games:
            print(f"\n{Colors.CYAN}📈 DETAILED BET ANALYSIS FOR Test_Bet_Range_Bot:{Colors.END}")
            
            bet_amounts = [game.get("bet_amount", 0) for game in test_bot_games]
            min_bet = min(bet_amounts) if bet_amounts else 0
            max_bet = max(bet_amounts) if bet_amounts else 0
            avg_bet = sum(bet_amounts) / len(bet_amounts) if bet_amounts else 0
            
            print(f"   Total games: {len(test_bot_games)}")
            print(f"   Bet amounts: {bet_amounts}")
            print(f"   Min bet: {min_bet}")
            print(f"   Max bet: {max_bet}")
            print(f"   Average bet: {avg_bet:.2f}")
            print(f"   Expected range: 10.0 - 30.0")
            
            # Check gem types diversity
            gem_types_used = set()
            for game in test_bot_games:
                bet_gems = game.get("bet_gems", {})
                if isinstance(bet_gems, dict):
                    gem_types_used.update(bet_gems.keys())
            
            print(f"   Gem types used: {list(gem_types_used)}")
            
            # Analyze each game in detail
            print(f"\n{Colors.CYAN}🔍 INDIVIDUAL GAME ANALYSIS:{Colors.END}")
            for i, game in enumerate(test_bot_games, 1):
                bet_amount = game.get("bet_amount", 0)
                bet_gems = game.get("bet_gems", {})
                status = game.get("status", "unknown")
                game_id = game.get("id", "unknown")
                
                in_range = "✅" if 10.0 <= bet_amount <= 30.0 else "❌"
                
                print(f"   Game {i}: {in_range} ID={game_id[:8]}..., Amount={bet_amount}, Status={status}")
                print(f"            Gems: {bet_gems}")
            
            # Final assessment
            all_in_range = all(10.0 <= game.get("bet_amount", 0) <= 30.0 for game in test_bot_games)
            
            record_test(
                "Detailed bet analysis",
                all_in_range,
                f"Range analysis: min={min_bet}, max={max_bet}, avg={avg_bet:.2f}, all_in_range={all_in_range}"
            )
        else:
            record_test(
                "Detailed bet analysis",
                False,
                "No Test_Bet_Range_Bot games found for detailed analysis"
            )
    else:
        record_test(
            "Detailed bet analysis",
            False,
            f"Failed to get games for analysis: {details}"
        )

def test_wait_and_recheck_bets(token: str):
    """Test 4: Wait longer and recheck to ensure bot automation is working"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Extended wait and recheck for bot automation{Colors.END}")
    
    print(f"{Colors.BLUE}⏳ Waiting additional 10 seconds for bot automation to stabilize...{Colors.END}")
    time.sleep(10)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        test_bot_games = [game for game in games if game.get("creator_name") == "Test_Bet_Range_Bot"]
        
        if test_bot_games:
            bet_amounts = [game.get("bet_amount", 0) for game in test_bot_games]
            out_of_range = [amount for amount in bet_amounts if not (10.0 <= amount <= 30.0)]
            
            if not out_of_range:
                record_test(
                    "Extended wait - all bets still in range",
                    True,
                    f"After extended wait: {len(test_bot_games)} games, all bet amounts in range 10.0-30.0: {bet_amounts}"
                )
            else:
                record_test(
                    "Extended wait - all bets still in range",
                    False,
                    f"After extended wait: found {len(out_of_range)} bets outside range: {out_of_range}"
                )
        else:
            record_test(
                "Extended wait - bot games exist",
                False,
                "No Test_Bet_Range_Bot games found after extended wait"
            )
    else:
        record_test(
            "Extended wait - API accessible",
            False,
            f"Failed to access active games after extended wait: {details}"
        )

def print_final_summary():
    """Print final test summary"""
    print_header("BET RANGE GENERATION TESTING SUMMARY")
    
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
        "Создать бота Test_Bet_Range_Bot с min_bet=10.0, max_bet=30.0",
        "Проверить что создано 5 активных ставок (cycle_games=5)",
        "Убедиться что все ставки в диапазоне 10.0-30.0 гемов",
        "Диагностика ставок вне диапазона (если найдены)"
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: BET RANGE GENERATION FIX IS WORKING ({success_rate:.1f}% success)!{Colors.END}")
        print(f"{Colors.GREEN}Regular bots are correctly generating bets within the specified min_bet_amount and max_bet_amount range.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: BET RANGE GENERATION PARTIALLY WORKING ({success_rate:.1f}% success){Colors.END}")
        print(f"{Colors.YELLOW}Some issues detected but core bet range functionality appears to be working.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: BET RANGE GENERATION FIX NEEDS ATTENTION ({success_rate:.1f}% success){Colors.END}")
        print(f"{Colors.RED}Critical issues found with bet range generation. Bots may be creating bets outside the specified range.{Colors.END}")

def main():
    """Main test execution"""
    print_header("REGULAR BOTS BET RANGE GENERATION TESTING")
    print(f"{Colors.BLUE}🎯 Testing bet range generation fix for Regular bots{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: min_bet_amount=10.0, max_bet_amount=30.0, cycle_games=5{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Cannot proceed without authentication{Colors.END}")
        sys.exit(1)
    
    try:
        # Run all tests in sequence
        bot_id = test_create_bet_range_bot(token)
        test_bot_active_games_range(token, bot_id)
        test_detailed_bet_analysis(token)
        test_wait_and_recheck_bets(token)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()