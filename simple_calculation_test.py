#!/usr/bin/env python3
"""
Простой тест проверки логики расчётов ботов
"""

import math

def half_up_round(x):
    """Округление half-up: ≥0.5 вверх, <0.5 вниз"""
    return int(x + 0.5) if x >= 0 else int(x - 0.5)

def test_calculation_logic():
    """Тестирует логику расчётов"""
    print("🧪 ТЕСТ ЛОГИКИ РАСЧЁТОВ БОТОВ")
    print("=" * 50)
    
    # Эталонные параметры
    exact_cycle_total = 809
    wins_percentage = 44.0
    losses_percentage = 36.0
    draws_percentage = 20.0
    
    print(f"📊 Входные параметры:")
    print(f"   Общая сумма цикла: {exact_cycle_total}")
    print(f"   Проценты: W={wins_percentage}%, L={losses_percentage}%, D={draws_percentage}%")
    
    # 1. Тест расчёта сырых значений
    print(f"\n🔢 ШАГ 1: Расчёт сырых значений")
    raw_w = exact_cycle_total * (wins_percentage / 100.0)
    raw_l = exact_cycle_total * (losses_percentage / 100.0)
    raw_d = exact_cycle_total * (draws_percentage / 100.0)
    
    print(f"   W: {exact_cycle_total} × {wins_percentage/100} = {raw_w:.2f}")
    print(f"   L: {exact_cycle_total} × {losses_percentage/100} = {raw_l:.2f}")
    print(f"   D: {exact_cycle_total} × {draws_percentage/100} = {raw_d:.2f}")
    
    # 2. Тест округления half-up
    print(f"\n📐 ШАГ 2: Округление half-up")
    wins_sum = half_up_round(raw_w)
    losses_sum = half_up_round(raw_l)
    draws_sum = half_up_round(raw_d)
    
    print(f"   W: {raw_w:.2f} → дробная часть {raw_w - math.floor(raw_w):.2f} → {wins_sum}")
    print(f"   L: {raw_l:.2f} → дробная часть {raw_l - math.floor(raw_l):.2f} → {losses_sum}")
    print(f"   D: {raw_d:.2f} → дробная часть {raw_d - math.floor(raw_d):.2f} → {draws_sum}")
    
    # 3. Проверка суммы
    print(f"\n✅ ШАГ 3: Проверка суммы")
    total_sum = wins_sum + losses_sum + draws_sum
    print(f"   Сумма: {wins_sum} + {losses_sum} + {draws_sum} = {total_sum}")
    print(f"   Соответствие: {total_sum} == {exact_cycle_total} → {'✅' if total_sum == exact_cycle_total else '❌'}")
    
    # 4. Расчёт финансовых показателей
    print(f"\n💰 ШАГ 4: Финансовые показатели")
    active_pool = wins_sum + losses_sum
    profit = wins_sum - losses_sum
    roi = (profit / active_pool * 100) if active_pool > 0 else 0
    
    print(f"   Активный пул: {wins_sum} + {losses_sum} = {active_pool}")
    print(f"   Прибыль: {wins_sum} - {losses_sum} = {profit}")
    print(f"   ROI: {profit} / {active_pool} × 100 = {roi:.2f}%")
    
    # 5. Сравнение с эталонными значениями
    print(f"\n🎯 ШАГ 5: Сравнение с эталоном")
    expected = {
        "total": 809,
        "wins": 356,
        "losses": 291,
        "draws": 162,
        "active_pool": 647,
        "profit": 65,
        "roi": 10.05
    }
    
    actual = {
        "total": total_sum,
        "wins": wins_sum,
        "losses": losses_sum,
        "draws": draws_sum,
        "active_pool": active_pool,
        "profit": profit,
        "roi": round(roi, 2)
    }
    
    all_correct = True
    for key in expected:
        exp_val = expected[key]
        act_val = actual[key]
        
        if key == "roi":
            # Для ROI допускаем погрешность
            correct = abs(act_val - exp_val) < 0.1
        else:
            correct = act_val == exp_val
        
        status = "✅" if correct else "❌"
        print(f"   {key}: {act_val} (ожидалось {exp_val}) {status}")
        
        if not correct:
            all_correct = False
    
    print(f"\n🏆 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    if all_correct:
        print("✅ ВСЕ РАСЧЁТЫ КОРРЕКТНЫ! Логика работает правильно.")
        return True
    else:
        print("❌ ОБНАРУЖЕНЫ ОШИБКИ! Требуется исправление логики.")
        return False

def test_different_scenarios():
    """Тестирует различные сценарии"""
    print(f"\n🔄 ТЕСТ РАЗЛИЧНЫХ СЦЕНАРИЕВ")
    print("=" * 50)
    
    scenarios = [
        {"total": 809, "w": 44, "l": 36, "d": 20, "name": "Эталонный (1-100, 16 игр)"},
        {"total": 800, "w": 50, "l": 30, "d": 20, "name": "Альтернативный 1"},
        {"total": 1000, "w": 40, "l": 40, "d": 20, "name": "Альтернативный 2"},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Сценарий {i}: {scenario['name']}")
        total = scenario["total"]
        w_pct = scenario["w"]
        l_pct = scenario["l"]
        d_pct = scenario["d"]
        
        # Расчёт
        raw_w = total * (w_pct / 100.0)
        raw_l = total * (l_pct / 100.0)
        raw_d = total * (d_pct / 100.0)
        
        wins = half_up_round(raw_w)
        losses = half_up_round(raw_l)
        draws = half_up_round(raw_d)
        
        calc_total = wins + losses + draws
        active_pool = wins + losses
        profit = wins - losses
        roi = (profit / active_pool * 100) if active_pool > 0 else 0
        
        print(f"   Входные: {total} ({w_pct}%/{l_pct}%/{d_pct}%)")
        print(f"   Результат: W={wins}, L={losses}, D={draws}, Σ={calc_total}")
        print(f"   Финансы: активный_пул={active_pool}, прибыль={profit}, ROI={roi:.2f}%")
        print(f"   Точность: {'✅' if calc_total == total else '❌'}")

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ЛОГИКИ РАСЧЁТОВ")
    print("=" * 60)
    
    # Основной тест
    success = test_calculation_logic()
    
    # Дополнительные сценарии
    test_different_scenarios()
    
    print(f"\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Логика расчётов работает корректно.")
    else:
        print("⚠️  ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется проверка и исправление логики.")
    print("=" * 60)

if __name__ == "__main__":
    main()