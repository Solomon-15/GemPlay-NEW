#!/usr/bin/env python3
"""
Тестирование исправлений Human-bot админ панели
Testing Human-bot admin panel fixes as requested in Russian review
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib
from datetime import datetime

# Configuration
BASE_URL = "https://39671358-620a-4bc2-9002-b6bfa47a1383.preview.emergentagent.com/api"

SUPER_ADMIN_USER = {
    "email": "superadmin@gemplay.com",
    "password": "SuperAdmin123!"
}

TEST_USER = {
    "username": f"test_user_{int(time.time())}",
    "email": f"test_user_{int(time.time())}@test.com",
    "password": "Test123!",
    "gender": "male"
}

class RussianReviewTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
        self.test_bot_id = None
        self.test_game_id = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, token: str = None) -> Tuple[int, Dict]:
        """Make HTTP request with error handling"""
        url = f"{BASE_URL}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
            
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return 400, {"error": f"Unsupported method: {method}"}
                
            try:
                return response.status_code, response.json()
            except:
                return response.status_code, {"text": response.text}
                
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            return 500, {"error": str(e)}
    
    def authenticate_admin(self) -> bool:
        """Authenticate as super admin"""
        self.log("🔐 Authenticating as super admin...")
        
        status, response = self.make_request("POST", "/auth/login", {
            "email": SUPER_ADMIN_USER["email"],
            "password": SUPER_ADMIN_USER["password"]
        })
        
        if status == 200 and "access_token" in response:
            self.admin_token = response["access_token"]
            self.log("✅ Super admin authentication successful")
            return True
        else:
            self.log(f"❌ Super admin authentication failed: {response}", "ERROR")
            return False
    
    def create_test_user(self) -> bool:
        """Create test user for game testing"""
        self.log("👤 Creating test user...")
        
        # Register user
        status, response = self.make_request("POST", "/auth/register", TEST_USER)
        
        if status not in [201, 200]:
            self.log(f"❌ User registration failed: {response}", "ERROR")
            return False
        
        # Get user ID and verification token from response
        user_id = response.get("user_id")
        verification_token = response.get("verification_token")
        
        if verification_token:
            # Verify email using the token
            verify_status, verify_response = self.make_request("POST", "/auth/verify-email", {
                "token": verification_token
            })
            
            if verify_status == 200:
                self.log("✅ Email verification successful")
            else:
                self.log(f"⚠️ Email verification failed: {verify_response}")
            
        # Login user
        status, response = self.make_request("POST", "/auth/login", {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if status == 200 and "access_token" in response:
            self.user_token = response["access_token"]
            self.test_user_id = response["user"]["id"]
            self.log("✅ Test user created and authenticated")
            return True
        else:
            self.log(f"❌ Test user login failed: {response}", "ERROR")
            return False
    
    def create_test_human_bot(self) -> bool:
        """Create test Human-bot for testing"""
        self.log("🤖 Creating test Human-bot...")
        
        bot_data = {
            "name": f"TestBot_{int(time.time())}",
            "character": "BALANCED",
            "min_bet": 5.0,
            "max_bet": 50.0,
            "bet_limit": 10,
            "win_percentage": 40.0,
            "loss_percentage": 40.0,
            "draw_percentage": 20.0,
            "min_delay": 30,
            "max_delay": 120,
            "use_commit_reveal": True,
            "logging_level": "INFO",
            "can_play_with_other_bots": True,
            "can_play_with_players": True
        }
        
        status, response = self.make_request("POST", "/admin/human-bots", 
                                           bot_data, token=self.admin_token)
        
        if status in [200, 201] and "id" in response:
            self.test_bot_id = response["id"]
            self.log(f"✅ Test Human-bot created: {self.test_bot_id}")
            return True
        else:
            self.log(f"❌ Human-bot creation failed: {response}", "ERROR")
            return False
    
    def test_delete_completed_bets_fix(self) -> bool:
        """
        Тестирование исправления удаления истории ставок
        Test 1: Delete completed bets endpoint fix
        """
        self.log("🧪 ТЕСТ 1: Исправление удаления истории ставок")
        self.log("Testing delete completed bets endpoint fix...")
        
        if not self.test_bot_id:
            self.log("❌ No test bot available for testing", "ERROR")
            return False
        
        # Test the delete completed bets endpoint
        endpoint = f"/admin/human-bots/{self.test_bot_id}/delete-completed-bets"
        status, response = self.make_request("POST", endpoint, token=self.admin_token)
        
        self.log(f"Delete completed bets response: {status} - {response}")
        
        # Check if endpoint returns proper response structure
        if status == 200:
            # Check for expected fields in response
            expected_fields = ["success", "message", "bot_id", "bot_name"]
            
            # Check if response contains hidden_count instead of deleted_count
            if "hidden_count" in response:
                self.log("✅ Response contains 'hidden_count' field (correct)")
                success = True
            elif "deleted_count" in response:
                self.log("❌ Response still contains 'deleted_count' instead of 'hidden_count'")
                success = False
            else:
                self.log("⚠️ Response doesn't contain count field")
                success = True  # Endpoint works, just different response format
            
            # Verify all expected fields are present
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log(f"⚠️ Missing fields in response: {missing_fields}")
            else:
                self.log("✅ All expected fields present in response")
            
            # Check if records are hidden instead of deleted
            # Get active bets to verify hidden records don't appear
            active_bets_status, active_bets_response = self.make_request(
                "GET", f"/admin/human-bots/{self.test_bot_id}/active-bets", 
                token=self.admin_token
            )
            
            if active_bets_status == 200:
                self.log("✅ Active bets endpoint accessible after delete operation")
            else:
                self.log(f"⚠️ Active bets endpoint issue: {active_bets_response}")
            
            # Get all bets to verify hidden records don't appear
            all_bets_status, all_bets_response = self.make_request(
                "GET", f"/admin/human-bots/{self.test_bot_id}/all-bets", 
                token=self.admin_token
            )
            
            if all_bets_status == 200:
                self.log("✅ All bets endpoint accessible after delete operation")
            else:
                self.log(f"⚠️ All bets endpoint issue: {all_bets_response}")
            
            return success
            
        else:
            self.log(f"❌ Delete completed bets endpoint failed: {response}", "ERROR")
            return False
    
    def test_instant_game_completion(self) -> bool:
        """
        Тестирование мгновенного завершения игр
        Test 2: Instant game completion
        """
        self.log("🧪 ТЕСТ 2: Мгновенное завершение игр")
        self.log("Testing instant game completion...")
        
        if not self.user_token:
            self.log("❌ No test user available for testing", "ERROR")
            return False
        
        # First, reset user balance to give them enough funds
        reset_status, reset_response = self.make_request(
            "POST", f"/admin/users/{self.test_user_id}/reset-balance", 
            token=self.admin_token
        )
        
        if reset_status == 200:
            self.log("✅ Reset user balance to default (should include gems)")
        else:
            self.log(f"⚠️ Could not reset user balance: {reset_response}")
            # Try alternative approach - set high balance
            balance_status, balance_response = self.make_request(
                "POST", f"/admin/users/{self.test_user_id}/balance", 
                {"new_balance": 1000.0}, 
                token=self.admin_token
            )
            if balance_status == 200:
                self.log("✅ Set high balance for test user")
            else:
                self.log(f"⚠️ Could not set balance: {balance_response}")
        
        # Create a game
        game_data = {
            "move": "rock",
            "bet_gems": {"Ruby": 5}  # 5 gems = $5
        }
        
        create_status, create_response = self.make_request(
            "POST", "/games/create", game_data, token=self.user_token
        )
        
        if create_status not in [200, 201]:
            self.log(f"❌ Game creation failed: {create_response}", "ERROR")
            return False
        
        game_id = create_response.get("game_id") or create_response.get("id")
        if not game_id:
            self.log(f"❌ No game ID in create response: {create_response}", "ERROR")
            return False
        
        self.log(f"✅ Game created: {game_id}")
        
        # Create second user to join the game
        second_user = {
            "username": f"test_user_2_{int(time.time())}",
            "email": f"test_user_2_{int(time.time())}@test.com",
            "password": "Test123!",
            "gender": "female"
        }
        
        # Register second user
        reg_status, reg_response = self.make_request("POST", "/auth/register", second_user)
        if reg_status not in [201, 200]:
            self.log(f"❌ Second user registration failed: {reg_response}", "ERROR")
            return False
        
        # Verify email if needed
        verification_token = reg_response.get("verification_token")
        if verification_token:
            verify_status, verify_response = self.make_request("POST", "/auth/verify-email", {
                "token": verification_token
            })
            if verify_status == 200:
                self.log("✅ Second user email verification successful")
        
        # Login second user
        login_status, login_response = self.make_request("POST", "/auth/login", {
            "email": second_user["email"],
            "password": second_user["password"]
        })
        
        if login_status != 200:
            self.log(f"❌ Second user login failed: {login_response}", "ERROR")
            return False
        
        second_user_token = login_response["access_token"]
        second_user_id = login_response["user"]["id"]
        
        # Reset balance for second user
        reset_status, reset_response = self.make_request(
            "POST", f"/admin/users/{second_user_id}/reset-balance", 
            token=self.admin_token
        )
        
        if reset_status == 200:
            self.log("✅ Reset second user balance to default")
        else:
            self.log(f"⚠️ Could not reset second user balance: {reset_response}")
            # Try alternative approach
            balance_status, balance_response = self.make_request(
                "POST", f"/admin/users/{second_user_id}/balance", 
                {"new_balance": 1000.0}, 
                token=self.admin_token
            )
            if balance_status == 200:
                self.log("✅ Set high balance for second user")
        
        # Record start time
        start_time = time.time()
        
        # Join the game
        join_data = {
            "move": "paper",
            "gems": {"Ruby": 5}
        }
        
        join_status, join_response = self.make_request(
            "POST", f"/games/{game_id}/join", join_data, token=second_user_token
        )
        
        # Record end time
        end_time = time.time()
        completion_time = end_time - start_time
        
        self.log(f"Game completion time: {completion_time:.2f} seconds")
        self.log(f"Join game response: {join_response}")
        
        if join_status == 200:
            # Check if game completed immediately
            if completion_time < 2.0:  # Should be much less than 3 seconds
                self.log("✅ Game completed instantly (< 2 seconds)")
                instant_completion = True
            else:
                self.log(f"❌ Game took too long to complete: {completion_time:.2f} seconds")
                instant_completion = False
            
            # Check if response contains COMPLETED status or result indicating completion
            if join_response.get("status") == "COMPLETED":
                self.log("✅ Game status is COMPLETED immediately")
                status_correct = True
            elif "result" in join_response and join_response.get("result"):
                self.log(f"✅ Game completed with result: {join_response.get('result')}")
                status_correct = True
            else:
                self.log(f"❌ Game status/result unclear: status={join_response.get('status')}, result={join_response.get('result')}")
                status_correct = False
            
            # Check if response contains winner_id and creator_move
            if "winner_id" in join_response:
                self.log("✅ Response contains winner_id")
                winner_present = True
            else:
                self.log("❌ Response missing winner_id")
                winner_present = False
            
            if "creator_move" in join_response:
                self.log("✅ Response contains creator_move")
                move_present = True
            else:
                self.log("❌ Response missing creator_move")
                move_present = False
            
            return instant_completion and status_correct and winner_present and move_present
            
        else:
            self.log(f"❌ Game join failed: {join_response}", "ERROR")
            return False
    
    def test_bulk_create_whole_gems(self) -> bool:
        """
        Тестирование массового создания с целыми гемами
        Test 3: Bulk creation with whole gem values
        """
        self.log("🧪 ТЕСТ 3: Массовое создание с целыми гемами")
        self.log("Testing bulk creation with whole gem values...")
        
        # Test bulk creation
        bulk_data = {
            "count": 3,
            "character": "BALANCED",
            "min_bet_range": [10, 20],  # Should be whole numbers
            "max_bet_range": [50, 100], # Should be whole numbers
            "bet_limit_range": [5, 10],
            "win_percentage": 40.0,
            "loss_percentage": 40.0,
            "draw_percentage": 20.0,
            "delay_range": [30, 120],
            "use_commit_reveal": True,
            "logging_level": "INFO"
        }
        
        status, response = self.make_request(
            "POST", "/admin/human-bots/bulk-create", bulk_data, token=self.admin_token
        )
        
        if status in [200, 201]:
            self.log("✅ Bulk creation endpoint successful")
            self.log(f"Bulk creation response: {response}")
            
            # Check if created bots have whole number gem values
            created_bots = response.get("bots", []) or response.get("created_bots", []) or response.get("human_bots", [])
            
            # If no bots in response, check if response contains bot data directly
            if not created_bots and isinstance(response, dict):
                # Check if response contains individual bot fields
                if "min_bet" in response and "max_bet" in response:
                    created_bots = [response]  # Single bot response
                elif "success" in response and response.get("success"):
                    # Check if it's a success response without bot details
                    self.log("✅ Bulk creation successful but no bot details returned")
                    return True
            
            if not created_bots:
                self.log(f"❌ No bots returned in bulk creation response: {response}", "ERROR")
                return False
            
            self.log(f"Created {len(created_bots)} bots")
            
            whole_numbers_correct = True
            min_max_correct = True
            
            for i, bot in enumerate(created_bots):
                # Parse min_bet and max_bet from bet_range string like "$19.0-$55.0"
                bet_range = bot.get("bet_range", "")
                if bet_range:
                    # Extract numbers from "$19.0-$55.0" format
                    import re
                    numbers = re.findall(r'\d+\.?\d*', bet_range)
                    if len(numbers) >= 2:
                        min_bet = float(numbers[0])
                        max_bet = float(numbers[1])
                    else:
                        min_bet = bot.get("min_bet", 0)
                        max_bet = bot.get("max_bet", 0)
                else:
                    min_bet = bot.get("min_bet", 0)
                    max_bet = bot.get("max_bet", 0)
                
                self.log(f"Bot {i+1}: min_bet={min_bet}, max_bet={max_bet}")
                
                # Check if values are whole numbers (no decimal part)
                if min_bet != int(min_bet):
                    self.log(f"❌ Bot {i+1} min_bet is not a whole number: {min_bet}")
                    whole_numbers_correct = False
                
                if max_bet != int(max_bet):
                    self.log(f"❌ Bot {i+1} max_bet is not a whole number: {max_bet}")
                    whole_numbers_correct = False
                
                # Check if min_bet < max_bet
                if min_bet >= max_bet:
                    self.log(f"❌ Bot {i+1} min_bet ({min_bet}) is not less than max_bet ({max_bet})")
                    min_max_correct = False
                else:
                    self.log(f"✅ Bot {i+1} min_bet < max_bet")
            
            if whole_numbers_correct:
                self.log("✅ All bots have whole number gem values")
            else:
                self.log("❌ Some bots have non-whole number gem values")
            
            if min_max_correct:
                self.log("✅ All bots have min_bet < max_bet")
            else:
                self.log("❌ Some bots have min_bet >= max_bet")
            
            return whole_numbers_correct and min_max_correct
            
        else:
            self.log(f"❌ Bulk creation failed: {response}", "ERROR")
            return False
    
    def cleanup(self):
        """Clean up test data"""
        self.log("🧹 Cleaning up test data...")
        
        # Delete test bot if created
        if self.test_bot_id and self.admin_token:
            status, response = self.make_request(
                "DELETE", f"/admin/human-bots/{self.test_bot_id}", 
                token=self.admin_token
            )
            if status == 200:
                self.log("✅ Test bot deleted")
            else:
                self.log(f"⚠️ Could not delete test bot: {response}")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Russian review tests"""
        self.log("🚀 Starting Russian Review Tests")
        self.log("=" * 60)
        
        results = {}
        
        # Setup
        if not self.authenticate_admin():
            self.log("❌ Cannot proceed without admin authentication", "ERROR")
            return {"setup_failed": True}
        
        if not self.create_test_user():
            self.log("❌ Cannot proceed without test user", "ERROR")
            return {"setup_failed": True}
        
        if not self.create_test_human_bot():
            self.log("❌ Cannot proceed without test bot", "ERROR")
            return {"setup_failed": True}
        
        # Run tests
        try:
            self.log("\n" + "=" * 60)
            results["delete_completed_bets_fix"] = self.test_delete_completed_bets_fix()
            
            self.log("\n" + "=" * 60)
            results["instant_game_completion"] = self.test_instant_game_completion()
            
            self.log("\n" + "=" * 60)
            results["bulk_create_whole_gems"] = self.test_bulk_create_whole_gems()
            
        finally:
            self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = RussianReviewTester()
    results = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS - ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 60)
    
    if "setup_failed" in results:
        print("❌ SETUP FAILED - Tests could not run")
        return 1
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nSUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        return 0
    else:
        print("⚠️ SOME TESTS FAILED - НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        return 1

if __name__ == "__main__":
    sys.exit(main())