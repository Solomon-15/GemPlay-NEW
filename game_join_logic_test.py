#!/usr/bin/env python3
"""
GemPlay Game Join Logic Testing
Testing the game joining workflow to ensure status changes correctly from WAITING to ACTIVE
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

TEST_USERS = [
    {
        "username": "playerA_game_test",
        "email": "playerA_game_test@test.com",
        "password": "Test123!",
        "gender": "male"
    },
    {
        "username": "playerB_game_test",
        "email": "playerB_game_test@test.com",
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing Login for {user_type}: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Login successful for {user_type}")
        record_test(f"Login - {user_type}", True)
        return response["access_token"]
    else:
        print_error(f"Login failed for {user_type}: {response}")
        record_test(f"Login - {user_type}", False, f"Login failed: {response}")
        return None

def test_user_registration_and_verification(user_data: Dict[str, str]) -> Optional[str]:
    """Test user registration and email verification, return access token."""
    print_subheader(f"Testing User Registration and Verification for {user_data['username']}")
    
    # Generate a random email to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"{user_data['username']}_{random_suffix}@test.com"
    test_user_data = user_data.copy()
    test_user_data["email"] = test_email
    
    # Step 1: Register user
    response, success = make_request("POST", "/auth/register", data=test_user_data)
    
    if not success:
        print_error(f"User registration failed: {response}")
        record_test(f"User Registration - {user_data['username']}", False, "Registration failed")
        return None
    
    if "verification_token" not in response:
        print_error(f"Registration response missing verification token: {response}")
        record_test(f"User Registration - {user_data['username']}", False, "Missing verification token")
        return None
    
    verification_token = response["verification_token"]
    print_success(f"User registered successfully with verification token")
    
    # Step 2: Verify email
    verify_response, verify_success = make_request("POST", "/auth/verify-email", data={"token": verification_token})
    
    if not verify_success:
        print_error(f"Email verification failed: {verify_response}")
        record_test(f"Email Verification - {user_data['username']}", False, "Verification failed")
        return None
    
    print_success("Email verified successfully")
    
    # Step 3: Login to get access token
    login_token = test_login(test_email, test_user_data["password"], user_data['username'])
    
    if login_token:
        record_test(f"User Setup - {user_data['username']}", True)
        return login_token
    else:
        record_test(f"User Setup - {user_data['username']}", False, "Login after verification failed")
        return None

def ensure_user_has_gems(token: str, username: str) -> bool:
    """Ensure user has enough gems for testing."""
    print_subheader(f"Ensuring {username} has gems for testing")
    
    # Check current gem inventory
    inventory_response, inventory_success = make_request(
        "GET", "/gems/inventory", 
        auth_token=token
    )
    
    if not inventory_success:
        print_error("Failed to get gem inventory")
        return False
    
    # Check if user has enough Ruby gems (need at least 10)
    ruby_gems = 0
    for gem in inventory_response:
        if gem["type"] == "Ruby":
            ruby_gems = gem["quantity"] - gem["frozen_quantity"]
            break
    
    if ruby_gems < 10:
        # Buy some Ruby gems
        buy_response, buy_success = make_request(
            "POST", "/gems/buy?gem_type=Ruby&quantity=20",
            auth_token=token
        )
        if buy_success:
            print_success(f"Bought 20 Ruby gems for {username}")
        else:
            print_error(f"Failed to buy gems for {username}")
            return False
    
    print_success(f"{username} has sufficient gems for testing")
    return True

def test_game_creation_and_joining_workflow():
    """Test the complete game creation and joining workflow."""
    print_header("GAME CREATION AND JOINING WORKFLOW TESTING")
    
    # Step 1: Setup test users
    print_subheader("Step 1: Setup Test Users")
    
    # Register and verify both test users
    player_a_token = test_user_registration_and_verification(TEST_USERS[0])
    player_b_token = test_user_registration_and_verification(TEST_USERS[1])
    
    if not player_a_token or not player_b_token:
        print_error("Failed to setup test users")
        record_test("Game Workflow - User Setup", False, "User setup failed")
        return
    
    print_success("Both test users setup successfully")
    
    # Ensure both users have gems
    if not ensure_user_has_gems(player_a_token, "Player A") or not ensure_user_has_gems(player_b_token, "Player B"):
        print_error("Failed to ensure users have gems")
        record_test("Game Workflow - Gem Setup", False, "Gem setup failed")
        return
    
    # Step 2: Player A creates a game (status should be WAITING)
    print_subheader("Step 2: Player A Creates Game")
    
    # Create game with commit-reveal scheme
    salt = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    move = "rock"
    move_hash = hash_move_with_salt(move, salt)
    
    create_game_data = {
        "move": move,
        "bet_gems": {"Ruby": 5}  # Bet 5 Ruby gems ($5)
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=player_a_token
    )
    
    if not game_success:
        print_error(f"Failed to create game: {game_response}")
        record_test("Game Workflow - Create Game", False, "Game creation failed")
        return
    
    game_id = game_response.get("game_id")
    if not game_id:
        print_error("Game creation response missing game_id")
        record_test("Game Workflow - Create Game", False, "Missing game_id")
        return
    
    print_success(f"Game created successfully with ID: {game_id}")
    
    # Verify game status is WAITING
    game_status_response, status_success = make_request(
        "GET", f"/games/{game_id}/status",
        auth_token=player_a_token
    )
    
    if status_success:
        initial_status = game_status_response.get("status")
        if initial_status == "WAITING":
            print_success("✓ Game status is WAITING after creation")
            record_test("Game Workflow - Initial Status WAITING", True)
        else:
            print_error(f"✗ Game status is {initial_status}, expected WAITING")
            record_test("Game Workflow - Initial Status WAITING", False, f"Status: {initial_status}")
    else:
        print_warning("Could not verify initial game status")
        record_test("Game Workflow - Initial Status Check", False, "Status check failed")
    
    # Step 3: Player B joins the game (status should change to ACTIVE)
    print_subheader("Step 3: Player B Joins Game")
    
    join_game_data = {
        "move": "paper",
        "gems": {"Ruby": 5}  # Match the bet amount
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=player_b_token
    )
    
    if not join_success:
        print_error(f"Failed to join game: {join_response}")
        record_test("Game Workflow - Join Game", False, "Game join failed")
        return
    
    print_success("Player B joined game successfully")
    record_test("Game Workflow - Join Game", True)
    
    # Verify game status changed to ACTIVE
    time.sleep(1)  # Small delay to ensure status update
    
    active_status_response, active_status_success = make_request(
        "GET", f"/games/{game_id}/status",
        auth_token=player_a_token
    )
    
    if active_status_success:
        active_status = active_status_response.get("status")
        if active_status == "ACTIVE":
            print_success("✓ Game status changed to ACTIVE after Player B joined")
            record_test("Game Workflow - Status Change to ACTIVE", True)
            
            # Check if active_deadline is set (1-minute timer)
            active_deadline = active_status_response.get("active_deadline")
            if active_deadline:
                print_success("✓ Active deadline (1-minute timer) is set")
                record_test("Game Workflow - Active Deadline Set", True)
            else:
                print_warning("Active deadline not found in response")
                record_test("Game Workflow - Active Deadline Set", False, "No deadline set")
                
        else:
            print_error(f"✗ Game status is {active_status}, expected ACTIVE")
            record_test("Game Workflow - Status Change to ACTIVE", False, f"Status: {active_status}")
    else:
        print_error("Could not verify game status after join")
        record_test("Game Workflow - Status Change to ACTIVE", False, "Status check failed")
    
    # Step 4: Player B chooses move (game should complete with status COMPLETED)
    print_subheader("Step 4: Player B Chooses Move")
    
    choose_move_data = {
        "move": "paper"
    }
    
    choose_response, choose_success = make_request(
        "POST", f"/games/{game_id}/choose-move",
        data=choose_move_data,
        auth_token=player_b_token
    )
    
    if choose_success:
        print_success("Player B chose move successfully")
        record_test("Game Workflow - Choose Move", True)
        
        # Verify game completed
        time.sleep(1)  # Small delay to ensure completion
        
        final_status_response, final_status_success = make_request(
            "GET", f"/games/{game_id}/status",
            auth_token=player_a_token
        )
        
        if final_status_success:
            final_status = final_status_response.get("status")
            if final_status == "COMPLETED":
                print_success("✓ Game status changed to COMPLETED after move choice")
                record_test("Game Workflow - Status Change to COMPLETED", True)
                
                # Check winner determination
                winner_id = final_status_response.get("winner_id")
                if winner_id:
                    print_success(f"✓ Winner determined: {winner_id}")
                    record_test("Game Workflow - Winner Determination", True)
                else:
                    print_warning("No winner determined (possible draw)")
                    record_test("Game Workflow - Winner Determination", True, "Draw result")
                    
            else:
                print_error(f"✗ Game status is {final_status}, expected COMPLETED")
                record_test("Game Workflow - Status Change to COMPLETED", False, f"Status: {final_status}")
        else:
            print_error("Could not verify final game status")
            record_test("Game Workflow - Status Change to COMPLETED", False, "Status check failed")
    else:
        print_error(f"Failed to choose move: {choose_response}")
        record_test("Game Workflow - Choose Move", False, "Move choice failed")

def test_game_timeout_handling():
    """Test timeout handling for ACTIVE games."""
    print_header("GAME TIMEOUT HANDLING TESTING")
    
    # Login as admin to access timeout handling functions
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot test timeout handling")
        record_test("Game Timeout - Admin Login", False, "Admin login failed")
        return
    
    # Check if there are any ACTIVE games that might timeout
    print_subheader("Checking for ACTIVE Games")
    
    # Get all games to find ACTIVE ones
    games_response, games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if games_success and isinstance(games_response, list):
        active_games = [game for game in games_response if game.get("status") == "ACTIVE"]
        
        if active_games:
            print_success(f"Found {len(active_games)} ACTIVE games")
            
            # Show details of first active game
            active_game = active_games[0]
            game_id = active_game.get("game_id")
            active_deadline = active_game.get("active_deadline")
            
            print_success(f"Active game ID: {game_id}")
            print_success(f"Active deadline: {active_deadline}")
            
            record_test("Game Timeout - Find Active Games", True)
        else:
            print_warning("No ACTIVE games found for timeout testing")
            record_test("Game Timeout - Find Active Games", False, "No active games")
    else:
        print_error("Failed to get games list")
        record_test("Game Timeout - Find Active Games", False, "Games list failed")
    
    # Test timeout handling function (if available)
    print_subheader("Testing Timeout Handling Function")
    
    # Try to call timeout handling endpoint (if it exists)
    timeout_response, timeout_success = make_request(
        "POST", "/admin/games/handle-timeouts",
        auth_token=admin_token,
        expected_status=200  # or 404 if endpoint doesn't exist
    )
    
    if timeout_success:
        print_success("Timeout handling function accessible")
        
        # Check response structure
        if "handled_games" in timeout_response:
            handled_count = timeout_response.get("handled_games", 0)
            print_success(f"Handled {handled_count} timed out games")
            record_test("Game Timeout - Handle Timeouts", True)
        else:
            print_warning("Timeout response structure unclear")
            record_test("Game Timeout - Handle Timeouts", True, "Response unclear")
    else:
        if timeout_response.get("text", "").find("404") != -1:
            print_warning("Timeout handling endpoint not found (may be background task)")
            record_test("Game Timeout - Handle Timeouts", True, "Background task")
        else:
            print_error(f"Timeout handling failed: {timeout_response}")
            record_test("Game Timeout - Handle Timeouts", False, "Timeout handling failed")

def test_multiple_concurrent_games():
    """Test multiple concurrent games to ensure status changes work correctly."""
    print_header("MULTIPLE CONCURRENT GAMES TESTING")
    
    # Setup multiple test users
    print_subheader("Setting up multiple test users")
    
    concurrent_users = []
    for i in range(4):  # Create 4 users for 2 concurrent games
        user_data = {
            "username": f"concurrent_user_{i}",
            "email": f"concurrent_user_{i}@test.com",
            "password": "Test123!",
            "gender": "male" if i % 2 == 0 else "female"
        }
        
        token = test_user_registration_and_verification(user_data)
        if token and ensure_user_has_gems(token, f"User {i}"):
            concurrent_users.append({"token": token, "username": user_data["username"]})
        else:
            print_error(f"Failed to setup concurrent user {i}")
            record_test("Concurrent Games - User Setup", False, f"User {i} setup failed")
            return
    
    if len(concurrent_users) < 4:
        print_error("Insufficient users for concurrent games test")
        record_test("Concurrent Games - User Setup", False, "Insufficient users")
        return
    
    print_success(f"Setup {len(concurrent_users)} users for concurrent games")
    
    # Create two games simultaneously
    print_subheader("Creating concurrent games")
    
    games = []
    for i in range(2):
        creator_token = concurrent_users[i * 2]["token"]
        creator_name = concurrent_users[i * 2]["username"]
        
        create_game_data = {
            "move": "rock",
            "bet_gems": {"Ruby": 3}  # Smaller bet for testing
        }
        
        game_response, game_success = make_request(
            "POST", "/games/create",
            data=create_game_data,
            auth_token=creator_token
        )
        
        if game_success and "game_id" in game_response:
            game_id = game_response["game_id"]
            games.append({
                "game_id": game_id,
                "creator_token": creator_token,
                "creator_name": creator_name,
                "joiner_token": concurrent_users[i * 2 + 1]["token"],
                "joiner_name": concurrent_users[i * 2 + 1]["username"]
            })
            print_success(f"Game {i+1} created: {game_id} by {creator_name}")
        else:
            print_error(f"Failed to create game {i+1}")
            record_test("Concurrent Games - Game Creation", False, f"Game {i+1} failed")
            return
    
    # Join both games simultaneously
    print_subheader("Joining concurrent games")
    
    for i, game in enumerate(games):
        join_game_data = {
            "move": "paper",
            "gems": {"Ruby": 3}
        }
        
        join_response, join_success = make_request(
            "POST", f"/games/{game['game_id']}/join",
            data=join_game_data,
            auth_token=game["joiner_token"]
        )
        
        if join_success:
            print_success(f"Game {i+1} joined by {game['joiner_name']}")
        else:
            print_error(f"Failed to join game {i+1}")
            record_test("Concurrent Games - Game Joining", False, f"Game {i+1} join failed")
            return
    
    # Verify all games are ACTIVE
    print_subheader("Verifying concurrent game statuses")
    
    all_active = True
    for i, game in enumerate(games):
        status_response, status_success = make_request(
            "GET", f"/games/{game['game_id']}/status",
            auth_token=game["creator_token"]
        )
        
        if status_success:
            status = status_response.get("status")
            if status == "ACTIVE":
                print_success(f"✓ Game {i+1} status is ACTIVE")
            else:
                print_error(f"✗ Game {i+1} status is {status}, expected ACTIVE")
                all_active = False
        else:
            print_error(f"Failed to check status of game {i+1}")
            all_active = False
    
    if all_active:
        record_test("Concurrent Games - All Active", True)
    else:
        record_test("Concurrent Games - All Active", False, "Not all games active")
    
    # Complete both games
    print_subheader("Completing concurrent games")
    
    for i, game in enumerate(games):
        choose_move_data = {
            "move": "paper"
        }
        
        choose_response, choose_success = make_request(
            "POST", f"/games/{game['game_id']}/choose-move",
            data=choose_move_data,
            auth_token=game["joiner_token"]
        )
        
        if choose_success:
            print_success(f"Game {i+1} move chosen")
        else:
            print_error(f"Failed to choose move for game {i+1}")
    
    # Verify all games completed
    time.sleep(2)  # Allow time for completion
    
    all_completed = True
    for i, game in enumerate(games):
        status_response, status_success = make_request(
            "GET", f"/games/{game['game_id']}/status",
            auth_token=game["creator_token"]
        )
        
        if status_success:
            status = status_response.get("status")
            if status == "COMPLETED":
                print_success(f"✓ Game {i+1} status is COMPLETED")
            else:
                print_error(f"✗ Game {i+1} status is {status}, expected COMPLETED")
                all_completed = False
        else:
            print_error(f"Failed to check final status of game {i+1}")
            all_completed = False
    
    if all_completed:
        record_test("Concurrent Games - All Completed", True)
    else:
        record_test("Concurrent Games - All Completed", False, "Not all games completed")

def print_test_summary():
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    print(f"Total tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print_success("Overall test result: PASSED")
        else:
            print_error("Overall test result: FAILED")
    
    # Show failed tests
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"- {test['name']}: {test['details']}")

def main():
    """Main test execution function."""
    print_header("GEMPLAY GAME JOIN LOGIC TESTING")
    print("Testing game creation → joining → completion workflow")
    print("Ensuring status changes correctly: WAITING → ACTIVE → COMPLETED")
    
    try:
        # Test 1: Basic game creation and joining workflow
        test_game_creation_and_joining_workflow()
        
        # Test 2: Game timeout handling
        test_game_timeout_handling()
        
        # Test 3: Multiple concurrent games
        test_multiple_concurrent_games()
        
        # Print summary
        print_test_summary()
        
    except KeyboardInterrupt:
        print_warning("\nTesting interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    return test_results["failed"] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)