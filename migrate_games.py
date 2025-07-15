#!/usr/bin/env python3
"""
Скрипт для миграции существующих игр и установки правильного creator_type
"""
import asyncio
import sys
sys.path.append('/app/backend')

from server import db

async def migrate_games():
    """Миграция существующих игр"""
    print("🔄 Начинаем миграцию существующих игр...")
    
    # Найдем все игры без creator_type
    games_without_type = await db.games.find({"creator_type": {"$exists": False}}).to_list(1000)
    print(f"Найдено {len(games_without_type)} игр без creator_type")
    
    updated_count = 0
    
    for game in games_without_type:
        creator_type = "user"  # По умолчанию
        bot_type = None
        is_regular_bot_game = False
        
        # Проверим, является ли создатель ботом
        bot = await db.bots.find_one({"id": game["creator_id"]})
        if bot:
            creator_type = "bot"
            bot_type = bot.get("bot_type", "HUMAN")
            is_regular_bot_game = bot.get("bot_type") == "REGULAR"
        
        # Обновим игру
        await db.games.update_one(
            {"id": game["id"]},
            {
                "$set": {
                    "creator_type": creator_type,
                    "bot_type": bot_type,
                    "is_regular_bot_game": is_regular_bot_game
                }
            }
        )
        updated_count += 1
        
        if updated_count % 100 == 0:
            print(f"Обновлено {updated_count} игр...")
    
    print(f"✅ Миграция завершена! Обновлено {updated_count} игр")
    
    # Проверим результат
    game_stats = await db.games.aggregate([
        {"$group": {
            "_id": "$creator_type",
            "count": {"$sum": 1}
        }}
    ]).to_list(10)
    
    print("📊 Статистика после миграции:")
    for stat in game_stats:
        print(f"   {stat['_id']}: {stat['count']} игр")

if __name__ == "__main__":
    asyncio.run(migrate_games())