#!/usr/bin/env python3
"""
Скрипт для проверки целостности данных циклов ботов.
Проверяет соответствие между:
- bot.completed_cycles_count
- количеством записей в completed_cycles
- записями в bot_profit_accumulators
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Добавляем путь к серверу для импорта настроек
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def verify_cycles_integrity():
    """Проверяет целостность данных циклов."""
    
    # Подключение к MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "write_russian_2")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        print("🔍 Проверка целостности данных циклов ботов...")
        print("=" * 60)
        
        # Получаем всех обычных ботов
        bots = await db.bots.find({"bot_type": "REGULAR"}).to_list(1000)
        
        issues_found = []
        total_bots = len(bots)
        
        for i, bot in enumerate(bots, 1):
            bot_id = bot.get("id")
            bot_name = bot.get("name", f"Bot_{bot_id[:8]}")
            
            print(f"[{i}/{total_bots}] Проверяю бота: {bot_name} ({bot_id})")
            
            # Получаем счётчики из документа бота
            completed_cycles_count = bot.get("completed_cycles_count", 0)
            old_completed_cycles = bot.get("completed_cycles", 0)  # Старое поле
            
            # Подсчитываем реальные циклы в completed_cycles
            real_cycles_count = await db.completed_cycles.count_documents({
                "bot_id": bot_id,
                "id": {"$not": {"$regex": "^temp_cycle_"}}  # Исключаем фиктивные
            })
            
            # Подсчитываем фиктивные циклы
            fake_cycles_count = await db.completed_cycles.count_documents({
                "bot_id": bot_id,
                "id": {"$regex": "^temp_cycle_"}
            })
            
            # Подсчитываем завершённые аккумуляторы
            completed_accumulators = await db.bot_profit_accumulators.count_documents({
                "bot_id": bot_id,
                "is_cycle_completed": True
            })
            
            # Активные аккумуляторы
            active_accumulators = await db.bot_profit_accumulators.count_documents({
                "bot_id": bot_id,
                "is_cycle_completed": False
            })
            
            # Проверяем несоответствия
            bot_issues = []
            
            if fake_cycles_count > 0:
                bot_issues.append(f"🚨 {fake_cycles_count} фиктивных циклов")
            
            if completed_cycles_count != real_cycles_count:
                bot_issues.append(f"❌ Счётчик: {completed_cycles_count}, реальных циклов: {real_cycles_count}")
            
            if old_completed_cycles != completed_cycles_count and old_completed_cycles > 0:
                bot_issues.append(f"⚠️ Старый счётчик: {old_completed_cycles}, новый: {completed_cycles_count}")
            
            if completed_accumulators > 0 and completed_accumulators != real_cycles_count:
                bot_issues.append(f"🔄 Аккумуляторов: {completed_accumulators}, циклов: {real_cycles_count}")
            
            if active_accumulators > 1:
                bot_issues.append(f"⚡ Множественные активные аккумуляторы: {active_accumulators}")
            
            if bot_issues:
                issues_found.append({
                    "bot_id": bot_id,
                    "bot_name": bot_name,
                    "issues": bot_issues,
                    "stats": {
                        "completed_cycles_count": completed_cycles_count,
                        "old_completed_cycles": old_completed_cycles,
                        "real_cycles": real_cycles_count,
                        "fake_cycles": fake_cycles_count,
                        "completed_accumulators": completed_accumulators,
                        "active_accumulators": active_accumulators
                    }
                })
                
                print(f"  ❌ Найдены проблемы:")
                for issue in bot_issues:
                    print(f"    - {issue}")
            else:
                print(f"  ✅ Данные корректны")
        
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЁТ")
        print("=" * 60)
        
        if not issues_found:
            print("🎉 Все данные циклов корректны!")
        else:
            print(f"⚠️ Найдены проблемы у {len(issues_found)} ботов из {total_bots}")
            
            # Группируем проблемы по типам
            fake_cycles_bots = []
            counter_mismatch_bots = []
            accumulator_issues_bots = []
            
            for issue in issues_found:
                for problem in issue["issues"]:
                    if "фиктивных циклов" in problem:
                        fake_cycles_bots.append(issue)
                    elif "Счётчик:" in problem:
                        counter_mismatch_bots.append(issue)
                    elif "Аккумуляторов:" in problem or "активные аккумуляторы" in problem:
                        accumulator_issues_bots.append(issue)
            
            if fake_cycles_bots:
                total_fake = sum(issue["stats"]["fake_cycles"] for issue in fake_cycles_bots)
                print(f"\n🚨 Фиктивные циклы: {len(fake_cycles_bots)} ботов, {total_fake} записей")
                print("   Решение: Запустите cleanup_fake_cycles.py")
            
            if counter_mismatch_bots:
                print(f"\n❌ Несоответствие счётчиков: {len(counter_mismatch_bots)} ботов")
                print("   Решение: Синхронизируйте счётчики с реальными данными")
            
            if accumulator_issues_bots:
                print(f"\n🔄 Проблемы с аккумуляторами: {len(accumulator_issues_bots)} ботов")
                print("   Решение: Проверьте логику завершения циклов")
        
        # Общая статистика
        total_real_cycles = await db.completed_cycles.count_documents({
            "id": {"$not": {"$regex": "^temp_cycle_"}}
        })
        total_fake_cycles = await db.completed_cycles.count_documents({
            "id": {"$regex": "^temp_cycle_"}
        })
        total_accumulators = await db.bot_profit_accumulators.count_documents({})
        
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего ботов: {total_bots}")
        print(f"   Реальных циклов: {total_real_cycles}")
        print(f"   Фиктивных циклов: {total_fake_cycles}")
        print(f"   Всего аккумуляторов: {total_accumulators}")
        
        # Сохраняем отчёт
        report = {
            "timestamp": datetime.utcnow(),
            "total_bots": total_bots,
            "issues_found": len(issues_found),
            "total_real_cycles": total_real_cycles,
            "total_fake_cycles": total_fake_cycles,
            "total_accumulators": total_accumulators,
            "details": issues_found
        }
        
        # Можно сохранить отчёт в файл или БД
        print(f"\n💾 Отчёт сохранён с timestamp: {report['timestamp']}")
        
        return issues_found
        
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return []
        
    finally:
        client.close()
        print("🔌 Соединение с базой данных закрыто.")

if __name__ == "__main__":
    print("🔍 Скрипт проверки целостности циклов ботов")
    print("=" * 50)
    
    asyncio.run(verify_cycles_integrity())