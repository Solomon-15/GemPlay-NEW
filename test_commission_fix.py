#!/usr/bin/env python3
"""
Тест исправления двойного отображения комиссий Human-ботов
"""

import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime
import sys

# Конфигурация
BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "securepassword"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Тест: {test_name}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def generate_username(prefix="test"):
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"

async def login_admin(session):
    """Вход под администратором"""
    try:
        async with session.post(f"{BASE_URL}/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["access_token"]
            else:
                print_error(f"Ошибка входа: {resp.status}")
                return None
    except Exception as e:
        print_error(f"Ошибка при входе: {e}")
        return None

async def get_commission_data(session, token):
    """Получить данные о комиссиях из всех источников"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {}
    
    # 1. Статистика прибыли (основная плитка)
    async with session.get(f"{BASE_URL}/admin/profit/stats", headers=headers) as resp:
        if resp.status == 200:
            profit_data = await resp.json()
            data['profit_stats'] = {
                'bet_commission': profit_data.get('bet_commission', 0),
                'human_bot_commission': profit_data.get('human_bot_commission', 0)
            }
            
    # 2. Модальное окно Human-bot комиссий
    async with session.get(f"{BASE_URL}/admin/human-bots-total-commission", headers=headers) as resp:
        if resp.status == 200:
            modal_data = await resp.json()
            data['modal_commission'] = modal_data.get('total_commission', 0)
            
    # 3. Детализация комиссий
    async with session.get(f"{BASE_URL}/admin/profit/human-bot-commission-breakdown?period=all", headers=headers) as resp:
        if resp.status == 200:
            breakdown_data = await resp.json()
            data['breakdown_commission'] = breakdown_data.get('total_amount', 0)
            
    # 4. Статистика Human-ботов
    async with session.get(f"{BASE_URL}/admin/human-bots/stats", headers=headers) as resp:
        if resp.status == 200:
            human_stats = await resp.json()
            data['period_revenue'] = human_stats.get('period_revenue', 0)
            
    return data

async def clear_test_data(session, token):
    """Очистить тестовые данные"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print_info("Очистка тестовых данных...")
    
    # Сброс дохода за период (удаляет все HUMAN_BOT_COMMISSION записи)
    async with session.post(f"{BASE_URL}/admin/human-bots/reset-period-revenue", headers=headers) as resp:
        if resp.status == 200:
            result = await resp.json()
            print_success(f"Сброшен доход за период: {result.get('message', '')}")
            
    # Для полной очистки можно также удалить BET_COMMISSION записи через базу данных
    # Но это требует прямого доступа к БД

async def create_test_user(session, admin_token, balance=1000):
    """Создать тестового пользователя"""
    username = generate_username("user")
    password = "testpass123"
    
    # Регистрация
    async with session.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "password": password,
        "confirm_password": password
    }) as resp:
        if resp.status != 200:
            return None
            
    # Вход
    async with session.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    }) as resp:
        if resp.status == 200:
            data = await resp.json()
            user_data = {
                "id": data["user"]["id"],
                "username": username,
                "token": data["access_token"]
            }
            
            # Установка баланса
            if balance > 0:
                headers = {"Authorization": f"Bearer {admin_token}"}
                await session.put(
                    f"{BASE_URL}/admin/users/{user_data['id']}/balance",
                    headers=headers,
                    json={"balance": balance}
                )
                
            return user_data
            
    return None

async def create_test_human_bot(session, admin_token, character="aggressive"):
    """Создать тестового Human-бота"""
    bot_name = generate_username(f"hbot_{character[:3]}")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with session.post(f"{BASE_URL}/admin/human-bots", headers=headers, json={
        "name": bot_name,
        "character": character,
        "min_bet": 10,
        "max_bet": 100,
        "response_time_min": 1,
        "response_time_max": 3,
        "activity_start_hour": 0,
        "activity_end_hour": 23,
        "max_daily_games": 100,
        "win_rate_adjustment": 0,
        "is_active": True
    }) as resp:
        if resp.status == 200:
            data = await resp.json()
            return {
                "id": data["id"],
                "name": bot_name,
                "character": character
            }
    return None

async def run_test_games(session, admin_token):
    """Запустить тестовые игры"""
    print_test_header("Создание тестовых игр")
    
    # Создаём участников
    print_info("Создание участников...")
    
    player1 = await create_test_user(session, admin_token, 500)
    player2 = await create_test_user(session, admin_token, 500)
    bot1 = await create_test_human_bot(session, admin_token, "aggressive")
    bot2 = await create_test_human_bot(session, admin_token, "defensive")
    
    if not all([player1, player2, bot1, bot2]):
        print_error("Не удалось создать всех участников")
        return False
        
    print_success(f"Создан игрок 1: {player1['username']}")
    print_success(f"Создан игрок 2: {player2['username']}")
    print_success(f"Создан Human-бот 1: {bot1['name']}")
    print_success(f"Создан Human-бот 2: {bot2['name']}")
    
    # Игра 1: Живой vs Живой
    print_info("\nИгра 1: Живой игрок vs Живой игрок (ставка $30)")
    headers1 = {"Authorization": f"Bearer {player1['token']}"}
    async with session.post(f"{BASE_URL}/games", headers=headers1, json={
        "bet_amount": 30,
        "is_public": True,
        "selected_move": "rock"
    }) as resp:
        if resp.status == 200:
            game1 = await resp.json()
            game1_id = game1["id"]
            
            # Игрок 2 присоединяется
            headers2 = {"Authorization": f"Bearer {player2['token']}"}
            async with session.post(f"{BASE_URL}/games/{game1_id}/join", headers=headers2, json={
                "selected_move": "paper"
            }) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print_success(f"Игра завершена. Победитель: Игрок 2. Комиссия: ${result.get('commission_amount', 0):.2f}")
                    
    await asyncio.sleep(2)
    
    # Игра 2: Human-бот vs Human-бот
    print_info("\nИгра 2: Human-бот vs Human-бот (ставка $40)")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    async with session.post(f"{BASE_URL}/admin/human-bots/{bot1['id']}/create-game", 
                          headers=admin_headers, 
                          json={"bet_amount": 40}) as resp:
        if resp.status == 200:
            await asyncio.sleep(5)  # Ждём завершения
            print_success("Игра между Human-ботами завершена")
            
    await asyncio.sleep(2)
    
    # Игра 3: Живой vs Human-бот (живой выигрывает)
    print_info("\nИгра 3: Живой игрок vs Human-бот (ставка $50)")
    async with session.post(f"{BASE_URL}/games", headers=headers1, json={
        "bet_amount": 50,
        "is_public": True,
        "selected_move": "scissors"  # Выберем ход, который может выиграть
    }) as resp:
        if resp.status == 200:
            game3 = await resp.json()
            await asyncio.sleep(5)  # Ждём, пока бот присоединится
            print_success("Игра Живой vs Human-бот завершена")
            
    return True

async def main():
    """Основная функция тестирования"""
    print(f"{Colors.BOLD}{Colors.CYAN}Тест исправления двойного отображения комиссий{Colors.RESET}")
    print(f"{Colors.CYAN}Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")
    
    async with aiohttp.ClientSession() as session:
        # Вход администратора
        token = await login_admin(session)
        if not token:
            print_error("Не удалось войти как администратор")
            return
            
        print_success("Администратор успешно вошёл в систему")
        
        # Очистка данных
        await clear_test_data(session, token)
        await asyncio.sleep(2)
        
        # Проверка начальных данных
        print_test_header("Проверка начальных данных")
        initial_data = await get_commission_data(session, token)
        
        print_info("Начальные значения:")
        print_info(f"  Плитка 'Комиссия от ставок': ${initial_data['profit_stats']['bet_commission']:.2f}")
        print_info(f"  Плитка 'Комиссия от Human-ботов': ${initial_data['profit_stats']['human_bot_commission']:.2f}")
        print_info(f"  Модальное окно Human-бот комиссий: ${initial_data['modal_commission']:.2f}")
        print_info(f"  Детализация комиссий: ${initial_data['breakdown_commission']:.2f}")
        print_info(f"  Доход за период: ${initial_data['period_revenue']:.2f}")
        
        # Запуск тестовых игр
        success = await run_test_games(session, token)
        if not success:
            print_error("Ошибка при создании тестовых игр")
            return
            
        await asyncio.sleep(3)
        
        # Проверка результатов
        print_test_header("Проверка результатов после игр")
        final_data = await get_commission_data(session, token)
        
        print_info("Финальные значения:")
        print_info(f"  Плитка 'Комиссия от ставок': ${final_data['profit_stats']['bet_commission']:.2f}")
        print_info(f"  Плитка 'Комиссия от Human-ботов': ${final_data['profit_stats']['human_bot_commission']:.2f}")
        print_info(f"  Модальное окно Human-бот комиссий: ${final_data['modal_commission']:.2f}")
        print_info(f"  Детализация комиссий: ${final_data['breakdown_commission']:.2f}")
        print_info(f"  Доход за период: ${final_data['period_revenue']:.2f}")
        
        # Анализ результатов
        print_test_header("Анализ синхронизации")
        
        # Проверка синхронизации Human-bot комиссий
        human_bot_values = [
            final_data['profit_stats']['human_bot_commission'],
            final_data['modal_commission'],
            final_data['breakdown_commission'],
            final_data['period_revenue']
        ]
        
        all_equal = all(abs(v - human_bot_values[0]) < 0.01 for v in human_bot_values)
        
        if all_equal:
            print_success("✓ Все значения Human-bot комиссий синхронизированы!")
            print_info(f"  Единое значение: ${human_bot_values[0]:.2f}")
        else:
            print_error("✗ Обнаружены расхождения в Human-bot комиссиях:")
            print_error(f"  Плитка: ${final_data['profit_stats']['human_bot_commission']:.2f}")
            print_error(f"  Модальное окно: ${final_data['modal_commission']:.2f}")
            print_error(f"  Детализация: ${final_data['breakdown_commission']:.2f}")
            print_error(f"  Доход за период: ${final_data['period_revenue']:.2f}")
            
        # Проверка наличия комиссий от ставок
        if final_data['profit_stats']['bet_commission'] > 0:
            print_success(f"✓ Комиссия от ставок записывается: ${final_data['profit_stats']['bet_commission']:.2f}")
        else:
            print_warning("⚠ Комиссия от ставок отсутствует")
            
        # Проверка изменений
        print_test_header("Изменения в данных")
        
        bet_diff = final_data['profit_stats']['bet_commission'] - initial_data['profit_stats']['bet_commission']
        human_bot_diff = final_data['profit_stats']['human_bot_commission'] - initial_data['profit_stats']['human_bot_commission']
        
        print_info(f"Изменение комиссии от ставок: +${bet_diff:.2f}")
        print_info(f"Изменение комиссии от Human-ботов: +${human_bot_diff:.2f}")
        
        # Итоговый вердикт
        print_test_header("Итоговый результат")
        
        if all_equal and bet_diff > 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}ТЕСТ ПРОЙДЕН УСПЕШНО!{Colors.RESET}")
            print_success("Проблема двойного отображения комиссий исправлена")
            print_success("Все значения синхронизированы")
            print_success("Комиссии записываются согласно новым правилам")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}ТЕСТ НЕ ПРОЙДЕН{Colors.RESET}")
            if not all_equal:
                print_error("Значения Human-bot комиссий не синхронизированы")
            if bet_diff <= 0:
                print_error("Комиссии от ставок не записываются")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Тест прерван пользователем{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Ошибка: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()