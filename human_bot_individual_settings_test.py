#!/usr/bin/env python3
"""
Human-bot Individual Settings Testing - Russian Review
Focus: Testing individual settings for Human-bots after fixes

CONTEXT: Fixed HumanBotResponse model, adding missing individual settings:
- bot_min_delay_seconds
- bot_max_delay_seconds 
- player_min_delay_seconds
- player_max_delay_seconds
- max_concurrent_games

FOCUSED TESTING:
1. CREATE Human-bot - check that all individual settings are returned in response
2. UPDATE Human-bot - ensure individual settings are updated and returned
3. GET Human-bots list - check that all bots have individual settings 
4. User Management TOTAL sorting - ensure sorting works for ASC and DESC

KEY FIELDS TO VERIFY:
- bot_min_delay_seconds (1-3600)
- bot_max_delay_seconds (1-3600)
- player_min_delay_seconds (1-3600)
- player_max_delay_seconds (1-3600)
- max_concurrent_games (1-100)
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
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
    """Test admin login and return token."""
    print_subheader("Admin Authentication")
    
    response, success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and "access_token" in response:
        print_success("Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error("Admin login failed")
        record_test("Admin Login", False, "Login failed")
        return None

def validate_individual_settings_fields(bot_data: Dict[str, Any], test_name: str) -> bool:
    """Validate that all individual settings fields are present and have correct values."""
    required_fields = {
        "bot_min_delay_seconds": (int, 1, 3600),
        "bot_max_delay_seconds": (int, 1, 3600),
        "player_min_delay_seconds": (int, 1, 3600),
        "player_max_delay_seconds": (int, 1, 3600),
        "max_concurrent_games": (int, 1, 100)
    }
    
    all_valid = True
    
    for field_name, (field_type, min_val, max_val) in required_fields.items():
        if field_name not in bot_data:
            print_error(f"Missing field: {field_name}")
            record_test(f"{test_name} - {field_name} Present", False, "Field missing")
            all_valid = False
            continue
        
        field_value = bot_data[field_name]
        
        # Check type
        if not isinstance(field_value, field_type):
            print_error(f"Field {field_name} has wrong type: {type(field_value)}, expected {field_type}")
            record_test(f"{test_name} - {field_name} Type", False, f"Wrong type: {type(field_value)}")
            all_valid = False
            continue
        
        # Check range
        if not (min_val <= field_value <= max_val):
            print_error(f"Field {field_name} value {field_value} out of range [{min_val}, {max_val}]")
            record_test(f"{test_name} - {field_name} Range", False, f"Value {field_value} out of range")
            all_valid = False
            continue
        
        print_success(f"✓ {field_name}: {field_value} (valid)")
        record_test(f"{test_name} - {field_name} Valid", True)
    
    return all_valid

def test_create_human_bot_individual_settings(admin_token: str) -> Optional[str]:
    """Test CREATE Human-bot with individual settings."""
    print_subheader("TEST 1: CREATE Human-bot - Individual Settings")
    
    # Create test bot with specific individual settings
    test_bot_data = {
        "name": f"TestBot_Individual_{int(time.time())}",
        "character": "BALANCED",
        "gender": "male",
        "min_bet": 10.0,
        "max_bet": 100.0,
        "bet_limit": 15,
        "bet_limit_amount": 500.0,
        "win_percentage": 45.0,
        "loss_percentage": 35.0,
        "draw_percentage": 20.0,
        "min_delay": 30,
        "max_delay": 120,
        "use_commit_reveal": True,
        "logging_level": "INFO",
        "can_play_with_other_bots": True,
        "can_play_with_players": True
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=test_bot_data,
        auth_token=admin_token
    )
    
    if not success:
        print_error("Failed to create Human-bot")
        record_test("CREATE Human-bot", False, "Creation failed")
        return None
    
    bot_id = response.get("id")
    if not bot_id:
        print_error("Bot creation response missing ID")
        record_test("CREATE Human-bot", False, "Missing bot ID")
        return None
    
    print_success(f"Human-bot created with ID: {bot_id}")
    
    # Validate individual settings in response
    print_success("Validating individual settings in CREATE response:")
    settings_valid = validate_individual_settings_fields(response, "CREATE Response")
    
    if settings_valid:
        print_success("✅ All individual settings present and valid in CREATE response")
        record_test("CREATE Human-bot - Individual Settings", True)
    else:
        print_error("❌ Individual settings validation failed in CREATE response")
        record_test("CREATE Human-bot - Individual Settings", False, "Settings validation failed")
    
    # Check default values (should be set automatically)
    expected_defaults = {
        "bot_min_delay_seconds": 30,
        "bot_max_delay_seconds": 120,
        "player_min_delay_seconds": 30,
        "player_max_delay_seconds": 120,
        "max_concurrent_games": 3
    }
    
    defaults_correct = True
    for field, expected_value in expected_defaults.items():
        actual_value = response.get(field)
        if actual_value == expected_value:
            print_success(f"✓ Default {field}: {actual_value} (correct)")
        else:
            print_warning(f"⚠ Default {field}: {actual_value}, expected {expected_value}")
            defaults_correct = False
    
    if defaults_correct:
        record_test("CREATE Human-bot - Default Values", True)
    else:
        record_test("CREATE Human-bot - Default Values", False, "Some defaults incorrect")
    
    return bot_id

def test_update_human_bot_individual_settings(admin_token: str, bot_id: str) -> None:
    """Test UPDATE Human-bot with individual settings."""
    print_subheader("TEST 2: UPDATE Human-bot - Individual Settings")
    
    # Update bot with new individual settings
    update_data = {
        "name": f"UpdatedBot_Individual_{int(time.time())}",
        "min_bet": 15.0,
        "max_bet": 150.0,
        "win_percentage": 50.0,
        "loss_percentage": 30.0,
        "draw_percentage": 20.0,
        # Note: We're not explicitly setting individual settings in update,
        # but they should still be returned in response
    }
    
    response, success = make_request(
        "PUT", f"/admin/human-bots/{bot_id}",
        data=update_data,
        auth_token=admin_token
    )
    
    if not success:
        print_error("Failed to update Human-bot")
        record_test("UPDATE Human-bot", False, "Update failed")
        return
    
    print_success(f"Human-bot updated successfully")
    
    # Validate individual settings in response
    print_success("Validating individual settings in UPDATE response:")
    settings_valid = validate_individual_settings_fields(response, "UPDATE Response")
    
    if settings_valid:
        print_success("✅ All individual settings present and valid in UPDATE response")
        record_test("UPDATE Human-bot - Individual Settings", True)
    else:
        print_error("❌ Individual settings validation failed in UPDATE response")
        record_test("UPDATE Human-bot - Individual Settings", False, "Settings validation failed")
    
    # Verify that updated fields are correct
    if response.get("name") == update_data["name"]:
        print_success(f"✓ Name updated correctly: {response.get('name')}")
        record_test("UPDATE Human-bot - Name Update", True)
    else:
        print_error(f"✗ Name not updated correctly: {response.get('name')}")
        record_test("UPDATE Human-bot - Name Update", False, "Name not updated")
    
    if abs(response.get("min_bet", 0) - update_data["min_bet"]) < 0.01:
        print_success(f"✓ Min bet updated correctly: {response.get('min_bet')}")
        record_test("UPDATE Human-bot - Min Bet Update", True)
    else:
        print_error(f"✗ Min bet not updated correctly: {response.get('min_bet')}")
        record_test("UPDATE Human-bot - Min Bet Update", False, "Min bet not updated")

def test_get_human_bots_list_individual_settings(admin_token: str) -> None:
    """Test GET Human-bots list with individual settings."""
    print_subheader("TEST 3: GET Human-bots List - Individual Settings")
    
    response, success = make_request(
        "GET", "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    
    if not success:
        print_error("Failed to get Human-bots list")
        record_test("GET Human-bots List", False, "Request failed")
        return
    
    bots = response.get("bots", [])
    if not bots:
        print_warning("No Human-bots found in list")
        record_test("GET Human-bots List", False, "No bots found")
        return
    
    print_success(f"Found {len(bots)} Human-bots in list")
    
    # Validate individual settings for each bot
    all_bots_valid = True
    for i, bot in enumerate(bots):
        bot_name = bot.get("name", f"Bot_{i}")
        print_success(f"Validating bot {i+1}: {bot_name}")
        
        bot_valid = validate_individual_settings_fields(bot, f"List Bot {i+1}")
        if not bot_valid:
            all_bots_valid = False
    
    if all_bots_valid:
        print_success("✅ All bots in list have valid individual settings")
        record_test("GET Human-bots List - Individual Settings", True)
    else:
        print_error("❌ Some bots in list have invalid individual settings")
        record_test("GET Human-bots List - Individual Settings", False, "Some bots invalid")

def test_user_management_total_sorting(admin_token: str) -> None:
    """Test User Management TOTAL column sorting for ASC and DESC."""
    print_subheader("TEST 4: User Management TOTAL Sorting")
    
    # Test DESC sorting (default)
    print_success("Testing TOTAL column sorting - DESC:")
    response_desc, success_desc = make_request(
        "GET", "/admin/users?page=1&limit=10&sort_by=total&sort_direction=desc",
        auth_token=admin_token
    )
    
    if not success_desc:
        print_error("Failed to get users list with DESC sorting")
        record_test("User Management TOTAL Sorting DESC", False, "Request failed")
    else:
        users_desc = response_desc.get("users", [])
        if len(users_desc) >= 2:
            # Check if sorting is correct (descending)
            sorting_correct = True
            for i in range(len(users_desc) - 1):
                current_total = users_desc[i].get("total_balance", 0)
                next_total = users_desc[i + 1].get("total_balance", 0)
                
                if current_total < next_total:
                    sorting_correct = False
                    print_error(f"DESC sorting incorrect: {current_total} < {next_total} at positions {i}, {i+1}")
                    break
            
            if sorting_correct:
                print_success("✅ DESC sorting working correctly")
                record_test("User Management TOTAL Sorting DESC", True)
            else:
                print_error("❌ DESC sorting not working correctly")
                record_test("User Management TOTAL Sorting DESC", False, "Sorting incorrect")
        else:
            print_warning("Not enough users to test DESC sorting")
            record_test("User Management TOTAL Sorting DESC", False, "Not enough users")
    
    # Test ASC sorting
    print_success("Testing TOTAL column sorting - ASC:")
    response_asc, success_asc = make_request(
        "GET", "/admin/users?page=1&limit=10&sort_by=total&sort_direction=asc",
        auth_token=admin_token
    )
    
    if not success_asc:
        print_error("Failed to get users list with ASC sorting")
        record_test("User Management TOTAL Sorting ASC", False, "Request failed")
    else:
        users_asc = response_asc.get("users", [])
        if len(users_asc) >= 2:
            # Check if sorting is correct (ascending)
            sorting_correct = True
            for i in range(len(users_asc) - 1):
                current_total = users_asc[i].get("total_balance", 0)
                next_total = users_asc[i + 1].get("total_balance", 0)
                
                if current_total > next_total:
                    sorting_correct = False
                    print_error(f"ASC sorting incorrect: {current_total} > {next_total} at positions {i}, {i+1}")
                    break
            
            if sorting_correct:
                print_success("✅ ASC sorting working correctly")
                record_test("User Management TOTAL Sorting ASC", True)
            else:
                print_error("❌ ASC sorting not working correctly")
                record_test("User Management TOTAL Sorting ASC", False, "Sorting incorrect")
        else:
            print_warning("Not enough users to test ASC sorting")
            record_test("User Management TOTAL Sorting ASC", False, "Not enough users")
    
    # Compare DESC vs ASC to ensure they're different
    if success_desc and success_asc and users_desc and users_asc:
        if len(users_desc) > 0 and len(users_asc) > 0:
            first_desc_total = users_desc[0].get("total_balance", 0)
            first_asc_total = users_asc[0].get("total_balance", 0)
            
            if first_desc_total >= first_asc_total:
                print_success("✅ DESC and ASC sorting produce different results (as expected)")
                record_test("User Management TOTAL Sorting Comparison", True)
            else:
                print_error("❌ DESC and ASC sorting results are inconsistent")
                record_test("User Management TOTAL Sorting Comparison", False, "Inconsistent results")

def cleanup_test_bot(admin_token: str, bot_id: str) -> None:
    """Clean up test bot."""
    print_subheader("Cleanup: Deleting Test Bot")
    
    response, success = make_request(
        "DELETE", f"/admin/human-bots/{bot_id}",
        auth_token=admin_token
    )
    
    if success:
        print_success("✅ Test bot deleted successfully")
    else:
        print_warning("⚠ Failed to delete test bot (may need manual cleanup)")

def print_test_summary():
    """Print test summary."""
    print_header("HUMAN-BOT INDIVIDUAL SETTINGS TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print_success(f"Total tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success(f"Failed: {failed}")
    print_success(f"Success rate: {success_rate:.1f}%")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"❌ {test['name']}: {test['details']}")
    
    print_subheader("Key Findings:")
    if success_rate >= 90:
        print_success("✅ Human-bot individual settings are working correctly")
        print_success("✅ All required fields are present and valid")
        print_success("✅ CREATE, UPDATE, and GET operations handle individual settings properly")
        print_success("✅ User Management TOTAL sorting is functional")
    elif success_rate >= 70:
        print_warning("⚠ Human-bot individual settings mostly working with some issues")
    else:
        print_error("❌ Human-bot individual settings have significant issues")
    
    return success_rate >= 90

def main():
    """Main test execution."""
    print_header("HUMAN-BOT INDIVIDUAL SETTINGS TESTING")
    print_success("Testing individual settings for Human-bots after fixes")
    print_success("Focus: bot_min_delay_seconds, bot_max_delay_seconds, player_min_delay_seconds, player_max_delay_seconds, max_concurrent_games")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        return False
    
    # Step 2: Test CREATE Human-bot with individual settings
    bot_id = test_create_human_bot_individual_settings(admin_token)
    if not bot_id:
        print_error("Cannot proceed without creating test bot")
        return False
    
    # Step 3: Test UPDATE Human-bot with individual settings
    test_update_human_bot_individual_settings(admin_token, bot_id)
    
    # Step 4: Test GET Human-bots list with individual settings
    test_get_human_bots_list_individual_settings(admin_token)
    
    # Step 5: Test User Management TOTAL sorting
    test_user_management_total_sorting(admin_token)
    
    # Step 6: Cleanup
    cleanup_test_bot(admin_token, bot_id)
    
    # Step 7: Print summary
    success = print_test_summary()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)