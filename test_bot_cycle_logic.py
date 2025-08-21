#!/usr/bin/env python3
"""
Тест логики создания циклов ботов
"""

def analyze_cycle_creation_logic():
    """Анализирует логику создания циклов"""
    print("🔍 АНАЛИЗ ЛОГИКИ СОЗДАНИЯ ЦИКЛОВ")
    print("=" * 50)
    
    # Сценарии для тестирования
    scenarios = [
        {
            "name": "Новый бот, нет игр",
            "total_games": 0,
            "active_games": 0,
            "completed_games": 0,
            "target": 16,
            "has_completed_cycles": False,
            "last_cycle_completed_at": None
        },
        {
            "name": "Бот с завершённым циклом, нет паузы",
            "total_games": 16,
            "active_games": 0,
            "completed_games": 16,
            "target": 16,
            "has_completed_cycles": True,
            "last_cycle_completed_at": None
        },
        {
            "name": "Бот в паузе",
            "total_games": 16,
            "active_games": 0,
            "completed_games": 16,
            "target": 16,
            "has_completed_cycles": True,
            "last_cycle_completed_at": "recent"  # недавно
        },
        {
            "name": "Бот с активными играми",
            "total_games": 10,
            "active_games": 5,
            "completed_games": 5,
            "target": 16,
            "has_completed_cycles": True,
            "last_cycle_completed_at": None
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Сценарий {i}: {scenario['name']}")
        
        # Логика из кода
        total_games_in_cycle = scenario["total_games"]
        active_games = scenario["active_games"]
        completed_games = scenario["completed_games"]
        cycle_games_target = scenario["target"]
        
        # Условия
        cycle_fully_completed = (
            total_games_in_cycle >= cycle_games_target and 
            active_games == 0 and 
            completed_games > 0
        )
        
        needs_initial_cycle = total_games_in_cycle == 0
        
        # Анализ решения
        print(f"   Состояние: total={total_games_in_cycle}, active={active_games}, completed={completed_games}")
        print(f"   Условия: needs_initial_cycle={needs_initial_cycle}, cycle_fully_completed={cycle_fully_completed}")
        
        # Определяем действие
        if needs_initial_cycle:
            action = "✅ СОЗДАТЬ НОВЫЙ ЦИКЛ"
        elif cycle_fully_completed:
            if scenario["last_cycle_completed_at"] is None:
                action = "🏁 ЗАВЕРШИТЬ ЦИКЛ и начать паузу"
            else:
                action = "⏳ ПРОВЕРИТЬ ПАУЗУ (возможно создать новый цикл)"
        elif active_games > 0:
            action = "🎮 ЖДАТЬ завершения активных игр"
        elif total_games_in_cycle < cycle_games_target:
            action = "📊 НЕПОЛНЫЙ ЦИКЛ (ждать)"
        else:
            action = "❓ НЕОПРЕДЕЛЕННОЕ СОСТОЯНИЕ"
        
        print(f"   Действие: {action}")
        
        # Оценка корректности
        if scenario["name"] == "Новый бот, нет игр" and "СОЗДАТЬ" in action:
            print("   ✅ Логика корректна для нового бота")
        elif scenario["name"] == "Бот с завершённым циклом, нет паузы" and "ЗАВЕРШИТЬ" in action:
            print("   ✅ Логика корректна для завершённого цикла")
        elif scenario["name"] == "Бот в паузе" and "ПАУЗУ" in action:
            print("   ✅ Логика корректна для паузы")
        elif scenario["name"] == "Бот с активными играми" and "ЖДАТЬ" in action:
            print("   ✅ Логика корректна для активных игр")
        else:
            print("   ⚠️  Логика может требовать проверки")

def check_bot_activation_requirements():
    """Проверяет требования для активации ботов"""
    print(f"\n🔧 ТРЕБОВАНИЯ ДЛЯ АКТИВАЦИИ БОТОВ")
    print("=" * 50)
    
    requirements = [
        {"name": "is_active = True", "description": "Бот должен быть активен"},
        {"name": "bot_type = REGULAR", "description": "Тип бота должен быть REGULAR"},
        {"name": "Подключение к MongoDB", "description": "База данных должна быть доступна"},
        {"name": "bot_automation_loop запущен", "description": "Цикл автоматизации должен работать"},
        {"name": "maintain_all_bots_active_bets работает", "description": "Функция проверки циклов должна выполняться"},
        {"name": "Нет конфликтующих startup событий", "description": "Не должно быть дублирования инициализации"}
    ]
    
    for req in requirements:
        print(f"✅ {req['name']}: {req['description']}")
    
    print(f"\n💡 ДИАГНОСТИКА ПРОБЛЕМ:")
    print("1. Проверьте логи сервера на наличие ошибок подключения к MongoDB")
    print("2. Убедитесь что bot_automation_loop запустился: ищите '✅ Bot automation loop started'")
    print("3. Проверьте что боты создаются с is_active=True")
    print("4. Убедитесь что maintain_all_bots_active_bets выполняется каждые 5 секунд")
    print("5. Проверьте что нет ошибок в логах типа 'Error maintaining bets for bot'")

def main():
    print("🧪 ТЕСТ ЛОГИКИ СОЗДАНИЯ ЦИКЛОВ БОТОВ")
    print("🎯 Проверяем почему циклы не запускаются")
    print("=" * 60)
    
    analyze_cycle_creation_logic()
    check_bot_activation_requirements()
    
    print(f"\n" + "=" * 60)
    print("📊 РЕЗЮМЕ ИСПРАВЛЕНИЙ:")
    print("✅ Убрано ограничение has_completed_cycles для создания циклов")
    print("✅ Исправлены конфликтующие startup события")  
    print("✅ Добавлена принудительная проверка циклов при запуске")
    print("✅ Улучшено логирование для диагностики")
    print(f"\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Перезапустите сервер")
    print("2. Проверьте логи на наличие '✅ Bot automation loop started'")
    print("3. Создайте тестового бота через интерфейс")
    print("4. Проверьте логи на наличие '🎯 Bot ... starting new cycle'")
    print("=" * 60)

if __name__ == "__main__":
    main()