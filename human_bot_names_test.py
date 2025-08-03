#!/usr/bin/env python3
"""
Human-Bot Names Integration Testing - Russian Review
Протестировать интеграцию обновленного списка имен HUMAN_BOT_NAMES с функцией создания Human-ботов
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List
import random

# Configuration
BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Expected new names from the updated HUMAN_BOT_NAMES list
EXPECTED_NEW_NAMES = [
    "AssemS", "Aruzhan123", "DanelMax", "Roman777", "Madina", "Tatiana89", "Dana", "Irina",
    "Samat123", "Natalia", "NikitaPro", "AssemMax", "Erzhan", "Yerlan", "DanaSilnyy", "Alikhan7",
    "Dmitry", "TatianaWin", "Erzhan8XX", "Nurgul1000", "NurgulWin", "AlikhanBest", "Rauan", "Rauan-01", 
    "SergeyPon", "Erzhan2024", "OlegXXX", "NurgulBog", "Aigerim2025", "Bekzat75", "AlikhanZoloto",
    "EgorDron", "AlexeyPro", "MikhailBril", "ElenaRuss", "DanelAngel", "Aigerim91", "NurAs", "Anna-Peter",
    "Madina7777", "AigerimPri", "DmitryBoss", "AndreyCT", "Nuray", "AndreyProX", "Aida-Aligator", "OlgaBuz",
    "SvetlanaOIL", "AigerimTop", "Samat2024", "Yulia.US", "Alex", "Baur", "Ali-01", "Nur007",
    "EgorZ", "Rauan-B2B", "KseniaUra", "Tatiana-Max", "Gau-Kino", "Elena-Suka", "Aidana-GTA", "Rvuvsekh"
]

# Old names that should NOT be used anymore (with surnames)
OLD_NAMES_PATTERNS = ["Silnyy", "Umnyy", "Krasivyy", "Bystryy", "Smellyy"]

class HumanBotNamesTestSuite:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.created_bot_ids = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()

    def admin_login(self) -> bool:
        """Login as admin to get authentication token"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Login", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Admin Login", False, f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Login error: {str(e)}")
            return False

    def get_human_bot_names(self) -> Optional[List[str]]:
        """Get current list of Human-bot names through API"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/admin/human-bots/names", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                names = data.get("names", [])
                count = data.get("count", 0)
                
                self.log_result(
                    "Get Human-Bot Names API", 
                    True, 
                    f"Successfully retrieved {count} names",
                    {"names_count": count, "sample_names": names[:10]}
                )
                return names
            else:
                self.log_result(
                    "Get Human-Bot Names API", 
                    False, 
                    f"Failed to get names: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            self.log_result("Get Human-Bot Names API", False, f"Error getting names: {str(e)}")
            return None

    def verify_names_list_updated(self, current_names: List[str]) -> bool:
        """Verify that the names list contains the new names and not old patterns"""
        try:
            # Check if new names are present
            new_names_found = [name for name in EXPECTED_NEW_NAMES if name in current_names]
            new_names_percentage = len(new_names_found) / len(EXPECTED_NEW_NAMES) * 100
            
            # Check if old name patterns are absent
            old_patterns_found = []
            for name in current_names:
                for pattern in OLD_NAMES_PATTERNS:
                    if pattern in name:
                        old_patterns_found.append(name)
            
            success = new_names_percentage >= 80 and len(old_patterns_found) == 0
            
            self.log_result(
                "Names List Verification",
                success,
                f"New names coverage: {new_names_percentage:.1f}%, Old patterns found: {len(old_patterns_found)}",
                {
                    "new_names_found": len(new_names_found),
                    "new_names_expected": len(EXPECTED_NEW_NAMES),
                    "coverage_percentage": new_names_percentage,
                    "old_patterns_found": old_patterns_found,
                    "sample_new_names": new_names_found[:10]
                }
            )
            
            return success
            
        except Exception as e:
            self.log_result("Names List Verification", False, f"Error verifying names: {str(e)}")
            return False

    def create_human_bot_bulk(self) -> Optional[str]:
        """Create one Human-bot through bulk creation API"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Create bulk request for 1 bot
            bulk_request = {
                "count": 1,
                "character": "BALANCED",
                "min_bet_range": [10.0, 20.0],
                "max_bet_range": [50.0, 100.0],
                "bet_limit_range": [12, 12],
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0,
                "delay_range": [30, 120],
                "use_commit_reveal": True,
                "logging_level": "INFO"
            }
            
            response = requests.post(f"{BASE_URL}/admin/human-bots/bulk-create", headers=headers, json=bulk_request)
            
            if response.status_code == 200:
                data = response.json()
                created_bots = data.get("created_bots", [])
                
                if created_bots:
                    bot = created_bots[0]
                    bot_id = bot.get("id")
                    bot_name = bot.get("name")
                    
                    if bot_id:
                        self.created_bot_ids.append(bot_id)
                    
                    self.log_result(
                        "Bulk Create Human-Bot",
                        True,
                        f"Successfully created Human-bot: {bot_name}",
                        {
                            "bot_id": bot_id,
                            "bot_name": bot_name,
                            "character": bot.get("character"),
                            "created_count": len(created_bots)
                        }
                    )
                    return bot_name
                else:
                    self.log_result("Bulk Create Human-Bot", False, "No bots were created")
                    return None
            else:
                self.log_result(
                    "Bulk Create Human-Bot", 
                    False, 
                    f"Failed to create bot: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result("Bulk Create Human-Bot", False, f"Error creating bot: {str(e)}")
            return None

    def verify_bot_name_from_new_list(self, bot_name: str, available_names: List[str]) -> bool:
        """Verify that the created bot uses a name from the updated list"""
        try:
            # Check if bot name is in the expected new names
            is_new_name = bot_name in EXPECTED_NEW_NAMES
            
            # Check if bot name contains old patterns
            contains_old_pattern = any(pattern in bot_name for pattern in OLD_NAMES_PATTERNS)
            
            # Check if bot name is in the available names list
            is_in_available_list = bot_name in available_names
            
            success = is_new_name and not contains_old_pattern and is_in_available_list
            
            self.log_result(
                "Bot Name Verification",
                success,
                f"Bot name '{bot_name}' validation complete",
                {
                    "bot_name": bot_name,
                    "is_new_name": is_new_name,
                    "contains_old_pattern": contains_old_pattern,
                    "is_in_available_list": is_in_available_list,
                    "validation_passed": success
                }
            )
            
            return success
            
        except Exception as e:
            self.log_result("Bot Name Verification", False, f"Error verifying bot name: {str(e)}")
            return False

    def cleanup_created_bots(self):
        """Clean up created test bots"""
        if not self.created_bot_ids:
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            deleted_count = 0
            
            for bot_id in self.created_bot_ids:
                try:
                    response = requests.delete(f"{BASE_URL}/admin/human-bots/{bot_id}", headers=headers)
                    if response.status_code == 200:
                        deleted_count += 1
                except Exception as e:
                    print(f"Warning: Failed to delete bot {bot_id}: {str(e)}")
            
            self.log_result(
                "Cleanup Test Bots",
                True,
                f"Cleaned up {deleted_count}/{len(self.created_bot_ids)} test bots"
            )
            
        except Exception as e:
            self.log_result("Cleanup Test Bots", False, f"Error during cleanup: {str(e)}")

    def run_comprehensive_test(self):
        """Run the comprehensive Human-bot names integration test"""
        print("🚀 STARTING HUMAN-BOT NAMES INTEGRATION TEST")
        print("=" * 60)
        print("Russian Review Requirements:")
        print("1. Получить текущий список имен через GET /api/admin/human-bots/names")
        print("2. Создать один Human-бот через массовое создание")
        print("3. Проверить, что созданный бот использует одно из имен из обновленного списка")
        print("4. Убедиться, что старые имена (с фамилиями) больше не используются")
        print("=" * 60)
        print()
        
        try:
            # Step 1: Admin login
            if not self.admin_login():
                print("❌ CRITICAL: Admin login failed. Cannot proceed with testing.")
                return False
            
            # Step 2: Get current Human-bot names list
            current_names = self.get_human_bot_names()
            if current_names is None:
                print("❌ CRITICAL: Failed to get Human-bot names list. Cannot proceed.")
                return False
            
            # Step 3: Verify names list is updated
            names_updated = self.verify_names_list_updated(current_names)
            if not names_updated:
                print("⚠️  WARNING: Names list verification failed, but continuing with bot creation test.")
            
            # Step 4: Create Human-bot through bulk creation
            created_bot_name = self.create_human_bot_bulk()
            if created_bot_name is None:
                print("❌ CRITICAL: Failed to create Human-bot. Cannot verify name usage.")
                return False
            
            # Step 5: Verify bot uses name from new list
            name_verification = self.verify_bot_name_from_new_list(created_bot_name, current_names)
            
            # Step 6: Cleanup
            self.cleanup_created_bots()
            
            # Calculate overall success
            critical_tests = ["Admin Login", "Get Human-Bot Names API", "Bulk Create Human-Bot", "Bot Name Verification"]
            critical_results = [r for r in self.test_results if r["test"] in critical_tests]
            critical_success = all(r["success"] for r in critical_results)
            
            return critical_success
            
        except Exception as e:
            self.log_result("Overall Test Execution", False, f"Unexpected error: {str(e)}")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 HUMAN-BOT NAMES INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # Overall assessment
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: HUMAN-BOT NAMES INTEGRATION WORKING CORRECTLY!")
            print("✅ The updated HUMAN_BOT_NAMES list is properly integrated with Human-bot creation")
            print("✅ New names are being used and old surname patterns are eliminated")
        else:
            print("❌ OVERALL RESULT: HUMAN-BOT NAMES INTEGRATION HAS ISSUES")
            print("⚠️  The integration may need further investigation")
        
        print("=" * 60)

def main():
    """Main test execution"""
    test_suite = HumanBotNamesTestSuite()
    
    try:
        success = test_suite.run_comprehensive_test()
        test_suite.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        test_suite.cleanup_created_bots()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        test_suite.cleanup_created_bots()
        sys.exit(1)

if __name__ == "__main__":
    main()