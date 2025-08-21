#!/usr/bin/env python3
"""
Объяснение логики накопления прибыли: 809→874 (+65)
"""

def explain_profit_accumulation():
    print("💰 ОБЪЯСНЕНИЕ ЛОГИКИ НАКОПЛЕНИЯ ПРИБЫЛИ")
    print("🎯 Почему 809→874 (+65)?")
    print("=" * 60)
    
    # Исходные данные
    total_spent = 809  # Бот потратил на ставки
    wins_amount = 356  # Сумма выигрышных ставок
    losses_amount = 291  # Сумма проигрышных ставок  
    draws_amount = 162  # Сумма ничейных ставок
    
    print(f"📊 ИСХОДНЫЕ ДАННЫЕ:")
    print(f"   Всего потрачено ботом: ${total_spent}")
    print(f"   Выигрышные ставки: ${wins_amount}")
    print(f"   Проигрышные ставки: ${losses_amount}")
    print(f"   Ничейные ставки: ${draws_amount}")
    print(f"   Проверка: {wins_amount} + {losses_amount} + {draws_amount} = {wins_amount + losses_amount + draws_amount}")
    
    print(f"\n🎮 ЛОГИКА ВЫПЛАТ В ИГРЕ:")
    print(f"   При ПОБЕДЕ бота:")
    print(f"     - Бот получает: свою ставку + ставку противника = ставка × 2")
    print(f"     - Пример: ставка $50 → бот получает $100")
    
    print(f"   При ПОРАЖЕНИИ бота:")
    print(f"     - Бот получает: $0 (теряет свою ставку)")
    print(f"     - Пример: ставка $50 → бот получает $0")
    
    print(f"   При НИЧЬЕ:")
    print(f"     - Бот получает: свою ставку обратно = ставка × 1")
    print(f"     - Пример: ставка $50 → бот получает $50")
    
    print(f"\n💰 РАСЧЁТ TOTAL_EARNED:")
    
    # Заработано от побед (ставка × 2)
    earned_from_wins = wins_amount * 2
    print(f"   От побед: ${wins_amount} × 2 = ${earned_from_wins}")
    
    # Заработано от ничьих (ставка × 1)
    earned_from_draws = draws_amount * 1
    print(f"   От ничьих: ${draws_amount} × 1 = ${earned_from_draws}")
    
    # Заработано от поражений (ставка × 0)
    earned_from_losses = losses_amount * 0
    print(f"   От поражений: ${losses_amount} × 0 = ${earned_from_losses}")
    
    # Общее заработанное
    total_earned = earned_from_wins + earned_from_draws + earned_from_losses
    print(f"   Всего заработано: ${earned_from_wins} + ${earned_from_draws} + ${earned_from_losses} = ${total_earned}")
    
    print(f"\n📈 РАСЧЁТ ПРИБЫЛИ:")
    profit = total_earned - total_spent
    print(f"   Прибыль = Заработано - Потрачено")
    print(f"   Прибыль = ${total_earned} - ${total_spent} = ${profit}")
    
    print(f"\n🎯 ПРОВЕРКА АЛЬТЕРНАТИВНЫМ СПОСОБОМ:")
    # Альтернативный расчёт: прибыль = выигрыши - потери
    alternative_profit = wins_amount - losses_amount
    print(f"   Альтернативно: Выигрыши - Потери")
    print(f"   Альтернативно: ${wins_amount} - ${losses_amount} = ${alternative_profit}")
    
    print(f"\n✅ ПРОВЕРКА СООТВЕТСТВИЯ:")
    if profit == alternative_profit:
        print(f"   ✅ Оба способа дают одинаковый результат: ${profit}")
        print(f"   ✅ Логика накопления корректна!")
    else:
        print(f"   ❌ Расхождение: {profit} ≠ {alternative_profit}")
    
    print(f"\n🔍 ДЕТАЛЬНЫЙ РАЗБОР ПО ИГРАМ:")
    print(f"   Победы (7 игр):")
    print(f"     - Бот ставит: ${wins_amount}")
    print(f"     - Бот получает: ${wins_amount} × 2 = ${earned_from_wins}")
    print(f"     - Чистый результат: +${wins_amount}")
    
    print(f"   Поражения (6 игр):")
    print(f"     - Бот ставит: ${losses_amount}")
    print(f"     - Бот получает: $0")
    print(f"     - Чистый результат: -${losses_amount}")
    
    print(f"   Ничьи (3 игры):")
    print(f"     - Бот ставит: ${draws_amount}")
    print(f"     - Бот получает: ${draws_amount}")
    print(f"     - Чистый результат: $0 (без влияния на прибыль)")
    
    print(f"\n🎯 ИТОГОВАЯ ПРИБЫЛЬ:")
    print(f"   +${wins_amount} (от побед) - ${losses_amount} (от поражений) + $0 (от ничьих) = +${profit}")
    
    return profit == 65

def explain_why_this_logic():
    print(f"\n🤔 ПОЧЕМУ ИМЕННО ТАКАЯ ЛОГИКА?")
    print("=" * 60)
    
    reasons = [
        {
            "title": "1. Реалистичная игровая механика",
            "explanation": "В реальной игре 'камень-ножницы-бумага' победитель забирает всю сумму ставок (свою + противника)"
        },
        {
            "title": "2. Правильный учёт ничьих",
            "explanation": "При ничье игроки получают свои ставки обратно - никто не теряет деньги"
        },
        {
            "title": "3. Математическая корректность",
            "explanation": "total_earned - total_spent = (wins×2 + draws×1 + losses×0) - (wins + losses + draws)"
        },
        {
            "title": "4. Соответствие ROI расчётам",
            "explanation": "ROI считается от активного пула (без ничьих), что правильно для оценки эффективности"
        },
        {
            "title": "5. Простота аудита",
            "explanation": "Легко проверить: прибыль = сумма_выигрышей - сумма_проигрышей (ничьи не влияют)"
        }
    ]
    
    for reason in reasons:
        print(f"\n{reason['title']}:")
        print(f"   {reason['explanation']}")
    
    print(f"\n🔍 АЛЬТЕРНАТИВНЫЕ ПОДХОДЫ (НЕПРАВИЛЬНЫЕ):")
    
    wrong_approaches = [
        {
            "approach": "Считать прибыль от общей суммы",
            "formula": "profit = total_earned - 809",
            "why_wrong": "Не учитывает что ничьи возвращают ставки"
        },
        {
            "approach": "Включать ничьи в активный пул",
            "formula": "active_pool = wins + losses + draws",
            "why_wrong": "Ничьи не участвуют в создании прибыли/убытка"
        },
        {
            "approach": "Считать ROI от общей суммы",
            "formula": "roi = profit / 809 * 100",
            "why_wrong": "Искажает реальную доходность активных инвестиций"
        }
    ]
    
    for approach in wrong_approaches:
        print(f"\n❌ {approach['approach']}:")
        print(f"     Формула: {approach['formula']}")
        print(f"     Почему неправильно: {approach['why_wrong']}")

def show_step_by_step_calculation():
    print(f"\n📋 ПОШАГОВЫЙ РАСЧЁТ НАКОПЛЕНИЯ:")
    print("=" * 60)
    
    # Симуляция накопления по играм
    games = [
        {"type": "win", "amount": 51, "earned": 102},   # Пример выигрышной игры
        {"type": "loss", "amount": 48, "earned": 0},    # Пример проигрышной игры
        {"type": "draw", "amount": 54, "earned": 54},   # Пример ничейной игры
    ]
    
    running_spent = 0
    running_earned = 0
    
    print(f"   {'Игра':<6} {'Тип':<6} {'Ставка':<8} {'Получено':<10} {'Потрачено':<12} {'Заработано':<12} {'Прибыль':<10}")
    print(f"   {'-'*6} {'-'*6} {'-'*8} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")
    
    for i, game in enumerate(games, 1):
        running_spent += game["amount"]
        running_earned += game["earned"]
        profit = running_earned - running_spent
        
        print(f"   {i:<6} {game['type']:<6} ${game['amount']:<7} ${game['earned']:<9} ${running_spent:<11} ${running_earned:<11} ${profit:<9}")
    
    print(f"\n💡 ПРИНЦИП:")
    print(f"   - total_spent увеличивается на каждую ставку")
    print(f"   - total_earned увеличивается на выплату")
    print(f"   - profit = total_earned - total_spent")
    
    print(f"\n🎯 ДЛЯ ПОЛНОГО ЦИКЛА:")
    print(f"   - Потрачено: $809 (все 16 ставок)")
    print(f"   - Заработано: $874 (356×2 + 162×1 + 291×0)")
    print(f"   - Прибыль: $65 (874 - 809)")

def main():
    print("🧮 АНАЛИЗ ЛОГИКИ НАКОПЛЕНИЯ ПРИБЫЛИ")
    print("❓ Вопрос: Почему 809→874 (+65)?")
    print("=" * 60)
    
    # Основное объяснение
    is_correct = explain_profit_accumulation()
    
    # Дополнительные объяснения
    explain_why_this_logic()
    
    # Пошаговый расчёт
    show_step_by_step_calculation()
    
    print(f"\n" + "=" * 60)
    print("📊 ЗАКЛЮЧЕНИЕ")
    print("=" * 60)
    
    if is_correct:
        print("✅ ЛОГИКА НАКОПЛЕНИЯ АБСОЛЮТНО КОРРЕКТНА!")
        print(f"\n🎯 Формула: total_earned = (выигрыши × 2) + (ничьи × 1) + (поражения × 0)")
        print(f"   = (356 × 2) + (162 × 1) + (291 × 0)")
        print(f"   = 712 + 162 + 0 = 874")
        print(f"\n💰 Прибыль = 874 - 809 = 65")
        print(f"\n✨ Это стандартная игровая механика!")
    else:
        print("❌ Обнаружена ошибка в логике")
    
    print(f"\n💡 КЛЮЧЕВОЙ ПРИНЦИП:")
    print("Бот получает выплаты согласно правилам игры, а прибыль рассчитывается")
    print("как разность между полученным и потраченным. Ничьи не создают прибыли,")
    print("но и не создают убытков - они 'нейтральны' для финансового результата.")

if __name__ == "__main__":
    main()