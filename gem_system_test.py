#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib

# Configuration
BASE_URL = "https://629f70b8-18fb-40e8-982a-1f9a2bdf94c1.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

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

def record_test(name: str, passed: bool, details: str = "") -> None:
    """Record a test result."""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })

def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    auth_token: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"Making {method} request to {url}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        response_data = {"text": response.text}
        print(f"Response text: {response.text}")
    
    success = response.status_code == expected_status
    
    if not success:
        print_error(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success

def test_login(email: str, password: str) -> Optional[str]:
    """Test user login."""
    print_subheader(f"Testing User Login for {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response and "user" in response:
        print_success(f"User logged in successfully")
        print_success(f"User details: {response['user']['username']} ({response['user']['email']})")
        print_success(f"Balance: ${response['user']['virtual_balance']}")
        record_test(f"User Login - {email}", True)
        return response["access_token"]
    else:
        print_error(f"Login failed: {response}")
        record_test(f"User Login - {email}", False, f"Login failed: {response}")
        return None

def test_get_gem_definitions(token: str) -> Dict[str, Dict[str, Any]]:
    """Test getting gem definitions."""
    print_subheader("Testing Get Gem Definitions")
    
    if not token:
        print_error("No auth token available")
        record_test("Get Gem Definitions", False, "No token available")
        return {}
    
    response, success = make_request("GET", "/gems/definitions", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Got gem definitions: {len(response)} types")
            
            # Create a dictionary of gem definitions for easy access
            gem_defs = {}
            for gem in response:
                print_success(f"{gem['name']}: ${gem['price']} ({gem['rarity']})")
                gem_defs[gem['type']] = gem
            
            record_test("Get Gem Definitions", True)
            return gem_defs
        else:
            print_error(f"Gem definitions response is not a list: {response}")
            record_test("Get Gem Definitions", False, "Response is not a list")
    else:
        record_test("Get Gem Definitions", False, "Request failed")
    
    return {}

def test_get_user_gems(token: str) -> Dict[str, int]:
    """Test getting user's gem inventory."""
    print_subheader("Testing Get User Gems")
    
    if not token:
        print_error("No auth token available")
        record_test("Get User Gems", False, "No token available")
        return {}
    
    response, success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Got user gems: {len(response)} types")
            
            # Create a dictionary of gem types and quantities
            gem_inventory = {}
            for gem in response:
                print_success(f"{gem['name']}: {gem['quantity']} (Frozen: {gem['frozen_quantity']})")
                gem_inventory[gem['type']] = gem['quantity']
            
            record_test("Get User Gems", True)
            return gem_inventory
        else:
            print_error(f"User gems response is not a list: {response}")
            record_test("Get User Gems", False, "Response is not a list")
    else:
        record_test("Get User Gems", False, "Request failed")
    
    return {}

def test_get_economy_balance(token: str) -> Dict[str, Any]:
    """Test getting user's economic status."""
    print_subheader("Testing Get Economy Balance")
    
    if not token:
        print_error("No auth token available")
        record_test("Get Economy Balance", False, "No token available")
        return {}
    
    response, success = make_request("GET", "/economy/balance", auth_token=token)
    
    if success:
        if isinstance(response, dict):
            print_success(f"Got economy balance:")
            print_success(f"Virtual Balance: ${response.get('virtual_balance', 0)}")
            print_success(f"Frozen Balance: ${response.get('frozen_balance', 0)}")
            print_success(f"Total Gem Value: ${response.get('total_gem_value', 0)}")
            print_success(f"Available Gem Value: ${response.get('available_gem_value', 0)}")
            print_success(f"Total Value: ${response.get('total_value', 0)}")
            print_success(f"Daily Limit Used: ${response.get('daily_limit_used', 0)}")
            print_success(f"Daily Limit Max: ${response.get('daily_limit_max', 0)}")
            
            record_test("Get Economy Balance", True)
            return response
        else:
            print_error(f"Economy balance response is not a dictionary: {response}")
            record_test("Get Economy Balance", False, "Response is not a dictionary")
    else:
        record_test("Get Economy Balance", False, "Request failed")
    
    return {}

def test_buy_gems(token: str, gem_type: str, quantity: int) -> bool:
    """Test buying gems."""
    print_subheader(f"Testing Buy Gems - {gem_type} x{quantity}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Buy Gems - {gem_type} x{quantity}", False, "No token available")
        return False
    
    response, success = make_request(
        "POST", 
        f"/gems/buy?gem_type={gem_type}&quantity={quantity}", 
        auth_token=token
    )
    
    if success:
        if "message" in response and "total_cost" in response and "new_balance" in response:
            print_success(f"Successfully bought {quantity} {gem_type} gems")
            print_success(f"Total cost: ${response['total_cost']}")
            print_success(f"New balance: ${response['new_balance']}")
            record_test(f"Buy Gems - {gem_type} x{quantity}", True)
            return True
        else:
            print_error(f"Buy gems response missing expected fields: {response}")
            record_test(f"Buy Gems - {gem_type} x{quantity}", False, "Response missing expected fields")
    else:
        record_test(f"Buy Gems - {gem_type} x{quantity}", False, "Request failed")
    
    return False

def test_sell_gems(token: str, gem_type: str, quantity: int) -> bool:
    """Test selling gems."""
    print_subheader(f"Testing Sell Gems - {gem_type} x{quantity}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Sell Gems - {gem_type} x{quantity}", False, "No token available")
        return False
    
    response, success = make_request(
        "POST", 
        f"/gems/sell?gem_type={gem_type}&quantity={quantity}", 
        auth_token=token
    )
    
    if success:
        if "message" in response and "total_value" in response and "new_balance" in response:
            print_success(f"Successfully sold {quantity} {gem_type} gems")
            print_success(f"Total value: ${response['total_value']}")
            print_success(f"New balance: ${response['new_balance']}")
            record_test(f"Sell Gems - {gem_type} x{quantity}", True)
            return True
        else:
            print_error(f"Sell gems response missing expected fields: {response}")
            record_test(f"Sell Gems - {gem_type} x{quantity}", False, "Response missing expected fields")
    else:
        record_test(f"Sell Gems - {gem_type} x{quantity}", False, "Request failed")
    
    return False

def test_add_balance(token: str, amount: float) -> bool:
    """Test adding balance to user account."""
    print_subheader(f"Testing Add Balance - ${amount}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Add Balance - ${amount}", False, "No token available")
        return False
    
    response, success = make_request(
        "POST", 
        "/auth/add-balance", 
        data={"amount": amount},
        auth_token=token
    )
    
    if success:
        if "message" in response and "amount" in response and "new_balance" in response:
            print_success(f"Successfully added ${amount} to balance")
            print_success(f"New balance: ${response['new_balance']}")
            print_success(f"Remaining daily limit: ${response.get('remaining_daily_limit', 'N/A')}")
            record_test(f"Add Balance - ${amount}", True)
            return True
        else:
            print_error(f"Add balance response missing expected fields: {response}")
            record_test(f"Add Balance - ${amount}", False, "Response missing expected fields")
    else:
        record_test(f"Add Balance - ${amount}", False, "Request failed")
    
    return False

def test_add_balance_limit(token: str, amount: float, expected_error: str) -> bool:
    """Test adding balance beyond the daily limit."""
    print_subheader(f"Testing Add Balance Limit - ${amount} (Expected Error: {expected_error})")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Add Balance Limit - ${amount}", False, "No token available")
        return False
    
    response, success = make_request(
        "POST", 
        "/auth/add-balance", 
        data={"amount": amount},
        auth_token=token,
        expected_status=400
    )
    
    if not success and "detail" in response and expected_error in response["detail"]:
        print_success(f"Correctly received error: {response['detail']}")
        record_test(f"Add Balance Limit - ${amount}", True)
        return True
    else:
        print_error(f"Did not receive expected error. Response: {response}")
        record_test(f"Add Balance Limit - ${amount}", False, f"Did not receive expected error")
        return False

def test_create_game_with_gems(token: str, move: str, bet_gems: Dict[str, int]) -> Optional[str]:
    """Test creating a game with gems."""
    print_subheader(f"Testing Create Game with Gems")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Create Game with Gems", False, "No token available")
        return None
    
    # Send both move and bet_gems in the request body
    data = {
        "move": move,
        "bet_gems": bet_gems
    }
    
    response, success = make_request(
        "POST", 
        "/games/create", 
        data=data,
        auth_token=token
    )
    
    if success:
        if "message" in response and "game_id" in response and "bet_amount" in response:
            print_success(f"Game created successfully with ID: {response['game_id']}")
            print_success(f"Bet amount: ${response['bet_amount']}")
            print_success(f"Commission reserved: ${response['commission_reserved']}")
            record_test(f"Create Game with Gems", True)
            return response["game_id"]
        else:
            print_error(f"Create game response missing expected fields: {response}")
            record_test(f"Create Game with Gems", False, "Response missing expected fields")
    else:
        record_test(f"Create Game with Gems", False, "Request failed")
    
    return None

def print_summary() -> None:
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results["failed"] > 0:
        print("\nFailed tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"{Colors.FAIL}✗ {test['name']}: {test['details']}{Colors.ENDC}")
    
    success_rate = (test_results["passed"] / test_results["total"]) * 100 if test_results["total"] > 0 else 0
    print(f"\nSuccess rate: {Colors.BOLD}{success_rate:.2f}%{Colors.ENDC}")
    
    if test_results["failed"] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests passed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some tests failed!{Colors.ENDC}")

def test_gem_system() -> None:
    """Test the gem system and balance functionality."""
    print_header("TESTING GEM SYSTEM AND BALANCE FUNCTIONALITY")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"])
    
    if not admin_token:
        print_error("Failed to login as admin")
        return
    
    # Get initial balance and gem inventory
    initial_balance = test_get_economy_balance(admin_token)
    initial_gems = test_get_user_gems(admin_token)
    gem_definitions = test_get_gem_definitions(admin_token)
    
    if not gem_definitions:
        print_error("Failed to get gem definitions")
        return
    
    # Test 1: Buy different types of gems
    print_subheader("TEST 1: BUY DIFFERENT TYPES OF GEMS")
    
    # Buy Ruby gems (lowest value)
    test_buy_gems(admin_token, "Ruby", 10)
    
    # Buy Emerald gems (medium value)
    test_buy_gems(admin_token, "Emerald", 5)
    
    # Buy Magic gems (highest value)
    test_buy_gems(admin_token, "Magic", 2)
    
    # Check updated balance and gem inventory
    post_purchase_balance = test_get_economy_balance(admin_token)
    post_purchase_gems = test_get_user_gems(admin_token)
    
    # Test 2: Sell gems back to the shop
    print_subheader("TEST 2: SELL GEMS BACK TO THE SHOP")
    
    # Sell some Ruby gems
    test_sell_gems(admin_token, "Ruby", 5)
    
    # Sell some Emerald gems
    test_sell_gems(admin_token, "Emerald", 2)
    
    # Check updated balance and gem inventory
    post_sell_balance = test_get_economy_balance(admin_token)
    post_sell_gems = test_get_user_gems(admin_token)
    
    # Test 3: Add balance to account
    print_subheader("TEST 3: ADD BALANCE TO ACCOUNT")
    
    # Add small amount
    test_add_balance(admin_token, 100)
    
    # Add medium amount
    test_add_balance(admin_token, 500)
    
    # Check updated balance
    post_add_balance = test_get_economy_balance(admin_token)
    
    # Test 4: Test daily limit
    print_subheader("TEST 4: TEST DAILY LIMIT")
    
    # Try to add amount that would exceed daily limit
    remaining_limit = post_add_balance.get('daily_limit_max', 1000) - post_add_balance.get('daily_limit_used', 0)
    
    if remaining_limit > 0:
        # Try to add slightly more than the remaining limit
        test_add_balance_limit(admin_token, remaining_limit + 50, "Amount exceeds remaining daily limit")
        
        # Add exactly the remaining limit (should succeed)
        if remaining_limit > 0:
            test_add_balance(admin_token, remaining_limit)
    else:
        print_warning(f"Daily limit already reached (${post_add_balance.get('daily_limit_used', 0)}/${post_add_balance.get('daily_limit_max', 1000)})")
        # Try to add any amount (should fail)
        test_add_balance_limit(admin_token, 100, "Daily limit already reached")
    
    # Check final balance
    final_balance = test_get_economy_balance(admin_token)
    
    # Test 5: Create game with gems
    print_subheader("TEST 5: CREATE GAME WITH GEMS")
    
    # Get current gem inventory
    current_gems = test_get_user_gems(admin_token)
    
    # Create a bet with gems we have
    bet_gems = {}
    for gem_type, quantity in current_gems.items():
        if quantity >= 2:  # Use 2 of each gem type we have at least 2 of
            bet_gems[gem_type] = 2
            break
    
    if bet_gems:
        game_id = test_create_game_with_gems(admin_token, "rock", bet_gems)
        
        # Check updated gem inventory (gems should be frozen)
        post_game_gems = test_get_user_gems(admin_token)
    else:
        print_warning("Not enough gems to create a game")

def run_all_tests() -> None:
    """Run all tests in sequence."""
    print_header("GEMPLAY GEM SYSTEM AND BALANCE TESTING")
    
    # Test gem system and balance functionality
    test_gem_system()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_all_tests()