#!/usr/bin/env python3
"""
MODAL CYCLE HISTORY TESTING - Russian Review Request
Тестирование модального окна "📈 История цикла: Bot#"

КРИТИЧЕСКИ ВАЖНО - ПРОВЕРИТЬ ИСПРАВЛЕНИЯ:
1. Финансовые показатели (верхняя часть модалки):
   - "Поставлено" - ДОЛЖНО показывать реальную сумму (НЕ $0)
   - "Выиграно" - ДОЛЖНО показывать фактические выигрыши  
   - "Проиграно" - ДОЛЖНО показывать реальные проигрыши
   - "Итого" - ДОЛЖНО показывать правильный профит (выигрыши - ставки)

2. Таблица игр - все должно работать правильно:
   - СТАВКА: реальные суммы (не $0) ✅
   - ГЕМЫ: иконки с количеством ✅ 
   - ХОДЫ: реальные ходы игроков ✅
   - СОПЕРНИК: реальные имена ✅
   - РЕЗУЛЬТАТ: правильные результаты ✅
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
from datetime import datetime

# Configuration
BASE_URL = "https://opus-shop-next.preview.emergentagent.com/api"
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

def test_regular_bots_list():
    """Get list of regular bots to test cycle history modal"""
    print(f"\n{Colors.MAGENTA}🧪 Getting Regular Bots List for Modal Testing{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        print(f"{Colors.RED}❌ Failed to authenticate as admin{Colors.END}")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get regular bots list
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular",
        headers=headers
    )
    
    if not success or not response_data:
        print(f"{Colors.RED}❌ Failed to get regular bots: {details}{Colors.END}")
        return None
    
    bots = response_data.get("bots", []) if isinstance(response_data, dict) else response_data
    
    if not bots:
        print(f"{Colors.YELLOW}⚠️ No regular bots found{Colors.END}")
        return None
    
    print(f"{Colors.GREEN}✅ Found {len(bots)} regular bots{Colors.END}")
    
    # Find a bot with completed cycles for testing
    suitable_bot = None
    for bot in bots:
        if bot.get("completed_cycles", 0) > 0:
            suitable_bot = bot
            break
    
    if not suitable_bot:
        # Use the first bot even if no completed cycles
        suitable_bot = bots[0]
        print(f"{Colors.YELLOW}⚠️ No bots with completed cycles, using first bot: {suitable_bot.get('name', 'Unknown')}{Colors.END}")
    else:
        print(f"{Colors.GREEN}✅ Found suitable bot with completed cycles: {suitable_bot.get('name', 'Unknown')}{Colors.END}")
    
    return suitable_bot, admin_token

def test_bot_cycle_history_api(bot_id: str, admin_token: str):
    """Test the bot cycle history API that feeds the modal"""
    print(f"\n{Colors.MAGENTA}🧪 Testing Bot Cycle History API for Modal Data{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test the cycle history endpoint
    success, response_data, details = make_request(
        "GET",
        f"/admin/bots/regular/{bot_id}/cycle-history",
        headers=headers
    )
    
    if not success or not response_data:
        print(f"{Colors.RED}❌ Failed to get cycle history: {details}{Colors.END}")
        return None
    
    print(f"{Colors.GREEN}✅ Successfully retrieved cycle history data{Colors.END}")
    
    # Analyze the response structure for modal requirements
    print(f"\n{Colors.BLUE}📊 Analyzing Modal Data Structure:{Colors.END}")
    
    # Check if we have the required financial indicators
    financial_indicators = {
        "total_wagered": response_data.get("total_wagered", 0),
        "total_won": response_data.get("total_won", 0), 
        "total_lost": response_data.get("total_lost", 0),
        "net_profit": response_data.get("net_profit", 0)
    }
    
    print(f"   💰 Financial Indicators:")
    print(f"      Поставлено (Total Wagered): ${financial_indicators['total_wagered']}")
    print(f"      Выиграно (Total Won): ${financial_indicators['total_won']}")
    print(f"      Проиграно (Total Lost): ${financial_indicators['total_lost']}")
    print(f"      Итого (Net Profit): ${financial_indicators['net_profit']}")
    
    # Check for zero values (critical issue)
    zero_values = []
    for key, value in financial_indicators.items():
        if value == 0:
            zero_values.append(key)
    
    if zero_values:
        print(f"{Colors.RED}🚨 CRITICAL ISSUE: Found zero values in: {', '.join(zero_values)}{Colors.END}")
    else:
        print(f"{Colors.GREEN}✅ All financial indicators have non-zero values{Colors.END}")
    
    # Check games data
    games = response_data.get("games", [])
    print(f"\n   🎮 Games Data:")
    print(f"      Total games: {len(games)}")
    
    if games:
        # Analyze first few games
        for i, game in enumerate(games[:3]):
            print(f"      Game {i+1}:")
            print(f"         Ставка (Bet): ${game.get('bet_amount', 0)}")
            print(f"         Гемы (Gems): {game.get('bet_gems', {})}")
            print(f"         Ходы (Moves): Creator={game.get('creator_move', 'N/A')}, Opponent={game.get('opponent_move', 'N/A')}")
            print(f"         Соперник (Opponent): {game.get('opponent_name', 'N/A')}")
            print(f"         Результат (Result): {game.get('winner_id', 'N/A')}")
    
    # Validate mathematical correctness
    calculated_profit = financial_indicators['total_won'] - financial_indicators['total_wagered']
    profit_matches = abs(calculated_profit - financial_indicators['net_profit']) < 0.01
    
    print(f"\n   🧮 Mathematical Validation:")
    print(f"      Calculated Profit: ${calculated_profit}")
    print(f"      Reported Profit: ${financial_indicators['net_profit']}")
    print(f"      Math Correct: {Colors.GREEN}✅{Colors.END}" if profit_matches else f"{Colors.RED}❌{Colors.END}")
    
    return {
        "financial_indicators": financial_indicators,
        "games": games,
        "zero_values": zero_values,
        "math_correct": profit_matches,
        "response_data": response_data
    }

def main():
    """Main test execution for Modal Cycle History"""
    print_header("MODAL CYCLE HISTORY TESTING - Russian Review")
    print(f"{Colors.BLUE}🎯 Testing Modal '📈 История цикла: Bot#' Data{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Get regular bots list
        result = test_regular_bots_list()
        if not result:
            print(f"{Colors.RED}❌ Cannot proceed without bot data{Colors.END}")
            return
        
        bot, admin_token = result
        bot_id = bot.get("id")
        bot_name = bot.get("name", "Unknown")
        
        print(f"\n{Colors.BLUE}🤖 Testing with bot: {bot_name} (ID: {bot_id}){Colors.END}")
        
        # Test cycle history API
        cycle_data = test_bot_cycle_history_api(bot_id, admin_token)
        
        if cycle_data:
            print(f"\n{Colors.BOLD}📋 MODAL TESTING SUMMARY:{Colors.END}")
            
            # Check critical requirements
            zero_values = cycle_data["zero_values"]
            math_correct = cycle_data["math_correct"]
            has_games = len(cycle_data["games"]) > 0
            
            if not zero_values and math_correct and has_games:
                print(f"{Colors.GREEN}🎉 SUCCESS: Modal data meets all requirements!{Colors.END}")
                print(f"{Colors.GREEN}✅ No zero financial values{Colors.END}")
                print(f"{Colors.GREEN}✅ Mathematical calculations correct{Colors.END}")
                print(f"{Colors.GREEN}✅ Games data available{Colors.END}")
            else:
                print(f"{Colors.RED}🚨 ISSUES FOUND:{Colors.END}")
                if zero_values:
                    print(f"{Colors.RED}❌ Zero values in: {', '.join(zero_values)}{Colors.END}")
                if not math_correct:
                    print(f"{Colors.RED}❌ Mathematical calculations incorrect{Colors.END}")
                if not has_games:
                    print(f"{Colors.RED}❌ No games data available{Colors.END}")
            
            print(f"\n{Colors.BLUE}💡 NEXT STEP: Use browser automation to test the actual modal UI{Colors.END}")
            
        else:
            print(f"{Colors.RED}❌ Failed to get cycle data for modal testing{Colors.END}")
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")

if __name__ == "__main__":
    main()