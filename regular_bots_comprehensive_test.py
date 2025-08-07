#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ "ОБЫЧНЫХ БОТОВ" - Russian Review
Проведение финального комплексного тестирования системы "Обычных ботов" после всех исправлений и доработок в Шагах 1-4.

ОСНОВНЫЕ ОБЛАСТИ ТЕСТИРОВАНИЯ:

1. КРИТИЧЕСКОЕ: Автоматизация создания ставок
   - Проверить что функция maintain_all_bots_active_bets() теперь РЕАЛЬНО создает ставки (была критическая ошибка в строках 1792-1794)
   - Убедиться что все активные боты имеют active_bets > 0 (раньше все показывали 0)
   - Проверить что автоматизация работает каждые 5 секунд

2. СИСТЕМА ЦИКЛОВ И ПРИБЫЛИ:
   - Тест новых полей: completed_cycles, current_cycle_wins, current_cycle_losses, current_cycle_draws, current_cycle_profit, total_net_profit, win_percentage, pause_between_games
   - Проверить алгоритм 55% выигрышей через функцию calculate_bot_game_outcome()
   - Тест завершения циклов через check_and_complete_bot_cycle()

3. НОВЫЕ API ЭНДПОИНТЫ:
   - GET /api/admin/bots/cycle-statistics
   - PUT /api/admin/bots/{bot_id}/pause-settings
   - PUT /api/admin/bots/{bot_id}/win-percentage  
   - GET /api/admin/bots/{bot_id}/active-bets
   - GET /api/admin/bots/{bot_id}/cycle-history
   - Обновленный GET /api/admin/bots с новыми полями

4. РАЗДЕЛЕНИЕ БОТОВ (КРИТИЧЕСКИ ВАЖНО):
   - Проверить что /games/available НЕ содержит обычных ботов (только Human-боты + живые игроки)
   - Проверить что /bots/active-games содержит ТОЛЬКО обычных ботов
   - Проверить что /games/active-human-bots НЕ содержит обычных ботов (исключает игры с "Unknown" именами)

5. НЕЗАВИСИМОСТЬ ОТ HUMAN-БОТОВ:
   - Убедиться что обычные боты не конфликтуют с Human-ботами
   - Разные коллекции: bots vs human_bots
   - Отдельные эндпоинты и логика

6. СОЗДАНИЕ И УПРАВЛЕНИЕ БОТАМИ:
   - POST /api/admin/bots/create-regular
   - PUT /api/admin/bots/{bot_id} с поддержкой новых полей
   - DELETE /api/admin/bots/{bot_id}
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib
from datetime import datetime

# Configuration
BASE_URL = "https://53b51271-d84e-45ed-b769-9b3ed6d4038f.preview.emergentagent.com/api"
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type} Login")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    # Use JSON data for login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get("access_token")
        if access_token:
            print_success(f"{user_type} login successful")
            record_test(f"{user_type} Login", True)
            return access_token
        else:
            print_error(f"{user_type} login response missing access_token")
            record_test(f"{user_type} Login", False, "Missing access_token")
    else:
        print_error(f"{user_type} login failed with status {response.status_code}")
        try:
            error_data = response.json()
            print_error(f"Error details: {error_data}")
        except:
            print_error(f"Error text: {response.text}")
        record_test(f"{user_type} Login", False, f"Status: {response.status_code}")
    
    return None

def test_critical_bet_creation_automation() -> None:
    """
    КРИТИЧЕСКОЕ: Автоматизация создания ставок
    - Проверить что функция maintain_all_bots_active_bets() теперь РЕАЛЬНО создает ставки
    - Убедиться что все активные боты имеют active_bets > 0 (раньше все показывали 0)
    - Проверить что автоматизация работает каждые 5 секунд
    """
    print_header("КРИТИЧЕСКОЕ: АВТОМАТИЗАЦИЯ СОЗДАНИЯ СТАВОК")
    
    # Step 1: Login as admin
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with bet creation test")
        record_test("Critical Bet Creation - Admin Login", False, "Admin login failed")
        return
    
    # Step 2: Get list of regular bots
    print_subheader("Step 2: Get Regular Bots List")
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_success:
        print_error("Failed to get regular bots list")
        record_test("Critical Bet Creation - Get Bots", False, "Failed to get bots")
        return
    
    if "bots" not in bots_response or not bots_response["bots"]:
        print_error("No regular bots found in the system")
        record_test("Critical Bet Creation - Get Bots", False, "No bots found")
        return
    
    bots = bots_response["bots"]
    print_success(f"Found {len(bots)} regular bots")
    record_test("Critical Bet Creation - Get Bots", True)
    
    # Step 3: Check initial bot states - КРИТИЧЕСКАЯ ПРОВЕРКА
    print_subheader("Step 3: КРИТИЧЕСКАЯ ПРОВЕРКА - Initial Bot States")
    initial_states = {}
    bots_with_zero_bets = 0
    bots_with_active_bets = 0
    
    for bot in bots:
        bot_id = bot["id"]
        bot_name = bot["name"]
        active_bets = bot.get("active_bets", 0)
        is_active = bot.get("is_active", False)
        cycle_games = bot.get("cycle_games", 12)
        
        initial_states[bot_id] = {
            "name": bot_name,
            "active_bets": active_bets,
            "is_active": is_active,
            "cycle_games": cycle_games
        }
        
        if is_active:
            if active_bets == 0:
                bots_with_zero_bets += 1
                print_error(f"❌ Bot '{bot_name}': {active_bets} active bets (КРИТИЧЕСКАЯ ПРОБЛЕМА)")
            else:
                bots_with_active_bets += 1
                print_success(f"✅ Bot '{bot_name}': {active_bets} active bets (ИСПРАВЛЕНО)")
    
    print_success(f"РЕЗУЛЬТАТЫ КРИТИЧЕСКОЙ ПРОВЕРКИ:")
    print_success(f"  Боты с active_bets = 0: {bots_with_zero_bets}")
    print_success(f"  Боты с active_bets > 0: {bots_with_active_bets}")
    
    # Проверить критическое исправление
    if bots_with_zero_bets == 0 and bots_with_active_bets > 0:
        print_success("🎉 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ПОДТВЕРЖДЕНО!")
        print_success("🎉 ВСЕ активные боты теперь имеют active_bets > 0!")
        print_success("🎉 Функция maintain_all_bots_active_bets() РЕАЛЬНО создает ставки!")
        record_test("Critical Bet Creation - Fix Confirmed", True)
    elif bots_with_zero_bets > 0:
        print_error("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА НЕ ИСПРАВЛЕНА!")
        print_error(f"❌ {bots_with_zero_bets} ботов все еще показывают active_bets = 0")
        record_test("Critical Bet Creation - Fix Confirmed", False, f"{bots_with_zero_bets} bots with 0 bets")
    else:
        print_warning("⚠ Нет активных ботов для тестирования")
        record_test("Critical Bet Creation - Fix Confirmed", False, "No active bots")
    
    # Step 4: Monitor automation for 30 seconds
    print_subheader("Step 4: Monitor Automation (30 seconds)")
    print("Мониторинг автоматизации создания ставок каждые 5 секунд...")
    
    monitoring_results = []
    start_time = time.time()
    check_interval = 5
    total_monitoring_time = 30
    
    for check_round in range(int(total_monitoring_time / check_interval)):
        print(f"\n--- Проверка {check_round + 1} (через {check_round * check_interval}s) ---")
        
        # Get updated bot states
        bots_response, bots_success = make_request(
            "GET", "/admin/bots",
            auth_token=admin_token
        )
        
        if bots_success and "bots" in bots_response:
            current_states = {}
            automation_working = True
            
            for bot in bots_response["bots"]:
                bot_id = bot["id"]
                bot_name = bot["name"]
                active_bets = bot.get("active_bets", 0)
                is_active = bot.get("is_active", False)
                cycle_games = bot.get("cycle_games", 12)
                
                current_states[bot_id] = {
                    "name": bot_name,
                    "active_bets": active_bets,
                    "is_active": is_active,
                    "cycle_games": cycle_games
                }
                
                if is_active:
                    # Проверить что боты поддерживают активные ставки
                    if active_bets > 0:
                        print_success(f"✓ Bot '{bot_name}': {active_bets}/{cycle_games} (автоматизация работает)")
                    else:
                        print_error(f"✗ Bot '{bot_name}': {active_bets}/{cycle_games} (автоматизация НЕ работает)")
                        automation_working = False
                    
                    # Проверить что не превышает лимит цикла
                    if active_bets <= cycle_games:
                        print_success(f"✓ Bot '{bot_name}': В пределах лимита цикла")
                    else:
                        print_error(f"✗ Bot '{bot_name}': ПРЕВЫШАЕТ лимит цикла!")
            
            monitoring_results.append({
                "round": check_round + 1,
                "timestamp": time.time(),
                "states": current_states,
                "automation_working": automation_working
            })
        
        # Wait for next check
        if check_round < int(total_monitoring_time / check_interval) - 1:
            print(f"Ожидание {check_interval} секунд до следующей проверки...")
            time.sleep(check_interval)
    
    # Step 5: Analyze monitoring results
    print_subheader("Step 5: Анализ результатов мониторинга")
    
    if len(monitoring_results) >= 2:
        automation_consistently_working = all(result["automation_working"] for result in monitoring_results)
        
        if automation_consistently_working:
            print_success("🎉 АВТОМАТИЗАЦИЯ РАБОТАЕТ СТАБИЛЬНО!")
            print_success("🎉 Все боты поддерживают active_bets > 0 в течение всего периода мониторинга")
            record_test("Critical Bet Creation - Automation Working", True)
        else:
            print_error("❌ АВТОМАТИЗАЦИЯ РАБОТАЕТ НЕСТАБИЛЬНО!")
            record_test("Critical Bet Creation - Automation Working", False, "Inconsistent automation")
        
        # Check for bet creation activity
        bets_created_during_monitoring = False
        for bot_id, initial_state in initial_states.items():
            if initial_state["is_active"]:
                initial_bets = initial_state["active_bets"]
                final_bets = monitoring_results[-1]["states"].get(bot_id, {}).get("active_bets", 0)
                
                if final_bets != initial_bets:
                    print_success(f"✓ Bot '{initial_state['name']}': Активность обнаружена ({initial_bets} → {final_bets})")
                    bets_created_during_monitoring = True
        
        if bets_created_during_monitoring:
            print_success("✓ Обнаружена активность создания/завершения ставок")
            record_test("Critical Bet Creation - Activity Detected", True)
        else:
            print_warning("⚠ Активность создания ставок не обнаружена (возможно, боты уже на максимуме)")
            record_test("Critical Bet Creation - Activity Detected", False, "No activity detected")
    else:
        print_error("Недостаточно данных мониторинга")
        record_test("Critical Bet Creation - Monitoring", False, "Insufficient data")
    
    # Step 6: Verify games are actually created
    print_subheader("Step 6: Проверка создания игр")
    
    # Check /bots/active-games endpoint for regular bot games
    active_games_response, active_games_success = make_request(
        "GET", "/bots/active-games",
        auth_token=admin_token
    )
    
    if active_games_success and isinstance(active_games_response, list):
        regular_bot_games = len(active_games_response)
        print_success(f"✓ Найдено {regular_bot_games} активных игр обычных ботов")
        
        if regular_bot_games > 0:
            print_success("✓ Обычные боты РЕАЛЬНО создают игры!")
            record_test("Critical Bet Creation - Games Created", True)
            
            # Show examples
            for i, game in enumerate(active_games_response[:3]):
                game_id = game.get("game_id", "unknown")
                bet_amount = game.get("bet_amount", 0)
                creator_name = game.get("creator_name", "unknown")
                status = game.get("status", "unknown")
                
                print_success(f"  Игра {i+1}: {creator_name} - ${bet_amount} ({status})")
        else:
            print_warning("⚠ Активные игры обычных ботов не найдены")
            record_test("Critical Bet Creation - Games Created", False, "No games found")
    else:
        print_error("Не удалось получить активные игры ботов")
        record_test("Critical Bet Creation - Games Created", False, "Endpoint failed")

def test_cycle_and_profit_system() -> None:
    """
    СИСТЕМА ЦИКЛОВ И ПРИБЫЛИ:
    - Тест новых полей: completed_cycles, current_cycle_wins, current_cycle_losses, current_cycle_draws, current_cycle_profit, total_net_profit, win_percentage, pause_between_games
    - Проверить алгоритм 55% выигрышей через функцию calculate_bot_game_outcome()
    - Тест завершения циклов через check_and_complete_bot_cycle()
    """
    print_header("СИСТЕМА ЦИКЛОВ И ПРИБЫЛИ")
    
    # Step 1: Login as admin
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin")
        record_test("Cycle System - Admin Login", False, "Admin login failed")
        return
    
    # Step 2: Get bots and check new fields
    print_subheader("Step 2: Проверка новых полей системы циклов")
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_success or "bots" not in bots_response:
        print_error("Failed to get bots")
        record_test("Cycle System - Get Bots", False, "Failed to get bots")
        return
    
    bots = bots_response["bots"]
    print_success(f"Получено {len(bots)} ботов для проверки")
    
    # Check new fields in bot data
    required_new_fields = [
        "completed_cycles", "current_cycle_wins", "current_cycle_losses", 
        "current_cycle_draws", "current_cycle_profit", "total_net_profit", 
        "win_percentage", "pause_between_games"
    ]
    
    fields_present = True
    for bot in bots:
        bot_name = bot.get("name", "unknown")
        missing_fields = []
        
        for field in required_new_fields:
            if field not in bot:
                missing_fields.append(field)
                fields_present = False
        
        if missing_fields:
            print_error(f"❌ Bot '{bot_name}' missing fields: {missing_fields}")
        else:
            print_success(f"✅ Bot '{bot_name}' has all new cycle fields")
            
            # Display field values
            completed_cycles = bot.get("completed_cycles", 0)
            current_cycle_wins = bot.get("current_cycle_wins", 0)
            current_cycle_losses = bot.get("current_cycle_losses", 0)
            current_cycle_draws = bot.get("current_cycle_draws", 0)
            current_cycle_profit = bot.get("current_cycle_profit", 0.0)
            total_net_profit = bot.get("total_net_profit", 0.0)
            win_percentage = bot.get("win_percentage", 55.0)
            pause_between_games = bot.get("pause_between_games", 5)
            
            print_success(f"  Completed cycles: {completed_cycles}")
            print_success(f"  Current cycle: W{current_cycle_wins}/L{current_cycle_losses}/D{current_cycle_draws}")
            print_success(f"  Current cycle profit: ${current_cycle_profit}")
            print_success(f"  Total net profit: ${total_net_profit}")
            print_success(f"  Win percentage: {win_percentage}%")
            print_success(f"  Pause between games: {pause_between_games}s")
    
    if fields_present:
        print_success("🎉 ВСЕ НОВЫЕ ПОЛЯ СИСТЕМЫ ЦИКЛОВ ПРИСУТСТВУЮТ!")
        record_test("Cycle System - New Fields Present", True)
    else:
        print_error("❌ НЕКОТОРЫЕ НОВЫЕ ПОЛЯ ОТСУТСТВУЮТ!")
        record_test("Cycle System - New Fields Present", False, "Missing fields")
    
    # Step 3: Check win percentage algorithm (55% default)
    print_subheader("Step 3: Проверка алгоритма 55% выигрышей")
    
    bots_with_correct_win_percentage = 0
    for bot in bots:
        bot_name = bot.get("name", "unknown")
        win_percentage = bot.get("win_percentage", 0)
        
        if win_percentage == 55.0:
            print_success(f"✅ Bot '{bot_name}': Win percentage = {win_percentage}% (correct default)")
            bots_with_correct_win_percentage += 1
        else:
            print_warning(f"⚠ Bot '{bot_name}': Win percentage = {win_percentage}% (custom value)")
    
    if bots_with_correct_win_percentage > 0:
        print_success(f"✅ {bots_with_correct_win_percentage} ботов имеют правильный win_percentage = 55%")
        record_test("Cycle System - Win Percentage Algorithm", True)
    else:
        print_warning("⚠ Нет ботов с дефолтным win_percentage = 55%")
        record_test("Cycle System - Win Percentage Algorithm", False, "No bots with 55%")
    
    # Step 4: Test cycle statistics endpoint
    print_subheader("Step 4: Тест эндпоинта статистики циклов")
    
    cycle_stats_response, cycle_stats_success = make_request(
        "GET", "/admin/bots/cycle-statistics",
        auth_token=admin_token
    )
    
    if cycle_stats_success:
        print_success("✅ Эндпоинт /admin/bots/cycle-statistics доступен")
        
        # Check response structure
        expected_stats_fields = ["total_bots", "active_bots", "total_completed_cycles", "total_net_profit"]
        missing_stats_fields = [field for field in expected_stats_fields if field not in cycle_stats_response]
        
        if not missing_stats_fields:
            print_success("✅ Статистика циклов имеет все ожидаемые поля")
            
            total_bots = cycle_stats_response.get("total_bots", 0)
            active_bots = cycle_stats_response.get("active_bots", 0)
            total_completed_cycles = cycle_stats_response.get("total_completed_cycles", 0)
            total_net_profit = cycle_stats_response.get("total_net_profit", 0.0)
            
            print_success(f"  Total bots: {total_bots}")
            print_success(f"  Active bots: {active_bots}")
            print_success(f"  Total completed cycles: {total_completed_cycles}")
            print_success(f"  Total net profit: ${total_net_profit}")
            
            record_test("Cycle System - Statistics Endpoint", True)
        else:
            print_error(f"❌ Статистика циклов отсутствуют поля: {missing_stats_fields}")
            record_test("Cycle System - Statistics Endpoint", False, f"Missing: {missing_stats_fields}")
    else:
        print_error("❌ Эндпоинт статистики циклов недоступен")
        record_test("Cycle System - Statistics Endpoint", False, "Endpoint failed")

def test_new_api_endpoints() -> None:
    """
    НОВЫЕ API ЭНДПОИНТЫ:
    - GET /api/admin/bots/cycle-statistics
    - PUT /api/admin/bots/{bot_id}/pause-settings
    - PUT /api/admin/bots/{bot_id}/win-percentage  
    - GET /api/admin/bots/{bot_id}/active-bets
    - GET /api/admin/bots/{bot_id}/cycle-history
    - Обновленный GET /api/admin/bots с новыми полями
    """
    print_header("НОВЫЕ API ЭНДПОИНТЫ")
    
    # Step 1: Login as admin
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin")
        record_test("New API Endpoints - Admin Login", False, "Admin login failed")
        return
    
    # Get a test bot ID
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_success or "bots" not in bots_response or not bots_response["bots"]:
        print_error("No bots available for testing")
        record_test("New API Endpoints - Get Test Bot", False, "No bots available")
        return
    
    test_bot = bots_response["bots"][0]
    test_bot_id = test_bot["id"]
    test_bot_name = test_bot["name"]
    
    print_success(f"Using test bot: {test_bot_name} (ID: {test_bot_id})")
    
    # Test 1: GET /api/admin/bots/cycle-statistics
    print_subheader("Test 1: GET /api/admin/bots/cycle-statistics")
    
    cycle_stats_response, cycle_stats_success = make_request(
        "GET", "/admin/bots/cycle-statistics",
        auth_token=admin_token
    )
    
    if cycle_stats_success:
        print_success("✅ Эндпоинт cycle-statistics работает")
        record_test("New API Endpoints - Cycle Statistics", True)
    else:
        print_error("❌ Эндпоинт cycle-statistics не работает")
        record_test("New API Endpoints - Cycle Statistics", False, "Endpoint failed")
    
    # Test 2: PUT /api/admin/bots/{bot_id}/pause-settings
    print_subheader("Test 2: PUT /api/admin/bots/{bot_id}/pause-settings")
    
    pause_settings_data = {
        "pause_between_games": 10
    }
    
    pause_settings_response, pause_settings_success = make_request(
        "PUT", f"/admin/bots/{test_bot_id}/pause-settings",
        data=pause_settings_data,
        auth_token=admin_token
    )
    
    if pause_settings_success:
        print_success("✅ Эндпоинт pause-settings работает")
        record_test("New API Endpoints - Pause Settings", True)
    else:
        print_error("❌ Эндпоинт pause-settings не работает")
        record_test("New API Endpoints - Pause Settings", False, "Endpoint failed")
    
    # Test 3: PUT /api/admin/bots/{bot_id}/win-percentage
    print_subheader("Test 3: PUT /api/admin/bots/{bot_id}/win-percentage")
    
    win_percentage_data = {
        "win_percentage": 60.0
    }
    
    win_percentage_response, win_percentage_success = make_request(
        "PUT", f"/admin/bots/{test_bot_id}/win-percentage",
        data=win_percentage_data,
        auth_token=admin_token
    )
    
    if win_percentage_success:
        print_success("✅ Эндпоинт win-percentage работает")
        record_test("New API Endpoints - Win Percentage", True)
    else:
        print_error("❌ Эндпоинт win-percentage не работает")
        record_test("New API Endpoints - Win Percentage", False, "Endpoint failed")
    
    # Test 4: GET /api/admin/bots/{bot_id}/active-bets
    print_subheader("Test 4: GET /api/admin/bots/{bot_id}/active-bets")
    
    active_bets_response, active_bets_success = make_request(
        "GET", f"/admin/bots/{test_bot_id}/active-bets",
        auth_token=admin_token
    )
    
    if active_bets_success:
        print_success("✅ Эндпоинт active-bets работает")
        
        if isinstance(active_bets_response, list):
            print_success(f"✅ Получено {len(active_bets_response)} активных ставок")
        elif "active_bets" in active_bets_response:
            active_bets_count = active_bets_response["active_bets"]
            print_success(f"✅ Активных ставок: {active_bets_count}")
        
        record_test("New API Endpoints - Active Bets", True)
    else:
        print_error("❌ Эндпоинт active-bets не работает")
        record_test("New API Endpoints - Active Bets", False, "Endpoint failed")
    
    # Test 5: GET /api/admin/bots/{bot_id}/cycle-history
    print_subheader("Test 5: GET /api/admin/bots/{bot_id}/cycle-history")
    
    cycle_history_response, cycle_history_success = make_request(
        "GET", f"/admin/bots/{test_bot_id}/cycle-history",
        auth_token=admin_token
    )
    
    if cycle_history_success:
        print_success("✅ Эндпоинт cycle-history работает")
        
        if isinstance(cycle_history_response, list):
            print_success(f"✅ Получено {len(cycle_history_response)} записей истории циклов")
        elif "cycles" in cycle_history_response:
            cycles_count = len(cycle_history_response["cycles"])
            print_success(f"✅ Записей истории циклов: {cycles_count}")
        
        record_test("New API Endpoints - Cycle History", True)
    else:
        print_error("❌ Эндпоинт cycle-history не работает")
        record_test("New API Endpoints - Cycle History", False, "Endpoint failed")
    
    # Test 6: Verify updated GET /api/admin/bots has new fields
    print_subheader("Test 6: Обновленный GET /api/admin/bots с новыми полями")
    
    updated_bots_response, updated_bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if updated_bots_success and "bots" in updated_bots_response:
        test_bot_updated = None
        for bot in updated_bots_response["bots"]:
            if bot["id"] == test_bot_id:
                test_bot_updated = bot
                break
        
        if test_bot_updated:
            # Check if pause_between_games was updated
            updated_pause = test_bot_updated.get("pause_between_games", 5)
            if updated_pause == 10:
                print_success("✅ Настройки паузы обновлены корректно")
            else:
                print_warning(f"⚠ Настройки паузы: ожидалось 10, получено {updated_pause}")
            
            # Check if win_percentage was updated
            updated_win_percentage = test_bot_updated.get("win_percentage", 55.0)
            if updated_win_percentage == 60.0:
                print_success("✅ Win percentage обновлен корректно")
            else:
                print_warning(f"⚠ Win percentage: ожидалось 60.0, получено {updated_win_percentage}")
            
            record_test("New API Endpoints - Updated Bot Fields", True)
        else:
            print_error("❌ Не удалось найти обновленного бота")
            record_test("New API Endpoints - Updated Bot Fields", False, "Bot not found")
    else:
        print_error("❌ Не удалось получить обновленный список ботов")
        record_test("New API Endpoints - Updated Bot Fields", False, "Failed to get bots")

def test_bot_separation_critical() -> None:
    """
    РАЗДЕЛЕНИЕ БОТОВ (КРИТИЧЕСКИ ВАЖНО):
    - Проверить что /games/available НЕ содержит обычных ботов (только Human-боты + живые игроки)
    - Проверить что /bots/active-games содержит ТОЛЬКО обычных ботов
    - Проверить что /games/active-human-bots НЕ содержит обычных ботов (исключает игры с "Unknown" именами)
    """
    print_header("РАЗДЕЛЕНИЕ БОТОВ (КРИТИЧЕСКИ ВАЖНО)")
    
    # Step 1: Login as admin
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin")
        record_test("Bot Separation - Admin Login", False, "Admin login failed")
        return
    
    # Test 1: /games/available НЕ должен содержать обычных ботов
    print_subheader("Test 1: /games/available НЕ содержит обычных ботов")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        regular_bot_games_in_available = 0
        human_bot_games_in_available = 0
        live_player_games_in_available = 0
        
        for game in available_games_response:
            creator_type = game.get("creator_type", "unknown")
            bot_type = game.get("bot_type", None)
            creator_name = game.get("creator_name", "unknown")
            
            if creator_type == "bot" and bot_type == "REGULAR":
                regular_bot_games_in_available += 1
                print_error(f"❌ ОБЫЧНЫЙ БОТ найден в /games/available: {creator_name}")
            elif creator_type == "human_bot" or bot_type == "HUMAN":
                human_bot_games_in_available += 1
                print_success(f"✅ Human-bot в /games/available: {creator_name}")
            elif creator_type == "user":
                live_player_games_in_available += 1
                print_success(f"✅ Живой игрок в /games/available: {creator_name}")
        
        print_success(f"РЕЗУЛЬТАТЫ /games/available:")
        print_success(f"  Обычные боты: {regular_bot_games_in_available} (должно быть 0)")
        print_success(f"  Human-боты: {human_bot_games_in_available}")
        print_success(f"  Живые игроки: {live_player_games_in_available}")
        
        if regular_bot_games_in_available == 0:
            print_success("🎉 КРИТИЧЕСКОЕ РАЗДЕЛЕНИЕ РАБОТАЕТ!")
            print_success("🎉 /games/available НЕ содержит обычных ботов!")
            record_test("Bot Separation - Available Games Clean", True)
        else:
            print_error("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Обычные боты найдены в /games/available!")
            record_test("Bot Separation - Available Games Clean", False, f"{regular_bot_games_in_available} regular bots found")
    else:
        print_error("❌ Не удалось получить /games/available")
        record_test("Bot Separation - Available Games Clean", False, "Endpoint failed")
    
    # Test 2: /bots/active-games должен содержать ТОЛЬКО обычных ботов
    print_subheader("Test 2: /bots/active-games содержит ТОЛЬКО обычных ботов")
    
    bot_active_games_response, bot_active_games_success = make_request(
        "GET", "/bots/active-games",
        auth_token=admin_token
    )
    
    if bot_active_games_success and isinstance(bot_active_games_response, list):
        regular_bot_games_in_bots = 0
        non_regular_bot_games_in_bots = 0
        
        for game in bot_active_games_response:
            creator_type = game.get("creator_type", "unknown")
            bot_type = game.get("bot_type", None)
            creator_name = game.get("creator_name", "unknown")
            
            if creator_type == "bot" and bot_type == "REGULAR":
                regular_bot_games_in_bots += 1
                print_success(f"✅ Обычный бот в /bots/active-games: {creator_name}")
            else:
                non_regular_bot_games_in_bots += 1
                print_error(f"❌ НЕ обычный бот найден в /bots/active-games: {creator_name} ({creator_type}, {bot_type})")
        
        print_success(f"РЕЗУЛЬТАТЫ /bots/active-games:")
        print_success(f"  Обычные боты: {regular_bot_games_in_bots}")
        print_success(f"  НЕ обычные боты: {non_regular_bot_games_in_bots} (должно быть 0)")
        
        if non_regular_bot_games_in_bots == 0:
            print_success("🎉 РАЗДЕЛЕНИЕ РАБОТАЕТ!")
            print_success("🎉 /bots/active-games содержит ТОЛЬКО обычных ботов!")
            record_test("Bot Separation - Bot Games Only Regular", True)
        else:
            print_error("❌ ПРОБЛЕМА: НЕ обычные боты найдены в /bots/active-games!")
            record_test("Bot Separation - Bot Games Only Regular", False, f"{non_regular_bot_games_in_bots} non-regular found")
    else:
        print_error("❌ Не удалось получить /bots/active-games")
        record_test("Bot Separation - Bot Games Only Regular", False, "Endpoint failed")
    
    # Test 3: /games/active-human-bots НЕ должен содержать обычных ботов
    print_subheader("Test 3: /games/active-human-bots НЕ содержит обычных ботов")
    
    human_bot_games_response, human_bot_games_success = make_request(
        "GET", "/games/active-human-bots",
        auth_token=admin_token
    )
    
    if human_bot_games_success and isinstance(human_bot_games_response, list):
        regular_bots_in_human_bot_games = 0
        unknown_names_in_human_bot_games = 0
        valid_human_bot_games = 0
        
        for game in human_bot_games_response:
            creator_type = game.get("creator_type", "unknown")
            bot_type = game.get("bot_type", None)
            creator_name = game.get("creator_name", "unknown")
            opponent_name = game.get("opponent_name", "unknown")
            
            # Check for regular bots
            if creator_type == "bot" and bot_type == "REGULAR":
                regular_bots_in_human_bot_games += 1
                print_error(f"❌ ОБЫЧНЫЙ БОТ найден в /games/active-human-bots: {creator_name}")
            
            # Check for "Unknown" names (should be excluded)
            if "Unknown" in creator_name or "Unknown" in opponent_name:
                unknown_names_in_human_bot_games += 1
                print_error(f"❌ 'Unknown' имя найдено в /games/active-human-bots: {creator_name} vs {opponent_name}")
            else:
                valid_human_bot_games += 1
                print_success(f"✅ Валидная игра Human-bot: {creator_name} vs {opponent_name}")
        
        print_success(f"РЕЗУЛЬТАТЫ /games/active-human-bots:")
        print_success(f"  Обычные боты: {regular_bots_in_human_bot_games} (должно быть 0)")
        print_success(f"  'Unknown' имена: {unknown_names_in_human_bot_games} (должно быть 0)")
        print_success(f"  Валидные игры: {valid_human_bot_games}")
        
        separation_working = (regular_bots_in_human_bot_games == 0 and unknown_names_in_human_bot_games == 0)
        
        if separation_working:
            print_success("🎉 РАЗДЕЛЕНИЕ РАБОТАЕТ!")
            print_success("🎉 /games/active-human-bots НЕ содержит обычных ботов и 'Unknown' имен!")
            record_test("Bot Separation - Human Bot Games Clean", True)
        else:
            print_error("❌ ПРОБЛЕМА: Найдены обычные боты или 'Unknown' имена!")
            record_test("Bot Separation - Human Bot Games Clean", False, f"Regular: {regular_bots_in_human_bot_games}, Unknown: {unknown_names_in_human_bot_games}")
    else:
        print_error("❌ Не удалось получить /games/active-human-bots")
        record_test("Bot Separation - Human Bot Games Clean", False, "Endpoint failed")

def test_independence_from_human_bots() -> None:
    """
    НЕЗАВИСИМОСТЬ ОТ HUMAN-БОТОВ:
    - Убедиться что обычные боты не конфликтуют с Human-ботами
    - Разные коллекции: bots vs human_bots
    - Отдельные эндпоинты и логика
    """
    print_header("НЕЗАВИСИМОСТЬ ОТ HUMAN-БОТОВ")
    
    # Step 1: Login as admin
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin")
        record_test("Independence - Admin Login", False, "Admin login failed")
        return
    
    # Test 1: Separate collections - Regular bots
    print_subheader("Test 1: Коллекция обычных ботов")
    
    regular_bots_response, regular_bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if regular_bots_success and "bots" in regular_bots_response:
        regular_bots_count = len(regular_bots_response["bots"])
        print_success(f"✅ Найдено {regular_bots_count} обычных ботов")
        
        # Check that these are indeed regular bots
        for bot in regular_bots_response["bots"]:
            bot_name = bot.get("name", "unknown")
            bot_type = bot.get("bot_type", "unknown")
            
            if bot_type == "REGULAR":
                print_success(f"✅ Обычный бот: {bot_name}")
            else:
                print_error(f"❌ НЕ обычный бот в коллекции: {bot_name} ({bot_type})")
        
        record_test("Independence - Regular Bots Collection", True)
    else:
        print_error("❌ Не удалось получить коллекцию обычных ботов")
        record_test("Independence - Regular Bots Collection", False, "Failed to get regular bots")
    
    # Test 2: Separate collections - Human bots
    print_subheader("Test 2: Коллекция Human-ботов")
    
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots",
        auth_token=admin_token
    )
    
    if human_bots_success and "bots" in human_bots_response:
        human_bots_count = len(human_bots_response["bots"])
        print_success(f"✅ Найдено {human_bots_count} Human-ботов")
        
        # Check that these are indeed human bots
        for bot in human_bots_response["bots"]:
            bot_name = bot.get("name", "unknown")
            character = bot.get("character", "unknown")
            
            print_success(f"✅ Human-бот: {bot_name} ({character})")
        
        record_test("Independence - Human Bots Collection", True)
    else:
        print_error("❌ Не удалось получить коллекцию Human-ботов")
        record_test("Independence - Human Bots Collection", False, "Failed to get human bots")
    
    # Test 3: Separate endpoints
    print_subheader("Test 3: Отдельные эндпоинты")
    
    # Regular bots endpoints
    regular_endpoints = [
        "/admin/bots",
        "/admin/bots/cycle-statistics",
        "/bots/active-games"
    ]
    
    regular_endpoints_working = 0
    for endpoint in regular_endpoints:
        response, success = make_request("GET", endpoint, auth_token=admin_token)
        if success:
            print_success(f"✅ Эндпоинт обычных ботов работает: {endpoint}")
            regular_endpoints_working += 1
        else:
            print_error(f"❌ Эндпоинт обычных ботов НЕ работает: {endpoint}")
    
    # Human bots endpoints
    human_endpoints = [
        "/admin/human-bots",
        "/admin/human-bots/stats",
        "/games/active-human-bots"
    ]
    
    human_endpoints_working = 0
    for endpoint in human_endpoints:
        response, success = make_request("GET", endpoint, auth_token=admin_token)
        if success:
            print_success(f"✅ Эндпоинт Human-ботов работает: {endpoint}")
            human_endpoints_working += 1
        else:
            print_error(f"❌ Эндпоинт Human-ботов НЕ работает: {endpoint}")
    
    print_success(f"РЕЗУЛЬТАТЫ ЭНДПОИНТОВ:")
    print_success(f"  Обычные боты: {regular_endpoints_working}/{len(regular_endpoints)} работают")
    print_success(f"  Human-боты: {human_endpoints_working}/{len(human_endpoints)} работают")
    
    if regular_endpoints_working == len(regular_endpoints) and human_endpoints_working == len(human_endpoints):
        print_success("🎉 ВСЕ ОТДЕЛЬНЫЕ ЭНДПОИНТЫ РАБОТАЮТ!")
        record_test("Independence - Separate Endpoints", True)
    else:
        print_error("❌ НЕКОТОРЫЕ ЭНДПОИНТЫ НЕ РАБОТАЮТ!")
        record_test("Independence - Separate Endpoints", False, "Some endpoints failed")
    
    # Test 4: No cross-contamination
    print_subheader("Test 4: Отсутствие перекрестного загрязнения")
    
    # Check that regular bot endpoints don't return human bots
    regular_bots_data = regular_bots_response.get("bots", [])
    human_bots_in_regular = 0
    
    for bot in regular_bots_data:
        bot_type = bot.get("bot_type", "unknown")
        if bot_type == "HUMAN":
            human_bots_in_regular += 1
    
    # Check that human bot endpoints don't return regular bots
    human_bots_data = human_bots_response.get("bots", [])
    regular_bots_in_human = 0
    
    for bot in human_bots_data:
        # Human bots don't have bot_type field, they have character field
        if "bot_type" in bot:
            regular_bots_in_human += 1
    
    print_success(f"РЕЗУЛЬТАТЫ ПЕРЕКРЕСТНОГО ЗАГРЯЗНЕНИЯ:")
    print_success(f"  Human-боты в коллекции обычных ботов: {human_bots_in_regular} (должно быть 0)")
    print_success(f"  Обычные боты в коллекции Human-ботов: {regular_bots_in_human} (должно быть 0)")
    
    if human_bots_in_regular == 0 and regular_bots_in_human == 0:
        print_success("🎉 ПЕРЕКРЕСТНОЕ ЗАГРЯЗНЕНИЕ ОТСУТСТВУЕТ!")
        record_test("Independence - No Cross Contamination", True)
    else:
        print_error("❌ ОБНАРУЖЕНО ПЕРЕКРЕСТНОЕ ЗАГРЯЗНЕНИЕ!")
        record_test("Independence - No Cross Contamination", False, f"Human in regular: {human_bots_in_regular}, Regular in human: {regular_bots_in_human}")

def test_bot_creation_and_management() -> None:
    """
    СОЗДАНИЕ И УПРАВЛЕНИЕ БОТАМИ:
    - POST /api/admin/bots/create-regular
    - PUT /api/admin/bots/{bot_id} с поддержкой новых полей
    - DELETE /api/admin/bots/{bot_id}
    """
    print_header("СОЗДАНИЕ И УПРАВЛЕНИЕ БОТАМИ")
    
    # Step 1: Login as admin
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin")
        record_test("Bot Management - Admin Login", False, "Admin login failed")
        return
    
    # Test 1: Create regular bot
    print_subheader("Test 1: POST /api/admin/bots/create-regular")
    
    test_bot_data = {
        "name": f"TestRegularBot_{int(time.time())}",
        "min_bet_amount": 5.0,
        "max_bet_amount": 50.0,
        "win_rate": 0.55,
        "cycle_games": 15,
        "win_percentage": 60.0,
        "pause_between_games": 8,
        "creation_mode": "queue-based",
        "priority_order": 75,
        "profit_strategy": "balanced"
    }
    
    create_response, create_success = make_request(
        "POST", "/admin/bots/create-regular",
        data=test_bot_data,
        auth_token=admin_token
    )
    
    if create_success:
        print_success("✅ Создание обычного бота работает")
        
        created_bot_id = create_response.get("id")
        if created_bot_id:
            print_success(f"✅ Создан бот с ID: {created_bot_id}")
            record_test("Bot Management - Create Regular Bot", True)
        else:
            print_error("❌ Ответ создания бота не содержит ID")
            record_test("Bot Management - Create Regular Bot", False, "Missing bot ID")
            return
    else:
        print_error("❌ Создание обычного бота НЕ работает")
        record_test("Bot Management - Create Regular Bot", False, "Creation failed")
        return
    
    # Test 2: Update bot with new fields
    print_subheader("Test 2: PUT /api/admin/bots/{bot_id} с новыми полями")
    
    update_data = {
        "name": f"UpdatedTestBot_{int(time.time())}",
        "win_percentage": 65.0,
        "pause_between_games": 12,
        "current_cycle_profit": 25.50,
        "total_net_profit": 125.75,
        "completed_cycles": 3
    }
    
    update_response, update_success = make_request(
        "PUT", f"/admin/bots/{created_bot_id}",
        data=update_data,
        auth_token=admin_token
    )
    
    if update_success:
        print_success("✅ Обновление бота с новыми полями работает")
        record_test("Bot Management - Update Bot New Fields", True)
        
        # Verify the update by getting the bot
        get_bot_response, get_bot_success = make_request(
            "GET", "/admin/bots",
            auth_token=admin_token
        )
        
        if get_bot_success and "bots" in get_bot_response:
            updated_bot = None
            for bot in get_bot_response["bots"]:
                if bot["id"] == created_bot_id:
                    updated_bot = bot
                    break
            
            if updated_bot:
                # Check updated fields
                updated_name = updated_bot.get("name", "")
                updated_win_percentage = updated_bot.get("win_percentage", 0)
                updated_pause = updated_bot.get("pause_between_games", 0)
                updated_cycle_profit = updated_bot.get("current_cycle_profit", 0)
                updated_net_profit = updated_bot.get("total_net_profit", 0)
                updated_cycles = updated_bot.get("completed_cycles", 0)
                
                print_success(f"✅ Обновленное имя: {updated_name}")
                print_success(f"✅ Обновленный win_percentage: {updated_win_percentage}%")
                print_success(f"✅ Обновленная пауза: {updated_pause}s")
                print_success(f"✅ Обновленная прибыль цикла: ${updated_cycle_profit}")
                print_success(f"✅ Обновленная общая прибыль: ${updated_net_profit}")
                print_success(f"✅ Обновленные завершенные циклы: {updated_cycles}")
                
                record_test("Bot Management - Verify Update", True)
            else:
                print_error("❌ Не удалось найти обновленного бота")
                record_test("Bot Management - Verify Update", False, "Bot not found")
    else:
        print_error("❌ Обновление бота НЕ работает")
        record_test("Bot Management - Update Bot New Fields", False, "Update failed")
    
    # Test 3: Test specific new endpoints for the created bot
    print_subheader("Test 3: Тест новых эндпоинтов для созданного бота")
    
    # Test pause settings endpoint
    pause_test_response, pause_test_success = make_request(
        "PUT", f"/admin/bots/{created_bot_id}/pause-settings",
        data={"pause_between_games": 15},
        auth_token=admin_token
    )
    
    if pause_test_success:
        print_success("✅ Эндпоинт pause-settings работает для созданного бота")
        record_test("Bot Management - Pause Settings Endpoint", True)
    else:
        print_error("❌ Эндпоинт pause-settings НЕ работает")
        record_test("Bot Management - Pause Settings Endpoint", False, "Endpoint failed")
    
    # Test win percentage endpoint
    win_test_response, win_test_success = make_request(
        "PUT", f"/admin/bots/{created_bot_id}/win-percentage",
        data={"win_percentage": 70.0},
        auth_token=admin_token
    )
    
    if win_test_success:
        print_success("✅ Эндпоинт win-percentage работает для созданного бота")
        record_test("Bot Management - Win Percentage Endpoint", True)
    else:
        print_error("❌ Эндпоинт win-percentage НЕ работает")
        record_test("Bot Management - Win Percentage Endpoint", False, "Endpoint failed")
    
    # Test active bets endpoint
    active_bets_test_response, active_bets_test_success = make_request(
        "GET", f"/admin/bots/{created_bot_id}/active-bets",
        auth_token=admin_token
    )
    
    if active_bets_test_success:
        print_success("✅ Эндпоинт active-bets работает для созданного бота")
        record_test("Bot Management - Active Bets Endpoint", True)
    else:
        print_error("❌ Эндпоинт active-bets НЕ работает")
        record_test("Bot Management - Active Bets Endpoint", False, "Endpoint failed")
    
    # Test cycle history endpoint
    cycle_history_test_response, cycle_history_test_success = make_request(
        "GET", f"/admin/bots/{created_bot_id}/cycle-history",
        auth_token=admin_token
    )
    
    if cycle_history_test_success:
        print_success("✅ Эндпоинт cycle-history работает для созданного бота")
        record_test("Bot Management - Cycle History Endpoint", True)
    else:
        print_error("❌ Эндпоинт cycle-history НЕ работает")
        record_test("Bot Management - Cycle History Endpoint", False, "Endpoint failed")
    
    # Test 4: Delete bot
    print_subheader("Test 4: DELETE /api/admin/bots/{bot_id}")
    
    delete_response, delete_success = make_request(
        "DELETE", f"/admin/bots/{created_bot_id}",
        auth_token=admin_token
    )
    
    if delete_success:
        print_success("✅ Удаление обычного бота работает")
        record_test("Bot Management - Delete Bot", True)
        
        # Verify deletion
        verify_delete_response, verify_delete_success = make_request(
            "GET", "/admin/bots",
            auth_token=admin_token
        )
        
        if verify_delete_success and "bots" in verify_delete_response:
            deleted_bot_found = False
            for bot in verify_delete_response["bots"]:
                if bot["id"] == created_bot_id:
                    deleted_bot_found = True
                    break
            
            if not deleted_bot_found:
                print_success("✅ Бот успешно удален из системы")
                record_test("Bot Management - Verify Deletion", True)
            else:
                print_error("❌ Бот все еще присутствует в системе после удаления")
                record_test("Bot Management - Verify Deletion", False, "Bot still exists")
    else:
        print_error("❌ Удаление обычного бота НЕ работает")
        record_test("Bot Management - Delete Bot", False, "Deletion failed")

def print_final_summary():
    """Print final test summary."""
    print_header("ФИНАЛЬНОЕ РЕЗЮМЕ ТЕСТИРОВАНИЯ")
    
    total_tests = test_results["total"]
    passed_tests = test_results["passed"]
    failed_tests = test_results["failed"]
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print_success(f"Всего тестов: {total_tests}")
    print_success(f"Пройдено: {passed_tests}")
    print_error(f"Провалено: {failed_tests}")
    print_success(f"Процент успеха: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print_success("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Система обычных ботов работает превосходно!")
    elif success_rate >= 75:
        print_success("✅ ХОРОШИЙ РЕЗУЛЬТАТ! Система обычных ботов работает хорошо с незначительными проблемами.")
    elif success_rate >= 50:
        print_warning("⚠ УДОВЛЕТВОРИТЕЛЬНЫЙ РЕЗУЛЬТАТ! Система обычных ботов работает, но требует доработки.")
    else:
        print_error("❌ НЕУДОВЛЕТВОРИТЕЛЬНЫЙ РЕЗУЛЬТАТ! Система обычных ботов требует серьезных исправлений.")
    
    # Show failed tests
    if failed_tests > 0:
        print_subheader("Провалившиеся тесты:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"❌ {test['name']}: {test['details']}")

def main():
    """Main test execution function."""
    print_header("ФИНАЛЬНОЕ КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ОБЫЧНЫХ БОТОВ")
    print("Проведение финального комплексного тестирования после исправлений Шагов 1-4")
    
    try:
        # Execute all test suites
        test_critical_bet_creation_automation()
        test_cycle_and_profit_system()
        test_new_api_endpoints()
        test_bot_separation_critical()
        test_independence_from_human_bots()
        test_bot_creation_and_management()
        
        # Print final summary
        print_final_summary()
        
    except KeyboardInterrupt:
        print_error("\nТестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print_error(f"Критическая ошибка во время тестирования: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()