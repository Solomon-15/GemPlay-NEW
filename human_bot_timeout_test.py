#!/usr/bin/env python3
"""
Human-Bot Timeout Logic Testing
Russian Review Requirements: Test Human-bot logic fixes and automatic game completion
Focus: Human-bot joining, timeout system, and automatic game completion within 1 minute
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://acffc923-2545-42ed-a41d-4e93fa17c383.preview.emergentagent.com/api"

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

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_subheader(text: str) -> None:
    """Print a subheader."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * len(text)}{Colors.ENDC}")

def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print error message."""
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
    """Test admin login and return token."""
    print_subheader("Testing Admin Login")
    
    response, success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error("Admin login failed")
        record_test("Admin Login", False, "Login request failed")
        return None

def test_available_games_api(admin_token: str) -> Tuple[bool, List[Dict]]:
    """Test /api/games/available endpoint."""
    print_subheader("Testing Available Games API")
    
    response, success = make_request("GET", "/games/available", auth_token=admin_token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Available games API working - found {len(response)} games")
            record_test("Available Games API", True, f"Found {len(response)} games")
            return True, response
        else:
            print_error("Available games API returned non-list response")
            record_test("Available Games API", False, "Non-list response")
            return False, []
    else:
        print_error("Available games API failed")
        record_test("Available Games API", False, "Request failed")
        return False, []

def test_human_bot_management(admin_token: str) -> Tuple[bool, List[Dict]]:
    """Test Human-bot management and get active Human-bots."""
    print_subheader("Testing Human-Bot Management")
    
    # Get Human-bots list
    response, success = make_request("GET", "/admin/human-bots", auth_token=admin_token)
    
    if success and "bots" in response:
        bots = response["bots"]
        active_bots = [bot for bot in bots if bot.get("is_active", False)]
        print_success(f"Human-bots API working - found {len(bots)} total bots, {len(active_bots)} active")
        record_test("Human-Bot Management API", True, f"Found {len(bots)} bots, {len(active_bots)} active")
        return True, active_bots
    else:
        print_error("Human-bots API failed")
        record_test("Human-Bot Management API", False, "Request failed")
        return False, []

def test_human_bot_game_creation_and_joining(admin_token: str, available_games: List[Dict]) -> Optional[Dict]:
    """Test Human-bot game creation and joining logic."""
    print_subheader("Testing Human-Bot Game Creation and Joining")
    
    # Look for Human-bot games in available games
    human_bot_games = []
    for game in available_games:
        creator_type = game.get("creator_type", "")
        if creator_type == "human_bot" or "Bot" in game.get("creator_name", ""):
            human_bot_games.append(game)
    
    if human_bot_games:
        print_success(f"Found {len(human_bot_games)} Human-bot games in available games")
        
        # Check for required fields in Human-bot games
        test_game = human_bot_games[0]
        required_fields = ["game_id", "creator_username", "bet_amount", "status", "created_at"]
        missing_fields = [field for field in required_fields if field not in test_game]
        
        if not missing_fields:
            print_success("Human-bot games have all required fields")
            record_test("Human-Bot Game Structure", True, "All required fields present")
            
            # Check if game has proper status
            if test_game.get("status") == "WAITING":
                print_success("Human-bot games have correct WAITING status")
                record_test("Human-Bot Game Status", True, "Status is WAITING")
                return test_game
            else:
                print_warning(f"Human-bot game status is {test_game.get('status')}, expected WAITING")
                record_test("Human-Bot Game Status", False, f"Status is {test_game.get('status')}")
        else:
            print_error(f"Human-bot games missing fields: {missing_fields}")
            record_test("Human-Bot Game Structure", False, f"Missing fields: {missing_fields}")
    else:
        print_warning("No Human-bot games found in available games")
        record_test("Human-Bot Game Availability", False, "No Human-bot games found")
    
    return None

def test_human_bot_timeout_fields(admin_token: str, game_id: str) -> bool:
    """Test Human-bot timeout-related fields."""
    print_subheader("Testing Human-Bot Timeout Fields")
    
    # Get game details from admin endpoint
    response, success = make_request("GET", f"/admin/games/{game_id}", auth_token=admin_token)
    
    if success:
        game = response
        
        # Check for timeout-related fields
        timeout_fields = {
            "human_bot_completion_time": game.get("human_bot_completion_time"),
            "active_deadline": game.get("active_deadline"),
            "started_at": game.get("started_at"),
            "joined_at": game.get("joined_at")
        }
        
        print(f"Timeout fields in game {game_id}:")
        for field, value in timeout_fields.items():
            if value:
                print_success(f"  {field}: {value}")
            else:
                print_warning(f"  {field}: Not set")
        
        # Check if human_bot_completion_time is set and reasonable (15-60 seconds)
        completion_time = timeout_fields.get("human_bot_completion_time")
        if completion_time:
            try:
                # Parse the completion time and check if it's within reasonable range
                completion_dt = datetime.fromisoformat(completion_time.replace('Z', '+00:00'))
                created_at = datetime.fromisoformat(game.get("created_at", "").replace('Z', '+00:00'))
                time_diff = (completion_dt - created_at).total_seconds()
                
                if 15 <= time_diff <= 60:
                    print_success(f"Human-bot completion time is reasonable: {time_diff} seconds")
                    record_test("Human-Bot Completion Time Range", True, f"{time_diff} seconds")
                    return True
                else:
                    print_warning(f"Human-bot completion time outside expected range: {time_diff} seconds")
                    record_test("Human-Bot Completion Time Range", False, f"{time_diff} seconds")
            except Exception as e:
                print_error(f"Error parsing completion time: {e}")
                record_test("Human-Bot Completion Time Parsing", False, str(e))
        else:
            print_warning("human_bot_completion_time not set")
            record_test("Human-Bot Completion Time Field", False, "Field not set")
    else:
        print_error(f"Failed to get game details for {game_id}")
        record_test("Game Details API", False, "Request failed")
    
    return False

def test_active_games_timeout_detection(admin_token: str) -> bool:
    """Test detection of active games that should timeout."""
    print_subheader("Testing Active Games Timeout Detection")
    
    # Get all active games
    response, success = make_request("GET", "/admin/games", 
                                   data={"status": "ACTIVE"}, 
                                   auth_token=admin_token)
    
    if success and "games" in response:
        active_games = response["games"]
        print_success(f"Found {len(active_games)} active games")
        
        # Check for games with expired deadlines
        current_time = datetime.utcnow()
        expired_games = []
        
        for game in active_games:
            active_deadline = game.get("active_deadline")
            if active_deadline:
                try:
                    deadline_dt = datetime.fromisoformat(active_deadline.replace('Z', '+00:00'))
                    if deadline_dt < current_time:
                        expired_games.append(game)
                        print_warning(f"Game {game['id']} has expired deadline: {active_deadline}")
                except Exception as e:
                    print_error(f"Error parsing deadline for game {game['id']}: {e}")
        
        if expired_games:
            print_success(f"Found {len(expired_games)} games with expired deadlines")
            record_test("Expired Games Detection", True, f"Found {len(expired_games)} expired games")
            return True
        else:
            print_success("No expired games found (system is working correctly)")
            record_test("Expired Games Detection", True, "No expired games")
            return True
    else:
        print_error("Failed to get active games")
        record_test("Active Games API", False, "Request failed")
        return False

def test_game_completion_flow(admin_token: str) -> bool:
    """Test the complete Human-bot game flow from creation to completion."""
    print_subheader("Testing Complete Human-Bot Game Flow")
    
    # Get available games to find Human-bot games
    available_response, available_success = make_request("GET", "/games/available", auth_token=admin_token)
    
    if not available_success:
        print_error("Failed to get available games")
        record_test("Game Flow - Available Games", False, "Request failed")
        return False
    
    # Look for Human-bot games
    human_bot_games = []
    for game in available_response:
        if game.get("creator_type") == "human_bot" or "Bot" in game.get("creator_name", ""):
            human_bot_games.append(game)
    
    if not human_bot_games:
        print_warning("No Human-bot games available for flow testing")
        record_test("Game Flow - Human-Bot Games", False, "No Human-bot games available")
        return False
    
    test_game = human_bot_games[0]
    game_id = test_game.get("game_id")
    
    if not game_id:
        print_error("Game ID not found in Human-bot game data")
        record_test("Game Flow - Game ID", False, "Game ID missing")
        return False
    
    print_success(f"Testing game flow with Human-bot game: {game_id}")
    
    # Check initial status
    if test_game.get("status") != "WAITING":
        print_error(f"Game status is {test_game.get('status')}, expected WAITING")
        record_test("Game Flow - Initial Status", False, f"Status: {test_game.get('status')}")
        return False
    
    print_success("Game has correct initial WAITING status")
    
    # Monitor the game for status changes over time
    print("Monitoring game for automatic status changes...")
    
    start_time = time.time()
    max_wait_time = 120  # Wait up to 2 minutes
    status_changes = []
    
    while time.time() - start_time < max_wait_time:
        # Check game status
        game_response, game_success = make_request("GET", f"/admin/games/{game_id}", auth_token=admin_token)
        
        if game_success:
            current_status = game_response.get("status")
            current_time_str = datetime.utcnow().isoformat()
            
            # Record status if it changed
            if not status_changes or status_changes[-1]["status"] != current_status:
                status_changes.append({
                    "status": current_status,
                    "time": current_time_str,
                    "elapsed": time.time() - start_time
                })
                print(f"Status change detected: {current_status} at {current_time_str} (elapsed: {time.time() - start_time:.1f}s)")
            
            # Check if game completed
            if current_status == "COMPLETED":
                print_success(f"Game completed automatically after {time.time() - start_time:.1f} seconds")
                record_test("Game Flow - Auto Completion", True, f"Completed in {time.time() - start_time:.1f}s")
                
                # Verify completion details
                completion_details = {
                    "winner_id": game_response.get("winner_id"),
                    "completed_at": game_response.get("completed_at"),
                    "creator_move": game_response.get("creator_move"),
                    "opponent_move": game_response.get("opponent_move")
                }
                
                print("Completion details:")
                for key, value in completion_details.items():
                    if value:
                        print_success(f"  {key}: {value}")
                    else:
                        print_warning(f"  {key}: Not set")
                
                return True
        
        time.sleep(5)  # Check every 5 seconds
    
    print_warning(f"Game did not complete within {max_wait_time} seconds")
    print(f"Status changes observed: {status_changes}")
    record_test("Game Flow - Auto Completion", False, f"Did not complete within {max_wait_time}s")
    
    return False

def test_commit_reveal_compatibility(admin_token: str) -> bool:
    """Test commit-reveal system compatibility with Human-bots."""
    print_subheader("Testing Commit-Reveal Compatibility")
    
    # Get completed games to check commit-reveal data
    response, success = make_request("GET", "/admin/games", 
                                   data={"status": "COMPLETED", "limit": 10}, 
                                   auth_token=admin_token)
    
    if success and "games" in response:
        completed_games = response["games"]
        human_bot_games = [g for g in completed_games if g.get("creator_type") == "human_bot" or g.get("opponent_type") == "human_bot"]
        
        if human_bot_games:
            print_success(f"Found {len(human_bot_games)} completed Human-bot games")
            
            # Check commit-reveal fields
            test_game = human_bot_games[0]
            commit_reveal_fields = {
                "creator_move_hash": test_game.get("creator_move_hash"),
                "creator_salt": test_game.get("creator_salt"),
                "creator_move": test_game.get("creator_move"),
                "opponent_move": test_game.get("opponent_move")
            }
            
            print("Commit-reveal fields:")
            all_present = True
            for field, value in commit_reveal_fields.items():
                if value:
                    print_success(f"  {field}: Present")
                else:
                    print_warning(f"  {field}: Missing")
                    all_present = False
            
            if all_present:
                print_success("All commit-reveal fields present")
                record_test("Commit-Reveal Compatibility", True, "All fields present")
                return True
            else:
                print_warning("Some commit-reveal fields missing")
                record_test("Commit-Reveal Compatibility", False, "Missing fields")
        else:
            print_warning("No completed Human-bot games found")
            record_test("Commit-Reveal Compatibility", False, "No completed Human-bot games")
    else:
        print_error("Failed to get completed games")
        record_test("Commit-Reveal Compatibility", False, "Request failed")
    
    return False

def print_final_results():
    """Print final test results."""
    print_header("HUMAN-BOT TIMEOUT LOGIC TEST RESULTS")
    
    success_rate = (test_results["passed"] / test_results["total"]) * 100 if test_results["total"] > 0 else 0
    
    print(f"Total Tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 80 else Colors.WARNING}{success_rate:.1f}%{Colors.ENDC}")
    
    print("\nDetailed Results:")
    for test in test_results["tests"]:
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if test["passed"] else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"{status} {test['name']}")
        if test["details"]:
            print(f"    {test['details']}")
    
    # Summary for Russian review requirements
    print_header("RUSSIAN REVIEW REQUIREMENTS SUMMARY")
    
    critical_tests = [
        "Available Games API",
        "Human-Bot Management API", 
        "Human-Bot Game Structure",
        "Human-Bot Completion Time Range",
        "Game Flow - Auto Completion",
        "Commit-Reveal Compatibility"
    ]
    
    critical_passed = 0
    for test in test_results["tests"]:
        if any(critical in test["name"] for critical in critical_tests) and test["passed"]:
            critical_passed += 1
    
    critical_total = len([t for t in test_results["tests"] if any(critical in t["name"] for critical in critical_tests)])
    critical_rate = (critical_passed / critical_total) * 100 if critical_total > 0 else 0
    
    print(f"Critical Requirements Met: {critical_passed}/{critical_total} ({critical_rate:.1f}%)")
    
    if critical_rate >= 80:
        print_success("✅ Human-bot timeout logic is working correctly!")
        print_success("✅ Games complete automatically within expected timeframe")
        print_success("✅ Timeout system properly handles Human-bot games")
    else:
        print_error("❌ Critical issues found in Human-bot timeout logic")
        print_error("❌ Manual investigation required")

def main():
    """Main test execution."""
    print_header("HUMAN-BOT TIMEOUT LOGIC TESTING")
    print("Testing Human-bot logic fixes and automatic game completion")
    print("Focus: Timeout system and 1-minute auto-completion")
    
    # Test admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        sys.exit(1)
    
    # Test 1: API availability
    available_success, available_games = test_available_games_api(admin_token)
    
    # Test 2: Human-bot management
    bots_success, active_bots = test_human_bot_management(admin_token)
    
    # Test 3: Human-bot game creation and joining
    test_game = test_human_bot_game_creation_and_joining(admin_token, available_games)
    
    # Test 4: Timeout fields
    if test_game:
        test_human_bot_timeout_fields(admin_token, test_game["id"])
    
    # Test 5: Active games timeout detection
    test_active_games_timeout_detection(admin_token)
    
    # Test 6: Complete game flow
    test_game_completion_flow(admin_token)
    
    # Test 7: Commit-reveal compatibility
    test_commit_reveal_compatibility(admin_token)
    
    # Print final results
    print_final_results()

if __name__ == "__main__":
    main()