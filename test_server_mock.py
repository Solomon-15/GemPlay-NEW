#!/usr/bin/env python3
"""
Mock сервер для тестирования без MongoDB
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from typing import Dict, List, Any
import uvicorn

app = FastAPI(title="GemPlay Mock API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data storage
mock_data = {
    "bots": [],
    "completed_cycles": [],
    "bot_profit_accumulators": [],
    "users": [
        {
            "id": "admin_1",
            "username": "admin",
            "email": "admin@test.com",
            "role": "ADMIN",
            "is_active": True
        }
    ]
}

# Mock bot data with correct calculations
def create_mock_completed_cycle(bot_id: str, cycle_number: int = 1):
    """Создаёт mock завершённый цикл с правильными расчётами"""
    return {
        "id": f"cycle_{bot_id}_{cycle_number}",
        "bot_id": bot_id,
        "cycle_number": cycle_number,
        "start_time": datetime.utcnow().isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "duration_seconds": 3600,  # 1 час
        "total_bets": 16,
        "wins_count": 7,
        "losses_count": 6,
        "draws_count": 3,
        "total_bet_amount": 800,  # ✅ База 800
        "total_winnings": 317,    # ✅ Сумма выигрышей
        "total_losses": 259,      # ✅ Сумма потерь
        "total_draws": 224,       # ✅ Сумма ничьих
        "net_profit": 58,         # ✅ Прибыль (317-259)
        "is_profitable": True,
        "active_pool": 576,       # ✅ Активный пул (317+259)
        "roi_active": 10.07,      # ✅ ROI (58/576*100)
        "created_by_system_version": "v5.0_corrected",
        "created_at": datetime.utcnow().isoformat()
    }

def create_mock_bot(bot_id: str, name: str):
    """Создаёт mock бота"""
    return {
        "id": bot_id,
        "name": name,
        "bot_type": "REGULAR",
        "is_active": True,
        "cycle_games": 16,
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "wins_percentage": 44.0,
        "losses_percentage": 36.0,
        "draws_percentage": 20.0,
        "wins_count": 7,
        "losses_count": 6,
        "draws_count": 3,
        "completed_cycles": 1,
        "created_at": datetime.utcnow().isoformat()
    }

# Инициализируем mock данные
mock_data["bots"].append(create_mock_bot("test_bot_001", "TestBot ROI"))
mock_data["completed_cycles"].append(create_mock_completed_cycle("test_bot_001"))

@app.get("/")
async def root():
    return {"message": "GemPlay Mock API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "database": "mock"}

@app.get("/admin/bots/regular/list")
async def get_regular_bots():
    """Список обычных ботов"""
    return {
        "success": True,
        "bots": mock_data["bots"],
        "total_count": len(mock_data["bots"])
    }

@app.get("/admin/bots/{bot_id}/completed-cycles")
async def get_bot_completed_cycles(bot_id: str):
    """Завершённые циклы бота"""
    cycles = [cycle for cycle in mock_data["completed_cycles"] if cycle["bot_id"] == bot_id]
    bot = next((bot for bot in mock_data["bots"] if bot["id"] == bot_id), None)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Форматируем данные для фронтенда
    formatted_cycles = []
    for cycle in cycles:
        formatted_cycles.append({
            "id": cycle["id"],
            "cycle_number": cycle["cycle_number"],
            "completed_at": cycle["end_time"],
            "duration": "1ч 0м",
            "total_games": cycle["total_bets"],
            "games_played": cycle["total_bets"],
            "wins": cycle["wins_count"],
            "losses": cycle["losses_count"],
            "draws": cycle["draws_count"],
            "total_bet": cycle["total_bet_amount"],
            "total_winnings": cycle["total_winnings"],
            "total_losses": cycle["total_losses"],
            "profit": cycle["net_profit"],
            "roi_percent": cycle["roi_active"]
        })
    
    return {
        "bot_id": bot_id,
        "bot_name": bot["name"],
        "total_completed_cycles": len(formatted_cycles),
        "cycles": formatted_cycles
    }

@app.get("/admin/profit/bot-cycles-history")
async def get_bot_cycles_history():
    """История циклов ботов"""
    formatted_cycles = []
    
    for cycle in mock_data["completed_cycles"]:
        bot = next((bot for bot in mock_data["bots"] if bot["id"] == cycle["bot_id"]), None)
        bot_name = bot["name"] if bot else "Unknown Bot"
        
        formatted_cycles.append({
            "id": cycle["id"],
            "bot_id": cycle["bot_id"],
            "bot_name": bot_name,
            "cycle_number": cycle["cycle_number"],
            "start_time": cycle["start_time"],
            "end_time": cycle["end_time"],
            "duration_hours": 1.0,
            "total_games": cycle["total_bets"],
            "wins": cycle["wins_count"],
            "losses": cycle["losses_count"],
            "draws": cycle["draws_count"],
            "total_bet_amount": cycle["total_bet_amount"],
            "net_profit": cycle["net_profit"],
            "roi_percent": cycle["roi_active"],
            "is_profitable": cycle["is_profitable"]
        })
    
    return {
        "success": True,
        "cycles": formatted_cycles,
        "pagination": {
            "current_page": 1,
            "total_pages": 1,
            "total_count": len(formatted_cycles),
            "limit": 20
        },
        "summary": {
            "total_profit": sum(c["net_profit"] for c in formatted_cycles),
            "total_games": sum(c["total_games"] for c in formatted_cycles),
            "profitable_cycles": len([c for c in formatted_cycles if c["is_profitable"]]),
            "profitability_rate": 100.0,
            "avg_roi": 10.05
        }
    }

@app.get("/admin/profit/bot-revenue-summary")
async def get_bot_revenue_summary():
    """Сводка доходов от ботов"""
    cycles = mock_data["completed_cycles"]
    
    total_revenue = sum(cycle["net_profit"] for cycle in cycles)
    total_cycles = len(cycles)
    profitable_cycles = len([c for c in cycles if c["is_profitable"]])
    total_games = sum(cycle["total_bets"] for cycle in cycles)
    total_bet_amount = sum(cycle["total_bet_amount"] for cycle in cycles)
    
    return {
        "success": True,
        "period": "all",
        "revenue": {
            "total": total_revenue,
            "avg_per_cycle": total_revenue / total_cycles if total_cycles > 0 else 0
        },
        "cycles": {
            "total": total_cycles,
            "profitable": profitable_cycles,
            "profitability_rate": (profitable_cycles / total_cycles * 100) if total_cycles > 0 else 0,
            "avg_games": total_games / total_cycles if total_cycles > 0 else 0
        },
        "bots": {
            "active": len([b for b in mock_data["bots"] if b["is_active"]]),
            "total": len(mock_data["bots"])
        },
        "performance": {
            "total_games": total_games,
            "total_bet_volume": total_bet_amount,
            "avg_roi": 10.05
        }
    }

@app.post("/admin/bots/create")
async def create_bot(bot_data: Dict[str, Any]):
    """Создание бота (mock)"""
    bot_id = f"bot_{len(mock_data['bots']) + 1:03d}"
    new_bot = create_mock_bot(bot_id, bot_data.get("name", f"Bot {bot_id}"))
    mock_data["bots"].append(new_bot)
    
    # Создаём mock завершённый цикл для демонстрации
    mock_cycle = create_mock_completed_cycle(bot_id)
    mock_data["completed_cycles"].append(mock_cycle)
    
    return {
        "success": True,
        "bot": new_bot,
        "message": f"Бот {new_bot['name']} создан с правильными расчётами"
    }

@app.get("/admin/bots/{bot_id}/cycle-bets")
async def get_bot_cycle_bets(bot_id: str):
    """Детальная информация о ставках цикла"""
    bot = next((bot for bot in mock_data["bots"] if bot["id"] == bot_id), None)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {
        "success": True,
        "bot_name": bot["name"],
        "cycle_length": 16,
        "exact_cycle_total": 800,  # ✅ База 800
        "sums": {
            "wins_sum": 317,    # ✅ Суммы
            "losses_sum": 259,  # ✅
            "draws_sum": 224,   # ✅
            "total_sum": 800,   # ✅
            "active_pool": 576, # ✅
            "profit": 58,       # ✅
            "roi_active": 10.07 # ✅
        },
        "bets": [
            # Mock ставки для демонстрации
            {"index": i+1, "amount": 50, "result": "win" if i < 7 else ("loss" if i < 13 else "draw")}
            for i in range(16)
        ]
    }

if __name__ == "__main__":
    print("🚀 Запуск Mock сервера GemPlay")
    print("📊 Данные содержат расчёты по базе 800:")
    print("   - Общая сумма цикла: 800")
    print("   - Выигрыши: 317, Потери: 259, Ничьи: 224") 
    print("   - Активный пул: 576, Прибыль: 58, ROI: 10.07%")
    print("🔗 Сервер будет доступен на http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)