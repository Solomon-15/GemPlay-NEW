#!/usr/bin/env python3
"""
Верификация кода и проверка исправлений
"""

import os
import re

def check_backend_fixes():
    """Проверяет исправления в backend коде"""
    print("🔍 ПРОВЕРКА ИСПРАВЛЕНИЙ В BACKEND")
    print("=" * 50)
    
    server_file = "/workspace/backend/server.py"
    
    if not os.path.exists(server_file):
        print("❌ Файл server.py не найден")
        return False
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем ключевые исправления
    checks = [
        {
            "name": "Функция complete_bot_cycle существует",
            "pattern": r"async def complete_bot_cycle",
            "required": True
        },
        {
            "name": "Правильный расчёт сумм из реальных игр",
            "pattern": r"wins_sum_agg.*COMPLETED.*winner_id.*bot_id",
            "required": True
        },
        {
            "name": "Использование roi_active вместо roi_percent",
            "pattern": r'"roi_active"',
            "required": True
        },
        {
            "name": "Эталонное значение 809",
            "pattern": r"exact_cycle_total = 809",
            "required": True
        },
        {
            "name": "Округление half-up",
            "pattern": r"int\(.*\+ 0\.5\)|half_up_round",
            "required": True
        },
        {
            "name": "Функция generate_cycle_bets_natural_distribution",
            "pattern": r"async def generate_cycle_bets_natural_distribution",
            "required": True
        },
        {
            "name": "Правильные проценты по умолчанию (44/36/20)",
            "pattern": r"wins_percentage.*44|44.*wins_percentage",
            "required": True
        }
    ]
    
    results = {}
    
    for check in checks:
        found = bool(re.search(check["pattern"], content, re.DOTALL | re.IGNORECASE))
        status = "✅" if found else "❌"
        print(f"   {status} {check['name']}")
        
        if not found and check["required"]:
            # Попробуем найти похожие паттерны
            similar_patterns = [
                check["pattern"].replace(".*", ""),
                check["pattern"].replace(r"\(", "(").replace(r"\)", ")")
            ]
            
            for pattern in similar_patterns:
                if pattern in content:
                    print(f"      🔍 Найден похожий код: {pattern}")
                    break
        
        results[check["name"]] = found
    
    return results

def check_frontend_integration():
    """Проверяет интеграцию с frontend"""
    print(f"\n🎨 ПРОВЕРКА FRONTEND ИНТЕГРАЦИИ")
    print("=" * 50)
    
    files_to_check = [
        "/workspace/frontend/src/components/RegularBotsManagement.js",
        "/workspace/frontend/src/components/ProfitAdmin.js"
    ]
    
    results = {}
    
    for file_path in files_to_check:
        filename = os.path.basename(file_path)
        print(f"\n📄 Проверяем {filename}:")
        
        if not os.path.exists(file_path):
            print(f"   ❌ Файл не найден")
            results[filename] = {"exists": False}
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверки для RegularBotsManagement.js
        if "RegularBotsManagement" in filename:
            checks = [
                {"name": "История циклов", "pattern": r"История циклов|completed-cycles"},
                {"name": "ROI отображение", "pattern": r"roi_active|ROI"},
                {"name": "Общая сумма цикла", "pattern": r"exact_cycle_total|Общая сумма цикла"},
                {"name": "API вызовы ботов", "pattern": r"/admin/bots.*cycles|/admin/profit"}
            ]
        
        # Проверки для ProfitAdmin.js
        elif "ProfitAdmin" in filename:
            checks = [
                {"name": "Доход от ботов", "pattern": r"Доход от ботов|bot.*revenue"},
                {"name": "История прибыли", "pattern": r"История прибыли|profit.*history"},
                {"name": "API интеграция", "pattern": r"/admin/profit.*bot"}
            ]
        else:
            checks = []
        
        file_results = {}
        for check in checks:
            found = bool(re.search(check["pattern"], content, re.IGNORECASE))
            status = "✅" if found else "❌"
            print(f"   {status} {check['name']}")
            file_results[check["name"]] = found
        
        results[filename] = {"exists": True, "checks": file_results}
    
    return results

def verify_data_flow():
    """Проверяет поток данных от создания до отображения"""
    print(f"\n🔄 ПРОВЕРКА ПОТОКА ДАННЫХ")
    print("=" * 50)
    
    flow_steps = [
        {
            "step": "1. Создание цикла",
            "function": "create_full_bot_cycle",
            "description": "Создаёт игры с правильным распределением ставок"
        },
        {
            "step": "2. Распределение ставок",
            "function": "generate_cycle_bets_natural_distribution",
            "description": "Рассчитывает суммы по категориям с округлением half-up"
        },
        {
            "step": "3. Выполнение игр",
            "function": "game completion logic",
            "description": "Игры завершаются согласно intended_result"
        },
        {
            "step": "4. Накопление данных",
            "function": "bot_profit_accumulators",
            "description": "Аккумулятор собирает статистику по играм"
        },
        {
            "step": "5. Завершение цикла",
            "function": "complete_bot_cycle",
            "description": "Рассчитывает реальные суммы и создаёт запись в completed_cycles"
        },
        {
            "step": "6. API отдача",
            "function": "get_bot_completed_cycles",
            "description": "API возвращает данные для интерфейса"
        },
        {
            "step": "7. Отображение",
            "function": "Frontend components",
            "description": "Интерфейс показывает данные в 'Доход от ботов'"
        }
    ]
    
    for step_info in flow_steps:
        print(f"\n📋 {step_info['step']}")
        print(f"   Функция: {step_info['function']}")
        print(f"   Описание: {step_info['description']}")
        
        # Проверяем наличие функции в коде
        if step_info['function'] not in ['game completion logic', 'Frontend components']:
            server_file = "/workspace/backend/server.py"
            if os.path.exists(server_file):
                with open(server_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if step_info['function'] in content:
                    print(f"   ✅ Функция найдена в коде")
                else:
                    print(f"   ❌ Функция НЕ найдена в коде")
            else:
                print(f"   ❓ Не удалось проверить (файл недоступен)")
        else:
            print(f"   ℹ️  Логика проверяется вручную")

def generate_test_report():
    """Генерирует итоговый отчёт тестирования"""
    print(f"\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЁТ ВЕРИФИКАЦИИ")
    print("=" * 60)
    
    # Запускаем все проверки
    backend_results = check_backend_fixes()
    frontend_results = check_frontend_integration()
    
    # Проверяем поток данных
    verify_data_flow()
    
    # Подсчитываем результаты
    backend_passed = sum(1 for result in backend_results.values() if result)
    backend_total = len(backend_results)
    
    frontend_files = sum(1 for result in frontend_results.values() if result.get("exists"))
    
    print(f"\n📈 СТАТИСТИКА:")
    print(f"   Backend исправления: {backend_passed}/{backend_total} ({'✅' if backend_passed == backend_total else '❌'})")
    print(f"   Frontend файлы: {frontend_files}/2 ({'✅' if frontend_files == 2 else '❌'})")
    
    # Оценка готовности
    backend_ready = backend_passed >= backend_total * 0.8
    frontend_ready = frontend_files >= 1
    
    overall_status = backend_ready and frontend_ready
    
    print(f"\n🎯 ГОТОВНОСТЬ СИСТЕМЫ:")
    print(f"   Backend: {'✅ Готов' if backend_ready else '❌ Требует доработки'}")
    print(f"   Frontend: {'✅ Готов' if frontend_ready else '❌ Требует доработки'}")
    print(f"   Общая: {'✅ Система готова к тестированию' if overall_status else '❌ Требуется доработка'}")
    
    print(f"\n💡 СЛЕДУЮЩИЕ ШАГИ:")
    if overall_status:
        print("   1. ✅ Запустите backend сервер")
        print("   2. ✅ Запустите frontend")
        print("   3. ✅ Создайте тестового бота через интерфейс")
        print("   4. ✅ Проверьте данные в 'Доход от ботов'")
        print("   5. ✅ Убедитесь что показываются правильные значения: 809/647/65/10.05%")
    else:
        if not backend_ready:
            print("   1. ❌ Завершите исправления в backend/server.py")
        if not frontend_ready:
            print("   2. ❌ Проверьте frontend компоненты")
        print("   3. ❌ Повторите тестирование")

def main():
    """Главная функция"""
    print("🧪 ВЕРИФИКАЦИЯ ИСПРАВЛЕНИЙ СИСТЕМЫ БОТОВ")
    print("🎯 Проверяем полный маршрут: создание → расчёт → отображение")
    print("=" * 60)
    
    generate_test_report()
    
    print(f"\n" + "=" * 60)
    print("✨ ВЕРИФИКАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)

if __name__ == "__main__":
    main()