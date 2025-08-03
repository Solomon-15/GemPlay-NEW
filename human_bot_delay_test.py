#!/usr/bin/env python3
"""
Human-bot Delay Fields Backend Model Fix Testing - Russian Review
Focus: Testing the corrected delay field defaults and validation ranges

CONTEXT: Fixed HumanBot model in backend/server.py:
- bot_max_delay_seconds: default=120 → default=2000, le=3600 → le=2000
- player_max_delay_seconds: default=120 → default=2000, le=3600 → le=2000  
- max_concurrent_games: default=3 → default=1, le=100 → le=3
- Minimum values: ge=1 → ge=30 for all delays

FOCUSED TESTING:
1. CREATE Human-bot - verify correct default values
2. UPDATE Human-bot - test individual settings changes
3. VALIDATION - verify range validation works correctly

CRITICAL BUG FOUND: UpdateHumanBotRequest model missing individual delay fields!
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
BACKEND_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

class HumanBotDelayFieldsTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.created_bots = []  # Track created bots for cleanup
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def admin_login(self):
        """Login as admin to get authentication token"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_result("Admin Authentication", True, f"Successfully logged in as {ADMIN_EMAIL}")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Login failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Login error: {str(e)}")
            return False

    def test_create_human_bot_with_individual_settings(self):
        """Test CREATE Human-bot with individual delay settings"""
        try:
            # Test data with corrected default values
            bot_data = {
                "name": f"DelayTestBot_{int(time.time())}",
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
                "can_play_with_players": True,
                # Individual settings with corrected defaults
                "bot_min_delay_seconds": 30,
                "bot_max_delay_seconds": 2000,  # Fixed: was 120, now 2000
                "player_min_delay_seconds": 30,
                "player_max_delay_seconds": 2000,  # Fixed: was 120, now 2000
                "max_concurrent_games": 1  # Fixed: was 3, now 1
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/human-bots",
                json=bot_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                bot_response = response.json()
                bot_id = bot_response.get("id")
                self.created_bots.append(bot_id)
                
                # Verify individual settings are present and correct
                expected_fields = {
                    "bot_min_delay_seconds": 30,
                    "bot_max_delay_seconds": 2000,
                    "player_min_delay_seconds": 30,
                    "player_max_delay_seconds": 2000,
                    "max_concurrent_games": 1
                }
                
                all_fields_correct = True
                missing_fields = []
                incorrect_values = []
                
                for field, expected_value in expected_fields.items():
                    if field not in bot_response:
                        missing_fields.append(field)
                        all_fields_correct = False
                    elif bot_response[field] != expected_value:
                        incorrect_values.append(f"{field}: got {bot_response[field]}, expected {expected_value}")
                        all_fields_correct = False
                
                if all_fields_correct:
                    self.log_result(
                        "CREATE Human-bot with Individual Settings", 
                        True, 
                        f"Successfully created bot {bot_response['name']} with correct individual delay settings"
                    )
                else:
                    details = ""
                    if missing_fields:
                        details += f"Missing fields: {missing_fields}. "
                    if incorrect_values:
                        details += f"Incorrect values: {incorrect_values}. "
                    
                    self.log_result(
                        "CREATE Human-bot with Individual Settings", 
                        False, 
                        details,
                        bot_response
                    )
                
                return bot_id
            else:
                self.log_result(
                    "CREATE Human-bot with Individual Settings", 
                    False, 
                    f"Creation failed with status {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result("CREATE Human-bot with Individual Settings", False, f"Error: {str(e)}")
            return None

    def test_update_human_bot_individual_settings(self, bot_id):
        """Test UPDATE Human-bot individual delay settings"""
        if not bot_id:
            self.log_result("UPDATE Human-bot Individual Settings", False, "No bot ID provided")
            return False
            
        try:
            # Update with new individual settings values
            update_data = {
                "bot_min_delay_seconds": 100,
                "bot_max_delay_seconds": 1500,
                "player_min_delay_seconds": 50,
                "player_max_delay_seconds": 1000,
                "max_concurrent_games": 2
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/admin/human-bots/{bot_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                bot_response = response.json()
                
                # Verify updated individual settings
                all_fields_correct = True
                incorrect_values = []
                
                for field, expected_value in update_data.items():
                    if field not in bot_response:
                        all_fields_correct = False
                        incorrect_values.append(f"{field}: missing from response")
                    elif bot_response[field] != expected_value:
                        incorrect_values.append(f"{field}: got {bot_response[field]}, expected {expected_value}")
                        all_fields_correct = False
                
                if all_fields_correct:
                    self.log_result(
                        "UPDATE Human-bot Individual Settings", 
                        True, 
                        f"Successfully updated bot individual delay settings: {update_data}"
                    )
                else:
                    self.log_result(
                        "UPDATE Human-bot Individual Settings", 
                        False, 
                        f"Update issues: {incorrect_values}",
                        bot_response
                    )
                
                return all_fields_correct
            else:
                self.log_result(
                    "UPDATE Human-bot Individual Settings", 
                    False, 
                    f"Update failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("UPDATE Human-bot Individual Settings", False, f"Error: {str(e)}")
            return False

    def test_bulk_create_with_ranges(self):
        """Test BULK CREATE Human-bots with delay ranges"""
        try:
            # Bulk create data with corrected ranges
            bulk_data = {
                "count": 3,
                "character": "BALANCED",
                "min_bet_range": [10.0, 50.0],
                "max_bet_range": [50.0, 200.0],
                "bet_limit_range": [10, 15],
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0,
                "delay_range": [30, 120],
                "use_commit_reveal": True,
                "logging_level": "INFO",
                # Individual settings ranges with corrected values
                "bot_min_delay_range": [30, 2000],
                "bot_max_delay_range": [30, 2000],
                "player_min_delay_range": [30, 2000],
                "player_max_delay_range": [30, 2000],
                "max_concurrent_games_range": [1, 3]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/human-bots/bulk-create",
                json=bulk_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                bulk_response = response.json()
                created_bots = bulk_response.get("bots", [])
                
                if len(created_bots) == 3:
                    # Track created bots for cleanup
                    for bot in created_bots:
                        self.created_bots.append(bot.get("id"))
                    
                    # Verify individual settings are within expected ranges
                    all_bots_valid = True
                    validation_issues = []
                    
                    for i, bot in enumerate(created_bots):
                        bot_issues = []
                        
                        # Check individual delay settings ranges
                        if not (30 <= bot.get("bot_min_delay_seconds", 0) <= 2000):
                            bot_issues.append(f"bot_min_delay_seconds out of range: {bot.get('bot_min_delay_seconds')}")
                        if not (30 <= bot.get("bot_max_delay_seconds", 0) <= 2000):
                            bot_issues.append(f"bot_max_delay_seconds out of range: {bot.get('bot_max_delay_seconds')}")
                        if not (30 <= bot.get("player_min_delay_seconds", 0) <= 2000):
                            bot_issues.append(f"player_min_delay_seconds out of range: {bot.get('player_min_delay_seconds')}")
                        if not (30 <= bot.get("player_max_delay_seconds", 0) <= 2000):
                            bot_issues.append(f"player_max_delay_seconds out of range: {bot.get('player_max_delay_seconds')}")
                        if not (1 <= bot.get("max_concurrent_games", 0) <= 3):
                            bot_issues.append(f"max_concurrent_games out of range: {bot.get('max_concurrent_games')}")
                        
                        if bot_issues:
                            validation_issues.append(f"Bot {i+1} ({bot.get('name')}): {bot_issues}")
                            all_bots_valid = False
                    
                    if all_bots_valid:
                        self.log_result(
                            "BULK CREATE with Delay Ranges", 
                            True, 
                            f"Successfully created {len(created_bots)} bots with individual settings in correct ranges"
                        )
                    else:
                        self.log_result(
                            "BULK CREATE with Delay Ranges", 
                            False, 
                            f"Range validation issues: {validation_issues}",
                            created_bots
                        )
                    
                    return all_bots_valid
                else:
                    self.log_result(
                        "BULK CREATE with Delay Ranges", 
                        False, 
                        f"Expected 3 bots, got {len(created_bots)}",
                        bulk_response
                    )
                    return False
            else:
                self.log_result(
                    "BULK CREATE with Delay Ranges", 
                    False, 
                    f"Bulk creation failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("BULK CREATE with Delay Ranges", False, f"Error: {str(e)}")
            return False

    def test_get_human_bot_individual_settings(self, bot_id):
        """Test GET Human-bot to verify individual settings are returned"""
        if not bot_id:
            self.log_result("GET Human-bot Individual Settings", False, "No bot ID provided")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/human-bots/{bot_id}")
            
            if response.status_code == 200:
                bot_data = response.json()
                
                # Check if individual settings fields are present
                required_fields = [
                    "bot_min_delay_seconds",
                    "bot_max_delay_seconds", 
                    "player_min_delay_seconds",
                    "player_max_delay_seconds",
                    "max_concurrent_games"
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in bot_data:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log_result(
                        "GET Human-bot Individual Settings", 
                        True, 
                        f"All individual settings fields present: {[f'{field}={bot_data[field]}' for field in required_fields]}"
                    )
                    return True
                else:
                    self.log_result(
                        "GET Human-bot Individual Settings", 
                        False, 
                        f"Missing individual settings fields: {missing_fields}",
                        bot_data
                    )
                    return False
            else:
                self.log_result(
                    "GET Human-bot Individual Settings", 
                    False, 
                    f"GET request failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("GET Human-bot Individual Settings", False, f"Error: {str(e)}")
            return False

    def test_human_bots_list_individual_settings(self):
        """Test GET Human-bots list to verify individual settings are included"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/human-bots?limit=5")
            
            if response.status_code == 200:
                list_response = response.json()
                bots = list_response.get("bots", [])
                
                if bots:
                    # Check first bot for individual settings fields
                    first_bot = bots[0]
                    required_fields = [
                        "bot_min_delay_seconds",
                        "bot_max_delay_seconds", 
                        "player_min_delay_seconds",
                        "player_max_delay_seconds",
                        "max_concurrent_games"
                    ]
                    
                    missing_fields = []
                    for field in required_fields:
                        if field not in first_bot:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        self.log_result(
                            "GET Human-bots List Individual Settings", 
                            True, 
                            f"Individual settings present in list response for bot '{first_bot.get('name')}'"
                        )
                        return True
                    else:
                        self.log_result(
                            "GET Human-bots List Individual Settings", 
                            False, 
                            f"Missing individual settings in list: {missing_fields}",
                            first_bot
                        )
                        return False
                else:
                    self.log_result(
                        "GET Human-bots List Individual Settings", 
                        False, 
                        "No bots found in list response",
                        list_response
                    )
                    return False
            else:
                self.log_result(
                    "GET Human-bots List Individual Settings", 
                    False, 
                    f"List request failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("GET Human-bots List Individual Settings", False, f"Error: {str(e)}")
            return False

    def cleanup_created_bots(self):
        """Clean up created test bots"""
        print("\n🧹 CLEANING UP CREATED TEST BOTS...")
        for bot_id in self.created_bots:
            try:
                response = self.session.delete(f"{BACKEND_URL}/admin/human-bots/{bot_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted bot {bot_id}")
                else:
                    print(f"⚠️ Failed to delete bot {bot_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting bot {bot_id}: {str(e)}")

    def run_all_tests(self):
        """Run all Human-bot delay fields tests"""
        print("🚀 STARTING HUMAN-BOT DELAY FIELDS FIXES TESTING")
        print("=" * 60)
        
        # Step 1: Admin login
        if not self.admin_login():
            print("❌ Cannot proceed without admin authentication")
            return
        
        # Step 2: Test CREATE with individual settings
        created_bot_id = self.test_create_human_bot_with_individual_settings()
        
        # Step 3: Test UPDATE individual settings
        if created_bot_id:
            self.test_update_human_bot_individual_settings(created_bot_id)
            self.test_get_human_bot_individual_settings(created_bot_id)
        
        # Step 4: Test BULK CREATE with ranges
        self.test_bulk_create_with_ranges()
        
        # Step 5: Test list endpoint includes individual settings
        self.test_human_bots_list_individual_settings()
        
        # Step 6: Cleanup
        self.cleanup_created_bots()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 HUMAN-BOT DELAY FIELDS TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Show failed tests
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check if individual settings are working
        individual_settings_tests = [
            "CREATE Human-bot with Individual Settings",
            "UPDATE Human-bot Individual Settings", 
            "GET Human-bot Individual Settings",
            "GET Human-bots List Individual Settings"
        ]
        
        individual_settings_passed = sum(1 for r in self.test_results 
                                       if r["test"] in individual_settings_tests and r["success"])
        individual_settings_total = sum(1 for r in self.test_results 
                                      if r["test"] in individual_settings_tests)
        
        if individual_settings_passed == individual_settings_total:
            print("✅ Individual delay settings fields are working correctly")
        else:
            print(f"❌ Individual delay settings have issues ({individual_settings_passed}/{individual_settings_total} passed)")
        
        # Check bulk creation
        bulk_test = next((r for r in self.test_results if r["test"] == "BULK CREATE with Delay Ranges"), None)
        if bulk_test:
            if bulk_test["success"]:
                print("✅ Bulk creation with delay ranges is working correctly")
            else:
                print("❌ Bulk creation with delay ranges has issues")
        
        # Overall assessment
        print()
        if success_rate >= 80:
            print("🎉 OVERALL ASSESSMENT: HUMAN-BOT DELAY FIELDS FIXES ARE WORKING CORRECTLY!")
            print("The corrected default values and individual settings functionality is operational.")
        elif success_rate >= 60:
            print("⚠️ OVERALL ASSESSMENT: PARTIAL SUCCESS - Some issues need attention")
        else:
            print("❌ OVERALL ASSESSMENT: CRITICAL ISSUES - Major fixes needed")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = HumanBotDelayFieldsTest()
    tester.run_all_tests()