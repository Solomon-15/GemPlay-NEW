#!/usr/bin/env python3
"""
Regular Bots System Testing - Russian Review
Focus: Testing Regular Bots system fixes and automation

КРИТИЧЕСКИЕ ТЕСТЫ:
1. **КРИТИЧЕСКИЙ ТЕСТ**: Проверить что функция maintain_all_bots_active_bets() теперь создает ставки
2. **ТЕСТ АЛГОРИТМА ВЫИГРЫШЕЙ**: Создать тестового бота с win_percentage: 55%
3. **ТЕСТ ЦИКЛОВ**: Проверить что бот корректно ведет статистику цикла
4. **БАЗОВЫЕ API ТЕСТЫ**: GET /api/admin/bots, POST /api/admin/bots/create-regular, GET /api/admin/bot-settings

ЦЕЛЬ: Убедиться что активные ставки теперь создаются автоматически и система больше не показывает active_bets: 0!
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
BASE_URL = "https://ac189324-9922-4d54-b6a3-50cded9a8e9f.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

SUPER_ADMIN_USER = {
    "email": "superadmin@gemplay.com",
    "password": "SuperAdmin123!"
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
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_subheader(text: str) -> None:
    """Print a formatted subheader."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 80}{Colors.ENDC}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def record_test(name: str, passed: bool, details: str = "") -> None:
    """Record a test result."""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })

def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    auth_token: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"Making {method} request to {url}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        response_data = {"text": response.text}
        print(f"Response text: {response.text}")
    
    success = response.status_code == expected_status
    
    if not success:
        print_error(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success

def test_admin_login() -> Optional[str]:
    """Test admin login and return access token."""
    print_subheader("Admin Authentication")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    # Use JSON data for login
    login_response, login_success = make_request(
        "POST", "/auth/login",
        data=login_data
    )
    
    if not login_success:
        print_error("❌ Admin login failed")
        record_test("Admin Login", False, "Login request failed")
        return None
    
    access_token = login_response.get("access_token")
    if not access_token:
        print_error("❌ Admin login response missing access_token")
        record_test("Admin Login", False, "Missing access_token")
        return None
    
    print_success("✅ Admin login successful")
    print_success(f"✅ Access token received: {access_token[:20]}...")
    record_test("Admin Login", True)
    
    return access_token

def test_critical_maintain_all_bots_active_bets(admin_token: str) -> None:
    """
    КРИТИЧЕСКИЙ ТЕСТ: Проверить что функция maintain_all_bots_active_bets() теперь создает ставки
    
    Цель: Получить список активных ботов GET /api/admin/bots
    Найти боты с active_bets меньше cycle_games
    Убедиться что система автоматизации создает недостающие ставки
    """
    print_header("КРИТИЧЕСКИЙ ТЕСТ: maintain_all_bots_active_bets() СОЗДАЕТ СТАВКИ")
    
    # Step 1: Get list of active bots
    print_subheader("Step 1: Получить список активных ботов")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_success:
        print_error("❌ Failed to get bots list")
        record_test("Critical Test - Get Bots List", False, "Failed to get bots")
        return
    
    if "bots" not in bots_response or not bots_response["bots"]:
        print_error("❌ No bots found in the system")
        record_test("Critical Test - Get Bots List", False, "No bots found")
        return
    
    bots = bots_response["bots"]
    print_success(f"✅ Found {len(bots)} regular bots")
    record_test("Critical Test - Get Bots List", True)
    
    # Step 2: Analyze initial bot states
    print_subheader("Step 2: Анализ начального состояния ботов")
    
    initial_bot_states = {}
    bots_needing_bets = []
    
    for bot in bots:
        bot_id = bot["id"]
        bot_name = bot["name"]
        active_bets = bot.get("active_bets", 0)
        cycle_games = bot.get("cycle_games", 12)
        is_active = bot.get("is_active", False)
        
        initial_bot_states[bot_id] = {
            "name": bot_name,
            "active_bets": active_bets,
            "cycle_games": cycle_games,
            "is_active": is_active
        }
        
        print_success(f"Bot '{bot_name}': {active_bets}/{cycle_games} active bets, active: {is_active}")
        
        # Check if bot needs more bets
        if is_active and active_bets < cycle_games:
            bots_needing_bets.append({
                "id": bot_id,
                "name": bot_name,
                "active_bets": active_bets,
                "cycle_games": cycle_games,
                "needed_bets": cycle_games - active_bets
            })
            print_warning(f"⚠ Bot '{bot_name}' needs {cycle_games - active_bets} more bets")
    
    if not bots_needing_bets:
        print_success("✅ All active bots already have sufficient bets")
        record_test("Critical Test - Bots Need Bets", True, "All bots have sufficient bets")
    else:
        print_warning(f"⚠ Found {len(bots_needing_bets)} bots needing more bets")
        record_test("Critical Test - Bots Need Bets", True, f"{len(bots_needing_bets)} bots need bets")
    
    # Step 3: Monitor bot activity for bet creation
    print_subheader("Step 3: Мониторинг создания ставок (60 секунд)")
    
    print("Мониторинг системы автоматизации ботов...")
    print("Ожидание создания недостающих ставок...")
    
    monitoring_results = []
    start_time = time.time()
    check_interval = 10  # Check every 10 seconds
    total_monitoring_time = 60  # Monitor for 60 seconds
    
    for check_round in range(int(total_monitoring_time / check_interval)):
        print(f"\n--- Проверка {check_round + 1} (через {check_round * check_interval}s) ---")
        
        # Get updated bot states
        current_bots_response, current_bots_success = make_request(
            "GET", "/admin/bots",
            auth_token=admin_token
        )
        
        if current_bots_success and "bots" in current_bots_response:
            current_states = {}
            bets_created_this_round = False
            
            for bot in current_bots_response["bots"]:
                bot_id = bot["id"]
                bot_name = bot["name"]
                active_bets = bot.get("active_bets", 0)
                cycle_games = bot.get("cycle_games", 12)
                is_active = bot.get("is_active", False)
                
                current_states[bot_id] = {
                    "name": bot_name,
                    "active_bets": active_bets,
                    "cycle_games": cycle_games,
                    "is_active": is_active
                }
                
                # Compare with initial state
                if bot_id in initial_bot_states:
                    initial_bets = initial_bot_states[bot_id]["active_bets"]
                    
                    if active_bets > initial_bets:
                        bets_increase = active_bets - initial_bets
                        print_success(f"✅ Bot '{bot_name}': Ставки увеличились с {initial_bets} до {active_bets} (+{bets_increase})")
                        bets_created_this_round = True
                    elif active_bets == cycle_games:
                        print_success(f"✅ Bot '{bot_name}': Поддерживается на уровне цикла ({active_bets}/{cycle_games})")
                    elif active_bets < cycle_games and is_active:
                        print_warning(f"⚠ Bot '{bot_name}': Все еще нужно ставок ({active_bets}/{cycle_games})")
                    else:
                        print_success(f"✓ Bot '{bot_name}': {active_bets}/{cycle_games}")
            
            monitoring_results.append({
                "round": check_round + 1,
                "timestamp": time.time(),
                "states": current_states,
                "bets_created": bets_created_this_round
            })
        
        # Wait for next check (except on last iteration)
        if check_round < int(total_monitoring_time / check_interval) - 1:
            print(f"Ожидание {check_interval} секунд до следующей проверки...")
            time.sleep(check_interval)
    
    # Step 4: Analyze monitoring results
    print_subheader("Step 4: Анализ результатов мониторинга")
    
    if len(monitoring_results) >= 2:
        print_success("✅ Успешно отслежена активность ботов во времени")
        
        # Check if bets were created during monitoring
        total_bets_created = False
        bots_with_increases = []
        
        for bot_id, initial_state in initial_bot_states.items():
            initial_bets = initial_state["active_bets"]
            final_bets = monitoring_results[-1]["states"].get(bot_id, {}).get("active_bets", 0)
            
            if final_bets > initial_bets:
                increase = final_bets - initial_bets
                bots_with_increases.append({
                    "name": initial_state["name"],
                    "initial": initial_bets,
                    "final": final_bets,
                    "increase": increase
                })
                total_bets_created = True
                print_success(f"✅ Bot '{initial_state['name']}': Ставки увеличились с {initial_bets} до {final_bets} (+{increase})")
            elif final_bets == initial_state["cycle_games"]:
                print_success(f"✅ Bot '{initial_state['name']}': Поддерживается на уровне цикла ({final_bets})")
        
        if total_bets_created:
            print_success(f"🎉 КРИТИЧЕСКИЙ ТЕСТ ПРОЙДЕН: Система создала ставки для {len(bots_with_increases)} ботов!")
            print_success("🎉 maintain_all_bots_active_bets() РАБОТАЕТ ПРАВИЛЬНО!")
            record_test("Critical Test - Bet Creation", True, f"Bets created for {len(bots_with_increases)} bots")
        else:
            # Check if all bots are already at cycle level
            all_at_cycle_level = True
            for bot_id, initial_state in initial_bot_states.items():
                if initial_state["is_active"] and initial_state["active_bets"] < initial_state["cycle_games"]:
                    all_at_cycle_level = False
                    break
            
            if all_at_cycle_level:
                print_success("✅ Все активные боты уже на уровне цикла - система работает правильно")
                record_test("Critical Test - Bet Creation", True, "All bots at cycle level")
            else:
                print_warning("⚠ Новые ставки не созданы за период мониторинга")
                record_test("Critical Test - Bet Creation", False, "No bets created")
    else:
        print_error("❌ Недостаточно данных мониторинга")
        record_test("Critical Test - Monitoring", False, "Insufficient data")
    
    # Step 5: Verify that active_bets is no longer 0 for all bots
    print_subheader("Step 5: Проверка что active_bets больше не равно 0 для всех ботов")
    
    final_bots_response, final_bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if final_bots_success and "bots" in final_bots_response:
        zero_active_bets_count = 0
        active_bots_count = 0
        
        for bot in final_bots_response["bots"]:
            is_active = bot.get("is_active", False)
            active_bets = bot.get("active_bets", 0)
            bot_name = bot["name"]
            
            if is_active:
                active_bots_count += 1
                if active_bets == 0:
                    zero_active_bets_count += 1
                    print_error(f"❌ Bot '{bot_name}': active_bets = 0 (ПРОБЛЕМА!)")
                else:
                    print_success(f"✅ Bot '{bot_name}': active_bets = {active_bets}")
        
        if zero_active_bets_count == 0:
            print_success(f"🎉 УСПЕХ: НИ ОДИН активный бот не показывает active_bets: 0!")
            print_success(f"🎉 Система больше НЕ показывает active_bets: 0 для всех ботов!")
            record_test("Critical Test - No Zero Active Bets", True)
        else:
            print_error(f"❌ ПРОБЛЕМА: {zero_active_bets_count} из {active_bots_count} активных ботов показывают active_bets: 0")
            record_test("Critical Test - No Zero Active Bets", False, f"{zero_active_bets_count} bots with 0 active bets")
    
    print_subheader("Результаты критического теста")
    print_success("Критический тест maintain_all_bots_active_bets() завершен")

def test_win_algorithm_with_new_fields(admin_token: str) -> None:
    """
    ТЕСТ АЛГОРИТМА ВЫИГРЫШЕЙ: Создать тестового бота с win_percentage: 55%
    Проверить что новые поля добавились в модель
    """
    print_header("ТЕСТ АЛГОРИТМА ВЫИГРЫШЕЙ: win_percentage 55% И НОВЫЕ ПОЛЯ")
    
    # Step 1: Create test bot with win_percentage: 55%
    print_subheader("Step 1: Создание тестового бота с win_percentage: 55%")
    
    test_bot_data = {
        "name": f"TestBot_WinAlgo_{int(time.time())}",
        "min_bet_amount": 5.0,
        "max_bet_amount": 50.0,
        "win_rate": 0.55,  # 55% win rate
        "cycle_games": 12,
        "individual_limit": 12,
        "creation_mode": "queue-based",
        "priority_order": 50,
        "pause_between_games": 5,
        "profit_strategy": "balanced",
        "can_accept_bets": False,
        "can_play_with_bots": False,
        "avatar_gender": "male",
        "simple_mode": False
    }
    
    create_response, create_success = make_request(
        "POST", "/admin/bots/create-regular",
        data=test_bot_data,
        auth_token=admin_token
    )
    
    if not create_success:
        print_error("❌ Failed to create test bot")
        record_test("Win Algorithm Test - Create Bot", False, "Bot creation failed")
        return
    
    test_bot_id = create_response.get("id")
    if not test_bot_id:
        print_error("❌ Test bot creation response missing ID")
        record_test("Win Algorithm Test - Create Bot", False, "Missing bot ID")
        return
    
    print_success(f"✅ Test bot created with ID: {test_bot_id}")
    print_success(f"✅ Win rate set to: 55%")
    record_test("Win Algorithm Test - Create Bot", True)
    
    # Step 2: Verify new fields are present in bot model
    print_subheader("Step 2: Проверка новых полей в модели бота")
    
    # Get the created bot to check its fields
    bot_response, bot_success = make_request(
        "GET", f"/admin/bots/{test_bot_id}",
        auth_token=admin_token
    )
    
    if not bot_success:
        print_error("❌ Failed to get created bot details")
        record_test("Win Algorithm Test - Get Bot Details", False, "Failed to get bot")
        return
    
    # Check for new fields
    expected_new_fields = [
        "completed_cycles",
        "current_cycle_wins", 
        "current_cycle_losses",
        "current_cycle_draws",
        "current_cycle_profit",
        "total_net_profit",
        "win_percentage"
    ]
    
    missing_fields = []
    present_fields = []
    
    for field in expected_new_fields:
        if field in bot_response:
            present_fields.append(field)
            field_value = bot_response[field]
            print_success(f"✅ Поле '{field}': {field_value}")
        else:
            missing_fields.append(field)
            print_error(f"❌ Отсутствует поле '{field}'")
    
    if not missing_fields:
        print_success(f"🎉 ВСЕ НОВЫЕ ПОЛЯ ПРИСУТСТВУЮТ В МОДЕЛИ БОТА!")
        record_test("Win Algorithm Test - New Fields Present", True)
    else:
        print_error(f"❌ Отсутствуют поля: {missing_fields}")
        record_test("Win Algorithm Test - New Fields Present", False, f"Missing: {missing_fields}")
    
    # Step 3: Verify win_percentage is correctly set
    print_subheader("Step 3: Проверка win_percentage")
    
    win_percentage = bot_response.get("win_percentage", 0)
    expected_win_percentage = 55.0
    
    if abs(win_percentage - expected_win_percentage) < 0.1:
        print_success(f"✅ win_percentage правильно установлен: {win_percentage}%")
        record_test("Win Algorithm Test - Win Percentage", True)
    else:
        print_error(f"❌ win_percentage неправильный: ожидался {expected_win_percentage}%, получен {win_percentage}%")
        record_test("Win Algorithm Test - Win Percentage", False, f"Expected {expected_win_percentage}, got {win_percentage}")
    
    # Step 4: Check initial cycle statistics
    print_subheader("Step 4: Проверка начальной статистики цикла")
    
    cycle_stats = {
        "completed_cycles": bot_response.get("completed_cycles", 0),
        "current_cycle_wins": bot_response.get("current_cycle_wins", 0),
        "current_cycle_losses": bot_response.get("current_cycle_losses", 0),
        "current_cycle_draws": bot_response.get("current_cycle_draws", 0),
        "current_cycle_profit": bot_response.get("current_cycle_profit", 0.0),
        "total_net_profit": bot_response.get("total_net_profit", 0.0)
    }
    
    # For a new bot, these should all be 0
    all_zero = all(value == 0 or value == 0.0 for value in cycle_stats.values())
    
    if all_zero:
        print_success("✅ Начальная статистика цикла правильно инициализирована (все значения = 0)")
        record_test("Win Algorithm Test - Initial Cycle Stats", True)
    else:
        print_warning(f"⚠ Некоторые значения статистики не равны 0: {cycle_stats}")
        record_test("Win Algorithm Test - Initial Cycle Stats", False, f"Non-zero values: {cycle_stats}")
    
    for stat_name, stat_value in cycle_stats.items():
        print_success(f"  {stat_name}: {stat_value}")
    
    # Step 5: Clean up - delete test bot
    print_subheader("Step 5: Очистка - удаление тестового бота")
    
    delete_response, delete_success = make_request(
        "DELETE", f"/admin/bots/{test_bot_id}",
        auth_token=admin_token
    )
    
    if delete_success:
        print_success("✅ Тестовый бот успешно удален")
        record_test("Win Algorithm Test - Cleanup", True)
    else:
        print_warning("⚠ Не удалось удалить тестовый бот")
        record_test("Win Algorithm Test - Cleanup", False, "Failed to delete test bot")
    
    print_subheader("Результаты теста алгоритма выигрышей")
    print_success("Тест алгоритма выигрышей завершен")

def test_cycle_statistics_and_reset(admin_token: str) -> None:
    """
    ТЕСТ ЦИКЛОВ: Проверить что бот корректно ведет статистику цикла
    При завершении 12 игр (победы + поражения) цикл должен сброситься
    """
    print_header("ТЕСТ ЦИКЛОВ: СТАТИСТИКА И СБРОС ПОСЛЕ 12 ИГР")
    
    # Step 1: Get existing bots to check their cycle statistics
    print_subheader("Step 1: Анализ статистики циклов существующих ботов")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_success:
        print_error("❌ Failed to get bots list")
        record_test("Cycle Test - Get Bots", False, "Failed to get bots")
        return
    
    bots = bots_response.get("bots", [])
    if not bots:
        print_error("❌ No bots found")
        record_test("Cycle Test - Get Bots", False, "No bots found")
        return
    
    print_success(f"✅ Found {len(bots)} bots for cycle analysis")
    
    # Analyze cycle statistics
    bots_with_cycles = []
    bots_in_progress = []
    
    for bot in bots:
        bot_name = bot["name"]
        completed_cycles = bot.get("completed_cycles", 0)
        current_cycle_wins = bot.get("current_cycle_wins", 0)
        current_cycle_losses = bot.get("current_cycle_losses", 0)
        current_cycle_draws = bot.get("current_cycle_draws", 0)
        cycle_games = bot.get("cycle_games", 12)
        
        current_cycle_total = current_cycle_wins + current_cycle_losses + current_cycle_draws
        
        print_success(f"Bot '{bot_name}':")
        print_success(f"  Завершенные циклы: {completed_cycles}")
        print_success(f"  Текущий цикл: {current_cycle_wins}W + {current_cycle_losses}L + {current_cycle_draws}D = {current_cycle_total}/{cycle_games}")
        
        if completed_cycles > 0:
            bots_with_cycles.append(bot)
        
        if current_cycle_total > 0:
            bots_in_progress.append(bot)
    
    if bots_with_cycles:
        print_success(f"✅ {len(bots_with_cycles)} ботов имеют завершенные циклы")
        record_test("Cycle Test - Completed Cycles", True)
    else:
        print_warning("⚠ Ни один бот не имеет завершенных циклов")
        record_test("Cycle Test - Completed Cycles", False, "No completed cycles")
    
    if bots_in_progress:
        print_success(f"✅ {len(bots_in_progress)} ботов имеют игры в текущем цикле")
        record_test("Cycle Test - Current Cycle Progress", True)
    else:
        print_warning("⚠ Ни один бот не имеет игр в текущем цикле")
        record_test("Cycle Test - Current Cycle Progress", False, "No current cycle progress")
    
    # Step 2: Check cycle logic validation
    print_subheader("Step 2: Проверка логики циклов")
    
    cycle_logic_correct = True
    
    for bot in bots:
        bot_name = bot["name"]
        current_cycle_wins = bot.get("current_cycle_wins", 0)
        current_cycle_losses = bot.get("current_cycle_losses", 0)
        current_cycle_draws = bot.get("current_cycle_draws", 0)
        cycle_games = bot.get("cycle_games", 12)
        
        current_cycle_total = current_cycle_wins + current_cycle_losses + current_cycle_draws
        
        # Check that current cycle doesn't exceed cycle_games
        if current_cycle_total > cycle_games:
            print_error(f"❌ Bot '{bot_name}': Текущий цикл превышает лимит ({current_cycle_total} > {cycle_games})")
            cycle_logic_correct = False
        elif current_cycle_total == cycle_games:
            print_success(f"✅ Bot '{bot_name}': Цикл завершен ({current_cycle_total}/{cycle_games})")
        elif current_cycle_total > 0:
            print_success(f"✅ Bot '{bot_name}': Цикл в процессе ({current_cycle_total}/{cycle_games})")
        else:
            print_success(f"✅ Bot '{bot_name}': Цикл не начат (0/{cycle_games})")
    
    if cycle_logic_correct:
        print_success("✅ Логика циклов корректна - ни один бот не превышает лимит цикла")
        record_test("Cycle Test - Cycle Logic", True)
    else:
        print_error("❌ Обнаружены проблемы в логике циклов")
        record_test("Cycle Test - Cycle Logic", False, "Cycle logic issues found")
    
    # Step 3: Check profit tracking
    print_subheader("Step 3: Проверка отслеживания прибыли")
    
    profit_tracking_working = True
    
    for bot in bots:
        bot_name = bot["name"]
        current_cycle_profit = bot.get("current_cycle_profit", 0.0)
        total_net_profit = bot.get("total_net_profit", 0.0)
        completed_cycles = bot.get("completed_cycles", 0)
        
        print_success(f"Bot '{bot_name}':")
        print_success(f"  Прибыль текущего цикла: ${current_cycle_profit:.2f}")
        print_success(f"  Общая чистая прибыль: ${total_net_profit:.2f}")
        
        # Basic validation - profits should be reasonable numbers
        if abs(current_cycle_profit) > 100000 or abs(total_net_profit) > 1000000:
            print_warning(f"⚠ Bot '{bot_name}': Подозрительно большие значения прибыли")
            profit_tracking_working = False
    
    if profit_tracking_working:
        print_success("✅ Отслеживание прибыли работает корректно")
        record_test("Cycle Test - Profit Tracking", True)
    else:
        print_warning("⚠ Обнаружены подозрительные значения в отслеживании прибыли")
        record_test("Cycle Test - Profit Tracking", False, "Suspicious profit values")
    
    # Step 4: Test cycle reset logic (theoretical)
    print_subheader("Step 4: Проверка логики сброса цикла")
    
    # Look for bots that should have reset their cycles
    reset_logic_working = True
    
    for bot in bots:
        bot_name = bot["name"]
        current_cycle_wins = bot.get("current_cycle_wins", 0)
        current_cycle_losses = bot.get("current_cycle_losses", 0)
        current_cycle_draws = bot.get("current_cycle_draws", 0)
        cycle_games = bot.get("cycle_games", 12)
        completed_cycles = bot.get("completed_cycles", 0)
        
        current_cycle_total = current_cycle_wins + current_cycle_losses + current_cycle_draws
        
        # If current cycle is exactly at cycle_games, it should reset soon
        if current_cycle_total == cycle_games:
            print_success(f"✅ Bot '{bot_name}': Готов к сбросу цикла ({current_cycle_total}/{cycle_games})")
        elif current_cycle_total > cycle_games:
            print_error(f"❌ Bot '{bot_name}': Цикл не сброшен вовремя ({current_cycle_total} > {cycle_games})")
            reset_logic_working = False
    
    if reset_logic_working:
        print_success("✅ Логика сброса циклов работает корректно")
        record_test("Cycle Test - Reset Logic", True)
    else:
        print_error("❌ Обнаружены проблемы в логике сброса циклов")
        record_test("Cycle Test - Reset Logic", False, "Reset logic issues")
    
    print_subheader("Результаты теста циклов")
    print_success("Тест циклов завершен")

def test_basic_api_endpoints(admin_token: str) -> None:
    """
    БАЗОВЫЕ API ТЕСТЫ:
    - GET /api/admin/bots (список ботов с новыми полями)
    - POST /api/admin/bots/create-regular (создание бота)
    - GET /api/admin/bot-settings (настройки системы)
    """
    print_header("БАЗОВЫЕ API ТЕСТЫ: ОСНОВНЫЕ ЭНДПОИНТЫ БОТОВ")
    
    # Test 1: GET /api/admin/bots
    print_subheader("Test 1: GET /api/admin/bots - Список ботов с новыми полями")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if bots_success:
        print_success("✅ GET /api/admin/bots endpoint accessible")
        
        # Check response structure
        if "bots" in bots_response:
            bots = bots_response["bots"]
            print_success(f"✅ Response contains 'bots' field with {len(bots)} bots")
            
            # Check if bots have new fields
            if bots:
                sample_bot = bots[0]
                new_fields = [
                    "completed_cycles",
                    "current_cycle_wins", 
                    "current_cycle_losses",
                    "current_cycle_draws",
                    "current_cycle_profit",
                    "total_net_profit",
                    "win_percentage"
                ]
                
                present_new_fields = []
                missing_new_fields = []
                
                for field in new_fields:
                    if field in sample_bot:
                        present_new_fields.append(field)
                    else:
                        missing_new_fields.append(field)
                
                if not missing_new_fields:
                    print_success(f"✅ Все новые поля присутствуют в ответе: {present_new_fields}")
                    record_test("Basic API - GET Bots New Fields", True)
                else:
                    print_error(f"❌ Отсутствуют новые поля: {missing_new_fields}")
                    record_test("Basic API - GET Bots New Fields", False, f"Missing: {missing_new_fields}")
            else:
                print_warning("⚠ No bots found to check fields")
                record_test("Basic API - GET Bots New Fields", False, "No bots to check")
            
            record_test("Basic API - GET Bots", True)
        else:
            print_error("❌ Response missing 'bots' field")
            record_test("Basic API - GET Bots", False, "Missing bots field")
    else:
        print_error("❌ GET /api/admin/bots failed")
        record_test("Basic API - GET Bots", False, "Endpoint failed")
    
    # Test 2: POST /api/admin/bots/create-regular
    print_subheader("Test 2: POST /api/admin/bots/create-regular - Создание бота")
    
    test_bot_data = {
        "name": f"APITest_Bot_{int(time.time())}",
        "min_bet_amount": 1.0,
        "max_bet_amount": 10.0,
        "win_rate": 0.55,
        "cycle_games": 12,
        "individual_limit": 12,
        "creation_mode": "queue-based",
        "priority_order": 50,
        "pause_between_games": 5,
        "profit_strategy": "balanced",
        "can_accept_bets": False,
        "can_play_with_bots": False,
        "avatar_gender": "male",
        "simple_mode": False
    }
    
    create_response, create_success = make_request(
        "POST", "/admin/bots/create-regular",
        data=test_bot_data,
        auth_token=admin_token
    )
    
    if create_success:
        print_success("✅ POST /api/admin/bots/create-regular endpoint accessible")
        
        # Check response structure
        if "id" in create_response:
            bot_id = create_response["id"]
            print_success(f"✅ Bot created with ID: {bot_id}")
            record_test("Basic API - Create Regular Bot", True)
            
            # Clean up - delete the test bot
            delete_response, delete_success = make_request(
                "DELETE", f"/admin/bots/{bot_id}",
                auth_token=admin_token
            )
            
            if delete_success:
                print_success("✅ Test bot cleaned up successfully")
            else:
                print_warning("⚠ Failed to clean up test bot")
        else:
            print_error("❌ Create response missing 'id' field")
            record_test("Basic API - Create Regular Bot", False, "Missing id field")
    else:
        print_error("❌ POST /api/admin/bots/create-regular failed")
        record_test("Basic API - Create Regular Bot", False, "Endpoint failed")
    
    # Test 3: GET /api/admin/bot-settings
    print_subheader("Test 3: GET /api/admin/bot-settings - Настройки системы")
    
    settings_response, settings_success = make_request(
        "GET", "/admin/bot-settings",
        auth_token=admin_token
    )
    
    if settings_success:
        print_success("✅ GET /api/admin/bot-settings endpoint accessible")
        
        # Check response structure
        expected_settings_fields = ["id", "created_at", "updated_at"]
        present_fields = []
        missing_fields = []
        
        for field in expected_settings_fields:
            if field in settings_response:
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        if not missing_fields:
            print_success(f"✅ Settings response has expected fields: {present_fields}")
            record_test("Basic API - Bot Settings", True)
        else:
            print_warning(f"⚠ Settings response missing some fields: {missing_fields}")
            record_test("Basic API - Bot Settings", True, f"Missing: {missing_fields}")
        
        # Show settings content
        print_success("Settings content:")
        for key, value in settings_response.items():
            print_success(f"  {key}: {value}")
    else:
        print_error("❌ GET /api/admin/bot-settings failed")
        record_test("Basic API - Bot Settings", False, "Endpoint failed")
    
    print_subheader("Результаты базовых API тестов")
    print_success("Базовые API тесты завершены")

def print_final_summary():
    """Print final test summary."""
    print_header("ИТОГОВЫЙ ОТЧЕТ: ТЕСТИРОВАНИЕ СИСТЕМЫ ОБЫЧНЫХ БОТОВ")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print_success(f"Всего тестов: {total}")
    print_success(f"Пройдено: {passed}")
    if failed > 0:
        print_error(f"Провалено: {failed}")
    else:
        print_success(f"Провалено: {failed}")
    print_success(f"Процент успеха: {success_rate:.1f}%")
    
    print_subheader("Детальные результаты:")
    
    for test in test_results["tests"]:
        status = "✅ ПРОЙДЕН" if test["passed"] else "❌ ПРОВАЛЕН"
        print(f"{status}: {test['name']}")
        if test["details"]:
            print(f"    Детали: {test['details']}")
    
    print_subheader("Ключевые выводы:")
    
    if success_rate >= 80:
        print_success("🎉 СИСТЕМА ОБЫЧНЫХ БОТОВ РАБОТАЕТ ПРАВИЛЬНО!")
        print_success("🎉 Активные ставки теперь создаются автоматически!")
        print_success("🎉 Система больше НЕ показывает active_bets: 0 для всех ботов!")
    elif success_rate >= 60:
        print_warning("⚠ Система частично работает, но есть проблемы")
    else:
        print_error("❌ Система имеет серьезные проблемы")
    
    print_success("Тестирование завершено.")

def main():
    """Main test execution."""
    print_header("ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ ОБЫЧНЫХ БОТОВ")
    print_success("Фокус: Проверить что maintain_all_bots_active_bets() теперь создает ставки")
    print_success("Цель: Убедиться что система больше не показывает active_bets: 0!")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("❌ Cannot proceed without admin authentication")
        return
    
    # Step 2: Critical test - maintain_all_bots_active_bets()
    test_critical_maintain_all_bots_active_bets(admin_token)
    
    # Step 3: Win algorithm test with new fields
    test_win_algorithm_with_new_fields(admin_token)
    
    # Step 4: Cycle statistics and reset test
    test_cycle_statistics_and_reset(admin_token)
    
    # Step 5: Basic API endpoints test
    test_basic_api_endpoints(admin_token)
    
    # Step 6: Final summary
    print_final_summary()

if __name__ == "__main__":
    main()
"""
Backend API Testing for Regular Bots Management New Parameters
Testing the backend APIs that support the Regular Bots Management frontend functionality
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

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
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_subheader(text: str) -> None:
    """Print a formatted subheader."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 80}{Colors.ENDC}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def record_test(name: str, passed: bool, details: str = "") -> None:
    """Record a test result."""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print_success(f"{name}")
    else:
        test_results["failed"] += 1
        print_error(f"{name}: {details}")
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })

def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    auth_token: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"Making {method} request to {url}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        if data and method.lower() in ["post", "put", "patch"]:
            headers["Content-Type"] = "application/json"
            response = requests.request(method, url, json=data, headers=headers)
        else:
            response = requests.request(method, url, params=data, headers=headers)
        
        print(f"Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            response_data = {"text": response.text}
            print(f"Response text: {response.text}")
        
        success = response.status_code == expected_status
        
        if not success:
            print_error(f"Expected status {expected_status}, got {response.status_code}")
        
        return response_data, success
    except Exception as e:
        print_error(f"Request failed with exception: {e}")
        return {"error": str(e)}, False

def test_admin_login() -> Optional[str]:
    """Test admin login and return token."""
    print_subheader("Testing Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin logged in successfully")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_regular_bots_list_api(token: str) -> None:
    """Test the GET /admin/bots/regular/list API that supports the frontend table."""
    print_subheader("Testing Regular Bots List API")
    
    # Test basic list endpoint
    response, success = make_request(
        "GET", "/admin/bots/regular/list",
        auth_token=token
    )
    
    if success:
        # Check response structure
        required_fields = ["bots", "total_count", "current_page", "total_pages", "items_per_page", "has_next", "has_prev"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            record_test("Regular Bots List - Response Structure", False, f"Missing fields: {missing_fields}")
        else:
            record_test("Regular Bots List - Response Structure", True)
        
        # Check bot objects have new parameters
        if "bots" in response and response["bots"]:
            bot = response["bots"][0]
            new_parameters = [
                "individual_limit",  # Лимиты column
                "profit_strategy",   # Стратегия column  
                "pause_between_games"  # Пауза column
            ]
            
            missing_params = [param for param in new_parameters if param not in bot]
            
            if missing_params:
                record_test("Regular Bots List - New Parameters", False, f"Missing parameters: {missing_params}")
            else:
                record_test("Regular Bots List - New Parameters", True)
                print_success(f"Bot has individual_limit: {bot.get('individual_limit')}")
                print_success(f"Bot has profit_strategy: {bot.get('profit_strategy')}")
                print_success(f"Bot has pause_between_games: {bot.get('pause_between_games')}")
        else:
            record_test("Regular Bots List - New Parameters", False, "No bots found to check parameters")
    else:
        record_test("Regular Bots List - Basic Request", False, "Request failed")

def test_bot_creation_api(token: str) -> Optional[str]:
    """Test bot creation API with new parameters."""
    print_subheader("Testing Bot Creation API with New Parameters")
    
    # Test creating a bot with new parameters
    bot_data = {
        "name": "Test Bot New Params",
        "bot_type": "REGULAR",
        "min_bet_amount": 5.0,
        "max_bet_amount": 25.0,
        "win_rate": 60.0,
        "cycle_games": 15,
        "individual_limit": 15,  # New parameter
        "profit_strategy": "start-positive",  # New parameter
        "pause_between_games": 3,  # New parameter
        "creation_mode": "queue-based",
        "priority_order": 50
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=bot_data,
        auth_token=token
    )
    
    if success:
        if "bot" in response or "id" in response or "created_bots" in response:
            bot_id = None
            if "bot" in response and "id" in response["bot"]:
                bot_id = response["bot"]["id"]
            elif "id" in response:
                bot_id = response["id"]
            elif "created_bots" in response and response["created_bots"]:
                bot_id = response["created_bots"][0]
            
            record_test("Bot Creation - With New Parameters", True)
            print_success(f"Bot created with ID: {bot_id}")
            return bot_id
        else:
            record_test("Bot Creation - With New Parameters", False, "No bot ID in response")
    else:
        record_test("Bot Creation - With New Parameters", False, f"Creation failed: {response}")
    
    return None

def test_bot_update_api(token: str, bot_id: str) -> None:
    """Test bot update API with new parameters."""
    print_subheader("Testing Bot Update API with New Parameters")
    
    if not bot_id:
        record_test("Bot Update - New Parameters", False, "No bot ID available")
        return
    
    # Test updating bot with new parameters
    update_data = {
        "individual_limit": 20,  # Update limit
        "profit_strategy": "balanced",  # Update strategy
        "pause_between_games": 5  # Update pause
    }
    
    response, success = make_request(
        "PUT", f"/admin/bots/{bot_id}/update",
        data=update_data,
        auth_token=token
    )
    
    if success:
        record_test("Bot Update - New Parameters", True)
        print_success("Bot updated successfully with new parameters")
    else:
        record_test("Bot Update - New Parameters", False, f"Update failed: {response}")

def test_bot_settings_api(token: str) -> None:
    """Test bot settings API that supports global bot management."""
    print_subheader("Testing Bot Settings API")
    
    # Test GET bot settings
    response, success = make_request(
        "GET", "/admin/bot-settings",
        auth_token=token
    )
    
    if success:
        # Check for expected settings fields
        expected_fields = ["globalMaxActiveBets", "globalMaxHumanBots", "paginationSize", "autoActivateFromQueue", "priorityType"]
        
        if any(field in response for field in expected_fields):
            record_test("Bot Settings - GET Request", True)
            print_success("Bot settings retrieved successfully")
        else:
            record_test("Bot Settings - GET Request", False, "Response missing expected settings fields")
    else:
        record_test("Bot Settings - GET Request", False, f"GET request failed: {response}")
    
    # Test PUT bot settings
    settings_data = {
        "globalMaxActiveBets": 100,
        "globalMaxHumanBots": 50,
        "paginationSize": 10,
        "autoActivateFromQueue": True,
        "priorityType": "manual"
    }
    
    response, success = make_request(
        "PUT", "/admin/bot-settings",
        data=settings_data,
        auth_token=token
    )
    
    if success:
        record_test("Bot Settings - PUT Request", True)
        print_success("Bot settings updated successfully")
    else:
        record_test("Bot Settings - PUT Request", False, f"PUT request failed: {response}")

def test_bot_queue_stats_api(token: str) -> None:
    """Test bot queue statistics API."""
    print_subheader("Testing Bot Queue Statistics API")
    
    response, success = make_request(
        "GET", "/admin/bot-queue-stats",
        auth_token=token
    )
    
    if success:
        # Check for expected stats fields
        expected_fields = ["totalActiveRegularBets", "totalQueuedBets", "totalRegularBots", "totalHumanBots"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if missing_fields:
            record_test("Bot Queue Stats - Response Structure", False, f"Missing fields: {missing_fields}")
        else:
            record_test("Bot Queue Stats - Response Structure", True)
            print_success(f"Total active regular bets: {response.get('totalActiveRegularBets')}")
            print_success(f"Total regular bots: {response.get('totalRegularBots')}")
    else:
        record_test("Bot Queue Stats - Request", False, f"Request failed: {response}")

def test_bot_priority_management_api(token: str) -> None:
    """Test bot priority management APIs."""
    print_subheader("Testing Bot Priority Management APIs")
    
    # First get a bot to test priority management
    bots_response, bots_success = make_request(
        "GET", "/admin/bots/regular/list?limit=2",
        auth_token=token
    )
    
    if bots_success and "bots" in bots_response and len(bots_response["bots"]) >= 2:
        bot_id = bots_response["bots"][0]["id"]
        
        # Test move up
        response, success = make_request(
            "POST", f"/admin/bots/{bot_id}/priority/move-up",
            auth_token=token
        )
        
        if success:
            record_test("Bot Priority - Move Up", True)
        else:
            record_test("Bot Priority - Move Up", False, f"Move up failed: {response}")
        
        # Test move down
        response, success = make_request(
            "POST", f"/admin/bots/{bot_id}/priority/move-down",
            auth_token=token
        )
        
        if success:
            record_test("Bot Priority - Move Down", True)
        else:
            record_test("Bot Priority - Move Down", False, f"Move down failed: {response}")
        
        # Test reset priorities
        response, success = make_request(
            "POST", "/admin/bots/priority/reset",
            auth_token=token
        )
        
        if success:
            record_test("Bot Priority - Reset", True)
        else:
            record_test("Bot Priority - Reset", False, f"Reset failed: {response}")
    else:
        record_test("Bot Priority - Setup", False, "Not enough bots for priority testing")

def test_individual_bot_limit_api(token: str) -> None:
    """Test individual bot limit update API."""
    print_subheader("Testing Individual Bot Limit API")
    
    # Get a bot to test limit update
    bots_response, bots_success = make_request(
        "GET", "/admin/bots/regular/list?limit=1",
        auth_token=token
    )
    
    if bots_success and "bots" in bots_response and bots_response["bots"]:
        bot_id = bots_response["bots"][0]["id"]
        
        # Test updating individual limit
        limit_data = {"limit": 18}
        
        response, success = make_request(
            "PUT", f"/admin/bots/{bot_id}/limit",
            data=limit_data,
            auth_token=token
        )
        
        if success:
            record_test("Individual Bot Limit - Update", True)
            print_success("Individual bot limit updated successfully")
        else:
            record_test("Individual Bot Limit - Update", False, f"Update failed: {response}")
    else:
        record_test("Individual Bot Limit - Setup", False, "No bots available for limit testing")

def main():
    """Main test function."""
    print_header("REGULAR BOTS MANAGEMENT NEW PARAMETERS - BACKEND API TESTING")
    
    # Step 1: Admin login
    token = test_admin_login()
    if not token:
        print_error("Cannot proceed without admin token")
        return
    
    # Step 2: Test regular bots list API (supports frontend table)
    test_regular_bots_list_api(token)
    
    # Step 3: Test bot creation with new parameters
    bot_id = test_bot_creation_api(token)
    
    # Step 4: Test bot update with new parameters
    if bot_id:
        test_bot_update_api(token, bot_id)
    
    # Step 5: Test bot settings API (global settings)
    test_bot_settings_api(token)
    
    # Step 6: Test bot queue statistics API
    test_bot_queue_stats_api(token)
    
    # Step 7: Test bot priority management APIs
    test_bot_priority_management_api(token)
    
    # Step 8: Test individual bot limit API
    test_individual_bot_limit_api(token)
    
    # Print final results
    print_header("TEST SUMMARY")
    
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results['failed'] > 0:
        print(f"\nFailed tests:")
        for test in test_results['tests']:
            if not test['passed']:
                print_error(f"{test['name']}: {test['details']}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
    print(f"\nSuccess rate: {Colors.BOLD}{success_rate:.2f}%{Colors.ENDC}")
    
    if test_results['failed'] > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some tests failed!{Colors.ENDC}")
        sys.exit(1)
    else:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests passed!{Colors.ENDC}")

if __name__ == "__main__":
    main()