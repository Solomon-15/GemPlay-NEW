#!/usr/bin/env python3
"""
Скрипт для тестирования глобальных лимитов ботов
"""

import asyncio
from pymongo import MongoClient
import os
import uuid
from datetime import datetime

async def test_global_limits():
    """Тестирование глобальных лимитов"""
    
    # Подключение к MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/gemplay')
    client = MongoClient(mongo_url)
    db = client.gemplay
    
    print("=== ТЕСТИРОВАНИЕ ГЛОБАЛЬНЫХ ЛИМИТОВ ===")
    
    # Создаем тестового Regular бота
    test_bot = {
        "id": str(uuid.uuid4()),
        "name": "Test Regular Bot",
        "bot_type": "REGULAR",
        "is_active": True,
        "cycle_length": 12,
        "cycle_amount": 1000,
        "min_bet": 10,
        "max_bet": 100,
        "win_percentage": 60,
        "current_limit": 10,
        "active_bets": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Вставляем тестового бота
    db.bots.insert_one(test_bot)
    print(f"✅ Создан тестовый бот: {test_bot['name']} ({test_bot['bot_type']})")
    
    # Создаем тестового Human бота
    test_human_bot = {
        "id": str(uuid.uuid4()),
        "name": "Test Human Bot",
        "bot_type": "HUMAN",
        "is_active": True,
        "cycle_length": 12,
        "cycle_amount": 1000,
        "min_bet": 10,
        "max_bet": 100,
        "win_percentage": 60,
        "current_limit": 10,
        "active_bets": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Вставляем тестового Human бота
    db.bots.insert_one(test_human_bot)
    print(f"✅ Создан тестовый Human бот: {test_human_bot['name']} ({test_human_bot['bot_type']})")
    
    # Теперь симулируем создание ставок чтобы проверить лимиты
    print("\n=== СИМУЛЯЦИЯ СОЗДАНИЯ СТАВОК ===")
    
    # Создаем 5 ставок для Regular бота
    for i in range(5):
        game = {
            "id": str(uuid.uuid4()),
            "creator_id": test_bot["id"],
            "creator_type": "bot",
            "is_bot_game": True,
            "bot_type": "REGULAR",
            "status": "WAITING",
            "bet_amount": 50,
            "gems": {"Ruby": 50},
            "created_at": datetime.utcnow(),
            "metadata": {"bot_type": "REGULAR"}
        }
        db.games.insert_one(game)
    
    print(f"✅ Созданы 5 ставок для Regular бота")
    
    # Создаем 3 ставки для Human бота
    for i in range(3):
        game = {
            "id": str(uuid.uuid4()),
            "creator_id": test_human_bot["id"],
            "creator_type": "bot",
            "is_bot_game": True,
            "bot_type": "HUMAN",
            "status": "WAITING",
            "bet_amount": 50,
            "gems": {"Ruby": 50},
            "created_at": datetime.utcnow(),
            "metadata": {"bot_type": "HUMAN"}
        }
        db.games.insert_one(game)
    
    print(f"✅ Созданы 3 ставки для Human бота")
    
    # Проверяем лимиты
    print("\n=== ПРОВЕРКА ЛИМИТОВ ПОСЛЕ СОЗДАНИЯ СТАВОК ===")
    
    # Получаем настройки
    bot_settings = db.bot_settings.find_one({"id": "bot_settings"})
    max_regular = bot_settings.get("max_active_bets_regular", 50)
    max_human = bot_settings.get("max_active_bets_human", 30)
    
    # Проверяем Regular боты
    regular_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "REGULAR"},
            {"metadata.bot_type": "REGULAR"}
        ]
    })
    
    # Проверяем Human боты  
    human_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "HUMAN"},
            {"metadata.bot_type": "HUMAN"}
        ]
    })
    
    print(f"🤖 Regular боты: {regular_bets}/{max_regular}")
    print(f"👤 Human боты: {human_bets}/{max_human}")
    
    # Проверяем что лимиты соблюдаются
    if regular_bets <= max_regular:
        print("✅ Лимит Regular ботов соблюден")
    else:
        print("❌ Лимит Regular ботов превышен")
    
    if human_bets <= max_human:
        print("✅ Лимит Human ботов соблюден")
    else:
        print("❌ Лимит Human ботов превышен")
    
    # Очищаем тестовые данные
    print("\n=== ОЧИСТКА ТЕСТОВЫХ ДАННЫХ ===")
    
    # Удаляем тестовые игры
    db.games.delete_many({
        "creator_id": {"$in": [test_bot["id"], test_human_bot["id"]]}
    })
    
    # Удаляем тестовые боты
    db.bots.delete_many({
        "id": {"$in": [test_bot["id"], test_human_bot["id"]]}
    })
    
    print("✅ Тестовые данные очищены")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_global_limits())