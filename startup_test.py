#!/usr/bin/env python3
"""
Скрипт для тестирования при запуске реального сервера
"""

import time
import urllib.request
import json

def test_server_startup():
    print("🚀 ТЕСТ ЗАПУСКА СЕРВЕРА")
    print("=" * 40)
    
    # Ждём запуска сервера
    print("⏳ Ожидание запуска сервера...")
    for i in range(30):
        try:
            with urllib.request.urlopen("http://localhost:8000/health", timeout=2) as response:
                if response.status == 200:
                    print(f"✅ Сервер запущен (попытка {i+1})")
                    break
        except:
            time.sleep(1)
    else:
        print("❌ Сервер не запустился за 30 секунд")
        return False
    
    # Тестируем API эндпоинты
    endpoints = [
        ("Список ботов", "/admin/bots/regular/list"),
        ("История циклов", "/admin/profit/bot-cycles-history"),
        ("Сводка доходов", "/admin/profit/bot-revenue-summary")
    ]
    
    for name, endpoint in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    print(f"✅ {name}: API работает")
                else:
                    print(f"❌ {name}: HTTP {response.status}")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print("\n🎯 ИНСТРУКЦИИ ДЛЯ РУЧНОГО ТЕСТИРОВАНИЯ:")
    print("1. Откройте http://localhost:3000")
    print("2. Войдите как администратор")
    print("3. Создайте бота: диапазон 1-100, 16 игр")
    print("4. Проверьте что НЕТ поля 'Пауза при ничье'")
    print("5. Проверьте что цикл создался автоматически")
    print("6. Проверьте 'Доход от ботов' - должны быть правильные значения")

if __name__ == "__main__":
    test_server_startup()
