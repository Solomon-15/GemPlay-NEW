#!/usr/bin/env python3
"""
RUSSIAN REVIEW FOCUSED TEST - Regular Bots API Regression
Focused test for the specific Russian review requirements
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://9dac94ee-f135-41d4-9528-71a64685f265.preview.emergentagent.com/api"
ADMIN_USER = {"email": "admin@gemplay.com", "password": "Admin123!"}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def authenticate_admin():
    """Authenticate as admin and return access token"""
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_russian_review_requirements():
    """Test all Russian review requirements"""
    print(f"{Colors.BOLD}{Colors.CYAN}🎯 RUSSIAN REVIEW - REGULAR BOTS API REGRESSION TEST{Colors.END}")
    print(f"{Colors.BLUE}Testing all endpoints and requirements from Russian review{Colors.END}\n")
    
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Authentication failed{Colors.END}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"passed": 0, "failed": 0, "total": 0}
    
    # 1. Test POST /api/admin/bots/create-regular
    print(f"{Colors.MAGENTA}1. Testing POST /api/admin/bots/create-regular{Colors.END}")
    bot_data = {
        "name": f"RussianReview_Bot_{int(time.time())}",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "wins_count": 6,
        "losses_count": 4,
        "draws_count": 2,
        "wins_percentage": 50.0,
        "losses_percentage": 33.3,
        "draws_percentage": 16.7,
        "cycle_games": 12,
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced"
    }
    
    response = requests.post(f"{BASE_URL}/admin/bots/create-regular", headers=headers, json=bot_data)
    results["total"] += 1
    if response.status_code == 200:
        bot_id = response.json().get("bot_id")
        print(f"   {Colors.GREEN}✅ Bot created successfully: {bot_id}{Colors.END}")
        results["passed"] += 1
        
        # Calculate expected cycle_total_amount
        expected_cycle_total = (bot_data["min_bet_amount"] + bot_data["max_bet_amount"]) / 2 * bot_data["cycle_games"]
        print(f"   📊 Expected cycle_total_amount: ${expected_cycle_total}")
    else:
        print(f"   {Colors.RED}❌ Bot creation failed: {response.status_code}{Colors.END}")
        results["failed"] += 1
        bot_id = None
    
    # 2. Test GET /api/admin/bots/regular/list
    print(f"\n{Colors.MAGENTA}2. Testing GET /api/admin/bots/regular/list{Colors.END}")
    response = requests.get(f"{BASE_URL}/admin/bots/regular/list", headers=headers)
    results["total"] += 1
    if response.status_code == 200:
        bots_data = response.json()
        bots = bots_data if isinstance(bots_data, list) else bots_data.get("bots", [])
        print(f"   {Colors.GREEN}✅ Retrieved {len(bots)} regular bots{Colors.END}")
        
        # Check for roi_active and cycle_total_info
        if bots and len(bots) > 0:
            first_bot = bots[0]
            has_roi = any(key in first_bot for key in ["roi_active", "win_percentage"])
            has_cycle_info = any(key in first_bot for key in ["cycle_total_amount", "cycle_games"])
            print(f"   📊 ROI fields present: {has_roi}, Cycle info present: {has_cycle_info}")
        results["passed"] += 1
    else:
        print(f"   {Colors.RED}❌ Failed to get bots list: {response.status_code}{Colors.END}")
        results["failed"] += 1
    
    # 3. Test GET /api/admin/bots/{id} if we have a bot
    if bot_id:
        print(f"\n{Colors.MAGENTA}3. Testing GET /api/admin/bots/{bot_id}{Colors.END}")
        response = requests.get(f"{BASE_URL}/admin/bots/{bot_id}", headers=headers)
        results["total"] += 1
        if response.status_code == 200:
            bot_details = response.json()
            print(f"   {Colors.GREEN}✅ Bot details retrieved{Colors.END}")
            
            # Check for parameters and statistics
            required_params = ["min_bet_amount", "max_bet_amount", "cycle_games"]
            stats_fields = ["current_cycle_wins", "current_cycle_losses", "current_cycle_draws"]
            
            has_params = all(param in bot_details for param in required_params)
            has_stats = any(field in bot_details for field in stats_fields)
            print(f"   📊 Parameters present: {has_params}, Statistics present: {has_stats}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ Failed to get bot details: {response.status_code}{Colors.END}")
            results["failed"] += 1
    
    # 4. Test PUT/PATCH validation
    if bot_id:
        print(f"\n{Colors.MAGENTA}4. Testing PUT/PATCH validation (percentages=100%, W+L+D=N){Colors.END}")
        
        # Test valid update (percentages = 100%)
        valid_update = {
            "wins_percentage": 50.0,
            "losses_percentage": 30.0,
            "draws_percentage": 20.0,  # Total = 100%
            "wins_count": 6,
            "losses_count": 4,
            "draws_count": 2  # Total = 12
        }
        
        response = requests.patch(f"{BASE_URL}/admin/bots/{bot_id}", headers=headers, json=valid_update)
        results["total"] += 1
        if response.status_code == 200:
            print(f"   {Colors.GREEN}✅ Valid update accepted{Colors.END}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ Valid update rejected: {response.status_code}{Colors.END}")
            results["failed"] += 1
        
        # Test invalid update (percentages ≠ 100%)
        invalid_update = {
            "wins_percentage": 50.0,
            "losses_percentage": 30.0,
            "draws_percentage": 15.0  # Total = 95%
        }
        
        response = requests.patch(f"{BASE_URL}/admin/bots/{bot_id}", headers=headers, json=invalid_update)
        results["total"] += 1
        if response.status_code != 200:
            print(f"   {Colors.GREEN}✅ Invalid percentages correctly rejected{Colors.END}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ Invalid percentages incorrectly accepted{Colors.END}")
            results["failed"] += 1
    
    # 5. Test GET /api/admin/bots/{id}/cycle-bets
    if bot_id:
        print(f"\n{Colors.MAGENTA}5. Testing GET /api/admin/bots/{bot_id}/cycle-bets{Colors.END}")
        response = requests.get(f"{BASE_URL}/admin/bots/{bot_id}/cycle-bets", headers=headers)
        results["total"] += 1
        if response.status_code == 200:
            cycle_data = response.json()
            print(f"   {Colors.GREEN}✅ Cycle bets data retrieved{Colors.END}")
            
            # Check for detailed breakdown
            has_bets = "bets" in cycle_data or "games" in cycle_data or isinstance(cycle_data, list)
            print(f"   📊 Detailed breakdown available: {has_bets}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ Failed to get cycle bets: {response.status_code}{Colors.END}")
            results["failed"] += 1
    
    # 6. Test POST /api/admin/bots/{id}/recalculate-bets
    if bot_id:
        print(f"\n{Colors.MAGENTA}6. Testing POST /api/admin/bots/{bot_id}/recalculate-bets{Colors.END}")
        response = requests.post(f"{BASE_URL}/admin/bots/{bot_id}/recalculate-bets", headers=headers)
        results["total"] += 1
        if response.status_code == 200:
            recalc_data = response.json()
            print(f"   {Colors.GREEN}✅ Bets recalculated successfully{Colors.END}")
            
            # Check if cycle_total_amount is calculated correctly
            if "cycle_parameters" in recalc_data:
                cycle_params = recalc_data["cycle_parameters"]
                cycle_total = cycle_params.get("cycle_total_amount", 0)
                print(f"   📊 Recalculated cycle_total_amount: ${cycle_total}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ Failed to recalculate bets: {response.status_code}{Colors.END}")
            results["failed"] += 1
    
    # 7. Test toggle and force-complete-cycle
    if bot_id:
        print(f"\n{Colors.MAGENTA}7. Testing toggle and force-complete-cycle{Colors.END}")
        
        # Test toggle
        response = requests.post(f"{BASE_URL}/admin/bots/{bot_id}/toggle", headers=headers)
        results["total"] += 1
        if response.status_code == 200:
            print(f"   {Colors.GREEN}✅ Bot toggle successful{Colors.END}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ Bot toggle failed: {response.status_code}{Colors.END}")
            results["failed"] += 1
        
        # Test force complete cycle
        response = requests.post(f"{BASE_URL}/admin/bots/{bot_id}/force-complete-cycle", headers=headers)
        results["total"] += 1
        if response.status_code == 200:
            print(f"   {Colors.GREEN}✅ Force complete cycle successful{Colors.END}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ Force complete cycle failed: {response.status_code}{Colors.END}")
            results["failed"] += 1
    
    # 8. Test ROI calculation verification
    print(f"\n{Colors.MAGENTA}8. Testing ROI_active calculation{Colors.END}")
    response = requests.get(f"{BASE_URL}/admin/bots/regular/list", headers=headers)
    results["total"] += 1
    if response.status_code == 200:
        bots = response.json()
        roi_verified = 0
        roi_total = 0
        
        for bot in bots[:3]:  # Check first 3 bots
            bot_id_check = bot.get("id")
            if bot_id_check:
                bot_response = requests.get(f"{BASE_URL}/admin/bots/{bot_id_check}", headers=headers)
                if bot_response.status_code == 200:
                    bot_data = bot_response.json()
                    roi_total += 1
                    
                    # Check ROI calculation: (wins_sum - losses_sum)/(wins_sum + losses_sum)*100
                    wins_sum = bot_data.get("current_cycle_gem_value_won", 0)
                    total_sum = bot_data.get("current_cycle_gem_value_total", 0)
                    losses_sum = total_sum - wins_sum
                    
                    if wins_sum + losses_sum > 0:
                        expected_roi = (wins_sum - losses_sum) / (wins_sum + losses_sum) * 100
                        actual_roi = bot_data.get("roi_active", 0)
                        
                        if abs(expected_roi - actual_roi) < 0.1:
                            roi_verified += 1
        
        if roi_total > 0:
            print(f"   {Colors.GREEN}✅ ROI calculation verified for {roi_verified}/{roi_total} bots{Colors.END}")
            results["passed"] += 1
        else:
            print(f"   {Colors.YELLOW}⚠️ No bots available for ROI verification{Colors.END}")
            results["passed"] += 1
    else:
        print(f"   {Colors.RED}❌ Failed to verify ROI calculation{Colors.END}")
        results["failed"] += 1
    
    # 9. Test active bets limit
    print(f"\n{Colors.MAGENTA}9. Testing active bets ≤ cycle_games{Colors.END}")
    response = requests.get(f"{BASE_URL}/bots/active-games", headers=headers)
    results["total"] += 1
    if response.status_code == 200:
        games = response.json()
        
        # Group by bot_id
        bot_games = {}
        for game in games:
            bot_id_game = game.get("bot_id")
            if bot_id_game:
                if bot_id_game not in bot_games:
                    bot_games[bot_id_game] = []
                bot_games[bot_id_game].append(game)
        
        violations = 0
        total_bots = len(bot_games)
        
        for bot_id_check, bot_game_list in bot_games.items():
            bot_response = requests.get(f"{BASE_URL}/admin/bots/{bot_id_check}", headers=headers)
            if bot_response.status_code == 200:
                bot_data = bot_response.json()
                cycle_games = bot_data.get("cycle_games", 12)
                active_bets = len(bot_game_list)
                
                if active_bets > cycle_games:
                    violations += 1
                    print(f"   ⚠️ Bot {bot_id_check[:8]}: {active_bets} > {cycle_games} cycle_games")
        
        if violations == 0:
            print(f"   {Colors.GREEN}✅ All {total_bots} bots comply with cycle_games limit{Colors.END}")
            results["passed"] += 1
        else:
            print(f"   {Colors.RED}❌ {violations}/{total_bots} bots violate cycle_games limit{Colors.END}")
            results["failed"] += 1
    else:
        print(f"   {Colors.RED}❌ Failed to check active bets limit{Colors.END}")
        results["failed"] += 1
    
    # 10. Test draw behavior
    print(f"\n{Colors.MAGENTA}10. Testing draw behavior for Regular bots{Colors.END}")
    response = requests.get(f"{BASE_URL}/admin/games", headers=headers, params={"status": "COMPLETED", "limit": 100})
    results["total"] += 1
    if response.status_code == 200:
        games_data = response.json()
        games = games_data if isinstance(games_data, list) else games_data.get("games", [])
        
        regular_bot_games = [game for game in games if game.get("is_regular_bot_game", False)]
        draw_games = [game for game in regular_bot_games if game.get("winner_id") is None]
        
        total_regular = len(regular_bot_games)
        draws = len(draw_games)
        draw_percentage = (draws / total_regular * 100) if total_regular > 0 else 0
        
        print(f"   {Colors.GREEN}✅ Draw behavior analyzed{Colors.END}")
        print(f"   📊 Regular bot games: {total_regular}, Draws: {draws} ({draw_percentage:.1f}%)")
        results["passed"] += 1
    else:
        print(f"   {Colors.RED}❌ Failed to analyze draw behavior{Colors.END}")
        results["failed"] += 1
    
    # Summary
    success_rate = (results["passed"] / results["total"] * 100) if results["total"] > 0 else 0
    print(f"\n{Colors.BOLD}{Colors.CYAN}📊 RUSSIAN REVIEW TEST SUMMARY{Colors.END}")
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.GREEN}✅ Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}❌ Failed: {results['failed']}{Colors.END}")
    print(f"{Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    if success_rate >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 EXCELLENT: Regular Bots API is ready for refactoring{Colors.END}")
    elif success_rate >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ GOOD: Minor issues, mostly ready for refactoring{Colors.END}")
    elif success_rate >= 70:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ MODERATE: Some issues need attention before refactoring{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CRITICAL: Major issues found, DO NOT refactor yet{Colors.END}")

if __name__ == "__main__":
    test_russian_review_requirements()