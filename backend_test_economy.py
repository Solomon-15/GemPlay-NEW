#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://aeee184a-ce91-4393-b9b2-af26aae57394.preview.emergentagent.com/api"
TEST_USER1 = {
    "username": "testuser_economy1",
    "email": "testuser_economy1@example.com",
    "password": "Test123!",
    "gender": "male"
}
TEST_USER2 = {
    "username": "testuser_economy2",
    "email": "testuser_economy2@example.com",
    "password": "Test123!",
    "gender": "female"
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
    auth_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None
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
    if params:
        print(f"Request params: {json.dumps(params, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers, params=params)
    else:
        response = requests.request(method, url, params=params or data, headers=headers)
    
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

def register_user(user_data: Dict[str, str]) -> Tuple[Optional[str], str, str]:
    """Register a new user."""
    print_subheader(f"Registering user: {user_data['username']}")
    
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if success:
        if "message" in response and "user_id" in response and "verification_token" in response:
            print_success(f"User registered successfully with ID: {response['user_id']}")
            print_success(f"Verification token: {response['verification_token']}")
            return response["verification_token"], user_data["email"], user_data["username"]
        else:
            print_error(f"User registration response missing expected fields: {response}")
    else:
        print_error(f"User registration failed: {response}")
    
    return None, user_data["email"], user_data["username"]

def verify_email(token: str) -> bool:
    """Verify user email."""
    print_subheader("Verifying email")
    
    if not token:
        print_error("No verification token available")
        return False
    
    response, success = make_request("POST", "/auth/verify-email", data={"token": token})
    
    if success:
        if "message" in response and "verified" in response["message"].lower():
            print_success("Email verified successfully")
            return True
        else:
            print_error(f"Email verification response unexpected: {response}")
    else:
        print_error(f"Email verification failed: {response}")
    
    return False

def login_user(email: str, password: str) -> Optional[str]:
    """Login a user and return the auth token."""
    print_subheader(f"Logging in user: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response and "user" in response:
        print_success(f"User logged in successfully")
        print_success(f"User details: {response['user']['username']} ({response['user']['email']})")
        print_success(f"Balance: ${response['user']['virtual_balance']}")
        return response["access_token"]
    else:
        print_error(f"Login failed: {response}")
        return None

def test_gem_definitions() -> None:
    """Test getting gem definitions."""
    print_subheader("Testing Gem Definitions API")
    
    response, success = make_request("GET", "/gems/definitions")
    
    if success:
        if isinstance(response, list) and len(response) > 0:
            print_success(f"Retrieved {len(response)} gem definitions")
            for gem in response:
                print_success(f"Gem: {gem['name']} (Type: {gem['type']}, Price: ${gem['price']})")
            record_test("Gem Definitions API", True)
        else:
            print_error("Gem definitions response is empty or not a list")
            record_test("Gem Definitions API", False, "Empty or invalid response")
    else:
        record_test("Gem Definitions API", False, "Request failed")

def test_user_inventory(token: str) -> List[Dict[str, Any]]:
    """Test getting user's gem inventory."""
    print_subheader("Testing User Inventory API")
    
    if not token:
        print_error("No auth token available")
        record_test("Inventory API", False, "No token available")
        return []
    
    response, success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Retrieved user inventory with {len(response)} gem types")
            for gem in response:
                print_success(f"Gem: {gem['name']} (Quantity: {gem['quantity']}, Value: ${gem['price'] * gem['quantity']})")
            record_test("Inventory API", True)
            return response
        else:
            print_error("Inventory response is not a list")
            record_test("Inventory API", False, "Invalid response format")
    else:
        record_test("Inventory API", False, "Request failed")
    
    return []

def test_economy_balance(token: str) -> Dict[str, Any]:
    """Test getting user's economy balance."""
    print_subheader("Testing Economy Balance API")
    
    if not token:
        print_error("No auth token available")
        record_test("Economy Balance API", False, "No token available")
        return {}
    
    response, success = make_request("GET", "/economy/balance", auth_token=token)
    
    if success:
        if isinstance(response, dict) and "virtual_balance" in response and "total_gem_value" in response:
            print_success(f"Retrieved economy balance:")
            print_success(f"Virtual Balance: ${response['virtual_balance']}")
            print_success(f"Total Gem Value: ${response['total_gem_value']}")
            print_success(f"Total Value: ${response['total_value']}")
            record_test("Economy Balance API", True)
            return response
        else:
            print_error("Economy balance response missing expected fields")
            record_test("Economy Balance API", False, "Invalid response format")
    else:
        record_test("Economy Balance API", False, "Request failed")
    
    return {}

def test_buy_gems(token: str, gem_type: str, quantity: int) -> bool:
    """Test buying gems."""
    print_subheader(f"Testing Buy Gems API - Buying {quantity} {gem_type} gems")
    
    if not token:
        print_error("No auth token available")
        record_test("Buy Gems API", False, "No token available")
        return False
    
    params = {
        "gem_type": gem_type,
        "quantity": quantity
    }
    
    response, success = make_request("POST", "/gems/buy", params=params, auth_token=token)
    
    if success:
        if "message" in response and "total_cost" in response and "new_balance" in response:
            print_success(f"Successfully bought {quantity} {gem_type} gems")
            print_success(f"Total Cost: ${response['total_cost']}")
            print_success(f"New Balance: ${response['new_balance']}")
            record_test(f"Buy Gems API - {gem_type}", True)
            return True
        else:
            print_error("Buy gems response missing expected fields")
            record_test(f"Buy Gems API - {gem_type}", False, "Invalid response format")
    else:
        record_test(f"Buy Gems API - {gem_type}", False, "Request failed")
    
    return False

def test_sell_gems(token: str, gem_type: str, quantity: int) -> bool:
    """Test selling gems."""
    print_subheader(f"Testing Sell Gems API - Selling {quantity} {gem_type} gems")
    
    if not token:
        print_error("No auth token available")
        record_test("Sell Gems API", False, "No token available")
        return False
    
    params = {
        "gem_type": gem_type,
        "quantity": quantity
    }
    
    response, success = make_request("POST", "/gems/sell", params=params, auth_token=token)
    
    if success:
        if "message" in response and "total_value" in response and "new_balance" in response:
            print_success(f"Successfully sold {quantity} {gem_type} gems")
            print_success(f"Total Value: ${response['total_value']}")
            print_success(f"New Balance: ${response['new_balance']}")
            record_test(f"Sell Gems API - {gem_type}", True)
            return True
        else:
            print_error("Sell gems response missing expected fields")
            record_test(f"Sell Gems API - {gem_type}", False, "Invalid response format")
    else:
        record_test(f"Sell Gems API - {gem_type}", False, "Request failed")
    
    return False

def test_gift_gems(sender_token: str, recipient_email: str, gem_type: str, quantity: int) -> bool:
    """Test gifting gems to another user."""
    print_subheader(f"Testing Gift Gems API - Gifting {quantity} {gem_type} gems to {recipient_email}")
    
    if not sender_token:
        print_error("No auth token available")
        record_test("Gift Gems API", False, "No token available")
        return False
    
    params = {
        "recipient_email": recipient_email,
        "gem_type": gem_type,
        "quantity": quantity
    }
    
    response, success = make_request("POST", "/gems/gift", params=params, auth_token=sender_token)
    
    if success:
        if "message" in response and "gem_value" in response and "commission" in response:
            print_success(f"Successfully gifted {quantity} {gem_type} gems to {recipient_email}")
            print_success(f"Gem Value: ${response['gem_value']}")
            print_success(f"Commission (3%): ${response['commission']}")
            print_success(f"New Balance: ${response['new_balance']}")
            
            # Verify commission is 3% of gem value
            expected_commission = round(response['gem_value'] * 0.03, 2)
            actual_commission = round(response['commission'], 2)
            
            if expected_commission == actual_commission:
                print_success(f"Commission calculation is correct: ${actual_commission} (3% of ${response['gem_value']})")
                record_test("Gift Gems API - Commission", True)
            else:
                print_error(f"Commission calculation is incorrect: ${actual_commission} (expected ${expected_commission})")
                record_test("Gift Gems API - Commission", False, f"Incorrect commission: got ${actual_commission}, expected ${expected_commission}")
            
            record_test("Gift Gems API", True)
            return True
        else:
            print_error("Gift gems response missing expected fields")
            record_test("Gift Gems API", False, "Invalid response format")
    else:
        record_test("Gift Gems API", False, "Request failed")
    
    return False

def test_transaction_history(token: str) -> None:
    """Test getting transaction history."""
    print_subheader("Testing Transaction History API")
    
    if not token:
        print_error("No auth token available")
        record_test("Transaction History API", False, "No token available")
        return
    
    response, success = make_request("GET", "/transactions/history", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Retrieved {len(response)} transactions")
            for transaction in response[:5]:  # Show first 5 transactions
                print_success(f"Transaction: {transaction['transaction_type']} - Amount: ${transaction['amount']} - Description: {transaction['description']}")
            record_test("Transaction History API", True)
        else:
            print_error("Transaction history response is not a list")
            record_test("Transaction History API", False, "Invalid response format")
    else:
        record_test("Transaction History API", False, "Request failed")

def test_insufficient_funds(token: str) -> None:
    """Test buying gems with insufficient funds."""
    print_subheader("Testing Insufficient Funds Validation")
    
    if not token:
        print_error("No auth token available")
        record_test("Insufficient Funds Validation", False, "No token available")
        return
    
    # Get current balance
    balance_response, balance_success = make_request("GET", "/economy/balance", auth_token=token)
    
    if not balance_success:
        print_error("Failed to get current balance")
        record_test("Insufficient Funds Validation", False, "Failed to get current balance")
        return
    
    current_balance = balance_response.get("virtual_balance", 0)
    
    # Try to buy gems worth more than current balance
    # Using Magic gems which are the most expensive
    quantity = int(current_balance / 100) + 10  # Ensure it's more than current balance
    
    params = {
        "gem_type": "Magic",
        "quantity": quantity
    }
    
    # We expect a 400 error, so we set expected_status=400
    response, success = make_request("POST", "/gems/buy", params=params, auth_token=token, expected_status=400)
    
    # For validation tests, success means the server correctly returned a 400 error with the right message
    if success and "detail" in response and "Insufficient balance" in response["detail"]:
        print_success("Server correctly rejected purchase with insufficient funds")
        record_test("Insufficient Funds Validation", True)
    else:
        print_error("Server did not properly validate insufficient funds")
        record_test("Insufficient Funds Validation", False, "Validation failed")

def test_insufficient_gems(token: str) -> None:
    """Test selling more gems than available."""
    print_subheader("Testing Insufficient Gems Validation")
    
    if not token:
        print_error("No auth token available")
        record_test("Insufficient Gems Validation", False, "No token available")
        return
    
    # Get current inventory
    inventory_response, inventory_success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if not inventory_success or not isinstance(inventory_response, list) or len(inventory_response) == 0:
        print_error("Failed to get current inventory or inventory is empty")
        record_test("Insufficient Gems Validation", False, "Failed to get current inventory")
        return
    
    # Pick a gem type from inventory
    gem = inventory_response[0]
    gem_type = gem["type"]
    current_quantity = gem["quantity"]
    
    # Try to sell more gems than available
    sell_quantity = current_quantity + 10
    
    params = {
        "gem_type": gem_type,
        "quantity": sell_quantity
    }
    
    # We expect a 400 error, so we set expected_status=400
    response, success = make_request("POST", "/gems/sell", params=params, auth_token=token, expected_status=400)
    
    # For validation tests, success means the server correctly returned a 400 error with the right message
    if success and "detail" in response and "Insufficient gems" in response["detail"]:
        print_success("Server correctly rejected selling more gems than available")
        record_test("Insufficient Gems Validation", True)
    else:
        print_error("Server did not properly validate insufficient gems")
        record_test("Insufficient Gems Validation", False, "Validation failed")

def test_frozen_gems_validation(token: str) -> None:
    """Test frozen gems validation (basic logic without actual bets)."""
    print_subheader("Testing Frozen Gems Validation")
    
    # Since we can't actually create bets in this test, we'll just check if the frozen_quantity field exists
    # and is being returned in the inventory API
    
    if not token:
        print_error("No auth token available")
        record_test("Frozen Gems Validation", False, "No token available")
        return
    
    inventory_response, inventory_success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if inventory_success and isinstance(inventory_response, list) and len(inventory_response) > 0:
        has_frozen_field = all("frozen_quantity" in gem for gem in inventory_response)
        
        if has_frozen_field:
            print_success("All gems in inventory have frozen_quantity field")
            record_test("Frozen Gems Validation", True)
        else:
            print_error("Some gems in inventory are missing frozen_quantity field")
            record_test("Frozen Gems Validation", False, "Missing frozen_quantity field")
    else:
        print_error("Failed to get inventory or inventory is empty")
        record_test("Frozen Gems Validation", False, "Failed to get inventory")

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

def run_economy_tests() -> None:
    """Run all economy-related tests."""
    print_header("GEMPLAY ECONOMY API TESTING")
    
    # Test gem definitions API
    test_gem_definitions()
    
    # Register and verify first test user
    token1, email1, username1 = register_user(TEST_USER1)
    if token1:
        verify_email(token1)
        auth_token1 = login_user(email1, TEST_USER1["password"])
    else:
        # Try to login with existing user
        auth_token1 = login_user(TEST_USER1["email"], TEST_USER1["password"])
    
    if not auth_token1:
        print_error("Failed to setup first test user. Aborting tests.")
        return
    
    # Register and verify second test user
    token2, email2, username2 = register_user(TEST_USER2)
    if token2:
        verify_email(token2)
        auth_token2 = login_user(email2, TEST_USER2["password"])
    else:
        # Try to login with existing user
        auth_token2 = login_user(TEST_USER2["email"], TEST_USER2["password"])
    
    if not auth_token2:
        print_error("Failed to setup second test user. Continuing with limited tests.")
    
    # Test initial inventory and balance
    initial_inventory = test_user_inventory(auth_token1)
    initial_balance = test_economy_balance(auth_token1)
    
    # Test buying different gem types
    test_buy_gems(auth_token1, "Ruby", 10)
    test_buy_gems(auth_token1, "Emerald", 5)
    test_buy_gems(auth_token1, "Sapphire", 2)
    
    # Test inventory after buying
    post_purchase_inventory = test_user_inventory(auth_token1)
    post_purchase_balance = test_economy_balance(auth_token1)
    
    # Test selling some gems
    test_sell_gems(auth_token1, "Ruby", 5)
    
    # Test inventory after selling
    post_sell_inventory = test_user_inventory(auth_token1)
    post_sell_balance = test_economy_balance(auth_token1)
    
    # Test gifting gems between users
    if auth_token2:
        test_gift_gems(auth_token1, TEST_USER2["email"], "Emerald", 2)
        
        # Check recipient's inventory
        print_subheader("Checking recipient's inventory after gift")
        recipient_inventory = test_user_inventory(auth_token2)
    
    # Test transaction history
    test_transaction_history(auth_token1)
    
    # Test validation scenarios
    test_insufficient_funds(auth_token1)
    test_insufficient_gems(auth_token1)
    test_frozen_gems_validation(auth_token1)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_economy_tests()