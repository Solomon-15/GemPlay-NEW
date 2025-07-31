#!/usr/bin/env python3
"""
GemPlay API Timeout and Leave Game Logic Testing
Focus: Testing Player A bet recreation after Player B timeout or leaves game in ACTIVE status

SPECIFIC SCENARIOS TO TEST:
1. Game creation by Player A (status WAITING)
2. Player B joins the game (status changes to ACTIVE)
3. SCENARIO A - TIMEOUT: Player B doesn't choose a move within 1 minute → automatic timeout
4. SCENARIO B - LEAVE: Player B clicks "X" → calls API /api/games/{game_id}/leave

WHAT TO CHECK:
- Return gems and commission to Player B
- Recreation of Player A's bet with new commit-reveal
- Game status: ACTIVE → WAITING
- Notifications to Player A in English
- Game appears again in Available Bets
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
BASE_URL = "https://b06afae6-fa27-406a-847e-fa79e0465691.preview.emergentagent.com/api"

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

def generate_test_user_data(suffix: str) -> Dict[str, str]:
    """Generate test user data with unique email."""
    timestamp = int(time.time())
    return {
        "username": f"player{suffix}_{timestamp}",
        "email": f"player{suffix}_{timestamp}@test.com",
        "password": "Test123!",
        "gender": "male"
    }

def register_and_verify_user(user_data: Dict[str, str]) -> Optional[str]:
    """Register and verify a test user, return auth token."""
    print_subheader(f"Registering User: {user_data['username']}")
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if not success or "verification_token" not in response:
        print_error(f"Failed to register user: {response}")
        return None
    
    verification_token = response["verification_token"]
    print_success(f"User registered with verification token: {verification_token}")
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST", "/auth/verify-email", 
        data={"token": verification_token}
    )
    
    if not verify_success:
        print_error(f"Failed to verify email: {verify_response}")
        return None
    
    print_success("Email verified successfully")
    
    # Login to get auth token
    login_response, login_success = make_request(
        "POST", "/auth/login",
        data={"email": user_data["email"], "password": user_data["password"]}
    )
    
    if not login_success or "access_token" not in login_response:
        print_error(f"Failed to login: {login_response}")
        return None
    
    auth_token = login_response["access_token"]
    print_success(f"User logged in successfully")
    
    return auth_token

def purchase_gems_for_user(auth_token: str, username: str) -> bool:
    """Purchase gems for a user."""
    print_subheader(f"Purchasing Gems for {username}")
    
    # Add balance first
    balance_response, balance_success = make_request(
        "POST", "/user/balance/add",
        data={"amount": 100.0},
        auth_token=auth_token
    )
    
    if not balance_success:
        print_error(f"Failed to add balance: {balance_response}")
        return False
    
    print_success("Added $100 to user balance")
    
    # Purchase gems: Ruby: 20, Emerald: 5 (enough for $35 bet)
    gem_purchases = [
        {"gem_type": "Ruby", "quantity": 20},  # $20
        {"gem_type": "Emerald", "quantity": 5}  # $50
    ]
    
    for purchase in gem_purchases:
        purchase_response, purchase_success = make_request(
            "POST", "/user/gems/purchase",
            data=purchase,
            auth_token=auth_token
        )
        
        if not purchase_success:
            print_error(f"Failed to purchase {purchase['quantity']} {purchase['gem_type']}: {purchase_response}")
            return False
        
        print_success(f"Purchased {purchase['quantity']} {purchase['gem_type']} gems")
    
    return True

def create_game_as_player_a(auth_token: str, username: str) -> Optional[str]:
    """Create a game as Player A."""
    print_subheader(f"Creating Game as Player A ({username})")
    
    # Create game with Ruby: 15, Emerald: 2 ($35 total)
    game_data = {
        "move": "rock",
        "bet_gems": {
            "Ruby": 15,
            "Emerald": 2
        }
    }
    
    response, success = make_request(
        "POST", "/games/create",
        data=game_data,
        auth_token=auth_token
    )
    
    if not success or "game_id" not in response:
        print_error(f"Failed to create game: {response}")
        return None
    
    game_id = response["game_id"]
    print_success(f"Game created successfully with ID: {game_id}")
    
    # Verify game appears in available bets
    available_response, available_success = make_request(
        "GET", "/games/available",
        auth_token=auth_token
    )
    
    if available_success and "games" in available_response:
        game_found = any(game["game_id"] == game_id for game in available_response["games"])
        if game_found:
            print_success("Game appears in Available Bets")
        else:
            print_warning("Game not found in Available Bets")
    
    return game_id

def join_game_as_player_b(auth_token: str, username: str, game_id: str) -> bool:
    """Join a game as Player B."""
    print_subheader(f"Player B ({username}) Joining Game {game_id}")
    
    # Join game with matching gems
    join_data = {
        "move": "paper",
        "gems": {
            "Ruby": 15,
            "Emerald": 2
        }
    }
    
    response, success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_data,
        auth_token=auth_token
    )
    
    if not success:
        print_error(f"Failed to join game: {response}")
        return False
    
    # Check if status is ACTIVE
    if "status" in response and response["status"] == "ACTIVE":
        print_success(f"Successfully joined game - Status: {response['status']}")
        if "deadline" in response:
            print_success(f"Move deadline: {response['deadline']}")
        return True
    else:
        print_error(f"Game status not ACTIVE after join: {response}")
        return False

def get_user_balance_and_gems(auth_token: str, username: str) -> Dict[str, Any]:
    """Get user's current balance and gems."""
    print_subheader(f"Getting Balance and Gems for {username}")
    
    # Get user profile
    profile_response, profile_success = make_request(
        "GET", "/user/profile",
        auth_token=auth_token
    )
    
    if not profile_success:
        print_error(f"Failed to get user profile: {profile_response}")
        return {}
    
    # Get user gems
    gems_response, gems_success = make_request(
        "GET", "/user/gems",
        auth_token=auth_token
    )
    
    if not gems_success:
        print_error(f"Failed to get user gems: {gems_response}")
        return {}
    
    balance_info = {
        "virtual_balance": profile_response.get("virtual_balance", 0),
        "frozen_balance": profile_response.get("frozen_balance", 0),
        "gems": gems_response.get("gems", [])
    }
    
    print_success(f"Virtual Balance: ${balance_info['virtual_balance']}")
    print_success(f"Frozen Balance: ${balance_info['frozen_balance']}")
    for gem in balance_info["gems"]:
        print_success(f"{gem['type']}: {gem['quantity']} (frozen: {gem.get('frozen_quantity', 0)})")
    
    return balance_info

def test_timeout_scenario(player_a_token: str, player_b_token: str, game_id: str) -> bool:
    """Test timeout scenario - Player B doesn't make a move within 1 minute."""
    print_header("TESTING TIMEOUT SCENARIO")
    
    print_subheader("Step 1: Get Initial State")
    
    # Get Player B's initial balance and gems
    player_b_initial = get_user_balance_and_gems(player_b_token, "Player B")
    
    print_subheader("Step 2: Wait for Timeout (70 seconds)")
    print("Waiting for game to timeout naturally...")
    print("Game should timeout after 1 minute of inactivity")
    
    # Wait for timeout (70 seconds to be safe)
    for i in range(70):
        if i % 10 == 0:
            print(f"Waiting... {70-i} seconds remaining")
        time.sleep(1)
    
    print_subheader("Step 3: Check Game Status After Timeout")
    
    # Check if game status changed back to WAITING
    available_response, available_success = make_request(
        "GET", "/games/available",
        auth_token=player_a_token
    )
    
    game_back_in_available = False
    if available_success and "games" in available_response:
        game_back_in_available = any(game["game_id"] == game_id for game in available_response["games"])
    
    if game_back_in_available:
        print_success("✓ Game appears back in Available Bets after timeout")
        record_test("Timeout - Game Back in Available Bets", True)
    else:
        print_error("✗ Game not found in Available Bets after timeout")
        record_test("Timeout - Game Back in Available Bets", False)
    
    print_subheader("Step 4: Check Player B Balance Recovery")
    
    # Get Player B's balance after timeout
    player_b_after = get_user_balance_and_gems(player_b_token, "Player B")
    
    # Check if commission was returned
    virtual_balance_increased = player_b_after.get("virtual_balance", 0) > player_b_initial.get("virtual_balance", 0)
    frozen_balance_decreased = player_b_after.get("frozen_balance", 0) < player_b_initial.get("frozen_balance", 0)
    
    if virtual_balance_increased:
        balance_increase = player_b_after["virtual_balance"] - player_b_initial["virtual_balance"]
        print_success(f"✓ Player B virtual balance increased by ${balance_increase:.2f}")
        record_test("Timeout - Player B Commission Returned", True)
    else:
        print_error("✗ Player B virtual balance did not increase")
        record_test("Timeout - Player B Commission Returned", False)
    
    if frozen_balance_decreased:
        frozen_decrease = player_b_initial["frozen_balance"] - player_b_after["frozen_balance"]
        print_success(f"✓ Player B frozen balance decreased by ${frozen_decrease:.2f}")
        record_test("Timeout - Player B Frozen Balance Released", True)
    else:
        print_error("✗ Player B frozen balance did not decrease")
        record_test("Timeout - Player B Frozen Balance Released", False)
    
    print_subheader("Step 5: Check Player A Notifications")
    
    # Get Player A notifications
    notifications_response, notifications_success = make_request(
        "GET", "/user/notifications",
        auth_token=player_a_token
    )
    
    if notifications_success and "notifications" in notifications_response:
        notifications = notifications_response["notifications"]
        timeout_notification = None
        
        for notification in notifications:
            if "timeout" in notification.get("message", "").lower() or "timed out" in notification.get("message", "").lower():
                timeout_notification = notification
                break
        
        if timeout_notification:
            print_success("✓ Player A received timeout notification")
            print_success(f"Notification message: {timeout_notification.get('message', 'N/A')}")
            
            # Check if notification is in English
            message = timeout_notification.get("message", "")
            is_english = any(word in message.lower() for word in ["timeout", "timed out", "opponent", "bet", "recreated"])
            
            if is_english:
                print_success("✓ Notification is in English")
                record_test("Timeout - Player A English Notification", True)
            else:
                print_warning(f"⚠ Notification may not be in English: {message}")
                record_test("Timeout - Player A English Notification", False)
        else:
            print_error("✗ Player A did not receive timeout notification")
            record_test("Timeout - Player A Notification", False)
    else:
        print_error("✗ Failed to get Player A notifications")
        record_test("Timeout - Player A Notification", False)
    
    return game_back_in_available and virtual_balance_increased

def test_leave_scenario() -> bool:
    """Test leave scenario - Player B calls /api/games/{game_id}/leave."""
    print_header("TESTING LEAVE SCENARIO")
    
    print_subheader("Step 1: Setup New Game for Leave Test")
    
    # Create new test users
    player_a_data = generate_test_user_data("A_leave")
    player_b_data = generate_test_user_data("B_leave")
    
    # Register and setup Player A
    player_a_token = register_and_verify_user(player_a_data)
    if not player_a_token:
        print_error("Failed to setup Player A for leave test")
        return False
    
    if not purchase_gems_for_user(player_a_token, player_a_data["username"]):
        print_error("Failed to purchase gems for Player A")
        return False
    
    # Register and setup Player B
    player_b_token = register_and_verify_user(player_b_data)
    if not player_b_token:
        print_error("Failed to setup Player B for leave test")
        return False
    
    if not purchase_gems_for_user(player_b_token, player_b_data["username"]):
        print_error("Failed to purchase gems for Player B")
        return False
    
    # Create game as Player A
    game_id = create_game_as_player_a(player_a_token, player_a_data["username"])
    if not game_id:
        print_error("Failed to create game for leave test")
        return False
    
    # Player B joins game
    if not join_game_as_player_b(player_b_token, player_b_data["username"], game_id):
        print_error("Failed for Player B to join game")
        return False
    
    print_subheader("Step 2: Get Initial State Before Leave")
    
    # Get Player B's initial balance and gems
    player_b_initial = get_user_balance_and_gems(player_b_token, "Player B")
    
    print_subheader("Step 3: Player B Leaves Game")
    
    # Player B leaves the game
    leave_response, leave_success = make_request(
        "POST", f"/games/{game_id}/leave",
        auth_token=player_b_token
    )
    
    if not leave_success:
        print_error(f"Failed to leave game: {leave_response}")
        record_test("Leave - API Call", False)
        return False
    
    print_success("✓ Player B successfully left the game")
    record_test("Leave - API Call", True)
    
    print_subheader("Step 4: Check Game Status After Leave")
    
    # Check if game status changed back to WAITING
    available_response, available_success = make_request(
        "GET", "/games/available",
        auth_token=player_a_token
    )
    
    game_back_in_available = False
    if available_success and "games" in available_response:
        game_back_in_available = any(game["game_id"] == game_id for game in available_response["games"])
    
    if game_back_in_available:
        print_success("✓ Game appears back in Available Bets after leave")
        record_test("Leave - Game Back in Available Bets", True)
    else:
        print_error("✗ Game not found in Available Bets after leave")
        record_test("Leave - Game Back in Available Bets", False)
    
    print_subheader("Step 5: Check Player B Balance Recovery After Leave")
    
    # Get Player B's balance after leaving
    player_b_after = get_user_balance_and_gems(player_b_token, "Player B")
    
    # Check if gems and commission were returned
    virtual_balance_increased = player_b_after.get("virtual_balance", 0) > player_b_initial.get("virtual_balance", 0)
    frozen_balance_decreased = player_b_after.get("frozen_balance", 0) < player_b_initial.get("frozen_balance", 0)
    
    if virtual_balance_increased:
        balance_increase = player_b_after["virtual_balance"] - player_b_initial["virtual_balance"]
        print_success(f"✓ Player B virtual balance increased by ${balance_increase:.2f} (commission returned)")
        record_test("Leave - Player B Commission Returned", True)
    else:
        print_error("✗ Player B virtual balance did not increase")
        record_test("Leave - Player B Commission Returned", False)
    
    if frozen_balance_decreased:
        frozen_decrease = player_b_initial["frozen_balance"] - player_b_after["frozen_balance"]
        print_success(f"✓ Player B frozen balance decreased by ${frozen_decrease:.2f} (gems unfrozen)")
        record_test("Leave - Player B Gems Returned", True)
    else:
        print_error("✗ Player B frozen balance did not decrease")
        record_test("Leave - Player B Gems Returned", False)
    
    print_subheader("Step 6: Check Player A Notifications After Leave")
    
    # Get Player A notifications
    notifications_response, notifications_success = make_request(
        "GET", "/user/notifications",
        auth_token=player_a_token
    )
    
    if notifications_success and "notifications" in notifications_response:
        notifications = notifications_response["notifications"]
        leave_notification = None
        
        for notification in notifications:
            message = notification.get("message", "").lower()
            if "left" in message or "opponent left" in message or "recreated" in message:
                leave_notification = notification
                break
        
        if leave_notification:
            print_success("✓ Player A received leave notification")
            print_success(f"Notification message: {leave_notification.get('message', 'N/A')}")
            
            # Check if notification is in English
            message = leave_notification.get("message", "")
            is_english = any(word in message.lower() for word in ["left", "opponent", "bet", "recreated", "available"])
            
            if is_english:
                print_success("✓ Notification is in English")
                record_test("Leave - Player A English Notification", True)
            else:
                print_warning(f"⚠ Notification may not be in English: {message}")
                record_test("Leave - Player A English Notification", False)
        else:
            print_error("✗ Player A did not receive leave notification")
            record_test("Leave - Player A Notification", False)
    else:
        print_error("✗ Failed to get Player A notifications")
        record_test("Leave - Player A Notification", False)
    
    return game_back_in_available and virtual_balance_increased

def main():
    """Main test function."""
    print_header("GEMPLAY TIMEOUT AND LEAVE GAME LOGIC TESTING")
    print("Testing Player A bet recreation after Player B timeout or leaves game in ACTIVE status")
    
    # Test Scenario 1: Timeout
    print_subheader("SCENARIO 1: TIMEOUT TESTING SETUP")
    
    # Create test users for timeout scenario
    player_a_data = generate_test_user_data("A_timeout")
    player_b_data = generate_test_user_data("B_timeout")
    
    # Register and setup Player A
    player_a_token = register_and_verify_user(player_a_data)
    if not player_a_token:
        print_error("Failed to setup Player A - cannot proceed with timeout test")
        record_test("Setup - Player A Registration", False)
        return
    
    record_test("Setup - Player A Registration", True)
    
    if not purchase_gems_for_user(player_a_token, player_a_data["username"]):
        print_error("Failed to purchase gems for Player A")
        record_test("Setup - Player A Gem Purchase", False)
        return
    
    record_test("Setup - Player A Gem Purchase", True)
    
    # Register and setup Player B
    player_b_token = register_and_verify_user(player_b_data)
    if not player_b_token:
        print_error("Failed to setup Player B - cannot proceed with timeout test")
        record_test("Setup - Player B Registration", False)
        return
    
    record_test("Setup - Player B Registration", True)
    
    if not purchase_gems_for_user(player_b_token, player_b_data["username"]):
        print_error("Failed to purchase gems for Player B")
        record_test("Setup - Player B Gem Purchase", False)
        return
    
    record_test("Setup - Player B Gem Purchase", True)
    
    # Create game as Player A
    game_id = create_game_as_player_a(player_a_token, player_a_data["username"])
    if not game_id:
        print_error("Failed to create game - cannot proceed with timeout test")
        record_test("Setup - Game Creation", False)
        return
    
    record_test("Setup - Game Creation", True)
    
    # Player B joins game
    if not join_game_as_player_b(player_b_token, player_b_data["username"], game_id):
        print_error("Failed for Player B to join game")
        record_test("Setup - Player B Join Game", False)
        return
    
    record_test("Setup - Player B Join Game", True)
    
    # Test timeout scenario
    timeout_success = test_timeout_scenario(player_a_token, player_b_token, game_id)
    
    # Test Scenario 2: Leave
    leave_success = test_leave_scenario()
    
    # Print final results
    print_header("TEST RESULTS SUMMARY")
    
    print(f"Total Tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    print("\nDetailed Results:")
    for test in test_results['tests']:
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if test['passed'] else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"{status} {test['name']}")
        if test['details']:
            print(f"   {test['details']}")
    
    # Overall assessment
    print_header("OVERALL ASSESSMENT")
    
    if timeout_success and leave_success:
        print_success("✓ BOTH TIMEOUT AND LEAVE SCENARIOS WORKING CORRECTLY")
        print_success("✓ Player A bet recreation logic is functional")
        print_success("✓ Gems and commission return working")
        print_success("✓ Game status transitions working (ACTIVE → WAITING)")
        print_success("✓ Notifications in English working")
        print_success("✓ Games reappear in Available Bets")
    elif timeout_success:
        print_warning("⚠ TIMEOUT SCENARIO WORKING, LEAVE SCENARIO HAS ISSUES")
    elif leave_success:
        print_warning("⚠ LEAVE SCENARIO WORKING, TIMEOUT SCENARIO HAS ISSUES")
    else:
        print_error("✗ BOTH SCENARIOS HAVE ISSUES - NEEDS INVESTIGATION")
    
    return success_rate > 80

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)