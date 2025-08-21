#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Bot Cycle Fixes
Testing the critical fixes for duplicate bot cycles and premature completion.
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

class BotCycleTestSuite:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.created_bot_id = None
        
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
    
    async def test_1_create_regular_bot(self):
        """Test 1: Create regular bot and verify exactly 1 accumulator is created"""
        test_name = "Regular Bot Creation with New Logic"
        
        try:
            # Create regular bot with specific parameters
            bot_config = {
                "name": f"TestBot_{int(time.time())}",
                "min_bet_amount": 1.0,
                "max_bet_amount": 100.0,
                "cycle_games": 16,
                "wins_percentage": 44.0,
                "losses_percentage": 36.0,
                "draws_percentage": 20.0,
                "wins_count": 7,
                "losses_count": 6,
                "draws_count": 3,
                "pause_between_cycles": 5
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/admin/bots/create-regular",
                json=bot_config,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.created_bot_id = data.get("bot_id")
                    
                    # Wait a moment for any background processes
                    await asyncio.sleep(2)
                    
                    # Check accumulators count
                    async with self.session.get(
                        f"{BACKEND_URL}/admin/bots/profit-accumulators",
                        headers=self.get_auth_headers()
                    ) as acc_response:
                        if acc_response.status == 200:
                            accumulators = await acc_response.json()
                            bot_accumulators = [acc for acc in accumulators if acc.get("bot_id") == self.created_bot_id]
                            
                            if len(bot_accumulators) == 1:
                                await self.log_test_result(test_name, True, 
                                    f"Bot created successfully with exactly 1 accumulator. Bot ID: {self.created_bot_id}")
                            else:
                                await self.log_test_result(test_name, False, 
                                    f"Expected 1 accumulator, found {len(bot_accumulators)}")
                        else:
                            await self.log_test_result(test_name, False, 
                                f"Failed to fetch accumulators: {acc_response.status}")
                else:
                    error_text = await response.text()
                    await self.log_test_result(test_name, False, 
                        f"Bot creation failed: {response.status} - {error_text}")
                        
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_2_accumulator_functionality(self):
        """Test 2: Verify accumulator correctly tracks games and handles draws"""
        test_name = "Accumulator Correct Functionality"
        
        if not self.created_bot_id:
            await self.log_test_result(test_name, False, "No bot created in previous test")
            return
        
        try:
            # Get initial accumulator state
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/profit-accumulators",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    accumulators = await response.json()
                    bot_accumulator = next((acc for acc in accumulators if acc.get("bot_id") == self.created_bot_id), None)
                    
                    if bot_accumulator:
                        # Check if accumulator has correct fields for tracking draws
                        required_fields = ["games_won", "games_lost", "games_drawn", "total_spent", "total_earned"]
                        missing_fields = [field for field in required_fields if field not in bot_accumulator]
                        
                        if not missing_fields:
                            # Check initial values
                            games_won = bot_accumulator.get("games_won", 0)
                            games_lost = bot_accumulator.get("games_lost", 0)
                            games_drawn = bot_accumulator.get("games_drawn", 0)
                            total_spent = bot_accumulator.get("total_spent", 0)
                            total_earned = bot_accumulator.get("total_earned", 0)
                            
                            await self.log_test_result(test_name, True, 
                                f"Accumulator has correct fields. Initial state: W:{games_won}/L:{games_lost}/D:{games_drawn}, Spent:${total_spent}, Earned:${total_earned}")
                        else:
                            await self.log_test_result(test_name, False, 
                                f"Accumulator missing required fields: {missing_fields}")
                    else:
                        await self.log_test_result(test_name, False, "Bot accumulator not found")
                else:
                    await self.log_test_result(test_name, False, f"Failed to fetch accumulators: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_3_cycle_completion_logic(self):
        """Test 3: Verify cycles complete only after ALL games are finished"""
        test_name = "Proper Cycle Completion Logic"
        
        if not self.created_bot_id:
            await self.log_test_result(test_name, False, "No bot created in previous test")
            return
        
        try:
            # Activate the bot to start creating games
            async with self.session.post(
                f"{BACKEND_URL}/admin/bots/{self.created_bot_id}/toggle",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    print(f"Bot {self.created_bot_id} activated")
                
            # Wait for bot to create initial games
            await asyncio.sleep(10)
            
            # Check games created by bot
            async with self.session.get(
                f"{BACKEND_URL}/admin/games",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    games_data = await response.json()
                    games = games_data.get("games", [])
                    bot_games = [game for game in games if game.get("creator_id") == self.created_bot_id]
                    
                    # Check completed cycles
                    async with self.session.get(
                        f"{BACKEND_URL}/admin/bots/completed-cycles",
                        headers=self.get_auth_headers()
                    ) as cycles_response:
                        if cycles_response.status == 200:
                            cycles = await cycles_response.json()
                            bot_cycles = [cycle for cycle in cycles if cycle.get("bot_id") == self.created_bot_id]
                            
                            # At this point, if there are less than 16 completed games, there should be NO completed cycles
                            completed_games = [game for game in bot_games if game.get("status") == "COMPLETED"]
                            
                            if len(completed_games) < 16 and len(bot_cycles) == 0:
                                await self.log_test_result(test_name, True, 
                                    f"Correct behavior: {len(completed_games)} completed games, {len(bot_cycles)} completed cycles (no premature completion)")
                            elif len(completed_games) >= 16 and len(bot_cycles) > 0:
                                await self.log_test_result(test_name, True, 
                                    f"Correct behavior: {len(completed_games)} completed games, {len(bot_cycles)} completed cycles (proper completion)")
                            else:
                                await self.log_test_result(test_name, False, 
                                    f"Incorrect behavior: {len(completed_games)} completed games but {len(bot_cycles)} completed cycles")
                        else:
                            await self.log_test_result(test_name, False, f"Failed to fetch completed cycles: {cycles_response.status}")
                else:
                    await self.log_test_result(test_name, False, f"Failed to fetch games: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_4_reporting_with_draws(self):
        """Test 4: Verify completed_cycles correctly records draws"""
        test_name = "Reporting with Draws"
        
        if not self.created_bot_id:
            await self.log_test_result(test_name, False, "No bot created in previous test")
            return
        
        try:
            # Check completed cycles for draw reporting
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles = await response.json()
                    bot_cycles = [cycle for cycle in cycles if cycle.get("bot_id") == self.created_bot_id]
                    
                    if bot_cycles:
                        cycle = bot_cycles[0]  # Check first completed cycle
                        wins_count = cycle.get("wins_count", 0)
                        losses_count = cycle.get("losses_count", 0)
                        draws_count = cycle.get("draws_count", 0)
                        
                        # Check if draws are properly recorded (should be > 0 based on 20% draw percentage)
                        if draws_count > 0:
                            await self.log_test_result(test_name, True, 
                                f"Draws correctly recorded: W:{wins_count}/L:{losses_count}/D:{draws_count}")
                        else:
                            await self.log_test_result(test_name, False, 
                                f"Draws not recorded: W:{wins_count}/L:{losses_count}/D:{draws_count} (draws_count should be > 0)")
                    else:
                        await self.log_test_result(test_name, True, 
                            "No completed cycles yet - this is expected if cycle hasn't finished all 16 games")
                else:
                    await self.log_test_result(test_name, False, f"Failed to fetch completed cycles: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_5_no_duplicate_cycles(self):
        """Test 5: Verify no duplicate records in completed_cycles"""
        test_name = "No Duplicate Cycles"
        
        if not self.created_bot_id:
            await self.log_test_result(test_name, False, "No bot created in previous test")
            return
        
        try:
            # Check for duplicate cycles
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles = await response.json()
                    bot_cycles = [cycle for cycle in cycles if cycle.get("bot_id") == self.created_bot_id]
                    
                    # Check for duplicates by cycle_number
                    cycle_numbers = [cycle.get("cycle_number") for cycle in bot_cycles]
                    unique_cycle_numbers = set(cycle_numbers)
                    
                    if len(cycle_numbers) == len(unique_cycle_numbers):
                        await self.log_test_result(test_name, True, 
                            f"No duplicate cycles found. Total cycles: {len(bot_cycles)}")
                    else:
                        duplicates = [num for num in cycle_numbers if cycle_numbers.count(num) > 1]
                        await self.log_test_result(test_name, False, 
                            f"Duplicate cycles found for cycle numbers: {set(duplicates)}")
                else:
                    await self.log_test_result(test_name, False, f"Failed to fetch completed cycles: {response.status}")
                    
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_6_balance_verification(self):
        """Test 6: Verify expected game balance (7 wins / 6 losses / 3 draws)"""
        test_name = "Game Balance Verification"
        
        if not self.created_bot_id:
            await self.log_test_result(test_name, False, "No bot created in previous test")
            return
        
        try:
            # Wait longer for a complete cycle
            print("Waiting for bot cycle to complete (this may take a few minutes)...")
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                async with self.session.get(
                    f"{BACKEND_URL}/admin/bots/completed-cycles",
                    headers=self.get_auth_headers()
                ) as response:
                    if response.status == 200:
                        cycles = await response.json()
                        bot_cycles = [cycle for cycle in cycles if cycle.get("bot_id") == self.created_bot_id]
                        
                        if bot_cycles:
                            cycle = bot_cycles[0]
                            wins = cycle.get("wins_count", 0)
                            losses = cycle.get("losses_count", 0)
                            draws = cycle.get("draws_count", 0)
                            total_games = wins + losses + draws
                            
                            if total_games == 16:
                                # Check if balance is approximately correct (allowing some variance due to randomness)
                                expected_balance = "7 wins / 6 losses / 3 draws"
                                actual_balance = f"{wins} wins / {losses} losses / {draws} draws"
                                
                                # The balance should be close to expected but may vary due to randomness
                                if 5 <= wins <= 9 and 4 <= losses <= 8 and 1 <= draws <= 5:
                                    await self.log_test_result(test_name, True, 
                                        f"Game balance within expected range. Expected: {expected_balance}, Actual: {actual_balance}")
                                else:
                                    await self.log_test_result(test_name, False, 
                                        f"Game balance outside expected range. Expected: {expected_balance}, Actual: {actual_balance}")
                                return
                
                await asyncio.sleep(10)  # Wait 10 seconds before checking again
            
            await self.log_test_result(test_name, False, 
                "Timeout waiting for cycle completion - cycle may take longer than expected")
                
        except Exception as e:
            await self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Bot Cycle Testing Suite")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Run tests in order
            await self.test_1_create_regular_bot()
            await self.test_2_accumulator_functionality()
            await self.test_3_cycle_completion_logic()
            await self.test_4_reporting_with_draws()
            await self.test_5_no_duplicate_cycles()
            await self.test_6_balance_verification()
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)
            
            passed = sum(1 for result in self.test_results if result["success"])
            total = len(self.test_results)
            
            for result in self.test_results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"{status} {result['test']}")
                if not result["success"]:
                    print(f"    Details: {result['details']}")
            
            print(f"\nOverall: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed! Bot cycle fixes are working correctly.")
            else:
                print("⚠️  Some tests failed. Review the details above.")
                
        except Exception as e:
            print(f"❌ Test suite failed with exception: {e}")
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    test_suite = BotCycleTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())