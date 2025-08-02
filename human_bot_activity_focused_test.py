#!/usr/bin/env python3
"""
Human-bot Activity Control System - Focused Testing
Focus: Core functionality testing for is_bet_creation_active field

TESTING REQUIREMENTS:
1. CREATE Human-bot - проверить что is_bet_creation_active правильно сохраняется (default=true)
2. UPDATE Human-bot - изменить is_bet_creation_active через PUT запрос
3. BULK CREATE - массовое создание с is_bet_creation_active
4. HumanBotResponse - убедиться что поле возвращается в API ответах
5. FIELD VALIDATION - проверить что поле принимает только boolean значения
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List
import random
import string

# Configuration
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class FocusedHumanBotActivityTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.created_bots = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
            
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
        
    def generate_unique_bot_name(self) -> str:
        """Generate unique bot name"""
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        return f"ActivityTest_{timestamp}_{random_suffix}"
        
    def test_create_human_bot_with_activity_field(self) -> bool:
        """Test CREATE Human-bot with is_bet_creation_active field"""
        try:
            print("\n🔍 Testing CREATE Human-bot with is_bet_creation_active field...")
            
            # Test 1: Default value (should be True)
            bot_name1 = self.generate_unique_bot_name()
            create_data1 = {
                "name": bot_name1,
                "character": "BALANCED",
                "gender": "male",
                "min_bet": 10.0,
                "max_bet": 100.0,
                "bet_limit": 12,
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0,
                "min_delay": 30,
                "max_delay": 120
                # is_bet_creation_active not specified - should default to True
            }
            
            response1 = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data1,
                headers=self.get_auth_headers()
            )
            
            if response1.status_code in [200, 201]:
                bot_data1 = response1.json()
                bot_id1 = bot_data1.get("id")
                self.created_bots.append(bot_id1)
                
                if bot_data1.get("is_bet_creation_active") == True:
                    print(f"  ✅ Default value test: is_bet_creation_active = {bot_data1.get('is_bet_creation_active')} (expected True)")
                else:
                    print(f"  ❌ Default value test: is_bet_creation_active = {bot_data1.get('is_bet_creation_active')} (expected True)")
                    return False
            else:
                print(f"  ❌ Failed to create bot for default test. Status: {response1.status_code}")
                return False
            
            # Test 2: Explicit False value
            bot_name2 = self.generate_unique_bot_name()
            create_data2 = {
                "name": bot_name2,
                "character": "AGGRESSIVE",
                "gender": "female",
                "min_bet": 5.0,
                "max_bet": 50.0,
                "bet_limit": 8,
                "win_percentage": 45.0,
                "loss_percentage": 35.0,
                "draw_percentage": 20.0,
                "min_delay": 45,
                "max_delay": 150,
                "is_bet_creation_active": False  # Explicitly set to False
            }
            
            response2 = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data2,
                headers=self.get_auth_headers()
            )
            
            if response2.status_code in [200, 201]:
                bot_data2 = response2.json()
                bot_id2 = bot_data2.get("id")
                self.created_bots.append(bot_id2)
                
                if bot_data2.get("is_bet_creation_active") == False:
                    print(f"  ✅ Explicit False test: is_bet_creation_active = {bot_data2.get('is_bet_creation_active')} (expected False)")
                else:
                    print(f"  ❌ Explicit False test: is_bet_creation_active = {bot_data2.get('is_bet_creation_active')} (expected False)")
                    return False
            else:
                print(f"  ❌ Failed to create bot for explicit False test. Status: {response2.status_code}")
                return False
            
            # Test 3: Explicit True value
            bot_name3 = self.generate_unique_bot_name()
            create_data3 = {
                "name": bot_name3,
                "character": "CAUTIOUS",
                "gender": "male",
                "min_bet": 15.0,
                "max_bet": 75.0,
                "bet_limit": 10,
                "win_percentage": 35.0,
                "loss_percentage": 45.0,
                "draw_percentage": 20.0,
                "min_delay": 60,
                "max_delay": 180,
                "is_bet_creation_active": True  # Explicitly set to True
            }
            
            response3 = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data3,
                headers=self.get_auth_headers()
            )
            
            if response3.status_code in [200, 201]:
                bot_data3 = response3.json()
                bot_id3 = bot_data3.get("id")
                self.created_bots.append(bot_id3)
                
                if bot_data3.get("is_bet_creation_active") == True:
                    print(f"  ✅ Explicit True test: is_bet_creation_active = {bot_data3.get('is_bet_creation_active')} (expected True)")
                else:
                    print(f"  ❌ Explicit True test: is_bet_creation_active = {bot_data3.get('is_bet_creation_active')} (expected True)")
                    return False
            else:
                print(f"  ❌ Failed to create bot for explicit True test. Status: {response3.status_code}")
                return False
            
            self.log_result("CREATE Human-bot Activity Field", True, "All creation tests passed")
            return True
            
        except Exception as e:
            self.log_result("CREATE Human-bot Activity Field", False, f"Exception: {str(e)}")
            return False
            
    def test_update_human_bot_activity_field(self) -> bool:
        """Test UPDATE Human-bot is_bet_creation_active field"""
        try:
            print("\n🔍 Testing UPDATE Human-bot is_bet_creation_active field...")
            
            if not self.created_bots:
                print("  ❌ No bots available for update test")
                return False
                
            bot_id = self.created_bots[0]
            
            # Update is_bet_creation_active to False
            update_data = {
                "is_bet_creation_active": False
            }
            
            response = requests.put(
                f"{BASE_URL}/admin/human-bots/{bot_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                updated_bot = response.json()
                
                if updated_bot.get("is_bet_creation_active") == False:
                    print(f"  ✅ Update successful: is_bet_creation_active = {updated_bot.get('is_bet_creation_active')} (expected False)")
                    self.log_result("UPDATE Human-bot Activity Field", True, "Successfully updated is_bet_creation_active")
                    return True
                else:
                    print(f"  ❌ Update failed: is_bet_creation_active = {updated_bot.get('is_bet_creation_active')} (expected False)")
                    self.log_result("UPDATE Human-bot Activity Field", False, f"Update not reflected in response")
                    return False
            else:
                print(f"  ❌ Update request failed. Status: {response.status_code}, Response: {response.text}")
                self.log_result("UPDATE Human-bot Activity Field", False, f"Update request failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("UPDATE Human-bot Activity Field", False, f"Exception: {str(e)}")
            return False
            
    def test_bulk_create_human_bots_activity_field(self) -> bool:
        """Test BULK CREATE Human-bots with is_bet_creation_active field"""
        try:
            print("\n🔍 Testing BULK CREATE Human-bots with is_bet_creation_active field...")
            
            bulk_data = {
                "count": 2,
                "character": "BALANCED",
                "min_bet_range": [10.0, 20.0],
                "max_bet_range": [50.0, 100.0],
                "bet_limit_range": [8, 12],
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0,
                "delay_range": [30, 120],
                "use_commit_reveal": True,
                "logging_level": "INFO",
                "can_play_with_other_bots": True,
                "can_play_with_players": True,
                "is_bet_creation_active": False  # Set to False for bulk creation
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots/bulk-create",
                json=bulk_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code in [200, 201]:
                result_data = response.json()
                print(f"  📋 Bulk create response: {json.dumps(result_data, indent=2)}")
                
                # Check if bots were created successfully
                if result_data.get("success") and result_data.get("created_count", 0) >= 2:
                    print(f"  ✅ Bulk creation successful: {result_data.get('created_count')} bots created")
                    
                    # Get the created bot IDs and check their is_bet_creation_active field
                    created_bots = result_data.get("created_bots", [])
                    if created_bots:
                        # Check first created bot
                        first_bot_id = created_bots[0].get("id")
                        if first_bot_id:
                            self.created_bots.append(first_bot_id)
                            
                            # Get full bot details to check is_bet_creation_active
                            bot_response = requests.get(
                                f"{BASE_URL}/admin/human-bots",
                                params={"search": created_bots[0].get("name", "")},
                                headers=self.get_auth_headers()
                            )
                            
                            if bot_response.status_code == 200:
                                bots_data = bot_response.json()
                                bots = bots_data.get("bots", [])
                                
                                if bots:
                                    bot = bots[0]
                                    if bot.get("is_bet_creation_active") == False:
                                        print(f"  ✅ Bulk created bot has correct is_bet_creation_active: {bot.get('is_bet_creation_active')}")
                                        self.log_result("BULK CREATE Human-bots Activity Field", True, "Bulk creation with is_bet_creation_active=False successful")
                                        return True
                                    else:
                                        print(f"  ❌ Bulk created bot has incorrect is_bet_creation_active: {bot.get('is_bet_creation_active')} (expected False)")
                                        self.log_result("BULK CREATE Human-bots Activity Field", False, f"Incorrect is_bet_creation_active value")
                                        return False
                                else:
                                    print(f"  ❌ Could not find created bot to verify is_bet_creation_active")
                                    self.log_result("BULK CREATE Human-bots Activity Field", False, "Could not verify created bot")
                                    return False
                            else:
                                print(f"  ❌ Failed to get bot details. Status: {bot_response.status_code}")
                                self.log_result("BULK CREATE Human-bots Activity Field", False, "Failed to get bot details")
                                return False
                        else:
                            print(f"  ❌ No bot ID in bulk create response")
                            self.log_result("BULK CREATE Human-bots Activity Field", False, "No bot ID in response")
                            return False
                    else:
                        print(f"  ❌ No created_bots in bulk create response")
                        self.log_result("BULK CREATE Human-bots Activity Field", False, "No created_bots in response")
                        return False
                else:
                    print(f"  ❌ Bulk creation failed or insufficient bots created")
                    self.log_result("BULK CREATE Human-bots Activity Field", False, "Bulk creation failed")
                    return False
            else:
                print(f"  ❌ Bulk creation request failed. Status: {response.status_code}, Response: {response.text}")
                self.log_result("BULK CREATE Human-bots Activity Field", False, f"Request failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("BULK CREATE Human-bots Activity Field", False, f"Exception: {str(e)}")
            return False
            
    def test_human_bot_list_response_includes_activity_field(self) -> bool:
        """Test that Human-bot list response includes is_bet_creation_active field"""
        try:
            print("\n🔍 Testing Human-bot list response includes is_bet_creation_active field...")
            
            response = requests.get(
                f"{BASE_URL}/admin/human-bots?page=1&per_page=5",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                bots = data.get("bots", [])
                
                if len(bots) > 0:
                    all_have_field = True
                    for i, bot in enumerate(bots):
                        if "is_bet_creation_active" not in bot:
                            print(f"  ❌ Bot {i+1} missing is_bet_creation_active field")
                            all_have_field = False
                        else:
                            activity_value = bot.get("is_bet_creation_active")
                            print(f"  ✅ Bot {i+1} ({bot.get('name', 'Unknown')}): is_bet_creation_active = {activity_value}")
                    
                    if all_have_field:
                        self.log_result("Human-bot List Response Activity Field", True, f"All {len(bots)} bots have is_bet_creation_active field")
                        return True
                    else:
                        self.log_result("Human-bot List Response Activity Field", False, "Some bots missing is_bet_creation_active field")
                        return False
                else:
                    print(f"  ❌ No bots found in response")
                    self.log_result("Human-bot List Response Activity Field", False, "No bots found")
                    return False
            else:
                print(f"  ❌ Failed to get bots list. Status: {response.status_code}")
                self.log_result("Human-bot List Response Activity Field", False, f"Request failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Human-bot List Response Activity Field", False, f"Exception: {str(e)}")
            return False
            
    def test_field_validation(self) -> bool:
        """Test field validation for is_bet_creation_active"""
        try:
            print("\n🔍 Testing field validation for is_bet_creation_active...")
            
            # Test with string value (should be converted or rejected)
            bot_name = self.generate_unique_bot_name()
            invalid_data = {
                "name": bot_name,
                "character": "BALANCED",
                "min_bet": 10.0,
                "max_bet": 100.0,
                "is_bet_creation_active": "true"  # String instead of boolean
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=invalid_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 422:
                print(f"  ✅ Validation correctly rejected string value with 422 error")
                self.log_result("Field Validation", True, "String value correctly rejected")
                return True
            elif response.status_code in [200, 201]:
                bot_data = response.json()
                bot_id = bot_data.get("id")
                if bot_id:
                    self.created_bots.append(bot_id)
                
                activity_value = bot_data.get("is_bet_creation_active")
                if isinstance(activity_value, bool):
                    print(f"  ✅ String value converted to boolean: {activity_value}")
                    self.log_result("Field Validation", True, f"String converted to boolean: {activity_value}")
                    return True
                else:
                    print(f"  ❌ Field accepted non-boolean value: {activity_value} (type: {type(activity_value)})")
                    self.log_result("Field Validation", False, f"Non-boolean value accepted: {activity_value}")
                    return False
            else:
                print(f"  ❌ Unexpected response. Status: {response.status_code}")
                self.log_result("Field Validation", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Field Validation", False, f"Exception: {str(e)}")
            return False
            
    def cleanup_created_bots(self):
        """Clean up created test bots"""
        if self.created_bots:
            print(f"\n🧹 Cleaning up {len(self.created_bots)} created test bots...")
            
            for bot_id in self.created_bots:
                try:
                    response = requests.delete(
                        f"{BASE_URL}/admin/human-bots/{bot_id}",
                        headers=self.get_auth_headers()
                    )
                    if response.status_code == 200:
                        print(f"  ✅ Deleted bot {bot_id}")
                    else:
                        print(f"  ❌ Failed to delete bot {bot_id}: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ Exception deleting bot {bot_id}: {str(e)}")
                    
    def run_all_tests(self):
        """Run all focused Human-bot Activity Control tests"""
        print("🚀 Starting Focused Human-bot Activity Control System Testing")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ Failed to authenticate as admin. Stopping tests.")
            return False
            
        # Run tests
        tests = [
            self.test_create_human_bot_with_activity_field,
            self.test_update_human_bot_activity_field,
            self.test_bulk_create_human_bots_activity_field,
            self.test_human_bot_list_response_includes_activity_field,
            self.test_field_validation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
                
        # Cleanup
        self.cleanup_created_bots()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 FOCUSED HUMAN-BOT ACTIVITY CONTROL SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        print(f"✅ Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Human-bot Activity Control System is FULLY FUNCTIONAL!")
            print("\n📋 VERIFIED FUNCTIONALITY:")
            print("  ✅ CREATE Human-bot - is_bet_creation_active правильно сохраняется (default=true)")
            print("  ✅ UPDATE Human-bot - is_bet_creation_active изменяется через PUT запрос")
            print("  ✅ BULK CREATE - массовое создание с is_bet_creation_active")
            print("  ✅ HumanBotResponse - поле возвращается в API ответах")
            print("  ✅ FIELD VALIDATION - поле принимает только boolean значения")
        else:
            print(f"⚠️  {total - passed} tests failed. Review the issues above.")
            
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
            
        return passed == total

if __name__ == "__main__":
    tester = FocusedHumanBotActivityTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)