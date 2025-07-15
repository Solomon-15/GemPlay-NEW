#!/usr/bin/env python3
"""
Тест для проверки логики заморозки баланса при игре с обычными ботами
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Добавляем путь к серверу
sys.path.append('/app/backend')

from server import db

async def test_regular_bot_commission_logic():
    """Тест логики комиссии для обычных ботов"""
    print("🧪 Начинаем тест логики комиссии для обычных ботов...")
    
    # Найдем игру с обычным ботом
    regular_bot_game = await db.games.find_one({
        "creator_type": "bot",
        "bot_type": "REGULAR",
        "status": "ACTIVE"
    })
    
    if regular_bot_game:
        print(f"✅ Найдена игра с обычным ботом: {regular_bot_game['id']}")
        print(f"   Создатель: {regular_bot_game['creator_id']}")
        print(f"   Тип создателя: {regular_bot_game.get('creator_type', 'не указан')}")
        print(f"   Тип бота: {regular_bot_game.get('bot_type', 'не указан')}")
        print(f"   Флаг regular bot game: {regular_bot_game.get('is_regular_bot_game', False)}")
        print(f"   Сумма ставки: ${regular_bot_game['bet_amount']}")
        
        # Проверим оппонента
        if regular_bot_game.get('opponent_id'):
            opponent = await db.users.find_one({"id": regular_bot_game['opponent_id']})
            if opponent:
                print(f"   Оппонент: {opponent.get('username', 'Неизвестно')}")
                print(f"   Баланс оппонента: ${opponent.get('virtual_balance', 0)}")
                print(f"   Заморожено у оппонента: ${opponent.get('frozen_balance', 0)}")
    else:
        print("❌ Не найдено игр с обычными ботами")
    
    # Найдем игру между пользователями
    user_game = await db.games.find_one({
        "creator_type": "user",
        "status": "ACTIVE"
    })
    
    if user_game:
        print(f"\n✅ Найдена игра между пользователями: {user_game['id']}")
        print(f"   Создатель: {user_game['creator_id']}")
        print(f"   Тип создателя: {user_game.get('creator_type', 'не указан')}")
        print(f"   Сумма ставки: ${user_game['bet_amount']}")
        
        # Проверим создателя
        creator = await db.users.find_one({"id": user_game['creator_id']})
        if creator:
            print(f"   Создатель: {creator.get('username', 'Неизвестно')}")
            print(f"   Баланс создателя: ${creator.get('virtual_balance', 0)}")
            print(f"   Заморожено у создателя: ${creator.get('frozen_balance', 0)}")
        
        # Проверим оппонента
        if user_game.get('opponent_id'):
            opponent = await db.users.find_one({"id": user_game['opponent_id']})
            if opponent:
                print(f"   Оппонент: {opponent.get('username', 'Неизвестно')}")
                print(f"   Баланс оппонента: ${opponent.get('virtual_balance', 0)}")
                print(f"   Заморожено у оппонента: ${opponent.get('frozen_balance', 0)}")
    else:
        print("❌ Не найдено игр между пользователями")
    
    # Проверим общую статистику замороженных средств
    total_frozen_pipeline = [
        {"$group": {"_id": None, "total_frozen": {"$sum": "$frozen_balance"}}}
    ]
    frozen_result = await db.users.aggregate(total_frozen_pipeline).to_list(1)
    total_frozen = frozen_result[0]["total_frozen"] if frozen_result else 0
    
    print(f"\n📊 Общая статистика:")
    print(f"   Всего заморожено средств: ${total_frozen}")
    
    # Проверим количество игр по типам
    game_stats = await db.games.aggregate([
        {"$group": {
            "_id": "$creator_type",
            "count": {"$sum": 1}
        }}
    ]).to_list(10)
    
    print(f"   Статистика игр по типам:")
    for stat in game_stats:
        print(f"     {stat['_id']}: {stat['count']} игр")
    
    # Проверим обычных ботов
    regular_bots = await db.bots.find({"bot_type": "REGULAR"}).to_list(10)
    print(f"   Обычных ботов в системе: {len(regular_bots)}")
    
    print("\n🎯 Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_regular_bot_commission_logic())