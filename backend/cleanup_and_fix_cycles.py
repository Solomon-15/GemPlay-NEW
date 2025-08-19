#!/usr/bin/env python3
"""
Комплексный скрипт очистки и исправления циклов ботов.
1. Удаляет фиктивные циклы
2. Синхронизирует счетчики
3. Создает уникальный индекс
4. Проверяет целостность данных
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def cleanup_and_fix_cycles():
    """Комплексная очистка и исправление данных циклов."""
    
    # Подключение к MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "write_russian_2")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        print("🧹 Комплексная очистка и исправление циклов ботов")
        print("=" * 60)
        
        # ШАГ 1: Статистика до очистки
        print("\n📊 СТАТИСТИКА ДО ОЧИСТКИ:")
        total_cycles = await db.completed_cycles.count_documents({})
        fake_cycles = await db.completed_cycles.count_documents({
            "id": {"$regex": "^temp_cycle_"}
        })
        print(f"   Всего циклов: {total_cycles}")
        print(f"   Фиктивных циклов: {fake_cycles}")
        print(f"   Реальных циклов: {total_cycles - fake_cycles}")
        
        if fake_cycles == 0:
            print("✅ Фиктивные циклы не найдены!")
        else:
            # Показываем детали фиктивных циклов по ботам
            fake_cycles_by_bot = await db.completed_cycles.aggregate([
                {"$match": {"id": {"$regex": "^temp_cycle_"}}},
                {"$group": {
                    "_id": "$bot_id",
                    "count": {"$sum": 1},
                    "total_fake_profit": {"$sum": "$net_profit"}
                }}
            ]).to_list(1000)
            
            print(f"\n🚨 ФИКТИВНЫЕ ЦИКЛЫ ПО БОТАМ:")
            total_fake_profit = 0
            for bot_data in fake_cycles_by_bot:
                bot_id = bot_data["_id"]
                count = bot_data["count"]
                fake_profit = bot_data["total_fake_profit"]
                total_fake_profit += fake_profit
                print(f"   Bot {bot_id}: {count} циклов, ${fake_profit:.2f} фиктивной прибыли")
            
            print(f"   ИТОГО фиктивной прибыли: ${total_fake_profit:.2f}")
            
            # Подтверждение удаления
            response = input(f"\n❓ Удалить {fake_cycles} фиктивных циклов? (yes/no): ")
            if response.lower() not in ['yes', 'y', 'да', 'д']:
                print("❌ Операция отменена.")
                return
        
        # ШАГ 2: Создание уникального индекса
        print("\n🔧 СОЗДАНИЕ УНИКАЛЬНОГО ИНДЕКСА:")
        try:
            existing_indexes = await db.completed_cycles.list_indexes().to_list(100)
            unique_index_exists = any(
                idx.get('name') == 'unique_bot_cycle' 
                for idx in existing_indexes
            )
            
            if unique_index_exists:
                print("✅ Уникальный индекс 'unique_bot_cycle' уже существует")
            else:
                result = await db.completed_cycles.create_index(
                    [("bot_id", 1), ("cycle_number", 1)],
                    unique=True,
                    name="unique_bot_cycle",
                    background=True
                )
                print(f"✅ Создан уникальный индекс: {result}")
        except Exception as idx_error:
            print(f"⚠️ Ошибка создания индекса: {idx_error}")
        
        # ШАГ 3: Удаление фиктивных циклов
        if fake_cycles > 0:
            print(f"\n🗑️ УДАЛЕНИЕ {fake_cycles} ФИКТИВНЫХ ЦИКЛОВ:")
            
            # Удаляем фиктивные циклы
            delete_result = await db.completed_cycles.delete_many({
                "id": {"$regex": "^temp_cycle_"}
            })
            print(f"✅ Удалено циклов: {delete_result.deleted_count}")
            
            # Удаляем связанные игры
            games_delete_result = await db.cycle_games.delete_many({
                "cycle_id": {"$regex": "^temp_cycle_"}
            })
            print(f"✅ Удалено связанных игр: {games_delete_result.deleted_count}")
        
        # ШАГ 4: Синхронизация счетчиков ботов
        print(f"\n🔄 СИНХРОНИЗАЦИЯ СЧЕТЧИКОВ БОТОВ:")
        
        # Получаем всех обычных ботов
        bots = await db.bots.find({"bot_type": "REGULAR"}).to_list(1000)
        updated_bots = 0
        
        for bot in bots:
            bot_id = bot.get("id")
            if not bot_id:
                continue
                
            # Подсчитываем реальные циклы
            real_cycles_count = await db.completed_cycles.count_documents({
                "bot_id": bot_id,
                "id": {"$not": {"$regex": "^temp_cycle_"}}
            })
            
            # Текущий счетчик в документе бота
            current_count = bot.get("completed_cycles_count", 0)
            
            if current_count != real_cycles_count:
                # Обновляем счетчик
                await db.bots.update_one(
                    {"id": bot_id},
                    {"$set": {"completed_cycles_count": real_cycles_count}}
                )
                print(f"   Bot {bot_id}: {current_count} → {real_cycles_count}")
                updated_bots += 1
        
        print(f"✅ Обновлено счетчиков: {updated_bots}")
        
        # ШАГ 5: Финальная проверка
        print(f"\n📊 СТАТИСТИКА ПОСЛЕ ОЧИСТКИ:")
        final_total = await db.completed_cycles.count_documents({})
        final_fake = await db.completed_cycles.count_documents({
            "id": {"$regex": "^temp_cycle_"}
        })
        print(f"   Всего циклов: {final_total}")
        print(f"   Фиктивных циклов: {final_fake}")
        print(f"   Реальных циклов: {final_total - final_fake}")
        
        # ШАГ 6: Создание записи в логах админа
        admin_log = {
            "id": f"cleanup_cycles_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "user_id": "system",
            "action": "CLEANUP_CYCLES_COMPREHENSIVE",
            "target_type": "database",
            "target_id": "completed_cycles",
            "details": {
                "deleted_fake_cycles": fake_cycles,
                "updated_bot_counters": updated_bots,
                "final_real_cycles": final_total - final_fake,
                "unique_index_created": not unique_index_exists if fake_cycles > 0 else None
            },
            "timestamp": datetime.utcnow(),
            "ip_address": "127.0.0.1",
            "user_agent": "cleanup_script_comprehensive"
        }
        
        await db.admin_logs.insert_one(admin_log)
        print("📝 Создана запись в логах администратора.")
        
        print(f"\n🎉 ОЧИСТКА ЗАВЕРШЕНА УСПЕШНО!")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        
    finally:
        client.close()
        print("🔌 Соединение с базой данных закрыто.")

def main():
    """Главная функция скрипта."""
    print("🧹 Комплексный скрипт очистки и исправления циклов ботов")
    print("=" * 60)
    
    asyncio.run(cleanup_and_fix_cycles())

if __name__ == "__main__":
    main()