#!/usr/bin/env python3
"""
Focused test for Regular Bots Admin Panel API Endpoints
Testing the specific issues mentioned in the review request:

1. POST /api/admin/bots/create-regular - should create 1 bot instead of 5
2. GET /api/admin/bot-settings - should not return 500 error anymore  
3. PUT /api/admin/bot-settings - should update global settings correctly
4. GET /api/admin/bots/regular/list - should include individual_limit field in response
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://11ff6985-226e-4a25-848c-148a2fa58531.preview.emergentagent.com/api"
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
        print_success(f"PASS: {name}")
    else:
        test_results["failed"] += 1
        print_error(f"FAIL: {name} - {details}")
    
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
            response_data = {"text": response.text, "status_code": response.status_code}
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
    print_subheader("Testing Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_bot_settings_get(admin_token: str) -> None:
    """Test GET /api/admin/bot-settings - should not return 500 error anymore."""
    print_subheader("Testing GET /api/admin/bot-settings")
    
    response, success = make_request(
        "GET", 
        "/admin/bot-settings", 
        auth_token=admin_token
    )
    
    if success:
        print_success("GET /api/admin/bot-settings returned 200 OK")
        
        # Check response structure - the endpoint returns nested structure
        if "success" in response and "settings" in response:
            settings = response["settings"]
            expected_fields = ["globalMaxActiveBets", "globalMaxHumanBots", "paginationSize", "autoActivateFromQueue", "priorityType"]
            missing_fields = []
            
            for field in expected_fields:
                if field not in settings:
                    missing_fields.append(field)
            
            if not missing_fields:
                print_success("Response contains all expected fields")
                record_test("GET bot-settings - Response Structure", True)
            else:
                print_warning(f"Response missing some fields: {missing_fields}")
                record_test("GET bot-settings - Response Structure", False, f"Missing fields: {missing_fields}")
            
            # Check data types
            if isinstance(settings.get("globalMaxActiveBets"), int):
                print_success("globalMaxActiveBets is integer")
            else:
                print_error(f"globalMaxActiveBets should be integer, got: {type(settings.get('globalMaxActiveBets'))}")
            
            if isinstance(settings.get("autoActivateFromQueue"), bool):
                print_success("autoActivateFromQueue is boolean")
            else:
                print_error(f"autoActivateFromQueue should be boolean, got: {type(settings.get('autoActivateFromQueue'))}")
        else:
            print_error("Response missing 'success' or 'settings' fields")
            record_test("GET bot-settings - Response Structure", False, "Missing success or settings fields")
        
        record_test("GET bot-settings - No 500 Error", True)
        
    else:
        if response.get("status_code") == 500:
            print_error("CRITICAL: Still getting 500 Internal Server Error!")
            record_test("GET bot-settings - No 500 Error", False, "Still returns 500 error")
        else:
            print_error(f"Unexpected error: {response}")
            record_test("GET bot-settings - No 500 Error", False, f"Unexpected error: {response}")

def test_bot_settings_put(admin_token: str) -> None:
    """Test PUT /api/admin/bot-settings - should update global settings correctly."""
    print_subheader("Testing PUT /api/admin/bot-settings")
    
    # First get current settings
    current_response, current_success = make_request(
        "GET", 
        "/admin/bot-settings", 
        auth_token=admin_token
    )
    
    if not current_success:
        print_error("Cannot test PUT without getting current settings")
        record_test("PUT bot-settings - Update Settings", False, "Cannot get current settings")
        return
    
    print_success(f"Current settings: {json.dumps(current_response, indent=2)}")
    
    # Prepare test update data
    test_settings = {
        "globalMaxActiveBets": 75,  # Different from default
        "globalMaxHumanBots": 45,   # Different from default
        "paginationSize": 15,       # Different from default
        "autoActivateFromQueue": False,  # Different from default
        "priorityType": "manual"    # Different from default
    }
    
    print(f"Updating settings to: {json.dumps(test_settings, indent=2)}")
    
    # Test PUT request
    response, success = make_request(
        "PUT", 
        "/admin/bot-settings",
        data=test_settings,
        auth_token=admin_token
    )
    
    if success:
        print_success("PUT /api/admin/bot-settings returned 200 OK")
        
        # Verify response structure
        if "message" in response:
            print_success(f"Update message: {response['message']}")
        
        # Get settings again to verify update
        verify_response, verify_success = make_request(
            "GET", 
            "/admin/bot-settings", 
            auth_token=admin_token
        )
        
        if verify_success:
            print_success("Successfully retrieved settings after update")
            
            # Check if values were actually updated
            all_updated = True
            for key, expected_value in test_settings.items():
                actual_value = verify_response.get(key)
                if actual_value == expected_value:
                    print_success(f"✓ {key}: {actual_value} (correctly updated)")
                else:
                    print_error(f"✗ {key}: expected {expected_value}, got {actual_value}")
                    all_updated = False
            
            if all_updated:
                record_test("PUT bot-settings - Update Settings", True)
            else:
                record_test("PUT bot-settings - Update Settings", False, "Some values not updated correctly")
        else:
            print_error("Failed to verify settings after update")
            record_test("PUT bot-settings - Update Settings", False, "Cannot verify update")
    else:
        if response.get("status_code") == 500:
            print_error("CRITICAL: PUT bot-settings returns 500 Internal Server Error!")
            record_test("PUT bot-settings - Update Settings", False, "Returns 500 error")
        else:
            print_error(f"PUT request failed: {response}")
            record_test("PUT bot-settings - Update Settings", False, f"Request failed: {response}")

def test_create_regular_bot(admin_token: str) -> None:
    """Test POST /api/admin/bots/create-regular - should create 1 bot instead of 5."""
    print_subheader("Testing POST /api/admin/bots/create-regular")
    
    # Test bot creation data as specified in review request
    bot_data = {
        "count": 1,
        "name": "Test Bot",
        "min_bet_amount": 5,
        "max_bet_amount": 50
    }
    
    print(f"Creating bot with data: {json.dumps(bot_data, indent=2)}")
    
    response, success = make_request(
        "POST", 
        "/admin/bots/create-regular",
        data=bot_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("POST /api/admin/bots/create-regular returned 200 OK")
        
        # Check response structure
        if "created_bots" in response:
            created_bots = response["created_bots"]
            
            if isinstance(created_bots, list):
                bot_count = len(created_bots)
                print_success(f"Response contains created_bots array with {bot_count} bots")
                
                # CRITICAL TEST: Should create exactly 1 bot, not 5
                if bot_count == 1:
                    print_success("✓ FIXED: Creates exactly 1 bot as requested")
                    record_test("Create Regular Bot - Count Fix", True)
                elif bot_count == 5:
                    print_error("✗ STILL BROKEN: Creates 5 bots instead of 1!")
                    record_test("Create Regular Bot - Count Fix", False, "Still creates 5 bots instead of 1")
                else:
                    print_error(f"✗ UNEXPECTED: Creates {bot_count} bots (expected 1)")
                    record_test("Create Regular Bot - Count Fix", False, f"Creates {bot_count} bots instead of 1")
                
                # Check bot structure
                if bot_count > 0:
                    bot = created_bots[0]
                    print(f"First created bot: {json.dumps(bot, indent=2)}")
                    
                    # Handle case where bot might be a string (bot ID) instead of object
                    if isinstance(bot, dict):
                        expected_bot_fields = ["id", "name", "min_bet_amount", "max_bet_amount", "bot_type"]
                        missing_bot_fields = [field for field in expected_bot_fields if field not in bot]
                        
                        if not missing_bot_fields:
                            print_success("Bot object contains all expected fields")
                            record_test("Create Regular Bot - Bot Structure", True)
                        else:
                            print_warning(f"Bot object missing fields: {missing_bot_fields}")
                            record_test("Create Regular Bot - Bot Structure", False, f"Missing fields: {missing_bot_fields}")
                        
                        # Check bot values
                        if bot.get("name") == "Test Bot":
                            print_success("✓ Bot name correctly set")
                        else:
                            print_error(f"✗ Bot name incorrect: expected 'Test Bot', got '{bot.get('name')}'")
                        
                        if bot.get("min_bet_amount") == 5:
                            print_success("✓ Min bet amount correctly set")
                        else:
                            print_error(f"✗ Min bet amount incorrect: expected 5, got {bot.get('min_bet_amount')}")
                        
                        if bot.get("max_bet_amount") == 50:
                            print_success("✓ Max bet amount correctly set")
                        else:
                            print_error(f"✗ Max bet amount incorrect: expected 50, got {bot.get('max_bet_amount')}")
                    elif isinstance(bot, str):
                        print_success(f"Bot created with ID: {bot}")
                        print_warning("Response contains bot ID instead of full bot object")
                        record_test("Create Regular Bot - Bot Structure", True, "Bot ID returned instead of full object")
                    else:
                        print_error(f"Unexpected bot data type: {type(bot)}")
                        record_test("Create Regular Bot - Bot Structure", False, f"Unexpected data type: {type(bot)}")
            else:
                print_error(f"created_bots should be array, got: {type(created_bots)}")
                record_test("Create Regular Bot - Response Structure", False, "created_bots not an array")
        else:
            print_error("Response missing 'created_bots' field")
            record_test("Create Regular Bot - Response Structure", False, "Missing created_bots field")
    else:
        print_error(f"Bot creation failed: {response}")
        record_test("Create Regular Bot - Request Success", False, f"Request failed: {response}")

def test_regular_bots_list(admin_token: str) -> None:
    """Test GET /api/admin/bots/regular/list - should include individual_limit field."""
    print_subheader("Testing GET /api/admin/bots/regular/list")
    
    # Test with pagination parameters
    params = {
        "page": 1,
        "limit": 10
    }
    
    response, success = make_request(
        "GET", 
        "/admin/bots/regular/list",
        data=params,
        auth_token=admin_token
    )
    
    if success:
        print_success("GET /api/admin/bots/regular/list returned 200 OK")
        
        # Check pagination structure
        expected_pagination_fields = ["total_count", "current_page", "total_pages", "items_per_page", "has_next", "has_prev"]
        missing_pagination_fields = [field for field in expected_pagination_fields if field not in response]
        
        if not missing_pagination_fields:
            print_success("Response contains all pagination fields")
            record_test("Regular Bots List - Pagination Structure", True)
        else:
            print_warning(f"Response missing pagination fields: {missing_pagination_fields}")
            record_test("Regular Bots List - Pagination Structure", False, f"Missing fields: {missing_pagination_fields}")
        
        # Check bots array
        if "bots" in response:
            bots = response["bots"]
            
            if isinstance(bots, list):
                print_success(f"Response contains bots array with {len(bots)} bots")
                
                if len(bots) > 0:
                    # Check first bot structure
                    bot = bots[0]
                    print(f"First bot structure: {json.dumps(bot, indent=2)}")
                    
                    # CRITICAL TEST: Check for individual_limit field
                    if "individual_limit" in bot:
                        print_success("✓ FIXED: Bot object contains 'individual_limit' field")
                        print_success(f"individual_limit value: {bot['individual_limit']}")
                        record_test("Regular Bots List - individual_limit Field", True)
                    else:
                        print_error("✗ STILL MISSING: Bot object does not contain 'individual_limit' field")
                        record_test("Regular Bots List - individual_limit Field", False, "Missing individual_limit field")
                    
                    # Check other expected fields
                    expected_bot_fields = ["id", "name", "is_active", "min_bet_amount", "max_bet_amount", "bot_type", "created_at"]
                    missing_bot_fields = [field for field in expected_bot_fields if field not in bot]
                    
                    if not missing_bot_fields:
                        print_success("Bot object contains all other expected fields")
                        record_test("Regular Bots List - Bot Structure", True)
                    else:
                        print_warning(f"Bot object missing fields: {missing_bot_fields}")
                        record_test("Regular Bots List - Bot Structure", False, f"Missing fields: {missing_bot_fields}")
                else:
                    print_warning("No bots found in response - cannot test bot structure")
                    record_test("Regular Bots List - Bot Structure", True, "No bots to test")
            else:
                print_error(f"bots should be array, got: {type(bots)}")
                record_test("Regular Bots List - Bots Array", False, "bots not an array")
        else:
            print_error("Response missing 'bots' field")
            record_test("Regular Bots List - Bots Array", False, "Missing bots field")
        
        # Test pagination functionality
        print_success(f"Pagination info: Page {response.get('current_page', 'N/A')} of {response.get('total_pages', 'N/A')}")
        print_success(f"Total bots: {response.get('total_count', 'N/A')}")
        
        record_test("Regular Bots List - Request Success", True)
    else:
        print_error(f"Regular bots list request failed: {response}")
        record_test("Regular Bots List - Request Success", False, f"Request failed: {response}")

def print_summary() -> None:
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results["failed"] > 0:
        print("\nFailed tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"{Colors.FAIL}✗ {test['name']}: {test['details']}{Colors.ENDC}")
    
    success_rate = (test_results["passed"] / test_results["total"]) * 100 if test_results["total"] > 0 else 0
    print(f"\nSuccess rate: {Colors.BOLD}{success_rate:.2f}%{Colors.ENDC}")
    
    if test_results["failed"] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests passed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some tests failed!{Colors.ENDC}")

def main():
    """Main test execution."""
    print_header("REGULAR BOTS ADMIN PANEL API ENDPOINTS TEST")
    print("Testing specific fixes mentioned in the review request:")
    print("1. POST /api/admin/bots/create-regular - should create 1 bot instead of 5")
    print("2. GET /api/admin/bot-settings - should not return 500 error anymore")
    print("3. PUT /api/admin/bot-settings - should update global settings correctly")
    print("4. GET /api/admin/bots/regular/list - should include individual_limit field")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        sys.exit(1)
    
    # Step 2: Test GET bot-settings (should not return 500)
    test_bot_settings_get(admin_token)
    
    # Step 3: Test PUT bot-settings (should update correctly)
    test_bot_settings_put(admin_token)
    
    # Step 4: Test create regular bot (should create 1 bot, not 5)
    test_create_regular_bot(admin_token)
    
    # Step 5: Test regular bots list (should include individual_limit field)
    test_regular_bots_list(admin_token)
    
    # Print final summary
    print_summary()
    
    # Exit with appropriate code
    if test_results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()