#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логики циклов без подключения к БД.
Имитирует различные сценарии и проверяет корректность обработки.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockDB:
    """Мок базы данных для тестирования."""
    
    def __init__(self):
        self.completed_cycles = []
        self.bots = []
        self.games = []
        self.bot_profit_accumulators = []
        self.cycle_games = []
        
    async def find_one(self, collection, query, projection=None):
        """Имитация поиска одного документа."""
        
        if collection == "completed_cycles":
            # Проверяем существование цикла
            for cycle in self.completed_cycles:
                if (query.get("bot_id") == cycle.get("bot_id") and 
                    query.get("cycle_number") == cycle.get("cycle_number")):
                    return cycle if not projection else {"_id": "mock_id"}
            return None
            
        elif collection == "bots":
            for bot in self.bots:
                if query.get("id") == bot.get("id"):
                    return bot
            return None
            
        return None
    
    async def insert_one(self, collection, document):
        """Имитация вставки документа."""
        
        if collection == "completed_cycles":
            # Проверяем дублирование
            for cycle in self.completed_cycles:
                if (document.get("bot_id") == cycle.get("bot_id") and 
                    document.get("cycle_number") == cycle.get("cycle_number")):
                    # Имитируем ошибку дублирования
                    raise Exception("E11000 duplicate key error")
            
            # Добавляем документ
            self.completed_cycles.append(document)
            return MagicMock(inserted_id="mock_inserted_id")
            
        return MagicMock(inserted_id="mock_inserted_id")
    
    async def update_one(self, collection, query, update):
        """Имитация обновления документа."""
        return MagicMock(modified_count=1)

# Глобальная переменная для мока БД
db = None

async def save_completed_cycle(bot_doc: dict, completion_time: datetime):
    """Имитация функции save_completed_cycle с логикой из основного кода."""
    try:
        bot_id = bot_doc.get("id")
        if not bot_id:
            logger.error("Bot ID is missing")
            return
        
        # Имитируем наличие завершенных игр
        completed_games = [
            {"bet_amount": 50.0, "winner_id": bot_id, "created_at": completion_time - timedelta(hours=1)},
            {"bet_amount": 50.0, "winner_id": None, "created_at": completion_time - timedelta(minutes=30)},
            {"bet_amount": 50.0, "winner_id": "opponent", "created_at": completion_time - timedelta(minutes=15)}
        ]
        
        if not completed_games:
            logger.warning(f"No completed games found for bot {bot_id} cycle")
            return
        
        # Рассчитываем статистику
        wins_count = sum(1 for game in completed_games if game.get("winner_id") == bot_id)
        losses_count = sum(1 for game in completed_games if game.get("winner_id") not in [bot_id, None])
        draws_count = sum(1 for game in completed_games if game.get("winner_id") is None)
        total_bet_amount = sum(float(game.get("bet_amount", 0)) for game in completed_games)
        total_winnings = wins_count * 50.0  # Упрощенная логика
        total_losses = losses_count * 50.0
        net_profit = total_winnings - total_losses
        
        # Получаем номер цикла
        cycle_number = bot_doc.get("completed_cycles_count", 0) + 1
        
        logger.info(f"🔍 Checking cycle #{cycle_number} for bot {bot_id}")
        
        # Проверяем существование цикла
        existing_cycle = await db.find_one("completed_cycles", {
            "bot_id": bot_id,
            "cycle_number": cycle_number
        }, {"_id": 1})
        
        if existing_cycle:
            logger.warning(f"✅ Cycle #{cycle_number} for bot {bot_id} already exists in completed_cycles, skipping duplicate save (idempotent)")
            return
        
        # Создаем запись о цикле
        completed_cycle = {
            "id": f"cycle_{bot_id}_{cycle_number}",
            "bot_id": bot_id,
            "cycle_number": cycle_number,
            "start_time": completion_time - timedelta(hours=2),
            "end_time": completion_time,
            "duration_seconds": 7200,
            "total_bets": len(completed_games),
            "wins_count": wins_count,
            "losses_count": losses_count,
            "draws_count": draws_count,
            "total_bet_amount": total_bet_amount,
            "total_winnings": total_winnings,
            "total_losses": total_losses,
            "net_profit": net_profit,
            "bot_name": bot_doc.get("name", f"Bot_{bot_id[:8]}"),
            "created_at": datetime.utcnow()
        }
        
        logger.info(f"💾 Attempting to save cycle #{cycle_number} for bot {bot_id}: profit=${net_profit:.2f}")
        
        # Пытаемся сохранить
        try:
            result = await db.insert_one("completed_cycles", completed_cycle)
            logger.info(f"✅ Inserted new cycle #{cycle_number} for bot {bot_id} with ID: {result.inserted_id}")
        except Exception as insert_error:
            error_str = str(insert_error).lower()
            if "duplicate key" in error_str or "e11000" in error_str or "unique" in error_str:
                logger.warning(f"✅ Cycle #{cycle_number} for bot {bot_id} already exists in database (race condition), operation is idempotent")
                return
            else:
                logger.error(f"❌ Failed to insert cycle #{cycle_number} for bot {bot_id}: {insert_error}")
                raise insert_error
        
        # Обновляем счетчик
        await db.update_one("bots", {"id": bot_id}, {"$inc": {"completed_cycles_count": 1}})
        
        logger.info(f"✅ Saved completed cycle #{cycle_number} for bot {bot_doc.get('name', 'Unknown')}: profit=${net_profit:.2f}")
        
    except Exception as e:
        logger.error(f"Error saving completed cycle for bot {bot_doc.get('id', 'unknown')}: {e}")

async def test_cycle_scenarios():
    """Тестирует различные сценарии сохранения циклов."""
    global db
    
    print("🧪 Тестирование логики циклов")
    print("=" * 50)
    
    # Инициализируем мок БД
    db = MockDB()
    
    # Тестовый бот
    test_bot = {
        "id": "test_bot_123",
        "name": "TestBot",
        "completed_cycles_count": 0
    }
    db.bots.append(test_bot)
    
    completion_time = datetime.utcnow()
    
    # СЦЕНАРИЙ 1: Первое сохранение цикла
    print("\n📝 СЦЕНАРИЙ 1: Первое сохранение цикла")
    await save_completed_cycle(test_bot, completion_time)
    print(f"   Циклов в БД: {len(db.completed_cycles)}")
    
    # СЦЕНАРИЙ 2: Попытка дублирования (должна быть отклонена)
    print("\n📝 СЦЕНАРИЙ 2: Попытка дублирования")
    await save_completed_cycle(test_bot, completion_time)
    print(f"   Циклов в БД: {len(db.completed_cycles)} (должно остаться 1)")
    
    # СЦЕНАРИЙ 3: Следующий цикл
    print("\n📝 СЦЕНАРИЙ 3: Следующий цикл")
    test_bot["completed_cycles_count"] = 1
    await save_completed_cycle(test_bot, completion_time + timedelta(hours=3))
    print(f"   Циклов в БД: {len(db.completed_cycles)} (должно стать 2)")
    
    # СЦЕНАРИЙ 4: Параллельные вызовы (имитация race condition)
    print("\n📝 СЦЕНАРИЙ 4: Параллельные вызовы")
    test_bot["completed_cycles_count"] = 2
    
    tasks = []
    for i in range(5):
        task = save_completed_cycle(test_bot, completion_time + timedelta(hours=6))
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)
    print(f"   Циклов в БД: {len(db.completed_cycles)} (должно стать 3, не 7)")
    
    # ИТОГОВАЯ СТАТИСТИКА
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    for i, cycle in enumerate(db.completed_cycles, 1):
        print(f"   Цикл {i}: {cycle['id']}, прибыль: ${cycle['net_profit']:.2f}")
    
    print(f"\n✅ Тестирование завершено. Всего циклов: {len(db.completed_cycles)}")

if __name__ == "__main__":
    asyncio.run(test_cycle_scenarios())