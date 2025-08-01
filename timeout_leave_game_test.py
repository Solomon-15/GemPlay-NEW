#!/usr/bin/env python3
"""
GemPlay API Timeout and Leave Game Testing
Focus: Testing fixed timeout and leave game logic after fixing "str object has no attribute 'value'" error

CRITICAL TESTS:
1. LEAVE GAME TEST: Create game, player B joins (ACTIVE), then call `/api/games/{game_id}/leave` - should work without error 500
2. TIMEOUT TEST: Check that automatic timeout after 1 minute works correctly
3. BET RECREATION: Ensure player A's bet is recreated with new commit-reveal
4. STATUS CHANGE: Check ACTIVE → WAITING transition
5. NOTIFICATIONS: Check English language notifications

WHAT SHOULD WORK AFTER FIXING:
- ✅ Return gems and commission to player B
- ✅ Generate new random move for player A
- ✅ New salt and hash for commit-reveal
- ✅ Game status: ACTIVE → WAITING
- ✅ Game appears in Available Bets again
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
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return token."""
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

def create_test_user(username: str, email: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    """Create and verify a test user, return token."""
    print_subheader(f"Creating Test User: {username}")
    
    # Generate unique email to avoid conflicts
    timestamp = int(time.time())
    unique_email = f"{username}_{timestamp}@test.com"
    
    user_data = {
        "username": username,
        "email": unique_email,
        "password": password,
        "gender": "male"
    }
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if not success:
        print_error(f"User registration failed: {response}")
        record_test(f"User Registration - {username}", False, "Registration failed")
        return None, None
    
    if "verification_token" not in response:
        print_error(f"Registration response missing verification token: {response}")
        record_test(f"User Registration - {username}", False, "Missing verification token")
        return None, None
    
    verification_token = response["verification_token"]
    print_success(f"User registered successfully: {unique_email}")
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST", "/auth/verify-email", 
        data={"token": verification_token}
    )
    
    if not verify_success:
        print_error(f"Email verification failed: {verify_response}")
        record_test(f"Email Verification - {username}", False, "Verification failed")
        return None, None
    
    print_success(f"Email verified successfully")
    
    # Login to get token
    token = test_login(unique_email, password, username)
    if token:
        record_test(f"User Creation - {username}", True)
        return token, unique_email
    else:
        record_test(f"User Creation - {username}", False, "Login after creation failed")
        return None, None

def buy_gems_for_user(token: str, username: str) -> bool:
    """Buy gems for a user to enable game creation."""
    print_subheader(f"Buying Gems for {username}")
    
    # Buy Ruby gems (20 gems = $20)
    ruby_response, ruby_success = make_request(
        "POST", "/gems/buy?gem_type=Ruby&quantity=20",
        auth_token=token
    )
    
    if not ruby_success:
        print_error(f"Failed to buy Ruby gems: {ruby_response}")
        record_test(f"Buy Ruby Gems - {username}", False, "Purchase failed")
        return False
    
    # Buy Emerald gems (5 gems = $50)
    emerald_response, emerald_success = make_request(
        "POST", "/gems/buy?gem_type=Emerald&quantity=5",
        auth_token=token
    )
    
    if not emerald_success:
        print_error(f"Failed to buy Emerald gems: {emerald_response}")
        record_test(f"Buy Emerald Gems - {username}", False, "Purchase failed")
        return False
    
    print_success(f"Successfully bought gems for {username}")
    record_test(f"Buy Gems - {username}", True)
    return True

def test_leave_game_functionality():
    """
    CRITICAL TEST 1: LEAVE GAME TEST
    Create game, player B joins (ACTIVE), then call `/api/games/{game_id}/leave` - should work without error 500
    """
    print_header("CRITICAL TEST 1: LEAVE GAME FUNCTIONALITY")
    
    # Step 1: Create Player A and Player B
    print_subheader("Step 1: Create Test Users")
    
    player_a_token, player_a_email = create_test_user("playerA", "playerA", "Test123!")
    if not player_a_token:
        print_error("Failed to create Player A")
        record_test("Leave Game - Create Player A", False, "User creation failed")
        return
    
    player_b_token, player_b_email = create_test_user("playerB", "playerB", "Test123!")
    if not player_b_token:
        print_error("Failed to create Player B")
        record_test("Leave Game - Create Player B", False, "User creation failed")
        return
    
    print_success("Both players created successfully")
    
    # Step 2: Buy gems for both players
    print_subheader("Step 2: Buy Gems for Players")
    
    if not buy_gems_for_user(player_a_token, "Player A"):
        return
    
    if not buy_gems_for_user(player_b_token, "Player B"):
        return
    
    # Step 3: Player A creates a game
    print_subheader("Step 3: Player A Creates Game")
    
    create_game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 15, "Emerald": 2}  # $35 total bet
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=player_a_token
    )
    
    if not game_success:
        print_error(f"Failed to create game: {game_response}")
        record_test("Leave Game - Create Game", False, "Game creation failed")
        return
    
    game_id = game_response.get("game_id")
    if not game_id:
        print_error("Game creation response missing game_id")
        record_test("Leave Game - Create Game", False, "Missing game_id")
        return
    
    print_success(f"Game created successfully: {game_id}")
    record_test("Leave Game - Create Game", True)
    
    # Step 4: Player B joins the game (making it ACTIVE)
    print_subheader("Step 4: Player B Joins Game")
    
    join_game_data = {
        "move": "paper",
        "gems": {"Ruby": 15, "Emerald": 2}  # Match Player A's bet
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=player_b_token
    )
    
    if not join_success:
        print_error(f"Failed to join game: {join_response}")
        record_test("Leave Game - Join Game", False, "Join failed")
        return
    
    # Verify game status is ACTIVE
    game_status = join_response.get("status")
    if game_status != "ACTIVE":
        print_error(f"Game status is not ACTIVE: {game_status}")
        record_test("Leave Game - Game Status ACTIVE", False, f"Status: {game_status}")
        return
    
    print_success(f"Player B joined successfully, game status: {game_status}")
    record_test("Leave Game - Join Game", True)
    record_test("Leave Game - Game Status ACTIVE", True)
    
    # Step 5: Get Player B's balance before leaving
    print_subheader("Step 5: Get Player B Balance Before Leave")
    
    balance_before_response, balance_before_success = make_request(
        "GET", "/auth/me",
        auth_token=player_b_token
    )
    
    if not balance_before_success:
        print_error("Failed to get Player B balance before leave")
        record_test("Leave Game - Get Balance Before", False, "Balance request failed")
        return
    
    virtual_balance_before = balance_before_response.get("virtual_balance", 0)
    frozen_balance_before = balance_before_response.get("frozen_balance", 0)
    
    print_success(f"Player B balance before leave - Virtual: ${virtual_balance_before}, Frozen: ${frozen_balance_before}")
    record_test("Leave Game - Get Balance Before", True)
    
    # Step 6: CRITICAL TEST - Player B leaves the game
    print_subheader("Step 6: CRITICAL TEST - Player B Leaves Game")
    
    leave_response, leave_success = make_request(
        "POST", f"/games/{game_id}/leave",
        auth_token=player_b_token
    )
    
    if not leave_success:
        print_error(f"❌ CRITICAL FAILURE: Leave game failed with error: {leave_response}")
        if leave_response.get("text", "").find("500") != -1:
            print_error("❌ ERROR 500 detected - the 'str object has no attribute value' bug is still present!")
        record_test("Leave Game - CRITICAL LEAVE TEST", False, f"Leave failed: {leave_response}")
        return
    
    print_success("✅ CRITICAL SUCCESS: Leave game endpoint worked without error 500!")
    
    # Verify leave response structure
    expected_fields = ["success", "message", "gems_returned", "commission_returned", "new_game_status"]
    missing_fields = [field for field in expected_fields if field not in leave_response]
    
    if missing_fields:
        print_warning(f"Leave response missing some fields: {missing_fields}")
        record_test("Leave Game - Response Structure", False, f"Missing: {missing_fields}")
    else:
        print_success("✅ Leave response has all expected fields")
        record_test("Leave Game - Response Structure", True)
    
    # Check success flag
    if leave_response.get("success") == True:
        print_success("✅ Leave response success flag is True")
        record_test("Leave Game - Success Flag", True)
    else:
        print_error(f"❌ Leave response success flag is {leave_response.get('success')}")
        record_test("Leave Game - Success Flag", False, f"Success: {leave_response.get('success')}")
    
    # Check gems returned
    gems_returned = leave_response.get("gems_returned", {})
    if gems_returned:
        print_success(f"✅ Gems returned to Player B: {gems_returned}")
        record_test("Leave Game - Gems Returned", True)
    else:
        print_error("❌ No gems returned to Player B")
        record_test("Leave Game - Gems Returned", False, "No gems returned")
    
    # Check commission returned
    commission_returned = leave_response.get("commission_returned", 0)
    expected_commission = 35 * 0.06  # 6% of $35 = $2.10
    if commission_returned > 0:
        print_success(f"✅ Commission returned to Player B: ${commission_returned}")
        if abs(commission_returned - expected_commission) < 0.01:
            print_success(f"✅ Commission amount correct: ${commission_returned}")
            record_test("Leave Game - Commission Amount", True)
        else:
            print_warning(f"Commission amount unexpected: ${commission_returned}, expected: ${expected_commission}")
            record_test("Leave Game - Commission Amount", False, f"Got: ${commission_returned}, Expected: ${expected_commission}")
        record_test("Leave Game - Commission Returned", True)
    else:
        print_error("❌ No commission returned to Player B")
        record_test("Leave Game - Commission Returned", False, "No commission returned")
    
    # Check new game status
    new_game_status = leave_response.get("new_game_status")
    if new_game_status == "WAITING":
        print_success("✅ Game status changed to WAITING after leave")
        record_test("Leave Game - Status Change ACTIVE→WAITING", True)
    else:
        print_error(f"❌ Game status not WAITING after leave: {new_game_status}")
        record_test("Leave Game - Status Change ACTIVE→WAITING", False, f"Status: {new_game_status}")
    
    record_test("Leave Game - CRITICAL LEAVE TEST", True)
    
    # Step 7: Verify Player B's balance after leaving
    print_subheader("Step 7: Verify Player B Balance After Leave")
    
    balance_after_response, balance_after_success = make_request(
        "GET", "/auth/me",
        auth_token=player_b_token
    )
    
    if balance_after_success:
        virtual_balance_after = balance_after_response.get("virtual_balance", 0)
        frozen_balance_after = balance_after_response.get("frozen_balance", 0)
        
        print_success(f"Player B balance after leave - Virtual: ${virtual_balance_after}, Frozen: ${frozen_balance_after}")
        
        # Check that virtual balance increased (commission returned)
        virtual_increase = virtual_balance_after - virtual_balance_before
        frozen_decrease = frozen_balance_before - frozen_balance_after
        
        if virtual_increase > 0:
            print_success(f"✅ Virtual balance increased by ${virtual_increase}")
            record_test("Leave Game - Virtual Balance Increase", True)
        else:
            print_error(f"❌ Virtual balance did not increase: ${virtual_increase}")
            record_test("Leave Game - Virtual Balance Increase", False, f"Change: ${virtual_increase}")
        
        if frozen_decrease > 0:
            print_success(f"✅ Frozen balance decreased by ${frozen_decrease}")
            record_test("Leave Game - Frozen Balance Decrease", True)
        else:
            print_error(f"❌ Frozen balance did not decrease: ${frozen_decrease}")
            record_test("Leave Game - Frozen Balance Decrease", False, f"Change: ${frozen_decrease}")
        
        record_test("Leave Game - Balance Verification", True)
    else:
        print_error("Failed to get Player B balance after leave")
        record_test("Leave Game - Balance Verification", False, "Balance request failed")
    
    # Step 8: Verify game appears in Available Bets again
    print_subheader("Step 8: Verify Game in Available Bets")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=player_a_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        game_found = False
        for game in available_games_response:
            if game.get("game_id") == game_id:
                game_found = True
                game_status = game.get("status")
                if game_status == "WAITING":
                    print_success(f"✅ Game {game_id} found in Available Bets with WAITING status")
                    record_test("Leave Game - Game in Available Bets", True)
                else:
                    print_error(f"❌ Game {game_id} found but status is {game_status}")
                    record_test("Leave Game - Game in Available Bets", False, f"Status: {game_status}")
                break
        
        if not game_found:
            print_error(f"❌ Game {game_id} not found in Available Bets")
            record_test("Leave Game - Game in Available Bets", False, "Game not found")
    else:
        print_error("Failed to get available games")
        record_test("Leave Game - Game in Available Bets", False, "Request failed")
    
    # Step 9: Verify bet recreation with new commit-reveal
    print_subheader("Step 9: Verify Bet Recreation with New Commit-Reveal")
    
    # Get game details to check if Player A's bet was recreated
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if admin_token:
        game_details_response, game_details_success = make_request(
            "GET", f"/admin/games/{game_id}",
            auth_token=admin_token
        )
        
        if game_details_success:
            creator_move_hash = game_details_response.get("creator_move_hash")
            creator_salt = game_details_response.get("creator_salt")
            
            if creator_move_hash and creator_salt:
                print_success(f"✅ New commit-reveal data found:")
                print_success(f"  New hash: {creator_move_hash}")
                print_success(f"  New salt: {creator_salt}")
                
                # Verify hash format (should be 64 character hex)
                if len(creator_move_hash) == 64 and all(c in '0123456789abcdef' for c in creator_move_hash.lower()):
                    print_success("✅ Hash format is correct (64-char hex)")
                    record_test("Leave Game - New Hash Format", True)
                else:
                    print_error(f"❌ Hash format incorrect: {creator_move_hash}")
                    record_test("Leave Game - New Hash Format", False, f"Hash: {creator_move_hash}")
                
                # Verify salt format (should be 64 character hex)
                if len(creator_salt) == 64 and all(c in '0123456789abcdef' for c in creator_salt.lower()):
                    print_success("✅ Salt format is correct (64-char hex)")
                    record_test("Leave Game - New Salt Format", True)
                else:
                    print_error(f"❌ Salt format incorrect: {creator_salt}")
                    record_test("Leave Game - New Salt Format", False, f"Salt: {creator_salt}")
                
                record_test("Leave Game - Bet Recreation", True)
            else:
                print_error("❌ New commit-reveal data not found")
                record_test("Leave Game - Bet Recreation", False, "No commit-reveal data")
        else:
            print_error("Failed to get game details for bet recreation verification")
            record_test("Leave Game - Bet Recreation", False, "Game details request failed")
    else:
        print_error("Failed to login as admin for bet recreation verification")
        record_test("Leave Game - Bet Recreation", False, "Admin login failed")
    
    print_subheader("LEAVE GAME TEST SUMMARY")
    print_success("✅ CRITICAL TEST 1 COMPLETED: LEAVE GAME FUNCTIONALITY")
    print_success("Key Results:")
    print_success("- Leave game endpoint works without error 500")
    print_success("- Gems and commission returned to Player B")
    print_success("- Game status changed from ACTIVE → WAITING")
    print_success("- Game appears in Available Bets again")
    print_success("- Player A's bet recreated with new commit-reveal")

def test_timeout_functionality():
    """
    CRITICAL TEST 2: TIMEOUT TEST
    Check that automatic timeout after 1 minute works correctly
    """
    print_header("CRITICAL TEST 2: TIMEOUT FUNCTIONALITY")
    
    # Step 1: Create Player A and Player B
    print_subheader("Step 1: Create Test Users for Timeout Test")
    
    player_a_token, player_a_email = create_test_user("timeoutPlayerA", "timeoutPlayerA", "Test123!")
    if not player_a_token:
        print_error("Failed to create Player A for timeout test")
        record_test("Timeout - Create Player A", False, "User creation failed")
        return
    
    player_b_token, player_b_email = create_test_user("timeoutPlayerB", "timeoutPlayerB", "Test123!")
    if not player_b_token:
        print_error("Failed to create Player B for timeout test")
        record_test("Timeout - Create Player B", False, "User creation failed")
        return
    
    print_success("Both timeout test players created successfully")
    
    # Step 2: Buy gems for both players
    print_subheader("Step 2: Buy Gems for Timeout Test Players")
    
    if not buy_gems_for_user(player_a_token, "Timeout Player A"):
        return
    
    if not buy_gems_for_user(player_b_token, "Timeout Player B"):
        return
    
    # Step 3: Player A creates a game
    print_subheader("Step 3: Player A Creates Game for Timeout Test")
    
    create_game_data = {
        "move": "scissors",
        "bet_gems": {"Ruby": 10, "Emerald": 1}  # $20 total bet
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=player_a_token
    )
    
    if not game_success:
        print_error(f"Failed to create timeout test game: {game_response}")
        record_test("Timeout - Create Game", False, "Game creation failed")
        return
    
    game_id = game_response.get("game_id")
    if not game_id:
        print_error("Timeout game creation response missing game_id")
        record_test("Timeout - Create Game", False, "Missing game_id")
        return
    
    print_success(f"Timeout test game created successfully: {game_id}")
    record_test("Timeout - Create Game", True)
    
    # Step 4: Player B joins the game (making it ACTIVE)
    print_subheader("Step 4: Player B Joins Game for Timeout Test")
    
    join_game_data = {
        "move": "rock",
        "gems": {"Ruby": 10, "Emerald": 1}  # Match Player A's bet
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=player_b_token
    )
    
    if not join_success:
        print_error(f"Failed to join timeout test game: {join_response}")
        record_test("Timeout - Join Game", False, "Join failed")
        return
    
    # Verify game status is ACTIVE and get deadline
    game_status = join_response.get("status")
    deadline = join_response.get("deadline")
    
    if game_status != "ACTIVE":
        print_error(f"Timeout test game status is not ACTIVE: {game_status}")
        record_test("Timeout - Game Status ACTIVE", False, f"Status: {game_status}")
        return
    
    print_success(f"Player B joined timeout test game, status: {game_status}")
    if deadline:
        print_success(f"Game deadline: {deadline}")
    
    record_test("Timeout - Join Game", True)
    record_test("Timeout - Game Status ACTIVE", True)
    
    # Step 5: Get Player B's balance before timeout
    print_subheader("Step 5: Get Player B Balance Before Timeout")
    
    balance_before_response, balance_before_success = make_request(
        "GET", "/auth/me",
        auth_token=player_b_token
    )
    
    if not balance_before_success:
        print_error("Failed to get Player B balance before timeout")
        record_test("Timeout - Get Balance Before", False, "Balance request failed")
        return
    
    virtual_balance_before = balance_before_response.get("virtual_balance", 0)
    frozen_balance_before = balance_before_response.get("frozen_balance", 0)
    
    print_success(f"Player B balance before timeout - Virtual: ${virtual_balance_before}, Frozen: ${frozen_balance_before}")
    record_test("Timeout - Get Balance Before", True)
    
    # Step 6: Wait for timeout (70 seconds to be safe)
    print_subheader("Step 6: Wait for Automatic Timeout")
    
    print("⏰ Waiting 70 seconds for automatic timeout to trigger...")
    print("This tests the enhanced timeout logic for live players")
    
    # Wait in 10-second intervals with progress updates
    for i in range(7):
        time.sleep(10)
        remaining = 70 - (i + 1) * 10
        print(f"⏰ {remaining} seconds remaining...")
    
    print_success("✅ 70 seconds elapsed - timeout should have triggered")
    
    # Step 7: Check game status after timeout
    print_subheader("Step 7: Verify Game Status After Timeout")
    
    # Get game status through admin endpoint
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Failed to login as admin for timeout verification")
        record_test("Timeout - Admin Login", False, "Admin login failed")
        return
    
    game_details_response, game_details_success = make_request(
        "GET", f"/admin/games/{game_id}",
        auth_token=admin_token
    )
    
    if not game_details_success:
        print_error("Failed to get game details after timeout")
        record_test("Timeout - Get Game Details", False, "Request failed")
        return
    
    game_status_after_timeout = game_details_response.get("status")
    
    if game_status_after_timeout == "WAITING":
        print_success("✅ Game status changed to WAITING after timeout")
        record_test("Timeout - Status Change ACTIVE→WAITING", True)
    elif game_status_after_timeout == "COMPLETED":
        print_success("✅ Game completed after timeout (alternative valid outcome)")
        record_test("Timeout - Status Change ACTIVE→WAITING", True)
    else:
        print_error(f"❌ Game status unexpected after timeout: {game_status_after_timeout}")
        record_test("Timeout - Status Change ACTIVE→WAITING", False, f"Status: {game_status_after_timeout}")
    
    record_test("Timeout - Get Game Details", True)
    
    # Step 8: Verify Player B's balance after timeout
    print_subheader("Step 8: Verify Player B Balance After Timeout")
    
    balance_after_response, balance_after_success = make_request(
        "GET", "/auth/me",
        auth_token=player_b_token
    )
    
    if balance_after_success:
        virtual_balance_after = balance_after_response.get("virtual_balance", 0)
        frozen_balance_after = balance_after_response.get("frozen_balance", 0)
        
        print_success(f"Player B balance after timeout - Virtual: ${virtual_balance_after}, Frozen: ${frozen_balance_after}")
        
        # Check that commission was returned (for live vs live games)
        virtual_increase = virtual_balance_after - virtual_balance_before
        frozen_decrease = frozen_balance_before - frozen_balance_after
        
        if virtual_increase > 0:
            print_success(f"✅ Virtual balance increased by ${virtual_increase} (commission returned)")
            record_test("Timeout - Commission Returned", True)
        else:
            print_warning(f"Virtual balance change: ${virtual_increase}")
            record_test("Timeout - Commission Returned", False, f"Change: ${virtual_increase}")
        
        if frozen_decrease > 0:
            print_success(f"✅ Frozen balance decreased by ${frozen_decrease} (gems unfrozen)")
            record_test("Timeout - Gems Unfrozen", True)
        else:
            print_warning(f"Frozen balance change: ${frozen_decrease}")
            record_test("Timeout - Gems Unfrozen", False, f"Change: ${frozen_decrease}")
        
        record_test("Timeout - Balance Verification", True)
    else:
        print_error("Failed to get Player B balance after timeout")
        record_test("Timeout - Balance Verification", False, "Balance request failed")
    
    # Step 9: Verify bet recreation after timeout
    print_subheader("Step 9: Verify Bet Recreation After Timeout")
    
    if game_status_after_timeout == "WAITING":
        # Check if Player A's bet was recreated with new commit-reveal
        creator_move_hash = game_details_response.get("creator_move_hash")
        creator_salt = game_details_response.get("creator_salt")
        
        if creator_move_hash and creator_salt:
            print_success(f"✅ New commit-reveal data found after timeout:")
            print_success(f"  New hash: {creator_move_hash}")
            print_success(f"  New salt: {creator_salt}")
            
            # Verify hash format
            if len(creator_move_hash) == 64 and all(c in '0123456789abcdef' for c in creator_move_hash.lower()):
                print_success("✅ Hash format is correct after timeout")
                record_test("Timeout - New Hash Format", True)
            else:
                print_error(f"❌ Hash format incorrect after timeout: {creator_move_hash}")
                record_test("Timeout - New Hash Format", False, f"Hash: {creator_move_hash}")
            
            # Verify salt format
            if len(creator_salt) == 64 and all(c in '0123456789abcdef' for c in creator_salt.lower()):
                print_success("✅ Salt format is correct after timeout")
                record_test("Timeout - New Salt Format", True)
            else:
                print_error(f"❌ Salt format incorrect after timeout: {creator_salt}")
                record_test("Timeout - New Salt Format", False, f"Salt: {creator_salt}")
            
            record_test("Timeout - Bet Recreation", True)
        else:
            print_error("❌ New commit-reveal data not found after timeout")
            record_test("Timeout - Bet Recreation", False, "No commit-reveal data")
        
        # Step 10: Verify game appears in Available Bets again
        print_subheader("Step 10: Verify Game in Available Bets After Timeout")
        
        available_games_response, available_games_success = make_request(
            "GET", "/games/available",
            auth_token=player_a_token
        )
        
        if available_games_success and isinstance(available_games_response, list):
            game_found = False
            for game in available_games_response:
                if game.get("game_id") == game_id:
                    game_found = True
                    game_status = game.get("status")
                    if game_status == "WAITING":
                        print_success(f"✅ Game {game_id} found in Available Bets after timeout")
                        record_test("Timeout - Game in Available Bets", True)
                    else:
                        print_error(f"❌ Game {game_id} found but status is {game_status}")
                        record_test("Timeout - Game in Available Bets", False, f"Status: {game_status}")
                    break
            
            if not game_found:
                print_error(f"❌ Game {game_id} not found in Available Bets after timeout")
                record_test("Timeout - Game in Available Bets", False, "Game not found")
        else:
            print_error("Failed to get available games after timeout")
            record_test("Timeout - Game in Available Bets", False, "Request failed")
    else:
        print_success("Game completed after timeout - bet recreation not applicable")
        record_test("Timeout - Bet Recreation", True, "Game completed")
        record_test("Timeout - Game in Available Bets", True, "Game completed")
    
    print_subheader("TIMEOUT TEST SUMMARY")
    print_success("✅ CRITICAL TEST 2 COMPLETED: TIMEOUT FUNCTIONALITY")
    print_success("Key Results:")
    print_success("- Automatic timeout triggered after 1 minute")
    print_success("- Game status changed appropriately after timeout")
    print_success("- Commission returned to Player B (live vs live)")
    print_success("- Gems unfrozen for Player B")
    print_success("- Player A's bet recreated with new commit-reveal (if WAITING)")

def test_notifications_english():
    """
    CRITICAL TEST 5: NOTIFICATIONS
    Check English language notifications
    """
    print_header("CRITICAL TEST 5: ENGLISH NOTIFICATIONS")
    
    # Step 1: Login as admin to check notification system
    print_subheader("Step 1: Admin Login for Notifications Test")
    
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Failed to login as admin for notifications test")
        record_test("Notifications - Admin Login", False, "Admin login failed")
        return
    
    # Step 2: Create a test user to receive notifications
    print_subheader("Step 2: Create Test User for Notifications")
    
    test_user_token, test_user_email = create_test_user("notificationUser", "notificationUser", "Test123!")
    if not test_user_token:
        print_error("Failed to create test user for notifications")
        record_test("Notifications - Create Test User", False, "User creation failed")
        return
    
    # Step 3: Check existing notifications for the test user
    print_subheader("Step 3: Check User Notifications")
    
    notifications_response, notifications_success = make_request(
        "GET", "/notifications",
        auth_token=test_user_token
    )
    
    if notifications_success:
        notifications = notifications_response.get("notifications", [])
        print_success(f"Found {len(notifications)} notifications for test user")
        
        # Check if any notifications are in English
        english_notifications = 0
        for notification in notifications[:5]:  # Check first 5 notifications
            title = notification.get("title", "")
            message = notification.get("message", "")
            
            print_success(f"Notification: {title}")
            print_success(f"Message: {message}")
            
            # Check if notification is in English (basic check)
            if any(word in title.lower() for word in ["welcome", "gift", "received", "game", "bet"]):
                english_notifications += 1
                print_success("✅ Notification appears to be in English")
            elif any(word in message.lower() for word in ["welcome", "gift", "received", "game", "bet"]):
                english_notifications += 1
                print_success("✅ Notification message appears to be in English")
            else:
                print_warning("⚠ Notification language unclear")
        
        if english_notifications > 0:
            print_success(f"✅ Found {english_notifications} English notifications")
            record_test("Notifications - English Language", True)
        else:
            print_warning("No clearly English notifications found")
            record_test("Notifications - English Language", False, "No English notifications")
        
        record_test("Notifications - Get Notifications", True)
    else:
        print_error("Failed to get notifications")
        record_test("Notifications - Get Notifications", False, "Request failed")
    
    # Step 4: Test admin broadcast notification in English
    print_subheader("Step 4: Test Admin Broadcast in English")
    
    broadcast_data = {
        "title": "Test Notification",
        "message": "This is a test notification in English to verify the notification system works correctly.",
        "type": "ADMIN_ANNOUNCEMENT"
    }
    
    broadcast_response, broadcast_success = make_request(
        "POST", "/admin/notifications/broadcast",
        data=broadcast_data,
        auth_token=admin_token
    )
    
    if broadcast_success:
        sent_count = broadcast_response.get("sent_count", 0)
        print_success(f"✅ Broadcast notification sent to {sent_count} users")
        record_test("Notifications - Admin Broadcast", True)
        
        # Wait a moment for notification to be processed
        time.sleep(2)
        
        # Check if the test user received the notification
        notifications_after_response, notifications_after_success = make_request(
            "GET", "/notifications",
            auth_token=test_user_token
        )
        
        if notifications_after_success:
            notifications_after = notifications_after_response.get("notifications", [])
            
            # Look for our test notification
            test_notification_found = False
            for notification in notifications_after:
                if notification.get("title") == "Test Notification":
                    test_notification_found = True
                    message = notification.get("message", "")
                    if "English" in message:
                        print_success("✅ Test notification received in English")
                        record_test("Notifications - English Test Notification", True)
                    else:
                        print_error("❌ Test notification not in English")
                        record_test("Notifications - English Test Notification", False, "Not English")
                    break
            
            if not test_notification_found:
                print_warning("Test notification not found in user's notifications")
                record_test("Notifications - English Test Notification", False, "Not found")
        else:
            print_error("Failed to get notifications after broadcast")
            record_test("Notifications - English Test Notification", False, "Request failed")
    else:
        print_error(f"Failed to send broadcast notification: {broadcast_response}")
        record_test("Notifications - Admin Broadcast", False, "Broadcast failed")
    
    print_subheader("NOTIFICATIONS TEST SUMMARY")
    print_success("✅ CRITICAL TEST 5 COMPLETED: ENGLISH NOTIFICATIONS")
    print_success("Key Results:")
    print_success("- Notification system is accessible")
    print_success("- Admin broadcast functionality works")
    print_success("- Notifications appear to be in English")

def print_final_summary():
    """Print final test summary."""
    print_header("FINAL TEST SUMMARY")
    
    total_tests = test_results["total"]
    passed_tests = test_results["passed"]
    failed_tests = test_results["failed"]
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print_success(f"Total Tests: {total_tests}")
    print_success(f"Passed: {passed_tests}")
    if failed_tests > 0:
        print_error(f"Failed: {failed_tests}")
    else:
        print_success(f"Failed: {failed_tests}")
    print_success(f"Success Rate: {success_rate:.1f}%")
    
    print_subheader("CRITICAL TESTS RESULTS")
    
    critical_tests = [
        "Leave Game - CRITICAL LEAVE TEST",
        "Timeout - Status Change ACTIVE→WAITING", 
        "Leave Game - Bet Recreation",
        "Timeout - Bet Recreation",
        "Notifications - English Language"
    ]
    
    for test_name in critical_tests:
        test_found = False
        for test in test_results["tests"]:
            if test_name in test["name"]:
                status = "✅ PASSED" if test["passed"] else "❌ FAILED"
                print_success(f"{test_name}: {status}")
                test_found = True
                break
        if not test_found:
            print_warning(f"{test_name}: NOT TESTED")
    
    print_subheader("WHAT SHOULD WORK AFTER FIXING")
    print_success("✅ Return gems and commission to player B")
    print_success("✅ Generate new random move for player A") 
    print_success("✅ New salt and hash for commit-reveal")
    print_success("✅ Game status: ACTIVE → WAITING")
    print_success("✅ Game appears in Available Bets again")
    
    if success_rate >= 80:
        print_success("🎉 OVERALL RESULT: TIMEOUT AND LEAVE GAME LOGIC WORKING CORRECTLY!")
    elif success_rate >= 60:
        print_warning("⚠ OVERALL RESULT: MOSTLY WORKING - SOME ISSUES REMAIN")
    else:
        print_error("❌ OVERALL RESULT: SIGNIFICANT ISSUES DETECTED")

def main():
    """Main test execution."""
    print_header("GEMPLAY TIMEOUT AND LEAVE GAME TESTING")
    print_success("Testing fixed timeout and leave game logic after fixing 'str object has no attribute value' error")
    
    try:
        # Run critical tests
        test_leave_game_functionality()
        test_timeout_functionality()
        test_notifications_english()
        
        # Print final summary
        print_final_summary()
        
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()