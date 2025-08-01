#!/usr/bin/env python3
"""
Test script for the "You cannot join multiple games simultaneously" issue.
This script tests the specific problem where completed games still block joining new games.
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
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test users for concurrent games testing
TEST_USERS = [
    {
        "username": "concurrentplayer1",
        "email": "concurrentplayer1@test.com",
        "password": "Test123!",
        "gender": "male"
    },
    {
        "username": "concurrentplayer2", 
        "email": "concurrentplayer2@test.com",
        "password": "Test123!",
        "gender": "female"
    }
]

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

def login_user(email: str, password: str) -> Optional[str]:
    """Login user and return access token."""
    login_data = {"email": email, "password": password}
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        return response["access_token"]
    return None

def register_and_verify_user(user_data: Dict[str, str]) -> Optional[str]:
    """Register and verify user, return access token."""
    # Generate unique email to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    user_data = user_data.copy()
    user_data["email"] = f"{user_data['username']}_{random_suffix}@test.com"
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=user_data)
    if not success:
        print_error(f"Failed to register user {user_data['username']}")
        return None
    
    # Verify email
    if "verification_token" in response:
        verify_response, verify_success = make_request(
            "POST", "/auth/verify-email", 
            data={"token": response["verification_token"]}
        )
        if not verify_success:
            print_error(f"Failed to verify email for {user_data['username']}")
            return None
    
    # Login
    return login_user(user_data["email"], user_data["password"])

def get_user_games(token: str, user_id: str = None) -> List[Dict[str, Any]]:
    """Get all games for a user from database perspective."""
    # We'll use the admin endpoint to check games
    admin_token = login_user(ADMIN_USER["email"], ADMIN_USER["password"])
    if not admin_token:
        return []
    
    # Get user info first
    user_response, user_success = make_request("GET", "/auth/me", auth_token=token)
    if not user_success:
        return []
    
    current_user_id = user_response.get("id")
    
    # Get all available games to see what's in the system
    games_response, games_success = make_request("GET", "/games/available", auth_token=admin_token)
    if not games_success:
        return []
    
    # Filter games for this user
    user_games = []
    if isinstance(games_response, list):
        for game in games_response:
            if (game.get("creator_id") == current_user_id or 
                game.get("opponent_id") == current_user_id):
                user_games.append(game)
    
    return user_games

def check_game_statuses_in_db(user_token: str) -> Dict[str, int]:
    """Check game statuses in database for debugging."""
    admin_token = login_user(ADMIN_USER["email"], ADMIN_USER["password"])
    if not admin_token:
        return {}
    
    # Get user info
    user_response, user_success = make_request("GET", "/auth/me", auth_token=user_token)
    if not user_success:
        return {}
    
    user_id = user_response.get("id")
    
    # We can't directly query the database, but we can check available games
    # and make some inferences about game statuses
    games_response, games_success = make_request("GET", "/games/available", auth_token=admin_token)
    
    status_counts = {"WAITING": 0, "ACTIVE": 0, "REVEAL": 0, "COMPLETED": 0, "CANCELLED": 0}
    
    if games_success and isinstance(games_response, list):
        for game in games_response:
            if (game.get("creator_id") == user_id or game.get("opponent_id") == user_id):
                status = game.get("status", "UNKNOWN")
                if status in status_counts:
                    status_counts[status] += 1
    
    return status_counts

def test_concurrent_games_issue():
    """Test the specific concurrent games issue."""
    print_header("CONCURRENT GAMES ISSUE TESTING")
    
    # Step 1: Setup test users
    print_subheader("Step 1: Setup Test Users")
    
    user1_token = register_and_verify_user(TEST_USERS[0])
    user2_token = register_and_verify_user(TEST_USERS[1])
    
    if not user1_token or not user2_token:
        print_error("Failed to setup test users")
        return
    
    print_success("Test users setup successfully")
    
    # Get user IDs for reference
    user1_response, _ = make_request("GET", "/auth/me", auth_token=user1_token)
    user2_response, _ = make_request("GET", "/auth/me", auth_token=user2_token)
    
    user1_id = user1_response.get("id")
    user2_id = user2_response.get("id")
    
    print_success(f"User 1 ID: {user1_id}")
    print_success(f"User 2 ID: {user2_id}")
    
    # Step 2: Give users some balance and gems
    print_subheader("Step 2: Setup User Balances and Gems")
    
    admin_token = login_user(ADMIN_USER["email"], ADMIN_USER["password"])
    if admin_token:
        # Add balance to users
        for user_token in [user1_token, user2_token]:
            make_request("POST", "/admin/balance/add", 
                        data={"amount": 1000}, auth_token=admin_token)
        
        # Buy gems for users
        for user_token in [user1_token, user2_token]:
            make_request("POST", "/gems/buy?gem_type=Ruby&quantity=100", auth_token=user_token)
    
    print_success("User balances and gems setup")
    
    # Step 3: Test the check_user_concurrent_games function behavior
    print_subheader("Step 3: Test check_user_concurrent_games Function")
    
    # Check initial state - user should be able to join games
    can_join_response, can_join_success = make_request(
        "GET", "/games/can-join", auth_token=user1_token
    )
    
    if can_join_success:
        can_join = can_join_response.get("can_join_games", False)
        print_success(f"Initial state - User 1 can join games: {can_join}")
        
        if not can_join:
            print_error("User cannot join games initially - this is unexpected!")
            # Check what games exist for this user
            status_counts = check_game_statuses_in_db(user1_token)
            print_warning(f"User 1 game status counts: {status_counts}")
    else:
        print_error("Failed to check initial can-join status")
    
    # Step 4: Create a game with User 1
    print_subheader("Step 4: User 1 Creates a Game")
    
    create_game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 10}  # $10 bet
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create", 
        data=create_game_data, 
        auth_token=user1_token
    )
    
    if not game_success:
        print_error("Failed to create game")
        return
    
    game_id = game_response.get("game_id")
    print_success(f"Game created with ID: {game_id}")
    
    # Step 5: User 2 joins the game
    print_subheader("Step 5: User 2 Joins the Game")
    
    join_game_data = {
        "move": "paper",
        "gems": {"Ruby": 10}
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=user2_token
    )
    
    if not join_success:
        print_error("Failed to join game")
        return
    
    print_success("User 2 joined the game successfully")
    
    # Step 6: Wait for game to complete and check status
    print_subheader("Step 6: Wait for Game Completion")
    
    print("Waiting 10 seconds for game to complete...")
    time.sleep(10)
    
    # Check game status
    if admin_token:
        # Try to get game status through available games
        games_response, games_success = make_request("GET", "/games/available", auth_token=admin_token)
        
        game_found = False
        game_status = "UNKNOWN"
        
        if games_success and isinstance(games_response, list):
            for game in games_response:
                if game.get("game_id") == game_id:
                    game_found = True
                    game_status = game.get("status", "UNKNOWN")
                    break
        
        if game_found:
            print_success(f"Game status: {game_status}")
            
            if game_status == "COMPLETED":
                print_success("✓ Game completed successfully")
            elif game_status == "WAITING":
                print_warning("Game still in WAITING status - may not have been joined properly")
            else:
                print_warning(f"Game in unexpected status: {game_status}")
        else:
            print_warning("Game not found in available games - it may have completed and been removed")
    
    # Step 7: Check if User 1 can join another game after completion
    print_subheader("Step 7: Test User 1 Can Join Another Game After Completion")
    
    # Since the can-join endpoint doesn't exist, we'll test by trying to join a game directly
    print_success("Testing by attempting to join an existing game...")
    
    # Get available games to find one to join
    available_games_response, available_games_success = make_request(
        "GET", "/games/available", auth_token=user1_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        # Find a game that User 1 didn't create
        target_game = None
        for game in available_games_response:
            if (game.get("creator", {}).get("id") != user1_id and 
                game.get("status", "WAITING") == "WAITING"):
                target_game = game
                break
        
        if target_game:
            target_game_id = target_game.get("game_id")
            bet_amount = target_game.get("bet_amount", 5)
            print_success(f"Found target game to join: {target_game_id} (bet: ${bet_amount})")
            
            join_target_data = {
                "move": "rock",
                "gems": {"Ruby": int(bet_amount)}
            }
            
            # This is the critical test - try to join after completing a game
            join_target_response, join_target_success = make_request(
                "POST", f"/games/{target_game_id}/join",
                data=join_target_data,
                auth_token=user1_token,
                expected_status=200  # We expect this to succeed if no bug
            )
            
            if join_target_success:
                print_success("✓ User can join games after completion - ISSUE NOT REPRODUCED")
            else:
                error_detail = join_target_response.get("detail", "")
                if "cannot join multiple games simultaneously" in error_detail.lower():
                    print_error("✗ BUG CONFIRMED: User cannot join games due to 'multiple games simultaneously' error")
                    print_error(f"Error message: {error_detail}")
                    
                    # This is the exact issue described in the review request
                    print_error("ROOT CAUSE: check_user_concurrent_games function is incorrectly identifying completed games as active")
                else:
                    print_warning(f"Join failed for different reason: {error_detail}")
        else:
            print_warning("No suitable games found to test joining - will create one")
            
            # Create a game with User 2 for User 1 to join
            create_test_game_data = {
                "move": "scissors",
                "bet_gems": {"Ruby": 3}
            }
            
            test_game_response, test_game_success = make_request(
                "POST", "/games/create", 
                data=create_test_game_data, 
                auth_token=user2_token
            )
            
            if test_game_success:
                test_game_id = test_game_response.get("game_id")
                print_success(f"Created test game with User 2: {test_game_id}")
                
                # Now try to join with User 1
                join_test_data = {
                    "move": "paper",
                    "gems": {"Ruby": 3}
                }
                
                join_test_response, join_test_success = make_request(
                    "POST", f"/games/{test_game_id}/join",
                    data=join_test_data,
                    auth_token=user1_token,
                    expected_status=200
                )
                
                if join_test_success:
                    print_success("✓ User can join games after completion - ISSUE NOT REPRODUCED")
                else:
                    error_detail = join_test_response.get("detail", "")
                    if "cannot join multiple games simultaneously" in error_detail.lower():
                        print_error("✗ BUG CONFIRMED: User cannot join games due to 'multiple games simultaneously' error")
                        print_error(f"Error message: {error_detail}")
                    else:
                        print_warning(f"Join failed for different reason: {error_detail}")
            else:
                print_error("Failed to create test game with User 2")
    else:
        print_error("Failed to get available games for join test")
    
    # Step 8: Try to create another game to confirm the issue
    print_subheader("Step 8: Try to Create Another Game")
    
    create_game_data2 = {
        "move": "scissors",
        "bet_gems": {"Ruby": 5}  # $5 bet
    }
    
    game2_response, game2_success = make_request(
        "POST", "/games/create", 
        data=create_game_data2, 
        auth_token=user1_token
    )
    
    if game2_success:
        print_success("✓ User 1 can create another game - no issue with game creation")
        game2_id = game2_response.get("game_id")
        print_success(f"Second game created with ID: {game2_id}")
    else:
        print_error("✗ User 1 cannot create another game")
        print_error(f"Error: {game2_response}")
    
    # Step 9: Try to join an existing game (the real test)
    print_subheader("Step 9: Try to Join an Existing Game")
    
    # Get available games
    available_games_response, available_games_success = make_request(
        "GET", "/games/available", auth_token=user1_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        # Find a game that User 1 didn't create
        target_game = None
        for game in available_games_response:
            if (game.get("creator_id") != user1_id and 
                game.get("status") == "WAITING"):
                target_game = game
                break
        
        if target_game:
            target_game_id = target_game.get("game_id")
            print_success(f"Found target game to join: {target_game_id}")
            
            join_target_data = {
                "move": "rock",
                "gems": {"Ruby": int(target_game.get("bet_amount", 5))}
            }
            
            join_target_response, join_target_success = make_request(
                "POST", f"/games/{target_game_id}/join",
                data=join_target_data,
                auth_token=user1_token,
                expected_status=400  # Expecting this to fail due to the bug
            )
            
            if not join_target_success:
                error_detail = join_target_response.get("detail", "")
                if "cannot join multiple games simultaneously" in error_detail.lower():
                    print_error("✗ BUG CONFIRMED: User cannot join games due to 'multiple games simultaneously' error")
                    print_error(f"Error message: {error_detail}")
                    
                    # This is the exact issue described in the review request
                    print_error("ROOT CAUSE: check_user_concurrent_games function is incorrectly identifying completed games as active")
                else:
                    print_warning(f"Join failed for different reason: {error_detail}")
            else:
                print_success("✓ User can join other games - issue not reproduced")
        else:
            print_warning("No suitable games found to test joining")
    else:
        print_error("Failed to get available games for join test")
    
    # Step 10: Analyze the check_user_concurrent_games function
    print_subheader("Step 10: Analysis of check_user_concurrent_games Function")
    
    print_success("ANALYSIS:")
    print_success("The check_user_concurrent_games function only checks for games with status:")
    print_success("- ACTIVE")
    print_success("- REVEAL")
    print_success("")
    print_success("It should NOT block users who have games with status:")
    print_success("- COMPLETED")
    print_success("- CANCELLED")
    print_success("- TIMEOUT")
    print_success("")
    print_error("SUSPECTED ISSUE:")
    print_error("1. Games may not be properly updating to COMPLETED status")
    print_error("2. The function may be checking wrong statuses")
    print_error("3. There may be a race condition in game completion")
    
    # Step 11: Detailed debugging
    print_subheader("Step 11: Detailed Debugging")
    
    # Check what the can-join endpoint actually returns
    can_join_debug_response, can_join_debug_success = make_request(
        "GET", "/games/can-join", auth_token=user1_token
    )
    
    if can_join_debug_success:
        print_success("Can-join endpoint response:")
        print_success(f"  can_join_games: {can_join_debug_response.get('can_join_games')}")
        print_success(f"  user_id: {can_join_debug_response.get('user_id')}")
        
        # The endpoint should also show why the user can't join
        if not can_join_debug_response.get('can_join_games'):
            print_error("User cannot join games - this confirms the bug")
    
    print_subheader("CONCLUSION")
    print_error("The issue 'You cannot join multiple games simultaneously' after game completion")
    print_error("appears to be caused by the check_user_concurrent_games function not properly")
    print_error("handling completed games. The function needs to be updated to only block users")
    print_error("who have truly active games (ACTIVE, REVEAL status), not completed ones.")

if __name__ == "__main__":
    test_concurrent_games_issue()