#!/usr/bin/env python3
"""
Скрипт для очистки избыточных ставок ботов
"""

import asyncio
from pymongo import MongoClient
import os

async def cleanup_excess_bot_bets():
    """Очистка избыточных ставок ботов"""
    
    # Подключение к MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db_name = os.environ.get('DB_NAME', 'gemplay_db')
    db = client[db_name]
    
    print(f"=== ОЧИСТКА ИЗБЫТОЧНЫХ СТАВОК БОТОВ в {db_name} ===")
    
    # Получаем настройки глобальных лимитов
    bot_settings = db.bot_settings.find_one({"id": "bot_settings"})
    if bot_settings:
        max_regular = bot_settings.get("max_active_bets_regular", 50)
        max_human = bot_settings.get("max_active_bets_human", 30)
        print(f"📊 Текущие глобальные лимиты:")
        print(f"   - Regular боты: {max_regular}")
        print(f"   - Human боты: {max_human}")
    else:
        print("❌ Настройки не найдены")
        return
    
    # Получаем всех ботов
    bots = list(db.bots.find({"is_active": True}))
    print(f"👥 Найдено активных ботов: {len(bots)}")
    
    if not bots:
        print("❌ Боты не найдены, проверим все боты...")
        all_bots = list(db.bots.find({}))
        print(f"👥 Всего ботов в базе: {len(all_bots)}")
        for bot in all_bots:
            print(f"  - {bot.get('name', bot['id'])} (active: {bot.get('is_active', False)})")
        return
    
    total_deleted = 0
    
    for bot in bots:
        bot_id = bot["id"]
        bot_name = bot.get("name", f"Bot #{bot_id[:3]}")
        bot_type = bot.get("bot_type", "REGULAR")
        
        # Получаем все активные ставки бота
        active_bets = list(db.games.find({
            "creator_id": bot_id,
            "status": "WAITING"
        }).sort("created_at", -1))  # Сортируем по дате создания (новые первыми)
        
        current_count = len(active_bets)
        individual_limit = bot.get("current_limit") or bot.get("cycle_games", 12)
        
        print(f"\n🤖 {bot_name} ({bot_type}): {current_count} активных ставок, лимит: {individual_limit}")
        
        if current_count > individual_limit:
            # Удаляем избыточные ставки (оставляем только новые)
            bets_to_delete = active_bets[individual_limit:]
            
            for bet in bets_to_delete:
                # Удаляем ставку
                db.games.delete_one({"id": bet["id"]})
                total_deleted += 1
                print(f"   ❌ Удалена ставка {bet['id']} ({bet['bet_amount']}$)")
            
            print(f"   ✅ Удалено {len(bets_to_delete)} избыточных ставок")
        else:
            print(f"   ✅ Лимит соблюден")
    
    # Проверяем глобальные лимиты после очистки
    print(f"\n=== ПРОВЕРКА ГЛОБАЛЬНЫХ ЛИМИТОВ ПОСЛЕ ОЧИСТКИ ===")
    
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
    
    print(f"🤖 Regular боты: {regular_bets}/{max_regular}")
    print(f"👤 Human боты: {human_bets}/{max_human}")
    
    if regular_bets > max_regular:
        print(f"❌ Глобальный лимит Regular ботов все еще превышен!")
        # Удаляем дополнительные ставки
        excess_regular = regular_bets - max_regular
        excess_games = list(db.games.find({
            "creator_type": "bot",
            "is_bot_game": True,
            "status": "WAITING",
            "$or": [
                {"bot_type": "REGULAR"},
                {"metadata.bot_type": "REGULAR"}
            ]
        }).sort("created_at", 1).limit(excess_regular))
        
        for game in excess_games:
            db.games.delete_one({"id": game["id"]})
            total_deleted += 1
            print(f"   ❌ Удалена глобальная избыточная ставка {game['id']}")
    
    if human_bets > max_human:
        print(f"❌ Глобальный лимит Human ботов все еще превышен!")
        # Удаляем дополнительные ставки
        excess_human = human_bets - max_human
        excess_games = list(db.games.find({
            "creator_type": "bot",
            "is_bot_game": True,
            "status": "WAITING",
            "$or": [
                {"bot_type": "HUMAN"},
                {"metadata.bot_type": "HUMAN"}
            ]
        }).sort("created_at", 1).limit(excess_human))
        
        for game in excess_games:
            db.games.delete_one({"id": game["id"]})
            total_deleted += 1
            print(f"   ❌ Удалена глобальная избыточная ставка {game['id']}")
    
    print(f"\n✅ Всего удалено ставок: {total_deleted}")
    print("✅ Очистка завершена")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_excess_bot_bets())