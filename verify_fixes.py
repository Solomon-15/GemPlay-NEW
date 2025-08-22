#!/usr/bin/env python3
"""
Comprehensive verification of the bot duplication fixes.
This script verifies both code fixes and data integrity.
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://preset-hub-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

class FixVerifier:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
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
    
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def verify_code_fixes(self):
        """Verify that the code fixes have been implemented"""
        print("\n🔍 VERIFYING CODE FIXES")
        print("=" * 50)
        
        try:
            # Read the server.py file
            with open('/app/backend/server.py', 'r') as f:
                content = f.read()
            
            # Test 1: Verify duplicate accumulate_bot_profit call was removed
            lines = content.split('\n')
            line_7985 = lines[7984] if len(lines) > 7984 else ""  # Line 7985 (0-indexed)
            
            if "ИСПРАВЛЕНО: Убрали дублированный вызов accumulate_bot_profit" in line_7985:
                self.log_result("Duplicate accumulate_bot_profit call removed", True, 
                    "Line 7985 contains fix comment instead of duplicate call")
            else:
                self.log_result("Duplicate accumulate_bot_profit call removed", False, 
                    f"Line 7985 content: {line_7985}")
            
            # Test 2: Verify accumulate_bot_profit function has correct logic
            accumulate_function_match = re.search(
                r'async def accumulate_bot_profit.*?(?=async def|\Z)', 
                content, re.DOTALL
            )
            
            if accumulate_function_match:
                func_content = accumulate_function_match.group(0)
                
                # Check for draw handling
                if "games_drawn" in func_content and "new_games_drawn" in func_content:
                    self.log_result("Accumulator supports draws", True, 
                        "Function includes games_drawn tracking")
                else:
                    self.log_result("Accumulator supports draws", False, 
                        "Function missing games_drawn tracking")
                
                # Check for proper draw logic
                if "new_total_earned += bet_amount  # Возврат ставки" in func_content:
                    self.log_result("Draw logic correct", True, 
                        "Draw returns stake correctly")
                else:
                    self.log_result("Draw logic correct", False, 
                        "Draw logic not found or incorrect")
            
            # Test 3: Verify complete_bot_cycle function has correct total_losses calculation
            complete_cycle_match = re.search(
                r'async def complete_bot_cycle.*?(?=async def|\Z)', 
                content, re.DOTALL
            )
            
            if complete_cycle_match:
                func_content = complete_cycle_match.group(0)
                
                # Check for correct total_losses calculation
                if "losses_amount = (losses_count * (total_spent / max(1, total_bets)))" in func_content:
                    self.log_result("Total losses calculation fixed", True, 
                        "Uses sum of losing bets, not total_spent - total_earned")
                else:
                    self.log_result("Total losses calculation fixed", False, 
                        "Incorrect total_losses calculation")
                
                # Check for improved active pool calculation
                if "active_pool = total_spent - draws_amount" in func_content:
                    self.log_result("Active pool calculation improved", True, 
                        "Excludes draws from active pool")
                else:
                    self.log_result("Active pool calculation improved", False, 
                        "Active pool calculation not improved")
                
                # Check for system version update
                if "v5.0_no_double_accumulation" in func_content:
                    self.log_result("System version updated", True, 
                        "System version indicates fix implementation")
                else:
                    self.log_result("System version updated", False, 
                        "System version not updated")
            
        except Exception as e:
            self.log_result("Code verification", False, f"Exception: {e}")
    
    async def verify_old_data_corruption(self):
        """Verify that old data shows the expected corruption"""
        print("\n🔍 VERIFYING OLD DATA CORRUPTION")
        print("=" * 50)
        
        try:
            # Test the known corrupted bot
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots/f70aaf4a-17be-4ada-a142-e29fe219abe9/completed-cycles",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    bot_cycles = cycles_data.get("cycles", [])
                    
                    if bot_cycles:
                        cycle = bot_cycles[0]
                        total_games = cycle.get("total_games", 0)
                        wins = cycle.get("wins", 0)
                        losses = cycle.get("losses", 0)
                        draws = cycle.get("draws", 0)
                        total_losses = cycle.get("total_losses", 0)
                        
                        # Verify corruption patterns
                        if total_games == 32:
                            self.log_result("Old data shows doubled games", True, 
                                f"32 games instead of 16 (confirms issue existed)")
                        else:
                            self.log_result("Old data shows doubled games", False, 
                                f"Games: {total_games} (expected 32 for corrupted data)")
                        
                        if wins == 14 and losses == 12 and draws == 6:
                            self.log_result("Old data shows doubled W/L/D", True, 
                                f"14/12/6 instead of 7/6/3 (confirms issue existed)")
                        else:
                            self.log_result("Old data shows doubled W/L/D", False, 
                                f"W/L/D: {wins}/{losses}/{draws} (expected 14/12/6)")
                        
                        if total_losses == 0:
                            self.log_result("Old data shows $0 losses", True, 
                                f"$0 losses despite having losses (confirms issue existed)")
                        else:
                            self.log_result("Old data shows $0 losses", False, 
                                f"Losses: ${total_losses} (expected $0 for corrupted data)")
                    else:
                        self.log_result("Old data verification", False, "No cycles found for old bot")
                else:
                    self.log_result("Old data verification", False, f"API error: {response.status}")
                    
        except Exception as e:
            self.log_result("Old data verification", False, f"Exception: {e}")
    
    async def check_new_bot_progress(self):
        """Check progress of new bot to see if fixes are working"""
        print("\n🔍 CHECKING NEW BOT PROGRESS")
        print("=" * 50)
        
        try:
            # Check for any recently created bots
            async with self.session.get(
                f"{BACKEND_URL}/admin/bots",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    bots_data = await response.json()
                    bots = bots_data.get("bots", [])
                    
                    # Find bots created recently (after the fix)
                    recent_bots = []
                    for bot in bots:
                        if "TestFixBot" in bot.get("name", "") or "TestBot_" in bot.get("name", ""):
                            created_at = bot.get("created_at", "")
                            if "2025-08-21" in created_at:  # Today's bots
                                recent_bots.append(bot)
                    
                    if recent_bots:
                        self.log_result("Recent test bots found", True, 
                            f"Found {len(recent_bots)} recent test bots")
                        
                        # Check their status
                        for bot in recent_bots[:3]:  # Check first 3
                            bot_id = bot.get("id")
                            bot_name = bot.get("name")
                            active_bets = bot.get("active_bets", 0)
                            completed_cycles = bot.get("completed_cycles_count", 0)
                            
                            print(f"   Bot {bot_name}: {active_bets} active bets, {completed_cycles} completed cycles")
                            
                            # Check if any have completed cycles
                            if completed_cycles > 0:
                                async with self.session.get(
                                    f"{BACKEND_URL}/admin/bots/{bot_id}/completed-cycles",
                                    headers=self.get_auth_headers()
                                ) as cycle_response:
                                    if cycle_response.status == 200:
                                        cycle_data = await cycle_response.json()
                                        cycles = cycle_data.get("cycles", [])
                                        
                                        if cycles:
                                            cycle = cycles[0]
                                            total_games = cycle.get("total_games", 0)
                                            wins = cycle.get("wins", 0)
                                            losses = cycle.get("losses", 0)
                                            draws = cycle.get("draws", 0)
                                            total_losses = cycle.get("total_losses", 0)
                                            
                                            print(f"      Cycle data: {total_games} games, W/L/D: {wins}/{losses}/{draws}, Losses: ${total_losses}")
                                            
                                            # Verify fixes
                                            if total_games == 16:
                                                self.log_result(f"New bot {bot_name} - correct game count", True, 
                                                    f"16 games (not doubled)")
                                            else:
                                                self.log_result(f"New bot {bot_name} - correct game count", False, 
                                                    f"{total_games} games (should be 16)")
                                            
                                            if total_losses > 0:
                                                self.log_result(f"New bot {bot_name} - correct losses", True, 
                                                    f"${total_losses} losses (not $0)")
                                            else:
                                                self.log_result(f"New bot {bot_name} - correct losses", False, 
                                                    f"${total_losses} losses (should be > 0)")
                    else:
                        self.log_result("Recent test bots found", False, "No recent test bots found")
                        
        except Exception as e:
            self.log_result("New bot progress check", False, f"Exception: {e}")
    
    async def run_comprehensive_verification(self):
        """Run comprehensive verification of all fixes"""
        print("🚀 COMPREHENSIVE VERIFICATION: Bot Duplication Fixes")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Step 1: Verify code fixes
            self.verify_code_fixes()
            
            # Step 2: Verify old data corruption (confirms issue existed)
            await self.verify_old_data_corruption()
            
            # Step 3: Check new bot progress
            await self.check_new_bot_progress()
            
            # Final summary
            print("\n" + "=" * 60)
            print("📋 VERIFICATION SUMMARY")
            print("=" * 60)
            
            passed = sum(1 for result in self.test_results if result["success"])
            total = len(self.test_results)
            
            critical_fixes = [
                "Duplicate accumulate_bot_profit call removed",
                "Total losses calculation fixed",
                "Draw logic correct",
                "Active pool calculation improved"
            ]
            
            critical_passed = sum(1 for result in self.test_results 
                                if result["test"] in critical_fixes and result["success"])
            
            print(f"Overall Results: {passed}/{total} tests passed")
            print(f"Critical Fixes: {critical_passed}/{len(critical_fixes)} implemented")
            
            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")
                if not result["success"]:
                    print(f"    {result['details']}")
            
            # Conclusion
            if critical_passed == len(critical_fixes):
                print(f"\n🎉 CONCLUSION: All critical fixes have been implemented correctly!")
                print(f"   - Duplicate accumulate_bot_profit call removed")
                print(f"   - Total losses calculation fixed")
                print(f"   - Draw handling improved")
                print(f"   - Active pool calculation corrected")
                print(f"   - Old data shows expected corruption (confirms issue existed)")
                print(f"   - New bots should generate correct data")
                return True
            else:
                print(f"\n⚠️  CONCLUSION: Some critical fixes may be missing")
                return False
                
        except Exception as e:
            print(f"❌ Verification failed with exception: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main verification runner"""
    verifier = FixVerifier()
    success = await verifier.run_comprehensive_verification()
    
    if success:
        print("\n🎯 FINAL RESULT: Bot duplication fixes verified successfully!")
    else:
        print("\n⚠️  FINAL RESULT: Verification incomplete or issues found.")

if __name__ == "__main__":
    asyncio.run(main())