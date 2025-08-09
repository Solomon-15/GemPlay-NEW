#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ТОЧНОЙ СУММЫ ЦИКЛА - Russian Review Testing
Тестирование ФИНАЛЬНОГО ИСПРАВЛЕНИЯ точной суммы цикла ставок

ФИНАЛЬНЫЙ ТЕСТ:
1. POST /api/admin/bots/create-regular - создать бота "Final_Perfect_Test_Bot"
2. Подождать 30 секунд для создания ВСЕХ 12 ставок
3. GET /api/bots/active-games - получить все игры бота
4. Вычислить ТОЧНУЮ сумму всех bet_amount
5. Проверить что сумма РАВНА 306.0
6. Проверить что количество ставок = 12
7. Проверить логи на:
   - "🎯 Bot ID: GENERATING COMPLETE CYCLE"
   - "🎯 Bot ID: CYCLE BETS SAVED - 12 bets with total sum 306"
   - "🎯 Bot ID: EXACT bet amount=X, gem_total=Y" для каждой ставки

КРИТЕРИЙ УСПЕХА: Сумма = 306.0 AND количество = 12. Это должно быть ИДЕАЛЬНО после всех исправлений архитектуры и итерации.
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

def main():
    """Main test execution for FINAL PERFECT TEST"""
    print_header("ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ТОЧНОЙ СУММЫ ЦИКЛА - FINAL PERFECT TEST")
    print(f"{Colors.BLUE}🎯 Testing ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ точной суммы цикла ставок{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Regular bot 'Final_Perfect_Test_Bot', cycle sum = 306.0{Colors.END}")
    print(f"{Colors.BLUE}🎲 Expected: (1+50)/2*12 = 25.5*12 = 306.0{Colors.END}")
    print(f"{Colors.BLUE}🚨 КРИТЕРИЙ УСПЕХА: Сумма = 306.0 AND количество = 12{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        print(f"{Colors.RED}❌ Cannot proceed without admin authentication{Colors.END}")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot with EXACT settings from Russian review
    bot_data = {
        "name": "Final_Perfect_Test_Bot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "cycle_games": 12,
        "win_percentage": 55,
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"\n{Colors.MAGENTA}🧪 STEP 1: Creating Regular bot 'Final_Perfect_Test_Bot'{Colors.END}")
    print(f"   📝 Bot settings: {bot_data}")
    
    # Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        print(f"{Colors.RED}❌ FAILED to create Regular bot: {details}{Colors.END}")
        return
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        print(f"{Colors.RED}❌ Bot created but no bot_id returned{Colors.END}")
        return
    
    print(f"{Colors.GREEN}✅ Regular bot 'Final_Perfect_Test_Bot' created successfully with ID: {bot_id}{Colors.END}")
    
    print(f"\n{Colors.MAGENTA}🧪 STEP 2: Waiting 30 seconds for COMPLETE cycle creation{Colors.END}")
    print(f"   ⏳ Waiting for ALL 12 bets to be created...")
    time.sleep(30)
    
    print(f"\n{Colors.MAGENTA}🧪 STEP 3: Getting all active games for the bot{Colors.END}")
    # Get ALL active games for this specific bot
    success, games_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not games_data:
        print(f"{Colors.RED}❌ FAILED to get active games: {details}{Colors.END}")
        return
    
    # Filter games for our specific bot
    bot_games = []
    if isinstance(games_data, list):
        bot_games = [game for game in games_data if game.get("bot_id") == bot_id]
    elif isinstance(games_data, dict) and "games" in games_data:
        bot_games = [game for game in games_data["games"] if game.get("bot_id") == bot_id]
    
    if not bot_games:
        print(f"{Colors.RED}❌ No active games found for bot {bot_id}{Colors.END}")
        print(f"   Total games in response: {len(games_data) if isinstance(games_data, list) else 'unknown'}")
        return
    
    print(f"{Colors.GREEN}✅ Found {len(bot_games)} active games for Final_Perfect_Test_Bot{Colors.END}")
    
    print(f"\n{Colors.MAGENTA}🧪 STEP 4: Calculating EXACT sum of all bet_amount values{Colors.END}")
    # Calculate EXACT sum of ALL bet_amount values
    bet_amounts = [float(game.get("bet_amount", 0)) for game in bot_games]
    total_sum = sum(bet_amounts)
    bet_count = len(bet_amounts)
    min_bet = min(bet_amounts) if bet_amounts else 0
    max_bet = max(bet_amounts) if bet_amounts else 0
    avg_bet = total_sum / bet_count if bet_count > 0 else 0
    
    print(f"   📊 ФИНАЛЬНЫЙ АНАЛИЗ:")
    print(f"      Количество ставок: {bet_count}")
    print(f"      Минимальная ставка: ${min_bet:.1f}")
    print(f"      Максимальная ставка: ${max_bet:.1f}")
    print(f"      Средняя ставка: ${avg_bet:.1f}")
    print(f"      ТОЧНАЯ СУММА: ${total_sum:.1f}")
    print(f"      ОЖИДАЕМАЯ СУММА: $306.0")
    print(f"   🔍 Individual bet amounts: {sorted(bet_amounts)}")
    
    print(f"\n{Colors.MAGENTA}🧪 STEP 5: Checking if sum EQUALS 306.0{Colors.END}")
    expected_sum = 306.0
    is_exact_match = abs(total_sum - expected_sum) < 0.01  # Allow for floating point precision
    
    print(f"\n{Colors.MAGENTA}🧪 STEP 6: Checking if bet count = 12{Colors.END}")
    correct_bet_count = bet_count == 12
    
    print(f"\n{Colors.MAGENTA}🧪 STEP 7: Checking backend logs for specific messages{Colors.END}")
    try:
        import subprocess
        
        # Get recent backend logs
        result = subprocess.run(
            ["tail", "-n", "300", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for specific messages
            generating_cycle_msgs = log_content.count("🎯 Bot ID: GENERATING COMPLETE CYCLE")
            cycle_bets_saved_msgs = log_content.count("🎯 Bot ID: CYCLE BETS SAVED - 12 bets with total sum 306")
            exact_bet_msgs = log_content.count("🎯 Bot ID: EXACT bet amount=")
            
            print(f"   📋 Backend Log Analysis:")
            print(f"      🎯 'GENERATING COMPLETE CYCLE' messages: {generating_cycle_msgs}")
            print(f"      🎯 'CYCLE BETS SAVED - 12 bets with total sum 306' messages: {cycle_bets_saved_msgs}")
            print(f"      🎯 'EXACT bet amount=' messages: {exact_bet_msgs}")
            
            # Show relevant log lines
            relevant_lines = []
            for line in log_content.split('\n'):
                if any(keyword in line for keyword in [
                    "🎯 Bot ID: GENERATING COMPLETE CYCLE",
                    "🎯 Bot ID: CYCLE BETS SAVED",
                    "🎯 Bot ID: EXACT bet amount=",
                    "Final_Perfect_Test_Bot"
                ]):
                    relevant_lines.append(line.strip())
            
            if relevant_lines:
                print(f"   📝 Relevant log lines:")
                for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                    print(f"      {line}")
            else:
                print(f"   ⚠️ No relevant log lines found")
                
        else:
            print(f"   ❌ Failed to read backend logs: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Error reading logs: {str(e)}")
    
    # FINAL RESULT
    print_header("ФИНАЛЬНЫЙ РЕЗУЛЬТАТ")
    
    if is_exact_match and correct_bet_count:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 УСПЕХ! ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ РАБОТАЕТ ИДЕАЛЬНО!{Colors.END}")
        print(f"{Colors.GREEN}✅ Сумма = {total_sum:.1f} (точно равна 306.0){Colors.END}")
        print(f"{Colors.GREEN}✅ Количество ставок = {bet_count} (точно равно 12){Colors.END}")
        print(f"{Colors.GREEN}✅ Диапазон ставок: ${min_bet:.1f} - ${max_bet:.1f}{Colors.END}")
        print(f"{Colors.GREEN}✅ Средняя ставка: ${avg_bet:.1f}{Colors.END}")
        print(f"{Colors.GREEN}🎯 КРИТЕРИЙ УСПЕХА ДОСТИГНУТ: Сумма = 306.0 AND количество = 12{Colors.END}")
        print(f"{Colors.GREEN}🚀 Система готова к продакшену!{Colors.END}")
    else:
        difference = total_sum - expected_sum
        issues = []
        if not is_exact_match:
            issues.append(f"Сумма неточная: {total_sum:.1f} ≠ 306.0 (разница: {difference:+.1f})")
        if not correct_bet_count:
            issues.append(f"Неверное количество ставок: {bet_count} ≠ 12")
        
        print(f"{Colors.RED}{Colors.BOLD}🚨 ПРОВАЛ! ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ!{Colors.END}")
        print(f"{Colors.RED}❌ {'; '.join(issues)}{Colors.END}")
        print(f"{Colors.RED}❌ КРИТЕРИЙ УСПЕХА НЕ ДОСТИГНУТ{Colors.END}")
        print(f"{Colors.RED}🔧 Требуется дополнительная работа над архитектурой создания ставок{Colors.END}")
        
        # Show what we got vs what was expected
        print(f"\n{Colors.YELLOW}📊 Детальное сравнение:{Colors.END}")
        print(f"   Получено: {bet_count} ставок на сумму ${total_sum:.1f}")
        print(f"   Ожидалось: 12 ставок на сумму $306.0")
        print(f"   Ставки: {sorted(bet_amounts)}")

if __name__ == "__main__":
    main()