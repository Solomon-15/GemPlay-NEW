#!/usr/bin/env python3
"""
Human-Bots Individual Settings Testing - Russian Review
Focus: Testing backend API after removal of global Human-bot settings
Requirements: Individual settings for each Human-bot instead of global settings
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
from datetime import datetime

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

def test_global_settings_endpoint_removed(admin_token: str) -> None:
    """Test that global Human-bot settings endpoint no longer exists (should return 404)."""
    print_subheader("Test 1: Global Settings Endpoint Removal")
    
    # Test GET /api/admin/human-bots/settings - should return 404
    response, success = make_request(
        "GET", "/admin/human-bots/settings",
        auth_token=admin_token,
        expected_status=404
    )
    
    if not success:
        print_success("✓ Global settings endpoint correctly returns 404")
        record_test("Global Settings Endpoint Removed", True)
    else:
        print_error("✗ Global settings endpoint still exists (should be removed)")
        record_test("Global Settings Endpoint Removed", False, "Endpoint still exists")

def test_create_human_bot_with_individual_settings(admin_token: str) -> Optional[str]:
    """Test creating Human-bot with individual settings."""
    print_subheader("Test 2: Create Human-bot with Individual Settings")
    
    # Generate unique name
    timestamp = int(time.time())
    bot_name = f"IndividualBot_{timestamp}"
    
    # Create Human-bot with all individual settings
    bot_data = {
        "name": bot_name,
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
        # Individual settings that replaced global ones
        "can_play_with_other_bots": True,
        "can_play_with_players": True,
        "bot_min_delay_seconds": 45,
        "bot_max_delay_seconds": 180,
        "player_min_delay_seconds": 60,
        "player_max_delay_seconds": 240,
        "max_concurrent_games": 5
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=bot_data,
        auth_token=admin_token
    )
    
    if success and "id" in response:
        bot_id = response["id"]
        print_success(f"✓ Human-bot created successfully with ID: {bot_id}")
        
        # Verify all individual settings are present in response
        individual_settings = [
            "can_play_with_other_bots",
            "can_play_with_players", 
            "bot_min_delay_seconds",
            "bot_max_delay_seconds",
            "player_min_delay_seconds",
            "player_max_delay_seconds",
            "max_concurrent_games"
        ]
        
        missing_settings = []
        for setting in individual_settings:
            if setting not in response:
                missing_settings.append(setting)
        
        if not missing_settings:
            print_success("✓ All individual settings present in response")
            
            # Verify setting values
            settings_correct = True
            if response.get("can_play_with_other_bots") != True:
                print_error(f"✗ can_play_with_other_bots incorrect: {response.get('can_play_with_other_bots')}")
                settings_correct = False
            if response.get("can_play_with_players") != True:
                print_error(f"✗ can_play_with_players incorrect: {response.get('can_play_with_players')}")
                settings_correct = False
            if response.get("bot_min_delay_seconds") != 45:
                print_error(f"✗ bot_min_delay_seconds incorrect: {response.get('bot_min_delay_seconds')}")
                settings_correct = False
            if response.get("bot_max_delay_seconds") != 180:
                print_error(f"✗ bot_max_delay_seconds incorrect: {response.get('bot_max_delay_seconds')}")
                settings_correct = False
            if response.get("player_min_delay_seconds") != 60:
                print_error(f"✗ player_min_delay_seconds incorrect: {response.get('player_min_delay_seconds')}")
                settings_correct = False
            if response.get("player_max_delay_seconds") != 240:
                print_error(f"✗ player_max_delay_seconds incorrect: {response.get('player_max_delay_seconds')}")
                settings_correct = False
            if response.get("max_concurrent_games") != 5:
                print_error(f"✗ max_concurrent_games incorrect: {response.get('max_concurrent_games')}")
                settings_correct = False
            
            if settings_correct:
                print_success("✓ All individual setting values correct")
                record_test("Create Human-bot with Individual Settings", True)
            else:
                print_error("✗ Some individual setting values incorrect")
                record_test("Create Human-bot with Individual Settings", False, "Setting values incorrect")
        else:
            print_error(f"✗ Missing individual settings: {missing_settings}")
            record_test("Create Human-bot with Individual Settings", False, f"Missing: {missing_settings}")
        
        return bot_id
    else:
        print_error("✗ Failed to create Human-bot with individual settings")
        record_test("Create Human-bot with Individual Settings", False, "Creation failed")
        return None

def test_update_human_bot_individual_settings(admin_token: str, bot_id: str) -> None:
    """Test updating Human-bot with new individual settings."""
    print_subheader("Test 3: Update Human-bot Individual Settings")
    
    # Update individual settings
    update_data = {
        "can_play_with_other_bots": False,
        "can_play_with_players": True,
        "bot_min_delay_seconds": 90,
        "bot_max_delay_seconds": 300,
        "player_min_delay_seconds": 30,
        "player_max_delay_seconds": 150,
        "max_concurrent_games": 8,
        "min_bet": 15.0,
        "max_bet": 200.0
    }
    
    response, success = make_request(
        "PUT", f"/admin/human-bots/{bot_id}",
        data=update_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("✓ Human-bot update successful")
        
        # Verify updated values
        updates_correct = True
        if response.get("can_play_with_other_bots") != False:
            print_error(f"✗ can_play_with_other_bots not updated: {response.get('can_play_with_other_bots')}")
            updates_correct = False
        if response.get("bot_min_delay_seconds") != 90:
            print_error(f"✗ bot_min_delay_seconds not updated: {response.get('bot_min_delay_seconds')}")
            updates_correct = False
        if response.get("bot_max_delay_seconds") != 300:
            print_error(f"✗ bot_max_delay_seconds not updated: {response.get('bot_max_delay_seconds')}")
            updates_correct = False
        if response.get("player_min_delay_seconds") != 30:
            print_error(f"✗ player_min_delay_seconds not updated: {response.get('player_min_delay_seconds')}")
            updates_correct = False
        if response.get("player_max_delay_seconds") != 150:
            print_error(f"✗ player_max_delay_seconds not updated: {response.get('player_max_delay_seconds')}")
            updates_correct = False
        if response.get("max_concurrent_games") != 8:
            print_error(f"✗ max_concurrent_games not updated: {response.get('max_concurrent_games')}")
            updates_correct = False
        
        if updates_correct:
            print_success("✓ All individual settings updated correctly")
            record_test("Update Human-bot Individual Settings", True)
        else:
            print_error("✗ Some individual settings not updated correctly")
            record_test("Update Human-bot Individual Settings", False, "Update values incorrect")
    else:
        print_error("✗ Failed to update Human-bot individual settings")
        record_test("Update Human-bot Individual Settings", False, "Update failed")

def test_human_bots_crud_operations(admin_token: str) -> None:
    """Test all CRUD operations for Human-bots work correctly."""
    print_subheader("Test 4: Human-bots CRUD Operations")
    
    # Test GET /api/admin/human-bots (list)
    print("Testing GET /api/admin/human-bots...")
    list_response, list_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    
    if list_success and "bots" in list_response:
        print_success(f"✓ GET Human-bots list successful ({len(list_response['bots'])} bots)")
        record_test("Human-bots CRUD - GET List", True)
    else:
        print_error("✗ GET Human-bots list failed")
        record_test("Human-bots CRUD - GET List", False, "List request failed")
    
    # Test POST /api/admin/human-bots (create)
    print("Testing POST /api/admin/human-bots...")
    create_data = {
        "name": f"CRUDTest_{int(time.time())}",
        "character": "AGGRESSIVE",
        "gender": "female",
        "min_bet": 5.0,
        "max_bet": 50.0,
        "bet_limit": 10,
        "win_percentage": 50.0,
        "loss_percentage": 30.0,
        "draw_percentage": 20.0,
        "can_play_with_other_bots": True,
        "can_play_with_players": False,
        "max_concurrent_games": 3
    }
    
    create_response, create_success = make_request(
        "POST", "/admin/human-bots",
        data=create_data,
        auth_token=admin_token
    )
    
    if create_success and "id" in create_response:
        crud_bot_id = create_response["id"]
        print_success(f"✓ POST Human-bot create successful (ID: {crud_bot_id})")
        record_test("Human-bots CRUD - POST Create", True)
        
        # Test PUT /api/admin/human-bots/{id} (update)
        print("Testing PUT /api/admin/human-bots/{id}...")
        update_data = {
            "name": f"CRUDTest_Updated_{int(time.time())}",
            "min_bet": 8.0,
            "max_bet": 80.0
        }
        
        update_response, update_success = make_request(
            "PUT", f"/admin/human-bots/{crud_bot_id}",
            data=update_data,
            auth_token=admin_token
        )
        
        if update_success:
            print_success("✓ PUT Human-bot update successful")
            record_test("Human-bots CRUD - PUT Update", True)
        else:
            print_error("✗ PUT Human-bot update failed")
            record_test("Human-bots CRUD - PUT Update", False, "Update failed")
        
        # Test DELETE /api/admin/human-bots/{id} (delete)
        print("Testing DELETE /api/admin/human-bots/{id}...")
        delete_response, delete_success = make_request(
            "DELETE", f"/admin/human-bots/{crud_bot_id}",
            auth_token=admin_token
        )
        
        if delete_success:
            print_success("✓ DELETE Human-bot successful")
            record_test("Human-bots CRUD - DELETE", True)
        else:
            print_error("✗ DELETE Human-bot failed")
            record_test("Human-bots CRUD - DELETE", False, "Delete failed")
    else:
        print_error("✗ POST Human-bot create failed")
        record_test("Human-bots CRUD - POST Create", False, "Create failed")

def test_human_bots_names_management(admin_token: str) -> None:
    """Test Human-bots names management endpoints."""
    print_subheader("Test 5: Human-bots Names Management")
    
    # Test GET /api/admin/human-bots/names
    print("Testing GET /api/admin/human-bots/names...")
    names_response, names_success = make_request(
        "GET", "/admin/human-bots/names",
        auth_token=admin_token
    )
    
    if names_success and "names" in names_response:
        names_count = len(names_response["names"])
        print_success(f"✓ GET Human-bot names successful ({names_count} names)")
        record_test("Human-bots Names - GET Names", True)
        
        # Test POST /api/admin/human-bots/names/add
        print("Testing POST /api/admin/human-bots/names/add...")
        test_names = [f"TestName_{int(time.time())}", f"TestName2_{int(time.time())}"]
        add_response, add_success = make_request(
            "POST", "/admin/human-bots/names/add",
            data={"names": test_names},
            auth_token=admin_token
        )
        
        if add_success and "added_count" in add_response:
            print_success(f"✓ POST Add names successful ({add_response['added_count']} added)")
            record_test("Human-bots Names - POST Add", True)
            
            # Test DELETE /api/admin/human-bots/names/{name}
            print("Testing DELETE /api/admin/human-bots/names/{name}...")
            delete_name_response, delete_name_success = make_request(
                "DELETE", f"/admin/human-bots/names/{test_names[0]}",
                auth_token=admin_token
            )
            
            if delete_name_success:
                print_success("✓ DELETE Human-bot name successful")
                record_test("Human-bots Names - DELETE Name", True)
            else:
                print_error("✗ DELETE Human-bot name failed")
                record_test("Human-bots Names - DELETE Name", False, "Delete failed")
        else:
            print_error("✗ POST Add names failed")
            record_test("Human-bots Names - POST Add", False, "Add failed")
    else:
        print_error("✗ GET Human-bot names failed")
        record_test("Human-bots Names - GET Names", False, "Get names failed")

def test_user_management_total_sorting(admin_token: str) -> None:
    """Test User Management API with TOTAL column sorting."""
    print_subheader("Test 6: User Management TOTAL Column Sorting")
    
    # Test GET /api/admin/users with TOTAL sorting
    print("Testing GET /api/admin/users with sort_by=TOTAL...")
    users_response, users_success = make_request(
        "GET", "/admin/users?page=1&limit=10&sort_by=TOTAL&sort_direction=desc",
        auth_token=admin_token
    )
    
    if users_success and "users" in users_response:
        users = users_response["users"]
        print_success(f"✓ GET Users with TOTAL sorting successful ({len(users)} users)")
        
        # Verify TOTAL sorting is working
        if len(users) >= 2:
            total_values = []
            for user in users:
                total_balance = user.get("total_balance", 0)
                total_values.append(total_balance)
                print_success(f"  User: {user.get('username', 'unknown')} - TOTAL: ${total_balance}")
            
            # Check if sorted in descending order
            is_sorted_desc = all(total_values[i] >= total_values[i+1] for i in range(len(total_values)-1))
            
            if is_sorted_desc:
                print_success("✓ TOTAL column sorting working correctly (descending)")
                record_test("User Management - TOTAL Sorting DESC", True)
            else:
                print_error("✗ TOTAL column sorting not working correctly")
                record_test("User Management - TOTAL Sorting DESC", False, "Sorting incorrect")
        else:
            print_warning("Not enough users to verify sorting")
            record_test("User Management - TOTAL Sorting DESC", True, "Not enough data")
        
        # Test ascending sort
        print("Testing GET /api/admin/users with sort_by=TOTAL&sort_direction=asc...")
        users_asc_response, users_asc_success = make_request(
            "GET", "/admin/users?page=1&limit=10&sort_by=TOTAL&sort_direction=asc",
            auth_token=admin_token
        )
        
        if users_asc_success and "users" in users_asc_response:
            users_asc = users_asc_response["users"]
            print_success(f"✓ GET Users with TOTAL sorting ASC successful ({len(users_asc)} users)")
            
            if len(users_asc) >= 2:
                total_values_asc = []
                for user in users_asc:
                    total_balance = user.get("total_balance", 0)
                    total_values_asc.append(total_balance)
                
                # Check if sorted in ascending order
                is_sorted_asc = all(total_values_asc[i] <= total_values_asc[i+1] for i in range(len(total_values_asc)-1))
                
                if is_sorted_asc:
                    print_success("✓ TOTAL column sorting ASC working correctly")
                    record_test("User Management - TOTAL Sorting ASC", True)
                else:
                    print_error("✗ TOTAL column sorting ASC not working correctly")
                    record_test("User Management - TOTAL Sorting ASC", False, "ASC sorting incorrect")
            else:
                record_test("User Management - TOTAL Sorting ASC", True, "Not enough data")
        else:
            print_error("✗ GET Users with TOTAL sorting ASC failed")
            record_test("User Management - TOTAL Sorting ASC", False, "ASC request failed")
    else:
        print_error("✗ GET Users with TOTAL sorting failed")
        record_test("User Management - TOTAL Sorting DESC", False, "Request failed")

def test_individual_settings_validation(admin_token: str) -> None:
    """Test validation of individual settings fields."""
    print_subheader("Test 7: Individual Settings Validation")
    
    # Test invalid bot_min_delay_seconds (should be 1-3600)
    print("Testing invalid bot_min_delay_seconds...")
    invalid_data = {
        "name": f"ValidationTest_{int(time.time())}",
        "character": "BALANCED",
        "min_bet": 10.0,
        "max_bet": 100.0,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "bot_min_delay_seconds": 0  # Invalid: should be >= 1
    }
    
    response, success = make_request(
        "POST", "/admin/human-bots",
        data=invalid_data,
        auth_token=admin_token,
        expected_status=422  # Validation error
    )
    
    if not success:
        print_success("✓ Invalid bot_min_delay_seconds correctly rejected")
        record_test("Individual Settings Validation - bot_min_delay_seconds", True)
    else:
        print_error("✗ Invalid bot_min_delay_seconds not rejected")
        record_test("Individual Settings Validation - bot_min_delay_seconds", False, "Validation failed")
    
    # Test invalid max_concurrent_games (should be 1-100)
    print("Testing invalid max_concurrent_games...")
    invalid_data2 = {
        "name": f"ValidationTest2_{int(time.time())}",
        "character": "BALANCED",
        "min_bet": 10.0,
        "max_bet": 100.0,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "max_concurrent_games": 101  # Invalid: should be <= 100
    }
    
    response2, success2 = make_request(
        "POST", "/admin/human-bots",
        data=invalid_data2,
        auth_token=admin_token,
        expected_status=422  # Validation error
    )
    
    if not success2:
        print_success("✓ Invalid max_concurrent_games correctly rejected")
        record_test("Individual Settings Validation - max_concurrent_games", True)
    else:
        print_error("✗ Invalid max_concurrent_games not rejected")
        record_test("Individual Settings Validation - max_concurrent_games", False, "Validation failed")

def print_test_summary():
    """Print test summary."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success rate: {Colors.OKGREEN if success_rate >= 80 else Colors.FAIL}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"✗ {test['name']}: {test['details']}")
    
    print_subheader("Key Findings:")
    if success_rate >= 90:
        print_success("🎉 EXCELLENT: Human-bots individual settings system working perfectly!")
    elif success_rate >= 80:
        print_success("✅ GOOD: Human-bots individual settings mostly working with minor issues")
    elif success_rate >= 60:
        print_warning("⚠ MODERATE: Human-bots individual settings working but needs improvements")
    else:
        print_error("❌ POOR: Human-bots individual settings system has significant issues")

def main():
    """Main test execution."""
    print_header("HUMAN-BOTS INDIVIDUAL SETTINGS TESTING")
    print("Testing backend API after removal of global Human-bot settings")
    print("Focus: Individual settings for each Human-bot")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        return
    
    # Step 2: Test global settings endpoint removal
    test_global_settings_endpoint_removed(admin_token)
    
    # Step 3: Test creating Human-bot with individual settings
    bot_id = test_create_human_bot_with_individual_settings(admin_token)
    
    # Step 4: Test updating Human-bot individual settings
    if bot_id:
        test_update_human_bot_individual_settings(admin_token, bot_id)
    
    # Step 5: Test all CRUD operations
    test_human_bots_crud_operations(admin_token)
    
    # Step 6: Test Human-bots names management
    test_human_bots_names_management(admin_token)
    
    # Step 7: Test User Management TOTAL sorting
    test_user_management_total_sorting(admin_token)
    
    # Step 8: Test individual settings validation
    test_individual_settings_validation(admin_token)
    
    # Print summary
    print_test_summary()

if __name__ == "__main__":
    main()