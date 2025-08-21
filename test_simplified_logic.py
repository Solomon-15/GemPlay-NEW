#!/usr/bin/env python3
"""
Тест упрощённой логики расчёта прибыли
"""

def test_simplified_profit_calculation():
    print("🎯 ТЕСТ УПРОЩЁННОЙ ЛОГИКИ РАСЧЁТА ПРИБЫЛИ")
    print("=" * 60)
    
    # Исходные данные
    wins_amount = 356    # Сумма выигрышных ставок
    losses_amount = 291  # Сумма проигрышных ставок
    draws_amount = 162   # Сумма ничейных ставок
    
    print(f"📊 ИСХОДНЫЕ ДАННЫЕ:")
    print(f"   Выигрышные ставки: ${wins_amount}")
    print(f"   Проигрышные ставки: ${losses_amount}")
    print(f"   Ничейные ставки: ${draws_amount}")
    
    # ОСТАВЛЯЕМ total_spent для совместимости
    total_spent = wins_amount + losses_amount + draws_amount
    print(f"   total_spent: ${total_spent} ✅ (ОСТАВЛЯЕМ)")
    
    print(f"\n❌ СТАРАЯ СЛОЖНАЯ ЛОГИКА (УДАЛЯЕМ):")
    print(f"   total_earned = (wins×2) + (draws×1) + (losses×0)")
    print(f"   total_earned = ({wins_amount}×2) + ({draws_amount}×1) + ({losses_amount}×0)")
    total_earned_old = (wins_amount * 2) + (draws_amount * 1) + (losses_amount * 0)
    print(f"   total_earned = {total_earned_old}")
    profit_old_way = total_earned_old - total_spent
    print(f"   profit = {total_earned_old} - {total_spent} = {profit_old_way}")
    print(f"   ❌ СЛОЖНО И ЗАПУТАННО!")
    
    print(f"\n✅ НОВАЯ ПРОСТАЯ ЛОГИКА (ИСПОЛЬЗУЕМ):")
    print(f"   profit = wins_amount - losses_amount")
    print(f"   profit = ${wins_amount} - ${losses_amount} = ${wins_amount - losses_amount}")
    profit_new_way = wins_amount - losses_amount
    print(f"   ✅ ПРОСТО И ПОНЯТНО!")
    
    print(f"\n🔍 ПРОВЕРКА ЭКВИВАЛЕНТНОСТИ:")
    print(f"   Старый способ: ${profit_old_way}")
    print(f"   Новый способ: ${profit_new_way}")
    print(f"   Результат одинаковый: {'✅' if profit_old_way == profit_new_way else '❌'}")
    
    print(f"\n📈 ФИНАЛЬНЫЕ РАСЧЁТЫ:")
    active_pool = wins_amount + losses_amount
    roi = (profit_new_way / active_pool * 100) if active_pool > 0 else 0
    
    print(f"   Активный пул: ${wins_amount} + ${losses_amount} = ${active_pool}")
    print(f"   Прибыль: ${profit_new_way}")
    print(f"   ROI: ${profit_new_way} / ${active_pool} × 100 = {roi:.2f}%")
    
    print(f"\n🎯 НОВАЯ СТРУКТУРА АККУМУЛЯТОРА:")
    new_accumulator = {
        "total_spent": total_spent,        # ✅ ОСТАВЛЯЕМ (нужна в проекте)
        # "total_earned": "УДАЛЕНО",       # ❌ УБИРАЕМ (сложная логика)
        "wins_amount": wins_amount,        # ✅ ДОБАВЛЯЕМ (прямой доступ)
        "losses_amount": losses_amount,    # ✅ ДОБАВЛЯЕМ (прямой доступ)
        "draws_amount": draws_amount,      # ✅ ДОБАВЛЯЕМ (прямой доступ)
        "games_won": 7,
        "games_lost": 6,
        "games_drawn": 3
    }
    
    for field, value in new_accumulator.items():
        if isinstance(value, str):
            print(f"   {field}: {value}")
        else:
            print(f"   {field}: {value}")
    
    print(f"\n💡 ПРЕИМУЩЕСТВА НОВОЙ ЛОГИКИ:")
    advantages = [
        "Прямой расчёт: profit = wins_amount - losses_amount",
        "Сохранён total_spent для совместимости с проектом",
        "Убрана сложная логика с total_earned",
        "Ничьи явно отделены и не влияют на прибыль",
        "Код стал проще и понятнее"
    ]
    
    for i, advantage in enumerate(advantages, 1):
        print(f"   {i}. {advantage}")
    
    return profit_new_way == 65

def main():
    print("🔄 УПРОЩЕНИЕ ЛОГИКИ РАСЧЁТА ПРИБЫЛИ")
    print("✅ Оставляем: total_spent = 809")
    print("❌ Убираем: total_earned = 874")  
    print("✅ Используем: profit = wins_amount - losses_amount = 65")
    print("=" * 60)
    
    success = test_simplified_profit_calculation()
    
    print(f"\n" + "=" * 60)
    print("📊 ЗАКЛЮЧЕНИЕ")
    print("=" * 60)
    
    if success:
        print("✅ УПРОЩЁННАЯ ЛОГИКА АБСОЛЮТНО КОРРЕКТНА!")
        print(f"\n🎯 ИТОГОВАЯ ФОРМУЛА:")
        print(f"   total_spent = 809 (общая сумма ставок) ✅")
        print(f"   profit = 356 - 291 = 65 (прямой расчёт) ✅")
        print(f"   roi = 65 / 647 × 100 = 10.05% ✅")
        print(f"\n✨ НИКАКИХ СЛОЖНЫХ РАСЧЁТОВ С EARNED!")
    else:
        print("❌ Ошибка в упрощённой логике")
    
    print(f"\n💡 КЛЮЧЕВОЙ ПРИНЦИП:")
    print("total_spent нужна для проекта, но прибыль рассчитывается ПРЯМО:")
    print("Выигрыши - Потери. Ничьи не влияют на прибыль!")

if __name__ == "__main__":
    main()