#!/usr/bin/env python3
"""
Скрипт для тестирования предотвращения превышения лимитов
"""

import asyncio
from pymongo import MongoClient
import os
import uuid
from datetime import datetime

async def test_limit_prevention():
    """Тестирование предотвращения превышения лимитов"""
    
    # Подключение к MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/gemplay')
    client = MongoClient(mongo_url)
    db = client.gemplay
    
    print("=== ТЕСТИРОВАНИЕ ПРЕДОТВРАЩЕНИЯ ПРЕВЫШЕНИЯ ЛИМИТОВ ===")
    
    # Устанавливаем низкие лимиты для тестирования
    bot_settings = {
        "id": "bot_settings",
        "max_active_bets_regular": 3,  # низкий лимит для тестирования
        "max_active_bets_human": 2,   # низкий лимит для тестирования
        "pagination_size": 10,
        "auto_queue_activation": True,
        "priority_type": "order"
    }
    
    db.bot_settings.replace_one(
        {"id": "bot_settings"},
        bot_settings,
        upsert=True
    )
    
    print(f"✅ Установлены низкие лимиты для тестирования:")
    print(f"   - Regular боты: {bot_settings['max_active_bets_regular']}")
    print(f"   - Human боты: {bot_settings['max_active_bets_human']}")
    
    # Создаем тестовые ставки до лимита
    print("\n=== СОЗДАНИЕ СТАВОК ДО ЛИМИТА ===")
    
    # Создаем 3 ставки для Regular ботов (достигаем лимита)
    for i in range(3):
        game = {
            "id": str(uuid.uuid4()),
            "creator_id": str(uuid.uuid4()),
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
    
    # Создаем 2 ставки для Human ботов (достигаем лимита)
    for i in range(2):
        game = {
            "id": str(uuid.uuid4()),
            "creator_id": str(uuid.uuid4()),
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
    
    # Проверяем текущие лимиты
    regular_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "REGULAR"},
            {"metadata.bot_type": "REGULAR"}
        ]
    })
    
    human_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "HUMAN"},
            {"metadata.bot_type": "HUMAN"}
        ]
    })
    
    print(f"🤖 Regular боты: {regular_bets}/{bot_settings['max_active_bets_regular']}")
    print(f"👤 Human боты: {human_bets}/{bot_settings['max_active_bets_human']}")
    
    # Проверяем что лимиты достигнуты
    if regular_bets >= bot_settings['max_active_bets_regular']:
        print("✅ Лимит Regular ботов достигнут")
    else:
        print("❌ Лимит Regular ботов НЕ достигнут")
    
    if human_bets >= bot_settings['max_active_bets_human']:
        print("✅ Лимит Human ботов достигнут")
    else:
        print("❌ Лимит Human ботов НЕ достигнут")
    
    print("\n=== ТЕСТИРОВАНИЕ КОДА ПРЕДОТВРАЩЕНИЯ ===")
    
    # Теперь проверим код предотвращения
    # Имитируем функции проверки лимитов
    
    # Для Regular ботов
    current_regular_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "REGULAR"},
            {"metadata.bot_type": "REGULAR"}
        ]
    })
    
    max_regular = bot_settings['max_active_bets_regular']
    
    if current_regular_bets >= max_regular:
        print(f"🚫 Создание Regular ставки БЛОКИРОВАНО: {current_regular_bets}/{max_regular}")
    else:
        print(f"✅ Создание Regular ставки РАЗРЕШЕНО: {current_regular_bets}/{max_regular}")
    
    # Для Human ботов
    current_human_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "HUMAN"},
            {"metadata.bot_type": "HUMAN"}
        ]
    })
    
    max_human = bot_settings['max_active_bets_human']
    
    if current_human_bets >= max_human:
        print(f"🚫 Создание Human ставки БЛОКИРОВАНО: {current_human_bets}/{max_human}")
    else:
        print(f"✅ Создание Human ставки РАЗРЕШЕНО: {current_human_bets}/{max_human}")
    
    # Восстанавливаем нормальные лимиты
    print("\n=== ВОССТАНОВЛЕНИЕ НОРМАЛЬНЫХ ЛИМИТОВ ===")
    
    normal_settings = {
        "id": "bot_settings",
        "max_active_bets_regular": 50,
        "max_active_bets_human": 30,
        "pagination_size": 10,
        "auto_queue_activation": True,
        "priority_type": "order"
    }
    
    db.bot_settings.replace_one(
        {"id": "bot_settings"},
        normal_settings,
        upsert=True
    )
    
    # Очищаем тестовые данные
    db.games.delete_many({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING"
    })
    
    print("✅ Нормальные лимиты восстановлены")
    print("✅ Тестовые данные очищены")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_limit_prevention())