#!/usr/bin/env python3
"""
Тест функционала колонок "Статистика" и "Ставки" для Human-ботов
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_admin_login():
    """Пытается войти с различными учетными данными"""
    
    # Список возможных учетных данных
    credentials = [
        {"email": "admin@example.com", "password": "admin123"},
        {"email": "testadmin@example.com", "password": "admin123"},
        {"email": "smukhammedali@gmail.com", "password": "admin123"},
        {"email": "admin@gemplay.com", "password": "admin123"},
        {"email": "admin", "password": "admin123"}
    ]
    
    for cred in credentials:
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json=cred,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    print(f"✅ Успешная авторизация: {cred['email']}")
                    return token
                    
        except Exception as e:
            print(f"❌ Ошибка авторизации для {cred['email']}: {e}")
            continue
    
    return None

def test_human_bots_statistics(token):
    """Тест получения статистики Human-ботов"""
    
    print("\n=== ТЕСТ СТАТИСТИКИ HUMAN-БОТОВ ===")
    
    try:
        # Получаем список Human-ботов
        response = requests.get(
            f"{BASE_URL}/api/admin/human-bots",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения Human-ботов: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
        
        data = response.json()
        bots = data.get("human_bots", [])
        
        if not bots:
            print("⚠️  Нет Human-ботов в системе")
            return False
            
        print(f"✅ Найдено {len(bots)} Human-ботов")
        
        # Проверяем каждого бота
        for i, bot in enumerate(bots[:3]):  # Проверяем первых 3 ботов
            print(f"\n--- Бот {i+1}: {bot.get('name', 'Unknown')} ---")
            
            # Проверяем поля статистики
            stats_fields = [
                "total_games_played",
                "total_games_won", 
                "win_percentage",
                "total_amount_won",
                "total_amount_wagered",
                "active_bets_count"
            ]
            
            print("📊 Статистика:")
            for field in stats_fields:
                value = bot.get(field, "отсутствует")
                print(f"  {field}: {value}")
            
            # Проверяем вычисления
            total_games = bot.get("total_games_played", 0)
            total_wins = bot.get("total_games_won", 0)
            win_percentage = bot.get("win_percentage", 0)
            
            if total_games > 0:
                expected_win_rate = (total_wins / total_games) * 100
                print(f"  Ожидаемый win_rate: {expected_win_rate:.2f}%")
                if abs(win_percentage - expected_win_rate) < 0.1:
                    print("  ✅ Win rate корректный")
                else:
                    print("  ❌ Win rate некорректный")
            
            # Проверяем прибыль
            total_won = bot.get("total_amount_won", 0)
            total_wagered = bot.get("total_amount_wagered", 0)
            net_profit = total_won - total_wagered
            print(f"  Чистая прибыль: {net_profit:.2f}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании статистики: {e}")
        return False

def test_active_bets(token, bot_id):
    """Тест получения активных ставок"""
    
    print(f"\n=== ТЕСТ АКТИВНЫХ СТАВОК ДЛЯ БОТА {bot_id} ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/human-bots/{bot_id}/active-bets",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения активных ставок: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
        
        data = response.json()
        active_bets = data.get("active_bets", [])
        
        print(f"✅ Активных ставок: {len(active_bets)}")
        
        if active_bets:
            print("📋 Первые 3 активные ставки:")
            for i, bet in enumerate(active_bets[:3]):
                print(f"  Ставка {i+1}:")
                print(f"    ID: {bet.get('id', 'N/A')}")
                print(f"    Размер: {bet.get('bet_amount', 'N/A')}")
                print(f"    Статус: {bet.get('status', 'N/A')}")
                print(f"    Дата: {bet.get('created_at', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании активных ставок: {e}")
        return False

def test_all_bets(token, bot_id):
    """Тест получения всех ставок с пагинацией"""
    
    print(f"\n=== ТЕСТ ВСЕХ СТАВОК ДЛЯ БОТА {bot_id} ===")
    
    try:
        # Тест первой страницы
        response = requests.get(
            f"{BASE_URL}/api/admin/human-bots/{bot_id}/all-bets?page=1&limit=5",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения всех ставок: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
        
        data = response.json()
        bets = data.get("bets", [])
        total = data.get("total", 0)
        page = data.get("page", 1)
        
        print(f"✅ Всего ставок: {total}")
        print(f"✅ Страница: {page}")
        print(f"✅ Ставок на странице: {len(bets)}")
        
        if bets:
            print("📋 Первые 3 ставки:")
            for i, bet in enumerate(bets[:3]):
                print(f"  Ставка {i+1}:")
                print(f"    ID: {bet.get('id', 'N/A')}")
                print(f"    Размер: {bet.get('bet_amount', 'N/A')}")
                print(f"    Статус: {bet.get('status', 'N/A')}")
                print(f"    Дата: {bet.get('created_at', 'N/A')}")
        
        # Тест второй страницы, если есть данные
        if total > 5:
            print("\n--- Тест второй страницы ---")
            response2 = requests.get(
                f"{BASE_URL}/api/admin/human-bots/{bot_id}/all-bets?page=2&limit=5",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                bets2 = data2.get("bets", [])
                print(f"✅ Страница 2: {len(bets2)} ставок")
            else:
                print(f"❌ Ошибка второй страницы: {response2.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании всех ставок: {e}")
        return False

def main():
    """Основная функция тестирования"""
    
    print("🔍 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА КОЛОНОК 'СТАТИСТИКА' И 'СТАВКИ'")
    print("=" * 70)
    
    # Шаг 1: Авторизация
    print("\n1. Авторизация...")
    token = test_admin_login()
    
    if not token:
        print("❌ Не удалось авторизоваться. Тест прерван.")
        return
    
    # Шаг 2: Тест статистики Human-ботов
    print("\n2. Тестирование статистики Human-ботов...")
    stats_success = test_human_bots_statistics(token)
    
    if not stats_success:
        print("❌ Тест статистики не прошел")
        return
    
    # Шаг 3: Получаем ID бота для тестирования ставок
    print("\n3. Получение ID бота для тестирования ставок...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/human-bots",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            bots = data.get("human_bots", [])
            
            if bots:
                bot_id = bots[0].get("id")
                bot_name = bots[0].get("name")
                print(f"✅ Выбран бот: {bot_name} (ID: {bot_id})")
                
                # Шаг 4: Тест активных ставок
                print("\n4. Тестирование активных ставок...")
                test_active_bets(token, bot_id)
                
                # Шаг 5: Тест всех ставок
                print("\n5. Тестирование всех ставок...")
                test_all_bets(token, bot_id)
                
            else:
                print("❌ Нет ботов для тестирования ставок")
        else:
            print(f"❌ Ошибка получения списка ботов: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при получении ID бота: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    main()