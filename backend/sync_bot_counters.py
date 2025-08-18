#!/usr/bin/env python3
"""
Скрипт для синхронизации счётчиков завершённых циклов с реальными данными.
Обновляет bot.completed_cycles_count на основе реальных записей в completed_cycles.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Добавляем путь к серверу для импорта настроек
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def sync_bot_counters():
    """Синхронизирует счётчики завершённых циклов."""
    
    # Подключение к MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "write_russian_2")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        print("🔄 Синхронизация счётчиков завершённых циклов...")
        print("=" * 60)
        
        # Получаем всех обычных ботов
        bots = await db.bots.find({"bot_type": "REGULAR"}).to_list(1000)
        
        updates_made = 0
        total_bots = len(bots)
        
        for i, bot in enumerate(bots, 1):
            bot_id = bot.get("id")
            bot_name = bot.get("name", f"Bot_{bot_id[:8]}")
            
            print(f"[{i}/{total_bots}] Синхронизирую бота: {bot_name}")
            
            # Подсчитываем реальные циклы в completed_cycles (исключаем фиктивные)
            real_cycles_count = await db.completed_cycles.count_documents({
                "bot_id": bot_id,
                "id": {"$not": {"$regex": "^temp_cycle_"}}
            })
            
            # Текущий счётчик в документе бота
            current_count = bot.get("completed_cycles_count", 0)
            old_count = bot.get("completed_cycles", 0)  # Старое поле
            
            # Определяем, нужно ли обновление
            needs_update = current_count != real_cycles_count
            
            if needs_update:
                print(f"  📊 Обновляю: {current_count} → {real_cycles_count}")
                
                # Обновляем счётчик
                update_data = {
                    "completed_cycles_count": real_cycles_count,
                    "updated_at": datetime.utcnow()
                }
                
                # Также синхронизируем старое поле если оно существует
                if old_count != real_cycles_count:
                    update_data["completed_cycles"] = real_cycles_count
                
                await db.bots.update_one(
                    {"id": bot_id},
                    {"$set": update_data}
                )
                
                updates_made += 1
                print(f"  ✅ Обновлено")
            else:
                print(f"  ✅ Уже корректно ({real_cycles_count})")
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТ СИНХРОНИЗАЦИИ")
        print("=" * 60)
        
        if updates_made == 0:
            print("🎉 Все счётчики уже корректны!")
        else:
            print(f"✅ Обновлено счётчиков: {updates_made} из {total_bots}")
        
        # Проверяем результат
        print("\n🔍 Финальная проверка...")
        
        mismatches = 0
        async for bot in db.bots.find({"bot_type": "REGULAR"}):
            bot_id = bot.get("id")
            current_count = bot.get("completed_cycles_count", 0)
            
            real_count = await db.completed_cycles.count_documents({
                "bot_id": bot_id,
                "id": {"$not": {"$regex": "^temp_cycle_"}}
            })
            
            if current_count != real_count:
                mismatches += 1
                print(f"❌ {bot.get('name', bot_id)}: {current_count} ≠ {real_count}")
        
        if mismatches == 0:
            print("✅ Все счётчики синхронизированы!")
        else:
            print(f"⚠️ Осталось {mismatches} несоответствий")
        
        # Создаём запись в логах
        admin_log = {
            "id": f"sync_counters_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "user_id": "system",
            "action": "SYNC_BOT_COUNTERS",
            "target_type": "database",
            "target_id": "bots",
            "details": {
                "total_bots_processed": total_bots,
                "counters_updated": updates_made,
                "remaining_mismatches": mismatches
            },
            "timestamp": datetime.utcnow(),
            "ip_address": "127.0.0.1",
            "user_agent": "sync_script"
        }
        
        await db.admin_logs.insert_one(admin_log)
        print("📝 Создана запись в логах администратора.")
        
        return updates_made
        
    except Exception as e:
        print(f"❌ Ошибка при синхронизации: {e}")
        return 0
        
    finally:
        client.close()
        print("🔌 Соединение с базой данных закрыто.")

if __name__ == "__main__":
    print("🔄 Скрипт синхронизации счётчиков циклов ботов")
    print("=" * 50)
    
    asyncio.run(sync_bot_counters())