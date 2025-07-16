#!/usr/bin/env python3
"""
Скрипт для проверки активных ставок ботов напрямую из API
"""

import requests
import json

# Получаем токен авторизации
def get_auth_token():
    url = "http://localhost:8001/api/auth/login"
    data = {"email": "admin@gemplay.com", "password": "Admin123!"}
    response = requests.post(url, json=data)
    return response.json()["access_token"]

def check_active_bets():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=== ПРОВЕРКА АКТИВНЫХ СТАВОК БОТОВ ЧЕРЕЗ API ===")
    
    # Получаем активные ставки
    response = requests.get("http://localhost:8001/api/bots/active-games", headers=headers)
    active_bets = response.json()
    
    print(f"📊 Всего активных ставок: {len(active_bets)}")
    
    # Группируем по ботам
    bot_stats = {}
    for bet in active_bets:
        bot_id = bet["bot_id"]
        bot_username = bet["creator_username"]
        bot_type = bet.get("bot_type", "REGULAR")
        
        if bot_id not in bot_stats:
            bot_stats[bot_id] = {
                "username": bot_username,
                "type": bot_type,
                "count": 0
            }
        bot_stats[bot_id]["count"] += 1
    
    print("\n📈 Статистика по ботам:")
    total_regular = 0
    total_human = 0
    
    for bot_id, stats in bot_stats.items():
        print(f"   🤖 {stats['username']} ({stats['type']}): {stats['count']} активных ставок")
        if stats['type'] == 'REGULAR':
            total_regular += stats['count']
        else:
            total_human += stats['count']
    
    print(f"\n📊 Итого:")
    print(f"   - Regular боты: {total_regular}")
    print(f"   - Human боты: {total_human}")
    print(f"   - Всего: {total_regular + total_human}")
    
    # Получаем настройки лимитов
    response = requests.get("http://localhost:8001/api/admin/bots/settings", headers=headers)
    settings = response.json()
    
    print(f"\n⚙️  Настройки лимитов:")
    print(f"   - Regular боты: {settings['max_active_bets_regular']}")
    print(f"   - Human боты: {settings['max_active_bets_human']}")
    
    # Проверяем превышение лимитов
    print(f"\n🔍 Анализ лимитов:")
    if total_regular > settings['max_active_bets_regular']:
        print(f"   ❌ Превышение лимита Regular ботов: {total_regular}/{settings['max_active_bets_regular']}")
    else:
        print(f"   ✅ Лимит Regular ботов соблюден: {total_regular}/{settings['max_active_bets_regular']}")
    
    if total_human > settings['max_active_bets_human']:
        print(f"   ❌ Превышение лимита Human ботов: {total_human}/{settings['max_active_bets_human']}")
    else:
        print(f"   ✅ Лимит Human ботов соблюден: {total_human}/{settings['max_active_bets_human']}")

if __name__ == "__main__":
    check_active_bets()