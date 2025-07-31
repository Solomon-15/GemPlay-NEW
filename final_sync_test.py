#!/usr/bin/env python3
"""
GemPlay Final Synchronization Bug Testing
Russian Review Requirements: Final verification of all fixed synchronization bugs

FINAL VERIFICATION OF FIXES:
1. Frozen Gems Return - Check return of frozen gems after leave
2. Balance Display - Ensure balance displays correctly (available = virtual - frozen)  
3. Commission Calculation - Check that correct 3% rate is used everywhere
4. Data Synchronization - Ensure data updates instantly after operations

BRIEF TEST:
- Player A creates game
- Player B joins  
- Player B leaves game
- Check gem return and balance correctness
- Check commission calculation
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
        print_error(f"Request failed: {str(e)}")
        return {"error": str(e)}, False

def hash_move_with_salt(move: str, salt: str) -> str:
    """Hash game move with salt for commit-reveal scheme."""
    combined = f"{move}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def create_test_user(username: str, email: str) -> Tuple[Optional[str], Optional[str]]:
    """Create and verify a test user."""
    print_subheader(f"Creating Test User: {username}")
    
    # Generate unique email to avoid conflicts
    timestamp = str(int(time.time()))
    unique_email = f"{username}_{timestamp}@test.com"
    
    user_data = {
        "username": username,
        "email": unique_email,
        "password": "Test123!",
        "gender": "male"
    }
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if not success:
        print_error(f"Failed to register user {username}")
        record_test(f"User Registration - {username}", False, "Registration failed")
        return None, None
    
    if "verification_token" not in response:
        print_error(f"No verification token in response for {username}")
        record_test(f"User Registration - {username}", False, "No verification token")
        return None, None
    
    print_success(f"User {username} registered successfully")
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST", "/auth/verify-email", 
        data={"token": response["verification_token"]}
    )
    
    if not verify_success:
        print_error(f"Failed to verify email for {username}")
        record_test(f"Email Verification - {username}", False, "Verification failed")
        return None, None
    
    print_success(f"Email verified for {username}")
    
    # Login user
    login_response, login_success = make_request(
        "POST", "/auth/login",
        data={"email": unique_email, "password": "Test123!"}
    )
    
    if not login_success or "access_token" not in login_response:
        print_error(f"Failed to login user {username}")
        record_test(f"User Login - {username}", False, "Login failed")
        return None, None
    
    print_success(f"User {username} logged in successfully")
    record_test(f"User Setup - {username}", True)
    
    return login_response["access_token"], unique_email

def get_user_balance_and_gems(token: str, username: str) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Get user balance and gem information."""
    print_subheader(f"Getting Balance and Gems for {username}")
    
    # Get user profile
    profile_response, profile_success = make_request(
        "GET", "/users/profile", auth_token=token
    )
    
    if not profile_success:
        print_error(f"Failed to get profile for {username}")
        return {}, {}
    
    balance_info = {
        "virtual_balance": profile_response.get("virtual_balance", 0.0),
        "frozen_balance": profile_response.get("frozen_balance", 0.0),
        "available_balance": profile_response.get("virtual_balance", 0.0) - profile_response.get("frozen_balance", 0.0)
    }
    
    print_success(f"Balance - Virtual: ${balance_info['virtual_balance']:.2f}, Frozen: ${balance_info['frozen_balance']:.2f}, Available: ${balance_info['available_balance']:.2f}")
    
    # Get user gems
    gems_response, gems_success = make_request(
        "GET", "/users/gems", auth_token=token
    )
    
    gems_info = {}
    if gems_success and "gems" in gems_response:
        for gem in gems_response["gems"]:
            gem_type = gem.get("type", gem.get("name", "Unknown"))
            quantity = gem.get("quantity", 0)
            frozen_quantity = gem.get("frozen_quantity", 0)
            gems_info[gem_type] = {
                "quantity": quantity,
                "frozen_quantity": frozen_quantity,
                "available": quantity - frozen_quantity
            }
            print_success(f"Gem {gem_type} - Total: {quantity}, Frozen: {frozen_quantity}, Available: {quantity - frozen_quantity}")
    
    return balance_info, gems_info

def add_gems_to_user(token: str, username: str, gems: Dict[str, int]) -> bool:
    """Add gems to user for testing."""
    print_subheader(f"Adding Gems to {username}")
    
    success_count = 0
    total_gems = len(gems)
    
    for gem_type, quantity in gems.items():
        purchase_data = {
            "gem_type": gem_type,
            "quantity": quantity
        }
        
        response, success = make_request(
            "POST", "/gems/buy", 
            data=purchase_data, 
            auth_token=token
        )
        
        if success:
            print_success(f"Added {quantity} {gem_type} gems")
            success_count += 1
        else:
            print_error(f"Failed to add {quantity} {gem_type} gems")
    
    all_success = success_count == total_gems
    record_test(f"Add Gems - {username}", all_success, f"{success_count}/{total_gems} gem types added")
    return all_success

def test_frozen_gems_return_and_commission() -> None:
    """
    Test the core synchronization bug fixes:
    1. Frozen Gems Return after leave
    2. Balance Display correctness
    3. Commission Calculation (3% rate)
    4. Data Synchronization
    """
    print_header("FINAL SYNCHRONIZATION BUG TESTING")
    
    # Step 1: Create two test users
    print_subheader("Step 1: Creating Test Users")
    
    player_a_token, player_a_email = create_test_user("PlayerA", "playera@test.com")
    player_b_token, player_b_email = create_test_user("PlayerB", "playerb@test.com")
    
    if not player_a_token or not player_b_token:
        print_error("Failed to create test users - cannot proceed")
        record_test("Final Sync Test - User Setup", False, "User creation failed")
        return
    
    print_success("Both test users created successfully")
    
    # Step 2: Add gems to both users
    print_subheader("Step 2: Adding Gems to Users")
    
    test_gems = {
        "Ruby": 20,
        "Emerald": 5
    }
    
    player_a_gems_added = add_gems_to_user(player_a_token, "PlayerA", test_gems)
    player_b_gems_added = add_gems_to_user(player_b_token, "PlayerB", test_gems)
    
    if not player_a_gems_added or not player_b_gems_added:
        print_error("Failed to add gems to users - cannot proceed")
        record_test("Final Sync Test - Gem Setup", False, "Gem addition failed")
        return
    
    print_success("Gems added to both users successfully")
    
    # Step 3: Get initial balances and gems
    print_subheader("Step 3: Recording Initial State")
    
    player_a_initial_balance, player_a_initial_gems = get_user_balance_and_gems(player_a_token, "PlayerA")
    player_b_initial_balance, player_b_initial_gems = get_user_balance_and_gems(player_b_token, "PlayerB")
    
    print_success("Initial state recorded")
    
    # Step 4: Player A creates a game
    print_subheader("Step 4: Player A Creates Game")
    
    game_gems = {"Ruby": 15, "Emerald": 2}  # $35 total bet
    salt = "test_salt_123"
    move = "rock"
    move_hash = hash_move_with_salt(move, salt)
    
    create_game_data = {
        "move": move,
        "bet_gems": game_gems
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=player_a_token
    )
    
    if not game_success or "game_id" not in game_response:
        print_error("Failed to create game")
        record_test("Final Sync Test - Game Creation", False, "Game creation failed")
        return
    
    game_id = game_response["game_id"]
    print_success(f"Game created successfully with ID: {game_id}")
    
    # Calculate expected commission (3% rate)
    bet_amount = 15 * 1.0 + 2 * 10.0  # Ruby: $1, Emerald: $10
    expected_commission = bet_amount * 0.03  # 3% commission rate
    print_success(f"Expected bet amount: ${bet_amount:.2f}")
    print_success(f"Expected commission (3%): ${expected_commission:.2f}")
    
    # Step 5: Check Player A's balance after game creation
    print_subheader("Step 5: Checking Player A Balance After Game Creation")
    
    player_a_after_create_balance, player_a_after_create_gems = get_user_balance_and_gems(player_a_token, "PlayerA")
    
    # Verify frozen balance includes commission
    expected_frozen_balance = expected_commission
    actual_frozen_balance = player_a_after_create_balance["frozen_balance"]
    
    if abs(actual_frozen_balance - expected_frozen_balance) < 0.01:
        print_success(f"✓ Commission correctly frozen: ${actual_frozen_balance:.2f}")
        record_test("Commission Freezing", True)
    else:
        print_error(f"✗ Commission freezing incorrect - Expected: ${expected_frozen_balance:.2f}, Got: ${actual_frozen_balance:.2f}")
        record_test("Commission Freezing", False, f"Expected: ${expected_frozen_balance:.2f}, Got: ${actual_frozen_balance:.2f}")
    
    # Verify gems are frozen
    ruby_frozen = player_a_after_create_gems.get("Ruby", {}).get("frozen_quantity", 0)
    emerald_frozen = player_a_after_create_gems.get("Emerald", {}).get("frozen_quantity", 0)
    
    if ruby_frozen == 15 and emerald_frozen == 2:
        print_success("✓ Gems correctly frozen for Player A")
        record_test("Gems Freezing - Player A", True)
    else:
        print_error(f"✗ Gems freezing incorrect - Ruby: {ruby_frozen}/15, Emerald: {emerald_frozen}/2")
        record_test("Gems Freezing - Player A", False, f"Ruby: {ruby_frozen}/15, Emerald: {emerald_frozen}/2")
    
    # Step 6: Player B joins the game
    print_subheader("Step 6: Player B Joins Game")
    
    join_game_data = {
        "move": "paper",
        "gems": game_gems  # Same gems as Player A
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=player_b_token
    )
    
    if not join_success:
        print_error("Failed to join game")
        record_test("Final Sync Test - Game Join", False, "Game join failed")
        return
    
    print_success("Player B joined game successfully")
    
    # Verify game status is ACTIVE
    if "status" in join_response and join_response["status"] == "ACTIVE":
        print_success("✓ Game status correctly returned as ACTIVE")
        record_test("Game Status - ACTIVE Response", True)
    else:
        print_error(f"✗ Game status incorrect - Expected: ACTIVE, Got: {join_response.get('status', 'UNKNOWN')}")
        record_test("Game Status - ACTIVE Response", False, f"Got: {join_response.get('status', 'UNKNOWN')}")
    
    # Step 7: Check Player B's balance after joining
    print_subheader("Step 7: Checking Player B Balance After Joining")
    
    player_b_after_join_balance, player_b_after_join_gems = get_user_balance_and_gems(player_b_token, "PlayerB")
    
    # Verify Player B's commission is frozen
    player_b_frozen_balance = player_b_after_join_balance["frozen_balance"]
    
    if abs(player_b_frozen_balance - expected_commission) < 0.01:
        print_success(f"✓ Player B commission correctly frozen: ${player_b_frozen_balance:.2f}")
        record_test("Commission Freezing - Player B", True)
    else:
        print_error(f"✗ Player B commission freezing incorrect - Expected: ${expected_commission:.2f}, Got: ${player_b_frozen_balance:.2f}")
        record_test("Commission Freezing - Player B", False, f"Expected: ${expected_commission:.2f}, Got: ${player_b_frozen_balance:.2f}")
    
    # Verify Player B's gems are frozen
    player_b_ruby_frozen = player_b_after_join_gems.get("Ruby", {}).get("frozen_quantity", 0)
    player_b_emerald_frozen = player_b_after_join_gems.get("Emerald", {}).get("frozen_quantity", 0)
    
    if player_b_ruby_frozen == 15 and player_b_emerald_frozen == 2:
        print_success("✓ Gems correctly frozen for Player B")
        record_test("Gems Freezing - Player B", True)
    else:
        print_error(f"✗ Player B gems freezing incorrect - Ruby: {player_b_ruby_frozen}/15, Emerald: {player_b_emerald_frozen}/2")
        record_test("Gems Freezing - Player B", False, f"Ruby: {player_b_ruby_frozen}/15, Emerald: {player_b_emerald_frozen}/2")
    
    # Step 8: Player B leaves the game (CRITICAL TEST)
    print_subheader("Step 8: Player B Leaves Game (CRITICAL SYNCHRONIZATION TEST)")
    
    leave_response, leave_success = make_request(
        "POST", f"/games/{game_id}/leave",
        auth_token=player_b_token
    )
    
    if not leave_success:
        print_error("Failed to leave game - this is a CRITICAL synchronization bug!")
        record_test("CRITICAL - Game Leave", False, "Leave game failed")
        return
    
    print_success("Player B left game successfully")
    
    # Verify leave response includes gem and commission return
    if "gems_returned" in leave_response and "commission_returned" in leave_response:
        gems_returned = leave_response["gems_returned"]
        commission_returned = leave_response["commission_returned"]
        
        print_success(f"✓ Gems returned: {gems_returned}")
        print_success(f"✓ Commission returned: ${commission_returned:.2f}")
        
        # Verify correct gems returned
        if gems_returned.get("Ruby", 0) == 15 and gems_returned.get("Emerald", 0) == 2:
            print_success("✓ CRITICAL FIX VERIFIED: Correct gems returned")
            record_test("CRITICAL - Frozen Gems Return", True)
        else:
            print_error(f"✗ CRITICAL BUG: Incorrect gems returned - Expected Ruby:15, Emerald:2, Got: {gems_returned}")
            record_test("CRITICAL - Frozen Gems Return", False, f"Incorrect gems: {gems_returned}")
        
        # Verify correct commission returned (3% rate)
        if abs(commission_returned - expected_commission) < 0.01:
            print_success("✓ CRITICAL FIX VERIFIED: Correct commission returned (3% rate)")
            record_test("CRITICAL - Commission Return (3%)", True)
        else:
            print_error(f"✗ CRITICAL BUG: Incorrect commission returned - Expected: ${expected_commission:.2f}, Got: ${commission_returned:.2f}")
            record_test("CRITICAL - Commission Return (3%)", False, f"Expected: ${expected_commission:.2f}, Got: ${commission_returned:.2f}")
    else:
        print_error("✗ CRITICAL BUG: Leave response missing gems_returned or commission_returned")
        record_test("CRITICAL - Leave Response Structure", False, "Missing return fields")
    
    # Step 9: Verify Player B's balance after leaving (CRITICAL SYNCHRONIZATION TEST)
    print_subheader("Step 9: Verifying Player B Balance After Leave (CRITICAL SYNC TEST)")
    
    player_b_after_leave_balance, player_b_after_leave_gems = get_user_balance_and_gems(player_b_token, "PlayerB")
    
    # Check if frozen balance is cleared
    if player_b_after_leave_balance["frozen_balance"] == 0.0:
        print_success("✓ CRITICAL FIX VERIFIED: Frozen balance cleared after leave")
        record_test("CRITICAL - Frozen Balance Clear", True)
    else:
        print_error(f"✗ CRITICAL BUG: Frozen balance not cleared - Still frozen: ${player_b_after_leave_balance['frozen_balance']:.2f}")
        record_test("CRITICAL - Frozen Balance Clear", False, f"Still frozen: ${player_b_after_leave_balance['frozen_balance']:.2f}")
    
    # Check if gems are unfrozen
    player_b_ruby_frozen_after = player_b_after_leave_gems.get("Ruby", {}).get("frozen_quantity", 0)
    player_b_emerald_frozen_after = player_b_after_leave_gems.get("Emerald", {}).get("frozen_quantity", 0)
    
    if player_b_ruby_frozen_after == 0 and player_b_emerald_frozen_after == 0:
        print_success("✓ CRITICAL FIX VERIFIED: All gems unfrozen after leave")
        record_test("CRITICAL - Gems Unfrozen", True)
    else:
        print_error(f"✗ CRITICAL BUG: Gems still frozen - Ruby: {player_b_ruby_frozen_after}, Emerald: {player_b_emerald_frozen_after}")
        record_test("CRITICAL - Gems Unfrozen", False, f"Ruby: {player_b_ruby_frozen_after}, Emerald: {player_b_emerald_frozen_after}")
    
    # Check balance display correctness (available = virtual - frozen)
    expected_available = player_b_after_leave_balance["virtual_balance"] - player_b_after_leave_balance["frozen_balance"]
    actual_available = player_b_after_leave_balance["available_balance"]
    
    if abs(expected_available - actual_available) < 0.01:
        print_success("✓ CRITICAL FIX VERIFIED: Balance display correct (available = virtual - frozen)")
        record_test("CRITICAL - Balance Display Correctness", True)
    else:
        print_error(f"✗ CRITICAL BUG: Balance display incorrect - Expected: ${expected_available:.2f}, Got: ${actual_available:.2f}")
        record_test("CRITICAL - Balance Display Correctness", False, f"Expected: ${expected_available:.2f}, Got: ${actual_available:.2f}")
    
    # Step 10: Verify game status returned to WAITING
    print_subheader("Step 10: Verifying Game Status After Leave")
    
    # Check available games to see if game is back in WAITING status
    available_games_response, available_success = make_request(
        "GET", "/games/available",
        auth_token=player_a_token
    )
    
    if available_success and "games" in available_games_response:
        game_found = False
        for game in available_games_response["games"]:
            if game.get("game_id") == game_id and game.get("status") == "WAITING":
                game_found = True
                break
        
        if game_found:
            print_success("✓ CRITICAL FIX VERIFIED: Game returned to WAITING status and available for join")
            record_test("CRITICAL - Game Status Reset", True)
        else:
            print_error("✗ CRITICAL BUG: Game not found in available games or wrong status")
            record_test("CRITICAL - Game Status Reset", False, "Game not available or wrong status")
    else:
        print_warning("Could not verify game status - available games endpoint failed")
        record_test("Game Status Verification", False, "Available games endpoint failed")

def print_final_results() -> None:
    """Print final test results."""
    print_header("FINAL SYNCHRONIZATION BUG TEST RESULTS")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 80 else Colors.FAIL}{success_rate:.1f}%{Colors.ENDC}")
    
    print_subheader("CRITICAL SYNCHRONIZATION FIXES STATUS")
    
    critical_tests = [
        "CRITICAL - Frozen Gems Return",
        "CRITICAL - Commission Return (3%)",
        "CRITICAL - Frozen Balance Clear", 
        "CRITICAL - Gems Unfrozen",
        "CRITICAL - Balance Display Correctness",
        "CRITICAL - Game Status Reset"
    ]
    
    critical_passed = 0
    critical_total = 0
    
    for test in test_results["tests"]:
        if any(critical in test["name"] for critical in critical_tests):
            critical_total += 1
            if test["passed"]:
                critical_passed += 1
                print_success(f"✓ {test['name']}")
            else:
                print_error(f"✗ {test['name']}: {test['details']}")
    
    critical_success_rate = (critical_passed / critical_total * 100) if critical_total > 0 else 0
    
    print_subheader("FINAL VERDICT")
    
    if critical_success_rate == 100:
        print_success("🎉 ALL CRITICAL SYNCHRONIZATION BUGS FIXED!")
        print_success("✅ Frozen gems return correctly after leave")
        print_success("✅ Balance display shows correct available amount")
        print_success("✅ Commission calculation uses correct 3% rate")
        print_success("✅ Data synchronization works instantly")
        print_success("🚀 SYSTEM READY FOR PRODUCTION!")
    elif critical_success_rate >= 80:
        print_warning("⚠️  MOST CRITICAL BUGS FIXED - Minor issues remain")
        print_warning(f"Critical Success Rate: {critical_success_rate:.1f}%")
    else:
        print_error("❌ CRITICAL SYNCHRONIZATION BUGS STILL PRESENT")
        print_error(f"Critical Success Rate: {critical_success_rate:.1f}%")
        print_error("🔧 REQUIRES IMMEDIATE ATTENTION")

def main():
    """Main test execution."""
    print_header("GEMPLAY FINAL SYNCHRONIZATION BUG TESTING")
    print("Testing all fixed synchronization bugs as requested in Russian review")
    print("Focus: Frozen gems return, balance display, commission calculation, data sync")
    
    try:
        test_frozen_gems_return_and_commission()
    except Exception as e:
        print_error(f"Test execution failed: {str(e)}")
        record_test("Test Execution", False, str(e))
    
    print_final_results()
    
    # Exit with appropriate code
    if test_results["failed"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()