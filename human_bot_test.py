#!/usr/bin/env python3
"""
Comprehensive Human-Bot System Testing for GemPlay
Testing all Human-bot endpoints, background simulation, and game integration
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
    
    try:
        if data and method.lower() in ["post", "put", "patch"]:
            headers["Content-Type"] = "application/json"
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
        else:
            response = requests.request(method, url, params=data, headers=headers, timeout=30)
        
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
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return {"error": str(e)}, False

def test_admin_login() -> Optional[str]:
    """Test admin login and return token."""
    print_subheader("Admin Login")
    
    response, success = make_request(
        "POST", "/auth/login", 
        data=ADMIN_USER
    )
    
    if success and "access_token" in response:
        print_success("Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error("Admin login failed")
        record_test("Admin Login", False, "Login failed")
        return None

def test_human_bot_endpoints(admin_token: str) -> None:
    """Test all Human-bot API endpoints."""
    print_header("HUMAN-BOT API ENDPOINTS TESTING")
    
    # Test 1: GET /admin/human-bots (list with pagination and filters)
    print_subheader("Test 1: GET /admin/human-bots - List Human-bots")
    
    # Test basic list
    response, success = make_request(
        "GET", "/admin/human-bots",
        auth_token=admin_token
    )
    
    if success:
        print_success("Human-bots list retrieved successfully")
        initial_count = len(response.get("bots", []))
        print_success(f"Found {initial_count} existing Human-bots")
        record_test("GET /admin/human-bots - Basic List", True)
    else:
        print_error("Failed to get Human-bots list")
        record_test("GET /admin/human-bots - Basic List", False)
        return
    
    # Test pagination
    response, success = make_request(
        "GET", "/admin/human-bots?page=1&limit=5",
        auth_token=admin_token
    )
    
    if success and "pagination" in response:
        print_success("Pagination working correctly")
        record_test("GET /admin/human-bots - Pagination", True)
    else:
        print_warning("Pagination may not be implemented")
        record_test("GET /admin/human-bots - Pagination", False)
    
    # Test 2: POST /admin/human-bots (create new Human-bot)
    print_subheader("Test 2: POST /admin/human-bots - Create Human-bot")
    
    test_bot_data = {
        "name": f"TestBot_{random.randint(1000, 9999)}",
        "character": "AGGRESSIVE",
        "min_bet": 5.0,
        "max_bet": 50.0,
        "win_percentage": 45.0,
        "loss_percentage": 35.0,
        "draw_percentage": 20.0,
        "min_delay": 30,
        "max_delay": 90,
        "use_commit_reveal": True,
        "logging_level": "INFO"
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=test_bot_data,
        auth_token=admin_token,
        expected_status=201
    )
    
    created_bot_id = None
    if success and "id" in response:
        created_bot_id = response["id"]
        print_success(f"Human-bot created successfully with ID: {created_bot_id}")
        record_test("POST /admin/human-bots - Create Bot", True)
        
        # Validate response fields
        required_fields = ["id", "name", "character", "is_active", "min_bet", "max_bet"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("All required fields present in response")
            record_test("POST /admin/human-bots - Response Validation", True)
        else:
            print_error(f"Missing fields in response: {missing_fields}")
            record_test("POST /admin/human-bots - Response Validation", False)
    else:
        print_error("Failed to create Human-bot")
        record_test("POST /admin/human-bots - Create Bot", False)
        return
    
    # Test 3: PUT /admin/human-bots/{bot_id} (edit Human-bot)
    print_subheader("Test 3: PUT /admin/human-bots/{bot_id} - Edit Human-bot")
    
    if created_bot_id:
        update_data = {
            "name": f"UpdatedBot_{random.randint(1000, 9999)}",
            "character": "CAUTIOUS",
            "min_bet": 10.0,
            "max_bet": 100.0,
            "win_percentage": 40.0,
            "loss_percentage": 40.0,
            "draw_percentage": 20.0
        }
        
        response, success = make_request(
            "PUT", f"/admin/human-bots/{created_bot_id}",
            data=update_data,
            auth_token=admin_token
        )
        
        if success:
            print_success("Human-bot updated successfully")
            record_test("PUT /admin/human-bots/{id} - Update Bot", True)
            
            # Verify updates
            if response.get("character") == "CAUTIOUS" and response.get("min_bet") == 10.0:
                print_success("Update values correctly applied")
                record_test("PUT /admin/human-bots/{id} - Update Verification", True)
            else:
                print_error("Update values not correctly applied")
                record_test("PUT /admin/human-bots/{id} - Update Verification", False)
        else:
            print_error("Failed to update Human-bot")
            record_test("PUT /admin/human-bots/{id} - Update Bot", False)
    
    # Test 4: POST /admin/human-bots/{bot_id}/toggle-status (toggle status)
    print_subheader("Test 4: POST /admin/human-bots/{bot_id}/toggle-status - Toggle Status")
    
    if created_bot_id:
        response, success = make_request(
            "POST", f"/admin/human-bots/{created_bot_id}/toggle-status",
            auth_token=admin_token
        )
        
        if success:
            print_success("Human-bot status toggled successfully")
            record_test("POST /admin/human-bots/{id}/toggle-status", True)
            
            # Check if status changed
            if "is_active" in response:
                print_success(f"Bot status is now: {'Active' if response['is_active'] else 'Inactive'}")
            else:
                print_warning("Status field not in response")
        else:
            print_error("Failed to toggle Human-bot status")
            record_test("POST /admin/human-bots/{id}/toggle-status", False)
    
    # Test 5: POST /admin/human-bots/bulk-create (bulk creation)
    print_subheader("Test 5: POST /admin/human-bots/bulk-create - Bulk Creation")
    
    bulk_data = {
        "count": 3,
        "character": "BALANCED",
        "min_bet_range": [1.0, 5.0],
        "max_bet_range": [20.0, 50.0],
        "win_percentage": 42.0,
        "loss_percentage": 38.0,
        "draw_percentage": 20.0,
        "delay_range": [30, 120],
        "use_commit_reveal": True,
        "logging_level": "INFO"
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots/bulk-create",
        data=bulk_data,
        auth_token=admin_token,
        expected_status=201
    )
    
    bulk_created_ids = []
    if success and "bots" in response:
        bulk_created_ids = [bot["id"] for bot in response["bots"]]
        print_success(f"Bulk created {len(bulk_created_ids)} Human-bots")
        record_test("POST /admin/human-bots/bulk-create", True)
        
        # Validate unique names
        names = [bot["name"] for bot in response["bots"]]
        if len(names) == len(set(names)):
            print_success("All bulk-created bots have unique names")
            record_test("POST /admin/human-bots/bulk-create - Unique Names", True)
        else:
            print_error("Duplicate names found in bulk-created bots")
            record_test("POST /admin/human-bots/bulk-create - Unique Names", False)
    else:
        print_error("Failed to bulk create Human-bots")
        record_test("POST /admin/human-bots/bulk-create", False)
    
    # Test 6: GET /admin/human-bots/stats (statistics)
    print_subheader("Test 6: GET /admin/human-bots/stats - Statistics")
    
    response, success = make_request(
        "GET", "/admin/human-bots/stats",
        auth_token=admin_token
    )
    
    if success:
        print_success("Human-bots statistics retrieved successfully")
        record_test("GET /admin/human-bots/stats", True)
        
        # Validate stats structure
        expected_stats = ["total_bots", "active_bots", "character_distribution"]
        present_stats = [stat for stat in expected_stats if stat in response]
        
        if len(present_stats) >= 2:
            print_success(f"Statistics contain expected fields: {present_stats}")
            record_test("GET /admin/human-bots/stats - Structure", True)
        else:
            print_warning(f"Some expected statistics missing: {set(expected_stats) - set(present_stats)}")
            record_test("GET /admin/human-bots/stats - Structure", False)
    else:
        print_error("Failed to get Human-bots statistics")
        record_test("GET /admin/human-bots/stats", False)
    
    # Test 7: POST /admin/human-bots/toggle-all (mass toggle)
    print_subheader("Test 7: POST /admin/human-bots/toggle-all - Mass Toggle")
    
    toggle_data = {
        "action": "deactivate"  # or "activate"
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots/toggle-all",
        data=toggle_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("Mass toggle operation completed")
        record_test("POST /admin/human-bots/toggle-all", True)
        
        if "affected_count" in response:
            print_success(f"Affected {response['affected_count']} bots")
        else:
            print_warning("Affected count not in response")
    else:
        print_error("Failed to perform mass toggle")
        record_test("POST /admin/human-bots/toggle-all", False)
    
    # Test 8: DELETE /admin/human-bots/{bot_id} (delete Human-bot)
    print_subheader("Test 8: DELETE /admin/human-bots/{bot_id} - Delete Human-bot")
    
    # Delete the originally created bot
    if created_bot_id:
        response, success = make_request(
            "DELETE", f"/admin/human-bots/{created_bot_id}",
            auth_token=admin_token,
            expected_status=200
        )
        
        if success:
            print_success("Human-bot deleted successfully")
            record_test("DELETE /admin/human-bots/{id}", True)
        else:
            print_error("Failed to delete Human-bot")
            record_test("DELETE /admin/human-bots/{id}", False)
    
    # Clean up bulk created bots
    for bot_id in bulk_created_ids[:2]:  # Delete first 2, keep 1 for simulation testing
        response, success = make_request(
            "DELETE", f"/admin/human-bots/{bot_id}",
            auth_token=admin_token,
            expected_status=200
        )
        if success:
            print_success(f"Cleaned up bulk bot {bot_id}")

def test_human_bot_validation(admin_token: str) -> None:
    """Test Human-bot validation logic."""
    print_header("HUMAN-BOT VALIDATION TESTING")
    
    # Test 1: Invalid percentage distribution (not equal to 100%)
    print_subheader("Test 1: Invalid Percentage Distribution")
    
    invalid_percentage_data = {
        "name": "InvalidPercentageBot",
        "character": "STABLE",
        "min_bet": 1.0,
        "max_bet": 10.0,
        "win_percentage": 50.0,
        "loss_percentage": 30.0,
        "draw_percentage": 30.0  # Total = 110%, should fail
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=invalid_percentage_data,
        auth_token=admin_token,
        expected_status=422  # Validation error
    )
    
    if not success and response.get("detail"):
        print_success("Validation correctly rejected invalid percentage distribution")
        record_test("Validation - Invalid Percentage Distribution", True)
    else:
        print_error("Validation failed to catch invalid percentage distribution")
        record_test("Validation - Invalid Percentage Distribution", False)
    
    # Test 2: Invalid bet range (min > max)
    print_subheader("Test 2: Invalid Bet Range")
    
    invalid_bet_range_data = {
        "name": "InvalidBetRangeBot",
        "character": "STABLE",
        "min_bet": 100.0,  # Higher than max_bet
        "max_bet": 50.0,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=invalid_bet_range_data,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success:
        print_success("Validation correctly rejected invalid bet range")
        record_test("Validation - Invalid Bet Range", True)
    else:
        print_error("Validation failed to catch invalid bet range")
        record_test("Validation - Invalid Bet Range", False)
    
    # Test 3: Invalid delay range
    print_subheader("Test 3: Invalid Delay Range")
    
    invalid_delay_data = {
        "name": "InvalidDelayBot",
        "character": "STABLE",
        "min_bet": 1.0,
        "max_bet": 10.0,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "min_delay": 200,  # Higher than max_delay
        "max_delay": 100
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=invalid_delay_data,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success:
        print_success("Validation correctly rejected invalid delay range")
        record_test("Validation - Invalid Delay Range", True)
    else:
        print_error("Validation failed to catch invalid delay range")
        record_test("Validation - Invalid Delay Range", False)
    
    # Test 4: Duplicate name validation
    print_subheader("Test 4: Duplicate Name Validation")
    
    # First, create a bot
    unique_name = f"UniqueBot_{random.randint(10000, 99999)}"
    bot_data = {
        "name": unique_name,
        "character": "STABLE",
        "min_bet": 1.0,
        "max_bet": 10.0,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=bot_data,
        auth_token=admin_token,
        expected_status=201
    )
    
    created_bot_id = None
    if success:
        created_bot_id = response.get("id")
        print_success(f"Created bot with unique name: {unique_name}")
        
        # Now try to create another bot with the same name
        response, success = make_request(
            "POST", "/admin/human-bots",
            data=bot_data,
            auth_token=admin_token,
            expected_status=422
        )
        
        if not success:
            print_success("Validation correctly rejected duplicate name")
            record_test("Validation - Duplicate Name", True)
        else:
            print_error("Validation failed to catch duplicate name")
            record_test("Validation - Duplicate Name", False)
        
        # Clean up
        if created_bot_id:
            make_request("DELETE", f"/admin/human-bots/{created_bot_id}", auth_token=admin_token)
    else:
        print_error("Failed to create initial bot for duplicate name test")
        record_test("Validation - Duplicate Name", False)

def test_human_bot_simulation(admin_token: str) -> None:
    """Test Human-bot background simulation task."""
    print_header("HUMAN-BOT SIMULATION TESTING")
    
    # Step 1: Ensure we have at least one active Human-bot
    print_subheader("Step 1: Setup Active Human-bot for Simulation")
    
    # Get existing Human-bots
    response, success = make_request(
        "GET", "/admin/human-bots",
        auth_token=admin_token
    )
    
    active_human_bots = []
    if success and "bots" in response:
        active_human_bots = [bot for bot in response["bots"] if bot.get("is_active", False)]
    
    test_bot_id = None
    if not active_human_bots:
        # Create a test Human-bot for simulation
        test_bot_data = {
            "name": f"SimulationBot_{random.randint(1000, 9999)}",
            "character": "AGGRESSIVE",  # More active character
            "min_bet": 1.0,
            "max_bet": 20.0,
            "win_percentage": 45.0,
            "loss_percentage": 35.0,
            "draw_percentage": 20.0,
            "min_delay": 10,  # Short delay for testing
            "max_delay": 30,
            "use_commit_reveal": True,
            "logging_level": "DEBUG"
        }
        
        response, success = make_request(
            "POST", "/admin/human-bots",
            data=test_bot_data,
            auth_token=admin_token,
            expected_status=201
        )
        
        if success:
            test_bot_id = response["id"]
            print_success(f"Created test Human-bot for simulation: {test_bot_id}")
            record_test("Simulation Setup - Create Test Bot", True)
        else:
            print_error("Failed to create test Human-bot")
            record_test("Simulation Setup - Create Test Bot", False)
            return
    else:
        test_bot_id = active_human_bots[0]["id"]
        print_success(f"Using existing active Human-bot: {test_bot_id}")
        record_test("Simulation Setup - Use Existing Bot", True)
    
    # Step 2: Monitor for Human-bot activity
    print_subheader("Step 2: Monitor Human-bot Activity")
    
    # Get initial game count
    initial_games_response, success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    initial_game_count = 0
    if success and "games" in initial_games_response:
        initial_game_count = len(initial_games_response["games"])
    
    print_success(f"Initial available games count: {initial_game_count}")
    
    # Monitor for 60 seconds to see if Human-bot creates bets
    print("Monitoring Human-bot simulation for 60 seconds...")
    monitoring_start = time.time()
    monitoring_duration = 60
    check_interval = 15
    
    human_bot_activity_detected = False
    
    for check_round in range(int(monitoring_duration / check_interval)):
        print(f"\n--- Check Round {check_round + 1} (at {check_round * check_interval}s) ---")
        
        # Check available games
        games_response, success = make_request(
            "GET", "/games/available",
            auth_token=admin_token
        )
        
        if success and "games" in games_response:
            current_game_count = len(games_response["games"])
            print_success(f"Current available games count: {current_game_count}")
            
            # Look for games created by Human-bots
            human_bot_games = []
            for game in games_response["games"]:
                if game.get("creator_type") == "human_bot" or game.get("bot_type") == "HUMAN":
                    human_bot_games.append(game)
            
            if human_bot_games:
                print_success(f"Found {len(human_bot_games)} Human-bot games")
                human_bot_activity_detected = True
                
                # Display details of Human-bot games
                for game in human_bot_games[:3]:  # Show first 3
                    print_success(f"  Game ID: {game.get('id')}")
                    print_success(f"  Bet Amount: ${game.get('bet_amount', 0)}")
                    print_success(f"  Creator Type: {game.get('creator_type', 'unknown')}")
                    print_success(f"  Bot Type: {game.get('bot_type', 'unknown')}")
            else:
                print_warning("No Human-bot games found in this check")
        
        # Wait for next check (except on last iteration)
        if check_round < int(monitoring_duration / check_interval) - 1:
            print(f"Waiting {check_interval} seconds for next check...")
            time.sleep(check_interval)
    
    if human_bot_activity_detected:
        print_success("Human-bot simulation activity detected!")
        record_test("Human-bot Simulation - Activity Detection", True)
    else:
        print_warning("No Human-bot simulation activity detected in monitoring period")
        record_test("Human-bot Simulation - Activity Detection", False)
    
    # Step 3: Test Human-bot game joining behavior
    print_subheader("Step 3: Test Human-bot Game Joining")
    
    # Create a regular user game that Human-bot might join
    # First, we need to create a test user
    test_user_data = {
        "username": f"testuser_{random.randint(1000, 9999)}",
        "email": f"testuser_{random.randint(1000, 9999)}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    user_response, user_success = make_request(
        "POST", "/auth/register",
        data=test_user_data
    )
    
    if user_success and "verification_token" in user_response:
        # Verify email
        verify_response, verify_success = make_request(
            "POST", "/auth/verify-email",
            data={"token": user_response["verification_token"]}
        )
        
        if verify_success:
            # Login as test user
            login_response, login_success = make_request(
                "POST", "/auth/login",
                data={"email": test_user_data["email"], "password": test_user_data["password"]}
            )
            
            if login_success and "access_token" in login_response:
                user_token = login_response["access_token"]
                print_success("Test user created and logged in")
                
                # Give user some balance and gems (admin operation)
                balance_response, balance_success = make_request(
                    "POST", f"/admin/users/{login_response['user']['id']}/add-balance",
                    data={"amount": 100.0},
                    auth_token=admin_token
                )
                
                if balance_success:
                    print_success("Added balance to test user")
                    
                    # Create a game that Human-bot might join
                    game_data = {
                        "move": "rock",
                        "bet_gems": {"Ruby": 5, "Amber": 2}  # Small bet
                    }
                    
                    create_game_response, create_success = make_request(
                        "POST", "/games/create",
                        data=game_data,
                        auth_token=user_token,
                        expected_status=201
                    )
                    
                    if create_success:
                        created_game_id = create_game_response.get("id")
                        print_success(f"Created test game for Human-bot to potentially join: {created_game_id}")
                        
                        # Monitor for 30 seconds to see if Human-bot joins
                        print("Monitoring for Human-bot joining behavior...")
                        join_monitoring_start = time.time()
                        join_detected = False
                        
                        for i in range(6):  # Check every 5 seconds for 30 seconds
                            time.sleep(5)
                            
                            # Check game status
                            game_status_response, status_success = make_request(
                                "GET", f"/games/{created_game_id}",
                                auth_token=user_token
                            )
                            
                            if status_success:
                                game_status = game_status_response.get("status")
                                opponent_id = game_status_response.get("opponent_id")
                                
                                if opponent_id and game_status in ["ACTIVE", "REVEAL"]:
                                    print_success(f"Game joined! Status: {game_status}, Opponent: {opponent_id}")
                                    join_detected = True
                                    break
                                else:
                                    print(f"Check {i+1}: Game still waiting, status: {game_status}")
                        
                        if join_detected:
                            print_success("Human-bot successfully joined user game!")
                            record_test("Human-bot Simulation - Game Joining", True)
                        else:
                            print_warning("Human-bot did not join user game in monitoring period")
                            record_test("Human-bot Simulation - Game Joining", False)
                        
                        # Clean up - cancel game if still waiting
                        if not join_detected:
                            make_request("POST", f"/games/{created_game_id}/cancel", auth_token=user_token)
    
    # Clean up test bot if we created one
    if test_bot_id and test_bot_id not in [bot["id"] for bot in active_human_bots]:
        make_request("DELETE", f"/admin/human-bots/{test_bot_id}", auth_token=admin_token)
        print_success("Cleaned up test Human-bot")

def test_human_bot_game_integration(admin_token: str) -> None:
    """Test Human-bot integration in game process."""
    print_header("HUMAN-BOT GAME INTEGRATION TESTING")
    
    # Step 1: Check Human-bots appear in /games/available
    print_subheader("Step 1: Human-bots in Available Games")
    
    games_response, success = make_request(
        "GET", "/games/available"
    )
    
    if success and "games" in games_response:
        human_bot_games = [
            game for game in games_response["games"] 
            if game.get("creator_type") == "human_bot" or game.get("bot_type") == "HUMAN"
        ]
        
        if human_bot_games:
            print_success(f"Found {len(human_bot_games)} Human-bot games in available games")
            record_test("Game Integration - Human-bots in Available Games", True)
            
            # Check game properties
            sample_game = human_bot_games[0]
            required_fields = ["id", "bet_amount", "bet_gems", "created_at"]
            missing_fields = [field for field in required_fields if field not in sample_game]
            
            if not missing_fields:
                print_success("Human-bot games have all required fields")
                record_test("Game Integration - Game Properties", True)
            else:
                print_error(f"Human-bot games missing fields: {missing_fields}")
                record_test("Game Integration - Game Properties", False)
        else:
            print_warning("No Human-bot games found in available games")
            record_test("Game Integration - Human-bots in Available Games", False)
    else:
        print_error("Failed to get available games")
        record_test("Game Integration - Human-bots in Available Games", False)
    
    # Step 2: Test commission logic for Human-bots
    print_subheader("Step 2: Human-bot Commission Logic")
    
    # Create a test user to join Human-bot game
    test_user_data = {
        "username": f"commissiontest_{random.randint(1000, 9999)}",
        "email": f"commissiontest_{random.randint(1000, 9999)}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    user_response, user_success = make_request(
        "POST", "/auth/register",
        data=test_user_data
    )
    
    if user_success and "verification_token" in user_response:
        # Verify and login
        make_request("POST", "/auth/verify-email", data={"token": user_response["verification_token"]})
        
        login_response, login_success = make_request(
            "POST", "/auth/login",
            data={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        if login_success and "access_token" in login_response:
            user_token = login_response["access_token"]
            user_id = login_response["user"]["id"]
            
            # Add balance and gems
            make_request(
                "POST", f"/admin/users/{user_id}/add-balance",
                data={"amount": 100.0},
                auth_token=admin_token
            )
            
            # Get user's initial balance
            user_profile_response, profile_success = make_request(
                "GET", "/users/profile",
                auth_token=user_token
            )
            
            if profile_success:
                initial_balance = user_profile_response.get("virtual_balance", 0)
                initial_frozen = user_profile_response.get("frozen_balance", 0)
                
                print_success(f"User initial balance: ${initial_balance}, frozen: ${initial_frozen}")
                
                # Find a Human-bot game to join
                games_response, success = make_request("GET", "/games/available")
                
                if success and "games" in games_response:
                    human_bot_games = [
                        game for game in games_response["games"] 
                        if (game.get("creator_type") == "human_bot" or game.get("bot_type") == "HUMAN")
                        and game.get("bet_amount", 0) <= 20  # Small bet for testing
                    ]
                    
                    if human_bot_games:
                        test_game = human_bot_games[0]
                        game_id = test_game["id"]
                        bet_amount = test_game["bet_amount"]
                        expected_commission = bet_amount * 0.06  # 6% commission
                        
                        print_success(f"Joining Human-bot game: {game_id}, bet: ${bet_amount}")
                        print_success(f"Expected commission: ${expected_commission}")
                        
                        # Join the game
                        join_data = {
                            "move": "paper",
                            "gems": test_game["bet_gems"]  # Match the bet gems
                        }
                        
                        join_response, join_success = make_request(
                            "POST", f"/games/{game_id}/join",
                            data=join_data,
                            auth_token=user_token
                        )
                        
                        if join_success:
                            print_success("Successfully joined Human-bot game")
                            
                            # Check if commission was frozen
                            user_profile_after, profile_after_success = make_request(
                                "GET", "/users/profile",
                                auth_token=user_token
                            )
                            
                            if profile_after_success:
                                after_balance = user_profile_after.get("virtual_balance", 0)
                                after_frozen = user_profile_after.get("frozen_balance", 0)
                                
                                commission_frozen = after_frozen - initial_frozen
                                
                                print_success(f"After joining - balance: ${after_balance}, frozen: ${after_frozen}")
                                print_success(f"Commission frozen: ${commission_frozen}")
                                
                                if abs(commission_frozen - expected_commission) < 0.01:
                                    print_success("Commission correctly frozen for Human-bot game")
                                    record_test("Game Integration - Human-bot Commission", True)
                                else:
                                    print_error(f"Commission mismatch. Expected: ${expected_commission}, Got: ${commission_frozen}")
                                    record_test("Game Integration - Human-bot Commission", False)
                            
                            # Wait for game completion and check final balances
                            print("Waiting for game completion...")
                            time.sleep(10)
                            
                            final_profile_response, final_success = make_request(
                                "GET", "/users/profile",
                                auth_token=user_token
                            )
                            
                            if final_success:
                                final_balance = final_profile_response.get("virtual_balance", 0)
                                final_frozen = final_profile_response.get("frozen_balance", 0)
                                
                                print_success(f"Final - balance: ${final_balance}, frozen: ${final_frozen}")
                                
                                # Check game result
                                game_result_response, result_success = make_request(
                                    "GET", f"/games/{game_id}",
                                    auth_token=user_token
                                )
                                
                                if result_success:
                                    game_status = game_result_response.get("status")
                                    winner_id = game_result_response.get("winner_id")
                                    
                                    print_success(f"Game completed with status: {game_status}")
                                    if winner_id:
                                        if winner_id == user_id:
                                            print_success("User won against Human-bot")
                                        else:
                                            print_success("Human-bot won against user")
                                    else:
                                        print_success("Game ended in draw")
                                    
                                    record_test("Game Integration - Game Completion", True)
                        else:
                            print_error("Failed to join Human-bot game")
                            record_test("Game Integration - Human-bot Commission", False)
                    else:
                        print_warning("No suitable Human-bot games found for commission testing")
                        record_test("Game Integration - Human-bot Commission", False)

def test_human_bot_characters(admin_token: str) -> None:
    """Test Human-bot character behaviors."""
    print_header("HUMAN-BOT CHARACTER BEHAVIOR TESTING")
    
    characters = ["STABLE", "AGGRESSIVE", "CAUTIOUS", "BALANCED", "IMPULSIVE", "ANALYST", "MIMIC"]
    
    for character in characters:
        print_subheader(f"Testing Character: {character}")
        
        # Create bot with specific character
        bot_data = {
            "name": f"{character}Bot_{random.randint(1000, 9999)}",
            "character": character,
            "min_bet": 1.0,
            "max_bet": 50.0,
            "win_percentage": 40.0,
            "loss_percentage": 40.0,
            "draw_percentage": 20.0,
            "min_delay": 5,  # Short for testing
            "max_delay": 15,
            "use_commit_reveal": True,
            "logging_level": "DEBUG"
        }
        
        response, success = make_request(
            "POST", "/admin/human-bots",
            data=bot_data,
            auth_token=admin_token,
            expected_status=201
        )
        
        if success:
            bot_id = response["id"]
            print_success(f"Created {character} bot: {bot_id}")
            
            # Test character-specific behavior by checking created games
            # Wait a bit for bot to potentially create games
            time.sleep(10)
            
            # Check for games created by this bot
            games_response, games_success = make_request(
                "GET", "/games/available"
            )
            
            if games_success and "games" in games_response:
                bot_games = [
                    game for game in games_response["games"]
                    if game.get("creator_id") == bot_id
                ]
                
                if bot_games:
                    print_success(f"{character} bot created {len(bot_games)} games")
                    
                    # Analyze bet amounts for character consistency
                    bet_amounts = [game.get("bet_amount", 0) for game in bot_games]
                    avg_bet = sum(bet_amounts) / len(bet_amounts) if bet_amounts else 0
                    
                    print_success(f"Average bet amount: ${avg_bet:.2f}")
                    
                    # Character-specific validation
                    if character == "CAUTIOUS":
                        # Should prefer lower bets
                        if avg_bet <= (bot_data["min_bet"] + bot_data["max_bet"]) / 2:
                            print_success("CAUTIOUS character shows conservative betting")
                            record_test(f"Character Behavior - {character}", True)
                        else:
                            print_warning("CAUTIOUS character not showing conservative betting")
                            record_test(f"Character Behavior - {character}", False)
                    
                    elif character == "AGGRESSIVE":
                        # Should prefer higher bets
                        if avg_bet >= (bot_data["min_bet"] + bot_data["max_bet"]) / 2:
                            print_success("AGGRESSIVE character shows bold betting")
                            record_test(f"Character Behavior - {character}", True)
                        else:
                            print_warning("AGGRESSIVE character not showing bold betting")
                            record_test(f"Character Behavior - {character}", False)
                    
                    else:
                        # For other characters, just check they're creating games
                        print_success(f"{character} character is active")
                        record_test(f"Character Behavior - {character}", True)
                
                else:
                    print_warning(f"{character} bot hasn't created games yet")
                    record_test(f"Character Behavior - {character}", False)
            
            # Clean up
            make_request("DELETE", f"/admin/human-bots/{bot_id}", auth_token=admin_token)
        
        else:
            print_error(f"Failed to create {character} bot")
            record_test(f"Character Behavior - {character}", False)

def print_test_summary() -> None:
    """Print comprehensive test summary."""
    print_header("HUMAN-BOT SYSTEM TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 80 else Colors.WARNING}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print_subheader("Failed Tests Details")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"{test['name']}: {test['details']}")
    
    print_subheader("Test Categories Summary")
    
    categories = {}
    for test in test_results["tests"]:
        category = test["name"].split(" - ")[0] if " - " in test["name"] else "General"
        if category not in categories:
            categories[category] = {"passed": 0, "total": 0}
        categories[category]["total"] += 1
        if test["passed"]:
            categories[category]["passed"] += 1
    
    for category, stats in categories.items():
        rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        color = Colors.OKGREEN if rate >= 80 else Colors.WARNING if rate >= 60 else Colors.FAIL
        print(f"{category}: {color}{stats['passed']}/{stats['total']} ({rate:.1f}%){Colors.ENDC}")

def main():
    """Main test execution function."""
    print_header("GEMPLAY HUMAN-BOT SYSTEM COMPREHENSIVE TESTING")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        sys.exit(1)
    
    # Step 2: Test all Human-bot API endpoints
    test_human_bot_endpoints(admin_token)
    
    # Step 3: Test validation logic
    test_human_bot_validation(admin_token)
    
    # Step 4: Test background simulation
    test_human_bot_simulation(admin_token)
    
    # Step 5: Test game integration
    test_human_bot_game_integration(admin_token)
    
    # Step 6: Test character behaviors
    test_human_bot_characters(admin_token)
    
    # Step 7: Print comprehensive summary
    print_test_summary()
    
    # Return exit code based on results
    if test_results["failed"] == 0:
        print_success("All Human-bot system tests passed!")
        sys.exit(0)
    else:
        print_error(f"{test_results['failed']} tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()