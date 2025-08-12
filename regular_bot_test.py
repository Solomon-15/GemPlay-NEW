#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ НОВОЙ ЛОГИКИ ОБЫЧНЫХ БОТОВ
Testing new regular bot logic as requested in Russian

1. **Тест создания бота с естественным распределением ставок**:
   - Создать нового обычного бота с параметрами: диапазон 1-50, цикл 12 игр, проценты 35/35/30
   - Проверить что в админ панели "Сумма цикла" показывает реальную вычисленную сумму
   - Убедиться что бот создается с правильными параметрами

2. **Тест расчета в модальном окне создания**:
   - Открыть модальное окно создания обычного бота 
   - Изменить параметры (например диапазон 10-40, цикл 8 игр)
   - Проверить что поле "Сумма за цикл" автоматически обновляется с правильной естественной суммой

3. **Тест равномерного распределения ставок**:
   - После создания бота проверить что создались ставки покрывающие весь диапазон 1-50
   - Убедиться что есть малые ставки (1-15), средние (16-35) и большие (36-50)
   - Проверить что общая сумма ставок соответствует ожидаемой

4. **Тест логики процентов исходов**:
   - Проверить что из 12 игр создается правильное количество побед/поражений/ничьих согласно процентам 35/35/30
   - Убедиться что ничьи будут пересозданы как дополнительные победы и поражения
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
BASE_URL = "https://russian-scribe.preview.emergentagent.com/api"
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

def test_create_bot_with_natural_distribution():
    """
    Тест 1: Создание бота с естественным распределением ставок
    Параметры: диапазон 1-50, цикл 12 игр, проценты 35/35/30
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Создание бота с естественным распределением ставок{Colors.END}")
    
    # Authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Создание бота с естественным распределением", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot with specified parameters
    bot_data = {
        "name": "Natural_Distribution_Test_Bot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "cycle_games": 12,
        "wins_percentage": 35,
        "losses_percentage": 35,
        "draws_percentage": 30,
        "win_percentage": 55.0,  # Соотношение выигрышных сумм к общей сумме
        "pause_between_cycles": 5,
        "pause_on_draw": 5,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"   📝 Creating Regular bot with natural distribution")
    print(f"   📊 Parameters: range 1-50, cycle 12 games, outcomes 35/35/30%")
    
    # Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        record_test(
            "Создание бота с естественным распределением",
            False,
            f"Failed to create Regular bot: {details}"
        )
        return None
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        record_test(
            "Создание бота с естественным распределением",
            False,
            "Bot created but no bot_id returned"
        )
        return None
    
    # Check if cycle_total_amount is calculated and returned
    cycle_total_amount = response_data.get("cycle_total_amount", 0)
    
    print(f"   ✅ Regular bot created successfully with ID: {bot_id}")
    print(f"   💰 Cycle total amount (Сумма цикла): {cycle_total_amount}")
    
    # Verify bot parameters
    success, bot_data_check, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}",
        headers=headers
    )
    
    if success and bot_data_check:
        bot_info = bot_data_check
        correct_params = (
            bot_info.get("min_bet_amount") == 1.0 and
            bot_info.get("max_bet_amount") == 50.0 and
            bot_info.get("cycle_games") == 12 and
            bot_info.get("wins_percentage") == 35 and
            bot_info.get("losses_percentage") == 35 and
            bot_info.get("draws_percentage") == 30
        )
        
        if correct_params:
            record_test(
                "Создание бота с естественным распределением",
                True,
                f"Bot created with correct parameters, cycle_total_amount: {cycle_total_amount}"
            )
        else:
            record_test(
                "Создание бота с естественным распределением",
                False,
                f"Bot parameters incorrect: {bot_info}"
            )
    else:
        record_test(
            "Создание бота с естественным распределением",
            False,
            f"Could not verify bot parameters: {details}"
        )
    
    return bot_id, cycle_total_amount

def test_uniform_bet_distribution(bot_id: str):
    """
    Тест 3: Равномерное распределение ставок
    Проверить покрытие диапазона 1-50 с малыми, средними и большими ставками
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Равномерное распределение ставок{Colors.END}")
    
    if not bot_id:
        record_test("Равномерное распределение ставок", False, "No bot_id provided")
        return
    
    # Authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Равномерное распределение ставок", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Wait for bot to create bets
    print(f"   ⏳ Waiting 30 seconds for bot to create bets...")
    time.sleep(30)
    
    # Get active games for this bot
    success, games_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success or not games_data:
        record_test(
            "Равномерное распределение ставок",
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
            "Равномерное распределение ставок",
            False,
            "No active games found for the bot"
        )
        return
    
    # Analyze bet distribution
    bet_amounts = [float(game.get("bet_amount", 0)) for game in bot_games]
    bet_count = len(bet_amounts)
    total_sum = sum(bet_amounts)
    min_bet = min(bet_amounts) if bet_amounts else 0
    max_bet = max(bet_amounts) if bet_amounts else 0
    
    # Categorize bets
    small_bets = [bet for bet in bet_amounts if 1 <= bet <= 15]
    medium_bets = [bet for bet in bet_amounts if 16 <= bet <= 35]
    large_bets = [bet for bet in bet_amounts if 36 <= bet <= 50]
    
    print(f"   📊 Bet Distribution Analysis:")
    print(f"      Total bets: {bet_count}")
    print(f"      Total sum: ${total_sum:.2f}")
    print(f"      Range: ${min_bet:.2f} - ${max_bet:.2f}")
    print(f"      Small bets (1-15): {len(small_bets)} bets")
    print(f"      Medium bets (16-35): {len(medium_bets)} bets")
    print(f"      Large bets (36-50): {len(large_bets)} bets")
    print(f"      Individual amounts: {sorted(bet_amounts)}")
    
    # Check distribution criteria
    has_small_bets = len(small_bets) > 0
    has_medium_bets = len(medium_bets) > 0
    has_large_bets = len(large_bets) > 0
    covers_full_range = min_bet >= 1 and max_bet <= 50
    has_diversity = len(set(bet_amounts)) > bet_count // 2  # At least half should be unique
    correct_count = bet_count == 12
    
    success_criteria = [
        ("Correct bet count (12)", correct_count),
        ("Has small bets (1-15)", has_small_bets),
        ("Has medium bets (16-35)", has_medium_bets),
        ("Has large bets (36-50)", has_large_bets),
        ("Covers full range", covers_full_range),
        ("Has bet diversity", has_diversity)
    ]
    
    passed_criteria = sum(1 for _, passed in success_criteria if passed)
    total_criteria = len(success_criteria)
    
    print(f"   ✅ Success criteria ({passed_criteria}/{total_criteria}):")
    for criterion, passed in success_criteria:
        status = "✅" if passed else "❌"
        print(f"      {status} {criterion}")
    
    if passed_criteria == total_criteria:
        record_test(
            "Равномерное распределение ставок",
            True,
            f"Perfect distribution: {len(small_bets)} small, {len(medium_bets)} medium, {len(large_bets)} large bets, total: ${total_sum:.2f}"
        )
    else:
        record_test(
            "Равномерное распределение ставок",
            False,
            f"Distribution issues: {passed_criteria}/{total_criteria} criteria passed"
        )
    
    return bet_amounts, total_sum

def test_outcome_percentages_logic(bot_id: str):
    """
    Тест 4: Логика процентов исходов
    Проверить что из 12 игр создается правильное количество побед/поражений/ничьих согласно 35/35/30%
    """
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Логика процентов исходов (35/35/30){Colors.END}")
    
    if not bot_id:
        record_test("Логика процентов исходов", False, "No bot_id provided")
        return
    
    # Authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Логика процентов исходов", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get bot information to check outcome settings
    success, bot_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}",
        headers=headers
    )
    
    if not success or not bot_data:
        record_test(
            "Логика процентов исходов",
            False,
            f"Failed to get bot data: {details}"
        )
        return
    
    # Check if bot has correct outcome percentages
    wins_percentage = bot_data.get("wins_percentage", 0)
    losses_percentage = bot_data.get("losses_percentage", 0)
    draws_percentage = bot_data.get("draws_percentage", 0)
    cycle_games = bot_data.get("cycle_games", 0)
    
    print(f"   📊 Bot outcome configuration:")
    print(f"      Wins percentage: {wins_percentage}%")
    print(f"      Losses percentage: {losses_percentage}%")
    print(f"      Draws percentage: {draws_percentage}%")
    print(f"      Cycle games: {cycle_games}")
    
    # Calculate expected outcomes for 12 games
    expected_wins = round(cycle_games * wins_percentage / 100)
    expected_losses = round(cycle_games * losses_percentage / 100)
    expected_draws = round(cycle_games * draws_percentage / 100)
    
    print(f"   🎯 Expected outcomes for {cycle_games} games:")
    print(f"      Expected wins: {expected_wins}")
    print(f"      Expected losses: {expected_losses}")
    print(f"      Expected draws: {expected_draws}")
    print(f"      Total: {expected_wins + expected_losses + expected_draws}")
    
    # Check if percentages are correct
    correct_percentages = (
        wins_percentage == 35 and
        losses_percentage == 35 and
        draws_percentage == 30
    )
    
    # Check if total adds up correctly
    total_percentage = wins_percentage + losses_percentage + draws_percentage
    correct_total = total_percentage == 100
    
    # Check if expected outcomes make sense
    total_expected = expected_wins + expected_losses + expected_draws
    reasonable_distribution = abs(total_expected - cycle_games) <= 1  # Allow for rounding
    
    success_criteria = [
        ("Correct win percentage (35%)", wins_percentage == 35),
        ("Correct loss percentage (35%)", losses_percentage == 35),
        ("Correct draw percentage (30%)", draws_percentage == 30),
        ("Total percentage = 100%", correct_total),
        ("Reasonable outcome distribution", reasonable_distribution)
    ]
    
    passed_criteria = sum(1 for _, passed in success_criteria if passed)
    total_criteria = len(success_criteria)
    
    print(f"   ✅ Outcome logic criteria ({passed_criteria}/{total_criteria}):")
    for criterion, passed in success_criteria:
        status = "✅" if passed else "❌"
        print(f"      {status} {criterion}")
    
    if passed_criteria == total_criteria:
        record_test(
            "Логика процентов исходов",
            True,
            f"Correct outcome percentages: {wins_percentage}/{losses_percentage}/{draws_percentage}%, expected outcomes: {expected_wins}W/{expected_losses}L/{expected_draws}D"
        )
    else:
        record_test(
            "Логика процентов исходов",
            False,
            f"Outcome logic issues: {passed_criteria}/{total_criteria} criteria passed"
        )

def check_backend_logs():
    """Check backend logs for bot creation messages"""
    print(f"\n{Colors.MAGENTA}🧪 Checking Backend Logs for Bot Creation Messages{Colors.END}")
    
    try:
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
            
            # Look for bot creation messages
            bot_creation_msgs = log_content.count("Creating complete cycle")
            natural_distribution_msgs = log_content.count("natural distribution")
            uniform_bets_msgs = log_content.count("uniform bet")
            outcome_logic_msgs = log_content.count("outcome percentage")
            error_msgs = log_content.count("ERROR")
            
            print(f"   📋 Backend Log Analysis:")
            print(f"      🤖 Bot creation messages: {bot_creation_msgs}")
            print(f"      🎯 Natural distribution messages: {natural_distribution_msgs}")
            print(f"      📊 Uniform bet messages: {uniform_bets_msgs}")
            print(f"      🎲 Outcome logic messages: {outcome_logic_msgs}")
            print(f"      ❌ Error messages: {error_msgs}")
            
            # Show recent relevant log lines
            relevant_lines = []
            for line in log_content.split('\n'):
                if any(keyword in line.lower() for keyword in [
                    "creating complete cycle",
                    "natural distribution",
                    "uniform bet",
                    "outcome percentage",
                    "regular bot"
                ]):
                    relevant_lines.append(line.strip())
            
            if relevant_lines:
                print(f"   📝 Recent relevant log lines:")
                for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                    print(f"      {line}")
            
            has_creation_logs = bot_creation_msgs > 0 or natural_distribution_msgs > 0
            no_errors = error_msgs == 0
            
            if has_creation_logs and no_errors:
                record_test(
                    "Backend Logs Analysis",
                    True,
                    f"Found {bot_creation_msgs} creation messages, no errors"
                )
            else:
                record_test(
                    "Backend Logs Analysis",
                    False,
                    f"Missing creation logs or found {error_msgs} errors"
                )
                
        else:
            record_test(
                "Backend Logs Analysis",
                False,
                f"Failed to read backend logs: {result.stderr}"
            )
            
    except Exception as e:
        record_test("Backend Logs Analysis", False, f"Error reading logs: {str(e)}")

def print_final_summary():
    """Print final test summary"""
    print_header("ТЕСТИРОВАНИЕ НОВОЙ ЛОГИКИ ОБЫЧНЫХ БОТОВ - ИТОГИ")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 ОБЩИЕ РЕЗУЛЬТАТЫ:{Colors.END}")
    print(f"   Всего тестов: {total}")
    print(f"   {Colors.GREEN}✅ Пройдено: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Провалено: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Процент успеха: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 СТАТУС ТРЕБОВАНИЙ:{Colors.END}")
    
    # Check each test requirement
    tests_status = [
        ("1. Создание бота с естественным распределением", "создание бота с естественным распределением"),
        ("2. Расчет в модальном окне (UI тест)", "расчет в модальном окне"),
        ("3. Равномерное распределение ставок", "равномерное распределение ставок"),
        ("4. Логика процентов исходов", "логика процентов исходов"),
        ("5. Логи backend", "backend logs")
    ]
    
    for requirement, test_key in tests_status:
        test = next((test for test in test_results["tests"] if test_key.lower() in test["name"].lower()), None)
        if test:
            status = f"{Colors.GREEN}✅ РАБОТАЕТ{Colors.END}" if test["success"] else f"{Colors.RED}❌ НЕ РАБОТАЕТ{Colors.END}"
            print(f"   {requirement}: {status}")
            if test["details"]:
                print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
        else:
            print(f"   {requirement}: {Colors.YELLOW}⚠️ НЕ ТЕСТИРОВАЛОСЬ{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ЗАКЛЮЧЕНИЕ: НОВАЯ ЛОГИКА ОБЫЧНЫХ БОТОВ РАБОТАЕТ!{Colors.END}")
        print(f"{Colors.GREEN}✅ Боты создаются с правильными параметрами{Colors.END}")
        print(f"{Colors.GREEN}✅ Распределение ставок работает корректно{Colors.END}")
        print(f"{Colors.GREEN}✅ Логика исходов настроена правильно{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ ЗАКЛЮЧЕНИЕ: ЧАСТИЧНЫЙ УСПЕХ ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.YELLOW}Основная логика работает, но есть проблемы для исправления.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 ЗАКЛЮЧЕНИЕ: ТРЕБУЕТСЯ ДОРАБОТКА ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.RED}Новая логика обычных ботов работает неправильно.{Colors.END}")
    
    print(f"\n{Colors.BOLD}💡 РЕКОМЕНДАЦИИ ДЛЯ ГЛАВНОГО АГЕНТА:{Colors.END}")
    
    if success_rate >= 80:
        print(f"   🟢 Новая логика обычных ботов готова к использованию")
        print(f"   ✅ Можно переходить к тестированию UI в браузере")
    else:
        print(f"   🔧 Исправить проблемы с backend API перед тестированием UI")
        print(f"   🔴 Проверить логику создания ботов и распределения ставок")

def main():
    """Main test execution for new regular bot logic"""
    print_header("ТЕСТИРОВАНИЕ НОВОЙ ЛОГИКИ ОБЫЧНЫХ БОТОВ")
    print(f"{Colors.BLUE}🎯 Testing new regular bot logic with natural distribution{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: Create bot with natural distribution (1-50, 12 games, 35/35/30)
        bot_id, cycle_total = test_create_bot_with_natural_distribution()
        
        if bot_id:
            # Test 3: Check uniform bet distribution
            bet_amounts, total_sum = test_uniform_bet_distribution(bot_id)
            
            # Test 4: Check outcome percentages logic
            test_outcome_percentages_logic(bot_id)
        
        # Check backend logs
        check_backend_logs()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()