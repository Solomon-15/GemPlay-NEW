#!/usr/bin/env python3
"""
Тестирование логики уведомлений при входе на ставку
"""

import sys
import os

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_gem_combination_function():
    """Тест функции проверки комбинации гемов"""
    print("\n🧪 TEST 1: Проверка функции check_gem_combination_possible")
    print("="*50)
    
    try:
        from server import check_gem_combination_possible
        import asyncio
        
        # Тестовые случаи
        test_cases = [
            {
                "name": "Exact match",
                "gems": [{"type": "Ruby", "available_quantity": 2, "price": 5.0}],
                "target": 10.0,
                "expected": True
            },
            {
                "name": "Multiple gem types - possible",
                "gems": [
                    {"type": "Ruby", "available_quantity": 2, "price": 5.0},
                    {"type": "Emerald", "available_quantity": 3, "price": 2.0}
                ],
                "target": 12.0,  # 2*5 + 1*2 = 12
                "expected": True
            },
            {
                "name": "Multiple gem types - impossible",
                "gems": [
                    {"type": "Ruby", "available_quantity": 2, "price": 5.0},
                    {"type": "Emerald", "available_quantity": 3, "price": 2.0}
                ],
                "target": 13.0,  # Can't make 13 from 5 and 2
                "expected": False
            },
            {
                "name": "Insufficient total value",
                "gems": [{"type": "Ruby", "available_quantity": 1, "price": 5.0}],
                "target": 10.0,
                "expected": False
            },
            {
                "name": "Zero target",
                "gems": [{"type": "Ruby", "available_quantity": 1, "price": 5.0}],
                "target": 0.0,
                "expected": True
            },
            {
                "name": "Complex combination",
                "gems": [
                    {"type": "Diamond", "available_quantity": 3, "price": 10.0},
                    {"type": "Ruby", "available_quantity": 5, "price": 5.0},
                    {"type": "Sapphire", "available_quantity": 2, "price": 3.0}
                ],
                "target": 28.0,  # 2*10 + 1*5 + 1*3 = 28
                "expected": True
            }
        ]
        
        print("📋 Тестирование различных комбинаций:")
        for test in test_cases:
            result = asyncio.run(check_gem_combination_possible(test["gems"], test["target"]))
            status = "✅" if result == test["expected"] else "❌"
            print(f"{status} {test['name']}: target=${test['target']}, result={result}, expected={test['expected']}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")


def test_error_messages():
    """Проверка сообщений об ошибках"""
    print("\n🧪 TEST 2: Проверка сообщений об ошибках")
    print("="*50)
    
    backend_file = os.path.join(os.path.dirname(__file__), 'backend', 'server.py')
    
    try:
        with open(backend_file, 'r') as f:
            content = f.read()
            
        error_messages = [
            ("You don't have enough gems — purchase more.", "Недостаточно гемов"),
            ("You don't possess the required gem combination. Please buy from the Gem Shop.", "Неподходящая комбинация"),
            ("Insufficient funds for the commission — please top up your balance.", "Недостаточно средств на комиссию")
        ]
        
        print("📋 Проверка наличия сообщений об ошибках:")
        for message, description in error_messages:
            if message in content:
                print(f"✅ {description}: '{message}'")
            else:
                print(f"❌ {description}: сообщение не найдено")
                
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")


def test_check_order():
    """Проверка порядка проверок"""
    print("\n🧪 TEST 3: Проверка порядка выполнения проверок")
    print("="*50)
    
    backend_file = os.path.join(os.path.dirname(__file__), 'backend', 'server.py')
    
    try:
        with open(backend_file, 'r') as f:
            content = f.read()
            
        # Найти функцию reserve_game
        reserve_start = content.find("async def reserve_game(")
        if reserve_start == -1:
            print("❌ Функция reserve_game не найдена")
            return
            
        # Взять часть кода функции
        reserve_end = content.find("async def", reserve_start + 1)
        reserve_function = content[reserve_start:reserve_end if reserve_end != -1 else reserve_start + 5000]
        
        # Проверить порядок проверок
        check1_pos = reserve_function.find("Check 1: Total gem value")
        check2_pos = reserve_function.find("Check 2: Can form exact combination")
        check3_pos = reserve_function.find("Check 3: Commission")
        
        print("📋 Порядок проверок:")
        if check1_pos != -1 and check2_pos != -1 and check3_pos != -1:
            if check1_pos < check2_pos < check3_pos:
                print("✅ Правильный порядок проверок:")
                print("   1. Общее количество гемов")
                print("   2. Возможность собрать комбинацию")
                print("   3. Комиссия")
            else:
                print("❌ Неправильный порядок проверок")
        else:
            print("❌ Не все проверки найдены")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")


def test_bot_commission_logic():
    """Проверка логики комиссии для ботов"""
    print("\n🧪 TEST 4: Проверка логики комиссии для ботов")
    print("="*50)
    
    backend_file = os.path.join(os.path.dirname(__file__), 'backend', 'server.py')
    
    try:
        with open(backend_file, 'r') as f:
            content = f.read()
            
        # Найти функцию reserve_game
        reserve_start = content.find("async def reserve_game(")
        reserve_end = content.find("async def", reserve_start + 1)
        reserve_function = content[reserve_start:reserve_end if reserve_end != -1 else reserve_start + 5000]
        
        print("📋 Проверка логики для ботов:")
        
        # Проверка для обычных ботов
        if "bot_check = await db.bots.find_one" in reserve_function:
            print("✅ Проверка для обычных ботов найдена")
        else:
            print("❌ Проверка для обычных ботов не найдена")
            
        # Проверка для human-ботов
        if "human_bot_check = await db.human_bots.find_one" in reserve_function:
            print("✅ Проверка для human-ботов найдена")
        else:
            print("❌ Проверка для human-ботов не найдена")
            
        # Проверка пропуска комиссии только для обычных ботов
        if "Only skip commission for regular bots" in reserve_function:
            print("✅ Логика пропуска комиссии только для обычных ботов найдена")
        else:
            print("❌ Логика пропуска комиссии только для обычных ботов не найдена")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")


def test_frontend_integration():
    """Проверка интеграции с frontend"""
    print("\n🧪 TEST 5: Проверка интеграции с Frontend")
    print("="*50)
    
    lobby_file = os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'components', 'Lobby.js')
    
    try:
        with open(lobby_file, 'r') as f:
            content = f.read()
            
        print("📋 Проверка обработки ошибок в Lobby.js:")
        
        # Проверка удаления старой проверки
        if "userTotalGemValue < betAmount" not in content:
            print("✅ Старая проверка гемов удалена из frontend")
        else:
            print("❌ Старая проверка гемов всё ещё присутствует")
            
        # Проверка обработки ошибок от backend
        if "error.response?.data?.detail" in content:
            print("✅ Обработка детальных сообщений об ошибках настроена")
        else:
            print("❌ Обработка детальных сообщений об ошибках не найдена")
            
        # Проверка showError
        if "showError(error.response.data.detail)" in content:
            print("✅ Ошибки показываются через систему уведомлений")
        else:
            print("❌ showError не используется для показа ошибок")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")


def main():
    """Запуск всех тестов"""
    print("🚀 Тестирование логики уведомлений при входе на ставку")
    print("="*50)
    
    test_gem_combination_function()
    test_error_messages()
    test_check_order()
    test_bot_commission_logic()
    test_frontend_integration()
    
    print("\n✅ Проверка завершена!")
    print("\n📝 Реализованная логика:")
    print("1. При недостатке гемов: 'You don't have enough gems — purchase more.'")
    print("2. При невозможности собрать комбинацию: 'You don't possess the required gem combination. Please buy from the Gem Shop.'")
    print("3. При недостатке средств на комиссию: 'Insufficient funds for the commission — please top up your balance.'")
    print("\n⚠️  Примечание: Human-боты и живые игроки платят комиссию, обычные боты - нет.")


if __name__ == "__main__":
    main()