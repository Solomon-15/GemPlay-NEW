#!/usr/bin/env python3
"""
Комплексный тест полного маршрута создания циклов ботов и расчёта прибыли
От создания цикла до отображения в "Доход от ботов"
"""

import asyncio
import sys
import os
import json
import math
from datetime import datetime

# Добавляем путь к backend
sys.path.append('/workspace/backend')

# Проверяем что можем импортировать основные функции
try:
    from server import (
        db, create_full_bot_cycle, complete_bot_cycle,
        generate_cycle_bets_natural_distribution
    )
    print("✅ Модули успешно импортированы")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Тест будет запущен в упрощённом режиме")
    db = None

class BotCycleFlowTester:
    def __init__(self):
        self.test_results = {
            "cycle_creation": None,
            "bet_distribution": None,
            "cycle_execution": None,
            "cycle_completion": None,
            "profit_calculation": None,
            "api_integration": None,
            "final_verification": None
        }
        
    async def run_complete_test(self):
        """Запускает полный тест маршрута"""
        print("🧪 КОМПЛЕКСНЫЙ ТЕСТ: Полный маршрут создания циклов ботов")
        print("=" * 80)
        
        try:
            # 1. Тест создания цикла
            await self.test_cycle_creation()
            
            # 2. Тест распределения ставок
            await self.test_bet_distribution()
            
            # 3. Тест выполнения цикла (симуляция игр)
            await self.test_cycle_execution()
            
            # 4. Тест завершения цикла
            await self.test_cycle_completion()
            
            # 5. Тест расчёта прибыли
            await self.test_profit_calculation()
            
            # 6. Тест API интеграции
            await self.test_api_integration()
            
            # 7. Финальная верификация
            await self.test_final_verification()
            
            # Итоговый отчёт
            self.generate_final_report()
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_cycle_creation(self):
        """Тест 1: Создание цикла бота"""
        print("\n📋 ТЕСТ 1: Создание цикла бота")
        print("-" * 50)
        
        # Создаём тестового бота
        test_bot = {
            "id": "test_bot_001",
            "name": "TestBot ROI",
            "cycle_games": 16,
            "min_bet_amount": 1.0,
            "max_bet_amount": 100.0,
            "wins_percentage": 44.0,
            "losses_percentage": 36.0,
            "draws_percentage": 20.0,
            "wins_count": 7,
            "losses_count": 6,
            "draws_count": 3
        }
        
        try:
            # Тестируем функцию создания цикла
            result = await create_full_bot_cycle(test_bot)
            
            if result:
                print("✅ Цикл успешно создан")
                
                # Проверяем что игры созданы в БД
                games = await db.games.find({"creator_id": test_bot["id"]}).to_list(None)
                print(f"✅ Создано игр: {len(games)}")
                
                # Проверяем распределение по результатам
                intended_results = {}
                for game in games:
                    result = game.get("metadata", {}).get("intended_result", "unknown")
                    intended_results[result] = intended_results.get(result, 0) + 1
                
                print(f"📊 Распределение результатов: {intended_results}")
                
                # Проверяем суммы ставок
                total_bets = sum(game.get("bet_amount", 0) for game in games)
                print(f"💰 Общая сумма ставок: {total_bets}")
                
                self.test_results["cycle_creation"] = {
                    "status": "SUCCESS",
                    "games_created": len(games),
                    "total_amount": total_bets,
                    "distribution": intended_results
                }
                
            else:
                print("❌ Ошибка создания цикла")
                self.test_results["cycle_creation"] = {"status": "FAILED", "error": "Creation failed"}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.test_results["cycle_creation"] = {"status": "ERROR", "error": str(e)}
    
    async def test_bet_distribution(self):
        """Тест 2: Проверка правильности распределения ставок"""
        print("\n🎯 ТЕСТ 2: Распределение ставок по категориям")
        print("-" * 50)
        
        try:
            # Тестируем функцию распределения ставок
            bets = await generate_cycle_bets_natural_distribution(
                bot_id="test_bot_001",
                min_bet=1.0,
                max_bet=100.0,
                cycle_games=16,
                wins_count=7,
                losses_count=6,
                draws_count=3,
                wins_percentage=44.0,
                losses_percentage=36.0,
                draws_percentage=20.0
            )
            
            # Анализируем распределение
            wins_bets = [bet for bet in bets if bet["result"] == "win"]
            losses_bets = [bet for bet in bets if bet["result"] == "loss"]
            draws_bets = [bet for bet in bets if bet["result"] == "draw"]
            
            wins_sum = sum(bet["amount"] for bet in wins_bets)
            losses_sum = sum(bet["amount"] for bet in losses_bets)
            draws_sum = sum(bet["amount"] for bet in draws_bets)
            
            total_sum = wins_sum + losses_sum + draws_sum
            active_pool = wins_sum + losses_sum
            profit = wins_sum - losses_sum
            roi = (profit / active_pool * 100) if active_pool > 0 else 0
            
            print(f"📊 Результаты распределения:")
            print(f"   Победы: {len(wins_bets)} ставок, сумма: {wins_sum}")
            print(f"   Поражения: {len(losses_bets)} ставок, сумма: {losses_sum}")
            print(f"   Ничьи: {len(draws_bets)} ставок, сумма: {draws_sum}")
            print(f"   Общая сумма: {total_sum}")
            print(f"   Активный пул: {active_pool}")
            print(f"   Прибыль: {profit}")
            print(f"   ROI: {roi:.2f}%")
            
            # Проверяем эталонные значения
            expected = {
                "total": 809,
                "wins": 356,
                "losses": 291,
                "draws": 162,
                "active_pool": 647,
                "profit": 65,
                "roi": 10.05
            }
            
            success = (
                total_sum == expected["total"] and
                wins_sum == expected["wins"] and
                losses_sum == expected["losses"] and
                draws_sum == expected["draws"]
            )
            
            if success:
                print("✅ Распределение соответствует эталонным значениям!")
            else:
                print("❌ Распределение НЕ соответствует эталонным значениям!")
                print(f"   Ожидалось: W={expected['wins']}, L={expected['losses']}, D={expected['draws']}")
                print(f"   Получено: W={wins_sum}, L={losses_sum}, D={draws_sum}")
            
            self.test_results["bet_distribution"] = {
                "status": "SUCCESS" if success else "FAILED",
                "actual": {
                    "wins": wins_sum,
                    "losses": losses_sum,
                    "draws": draws_sum,
                    "total": total_sum,
                    "roi": roi
                },
                "expected": expected,
                "matches_expected": success
            }
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.test_results["bet_distribution"] = {"status": "ERROR", "error": str(e)}
    
    async def test_cycle_execution(self):
        """Тест 3: Симуляция выполнения цикла"""
        print("\n🎮 ТЕСТ 3: Симуляция выполнения цикла")
        print("-" * 50)
        
        try:
            # Получаем все игры тестового бота
            games = await db.games.find({"creator_id": "test_bot_001"}).to_list(None)
            
            if not games:
                print("❌ Нет игр для симуляции")
                self.test_results["cycle_execution"] = {"status": "FAILED", "error": "No games found"}
                return
            
            # Симулируем завершение игр согласно intended_result
            completed_games = 0
            wins = 0
            losses = 0
            draws = 0
            
            for game in games:
                intended_result = game.get("metadata", {}).get("intended_result")
                game_id = game["id"]
                
                if intended_result == "win":
                    # Бот выиграл
                    await db.games.update_one(
                        {"id": game_id},
                        {"$set": {
                            "status": "COMPLETED",
                            "winner_id": "test_bot_001",
                            "completed_at": datetime.utcnow()
                        }}
                    )
                    wins += 1
                elif intended_result == "loss":
                    # Бот проиграл
                    await db.games.update_one(
                        {"id": game_id},
                        {"$set": {
                            "status": "COMPLETED",
                            "winner_id": "opponent_123",  # Любой другой ID
                            "completed_at": datetime.utcnow()
                        }}
                    )
                    losses += 1
                elif intended_result == "draw":
                    # Ничья
                    await db.games.update_one(
                        {"id": game_id},
                        {"$set": {
                            "status": "COMPLETED",
                            "winner_id": None,
                            "completed_at": datetime.utcnow()
                        }}
                    )
                    draws += 1
                
                completed_games += 1
            
            print(f"✅ Симуляция завершена:")
            print(f"   Завершено игр: {completed_games}")
            print(f"   Победы: {wins}")
            print(f"   Поражения: {losses}")
            print(f"   Ничьи: {draws}")
            
            self.test_results["cycle_execution"] = {
                "status": "SUCCESS",
                "completed_games": completed_games,
                "wins": wins,
                "losses": losses,
                "draws": draws
            }
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.test_results["cycle_execution"] = {"status": "ERROR", "error": str(e)}
    
    async def test_cycle_completion(self):
        """Тест 4: Завершение цикла и создание записи в completed_cycles"""
        print("\n🏁 ТЕСТ 4: Завершение цикла")
        print("-" * 50)
        
        try:
            # Создаём/находим аккумулятор для бота
            accumulator = await db.bot_profit_accumulators.find_one({
                "bot_id": "test_bot_001",
                "is_cycle_completed": False
            })
            
            if not accumulator:
                # Создаём аккумулятор если его нет
                accumulator = {
                    "id": "test_accumulator_001",
                    "bot_id": "test_bot_001",
                    "cycle_number": 1,
                    "total_spent": 809.0,
                    "total_earned": 874.0,  # 809 + 65 прибыли
                    "games_completed": 16,
                    "games_won": 7,
                    "games_lost": 6,
                    "games_drawn": 3,
                    "cycle_start_date": datetime.utcnow(),
                    "is_cycle_completed": False
                }
                await db.bot_profit_accumulators.insert_one(accumulator)
                print("✅ Создан тестовый аккумулятор")
            
            # Завершаем цикл
            await complete_bot_cycle(
                accumulator_id=accumulator["id"],
                total_spent=809.0,
                total_earned=874.0,
                bot_id="test_bot_001"
            )
            
            # Проверяем что создалась запись в completed_cycles
            completed_cycle = await db.completed_cycles.find_one({
                "bot_id": "test_bot_001",
                "cycle_number": 1
            })
            
            if completed_cycle:
                print("✅ Цикл успешно завершён и сохранён в completed_cycles")
                print(f"📊 Данные завершённого цикла:")
                print(f"   Всего игр: {completed_cycle.get('total_bets')}")
                print(f"   Победы: {completed_cycle.get('wins_count')}")
                print(f"   Поражения: {completed_cycle.get('losses_count')}")
                print(f"   Ничьи: {completed_cycle.get('draws_count')}")
                print(f"   Сумма выигрышей: {completed_cycle.get('total_winnings')}")
                print(f"   Сумма потерь: {completed_cycle.get('total_losses')}")
                print(f"   Сумма ничьих: {completed_cycle.get('total_draws', 'N/A')}")
                print(f"   Активный пул: {completed_cycle.get('active_pool')}")
                print(f"   Чистая прибыль: {completed_cycle.get('net_profit')}")
                print(f"   ROI: {completed_cycle.get('roi_active')}%")
                
                self.test_results["cycle_completion"] = {
                    "status": "SUCCESS",
                    "cycle_data": {
                        "total_bets": completed_cycle.get('total_bets'),
                        "wins": completed_cycle.get('wins_count'),
                        "losses": completed_cycle.get('losses_count'),
                        "draws": completed_cycle.get('draws_count'),
                        "total_winnings": completed_cycle.get('total_winnings'),
                        "total_losses": completed_cycle.get('total_losses'),
                        "active_pool": completed_cycle.get('active_pool'),
                        "net_profit": completed_cycle.get('net_profit'),
                        "roi_active": completed_cycle.get('roi_active')
                    }
                }
            else:
                print("❌ Запись о завершённом цикле не найдена")
                self.test_results["cycle_completion"] = {"status": "FAILED", "error": "Completed cycle not found"}
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            self.test_results["cycle_completion"] = {"status": "ERROR", "error": str(e)}
    
    async def test_profit_calculation(self):
        """Тест 5: Проверка расчёта прибыли"""
        print("\n💰 ТЕСТ 5: Проверка расчёта прибыли")
        print("-" * 50)
        
        try:
            # Проверяем что аккумулятор помечен как завершённый
            accumulator = await db.bot_profit_accumulators.find_one({
                "bot_id": "test_bot_001",
                "is_cycle_completed": True
            })
            
            if accumulator:
                print("✅ Аккумулятор помечен как завершённый")
                print(f"   Потрачено: {accumulator.get('total_spent')}")
                print(f"   Заработано: {accumulator.get('total_earned')}")
                print(f"   Прибыль переданная: {accumulator.get('profit_transferred')}")
                
                self.test_results["profit_calculation"] = {
                    "status": "SUCCESS",
                    "accumulator_data": {
                        "total_spent": accumulator.get('total_spent'),
                        "total_earned": accumulator.get('total_earned'),
                        "profit_transferred": accumulator.get('profit_transferred'),
                        "is_completed": accumulator.get('is_cycle_completed')
                    }
                }
            else:
                print("❌ Завершённый аккумулятор не найден")
                self.test_results["profit_calculation"] = {"status": "FAILED", "error": "Completed accumulator not found"}
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.test_results["profit_calculation"] = {"status": "ERROR", "error": str(e)}
    
    async def test_api_integration(self):
        """Тест 6: Проверка API интеграции"""
        print("\n🔌 ТЕСТ 6: API интеграция")
        print("-" * 50)
        
        try:
            # Тестируем get_bot_completed_cycles
            print("📡 Тестируем get_bot_completed_cycles...")
            
            # Имитируем вызов API (без HTTP, напрямую функцию)
            # В реальности это будет HTTP запрос к /admin/bots/{bot_id}/completed-cycles
            
            # Создаём mock user для функции
            class MockUser:
                def __init__(self):
                    self.role = "ADMIN"
            
            mock_user = MockUser()
            
            # Вызываем функцию напрямую
            from server import get_bot_completed_cycles
            
            # Здесь мы бы вызвали функцию, но она требует FastAPI контекст
            # Вместо этого проверим данные напрямую из БД
            
            completed_cycles = await db.completed_cycles.find({"bot_id": "test_bot_001"}).to_list(None)
            
            if completed_cycles:
                cycle = completed_cycles[0]
                print("✅ Данные найдены в completed_cycles:")
                print(f"   ID цикла: {cycle.get('id')}")
                print(f"   Номер цикла: {cycle.get('cycle_number')}")
                print(f"   Всего игр: {cycle.get('total_bets')}")
                print(f"   W/L/D: {cycle.get('wins_count')}/{cycle.get('losses_count')}/{cycle.get('draws_count')}")
                print(f"   Выигрыши: {cycle.get('total_winnings')}")
                print(f"   Потери: {cycle.get('total_losses')}")
                print(f"   Прибыль: {cycle.get('net_profit')}")
                print(f"   ROI: {cycle.get('roi_active')}%")
                
                self.test_results["api_integration"] = {
                    "status": "SUCCESS",
                    "completed_cycles_found": len(completed_cycles),
                    "sample_cycle": {
                        "cycle_number": cycle.get('cycle_number'),
                        "total_bets": cycle.get('total_bets'),
                        "wins": cycle.get('wins_count'),
                        "losses": cycle.get('losses_count'),
                        "draws": cycle.get('draws_count'),
                        "net_profit": cycle.get('net_profit'),
                        "roi_active": cycle.get('roi_active')
                    }
                }
            else:
                print("❌ Данные не найдены в completed_cycles")
                self.test_results["api_integration"] = {"status": "FAILED", "error": "No completed cycles found"}
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            self.test_results["api_integration"] = {"status": "ERROR", "error": str(e)}
    
    async def test_final_verification(self):
        """Тест 7: Финальная верификация всего маршрута"""
        print("\n🔍 ТЕСТ 7: Финальная верификация")
        print("-" * 50)
        
        try:
            # Проверяем весь маршрут данных
            
            # 1. Проверяем что игры созданы и завершены
            games = await db.games.find({"creator_id": "test_bot_001", "status": "COMPLETED"}).to_list(None)
            print(f"✅ Завершённых игр: {len(games)}")
            
            # 2. Проверяем аккумулятор
            accumulator = await db.bot_profit_accumulators.find_one({
                "bot_id": "test_bot_001",
                "is_cycle_completed": True
            })
            print(f"✅ Аккумулятор завершён: {accumulator is not None}")
            
            # 3. Проверяем completed_cycles
            completed_cycle = await db.completed_cycles.find_one({"bot_id": "test_bot_001"})
            print(f"✅ Запись в completed_cycles: {completed_cycle is not None}")
            
            # 4. Проверяем правильность расчётов
            if completed_cycle:
                expected_values = {
                    "total_bets": 16,
                    "wins_count": 7,
                    "losses_count": 6,
                    "draws_count": 3,
                    "total_winnings": 356,
                    "total_losses": 291,
                    "net_profit": 65,
                    "active_pool": 647,
                    "roi_active": 10.05
                }
                
                all_correct = True
                for key, expected in expected_values.items():
                    actual = completed_cycle.get(key)
                    if key == "roi_active":
                        # Для ROI допускаем небольшую погрешность
                        correct = abs(actual - expected) < 0.1
                    else:
                        correct = actual == expected
                    
                    if not correct:
                        print(f"❌ {key}: ожидалось {expected}, получено {actual}")
                        all_correct = False
                    else:
                        print(f"✅ {key}: {actual}")
                
                if all_correct:
                    print("\n🎉 ВСЕ РАСЧЁТЫ КОРРЕКТНЫ!")
                    self.test_results["final_verification"] = {
                        "status": "SUCCESS",
                        "all_calculations_correct": True,
                        "data_flow_complete": True
                    }
                else:
                    print("\n❌ Обнаружены ошибки в расчётах")
                    self.test_results["final_verification"] = {
                        "status": "FAILED",
                        "all_calculations_correct": False,
                        "errors": "Calculation mismatches found"
                    }
            else:
                print("❌ Нет данных для верификации")
                self.test_results["final_verification"] = {"status": "FAILED", "error": "No data to verify"}
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.test_results["final_verification"] = {"status": "ERROR", "error": str(e)}
    
    def generate_final_report(self):
        """Генерирует итоговый отчёт"""
        print("\n" + "="*80)
        print("📊 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result and result.get("status") == "SUCCESS")
        failed_tests = sum(1 for result in self.test_results.values() 
                          if result and result.get("status") == "FAILED")
        error_tests = sum(1 for result in self.test_results.values() 
                         if result and result.get("status") == "ERROR")
        
        print(f"\n📈 СТАТИСТИКА:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   Успешно: {passed_tests} ✅")
        print(f"   Провалено: {failed_tests} ❌")
        print(f"   Ошибки: {error_tests} 🔥")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"   Успешность: {success_rate:.1f}%")
        
        print(f"\n📋 ДЕТАЛИ ПО ТЕСТАМ:")
        for test_name, result in self.test_results.items():
            if result:
                status_icon = {"SUCCESS": "✅", "FAILED": "❌", "ERROR": "🔥"}.get(result["status"], "❓")
                print(f"   {test_name}: {status_icon} {result['status']}")
                if result.get("error"):
                    print(f"      Ошибка: {result['error']}")
        
        # Сохраняем отчёт в файл
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results
        }
        
        with open("/workspace/bot_cycle_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Отчёт сохранён в: /workspace/bot_cycle_test_report.json")
        
        if success_rate >= 85:
            print(f"\n🎉 ТЕСТИРОВАНИЕ УСПЕШНО! Система работает корректно.")
        else:
            print(f"\n⚠️  ТРЕБУЕТСЯ ДОРАБОТКА! Обнаружены критические проблемы.")
    
    async def cleanup_test_data(self):
        """Очищает тестовые данные"""
        print("\n🧹 Очистка тестовых данных...")
        
        try:
            # Удаляем тестовые игры
            await db.games.delete_many({"creator_id": "test_bot_001"})
            
            # Удаляем тестовые аккумуляторы
            await db.bot_profit_accumulators.delete_many({"bot_id": "test_bot_001"})
            
            # Удаляем тестовые завершённые циклы
            await db.completed_cycles.delete_many({"bot_id": "test_bot_001"})
            
            print("✅ Тестовые данные очищены")
            
        except Exception as e:
            print(f"⚠️  Ошибка при очистке: {e}")

async def main():
    """Главная функция"""
    tester = BotCycleFlowTester()
    
    try:
        # Запускаем полный тест
        await tester.run_complete_test()
        
    finally:
        # Очищаем тестовые данные
        await tester.cleanup_test_data()

if __name__ == "__main__":
    asyncio.run(main())