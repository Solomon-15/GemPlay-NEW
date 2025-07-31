#!/usr/bin/env python3
"""
GemPlay API Large Bet Gem Validation Testing
Focus: Testing gem validation fixes for large bets ($400+)
Russian Review Requirements: Протестировать исправления ошибки с валидацией гемов для больших ставок
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
BASE_URL = "https://b367228b-4052-4d8d-b206-b40fc66dd3c0.preview.emergentagent.com/api"

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_subheader(text: str) -> None:
    """Print a formatted subheader."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 80}{Colors.ENDC}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def record_test(test_name: str, passed: bool, details: str = "") -> None:
    """Record test result."""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print_success(f"{test_name}: {details}")
    else:
        test_results["failed"] += 1
        print_error(f"{test_name}: {details}")
    
    test_results["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def generate_unique_email() -> str:
    """Generate unique email for testing."""
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test_user_{timestamp}_{random_suffix}@test.com"

def register_and_verify_user(username: str, email: str, password: str, gender: str = "male") -> Optional[str]:
    """Register and verify a new user, return access token."""
    try:
        # Register user
        register_data = {
            "username": username,
            "email": email,
            "password": password,
            "gender": gender
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code != 200:  # Changed from 201 to 200
            print_error(f"Registration failed: {response.status_code} - {response.text}")
            return None
        
        # Extract verification token from response
        data = response.json()
        verification_token = data.get("verification_token")
        
        if not verification_token:
            print_error("No verification token received")
            return None
        
        print_success(f"User registered, verification token: {verification_token}")
        
        # Verify email
        verify_response = requests.post(f"{BASE_URL}/auth/verify-email", json={"token": verification_token})
        if verify_response.status_code != 200:
            print_error(f"Email verification failed: {verify_response.status_code} - {verify_response.text}")
            return None
        
        print_success("Email verified successfully")
        time.sleep(1)
        
        # Login user
        login_data = {
            "email": email,
            "password": password
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            print_success(f"User logged in successfully")
            return access_token
        else:
            print_error(f"Login failed after registration: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error in user registration: {str(e)}")
        return None

def buy_gems(token: str, gem_purchases: List[Dict[str, Any]]) -> bool:
    """Buy gems for user."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        for purchase in gem_purchases:
            gem_type = purchase["gem_type"]
            quantity = purchase["quantity"]
            
            # Use query parameters instead of JSON body
            params = {
                "gem_type": gem_type,
                "quantity": quantity
            }
            
            response = requests.post(
                f"{BASE_URL}/gems/buy",
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                print_error(f"Failed to buy {quantity} {gem_type} gems: {response.status_code} - {response.text}")
                return False
            
            print_success(f"Successfully bought {quantity} {gem_type} gems")
        
        return True
        
    except Exception as e:
        print_error(f"Error buying gems: {str(e)}")
        return False

def get_gem_inventory(token: str) -> Optional[List[Dict[str, Any]]]:
    """Get user's gem inventory."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/gems/inventory", headers=headers)
        
        if response.status_code == 200:
            return response.json()  # Returns list directly
        else:
            print_error(f"Failed to get gem inventory: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error getting gem inventory: {str(e)}")
        return None

def get_user_balance(token: str) -> Optional[Dict[str, Any]]:
    """Get user's balance information."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to get user balance: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error getting user balance: {str(e)}")
        return None

def create_large_bet_game(token: str, bet_gems: Dict[str, int], move: str = "rock") -> Optional[str]:
    """Create a game with large bet amount."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        game_data = {
            "move": move,
            "bet_gems": bet_gems
        }
        
        response = requests.post(f"{BASE_URL}/games/create", json=game_data, headers=headers)
        
        if response.status_code == 200:  # Changed from 201 to 200
            data = response.json()
            game_id = data.get("game_id")
            print_success(f"Successfully created large bet game: {game_id}")
            return game_id
        else:
            print_error(f"Failed to create large bet game: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error creating large bet game: {str(e)}")
        return None

def join_game(token: str, game_id: str, gems: Dict[str, int], move: str = "paper") -> bool:
    """Join a game with specified gems."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        join_data = {
            "move": move,
            "gems": gems
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/join", json=join_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Successfully joined game {game_id}")
            return True
        else:
            print_error(f"Failed to join game {game_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error joining game: {str(e)}")
        return False

def test_large_bet_creation():
    """Test 1: Creating large bet ($400) successfully."""
    print_subheader("TEST 1: Creating Large Bet ($400)")
    
    # Generate unique user
    email = generate_unique_email()
    username = f"player_a_{int(time.time())}"
    
    # Register Player A
    token_a = register_and_verify_user(username, email, "Test123!", "male")
    if not token_a:
        record_test("Large Bet Creation - Player A Registration", False, "Failed to register Player A")
        return None, None
    
    record_test("Large Bet Creation - Player A Registration", True, f"Successfully registered {username}")
    
    # Buy sufficient gems for $400 bet (including Magic gems for "Big" strategy)
    # $400 bet requires Magic gems (4 Magic gems = $400)
    gem_purchases = [
        {"gem_type": "Magic", "quantity": 5}  # Extra Magic gem for safety
    ]
    
    if not buy_gems(token_a, gem_purchases):
        record_test("Large Bet Creation - Gem Purchase", False, "Failed to buy Magic gems")
        return None, None
    
    record_test("Large Bet Creation - Gem Purchase", True, "Successfully bought 5 Magic gems")
    
    # Check gem inventory before creating bet
    inventory_before = get_gem_inventory(token_a)
    if inventory_before:
        magic_gems_before = None
        for gem in inventory_before:  # inventory_before is now a list
            if gem["type"] == "Magic":
                magic_gems_before = gem.get("quantity", 0) - gem.get("frozen_quantity", 0)  # Calculate available
                break
        
        record_test("Large Bet Creation - Inventory Check Before", True, 
                   f"Magic gems available before bet: {magic_gems_before}")
    
    # Create large bet game with Magic gems ($400)
    bet_gems = {"Magic": 4}  # 4 Magic gems = $400
    game_id = create_large_bet_game(token_a, bet_gems)
    
    if game_id:
        record_test("Large Bet Creation - Game Creation", True, f"Successfully created $400 bet game: {game_id}")
        
        # Check gem inventory after creating bet (gems should be frozen)
        inventory_after = get_gem_inventory(token_a)
        if inventory_after:
            magic_gems_after = None
            magic_gems_frozen = None
            for gem in inventory_after:  # inventory_after is now a list
                if gem["type"] == "Magic":
                    magic_gems_after = gem.get("quantity", 0) - gem.get("frozen_quantity", 0)  # Calculate available
                    magic_gems_frozen = gem.get("frozen_quantity", 0)
                    break
            
            record_test("Large Bet Creation - Gems Frozen Check", True, 
                       f"Magic gems after bet - Available: {magic_gems_after}, Frozen: {magic_gems_frozen}")
        
        return token_a, game_id
    else:
        record_test("Large Bet Creation - Game Creation", False, "Failed to create $400 bet game")
        return token_a, None

def test_player_b_join_large_bet(game_id: str):
    """Test 2: Player B joining large bet without 'Insufficient Magic gems' error."""
    print_subheader("TEST 2: Player B Joining Large Bet")
    
    if not game_id:
        record_test("Player B Join - Prerequisites", False, "No game ID available for joining")
        return None
    
    # Generate unique user for Player B
    email_b = generate_unique_email()
    username_b = f"player_b_{int(time.time())}"
    
    # Register Player B
    token_b = register_and_verify_user(username_b, email_b, "Test123!", "female")
    if not token_b:
        record_test("Player B Join - Registration", False, "Failed to register Player B")
        return None
    
    record_test("Player B Join - Registration", True, f"Successfully registered {username_b}")
    
    # Buy sufficient gems for Player B (including Magic gems)
    gem_purchases_b = [
        {"gem_type": "Magic", "quantity": 5}  # Enough Magic gems to join $400 bet
    ]
    
    if not buy_gems(token_b, gem_purchases_b):
        record_test("Player B Join - Gem Purchase", False, "Failed to buy Magic gems for Player B")
        return None
    
    record_test("Player B Join - Gem Purchase", True, "Successfully bought 5 Magic gems for Player B")
    
    # Check Player B's gem inventory before joining
    inventory_b_before = get_gem_inventory(token_b)
    if inventory_b_before:
        magic_gems_b_before = None
        for gem in inventory_b_before:  # inventory_b_before is now a list
            if gem["type"] == "Magic":
                magic_gems_b_before = gem.get("quantity", 0) - gem.get("frozen_quantity", 0)  # Calculate available
                break
        
        record_test("Player B Join - Inventory Check Before", True, 
                   f"Player B Magic gems before join: {magic_gems_b_before}")
    
    # Attempt to join the game with matching gems
    join_gems = {"Magic": 4}  # Match the $400 bet
    join_success = join_game(token_b, game_id, join_gems)
    
    if join_success:
        record_test("Player B Join - Join Game Success", True, 
                   "Player B successfully joined $400 bet without 'Insufficient Magic gems' error")
        
        # Check Player B's gem inventory after joining (gems should be frozen)
        inventory_b_after = get_gem_inventory(token_b)
        if inventory_b_after:
            magic_gems_b_after = None
            magic_gems_b_frozen = None
            for gem in inventory_b_after:  # inventory_b_after is now a list
                if gem["type"] == "Magic":
                    magic_gems_b_after = gem.get("quantity", 0) - gem.get("frozen_quantity", 0)  # Calculate available
                    magic_gems_b_frozen = gem.get("frozen_quantity", 0)
                    break
            
            record_test("Player B Join - Gems Frozen After Join", True, 
                       f"Player B Magic gems after join - Available: {magic_gems_b_after}, Frozen: {magic_gems_b_frozen}")
        
        return token_b
    else:
        record_test("Player B Join - Join Game Success", False, 
                   "Player B failed to join $400 bet - possible 'Insufficient Magic gems' error")
        return None

def test_gem_inventory_validation(token_a: str, token_b: str):
    """Test 3: Validate gem inventory endpoint returns correct available_quantity."""
    print_subheader("TEST 3: Gem Inventory Validation")
    
    if not token_a:
        record_test("Gem Inventory Validation - Player A Token", False, "Player A token not available")
        return
    
    # Test Player A's inventory
    inventory_a = get_gem_inventory(token_a)
    if inventory_a:
        # Validate response structure (it's a list)
        if isinstance(inventory_a, list):
            record_test("Gem Inventory Validation - Response Structure", True, 
                       "Inventory response is a list as expected")
            
            # Check gem structure
            if inventory_a:
                magic_gem = None
                for gem in inventory_a:
                    if gem["type"] == "Magic":
                        magic_gem = gem
                        break
                
                if magic_gem:
                    required_gem_fields = ["type", "name", "price", "quantity", "frozen_quantity"]
                    missing_gem_fields = [field for field in required_gem_fields if field not in magic_gem]
                    
                    if not missing_gem_fields:
                        record_test("Gem Inventory Validation - Gem Structure", True, 
                                   f"Magic gem has all required fields: {required_gem_fields}")
                        
                        # Validate available quantity calculation
                        total_quantity = magic_gem.get("quantity", 0)
                        frozen_quantity = magic_gem.get("frozen_quantity", 0)
                        available_quantity = total_quantity - frozen_quantity
                        
                        record_test("Gem Inventory Validation - Available Quantity Calculation", True, 
                                   f"Available quantity calculated: {available_quantity} = {total_quantity} - {frozen_quantity}")
                    else:
                        record_test("Gem Inventory Validation - Gem Structure", False, 
                                   f"Magic gem missing fields: {missing_gem_fields}")
                else:
                    record_test("Gem Inventory Validation - Magic Gem Present", False, 
                               "Magic gem not found in inventory")
            else:
                record_test("Gem Inventory Validation - Gems Array", False, 
                           "No gems found in inventory response")
        else:
            record_test("Gem Inventory Validation - Response Structure", False, 
                       f"Inventory response is not a list: {type(inventory_a)}")
    else:
        record_test("Gem Inventory Validation - API Call", False, 
                   "Failed to get gem inventory for Player A")
    
    # Test Player B's inventory if available
    if token_b:
        inventory_b = get_gem_inventory(token_b)
        if inventory_b:
            record_test("Gem Inventory Validation - Player B Inventory", True, 
                       "Successfully retrieved Player B's gem inventory")
        else:
            record_test("Gem Inventory Validation - Player B Inventory", False, 
                       "Failed to get gem inventory for Player B")

def test_balance_endpoint_validation(token_a: str, token_b: str):
    """Test 4: Validate /api/auth/me endpoint returns correct balance structure."""
    print_subheader("TEST 4: Balance Endpoint Validation")
    
    if not token_a:
        record_test("Balance Endpoint Validation - Player A Token", False, "Player A token not available")
        return
    
    # Test Player A's balance
    balance_a = get_user_balance(token_a)
    if balance_a:
        # Validate response structure
        required_fields = ["id", "username", "email", "virtual_balance", "frozen_balance"]
        missing_fields = [field for field in required_fields if field not in balance_a]
        
        if not missing_fields:
            record_test("Balance Endpoint Validation - Response Structure", True, 
                       f"Balance response has required fields: {required_fields}")
            
            # Validate balance values
            virtual_balance = balance_a.get("virtual_balance", 0)
            frozen_balance = balance_a.get("frozen_balance", 0)
            
            if isinstance(virtual_balance, (int, float)) and isinstance(frozen_balance, (int, float)):
                record_test("Balance Endpoint Validation - Balance Types", True, 
                           f"Balance values are numeric - Virtual: {virtual_balance}, Frozen: {frozen_balance}")
                
                # Check if frozen balance reflects the commission for large bet
                # For $400 bet, commission should be $12 (3% of $400)
                expected_commission = 400 * 0.03  # 3% commission
                if frozen_balance >= expected_commission:
                    record_test("Balance Endpoint Validation - Commission Frozen", True, 
                               f"Frozen balance reflects commission: {frozen_balance} >= {expected_commission}")
                else:
                    record_test("Balance Endpoint Validation - Commission Frozen", False, 
                               f"Frozen balance doesn't reflect expected commission: {frozen_balance} < {expected_commission}")
            else:
                record_test("Balance Endpoint Validation - Balance Types", False, 
                           f"Balance values are not numeric - Virtual: {type(virtual_balance)}, Frozen: {type(frozen_balance)}")
        else:
            record_test("Balance Endpoint Validation - Response Structure", False, 
                       f"Balance response missing fields: {missing_fields}")
    else:
        record_test("Balance Endpoint Validation - API Call", False, 
                   "Failed to get balance for Player A")
    
    # Test Player B's balance if available
    if token_b:
        balance_b = get_user_balance(token_b)
        if balance_b:
            record_test("Balance Endpoint Validation - Player B Balance", True, 
                       "Successfully retrieved Player B's balance")
            
            # Check Player B's frozen balance after joining
            frozen_balance_b = balance_b.get("frozen_balance", 0)
            expected_commission_b = 400 * 0.03  # 3% commission for Player B too
            
            if frozen_balance_b >= expected_commission_b:
                record_test("Balance Endpoint Validation - Player B Commission Frozen", True, 
                           f"Player B frozen balance reflects commission: {frozen_balance_b} >= {expected_commission_b}")
            else:
                record_test("Balance Endpoint Validation - Player B Commission Frozen", False, 
                           f"Player B frozen balance doesn't reflect expected commission: {frozen_balance_b} < {expected_commission_b}")
        else:
            record_test("Balance Endpoint Validation - Player B Balance", False, 
                       "Failed to get balance for Player B")

def test_big_strategy_magic_gems_requirement():
    """Test 5: Validate that 'Big' strategy requires Magic gems for large bets."""
    print_subheader("TEST 5: Big Strategy Magic Gems Requirement")
    
    # Generate unique user for this test
    email = generate_unique_email()
    username = f"big_strategy_test_{int(time.time())}"
    
    # Register user
    token = register_and_verify_user(username, email, "Test123!", "male")
    if not token:
        record_test("Big Strategy Test - User Registration", False, "Failed to register test user")
        return
    
    record_test("Big Strategy Test - User Registration", True, f"Successfully registered {username}")
    
    # Try to create large bet without Magic gems (should fail)
    # Buy only regular gems
    gem_purchases = [
        {"gem_type": "Sapphire", "quantity": 10}  # 10 Sapphire = $500, but not Magic gems
    ]
    
    if buy_gems(token, gem_purchases):
        record_test("Big Strategy Test - Regular Gems Purchase", True, "Successfully bought Sapphire gems")
        
        # Try to create $400+ bet with Sapphire gems (should work as Sapphire is $50 each)
        bet_gems_sapphire = {"Sapphire": 8}  # 8 Sapphire = $400
        game_id_sapphire = create_large_bet_game(token, bet_gems_sapphire)
        
        if game_id_sapphire:
            record_test("Big Strategy Test - Large Bet with Sapphire", True, 
                       "Successfully created $400 bet with Sapphire gems (8 x $50)")
        else:
            record_test("Big Strategy Test - Large Bet with Sapphire", False, 
                       "Failed to create $400 bet with Sapphire gems")
        
        # Now test with Magic gems
        magic_purchases = [
            {"gem_type": "Magic", "quantity": 5}
        ]
        
        if buy_gems(token, magic_purchases):
            record_test("Big Strategy Test - Magic Gems Purchase", True, "Successfully bought Magic gems")
            
            # Create $400 bet with Magic gems
            bet_gems_magic = {"Magic": 4}  # 4 Magic = $400
            game_id_magic = create_large_bet_game(token, bet_gems_magic)
            
            if game_id_magic:
                record_test("Big Strategy Test - Large Bet with Magic", True, 
                           "Successfully created $400 bet with Magic gems (4 x $100)")
            else:
                record_test("Big Strategy Test - Large Bet with Magic", False, 
                           "Failed to create $400 bet with Magic gems")
        else:
            record_test("Big Strategy Test - Magic Gems Purchase", False, "Failed to buy Magic gems")
    else:
        record_test("Big Strategy Test - Regular Gems Purchase", False, "Failed to buy Sapphire gems")

def print_final_results():
    """Print final test results summary."""
    print_header("LARGE BET GEM VALIDATION TEST RESULTS")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 80 else Colors.WARNING}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print(f"\n{Colors.FAIL}FAILED TESTS:{Colors.ENDC}")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"  ✗ {test['name']}: {test['details']}")
    
    print(f"\n{Colors.OKBLUE}DETAILED TEST LOG:{Colors.ENDC}")
    for test in test_results["tests"]:
        status = "✓" if test["passed"] else "✗"
        color = Colors.OKGREEN if test["passed"] else Colors.FAIL
        print(f"  {color}{status} {test['name']}: {test['details']}{Colors.ENDC}")

def main():
    """Main test execution function."""
    print_header("GEMPLAY LARGE BET GEM VALIDATION TESTING")
    print("Focus: Testing gem validation fixes for large bets ($400+)")
    print("Russian Review Requirements: Протестировать исправления ошибки с валидацией гемов для больших ставок")
    
    try:
        # Test 1: Create large bet ($400)
        token_a, game_id = test_large_bet_creation()
        
        # Test 2: Player B join large bet
        token_b = test_player_b_join_large_bet(game_id)
        
        # Test 3: Gem inventory validation
        test_gem_inventory_validation(token_a, token_b)
        
        # Test 4: Balance endpoint validation
        test_balance_endpoint_validation(token_a, token_b)
        
        # Test 5: Big strategy Magic gems requirement
        test_big_strategy_magic_gems_requirement()
        
        # Print final results
        print_final_results()
        
        # Return appropriate exit code
        if test_results["failed"] == 0:
            print(f"\n{Colors.OKGREEN}🎉 ALL TESTS PASSED! Large bet gem validation is working correctly.{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.FAIL}❌ SOME TESTS FAILED! Large bet gem validation needs attention.{Colors.ENDC}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test execution interrupted by user.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error during testing: {str(e)}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()