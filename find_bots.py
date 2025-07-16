#!/usr/bin/env python3
"""
Скрипт для поиска всех коллекций с ботами
"""

import asyncio
from pymongo import MongoClient
import os

async def find_all_bot_collections():
    """Поиск всех коллекций с ботами"""
    
    # Подключение к MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/gemplay')
    client = MongoClient(mongo_url)
    db = client.gemplay
    
    print("=== ПОИСК ВСЕХ КОЛЛЕКЦИЙ С БОТАМИ ===")
    
    # Получаем все коллекции
    collections = db.list_collection_names()
    print(f"📊 Найдено коллекций: {len(collections)}")
    
    for collection_name in collections:
        count = db[collection_name].count_documents({})
        print(f"   - {collection_name}: {count} документов")
        
        if count > 0:
            # Получаем первые 5 документов
            docs = list(db[collection_name].find({}).limit(5))
            print(f"     👀 Первые документы:")
            for doc in docs:
                # Ищем bot-подобные поля
                bot_fields = []
                for key, value in doc.items():
                    if 'bot' in key.lower() or 'creator' in key.lower() or key in ['id', 'name', 'type']:
                        bot_fields.append(f"{key}: {value}")
                
                if bot_fields:
                    print(f"       - {' | '.join(bot_fields[:3])}")
    
    # Проверяем игры на bot данные
    print(f"\n=== ПРОВЕРКА ИГРОВЫХ ДАННЫХ ===")
    
    # Ищем игры с bot данными
    bot_games = list(db.games.find({
        "$or": [
            {"creator_type": "bot"},
            {"is_bot_game": True},
            {"creator_username": {"$regex": "Bot #"}}
        ]
    }).limit(5))
    
    print(f"🎮 Найдено bot игр: {len(bot_games)}")
    
    for game in bot_games:
        print(f"   - Game {game.get('id', 'Unknown')[:8]}...")
        print(f"     Creator: {game.get('creator_username', 'Unknown')}")
        print(f"     Creator ID: {game.get('creator_id', 'Unknown')}")
        print(f"     Status: {game.get('status', 'Unknown')}")
        print(f"     Bot type: {game.get('bot_type', 'Unknown')}")
        print(f"     Is bot game: {game.get('is_bot_game', False)}")
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(find_all_bot_collections())