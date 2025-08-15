#!/usr/bin/env python3
"""
CRITICAL BET RANGE GENERATION TEST - Russian Review
Критическое тестирование исправления генерации ставок обычных ботов

ОБНАРУЖЕНА ПРОБЛЕМА: Test_Bet_Range_Bot создает ставки ВНЕ диапазона min_bet_amount и max_bet_amount!

ФАКТИЧЕСКИЕ ДАННЫЕ:
- Bot: Test_Bet_Range_Bot (min_bet: 10.0, max_bet: 30.0)
- Фактические ставки: [100.0, 50.0, 28.0, 60.0, 50.0]
- В диапазоне (10-30): только 1 ставка (28.0)
- Вне диапазона: 4 ставки (100.0, 50.0, 60.0, 50.0)

КРИТИЧЕСКАЯ ОШИБКА: Исправление генерации ставок НЕ РАБОТАЕТ!
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://russian-writing-4.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.RED}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.RED}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.RED}{'='*80}{Colors.END}\n")

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    auth_response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if auth_response.status_code == 200:
        return auth_response.json()["access_token"]
    return None

def analyze_bet_range_issue():
    """Comprehensive analysis of the bet range generation issue"""
    print_header("КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ СТАВОК БОТОВ")
    
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Authentication failed{Colors.END}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"{Colors.BOLD}{Colors.CYAN}🔍 АНАЛИЗ ПРОБЛЕМЫ ГЕНЕРАЦИИ СТАВОК{Colors.END}")
    
    # Get all regular bots
    bots_response = requests.get(f"{BASE_URL}/admin/bots", headers=headers)
    bots_data = bots_response.json()
    bots = bots_data if isinstance(bots_data, list) else bots_data.get('bots', [])
    
    # Get active games
    games_response = requests.get(f"{BASE_URL}/bots/active-games", headers=headers)
    games_data = games_response.json()
    games = games_data if isinstance(games_data, list) else games_data.get('games', [])
    
    print(f"\n{Colors.BOLD}📊 ОБЩАЯ СТАТИСТИКА:{Colors.END}")
    print(f"   Всего обычных ботов: {len(bots)}")
    print(f"   Всего активных игр: {len(games)}")
    
    # Analyze each bot
    critical_issues = []
    
    for bot in bots:
        bot_id = bot.get("id", "")
        bot_name = bot.get("name", "N/A")
        min_bet = bot.get("min_bet_amount", 0)
        max_bet = bot.get("max_bet_amount", 0)
        cycle_games = bot.get("cycle_games", 0)
        active_bets = bot.get("active_bets", 0)
        
        # Find games created by this bot
        bot_games = [game for game in games if game.get("creator_id") == bot_id]
        bet_amounts = [game.get("bet_amount", 0) for game in bot_games]
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}🤖 БОТ: {bot_name}{Colors.END}")
        print(f"   ID: {bot_id[:8]}...")
        print(f"   Настройки: min_bet={min_bet}, max_bet={max_bet}, cycle_games={cycle_games}")
        print(f"   Активных ставок: {active_bets} (ожидается: {cycle_games})")
        print(f"   Найдено игр: {len(bot_games)}")
        
        if bet_amounts:
            print(f"   Суммы ставок: {bet_amounts}")
            
            # Check range compliance
            in_range = [amount for amount in bet_amounts if min_bet <= amount <= max_bet]
            out_of_range = [amount for amount in bet_amounts if not (min_bet <= amount <= max_bet)]
            
            min_actual = min(bet_amounts)
            max_actual = max(bet_amounts)
            avg_actual = sum(bet_amounts) / len(bet_amounts)
            
            print(f"   Диапазон ставок: {min_actual} - {max_actual} (среднее: {avg_actual:.2f})")
            print(f"   {Colors.GREEN}✅ В диапазоне ({min_bet}-{max_bet}): {len(in_range)} ставок: {in_range}{Colors.END}")
            
            if out_of_range:
                print(f"   {Colors.RED}❌ ВНЕ диапазона: {len(out_of_range)} ставок: {out_of_range}{Colors.END}")
                
                # This is a critical issue
                critical_issues.append({
                    "bot_name": bot_name,
                    "bot_id": bot_id[:8] + "...",
                    "expected_range": f"{min_bet}-{max_bet}",
                    "actual_range": f"{min_actual}-{max_actual}",
                    "out_of_range_bets": out_of_range,
                    "compliance_rate": f"{len(in_range)}/{len(bet_amounts)} ({len(in_range)/len(bet_amounts)*100:.1f}%)"
                })
            else:
                print(f"   {Colors.GREEN}✅ Все ставки в правильном диапазоне!{Colors.END}")
        else:
            print(f"   {Colors.YELLOW}⚠️ Нет активных игр для анализа{Colors.END}")
    
    # Summary of critical issues
    print(f"\n{Colors.BOLD}{Colors.RED}🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ:{Colors.END}")
    
    if critical_issues:
        print(f"   Количество ботов с проблемами: {len(critical_issues)}")
        print(f"   Общее количество ботов: {len(bots)}")
        print(f"   Процент проблемных ботов: {len(critical_issues)/len(bots)*100:.1f}%")
        
        print(f"\n{Colors.BOLD}📋 ДЕТАЛИ ПРОБЛЕМ:{Colors.END}")
        for i, issue in enumerate(critical_issues, 1):
            print(f"   {i}. {Colors.RED}БОТ: {issue['bot_name']} ({issue['bot_id']}){Colors.END}")
            print(f"      Ожидаемый диапазон: {issue['expected_range']}")
            print(f"      Фактический диапазон: {issue['actual_range']}")
            print(f"      Ставки вне диапазона: {issue['out_of_range_bets']}")
            print(f"      Соответствие: {issue['compliance_rate']}")
            print()
        
        print(f"{Colors.BOLD}{Colors.RED}🔥 ЗАКЛЮЧЕНИЕ: ИСПРАВЛЕНИЕ ГЕНЕРАЦИИ СТАВОК НЕ РАБОТАЕТ!{Colors.END}")
        print(f"{Colors.RED}Обычные боты создают ставки ВНЕ указанного диапазона min_bet_amount и max_bet_amount.{Colors.END}")
        print(f"{Colors.RED}Это критическая ошибка, которая требует немедленного исправления.{Colors.END}")
        
        # Specific focus on Test_Bet_Range_Bot
        test_bot_issue = next((issue for issue in critical_issues if "Test_Bet_Range_Bot" in issue['bot_name']), None)
        if test_bot_issue:
            print(f"\n{Colors.BOLD}{Colors.MAGENTA}🎯 СПЕЦИАЛЬНЫЙ АНАЛИЗ Test_Bet_Range_Bot:{Colors.END}")
            print(f"   Этот бот был создан специально для тестирования исправления")
            print(f"   Настройки: min_bet=10.0, max_bet=30.0, cycle_games=5")
            print(f"   {Colors.RED}РЕЗУЛЬТАТ: {test_bot_issue['compliance_rate']} ставок в правильном диапазоне{Colors.END}")
            print(f"   {Colors.RED}СТАВКИ ВНЕ ДИАПАЗОНА: {test_bot_issue['out_of_range_bets']}{Colors.END}")
            print(f"   {Colors.RED}ЭТО ДОКАЗЫВАЕТ ЧТО ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ!{Colors.END}")
    else:
        print(f"{Colors.GREEN}✅ Все боты создают ставки в правильном диапазоне!{Colors.END}")
        print(f"{Colors.GREEN}Исправление генерации ставок работает корректно.{Colors.END}")
    
    return len(critical_issues) == 0

def main():
    """Main execution"""
    success = analyze_bet_range_issue()
    
    if not success:
        print(f"\n{Colors.BOLD}{Colors.RED}❌ ТЕСТ ПРОВАЛЕН: Исправление генерации ставок НЕ РАБОТАЕТ{Colors.END}")
        sys.exit(1)
    else:
        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ ТЕСТ ПРОЙДЕН: Исправление генерации ставок работает корректно{Colors.END}")

if __name__ == "__main__":
    main()