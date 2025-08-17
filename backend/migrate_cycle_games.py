#!/usr/bin/env python3
"""
Скрипт миграции для сохранения игр существующих циклов в коллекцию cycle_games
"""

import asyncio
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Подключение к MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "rps_game")

async def migrate_cycle_games():
    """Мигрирует игры существующих циклов"""
    try:
        # Подключаемся к MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        
        print(f"Connected to MongoDB: {MONGODB_URL}")
        print(f"Database: {DB_NAME}")
        
        # Получаем все завершенные циклы
        cycles = await db.completed_cycles.find({}).to_list(None)
        print(f"Found {len(cycles)} completed cycles")
        
        migrated_count = 0
        
        for cycle in cycles:
            cycle_id = cycle["id"]
            bot_id = cycle["bot_id"]
            
            # Проверяем, есть ли уже сохраненные игры для этого цикла
            existing_games = await db.cycle_games.count_documents({
                "cycle_id": cycle_id,
                "bot_id": bot_id
            })
            
            if existing_games > 0:
                print(f"Cycle {cycle_id} already has {existing_games} saved games, skipping...")
                continue
            
            # Получаем игры по времени цикла
            start_time = cycle["start_time"]
            end_time = cycle["end_time"]
            
            games = await db.games.find({
                "creator_id": bot_id,
                "status": "COMPLETED",
                "created_at": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }).sort("created_at", 1).to_list(None)
            
            if not games:
                print(f"No games found for cycle {cycle_id} (bot: {bot_id})")
                continue
            
            # Сохраняем игры в коллекцию cycle_games
            cycle_games_to_save = []
            for game in games:
                cycle_game = {
                    "cycle_id": cycle_id,
                    "bot_id": bot_id,
                    "game_id": game.get("id"),
                    "game_data": game,
                    "created_at": datetime.utcnow()
                }
                cycle_games_to_save.append(cycle_game)
            
            if cycle_games_to_save:
                await db.cycle_games.insert_many(cycle_games_to_save)
                print(f"✅ Migrated {len(cycle_games_to_save)} games for cycle {cycle_id} (bot: {bot_id})")
                migrated_count += 1
        
        print(f"\n✅ Migration completed! Migrated {migrated_count} cycles")
        
        # Создаем индексы для оптимизации
        print("\nCreating indexes...")
        await db.cycle_games.create_index([("cycle_id", 1), ("bot_id", 1)])
        await db.cycle_games.create_index([("game_id", 1)])
        print("✅ Indexes created")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Starting cycle games migration...")
    asyncio.run(migrate_cycle_games())