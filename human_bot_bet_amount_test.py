#!/usr/bin/env python3
"""
Human-Bot Bet Amount Testing - Modal Window Fix Verification

This test specifically verifies the fix for the "Сумма" (Amount) column in the modal window 
for active bets of Human-bots in the admin panel.

The issue was that backend was using non-existent field "total_bet_amount" instead of "bet_amount".
This test verifies that the fix is working correctly.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random

# Configuration
BASE_URL = "https://7a07c3b0-a218-4c24-84e0-b12a9efb7441.preview.emergentagent.com/api"
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

def login_admin() -> Optional[str]:
    """Login as admin and return access token."""
    print_subheader("Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        token = response["access_token"]
        print_success(f"Admin logged in successfully")
        record_test("Admin Login", True)
        return token
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_human_bot_bet_amounts_fix():
    """
    Test the fix for Human-bot bet amounts in modal windows.
    
    This test verifies:
    1. /api/admin/human-bots/{bot_id}/active-bets returns correct bet amounts
    2. /api/admin/human-bots/{bot_id}/all-bets returns correct bet amounts  
    3. bet_amount field contains real amounts (not 0)
    4. Compare with /api/games/available where amounts display correctly
    5. Response structure is correct with all needed fields
    """
    print_header("HUMAN-BOT BET AMOUNTS MODAL WINDOW FIX TESTING")
    
    # Step 1: Login as admin
    admin_token = login_admin()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        return
    
    # Step 2: Get list of existing Human-bots
    print_subheader("Step 2: Get Existing Human-Bots")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=50",
        auth_token=admin_token
    )
    
    if not bots_success:
        print_error("Failed to get Human-bots list")
        record_test("Get Human-Bots List", False, "API request failed")
        return
    
    human_bots = bots_response.get("bots", [])
    if not human_bots:
        print_error("No Human-bots found in system")
        record_test("Get Human-Bots List", False, "No bots found")
        return
    
    print_success(f"Found {len(human_bots)} Human-bots in system")
    record_test("Get Human-Bots List", True)
    
    # Step 3: Select a Human-bot for testing (preferably one with active bets)
    print_subheader("Step 3: Select Human-Bot for Testing")
    
    selected_bot = None
    for bot in human_bots:
        active_bets_count = bot.get("active_bets_count", 0)
        if active_bets_count > 0:
            selected_bot = bot
            break
    
    # If no bot with active bets, use the first available bot
    if not selected_bot and human_bots:
        selected_bot = human_bots[0]
    
    if not selected_bot:
        print_error("No suitable Human-bot found for testing")
        record_test("Select Test Bot", False, "No suitable bot")
        return
    
    bot_id = selected_bot["id"]
    bot_name = selected_bot["name"]
    active_bets_count = selected_bot.get("active_bets_count", 0)
    
    print_success(f"Selected bot: {bot_name} (ID: {bot_id})")
    print_success(f"Active bets count: {active_bets_count}")
    record_test("Select Test Bot", True)
    
    # Step 4: Test /api/admin/human-bots/{bot_id}/active-bets endpoint
    print_subheader("Step 4: Test Active Bets Endpoint - Bet Amount Fix")
    
    active_bets_response, active_bets_success = make_request(
        "GET", f"/admin/human-bots/{bot_id}/active-bets",
        auth_token=admin_token
    )
    
    if not active_bets_success:
        print_error("Failed to get active bets")
        record_test("Active Bets API", False, "API request failed")
        return
    
    print_success("✓ Active bets API endpoint responded successfully")
    record_test("Active Bets API", True)
    
    # Verify response structure
    required_fields = ["success", "bot_id", "bot_name", "active_bets_count", "bets"]
    missing_fields = [field for field in required_fields if field not in active_bets_response]
    
    if missing_fields:
        print_error(f"Active bets response missing fields: {missing_fields}")
        record_test("Active Bets Response Structure", False, f"Missing: {missing_fields}")
    else:
        print_success("✓ Active bets response has correct structure")
        record_test("Active Bets Response Structure", True)
    
    # Check bet amounts in active bets
    active_bets = active_bets_response.get("bets", [])
    print_success(f"Found {len(active_bets)} active bets")
    
    active_bet_amounts_valid = True
    active_bet_amounts = []
    
    for i, bet in enumerate(active_bets):
        bet_amount = bet.get("bet_amount")
        game_id = bet.get("game_id", f"bet_{i}")
        
        if bet_amount is None:
            print_error(f"✗ Bet {game_id}: bet_amount field is missing")
            active_bet_amounts_valid = False
        elif bet_amount == 0:
            print_error(f"✗ Bet {game_id}: bet_amount is 0 (should be real amount)")
            active_bet_amounts_valid = False
        elif bet_amount > 0:
            print_success(f"✓ Bet {game_id}: bet_amount = ${bet_amount}")
            active_bet_amounts.append(bet_amount)
        else:
            print_error(f"✗ Bet {game_id}: bet_amount is negative (${bet_amount})")
            active_bet_amounts_valid = False
    
    if active_bet_amounts_valid and active_bets:
        print_success("✓ All active bets have valid bet_amount values")
        record_test("Active Bets - Bet Amount Field", True)
    elif not active_bets:
        print_warning("No active bets to validate amounts")
        record_test("Active Bets - Bet Amount Field", True, "No active bets")
    else:
        print_error("✗ Some active bets have invalid bet_amount values")
        record_test("Active Bets - Bet Amount Field", False, "Invalid bet amounts")
    
    # Step 5: Test /api/admin/human-bots/{bot_id}/all-bets endpoint
    print_subheader("Step 5: Test All Bets Endpoint - Bet Amount Fix")
    
    all_bets_response, all_bets_success = make_request(
        "GET", f"/admin/human-bots/{bot_id}/all-bets?page=1&limit=20",
        auth_token=admin_token
    )
    
    if not all_bets_success:
        print_error("Failed to get all bets")
        record_test("All Bets API", False, "API request failed")
        return
    
    print_success("✓ All bets API endpoint responded successfully")
    record_test("All Bets API", True)
    
    # Verify response structure
    required_all_bets_fields = ["success", "bot_id", "bot_name", "total_bets", "bets", "pagination"]
    missing_all_bets_fields = [field for field in required_all_bets_fields if field not in all_bets_response]
    
    if missing_all_bets_fields:
        print_error(f"All bets response missing fields: {missing_all_bets_fields}")
        record_test("All Bets Response Structure", False, f"Missing: {missing_all_bets_fields}")
    else:
        print_success("✓ All bets response has correct structure")
        record_test("All Bets Response Structure", True)
    
    # Check bet amounts in all bets
    all_bets = all_bets_response.get("bets", [])
    total_bets = all_bets_response.get("total_bets", 0)
    
    print_success(f"Found {len(all_bets)} bets in response (total: {total_bets})")
    
    all_bet_amounts_valid = True
    all_bet_amounts = []
    
    for i, bet in enumerate(all_bets):
        bet_amount = bet.get("bet_amount")
        game_id = bet.get("game_id", f"bet_{i}")
        status = bet.get("status", "unknown")
        
        if bet_amount is None:
            print_error(f"✗ Bet {game_id}: bet_amount field is missing")
            all_bet_amounts_valid = False
        elif bet_amount == 0:
            print_error(f"✗ Bet {game_id}: bet_amount is 0 (should be real amount)")
            all_bet_amounts_valid = False
        elif bet_amount > 0:
            print_success(f"✓ Bet {game_id} ({status}): bet_amount = ${bet_amount}")
            all_bet_amounts.append(bet_amount)
        else:
            print_error(f"✗ Bet {game_id}: bet_amount is negative (${bet_amount})")
            all_bet_amounts_valid = False
    
    if all_bet_amounts_valid and all_bets:
        print_success("✓ All bets have valid bet_amount values")
        record_test("All Bets - Bet Amount Field", True)
    elif not all_bets:
        print_warning("No bets to validate amounts")
        record_test("All Bets - Bet Amount Field", True, "No bets")
    else:
        print_error("✗ Some bets have invalid bet_amount values")
        record_test("All Bets - Bet Amount Field", False, "Invalid bet amounts")
    
    # Step 6: Compare with /api/games/available endpoint (reference)
    print_subheader("Step 6: Compare with /api/games/available (Reference)")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if not available_games_success:
        print_warning("Failed to get available games for comparison")
        record_test("Available Games Comparison", False, "API request failed")
    else:
        available_games = available_games_response if isinstance(available_games_response, list) else []
        
        # Find games created by Human-bots
        human_bot_games = []
        for game in available_games:
            if game.get("creator_type") == "human_bot" or game.get("bot_type") == "HUMAN":
                human_bot_games.append(game)
        
        print_success(f"Found {len(human_bot_games)} Human-bot games in available games")
        
        # Check bet amounts in available games
        available_amounts_valid = True
        available_bet_amounts = []
        
        for game in human_bot_games[:10]:  # Check first 10 games
            bet_amount = game.get("bet_amount")
            game_id = game.get("game_id", "unknown")
            creator_id = game.get("creator_id", "unknown")
            
            if bet_amount is None:
                print_error(f"✗ Available game {game_id}: bet_amount field is missing")
                available_amounts_valid = False
            elif bet_amount == 0:
                print_error(f"✗ Available game {game_id}: bet_amount is 0")
                available_amounts_valid = False
            elif bet_amount > 0:
                print_success(f"✓ Available game {game_id}: bet_amount = ${bet_amount}")
                available_bet_amounts.append(bet_amount)
            else:
                print_error(f"✗ Available game {game_id}: bet_amount is negative")
                available_amounts_valid = False
        
        if available_amounts_valid and human_bot_games:
            print_success("✓ Available games have valid bet_amount values")
            record_test("Available Games - Bet Amount Field", True)
        elif not human_bot_games:
            print_warning("No Human-bot games in available games")
            record_test("Available Games - Bet Amount Field", True, "No Human-bot games")
        else:
            print_error("✗ Some available games have invalid bet_amount values")
            record_test("Available Games - Bet Amount Field", False, "Invalid bet amounts")
        
        # Compare consistency between endpoints
        if active_bet_amounts and available_bet_amounts:
            print_success("✓ Both active bets and available games show non-zero bet amounts")
            print_success(f"Active bets amounts range: ${min(active_bet_amounts):.2f} - ${max(active_bet_amounts):.2f}")
            print_success(f"Available games amounts range: ${min(available_bet_amounts):.2f} - ${max(available_bet_amounts):.2f}")
            record_test("Bet Amount Consistency", True)
        else:
            print_warning("Cannot compare bet amounts (insufficient data)")
            record_test("Bet Amount Consistency", True, "Insufficient data")
    
    # Step 7: Test specific field presence and data types
    print_subheader("Step 7: Verify Field Presence and Data Types")
    
    field_validation_passed = True
    
    # Check active bets field types
    if active_bets:
        sample_active_bet = active_bets[0]
        
        # Required fields and their expected types
        expected_fields = {
            "game_id": str,
            "bet_amount": (int, float),
            "status": str,
            "created_at": str,
            "opponent": (str, type(None)),
            "time_until_cancel": (int, type(None))
        }
        
        for field_name, expected_type in expected_fields.items():
            if field_name not in sample_active_bet:
                print_error(f"✗ Active bet missing field: {field_name}")
                field_validation_passed = False
            else:
                field_value = sample_active_bet[field_name]
                if not isinstance(field_value, expected_type):
                    print_error(f"✗ Active bet field {field_name} has wrong type: {type(field_value)} (expected {expected_type})")
                    field_validation_passed = False
                else:
                    print_success(f"✓ Active bet field {field_name}: {type(field_value).__name__}")
    
    # Check all bets field types
    if all_bets:
        sample_all_bet = all_bets[0]
        
        for field_name, expected_type in expected_fields.items():
            if field_name not in sample_all_bet:
                print_error(f"✗ All bet missing field: {field_name}")
                field_validation_passed = False
            else:
                field_value = sample_all_bet[field_name]
                if not isinstance(field_value, expected_type):
                    print_error(f"✗ All bet field {field_name} has wrong type: {type(field_value)} (expected {expected_type})")
                    field_validation_passed = False
                else:
                    print_success(f"✓ All bet field {field_name}: {type(field_value).__name__}")
    
    if field_validation_passed:
        print_success("✓ All required fields present with correct data types")
        record_test("Field Validation", True)
    else:
        print_error("✗ Some fields missing or have incorrect data types")
        record_test("Field Validation", False, "Field validation failed")
    
    # Step 8: Test with different Human-bots (if available)
    print_subheader("Step 8: Test Multiple Human-Bots")
    
    if len(human_bots) > 1:
        # Test with second bot
        second_bot = human_bots[1]
        second_bot_id = second_bot["id"]
        second_bot_name = second_bot["name"]
        
        print_success(f"Testing second bot: {second_bot_name}")
        
        second_active_response, second_active_success = make_request(
            "GET", f"/admin/human-bots/{second_bot_id}/active-bets",
            auth_token=admin_token
        )
        
        if second_active_success:
            second_bets = second_active_response.get("bets", [])
            second_amounts_valid = True
            
            for bet in second_bets:
                bet_amount = bet.get("bet_amount")
                if bet_amount is None or bet_amount <= 0:
                    second_amounts_valid = False
                    break
            
            if second_amounts_valid:
                print_success(f"✓ Second bot ({second_bot_name}) also has valid bet amounts")
                record_test("Multiple Bots - Bet Amounts", True)
            else:
                print_error(f"✗ Second bot ({second_bot_name}) has invalid bet amounts")
                record_test("Multiple Bots - Bet Amounts", False, "Invalid amounts")
        else:
            print_warning(f"Failed to get active bets for second bot")
            record_test("Multiple Bots - Bet Amounts", False, "API request failed")
    else:
        print_warning("Only one Human-bot available for testing")
        record_test("Multiple Bots - Bet Amounts", True, "Only one bot available")
    
    # Step 9: Summary and final validation
    print_subheader("Step 9: Final Validation Summary")
    
    # Count successful validations
    critical_tests = [
        "Active Bets - Bet Amount Field",
        "All Bets - Bet Amount Field", 
        "Field Validation"
    ]
    
    critical_passed = 0
    for test in test_results["tests"]:
        if test["name"] in critical_tests and test["passed"]:
            critical_passed += 1
    
    if critical_passed == len(critical_tests):
        print_success("✓ CRITICAL FIX VERIFICATION PASSED")
        print_success("✓ bet_amount field is now correctly returned in both endpoints")
        print_success("✓ No more 0 values in bet amounts")
        print_success("✓ Response structure is correct")
        record_test("Human-Bot Bet Amount Fix - Overall", True)
    else:
        print_error("✗ CRITICAL FIX VERIFICATION FAILED")
        print_error(f"Only {critical_passed}/{len(critical_tests)} critical tests passed")
        record_test("Human-Bot Bet Amount Fix - Overall", False, f"Only {critical_passed}/{len(critical_tests)} passed")

def print_test_summary():
    """Print final test summary."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    print(f"Total tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    
    if failed > 0:
        print(f"\n{Colors.FAIL}FAILED TESTS:{Colors.ENDC}")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"  ✗ {test['name']}: {test['details']}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"{Colors.OKGREEN}✓ HUMAN-BOT BET AMOUNT FIX IS WORKING CORRECTLY{Colors.ENDC}")
    elif success_rate >= 70:
        print(f"{Colors.WARNING}⚠ HUMAN-BOT BET AMOUNT FIX HAS MINOR ISSUES{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ HUMAN-BOT BET AMOUNT FIX HAS MAJOR ISSUES{Colors.ENDC}")

if __name__ == "__main__":
    try:
        test_human_bot_bet_amounts_fix()
        print_test_summary()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Test failed with error: {e}{Colors.ENDC}")
        sys.exit(1)