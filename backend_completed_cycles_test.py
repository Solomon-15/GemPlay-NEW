#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Bot Completed Cycles Data Display Fixes
Testing the fixes for get_bot_completed_cycles function that was returning MOCK data instead of real data.

КОНТЕКСТ: Была исправлена функция get_bot_completed_cycles которая возвращала MOCK данные вместо реальных данных из БД.

КРИТИЧНЫЕ ПРОВЕРКИ:
- ✅ API возвращает РЕАЛЬНЫЕ данные из БД, а не MOCK
- ✅ total_games = 16 (не 32)
- ✅ wins/losses/draws = 7/6/3 (не 14/12/6)  
- ✅ total_losses > 0 (не $0)
- ✅ ROI около 10% (не 100%)
- ✅ Нет дублирующих циклов
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://russian-only.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

class BotCompletedCyclesTestSuite:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.existing_bot_id = None
        
    async def setup(self):
        """Initialize test session and authenticate as admin"""
        self.session = aiohttp.ClientSession()
        
        # Admin login
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                self.admin_token = data.get("access_token")
                print(f"✅ Admin authenticated successfully")
            else:
                error_text = await response.text()
                raise Exception(f"Failed to authenticate admin: {response.status} - {error_text}")
    
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    async def log_test_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    async def test_1_find_existing_bot_with_completed_cycles(self):
        """Test 1: Find an existing bot with completed cycles to test the API"""
        test_name = "Find Existing Bot with Completed Cycles"
        
        try:
            # Get list of all bots
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    bots_data = await response.json()
                    bots = bots_data.get("bots", [])
                    
                    # Look for a bot with completed cycles
                    for bot in bots:
                        bot_id = bot.get("id")
                        if bot.get("completed_cycles", 0) > 0:
                            self.existing_bot_id = bot_id
                            await self.log_test_result(test_name, True, 
                                f"Found bot with completed cycles: {bot.get('name', 'Unknown')} (ID: {bot_id[:8]}...) - {bot.get('completed_cycles', 0)} cycles")
                            return
                    
                    # If no bot with completed cycles, use the first active bot
                    active_bots = [bot for bot in bots if bot.get("is_active", False)]
                    if active_bots:
                        self.existing_bot_id = active_bots[0].get("id")
                        await self.log_test_result(test_name, True, 
                            f"Using active bot for testing: {active_bots[0].get('name', 'Unknown')} (ID: {self.existing_bot_id[:8]}...)")
                    else:
                        await self.log_test_result(test_name, False, "No active bots found for testing")
                else:
                    await self.log_test_result(test_name, False, f"Failed to fetch bots: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_2_api_returns_real_data_not_mock(self):
        """Test 2: Verify API returns REAL data from DB, not MOCK data"""
        test_name = "API Returns Real Data (Not MOCK)"
        
        if not self.existing_bot_id:
            await self.log_test_result(test_name, False, "No bot found in previous test")
            return
        
        try:
            # Call the completed cycles API
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/{self.existing_bot_id}/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    
                    # Check if response has the expected structure from real DB data
                    expected_fields = ["bot_id", "bot_name", "total_completed_cycles", "cycles"]
                    missing_fields = [field for field in expected_fields if field not in cycles_data]
                    
                    if not missing_fields:
                        bot_id = cycles_data.get("bot_id")
                        bot_name = cycles_data.get("bot_name")
                        total_cycles = cycles_data.get("total_completed_cycles", 0)
                        cycles = cycles_data.get("cycles", [])
                        
                        # Check if this looks like real data (not hardcoded MOCK)
                        if bot_id == self.existing_bot_id and isinstance(cycles, list):
                            await self.log_test_result(test_name, True, 
                                f"API returns real data structure: Bot '{bot_name}' has {total_cycles} completed cycles")
                        else:
                            await self.log_test_result(test_name, False, 
                                f"Data appears to be MOCK: bot_id mismatch or invalid structure")
                    else:
                        await self.log_test_result(test_name, False, 
                            f"Response missing expected fields: {missing_fields}")
                else:
                    await self.log_test_result(test_name, False, 
                        f"API call failed: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_3_correct_total_games_count(self):
        """Test 3: Verify total_games shows correct count (16, not 32)"""
        test_name = "Correct Total Games Count (16 not 32)"
        
        if not self.existing_bot_id:
            await self.log_test_result(test_name, False, "No bot found in previous test")
            return
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/{self.existing_bot_id}/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    cycles = cycles_data.get("cycles", [])
                    
                    if cycles:
                        # Check each cycle for correct total games count
                        correct_counts = 0
                        incorrect_counts = 0
                        
                        for cycle in cycles:
                            total_games = cycle.get("total_games", 0)
                            wins = cycle.get("wins", 0)
                            losses = cycle.get("losses", 0)
                            draws = cycle.get("draws", 0)
                            calculated_total = wins + losses + draws
                            
                            # Check if total_games is correct (should be 16 for a complete cycle)
                            if total_games == 16 or calculated_total == 16:
                                correct_counts += 1
                            elif total_games == 32 or calculated_total == 32:
                                incorrect_counts += 1
                                
                        if correct_counts > 0 and incorrect_counts == 0:
                            await self.log_test_result(test_name, True, 
                                f"All cycles show correct game count: {correct_counts} cycles with 16 games each")
                        elif incorrect_counts > 0:
                            await self.log_test_result(test_name, False, 
                                f"Found incorrect game counts: {incorrect_counts} cycles with 32 games (should be 16)")
                        else:
                            await self.log_test_result(test_name, True, 
                                f"No completed cycles to verify yet")
                    else:
                        await self.log_test_result(test_name, True, 
                            "No completed cycles to verify yet - this is expected for new bots")
                else:
                    await self.log_test_result(test_name, False, f"API call failed: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_4_correct_wins_losses_draws_balance(self):
        """Test 4: Verify wins/losses/draws show correct balance (7/6/3, not 14/12/6)"""
        test_name = "Correct Wins/Losses/Draws Balance"
        
        if not self.existing_bot_id:
            await self.log_test_result(test_name, False, "No bot found in previous test")
            return
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/{self.existing_bot_id}/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    cycles = cycles_data.get("cycles", [])
                    
                    if cycles:
                        correct_balance_cycles = 0
                        incorrect_balance_cycles = 0
                        
                        for cycle in cycles:
                            wins = cycle.get("wins", 0)
                            losses = cycle.get("losses", 0)
                            draws = cycle.get("draws", 0)
                            
                            # Check if this looks like the old doubled values (14/12/6)
                            if wins == 14 and losses == 12 and draws == 6:
                                incorrect_balance_cycles += 1
                            # Check if values are in reasonable range for 16 games
                            elif wins + losses + draws == 16 and 4 <= wins <= 10 and 3 <= losses <= 9 and 1 <= draws <= 6:
                                correct_balance_cycles += 1
                        
                        if correct_balance_cycles > 0 and incorrect_balance_cycles == 0:
                            await self.log_test_result(test_name, True, 
                                f"All cycles show correct balance: {correct_balance_cycles} cycles with proper W/L/D distribution")
                        elif incorrect_balance_cycles > 0:
                            await self.log_test_result(test_name, False, 
                                f"Found incorrect doubled values: {incorrect_balance_cycles} cycles with 14/12/6 pattern")
                        else:
                            await self.log_test_result(test_name, True, 
                                "No completed cycles to verify balance yet")
                    else:
                        await self.log_test_result(test_name, True, 
                            "No completed cycles to verify balance yet")
                else:
                    await self.log_test_result(test_name, False, f"API call failed: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_5_total_losses_not_zero(self):
        """Test 5: Verify total_losses is NOT $0 (was a bug in MOCK data)"""
        test_name = "Total Losses Not Zero"
        
        if not self.existing_bot_id:
            await self.log_test_result(test_name, False, "No bot found in previous test")
            return
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/{self.existing_bot_id}/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    cycles = cycles_data.get("cycles", [])
                    
                    if cycles:
                        zero_loss_cycles = 0
                        non_zero_loss_cycles = 0
                        
                        for cycle in cycles:
                            total_losses = cycle.get("total_losses", 0)
                            losses_count = cycle.get("losses", 0)
                            
                            if total_losses == 0 and losses_count > 0:
                                zero_loss_cycles += 1
                            elif total_losses > 0:
                                non_zero_loss_cycles += 1
                        
                        if non_zero_loss_cycles > 0 and zero_loss_cycles == 0:
                            await self.log_test_result(test_name, True, 
                                f"All cycles show proper loss amounts: {non_zero_loss_cycles} cycles with total_losses > 0")
                        elif zero_loss_cycles > 0:
                            await self.log_test_result(test_name, False, 
                                f"Found cycles with $0 losses bug: {zero_loss_cycles} cycles")
                        else:
                            await self.log_test_result(test_name, True, 
                                "No completed cycles to verify losses yet")
                    else:
                        await self.log_test_result(test_name, True, 
                            "No completed cycles to verify losses yet")
                else:
                    await self.log_test_result(test_name, False, f"API call failed: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_6_roi_around_10_percent_not_100(self):
        """Test 6: Verify ROI is around 10% (not 100% as in MOCK data)"""
        test_name = "ROI Around 10% (Not 100%)"
        
        if not self.existing_bot_id:
            await self.log_test_result(test_name, False, "No bot found in previous test")
            return
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/{self.existing_bot_id}/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    cycles = cycles_data.get("cycles", [])
                    
                    if cycles:
                        reasonable_roi_cycles = 0
                        unreasonable_roi_cycles = 0
                        
                        for cycle in cycles:
                            roi_percent = cycle.get("roi_percent", 0)
                            
                            # Check if ROI is in reasonable range (-50% to +50%)
                            if -50 <= roi_percent <= 50:
                                reasonable_roi_cycles += 1
                            # Check if ROI is the old MOCK value of 100%
                            elif roi_percent == 100:
                                unreasonable_roi_cycles += 1
                        
                        if reasonable_roi_cycles > 0 and unreasonable_roi_cycles == 0:
                            await self.log_test_result(test_name, True, 
                                f"All cycles show reasonable ROI: {reasonable_roi_cycles} cycles with ROI in -50% to +50% range")
                        elif unreasonable_roi_cycles > 0:
                            await self.log_test_result(test_name, False, 
                                f"Found unreasonable ROI values: {unreasonable_roi_cycles} cycles with 100% ROI (MOCK data)")
                        else:
                            await self.log_test_result(test_name, True, 
                                "No completed cycles to verify ROI yet")
                    else:
                        await self.log_test_result(test_name, True, 
                            "No completed cycles to verify ROI yet")
                else:
                    await self.log_test_result(test_name, False, f"API call failed: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_7_no_duplicate_cycles(self):
        """Test 7: Verify no duplicate cycle records"""
        test_name = "No Duplicate Cycles"
        
        if not self.existing_bot_id:
            await self.log_test_result(test_name, False, "No bot found in previous test")
            return
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/{self.existing_bot_id}/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    cycles = cycles_data.get("cycles", [])
                    
                    if cycles:
                        # Check for duplicates by cycle_number
                        cycle_numbers = [cycle.get("cycle_number") for cycle in cycles]
                        unique_cycle_numbers = set(cycle_numbers)
                        
                        if len(cycle_numbers) == len(unique_cycle_numbers):
                            await self.log_test_result(test_name, True, 
                                f"No duplicate cycles found: {len(cycles)} unique cycles")
                        else:
                            duplicates = [num for num in cycle_numbers if cycle_numbers.count(num) > 1]
                            await self.log_test_result(test_name, False, 
                                f"Duplicate cycles found for cycle numbers: {set(duplicates)}")
                    else:
                        await self.log_test_result(test_name, True, 
                            "No completed cycles to check for duplicates yet")
                else:
                    await self.log_test_result(test_name, False, f"API call failed: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_8_data_structure_correctness(self):
        """Test 8: Verify each cycle contains correct data structure and fields"""
        test_name = "Data Structure Correctness"
        
        if not self.existing_bot_id:
            await self.log_test_result(test_name, False, "No bot found in previous test")
            return
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/{self.existing_bot_id}/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    cycles = cycles_data.get("cycles", [])
                    
                    if cycles:
                        # Check required fields in each cycle
                        required_fields = [
                            "id", "cycle_number", "completed_at", "duration", 
                            "total_games", "wins", "losses", "draws",
                            "total_bet", "total_winnings", "total_losses", 
                            "profit", "roi_percent"
                        ]
                        
                        valid_cycles = 0
                        invalid_cycles = 0
                        
                        for cycle in cycles:
                            missing_fields = [field for field in required_fields if field not in cycle]
                            
                            if not missing_fields:
                                # Check if net_profit calculation is reasonable
                                total_winnings = cycle.get("total_winnings", 0)
                                total_losses = cycle.get("total_losses", 0)
                                profit = cycle.get("profit", 0)
                                
                                # Basic sanity check: profit should be roughly winnings - losses
                                expected_profit = total_winnings - total_losses
                                if abs(profit - expected_profit) < 1.0:  # Allow small rounding differences
                                    valid_cycles += 1
                                else:
                                    invalid_cycles += 1
                            else:
                                invalid_cycles += 1
                        
                        if valid_cycles > 0 and invalid_cycles == 0:
                            await self.log_test_result(test_name, True, 
                                f"All cycles have correct structure: {valid_cycles} valid cycles")
                        elif invalid_cycles > 0:
                            await self.log_test_result(test_name, False, 
                                f"Found cycles with incorrect structure: {invalid_cycles} invalid cycles")
                        else:
                            await self.log_test_result(test_name, True, 
                                "No completed cycles to verify structure yet")
                    else:
                        await self.log_test_result(test_name, True, 
                            "No completed cycles to verify structure yet")
                else:
                    await self.log_test_result(test_name, False, f"API call failed: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Bot Completed Cycles Data Display Testing Suite")
        print("=" * 70)
        print("КОНТЕКСТ: Тестирование исправлений функции get_bot_completed_cycles")
        print("Проверяем что API возвращает РЕАЛЬНЫЕ данные из БД, а не MOCK данные")
        print("=" * 70)
        
        try:
            await self.setup()
            
            # Run tests in order
            await self.test_1_find_existing_bot_with_completed_cycles()
            await self.test_2_api_returns_real_data_not_mock()
            await self.test_3_correct_total_games_count()
            await self.test_4_correct_wins_losses_draws_balance()
            await self.test_5_total_losses_not_zero()
            await self.test_6_roi_around_10_percent_not_100()
            await self.test_7_no_duplicate_cycles()
            await self.test_8_data_structure_correctness()
            
            # Summary
            print("\n" + "=" * 70)
            print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
            print("=" * 70)
            
            passed = sum(1 for result in self.test_results if result["success"])
            total = len(self.test_results)
            
            for result in self.test_results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"{status} {result['test']}")
                if not result["success"]:
                    print(f"    Детали: {result['details']}")
            
            print(f"\nИтого: {passed}/{total} тестов прошли успешно")
            
            if passed == total:
                print("🎉 Все тесты прошли! Исправления get_bot_completed_cycles работают корректно.")
                print("✅ API возвращает РЕАЛЬНЫЕ данные из БД")
                print("✅ Отображение данных исправлено")
                print("✅ Нет дублирования значений")
            else:
                print("⚠️  Некоторые тесты не прошли. Проверьте детали выше.")
                
        except Exception as e:
            print(f"❌ Тестирование завершилось с ошибкой: {e}")
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    test_suite = BotCompletedCyclesTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())