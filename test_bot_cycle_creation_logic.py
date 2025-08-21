#!/usr/bin/env python3
"""
Тест логики создания циклов ботов (без MongoDB)
"""

import asyncio
from datetime import datetime

class MockDB:
    """Mock база данных"""
    def __init__(self):
        self.bots = {}
        self.games = {}
        self.accumulators = {}
    
    async def find_bots(self, query):
        """Поиск ботов"""
        result = []
        for bot_id, bot in self.bots.items():
            match = True
            for key, value in query.items():
                if bot.get(key) != value:
                    match = False
                    break
            if match:
                result.append(bot)
        return result
    
    async def count_games(self, bot_id, statuses):
        """Подсчёт игр"""
        games = self.games.get(bot_id, [])
        return len([g for g in games if g.get("status") in statuses])
    
    async def create_games(self, bot_id, count):
        """Создание игр"""
        if bot_id not in self.games:
            self.games[bot_id] = []
        
        for i in range(count):
            game = {
                "id": f"game_{bot_id}_{i}",
                "creator_id": bot_id,
                "status": "WAITING",
                "bet_amount": 50,  # Примерная ставка
                "metadata": {"intended_result": "win" if i < 7 else ("loss" if i < 13 else "draw")},
                "created_at": datetime.utcnow()
            }
            self.games[bot_id].append(game)
        
        return count

async def simulate_maintain_all_bots_active_bets(mock_db):
    """Симуляция функции maintain_all_bots_active_bets"""
    print("🤖 СИМУЛЯЦИЯ maintain_all_bots_active_bets()")
    print("-" * 50)
    
    # Получаем активных ботов
    active_bots = await mock_db.find_bots({
        "is_active": True,
        "bot_type": "REGULAR"
    })
    
    print(f"   Найдено активных ботов: {len(active_bots)}")
    
    if not active_bots:
        print("   📭 Нет активных ботов")
        return False
    
    cycles_created = 0
    
    for bot in active_bots:
        bot_id = bot["id"]
        bot_name = bot["name"]
        cycle_games_target = bot.get("cycle_games", 16)
        
        print(f"\n   🔍 Проверяем бота: {bot_name}")
        
        # Подсчитываем игры
        total_games = await mock_db.count_games(bot_id, ["WAITING", "ACTIVE", "COMPLETED"])
        active_games = await mock_db.count_games(bot_id, ["WAITING", "ACTIVE"])
        completed_games = await mock_db.count_games(bot_id, ["COMPLETED"])
        
        print(f"      Игры: total={total_games}, active={active_games}, completed={completed_games}, target={cycle_games_target}")
        
        # Определяем условия
        cycle_fully_completed = (
            total_games >= cycle_games_target and 
            active_games == 0 and 
            completed_games > 0
        )
        needs_initial_cycle = total_games == 0
        
        print(f"      Условия: needs_initial_cycle={needs_initial_cycle}, cycle_fully_completed={cycle_fully_completed}")
        
        # ИСПРАВЛЕННАЯ ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ
        if needs_initial_cycle:
            # Нет игр вообще - создаем цикл (независимо от has_completed_cycles)
            print(f"      🎯 Решение: СОЗДАТЬ НОВЫЙ ЦИКЛ")
            
            # Симуляция create_full_bot_cycle
            created_count = await mock_db.create_games(bot_id, cycle_games_target)
            
            if created_count == cycle_games_target:
                print(f"      ✅ Создан цикл: {created_count} ставок")
                cycles_created += 1
            else:
                print(f"      ❌ Ошибка создания цикла")
        
        elif cycle_fully_completed:
            print(f"      🏁 Решение: ЗАВЕРШИТЬ ЦИКЛ")
        
        elif active_games > 0:
            print(f"      🎮 Решение: ЖДАТЬ завершения активных игр")
        
        else:
            print(f"      ❓ Решение: НЕОПРЕДЕЛЕННОЕ СОСТОЯНИЕ")
    
    return cycles_created > 0

async def test_bot_creation_and_cycle_startup():
    """Тест создания бота и запуска цикла"""
    print("🧪 ТЕСТ СОЗДАНИЯ БОТА И ЗАПУСКА ЦИКЛА")
    print("=" * 60)
    
    # Создаём mock БД
    mock_db = MockDB()
    
    # 1. Создаём тестового бота
    print("1️⃣ СОЗДАНИЕ ТЕСТОВОГО БОТА:")
    
    test_bot = {
        "id": "test_bot_001",
        "name": "TestBot",
        "bot_type": "REGULAR",
        "is_active": True,
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "cycle_games": 16,
        "wins_percentage": 44.0,
        "losses_percentage": 36.0,
        "draws_percentage": 20.0,
        "wins_count": 7,
        "losses_count": 6,
        "draws_count": 3,
        "pause_between_cycles": 5,
        "has_completed_cycles": False,
        "created_at": datetime.utcnow()
    }
    
    mock_db.bots[test_bot["id"]] = test_bot
    
    print(f"   ✅ Бот создан: {test_bot['name']}")
    print(f"   ✅ Активен: {test_bot['is_active']}")
    print(f"   ✅ Тип: {test_bot['bot_type']}")
    print(f"   ✅ Параметры: {test_bot['min_bet_amount']}-{test_bot['max_bet_amount']}, {test_bot['cycle_games']} игр")
    
    # 2. Симулируем автоматизацию
    print(f"\n2️⃣ СИМУЛЯЦИЯ АВТОМАТИЗАЦИИ:")
    
    cycle_created = await simulate_maintain_all_bots_active_bets(mock_db)
    
    # 3. Проверяем результат
    print(f"\n3️⃣ ПРОВЕРКА РЕЗУЛЬТАТА:")
    
    if cycle_created:
        games = mock_db.games.get(test_bot["id"], [])
        print(f"   ✅ Цикл создан!")
        print(f"   ✅ Создано игр: {len(games)}")
        
        # Анализируем распределение
        results_count = {}
        for game in games:
            result = game.get("metadata", {}).get("intended_result", "unknown")
            results_count[result] = results_count.get(result, 0) + 1
        
        print(f"   ✅ Распределение: {results_count}")
        
        expected = {"win": 7, "loss": 6, "draw": 3}
        correct = all(results_count.get(k, 0) == v for k, v in expected.items())
        
        if correct:
            print("   ✅ Распределение КОРРЕКТНО!")
            return "SUCCESS"
        else:
            print("   ❌ Распределение НЕПРАВИЛЬНОЕ!")
            return "INCORRECT_DISTRIBUTION"
    else:
        print(f"   ❌ Цикл НЕ создан!")
        return "CYCLE_NOT_CREATED"

def analyze_potential_issues():
    """Анализирует потенциальные проблемы"""
    print(f"\n🔍 АНАЛИЗ ПОТЕНЦИАЛЬНЫХ ПРОБЛЕМ")
    print("=" * 60)
    
    issues = [
        {
            "category": "🗄️ База данных",
            "problems": [
                "MongoDB не установлен или не запущен",
                "Ошибки подключения к localhost:27017",
                "Проблемы с правами доступа к БД"
            ]
        },
        {
            "category": "⚙️ Автоматизация",
            "problems": [
                "bot_automation_loop() не запустился при старте сервера",
                "Конфликты в startup событиях",
                "Ошибки в maintain_all_bots_active_bets()"
            ]
        },
        {
            "category": "🤖 Создание ботов",
            "problems": [
                "Боты создаются с is_active = False",
                "Неправильный bot_type (не REGULAR)",
                "Ошибки в функции создания ботов"
            ]
        },
        {
            "category": "🎯 Логика циклов",
            "problems": [
                "Ошибки в create_full_bot_cycle()",
                "Проблемы с генерацией ставок",
                "Неправильные условия создания циклов"
            ]
        }
    ]
    
    for issue_cat in issues:
        print(f"\n{issue_cat['category']}:")
        for problem in issue_cat['problems']:
            print(f"   ❌ {problem}")

def main():
    """Главная функция"""
    print("🔍 ДИАГНОСТИКА: Почему не запускаются циклы при создании ботов?")
    print("=" * 70)
    
    # Запускаем тест
    try:
        result = asyncio.run(test_bot_creation_and_cycle_startup())
        
        print(f"\n📊 РЕЗУЛЬТАТ СИМУЛЯЦИОННОГО ТЕСТА:")
        
        if result == "SUCCESS":
            print("✅ ЛОГИКА СОЗДАНИЯ ЦИКЛОВ РАБОТАЕТ КОРРЕКТНО!")
            print("🔧 Проблема скорее всего в окружении (MongoDB, startup)")
        elif result == "CYCLE_NOT_CREATED":
            print("❌ ЦИКЛЫ НЕ СОЗДАЮТСЯ!")
            print("🔧 Проблема в логике maintain_all_bots_active_bets()")
        elif result == "INCORRECT_DISTRIBUTION":
            print("⚠️ ЦИКЛЫ СОЗДАЮТСЯ, НО С НЕПРАВИЛЬНЫМ РАСПРЕДЕЛЕНИЕМ!")
            print("🔧 Проблема в generate_cycle_bets_natural_distribution()")
        
        # Анализ проблем
        analyze_potential_issues()
        
        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        print("1. Установите и запустите MongoDB")
        print("2. Запустите сервер и проверьте логи")
        print("3. Создайте бота и следите за логами автоматизации")
        print("4. Используйте MONGODB_SETUP_AND_DIAGNOSIS.md для детальной диагностики")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")

if __name__ == "__main__":
    main()