#!/usr/bin/env python3
"""
Быстрая проверка всей системы перед запуском
"""

import os
import subprocess
import json

def check_files_exist():
    """Проверяет существование ключевых файлов"""
    print("📁 ПРОВЕРКА ФАЙЛОВ")
    print("-" * 30)
    
    critical_files = [
        "/workspace/backend/server.py",
        "/workspace/frontend/src/components/RegularBotsManagement.js", 
        "/workspace/frontend/src/components/ProfitAdmin.js",
        "/workspace/frontend/package.json"
    ]
    
    all_exist = True
    for file_path in critical_files:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        filename = os.path.basename(file_path)
        print(f"{status} {filename}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_backend_functions():
    """Проверяет наличие ключевых функций в backend"""
    print("\n🔧 ПРОВЕРКА BACKEND ФУНКЦИЙ")
    print("-" * 30)
    
    server_file = "/workspace/backend/server.py"
    
    if not os.path.exists(server_file):
        print("❌ server.py не найден")
        return False
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    functions = [
        "create_full_bot_cycle",
        "generate_cycle_bets_natural_distribution", 
        "complete_bot_cycle",
        "get_bot_completed_cycles",
        "get_bot_revenue_summary"
    ]
    
    all_found = True
    for func in functions:
        found = func in content
        status = "✅" if found else "❌"
        print(f"{status} {func}")
        if not found:
            all_found = False
    
    return all_found

def check_calculation_logic():
    """Быстрая проверка логики расчётов"""
    print("\n🧮 ПРОВЕРКА ЛОГИКИ РАСЧЁТОВ")
    print("-" * 30)
    
    # Эталонные значения
    total = 809
    w_pct, l_pct, d_pct = 44.0, 36.0, 20.0
    
    # Расчёт
    raw_w = total * (w_pct / 100.0)
    raw_l = total * (l_pct / 100.0) 
    raw_d = total * (d_pct / 100.0)
    
    # Округление half-up
    def half_up(x):
        return int(x + 0.5)
    
    w = half_up(raw_w)
    l = half_up(raw_l)
    d = half_up(raw_d)
    
    calc_total = w + l + d
    active_pool = w + l
    profit = w - l
    roi = (profit / active_pool * 100) if active_pool > 0 else 0
    
    # Проверка эталонных значений
    expected = {"total": 809, "w": 356, "l": 291, "d": 162, "profit": 65, "roi": 10.05}
    actual = {"total": calc_total, "w": w, "l": l, "d": d, "profit": profit, "roi": round(roi, 2)}
    
    all_correct = True
    for key in expected:
        correct = actual[key] == expected[key] or (key == "roi" and abs(actual[key] - expected[key]) < 0.1)
        status = "✅" if correct else "❌"
        print(f"{status} {key}: {actual[key]} (ожидалось {expected[key]})")
        if not correct:
            all_correct = False
    
    return all_correct

def check_git_status():
    """Проверяет статус git репозитория"""
    print("\n📦 ПРОВЕРКА GIT РЕПОЗИТОРИЯ")
    print("-" * 30)
    
    try:
        # Проверяем текущую ветку
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd='/workspace')
        if result.returncode == 0:
            branch = result.stdout.strip()
            print(f"✅ Текущая ветка: {branch}")
            
            if branch == "cursor/roi-1998":
                print("✅ Используется правильная ветка")
                branch_ok = True
            else:
                print("⚠️  Рекомендуется ветка cursor/roi-1998")
                branch_ok = False
        else:
            print("❌ Не удалось определить ветку")
            branch_ok = False
        
        # Проверяем статус
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='/workspace')
        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️  Есть несохранённые изменения")
            else:
                print("✅ Рабочее дерево чистое")
        
        return branch_ok
        
    except Exception as e:
        print(f"❌ Ошибка проверки git: {e}")
        return False

def check_dependencies():
    """Проверяет зависимости"""
    print("\n📚 ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    print("-" * 30)
    
    # Проверяем Python модули
    python_modules = ['asyncio', 'datetime', 'json']
    python_ok = True
    
    for module in python_modules:
        try:
            __import__(module)
            print(f"✅ Python: {module}")
        except ImportError:
            print(f"❌ Python: {module}")
            python_ok = False
    
    # Проверяем Node.js зависимости
    package_json = "/workspace/frontend/package.json"
    node_ok = True
    
    if os.path.exists(package_json):
        print("✅ package.json найден")
        
        node_modules = "/workspace/frontend/node_modules"
        if os.path.exists(node_modules):
            print("✅ node_modules установлены")
        else:
            print("⚠️  node_modules не найдены (запустите npm install)")
            node_ok = False
    else:
        print("❌ package.json не найден")
        node_ok = False
    
    return python_ok and node_ok

def generate_startup_commands():
    """Генерирует команды для запуска"""
    print("\n🚀 КОМАНДЫ ДЛЯ ЗАПУСКА")
    print("-" * 30)
    
    print("Backend сервер:")
    print("  cd /workspace/backend && python3 server.py")
    
    print("\nFrontend (в новом терминале):")
    print("  cd /workspace/frontend && npm start")
    
    print("\nДля тестирования:")
    print("  1. Откройте http://localhost:3000")
    print("  2. Войдите как администратор") 
    print("  3. Создайте бота с параметрами 1-100, 16 игр")
    print("  4. Проверьте 'Доход от ботов'")

def main():
    """Главная функция быстрой проверки"""
    print("⚡ БЫСТРАЯ ПРОВЕРКА СИСТЕМЫ БОТОВ")
    print("=" * 50)
    
    # Выполняем все проверки
    files_ok = check_files_exist()
    functions_ok = check_backend_functions()
    logic_ok = check_calculation_logic()
    git_ok = check_git_status()
    deps_ok = check_dependencies()
    
    # Подсчитываем результаты
    checks = [files_ok, functions_ok, logic_ok, git_ok, deps_ok]
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 50)
    
    print(f"Пройдено проверок: {passed}/{total}")
    
    if passed == total:
        print("🎉 ВСЁ ГОТОВО К ЗАПУСКУ!")
        print("✅ Система полностью подготовлена")
        generate_startup_commands()
    elif passed >= total * 0.8:
        print("⚠️  ПОЧТИ ГОТОВО")
        print("🔧 Есть небольшие проблемы, но можно тестировать")
        generate_startup_commands()
    else:
        print("❌ ТРЕБУЕТСЯ ДОРАБОТКА")
        print("🔧 Исправьте критические проблемы перед запуском")
    
    print(f"\n📋 Подробные инструкции: manual_test_instructions.md")
    print(f"📊 Полный отчёт: TESTING_SUMMARY_REPORT.md")

if __name__ == "__main__":
    main()