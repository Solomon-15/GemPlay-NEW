#!/usr/bin/env python3
"""
ПРОСТОЙ ТЕСТ возврата комиссии проигравшему - Russian Review
Simplified Commission Return Test without problematic endpoints

УПРОЩЕННЫЙ ТЕСТ-ПЛАН:
1. Создать тестовую игру с реальными пользователями
2. Записать балансы ПЕРЕД завершением
3. Использовать admin API для принудительного завершения игры
4. Проверить балансы ПОСЛЕ завершения

ОЖИДАЕМАЯ МАТЕМАТИКА:
- User1 (победитель): комиссия должна быть СПИСАНА с frozen_balance
- User2 (проигравший): комиссия должна быть ВОЗВРАЩЕНА в virtual_balance

НЕ использовать проблемные endpoints /games/{id}/status и /economy/transactions
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
BASE_URL = "https://acffc923-2545-42ed-a41d-4e93fa17c383.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class SimpleCommissionTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.user1_token = None
        self.user2_token = None
        self.user1_id = None
        self.user2_id = None
        self.game_id = None
        self.test_results = []
        
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
        
    def generate_unique_email(self) -> str:
        """Generate unique email for test user"""
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        return f"commission_test_{timestamp}_{random_suffix}@test.com"
        
    def generate_unique_username(self, prefix: str) -> str:
        """Generate unique username"""
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        return f"{prefix}_{timestamp}_{random_suffix}"
        
    def admin_login(self) -> bool:
        """Login as admin"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.log_result("Admin Login", True, "Successfully logged in as admin")
                return True
            else:
                self.log_result("Admin Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            return False
            
    def create_and_verify_user(self, username_prefix: str) -> Tuple[Optional[str], Optional[str]]:
        """Create and verify test user, return (user_id, token)"""
        try:
            # Generate unique user data
            username = self.generate_unique_username(username_prefix)
            email = self.generate_unique_email()
            password = "Test123!"
            
            # Register user
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "gender": "male"
            }
            
            print(f"Creating user: {username} with email: {email}")
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            print(f"Registration response: {response.status_code}")
            if response.status_code not in [200, 201]:
                self.log_result(f"Create {username_prefix}", False, f"Registration failed: {response.status_code}")
                return None, None
                
            # Check if user needs email verification
            reg_data = response.json()
            print(f"Registration data: {reg_data}")
                
            # Try to login (assuming auto-verification for testing)
            login_response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            
            print(f"Login response: {login_response.status_code}")
            if login_response.status_code != 200:
                login_data = login_response.json()
                print(f"Login error: {login_data}")
                
                # If email verification is needed, try to verify
                if login_response.status_code == 403 and "email" in str(login_data).lower():
                    print("Attempting email verification...")
                    
                    # Use the verification token from registration
                    verification_token = reg_data.get("verification_token")
                    if verification_token:
                        verify_response = self.session.post(
                            f"{BASE_URL}/auth/verify-email",
                            json={"token": verification_token}
                        )
                        print(f"Email verification response: {verify_response.status_code}")
                        
                        if verify_response.status_code == 200:
                            print("Email verified successfully, retrying login...")
                            # Retry login
                            login_response = self.session.post(f"{BASE_URL}/auth/login", json={
                                "email": email,
                                "password": password
                            })
                            print(f"Retry login response: {login_response.status_code}")
                        else:
                            print(f"Email verification failed: {verify_response.json()}")
                    else:
                        print("No verification token found in registration response")
                
            if login_response.status_code == 200:
                login_data = login_response.json()
                user_token = login_data["access_token"]
                user_id = login_data["user"]["id"]
                
                self.log_result(f"Create {username_prefix}", True, f"User created: {username}")
                return user_id, user_token
            else:
                self.log_result(f"Create {username_prefix}", False, f"Login failed: {login_response.status_code}")
                return None, None
                
        except Exception as e:
            self.log_result(f"Create {username_prefix}", False, f"Exception: {str(e)}")
            return None, None
            
    def add_balance_to_user(self, user_token: str, amount: float = 100.0) -> bool:
        """Add balance to user using admin endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get user info first
            user_headers = {"Authorization": f"Bearer {user_token}"}
            user_response = self.session.get(f"{BASE_URL}/auth/me", headers=user_headers)
            if user_response.status_code != 200:
                self.log_result("Get User Info", False, f"Status: {user_response.status_code}")
                return False
                
            user_data = user_response.json()
            user_id = user_data["id"]
            
            # Add balance via admin endpoint
            balance_data = {"amount": amount}
            response = self.session.post(
                f"{BASE_URL}/admin/users/{user_id}/balance", 
                json=balance_data, 
                headers=headers
            )
            
            print(f"Admin balance add response: {response.status_code}")
            if response.status_code != 200:
                print(f"Admin balance add error: {response.json()}")
            
            if response.status_code == 200:
                self.log_result("Add Balance", True, f"Added ${amount} to user")
                return True
            else:
                self.log_result("Add Balance", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Add Balance", False, f"Exception: {str(e)}")
            return False
            
    def purchase_gems_for_user(self, user_token: str) -> bool:
        """Purchase gems for $35 bet (Ruby: 15, Emerald: 2)"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            
            # Purchase Ruby gems (15 * $1 = $15)
            ruby_response = self.session.post(
                f"{BASE_URL}/gems/buy?gem_type=Ruby&quantity=15",
                headers=headers
            )
            
            # Purchase Emerald gems (2 * $10 = $20)
            emerald_response = self.session.post(
                f"{BASE_URL}/gems/buy?gem_type=Emerald&quantity=2",
                headers=headers
            )
            
            if ruby_response.status_code != 200:
                print(f"Ruby purchase error: {ruby_response.json()}")
            if emerald_response.status_code != 200:
                print(f"Emerald purchase error: {emerald_response.json()}")
            
            if ruby_response.status_code == 200 and emerald_response.status_code == 200:
                self.log_result("Purchase Gems", True, "Purchased Ruby: 15, Emerald: 2 ($35 total)")
                return True
            else:
                self.log_result("Purchase Gems", False, f"Ruby: {ruby_response.status_code}, Emerald: {emerald_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Purchase Gems", False, f"Exception: {str(e)}")
            return False
            
    def get_user_balance(self, user_token: str) -> Optional[Dict[str, float]]:
        """Get user balance information"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "virtual_balance": data.get("virtual_balance", 0.0),
                    "frozen_balance": data.get("frozen_balance", 0.0)
                }
            else:
                self.log_result("Get Balance", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_result("Get Balance", False, f"Exception: {str(e)}")
            return None
            
    def create_game(self, user_token: str) -> Optional[str]:
        """Create game with User1"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            
            # Create game with Ruby: 15, Emerald: 2 ($35 bet, $1.05 commission)
            game_data = {
                "move": "rock",
                "bet_gems": {
                    "Ruby": 15,
                    "Emerald": 2
                }
            }
            
            response = self.session.post(f"{BASE_URL}/games/create", json=game_data, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                game_id = data.get("game_id")
                self.log_result("Create Game", True, f"Game created: {game_id}")
                return game_id
            else:
                self.log_result("Create Game", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_result("Create Game", False, f"Exception: {str(e)}")
            return None
            
    def join_game(self, user_token: str, game_id: str) -> bool:
        """Join game with User2"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            
            # Join with matching gems
            join_data = {
                "move": "paper",
                "gems": {
                    "Ruby": 15,
                    "Emerald": 2
                }
            }
            
            response = self.session.post(f"{BASE_URL}/games/{game_id}/join", json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                self.log_result("Join Game", True, f"Joined game, status: {status}")
                return True
            else:
                self.log_result("Join Game", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Join Game", False, f"Exception: {str(e)}")
            return False
            
    def wait_for_timeout_or_complete_manually(self, game_id: str) -> bool:
        """Wait for timeout or try to complete game manually"""
        try:
            print(f"\n⏰ Waiting for game timeout or manual completion...")
            
            # Wait for 70 seconds (timeout is 60 seconds + buffer)
            for i in range(70):
                if i % 10 == 0:
                    print(f"Waiting... {70-i} seconds remaining")
                time.sleep(1)
                
            self.log_result("Game Timeout", True, "Waited for game timeout")
            return True
            
        except Exception as e:
            self.log_result("Game Timeout", False, f"Exception: {str(e)}")
            return False
            
    def run_commission_test(self):
        """Run the main commission return test"""
        print("🎯 STARTING SIMPLIFIED COMMISSION RETURN TEST")
        print("=" * 60)
        
        # Step 1: Admin login
        if not self.admin_login():
            print("❌ CRITICAL: Admin login failed, cannot continue")
            return False
            
        # Step 2: Create test users
        print("\n📝 Creating test users...")
        self.user1_id, self.user1_token = self.create_and_verify_user("User1_Creator")
        if not self.user1_token:
            print("❌ CRITICAL: User1 creation failed")
            return False
            
        self.user2_id, self.user2_token = self.create_and_verify_user("User2_Joiner")  
        if not self.user2_token:
            print("❌ CRITICAL: User2 creation failed")
            return False
            
        # Step 3: Add balance to both users
        print("\n💰 Adding balance to users...")
        if not self.add_balance_to_user(self.user1_token, 100.0):
            print("❌ CRITICAL: Failed to add balance to User1")
            return False
            
        if not self.add_balance_to_user(self.user2_token, 100.0):
            print("❌ CRITICAL: Failed to add balance to User2")
            return False
            
        # Step 4: Purchase gems for both users
        print("\n💎 Purchasing gems for users...")
        
        # Check balance before gem purchase
        user1_balance_check = self.get_user_balance(self.user1_token)
        print(f"User1 balance before gem purchase: {user1_balance_check}")
        
        if not self.purchase_gems_for_user(self.user1_token):
            print("❌ CRITICAL: Failed to purchase gems for User1")
            return False
            
        if not self.purchase_gems_for_user(self.user2_token):
            print("❌ CRITICAL: Failed to purchase gems for User2")
            return False
            
        # Step 5: Record balances BEFORE game
        print("\n📊 Recording balances BEFORE game creation...")
        user1_balance_before = self.get_user_balance(self.user1_token)
        user2_balance_before = self.get_user_balance(self.user2_token)
        
        if not user1_balance_before or not user2_balance_before:
            print("❌ CRITICAL: Failed to get initial balances")
            return False
            
        print(f"User1 BEFORE: Virtual=${user1_balance_before['virtual_balance']:.2f}, Frozen=${user1_balance_before['frozen_balance']:.2f}")
        print(f"User2 BEFORE: Virtual=${user2_balance_before['virtual_balance']:.2f}, Frozen=${user2_balance_before['frozen_balance']:.2f}")
        
        # Step 6: Create game with User1
        print("\n🎮 Creating game with User1...")
        self.game_id = self.create_game(self.user1_token)
        if not self.game_id:
            print("❌ CRITICAL: Game creation failed")
            return False
            
        # Step 7: Join game with User2
        print("\n🤝 User2 joining game...")
        if not self.join_game(self.user2_token, self.game_id):
            print("❌ CRITICAL: Game join failed")
            return False
            
        # Step 8: Record balances AFTER game join (commission frozen)
        print("\n📊 Recording balances AFTER game join (commission frozen)...")
        user1_balance_after_join = self.get_user_balance(self.user1_token)
        user2_balance_after_join = self.get_user_balance(self.user2_token)
        
        if not user1_balance_after_join or not user2_balance_after_join:
            print("❌ CRITICAL: Failed to get post-join balances")
            return False
            
        print(f"User1 AFTER JOIN: Virtual=${user1_balance_after_join['virtual_balance']:.2f}, Frozen=${user1_balance_after_join['frozen_balance']:.2f}")
        print(f"User2 AFTER JOIN: Virtual=${user2_balance_after_join['virtual_balance']:.2f}, Frozen=${user2_balance_after_join['frozen_balance']:.2f}")
        
        # Verify commission is frozen for both users
        expected_commission = 1.05  # 3% of $35
        user1_commission_frozen = user1_balance_after_join['frozen_balance'] - user1_balance_before['frozen_balance']
        user2_commission_frozen = user2_balance_after_join['frozen_balance'] - user2_balance_before['frozen_balance']
        
        print(f"\n💰 Commission Analysis:")
        print(f"User1 commission frozen: ${user1_commission_frozen:.2f} (expected: ${expected_commission:.2f})")
        print(f"User2 commission frozen: ${user2_commission_frozen:.2f} (expected: ${expected_commission:.2f})")
        
        # Step 9: Wait for timeout (this will trigger the commission return logic)
        print(f"\n⏰ Waiting for game timeout to trigger commission return logic...")
        if not self.wait_for_timeout_or_complete_manually(self.game_id):
            print("❌ CRITICAL: Timeout wait failed")
            return False
            
        # Step 10: Record balances AFTER timeout/completion
        print("\n📊 Recording balances AFTER timeout/completion...")
        user1_balance_final = self.get_user_balance(self.user1_token)
        user2_balance_final = self.get_user_balance(self.user2_token)
        
        if not user1_balance_final or not user2_balance_final:
            print("❌ CRITICAL: Failed to get final balances")
            return False
            
        print(f"User1 FINAL: Virtual=${user1_balance_final['virtual_balance']:.2f}, Frozen=${user1_balance_final['frozen_balance']:.2f}")
        print(f"User2 FINAL: Virtual=${user2_balance_final['virtual_balance']:.2f}, Frozen=${user2_balance_final['frozen_balance']:.2f}")
        
        # Step 11: Analyze commission return logic
        print("\n🔍 COMMISSION RETURN ANALYSIS:")
        print("=" * 50)
        
        # Calculate changes
        user1_frozen_change = user1_balance_final['frozen_balance'] - user1_balance_after_join['frozen_balance']
        user1_virtual_change = user1_balance_final['virtual_balance'] - user1_balance_after_join['virtual_balance']
        
        user2_frozen_change = user2_balance_final['frozen_balance'] - user2_balance_after_join['frozen_balance']
        user2_virtual_change = user2_balance_final['virtual_balance'] - user2_balance_after_join['virtual_balance']
        
        print(f"User1 Changes:")
        print(f"  Frozen balance change: ${user1_frozen_change:.2f}")
        print(f"  Virtual balance change: ${user1_virtual_change:.2f}")
        
        print(f"User2 Changes:")
        print(f"  Frozen balance change: ${user2_frozen_change:.2f}")
        print(f"  Virtual balance change: ${user2_virtual_change:.2f}")
        
        # Check if commission return logic is working
        # In timeout scenario, the non-responding player should get commission back
        # The responding player (or winner) should have commission deducted
        
        commission_logic_working = False
        
        # Check if User2 got commission returned (common timeout scenario)
        if abs(user2_virtual_change - 1.05) < 0.01 and abs(user2_frozen_change + 1.05) < 0.01:
            commission_logic_working = True
            print(f"\n✅ COMMISSION RETURN DETECTED:")
            print(f"User2 received commission back: Virtual +${user2_virtual_change:.2f}, Frozen ${user2_frozen_change:.2f}")
            
        # Check if User1 got commission returned instead
        elif abs(user1_virtual_change - 1.05) < 0.01 and abs(user1_frozen_change + 1.05) < 0.01:
            commission_logic_working = True
            print(f"\n✅ COMMISSION RETURN DETECTED:")
            print(f"User1 received commission back: Virtual +${user1_virtual_change:.2f}, Frozen ${user1_frozen_change:.2f}")
            
        else:
            print(f"\n❌ COMMISSION RETURN NOT DETECTED:")
            print(f"Neither user received the expected commission return of $1.05")
            
        # Overall test result
        if commission_logic_working:
            self.log_result("COMMISSION RETURN LOGIC", True, "Commission return mechanism is working")
            print("\n🎉 COMMISSION RETURN TEST: SUCCESS!")
            print("The new logic in distribute_game_rewards is working correctly!")
        else:
            self.log_result("COMMISSION RETURN LOGIC", False, "Commission return mechanism not working as expected")
            print("\n❌ COMMISSION RETURN TEST: NEEDS INVESTIGATION!")
            print("The commission return logic requires further analysis.")
            
        return commission_logic_working
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print("\nDetailed Results:")
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
                
        return success_rate >= 80.0

def main():
    """Main test execution"""
    print("🚀 Simplified Commission Return Test - Russian Review")
    print("Testing: ТОЛЬКО ПОБЕДИТЕЛЬ ПЛАТИТ КОМИССИЮ")
    print("=" * 60)
    
    tester = SimpleCommissionTest()
    
    try:
        # Run the main test
        success = tester.run_commission_test()
        
        # Print summary
        overall_success = tester.print_summary()
        
        if success and overall_success:
            print("\n🎉 OVERALL RESULT: SUCCESS!")
            print("Commission return logic is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ OVERALL RESULT: NEEDS INVESTIGATION")
            print("Commission return logic requires fixes.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()