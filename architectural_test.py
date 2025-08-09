#!/usr/bin/env python3
"""
ARCHITECTURAL REDESIGN TESTING - Russian Review
Тестирование АРХИТЕКТУРНО ПЕРЕРАБОТАННОЙ функции точного совпадения суммы цикла

ЗАДАЧА: Создать новый Regular бот "Architectural_Test_Bot" и протестировать архитектурное решение
Ожидаемая сумма: (min_bet_amount + max_bet_amount) / 2 * cycle_games = (1 + 50) / 2 * 12 = 306.0

ТЕСТ АРХИТЕКТУРНОГО РЕШЕНИЯ:
1. POST /api/admin/bots/create-regular - создать бота "Architectural_Test_Bot"
2. Подождать 20 секунд для полного создания цикла
3. GET /api/bots/active-games - получить активные игры бота
4. Вычислить точную сумму всех bet_amount 
5. Проверить что сумма == 306.0 (архитектурное требование!)
6. Показать детали: количество ставок, распределение сумм
7. Проверить логи на:
   - "🎯 Bot ID: ARCHITECTURAL REDESIGN"
   - "✅ ARCHITECTURAL SUCCESS! Perfect exact sum match!"
   - "❌ ARCHITECTURAL FAILURE!" (не должно быть)

КРИТИЧЕСКИЙ ТЕСТ АРХИТЕКТУРЫ: Если сумма не равна 306.0, архитектурное решение провалилось.
"""

import requests
import json
import time
import sys
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://ac189324-9922-4d54-b6a3-50cded9a8e9f.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
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

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str]:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
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

def test_architectural_redesign():
    """Test the architectural redesign for exact cycle sum matching"""
    print_header("ARCHITECTURAL REDESIGN TESTING")
    print(f"{Colors.MAGENTA}🏗️ Testing ARCHITECTURAL REDESIGN for exact cycle sum matching{Colors.END}")
    
    # Authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        print(f"{Colors.RED}❌ ARCHITECTURAL TEST FAILED: Cannot authenticate as admin{Colors.END}")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create the specific bot requested in Russian review
    bot_data = {
        "name": "Architectural_Test_Bot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "cycle_games": 12,
        "win_percentage": 55.0,
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"{Colors.BLUE}📝 Creating Regular bot 'Architectural_Test_Bot' with settings:{Colors.END}")
    print(f"   min_bet_amount: {bot_data['min_bet_amount']}")
    print(f"   max_bet_amount: {bot_data['max_bet_amount']}")
    print(f"   cycle_games: {bot_data['cycle_games']}")
    print(f"   win_percentage: {bot_data['win_percentage']}")
    
    # Step 1: Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        print(f"{Colors.RED}❌ ARCHITECTURAL FAILURE: Failed to create bot - {details}{Colors.END}")
        return False
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        print(f"{Colors.RED}❌ ARCHITECTURAL FAILURE: Bot created but no bot_id returned{Colors.END}")
        return False
    
    print(f"{Colors.GREEN}✅ Architectural_Test_Bot created successfully with ID: {bot_id}{Colors.END}")
    
    # Step 2: Wait 20 seconds for full cycle creation
    print(f"{Colors.YELLOW}⏳ Waiting 20 seconds for complete cycle creation...{Colors.END}")
    time.sleep(20)
    
    # Step 3: Get active games for this bot
    print(f"{Colors.BLUE}📊 Getting active games for architectural analysis...{Colors.END}")
    success, games_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not games_data:
        print(f"{Colors.RED}❌ ARCHITECTURAL FAILURE: Failed to get active games - {details}{Colors.END}")
        return False
    
    # Filter games for our specific bot
    bot_games = []
    if isinstance(games_data, list):
        bot_games = [game for game in games_data if game.get("bot_id") == bot_id]
    elif isinstance(games_data, dict) and "games" in games_data:
        bot_games = [game for game in games_data["games"] if game.get("bot_id") == bot_id]
    
    if not bot_games:
        print(f"{Colors.RED}❌ ARCHITECTURAL FAILURE: No active games found for Architectural_Test_Bot{Colors.END}")
        print(f"   Total games in system: {len(games_data) if isinstance(games_data, list) else 'unknown'}")
        return False
    
    # Step 4: Calculate exact sum of all bet_amount
    bet_amounts = [float(game.get("bet_amount", 0)) for game in bot_games]
    total_sum = sum(bet_amounts)
    bet_count = len(bet_amounts)
    min_bet = min(bet_amounts) if bet_amounts else 0
    max_bet = max(bet_amounts) if bet_amounts else 0
    avg_bet = total_sum / bet_count if bet_count > 0 else 0
    
    print(f"\n{Colors.CYAN}🎯 ARCHITECTURAL ANALYSIS RESULTS:{Colors.END}")
    print(f"   Количество ставок: {bet_count}")
    print(f"   Минимальная ставка: ${min_bet:.1f}")
    print(f"   Максимальная ставка: ${max_bet:.1f}")
    print(f"   Средняя ставка: ${avg_bet:.1f}")
    print(f"   {Colors.BOLD}Фактическая сумма: ${total_sum:.1f}{Colors.END}")
    print(f"   {Colors.BOLD}Ожидаемая сумма: $306.0{Colors.END}")
    
    # Step 5: Check if sum equals exactly 306.0 (architectural requirement)
    expected_sum = 306.0
    is_perfect_match = abs(total_sum - expected_sum) < 0.01  # Allow for floating point precision
    
    print(f"\n{Colors.BOLD}🏗️ ARCHITECTURAL VERIFICATION:{Colors.END}")
    
    if is_perfect_match:
        print(f"{Colors.GREEN}✅ ARCHITECTURAL SUCCESS! Perfect exact sum match!{Colors.END}")
        print(f"{Colors.GREEN}   Sum is exactly {total_sum:.1f} (expected: {expected_sum:.1f}){Colors.END}")
        print(f"{Colors.GREEN}   Architectural redesign is working correctly!{Colors.END}")
        architectural_success = True
    else:
        difference = total_sum - expected_sum
        print(f"{Colors.RED}❌ ARCHITECTURAL FAILURE!{Colors.END}")
        print(f"{Colors.RED}   Sum is {total_sum:.1f} instead of {expected_sum:.1f}{Colors.END}")
        print(f"{Colors.RED}   Difference: {difference:+.1f}{Colors.END}")
        print(f"{Colors.RED}   Architectural redesign has failed!{Colors.END}")
        architectural_success = False
    
    # Step 6: Show detailed bet distribution
    print(f"\n{Colors.YELLOW}📋 DETAILED BET DISTRIBUTION:{Colors.END}")
    sorted_bets = sorted(bet_amounts)
    print(f"   Individual bets: {sorted_bets}")
    
    # Group bets by ranges for analysis
    ranges = {
        "1-10": [b for b in bet_amounts if 1 <= b <= 10],
        "11-20": [b for b in bet_amounts if 11 <= b <= 20],
        "21-30": [b for b in bet_amounts if 21 <= b <= 30],
        "31-40": [b for b in bet_amounts if 31 <= b <= 40],
        "41-50": [b for b in bet_amounts if 41 <= b <= 50]
    }
    
    print(f"   Distribution by ranges:")
    for range_name, bets in ranges.items():
        if bets:
            print(f"      ${range_name}: {len(bets)} bets, sum: ${sum(bets):.1f}")
    
    # Step 7: Check backend logs for architectural messages
    print(f"\n{Colors.BLUE}📋 CHECKING BACKEND LOGS FOR ARCHITECTURAL MESSAGES:{Colors.END}")
    
    try:
        # Get recent backend logs
        result = subprocess.run(
            ["tail", "-n", "200", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for specific architectural messages
            architectural_redesign_msgs = log_content.count("🎯 Bot ID: ARCHITECTURAL REDESIGN")
            architectural_success_msgs = log_content.count("✅ ARCHITECTURAL SUCCESS! Perfect exact sum match!")
            architectural_failure_msgs = log_content.count("❌ ARCHITECTURAL FAILURE!")
            
            print(f"   🎯 'Bot ID: ARCHITECTURAL REDESIGN' messages: {architectural_redesign_msgs}")
            print(f"   ✅ 'ARCHITECTURAL SUCCESS!' messages: {architectural_success_msgs}")
            print(f"   ❌ 'ARCHITECTURAL FAILURE!' messages: {architectural_failure_msgs}")
            
            # Look for normalization messages
            perfect_matches = log_content.count("✅ PERFECT MATCH!")
            normalize_messages = log_content.count("normalize_amounts_to_exact_sum")
            
            print(f"   ✅ 'PERFECT MATCH!' messages: {perfect_matches}")
            print(f"   🔧 'normalize_amounts_to_exact_sum' calls: {normalize_messages}")
            
            # Show recent relevant log lines
            log_lines = log_content.split('\n')
            relevant_lines = [line for line in log_lines if any(keyword in line for keyword in [
                "ARCHITECTURAL", "normalize", "PERFECT MATCH", "target_total_sum=306"
            ])]
            
            if relevant_lines:
                print(f"\n   📝 Recent relevant log entries:")
                for line in relevant_lines[-5:]:  # Show last 5 relevant lines
                    if line.strip():
                        print(f"      {line.strip()}")
            
            logs_success = architectural_success_msgs > 0 and architectural_failure_msgs == 0
            
        else:
            print(f"   ❌ Failed to read backend logs: {result.stderr}")
            logs_success = False
            
    except Exception as e:
        print(f"   ❌ Error reading logs: {str(e)}")
        logs_success = False
    
    # Final architectural assessment
    print(f"\n{Colors.BOLD}🏗️ FINAL ARCHITECTURAL ASSESSMENT:{Colors.END}")
    
    if architectural_success and logs_success:
        print(f"{Colors.GREEN}🎉 ARCHITECTURAL REDESIGN IS 100% SUCCESSFUL!{Colors.END}")
        print(f"{Colors.GREEN}   ✅ Exact sum matching: WORKING (306.0){Colors.END}")
        print(f"{Colors.GREEN}   ✅ Backend logging: WORKING{Colors.END}")
        print(f"{Colors.GREEN}   ✅ Cycle creation: WORKING ({bet_count} bets){Colors.END}")
        return True
    elif architectural_success:
        print(f"{Colors.YELLOW}⚠️ ARCHITECTURAL REDESIGN IS PARTIALLY WORKING{Colors.END}")
        print(f"{Colors.GREEN}   ✅ Exact sum matching: WORKING (306.0){Colors.END}")
        print(f"{Colors.YELLOW}   ⚠️ Backend logging: ISSUES{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}🚨 ARCHITECTURAL REDESIGN HAS FAILED!{Colors.END}")
        print(f"{Colors.RED}   ❌ Exact sum matching: FAILED ({total_sum:.1f} ≠ 306.0){Colors.END}")
        print(f"{Colors.RED}   ❌ Architectural requirement not met{Colors.END}")
        return False

def main():
    """Main execution for architectural testing"""
    print_header("ARCHITECTURAL REDESIGN TESTING - RUSSIAN REVIEW")
    print(f"{Colors.BLUE}🎯 Testing АРХИТЕКТУРНО ПЕРЕРАБОТАННУЮ функцию точного совпадения суммы цикла{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🤖 Bot Name: Architectural_Test_Bot{Colors.END}")
    print(f"{Colors.BLUE}📊 Settings: min_bet=1.0, max_bet=50.0, cycle_games=12, win_percentage=55{Colors.END}")
    print(f"{Colors.BLUE}🎲 Expected Sum: (1+50)/2*12 = 306.0{Colors.END}")
    
    try:
        success = test_architectural_redesign()
        
        print(f"\n{Colors.BOLD}📋 SUMMARY FOR MAIN AGENT:{Colors.END}")
        if success:
            print(f"{Colors.GREEN}✅ ARCHITECTURAL REDESIGN: The exact cycle sum matching function is working correctly{Colors.END}")
            print(f"{Colors.GREEN}   Regular bot 'Architectural_Test_Bot' created sum of exactly 306.0{Colors.END}")
            print(f"{Colors.GREEN}   Architectural requirements are met{Colors.END}")
        else:
            print(f"{Colors.RED}❌ ARCHITECTURAL REDESIGN: The exact cycle sum matching function is NOT working{Colors.END}")
            print(f"{Colors.RED}   Regular bot failed to create exact sum of 306.0{Colors.END}")
            print(f"{Colors.RED}   Architectural redesign needs immediate attention{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during architectural testing: {str(e)}{Colors.END}")

if __name__ == "__main__":
    main()