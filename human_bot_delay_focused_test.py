#!/usr/bin/env python3
"""
Human-bot Delay Fields Backend Model Fix Testing - Russian Review
FOCUSED TESTING as requested in the review context

CONTEXT: Fixed HumanBot model in backend/server.py:
- bot_max_delay_seconds: default=120 → default=2000, le=3600 → le=2000
- player_max_delay_seconds: default=120 → default=2000, le=3600 → le=2000  
- max_concurrent_games: default=3 → default=1, le=100 → le=3
- Minimum values: ge=1 → ge=30 for all delays

FOCUSED TESTING:
1. CREATE Human-bot - проверить что backend возвращает правильные значения по умолчанию
2. UPDATE Human-bot - изменить индивидуальные настройки  
3. VALIDATION - проверить что backend правильно валидирует диапазоны
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional
import random

# Configuration
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class HumanBotDelayFocusedTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.created_bot_ids = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
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
                self.admin_token = data["access_token"]
                self.log_result("Admin Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def generate_unique_name(self) -> str:
        """Generate unique bot name"""
        timestamp = int(time.time())
        return f"DelayTestBot_{timestamp}"
    
    def test_create_human_bot_defaults(self) -> bool:
        """
        TEST 1: CREATE Human-bot - проверить что backend возвращает правильные значения по умолчанию:
        - bot_min_delay_seconds: 30
        - bot_max_delay_seconds: 2000
        - player_min_delay_seconds: 30
        - player_max_delay_seconds: 2000
        - max_concurrent_games: 1
        """
        try:
            bot_name = self.generate_unique_name()
            create_data = {
                "name": bot_name,
                "character": "BALANCED",
                "gender": "male",
                "min_bet": 10.0,
                "max_bet": 100.0,
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0
                # Not specifying delay fields to test defaults
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=create_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                bot_data = response.json()
                self.created_bot_ids.append(bot_data["id"])
                
                # Verify expected default values from Russian review
                expected_defaults = {
                    "bot_min_delay_seconds": 30,
                    "bot_max_delay_seconds": 2000,
                    "player_min_delay_seconds": 30,
                    "player_max_delay_seconds": 2000,
                    "max_concurrent_games": 1
                }
                
                all_correct = True
                details = []
                
                for field, expected_value in expected_defaults.items():
                    actual_value = bot_data.get(field)
                    if actual_value == expected_value:
                        details.append(f"{field}: {actual_value} ✓")
                    else:
                        details.append(f"{field}: {actual_value} (expected {expected_value}) ✗")
                        all_correct = False
                
                self.log_result(
                    "CREATE Human-bot Default Values",
                    all_correct,
                    f"Bot created with ID {bot_data['id']}. " + "; ".join(details)
                )
                return all_correct
            else:
                self.log_result(
                    "CREATE Human-bot Default Values",
                    False,
                    f"Failed to create bot. Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("CREATE Human-bot Default Values", False, f"Exception: {str(e)}")
            return False
    
    def test_update_human_bot_individual_settings(self) -> bool:
        """
        TEST 2: UPDATE Human-bot - изменить индивидуальные настройки:
        - bot_min_delay_seconds: 100, bot_max_delay_seconds: 1500
        - player_min_delay_seconds: 50, player_max_delay_seconds: 1000
        - max_concurrent_games: 2
        """
        if not self.created_bot_ids:
            self.log_result("UPDATE Human-bot Individual Settings", False, "No bot available for update test")
            return False
            
        try:
            bot_id = self.created_bot_ids[0]
            
            # Update with specific delay values as requested in Russian review
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
                        details.append(f"{field}: {actual_value} ✓")
                    else:
                        details.append(f"{field}: {actual_value} (expected {expected_value}) ✗")
                        all_correct = False
                
                if not all_correct:
                    # CRITICAL BUG DETECTED: UpdateHumanBotRequest model missing individual delay fields
                    details.append("CRITICAL BUG: UpdateHumanBotRequest model missing individual delay fields!")
                
                self.log_result(
                    "UPDATE Human-bot Individual Settings",
                    all_correct,
                    "Updated bot settings. " + "; ".join(details)
                )
                return all_correct
            else:
                self.log_result(
                    "UPDATE Human-bot Individual Settings",
                    False,
                    f"Failed to update bot. Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("UPDATE Human-bot Individual Settings", False, f"Exception: {str(e)}")
            return False
    
    def test_validation_ranges(self) -> bool:
        """
        TEST 3: VALIDATION - проверить что backend правильно валидирует диапазоны:
        - Задержки: 30-2000 секунд
        - concurrent games: 1-3
        """
        validation_tests = [
            # Test minimum delay validation (should be >= 30)
            {
                "name": "Min Delay Too Low (< 30)",
                "data": {
                    "name": self.generate_unique_name(),
                    "character": "BALANCED",
                    "gender": "male",
                    "min_bet": 10.0,
                    "max_bet": 100.0,
                    "win_percentage": 40.0,
                    "loss_percentage": 40.0,
                    "draw_percentage": 20.0,
                    "bot_min_delay_seconds": 10  # Should fail (< 30)
                },
                "should_fail": True,
                "expected_error": "validation error"
            },
            # Test maximum delay validation (should be <= 2000)
            {
                "name": "Max Delay Too High (> 2000)",
                "data": {
                    "name": self.generate_unique_name(),
                    "character": "BALANCED",
                    "gender": "male",
                    "min_bet": 10.0,
                    "max_bet": 100.0,
                    "win_percentage": 40.0,
                    "loss_percentage": 40.0,
                    "draw_percentage": 20.0,
                    "bot_max_delay_seconds": 3000  # Should fail (> 2000)
                },
                "should_fail": True,
                "expected_error": "validation error"
            },
            # Test concurrent games validation (should be <= 3)
            {
                "name": "Concurrent Games Too High (> 3)",
                "data": {
                    "name": self.generate_unique_name(),
                    "character": "BALANCED",
                    "gender": "male",
                    "min_bet": 10.0,
                    "max_bet": 100.0,
                    "win_percentage": 40.0,
                    "loss_percentage": 40.0,
                    "draw_percentage": 20.0,
                    "max_concurrent_games": 5  # Should fail (> 3)
                },
                "should_fail": True,
                "expected_error": "validation error"
            },
            # Test valid ranges (should pass)
            {
                "name": "Valid Ranges (30-2000 seconds, 1-3 games)",
                "data": {
                    "name": self.generate_unique_name(),
                    "character": "BALANCED",
                    "gender": "male",
                    "min_bet": 10.0,
                    "max_bet": 100.0,
                    "win_percentage": 40.0,
                    "loss_percentage": 40.0,
                    "draw_percentage": 20.0,
                    "bot_min_delay_seconds": 30,
                    "bot_max_delay_seconds": 2000,
                    "player_min_delay_seconds": 30,
                    "player_max_delay_seconds": 2000,
                    "max_concurrent_games": 3
                },
                "should_fail": False,
                "expected_error": None
            }
        ]
        
        all_validation_passed = True
        
        for test in validation_tests:
            try:
                response = requests.post(
                    f"{BASE_URL}/admin/human-bots",
                    json=test["data"],
                    headers=self.get_auth_headers()
                )
                
                if test["should_fail"]:
                    # Should return validation error
                    if response.status_code == 422:  # Validation error
                        self.log_result(
                            f"VALIDATION - {test['name']}",
                            True,
                            f"Correctly rejected invalid data with status {response.status_code}"
                        )
                    else:
                        self.log_result(
                            f"VALIDATION - {test['name']}",
                            False,
                            f"Should have failed but got status {response.status_code}"
                        )
                        all_validation_passed = False
                else:
                    # Should succeed
                    if response.status_code == 200:
                        bot_data = response.json()
                        self.created_bot_ids.append(bot_data["id"])
                        self.log_result(
                            f"VALIDATION - {test['name']}",
                            True,
                            f"Correctly accepted valid data. Bot ID: {bot_data['id']}"
                        )
                    else:
                        self.log_result(
                            f"VALIDATION - {test['name']}",
                            False,
                            f"Should have succeeded but got status {response.status_code}: {response.text}"
                        )
                        all_validation_passed = False
                        
            except Exception as e:
                self.log_result(f"VALIDATION - {test['name']}", False, f"Exception: {str(e)}")
                all_validation_passed = False
        
        return all_validation_passed
    
    def cleanup_test_bots(self):
        """Clean up created test bots"""
        for bot_id in self.created_bot_ids:
            try:
                response = requests.delete(
                    f"{BASE_URL}/admin/human-bots/{bot_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    print(f"✅ Cleaned up test bot {bot_id}")
                else:
                    print(f"⚠️ Failed to clean up test bot {bot_id}")
            except Exception as e:
                print(f"⚠️ Exception cleaning up bot {bot_id}: {str(e)}")
    
    def run_all_tests(self):
        """Run all Human-bot delay field tests as requested in Russian review"""
        print("=" * 80)
        print("HUMAN-BOT DELAY FIELDS BACKEND MODEL FIX TESTING")
        print("Russian Review: Повторное тестирование исправлений полей задержек Human-ботов")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with tests.")
            return
        
        # Run focused tests as requested
        test_results = []
        
        print("\n🔍 TEST 1: CREATE Human-bot - проверить правильные значения по умолчанию")
        test_results.append(self.test_create_human_bot_defaults())
        
        print("\n🔍 TEST 2: UPDATE Human-bot - изменить индивидуальные настройки")
        test_results.append(self.test_update_human_bot_individual_settings())
        
        print("\n🔍 TEST 3: VALIDATION - проверить валидацию диапазонов")
        test_results.append(self.test_validation_ranges())
        
        # Summary
        print("\n" + "=" * 80)
        print("HUMAN-BOT DELAY FIELDS TESTING SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"✅ PASSED: {passed_tests}/{total_tests} tests ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 ALL HUMAN-BOT DELAY FIELD TESTS PASSED!")
            print("✅ Backend возвращает правильные значения по умолчанию")
            print("✅ UPDATE операции работают и сохраняют новые значения")
            print("✅ Валидация диапазонов работает корректно")
        else:
            print("❌ SOME TESTS FAILED - Backend model needs fixes")
            print("\n🔍 CRITICAL ISSUES FOUND:")
            if not test_results[1]:  # UPDATE test failed
                print("❌ CRITICAL BUG: UpdateHumanBotRequest model missing individual delay fields!")
                print("   Fields missing: bot_min_delay_seconds, bot_max_delay_seconds,")
                print("                   player_min_delay_seconds, player_max_delay_seconds,")
                print("                   max_concurrent_games")
                print("   Location: /app/backend/server.py lines 744-762")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        self.cleanup_test_bots()
        
        print("\n" + "=" * 80)
        print("HUMAN-BOT DELAY FIELDS TESTING COMPLETED")
        print("=" * 80)

if __name__ == "__main__":
    tester = HumanBotDelayFocusedTester()
    tester.run_all_tests()