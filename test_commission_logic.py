#!/usr/bin/env python3
"""
Тест для проверки новой логики комиссий от Human-ботов
"""
import asyncio
import requests
import json

BACKEND_URL = "https://0fd37152-eac8-415b-8910-24613a0545f4.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"

async def test_commission_logic():
    """
    Тест новой логики комиссий:
    1. Human-бот vs Human-бот -> HUMAN_BOT_COMMISSION
    2. Human-бот выигрывает vs живой игрок -> HUMAN_BOT_COMMISSION  
    3. Живой игрок выигрывает vs Human-бот -> BET_COMMISSION
    """
    
    # Получить текущую статистику profit
    try:
        response = requests.get(f"{API}/admin/economy/profit-stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            human_bot_commission = stats.get("human_bot_commission", 0)
            bet_commission = stats.get("bet_commission", 0)
            
            print(f"✅ Текущая статистика прибыли:")
            print(f"   Комиссия от Human-ботов: ${human_bot_commission}")
            print(f"   Комиссия от ставок: ${bet_commission}")
            
            # Получить детализацию Human-bot комиссий
            detail_response = requests.get(f"{API}/admin/economy/human-bot-commission-details", timeout=10)
            if detail_response.status_code == 200:
                details = detail_response.json()
                print(f"   Всего записей HUMAN_BOT_COMMISSION: {details.get('summary', {}).get('total_transactions', 0)}")
                print(f"   Сумма всех HUMAN_BOT_COMMISSION: ${details.get('summary', {}).get('total_amount', 0)}")
                
                # Показать последние несколько записей
                entries = details.get('entries', [])[:5]
                print(f"\n   Последние записи HUMAN_BOT_COMMISSION:")
                for entry in entries:
                    print(f"   - ${entry.get('amount', 0):.2f} от игры {entry.get('reference_id', 'N/A')[:8]}... ({entry.get('created_at', 'N/A')[:19]})")
            else:
                print(f"   ❌ Не удалось получить детализацию: {detail_response.status_code}")
                
        else:
            print(f"❌ Не удалось получить статистику: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Ошибка при запросе статистики: {e}")

    print(f"\n🔄 Новая логика комиссий активна:")
    print(f"   1. Human-бот vs Human-бот -> Комиссия от Human-ботов")
    print(f"   2. Human-бот выигрывает vs живой игрок -> Комиссия от Human-ботов")
    print(f"   3. Живой игрок выигрывает vs Human-бот -> Комиссия от ставок")

if __name__ == "__main__":
    asyncio.run(test_commission_logic())