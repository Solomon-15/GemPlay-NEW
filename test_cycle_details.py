#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы деталей цикла
"""

import asyncio
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import requests
import json

# Загружаем переменные окружения
load_dotenv()

# Подключение к MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "rps_game")
API_URL = "http://localhost:3000"

async def test_cycle_details():
    """Тестирует функционал деталей цикла"""
    try:
        # Подключаемся к MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        
        print(f"Connected to MongoDB: {MONGODB_URL}")
        print(f"Database: {DB_NAME}")
        
        # Авторизуемся
        print("\n🔐 Авторизация...")
        login_response = requests.post(f"{API_URL}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Ошибка авторизации: {login_response.status_code}")
            print(login_response.text)
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Авторизация успешна")
        
        # Получаем список ботов
        print("\n📋 Получение списка ботов...")
        bots_response = requests.get(f"{API_URL}/admin/bots", headers=headers)
        
        if bots_response.status_code != 200:
            print(f"❌ Ошибка получения ботов: {bots_response.status_code}")
            return
        
        bots = bots_response.json()["bots"]
        regular_bots = [b for b in bots if b.get("is_regular_bot")]
        print(f"✅ Найдено {len(regular_bots)} обычных ботов")
        
        # Находим бота с завершенными циклами
        test_bot = None
        for bot in regular_bots:
            if bot.get("completed_cycles", 0) > 0:
                test_bot = bot
                break
        
        if not test_bot:
            print("❌ Не найдено ботов с завершенными циклами")
            
            # Проверяем в БД напрямую
            cycles_count = await db.completed_cycles.count_documents({})
            print(f"📊 В БД найдено {cycles_count} завершенных циклов")
            
            if cycles_count > 0:
                # Берем первый цикл
                cycle = await db.completed_cycles.find_one({})
                bot_id = cycle["bot_id"]
                bot = await db.bots.find_one({"id": bot_id})
                if bot:
                    test_bot = bot
                    print(f"✅ Используем бота {bot['name']} из БД")
        
        if not test_bot:
            print("❌ Не удалось найти подходящего бота")
            return
        
        print(f"\n🤖 Тестируем бота: {test_bot['name']}")
        print(f"   Завершенных циклов: {test_bot.get('completed_cycles', 0)}")
        
        # Получаем историю циклов
        print("\n📊 Получение истории циклов...")
        history_response = requests.get(
            f"{API_URL}/admin/bots/{test_bot['id']}/cycle-history",
            headers=headers
        )
        
        if history_response.status_code != 200:
            print(f"❌ Ошибка получения истории: {history_response.status_code}")
            print(history_response.text)
            return
        
        cycles = history_response.json()["games"]
        print(f"✅ Найдено {len(cycles)} циклов")
        
        if not cycles:
            print("❌ Нет доступных циклов")
            return
        
        # Берем первый цикл
        test_cycle = cycles[0]
        print(f"\n🎯 Тестируем цикл #{test_cycle['cycle_number']}:")
        print(f"   ID: {test_cycle['id']}")
        print(f"   Ставок: {test_cycle['total_bets']}")
        print(f"   W/L/D: {test_cycle['wins']}/{test_cycle['losses']}/{test_cycle['draws']}")
        
        # Получаем детали цикла
        print("\n🔍 Получение деталей цикла...")
        details_response = requests.get(
            f"{API_URL}/admin/bots/{test_bot['id']}/completed-cycle-bets",
            params={"cycle_id": test_cycle['id']},
            headers=headers
        )
        
        if details_response.status_code != 200:
            print(f"❌ Ошибка получения деталей: {details_response.status_code}")
            print(details_response.text)
            
            # Проверяем данные в БД
            print("\n🔍 Проверка данных в БД...")
            
            # Проверяем цикл
            db_cycle = await db.completed_cycles.find_one({"id": test_cycle['id']})
            if db_cycle:
                print(f"✅ Цикл найден в БД")
                print(f"   Bot ID: {db_cycle.get('bot_id')}")
                print(f"   Start: {db_cycle.get('start_time')}")
                print(f"   End: {db_cycle.get('end_time')}")
            else:
                print(f"❌ Цикл не найден в БД")
            
            # Проверяем сохраненные игры
            saved_games = await db.cycle_games.count_documents({
                "cycle_id": test_cycle['id'],
                "bot_id": test_bot['id']
            })
            print(f"📊 Сохранено игр для цикла: {saved_games}")
            
            if saved_games == 0:
                print("⚠️ Игры не сохранены в cycle_games, проверяем по времени...")
                
                if db_cycle:
                    games_by_time = await db.games.count_documents({
                        "creator_id": test_bot['id'],
                        "status": "COMPLETED",
                        "created_at": {
                            "$gte": db_cycle["start_time"],
                            "$lte": db_cycle["end_time"]
                        }
                    })
                    print(f"📊 Найдено игр по времени: {games_by_time}")
            
            return
        
        data = details_response.json()
        bets = data.get("bets", [])
        
        print(f"✅ Получено {len(bets)} ставок")
        
        if bets:
            # Показываем первые 3 ставки
            print("\n📋 Примеры ставок:")
            for i, bet in enumerate(bets[:3], 1):
                print(f"\n   Ставка #{bet['game_number']}:")
                print(f"   ID: {bet['id']}")
                print(f"   Сумма: ${bet['bet_amount']}")
                print(f"   Гемы: {bet.get('bet_gems', {})}")
                print(f"   Ходы: {bet['creator_move']} vs {bet['opponent_move']}")
                print(f"   Противник: {bet['opponent_name']}")
                print(f"   Результат: {bet['result']}")
        
        print("\n✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Запуск теста деталей цикла...")
    asyncio.run(test_cycle_details())