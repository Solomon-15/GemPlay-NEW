#!/usr/bin/env python3
"""
Скрипт для создания настроек глобальных лимитов ботов
"""

import asyncio
from pymongo import MongoClient
import os

async def create_bot_settings():
    """Создание настроек глобальных лимитов"""
    
    # Подключение к MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/gemplay')
    client = MongoClient(mongo_url)
    db = client.gemplay
    
    print("=== СОЗДАНИЕ НАСТРОЕК ГЛОБАЛЬНЫХ ЛИМИТОВ ===")
    
    # Создаем настройки с defaults
    bot_settings = {
        "id": "bot_settings",
        "max_active_bets_regular": 50,
        "max_active_bets_human": 30,
        "pagination_size": 10,
        "auto_queue_activation": True,
        "priority_type": "order"
    }
    
    # Вставляем или обновляем настройки
    result = db.bot_settings.replace_one(
        {"id": "bot_settings"},
        bot_settings,
        upsert=True
    )
    
    if result.upserted_id:
        print("✅ Настройки глобальных лимитов созданы")
    else:
        print("✅ Настройки глобальных лимитов обновлены")
    
    print(f"📊 Установленные лимиты:")
    print(f"   - Regular боты: {bot_settings['max_active_bets_regular']}")
    print(f"   - Human боты: {bot_settings['max_active_bets_human']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_bot_settings())