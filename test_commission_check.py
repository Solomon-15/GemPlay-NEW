#!/usr/bin/env python3
"""
Проверяем, кто участвовал в последних играх - Human-боты или живые игроки
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

async def check_game_participants():
    """
    Проверяем участников последних игр и какие типы комиссий должны были быть созданы
    """
    
    try:
        # Получить последние завершенные игры с комиссией
        recent_games = await db.games.find({
            "status": "COMPLETED",
            "commission_amount": {"$gt": 0}
        }).sort("completed_at", -1).limit(10).to_list(10)
        
        print(f"🎮 Анализ последних {len(recent_games)} игр с комиссией:")
        
        for i, game in enumerate(recent_games):
            game_id = game.get("id", "N/A")[:8]
            creator_id = game.get("creator_id", "N/A")
            opponent_id = game.get("opponent_id", "N/A")
            winner_id = game.get("winner_id", "N/A")
            commission = game.get("commission_amount", 0)
            bet_amount = game.get("bet_amount", 0)
            completed = str(game.get("completed_at", "N/A"))[:19]
            
            # Проверяем, являются ли участники Human-ботами
            creator_is_human_bot = await db.human_bots.find_one({"id": creator_id}) is not None
            opponent_is_human_bot = await db.human_bots.find_one({"id": opponent_id}) is not None if opponent_id else False
            winner_is_human_bot = await db.human_bots.find_one({"id": winner_id}) is not None if winner_id else False
            
            # Определяем ожидаемый тип комиссии по новой логике
            if creator_is_human_bot and opponent_is_human_bot:
                expected_commission_type = "HUMAN_BOT_COMMISSION (Human vs Human)"
            elif winner_is_human_bot:
                expected_commission_type = "HUMAN_BOT_COMMISSION (Human-bot wins)"
            else:
                expected_commission_type = "BET_COMMISSION (Live player wins)"
            
            # Проверяем, какая комиссия была фактически создана
            actual_commission = await db.profit_entries.find_one({
                "reference_id": game_id,
                "amount": commission
            })
            
            actual_type = actual_commission.get("entry_type", "NOT_FOUND") if actual_commission else "NOT_FOUND"
            
            print(f"\n   {i+1}. Game {game_id}... | ${bet_amount} bet, ${commission:.2f} commission | {completed}")
            print(f"      Creator: {'Human-bot' if creator_is_human_bot else 'Live player'} ({creator_id[:8]}...)")
            print(f"      Opponent: {'Human-bot' if opponent_is_human_bot else 'Live player'} ({opponent_id[:8] if opponent_id else 'N/A'}...)")
            print(f"      Winner: {'Human-bot' if winner_is_human_bot else 'Live player'} ({winner_id[:8] if winner_id else 'N/A'}...)")
            print(f"      Ожидаемый тип: {expected_commission_type}")
            print(f"      Фактический тип: {actual_type}")
            
            # Проверка корректности
            if expected_commission_type.startswith("HUMAN_BOT_COMMISSION") and actual_type == "HUMAN_BOT_COMMISSION":
                print(f"      ✅ Логика работает правильно!")
            elif expected_commission_type.startswith("BET_COMMISSION") and actual_type == "BET_COMMISSION":
                print(f"      ✅ Логика работает правильно!")
            else:
                if "Human vs Human" in expected_commission_type or "Human-bot wins" in expected_commission_type:
                    if actual_type == "BET_COMMISSION":
                        print(f"      ⚠️  Возможно, игра была до обновления логики")
                    else:
                        print(f"      ❌ Неправильный тип комиссии!")
                else:
                    print(f"      ⚠️  Проверить логику")
        
        # Статистика по типам комиссий после обновления
        print(f"\nℹ️  Примечание: Новая логика применяется только к играм, завершенным после обновления кода.")
        print(f"   Игры, завершенные до обновления, могут иметь старые типы комиссий.")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе игр: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_game_participants())