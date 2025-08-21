#!/usr/bin/env python3
"""
Диагностика проблемы запуска циклов при создании ботов
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Добавляем путь к backend
sys.path.append('/workspace/backend')

async def diagnose_cycle_startup_issue():
    """Диагностирует проблему запуска циклов"""
    print("🔍 ДИАГНОСТИКА: Почему не запускаются циклы при создании ботов?")
    print("=" * 70)
    
    try:
        # Пробуем импортировать модули
        from server import (
            db, maintain_all_bots_active_bets, create_full_bot_cycle,
            Bot, BotType
        )
        print("✅ Модули сервера импортированы")
        
        # Проверяем подключение к БД
        try:
            # Простая проверка подключения
            await db.list_collection_names()
            print("✅ MongoDB подключен")
            db_available = True
        except Exception as e:
            print(f"❌ MongoDB недоступен: {e}")
            db_available = False
            return await simulate_diagnosis()
        
        # Создаём тестового бота
        test_bot_id = "diagnosis_bot_001"
        
        # Сначала очищаем старые данные
        await cleanup_test_bot(test_bot_id)
        
        # Создаём бота с правильными параметрами
        test_bot = Bot(
            id=test_bot_id,
            name="DiagnosisBot",
            bot_type=BotType.REGULAR,
            min_bet_amount=1.0,
            max_bet_amount=100.0,
            wins_percentage=44.0,
            losses_percentage=36.0,
            draws_percentage=20.0,
            wins_count=7,
            losses_count=6,
            draws_count=3,
            cycle_games=16,
            pause_between_cycles=5,
            is_active=True,
            has_completed_cycles=False  # Важно для диагностики
        )
        
        print(f"\n1️⃣ СОЗДАНИЕ ТЕСТОВОГО БОТА:")
        print(f"   ID: {test_bot.id}")
        print(f"   Активен: {test_bot.is_active}")
        print(f"   Тип: {test_bot.bot_type}")
        print(f"   Параметры: {test_bot.min_bet_amount}-{test_bot.max_bet_amount}, {test_bot.cycle_games} игр")
        print(f"   has_completed_cycles: {test_bot.has_completed_cycles}")
        
        # Сохраняем в БД
        await db.bots.insert_one(test_bot.dict())
        print("✅ Бот сохранён в БД")
        
        # Проверяем что бот действительно создался
        saved_bot = await db.bots.find_one({"id": test_bot_id})
        if saved_bot:
            print("✅ Бот найден в БД после создания")
        else:
            print("❌ Бот НЕ найден в БД!")
            return
        
        # 2. Проверяем начальное состояние
        print(f"\n2️⃣ ПРОВЕРКА НАЧАЛЬНОГО СОСТОЯНИЯ:")
        
        # Считаем игры бота
        total_games = await db.games.count_documents({
            "creator_id": test_bot_id,
            "status": {"$in": ["WAITING", "ACTIVE", "COMPLETED"]}
        })
        
        active_games = await db.games.count_documents({
            "creator_id": test_bot_id,
            "status": {"$in": ["WAITING", "ACTIVE"]}
        })
        
        completed_games = await db.games.count_documents({
            "creator_id": test_bot_id,
            "status": "COMPLETED"
        })
        
        print(f"   Всего игр: {total_games}")
        print(f"   Активных игр: {active_games}")
        print(f"   Завершённых игр: {completed_games}")
        
        # Проверяем условия создания цикла
        needs_initial_cycle = total_games == 0
        cycle_fully_completed = (total_games >= 16 and active_games == 0 and completed_games > 0)
        
        print(f"   needs_initial_cycle: {needs_initial_cycle}")
        print(f"   cycle_fully_completed: {cycle_fully_completed}")
        
        # 3. Тестируем логику maintain_all_bots_active_bets
        print(f"\n3️⃣ ТЕСТИРОВАНИЕ АВТОМАТИЗАЦИИ:")
        print("   Запускаем maintain_all_bots_active_bets()...")
        
        # Запускаем функцию автоматизации
        await maintain_all_bots_active_bets()
        
        # Проверяем результат
        games_after = await db.games.count_documents({
            "creator_id": test_bot_id,
            "status": {"$in": ["WAITING", "ACTIVE", "COMPLETED"]}
        })
        
        print(f"   Игр после автоматизации: {games_after}")
        
        if games_after > 0:
            print("✅ ЦИКЛ СОЗДАЛСЯ АВТОМАТИЧЕСКИ!")
            
            # Анализируем созданные игры
            games = await db.games.find({"creator_id": test_bot_id}).to_list(None)
            
            print(f"   Создано игр: {len(games)}")
            
            # Анализируем intended_result
            results_count = {}
            total_amount = 0
            for game in games:
                result = game.get("metadata", {}).get("intended_result", "unknown")
                results_count[result] = results_count.get(result, 0) + 1
                total_amount += game.get("bet_amount", 0)
            
            print(f"   Распределение: {results_count}")
            print(f"   Общая сумма: ${total_amount}")
            
            # Проверяем правильность
            expected_distribution = {"win": 7, "loss": 6, "draw": 3}
            distribution_correct = all(
                results_count.get(key, 0) == expected_distribution[key] 
                for key in expected_distribution
            )
            
            amount_correct = total_amount == 809
            
            if distribution_correct and amount_correct:
                print("✅ Цикл создан с ПРАВИЛЬНЫМИ параметрами!")
                print(f"   ✅ Распределение: {results_count}")
                print(f"   ✅ Общая сумма: ${total_amount}")
                return "SUCCESS"
            else:
                print("❌ Цикл создан с НЕПРАВИЛЬНЫМИ параметрами!")
                print(f"   Ожидалось: {expected_distribution}, сумма: 809")
                print(f"   Получено: {results_count}, сумма: {total_amount}")
                return "INCORRECT_PARAMETERS"
        else:
            print("❌ ЦИКЛ НЕ СОЗДАЛСЯ!")
            
            # Диагностируем почему
            print(f"\n🔍 ДИАГНОСТИКА ПРОБЛЕМЫ:")
            
            # Проверяем что бот активен
            fresh_bot = await db.bots.find_one({"id": test_bot_id})
            if fresh_bot:
                print(f"   Бот активен: {fresh_bot.get('is_active', False)}")
                print(f"   Тип бота: {fresh_bot.get('bot_type', 'Unknown')}")
                print(f"   has_completed_cycles: {fresh_bot.get('has_completed_cycles', False)}")
            else:
                print("   ❌ Бот исчез из БД!")
            
            # Проверяем логику создания циклов
            if needs_initial_cycle:
                print("   ✅ Условие needs_initial_cycle выполнено")
                print("   ❌ Но цикл не создался - проблема в create_full_bot_cycle()")
            else:
                print("   ❌ Условие needs_initial_cycle НЕ выполнено")
                print("   🔧 Проблема в логике определения состояния")
            
            return "CYCLE_NOT_CREATED"
    
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return await simulate_diagnosis()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return "ERROR"
    
    finally:
        # Очищаем тестовые данные
        try:
            await cleanup_test_bot(test_bot_id)
        except:
            pass

async def simulate_diagnosis():
    """Симуляция диагностики без БД"""
    print("\n🎭 СИМУЛЯЦИОННАЯ ДИАГНОСТИКА")
    print("=" * 50)
    
    print("📋 ПРОВЕРЯЕМЫЕ УСЛОВИЯ ДЛЯ СОЗДАНИЯ ЦИКЛА:")
    
    conditions = [
        {
            "name": "Бот активен (is_active = True)",
            "check": "Проверяется в maintain_all_bots_active_bets()",
            "status": "✅ Должно работать"
        },
        {
            "name": "Тип бота REGULAR",
            "check": "bot_type = 'REGULAR'",
            "status": "✅ Должно работать"
        },
        {
            "name": "Нет игр (total_games = 0)",
            "check": "needs_initial_cycle = True",
            "status": "✅ Для нового бота должно быть True"
        },
        {
            "name": "Логика создания исправлена",
            "check": "Убрано ограничение has_completed_cycles",
            "status": "✅ Исправлено в коде"
        },
        {
            "name": "Автоматизация запущена",
            "check": "bot_automation_loop() работает каждые 5 сек",
            "status": "⚠️ Зависит от MongoDB и startup"
        }
    ]
    
    for condition in conditions:
        print(f"\n   📋 {condition['name']}:")
        print(f"      Проверка: {condition['check']}")
        print(f"      Статус: {condition['status']}")
    
    print(f"\n🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ ПРОБЛЕМЫ:")
    
    issues = [
        {
            "issue": "MongoDB не запущен",
            "solution": "Установить и запустить MongoDB",
            "priority": "КРИТИЧНО"
        },
        {
            "issue": "bot_automation_loop() не запустился",
            "solution": "Проверить логи сервера на '✅ Bot automation loop started'",
            "priority": "КРИТИЧНО"
        },
        {
            "issue": "Ошибки в startup событиях",
            "solution": "Проверить что нет конфликтов в @app.on_event('startup')",
            "priority": "ВЫСОКИЙ"
        },
        {
            "issue": "Ошибки в create_full_bot_cycle()",
            "solution": "Проверить логи на ошибки создания ставок",
            "priority": "ВЫСОКИЙ"
        },
        {
            "issue": "Бот создается с is_active = False",
            "solution": "Проверить функцию создания ботов",
            "priority": "СРЕДНИЙ"
        }
    ]
    
    for issue in issues:
        print(f"\n   ❌ {issue['issue']}:")
        print(f"      Решение: {issue['solution']}")
        print(f"      Приоритет: {issue['priority']}")
    
    return "SIMULATION_COMPLETED"

async def cleanup_test_bot(bot_id):
    """Очищает тестового бота"""
    try:
        from server import db
        await db.bots.delete_many({"id": bot_id})
        await db.games.delete_many({"creator_id": bot_id})
        await db.bot_profit_accumulators.delete_many({"bot_id": bot_id})
        await db.completed_cycles.delete_many({"bot_id": bot_id})
    except:
        pass

def check_server_logs_instructions():
    """Инструкции по проверке логов сервера"""
    print(f"\n📋 ИНСТРУКЦИИ ПО ДИАГНОСТИКЕ:")
    print("=" * 50)
    
    print("🔍 ЧТО ПРОВЕРИТЬ В ЛОГАХ СЕРВЕРА:")
    
    log_checks = [
        {
            "message": "✅ Bot automation loop started",
            "meaning": "Автоматизация ботов запустилась",
            "action": "Если НЕТ - проблема в startup событиях"
        },
        {
            "message": "✅ Initial bot cycles check started", 
            "meaning": "Принудительная проверка циклов запустилась",
            "action": "Если НЕТ - проблема в startup_event_secondary()"
        },
        {
            "message": "🤖 Checking X active bots for cycle management",
            "meaning": "Автоматизация находит активных ботов",
            "action": "Если X=0 - боты не активны или не созданы"
        },
        {
            "message": "🔍 Bot TestBot: cycle status - total_games=0",
            "meaning": "Бот найден и проверяется состояние",
            "action": "Если НЕТ - бот не найден или не активен"
        },
        {
            "message": "🎯 Bot TestBot: no games found, starting new cycle",
            "meaning": "Принято решение создать цикл",
            "action": "Если НЕТ - проблема в логике принятия решений"
        },
        {
            "message": "✅ Bot TestBot created cycle of 16 bets",
            "meaning": "Цикл успешно создан",
            "action": "Если НЕТ - проблема в create_full_bot_cycle()"
        }
    ]
    
    for check in log_checks:
        print(f"\n   📝 '{check['message']}'")
        print(f"      Означает: {check['meaning']}")
        print(f"      Если НЕТ: {check['action']}")
    
    print(f"\n🚀 ПОШАГОВАЯ ДИАГНОСТИКА:")
    steps = [
        "1. Запустите сервер: cd /workspace/backend && python3 server.py",
        "2. Следите за логами при запуске",
        "3. Создайте бота через интерфейс",
        "4. Проверьте появились ли сообщения выше в логах",
        "5. Если нет - определите на каком этапе остановка"
    ]
    
    for step in steps:
        print(f"   {step}")

async def test_cycle_creation_conditions():
    """Тестирует условия создания циклов"""
    print(f"\n🧪 ТЕСТ УСЛОВИЙ СОЗДАНИЯ ЦИКЛОВ")
    print("=" * 50)
    
    # Симуляция различных состояний бота
    test_scenarios = [
        {
            "name": "Новый активный бот",
            "bot_state": {
                "is_active": True,
                "bot_type": "REGULAR",
                "has_completed_cycles": False
            },
            "games_state": {
                "total_games": 0,
                "active_games": 0,
                "completed_games": 0
            },
            "expected_action": "СОЗДАТЬ ЦИКЛ"
        },
        {
            "name": "Неактивный бот",
            "bot_state": {
                "is_active": False,
                "bot_type": "REGULAR",
                "has_completed_cycles": False
            },
            "games_state": {
                "total_games": 0,
                "active_games": 0,
                "completed_games": 0
            },
            "expected_action": "ПРОПУСТИТЬ"
        },
        {
            "name": "Human бот",
            "bot_state": {
                "is_active": True,
                "bot_type": "HUMAN",
                "has_completed_cycles": False
            },
            "games_state": {
                "total_games": 0,
                "active_games": 0,
                "completed_games": 0
            },
            "expected_action": "ПРОПУСТИТЬ"
        },
        {
            "name": "Бот с активными играми",
            "bot_state": {
                "is_active": True,
                "bot_type": "REGULAR",
                "has_completed_cycles": True
            },
            "games_state": {
                "total_games": 10,
                "active_games": 5,
                "completed_games": 5
            },
            "expected_action": "ЖДАТЬ"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 Сценарий: {scenario['name']}")
        
        bot_state = scenario["bot_state"]
        games_state = scenario["games_state"]
        
        # Логика из maintain_all_bots_active_bets
        if not bot_state["is_active"] or bot_state["bot_type"] != "REGULAR":
            action = "ПРОПУСТИТЬ"
        else:
            total_games = games_state["total_games"]
            active_games = games_state["active_games"]
            completed_games = games_state["completed_games"]
            
            needs_initial_cycle = total_games == 0
            cycle_fully_completed = (total_games >= 16 and active_games == 0 and completed_games > 0)
            
            if needs_initial_cycle:
                action = "СОЗДАТЬ ЦИКЛ"
            elif cycle_fully_completed:
                action = "ЗАВЕРШИТЬ ЦИКЛ"
            elif active_games > 0:
                action = "ЖДАТЬ"
            else:
                action = "НЕОПРЕДЕЛЕННОЕ"
        
        expected = scenario["expected_action"]
        correct = action == expected
        
        print(f"   Состояние: {bot_state}")
        print(f"   Игры: {games_state}")
        print(f"   Решение: {action}")
        print(f"   Ожидалось: {expected}")
        print(f"   Результат: {'✅' if correct else '❌'}")

def main():
    """Главная функция диагностики"""
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ ЗАПУСКА ЦИКЛОВ БОТОВ")
    print("❓ Почему при создании ботов не запускаются циклы?")
    print("=" * 70)
    
    # Запускаем диагностику
    try:
        result = asyncio.run(diagnose_cycle_startup_issue())
        
        # Дополнительные проверки
        asyncio.run(test_cycle_creation_conditions())
        
        # Инструкции
        check_server_logs_instructions()
        
        print(f"\n" + "=" * 70)
        print("📊 РЕЗУЛЬТАТ ДИАГНОСТИКИ")
        print("=" * 70)
        
        if result == "SUCCESS":
            print("✅ ЦИКЛЫ СОЗДАЮТСЯ ПРАВИЛЬНО!")
            print("Проблема может быть в конкретной среде или настройках")
        elif result == "CYCLE_NOT_CREATED":
            print("❌ ЦИКЛЫ НЕ СОЗДАЮТСЯ!")
            print("Проверьте логи сервера и состояние автоматизации")
        elif result == "INCORRECT_PARAMETERS":
            print("⚠️ ЦИКЛЫ СОЗДАЮТСЯ, НО С НЕПРАВИЛЬНЫМИ ПАРАМЕТРАМИ!")
            print("Проверьте функции генерации ставок")
        else:
            print("⚠️ ДИАГНОСТИКА В СИМУЛЯЦИОННОМ РЕЖИМЕ")
            print("Для полной диагностики нужен запущенный MongoDB")
        
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")

if __name__ == "__main__":
    main()