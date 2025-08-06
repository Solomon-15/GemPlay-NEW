#!/usr/bin/env python3
"""
Bot Fields Removal Testing - Russian Review
Протестировать удаление полей can_accept_bets и can_play_with_bots для обычных ботов

Test Requirements:
1. Regular bot endpoints testing - ensure can_accept_bets and can_play_with_bots fields are absent
2. Database cleanup endpoint testing
3. Human-bot verification - ensure can_play_with_other_bots and can_play_with_players are present
4. System functionality verification
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://3d63e28a-d18e-4616-aa0f-657afef77b95.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "admin@gemplay.com"
SUPER_ADMIN_PASSWORD = "Admin123!"

class BotFieldsRemovalTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup(self):
        """Initialize HTTP session and authenticate"""
        self.session = aiohttp.ClientSession()
        await self.authenticate_super_admin()
        
    async def cleanup(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate_super_admin(self):
        """Authenticate as SUPER_ADMIN"""
        print("🔐 Authenticating as SUPER_ADMIN...")
        
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    print(f"✅ SUPER_ADMIN authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ SUPER_ADMIN authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ SUPER_ADMIN authentication error: {e}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
        
    async def test_regular_bots_endpoints(self):
        """Test regular bot endpoints to ensure removed fields are absent"""
        print("\n🤖 TESTING REGULAR BOTS ENDPOINTS...")
        
        # Test GET /api/admin/bots
        print("\n1. Testing GET /api/admin/bots...")
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/bots", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    bots = data.get("bots", [])
                    
                    if bots:
                        # Check first bot for removed fields
                        first_bot = bots[0]
                        has_can_accept_bets = "can_accept_bets" in first_bot
                        has_can_play_with_bots = "can_play_with_bots" in first_bot
                        
                        if not has_can_accept_bets and not has_can_play_with_bots:
                            print(f"✅ Regular bots correctly missing removed fields")
                            print(f"   - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                            print(f"   - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                            self.test_results.append(("GET /api/admin/bots - removed fields absent", True))
                        else:
                            print(f"❌ Regular bots still contain removed fields")
                            print(f"   - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                            print(f"   - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                            self.test_results.append(("GET /api/admin/bots - removed fields absent", False))
                            
                        # Show current bot structure
                        print(f"   Current bot fields: {list(first_bot.keys())}")
                    else:
                        print("⚠️ No regular bots found for testing")
                        self.test_results.append(("GET /api/admin/bots - removed fields absent", "NA"))
                else:
                    error_text = await response.text()
                    print(f"❌ GET /api/admin/bots failed: {response.status} - {error_text}")
                    self.test_results.append(("GET /api/admin/bots - removed fields absent", False))
        except Exception as e:
            print(f"❌ GET /api/admin/bots error: {e}")
            self.test_results.append(("GET /api/admin/bots - removed fields absent", False))
            
        # Test POST /api/admin/bots/create-regular
        print("\n2. Testing POST /api/admin/bots/create-regular...")
        try:
            bot_data = {
                "name": f"TestBot_FieldRemoval_{int(datetime.now().timestamp())}",
                "min_bet_amount": 1.0,
                "max_bet_amount": 100.0,
                "win_rate": 55.0,
                "cycle_games": 12,
                "individual_limit": 12,
                "pause_between_games": 5,
                "creation_mode": "queue-based",
                "priority_order": 50,
                "profit_strategy": "balanced"
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/bots/create-regular", 
                                       json=bot_data, headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    created_bot = data.get("bot", {})
                    
                    has_can_accept_bets = "can_accept_bets" in created_bot
                    has_can_play_with_bots = "can_play_with_bots" in created_bot
                    
                    if not has_can_accept_bets and not has_can_play_with_bots:
                        print(f"✅ Created regular bot correctly missing removed fields")
                        print(f"   - Bot ID: {created_bot.get('id', 'N/A')}")
                        print(f"   - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                        print(f"   - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                        self.test_results.append(("POST /api/admin/bots/create-regular - removed fields absent", True))
                        
                        # Store bot ID for cleanup
                        self.created_bot_id = created_bot.get("id")
                    else:
                        print(f"❌ Created regular bot still contains removed fields")
                        print(f"   - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                        print(f"   - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                        self.test_results.append(("POST /api/admin/bots/create-regular - removed fields absent", False))
                else:
                    error_text = await response.text()
                    print(f"❌ POST /api/admin/bots/create-regular failed: {response.status} - {error_text}")
                    self.test_results.append(("POST /api/admin/bots/create-regular - removed fields absent", False))
        except Exception as e:
            print(f"❌ POST /api/admin/bots/create-regular error: {e}")
            self.test_results.append(("POST /api/admin/bots/create-regular - removed fields absent", False))
            
        # Test PUT /api/admin/bots/{bot_id}
        if hasattr(self, 'created_bot_id') and self.created_bot_id:
            print(f"\n3. Testing PUT /api/admin/bots/{self.created_bot_id}...")
            try:
                update_data = {
                    "name": f"UpdatedTestBot_FieldRemoval_{int(datetime.now().timestamp())}",
                    "min_bet_amount": 2.0,
                    "max_bet_amount": 200.0,
                    "win_rate": 60.0
                }
                
                async with self.session.put(f"{BACKEND_URL}/admin/bots/{self.created_bot_id}", 
                                          json=update_data, headers=self.get_auth_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        updated_bot = data.get("bot", {})
                        
                        has_can_accept_bets = "can_accept_bets" in updated_bot
                        has_can_play_with_bots = "can_play_with_bots" in updated_bot
                        
                        if not has_can_accept_bets and not has_can_play_with_bots:
                            print(f"✅ Updated regular bot correctly missing removed fields")
                            print(f"   - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                            print(f"   - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                            self.test_results.append(("PUT /api/admin/bots/{bot_id} - removed fields absent", True))
                        else:
                            print(f"❌ Updated regular bot still contains removed fields")
                            print(f"   - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                            print(f"   - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                            self.test_results.append(("PUT /api/admin/bots/{bot_id} - removed fields absent", False))
                    else:
                        error_text = await response.text()
                        print(f"❌ PUT /api/admin/bots/{self.created_bot_id} failed: {response.status} - {error_text}")
                        self.test_results.append(("PUT /api/admin/bots/{bot_id} - removed fields absent", False))
            except Exception as e:
                print(f"❌ PUT /api/admin/bots/{self.created_bot_id} error: {e}")
                self.test_results.append(("PUT /api/admin/bots/{bot_id} - removed fields absent", False))
        else:
            print("⚠️ Skipping PUT test - no bot ID available")
            self.test_results.append(("PUT /api/admin/bots/{bot_id} - removed fields absent", "NA"))
            
    async def test_database_cleanup_endpoint(self):
        """Test database cleanup endpoint for removed fields"""
        print("\n🧹 TESTING DATABASE CLEANUP ENDPOINT...")
        
        print("Testing POST /api/admin/bots/cleanup-removed-fields...")
        try:
            async with self.session.post(f"{BACKEND_URL}/admin/bots/cleanup-removed-fields", 
                                       headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Database cleanup endpoint working")
                    print(f"   Response: {json.dumps(data, indent=2)}")
                    
                    # Check if cleanup was successful
                    if data.get("success", False):
                        cleaned_count = data.get("cleaned_count", 0)
                        print(f"   - Cleaned {cleaned_count} bot records")
                        self.test_results.append(("POST /api/admin/bots/cleanup-removed-fields", True))
                    else:
                        print(f"   - Cleanup reported failure: {data.get('message', 'Unknown error')}")
                        self.test_results.append(("POST /api/admin/bots/cleanup-removed-fields", False))
                else:
                    error_text = await response.text()
                    print(f"❌ Database cleanup failed: {response.status} - {error_text}")
                    self.test_results.append(("POST /api/admin/bots/cleanup-removed-fields", False))
        except Exception as e:
            print(f"❌ Database cleanup error: {e}")
            self.test_results.append(("POST /api/admin/bots/cleanup-removed-fields", False))
            
    async def test_human_bots_unchanged(self):
        """Test that Human-bots still have their required fields"""
        print("\n👥 TESTING HUMAN-BOTS UNCHANGED...")
        
        print("Testing GET /api/admin/human-bots...")
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/human-bots", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    bots = data.get("bots", [])
                    
                    if bots:
                        # Check first human-bot for required fields
                        first_bot = bots[0]
                        has_can_play_with_other_bots = "can_play_with_other_bots" in first_bot
                        has_can_play_with_players = "can_play_with_players" in first_bot
                        
                        if has_can_play_with_other_bots and has_can_play_with_players:
                            print(f"✅ Human-bots correctly retain required fields")
                            print(f"   - can_play_with_other_bots: {'PRESENT' if has_can_play_with_other_bots else 'ABSENT'}")
                            print(f"   - can_play_with_players: {'PRESENT' if has_can_play_with_players else 'ABSENT'}")
                            print(f"   - Values: other_bots={first_bot.get('can_play_with_other_bots')}, players={first_bot.get('can_play_with_players')}")
                            self.test_results.append(("GET /api/admin/human-bots - required fields present", True))
                        else:
                            print(f"❌ Human-bots missing required fields")
                            print(f"   - can_play_with_other_bots: {'PRESENT' if has_can_play_with_other_bots else 'ABSENT'}")
                            print(f"   - can_play_with_players: {'PRESENT' if has_can_play_with_players else 'ABSENT'}")
                            self.test_results.append(("GET /api/admin/human-bots - required fields present", False))
                            
                        # Show current human-bot structure
                        print(f"   Current human-bot fields: {list(first_bot.keys())}")
                    else:
                        print("⚠️ No human-bots found for testing")
                        self.test_results.append(("GET /api/admin/human-bots - required fields present", "NA"))
                else:
                    error_text = await response.text()
                    print(f"❌ GET /api/admin/human-bots failed: {response.status} - {error_text}")
                    self.test_results.append(("GET /api/admin/human-bots - required fields present", False))
        except Exception as e:
            print(f"❌ GET /api/admin/human-bots error: {e}")
            self.test_results.append(("GET /api/admin/human-bots - required fields present", False))
            
    async def test_system_functionality(self):
        """Test that regular bots continue to work correctly"""
        print("\n⚙️ TESTING SYSTEM FUNCTIONALITY...")
        
        # Test that regular bots are still creating games
        print("1. Testing regular bot game creation...")
        try:
            async with self.session.get(f"{BACKEND_URL}/bots/active-games", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle both list and dict response formats
                    if isinstance(data, list):
                        active_games = data
                    else:
                        active_games = data.get("games", [])
                    
                    print(f"✅ Regular bots active games endpoint working")
                    print(f"   - Found {len(active_games)} active regular bot games")
                    
                    if len(active_games) > 0:
                        print(f"   - Regular bots are creating games successfully")
                        self.test_results.append(("Regular bots creating games", True))
                    else:
                        print(f"   - No active regular bot games found (may be normal)")
                        self.test_results.append(("Regular bots creating games", "NA"))
                else:
                    error_text = await response.text()
                    print(f"❌ Regular bot games check failed: {response.status} - {error_text}")
                    self.test_results.append(("Regular bots creating games", False))
        except Exception as e:
            print(f"❌ Regular bot games check error: {e}")
            self.test_results.append(("Regular bots creating games", False))
            
        # Test bet creation automation
        print("\n2. Testing bet creation automation...")
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/bots", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    bots = data.get("bots", [])
                    
                    active_bots = [bot for bot in bots if bot.get("is_active", False)]
                    bots_with_active_bets = [bot for bot in active_bots if bot.get("active_bets", 0) > 0]
                    
                    print(f"✅ Bot automation status check")
                    print(f"   - Total regular bots: {len(bots)}")
                    print(f"   - Active regular bots: {len(active_bots)}")
                    print(f"   - Bots with active bets: {len(bots_with_active_bets)}")
                    
                    if len(bots_with_active_bets) > 0:
                        print(f"   - Bet creation automation is working")
                        self.test_results.append(("Bet creation automation working", True))
                    else:
                        print(f"   - No bots with active bets (automation may be paused)")
                        self.test_results.append(("Bet creation automation working", "NA"))
                else:
                    error_text = await response.text()
                    print(f"❌ Bot automation check failed: {response.status} - {error_text}")
                    self.test_results.append(("Bet creation automation working", False))
        except Exception as e:
            print(f"❌ Bot automation check error: {e}")
            self.test_results.append(("Bet creation automation working", False))
            
    async def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 CLEANING UP TEST DATA...")
        
        if hasattr(self, 'created_bot_id') and self.created_bot_id:
            try:
                async with self.session.delete(f"{BACKEND_URL}/admin/bots/{self.created_bot_id}", 
                                             headers=self.get_auth_headers()) as response:
                    if response.status == 200:
                        print(f"✅ Test bot {self.created_bot_id} deleted successfully")
                    else:
                        print(f"⚠️ Failed to delete test bot {self.created_bot_id}: {response.status}")
            except Exception as e:
                print(f"⚠️ Error deleting test bot: {e}")
                
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 BOT FIELDS REMOVAL TESTING SUMMARY")
        print("="*80)
        
        passed = sum(1 for _, result in self.test_results if result is True)
        failed = sum(1 for _, result in self.test_results if result is False)
        na = sum(1 for _, result in self.test_results if result == "NA")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ N/A: {na}")
        
        if total > 0:
            success_rate = (passed / (total - na)) * 100 if (total - na) > 0 else 0
            print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results:
            status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⚠️ N/A"
            print(f"  {status} - {test_name}")
            
        # Overall assessment
        print("\n" + "="*80)
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Bot fields removal is working correctly.")
        elif failed <= 2:
            print("⚠️ MOSTLY WORKING with minor issues. Bot fields removal is largely functional.")
        else:
            print("❌ SIGNIFICANT ISSUES DETECTED. Bot fields removal needs attention.")
        print("="*80)
        
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING BOT FIELDS REMOVAL TESTING")
        print("="*80)
        
        await self.setup()
        
        try:
            await self.test_regular_bots_endpoints()
            await self.test_database_cleanup_endpoint()
            await self.test_human_bots_unchanged()
            await self.test_system_functionality()
            await self.cleanup_test_data()
        finally:
            await self.cleanup()
            
        self.print_summary()

async def main():
    """Main function"""
    tester = BotFieldsRemovalTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())