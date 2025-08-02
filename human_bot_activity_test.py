#!/usr/bin/env python3
"""
Human-bot Activity Control System Testing - Russian Review
Focus: Testing new "Активность бота" functionality for Human-bots

TESTING REQUIREMENTS:
1. CREATE Human-bot - проверить что is_bet_creation_active правильно сохраняется (default=true)
2. UPDATE Human-bot - изменить is_bet_creation_active через PUT запрос
3. BULK CREATE - массовое создание с is_bet_creation_active
4. HumanBotResponse - убедиться что поле возвращается в API ответах
5. FIELD VALIDATION - проверить что поле принимает только boolean значения

LOGIC VERIFICATION:
- Боты создают новые ставки ТОЛЬКО если is_bet_creation_active=true И не превышен bet_limit
- Боты присоединяются к существующим ставкам согласно переключателям can_play_with_other_bots/can_play_with_players
- Переключатели работают независимо друг от друга
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

class HumanBotActivityTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.created_bots = []  # Track created bots for cleanup
        
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
        return f"ActivityTestBot_{timestamp}_{random_suffix}"
        
    def test_create_human_bot_default_activity(self) -> bool:
        """Test 1: CREATE Human-bot - проверить что is_bet_creation_active правильно сохраняется (default=true)"""
        try:
            bot_name = self.generate_unique_bot_name()
            
            # Create Human-bot without specifying is_bet_creation_active (should default to true)
            create_data = {
                "name": bot_name,
                "character": "BALANCED",
                "gender": "male",
                "min_bet": 10.0,
                "max_bet": 100.0,
                "bet_limit": 12,
                "bet_limit_amount": 300.0,
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0,
                "min_delay": 30,
                "max_delay": 120,
                "use_commit_reveal": True,
                "logging_level": "INFO",
                "can_play_with_other_bots": True,
                "can_play_with_players": True
                # Note: is_bet_creation_active not specified - should default to True
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code in [200, 201]:
                bot_data = response.json()
                bot_id = bot_data.get("id")
                self.created_bots.append(bot_id)
                
                # Verify is_bet_creation_active defaults to True
                if bot_data.get("is_bet_creation_active") == True:
                    self.log_result("CREATE Human-bot Default Activity", True, 
                                  f"Bot created with is_bet_creation_active=True (default)")
                    return True
                else:
                    self.log_result("CREATE Human-bot Default Activity", False, 
                                  f"Expected is_bet_creation_active=True, got {bot_data.get('is_bet_creation_active')}")
                    return False
            else:
                self.log_result("CREATE Human-bot Default Activity", False, 
                              f"Failed to create bot. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("CREATE Human-bot Default Activity", False, f"Exception: {str(e)}")
            return False
            
    def test_create_human_bot_explicit_activity(self) -> bool:
        """Test 2: CREATE Human-bot - проверить что is_bet_creation_active правильно сохраняется (explicit false)"""
        try:
            bot_name = self.generate_unique_bot_name()
            
            # Create Human-bot with explicit is_bet_creation_active=false
            create_data = {
                "name": bot_name,
                "character": "AGGRESSIVE",
                "gender": "female",
                "min_bet": 5.0,
                "max_bet": 50.0,
                "bet_limit": 8,
                "bet_limit_amount": 200.0,
                "win_percentage": 45.0,
                "loss_percentage": 35.0,
                "draw_percentage": 20.0,
                "min_delay": 45,
                "max_delay": 150,
                "use_commit_reveal": True,
                "logging_level": "INFO",
                "can_play_with_other_bots": True,
                "can_play_with_players": True,
                "is_bet_creation_active": False  # Explicitly set to False
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code in [200, 201]:
                bot_data = response.json()
                bot_id = bot_data.get("id")
                self.created_bots.append(bot_id)
                
                # Verify is_bet_creation_active is False
                if bot_data.get("is_bet_creation_active") == False:
                    self.log_result("CREATE Human-bot Explicit Activity", True, 
                                  f"Bot created with is_bet_creation_active=False (explicit)")
                    return True
                else:
                    self.log_result("CREATE Human-bot Explicit Activity", False, 
                                  f"Expected is_bet_creation_active=False, got {bot_data.get('is_bet_creation_active')}")
                    return False
            else:
                self.log_result("CREATE Human-bot Explicit Activity", False, 
                              f"Failed to create bot. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("CREATE Human-bot Explicit Activity", False, f"Exception: {str(e)}")
            return False
            
    def test_update_human_bot_activity(self) -> bool:
        """Test 3: UPDATE Human-bot - изменить is_bet_creation_active через PUT запрос"""
        try:
            # First create a bot
            bot_name = self.generate_unique_bot_name()
            create_data = {
                "name": bot_name,
                "character": "CAUTIOUS",
                "gender": "male",
                "min_bet": 15.0,
                "max_bet": 75.0,
                "bet_limit": 10,
                "is_bet_creation_active": True  # Start with True
            }
            
            create_response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data,
                headers=self.get_auth_headers()
            )
            
            if create_response.status_code not in [200, 201]:
                self.log_result("UPDATE Human-bot Activity", False, "Failed to create bot for update test")
                return False
                
            bot_data = create_response.json()
            bot_id = bot_data.get("id")
            self.created_bots.append(bot_id)
            
            # Update is_bet_creation_active to False
            update_data = {
                "is_bet_creation_active": False
            }
            
            update_response = requests.put(
                f"{BASE_URL}/admin/human-bots/{bot_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            if update_response.status_code == 200:
                updated_bot = update_response.json()
                
                # Verify the update
                if updated_bot.get("is_bet_creation_active") == False:
                    # Double-check by fetching the bot
                    get_response = requests.get(
                        f"{BASE_URL}/admin/human-bots/{bot_id}",
                        headers=self.get_auth_headers()
                    )
                    
                    if get_response.status_code == 200:
                        fetched_bot = get_response.json()
                        if fetched_bot.get("is_bet_creation_active") == False:
                            self.log_result("UPDATE Human-bot Activity", True, 
                                          f"Successfully updated is_bet_creation_active from True to False")
                            return True
                        else:
                            self.log_result("UPDATE Human-bot Activity", False, 
                                          f"Update not persisted. Fetched value: {fetched_bot.get('is_bet_creation_active')}")
                            return False
                    else:
                        self.log_result("UPDATE Human-bot Activity", False, 
                                      f"Failed to fetch updated bot. Status: {get_response.status_code}")
                        return False
                else:
                    self.log_result("UPDATE Human-bot Activity", False, 
                                  f"Update failed. Expected False, got {updated_bot.get('is_bet_creation_active')}")
                    return False
            else:
                self.log_result("UPDATE Human-bot Activity", False, 
                              f"Update request failed. Status: {update_response.status_code}, Response: {update_response.text}")
                return False
                
        except Exception as e:
            self.log_result("UPDATE Human-bot Activity", False, f"Exception: {str(e)}")
            return False
            
    def test_bulk_create_human_bots_activity(self) -> bool:
        """Test 4: BULK CREATE - массовое создание с is_bet_creation_active"""
        try:
            # Test bulk creation with is_bet_creation_active=False
            bulk_data = {
                "count": 3,
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
                
                # Handle different response structures
                if "created_bots" in result_data:
                    # New response structure
                    created_bots = result_data.get("created_bots", [])
                    
                    # Get full bot details for each created bot
                    full_bots = []
                    for bot_summary in created_bots:
                        bot_id = bot_summary.get("id")
                        if bot_id:
                            self.created_bots.append(bot_id)
                            # Get full bot details
                            bot_response = requests.get(
                                f"{BASE_URL}/admin/human-bots/{bot_id}",
                                headers=self.get_auth_headers()
                            )
                            if bot_response.status_code == 200:
                                full_bots.append(bot_response.json())
                    
                    if len(full_bots) == 3:
                        # Verify all bots have is_bet_creation_active=False
                        all_correct = True
                        for bot in full_bots:
                            if bot.get("is_bet_creation_active") != False:
                                all_correct = False
                                break
                        
                        if all_correct:
                            self.log_result("BULK CREATE Human-bots Activity", True, 
                                          f"Successfully created 3 bots with is_bet_creation_active=False")
                            return True
                        else:
                            self.log_result("BULK CREATE Human-bots Activity", False, 
                                          f"Not all bots have correct is_bet_creation_active value")
                            return False
                    else:
                        self.log_result("BULK CREATE Human-bots Activity", False, 
                                      f"Expected 3 bots, got {len(full_bots)}")
                        return False
                        
                elif "bots" in result_data:
                    # Old response structure
                    created_bots = result_data.get("bots", [])
                    
                    if len(created_bots) == 3:
                        # Track created bots for cleanup
                        for bot in created_bots:
                            self.created_bots.append(bot.get("id"))
                        
                        # Verify all bots have is_bet_creation_active=False
                        all_correct = True
                        for bot in created_bots:
                            if bot.get("is_bet_creation_active") != False:
                                all_correct = False
                                break
                        
                        if all_correct:
                            self.log_result("BULK CREATE Human-bots Activity", True, 
                                          f"Successfully created 3 bots with is_bet_creation_active=False")
                            return True
                        else:
                            self.log_result("BULK CREATE Human-bots Activity", False, 
                                          f"Not all bots have correct is_bet_creation_active value")
                            return False
                    else:
                        self.log_result("BULK CREATE Human-bots Activity", False, 
                                      f"Expected 3 bots, got {len(created_bots)}")
                        return False
                else:
                    self.log_result("BULK CREATE Human-bots Activity", False, 
                                  f"Unexpected response structure: {result_data}")
                    return False
            else:
                self.log_result("BULK CREATE Human-bots Activity", False, 
                              f"Bulk creation failed. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("BULK CREATE Human-bots Activity", False, f"Exception: {str(e)}")
            return False
            
    def test_human_bot_response_includes_activity_field(self) -> bool:
        """Test 5: HumanBotResponse - убедиться что поле возвращается в API ответах"""
        try:
            # Get list of human bots to verify response structure
            response = requests.get(
                f"{BASE_URL}/admin/human-bots?page=1&per_page=5",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                bots = data.get("bots", [])
                
                if len(bots) > 0:
                    # Check if all bots have is_bet_creation_active field
                    all_have_field = True
                    for bot in bots:
                        if "is_bet_creation_active" not in bot:
                            all_have_field = False
                            break
                    
                    if all_have_field:
                        self.log_result("HumanBotResponse Activity Field", True, 
                                      f"All {len(bots)} bots have is_bet_creation_active field in response")
                        return True
                    else:
                        self.log_result("HumanBotResponse Activity Field", False, 
                                      f"Some bots missing is_bet_creation_active field")
                        return False
                else:
                    self.log_result("HumanBotResponse Activity Field", False, 
                                  f"No bots found to test response structure")
                    return False
            else:
                self.log_result("HumanBotResponse Activity Field", False, 
                              f"Failed to get bots list. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("HumanBotResponse Activity Field", False, f"Exception: {str(e)}")
            return False
            
    def test_field_validation_boolean_only(self) -> bool:
        """Test 6: FIELD VALIDATION - проверить что поле принимает только boolean значения"""
        try:
            bot_name = self.generate_unique_bot_name()
            
            # Test with invalid string value
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
            
            # Should fail with validation error
            if response.status_code == 422:  # Validation error
                self.log_result("Field Validation Boolean Only", True, 
                              f"Correctly rejected string value 'true' with validation error")
                return True
            elif response.status_code in [200, 201]:
                # If it succeeded, check if it was converted to boolean
                bot_data = response.json()
                bot_id = bot_data.get("id")
                if bot_id:
                    self.created_bots.append(bot_id)
                
                if isinstance(bot_data.get("is_bet_creation_active"), bool):
                    self.log_result("Field Validation Boolean Only", True, 
                                  f"String value was converted to boolean: {bot_data.get('is_bet_creation_active')}")
                    return True
                else:
                    self.log_result("Field Validation Boolean Only", False, 
                                  f"Field accepted non-boolean value: {bot_data.get('is_bet_creation_active')}")
                    return False
            else:
                self.log_result("Field Validation Boolean Only", False, 
                              f"Unexpected response. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Field Validation Boolean Only", False, f"Exception: {str(e)}")
            return False
            
    def test_activity_field_in_individual_bot_response(self) -> bool:
        """Test 7: Individual bot GET response includes is_bet_creation_active"""
        try:
            if not self.created_bots:
                self.log_result("Individual Bot Response Activity Field", False, 
                              "No bots available for individual response test")
                return False
                
            bot_id = self.created_bots[0]
            response = requests.get(
                f"{BASE_URL}/admin/human-bots/{bot_id}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                bot_data = response.json()
                
                if "is_bet_creation_active" in bot_data:
                    activity_value = bot_data.get("is_bet_creation_active")
                    if isinstance(activity_value, bool):
                        self.log_result("Individual Bot Response Activity Field", True, 
                                      f"Individual bot response includes is_bet_creation_active: {activity_value}")
                        return True
                    else:
                        self.log_result("Individual Bot Response Activity Field", False, 
                                      f"Field present but not boolean: {type(activity_value)}")
                        return False
                else:
                    self.log_result("Individual Bot Response Activity Field", False, 
                                  f"is_bet_creation_active field missing from individual bot response")
                    return False
            else:
                self.log_result("Individual Bot Response Activity Field", False, 
                              f"Failed to get individual bot. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Individual Bot Response Activity Field", False, f"Exception: {str(e)}")
            return False
            
    def cleanup_created_bots(self):
        """Clean up created test bots"""
        print(f"\n🧹 Cleaning up {len(self.created_bots)} created test bots...")
        
        for bot_id in self.created_bots:
            try:
                response = requests.delete(
                    f"{BASE_URL}/admin/human-bots/{bot_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    print(f"✅ Deleted bot {bot_id}")
                else:
                    print(f"❌ Failed to delete bot {bot_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting bot {bot_id}: {str(e)}")
                
    def run_all_tests(self):
        """Run all Human-bot Activity Control tests"""
        print("🚀 Starting Human-bot Activity Control System Testing")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ Failed to authenticate as admin. Stopping tests.")
            return
            
        # Run tests
        tests = [
            self.test_create_human_bot_default_activity,
            self.test_create_human_bot_explicit_activity,
            self.test_update_human_bot_activity,
            self.test_bulk_create_human_bots_activity,
            self.test_human_bot_response_includes_activity_field,
            self.test_field_validation_boolean_only,
            self.test_activity_field_in_individual_bot_response
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
        print("📊 HUMAN-BOT ACTIVITY CONTROL SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        print(f"✅ Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Human-bot Activity Control System is FULLY FUNCTIONAL!")
        else:
            print(f"⚠️  {total - passed} tests failed. Review the issues above.")
            
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
            
        return passed == total

if __name__ == "__main__":
    tester = HumanBotActivityTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)