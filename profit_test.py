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
BASE_URL = "https://11ff6985-226e-4a25-848c-148a2fa58531.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}
TEST_USERS = [
    {
        "username": "player1",
        "email": "player1@test.com",
        "password": "Test123!",
        "gender": "male"
    },
    {
        "username": "player2",
        "email": "player2@test.com",
        "password": "Test123!",
        "gender": "female"
    }
]

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

def test_login(email: str, password: str, username: str, expected_success: bool = True) -> Optional[str]:
    """Test user login."""
    print_subheader(f"Testing User Login for {username} {'(Expected Success)' if expected_success else '(Expected Failure)'}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    expected_status = 200 if expected_success else 401
    print(f"Attempting login with email: {email}, password: {password}")
    print(f"Expected status: {expected_status}")
    
    response, success = make_request("POST", "/auth/login", data=login_data, expected_status=expected_status)
    
    # For invalid login test
    if not expected_success:
        if "detail" in response and "Incorrect email or password" in response["detail"]:
            print_success("Login correctly failed with invalid credentials")
            record_test(f"Invalid Login Attempt - {username}", True)
        else:
            print_error(f"Login failed but with unexpected error: {response}")
            record_test(f"Invalid Login Attempt - {username}", False, f"Unexpected error: {response}")
        return None
    
    # For valid login test
    if expected_success:
        if success and "access_token" in response and "user" in response:
            print_success(f"User logged in successfully")
            print_success(f"User details: {response['user']['username']} ({response['user']['email']})")
            print_success(f"Balance: ${response['user']['virtual_balance']}")
            record_test(f"User Login - {username}", True)
            return response["access_token"]
        else:
            print_error(f"Login failed: {response}")
            record_test(f"User Login - {username}", False, f"Login failed: {response}")
            return None
    
    return None

def test_buy_gems(token: str, username: str, gem_type: str, quantity: int) -> bool:
    """Test buying gems."""
    print_subheader(f"Testing Buy Gems for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Buy Gems - {username}", False, "No token available")
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
            record_test(f"Buy Gems - {username}", True)
            return True
        else:
            print_error(f"Buy gems response missing expected fields: {response}")
            record_test(f"Buy Gems - {username}", False, "Response missing expected fields")
    else:
        record_test(f"Buy Gems - {username}", False, "Request failed")
    
    return False

def test_gift_gems(token: str, username: str, recipient_email: str, gem_type: str, quantity: int) -> bool:
    """Test gifting gems."""
    print_subheader(f"Testing Gift Gems for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Gift Gems - {username}", False, "No token available")
        return False
    
    response, success = make_request(
        "POST", 
        f"/gems/gift?recipient_email={recipient_email}&gem_type={gem_type}&quantity={quantity}", 
        auth_token=token
    )
    
    if success:
        if "message" in response and "gem_value" in response and "commission" in response:
            print_success(f"Successfully gifted {quantity} {gem_type} gems to {recipient_email}")
            print_success(f"Gem value: ${response['gem_value']}")
            print_success(f"Commission (3%): ${response['commission']}")
            record_test(f"Gift Gems - {username}", True)
            return True
        else:
            print_error(f"Gift gems response missing expected fields: {response}")
            record_test(f"Gift Gems - {username}", False, "Response missing expected fields")
    else:
        record_test(f"Gift Gems - {username}", False, "Request failed")
    
    return False

def test_create_game(token: str, username: str, move: str, bet_gems: Dict[str, int]) -> Optional[str]:
    """Test creating a game."""
    print_subheader(f"Testing Create Game for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Create Game - {username}", False, "No token available")
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
            record_test(f"Create Game - {username}", True)
            return response["game_id"]
        else:
            print_error(f"Create game response missing expected fields: {response}")
            record_test(f"Create Game - {username}", False, "Response missing expected fields")
    else:
        record_test(f"Create Game - {username}", False, "Request failed")
    
    return None

def test_join_game(token: str, username: str, game_id: str, move: str) -> Dict[str, Any]:
    """Test joining a game."""
    print_subheader(f"Testing Join Game for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Join Game - {username}", False, "No token available")
        return {}
    
    # Send move in the request body
    data = {
        "move": move
    }
    
    response, success = make_request(
        "POST", 
        f"/games/{game_id}/join", 
        data=data,
        auth_token=token
    )
    
    if success:
        if "game_id" in response and "result" in response and "creator_move" in response and "opponent_move" in response:
            print_success(f"Successfully joined game {game_id}")
            print_success(f"Result: {response['result']}")
            print_success(f"Creator move: {response['creator_move']}")
            print_success(f"Opponent move: {response['opponent_move']}")
            
            if "winner_id" in response:
                print_success(f"Winner ID: {response['winner_id']}")
            
            record_test(f"Join Game - {username}", True)
            return response
        else:
            print_error(f"Join game response missing expected fields: {response}")
            record_test(f"Join Game - {username}", False, "Response missing expected fields")
    else:
        record_test(f"Join Game - {username}", False, "Request failed")
    
    return {}

def test_get_profit_stats(token: str) -> bool:
    """Test getting profit statistics."""
    print_subheader("Testing Get Profit Stats")
    
    if not token:
        print_error("No auth token available")
        record_test("Get Profit Stats", False, "No token available")
        return False
    
    response, success = make_request("GET", "/admin/profit/stats", auth_token=token)
    
    if success:
        if "total_profit" in response and "recent_profit" in response and "weekly_profit" in response and "monthly_profit" in response and "profit_by_type" in response:
            print_success("Successfully retrieved profit statistics")
            print_success(f"Total profit: ${response['total_profit']}")
            print_success(f"Recent profit (24h): ${response['recent_profit']}")
            print_success(f"Weekly profit: ${response['weekly_profit']}")
            print_success(f"Monthly profit: ${response['monthly_profit']}")
            print_success(f"Profit by type: {response['profit_by_type']}")
            record_test("Get Profit Stats", True)
            return True
        else:
            print_error(f"Profit stats response missing expected fields: {response}")
            record_test("Get Profit Stats", False, "Response missing expected fields")
    else:
        record_test("Get Profit Stats", False, "Request failed")
    
    return False

def test_get_profit_entries(token: str) -> bool:
    """Test getting profit entries."""
    print_subheader("Testing Get Profit Entries")
    
    if not token:
        print_error("No auth token available")
        record_test("Get Profit Entries", False, "No token available")
        return False
    
    response, success = make_request("GET", "/admin/profit/entries", auth_token=token)
    
    if success:
        if "entries" in response and "total_count" in response:
            print_success("Successfully retrieved profit entries")
            print_success(f"Total entries: {response['total_count']}")
            
            if response['entries']:
                print_success(f"Sample entry: {response['entries'][0]}")
                
                # Check if entries have the expected fields
                sample_entry = response['entries'][0]
                expected_fields = ["id", "entry_type", "amount", "source_user_id", "created_at", "description"]
                missing_fields = [field for field in expected_fields if field not in sample_entry]
                
                if missing_fields:
                    print_warning(f"Sample entry missing fields: {missing_fields}")
                else:
                    print_success("Sample entry has all expected fields")
            else:
                print_warning("No profit entries found")
            
            record_test("Get Profit Entries", True)
            return True
        else:
            print_error(f"Profit entries response missing expected fields: {response}")
            record_test("Get Profit Entries", False, "Response missing expected fields")
    else:
        record_test("Get Profit Entries", False, "Request failed")
    
    return False

def test_get_commission_settings(token: str) -> bool:
    """Test getting commission settings."""
    print_subheader("Testing Get Commission Settings")
    
    if not token:
        print_error("No auth token available")
        record_test("Get Commission Settings", False, "No token available")
        return False
    
    response, success = make_request("GET", "/admin/profit/commission-settings", auth_token=token)
    
    if success:
        if "bet_commission" in response and "gift_commission" in response:
            print_success("Successfully retrieved commission settings")
            print_success(f"Bet commission: {response['bet_commission']}%")
            print_success(f"Gift commission: {response['gift_commission']}%")
            print_success(f"Min bet: ${response['min_bet']}")
            print_success(f"Max bet: ${response['max_bet']}")
            print_success(f"Daily deposit limit: ${response['daily_deposit_limit']}")
            record_test("Get Commission Settings", True)
            return True
        else:
            print_error(f"Commission settings response missing expected fields: {response}")
            record_test("Get Commission Settings", False, "Response missing expected fields")
    else:
        record_test("Get Commission Settings", False, "Request failed")
    
    return False

def test_get_economy_balance(token: str, username: str) -> Dict[str, Any]:
    """Test getting economy balance."""
    print_subheader(f"Testing Get Economy Balance for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Get Economy Balance - {username}", False, "No token available")
        return {}
    
    response, success = make_request("GET", "/economy/balance", auth_token=token)
    
    if success:
        if "virtual_balance" in response and "frozen_balance" in response and "total_gem_value" in response:
            print_success("Successfully retrieved economy balance")
            print_success(f"Virtual balance: ${response['virtual_balance']}")
            print_success(f"Frozen balance: ${response['frozen_balance']}")
            print_success(f"Total gem value: ${response['total_gem_value']}")
            print_success(f"Available gem value: ${response['available_gem_value']}")
            print_success(f"Total value: ${response['total_value']}")
            print_success(f"Daily limit used: ${response['daily_limit_used']}")
            print_success(f"Daily limit max: ${response['daily_limit_max']}")
            record_test(f"Get Economy Balance - {username}", True)
            return response
        else:
            print_error(f"Economy balance response missing expected fields: {response}")
            record_test(f"Get Economy Balance - {username}", False, "Response missing expected fields")
    else:
        record_test(f"Get Economy Balance - {username}", False, "Request failed")
    
    return {}

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

def test_profit_tracking_system() -> None:
    """Test the profit tracking system."""
    print_header("TESTING PROFIT TRACKING SYSTEM")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Failed to login as admin")
        return
    
    # Test getting profit stats
    test_get_profit_stats(admin_token)
    
    # Test getting profit entries
    test_get_profit_entries(admin_token)
    
    # Test getting commission settings
    test_get_commission_settings(admin_token)
    
    # Register and login as player1
    player1_token = test_login(TEST_USERS[0]["email"], TEST_USERS[0]["password"], TEST_USERS[0]["username"])
    if not player1_token:
        # Try to register player1
        print_warning("Player1 not found, trying to register...")
        response, success = make_request("POST", "/auth/register", data=TEST_USERS[0])
        if success:
            print_success("Player1 registered successfully")
            # Verify email (in this test environment)
            if "verification_token" in response:
                verify_response, verify_success = make_request("POST", "/auth/verify-email", data={"token": response["verification_token"]})
                if verify_success:
                    print_success("Player1 email verified successfully")
                    player1_token = test_login(TEST_USERS[0]["email"], TEST_USERS[0]["password"], TEST_USERS[0]["username"])
                else:
                    print_error("Failed to verify player1 email")
        else:
            print_error("Failed to register player1")
    
    # Register and login as player2
    player2_token = test_login(TEST_USERS[1]["email"], TEST_USERS[1]["password"], TEST_USERS[1]["username"])
    if not player2_token:
        # Try to register player2
        print_warning("Player2 not found, trying to register...")
        response, success = make_request("POST", "/auth/register", data=TEST_USERS[1])
        if success:
            print_success("Player2 registered successfully")
            # Verify email (in this test environment)
            if "verification_token" in response:
                verify_response, verify_success = make_request("POST", "/auth/verify-email", data={"token": response["verification_token"]})
                if verify_success:
                    print_success("Player2 email verified successfully")
                    player2_token = test_login(TEST_USERS[1]["email"], TEST_USERS[1]["password"], TEST_USERS[1]["username"])
                else:
                    print_error("Failed to verify player2 email")
        else:
            print_error("Failed to register player2")
    
    if not player1_token or not player2_token:
        print_error("Failed to set up test users")
        return
    
    # Get initial balances
    player1_initial_balance = test_get_economy_balance(player1_token, TEST_USERS[0]["username"])
    player2_initial_balance = test_get_economy_balance(player2_token, TEST_USERS[1]["username"])
    
    # Buy gems for player1
    test_buy_gems(player1_token, TEST_USERS[0]["username"], "Ruby", 20)
    test_buy_gems(player1_token, TEST_USERS[0]["username"], "Emerald", 10)
    
    # Buy gems for player2
    test_buy_gems(player2_token, TEST_USERS[1]["username"], "Ruby", 20)
    test_buy_gems(player2_token, TEST_USERS[1]["username"], "Emerald", 10)
    
    # Test gifting gems (3% commission)
    test_gift_gems(player1_token, TEST_USERS[0]["username"], TEST_USERS[1]["email"], "Ruby", 5)
    
    # Check profit entries after gifting
    print_subheader("Checking profit entries after gifting")
    test_get_profit_entries(admin_token)
    
    # Create a game with gems (6% commission freeze)
    bet_gems = {"Ruby": 5, "Emerald": 2}
    game_id = test_create_game(player1_token, TEST_USERS[0]["username"], "rock", bet_gems)
    
    if not game_id:
        print_error("Failed to create game")
        return
    
    # Check player1's balance after creating game (should have frozen balance)
    player1_after_create = test_get_economy_balance(player1_token, TEST_USERS[0]["username"])
    
    # Verify frozen balance after game creation
    if player1_after_create.get("frozen_balance", 0) > 0:
        print_success(f"Player1 has frozen balance after creating game: ${player1_after_create.get('frozen_balance', 0)}")
        record_test("Frozen Balance After Game Creation", True)
    else:
        print_error("Player1 does not have frozen balance after creating game")
        record_test("Frozen Balance After Game Creation", False, "No frozen balance")
    
    # Player2 joins the game
    game_result = test_join_game(player2_token, TEST_USERS[1]["username"], game_id, "paper")
    
    if not game_result:
        print_error("Failed to join game")
        return
    
    # Check balances after game completion
    player1_after_game = test_get_economy_balance(player1_token, TEST_USERS[0]["username"])
    player2_after_game = test_get_economy_balance(player2_token, TEST_USERS[1]["username"])
    
    # Verify frozen balance after game completion
    if player1_after_game.get("frozen_balance", 0) < player1_after_create.get("frozen_balance", 0):
        print_success(f"Player1's frozen balance decreased after game completion: ${player1_after_game.get('frozen_balance', 0)}")
        record_test("Frozen Balance After Game Completion", True)
    else:
        print_error("Player1's frozen balance did not decrease after game completion")
        record_test("Frozen Balance After Game Completion", False, "Frozen balance not decreased")
    
    # Check profit entries after game completion
    print_subheader("Checking profit entries after game completion")
    test_get_profit_entries(admin_token)
    
    # Check profit stats after all transactions
    print_subheader("Checking profit stats after all transactions")
    test_get_profit_stats(admin_token)

def run_all_tests() -> None:
    """Run all tests in sequence."""
    print_header("GEMPLAY PROFIT TRACKING SYSTEM TESTING")
    
    # Test profit tracking system
    test_profit_tracking_system()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_all_tests()