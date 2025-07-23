#!/usr/bin/env python3
"""
Focused testing for bot-settings API endpoints as requested in the review.

Testing the following endpoints:
1. GET /api/admin/bot-settings - should work and return correct data
2. PUT /api/admin/bot-settings - should update global bot settings
3. POST /api/admin/bots/create-regular - should create only 1 bot
4. GET /api/admin/bots/regular/list - should include individual_limit field

Authentication: admin@gemplay.com / Admin123!
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://3f3f02b9-c79c-40e7-814a-6b1e36d42891.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test data for PUT request as specified in review
TEST_BOT_SETTINGS = {
    "globalMaxActiveBets": 60,
    "globalMaxHumanBots": 25,
    "paginationSize": 15,
    "autoActivateFromQueue": True,
    "priorityType": "order"
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
        print_success(f"User: {response.get('user', {}).get('username', 'N/A')} ({response.get('user', {}).get('email', 'N/A')})")
        print_success(f"Role: {response.get('user', {}).get('role', 'N/A')}")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_get_bot_settings(admin_token: str) -> Optional[Dict[str, Any]]:
    """Test GET /api/admin/bot-settings endpoint."""
    print_subheader("Testing GET /api/admin/bot-settings")
    
    response, success = make_request(
        "GET", 
        "/admin/bot-settings", 
        auth_token=admin_token
    )
    
    if success:
        print_success("GET /api/admin/bot-settings endpoint is working!")
        
        # Check if response has expected structure
        expected_fields = ["globalMaxActiveBets", "globalMaxHumanBots", "paginationSize", "autoActivateFromQueue", "priorityType"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if missing_fields:
            print_warning(f"Response missing some expected fields: {missing_fields}")
            record_test("GET bot-settings - Response Structure", False, f"Missing fields: {missing_fields}")
        else:
            print_success("Response has all expected fields")
            record_test("GET bot-settings - Response Structure", True)
        
        # Validate data types
        validation_errors = []
        if not isinstance(response.get("globalMaxActiveBets"), int):
            validation_errors.append("globalMaxActiveBets should be int")
        if not isinstance(response.get("globalMaxHumanBots"), int):
            validation_errors.append("globalMaxHumanBots should be int")
        if not isinstance(response.get("paginationSize"), int):
            validation_errors.append("paginationSize should be int")
        if not isinstance(response.get("autoActivateFromQueue"), bool):
            validation_errors.append("autoActivateFromQueue should be bool")
        if not isinstance(response.get("priorityType"), str):
            validation_errors.append("priorityType should be str")
        
        if validation_errors:
            print_error(f"Data type validation errors: {validation_errors}")
            record_test("GET bot-settings - Data Types", False, f"Validation errors: {validation_errors}")
        else:
            print_success("All data types are correct")
            record_test("GET bot-settings - Data Types", True)
        
        record_test("GET bot-settings - Main Functionality", True)
        return response
    else:
        print_error("GET /api/admin/bot-settings endpoint failed!")
        if "status_code" in response and response["status_code"] == 500:
            print_error("CONFIRMED: Getting 500 Internal Server Error as reported in previous issues")
        record_test("GET bot-settings - Main Functionality", False, f"Request failed: {response}")
        return None

def test_put_bot_settings(admin_token: str) -> bool:
    """Test PUT /api/admin/bot-settings endpoint."""
    print_subheader("Testing PUT /api/admin/bot-settings")
    
    print(f"Using test data: {json.dumps(TEST_BOT_SETTINGS, indent=2)}")
    
    response, success = make_request(
        "PUT", 
        "/admin/bot-settings", 
        data=TEST_BOT_SETTINGS,
        auth_token=admin_token
    )
    
    if success:
        print_success("PUT /api/admin/bot-settings endpoint is working!")
        
        # Check if response indicates success
        if response.get("message") or response.get("success"):
            print_success("Update operation reported as successful")
            record_test("PUT bot-settings - Success Response", True)
        else:
            print_warning(f"Update response unclear: {response}")
            record_test("PUT bot-settings - Success Response", False, "Unclear success indication")
        
        # Verify the update by getting settings again
        print("Verifying update by retrieving settings...")
        verification_response, verification_success = make_request(
            "GET", 
            "/admin/bot-settings", 
            auth_token=admin_token
        )
        
        if verification_success:
            # Check if the values were actually updated
            verification_errors = []
            for key, expected_value in TEST_BOT_SETTINGS.items():
                actual_value = verification_response.get(key)
                if actual_value != expected_value:
                    verification_errors.append(f"{key}: expected {expected_value}, got {actual_value}")
            
            if verification_errors:
                print_error(f"Settings were not updated correctly: {verification_errors}")
                record_test("PUT bot-settings - Verification", False, f"Update verification failed: {verification_errors}")
            else:
                print_success("All settings were updated correctly!")
                record_test("PUT bot-settings - Verification", True)
        else:
            print_error("Could not verify settings update")
            record_test("PUT bot-settings - Verification", False, "Could not retrieve settings for verification")
        
        record_test("PUT bot-settings - Main Functionality", True)
        return True
    else:
        print_error("PUT /api/admin/bot-settings endpoint failed!")
        if "status_code" in response and response["status_code"] == 500:
            print_error("CONFIRMED: Getting 500 Internal Server Error as reported in previous issues")
        record_test("PUT bot-settings - Main Functionality", False, f"Request failed: {response}")
        return False

def test_create_regular_bot(admin_token: str) -> Optional[str]:
    """Test POST /api/admin/bots/create-regular endpoint."""
    print_subheader("Testing POST /api/admin/bots/create-regular")
    
    # Test data for creating a regular bot
    bot_data = {
        "name": "Test Bot",
        "min_bet_amount": 5,
        "max_bet_amount": 50,
        "win_rate": 55.0,
        "cycle_games": 12
    }
    
    print(f"Creating bot with data: {json.dumps(bot_data, indent=2)}")
    
    response, success = make_request(
        "POST", 
        "/admin/bots/create-regular", 
        data=bot_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("POST /api/admin/bots/create-regular endpoint is working!")
        
        # Check if only 1 bot was created (as requested in review)
        if "created_bots" in response:
            created_bots = response["created_bots"]
            if isinstance(created_bots, list) and len(created_bots) == 1:
                print_success("✓ Exactly 1 bot was created as expected")
                record_test("Create Regular Bot - Count", True)
                bot_id = created_bots[0]
                print_success(f"Created bot ID: {bot_id}")
            else:
                print_error(f"✗ Expected 1 bot, but got {len(created_bots) if isinstance(created_bots, list) else 'non-list'}")
                record_test("Create Regular Bot - Count", False, f"Created {len(created_bots) if isinstance(created_bots, list) else 'non-list'} bots instead of 1")
                bot_id = created_bots[0] if isinstance(created_bots, list) and created_bots else None
        elif "id" in response:
            # Single bot response format
            print_success("✓ Single bot created successfully")
            record_test("Create Regular Bot - Count", True)
            bot_id = response["id"]
            print_success(f"Created bot ID: {bot_id}")
        else:
            print_error("✗ Response missing bot ID information")
            record_test("Create Regular Bot - Count", False, "Missing bot ID in response")
            bot_id = None
        
        # Check response structure
        if "message" in response or "created_bots" in response or "id" in response:
            print_success("Response has expected structure")
            record_test("Create Regular Bot - Response Structure", True)
        else:
            print_warning(f"Response structure unexpected: {response}")
            record_test("Create Regular Bot - Response Structure", False, "Unexpected response structure")
        
        record_test("Create Regular Bot - Main Functionality", True)
        return bot_id
    else:
        print_error("POST /api/admin/bots/create-regular endpoint failed!")
        record_test("Create Regular Bot - Main Functionality", False, f"Request failed: {response}")
        return None

def test_get_regular_bots_list(admin_token: str) -> bool:
    """Test GET /api/admin/bots/regular/list endpoint."""
    print_subheader("Testing GET /api/admin/bots/regular/list")
    
    response, success = make_request(
        "GET", 
        "/admin/bots/regular/list", 
        auth_token=admin_token
    )
    
    if success:
        print_success("GET /api/admin/bots/regular/list endpoint is working!")
        
        # Check if response has expected pagination structure
        expected_pagination_fields = ["total_count", "current_page", "total_pages", "items_per_page", "has_next", "has_prev"]
        missing_pagination_fields = [field for field in expected_pagination_fields if field not in response]
        
        if missing_pagination_fields:
            print_warning(f"Response missing pagination fields: {missing_pagination_fields}")
            record_test("Get Regular Bots - Pagination Structure", False, f"Missing fields: {missing_pagination_fields}")
        else:
            print_success("Response has all expected pagination fields")
            record_test("Get Regular Bots - Pagination Structure", True)
        
        # Check if response has bots array
        if "bots" in response:
            bots = response["bots"]
            print_success(f"Found {len(bots)} bots in response")
            
            # Check if bots have individual_limit field (as requested in review)
            if bots:
                individual_limit_missing = []
                individual_limit_found = []
                
                for i, bot in enumerate(bots):
                    if "individual_limit" in bot:
                        individual_limit_found.append(f"Bot {i}: {bot['individual_limit']}")
                    else:
                        individual_limit_missing.append(f"Bot {i}")
                
                if individual_limit_missing:
                    print_error(f"✗ Bots missing individual_limit field: {individual_limit_missing}")
                    record_test("Get Regular Bots - individual_limit Field", False, f"Missing in bots: {individual_limit_missing}")
                else:
                    print_success("✓ All bots have individual_limit field")
                    print_success(f"individual_limit values: {individual_limit_found}")
                    record_test("Get Regular Bots - individual_limit Field", True)
                
                # Check other expected bot fields
                expected_bot_fields = ["id", "name", "is_active", "bot_type"]
                for i, bot in enumerate(bots[:3]):  # Check first 3 bots
                    missing_bot_fields = [field for field in expected_bot_fields if field not in bot]
                    if missing_bot_fields:
                        print_warning(f"Bot {i} missing fields: {missing_bot_fields}")
                    else:
                        print_success(f"Bot {i} has all expected fields")
            else:
                print_warning("No bots found in response - cannot test individual_limit field")
                record_test("Get Regular Bots - individual_limit Field", True, "No bots to test")
            
            record_test("Get Regular Bots - Bots Array", True)
        else:
            print_error("Response missing 'bots' array")
            record_test("Get Regular Bots - Bots Array", False, "Missing bots array")
        
        record_test("Get Regular Bots - Main Functionality", True)
        return True
    else:
        print_error("GET /api/admin/bots/regular/list endpoint failed!")
        record_test("Get Regular Bots - Main Functionality", False, f"Request failed: {response}")
        return False

def print_summary() -> None:
    """Print a summary of all test results."""
    print_header("BOT-SETTINGS API ENDPOINTS TEST SUMMARY")
    
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
    
    # Summary of key findings
    print_header("KEY FINDINGS SUMMARY")
    
    # Check specific endpoints mentioned in review
    get_bot_settings_working = any(test["name"] == "GET bot-settings - Main Functionality" and test["passed"] for test in test_results["tests"])
    put_bot_settings_working = any(test["name"] == "PUT bot-settings - Main Functionality" and test["passed"] for test in test_results["tests"])
    create_bot_working = any(test["name"] == "Create Regular Bot - Main Functionality" and test["passed"] for test in test_results["tests"])
    create_bot_count_correct = any(test["name"] == "Create Regular Bot - Count" and test["passed"] for test in test_results["tests"])
    list_bots_working = any(test["name"] == "Get Regular Bots - Main Functionality" and test["passed"] for test in test_results["tests"])
    individual_limit_present = any(test["name"] == "Get Regular Bots - individual_limit Field" and test["passed"] for test in test_results["tests"])
    
    print(f"1. GET /api/admin/bot-settings: {'✅ WORKING' if get_bot_settings_working else '❌ FAILING'}")
    print(f"2. PUT /api/admin/bot-settings: {'✅ WORKING' if put_bot_settings_working else '❌ FAILING'}")
    print(f"3. POST /api/admin/bots/create-regular: {'✅ WORKING' if create_bot_working else '❌ FAILING'}")
    print(f"   - Creates only 1 bot: {'✅ YES' if create_bot_count_correct else '❌ NO'}")
    print(f"4. GET /api/admin/bots/regular/list: {'✅ WORKING' if list_bots_working else '❌ FAILING'}")
    print(f"   - Has individual_limit field: {'✅ YES' if individual_limit_present else '❌ NO'}")
    
    if test_results["failed"] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! Bot-settings endpoints are working correctly.{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️  SOME TESTS FAILED! Issues remain with bot-settings endpoints.{Colors.ENDC}")

def main():
    """Main test execution."""
    print_header("BOT-SETTINGS API ENDPOINTS TESTING")
    print("Testing the specific endpoints mentioned in the review request:")
    print("1. GET /api/admin/bot-settings")
    print("2. PUT /api/admin/bot-settings") 
    print("3. POST /api/admin/bots/create-regular")
    print("4. GET /api/admin/bots/regular/list")
    print(f"\nAuthentication: {ADMIN_USER['email']} / {ADMIN_USER['password']}")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        print_summary()
        sys.exit(1)
    
    # Step 2: Test GET bot-settings
    current_settings = test_get_bot_settings(admin_token)
    
    # Step 3: Test PUT bot-settings
    test_put_bot_settings(admin_token)
    
    # Step 4: Test create regular bot
    created_bot_id = test_create_regular_bot(admin_token)
    
    # Step 5: Test get regular bots list
    test_get_regular_bots_list(admin_token)
    
    # Final summary
    print_summary()
    
    # Exit with appropriate code
    if test_results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()