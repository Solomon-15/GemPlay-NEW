#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import uuid

# Configuration
BASE_URL = "https://cc691930-a6c0-47a7-8521-266c2a4eb979.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
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

def login_admin() -> Optional[str]:
    """Login as admin and return the auth token."""
    print_subheader("Logging in as Admin")
    
    login_data = {
        "email": ADMIN_CREDENTIALS["email"],
        "password": ADMIN_CREDENTIALS["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success("Admin logged in successfully")
        return response["access_token"]
    else:
        print_error("Admin login failed")
        return None

def test_get_all_bots(admin_token: str) -> List[Dict[str, Any]]:
    """Test GET /api/bots endpoint."""
    print_subheader("Testing GET /api/bots")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/bots", False, "No admin token")
        return []
    
    try:
        response, success = make_request("GET", "/bots", auth_token=admin_token)
        
        if success:
            if isinstance(response, list):
                print_success(f"Successfully retrieved {len(response)} bots")
                record_test("GET /api/bots", True)
                return response
            else:
                print_error("Response is not a list")
                record_test("GET /api/bots", False, "Response is not a list")
        else:
            # If the endpoint returns 500, we'll mark it as a known issue but continue testing
            if response.get("text", "").strip() == "Internal Server Error":
                print_warning("GET /api/bots endpoint returns 500 Internal Server Error - known issue")
                record_test("GET /api/bots", False, "Internal Server Error (known issue)")
            else:
                record_test("GET /api/bots", False, "Request failed")
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        record_test("GET /api/bots", False, f"Exception: {str(e)}")
    
    return []

def test_create_bot(admin_token: str, bot_data: Dict[str, Any]) -> Optional[str]:
    """Test POST /api/bots endpoint."""
    print_subheader("Testing POST /api/bots")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("POST /api/bots", False, "No admin token")
        return None
    
    response, success = make_request("POST", "/bots", data=bot_data, auth_token=admin_token)
    
    if success:
        if "bot_id" in response and "message" in response:
            print_success(f"Bot created successfully with ID: {response['bot_id']}")
            record_test("POST /api/bots", True)
            return response["bot_id"]
        else:
            print_error("Response missing expected fields")
            record_test("POST /api/bots", False, "Response missing expected fields")
    else:
        record_test("POST /api/bots", False, "Request failed")
    
    return None

def test_update_bot(admin_token: str, bot_id: str, update_data: Dict[str, Any]) -> bool:
    """Test PUT /api/bots/{bot_id} endpoint."""
    print_subheader(f"Testing PUT /api/bots/{bot_id}")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"PUT /api/bots/{bot_id}", False, "No admin token")
        return False
    
    response, success = make_request("PUT", f"/bots/{bot_id}", data=update_data, auth_token=admin_token)
    
    if success:
        if "message" in response:
            print_success(f"Bot updated successfully: {response['message']}")
            record_test(f"PUT /api/bots/{bot_id}", True)
            return True
        else:
            print_error("Response missing expected fields")
            record_test(f"PUT /api/bots/{bot_id}", False, "Response missing expected fields")
    else:
        record_test(f"PUT /api/bots/{bot_id}", False, "Request failed")
    
    return False

def test_toggle_bot(admin_token: str, bot_id: str) -> bool:
    """Test POST /api/bots/{bot_id}/toggle endpoint."""
    print_subheader(f"Testing POST /api/bots/{bot_id}/toggle")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"POST /api/bots/{bot_id}/toggle", False, "No admin token")
        return False
    
    response, success = make_request("POST", f"/bots/{bot_id}/toggle", auth_token=admin_token)
    
    if success:
        if "message" in response and "is_active" in response:
            print_success(f"Bot toggled successfully: {response['message']}")
            print_success(f"Bot is now {'active' if response['is_active'] else 'inactive'}")
            record_test(f"POST /api/bots/{bot_id}/toggle", True)
            return True
        else:
            print_error("Response missing expected fields")
            record_test(f"POST /api/bots/{bot_id}/toggle", False, "Response missing expected fields")
    else:
        record_test(f"POST /api/bots/{bot_id}/toggle", False, "Request failed")
    
    return False

def test_delete_bot(admin_token: str, bot_id: str) -> bool:
    """Test DELETE /api/bots/{bot_id} endpoint."""
    print_subheader(f"Testing DELETE /api/bots/{bot_id}")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"DELETE /api/bots/{bot_id}", False, "No admin token")
        return False
    
    response, success = make_request("DELETE", f"/bots/{bot_id}", auth_token=admin_token)
    
    if success:
        if "message" in response:
            print_success(f"Bot deleted successfully: {response['message']}")
            record_test(f"DELETE /api/bots/{bot_id}", True)
            return True
        else:
            print_error("Response missing expected fields")
            record_test(f"DELETE /api/bots/{bot_id}", False, "Response missing expected fields")
    else:
        record_test(f"DELETE /api/bots/{bot_id}", False, "Request failed")
    
    return False

def test_setup_bot_gems(admin_token: str, bot_id: str) -> bool:
    """Test POST /api/bots/{bot_id}/setup-gems endpoint."""
    print_subheader(f"Testing POST /api/bots/{bot_id}/setup-gems")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"POST /api/bots/{bot_id}/setup-gems", False, "No admin token")
        return False
    
    response, success = make_request("POST", f"/bots/{bot_id}/setup-gems", auth_token=admin_token)
    
    if success:
        if "message" in response:
            print_success(f"Bot gems setup successfully: {response['message']}")
            record_test(f"POST /api/bots/{bot_id}/setup-gems", True)
            return True
        else:
            print_error("Response missing expected fields")
            record_test(f"POST /api/bots/{bot_id}/setup-gems", False, "Response missing expected fields")
    else:
        record_test(f"POST /api/bots/{bot_id}/setup-gems", False, "Request failed")
    
    return False

def test_bot_create_game(admin_token: str, bot_id: str) -> Optional[str]:
    """Test POST /api/bots/{bot_id}/create-game endpoint."""
    print_subheader(f"Testing POST /api/bots/{bot_id}/create-game")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"POST /api/bots/{bot_id}/create-game", False, "No admin token")
        return None
    
    # Send game data
    data = {
        "bet_gems": {"Ruby": 5, "Emerald": 2},
        "opponent_type": "any"
    }
    
    response, success = make_request("POST", f"/bots/{bot_id}/create-game", data=data, auth_token=admin_token)
    
    if success:
        if "message" in response and "game_id" in response:
            print_success(f"Bot created game successfully: {response['message']}")
            print_success(f"Game ID: {response['game_id']}")
            record_test(f"POST /api/bots/{bot_id}/create-game", True)
            return response["game_id"]
        else:
            print_error("Response missing expected fields")
            record_test(f"POST /api/bots/{bot_id}/create-game", False, "Response missing expected fields")
    else:
        record_test(f"POST /api/bots/{bot_id}/create-game", False, "Request failed")
    
    return None

def test_get_active_bots(admin_token: str) -> List[Dict[str, Any]]:
    """Test GET /api/bots/active endpoint."""
    print_subheader("Testing GET /api/bots/active")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/bots/active", False, "No admin token")
        return []
    
    response, success = make_request("GET", "/bots/active", auth_token=admin_token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Successfully retrieved {len(response)} active bots")
            record_test("GET /api/bots/active", True)
            return response
        else:
            print_error("Response is not a list")
            record_test("GET /api/bots/active", False, "Response is not a list")
    else:
        record_test("GET /api/bots/active", False, "Request failed")
    
    return []

def test_get_bot_stats(admin_token: str, bot_id: str) -> Dict[str, Any]:
    """Test GET /api/bots/{bot_id}/stats endpoint."""
    print_subheader(f"Testing GET /api/bots/{bot_id}/stats")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"GET /api/bots/{bot_id}/stats", False, "No admin token")
        return {}
    
    response, success = make_request("GET", f"/bots/{bot_id}/stats", auth_token=admin_token)
    
    if success:
        if "bot_id" in response and "name" in response:
            print_success(f"Successfully retrieved stats for bot {bot_id}")
            record_test(f"GET /api/bots/{bot_id}/stats", True)
            return response
        else:
            print_error("Response missing expected fields")
            record_test(f"GET /api/bots/{bot_id}/stats", False, "Response missing expected fields")
    else:
        record_test(f"GET /api/bots/{bot_id}/stats", False, "Request failed")
    
    return {}

def test_bot_game_logic(admin_token: str, bot_id: str) -> bool:
    """Test bot game logic by creating a game and checking cycle tracking."""
    print_subheader("Testing Bot Game Logic")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("Bot Game Logic", False, "No admin token")
        return False
    
    # First, get initial bot stats
    initial_stats = test_get_bot_stats(admin_token, bot_id)
    if not initial_stats:
        print_error("Failed to get initial bot stats")
        record_test("Bot Game Logic - Cycle Tracking", False, "Failed to get initial stats")
        return False
    
    initial_cycle_games = initial_stats.get("current_cycle_games", 0)
    initial_cycle_wins = initial_stats.get("current_cycle_wins", 0)
    
    # Make sure the bot is active
    if not initial_stats.get("is_active", False):
        print_warning("Bot is not active, toggling to active")
        test_toggle_bot(admin_token, bot_id)
    
    # Create a game with the bot
    game_id = test_bot_create_game(admin_token, bot_id)
    if not game_id:
        print_error("Failed to create a game with the bot")
        record_test("Bot Game Logic - Game Creation", False, "Failed to create game")
        return False
    
    # Wait a bit for the game to be processed
    print("Waiting for game to be processed...")
    time.sleep(2)
    
    # Get updated bot stats
    updated_stats = test_get_bot_stats(admin_token, bot_id)
    if not updated_stats:
        print_error("Failed to get updated bot stats")
        record_test("Bot Game Logic - Cycle Tracking", False, "Failed to get updated stats")
        return False
    
    updated_cycle_games = updated_stats.get("current_cycle_games", 0)
    updated_cycle_wins = updated_stats.get("current_cycle_wins", 0)
    
    # Check if cycle tracking was updated
    if updated_cycle_games > initial_cycle_games:
        print_success(f"Bot cycle games increased: {initial_cycle_games} -> {updated_cycle_games}")
        record_test("Bot Game Logic - Cycle Games Tracking", True)
    else:
        print_error(f"Bot cycle games did not increase: {initial_cycle_games} -> {updated_cycle_games}")
        record_test("Bot Game Logic - Cycle Games Tracking", False, "Cycle games not updated")
    
    # Note: We can't reliably test win tracking since it depends on the game outcome
    print_success(f"Bot cycle wins: {initial_cycle_wins} -> {updated_cycle_wins}")
    
    return True

def test_bot_integration_with_game_system(admin_token: str) -> bool:
    """Test integration of bots with the game system."""
    print_subheader("Testing Bot Integration with Game System")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("Bot Integration with Game System", False, "No admin token")
        return False
    
    # Create a new bot for testing
    bot_data = {
        "name": f"TestBot_{uuid.uuid4().hex[:8]}",
        "bot_type": "REGULAR",
        "win_rate": 0.5,
        "cycle_games": 10,
        "min_bet": 1.0,
        "max_bet": 100.0,
        "pause_between_games": 5,
        "can_accept_bets": True,
        "can_play_with_bots": False,
        "avatar_gender": "male"
    }
    
    bot_id = test_create_bot(admin_token, bot_data)
    if not bot_id:
        print_error("Failed to create test bot")
        record_test("Bot Integration - Bot Creation", False, "Failed to create bot")
        return False
    
    # Setup gems for the bot
    if not test_setup_bot_gems(admin_token, bot_id):
        print_error("Failed to setup gems for the bot")
        record_test("Bot Integration - Gem Setup", False, "Failed to setup gems")
        return False
    
    # Create a game with the bot
    game_id = test_bot_create_game(admin_token, bot_id)
    if not game_id:
        print_error("Failed to create a game with the bot")
        record_test("Bot Integration - Game Creation", False, "Failed to create game")
        return False
    
    # Wait a bit for the game to be processed
    print("Waiting for game to be processed...")
    time.sleep(2)
    
    # Get bot stats to check if the game was recorded
    stats = test_get_bot_stats(admin_token, bot_id)
    if not stats:
        print_error("Failed to get bot stats")
        record_test("Bot Integration - Game Recording", False, "Failed to get stats")
        return False
    
    # Check if the last_game_time is set, which indicates the bot has played a game
    if stats.get("last_game_time"):
        print_success(f"Bot has played a game, last game time: {stats.get('last_game_time')}")
        record_test("Bot Integration - Game Recording", True)
        game_found = True
    else:
        print_error("Bot has not played any games")
        record_test("Bot Integration - Game Recording", False, "No games played")
        game_found = False
    
    # Clean up - delete the test bot
    if test_delete_bot(admin_token, bot_id):
        print_success(f"Test bot {bot_id} deleted successfully")
    else:
        print_warning(f"Failed to delete test bot {bot_id}")
    
    return game_found

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

def run_all_tests() -> None:
    """Run all bot system tests."""
    print_header("GEMPLAY BOT SYSTEM API TESTING")
    
    # Login as admin
    admin_token = login_admin()
    if not admin_token:
        print_error("Failed to login as admin. Cannot proceed with tests.")
        return
    
    # Test 1: Get all bots
    bots = test_get_all_bots(admin_token)
    
    # Test 2: Create a new bot
    bot_data = {
        "name": f"TestBot_{uuid.uuid4().hex[:8]}",
        "bot_type": "REGULAR",
        "win_rate": 0.6,
        "cycle_games": 12,
        "min_bet": 1.0,
        "max_bet": 100.0,
        "pause_between_games": 30,
        "can_accept_bets": True,
        "can_play_with_bots": False,
        "avatar_gender": "male"
    }
    
    bot_id = test_create_bot(admin_token, bot_data)
    
    if bot_id:
        # Test 3: Update the bot
        update_data = {
            "name": f"UpdatedBot_{uuid.uuid4().hex[:8]}",
            "win_rate": 0.7,
            "cycle_games": 15
        }
        test_update_bot(admin_token, bot_id, update_data)
        
        # Test 4: Toggle bot active status
        test_toggle_bot(admin_token, bot_id)
        
        # Test 5: Setup gems for the bot
        test_setup_bot_gems(admin_token, bot_id)
        
        # Test 6: Get active bots
        test_get_active_bots(admin_token)
        
        # Test 7: Get bot stats
        test_get_bot_stats(admin_token, bot_id)
        
        # Test 8: Test bot game logic
        test_bot_game_logic(admin_token, bot_id)
        
        # Test 9: Delete the bot
        test_delete_bot(admin_token, bot_id)
    
    # Test 10: Test bot integration with game system
    test_bot_integration_with_game_system(admin_token)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_all_tests()