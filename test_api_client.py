#!/usr/bin/env python3
"""
Тест клиент для проверки API
"""

import json
import time
import subprocess
import sys

def test_api_endpoints():
    """Тестирует API эндпоинты"""
    print("🧪 ТЕСТИРОВАНИЕ API ЭНДПОИНТОВ")
    print("=" * 50)
    
    # Проверяем что сервер запущен
    try:
        result = subprocess.run(['python3', '-c', '''
import urllib.request
import json

def test_endpoint(url, name):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✅ {name}: {response.status}")
            return data
    except Exception as e:
        print(f"❌ {name}: {e}")
        return None

# Тестируем основные эндпоинты
print("📡 Тестируем API эндпоинты...")

# Health check
health = test_endpoint("http://localhost:8000/health", "Health Check")

# Список ботов  
bots = test_endpoint("http://localhost:8000/admin/bots/regular/list", "Список ботов")

# История циклов
cycles = test_endpoint("http://localhost:8000/admin/profit/bot-cycles-history", "История циклов")

# Завершённые циклы тестового бота
bot_cycles = test_endpoint("http://localhost:8000/admin/bots/test_bot_001/completed-cycles", "Циклы бота")

# Сводка доходов
revenue = test_endpoint("http://localhost:8000/admin/profit/bot-revenue-summary", "Сводка доходов")

# Детали ставок
bet_details = test_endpoint("http://localhost:8000/admin/bots/test_bot_001/cycle-bets", "Детали ставок")

print("\\n📊 АНАЛИЗ ДАННЫХ:")
if bot_cycles and bot_cycles.get("cycles"):
    cycle = bot_cycles["cycles"][0]
    print(f"Тестовый бот: {bot_cycles.get(\\"bot_name\\", \\"N/A\\")}")
    print(f"  Всего игр: {cycle.get(\\"total_games\\", \\"N/A\\")}")
    print(f"  W/L/D: {cycle.get(\\"wins\\", \\"N/A\\")}/{cycle.get(\\"losses\\", \\"N/A\\")}/{cycle.get(\\"draws\\", \\"N/A\\")}")
    print(f"  Общая сумма: ${cycle.get(\\"total_bet\\", \\"N/A\\")}")
    print(f"  Выигрыши: ${cycle.get(\\"total_winnings\\", \\"N/A\\")}")
    print(f"  Потери: ${cycle.get(\\"total_losses\\", \\"N/A\\")}")
    print(f"  Прибыль: ${cycle.get(\\"profit\\", \\"N/A\\")}")
    print(f"  ROI: {cycle.get(\\"roi_percent\\", \\"N/A\\\")}%")
    
    # Проверяем правильность значений
    expected = {"total_bet": 809, "total_winnings": 356, "total_losses": 291, "profit": 65, "roi_percent": 10.05}
    print("\\n🎯 ПРОВЕРКА ЭТАЛОННЫХ ЗНАЧЕНИЙ:")
    all_correct = True
    for key, expected_val in expected.items():
        actual_val = cycle.get(key)
        if key == "roi_percent":
            correct = abs(actual_val - expected_val) < 0.1 if actual_val is not None else False
        else:
            correct = actual_val == expected_val
        status = "✅" if correct else "❌"
        print(f"  {status} {key}: {actual_val} (ожидалось {expected_val})")
        if not correct:
            all_correct = False
    
    if all_correct:
        print("\\n🎉 ВСЕ ЗНАЧЕНИЯ КОРРЕКТНЫ!")
    else:
        print("\\n❌ ОБНАРУЖЕНЫ РАСХОЖДЕНИЯ!")

if revenue:
    print(f"\\n💰 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Общий доход: ${revenue.get(\\"revenue\\", {}).get(\\"total\\", \\"N/A\\")}")
    print(f"  Всего циклов: {revenue.get(\\"cycles\\", {}).get(\\"total\\", \\"N/A\\")}")
    print(f"  Прибыльных: {revenue.get(\\"cycles\\", {}).get(\\"profitable\\", \\"N/A\\")}")
'''], capture_output=True, text=True, timeout=10)
        
        print(result.stdout)
        if result.stderr:
            print("Ошибки:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут при тестировании API")
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def main():
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ MOCK API")
    print("Проверяем что сервер запущен и API работает корректно")
    print("=" * 60)
    
    test_api_endpoints()
    
    print(f"\n" + "=" * 60)
    print("📋 ИНСТРУКЦИИ ДЛЯ ДАЛЬНЕЙШЕГО ТЕСТИРОВАНИЯ:")
    print("1. Mock сервер запущен на http://localhost:8000")
    print("2. Запустите frontend: cd /workspace/frontend && npm start")
    print("3. Откройте http://localhost:3000 в браузере")
    print("4. Войдите как администратор (admin/admin)")
    print("5. Перейдите в 'Управление ботами' → 'Обычные боты'")
    print("6. Проверьте 'История циклов' для TestBot ROI")
    print("7. Проверьте 'Доход от ботов' в разделе прибыли")
    print("=" * 60)

if __name__ == "__main__":
    main()