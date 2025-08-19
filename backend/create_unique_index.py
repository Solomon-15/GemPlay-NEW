#!/usr/bin/env python3
"""
Скрипт для создания уникального индекса на коллекции completed_cycles
для предотвращения дублирования циклов ботов.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

async def create_unique_index():
    """Создает уникальный индекс на (bot_id, cycle_number) в коллекции completed_cycles."""
    
    # Подключение к MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "write_russian_2")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        print("🔧 Создание уникального индекса для коллекции completed_cycles...")
        
        # Проверяем существующие индексы
        existing_indexes = await db.completed_cycles.list_indexes().to_list(100)
        
        print("📋 Существующие индексы:")
        for idx in existing_indexes:
            print(f"  - {idx.get('name', 'unnamed')}: {idx.get('key', {})}")
        
        # Проверяем, есть ли уже нужный индекс
        unique_index_exists = any(
            idx.get('name') == 'unique_bot_cycle' 
            for idx in existing_indexes
        )
        
        if unique_index_exists:
            print("✅ Уникальный индекс 'unique_bot_cycle' уже существует")
        else:
            # Создаем уникальный индекс на (bot_id, cycle_number)
            result = await db.completed_cycles.create_index(
                [("bot_id", 1), ("cycle_number", 1)],
                unique=True,
                name="unique_bot_cycle",
                background=True
            )
            
            print(f"✅ Создан уникальный индекс: {result}")
        
        # Показываем статистику коллекции
        total_docs = await db.completed_cycles.count_documents({})
        fake_docs = await db.completed_cycles.count_documents({
            "id": {"$regex": "^temp_cycle_"}
        })
        
        print(f"\n📊 Статистика коллекции completed_cycles:")
        print(f"   Всего документов: {total_docs}")
        print(f"   Фиктивных циклов: {fake_docs}")
        print(f"   Реальных циклов: {total_docs - fake_docs}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании индекса: {e}")
        
    finally:
        client.close()
        print("🔌 Соединение с базой данных закрыто.")

if __name__ == "__main__":
    print("🔧 Скрипт создания уникального индекса для completed_cycles")
    print("=" * 60)
    
    asyncio.run(create_unique_index())