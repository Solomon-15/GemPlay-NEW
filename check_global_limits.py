#!/usr/bin/env python3
"""
Скрипт для проверки глобальных лимитов ботов
"""

import asyncio
from pymongo import MongoClient
import os

async def check_global_limits():
    """Проверка глобальных лимитов ботов"""
    
    # Подключение к MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/gemplay')
    client = MongoClient(mongo_url)
    db = client.gemplay
    
    print("=== ПРОВЕРКА ГЛОБАЛЬНЫХ ЛИМИТОВ БОТОВ ===")
    
    # Получаем настройки глобальных лимитов
    bot_settings = db.bot_settings.find_one({"id": "bot_settings"})
    if bot_settings:
        max_regular = bot_settings.get("max_active_bets_regular", 50)
        max_human = bot_settings.get("max_active_bets_human", 30)
        print(f"📊 Глобальные лимиты:")
        print(f"   - Regular боты: {max_regular}")
        print(f"   - Human боты: {max_human}")
    else:
        max_regular = 50
        max_human = 30
        print(f"⚠️  Настройки не найдены, используются defaults:")
        print(f"   - Regular боты: {max_regular}")
        print(f"   - Human боты: {max_human}")
    
    print("\n=== ТЕКУЩИЕ АКТИВНЫЕ СТАВКИ БОТОВ ===")
    
    # Проверяем текущие активные ставки Regular ботов
    regular_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "REGULAR"},
            {"metadata.bot_type": "REGULAR"}
        ]
    })
    print(f"🤖 Regular боты: {regular_bets}/{max_regular}")
    
    # Проверяем текущие активные ставки Human ботов
    human_bets = db.games.count_documents({
        "creator_type": "bot",
        "is_bot_game": True,
        "status": "WAITING",
        "$or": [
            {"bot_type": "HUMAN"},
            {"metadata.bot_type": "HUMAN"}
        ]
    })
    print(f"👤 Human боты: {human_bets}/{max_human}")
    
    # Проверяем превышение лимитов
    print("\n=== АНАЛИЗ СОБЛЮДЕНИЯ ЛИМИТОВ ===")
    
    if regular_bets > max_regular:
        print(f"❌ ПРЕВЫШЕНИЕ ЛИМИТА Regular ботов: {regular_bets} > {max_regular}")
    else:
        print(f"✅ Regular боты в пределах лимита: {regular_bets}/{max_regular}")
    
    if human_bets > max_human:
        print(f"❌ ПРЕВЫШЕНИЕ ЛИМИТА Human ботов: {human_bets} > {max_human}")
    else:
        print(f"✅ Human боты в пределах лимита: {human_bets}/{max_human}")
    
    # Общая статистика
    total_bot_bets = regular_bets + human_bets
    total_limit = max_regular + max_human
    print(f"\n📈 Общая статистика:")
    print(f"   - Всего активных ставок ботов: {total_bot_bets}")
    print(f"   - Общий лимит: {total_limit}")
    print(f"   - Загрузка: {total_bot_bets/total_limit*100:.1f}%")
    
    # Проверяем отдельные боты
    print("\n=== СТАТИСТИКА ПО ОТДЕЛЬНЫМ БОТАМ ===")
    
    # Получаем всех активных ботов
    active_bots = list(db.bots.find({"is_active": True}))
    print(f"👥 Активных ботов: {len(active_bots)}")
    
    for bot in active_bots:
        bot_active_bets = db.games.count_documents({
            "creator_id": bot["id"],
            "status": "WAITING"
        })
        bot_type = bot.get("bot_type", "REGULAR")
        print(f"   🤖 {bot['name']} ({bot_type}): {bot_active_bets} активных ставок")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_global_limits())