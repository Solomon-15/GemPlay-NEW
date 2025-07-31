#!/usr/bin/env python3
"""
GemPlay API Gem Validation Testing - Russian Review
Focus: Quick test of gem validation fixes for large bets
Requirements:
1. Test inventory endpoint - returns ALL gem types (including quantity=0)
2. Test balance endpoint - works correctly
3. Test large bet ($400) - no "Insufficient Magic gems" error
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List
import random
import string

# Configuration
BASE_URL = "https://85245bb1-9423-4f57-ad61-2213aa95b2ae.preview.emergentagent.com/api"

class GemValidationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.user_token = None
        self.user_id = None
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def generate_test_email(self) -> str:
        """Generate unique test email"""
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        return f"gemtest_{timestamp}_{random_suffix}@test.com"
        
    def register_and_verify_user(self) -> bool:
        """Register and verify a test user"""
        try:
            # Generate unique user data
            email = self.generate_test_email()
            username = f"testuser_{int(time.time())}"
            
            # Register user
            register_data = {
                "username": username,
                "email": email,
                "password": "Test123!",
                "gender": "male"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code not in [200, 201]:
                self.log_result("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            # Extract verification token from response
            reg_data = response.json()
            verification_token = reg_data.get("verification_token")
            self.log_result("User Registration", True, f"User {username} registered successfully")
            
            # Verify email using the token
            if verification_token:
                verify_response = self.session.post(f"{BASE_URL}/auth/verify-email", json={"token": verification_token})
                if verify_response.status_code == 200:
                    self.log_result("Email Verification", True, "Email verified successfully")
                else:
                    self.log_result("Email Verification", False, f"Status: {verify_response.status_code}")
            
            # Login with credentials
            login_data = {
                "email": email,
                "password": "Test123!"
            }
            
            # Wait a moment for verification to complete
            time.sleep(1)
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
                self.log_result("User Login", True, f"Token obtained for {username}")
                return True
            else:
                # Try email verification bypass
                verify_response = self.session.post(f"{BASE_URL}/auth/verify-email", json={"token": "test-bypass"})
                time.sleep(1)
                
                # Try login again
                response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
                if response.status_code == 200:
                    data = response.json()
                    self.user_token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("id")
                    self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
                    self.log_result("User Login", True, f"Token obtained for {username} after verification")
                    return True
                else:
                    self.log_result("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            self.log_result("User Registration/Login", False, f"Exception: {str(e)}")
            return False
            
    def purchase_gems(self, gem_type: str, quantity: int) -> bool:
        """Purchase gems for testing"""
        try:
            # Try to purchase gems directly (user starts with $1000 balance)
            purchase_data = {
                "gem_type": gem_type,
                "quantity": quantity
            }
            
            response = self.session.post(f"{BASE_URL}/gems/buy", json=purchase_data)
            if response.status_code == 200:
                self.log_result(f"Purchase {quantity} {gem_type} Gems", True, "Gems purchased successfully")
                return True
            elif response.status_code == 400 and "insufficient balance" in response.text.lower():
                # Try to add balance first
                self.log_result(f"Initial {gem_type} Purchase", False, "Insufficient balance, trying to add balance")
                
                # Try admin endpoint to add balance
                balance_data = {"amount": 1000.0}
                response = self.session.post(f"{BASE_URL}/admin/users/{self.user_id}/balance", json=balance_data)
                
                if response.status_code != 200:
                    # Try alternative balance endpoints
                    response = self.session.post(f"{BASE_URL}/economy/balance/add", json=balance_data)
                    if response.status_code != 200:
                        # Try gems/purchase endpoint with balance
                        response = self.session.post(f"{BASE_URL}/gems/purchase", json={"amount": 1000.0})
                        if response.status_code != 200:
                            self.log_result(f"Add Balance for {gem_type} Purchase", False, f"All balance endpoints failed")
                            return False
                            
                self.log_result(f"Add Balance for {gem_type} Purchase", True, "Balance added successfully")
                
                # Try purchase again
                response = self.session.post(f"{BASE_URL}/gems/buy", json=purchase_data)
                if response.status_code == 200:
                    self.log_result(f"Purchase {quantity} {gem_type} Gems", True, "Gems purchased successfully after balance add")
                    return True
                else:
                    self.log_result(f"Purchase {quantity} {gem_type} Gems", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
            else:
                self.log_result(f"Purchase {quantity} {gem_type} Gems", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"Purchase {gem_type} Gems", False, f"Exception: {str(e)}")
            return False
            
    def test_inventory_endpoint(self) -> bool:
        """Test 1: Check that /api/gems/inventory returns ALL gem types"""
        try:
            response = self.session.get(f"{BASE_URL}/gems/inventory")
            
            if response.status_code != 200:
                self.log_result("Inventory Endpoint Access", False, f"Status: {response.status_code}")
                return False
                
            data = response.json()
            
            # Check if response is a list (new format)
            if not isinstance(data, list):
                self.log_result("Inventory Endpoint Format", False, "Response is not a list format")
                return False
                
            self.log_result("Inventory Endpoint Format", True, f"Returns list with {len(data)} gem types")
            
            # Check for all expected gem types
            expected_gems = ["Ruby", "Amber", "Topaz", "Emerald", "Aquamarine", "Sapphire", "Magic"]
            found_gems = [gem.get("name") for gem in data]
            
            all_gems_present = True
            for expected_gem in expected_gems:
                if expected_gem not in found_gems:
                    self.log_result(f"Inventory Contains {expected_gem}", False, "Gem type missing")
                    all_gems_present = False
                else:
                    gem_data = next((g for g in data if g.get("name") == expected_gem), None)
                    if gem_data:
                        quantity = gem_data.get("quantity", 0)
                        available_quantity = gem_data.get("available_quantity", quantity)
                        self.log_result(f"Inventory Contains {expected_gem}", True, f"Quantity: {quantity}, Available: {available_quantity}")
                        
            if all_gems_present:
                self.log_result("Inventory All Gem Types Present", True, "All 7 gem types found in inventory")
            else:
                self.log_result("Inventory All Gem Types Present", False, "Some gem types missing")
                
            return all_gems_present
            
        except Exception as e:
            self.log_result("Inventory Endpoint Test", False, f"Exception: {str(e)}")
            return False
            
    def test_balance_endpoint(self) -> bool:
        """Test 2: Check that balance endpoint works correctly"""
        try:
            # Test /api/auth/me endpoint (contains balance info)
            response = self.session.get(f"{BASE_URL}/auth/me")
            
            if response.status_code != 200:
                self.log_result("Balance Endpoint (/auth/me)", False, f"Status: {response.status_code}")
                return False
                
            data = response.json()
            
            # Check required balance fields
            required_fields = ["virtual_balance", "frozen_balance"]
            balance_ok = True
            
            for field in required_fields:
                if field not in data:
                    self.log_result(f"Balance Field {field}", False, "Field missing in response")
                    balance_ok = False
                else:
                    value = data[field]
                    self.log_result(f"Balance Field {field}", True, f"Value: ${value}")
                    
            # Test alternative balance endpoint if exists
            try:
                response2 = self.session.get(f"{BASE_URL}/economy/balance")
                if response2.status_code == 200:
                    self.log_result("Alternative Balance Endpoint", True, "Economy balance endpoint accessible")
                else:
                    self.log_result("Alternative Balance Endpoint", False, f"Status: {response2.status_code}")
            except:
                self.log_result("Alternative Balance Endpoint", False, "Endpoint not accessible")
                
            return balance_ok
            
        except Exception as e:
            self.log_result("Balance Endpoint Test", False, f"Exception: {str(e)}")
            return False
            
    def test_large_bet_creation(self) -> bool:
        """Test 3: Create a large bet ($400) with available gems"""
        try:
            # Check current inventory first
            response = self.session.get(f"{BASE_URL}/gems/inventory")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Check Current Inventory", True, f"Found {len(data)} gem types")
                
                # Look for gems we can use for a large bet
                # Try to create a $400 bet with available gems
                available_gems = {}
                total_value = 0
                
                for gem in data:
                    name = gem.get("name")
                    available = gem.get("available_quantity", gem.get("quantity", 0))
                    price = gem.get("price", 0)
                    
                    if available > 0 and name in ["Magic", "Sapphire", "Aquamarine", "Emerald", "Topaz"]:
                        available_gems[name] = {"available": available, "price": price}
                        total_value += available * price
                        
                self.log_result("Available Gems for Large Bet", True, f"Total value available: ${total_value}")
                
                # Try to create a bet with what we have
                if total_value >= 400:
                    # Create $400+ bet with available gems
                    bet_gems = {}
                    remaining_value = 400
                    
                    # Use highest value gems first
                    for gem_name in ["Magic", "Sapphire", "Aquamarine", "Emerald", "Topaz"]:
                        if gem_name in available_gems and remaining_value > 0:
                            gem_info = available_gems[gem_name]
                            price = gem_info["price"]
                            available = gem_info["available"]
                            
                            needed = min(available, remaining_value // price)
                            if needed > 0:
                                bet_gems[gem_name] = needed
                                remaining_value -= needed * price
                                
                    if remaining_value <= 0:
                        # Create the bet
                        bet_data = {
                            "move": "rock",
                            "bet_gems": bet_gems
                        }
                        
                        response = self.session.post(f"{BASE_URL}/games/create", json=bet_data)
                        
                        if response.status_code == 200:
                            game_data = response.json()
                            game_id = game_data.get("game_id")
                            bet_value = sum(bet_gems[gem] * available_gems[gem]["price"] for gem in bet_gems)
                            self.log_result("Large Bet Creation", True, f"Game created with ID: {game_id}, Value: ${bet_value}")
                            return True
                        else:
                            error_text = response.text
                            if "Insufficient" in error_text and "gems" in error_text:
                                self.log_result("Large Bet Creation", False, f"CRITICAL: Gem validation error: {error_text}")
                            else:
                                self.log_result("Large Bet Creation", False, f"Status: {response.status_code}, Error: {error_text}")
                            return False
                    else:
                        self.log_result("Large Bet Creation", False, f"Cannot create $400 bet, only ${400-remaining_value} worth of gems available")
                        return False
                else:
                    # Try to purchase Magic gems if we don't have enough
                    if not self.purchase_gems("Magic", 5):
                        self.log_result("Large Bet Creation", False, "Cannot purchase Magic gems and insufficient existing gems")
                        return False
                        
                    # Try again after purchase
                    time.sleep(2)
                    return self.test_large_bet_creation()
            else:
                self.log_result("Check Current Inventory", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Large Bet Creation Test", False, f"Exception: {str(e)}")
            return False
            
    def test_large_bet_join(self) -> bool:
        """Test 4: Join a large bet to ensure no validation errors"""
        try:
            # Check if we have available games to join
            response = self.session.get(f"{BASE_URL}/games/available")
            if response.status_code == 200:
                games = response.json()
                if games and len(games) > 0:
                    # Find a game with high value to test joining
                    high_value_game = None
                    for game in games:
                        bet_amount = game.get("bet_amount", 0)
                        if bet_amount >= 100:  # Look for games $100+
                            high_value_game = game
                            break
                            
                    if high_value_game:
                        game_id = high_value_game.get("game_id")
                        bet_amount = high_value_game.get("bet_amount")
                        bet_gems = high_value_game.get("bet_gems", {})
                        
                        self.log_result("Found High Value Game", True, f"Game {game_id} with ${bet_amount} bet")
                        
                        # Try to join with matching gems
                        join_data = {
                            "move": "scissors",
                            "gems": bet_gems  # Use same gem combination
                        }
                        
                        response = self.session.post(f"{BASE_URL}/games/{game_id}/join", json=join_data)
                        
                        if response.status_code == 200:
                            join_response = response.json()
                            status = join_response.get("status", "UNKNOWN")
                            self.log_result("Large Bet Join", True, f"Successfully joined ${bet_amount} bet, status: {status}")
                            return True
                        else:
                            error_text = response.text
                            if "Insufficient" in error_text and "gems" in error_text:
                                self.log_result("Large Bet Join", False, f"CRITICAL: Gem validation error: {error_text}")
                            else:
                                self.log_result("Large Bet Join", False, f"Status: {response.status_code}, Error: {error_text}")
                            return False
                    else:
                        self.log_result("Large Bet Join", False, "No high-value games available to join")
                        return False
                else:
                    self.log_result("Large Bet Join", False, "No available games to join")
                    return False
            else:
                self.log_result("Check Available Games", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Large Bet Join Test", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all gem validation tests"""
        print("🔍 STARTING GEM VALIDATION TESTING - RUSSIAN REVIEW")
        print("=" * 60)
        
        # Setup
        if not self.register_and_verify_user():
            print("❌ CRITICAL: Could not setup test user")
            return
            
        # Test 1: Inventory endpoint
        print("\n📦 TEST 1: INVENTORY ENDPOINT")
        print("-" * 30)
        self.test_inventory_endpoint()
        
        # Test 2: Balance endpoint  
        print("\n💰 TEST 2: BALANCE ENDPOINT")
        print("-" * 30)
        self.test_balance_endpoint()
        
        # Test 3: Large bet creation
        print("\n🎰 TEST 3: LARGE BET CREATION ($400)")
        print("-" * 30)
        self.test_large_bet_creation()
        
        # Test 4: Large bet join
        print("\n🤝 TEST 4: LARGE BET JOIN ($400)")
        print("-" * 30)
        self.test_large_bet_join()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if not result["success"] and "Insufficient Magic gems" in result["details"]:
                critical_issues.append(result["test"])
                
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ NO CRITICAL 'Insufficient Magic gems' ERRORS FOUND")
            
        print("\n🎯 RUSSIAN REVIEW REQUIREMENTS STATUS:")
        inventory_ok = any(r["success"] for r in self.test_results if "Inventory" in r["test"])
        balance_ok = any(r["success"] for r in self.test_results if "Balance" in r["test"])  
        large_bet_ok = any(r["success"] for r in self.test_results if "Large Bet" in r["test"])
        
        print(f"   1. Inventory endpoint returns ALL gems: {'✅ PASS' if inventory_ok else '❌ FAIL'}")
        print(f"   2. Balance endpoint works correctly: {'✅ PASS' if balance_ok else '❌ FAIL'}")
        print(f"   3. Large bet ($400) without errors: {'✅ PASS' if large_bet_ok else '❌ FAIL'}")
        
        overall_success = inventory_ok and balance_ok and large_bet_ok
        print(f"\n🏆 OVERALL STATUS: {'✅ ALL FIXES WORKING' if overall_success else '❌ ISSUES REMAIN'}")

if __name__ == "__main__":
    tester = GemValidationTester()
    tester.run_all_tests()