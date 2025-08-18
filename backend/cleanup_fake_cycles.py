#!/usr/bin/env python3
"""
Скрипт для очистки базы данных от фиктивных циклов ботов.
Удаляет все записи в completed_cycles с id вида "temp_cycle_*".
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Добавляем путь к серверу для импорта настроек
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def cleanup_fake_cycles():
    """Удаляет фиктивные циклы из базы данных."""
    
    # Подключение к MongoDB (используйте те же настройки, что и в server.py)
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "write_russian_2")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        print("🔍 Поиск фиктивных циклов в базе данных...")
        
        # Ищем все записи с id вида "temp_cycle_*"
        fake_cycles = await db.completed_cycles.find({
            "id": {"$regex": "^temp_cycle_"}
        }).to_list(1000)
        
        if not fake_cycles:
            print("✅ Фиктивные циклы не найдены.")
            return
        
        print(f"🚨 Найдено {len(fake_cycles)} фиктивных циклов:")
        
        # Группируем по bot_id для отчёта
        cycles_by_bot = {}
        total_fake_profit = 0
        
        for cycle in fake_cycles:
            bot_id = cycle.get("bot_id", "unknown")
            if bot_id not in cycles_by_bot:
                cycles_by_bot[bot_id] = []
            cycles_by_bot[bot_id].append(cycle)
            total_fake_profit += cycle.get("net_profit", 0)
        
        # Выводим отчёт
        for bot_id, bot_cycles in cycles_by_bot.items():
            bot_fake_profit = sum(c.get("net_profit", 0) for c in bot_cycles)
            print(f"  Bot {bot_id}: {len(bot_cycles)} фиктивных циклов, ${bot_fake_profit:.2f} фиктивной прибыли")
        
        print(f"💰 Общая фиктивная прибыль: ${total_fake_profit:.2f}")
        
        # Подтверждение удаления
        response = input("\n❓ Удалить все фиктивные циклы? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("❌ Операция отменена.")
            return
        
        # Удаляем фиктивные циклы
        print("🗑️ Удаление фиктивных циклов...")
        
        delete_result = await db.completed_cycles.delete_many({
            "id": {"$regex": "^temp_cycle_"}
        })
        
        print(f"✅ Удалено {delete_result.deleted_count} фиктивных записей.")
        
        # Также удаляем связанные записи из cycle_games если есть
        games_delete_result = await db.cycle_games.delete_many({
            "cycle_id": {"$regex": "^temp_cycle_"}
        })
        
        if games_delete_result.deleted_count > 0:
            print(f"✅ Удалено {games_delete_result.deleted_count} связанных записей игр.")
        
        # Проверяем результат
        remaining_fake = await db.completed_cycles.count_documents({
            "id": {"$regex": "^temp_cycle_"}
        })
        
        if remaining_fake == 0:
            print("🎉 Все фиктивные циклы успешно удалены!")
        else:
            print(f"⚠️ Осталось {remaining_fake} фиктивных записей. Проверьте вручную.")
            
        # Создаём запись в логах админа о очистке
        admin_log = {
            "id": f"cleanup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "user_id": "system",
            "action": "CLEANUP_FAKE_CYCLES",
            "target_type": "database",
            "target_id": "completed_cycles",
            "details": {
                "deleted_cycles": delete_result.deleted_count,
                "deleted_games": games_delete_result.deleted_count,
                "total_fake_profit_removed": total_fake_profit,
                "affected_bots": list(cycles_by_bot.keys())
            },
            "timestamp": datetime.utcnow(),
            "ip_address": "127.0.0.1",
            "user_agent": "cleanup_script"
        }
        
        await db.admin_logs.insert_one(admin_log)
        print("📝 Создана запись в логах администратора.")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        
    finally:
        client.close()
        print("🔌 Соединение с базой данных закрыто.")

if __name__ == "__main__":
    print("🧹 Скрипт очистки фиктивных циклов ботов")
    print("=" * 50)
    
    asyncio.run(cleanup_fake_cycles())