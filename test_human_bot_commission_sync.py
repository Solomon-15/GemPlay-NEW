#!/usr/bin/env python3
"""
Тест синхронизации данных комиссий Human-ботов
"""

import asyncio
import aiohttp
import json
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

async def get_profit_stats(session, token):
    """Получить статистику прибыли"""
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{BASE_URL}/admin/profit/stats", headers=headers) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print_error(f"Ошибка получения статистики прибыли: {resp.status}")
            return None

async def get_human_bot_stats(session, token):
    """Получить статистику Human-ботов"""
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{BASE_URL}/admin/human-bots/stats", headers=headers) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print_error(f"Ошибка получения статистики Human-ботов: {resp.status}")
            return None

async def get_human_bot_commission_breakdown(session, token):
    """Получить детализацию комиссий Human-ботов"""
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{BASE_URL}/admin/profit/human-bot-commission-breakdown?period=all", headers=headers) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print_error(f"Ошибка получения детализации комиссий: {resp.status}")
            return None

async def sync_commission_data(session, token):
    """Синхронизировать данные комиссий"""
    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(f"{BASE_URL}/admin/human-bots/sync-commission-data", headers=headers) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print_error(f"Ошибка синхронизации данных: {resp.status}")
            return None

async def run_tests():
    """Основная функция тестирования"""
    async with aiohttp.ClientSession() as session:
        # 1. Вход в систему
        print_test_header("Вход администратора")
        token = await login_admin(session)
        if not token:
            print_error("Не удалось войти в систему")
            return
        print_success("Успешный вход в систему")

        # 2. Получение текущих данных
        print_test_header("Получение текущих данных комиссий")
        
        # Статистика прибыли
        profit_stats = await get_profit_stats(session, token)
        if profit_stats:
            human_bot_commission_profit = profit_stats.get("human_bot_commission", 0)
            print_info(f"Комиссия Human-ботов (ProfitAdmin): ${human_bot_commission_profit:.2f}")
        
        # Статистика Human-ботов
        human_bot_stats = await get_human_bot_stats(session, token)
        if human_bot_stats:
            period_revenue = human_bot_stats.get("period_revenue", 0)
            print_info(f"Доход за период (HumanBotsManagement): ${period_revenue:.2f}")
        
        # Детализация комиссий
        commission_breakdown = await get_human_bot_commission_breakdown(session, token)
        if commission_breakdown:
            total_commission = commission_breakdown.get("total_amount", 0)
            print_info(f"Общая сумма комиссий (модальное окно): ${total_commission:.2f}")
        
        # 3. Проверка синхронизации
        print_test_header("Проверка синхронизации данных")
        
        # Проверяем, совпадают ли значения
        if profit_stats and human_bot_stats and commission_breakdown:
            values_match = (
                abs(human_bot_commission_profit - period_revenue) < 0.01 and
                abs(human_bot_commission_profit - total_commission) < 0.01
            )
            
            if values_match:
                print_success("Все значения синхронизированы!")
                print_info(f"Единое значение комиссии: ${human_bot_commission_profit:.2f}")
            else:
                print_warning("Обнаружены расхождения в данных")
                print_info(f"ProfitAdmin: ${human_bot_commission_profit:.2f}")
                print_info(f"HumanBotsManagement: ${period_revenue:.2f}")
                print_info(f"Модальное окно: ${total_commission:.2f}")
                
                # 4. Синхронизация данных
                print_test_header("Синхронизация данных")
                sync_result = await sync_commission_data(session, token)
                if sync_result and sync_result.get("success"):
                    print_success("Данные успешно синхронизированы")
                    print_info(f"Старое значение: ${sync_result.get('old_value', 0):.2f}")
                    print_info(f"Новое значение: ${sync_result.get('new_value', 0):.2f}")
                    print_info(f"Разница: ${sync_result.get('difference', 0):.2f}")
                    
                    # 5. Повторная проверка после синхронизации
                    print_test_header("Проверка после синхронизации")
                    await asyncio.sleep(1)  # Небольшая задержка
                    
                    # Получаем обновленные данные
                    profit_stats = await get_profit_stats(session, token)
                    human_bot_stats = await get_human_bot_stats(session, token)
                    commission_breakdown = await get_human_bot_commission_breakdown(session, token)
                    
                    if profit_stats and human_bot_stats and commission_breakdown:
                        human_bot_commission_profit = profit_stats.get("human_bot_commission", 0)
                        period_revenue = human_bot_stats.get("period_revenue", 0)
                        total_commission = commission_breakdown.get("total_amount", 0)
                        
                        values_match = (
                            abs(human_bot_commission_profit - period_revenue) < 0.01 and
                            abs(human_bot_commission_profit - total_commission) < 0.01
                        )
                        
                        if values_match:
                            print_success("Все значения теперь синхронизированы!")
                            print_info(f"Единое значение комиссии: ${human_bot_commission_profit:.2f}")
                        else:
                            print_error("Значения всё ещё расходятся")
                            print_info(f"ProfitAdmin: ${human_bot_commission_profit:.2f}")
                            print_info(f"HumanBotsManagement: ${period_revenue:.2f}")
                            print_info(f"Модальное окно: ${total_commission:.2f}")
        
        # 6. Дополнительная информация
        print_test_header("Дополнительная информация")
        if human_bot_stats:
            print_info(f"Всего Human-ботов: {human_bot_stats.get('total_bots', 0)}")
            print_info(f"Активных Human-ботов: {human_bot_stats.get('active_bots', 0)}")
            print_info(f"Всего игр сыграно: {human_bot_stats.get('total_games_played', 0)}")
        
        if commission_breakdown:
            print_info(f"Уникальных ботов с комиссиями: {commission_breakdown.get('unique_bots', 0)}")
            print_info(f"Всего транзакций комиссий: {commission_breakdown.get('total_transactions', 0)}")
            if commission_breakdown.get('summary', {}).get('top_earning_bot'):
                print_info(f"Топ бот по комиссиям: {commission_breakdown['summary']['top_earning_bot']} "
                         f"(${commission_breakdown['summary']['top_earning_amount']:.2f})")

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.CYAN}Тест синхронизации комиссий Human-ботов{Colors.RESET}")
    print(f"{Colors.CYAN}Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    
    try:
        asyncio.run(run_tests())
        print(f"\n{Colors.GREEN}Тест завершен успешно{Colors.RESET}")
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Тест прерван пользователем{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Ошибка при выполнении теста: {e}{Colors.RESET}")
        sys.exit(1)