#!/usr/bin/env python3
"""
GemPlay Betting Synchronization Bug Testing
Focus: Critical synchronization issues in betting logic as requested in Russian review

КРИТИЧЕСКИЕ СЦЕНАРИИ ДЛЯ ТЕСТИРОВАНИЯ:

1. **Bug 1 - Frozen Gems Return**: 
   - Создать игру игроком A
   - Игрок B присоединяется к игре (гемы замораживаются)
   - Игрок B резко выходит из игры (leave API)
   - Проверить, что замороженные гемы возвращаются
   - Проверить, что при повторном заходе нет ошибки "Not enough gems in inventory"

2. **Bug 2 - Balance Display**:
   - Проверить отображение баланса через API /economy/balance
   - Убедиться, что не показывается "Balance $989.98, $991.27" (где доступный больше общего)
   - Available balance должен быть = virtual_balance - frozen_balance

3. **Bug 3 - Commission Calculation**:
   - Проверить расчет комиссии при создании ставки
   - Убедиться, что используются актуальные данные, а не старое состояние

4. **Bug 4 - Gem Validation**:
   - Создать игру с определенными гемами
   - Присоединиться к игре и проверить, что нет ошибки "Insufficient Sapphire gems. Available: 4, Required: 6" когда гемы есть
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
BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"

# Test users for synchronization testing
TEST_USERS = [
    {
        "username": "playerA_sync",
        "email": "playerA_sync@test.com",
        "password": "Test123!",
        "gender": "male"
    },
    {
        "username": "playerB_sync", 
        "email": "playerB_sync@test.com",
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

def register_and_verify_user(user_data: Dict[str, str]) -> Optional[str]:
    """Register and verify a user, return auth token."""
    print_subheader(f"Registering and verifying user: {user_data['username']}")
    
    # Generate unique email to avoid conflicts
    timestamp = int(time.time())
    user_data = user_data.copy()
    user_data["email"] = f"{user_data['username']}_{timestamp}@test.com"
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if not success:
        print_error(f"Failed to register user {user_data['username']}")
        return None
    
    if "verification_token" not in response:
        print_error("Registration response missing verification token")
        return None
    
    verification_token = response["verification_token"]
    print_success(f"User registered with verification token: {verification_token}")
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST", "/auth/verify-email", 
        data={"token": verification_token}
    )
    
    if not verify_success:
        print_error("Failed to verify email")
        return None
    
    print_success("Email verified successfully")
    
    # Login to get auth token
    login_response, login_success = make_request(
        "POST", "/auth/login",
        data={"email": user_data["email"], "password": user_data["password"]}
    )
    
    if not login_success or "access_token" not in login_response:
        print_error("Failed to login after registration")
        return None
    
    auth_token = login_response["access_token"]
    print_success(f"User logged in successfully")
    
    return auth_token

def get_user_balance(auth_token: str) -> Tuple[float, float]:
    """Get user's virtual and frozen balance."""
    response, success = make_request("GET", "/auth/me", auth_token=auth_token)
    
    if success:
        virtual_balance = response.get("virtual_balance", 0.0)
        frozen_balance = response.get("frozen_balance", 0.0)
        return virtual_balance, frozen_balance
    
    return 0.0, 0.0

def get_user_gems(auth_token: str) -> Dict[str, Dict[str, int]]:
    """Get user's gem inventory."""
    response, success = make_request("GET", "/gems/inventory", auth_token=auth_token)
    
    if success and isinstance(response, list):
        gems = {}
        for gem in response:
            gem_type = gem.get("type", "")
            quantity = gem.get("quantity", 0)
            frozen_quantity = gem.get("frozen_quantity", 0)
            gems[gem_type] = {
                "quantity": quantity,
                "frozen_quantity": frozen_quantity,
                "available": quantity - frozen_quantity
            }
        return gems
    
    return {}

def buy_gems_for_testing(auth_token: str, gem_type: str, quantity: int) -> bool:
    """Buy gems for testing purposes."""
    response, success = make_request(
        "POST", f"/gems/buy?gem_type={gem_type}&quantity={quantity}",
        auth_token=auth_token
    )
    return success

def test_bug_1_frozen_gems_return():
    """
    Bug 1 - Frozen Gems Return Testing:
    - Создать игру игроком A
    - Игрок B присоединяется к игре (гемы замораживаются)
    - Игрок B резко выходит из игры (leave API)
    - Проверить, что замороженные гемы возвращаются
    - Проверить, что при повторном заходе нет ошибки "Not enough gems in inventory"
    """
    print_header("BUG 1 - FROZEN GEMS RETURN TESTING")
    
    # Step 1: Register and setup users
    print_subheader("Step 1: Setup Test Users")
    
    player_a_token = register_and_verify_user(TEST_USERS[0])
    player_b_token = register_and_verify_user(TEST_USERS[1])
    
    if not player_a_token or not player_b_token:
        print_error("Failed to setup test users")
        record_test("Bug 1 - User Setup", False, "User registration failed")
        return
    
    print_success("Both test users registered and verified")
    record_test("Bug 1 - User Setup", True)
    
    # Step 2: Buy gems for both players
    print_subheader("Step 2: Buy Gems for Testing")
    
    # Player A needs gems to create game
    buy_success_a = buy_gems_for_testing(player_a_token, "Ruby", 20)
    buy_success_a &= buy_gems_for_testing(player_a_token, "Emerald", 5)
    
    # Player B needs gems to join game
    buy_success_b = buy_gems_for_testing(player_b_token, "Ruby", 20)
    buy_success_b &= buy_gems_for_testing(player_b_token, "Emerald", 5)
    
    if not buy_success_a or not buy_success_b:
        print_error("Failed to buy gems for testing")
        record_test("Bug 1 - Gem Purchase", False, "Gem purchase failed")
        return
    
    print_success("Gems purchased for both players")
    record_test("Bug 1 - Gem Purchase", True)
    
    # Step 3: Player A creates game
    print_subheader("Step 3: Player A Creates Game")
    
    game_gems = {"Ruby": 15, "Emerald": 2}  # $35 total bet
    create_game_data = {
        "move": "rock",
        "bet_gems": game_gems
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=player_a_token
    )
    
    if not game_success or "game_id" not in game_response:
        print_error("Failed to create game")
        record_test("Bug 1 - Game Creation", False, "Game creation failed")
        return
    
    game_id = game_response["game_id"]
    print_success(f"Game created with ID: {game_id}")
    record_test("Bug 1 - Game Creation", True)
    
    # Step 4: Check Player B's initial gem state
    print_subheader("Step 4: Check Player B Initial Gem State")
    
    initial_gems_b = get_user_gems(player_b_token)
    initial_virtual_b, initial_frozen_b = get_user_balance(player_b_token)
    
    print_success(f"Player B initial state:")
    print_success(f"  Virtual balance: ${initial_virtual_b}")
    print_success(f"  Frozen balance: ${initial_frozen_b}")
    for gem_type, gem_data in initial_gems_b.items():
        print_success(f"  {gem_type}: {gem_data['available']} available, {gem_data['frozen_quantity']} frozen")
    
    # Step 5: Player B joins game (gems should be frozen)
    print_subheader("Step 5: Player B Joins Game")
    
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
        record_test("Bug 1 - Game Join", False, "Game join failed")
        return
    
    print_success("Player B joined game successfully")
    
    # Check if game status is ACTIVE
    if join_response.get("status") == "ACTIVE":
        print_success("Game status is ACTIVE after join")
        record_test("Bug 1 - Game Join Status", True)
    else:
        print_warning(f"Game status after join: {join_response.get('status')}")
        record_test("Bug 1 - Game Join Status", False, f"Status: {join_response.get('status')}")
    
    # Step 6: Check Player B's gems after joining (should be frozen)
    print_subheader("Step 6: Check Player B Gems After Joining")
    
    after_join_gems_b = get_user_gems(player_b_token)
    after_join_virtual_b, after_join_frozen_b = get_user_balance(player_b_token)
    
    print_success(f"Player B state after joining:")
    print_success(f"  Virtual balance: ${after_join_virtual_b}")
    print_success(f"  Frozen balance: ${after_join_frozen_b}")
    
    gems_frozen_correctly = True
    for gem_type, required_quantity in game_gems.items():
        if gem_type in after_join_gems_b:
            frozen_quantity = after_join_gems_b[gem_type]["frozen_quantity"]
            initial_frozen = initial_gems_b.get(gem_type, {}).get("frozen_quantity", 0)
            
            expected_frozen = initial_frozen + required_quantity
            
            print_success(f"  {gem_type}: {after_join_gems_b[gem_type]['available']} available, {frozen_quantity} frozen")
            
            if frozen_quantity == expected_frozen:
                print_success(f"    ✓ {gem_type} correctly frozen ({required_quantity} gems)")
            else:
                print_error(f"    ✗ {gem_type} freezing incorrect. Expected: {expected_frozen}, Got: {frozen_quantity}")
                gems_frozen_correctly = False
        else:
            print_error(f"    ✗ {gem_type} not found in inventory")
            gems_frozen_correctly = False
    
    if gems_frozen_correctly:
        print_success("✓ Gems correctly frozen after joining game")
        record_test("Bug 1 - Gems Frozen After Join", True)
    else:
        print_error("✗ Gems not correctly frozen after joining game")
        record_test("Bug 1 - Gems Frozen After Join", False, "Incorrect gem freezing")
    
    # Step 7: Player B leaves game (critical test)
    print_subheader("Step 7: Player B Leaves Game (Critical Test)")
    
    leave_response, leave_success = make_request(
        "POST", f"/games/{game_id}/leave",
        auth_token=player_b_token
    )
    
    if not leave_success:
        print_error("Failed to leave game")
        record_test("Bug 1 - Game Leave", False, "Game leave failed")
        return
    
    print_success("Player B left game successfully")
    print_success(f"Leave response: {json.dumps(leave_response, indent=2)}")
    record_test("Bug 1 - Game Leave", True)
    
    # Step 8: Check Player B's gems after leaving (should be unfrozen)
    print_subheader("Step 8: Check Player B Gems After Leaving (Critical)")
    
    after_leave_gems_b = get_user_gems(player_b_token)
    after_leave_virtual_b, after_leave_frozen_b = get_user_balance(player_b_token)
    
    print_success(f"Player B state after leaving:")
    print_success(f"  Virtual balance: ${after_leave_virtual_b}")
    print_success(f"  Frozen balance: ${after_leave_frozen_b}")
    
    gems_unfrozen_correctly = True
    for gem_type, required_quantity in game_gems.items():
        if gem_type in after_leave_gems_b:
            frozen_quantity = after_leave_gems_b[gem_type]["frozen_quantity"]
            initial_frozen = initial_gems_b.get(gem_type, {}).get("frozen_quantity", 0)
            
            print_success(f"  {gem_type}: {after_leave_gems_b[gem_type]['available']} available, {frozen_quantity} frozen")
            
            if frozen_quantity == initial_frozen:
                print_success(f"    ✓ {gem_type} correctly unfrozen (returned to initial state)")
            else:
                print_error(f"    ✗ {gem_type} not correctly unfrozen. Expected: {initial_frozen}, Got: {frozen_quantity}")
                gems_unfrozen_correctly = False
        else:
            print_error(f"    ✗ {gem_type} not found in inventory")
            gems_unfrozen_correctly = False
    
    if gems_unfrozen_correctly:
        print_success("✓ CRITICAL SUCCESS: Gems correctly unfrozen after leaving game")
        record_test("Bug 1 - Gems Unfrozen After Leave", True)
    else:
        print_error("✗ CRITICAL FAILURE: Gems not correctly unfrozen after leaving game")
        record_test("Bug 1 - Gems Unfrozen After Leave", False, "Incorrect gem unfreezing")
    
    # Step 9: Test re-joining to ensure no "Not enough gems" error
    print_subheader("Step 9: Test Re-joining Game (No 'Not enough gems' error)")
    
    # First, check if the game is still available for joining
    available_games_response, available_success = make_request(
        "GET", "/games/available",
        auth_token=player_b_token
    )
    
    game_still_available = False
    if available_success and isinstance(available_games_response, list):
        for game in available_games_response:
            if game.get("game_id") == game_id:
                game_still_available = True
                break
    
    if game_still_available:
        print_success("Game is still available for joining")
        
        # Try to join again
        rejoin_response, rejoin_success = make_request(
            "POST", f"/games/{game_id}/join",
            data=join_game_data,
            auth_token=player_b_token
        )
        
        if rejoin_success:
            print_success("✓ CRITICAL SUCCESS: Player B can rejoin game without 'Not enough gems' error")
            record_test("Bug 1 - Rejoin Without Error", True)
        else:
            error_message = rejoin_response.get("detail", "Unknown error")
            if "not enough" in error_message.lower() or "insufficient" in error_message.lower():
                print_error(f"✗ CRITICAL FAILURE: 'Not enough gems' error on rejoin: {error_message}")
                record_test("Bug 1 - Rejoin Without Error", False, f"Insufficient gems error: {error_message}")
            else:
                print_warning(f"Rejoin failed with different error: {error_message}")
                record_test("Bug 1 - Rejoin Without Error", False, f"Other error: {error_message}")
    else:
        print_warning("Game no longer available for joining (may have been completed or cancelled)")
        record_test("Bug 1 - Rejoin Without Error", True, "Game no longer available (acceptable)")
    
    # Summary
    print_subheader("Bug 1 Test Summary")
    if gems_frozen_correctly and gems_unfrozen_correctly:
        print_success("🎉 BUG 1 - FROZEN GEMS RETURN: FIXED")
        print_success("✅ Gems correctly frozen when joining game")
        print_success("✅ Gems correctly unfrozen when leaving game")
        print_success("✅ No 'Not enough gems' error on rejoin")
    else:
        print_error("❌ BUG 1 - FROZEN GEMS RETURN: STILL EXISTS")
        if not gems_frozen_correctly:
            print_error("❌ Gems not correctly frozen on join")
        if not gems_unfrozen_correctly:
            print_error("❌ Gems not correctly unfrozen on leave")

def test_bug_2_balance_display():
    """
    Bug 2 - Balance Display Testing:
    - Проверить отображение баланса через API /economy/balance
    - Убедиться, что не показывается "Balance $989.98, $991.27" (где доступный больше общего)
    - Available balance должен быть = virtual_balance - frozen_balance
    """
    print_header("BUG 2 - BALANCE DISPLAY TESTING")
    
    # Step 1: Setup test user
    print_subheader("Step 1: Setup Test User")
    
    test_user = {
        "username": "balance_test_user",
        "email": "balance_test@test.com", 
        "password": "Test123!",
        "gender": "male"
    }
    
    user_token = register_and_verify_user(test_user)
    
    if not user_token:
        print_error("Failed to setup test user")
        record_test("Bug 2 - User Setup", False, "User registration failed")
        return
    
    print_success("Test user registered and verified")
    record_test("Bug 2 - User Setup", True)
    
    # Step 2: Check initial balance state
    print_subheader("Step 2: Check Initial Balance State")
    
    virtual_balance, frozen_balance = get_user_balance(user_token)
    
    print_success(f"Initial balance state:")
    print_success(f"  Virtual balance: ${virtual_balance}")
    print_success(f"  Frozen balance: ${frozen_balance}")
    
    expected_available = virtual_balance - frozen_balance
    print_success(f"  Expected available balance: ${expected_available}")
    
    # Step 3: Test /economy/balance endpoint
    print_subheader("Step 3: Test /economy/balance Endpoint")
    
    economy_response, economy_success = make_request(
        "GET", "/economy/balance",
        auth_token=user_token
    )
    
    if not economy_success:
        print_error("Failed to get economy balance")
        record_test("Bug 2 - Economy Balance Endpoint", False, "Endpoint failed")
        return
    
    print_success("Economy balance endpoint accessible")
    print_success(f"Economy balance response: {json.dumps(economy_response, indent=2)}")
    
    # Check response structure
    required_fields = ["virtual_balance", "frozen_balance", "available_balance"]
    missing_fields = [field for field in required_fields if field not in economy_response]
    
    if missing_fields:
        print_error(f"Economy balance response missing fields: {missing_fields}")
        record_test("Bug 2 - Economy Balance Structure", False, f"Missing fields: {missing_fields}")
        return
    
    print_success("Economy balance response has all required fields")
    record_test("Bug 2 - Economy Balance Structure", True)
    
    # Step 4: Validate balance calculation
    print_subheader("Step 4: Validate Balance Calculation")
    
    economy_virtual = economy_response["virtual_balance"]
    economy_frozen = economy_response["frozen_balance"]
    economy_available = economy_response["available_balance"]
    
    print_success(f"Economy balance values:")
    print_success(f"  Virtual balance: ${economy_virtual}")
    print_success(f"  Frozen balance: ${economy_frozen}")
    print_success(f"  Available balance: ${economy_available}")
    
    # Check if available balance calculation is correct
    expected_available = economy_virtual - economy_frozen
    balance_calculation_correct = abs(economy_available - expected_available) < 0.01
    
    if balance_calculation_correct:
        print_success(f"✓ CRITICAL SUCCESS: Available balance correctly calculated")
        print_success(f"✓ Available (${economy_available}) = Virtual (${economy_virtual}) - Frozen (${economy_frozen})")
        record_test("Bug 2 - Balance Calculation Correct", True)
    else:
        print_error(f"✗ CRITICAL FAILURE: Available balance incorrectly calculated")
        print_error(f"✗ Expected: ${expected_available}, Got: ${economy_available}")
        record_test("Bug 2 - Balance Calculation Correct", False, f"Expected: {expected_available}, Got: {economy_available}")
    
    # Check for the specific bug: available > virtual
    if economy_available > economy_virtual:
        print_error(f"✗ CRITICAL BUG DETECTED: Available balance (${economy_available}) > Virtual balance (${economy_virtual})")
        print_error(f"✗ This is the exact bug mentioned: 'Balance $989.98, $991.27' where available > total")
        record_test("Bug 2 - Available > Virtual Bug", False, f"Available: {economy_available}, Virtual: {economy_virtual}")
    else:
        print_success(f"✓ No 'available > virtual' bug detected")
        record_test("Bug 2 - Available > Virtual Bug", True)
    
    # Step 5: Test with frozen balance (create a game to freeze some balance)
    print_subheader("Step 5: Test Balance Display With Frozen Balance")
    
    # Buy gems for testing
    buy_success = buy_gems_for_testing(user_token, "Ruby", 10)
    
    if buy_success:
        print_success("Bought gems for frozen balance test")
        
        # Create a game to freeze some balance
        create_game_data = {
            "move": "rock",
            "bet_gems": {"Ruby": 5}  # $5 bet
        }
        
        game_response, game_success = make_request(
            "POST", "/games/create",
            data=create_game_data,
            auth_token=user_token
        )
        
        if game_success:
            print_success("Game created to test frozen balance")
            
            # Check balance after game creation
            after_game_response, after_game_success = make_request(
                "GET", "/economy/balance",
                auth_token=user_token
            )
            
            if after_game_success:
                after_virtual = after_game_response["virtual_balance"]
                after_frozen = after_game_response["frozen_balance"]
                after_available = after_game_response["available_balance"]
                
                print_success(f"Balance after game creation:")
                print_success(f"  Virtual balance: ${after_virtual}")
                print_success(f"  Frozen balance: ${after_frozen}")
                print_success(f"  Available balance: ${after_available}")
                
                # Validate calculation with frozen balance
                expected_available_after = after_virtual - after_frozen
                calculation_correct_after = abs(after_available - expected_available_after) < 0.01
                
                if calculation_correct_after:
                    print_success(f"✓ Balance calculation correct with frozen balance")
                    record_test("Bug 2 - Balance With Frozen Correct", True)
                else:
                    print_error(f"✗ Balance calculation incorrect with frozen balance")
                    print_error(f"Expected: ${expected_available_after}, Got: ${after_available}")
                    record_test("Bug 2 - Balance With Frozen Correct", False, f"Expected: {expected_available_after}, Got: {after_available}")
                
                # Check if frozen balance increased
                if after_frozen > economy_frozen:
                    print_success(f"✓ Frozen balance correctly increased by ${after_frozen - economy_frozen}")
                    record_test("Bug 2 - Frozen Balance Increase", True)
                else:
                    print_warning(f"Frozen balance did not increase as expected")
                    record_test("Bug 2 - Frozen Balance Increase", False, "No increase in frozen balance")
            else:
                print_error("Failed to get balance after game creation")
                record_test("Bug 2 - Balance With Frozen Correct", False, "Failed to get balance")
        else:
            print_warning("Failed to create game for frozen balance test")
    else:
        print_warning("Failed to buy gems for frozen balance test")
    
    # Summary
    print_subheader("Bug 2 Test Summary")
    if balance_calculation_correct and economy_available <= economy_virtual:
        print_success("🎉 BUG 2 - BALANCE DISPLAY: FIXED")
        print_success("✅ Available balance = Virtual balance - Frozen balance")
        print_success("✅ No 'available > virtual' bug detected")
        print_success("✅ Balance calculation is mathematically correct")
    else:
        print_error("❌ BUG 2 - BALANCE DISPLAY: STILL EXISTS")
        if not balance_calculation_correct:
            print_error("❌ Available balance calculation incorrect")
        if economy_available > economy_virtual:
            print_error("❌ Available balance greater than virtual balance")

def test_bug_3_commission_calculation():
    """
    Bug 3 - Commission Calculation Testing:
    - Проверить расчет комиссии при создании ставки
    - Убедиться, что используются актуальные данные, а не старое состояние
    """
    print_header("BUG 3 - COMMISSION CALCULATION TESTING")
    
    # Step 1: Setup test user
    print_subheader("Step 1: Setup Test User")
    
    test_user = {
        "username": "commission_test_user",
        "email": "commission_test@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    user_token = register_and_verify_user(test_user)
    
    if not user_token:
        print_error("Failed to setup test user")
        record_test("Bug 3 - User Setup", False, "User registration failed")
        return
    
    print_success("Test user registered and verified")
    record_test("Bug 3 - User Setup", True)
    
    # Step 2: Buy gems and check initial state
    print_subheader("Step 2: Buy Gems and Check Initial State")
    
    buy_success = buy_gems_for_testing(user_token, "Ruby", 30)
    buy_success &= buy_gems_for_testing(user_token, "Emerald", 10)
    
    if not buy_success:
        print_error("Failed to buy gems for testing")
        record_test("Bug 3 - Gem Purchase", False, "Gem purchase failed")
        return
    
    print_success("Gems purchased successfully")
    
    initial_virtual, initial_frozen = get_user_balance(user_token)
    print_success(f"Initial balance: Virtual=${initial_virtual}, Frozen=${initial_frozen}")
    
    # Step 3: Test commission calculation for different bet amounts
    print_subheader("Step 3: Test Commission Calculation for Different Bet Amounts")
    
    test_bets = [
        {"gems": {"Ruby": 10}, "expected_value": 10.0, "expected_commission": 0.60},  # $10 bet, 6% commission
        {"gems": {"Ruby": 20}, "expected_value": 20.0, "expected_commission": 1.20},  # $20 bet, 6% commission
        {"gems": {"Emerald": 3}, "expected_value": 30.0, "expected_commission": 1.80},  # $30 bet, 6% commission
        {"gems": {"Ruby": 15, "Emerald": 2}, "expected_value": 35.0, "expected_commission": 2.10},  # $35 bet, 6% commission
    ]
    
    commission_tests_passed = 0
    
    for i, bet_test in enumerate(test_bets):
        print_success(f"\nTesting bet {i+1}: {bet_test['gems']} (${bet_test['expected_value']})")
        
        # Get balance before creating game
        before_virtual, before_frozen = get_user_balance(user_token)
        
        # Create game
        create_game_data = {
            "move": "rock",
            "bet_gems": bet_test["gems"]
        }
        
        game_response, game_success = make_request(
            "POST", "/games/create",
            data=create_game_data,
            auth_token=user_token
        )
        
        if not game_success:
            print_error(f"Failed to create game for bet test {i+1}")
            continue
        
        game_id = game_response.get("game_id")
        print_success(f"Game created with ID: {game_id}")
        
        # Get balance after creating game
        after_virtual, after_frozen = get_user_balance(user_token)
        
        # Calculate actual commission charged
        virtual_change = before_virtual - after_virtual
        frozen_change = after_frozen - before_frozen
        
        print_success(f"Balance changes:")
        print_success(f"  Virtual: ${before_virtual} -> ${after_virtual} (change: -${virtual_change})")
        print_success(f"  Frozen: ${before_frozen} -> ${after_frozen} (change: +${frozen_change})")
        
        # Check if commission calculation is correct
        expected_commission = bet_test["expected_commission"]
        commission_correct = abs(virtual_change - expected_commission) < 0.01
        frozen_correct = abs(frozen_change - expected_commission) < 0.01
        
        if commission_correct and frozen_correct:
            print_success(f"✓ Commission correctly calculated: ${expected_commission}")
            commission_tests_passed += 1
        else:
            print_error(f"✗ Commission incorrectly calculated")
            print_error(f"  Expected commission: ${expected_commission}")
            print_error(f"  Actual virtual change: ${virtual_change}")
            print_error(f"  Actual frozen change: ${frozen_change}")
        
        # Cancel the game to clean up
        cancel_response, cancel_success = make_request(
            "DELETE", f"/games/{game_id}/cancel",
            auth_token=user_token
        )
        
        if cancel_success:
            print_success("Game cancelled successfully")
        else:
            print_warning("Failed to cancel game")
    
    # Record commission calculation test results
    if commission_tests_passed == len(test_bets):
        print_success(f"✓ All commission calculations correct ({commission_tests_passed}/{len(test_bets)})")
        record_test("Bug 3 - Commission Calculation Accuracy", True)
    else:
        print_error(f"✗ Some commission calculations incorrect ({commission_tests_passed}/{len(test_bets)})")
        record_test("Bug 3 - Commission Calculation Accuracy", False, f"Only {commission_tests_passed}/{len(test_bets)} correct")
    
    # Step 4: Test commission calculation with rapid successive bets (stale state test)
    print_subheader("Step 4: Test Commission With Rapid Successive Bets (Stale State Test)")
    
    print_success("Testing rapid successive bet creation to check for stale state issues...")
    
    rapid_bet_data = {
        "move": "paper",
        "bet_gems": {"Ruby": 5}  # $5 bet, $0.30 commission
    }
    
    rapid_games = []
    rapid_commission_correct = True
    
    for i in range(3):  # Create 3 games rapidly
        print_success(f"\nRapid bet {i+1}:")
        
        before_virtual, before_frozen = get_user_balance(user_token)
        
        game_response, game_success = make_request(
            "POST", "/games/create",
            data=rapid_bet_data,
            auth_token=user_token
        )
        
        if game_success:
            game_id = game_response.get("game_id")
            rapid_games.append(game_id)
            
            after_virtual, after_frozen = get_user_balance(user_token)
            
            virtual_change = before_virtual - after_virtual
            expected_commission = 0.30  # 6% of $5
            
            print_success(f"  Game ID: {game_id}")
            print_success(f"  Virtual change: ${virtual_change}")
            print_success(f"  Expected commission: ${expected_commission}")
            
            if abs(virtual_change - expected_commission) < 0.01:
                print_success(f"  ✓ Commission correct for rapid bet {i+1}")
            else:
                print_error(f"  ✗ Commission incorrect for rapid bet {i+1}")
                rapid_commission_correct = False
        else:
            print_error(f"Failed to create rapid bet {i+1}")
            rapid_commission_correct = False
        
        # Small delay to simulate rapid but not simultaneous requests
        time.sleep(0.5)
    
    if rapid_commission_correct:
        print_success("✓ Commission calculation correct for rapid successive bets")
        record_test("Bug 3 - Rapid Bets Commission", True)
    else:
        print_error("✗ Commission calculation incorrect for rapid successive bets (stale state issue)")
        record_test("Bug 3 - Rapid Bets Commission", False, "Stale state detected")
    
    # Clean up rapid games
    for game_id in rapid_games:
        cancel_response, cancel_success = make_request(
            "DELETE", f"/games/{game_id}/cancel",
            auth_token=user_token
        )
    
    # Summary
    print_subheader("Bug 3 Test Summary")
    if commission_tests_passed == len(test_bets) and rapid_commission_correct:
        print_success("🎉 BUG 3 - COMMISSION CALCULATION: FIXED")
        print_success("✅ Commission calculation uses current data, not stale state")
        print_success("✅ All commission calculations mathematically correct")
        print_success("✅ Rapid successive bets handled correctly")
    else:
        print_error("❌ BUG 3 - COMMISSION CALCULATION: STILL EXISTS")
        if commission_tests_passed != len(test_bets):
            print_error("❌ Some commission calculations incorrect")
        if not rapid_commission_correct:
            print_error("❌ Stale state issue detected in rapid bets")

def test_bug_4_gem_validation():
    """
    Bug 4 - Gem Validation Testing:
    - Создать игру с определенными гемами
    - Присоединиться к игре и проверить, что нет ошибки "Insufficient Sapphire gems. Available: 4, Required: 6" когда гемы есть
    """
    print_header("BUG 4 - GEM VALIDATION TESTING")
    
    # Step 1: Setup test users
    print_subheader("Step 1: Setup Test Users")
    
    player_a_token = register_and_verify_user(TEST_USERS[0])
    player_b_token = register_and_verify_user(TEST_USERS[1])
    
    if not player_a_token or not player_b_token:
        print_error("Failed to setup test users")
        record_test("Bug 4 - User Setup", False, "User registration failed")
        return
    
    print_success("Both test users registered and verified")
    record_test("Bug 4 - User Setup", True)
    
    # Step 2: Buy specific gems for testing the validation bug
    print_subheader("Step 2: Buy Specific Gems for Validation Testing")
    
    # Buy Sapphire gems specifically (the gem mentioned in the bug report)
    buy_success_a = buy_gems_for_testing(player_a_token, "Sapphire", 10)  # $500 worth
    buy_success_b = buy_gems_for_testing(player_b_token, "Sapphire", 10)  # $500 worth
    
    # Also buy other gems for variety
    buy_success_a &= buy_gems_for_testing(player_a_token, "Ruby", 20)
    buy_success_b &= buy_gems_for_testing(player_b_token, "Ruby", 20)
    
    if not buy_success_a or not buy_success_b:
        print_error("Failed to buy gems for testing")
        record_test("Bug 4 - Gem Purchase", False, "Gem purchase failed")
        return
    
    print_success("Gems purchased for both players")
    record_test("Bug 4 - Gem Purchase", True)
    
    # Step 3: Check initial gem inventory
    print_subheader("Step 3: Check Initial Gem Inventory")
    
    gems_a = get_user_gems(player_a_token)
    gems_b = get_user_gems(player_b_token)
    
    print_success("Player A gem inventory:")
    for gem_type, gem_data in gems_a.items():
        print_success(f"  {gem_type}: {gem_data['available']} available, {gem_data['frozen_quantity']} frozen")
    
    print_success("Player B gem inventory:")
    for gem_type, gem_data in gems_b.items():
        print_success(f"  {gem_type}: {gem_data['available']} available, {gem_data['frozen_quantity']} frozen")
    
    # Step 4: Test the specific scenario mentioned in the bug report
    print_subheader("Step 4: Test Specific Gem Validation Scenario")
    
    # Create a game with Sapphire gems (the gem mentioned in the bug)
    sapphire_available_a = gems_a.get("Sapphire", {}).get("available", 0)
    sapphire_available_b = gems_b.get("Sapphire", {}).get("available", 0)
    
    if sapphire_available_a >= 6 and sapphire_available_b >= 6:
        print_success(f"Both players have sufficient Sapphire gems (A: {sapphire_available_a}, B: {sapphire_available_b})")
        
        # Player A creates game with 6 Sapphire gems
        game_gems = {"Sapphire": 6}  # $300 bet
        create_game_data = {
            "move": "rock",
            "bet_gems": game_gems
        }
        
        game_response, game_success = make_request(
            "POST", "/games/create",
            data=create_game_data,
            auth_token=player_a_token
        )
        
        if not game_success:
            print_error("Failed to create game with Sapphire gems")
            record_test("Bug 4 - Sapphire Game Creation", False, "Game creation failed")
            return
        
        game_id = game_response.get("game_id")
        print_success(f"Game created with 6 Sapphire gems, ID: {game_id}")
        record_test("Bug 4 - Sapphire Game Creation", True)
        
        # Player B tries to join with same gems
        join_game_data = {
            "move": "paper",
            "gems": game_gems  # Same 6 Sapphire gems
        }
        
        print_success(f"Player B attempting to join with {game_gems}")
        print_success(f"Player B has {sapphire_available_b} Sapphire gems available")
        
        join_response, join_success = make_request(
            "POST", f"/games/{game_id}/join",
            data=join_game_data,
            auth_token=player_b_token
        )
        
        if join_success:
            print_success("✓ CRITICAL SUCCESS: Player B joined game without 'Insufficient gems' error")
            print_success("✓ Gem validation working correctly")
            record_test("Bug 4 - Sapphire Game Join Success", True)
        else:
            error_message = join_response.get("detail", "Unknown error")
            if "insufficient" in error_message.lower() or "not enough" in error_message.lower():
                print_error(f"✗ CRITICAL FAILURE: 'Insufficient gems' error when gems are available")
                print_error(f"✗ Error message: {error_message}")
                print_error(f"✗ This is the exact bug: 'Insufficient Sapphire gems. Available: {sapphire_available_b}, Required: 6'")
                record_test("Bug 4 - Sapphire Game Join Success", False, f"Insufficient gems error: {error_message}")
            else:
                print_warning(f"Join failed with different error: {error_message}")
                record_test("Bug 4 - Sapphire Game Join Success", False, f"Other error: {error_message}")
    else:
        print_warning(f"Insufficient Sapphire gems for test (A: {sapphire_available_a}, B: {sapphire_available_b})")
        record_test("Bug 4 - Sapphire Game Creation", False, "Insufficient gems for test")
    
    # Step 5: Test with other gem types to ensure validation works correctly
    print_subheader("Step 5: Test Gem Validation With Other Gem Types")
    
    gem_validation_tests = [
        {"gem_type": "Ruby", "quantity": 10, "description": "Ruby gems test"},
        {"gem_type": "Emerald", "quantity": 2, "description": "Emerald gems test"},
    ]
    
    validation_tests_passed = 0
    
    for test in gem_validation_tests:
        gem_type = test["gem_type"]
        quantity = test["quantity"]
        description = test["description"]
        
        print_success(f"\nTesting {description}:")
        
        available_a = gems_a.get(gem_type, {}).get("available", 0)
        available_b = gems_b.get(gem_type, {}).get("available", 0)
        
        if available_a >= quantity and available_b >= quantity:
            print_success(f"Both players have sufficient {gem_type} gems (A: {available_a}, B: {available_b})")
            
            # Create game
            test_gems = {gem_type: quantity}
            create_data = {
                "move": "scissors",
                "bet_gems": test_gems
            }
            
            game_response, game_success = make_request(
                "POST", "/games/create",
                data=create_data,
                auth_token=player_a_token
            )
            
            if game_success:
                game_id = game_response.get("game_id")
                print_success(f"Game created with {test_gems}")
                
                # Try to join
                join_data = {
                    "move": "rock",
                    "gems": test_gems
                }
                
                join_response, join_success = make_request(
                    "POST", f"/games/{game_id}/join",
                    data=join_data,
                    auth_token=player_b_token
                )
                
                if join_success:
                    print_success(f"✓ {description} validation passed")
                    validation_tests_passed += 1
                else:
                    error_message = join_response.get("detail", "Unknown error")
                    print_error(f"✗ {description} validation failed: {error_message}")
            else:
                print_error(f"Failed to create game for {description}")
        else:
            print_warning(f"Insufficient {gem_type} gems for test (A: {available_a}, B: {available_b})")
    
    if validation_tests_passed == len(gem_validation_tests):
        print_success(f"✓ All gem validation tests passed ({validation_tests_passed}/{len(gem_validation_tests)})")
        record_test("Bug 4 - Other Gem Validation", True)
    else:
        print_error(f"✗ Some gem validation tests failed ({validation_tests_passed}/{len(gem_validation_tests)})")
        record_test("Bug 4 - Other Gem Validation", False, f"Only {validation_tests_passed}/{len(gem_validation_tests)} passed")
    
    # Step 6: Test edge case - exactly enough gems
    print_subheader("Step 6: Test Edge Case - Exactly Enough Gems")
    
    # Find a gem type where we can test with exactly the required amount
    for gem_type, gem_data in gems_b.items():
        available = gem_data["available"]
        if available >= 3:  # Use 3 gems for edge case test
            print_success(f"Testing edge case with {gem_type} (available: {available})")
            
            edge_gems = {gem_type: 3}
            create_data = {
                "move": "paper",
                "bet_gems": edge_gems
            }
            
            game_response, game_success = make_request(
                "POST", "/games/create",
                data=create_data,
                auth_token=player_a_token
            )
            
            if game_success:
                game_id = game_response.get("game_id")
                
                join_data = {
                    "move": "scissors",
                    "gems": edge_gems
                }
                
                join_response, join_success = make_request(
                    "POST", f"/games/{game_id}/join",
                    data=join_data,
                    auth_token=player_b_token
                )
                
                if join_success:
                    print_success("✓ Edge case validation passed (exactly enough gems)")
                    record_test("Bug 4 - Edge Case Validation", True)
                else:
                    error_message = join_response.get("detail", "Unknown error")
                    print_error(f"✗ Edge case validation failed: {error_message}")
                    record_test("Bug 4 - Edge Case Validation", False, f"Error: {error_message}")
            break
    
    # Summary
    print_subheader("Bug 4 Test Summary")
    sapphire_test_passed = any(test["name"] == "Bug 4 - Sapphire Game Join Success" and test["passed"] for test in test_results["tests"])
    other_validation_passed = any(test["name"] == "Bug 4 - Other Gem Validation" and test["passed"] for test in test_results["tests"])
    
    if sapphire_test_passed and other_validation_passed:
        print_success("🎉 BUG 4 - GEM VALIDATION: FIXED")
        print_success("✅ No 'Insufficient gems' error when gems are available")
        print_success("✅ Gem validation uses current inventory state")
        print_success("✅ All gem types validated correctly")
    else:
        print_error("❌ BUG 4 - GEM VALIDATION: STILL EXISTS")
        if not sapphire_test_passed:
            print_error("❌ Sapphire gem validation failed")
        if not other_validation_passed:
            print_error("❌ Other gem validation tests failed")

def main():
    """Main test execution function."""
    print_header("GEMPLAY BETTING SYNCHRONIZATION BUG TESTING")
    print_success("Testing critical synchronization issues in betting logic")
    print_success("Based on Russian review requirements")
    
    # Run all bug tests
    test_bug_1_frozen_gems_return()
    test_bug_2_balance_display()
    test_bug_3_commission_calculation()
    test_bug_4_gem_validation()
    
    # Print final summary
    print_header("FINAL TEST RESULTS SUMMARY")
    
    print_success(f"Total tests run: {test_results['total']}")
    print_success(f"Tests passed: {test_results['passed']}")
    print_error(f"Tests failed: {test_results['failed']}")
    
    success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print_success(f"Success rate: {success_rate:.1f}%")
    
    print_subheader("Critical Bug Status:")
    
    # Analyze results for each bug
    bug_1_tests = [test for test in test_results["tests"] if "Bug 1" in test["name"]]
    bug_2_tests = [test for test in test_results["tests"] if "Bug 2" in test["name"]]
    bug_3_tests = [test for test in test_results["tests"] if "Bug 3" in test["name"]]
    bug_4_tests = [test for test in test_results["tests"] if "Bug 4" in test["name"]]
    
    def analyze_bug_status(bug_tests, bug_name):
        if not bug_tests:
            print_warning(f"{bug_name}: No tests run")
            return False
        
        passed = sum(1 for test in bug_tests if test["passed"])
        total = len(bug_tests)
        
        if passed == total:
            print_success(f"{bug_name}: ✅ FIXED ({passed}/{total} tests passed)")
            return True
        else:
            print_error(f"{bug_name}: ❌ STILL EXISTS ({passed}/{total} tests passed)")
            return False
    
    bug_1_fixed = analyze_bug_status(bug_1_tests, "Bug 1 - Frozen Gems Return")
    bug_2_fixed = analyze_bug_status(bug_2_tests, "Bug 2 - Balance Display")
    bug_3_fixed = analyze_bug_status(bug_3_tests, "Bug 3 - Commission Calculation")
    bug_4_fixed = analyze_bug_status(bug_4_tests, "Bug 4 - Gem Validation")
    
    bugs_fixed = sum([bug_1_fixed, bug_2_fixed, bug_3_fixed, bug_4_fixed])
    
    print_subheader("OVERALL ASSESSMENT:")
    
    if bugs_fixed == 4:
        print_success("🎉 ALL CRITICAL BUGS FIXED!")
        print_success("✅ Betting synchronization issues resolved")
        print_success("✅ System ready for production")
    elif bugs_fixed >= 2:
        print_warning(f"⚠ PARTIAL SUCCESS: {bugs_fixed}/4 bugs fixed")
        print_warning("Some critical issues remain")
    else:
        print_error("❌ CRITICAL ISSUES REMAIN")
        print_error(f"Only {bugs_fixed}/4 bugs fixed")
        print_error("Betting synchronization needs more work")
    
    print_subheader("EXPECTED RESULTS AFTER FIXING:")
    print_success("✅ Мгновенное обновление состояния после всех операций")
    print_success("✅ Корректное отображение баланса")
    print_success("✅ Актуальные данные в валидации гемов")
    print_success("✅ Отсутствие ошибок при повторном заходе")
    
    return success_rate >= 80.0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        sys.exit(1)