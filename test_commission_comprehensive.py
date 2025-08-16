#!/usr/bin/env python3
"""
Комплексный тест логики комиссий
Проверяет все сценарии начисления комиссий и синхронизацию данных
"""

import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime
import sys
import time

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
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Тест: {test_name}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_debug(message):
    print(f"{Colors.MAGENTA}🔍 {message}{Colors.RESET}")

def generate_username(prefix="test"):
    """Генерация уникального имени пользователя"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"

class CommissionTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_users = []
        self.test_human_bots = []
        self.initial_stats = {}
        self.commission_rate = 0.03  # 3% комиссия по умолчанию
        
    async def setup(self):
        """Инициализация тестера"""
        self.session = aiohttp.ClientSession()
        
        # Вход администратора
        self.admin_token = await self.login_admin()
        if not self.admin_token:
            raise Exception("Не удалось войти как администратор")
            
        # Получение начальных данных
        await self.get_initial_stats()
        
        # Получение текущей ставки комиссии
        await self.get_commission_settings()
        
    async def cleanup(self):
        """Очистка после тестов"""
        if self.session:
            await self.session.close()
            
    async def login_admin(self):
        """Вход под администратором"""
        try:
            async with self.session.post(f"{BASE_URL}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print_success("Администратор успешно вошёл в систему")
                    return data["access_token"]
                else:
                    print_error(f"Ошибка входа администратора: {resp.status}")
                    return None
        except Exception as e:
            print_error(f"Ошибка при входе: {e}")
            return None
            
    async def get_initial_stats(self):
        """Получить начальные статистики"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Статистика прибыли
        async with self.session.get(f"{BASE_URL}/admin/profit/stats", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.initial_stats['profit'] = data
                print_info(f"Начальная комиссия от ставок: ${data.get('bet_commission', 0):.2f}")
                print_info(f"Начальная комиссия от Human-ботов: ${data.get('human_bot_commission', 0):.2f}")
                
        # Статистика Human-ботов
        async with self.session.get(f"{BASE_URL}/admin/human-bots/stats", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.initial_stats['human_bots'] = data
                print_info(f"Начальный доход за период: ${data.get('period_revenue', 0):.2f}")
                
    async def get_commission_settings(self):
        """Получить настройки комиссии"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        async with self.session.get(f"{BASE_URL}/admin/profit/commission-settings", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.commission_rate = data.get('bet_commission_rate', 3) / 100
                print_info(f"Текущая ставка комиссии: {self.commission_rate*100:.1f}%")
                
    async def create_test_user(self, balance=1000):
        """Создать тестового пользователя"""
        username = generate_username("user")
        password = "testpass123"
        
        # Регистрация
        async with self.session.post(f"{BASE_URL}/auth/register", json={
            "username": username,
            "password": password,
            "confirm_password": password
        }) as resp:
            if resp.status != 200:
                print_error(f"Ошибка регистрации пользователя {username}: {resp.status}")
                return None
                
        # Вход
        async with self.session.post(f"{BASE_URL}/auth/login", json={
            "username": username,
            "password": password
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                user_data = {
                    "id": data["user"]["id"],
                    "username": username,
                    "token": data["access_token"],
                    "balance": balance
                }
                
                # Установка баланса через админа
                if balance > 0:
                    headers = {"Authorization": f"Bearer {self.admin_token}"}
                    await self.session.put(
                        f"{BASE_URL}/admin/users/{user_data['id']}/balance",
                        headers=headers,
                        json={"balance": balance}
                    )
                
                self.test_users.append(user_data)
                print_success(f"Создан пользователь {username} с балансом ${balance}")
                return user_data
            else:
                print_error(f"Ошибка входа пользователя {username}: {resp.status}")
                return None
                
    async def create_test_human_bot(self, character="aggressive"):
        """Создать тестового Human-бота"""
        bot_name = generate_username(f"hbot_{character[:3]}")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        async with self.session.post(f"{BASE_URL}/admin/human-bots", headers=headers, json={
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
                bot_data = {
                    "id": data["id"],
                    "name": bot_name,
                    "character": character
                }
                self.test_human_bots.append(bot_data)
                print_success(f"Создан Human-бот {bot_name} с характером {character}")
                return bot_data
            else:
                print_error(f"Ошибка создания Human-бота: {resp.status}")
                text = await resp.text()
                print_debug(f"Ответ: {text}")
                return None
                
    async def create_game(self, creator_token, bet_amount, selected_move=None):
        """Создать игру"""
        headers = {"Authorization": f"Bearer {creator_token}"}
        
        game_data = {
            "bet_amount": bet_amount,
            "is_public": True
        }
        
        if selected_move:
            game_data["selected_move"] = selected_move
            
        async with self.session.post(f"{BASE_URL}/games", headers=headers, json=game_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data
            else:
                print_error(f"Ошибка создания игры: {resp.status}")
                text = await resp.text()
                print_debug(f"Ответ: {text}")
                return None
                
    async def join_game(self, game_id, joiner_token, selected_move):
        """Присоединиться к игре"""
        headers = {"Authorization": f"Bearer {joiner_token}"}
        
        async with self.session.post(f"{BASE_URL}/games/{game_id}/join", headers=headers, json={
            "selected_move": selected_move
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data
            else:
                print_error(f"Ошибка присоединения к игре: {resp.status}")
                text = await resp.text()
                print_debug(f"Ответ: {text}")
                return None
                
    async def wait_for_human_bot_join(self, game_id, max_wait=10):
        """Ожидание присоединения Human-бота к игре"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        for i in range(max_wait):
            async with self.session.get(f"{BASE_URL}/games/{game_id}", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "COMPLETED":
                        return data
                    elif data.get("opponent_id"):
                        # Бот присоединился, ждём завершения
                        await asyncio.sleep(1)
                        continue
            await asyncio.sleep(1)
            
        return None
        
    async def get_game_details(self, game_id):
        """Получить детали игры"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        async with self.session.get(f"{BASE_URL}/games/{game_id}`, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return None
                
    async def get_current_stats(self):
        """Получить текущие статистики"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        stats = {}
        
        # Статистика прибыли
        async with self.session.get(f"{BASE_URL}/admin/profit/stats", headers=headers) as resp:
            if resp.status == 200:
                stats['profit'] = await resp.json()
                
        # Статистика Human-ботов
        async with self.session.get(f"{BASE_URL}/admin/human-bots/stats", headers=headers) as resp:
            if resp.status == 200:
                stats['human_bots'] = await resp.json()
                
        # Детализация комиссий Human-ботов
        async with self.session.get(f"{BASE_URL}/admin/profit/human-bot-commission-breakdown?period=all", headers=headers) as resp:
            if resp.status == 200:
                stats['commission_breakdown'] = await resp.json()
                
        return stats
        
    async def test_human_bot_vs_human_bot(self):
        """Тест: Human-бот vs Human-бот"""
        print_test_header("Human-бот vs Human-бот")
        
        # Создаём двух Human-ботов
        bot1 = await self.create_test_human_bot("aggressive")
        bot2 = await self.create_test_human_bot("defensive")
        
        if not bot1 or not bot2:
            print_error("Не удалось создать Human-ботов")
            return False
            
        # Создаём игру от имени первого бота
        print_info("Создаём игру от Human-бота...")
        
        # Для Human-ботов нужно использовать специальный эндпоинт
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        bet_amount = 50
        
        # Симулируем создание игры Human-ботом через админский эндпоинт
        async with self.session.post(f"{BASE_URL}/admin/human-bots/{bot1['id']}/create-game", 
                                   headers=headers, 
                                   json={"bet_amount": bet_amount}) as resp:
            if resp.status == 200:
                game_data = await resp.json()
                game_id = game_data["game_id"]
                print_success(f"Human-бот {bot1['name']} создал игру {game_id} со ставкой ${bet_amount}")
                
                # Ждём, пока второй бот присоединится
                print_info("Ожидаем присоединения второго Human-бота...")
                await asyncio.sleep(5)
                
                # Проверяем результат
                game = await self.wait_for_human_bot_join(game_id)
                if game and game.get("status") == "COMPLETED":
                    winner_id = game.get("winner_id")
                    commission = game.get("commission_amount", 0)
                    
                    print_success(f"Игра завершена!")
                    print_info(f"Победитель: {'Бот 1' if winner_id == bot1['id'] else 'Бот 2'}")
                    print_info(f"Комиссия: ${commission:.2f} ({commission/bet_amount*100:.1f}%)")
                    
                    # Проверяем статистику
                    await asyncio.sleep(1)
                    stats = await self.get_current_stats()
                    
                    bet_commission_diff = stats['profit']['bet_commission'] - self.initial_stats['profit']['bet_commission']
                    human_bot_commission_diff = stats['profit']['human_bot_commission'] - self.initial_stats['profit']['human_bot_commission']
                    period_revenue_diff = stats['human_bots']['period_revenue'] - self.initial_stats['human_bots']['period_revenue']
                    
                    print_info(f"\nИзменения в статистике:")
                    print_info(f"Комиссия от ставок: +${bet_commission_diff:.2f}")
                    print_info(f"Комиссия от Human-ботов: +${human_bot_commission_diff:.2f}")
                    print_info(f"Доход за период: +${period_revenue_diff:.2f}")
                    
                    # Проверка: комиссия должна быть записана как HUMAN_BOT_COMMISSION
                    if abs(human_bot_commission_diff - commission) < 0.01:
                        print_success("✓ Комиссия правильно записана как HUMAN_BOT_COMMISSION")
                    else:
                        print_error(f"✗ Ошибка: ожидалась комиссия ${commission:.2f}, получено ${human_bot_commission_diff:.2f}")
                        
                    # Проверка синхронизации
                    if abs(human_bot_commission_diff - period_revenue_diff) < 0.01:
                        print_success("✓ Данные синхронизированы между ProfitAdmin и HumanBotsManagement")
                    else:
                        print_error(f"✗ Расхождение данных: ProfitAdmin=${human_bot_commission_diff:.2f}, HumanBots=${period_revenue_diff:.2f}")
                        
                    return True
                else:
                    print_error("Игра не завершилась в ожидаемое время")
                    return False
            else:
                print_error(f"Ошибка создания игры Human-ботом: {resp.status}")
                text = await resp.text()
                print_debug(f"Ответ: {text}")
                return False
                
    async def test_human_bot_vs_player(self):
        """Тест: Human-бот vs живой игрок"""
        print_test_header("Human-бот vs Живой игрок")
        
        # Создаём Human-бота и игрока
        bot = await self.create_test_human_bot("balanced")
        player = await self.create_test_user(balance=500)
        
        if not bot or not player:
            print_error("Не удалось создать участников")
            return False
            
        bet_amount = 40
        
        # Сценарий 1: Игрок создаёт игру, Human-бот присоединяется
        print_info("\nСценарий 1: Игрок создаёт игру")
        
        game = await self.create_game(player['token'], bet_amount, "rock")
        if not game:
            return False
            
        game_id = game["id"]
        print_success(f"Игрок создал игру {game_id} со ставкой ${bet_amount}")
        
        # Ждём присоединения бота
        print_info("Ожидаем присоединения Human-бота...")
        completed_game = await self.wait_for_human_bot_join(game_id)
        
        if completed_game:
            winner_id = completed_game.get("winner_id")
            commission = completed_game.get("commission_amount", 0)
            
            print_success("Игра завершена!")
            print_info(f"Победитель: {'Human-бот' if winner_id == bot['id'] else 'Игрок'}")
            print_info(f"Комиссия: ${commission:.2f}")
            
            # Сохраняем текущую статистику
            stats_before = await self.get_current_stats()
            
            # Сценарий 2: Human-бот создаёт игру
            print_info("\nСценарий 2: Human-бот создаёт игру")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.post(f"{BASE_URL}/admin/human-bots/{bot['id']}/create-game",
                                       headers=headers,
                                       json={"bet_amount": bet_amount}) as resp:
                if resp.status == 200:
                    game_data = await resp.json()
                    game_id = game_data["game_id"]
                    print_success(f"Human-бот создал игру {game_id}")
                    
                    # Игрок присоединяется
                    join_result = await self.join_game(game_id, player['token'], "scissors")
                    
                    if join_result:
                        winner_id = join_result.get("winner_id")
                        commission = join_result.get("commission_amount", 0)
                        
                        print_success("Игра завершена!")
                        print_info(f"Победитель: {'Human-бот' if winner_id == bot['id'] else 'Игрок'}")
                        print_info(f"Комиссия: ${commission:.2f}")
                        
                        # Проверяем изменения в статистике
                        await asyncio.sleep(1)
                        stats_after = await self.get_current_stats()
                        
                        # Анализируем результаты обеих игр
                        total_bet_commission_diff = stats_after['profit']['bet_commission'] - self.initial_stats['profit']['bet_commission']
                        total_human_bot_commission_diff = stats_after['profit']['human_bot_commission'] - self.initial_stats['profit']['human_bot_commission']
                        total_period_revenue_diff = stats_after['human_bots']['period_revenue'] - self.initial_stats['human_bots']['period_revenue']
                        
                        print_info(f"\nОбщие изменения после двух игр:")
                        print_info(f"Комиссия от ставок: +${total_bet_commission_diff:.2f}")
                        print_info(f"Комиссия от Human-ботов: +${total_human_bot_commission_diff:.2f}")
                        print_info(f"Доход за период: +${total_period_revenue_diff:.2f}")
                        
                        # Проверка синхронизации
                        if abs(total_human_bot_commission_diff - total_period_revenue_diff) < 0.01:
                            print_success("✓ Данные синхронизированы")
                        else:
                            print_error(f"✗ Расхождение данных: ${total_human_bot_commission_diff:.2f} vs ${total_period_revenue_diff:.2f}")
                            
                        return True
                        
        return False
        
    async def test_player_vs_player(self):
        """Тест: Живой игрок vs Живой игрок"""
        print_test_header("Живой игрок vs Живой игрок")
        
        # Создаём двух игроков
        player1 = await self.create_test_user(balance=300)
        player2 = await self.create_test_user(balance=300)
        
        if not player1 or not player2:
            print_error("Не удалось создать игроков")
            return False
            
        bet_amount = 30
        
        # Сохраняем статистику до игры
        stats_before = await self.get_current_stats()
        
        # Игрок 1 создаёт игру
        game = await self.create_game(player1['token'], bet_amount, "rock")
        if not game:
            return False
            
        game_id = game["id"]
        print_success(f"Игрок 1 создал игру {game_id} со ставкой ${bet_amount}")
        
        # Игрок 2 присоединяется
        join_result = await self.join_game(game_id, player2['token'], "paper")
        
        if join_result:
            winner_id = join_result.get("winner_id")
            commission = join_result.get("commission_amount", 0)
            
            print_success("Игра завершена!")
            print_info(f"Победитель: {'Игрок 1' if winner_id == player1['id'] else 'Игрок 2'}")
            print_info(f"Комиссия: ${commission:.2f}")
            
            # Проверяем статистику
            await asyncio.sleep(1)
            stats_after = await self.get_current_stats()
            
            bet_commission_diff = stats_after['profit']['bet_commission'] - stats_before['profit']['bet_commission']
            human_bot_commission_diff = stats_after['profit']['human_bot_commission'] - stats_before['profit']['human_bot_commission']
            period_revenue_diff = stats_after['human_bots']['period_revenue'] - stats_before['human_bots']['period_revenue']
            
            print_info(f"\nИзменения в статистике:")
            print_info(f"Комиссия от ставок: +${bet_commission_diff:.2f}")
            print_info(f"Комиссия от Human-ботов: +${human_bot_commission_diff:.2f}")
            print_info(f"Доход за период: +${period_revenue_diff:.2f}")
            
            # Проверки
            if abs(bet_commission_diff - commission) < 0.01:
                print_success("✓ Комиссия правильно записана как BET_COMMISSION")
            else:
                print_error(f"✗ Ошибка в BET_COMMISSION: ожидалось ${commission:.2f}, получено ${bet_commission_diff:.2f}")
                
            if abs(human_bot_commission_diff) < 0.01:
                print_success("✓ HUMAN_BOT_COMMISSION не изменилась (правильно)")
            else:
                print_error(f"✗ HUMAN_BOT_COMMISSION неожиданно изменилась на ${human_bot_commission_diff:.2f}")
                
            if abs(period_revenue_diff) < 0.01:
                print_success("✓ period_revenue не изменился (правильно)")
            else:
                print_error(f"✗ period_revenue неожиданно изменился на ${period_revenue_diff:.2f}")
                
            return True
            
        return False
        
    async def test_commission_sync(self):
        """Тест синхронизации данных комиссий"""
        print_test_header("Синхронизация данных комиссий")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Получаем текущие данные
        stats = await self.get_current_stats()
        
        human_bot_commission = stats['profit'].get('human_bot_commission', 0)
        period_revenue = stats['human_bots'].get('period_revenue', 0)
        commission_breakdown_total = stats['commission_breakdown'].get('total_amount', 0)
        
        print_info(f"Текущие значения:")
        print_info(f"ProfitAdmin (human_bot_commission): ${human_bot_commission:.2f}")
        print_info(f"HumanBotsManagement (period_revenue): ${period_revenue:.2f}")
        print_info(f"Модальное окно (total_amount): ${commission_breakdown_total:.2f}")
        
        # Проверяем синхронизацию
        all_equal = (
            abs(human_bot_commission - period_revenue) < 0.01 and
            abs(human_bot_commission - commission_breakdown_total) < 0.01
        )
        
        if all_equal:
            print_success("✓ Все значения уже синхронизированы")
            return True
        else:
            print_warning("Обнаружены расхождения, запускаем синхронизацию...")
            
            # Запускаем синхронизацию
            async with self.session.post(f"{BASE_URL}/admin/human-bots/sync-commission-data", headers=headers) as resp:
                if resp.status == 200:
                    sync_data = await resp.json()
                    print_success("Синхронизация выполнена")
                    print_info(f"Старое значение: ${sync_data.get('old_value', 0):.2f}")
                    print_info(f"Новое значение: ${sync_data.get('new_value', 0):.2f}")
                    print_info(f"Разница: ${sync_data.get('difference', 0):.2f}")
                    
                    # Проверяем результат
                    await asyncio.sleep(1)
                    stats_after = await self.get_current_stats()
                    
                    human_bot_commission_after = stats_after['profit'].get('human_bot_commission', 0)
                    period_revenue_after = stats_after['human_bots'].get('period_revenue', 0)
                    commission_breakdown_total_after = stats_after['commission_breakdown'].get('total_amount', 0)
                    
                    all_equal_after = (
                        abs(human_bot_commission_after - period_revenue_after) < 0.01 and
                        abs(human_bot_commission_after - commission_breakdown_total_after) < 0.01
                    )
                    
                    if all_equal_after:
                        print_success("✓ Данные успешно синхронизированы")
                        print_info(f"Единое значение: ${human_bot_commission_after:.2f}")
                        return True
                    else:
                        print_error("✗ Данные всё ещё не синхронизированы")
                        return False
                else:
                    print_error(f"Ошибка синхронизации: {resp.status}")
                    return False
                    
    async def test_edge_cases(self):
        """Тест граничных случаев"""
        print_test_header("Граничные случаи и обработка ошибок")
        
        # Тест 1: Ничья (не должно быть комиссии)
        print_info("\nТест 1: Игра с ничьёй")
        
        player1 = await self.create_test_user(balance=100)
        player2 = await self.create_test_user(balance=100)
        
        if player1 and player2:
            stats_before = await self.get_current_stats()
            
            # Создаём игру с одинаковыми ходами
            game = await self.create_game(player1['token'], 20, "rock")
            if game:
                join_result = await self.join_game(game["id"], player2['token'], "rock")
                
                if join_result and join_result.get("result") == "draw":
                    print_success("Игра завершилась ничьёй")
                    
                    # Проверяем, что комиссия не взималась
                    await asyncio.sleep(1)
                    stats_after = await self.get_current_stats()
                    
                    bet_commission_diff = stats_after['profit']['bet_commission'] - stats_before['profit']['bet_commission']
                    human_bot_commission_diff = stats_after['profit']['human_bot_commission'] - stats_before['profit']['human_bot_commission']
                    
                    if abs(bet_commission_diff) < 0.01 and abs(human_bot_commission_diff) < 0.01:
                        print_success("✓ Комиссия не взималась при ничьей (правильно)")
                    else:
                        print_error(f"✗ Неожиданная комиссия при ничьей: BET=${bet_commission_diff:.2f}, HUMAN_BOT=${human_bot_commission_diff:.2f}")
                        
        # Тест 2: Сброс дохода за период
        print_info("\nТест 2: Сброс дохода за период")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Сначала проверяем текущий доход
        stats_before_reset = await self.get_current_stats()
        period_revenue_before = stats_before_reset['human_bots'].get('period_revenue', 0)
        human_bot_commission_before = stats_before_reset['profit'].get('human_bot_commission', 0)
        
        print_info(f"Доход до сброса: ${period_revenue_before:.2f}")
        
        if period_revenue_before > 0:
            # Выполняем сброс
            async with self.session.post(f"{BASE_URL}/admin/human-bots/reset-period-revenue", headers=headers) as resp:
                if resp.status == 200:
                    reset_data = await resp.json()
                    print_success(f"Доход сброшен. {reset_data.get('message', '')}")
                    
                    # Проверяем результат
                    await asyncio.sleep(1)
                    stats_after_reset = await self.get_current_stats()
                    
                    period_revenue_after = stats_after_reset['human_bots'].get('period_revenue', 0)
                    human_bot_commission_after = stats_after_reset['profit'].get('human_bot_commission', 0)
                    
                    if abs(period_revenue_after) < 0.01 and abs(human_bot_commission_after) < 0.01:
                        print_success("✓ Доход и комиссии успешно сброшены")
                    else:
                        print_error(f"✗ Ошибка сброса: period_revenue=${period_revenue_after:.2f}, commission=${human_bot_commission_after:.2f}")
                else:
                    print_error(f"Ошибка сброса дохода: {resp.status}")
        else:
            print_info("Доход уже нулевой, пропускаем тест сброса")
            
        return True
        
    async def run_all_tests(self):
        """Запуск всех тестов"""
        try:
            await self.setup()
            
            results = {
                "human_bot_vs_human_bot": False,
                "human_bot_vs_player": False,
                "player_vs_player": False,
                "commission_sync": False,
                "edge_cases": False
            }
            
            # Запускаем тесты
            results["human_bot_vs_human_bot"] = await self.test_human_bot_vs_human_bot()
            await asyncio.sleep(2)
            
            results["human_bot_vs_player"] = await self.test_human_bot_vs_player()
            await asyncio.sleep(2)
            
            results["player_vs_player"] = await self.test_player_vs_player()
            await asyncio.sleep(2)
            
            results["commission_sync"] = await self.test_commission_sync()
            await asyncio.sleep(2)
            
            results["edge_cases"] = await self.test_edge_cases()
            
            # Итоговая проверка синхронизации
            print_test_header("Финальная проверка синхронизации")
            
            final_stats = await self.get_current_stats()
            
            human_bot_commission = final_stats['profit'].get('human_bot_commission', 0)
            period_revenue = final_stats['human_bots'].get('period_revenue', 0)
            commission_breakdown_total = final_stats['commission_breakdown'].get('total_amount', 0)
            
            print_info(f"Финальные значения:")
            print_info(f"ProfitAdmin: ${human_bot_commission:.2f}")
            print_info(f"HumanBotsManagement: ${period_revenue:.2f}")
            print_info(f"Модальное окно: ${commission_breakdown_total:.2f}")
            
            all_synced = (
                abs(human_bot_commission - period_revenue) < 0.01 and
                abs(human_bot_commission - commission_breakdown_total) < 0.01
            )
            
            if all_synced:
                print_success("✓ Все данные полностью синхронизированы!")
            else:
                print_error("✗ Обнаружены расхождения в финальной проверке")
                
            # Сводка результатов
            print_test_header("Сводка результатов")
            
            passed = sum(1 for v in results.values() if v)
            total = len(results)
            
            for test_name, result in results.items():
                status = "✓ PASSED" if result else "✗ FAILED"
                color = Colors.GREEN if result else Colors.RED
                print(f"{color}{status}{Colors.RESET} - {test_name.replace('_', ' ').title()}")
                
            print(f"\nВсего тестов: {total}")
            print(f"Пройдено: {passed}")
            print(f"Провалено: {total - passed}")
            
            if passed == total and all_synced:
                print(f"\n{Colors.GREEN}{Colors.BOLD}ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!{Colors.RESET}")
                return True
            else:
                print(f"\n{Colors.RED}{Colors.BOLD}НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ{Colors.RESET}")
                return False
                
        finally:
            await self.cleanup()

async def main():
    """Основная функция"""
    print(f"{Colors.BOLD}{Colors.CYAN}Комплексный тест логики комиссий{Colors.RESET}")
    print(f"{Colors.CYAN}Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.CYAN}База данных: {BASE_URL}{Colors.RESET}")
    
    tester = CommissionTester()
    
    try:
        success = await tester.run_all_tests()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Тест прерван пользователем{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Критическая ошибка: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())