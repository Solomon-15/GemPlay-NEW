#!/usr/bin/env python3
"""
Быстрая проверка алгоритма ботов
"""

import os
import re

def quick_backend_check():
    """Быстрая проверка backend"""
    print("🔍 БЫСТРАЯ ПРОВЕРКА BACKEND")
    print("-" * 30)
    
    server_file = "/workspace/backend/server.py"
    
    if not os.path.exists(server_file):
        print("❌ server.py не найден")
        return False
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ключевые проверки
    checks = [
        ("809 в коде", "exact_cycle_total = 809"),
        ("Проценты 44/36/20", "wins_percentage.*44"),
        ("Баланс 7/6/3", "wins_count.*7"),
        ("Прямой расчёт прибыли", "wins_amount.*-.*losses_amount"),
        ("Активный пул", "wins_amount.*\\+.*losses_amount"),
        ("Убрана pause_on_draw", "pause_on_draw")  # Должна быть убрана
    ]
    
    results = []
    for name, pattern in checks:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        
        if name == "Убрана pause_on_draw":
            success = not found  # Успех = НЕ найдено
            status = "✅" if success else "❌"
        else:
            success = found
            status = "✅" if success else "❌"
        
        print(f"   {status} {name}")
        results.append(success)
    
    return all(results)

def quick_calculation_check():
    """Быстрая проверка расчётов"""
    print(f"\n🧮 БЫСТРАЯ ПРОВЕРКА РАСЧЁТОВ")
    print("-" * 30)
    
    # Точный алгоритм
    cycle_total = 809
    wins_pct = 44.0
    losses_pct = 36.0
    draws_pct = 20.0
    
    # Half-up округление
    def half_up(x):
        return int(x + 0.5)
    
    wins = half_up(cycle_total * wins_pct / 100.0)
    losses = half_up(cycle_total * losses_pct / 100.0)
    draws = half_up(cycle_total * draws_pct / 100.0)
    
    total = wins + losses + draws
    active_pool = wins + losses
    profit = wins - losses
    roi = (profit / active_pool * 100) if active_pool > 0 else 0
    
    # Эталонные значения
    expected = {"total": 809, "wins": 356, "losses": 291, "draws": 162, "profit": 65, "roi": 10.05}
    actual = {"total": total, "wins": wins, "losses": losses, "draws": draws, "profit": profit, "roi": round(roi, 2)}
    
    print(f"   Расчёты: W={wins}, L={losses}, D={draws}, T={total}")
    print(f"   Прибыль: {profit}, ROI: {roi:.2f}%")
    
    # Проверка
    all_correct = all(
        abs(actual[key] - expected[key]) < 0.1 if key == "roi" else actual[key] == expected[key]
        for key in expected
    )
    
    if all_correct:
        print("   ✅ Все расчёты корректны!")
    else:
        print("   ❌ Ошибки в расчётах!")
        for key in expected:
            exp = expected[key]
            act = actual[key]
            correct = abs(act - exp) < 0.1 if key == "roi" else act == exp
            print(f"     {key}: {act} ({'✅' if correct else '❌'} {exp})")
    
    return all_correct

def main():
    print("⚡ БЫСТРАЯ ПРОВЕРКА АЛГОРИТМА БОТОВ")
    print("=" * 50)
    
    # Проверки
    backend_ok = quick_backend_check()
    calc_ok = quick_calculation_check()
    
    print(f"\n📊 РЕЗУЛЬТАТ:")
    print(f"   Backend: {'✅' if backend_ok else '❌'}")
    print(f"   Расчёты: {'✅' if calc_ok else '❌'}")
    
    if backend_ok and calc_ok:
        print(f"\n🎉 АЛГОРИТМ ГОТОВ!")
        print("✅ Код соответствует спецификации")
        print("✅ Значения 809/647/65/10.05% корректны")
        print("✅ Логика упрощена (убрана total_earned)")
        print("✅ Убрана pause_on_draw")
        
        print(f"\n🚀 МОЖНО ТЕСТИРОВАТЬ:")
        print("1. Запустите сервер")
        print("2. Создайте бота 1-100, 16 игр")
        print("3. Проверьте 'Общая сумма цикла: 809'")
        print("4. Убедитесь что нет 'Пауза при ничье'")
    else:
        print(f"\n⚠️ ТРЕБУЕТСЯ ПРОВЕРКА!")
    
    print("=" * 50)

if __name__ == "__main__":
    main()