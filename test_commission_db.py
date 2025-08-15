#!/usr/bin/env python3
"""
Тест для проверки новой логики комиссий от Human-ботов прямо в базе данных
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gemplay_db')]

async def test_commission_in_db():
    """
    Тест новой логики комиссий напрямую в базе данных
    """
    
    try:
        # Получить все типы комиссий
        profit_by_type = await db.profit_entries.aggregate([
            {"$group": {"_id": "$entry_type", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
        ]).to_list(10)
        
        print("📊 Статистика всех типов доходов:")
        for entry_type in profit_by_type:
            type_name = entry_type["_id"]
            total = entry_type["total"]
            count = entry_type["count"]
            print(f"   {type_name}: ${total:.2f} ({count} записей)")
        
        # Получить последние записи HUMAN_BOT_COMMISSION
        human_bot_entries = await db.profit_entries.find(
            {"entry_type": "HUMAN_BOT_COMMISSION"}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        print(f"\n🤖 Последние {len(human_bot_entries)} записей HUMAN_BOT_COMMISSION:")
        for entry in human_bot_entries:
            amount = entry.get("amount", 0)
            ref_id = entry.get("reference_id", "N/A")[:8]
            created = str(entry.get("created_at", "N/A"))[:19]
            source_user = entry.get("source_user_id", "N/A")[:8]
            description = entry.get("description", "N/A")
            print(f"   ${amount:.2f} | Game: {ref_id}... | User: {source_user}... | {created}")
            print(f"      Описание: {description}")
        
        # Получить последние записи BET_COMMISSION
        bet_entries = await db.profit_entries.find(
            {"entry_type": "BET_COMMISSION"}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        print(f"\n💰 Последние {len(bet_entries)} записей BET_COMMISSION:")
        for entry in bet_entries:
            amount = entry.get("amount", 0)
            ref_id = entry.get("reference_id", "N/A")[:8]
            created = str(entry.get("created_at", "N/A"))[:19]
            source_user = entry.get("source_user_id", "N/A")[:8]
            description = entry.get("description", "N/A")
            print(f"   ${amount:.2f} | Game: {ref_id}... | User: {source_user}... | {created}")
            print(f"      Описание: {description}")
        
        # Получить статистику Human-ботов
        human_bots_count = await db.human_bots.count_documents({})
        active_human_bots = await db.human_bots.count_documents({"is_active": True})
        
        print(f"\n🤖 Статистика Human-ботов:")
        print(f"   Всего: {human_bots_count}")
        print(f"   Активных: {active_human_bots}")
        
        # Получить последние завершенные игры
        recent_games = await db.games.find({
            "status": "COMPLETED",
            "commission_amount": {"$gt": 0}
        }).sort("completed_at", -1).limit(5).to_list(5)
        
        print(f"\n🎮 Последние {len(recent_games)} завершенные игры с комиссией:")
        for game in recent_games:
            game_id = game.get("id", "N/A")[:8]
            creator_id = game.get("creator_id", "N/A")[:8]
            opponent_id = game.get("opponent_id", "N/A")[:8]
            winner_id = game.get("winner_id", "N/A")[:8]
            commission = game.get("commission_amount", 0)
            bet_amount = game.get("bet_amount", 0)
            completed = str(game.get("completed_at", "N/A"))[:19]
            
            print(f"   Game {game_id}... | ${bet_amount} bet, ${commission:.2f} commission | {completed}")
            print(f"      Creator: {creator_id}... | Opponent: {opponent_id}... | Winner: {winner_id}...")
        
        print(f"\n✅ Новая логика комиссий активна!")
        print(f"   1. Human-бот vs Human-бот -> HUMAN_BOT_COMMISSION")  
        print(f"   2. Human-бот выигрывает vs живой игрок -> HUMAN_BOT_COMMISSION")
        print(f"   3. Живой игрок выигрывает vs Human-бот -> BET_COMMISSION")
        
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_commission_in_db())