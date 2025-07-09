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
BASE_URL = "https://a2ff73b6-4501-4986-883b-e2ed6d281f4c.preview.emergentagent.com/api"
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

def hash_move_with_salt(move: str, salt: str) -> str:
    """Hash game move with salt for commit-reveal scheme."""
    combined = f"{move}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def test_user_registration(user_data: Dict[str, str]) -> Tuple[Optional[str], str, str]:
    """Test user registration."""
    print_subheader(f"Testing User Registration for {user_data['username']}")
    
    # Generate a random email to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = user_data["email"]
    test_username = user_data["username"]
    
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if success:
        if "message" in response and "user_id" in response and "verification_token" in response:
            print_success(f"User registered successfully with ID: {response['user_id']}")
            print_success(f"Verification token: {response['verification_token']}")
            record_test(f"User Registration - {test_username}", True)
            return response["verification_token"], test_email, test_username
        else:
            print_error(f"User registration response missing expected fields: {response}")
            record_test(f"User Registration - {test_username}", False, "Response missing expected fields")
    else:
        record_test(f"User Registration - {test_username}", False, "Request failed")
    
    return None, test_email, test_username

def test_email_verification(token: str, username: str) -> None:
    """Test email verification."""
    print_subheader(f"Testing Email Verification for {username}")
    
    if not token:
        print_error("No verification token available")
        record_test(f"Email Verification - {username}", False, "No token available")
        return
    
    response, success = make_request("POST", "/auth/verify-email", data={"token": token})
    
    if success:
        if "message" in response and "verified" in response["message"].lower():
            print_success("Email verified successfully")
            record_test(f"Email Verification - {username}", True)
        else:
            print_error(f"Email verification response unexpected: {response}")
            record_test(f"Email Verification - {username}", False, f"Unexpected response: {response}")
    else:
        record_test(f"Email Verification - {username}", False, "Request failed")

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

def test_get_user_gems(token: str, username: str) -> Dict[str, int]:
    """Test getting user's gem inventory."""
    print_subheader(f"Testing Get User Gems for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Get User Gems - {username}", False, "No token available")
        return {}
    
    response, success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Got user gems: {len(response)} types")
            for gem in response:
                print_success(f"{gem['name']}: {gem['quantity']} (Frozen: {gem['frozen_quantity']})")
            
            record_test(f"Get User Gems - {username}", True)
            
            # Return a dictionary of gem types and quantities
            return {gem["type"]: gem["quantity"] for gem in response}
        else:
            print_error(f"User gems response is not a list: {response}")
            record_test(f"Get User Gems - {username}", False, "Response is not a list")
    else:
        record_test(f"Get User Gems - {username}", False, "Request failed")
    
    return {}

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

def test_create_game_validation(token: str, username: str, move: str, bet_gems: Dict[str, int], expected_error: str) -> None:
    """Test validation when creating a game."""
    print_subheader(f"Testing Create Game Validation for {username} - Expected Error: {expected_error}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Create Game Validation - {username}", False, "No token available")
        return
    
    # Send both move and bet_gems in the request body
    data = {
        "move": move,
        "bet_gems": bet_gems
    }
    
    response, success = make_request(
        "POST", 
        "/games/create", 
        data=data,
        auth_token=token, 
        expected_status=400
    )
    
    if not success and "detail" in response and expected_error in response["detail"]:
        print_success(f"Validation correctly failed with error: {response['detail']}")
        record_test(f"Create Game Validation - {username} - {expected_error}", True)
    else:
        print_error(f"Validation did not fail as expected: {response}")
        record_test(f"Create Game Validation - {username} - {expected_error}", False, f"Unexpected response: {response}")

def test_get_available_games(token: str, username: str, expected_game_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Test getting available games."""
    print_subheader(f"Testing Get Available Games for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Get Available Games - {username}", False, "No token available")
        return []
    
    response, success = make_request("GET", "/games/available", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Got available games: {len(response)}")
            
            if expected_game_id:
                # Check if the expected game is in the list
                found = False
                for game in response:
                    if game["game_id"] == expected_game_id:
                        found = True
                        break
                
                if found:
                    print_success(f"Expected game {expected_game_id} found in available games")
                    record_test(f"Get Available Games - {username}", True)
                else:
                    print_error(f"Expected game {expected_game_id} not found in available games")
                    record_test(f"Get Available Games - {username}", False, f"Expected game not found")
            else:
                record_test(f"Get Available Games - {username}", True)
            
            return response
        else:
            print_error(f"Available games response is not a list: {response}")
            record_test(f"Get Available Games - {username}", False, "Response is not a list")
    else:
        record_test(f"Get Available Games - {username}", False, "Request failed")
    
    return []

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

def test_join_game_validation(token: str, username: str, game_id: str, move: str, expected_error: str) -> None:
    """Test validation when joining a game."""
    print_subheader(f"Testing Join Game Validation for {username} - Expected Error: {expected_error}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"Join Game Validation - {username}", False, "No token available")
        return
    
    # Send move in the request body
    data = {
        "move": move
    }
    
    response, success = make_request(
        "POST", 
        f"/games/{game_id}/join", 
        data=data,
        auth_token=token, 
        expected_status=400
    )
    
    if not success and "detail" in response and expected_error in response["detail"]:
        print_success(f"Validation correctly failed with error: {response['detail']}")
        record_test(f"Join Game Validation - {username} - {expected_error}", True)
    else:
        print_error(f"Validation did not fail as expected: {response}")
        record_test(f"Join Game Validation - {username} - {expected_error}", False, f"Unexpected response: {response}")

def test_get_user_gems_after_game(token: str, username: str, original_gems: Dict[str, int], is_winner: bool, bet_gems: Dict[str, int]) -> None:
    """Test getting user's gem inventory after a game to verify rewards."""
    print_subheader(f"Testing User Gems After Game for {username}")
    
    if not token:
        print_error("No auth token available")
        record_test(f"User Gems After Game - {username}", False, "No token available")
        return
    
    response, success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Got user gems after game: {len(response)} types")
            
            # Create a dictionary of current gem quantities
            current_gems = {gem["type"]: gem["quantity"] for gem in response}
            
            # Check if the gem quantities match expectations
            all_correct = True
            for gem_type, original_quantity in original_gems.items():
                bet_quantity = bet_gems.get(gem_type, 0)
                current_quantity = current_gems.get(gem_type, 0)
                
                if is_winner:
                    # Winner should have original quantity + bet quantity (doubled)
                    expected_quantity = original_quantity + bet_quantity
                else:
                    # Loser should have original quantity - bet quantity
                    expected_quantity = original_quantity - bet_quantity
                
                if current_quantity != expected_quantity:
                    print_error(f"{gem_type}: Expected {expected_quantity}, got {current_quantity}")
                    all_correct = False
                else:
                    print_success(f"{gem_type}: {current_quantity} (Expected: {expected_quantity})")
            
            if all_correct:
                print_success("All gem quantities match expectations after game")
                record_test(f"User Gems After Game - {username}", True)
            else:
                print_error("Some gem quantities do not match expectations after game")
                record_test(f"User Gems After Game - {username}", False, "Quantities do not match expectations")
        else:
            print_error(f"User gems response is not a list: {response}")
            record_test(f"User Gems After Game - {username}", False, "Response is not a list")
    else:
        record_test(f"User Gems After Game - {username}", False, "Request failed")

def test_rock_paper_scissors_logic(player1_token: str, player2_token: str) -> None:
    """Test rock-paper-scissors game logic with all possible combinations."""
    print_subheader("Testing Rock-Paper-Scissors Game Logic")
    
    if not player1_token or not player2_token:
        print_error("Missing player tokens")
        record_test("Rock-Paper-Scissors Logic", False, "Missing player tokens")
        return
    
    # All possible move combinations and expected results
    test_cases = [
        {"p1_move": "rock", "p2_move": "rock", "expected_result": "draw"},
        {"p1_move": "rock", "p2_move": "paper", "expected_result": "opponent_wins"},
        {"p1_move": "rock", "p2_move": "scissors", "expected_result": "creator_wins"},
        {"p1_move": "paper", "p2_move": "rock", "expected_result": "creator_wins"},
        {"p1_move": "paper", "p2_move": "paper", "expected_result": "draw"},
        {"p1_move": "paper", "p2_move": "scissors", "expected_result": "opponent_wins"},
        {"p1_move": "scissors", "p2_move": "rock", "expected_result": "opponent_wins"},
        {"p1_move": "scissors", "p2_move": "paper", "expected_result": "creator_wins"},
        {"p1_move": "scissors", "p2_move": "scissors", "expected_result": "draw"}
    ]
    
    # We'll use Ruby gems for all tests
    bet_gems = {"Ruby": 1}
    
    all_passed = True
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_case['p1_move']} vs {test_case['p2_move']} (Expected: {test_case['expected_result']})")
        
        # Make sure player 1 has enough gems
        test_buy_gems(player1_token, "player1", "Ruby", 10)
        
        # Make sure player 2 has enough gems
        test_buy_gems(player2_token, "player2", "Ruby", 10)
        
        # Player 1 creates a game
        game_id = test_create_game(player1_token, "player1", test_case["p1_move"], bet_gems)
        
        if not game_id:
            print_error("Failed to create game")
            all_passed = False
            continue
        
        # Player 2 joins the game
        result = test_join_game(player2_token, "player2", game_id, test_case["p2_move"])
        
        if not result:
            print_error("Failed to join game")
            all_passed = False
            continue
        
        # Check if the result matches the expected result
        if result["result"] == test_case["expected_result"]:
            print_success(f"Game result matches expected result: {result['result']}")
        else:
            print_error(f"Game result does not match expected result. Expected: {test_case['expected_result']}, Got: {result['result']}")
            all_passed = False
    
    if all_passed:
        record_test("Rock-Paper-Scissors Logic", True)
    else:
        record_test("Rock-Paper-Scissors Logic", False, "Some test cases failed")

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

def test_pvp_game_mechanics() -> None:
    """Test PvP game mechanics."""
    print_header("TESTING PVP GAME MECHANICS")
    
    # Register and verify player 1
    token1, email1, username1 = test_user_registration(TEST_USERS[0])
    test_email_verification(token1, username1)
    player1_token = test_login(email1, TEST_USERS[0]["password"], username1)
    
    # Register and verify player 2
    token2, email2, username2 = test_user_registration(TEST_USERS[1])
    test_email_verification(token2, username2)
    player2_token = test_login(email2, TEST_USERS[1]["password"], username2)
    
    if not player1_token or not player2_token:
        print_error("Failed to set up test users")
        return
    
    # Buy gems for both players
    test_buy_gems(player1_token, username1, "Ruby", 20)
    test_buy_gems(player1_token, username1, "Emerald", 10)
    test_buy_gems(player2_token, username2, "Ruby", 20)
    test_buy_gems(player2_token, username2, "Emerald", 10)
    
    # Get initial gem inventory for both players
    player1_gems = test_get_user_gems(player1_token, username1)
    player2_gems = test_get_user_gems(player2_token, username2)
    
    # Test 1: Create a game with valid data
    bet_gems = {"Ruby": 5, "Emerald": 2}
    game_id = test_create_game(player1_token, username1, "rock", bet_gems)
    
    # Test 2: Validation - Try to create a game with insufficient gems
    test_create_game_validation(player1_token, username1, "rock", {"Ruby": 100}, "Insufficient Ruby gems")
    
    # Test 3: Validation - Try to create a game with negative quantity
    test_create_game_validation(player1_token, username1, "rock", {"Ruby": -5}, "Invalid quantity for Ruby")
    
    # Test 4: Get available games (player 2 should see player 1's game)
    available_games = test_get_available_games(player2_token, username2, game_id)
    
    # Test 5: Validation - Player 1 should not see their own game in available games
    player1_available_games = test_get_available_games(player1_token, username1)
    own_game_visible = False
    for game in player1_available_games:
        if game["game_id"] == game_id:
            own_game_visible = True
            break
    
    if not own_game_visible:
        print_success("Player's own game is correctly not visible in available games")
        record_test("Own Game Not Visible", True)
    else:
        print_error("Player's own game is incorrectly visible in available games")
        record_test("Own Game Not Visible", False, "Own game is visible")
    
    # Test 6: Validation - Player 1 cannot join their own game
    test_join_game_validation(player1_token, username1, game_id, "paper", "Cannot join your own game")
    
    # Test 7: Player 2 joins the game
    game_result = test_join_game(player2_token, username2, game_id, "paper")
    
    # Test 8: Verify game result (paper beats rock, so player 2 should win)
    if game_result.get("result") == "opponent_wins":
        print_success("Game result is correct: opponent_wins (paper beats rock)")
        record_test("Game Result Verification", True)
    else:
        print_error(f"Game result is incorrect: {game_result.get('result')} (expected: opponent_wins)")
        record_test("Game Result Verification", False, f"Incorrect result: {game_result.get('result')}")
    
    # Test 9: Verify gem distribution after game
    test_get_user_gems_after_game(player1_token, username1, player1_gems, False, bet_gems)
    test_get_user_gems_after_game(player2_token, username2, player2_gems, True, bet_gems)
    
    # Test 10: Test all rock-paper-scissors combinations
    test_rock_paper_scissors_logic(player1_token, player2_token)

def run_all_tests() -> None:
    """Run all tests in sequence."""
    print_header("GEMPLAY PVP API TESTING")
    
    # Test PvP game mechanics
    test_pvp_game_mechanics()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_all_tests()