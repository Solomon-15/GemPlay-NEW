#!/usr/bin/env python3
"""
Bot Cycle History Modal Testing
Протестировать исправления в модальном окне "📈 История цикла: Bot#"

This test focuses specifically on the cycle history modal functionality
that was mentioned in the Russian review request.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://ac189324-9922-4d54-b6a3-50cded9a8e9f.preview.emergentagent.com/api"
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

def test_bot_cycle_history_api():
    """Test the bot cycle history API endpoints"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Bot Cycle History API Endpoints{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Bot Cycle History API Authentication", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get list of regular bots first
    print(f"   📝 Getting list of regular bots...")
    success, bots_data, details = make_request(
        "GET",
        "/admin/bots/regular",
        headers=headers
    )
    
    if not success or not bots_data:
        record_test("Get Regular Bots List", False, f"Failed to get bots list: {details}")
        return None
    
    # Find a bot with some activity
    bots = bots_data.get("bots", []) if isinstance(bots_data, dict) else bots_data
    if not bots:
        record_test("Find Active Bot", False, "No regular bots found")
        return None
    
    # Try to find a bot with some games
    test_bot = None
    for bot in bots:
        if bot.get("current_cycle_games", 0) > 0 or bot.get("completed_cycles", 0) > 0:
            test_bot = bot
            break
    
    if not test_bot:
        # Use the first bot if no active one found
        test_bot = bots[0]
    
    bot_id = test_bot.get("id")
    bot_name = test_bot.get("name", f"Bot#{bot_id[:8] if bot_id else 'Unknown'}")
    
    print(f"   🤖 Testing with bot: {bot_name} (ID: {bot_id[:8]}...)")
    print(f"   📊 Bot stats: {test_bot.get('current_cycle_games', 0)} current games, {test_bot.get('completed_cycles', 0)} completed cycles")
    
    record_test("Find Test Bot", True, f"Using bot {bot_name} for cycle history testing")
    
    # Test cycle history endpoint
    print(f"   📝 Testing cycle history endpoint...")
    success, cycle_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}/cycle-history",
        headers=headers
    )
    
    if success and cycle_data:
        # Analyze cycle history data structure
        games = cycle_data.get("games", [])
        cycle_info = cycle_data.get("cycle_info", {})
        cycle_stats = cycle_data.get("cycle_stats", {})
        
        print(f"   📊 Cycle history data structure:")
        print(f"      Games count: {len(games)}")
        print(f"      Cycle info keys: {list(cycle_info.keys()) if cycle_info else 'None'}")
        print(f"      Cycle stats keys: {list(cycle_stats.keys()) if cycle_stats else 'None'}")
        
        # Check for required fields in cycle_stats (financial indicators)
        required_stats = ["total_bet_amount", "total_winnings", "total_losses", "net_profit"]
        missing_stats = [stat for stat in required_stats if stat not in cycle_stats]
        
        if missing_stats:
            record_test(
                "Cycle History API - Financial Data",
                False,
                f"Missing required financial stats: {missing_stats}"
            )
        else:
            # Check if financial data is not zero (real data)
            total_bet = cycle_stats.get("total_bet_amount", 0)
            total_winnings = cycle_stats.get("total_winnings", 0)
            total_losses = cycle_stats.get("total_losses", 0)
            net_profit = cycle_stats.get("net_profit", 0)
            
            has_real_data = total_bet > 0 or total_winnings > 0 or total_losses > 0
            
            record_test(
                "Cycle History API - Financial Data",
                has_real_data,
                f"Financial data: Bet=${total_bet}, Won=${total_winnings}, Lost=${total_losses}, Profit=${net_profit}"
            )
        
        # Check games data structure
        if games:
            sample_game = games[0]
            required_game_fields = ["bet_amount", "bet_gems", "creator_move", "opponent_move", "opponent", "winner"]
            missing_game_fields = [field for field in required_game_fields if field not in sample_game]
            
            if missing_game_fields:
                record_test(
                    "Cycle History API - Game Data Structure",
                    False,
                    f"Missing required game fields: {missing_game_fields}"
                )
            else:
                # Check if game data has real values (not $0)
                bet_amount = sample_game.get("bet_amount", 0)
                bet_gems = sample_game.get("bet_gems", {})
                opponent = sample_game.get("opponent", "")
                
                has_real_game_data = bet_amount > 0 and bet_gems and opponent
                
                record_test(
                    "Cycle History API - Game Data Structure",
                    has_real_game_data,
                    f"Sample game: Bet=${bet_amount}, Gems={len(bet_gems) if bet_gems else 0} types, Opponent='{opponent}'"
                )
        else:
            record_test(
                "Cycle History API - Game Data",
                False,
                "No games data found in cycle history"
            )
        
        record_test(
            "Bot Cycle History API",
            True,
            f"Successfully retrieved cycle history for {bot_name}"
        )
        
        return test_bot, cycle_data
        
    else:
        record_test(
            "Bot Cycle History API",
            False,
            f"Failed to get cycle history: {details}"
        )
        return None

def test_cycle_data_validation(test_bot, cycle_data):
    """Test specific data validation for the cycle history modal"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Cycle Data Validation for Modal Display{Colors.END}")
    
    if not test_bot or not cycle_data:
        record_test("Cycle Data Validation", False, "No test data available")
        return
    
    bot_name = test_bot.get("name", "Unknown Bot")
    
    # Test 1: Financial indicators validation
    cycle_stats = cycle_data.get("cycle_stats", {})
    
    # Check "Поставлено" (total bet amount)
    total_bet = cycle_stats.get("total_bet_amount", 0)
    bet_amount_valid = total_bet > 0
    record_test(
        "Financial Indicator - Поставлено (Total Bet)",
        bet_amount_valid,
        f"Total bet amount: ${total_bet} (should be > $0)"
    )
    
    # Check "Выиграно" (total winnings)
    total_winnings = cycle_stats.get("total_winnings", 0)
    winnings_valid = total_winnings >= 0  # Can be 0 if no wins yet
    record_test(
        "Financial Indicator - Выиграно (Total Winnings)",
        winnings_valid,
        f"Total winnings: ${total_winnings}"
    )
    
    # Check "Проиграно" (total losses)
    total_losses = cycle_stats.get("total_losses", 0)
    losses_valid = total_losses >= 0  # Can be 0 if no losses yet
    record_test(
        "Financial Indicator - Проиграно (Total Losses)",
        losses_valid,
        f"Total losses: ${total_losses}"
    )
    
    # Check "Итого" (net profit)
    net_profit = cycle_stats.get("net_profit", 0)
    expected_profit = total_winnings - total_losses
    profit_calculation_valid = abs(net_profit - expected_profit) < 0.01
    record_test(
        "Financial Indicator - Итого (Net Profit Calculation)",
        profit_calculation_valid,
        f"Net profit: ${net_profit}, Expected: ${expected_profit}"
    )
    
    # Test 2: Game log table validation
    games = cycle_data.get("games", [])
    
    if games:
        # Check first few games for required data
        games_to_check = games[:3]  # Check first 3 games
        
        for i, game in enumerate(games_to_check):
            game_num = i + 1
            
            # Check "СТАВКА" column (bet amount)
            bet_amount = game.get("bet_amount", 0)
            bet_valid = bet_amount > 0
            record_test(
                f"Game {game_num} - СТАВКА Column (Bet Amount)",
                bet_valid,
                f"Bet amount: ${bet_amount} (should be > $0)"
            )
            
            # Check "ГЕМЫ" column (gems with icons)
            bet_gems = game.get("bet_gems", {})
            gems_valid = isinstance(bet_gems, dict) and len(bet_gems) > 0
            record_test(
                f"Game {game_num} - ГЕМЫ Column (Gems Data)",
                gems_valid,
                f"Gems: {bet_gems if gems_valid else 'Empty or invalid'}"
            )
            
            # Check "ХОДЫ" column (moves)
            creator_move = game.get("creator_move", "")
            opponent_move = game.get("opponent_move", "")
            moves_valid = creator_move in ["rock", "paper", "scissors"] and opponent_move in ["rock", "paper", "scissors"]
            record_test(
                f"Game {game_num} - ХОДЫ Column (Moves)",
                moves_valid,
                f"Bot: {creator_move}, Opponent: {opponent_move}"
            )
            
            # Check "СОПЕРНИК" column (opponent name)
            opponent = game.get("opponent", "")
            opponent_valid = opponent and opponent != "N/A" and len(opponent) > 0
            record_test(
                f"Game {game_num} - СОПЕРНИК Column (Opponent)",
                opponent_valid,
                f"Opponent: '{opponent}'"
            )
            
            # Check "РЕЗУЛЬТАТ" column (result)
            winner = game.get("winner", "")
            result_valid = winner in ["Победа", "Поражение", "Ничья"]
            record_test(
                f"Game {game_num} - РЕЗУЛЬТАТ Column (Result)",
                result_valid,
                f"Result: '{winner}'"
            )
    else:
        record_test(
            "Game Log Table Validation",
            False,
            "No games data available for validation"
        )

def print_summary():
    """Print test summary"""
    print_header("BOT CYCLE HISTORY MODAL TESTING SUMMARY")
    
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
    
    # Check specific requirements
    financial_tests = [test for test in test_results["tests"] if "Financial Indicator" in test["name"]]
    game_tests = [test for test in test_results["tests"] if "Column" in test["name"]]
    api_tests = [test for test in test_results["tests"] if "API" in test["name"]]
    
    financial_passed = sum(1 for test in financial_tests if test["success"])
    game_passed = sum(1 for test in game_tests if test["success"])
    api_passed = sum(1 for test in api_tests if test["success"])
    
    print(f"   1. Финансовые показатели: {Colors.GREEN if financial_passed == len(financial_tests) else Colors.RED}{'✅' if financial_passed == len(financial_tests) else '❌'} {financial_passed}/{len(financial_tests)}{Colors.END}")
    print(f"   2. Таблица лог матчей: {Colors.GREEN if game_passed >= len(game_tests) * 0.8 else Colors.RED}{'✅' if game_passed >= len(game_tests) * 0.8 else '❌'} {game_passed}/{len(game_tests)}{Colors.END}")
    print(f"   3. API функциональность: {Colors.GREEN if api_passed == len(api_tests) else Colors.RED}{'✅' if api_passed == len(api_tests) else '❌'} {api_passed}/{len(api_tests)}{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: BOT CYCLE HISTORY MODAL IS WORKING CORRECTLY!{Colors.END}")
        print(f"{Colors.GREEN}✅ All financial indicators show real data{Colors.END}")
        print(f"{Colors.GREEN}✅ Game log table has proper data structure{Colors.END}")
        print(f"{Colors.GREEN}✅ API endpoints are functional{Colors.END}")
    elif success_rate >= 70:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOSTLY WORKING ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Most functionality is working, but some minor issues need attention.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: SIGNIFICANT ISSUES FOUND ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}The bot cycle history modal has major issues that need fixing.{Colors.END}")
    
    # Recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    if financial_passed < len(financial_tests):
        print(f"   🔴 Fix financial indicators - some showing $0 instead of real amounts")
    if game_passed < len(game_tests) * 0.8:
        print(f"   🔴 Fix game log table data - missing or invalid game information")
    if api_passed < len(api_tests):
        print(f"   🔴 Fix API endpoints for cycle history")
    
    if success_rate >= 90:
        print(f"   🟢 Bot cycle history modal is ready for frontend testing")
    else:
        print(f"   🔧 Fix backend issues before proceeding with frontend testing")

def main():
    """Main test execution for bot cycle history modal"""
    print_header("BOT CYCLE HISTORY MODAL TESTING")
    print(f"{Colors.BLUE}🎯 Testing исправления в модальном окне '📈 История цикла: Bot#'{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: Bot cycle history API endpoints
        test_result = test_bot_cycle_history_api()
        
        # Test 2: Cycle data validation for modal display
        if test_result:
            test_bot, cycle_data = test_result
            test_cycle_data_validation(test_bot, cycle_data)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_summary()

if __name__ == "__main__":
    main()