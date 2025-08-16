#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ГЕНЕРАЦИИ СТАВОК (продолжение)
Final Testing of Bet Range Generation Fix - Russian Review

КОНТЕКСТ: Тестирование исправления генерации ставок для Regular ботов.
Проблема: Боты создают ставки вне диапазона min_bet_amount - max_bet_amount.

ЗАДАЧА:
1. Создать нового тестового бота "Final_Fix_Test_Bot":
   - min_bet_amount: 20.0  
   - max_bet_amount: 30.0
   - win_percentage: 55
   - cycle_games: 5

2. Подождать 15 секунд для автоматического создания ставок

3. Проверить что ВСЕ ставки бота находятся в диапазоне 20.0-30.0:
   - Получить активные игры через GET /api/bots/active-games
   - Найти все игры созданные "Final_Fix_Test_Bot"
   - Проверить каждую bet_amount - должна быть между 20.0 и 30.0
   - Должно быть ровно 5 ставок (cycle_games=5)

4. Показать детальную статистику и анализ проблемы

КРИТИЧНОСТЬ: Это последняя попытка исправить генерацию ставок.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://russian-commission.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test configuration
import time as time_module
TEST_BOT_NAME = f"Final_Fix_Test_Bot_{int(time_module.time())}"
MIN_BET_AMOUNT = 20.0
MAX_BET_AMOUNT = 30.0
WIN_PERCENTAGE = 55
CYCLE_GAMES = 5
WAIT_TIME = 15  # seconds

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

def print_step(step_num: int, description: str):
    """Print test step"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔹 ШАГ {step_num}: {description}{Colors.END}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️ {message}{Colors.END}")

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
    print_info("Аутентификация как администратор...")
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print_success("Аутентификация администратора успешна")
        return token
    else:
        print_error(f"Ошибка аутентификации администратора: {details}")
        return None

def delete_existing_test_bot(token: str) -> bool:
    """Delete existing test bot if it exists"""
    print_info(f"Проверка существующего бота '{TEST_BOT_NAME}'...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all bots
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        print_warning(f"Не удалось получить список ботов: {details}")
        return False
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    # Find test bot
    test_bot = None
    for bot in bots:
        if bot.get("name") == TEST_BOT_NAME:
            test_bot = bot
            break
    
    if test_bot:
        print_info(f"Найден существующий бот '{TEST_BOT_NAME}', удаляем...")
        
        success, response_data, details = make_request(
            "DELETE",
            f"/admin/bots/{test_bot['id']}",
            headers=headers
        )
        
        if success:
            print_success(f"Бот '{TEST_BOT_NAME}' успешно удален")
            return True
        else:
            print_warning(f"Не удалось удалить бота: {details}")
            return False
    else:
        print_info(f"Бот '{TEST_BOT_NAME}' не найден, продолжаем...")
        return True

def create_test_bot(token: str) -> Optional[str]:
    """Create test bot with specific parameters"""
    print_step(1, f"Создание нового тестового бота '{TEST_BOT_NAME}'")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    bot_data = {
        "name": TEST_BOT_NAME,
        "min_bet_amount": MIN_BET_AMOUNT,
        "max_bet_amount": MAX_BET_AMOUNT,
        "win_percentage": WIN_PERCENTAGE,
        "cycle_games": CYCLE_GAMES,
        "pause_between_cycles": 5,  # 5 seconds between cycles
        "pause_on_draw": 1,  # 1 second on draw
        "creation_mode": "queue-based",
        "profit_strategy": "balanced"
    }
    
    print_info(f"Параметры бота:")
    print_info(f"  - name: {bot_data['name']}")
    print_info(f"  - min_bet_amount: {bot_data['min_bet_amount']}")
    print_info(f"  - max_bet_amount: {bot_data['max_bet_amount']}")
    print_info(f"  - win_percentage: {bot_data['win_percentage']}")
    print_info(f"  - cycle_games: {bot_data['cycle_games']}")
    
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if success and response_data:
        bot_id = response_data.get("id") or response_data.get("bot_id")
        
        # Handle different response formats
        if not bot_id and "created_bots" in response_data:
            created_bots = response_data.get("created_bots", [])
            if created_bots:
                bot_id = created_bots[0]
        
        if bot_id:
            print_success(f"Бот '{TEST_BOT_NAME}' успешно создан с ID: {bot_id}")
            return bot_id
        else:
            print_error(f"Бот создан, но ID не найден в ответе: {response_data}")
            return None
    else:
        print_error(f"Ошибка создания бота: {details}")
        return None

def wait_for_bet_creation():
    """Wait for automatic bet creation"""
    print_step(2, f"Ожидание {WAIT_TIME} секунд для автоматического создания ставок")
    
    for i in range(WAIT_TIME):
        remaining = WAIT_TIME - i
        print(f"\r{Colors.YELLOW}⏳ Осталось секунд: {remaining:2d}{Colors.END}", end="", flush=True)
        time.sleep(1)
    
    print(f"\n{Colors.GREEN}✅ Ожидание завершено{Colors.END}")

def get_bot_active_games(token: str) -> List[Dict]:
    """Get all active games for regular bots"""
    print_step(3, "Получение активных игр через GET /api/bots/active-games")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        print_success(f"Получено {len(games)} активных игр Regular ботов")
        return games
    else:
        print_error(f"Ошибка получения активных игр: {details}")
        return []

def analyze_bot_bets(games: List[Dict], bot_id: str = None) -> Dict[str, Any]:
    """Analyze bets created by the test bot"""
    print_step(4, f"Анализ ставок созданных ботом '{TEST_BOT_NAME}'")
    
    # Find games created by our test bot
    test_bot_games = []
    
    print_info(f"Поиск игр среди {len(games)} активных игр...")
    print_info(f"Ищем по bot_id: {bot_id}")
    
    for game in games:
        # Check if game was created by our test bot
        creator_name = game.get("creator_name") or game.get("bot_name") or ""
        creator_id = game.get("creator_id", "")
        bot_game_id = game.get("bot_id", "")
        
        # Debug: show first few games to understand structure
        if len(test_bot_games) == 0 and len(games) > 0:
            print_info(f"Пример структуры игры: {list(game.keys())}")
            print_info(f"creator_name: '{creator_name}', creator_id: '{creator_id}', bot_id: '{bot_game_id}'")
        
        # Try multiple ways to match the bot
        if (creator_name == TEST_BOT_NAME or 
            creator_id == bot_id or 
            bot_game_id == bot_id):
            test_bot_games.append(game)
    
    print_info(f"Найдено {len(test_bot_games)} игр созданных ботом '{TEST_BOT_NAME}'")
    
    if not test_bot_games:
        print_warning("Бот не создал ни одной игры!")
        # Show some sample games for debugging
        if games:
            print_info("Примеры существующих игр:")
            for i, game in enumerate(games[:3]):
                creator_name = game.get("creator_name") or game.get("bot_name") or "Unknown"
                bet_amount = game.get("bet_amount", 0)
                print_info(f"  Игра {i+1}: creator='{creator_name}', bet=${bet_amount}")
        
        return {
            "total_games": 0,
            "games_in_range": 0,
            "games_out_of_range": 0,
            "bet_amounts": [],
            "out_of_range_bets": [],
            "success_rate": 0.0,
            "expected_games": CYCLE_GAMES,
            "analysis": "Бот не создал игры"
        }
    
    # Analyze bet amounts
    bet_amounts = []
    games_in_range = 0
    games_out_of_range = 0
    out_of_range_bets = []
    
    print_info("Детальный анализ ставок:")
    
    for i, game in enumerate(test_bot_games, 1):
        bet_amount = game.get("bet_amount", 0)
        bet_amounts.append(bet_amount)
        
        in_range = MIN_BET_AMOUNT <= bet_amount <= MAX_BET_AMOUNT
        
        if in_range:
            games_in_range += 1
            status = f"{Colors.GREEN}✅ В ДИАПАЗОНЕ{Colors.END}"
        else:
            games_out_of_range += 1
            out_of_range_bets.append(bet_amount)
            status = f"{Colors.RED}❌ ВНЕ ДИАПАЗОНА{Colors.END}"
        
        print(f"  Игра {i}: ${bet_amount:.1f} - {status}")
    
    success_rate = (games_in_range / len(test_bot_games)) * 100 if test_bot_games else 0
    
    return {
        "total_games": len(test_bot_games),
        "games_in_range": games_in_range,
        "games_out_of_range": games_out_of_range,
        "bet_amounts": bet_amounts,
        "out_of_range_bets": out_of_range_bets,
        "success_rate": success_rate,
        "expected_games": CYCLE_GAMES
    }

def get_gem_combinations_analysis(games: List[Dict]) -> Dict[str, Any]:
    """Analyze gem combinations for test bot games"""
    print_info("Анализ комбинаций гемов:")
    
    gem_combinations = []
    total_gem_value = 0
    
    for game in games:
        bet_gems = game.get("bet_gems", {})
        if bet_gems:
            gem_combinations.append(bet_gems)
            # Calculate gem value based on GEM_PRICES
            gem_prices = {
                "Ruby": 1.0,
                "Amber": 2.0,
                "Topaz": 5.0,
                "Emerald": 10.0,
                "Aquamarine": 25.0,
                "Sapphire": 50.0,
                "Magic": 100.0
            }
            
            game_gem_value = 0
            for gem_type, quantity in bet_gems.items():
                if gem_type in gem_prices:
                    game_gem_value += gem_prices[gem_type] * quantity
            
            total_gem_value += game_gem_value
            print_info(f"  Гемы: {bet_gems} = ${game_gem_value:.1f}")
    
    return {
        "combinations": gem_combinations,
        "total_value": total_gem_value,
        "average_value": total_gem_value / len(gem_combinations) if gem_combinations else 0
    }

def print_detailed_statistics(analysis: Dict[str, Any], games: List[Dict]):
    """Print detailed statistics and analysis"""
    print_header("ДЕТАЛЬНАЯ СТАТИСТИКА РЕЗУЛЬТАТОВ")
    
    total = analysis["total_games"]
    in_range = analysis["games_in_range"]
    out_of_range = analysis["games_out_of_range"]
    success_rate = analysis["success_rate"]
    expected = analysis["expected_games"]
    
    print(f"{Colors.BOLD}📊 ОСНОВНЫЕ ПОКАЗАТЕЛИ:{Colors.END}")
    print(f"   Ожидалось игр: {expected}")
    print(f"   Фактически создано: {total}")
    print(f"   {Colors.GREEN}✅ В диапазоне ({MIN_BET_AMOUNT}-{MAX_BET_AMOUNT}): {in_range}{Colors.END}")
    print(f"   {Colors.RED}❌ Вне диапазона: {out_of_range}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Процент успеха: {success_rate:.1f}%{Colors.END}")
    
    if analysis["bet_amounts"]:
        bet_amounts = analysis["bet_amounts"]
        print(f"\n{Colors.BOLD}💰 СУММЫ СТАВОК:{Colors.END}")
        print(f"   Все ставки: {bet_amounts}")
        print(f"   Минимальная: ${min(bet_amounts):.1f}")
        print(f"   Максимальная: ${max(bet_amounts):.1f}")
        print(f"   Средняя: ${sum(bet_amounts)/len(bet_amounts):.1f}")
    
    if analysis["out_of_range_bets"]:
        print(f"\n{Colors.BOLD}{Colors.RED}🚨 СТАВКИ ВНЕ ДИАПАЗОНА:{Colors.END}")
        for bet in analysis["out_of_range_bets"]:
            print(f"   ${bet:.1f}")
    
    # Gem combinations analysis
    if total > 0:
        test_bot_games = [g for g in games if g.get("creator_name") == TEST_BOT_NAME or g.get("bot_name") == TEST_BOT_NAME]
        gem_analysis = get_gem_combinations_analysis(test_bot_games)
        
        print(f"\n{Colors.BOLD}💎 АНАЛИЗ КОМБИНАЦИЙ ГЕМОВ:{Colors.END}")
        print(f"   Всего комбинаций: {len(gem_analysis['combinations'])}")
        print(f"   Общая стоимость гемов: ${gem_analysis['total_value']:.1f}")
        print(f"   Средняя стоимость: ${gem_analysis['average_value']:.1f}")

def print_final_conclusion(analysis: Dict[str, Any]):
    """Print final conclusion and recommendations"""
    print_header("ФИНАЛЬНОЕ ЗАКЛЮЧЕНИЕ")
    
    total = analysis["total_games"]
    success_rate = analysis["success_rate"]
    expected = analysis["expected_games"]
    
    if total == 0:
        print(f"{Colors.RED}{Colors.BOLD}🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: БОТ НЕ СОЗДАЛ НИ ОДНОЙ ИГРЫ!{Colors.END}")
        print(f"{Colors.RED}Возможные причины:{Colors.END}")
        print(f"{Colors.RED}  1. Автоматизация создания ставок не работает{Colors.END}")
        print(f"{Colors.RED}  2. Бот не активирован после создания{Colors.END}")
        print(f"{Colors.RED}  3. Ошибка в логике maintain_all_bots_active_bets(){Colors.END}")
        print(f"{Colors.RED}  4. Проблемы с циклами ботов{Colors.END}")
        
    elif total != expected:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ ПРОБЛЕМА С КОЛИЧЕСТВОМ ИГОР:{Colors.END}")
        print(f"{Colors.YELLOW}Ожидалось: {expected} игр, Создано: {total} игр{Colors.END}")
        print(f"{Colors.YELLOW}Логика cycle_games может работать некорректно{Colors.END}")
        
    if success_rate == 100.0 and total == expected:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ИСПРАВЛЕНИЕ ГЕНЕРАЦИИ СТАВОК УСПЕШНО!{Colors.END}")
        print(f"{Colors.GREEN}✅ Все {total} ставок находятся в правильном диапазоне {MIN_BET_AMOUNT}-{MAX_BET_AMOUNT}{Colors.END}")
        print(f"{Colors.GREEN}✅ Количество ставок соответствует cycle_games = {expected}{Colors.END}")
        print(f"{Colors.GREEN}✅ Система готова к продакшену{Colors.END}")
        
    elif success_rate >= 80.0:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ ЧАСТИЧНОЕ ИСПРАВЛЕНИЕ ({success_rate:.1f}% успеха){Colors.END}")
        print(f"{Colors.YELLOW}Большинство ставок в правильном диапазоне, но есть проблемы{Colors.END}")
        print(f"{Colors.YELLOW}Требуется дополнительная настройка алгоритма{Colors.END}")
        
    else:
        print(f"{Colors.RED}{Colors.BOLD}🚨 ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ! ({success_rate:.1f}% успеха){Colors.END}")
        print(f"{Colors.RED}Генерация ставок все еще нарушает диапазон min_bet_amount - max_bet_amount{Colors.END}")
        print(f"{Colors.RED}Требуется срочное вмешательство главного агента{Colors.END}")
        
        print(f"\n{Colors.RED}{Colors.BOLD}🔧 РЕКОМЕНДАЦИИ ДЛЯ ИСПРАВЛЕНИЯ:{Colors.END}")
        print(f"{Colors.RED}1. Проверить функцию generate_bot_bet_amount() в server.py{Colors.END}")
        print(f"{Colors.RED}2. Убедиться что min_bet_amount и max_bet_amount правильно используются{Colors.END}")
        print(f"{Colors.RED}3. Проверить логику расчета стоимости гемов{Colors.END}")
        print(f"{Colors.RED}4. Добавить дополнительную валидацию bet_amount перед созданием игры{Colors.END}")

def main():
    """Main test execution"""
    print_header("ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ГЕНЕРАЦИИ СТАВОК")
    print(f"{Colors.BLUE}🎯 Тестирование исправления генерации ставок для Regular ботов{Colors.END}")
    print(f"{Colors.BLUE}📋 Цель: Проверить что все ставки находятся в диапазоне {MIN_BET_AMOUNT}-{MAX_BET_AMOUNT}{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print_error("Невозможно продолжить без аутентификации")
        sys.exit(1)
    
    try:
        # Delete existing test bot if exists
        delete_existing_test_bot(token)
        
        # Create test bot
        bot_id = create_test_bot(token)
        if not bot_id:
            print_error("Невозможно продолжить без создания бота")
            sys.exit(1)
        
        # Wait for bet creation
        wait_for_bet_creation()
        
        # Get active games
        games = get_bot_active_games(token)
        
        # Analyze bot bets
        analysis = analyze_bot_bets(games, bot_id)
        
        # Print detailed statistics
        print_detailed_statistics(analysis, games)
        
        # Print final conclusion
        print_final_conclusion(analysis)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Тестирование прервано пользователем{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Неожиданная ошибка во время тестирования: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()