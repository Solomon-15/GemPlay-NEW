#!/usr/bin/env python3
"""
Скрипт миграции для обновления существующих записей completed_cycles
с новыми полями для отчетности
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime

async def migrate_completed_cycles():
    """Мигрирует существующие записи completed_cycles с добавлением новых полей"""
    
    # Load environment
    load_dotenv('/workspace/backend/.env')
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'gemplay_db')]
    
    print('🚀 Начинаем миграцию completed_cycles...')
    
    try:
        # Получаем все записи completed_cycles без новых полей
        cycles_to_migrate = await db.completed_cycles.find({
            "migration_source": {"$exists": False}  # Только старые записи
        }).to_list(1000)
        
        print(f'📊 Найдено {len(cycles_to_migrate)} записей для миграции')
        
        if not cycles_to_migrate:
            print('✅ Нет записей для миграции')
            return
        
        migrated_count = 0
        
        for cycle in cycles_to_migrate:
            try:
                # Получаем данные бота для дополнительной информации
                bot = await db.bots.find_one({"id": cycle["bot_id"]})
                if not bot:
                    print(f'⚠️  Бот {cycle["bot_id"]} не найден, пропускаем цикл {cycle.get("cycle_number", "?")}')
                    continue
                
                # Рассчитываем новые поля на основе существующих данных
                total_games = cycle.get("total_bets", 0)
                wins_count = cycle.get("wins_count", 0)
                net_profit = cycle.get("net_profit", 0)
                total_bet_amount = cycle.get("total_bet_amount", 0)
                duration_seconds = cycle.get("duration_seconds", 0)
                
                # Рассчитываем метрики
                win_rate_percent = (wins_count / total_games * 100) if total_games > 0 else 0
                average_bet_amount = total_bet_amount / total_games if total_games > 0 else 0
                profit_per_game = net_profit / total_games if total_games > 0 else 0
                games_per_hour = (total_games / (duration_seconds / 3600)) if duration_seconds > 0 else 0
                roi_percent = (net_profit / total_bet_amount * 100) if total_bet_amount > 0 else 0
                
                # Определяем категории
                is_profitable = net_profit > 0
                if net_profit > total_bet_amount * 0.5:  # ROI > 50%
                    profit_category = "HIGH_PROFIT"
                elif net_profit > 0:
                    profit_category = "LOW_PROFIT"
                elif abs(net_profit) <= total_bet_amount * 0.05:  # Потери < 5%
                    profit_category = "BREAK_EVEN"
                else:
                    profit_category = "LOSS"
                
                # Категория размера ставок
                if average_bet_amount < 10:
                    bet_size_category = "SMALL"
                elif average_bet_amount <= 50:
                    bet_size_category = "MEDIUM"
                else:
                    bet_size_category = "LARGE"
                
                # Обновляем запись
                update_data = {
                    # Новые поля для отчетности
                    "bot_name": bot.get("name", bot.get("username", f"Bot_{cycle['bot_id'][:8]}")),
                    "cycle_target_games": bot.get("cycle_games", 12),
                    "average_bet_amount": round(average_bet_amount, 2),
                    "win_rate_percent": round(win_rate_percent, 2),
                    "profit_per_game": round(profit_per_game, 2),
                    "games_per_hour": round(games_per_hour, 2),
                    "roi_percent": round(roi_percent, 2),
                    
                    # Категории для фильтрации
                    "is_profitable": is_profitable,
                    "profit_category": profit_category,
                    "bet_size_category": bet_size_category,
                    
                    # Дополнительные поля
                    "bot_created_at": bot.get("created_at", datetime.utcnow()),
                    "created_by_system_version": "v1.0_migrated",
                    "migration_source": "LEGACY",
                    "migrated_at": datetime.utcnow()
                }
                
                await db.completed_cycles.update_one(
                    {"_id": cycle["_id"]},
                    {"$set": update_data}
                )
                
                migrated_count += 1
                if migrated_count % 10 == 0:
                    print(f'✅ Мигрировано {migrated_count}/{len(cycles_to_migrate)} записей...')
                
            except Exception as e:
                print(f'❌ Ошибка миграции цикла {cycle.get("cycle_number", "?")}: {e}')
                continue
        
        print(f'🎉 Миграция завершена! Обновлено {migrated_count} записей из {len(cycles_to_migrate)}')
        
        # Проверяем результат
        total_cycles = await db.completed_cycles.count_documents({})
        migrated_cycles = await db.completed_cycles.count_documents({"migration_source": {"$exists": True}})
        
        print(f'📊 Статистика после миграции:')
        print(f'   Всего циклов: {total_cycles}')
        print(f'   Мигрированных: {migrated_cycles}')
        print(f'   Новых (v2.0): {await db.completed_cycles.count_documents({"migration_source": "NEW"})}')
        print(f'   Старых (LEGACY): {await db.completed_cycles.count_documents({"migration_source": "LEGACY"})}')
        
    except Exception as e:
        print(f'❌ Ошибка миграции: {e}')
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(migrate_completed_cycles())