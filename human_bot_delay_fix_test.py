#!/usr/bin/env python3
"""
Human-bot Fields Delay Fix Testing - Russian Review Final Verification
Focus: Testing corrected default values and individual delay field updates
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class HumanBotDelayFixTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.created_human_bots = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result with timestamp"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and data:
            print(f"    Data: {json.dumps(data, indent=2)}")
        print()

    def admin_login(self) -> bool:
        """Login as admin and get token"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Login", True, f"Successfully logged in as admin")
                return True
            else:
                self.log_result("Admin Login", False, f"Login failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Login error: {str(e)}")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}

    def test_create_human_bot_default_values(self) -> bool:
        """Test 1: CREATE Human-bot - verify corrected default values"""
        try:
            # Create human bot with minimal required fields to test defaults
            create_data = {
                "name": f"TestBot_DefaultValues_{int(time.time())}",
                "character": "BALANCED",
                "gender": "male",
                "min_bet": 10.0,
                "max_bet": 100.0
                # Not specifying delay fields to test defaults
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                bot_data = response.json()
                self.created_human_bots.append(bot_data["id"])
                
                # Check default values
                expected_defaults = {
                    "bot_min_delay_seconds": 30,
                    "bot_max_delay_seconds": 2000,  # Fixed from 120
                    "player_min_delay_seconds": 30,
                    "player_max_delay_seconds": 2000,  # Fixed from 120
                    "max_concurrent_games": 1  # Fixed from 3
                }
                
                all_correct = True
                details = []
                
                for field, expected_value in expected_defaults.items():
                    actual_value = bot_data.get(field)
                    if actual_value == expected_value:
                        details.append(f"✅ {field}: {actual_value} (correct)")
                    else:
                        details.append(f"❌ {field}: {actual_value} (expected {expected_value})")
                        all_correct = False
                
                self.log_result(
                    "CREATE Human-bot Default Values",
                    all_correct,
                    f"Default values verification: {'; '.join(details)}",
                    {
                        "bot_id": bot_data["id"],
                        "actual_values": {k: bot_data.get(k) for k in expected_defaults.keys()},
                        "expected_values": expected_defaults
                    }
                )
                return all_correct
            else:
                self.log_result(
                    "CREATE Human-bot Default Values",
                    False,
                    f"Failed to create human bot: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("CREATE Human-bot Default Values", False, f"Error: {str(e)}")
            return False

    def test_update_human_bot_individual_settings(self) -> bool:
        """Test 2: UPDATE Human-bot - test individual delay settings"""
        try:
            # First create a human bot
            create_data = {
                "name": f"TestBot_Update_{int(time.time())}",
                "character": "AGGRESSIVE",
                "gender": "female",
                "min_bet": 15.0,
                "max_bet": 200.0
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                self.log_result(
                    "UPDATE Human-bot Individual Settings",
                    False,
                    f"Failed to create bot for update test: {response.status_code}",
                    response.text
                )
                return False
            
            bot_data = response.json()
            bot_id = bot_data["id"]
            self.created_human_bots.append(bot_id)
            
            # Now update with individual settings
            update_data = {
                "bot_min_delay_seconds": 100,
                "bot_max_delay_seconds": 1500,
                "player_min_delay_seconds": 50,
                "player_max_delay_seconds": 1000,
                "max_concurrent_games": 2
            }
            
            response = requests.put(
                f"{BASE_URL}/admin/human-bots/{bot_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                updated_bot = response.json()
                
                all_correct = True
                details = []
                
                for field, expected_value in update_data.items():
                    actual_value = updated_bot.get(field)
                    if actual_value == expected_value:
                        details.append(f"✅ {field}: {actual_value} (correct)")
                    else:
                        details.append(f"❌ {field}: {actual_value} (expected {expected_value})")
                        all_correct = False
                
                self.log_result(
                    "UPDATE Human-bot Individual Settings",
                    all_correct,
                    f"Individual settings update: {'; '.join(details)}",
                    {
                        "bot_id": bot_id,
                        "actual_values": {k: updated_bot.get(k) for k in update_data.keys()},
                        "expected_values": update_data
                    }
                )
                return all_correct
            else:
                self.log_result(
                    "UPDATE Human-bot Individual Settings",
                    False,
                    f"Failed to update human bot: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("UPDATE Human-bot Individual Settings", False, f"Error: {str(e)}")
            return False

    def test_validation_ranges(self) -> bool:
        """Test 3: VALIDATION - test delay and concurrent games validation (input sanitization)"""
        try:
            validation_tests = [
                # Test delay validation - invalid input should be sanitized to valid default
                {
                    "name": "Delay Below Minimum (Sanitized)",
                    "data": {
                        "name": f"TestBot_ValidationSanitize1_{int(time.time())}",
                        "character": "CAUTIOUS",
                        "min_bet": 10.0,
                        "max_bet": 100.0,
                        "bot_min_delay_seconds": 20  # Below 30 minimum - should be sanitized to 30
                    },
                    "expected_sanitized_value": {"bot_min_delay_seconds": 30}
                },
                # Test delay validation - invalid input should be sanitized to valid default
                {
                    "name": "Delay Above Maximum (Sanitized)",
                    "data": {
                        "name": f"TestBot_ValidationSanitize2_{int(time.time())}",
                        "character": "IMPULSIVE",
                        "min_bet": 10.0,
                        "max_bet": 100.0,
                        "bot_max_delay_seconds": 2500  # Above 2000 maximum - should be sanitized to 2000
                    },
                    "expected_sanitized_value": {"bot_max_delay_seconds": 2000}
                },
                # Test concurrent games validation - invalid input should be sanitized to valid default
                {
                    "name": "Concurrent Games Above Maximum (Sanitized)",
                    "data": {
                        "name": f"TestBot_ValidationSanitize3_{int(time.time())}",
                        "character": "ANALYST",
                        "min_bet": 10.0,
                        "max_bet": 100.0,
                        "max_concurrent_games": 5  # Above 3 maximum - should be sanitized to 1 (default)
                    },
                    "expected_sanitized_value": {"max_concurrent_games": 1}
                },
                # Test valid ranges - should succeed with exact values
                {
                    "name": "Valid Ranges (Exact Values)",
                    "data": {
                        "name": f"TestBot_ValidationPass_{int(time.time())}",
                        "character": "STABLE",
                        "min_bet": 10.0,
                        "max_bet": 100.0,
                        "bot_min_delay_seconds": 30,  # Minimum valid
                        "bot_max_delay_seconds": 2000,  # Maximum valid
                        "player_min_delay_seconds": 100,  # Valid range
                        "player_max_delay_seconds": 1500,  # Valid range
                        "max_concurrent_games": 3  # Maximum valid
                    },
                    "expected_sanitized_value": {
                        "bot_min_delay_seconds": 30,
                        "bot_max_delay_seconds": 2000,
                        "player_min_delay_seconds": 100,
                        "player_max_delay_seconds": 1500,
                        "max_concurrent_games": 3
                    }
                }
            ]
            
            all_validation_correct = True
            validation_details = []
            
            for test in validation_tests:
                response = requests.post(
                    f"{BASE_URL}/admin/human-bots",
                    json=test["data"],
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    bot_data = response.json()
                    self.created_human_bots.append(bot_data["id"])
                    
                    # Check if values were properly sanitized/validated
                    sanitization_correct = True
                    for field, expected_value in test["expected_sanitized_value"].items():
                        actual_value = bot_data.get(field)
                        if actual_value != expected_value:
                            sanitization_correct = False
                            break
                    
                    if sanitization_correct:
                        validation_details.append(f"✅ {test['name']}: Input properly sanitized/validated")
                    else:
                        validation_details.append(f"❌ {test['name']}: Sanitization failed - expected {test['expected_sanitized_value']}, got {actual_value}")
                        all_validation_correct = False
                else:
                    validation_details.append(f"❌ {test['name']}: Request failed ({response.status_code})")
                    all_validation_correct = False
            
            self.log_result(
                "VALIDATION Ranges Testing (Input Sanitization)",
                all_validation_correct,
                f"Validation tests: {'; '.join(validation_details)}"
            )
            return all_validation_correct
            
        except Exception as e:
            self.log_result("VALIDATION Ranges Testing (Input Sanitization)", False, f"Error: {str(e)}")
            return False

    def cleanup_test_bots(self):
        """Clean up created test bots"""
        print("\n🧹 Cleaning up test bots...")
        for bot_id in self.created_human_bots:
            try:
                response = requests.delete(
                    f"{BASE_URL}/admin/human-bots/{bot_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    print(f"✅ Deleted bot {bot_id}")
                else:
                    print(f"⚠️ Failed to delete bot {bot_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error deleting bot {bot_id}: {str(e)}")

    def run_all_tests(self):
        """Run all Human-bot delay fix tests"""
        print("🚀 Starting Human-bot Fields Delay Fix Testing - Russian Review Final Verification")
        print("=" * 80)
        
        # Login as admin
        if not self.admin_login():
            print("❌ Cannot proceed without admin access")
            return False
        
        # Run tests
        test_results = []
        
        print("\n📋 Test 1: CREATE Human-bot - Verify Corrected Default Values")
        print("-" * 60)
        test_results.append(self.test_create_human_bot_default_values())
        
        print("\n📋 Test 2: UPDATE Human-bot - Individual Delay Settings")
        print("-" * 60)
        test_results.append(self.test_update_human_bot_individual_settings())
        
        print("\n📋 Test 3: VALIDATION - Delay and Concurrent Games Ranges")
        print("-" * 60)
        test_results.append(self.test_validation_ranges())
        
        # Cleanup
        self.cleanup_test_bots()
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 HUMAN-BOT DELAY FIX TESTING SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100.0:
            print("\n🎉 ALL CRITICAL PROBLEMS FIXED!")
            print("✅ Default values corrected (bot_max_delay_seconds: 2000, player_max_delay_seconds: 2000, max_concurrent_games: 1)")
            print("✅ Individual delay fields working in UpdateHumanBotRequest")
            print("✅ Validation working with new ranges (30-2000 seconds, 1-3 concurrent games)")
            print("\n🚀 SYSTEM IS PRODUCTION-READY!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} test(s) failed - issues still need to be addressed")
            
            # Show failed tests
            for i, result in enumerate(self.test_results):
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['details']}")
        
        return success_rate == 100.0

def main():
    """Main test execution"""
    tester = HumanBotDelayFixTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests passed - Human-bot delay fix verification complete!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - check the details above")
        sys.exit(1)

if __name__ == "__main__":
    main()