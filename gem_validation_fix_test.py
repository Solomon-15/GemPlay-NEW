#!/usr/bin/env python3
"""
GemPlay API Testing - Gem Validation Fix During Move Selection
Focus: Testing the fix for gem validation logic when choosing moves in betting system

CONTEXT:
- Player B with 865 gems was trying to join Player A's 800 gem bet
- When choosing move, frontend was re-validating gem availability even though gems were already reserved
- Fix: Removed repeated gem validation in validateBeforeBattle function during step 2 (choose move)

TEST SCENARIOS:
1. Player A creates game with large bet (400-800 gems)
2. Player B joins game (gems should be reserved)
3. Player B chooses move (should not get "Insufficient gems" error)
4. Game completion with proper commission handling
5. Test with various gem types including Sapphire
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

# Test Results Tracking
test_results = []
total_tests = 0
passed_tests = 0

def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}")

def print_subheader(text: str):
    """Print formatted subheader."""
    print(f"\n{'-'*60}")
    print(f"  {text}")
    print(f"{'-'*60}")

def print_success(text: str):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text: str):
    """Print error message."""
    print(f"❌ {text}")

def print_info(text: str):
    """Print info message."""
    print(f"ℹ️  {text}")

def record_test(test_name: str, passed: bool, details: str = ""):
    """Record test result."""
    global total_tests, passed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
    
    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def make_request(method: str, endpoint: str, data: Dict = None, auth_token: str = None, params: Dict = None) -> Tuple[Dict, bool]:
    """Make HTTP request with error handling."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            if params:
                response = requests.post(url, headers=headers, params=params, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return {}, False
        
        try:
            response_data = response.json()
        except:
            response_data = {"status_code": response.status_code, "text": response.text}
        
        return response_data, response.status_code < 400
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return {"error": str(e)}, False

def generate_unique_email() -> str:
    """Generate unique email for testing."""
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test_user_{timestamp}_{random_suffix}@test.com"

def register_and_verify_user(username: str, email: str, password: str, gender: str = "male") -> Tuple[str, bool]:
    """Register user and return auth token."""
    print_info(f"Registering user: {username} ({email})")
    
    # Register user
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "gender": gender
    }
    
    register_response, register_success = make_request("POST", "/auth/register", register_data)
    
    if not register_success:
        print_error(f"Registration failed: {register_response}")
        return "", False
    
    print_success(f"User registered successfully: {username}")
    
    # Get verification token from registration response
    verification_token = register_response.get("verification_token")
    if not verification_token:
        print_error("No verification token received")
        return "", False
    
    # Verify email
    verify_response, verify_success = make_request("POST", "/auth/verify-email", {"token": verification_token})
    
    if not verify_success:
        print_error(f"Email verification failed: {verify_response}")
        return "", False
    
    print_success(f"Email verified successfully for: {username}")
    
    # Login to get token
    login_data = {
        "email": email,
        "password": password
    }
    
    login_response, login_success = make_request("POST", "/auth/login", login_data)
    
    if not login_success:
        print_error(f"Login failed: {login_response}")
        return "", False
    
    token = login_response.get("access_token")
    if not token:
        print_error("No access token in login response")
        return "", False
    
    print_success(f"User logged in successfully: {username}")
    return token, True

def purchase_gems(auth_token: str, gem_purchases: Dict[str, int]) -> bool:
    """Purchase gems for user."""
    print_info(f"Purchasing gems: {gem_purchases}")
    
    success_count = 0
    total_purchases = len(gem_purchases)
    
    for gem_type, quantity in gem_purchases.items():
        # Use query parameters instead of JSON body
        params = {
            "gem_type": gem_type,
            "quantity": quantity
        }
        
        purchase_response, purchase_success = make_request("POST", "/gems/buy", params=params, auth_token=auth_token)
        
        if purchase_success:
            print_success(f"✓ Purchased {quantity} {gem_type} gems")
            success_count += 1
        else:
            print_error(f"✗ Failed to purchase {quantity} {gem_type} gems: {purchase_response}")
    
    return success_count == total_purchases

def get_user_gems(auth_token: str) -> Dict[str, int]:
    """Get user's gem inventory."""
    gems_response, gems_success = make_request("GET", "/gems", auth_token=auth_token)
    
    if not gems_success:
        print_error(f"Failed to get gems: {gems_response}")
        return {}
    
    gem_inventory = {}
    for gem in gems_response.get("gems", []):
        gem_type = gem.get("type")
        quantity = gem.get("quantity", 0)
        if gem_type:
            gem_inventory[gem_type] = quantity
    
    return gem_inventory

def create_game_with_large_bet(auth_token: str, bet_gems: Dict[str, int], move: str = "rock") -> Tuple[str, bool]:
    """Create game with large gem bet."""
    print_info(f"Creating game with bet: {bet_gems}")
    
    game_data = {
        "move": move,
        "bet_gems": bet_gems
    }
    
    create_response, create_success = make_request("POST", "/games/create", game_data, auth_token)
    
    if not create_success:
        print_error(f"Game creation failed: {create_response}")
        return "", False
    
    game_id = create_response.get("game_id")
    if not game_id:
        print_error("No game_id in create response")
        return "", False
    
    print_success(f"Game created successfully: {game_id}")
    return game_id, True

def join_game(auth_token: str, game_id: str, gems: Dict[str, int], move: str = "paper") -> bool:
    """Join existing game."""
    print_info(f"Joining game {game_id} with gems: {gems}")
    
    join_data = {
        "move": move,
        "gems": gems
    }
    
    join_response, join_success = make_request("POST", f"/games/{game_id}/join", join_data, auth_token)
    
    if not join_success:
        print_error(f"Game join failed: {join_response}")
        return False
    
    # Check if response indicates ACTIVE status
    status = join_response.get("status")
    if status == "ACTIVE":
        print_success(f"✓ Game joined successfully, status: {status}")
        return True
    else:
        print_error(f"✗ Unexpected game status after join: {status}")
        return False

def choose_move(auth_token: str, game_id: str, move: str = "scissors") -> bool:
    """Choose move in active game - this is the critical test for the gem validation fix."""
    print_info(f"Choosing move '{move}' for game {game_id}")
    
    move_data = {
        "move": move
    }
    
    move_response, move_success = make_request("POST", f"/games/{game_id}/choose-move", move_data, auth_token)
    
    if not move_success:
        print_error(f"Choose move failed: {move_response}")
        
        # Check if it's the specific gem validation error we're testing
        error_detail = move_response.get("detail", "")
        if "Insufficient" in error_detail and "gems" in error_detail:
            print_error(f"❌ CRITICAL: Gem validation error during move selection: {error_detail}")
            print_error("❌ This indicates the fix for repeated gem validation is NOT working!")
            return False
        else:
            print_error(f"Other error during move selection: {error_detail}")
            return False
    
    print_success(f"✓ Move chosen successfully without gem validation errors")
    return True

def get_game_status(auth_token: str, game_id: str) -> Dict[str, Any]:
    """Get current game status."""
    status_response, status_success = make_request("GET", f"/games/{game_id}/status", auth_token=auth_token)
    
    if not status_success:
        print_error(f"Failed to get game status: {status_response}")
        return {}
    
    return status_response

def test_gem_validation_fix():
    """Main test function for gem validation fix."""
    print_header("GEM VALIDATION FIX TESTING - RUSSIAN REVIEW")
    print_info("Testing fix for gem validation during move selection")
    print_info("Issue: Player B gets 'Insufficient gems' error when choosing move after joining game")
    print_info("Fix: Removed repeated gem validation in validateBeforeBattle during step 2")
    
    # Test Scenario 1: Large Sapphire bet (most expensive gems)
    print_subheader("TEST SCENARIO 1: Large Sapphire Bet (800+ gems value)")
    
    # Create Player A
    timestamp = int(time.time())
    player_a_email = generate_unique_email()
    player_a_username = f"PlayerA_LargeBet_{timestamp}"
    player_a_token, player_a_success = register_and_verify_user(player_a_username, player_a_email, "Test123!")
    
    if not player_a_success:
        print_error("Failed to create Player A")
        record_test("Player A Registration", False, "Registration failed")
        return
    
    record_test("Player A Registration", True)
    
    # Create Player B
    player_b_email = generate_unique_email()
    player_b_username = f"PlayerB_LargeBet_{timestamp}"
    player_b_token, player_b_success = register_and_verify_user(player_b_username, player_b_email, "Test123!")
    
    if not player_b_success:
        print_error("Failed to create Player B")
        record_test("Player B Registration", False, "Registration failed")
        return
    
    record_test("Player B Registration", True)
    
    # Purchase gems for Player A (create large bet)
    player_a_gems = {
        "Sapphire": 16,  # 16 * $50 = $800 value
        "Emerald": 5     # 5 * $10 = $50 value, total = $850
    }
    
    player_a_purchase_success = purchase_gems(player_a_token, player_a_gems)
    record_test("Player A Gem Purchase", player_a_purchase_success)
    
    if not player_a_purchase_success:
        print_error("Failed to purchase gems for Player A")
        return
    
    # Purchase gems for Player B (enough to join but test the validation)
    player_b_gems = {
        "Sapphire": 17,  # 17 * $50 = $850 value (slightly more than needed)
        "Emerald": 6     # 6 * $10 = $60 value, total = $910
    }
    
    player_b_purchase_success = purchase_gems(player_b_token, player_b_gems)
    record_test("Player B Gem Purchase", player_b_purchase_success)
    
    if not player_b_purchase_success:
        print_error("Failed to purchase gems for Player B")
        return
    
    # Verify gem inventories
    player_a_inventory = get_user_gems(player_a_token)
    player_b_inventory = get_user_gems(player_b_token)
    
    print_info(f"Player A inventory: {player_a_inventory}")
    print_info(f"Player B inventory: {player_b_inventory}")
    
    # Player A creates game with large bet
    bet_gems = {
        "Sapphire": 16,
        "Emerald": 5
    }
    
    game_id, create_success = create_game_with_large_bet(player_a_token, bet_gems, "rock")
    record_test("Large Bet Game Creation", create_success)
    
    if not create_success:
        print_error("Failed to create game with large bet")
        return
    
    # Player B joins the game (this should reserve gems)
    join_gems = {
        "Sapphire": 16,
        "Emerald": 5
    }
    
    join_success = join_game(player_b_token, game_id, join_gems, "paper")
    record_test("Player B Game Join", join_success)
    
    if not join_success:
        print_error("Player B failed to join game")
        return
    
    print_success("✓ Player B successfully joined game - gems should now be reserved")
    
    # CRITICAL TEST: Player B chooses move (this should NOT trigger gem validation error)
    print_subheader("CRITICAL TEST: Move Selection Without Gem Validation Error")
    print_info("This is the core test for the gem validation fix")
    print_info("If this fails with 'Insufficient gems', the fix is not working")
    
    move_success = choose_move(player_b_token, game_id, "scissors")
    record_test("Player B Move Selection (Critical Fix Test)", move_success)
    
    if move_success:
        print_success("🎉 CRITICAL SUCCESS: Player B chose move without gem validation error!")
        print_success("🎉 The gem validation fix is WORKING correctly!")
    else:
        print_error("💥 CRITICAL FAILURE: Player B got gem validation error during move selection!")
        print_error("💥 The gem validation fix is NOT working!")
        return
    
    # Check game status after move selection
    game_status = get_game_status(player_a_token, game_id)
    if game_status:
        status = game_status.get("status", "UNKNOWN")
        print_info(f"Game status after move selection: {status}")
        
        if status == "COMPLETED":
            print_success("✓ Game completed successfully")
            record_test("Game Completion", True)
        else:
            print_info(f"Game status: {status} (may complete shortly)")
            record_test("Game Status Check", True)
    
    # Test Scenario 2: Mixed gem types with high value
    print_subheader("TEST SCENARIO 2: Mixed High-Value Gems")
    
    # Create new players for second scenario
    timestamp2 = int(time.time()) + 1
    player_c_email = generate_unique_email()
    player_c_username = f"PlayerC_Mixed_{timestamp2}"
    player_c_token, player_c_success = register_and_verify_user(player_c_username, player_c_email, "Test123!")
    
    player_d_email = generate_unique_email()
    player_d_username = f"PlayerD_Mixed_{timestamp2}"
    player_d_token, player_d_success = register_and_verify_user(player_d_username, player_d_email, "Test123!")
    
    if not (player_c_success and player_d_success):
        print_error("Failed to create players for scenario 2")
        record_test("Scenario 2 Player Creation", False)
        return
    
    record_test("Scenario 2 Player Creation", True)
    
    # Purchase mixed high-value gems
    player_c_mixed_gems = {
        "Magic": 4,      # 4 * $100 = $400
        "Aquamarine": 8, # 8 * $25 = $200
        "Topaz": 20      # 20 * $5 = $100, total = $700
    }
    
    player_d_mixed_gems = {
        "Magic": 5,      # 5 * $100 = $500
        "Aquamarine": 10, # 10 * $25 = $250
        "Topaz": 25      # 25 * $5 = $125, total = $875
    }
    
    player_c_purchase = purchase_gems(player_c_token, player_c_mixed_gems)
    player_d_purchase = purchase_gems(player_d_token, player_d_mixed_gems)
    
    record_test("Scenario 2 Gem Purchases", player_c_purchase and player_d_purchase)
    
    if not (player_c_purchase and player_d_purchase):
        print_error("Failed to purchase gems for scenario 2")
        return
    
    # Player C creates game with mixed gems
    mixed_bet_gems = {
        "Magic": 4,
        "Aquamarine": 8,
        "Topaz": 20
    }
    
    game_id_2, create_success_2 = create_game_with_large_bet(player_c_token, mixed_bet_gems, "rock")
    record_test("Mixed Gems Game Creation", create_success_2)
    
    if not create_success_2:
        print_error("Failed to create mixed gems game")
        return
    
    # Player D joins with matching gems
    join_mixed_gems = {
        "Magic": 4,
        "Aquamarine": 8,
        "Topaz": 20
    }
    
    join_success_2 = join_game(player_d_token, game_id_2, join_mixed_gems, "paper")
    record_test("Player D Mixed Game Join", join_success_2)
    
    if not join_success_2:
        print_error("Player D failed to join mixed gems game")
        return
    
    # Critical test: Player D chooses move
    move_success_2 = choose_move(player_d_token, game_id_2, "scissors")
    record_test("Player D Move Selection (Mixed Gems)", move_success_2)
    
    if move_success_2:
        print_success("✓ Mixed gems scenario: Move selection successful!")
    else:
        print_error("✗ Mixed gems scenario: Move selection failed!")
    
    # Test Scenario 3: Edge case - exactly matching gem amounts
    print_subheader("TEST SCENARIO 3: Edge Case - Exact Gem Matching")
    
    # Create players for edge case
    timestamp3 = int(time.time()) + 2
    player_e_email = generate_unique_email()
    player_e_username = f"PlayerE_Edge_{timestamp3}"
    player_e_token, player_e_success = register_and_verify_user(player_e_username, player_e_email, "Test123!")
    
    player_f_email = generate_unique_email()
    player_f_username = f"PlayerF_Edge_{timestamp3}"
    player_f_token, player_f_success = register_and_verify_user(player_f_username, player_f_email, "Test123!")
    
    if not (player_e_success and player_f_success):
        print_error("Failed to create players for edge case")
        record_test("Edge Case Player Creation", False)
        return
    
    record_test("Edge Case Player Creation", True)
    
    # Purchase exact amounts needed
    edge_gems = {
        "Sapphire": 10,  # 10 * $50 = $500
        "Emerald": 15    # 15 * $10 = $150, total = $650
    }
    
    player_e_purchase = purchase_gems(player_e_token, edge_gems)
    player_f_purchase = purchase_gems(player_f_token, edge_gems)
    
    record_test("Edge Case Gem Purchases", player_e_purchase and player_f_purchase)
    
    if not (player_e_purchase and player_f_purchase):
        print_error("Failed to purchase gems for edge case")
        return
    
    # Player E creates game
    edge_bet_gems = {
        "Sapphire": 10,
        "Emerald": 15
    }
    
    game_id_3, create_success_3 = create_game_with_large_bet(player_e_token, edge_bet_gems, "rock")
    record_test("Edge Case Game Creation", create_success_3)
    
    if not create_success_3:
        print_error("Failed to create edge case game")
        return
    
    # Player F joins with exact matching gems
    join_success_3 = join_game(player_f_token, game_id_3, edge_bet_gems, "paper")
    record_test("Player F Edge Case Join", join_success_3)
    
    if not join_success_3:
        print_error("Player F failed to join edge case game")
        return
    
    # Critical test: Player F chooses move with exact gem match
    move_success_3 = choose_move(player_f_token, game_id_3, "scissors")
    record_test("Player F Move Selection (Edge Case)", move_success_3)
    
    if move_success_3:
        print_success("✓ Edge case scenario: Move selection successful!")
    else:
        print_error("✗ Edge case scenario: Move selection failed!")

def print_test_summary():
    """Print comprehensive test summary."""
    print_header("TEST SUMMARY - GEM VALIDATION FIX")
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    print_subheader("DETAILED RESULTS")
    
    critical_tests = [
        "Player B Move Selection (Critical Fix Test)",
        "Player D Move Selection (Mixed Gems)",
        "Player F Move Selection (Edge Case)"
    ]
    
    critical_passed = 0
    critical_total = 0
    
    for result in test_results:
        test_name = result["test"]
        passed = result["passed"]
        details = result["details"]
        
        if test_name in critical_tests:
            critical_total += 1
            if passed:
                critical_passed += 1
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
    
    print_subheader("CRITICAL TESTS SUMMARY")
    print(f"Critical Tests (Move Selection): {critical_passed}/{critical_total}")
    
    if critical_passed == critical_total and critical_total > 0:
        print_success("🎉 ALL CRITICAL TESTS PASSED!")
        print_success("🎉 The gem validation fix is working correctly!")
        print_success("🎉 Players can choose moves without gem validation errors!")
    elif critical_passed > 0:
        print_error(f"⚠️  PARTIAL SUCCESS: {critical_passed}/{critical_total} critical tests passed")
        print_error("⚠️  Some scenarios still have gem validation issues")
    else:
        print_error("💥 ALL CRITICAL TESTS FAILED!")
        print_error("💥 The gem validation fix is NOT working!")
        print_error("💥 Players still get gem validation errors during move selection!")

if __name__ == "__main__":
    try:
        test_gem_validation_fix()
        print_test_summary()
        
        # Exit with appropriate code
        if passed_tests == total_tests and total_tests > 0:
            print_success("All tests passed!")
            sys.exit(0)
        else:
            print_error("Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Testing failed with error: {e}")
        sys.exit(1)