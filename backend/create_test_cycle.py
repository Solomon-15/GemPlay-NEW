#!/usr/bin/env python3
"""
Скрипт для создания тестового завершенного цикла с играми
"""

import asyncio
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid
import random

# Загружаем переменные окружения
load_dotenv()

# Подключение к MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "rps_game")

async def create_test_cycle():
    """Создает тестовый завершенный цикл"""
    try:
        # Подключаемся к MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        
        print(f"Connected to MongoDB: {MONGODB_URL}")
        print(f"Database: {DB_NAME}")
        
        # Находим первого активного обычного бота
        bot = await db.bots.find_one({
            "is_active": True,
            "bot_type": "REGULAR"
        })
        
        if not bot:
            print("❌ Не найдено активных обычных ботов")
            return
        
        bot_id = bot["id"]
        bot_name = bot["name"]
        print(f"✅ Используем бота: {bot_name} (ID: {bot_id})")
        
        # Создаем тестовый цикл
        cycle_id = str(uuid.uuid4())
        start_time = datetime.utcnow() - timedelta(days=7)
        end_time = datetime.utcnow() - timedelta(days=1)
        
        # Статистика цикла
        total_bets = 20
        wins_count = 10
        losses_count = 7
        draws_count = 3
        total_bet_amount = 1000.0
        total_winnings = 1200.0
        total_losses = 700.0
        net_profit = 500.0
        
        # Создаем запись о завершенном цикле
        completed_cycle = {
            "id": cycle_id,
            "bot_id": bot_id,
            "cycle_number": bot.get("completed_cycles_count", 0) + 1,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": int((end_time - start_time).total_seconds()),
            "total_bets": total_bets,
            "wins_count": wins_count,
            "losses_count": losses_count,
            "draws_count": draws_count,
            "total_bet_amount": total_bet_amount,
            "total_winnings": total_winnings,
            "total_losses": total_losses,
            "net_profit": net_profit,
            "created_at": datetime.utcnow()
        }
        
        # Сохраняем цикл
        await db.completed_cycles.insert_one(completed_cycle)
        print(f"✅ Создан цикл: {cycle_id}")
        
        # Создаем тестовые игры
        gem_types = ["Ruby", "Amber", "Topaz", "Emerald", "Aquamarine", "Sapphire", "Magic"]
        opponent_names = ["Player123", "GamerPro", "NoobMaster", "CryptoKing", "LuckyGuy",
                         "ProPlayer", "GameMaster", "Winner777", "BetKing", "RPSMaster"]
        
        games = []
        cycle_games_to_save = []
        
        for i in range(total_bets):
            game_id = str(uuid.uuid4())
            game_time = start_time + timedelta(hours=i*8)
            
            # Определяем результат
            if i < wins_count:
                winner_id = bot_id
                bot_move = "ROCK" if i % 3 == 0 else "PAPER" if i % 3 == 1 else "SCISSORS"
                opponent_move = "SCISSORS" if i % 3 == 0 else "ROCK" if i % 3 == 1 else "PAPER"
            elif i < wins_count + losses_count:
                winner_id = f"user_{uuid.uuid4()}"
                bot_move = "SCISSORS" if i % 3 == 0 else "ROCK" if i % 3 == 1 else "PAPER"
                opponent_move = "ROCK" if i % 3 == 0 else "PAPER" if i % 3 == 1 else "SCISSORS"
            else:
                winner_id = None
                bot_move = opponent_move = ["ROCK", "PAPER", "SCISSORS"][i % 3]
            
            # Генерируем гемы
            bet_gems = {}
            if random.random() > 0.3:  # 70% игр с гемами
                num_gem_types = random.randint(1, 3)
                selected_gems = random.sample(gem_types, num_gem_types)
                for gem in selected_gems:
                    bet_gems[gem] = random.randint(1, 5)
            
            game = {
                "id": game_id,
                "creator_id": bot_id,
                "opponent_id": winner_id if winner_id and winner_id != bot_id else f"user_{uuid.uuid4()}",
                "creator_move": bot_move,
                "opponent_move": opponent_move,
                "winner_id": winner_id,
                "bet_amount": 50.0 + (i * 2),
                "bet_gems": bet_gems,
                "status": "COMPLETED",
                "created_at": game_time,
                "completed_at": game_time + timedelta(minutes=5)
            }
            
            games.append(game)
            
            # Подготавливаем для сохранения в cycle_games
            cycle_game = {
                "cycle_id": cycle_id,
                "bot_id": bot_id,
                "game_id": game_id,
                "game_data": game,
                "created_at": datetime.utcnow()
            }
            cycle_games_to_save.append(cycle_game)
        
        # Сохраняем игры
        if games:
            await db.games.insert_many(games)
            print(f"✅ Создано {len(games)} игр")
        
        # Сохраняем связи игр с циклом
        if cycle_games_to_save:
            await db.cycle_games.insert_many(cycle_games_to_save)
            print(f"✅ Сохранено {len(cycle_games_to_save)} связей игр с циклом")
        
        # Обновляем счетчик циклов у бота
        await db.bots.update_one(
            {"id": bot_id},
            {
                "$inc": {"completed_cycles": 1, "completed_cycles_count": 1},
                "$set": {"has_completed_cycles": True}
            }
        )
        
        print(f"\n✅ Тестовый цикл успешно создан!")
        print(f"   Bot: {bot_name}")
        print(f"   Cycle ID: {cycle_id}")
        print(f"   Games: {total_bets}")
        print(f"   W/L/D: {wins_count}/{losses_count}/{draws_count}")
        print(f"   Profit: ${net_profit}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестового цикла: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Создание тестового цикла...")
    asyncio.run(create_test_cycle())