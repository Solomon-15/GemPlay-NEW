#!/usr/bin/env python3
"""
Bot Game Commission Logic Testing
Focus: Test Regular Bot games without commission and Human vs Human games with commission
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib

# Configuration
BASE_URL = "https://cc691930-a6c0-47a7-8521-266c2a4eb979.preview.emergentagent.com/api"
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

def hash_move_with_salt(move: str, salt: str) -> str:
    """Hash game move with salt for commit-reveal scheme."""
    combined = f"{move}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def login_admin() -> Optional[str]:
    """Login as admin and return access token."""
    print_subheader("Admin Login")
    
    response, success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and "access_token" in response:
        print_success("Admin login successful")
        return response["access_token"]
    else:
        print_error("Admin login failed")
        return None

def create_test_user(username: str, email: str) -> Tuple[Optional[str], Optional[str]]:
    """Create a test user and return user_id and access_token."""
    print_subheader(f"Creating Test User: {username}")
    
    # Generate random suffix to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    test_email = f"{username}_{random_suffix}@test.com"
    test_username = f"{username}_{random_suffix}"
    
    user_data = {
        "username": test_username,
        "email": test_email,
        "password": "Test123!",
        "gender": "male"
    }
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if not success:
        print_error(f"Failed to register user {test_username}")
        return None, None
    
    user_id = response.get("user_id")
    verification_token = response.get("verification_token")
    
    if not user_id or not verification_token:
        print_error("Missing user_id or verification_token in registration response")
        return None, None
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST", "/auth/verify-email", 
        data={"token": verification_token}
    )
    
    if not verify_success:
        print_error(f"Failed to verify email for user {test_username}")
        return None, None
    
    # Login user
    login_response, login_success = make_request(
        "POST", "/auth/login", 
        data={"email": test_email, "password": "Test123!"}
    )
    
    if not login_success or "access_token" not in login_response:
        print_error(f"Failed to login user {test_username}")
        return None, None
    
    print_success(f"Test user {test_username} created and logged in successfully")
    return user_id, login_response["access_token"]

def get_user_balance(token: str) -> Dict[str, float]:
    """Get user's balance information."""
    response, success = make_request("GET", "/economy/balance", auth_token=token)
    
    if success:
        return {
            "virtual_balance": response.get("virtual_balance", 0),
            "frozen_balance": response.get("frozen_balance", 0),
            "available_balance": response.get("available_balance", 0)
        }
    return {"virtual_balance": 0, "frozen_balance": 0, "available_balance": 0}

def test_bot_games_available():
    """Test if there are any bot games available to join."""
    print_header("TESTING AVAILABLE BOT GAMES")
    
    # Create test user
    user_id, user_token = create_test_user("botgametest", "botgametest@test.com")
    if not user_id or not user_token:
        record_test("Test User Creation for Bot Games", False, "Failed to create test user")
        return
    
    record_test("Test User Creation for Bot Games", True, "Successfully created test user")
    
    # Get available bot games
    print_subheader("Getting Available Bot Games")
    bot_games_response, bot_games_success = make_request(
        "GET", "/bots/active-games",
        auth_token=user_token
    )
    
    if not bot_games_success:
        record_test("Get Available Bot Games", False, "Failed to get available bot games")
        return
    
    record_test("Get Available Bot Games", True, "Successfully retrieved available bot games")
    
    # Check if there are any games available
    available_games = bot_games_response if isinstance(bot_games_response, list) else bot_games_response.get("games", [])
    if not available_games:
        print_warning("No bot games available for testing")
        record_test("Bot Games Available", False, "No bot games available to test")
        return
    
    record_test("Bot Games Available", True, f"Found {len(available_games)} bot games available")
    
    # Test joining the first available bot game
    target_game = available_games[0]
    game_id = target_game.get("id")
    bet_amount = target_game.get("bet_amount", 20)
    
    print_subheader(f"Testing Bot Game Join - Game ID: {game_id}")
    print(f"Target game details: {target_game}")
    
    # Get balance before joining
    balance_before_join = get_user_balance(user_token)
    print(f"Balance before join: {balance_before_join}")
    
    # Try to join the bot game
    join_data = {
        "move": "rock",
        "gems": {"Ruby": 10, "Emerald": 1}  # Standard bet
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_data,
        auth_token=user_token
    )
    
    if not join_success:
        error_detail = join_response.get("detail", "Unknown error")
        if "Failed to determine game winner" in str(error_detail):
            record_test("Bot Game Join - Winner Determination Fix", False, 
                       "CRITICAL: 'Failed to determine game winner' error still occurs")
            print_error("🚨 CRITICAL ISSUE: The bot game winner determination logic is still broken!")
        else:
            record_test("Bot Game Join - General Error", False, f"Bot game join failed: {error_detail}")
        return
    
    record_test("Bot Game Join - Winner Determination Fix", True, 
               "Successfully joined bot game without 'Failed to determine game winner' error")
    
    # Check if this is a Regular Bot game (should have no commission)
    is_regular_bot_game = target_game.get("bot_type") == "REGULAR" or target_game.get("is_regular_bot_game", False)
    
    if is_regular_bot_game:
        print_subheader("Testing Regular Bot Commission Logic")
        
        # Get balance after game completion
        balance_after_game = get_user_balance(user_token)
        print(f"Balance after game: {balance_after_game}")
        
        # For Regular Bot games, there should be NO commission
        if balance_after_game["frozen_balance"] == 0:
            record_test("Regular Bot Game - No Commission Frozen", True, 
                       "Regular Bot game correctly has no frozen commission")
            print_success("✓ Regular Bot game has no commission frozen (as expected)")
        else:
            record_test("Regular Bot Game - No Commission Frozen", False, 
                       f"Regular Bot game incorrectly has frozen commission: ${balance_after_game['frozen_balance']}")
            print_error(f"✗ Regular Bot game has frozen commission: ${balance_after_game['frozen_balance']} (should be 0)")
        
        # Verify commission_amount is 0 for Regular Bot games
        commission_amount = join_response.get("commission_amount", None)
        if commission_amount is not None and commission_amount == 0:
            record_test("Regular Bot Game - Zero Commission Amount", True, 
                       "Regular Bot game correctly has commission_amount = 0")
            print_success("✓ Regular Bot game has commission_amount = 0 (as expected)")
        elif commission_amount is not None and commission_amount > 0:
            record_test("Regular Bot Game - Zero Commission Amount", False, 
                       f"Regular Bot game incorrectly has commission_amount = {commission_amount}")
            print_error(f"✗ Regular Bot game has commission_amount = {commission_amount} (should be 0)")
        else:
            record_test("Regular Bot Game - Zero Commission Amount", False, 
                       "commission_amount field missing from response")
    
    # Check game completion
    if join_response.get("status") == "COMPLETED":
        record_test("Bot Game Full Cycle", True, 
                   "Successfully completed full bot game cycle")
        print_success("✓ Bot game completed successfully")
        
        # Print game result details
        result = join_response.get("result")
        winner_id = join_response.get("winner_id")
        creator_move = join_response.get("creator_move")
        opponent_move = join_response.get("opponent_move")
        
        print(f"Game result: {result}")
        print(f"Creator move: {creator_move}, Opponent move: {opponent_move}")
        print(f"Winner ID: {winner_id}")
        
    else:
        record_test("Bot Game Completion", False, 
                   f"Game did not complete immediately, status: {join_response.get('status')}")
        print_warning(f"Game status after join: {join_response.get('status')} (expected: COMPLETED)")

def test_human_vs_human_commission():
    """Test that Human vs Human games still have commission."""
    print_header("TESTING HUMAN VS HUMAN COMMISSION LOGIC")
    
    # Create two test users
    user1_id, user1_token = create_test_user("human1", "human1@test.com")
    user2_id, user2_token = create_test_user("human2", "human2@test.com")
    
    if not user1_id or not user1_token or not user2_id or not user2_token:
        record_test("Human Players Creation", False, "Failed to create human test players")
        return
    
    record_test("Human Players Creation", True, "Successfully created human test players")
    
    # Get initial balances
    user1_balance = get_user_balance(user1_token)
    user2_balance = get_user_balance(user2_token)
    
    print(f"User1 initial balance: {user1_balance}")
    print(f"User2 initial balance: {user2_balance}")
    
    # User1 creates a game
    print_subheader("User1 Creates Human vs Human Game")
    
    create_game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 10, "Emerald": 1}  # $20 total bet
    }
    
    create_response, create_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=user1_token
    )
    
    if not create_success:
        record_test("Human Game Creation", False, "Failed to create human vs human game")
        return
    
    game_id = create_response.get("game_id")
    if not game_id:
        record_test("Human Game Creation", False, "No game_id in create response")
        return
    
    record_test("Human Game Creation", True, "Successfully created human vs human game")
    
    # Check that commission is frozen for User1 (6% of $20 = $1.20)
    user1_balance_after_create = get_user_balance(user1_token)
    expected_commission = 20 * 0.06  # 6% of $20
    
    if abs(user1_balance_after_create["frozen_balance"] - expected_commission) < 0.01:
        record_test("Human Game - Commission Frozen on Create", True, 
                   f"Correctly froze ${expected_commission} commission for human game")
        print_success(f"✓ Human game correctly froze ${expected_commission} commission")
    else:
        record_test("Human Game - Commission Frozen on Create", False, 
                   f"Expected ${expected_commission} frozen, got ${user1_balance_after_create['frozen_balance']}")
        print_error(f"✗ Expected ${expected_commission} frozen, got ${user1_balance_after_create['frozen_balance']}")
    
    # User2 joins the game
    print_subheader("User2 Joins Human vs Human Game")
    
    join_game_data = {
        "move": "scissors",
        "gems": {"Ruby": 10, "Emerald": 1}  # Same bet
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=user2_token
    )
    
    if not join_success:
        record_test("Human Game Join", False, "Failed to join human vs human game")
        return
    
    record_test("Human Game Join", True, "Successfully joined human vs human game")
    
    # Check final balances and commission handling
    user1_final_balance = get_user_balance(user1_token)
    user2_final_balance = get_user_balance(user2_token)
    
    print(f"User1 final balance: {user1_final_balance}")
    print(f"User2 final balance: {user2_final_balance}")
    
    # Verify commission was processed (should be unfrozen and either returned to loser or taken as profit)
    if user1_final_balance["frozen_balance"] == 0 and user2_final_balance["frozen_balance"] == 0:
        record_test("Human Game - Commission Processing", True, 
                   "Commission correctly processed (unfrozen) for human vs human game")
        print_success("✓ Human vs human game correctly processed commission")
    else:
        record_test("Human Game - Commission Processing", False, 
                   "Commission not properly processed for human vs human game")
        print_error("✗ Commission not properly processed for human vs human game")
    
    # Check game result
    result = join_response.get("result")
    winner_id = join_response.get("winner_id")
    commission_amount = join_response.get("commission_amount", 0)
    
    print(f"Game result: {result}, Winner: {winner_id}, Commission: ${commission_amount}")
    
    # For human vs human games, commission should be > 0
    if commission_amount > 0:
        record_test("Human Game - Commission Amount", True, 
                   f"Human vs human game correctly has commission_amount = ${commission_amount}")
        print_success(f"✓ Human vs human game has commission_amount = ${commission_amount} (as expected)")
    else:
        record_test("Human Game - Commission Amount", False, 
                   "Human vs human game incorrectly has commission_amount = 0")
        print_error("✗ Human vs human game has commission_amount = 0 (should be > 0)")

def print_test_summary():
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results['failed'] > 0:
        print_subheader("Failed Tests:")
        for test in test_results['tests']:
            if not test['passed']:
                print_error(f"{test['name']}: {test['details']}")
    
    print_subheader("Critical Issues Found:")
    
    critical_issues = []
    for test in test_results['tests']:
        if not test['passed']:
            if "Failed to determine game winner" in test['details']:
                critical_issues.append("🚨 CRITICAL: Bot games still failing with 'Failed to determine game winner' error")
            elif "commission" in test['name'].lower() and "regular bot" in test['name'].lower():
                critical_issues.append("⚠️  IMPORTANT: Regular Bot commission logic not working correctly")
            elif "commission" in test['name'].lower() and "human" in test['name'].lower():
                critical_issues.append("⚠️  IMPORTANT: Human vs Human commission logic broken")
    
    if critical_issues:
        for issue in critical_issues:
            print(issue)
    else:
        print_success("No critical issues found! All bot game and commission logic working correctly.")
    
    # Calculate success rate
    success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print_success("EXCELLENT: Bot game commission logic is working correctly!")
    elif success_rate >= 70:
        print_warning("GOOD: Most functionality working, minor issues found")
    else:
        print_error("POOR: Significant issues found that need immediate attention")

def main():
    """Main test execution."""
    print_header("BOT GAME COMMISSION LOGIC TESTING")
    print("Testing the fixes for:")
    print("1. 'Failed to determine game winner' error in bot games")
    print("2. Regular Bot games should work WITHOUT commission")
    print("3. Human vs Human games should work WITH commission")
    print("4. Full game cycle testing")
    
    try:
        # Test available bot games (main focus)
        test_bot_games_available()
        
        # Test Human vs Human commission logic (verification)
        test_human_vs_human_commission()
        
    except KeyboardInterrupt:
        print_warning("\nTesting interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print_test_summary()

if __name__ == "__main__":
    main()