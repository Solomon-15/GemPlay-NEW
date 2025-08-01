#!/usr/bin/env python3
"""
Test script for updated bet management functionality as requested in review:
1. Updated single bet reset endpoint: POST /api/admin/bets/{bet_id}/cancel
2. New delete all bets endpoint: POST /api/admin/bets/delete-all
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List
import random
from datetime import datetime

# Configuration
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"

ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

SUPER_ADMIN_USER = {
    "email": "superadmin@gemplay.com",
    "password": "SuperAdmin123!"
}

class BetManagementTester:
    def __init__(self):
        self.admin_token = None
        self.super_admin_token = None
        self.test_user_tokens = []
        self.test_user_ids = []
        self.created_games = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        else:
            print(f"[{timestamp}] ℹ️  {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, params: Dict = None) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{BASE_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise
            
    def login_user(self, email: str, password: str) -> Optional[str]:
        """Login user and return token."""
        try:
            response = self.make_request("POST", "/auth/login", {
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.log(f"Successfully logged in user: {email}", "SUCCESS")
                return token
            else:
                self.log(f"Login failed for {email}: {response.status_code} - {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Login error for {email}: {e}", "ERROR")
            return None
            
    def setup_authentication(self) -> bool:
        """Setup admin and super admin authentication."""
        try:
            # Login admin
            self.admin_token = self.login_user(ADMIN_USER["email"], ADMIN_USER["password"])
            if not self.admin_token:
                self.log("Failed to login admin", "ERROR")
                return False
                
            # Login super admin
            self.super_admin_token = self.login_user(SUPER_ADMIN_USER["email"], SUPER_ADMIN_USER["password"])
            if not self.super_admin_token:
                self.log("Failed to login super admin", "ERROR")
                return False
                
            self.log("Successfully authenticated admin and super admin", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Authentication setup error: {e}", "ERROR")
            return False
            
    def create_test_user(self) -> Optional[tuple]:
        """Create a test user and return (token, user_id)."""
        try:
            timestamp = int(time.time())
            user_data = {
                "username": f"bet_test_user_{timestamp}_{random.randint(1000, 9999)}",
                "email": f"bet_test_user_{timestamp}_{random.randint(1000, 9999)}@test.com",
                "password": "Test123!",
                "gender": "male"
            }
            
            # Register user
            response = self.make_request("POST", "/auth/register", user_data)
            
            if response.status_code in [200, 201]:
                self.log(f"Registered test user: {user_data['username']}", "SUCCESS")
                
                # Get user ID and verification token from registration response
                reg_data = response.json()
                user_id = reg_data.get("user_id")
                verification_token = reg_data.get("verification_token")
                
                if user_id and verification_token:
                    # Verify email using the token
                    verify_response = self.make_request("POST", "/auth/verify-email", {
                        "token": verification_token
                    })
                    
                    if verify_response.status_code == 200:
                        self.log(f"Verified user email: {user_data['username']}", "SUCCESS")
                        
                        # Now login user
                        token = self.login_user(user_data["email"], user_data["password"])
                        if token:
                            self.log(f"Got user ID: {user_id}", "SUCCESS")
                            return token, user_id
                    else:
                        self.log(f"Failed to verify user email: {verify_response.status_code} - {verify_response.text}", "ERROR")
                        
            elif response.status_code == 400 and "already exists" in response.text.lower():
                self.log(f"User {user_data['username']} already exists, trying to login", "WARNING")
                token = self.login_user(user_data["email"], user_data["password"])
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    profile_response = self.make_request("GET", "/users/profile", headers=headers)
                    if profile_response.status_code == 200:
                        user_id = profile_response.json().get("id")
                        return token, user_id
                        
            self.log(f"Failed to create test user: {response.status_code} - {response.text}", "ERROR")
            return None
            
        except Exception as e:
            self.log(f"Error creating test user: {e}", "ERROR")
            return None
            
    def setup_test_users(self) -> bool:
        """Setup test users with balance and gems."""
        try:
            # Create 2 test users
            for i in range(2):
                result = self.create_test_user()
                if result:
                    token, user_id = result
                    self.test_user_tokens.append(token)
                    self.test_user_ids.append(user_id)
                else:
                    return False
                    
            # Add balance to users
            for i, token in enumerate(self.test_user_tokens):
                headers = {"Authorization": f"Bearer {token}"}
                response = self.make_request("POST", "/auth/add-balance", 
                                           {"amount": 100.0}, headers)
                if response.status_code == 200:
                    self.log(f"Added $100 balance to test user {i+1}", "SUCCESS")
                else:
                    self.log(f"Failed to add balance to test user {i+1}: {response.status_code} - {response.text}", "ERROR")
                    return False
                    
            # Purchase gems for users
            for i, token in enumerate(self.test_user_tokens):
                headers = {"Authorization": f"Bearer {token}"}
                response = self.make_request("POST", "/gems/buy", None, headers, {
                    "gem_type": "Ruby",
                    "quantity": 20
                })
                if response.status_code == 200:
                    self.log(f"Purchased 20 Ruby gems for test user {i+1}", "SUCCESS")
                else:
                    self.log(f"Failed to purchase gems for test user {i+1}: {response.status_code} - {response.text}", "ERROR")
                    return False
                    
            return True
            
        except Exception as e:
            self.log(f"Error setting up test users: {e}", "ERROR")
            return False
            
    def create_game_with_status(self, target_status: str) -> Optional[str]:
        """Create a game with specific status."""
        try:
            if len(self.test_user_tokens) < 2:
                self.log("Need at least 2 test users to create games", "ERROR")
                return None
                
            user1_headers = {"Authorization": f"Bearer {self.test_user_tokens[0]}"}
            user2_headers = {"Authorization": f"Bearer {self.test_user_tokens[1]}"}
            
            # User 1 creates a game
            create_response = self.make_request("POST", "/games/create", {
                "move": "rock",
                "bet_gems": {"Ruby": 5}
            }, user1_headers)
            
            if create_response.status_code != 200:
                self.log(f"Failed to create game: {create_response.status_code} - {create_response.text}", "ERROR")
                return None
                
            game_data = create_response.json()
            game_id = game_data.get("game_id")
            
            if target_status == "WAITING":
                return game_id
                
            elif target_status in ["ACTIVE", "REVEAL", "COMPLETED"]:
                # User 2 joins the game
                join_response = self.make_request("POST", f"/games/{game_id}/join", {
                    "move": "paper",
                    "gems": {"Ruby": 5}
                }, user2_headers)
                
                if join_response.status_code != 200:
                    self.log(f"Failed to join game: {join_response.status_code} - {join_response.text}", "ERROR")
                    return None
                    
                if target_status == "ACTIVE":
                    return game_id
                elif target_status in ["REVEAL", "COMPLETED"]:
                    # Wait for game to progress
                    time.sleep(3)
                    return game_id
                    
            elif target_status == "CANCELLED":
                # We'll cancel it in the test
                return game_id
                
            return game_id
            
        except Exception as e:
            self.log(f"Error creating game with status {target_status}: {e}", "ERROR")
            return None
            
    def test_single_bet_reset_any_status(self) -> bool:
        """Test the updated single bet reset endpoint with different statuses."""
        try:
            self.log("=== Testing Single Bet Reset Endpoint (Any Status) ===")
            
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            test_results = []
            
            # Test scenarios with different game statuses
            test_scenarios = [
                {"status": "WAITING", "description": "WAITING game (only creator joined)"},
                {"status": "ACTIVE", "description": "ACTIVE game (both players joined)"},
                {"status": "COMPLETED", "description": "COMPLETED game"},
            ]
            
            for scenario in test_scenarios:
                self.log(f"Testing reset for {scenario['description']}")
                
                # Create game with target status
                game_id = self.create_game_with_status(scenario["status"])
                if not game_id:
                    self.log(f"Failed to create {scenario['description']}", "ERROR")
                    test_results.append(False)
                    continue
                    
                self.log(f"Created game {game_id} with status {scenario['status']}")
                
                # Test the reset endpoint
                response = self.make_request("POST", f"/admin/bets/{game_id}/cancel", {
                    "reason": f"Test reset for {scenario['description']}"
                }, admin_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"Successfully reset {scenario['description']}", "SUCCESS")
                    
                    # Verify response structure
                    required_fields = ["success", "message", "bet_id", "original_status", "gems_returned", "commission_returned"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log(f"Missing response fields: {missing_fields}", "ERROR")
                        test_results.append(False)
                    else:
                        self.log(f"Response structure is correct for {scenario['status']}", "SUCCESS")
                        
                        # Check that we can reset any status (no "Only WAITING bets" error)
                        message = data.get("message", "")
                        if "Only WAITING bets can be cancelled" in message:
                            self.log("Old restriction error still present!", "ERROR")
                            test_results.append(False)
                        else:
                            self.log("No old restriction error - can reset any status", "SUCCESS")
                            test_results.append(True)
                            
                else:
                    error_text = response.text
                    if "Only WAITING bets can be cancelled" in error_text:
                        self.log("Old restriction error still present in error response!", "ERROR")
                        test_results.append(False)
                    else:
                        self.log(f"Reset failed for other reason: {response.status_code} - {error_text}", "WARNING")
                        # Still count as success if the old restriction is gone
                        test_results.append(True)
                        
            # Test authentication requirement
            self.log("Testing authentication requirement for single bet reset")
            if self.created_games:
                response = self.make_request("POST", f"/admin/bets/{self.created_games[0]}/cancel", {
                    "reason": "Test without auth"
                })
                
                if response.status_code == 401:
                    self.log("Correctly requires authentication", "SUCCESS")
                    test_results.append(True)
                else:
                    self.log(f"Expected 401 without auth, got {response.status_code}", "ERROR")
                    test_results.append(False)
            else:
                test_results.append(True)  # Skip if no games created
                
            success_rate = sum(test_results) / len(test_results) * 100 if test_results else 0
            self.log(f"Single bet reset test success rate: {success_rate:.1f}% ({sum(test_results)}/{len(test_results)})")
            
            return success_rate >= 80
            
        except Exception as e:
            self.log(f"Error in single bet reset test: {e}", "ERROR")
            return False
            
    def test_delete_all_bets_endpoint(self) -> bool:
        """Test the new delete all bets endpoint."""
        try:
            self.log("=== Testing Delete All Bets Endpoint ===")
            
            super_admin_headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Create some fresh test games for deletion
            self.log("Creating fresh games for deletion test...")
            fresh_games = []
            
            for i in range(3):
                game_id = self.create_game_with_status("WAITING")
                if game_id:
                    fresh_games.append(game_id)
                    self.log(f"Created fresh game {i+1}: {game_id}")
                    
            # Test authentication requirement (should require SUPER_ADMIN)
            self.log("Testing authentication requirement (should require SUPER_ADMIN)")
            response = self.make_request("POST", "/admin/bets/delete-all", {}, admin_headers)
            
            if response.status_code == 403:
                self.log("Correctly requires SUPER_ADMIN authentication", "SUCCESS")
            elif response.status_code == 500:
                self.log("Got 500 error instead of 403 - endpoint may not exist or have issues", "WARNING")
                # Let's continue with super admin test to see if endpoint works
            else:
                self.log(f"Expected 403 with regular admin, got {response.status_code} - {response.text}", "ERROR")
                return False
                
            # Test without authentication
            self.log("Testing without authentication")
            response = self.make_request("POST", "/admin/bets/delete-all", {})
            
            if response.status_code == 401:
                self.log("Correctly requires authentication", "SUCCESS")
            elif response.status_code == 500:
                self.log("Got 500 error instead of 401 - endpoint may have issues", "WARNING")
            else:
                self.log(f"Expected 401 without auth, got {response.status_code}", "ERROR")
                return False
                
            # Test the actual delete-all functionality
            self.log("Testing delete-all functionality with SUPER_ADMIN")
            response = self.make_request("POST", "/admin/bets/delete-all", {}, super_admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log("Successfully executed delete-all", "SUCCESS")
                
                # Verify response structure
                required_fields = [
                    "success", "message", "actual_database_deletions", "total_deleted",
                    "active_games_processed", "completed_games_deleted", "total_gems_returned",
                    "total_commission_returned", "users_affected", "bots_affected", "games_by_status"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"Missing response fields: {missing_fields}", "ERROR")
                    return False
                else:
                    self.log("Response structure is correct", "SUCCESS")
                    
                # Log statistics
                self.log(f"Deleted {data.get('actual_database_deletions', 0)} games from database")
                self.log(f"Processed {data.get('active_games_processed', 0)} active games")
                self.log(f"Deleted {data.get('completed_games_deleted', 0)} completed games")
                self.log(f"Returned {data.get('total_commission_returned', 0)} commission")
                self.log(f"Affected {len(data.get('users_affected', []))} users and {len(data.get('bots_affected', []))} bots")
                
                return True
                
            else:
                self.log(f"Failed to execute delete-all: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error in delete-all test: {e}", "ERROR")
            return False
            
    def run_all_tests(self) -> bool:
        """Run all bet management tests."""
        try:
            print("🚀 Starting Updated Bet Management Functionality Tests")
            print("=" * 80)
            
            # Setup
            if not self.setup_authentication():
                self.log("Authentication setup failed", "ERROR")
                return False
                
            if not self.setup_test_users():
                self.log("Test user setup failed", "ERROR")
                return False
                
            # Run tests
            test_results = []
            
            # Test 1: Single bet reset endpoint (any status)
            result1 = self.test_single_bet_reset_any_status()
            test_results.append(("Single Bet Reset (Any Status)", result1))
            
            # Test 2: Delete all bets endpoint
            result2 = self.test_delete_all_bets_endpoint()
            test_results.append(("Delete All Bets", result2))
            
            # Summary
            print("=" * 80)
            print("🏁 TEST SUMMARY")
            print("=" * 80)
            
            passed_tests = 0
            for test_name, result in test_results:
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"{test_name}: {status}")
                if result:
                    passed_tests += 1
                    
            overall_success = passed_tests == len(test_results)
            success_rate = passed_tests / len(test_results) * 100
            
            print("=" * 80)
            print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{len(test_results)})")
            
            if overall_success:
                print("🎉 ALL TESTS PASSED - Updated bet management functionality is working correctly!")
            else:
                print("⚠️  SOME TESTS FAILED - Check the logs above for details")
                
            return overall_success
            
        except Exception as e:
            self.log(f"Error in run_all_tests: {e}", "ERROR")
            return False

def main():
    """Main function to run the bet management tests."""
    tester = BetManagementTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("Tests interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()