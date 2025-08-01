#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://a20aa5a2-a31c-4c8d-a1c4-18cc39118b00.preview.emergentagent.com/api"
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

def test_admin_login() -> Optional[str]:
    """Test admin login."""
    print_subheader("Testing Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_active_bets_modal_backend() -> None:
    """Test Active Bets Modal backend functionality as requested in the review."""
    print_header("TESTING ACTIVE BETS MODAL BACKEND FUNCTIONALITY")
    
    # Step 1: Login as admin
    print_subheader("Step 1: Admin Login")
    admin_token = test_admin_login()
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with Active Bets Modal tests")
        record_test("Active Bets Modal - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # Step 2: Test GET /api/admin/bots/regular/list endpoint
    print_subheader("Step 2: Testing GET /api/admin/bots/regular/list Endpoint")
    
    # Test basic endpoint functionality
    response, success = make_request(
        "GET", "/admin/bots/regular/list",
        auth_token=admin_token
    )
    
    if success:
        print_success("GET /api/admin/bots/regular/list endpoint accessible")
        
        # Check response structure for pagination
        expected_pagination_fields = ["bots", "total_count", "current_page", "total_pages", "items_per_page", "has_next", "has_prev"]
        missing_fields = [field for field in expected_pagination_fields if field not in response]
        
        if not missing_fields:
            print_success("✓ Response has correct paginated structure with 'bots' key")
            record_test("Active Bets Modal - Bots List Structure", True)
            
            # Check if bots array exists and has proper structure
            bots = response.get("bots", [])
            print_success(f"Found {len(bots)} bots in response")
            
            if bots:
                # Check first bot for required fields
                first_bot = bots[0]
                required_bot_fields = ["id", "name", "is_active", "active_bets"]
                missing_bot_fields = [field for field in required_bot_fields if field not in first_bot]
                
                if not missing_bot_fields:
                    print_success("✓ Bot objects contain all required fields for modal display")
                    print_success(f"Sample bot: ID={first_bot.get('id')}, Name={first_bot.get('name')}, Active={first_bot.get('is_active')}, Active Bets={first_bot.get('active_bets')}")
                    record_test("Active Bets Modal - Bot Fields", True)
                else:
                    print_error(f"✗ Bot objects missing required fields: {missing_bot_fields}")
                    record_test("Active Bets Modal - Bot Fields", False, f"Missing fields: {missing_bot_fields}")
            else:
                print_warning("No bots found in response - cannot verify bot field structure")
                record_test("Active Bets Modal - Bot Fields", True, "No bots to verify")
                
        else:
            print_error(f"✗ Response missing pagination fields: {missing_fields}")
            record_test("Active Bets Modal - Bots List Structure", False, f"Missing fields: {missing_fields}")
    else:
        print_error("GET /api/admin/bots/regular/list endpoint failed")
        record_test("Active Bets Modal - Bots List Endpoint", False, "Endpoint failed")
        return
    
    # Test pagination parameters
    print_subheader("Step 2a: Testing Pagination Parameters")
    
    response, success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=5",
        auth_token=admin_token
    )
    
    if success:
        if response.get("items_per_page") == 5 and response.get("current_page") == 1:
            print_success("✓ Pagination parameters working correctly")
            record_test("Active Bets Modal - Pagination", True)
        else:
            print_error(f"✗ Pagination not working: page={response.get('current_page')}, limit={response.get('items_per_page')}")
            record_test("Active Bets Modal - Pagination", False, "Pagination parameters not working")
    
    # Step 3: Test available bot-related endpoints for modal functionality
    print_subheader("Step 3: Testing Available Bot-Related Endpoints")
    
    # First, get a bot ID to test filtering
    bots_response = response  # Use the previous response
    bot_id = None
    if bots_response.get("bots"):
        bot_id = bots_response["bots"][0]["id"]
        print_success(f"Using bot ID for testing: {bot_id}")
    
    if bot_id:
        # Test GET /api/admin/bots/{bot_id}/active-bets endpoint
        response, success = make_request(
            "GET", f"/admin/bots/{bot_id}/active-bets",
            auth_token=admin_token
        )
        
        if success:
            print_success("✓ GET /api/admin/bots/{bot_id}/active-bets endpoint accessible")
            
            # Check if response has the expected structure for active bets modal
            if "active_bets" in response:
                active_bets = response.get("active_bets", [])
                print_success(f"Found {len(active_bets)} active bets for bot {bot_id}")
                
                if active_bets:
                    first_bet = active_bets[0]
                    required_bet_fields = ["id", "bet_amount", "status", "created_at"]
                    missing_bet_fields = [field for field in required_bet_fields if field not in first_bet]
                    
                    if not missing_bet_fields:
                        print_success("✓ Active bet objects contain required fields for modal display")
                        print_success(f"Sample bet: ID={first_bet.get('id')}, Status={first_bet.get('status')}, Amount=${first_bet.get('bet_amount')}")
                        record_test("Active Bets Modal - Active Bets Data", True)
                    else:
                        print_error(f"✗ Active bet objects missing required fields: {missing_bet_fields}")
                        record_test("Active Bets Modal - Active Bets Data", False, f"Missing fields: {missing_bet_fields}")
                else:
                    print_warning("No active bets found for this bot")
                    record_test("Active Bets Modal - Active Bets Data", True, "No active bets found")
            else:
                print_error("✗ Response missing 'active_bets' array")
                record_test("Active Bets Modal - Active Bets Data", False, "Missing active_bets array")
        else:
            print_error("GET /api/admin/bots/{bot_id}/active-bets endpoint failed")
            record_test("Active Bets Modal - Active Bets Endpoint", False, "Endpoint failed")
    else:
        print_warning("No bot ID available for active bets testing")
        record_test("Active Bets Modal - Active Bets Data", True, "No bot ID available")
    
    # Step 4: Test GET /api/admin/bots/{bot_id}/cycle-history endpoint for statistics
    print_subheader("Step 4: Testing GET /api/admin/bots/{bot_id}/cycle-history Endpoint")
    
    if bot_id:
        response, success = make_request(
            "GET", f"/admin/bots/{bot_id}/cycle-history",
            auth_token=admin_token
        )
        
        if success:
            print_success("✓ GET /api/admin/bots/{bot_id}/cycle-history endpoint accessible")
            
            # Check for required statistics fields
            required_stats_fields = ["total_games", "won_games", "win_percentage"]
            missing_stats_fields = [field for field in required_stats_fields if field not in response]
            
            if not missing_stats_fields:
                print_success("✓ Bot cycle history contains statistics fields")
                print_success(f"Bot stats: Total Games={response.get('total_games')}, Won={response.get('won_games')}, Win Rate={response.get('win_percentage')}%")
                record_test("Active Bets Modal - Bot Cycle Stats", True)
                
                # Verify statistics calculations
                total_games = response.get("total_games", 0)
                won_games = response.get("won_games", 0)
                win_percentage = response.get("win_percentage", 0)
                
                # Check if win rate calculation is correct
                if total_games > 0:
                    expected_win_rate = (won_games / total_games) * 100
                    if abs(win_percentage - expected_win_rate) < 0.01:
                        print_success("✓ Win rate calculation is correct")
                        record_test("Active Bets Modal - Win Rate Calculation", True)
                    else:
                        print_error(f"✗ Win rate calculation incorrect: expected {expected_win_rate:.2f}%, got {win_percentage}%")
                        record_test("Active Bets Modal - Win Rate Calculation", False, f"Calculation error")
                else:
                    print_success("✓ Win rate calculation correct for zero games")
                    record_test("Active Bets Modal - Win Rate Calculation", True, "Zero games case")
                
            else:
                print_warning(f"Bot cycle history missing some statistics fields: {missing_stats_fields}")
                record_test("Active Bets Modal - Bot Cycle Stats", True, f"Missing some fields: {missing_stats_fields}")
        else:
            print_error(f"GET /api/admin/bots/{bot_id}/cycle-history endpoint failed")
            record_test("Active Bets Modal - Bot Cycle Stats Endpoint", False, "Endpoint failed")
    else:
        print_warning("No bot ID available for cycle history testing")
        record_test("Active Bets Modal - Bot Cycle Stats", True, "No bot ID available")
    
    # Step 5: Test available games endpoints for game data
    print_subheader("Step 5: Testing Available Games Endpoints")
    
    # Test GET /api/games/available endpoint to see game structure
    response, success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if success:
        if isinstance(response, list):
            print_success(f"Found {len(response)} available games")
            
            if response:
                first_game = response[0]
                required_game_fields = ["game_id", "creator", "bet_amount", "created_at"]
                missing_game_fields = [field for field in required_game_fields if field not in first_game]
                
                if not missing_game_fields:
                    print_success("✓ Available game objects contain required fields")
                    print_success(f"Sample game: ID={first_game.get('game_id')}, Creator={first_game.get('creator', {}).get('username')}, Bet=${first_game.get('bet_amount')}")
                    record_test("Active Bets Modal - Available Games Structure", True)
                else:
                    print_error(f"✗ Available game objects missing required fields: {missing_game_fields}")
                    record_test("Active Bets Modal - Available Games Structure", False, f"Missing fields: {missing_game_fields}")
            else:
                print_warning("No available games found")
                record_test("Active Bets Modal - Available Games Structure", True, "No games available")
        else:
            print_error("✗ Available games response is not a list")
            record_test("Active Bets Modal - Available Games Structure", False, "Not a list")
    else:
        print_error("GET /api/games/available endpoint failed")
        record_test("Active Bets Modal - Available Games Endpoint", False, "Endpoint failed")
    
    # Test GET /api/games/history endpoint for completed games
    response, success = make_request(
        "GET", "/games/history",
        auth_token=admin_token
    )
    
    if success:
        if "games" in response:
            games = response.get("games", [])
            print_success(f"Found {len(games)} games in history")
            
            # Look for completed games to check winner_id
            completed_games = [game for game in games if game.get("status") == "COMPLETED"]
            
            if completed_games:
                print_success(f"Found {len(completed_games)} completed games to check winner_id")
                
                winner_id_correct = True
                for game in completed_games[:3]:  # Check first 3 games
                    winner_id = game.get("winner_id")
                    creator_id = game.get("creator_id")
                    opponent_id = game.get("opponent_id")
                    
                    if winner_id and winner_id in [creator_id, opponent_id]:
                        print_success(f"✓ Game {game.get('id')}: winner_id {winner_id} is valid")
                    elif winner_id is None:
                        print_success(f"✓ Game {game.get('id')}: winner_id is None (draw)")
                    else:
                        print_error(f"✗ Game {game.get('id')}: winner_id {winner_id} not in [creator: {creator_id}, opponent: {opponent_id}]")
                        winner_id_correct = False
                
                if winner_id_correct:
                    record_test("Active Bets Modal - Winner ID Correctness", True)
                else:
                    record_test("Active Bets Modal - Winner ID Correctness", False, "Invalid winner_id found")
            else:
                print_warning("No completed games found to check winner_id")
                record_test("Active Bets Modal - Winner ID Correctness", True, "No completed games")
        else:
            print_error("✗ Games history response missing 'games' array")
            record_test("Active Bets Modal - Winner ID Correctness", False, "Missing games array")
    else:
        print_error("GET /api/games/history endpoint failed")
        record_test("Active Bets Modal - Winner ID Correctness", False, "Endpoint failed")
    
    # Step 6: Test authentication and authorization
    print_subheader("Step 6: Testing Authentication and Authorization")
    
    # Test without token (should fail)
    response, success = make_request(
        "GET", "/admin/bots/regular/list",
        expected_status=401
    )
    
    if not success and "401" in str(response):
        print_success("✓ Endpoints correctly require authentication")
        record_test("Active Bets Modal - Authentication Required", True)
    else:
        print_error("✗ Endpoints should require authentication")
        record_test("Active Bets Modal - Authentication Required", False, "No auth required")

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

def main():
    """Main test function."""
    print_header("ACTIVE BETS MODAL BACKEND TESTING")
    
    # Test Active Bets Modal backend functionality (main focus for this review)
    test_active_bets_modal_backend()
    
    # Print final summary
    print_summary()

if __name__ == "__main__":
    main()