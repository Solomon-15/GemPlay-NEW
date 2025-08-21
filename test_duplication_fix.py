#!/usr/bin/env python3
"""
Test script to verify the complete fix for bot data duplication issue.
Tests the specific fixes mentioned in the review request.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://russian-only.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"
TEST_BOT_ID = "75646e1d-55cd-4941-8e6b-55474c5f7c42"

class DuplicationFixTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        
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
    
    async def test_new_bot_cycle_completion(self):
        """Test that new bot creates exactly 16 games and correct W/L/D balance"""
        print(f"\n🔍 Testing new bot {TEST_BOT_ID} for duplication fixes...")
        
        max_wait_time = 600  # 10 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check completed cycles
                async with self.session.get(
                    f"{BACKEND_URL}/admin/bots/{TEST_BOT_ID}/completed-cycles",
                    headers=self.get_auth_headers()
                ) as response:
                    if response.status == 200:
                        cycles_data = await response.json()
                        bot_cycles = cycles_data.get("cycles", [])
                        
                        if bot_cycles:
                            print(f"✅ Found {len(bot_cycles)} completed cycle(s)")
                            
                            # Test the first completed cycle
                            cycle = bot_cycles[0]
                            
                            # Extract key metrics
                            total_games = cycle.get("total_games", 0)
                            wins = cycle.get("wins", 0)
                            losses = cycle.get("losses", 0)
                            draws = cycle.get("draws", 0)
                            total_losses = cycle.get("total_losses", 0)
                            roi_percent = cycle.get("roi_percent", 0)
                            
                            print(f"\n📊 CYCLE ANALYSIS:")
                            print(f"   Total Games: {total_games} (Expected: 16)")
                            print(f"   W/L/D: {wins}/{losses}/{draws} (Expected: ~7/6/3)")
                            print(f"   Total Losses: ${total_losses} (Expected: > 0)")
                            print(f"   ROI: {roi_percent}% (Expected: ~10%)")
                            
                            # Verify fixes
                            issues_found = []
                            
                            # Test 1: Total games should be 16, not 32
                            if total_games == 16:
                                print(f"   ✅ FIXED: Total games = {total_games} (NOT doubled)")
                            else:
                                print(f"   ❌ ISSUE: Total games = {total_games} (should be 16)")
                                issues_found.append(f"Total games doubled: {total_games} instead of 16")
                            
                            # Test 2: W/L/D should sum to 16 and be around 7/6/3
                            total_wld = wins + losses + draws
                            if total_wld == 16:
                                print(f"   ✅ FIXED: W+L+D = {total_wld} (correct sum)")
                            else:
                                print(f"   ❌ ISSUE: W+L+D = {total_wld} (should be 16)")
                                issues_found.append(f"W/L/D sum incorrect: {total_wld} instead of 16")
                            
                            # Check if W/L/D are in reasonable range (allowing for randomness)
                            if 5 <= wins <= 9 and 4 <= losses <= 8 and 1 <= draws <= 5:
                                print(f"   ✅ FIXED: W/L/D balance reasonable: {wins}/{losses}/{draws}")
                            else:
                                print(f"   ❌ ISSUE: W/L/D balance unreasonable: {wins}/{losses}/{draws}")
                                issues_found.append(f"W/L/D balance outside expected range")
                            
                            # Test 3: Total losses should be > 0
                            if total_losses > 0:
                                print(f"   ✅ FIXED: Total losses = ${total_losses} (NOT $0)")
                            else:
                                print(f"   ❌ ISSUE: Total losses = ${total_losses} (should be > 0)")
                                issues_found.append(f"Total losses is $0 despite having losses")
                            
                            # Test 4: ROI should be reasonable (~10%, not 100%)
                            if 5 <= roi_percent <= 20:
                                print(f"   ✅ FIXED: ROI = {roi_percent}% (reasonable range)")
                            else:
                                print(f"   ❌ ISSUE: ROI = {roi_percent}% (should be ~10%)")
                                issues_found.append(f"ROI outside reasonable range: {roi_percent}%")
                            
                            # Summary
                            if not issues_found:
                                print(f"\n🎉 ALL FIXES VERIFIED! No duplication issues found.")
                                return True
                            else:
                                print(f"\n⚠️  ISSUES STILL PRESENT:")
                                for issue in issues_found:
                                    print(f"   - {issue}")
                                return False
                        else:
                            elapsed = int(time.time() - start_time)
                            print(f"   ⏳ Waiting for cycle completion... ({elapsed}s elapsed)")
                    else:
                        print(f"   ❌ API Error: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            await asyncio.sleep(15)  # Check every 15 seconds
        
        print(f"\n⏰ Timeout: No completed cycles found within {max_wait_time} seconds")
        return False
    
    async def test_old_bot_data_corruption(self):
        """Test that old bot data still shows the corruption (to confirm the issue existed)"""
        print(f"\n🔍 Testing old bot f70aaf4a-17be-4ada-a142-e29fe219abe9 for data corruption...")
        
        try:
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
                        
                        print(f"📊 OLD BOT DATA (before fix):")
                        print(f"   Total Games: {total_games}")
                        print(f"   W/L/D: {wins}/{losses}/{draws}")
                        print(f"   Total Losses: ${total_losses}")
                        
                        # Confirm corruption exists in old data
                        corruption_found = []
                        if total_games == 32:
                            corruption_found.append("Total games doubled (32 instead of 16)")
                        if wins == 14 and losses == 12 and draws == 6:
                            corruption_found.append("W/L/D values doubled (14/12/6 instead of 7/6/3)")
                        if total_losses == 0:
                            corruption_found.append("Total losses is $0 despite having losses")
                        
                        if corruption_found:
                            print(f"   ✅ CONFIRMED: Old data shows corruption (as expected):")
                            for issue in corruption_found:
                                print(f"      - {issue}")
                        else:
                            print(f"   ⚠️  Old data doesn't show expected corruption")
                        
                        return len(corruption_found) > 0
                    else:
                        print(f"   ❌ No cycles found for old bot")
                        return False
                else:
                    print(f"   ❌ API Error: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of the duplication fix"""
        print("🚀 COMPREHENSIVE TEST: Bot Data Duplication Fix")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Test 1: Confirm old data corruption exists
            print("\n1️⃣ TESTING OLD DATA CORRUPTION")
            old_corruption_confirmed = await self.test_old_bot_data_corruption()
            
            # Test 2: Test new bot with fixes
            print("\n2️⃣ TESTING NEW BOT WITH FIXES")
            new_bot_fixed = await self.test_new_bot_cycle_completion()
            
            # Final summary
            print("\n" + "=" * 60)
            print("📋 FINAL TEST SUMMARY")
            print("=" * 60)
            
            if old_corruption_confirmed:
                print("✅ Old data corruption confirmed (validates the issue existed)")
            else:
                print("⚠️  Old data corruption not found (unexpected)")
            
            if new_bot_fixed:
                print("✅ New bot data shows fixes are working correctly")
                print("🎉 DUPLICATION FIX VERIFICATION: SUCCESS")
            else:
                print("❌ New bot data still shows issues")
                print("⚠️  DUPLICATION FIX VERIFICATION: FAILED")
            
            return new_bot_fixed
            
        except Exception as e:
            print(f"❌ Test suite failed with exception: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    tester = DuplicationFixTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n🎯 CONCLUSION: The duplication fix is working correctly!")
    else:
        print("\n⚠️  CONCLUSION: Issues still exist or test incomplete.")

if __name__ == "__main__":
    asyncio.run(main())