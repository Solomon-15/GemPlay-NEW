#!/usr/bin/env python3
"""
BACK Button Blocking Test - Russian Review
Протестировать блокировку кнопки BACK после присоединения к активной игре

КОНТЕКСТ ИСПРАВЛЕНИЯ:
- Добавлена блокировка возможности вернуться назад (кнопка BACK) после успешного присоединения к игре
- При попытке нажать BACK теперь показывается сообщение "You cannot change gem combination now"
- Исправление в функции goToPrevStep в JoinBattleModal.js

ЗАДАЧА ТЕСТИРОВАНИЯ:
1. Протестировать полный игровой flow для подтверждения что backend logic работает корректно
2. Убедиться что API endpoints работают корректно
3. Проверить правильность обработки гемов и комиссий после присоединения

КРИТЕРИИ УСПЕХА:
- API endpoint /games/{id}/join корректно возвращает статус ACTIVE
- Игра корректно переходит из WAITING в ACTIVE состояние
- Гемы и комиссия правильно резервируются
- Все API endpoints работают без ошибок
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
BASE_URL = "https://a20aa5a2-a31c-4c8d-a1c4-18cc39118b00.preview.emergentagent.com/api"

class BackButtonBlockingTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.player_a_token = None
        self.player_b_token = None
        self.player_a_id = None
        self.player_b_id = None
        self.game_id = None
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result with details"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()

    def generate_test_user_data(self, suffix: str) -> Dict[str, str]:
        """Generate unique test user data"""
        timestamp = int(time.time())
        return {
            "username": f"testuser_{suffix}_{timestamp}",
            "email": f"testuser_{suffix}_{timestamp}@test.com",
            "password": "Test123!",
            "gender": "male"
        }

    def register_and_verify_user(self, user_data: Dict[str, str]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Register user and return success status, token, and user_id"""
        try:
            # Register user
            print(f"   Registering user: {user_data['email']}")
            register_response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            print(f"   Registration response status: {register_response.status_code}")
            
            if register_response.status_code not in [200, 201]:
                print(f"   Registration failed: {register_response.text}")
                return False, None, None
            
            register_data = register_response.json()
            verification_token = register_data.get("verification_token")
            print(f"   Got verification token: {verification_token}")
            
            if not verification_token:
                print("   No verification token received")
                return False, None, None
            
            # Verify email
            print("   Verifying email...")
            verify_response = self.session.post(
                f"{BASE_URL}/auth/verify-email",
                json={"token": verification_token}
            )
            print(f"   Verification response status: {verify_response.status_code}")
            
            if verify_response.status_code != 200:
                print(f"   Email verification failed: {verify_response.text}")
                return False, None, None
            
            # Login user
            print("   Logging in user...")
            login_response = self.session.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
            )
            print(f"   Login response status: {login_response.status_code}")
            
            if login_response.status_code != 200:
                print(f"   Login failed: {login_response.text}")
                return False, None, None
            
            login_data = login_response.json()
            token = login_data.get("access_token")
            user_id = login_data.get("user", {}).get("id")
            print(f"   Login successful, got token and user_id: {user_id}")
            
            return True, token, user_id
            
        except Exception as e:
            print(f"Error in register_and_verify_user: {e}")
            return False, None, None

    def purchase_gems(self, token: str, gem_type: str, quantity: int) -> bool:
        """Purchase gems for user"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.post(
                f"{BASE_URL}/gems/buy?gem_type={gem_type}&quantity={quantity}",
                headers=headers
            )
            print(f"   Gem purchase response for {quantity} {gem_type}: {response.status_code}")
            if response.status_code not in [200, 201]:
                print(f"   Gem purchase failed: {response.text}")
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error purchasing gems: {e}")
            return False

    def get_user_balance(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user balance information"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{BASE_URL}/economy/balance", headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting user balance: {e}")
            return None

    def create_game(self, token: str, bet_gems: Dict[str, int]) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Create a game and return success status, game_id, and response data"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            game_data = {
                "move": "rock",  # Player A's move
                "bet_gems": bet_gems
            }
            
            response = self.session.post(
                f"{BASE_URL}/games/create",
                json=game_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                game_id = response_data.get("game_id")
                return True, game_id, response_data
            else:
                return False, None, response.json() if response.content else None
                
        except Exception as e:
            print(f"Error creating game: {e}")
            return False, None, None

    def join_game(self, token: str, game_id: str, gems: Dict[str, int]) -> Tuple[bool, Optional[Dict]]:
        """Join a game and return success status and response data"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            join_data = {
                "move": "paper",  # Player B's move
                "gems": gems
            }
            
            print(f"   Joining game {game_id} with gems: {gems}")
            response = self.session.post(
                f"{BASE_URL}/games/{game_id}/join",
                json=join_data,
                headers=headers
            )
            
            print(f"   Join response status: {response.status_code}")
            print(f"   Join response content: {response.text}")
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.json() if response.content else None
                
        except Exception as e:
            print(f"Error joining game: {e}")
            return False, None

    def get_available_games(self, token: str) -> Tuple[bool, Optional[List]]:
        """Get available games"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{BASE_URL}/games/available", headers=headers)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, None
                
        except Exception as e:
            print(f"Error getting available games: {e}")
            return False, None

    def test_setup_users(self):
        """Test 1: Setup Player A and Player B"""
        print("🔧 SETTING UP TEST USERS...")
        
        # Setup Player A
        player_a_data = self.generate_test_user_data("playerA")
        success_a, token_a, user_id_a = self.register_and_verify_user(player_a_data)
        
        if not success_a:
            self.log_result("Setup Player A", False, "Failed to register and verify Player A")
            return False
        
        self.player_a_token = token_a
        self.player_a_id = user_id_a
        
        # Setup Player B
        player_b_data = self.generate_test_user_data("playerB")
        success_b, token_b, user_id_b = self.register_and_verify_user(player_b_data)
        
        if not success_b:
            self.log_result("Setup Player B", False, "Failed to register and verify Player B")
            return False
        
        self.player_b_token = token_b
        self.player_b_id = user_id_b
        
        # Purchase gems for both players
        gem_purchases = [
            (self.player_a_token, "Ruby", 20),
            (self.player_a_token, "Emerald", 5),
            (self.player_b_token, "Ruby", 20),
            (self.player_b_token, "Emerald", 5)
        ]
        
        for token, gem_type, quantity in gem_purchases:
            if not self.purchase_gems(token, gem_type, quantity):
                self.log_result("Setup Gem Purchases", False, f"Failed to purchase {quantity} {gem_type}")
                return False
        
        self.log_result("Setup Users and Gems", True, "Player A and Player B created successfully with gems")
        return True

    def test_game_creation_by_player_a(self):
        """Test 2: Player A creates a game (should be WAITING status)"""
        print("🎮 TESTING GAME CREATION BY PLAYER A...")
        
        bet_gems = {"Ruby": 15, "Emerald": 2}  # $35 total bet
        
        success, game_id, response_data = self.create_game(self.player_a_token, bet_gems)
        
        if not success:
            self.log_result("Player A Game Creation", False, "Failed to create game", response_data)
            return False
        
        self.game_id = game_id
        
        # Verify game creation response
        expected_fields = ["game_id", "message", "commission_reserved"]
        missing_fields = [field for field in expected_fields if field not in response_data]
        
        if missing_fields:
            self.log_result("Player A Game Creation", False, f"Missing fields in response: {missing_fields}", response_data)
            return False
        
        # Check commission calculation (3% of $35 = $1.05)
        expected_commission = 35 * 0.03  # $1.05
        actual_commission = response_data.get("commission_reserved", 0)
        
        if abs(actual_commission - expected_commission) > 0.01:  # Allow small floating point differences
            self.log_result("Player A Game Creation", False, f"Incorrect commission: expected {expected_commission}, got {actual_commission}", response_data)
            return False
        
        self.log_result("Player A Game Creation", True, f"Game created successfully with ID: {game_id}, Commission: ${actual_commission}", response_data)
        return True

    def test_available_games_contains_created_game(self):
        """Test 3: Verify created game appears in available games"""
        print("📋 TESTING AVAILABLE GAMES CONTAINS CREATED GAME...")
        
        success, available_games = self.get_available_games(self.player_b_token)
        
        if not success:
            self.log_result("Available Games Check", False, "Failed to get available games")
            return False
        
        # Find our created game
        our_game = None
        for game in available_games:
            if game.get("game_id") == self.game_id:
                our_game = game
                break
        
        if not our_game:
            self.log_result("Available Games Check", False, f"Created game {self.game_id} not found in available games", available_games)
            return False
        
        # Verify game status is WAITING
        if our_game.get("status") != "WAITING":
            self.log_result("Available Games Check", False, f"Game status should be WAITING, got: {our_game.get('status')}", our_game)
            return False
        
        self.log_result("Available Games Check", True, f"Game found in available games with WAITING status", our_game)
        return True

    def test_player_b_joins_game_active_status(self):
        """Test 4: Player B joins game and receives ACTIVE status (CRITICAL TEST)"""
        print("🔥 TESTING PLAYER B JOINS GAME - CRITICAL ACTIVE STATUS TEST...")
        
        # Get Player B's balance before joining
        balance_before = self.get_user_balance(self.player_b_token)
        
        bet_gems = {"Ruby": 15, "Emerald": 2}  # Matching Player A's bet
        
        success, response_data = self.join_game(self.player_b_token, self.game_id, bet_gems)
        
        if not success:
            self.log_result("Player B Join Game - ACTIVE Status", False, "Failed to join game", response_data)
            return False
        
        # CRITICAL CHECK: Verify status is ACTIVE
        game_status = response_data.get("status")
        if game_status != "ACTIVE":
            self.log_result("Player B Join Game - ACTIVE Status", False, f"Expected status ACTIVE, got: {game_status}", response_data)
            return False
        
        # Verify other required fields in response
        expected_fields = ["status", "message", "deadline", "next_action"]
        missing_fields = [field for field in expected_fields if field not in response_data]
        
        if missing_fields:
            self.log_result("Player B Join Game - ACTIVE Status", False, f"Missing fields in join response: {missing_fields}", response_data)
            return False
        
        # Verify deadline is set (should be ~1 minute from now)
        deadline = response_data.get("deadline")
        if not deadline:
            self.log_result("Player B Join Game - ACTIVE Status", False, "No deadline set in ACTIVE game", response_data)
            return False
        
        # Get Player B's balance after joining to verify commission frozen
        balance_after = self.get_user_balance(self.player_b_token)
        
        if balance_before and balance_after:
            frozen_before = balance_before.get("frozen_balance", 0)
            frozen_after = balance_after.get("frozen_balance", 0)
            commission_frozen = frozen_after - frozen_before
            
            expected_commission = 35 * 0.03  # $1.05
            if abs(commission_frozen - expected_commission) > 0.01:
                self.log_result("Player B Join Game - ACTIVE Status", False, f"Incorrect commission frozen: expected {expected_commission}, got {commission_frozen}")
                return False
        
        self.log_result("Player B Join Game - ACTIVE Status", True, f"✅ CRITICAL SUCCESS: Game status is ACTIVE, deadline set, commission frozen correctly", response_data)
        return True

    def test_game_removed_from_available_after_join(self):
        """Test 5: Verify game is removed from available games after join"""
        print("🔍 TESTING GAME REMOVED FROM AVAILABLE GAMES AFTER JOIN...")
        
        success, available_games = self.get_available_games(self.player_a_token)
        
        if not success:
            self.log_result("Game Removal from Available", False, "Failed to get available games after join")
            return False
        
        # Verify our game is NOT in available games anymore
        our_game = None
        for game in available_games:
            if game.get("game_id") == self.game_id:
                our_game = game
                break
        
        if our_game:
            self.log_result("Game Removal from Available", False, f"Game {self.game_id} still appears in available games after join", our_game)
            return False
        
        self.log_result("Game Removal from Available", True, f"Game correctly removed from available games after join (found {len(available_games)} available games)")
        return True

    def test_commission_and_gems_handling(self):
        """Test 6: Verify commission and gems are properly handled"""
        print("💰 TESTING COMMISSION AND GEMS HANDLING...")
        
        # Get both players' balances
        balance_a = self.get_user_balance(self.player_a_token)
        balance_b = self.get_user_balance(self.player_b_token)
        
        if not balance_a or not balance_b:
            self.log_result("Commission and Gems Handling", False, "Failed to get player balances")
            return False
        
        # Both players should have commission frozen (3% of $35 = $1.05 each)
        expected_commission = 35 * 0.03
        
        frozen_a = balance_a.get("frozen_balance", 0)
        frozen_b = balance_b.get("frozen_balance", 0)
        
        commission_errors = []
        if abs(frozen_a - expected_commission) > 0.01:
            commission_errors.append(f"Player A frozen balance incorrect: expected {expected_commission}, got {frozen_a}")
        
        if abs(frozen_b - expected_commission) > 0.01:
            commission_errors.append(f"Player B frozen balance incorrect: expected {expected_commission}, got {frozen_b}")
        
        if commission_errors:
            self.log_result("Commission and Gems Handling", False, "; ".join(commission_errors), {"balance_a": balance_a, "balance_b": balance_b})
            return False
        
        self.log_result("Commission and Gems Handling", True, f"Commission correctly frozen for both players: ${expected_commission} each", {"balance_a": balance_a, "balance_b": balance_b})
        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 STARTING BACK BUTTON BLOCKING BACKEND TESTS")
        print("=" * 60)
        
        tests = [
            self.test_setup_users,
            self.test_game_creation_by_player_a,
            self.test_available_games_contains_created_game,
            self.test_player_b_joins_game_active_status,  # CRITICAL TEST
            self.test_game_removed_from_available_after_join,
            self.test_commission_and_gems_handling
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
                else:
                    # If a critical test fails, we might want to continue to see other results
                    pass
            except Exception as e:
                print(f"❌ EXCEPTION in {test.__name__}: {e}")
                self.log_result(test.__name__, False, f"Exception: {e}")
        
        print("=" * 60)
        print("🏁 BACK BUTTON BLOCKING BACKEND TEST RESULTS")
        print(f"✅ Passed: {passed_tests}/{total_tests} tests")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests} tests")
        
        # Summary of critical findings
        print("\n🔥 CRITICAL FINDINGS:")
        critical_tests = [result for result in self.test_results if "ACTIVE Status" in result["test"]]
        for test in critical_tests:
            status = "✅ PASS" if test["success"] else "❌ FAIL"
            print(f"{status} {test['test']}: {test['details']}")
        
        print("\n📊 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        # Return success rate
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n🎯 SUCCESS RATE: {success_rate:.1f}%")
        
        return success_rate >= 80  # Consider 80%+ as overall success

if __name__ == "__main__":
    tester = BackButtonBlockingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 BACKEND TESTS PASSED: Ready for frontend BACK button blocking!")
        sys.exit(0)
    else:
        print("\n⚠️  BACKEND TESTS FAILED: Backend issues need to be resolved first!")
        sys.exit(1)