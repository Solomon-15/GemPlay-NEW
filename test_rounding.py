#!/usr/bin/env python3
"""
Тест правильного округления для расчёта сумм по категориям
"""

def half_up_round(x):
    """Округление half-up: ≥0.5 вверх, <0.5 вниз"""
    return int(x + 0.5) if x >= 0 else int(x - 0.5)

# Тестируем для эталонных значений
exact_cycle_total = 809
wins_percentage = 44.0
losses_percentage = 36.0
draws_percentage = 20.0

# Расчёт сырых значений
raw_w = exact_cycle_total * (wins_percentage / 100.0)
raw_l = exact_cycle_total * (losses_percentage / 100.0)
raw_d = exact_cycle_total * (draws_percentage / 100.0)

print(f"Сырые значения:")
print(f"  W: {raw_w:.2f}")
print(f"  L: {raw_l:.2f}")
print(f"  D: {raw_d:.2f}")

# Округление half-up
wins_sum = half_up_round(raw_w)
losses_sum = half_up_round(raw_l)
draws_sum = half_up_round(raw_d)

print(f"\nОкругление half-up:")
print(f"  W: {raw_w:.2f} → {wins_sum}")
print(f"  L: {raw_l:.2f} → {losses_sum}")
print(f"  D: {raw_d:.2f} → {draws_sum}")

# Проверка
total = wins_sum + losses_sum + draws_sum
active_pool = wins_sum + losses_sum
profit = wins_sum - losses_sum
roi = (profit / active_pool * 100) if active_pool > 0 else 0

print(f"\nРезультат:")
print(f"  Сумма: {total} (должно быть {exact_cycle_total})")
print(f"  Активный пул: {active_pool}")
print(f"  Прибыль: {profit}")
print(f"  ROI: {roi:.2f}%")
print(f"  Корректность: {'✅' if total == exact_cycle_total else '❌'}")