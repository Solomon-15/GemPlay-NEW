#!/usr/bin/env python3
"""
Скрипт для очистки старых записей BOT_REVENUE из profit_entries
после перехода на систему completed_cycles
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime

async def cleanup_bot_revenue():
    """Удаляет записи BOT_REVENUE из profit_entries после миграции"""
    
    # Load environment
    load_dotenv('/workspace/backend/.env')
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'gemplay_db')]
    
    print('🧹 Начинаем очистку BOT_REVENUE из profit_entries...')
    
    try:
        # Сначала проверяем сколько записей BOT_REVENUE есть
        bot_revenue_count = await db.profit_entries.count_documents({"entry_type": "BOT_REVENUE"})
        print(f'📊 Найдено {bot_revenue_count} записей BOT_REVENUE для удаления')
        
        if bot_revenue_count == 0:
            print('✅ Нет записей BOT_REVENUE для удаления')
            return
        
        # Создаем резервную копию перед удалением
        print('💾 Создаем резервную копию BOT_REVENUE записей...')
        bot_revenue_entries = await db.profit_entries.find({"entry_type": "BOT_REVENUE"}).to_list(1000)
        
        if bot_revenue_entries:
            # Сохраняем в отдельную коллекцию для резервного копирования
            backup_collection = f"profit_entries_bot_revenue_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await db[backup_collection].insert_many(bot_revenue_entries)
            print(f'✅ Резервная копия сохранена в коллекцию: {backup_collection}')
        
        # Показываем статистику перед удалением
        revenue_stats = await db.profit_entries.aggregate([
            {"$match": {"entry_type": "BOT_REVENUE"}},
            {"$group": {
                "_id": None,
                "total_amount": {"$sum": "$amount"},
                "count": {"$sum": 1},
                "avg_amount": {"$avg": "$amount"}
            }}
        ]).to_list(1)
        
        if revenue_stats:
            stats = revenue_stats[0]
            print(f'📊 Статистика удаляемых записей:')
            print(f'   Общая сумма: ${stats["total_amount"]:.2f}')
            print(f'   Количество: {stats["count"]}')
            print(f'   Средняя сумма: ${stats["avg_amount"]:.2f}')
        
        # Удаляем записи BOT_REVENUE
        result = await db.profit_entries.delete_many({"entry_type": "BOT_REVENUE"})
        print(f'🗑️  Удалено {result.deleted_count} записей BOT_REVENUE')
        
        # Проверяем что удаление прошло успешно
        remaining_bot_revenue = await db.profit_entries.count_documents({"entry_type": "BOT_REVENUE"})
        if remaining_bot_revenue == 0:
            print('✅ Все записи BOT_REVENUE успешно удалены')
        else:
            print(f'⚠️  Осталось {remaining_bot_revenue} записей BOT_REVENUE')
        
        # Показываем итоговую статистику profit_entries
        total_profit_entries = await db.profit_entries.count_documents({})
        print(f'📊 Осталось записей в profit_entries: {total_profit_entries}')
        
        # Показываем статистику по типам
        remaining_types = await db.profit_entries.aggregate([
            {"$group": {"_id": "$entry_type", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        print('📊 Оставшиеся типы записей:')
        for type_stat in remaining_types:
            print(f'   {type_stat["_id"]}: {type_stat["count"]}')
        
    except Exception as e:
        print(f'❌ Ошибка очистки: {e}')
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_bot_revenue())