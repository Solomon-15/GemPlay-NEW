#!/usr/bin/env python3
import requests
import json
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://64cc6386-92a9-4393-a3b5-44a72c0e549b.preview.emergentagent.com/api"
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

def login(email: str, password: str) -> Optional[str]:
    """Login and return access token."""
    print_subheader(f"Logging in as {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Successfully logged in as {email}")
        return response["access_token"]
    else:
        print_error(f"Login failed: {response}")
        return None

def test_get_gem_definitions(token: str) -> bool:
    """Test GET /api/gems/definitions endpoint."""
    print_subheader("Testing GET /api/gems/definitions")
    
    response, success = make_request("GET", "/gems/definitions", auth_token=token)
    
    if success:
        if isinstance(response, list):
            if len(response) == 7:  # Expecting 7 gem types
                print_success(f"Successfully retrieved all 7 gem types")
                
                # Check if all required fields are present for each gem
                all_fields_present = True
                gem_types = []
                
                for gem in response:
                    gem_types.append(gem["type"])
                    required_fields = ["type", "name", "price", "color", "icon", "rarity"]
                    for field in required_fields:
                        if field not in gem:
                            print_error(f"Missing required field '{field}' in gem: {gem['type']}")
                            all_fields_present = False
                
                # Check if all expected gem types are present
                expected_types = ["Ruby", "Amber", "Topaz", "Emerald", "Aquamarine", "Sapphire", "Magic"]
                all_types_present = all(gem_type in gem_types for gem_type in expected_types)
                
                if not all_types_present:
                    print_error(f"Missing some gem types. Expected: {expected_types}, Got: {gem_types}")
                    record_test("GET /api/gems/definitions", False, "Missing some gem types")
                    return False
                
                if all_fields_present:
                    print_success("All required fields are present for each gem")
                    record_test("GET /api/gems/definitions", True)
                    return True
                else:
                    record_test("GET /api/gems/definitions", False, "Missing required fields")
                    return False
            else:
                print_error(f"Expected 7 gem types, got {len(response)}")
                record_test("GET /api/gems/definitions", False, f"Expected 7 gem types, got {len(response)}")
                return False
        else:
            print_error("Response is not a list")
            record_test("GET /api/gems/definitions", False, "Response is not a list")
            return False
    else:
        record_test("GET /api/gems/definitions", False, "Request failed")
        return False

def test_get_user_gems(token: str) -> bool:
    """Test GET /api/gems/inventory endpoint."""
    print_subheader("Testing GET /api/gems/inventory")
    
    response, success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Successfully retrieved user's gem inventory with {len(response)} gem types")
            
            # Check if all required fields are present for each gem
            all_fields_present = True
            for gem in response:
                required_fields = ["type", "name", "price", "color", "icon", "rarity", "quantity", "frozen_quantity"]
                for field in required_fields:
                    if field not in gem:
                        print_error(f"Missing required field '{field}' in gem: {gem['type']}")
                        all_fields_present = False
            
            if all_fields_present:
                print_success("All required fields are present for each gem in inventory")
                record_test("GET /api/gems/inventory", True)
                return True
            else:
                record_test("GET /api/gems/inventory", False, "Missing required fields")
                return False
        else:
            print_error("Response is not a list")
            record_test("GET /api/gems/inventory", False, "Response is not a list")
            return False
    else:
        record_test("GET /api/gems/inventory", False, "Request failed")
        return False

def test_get_economy_balance(token: str) -> bool:
    """Test GET /api/economy/balance endpoint."""
    print_subheader("Testing GET /api/economy/balance")
    
    response, success = make_request("GET", "/economy/balance", auth_token=token)
    
    if success:
        if isinstance(response, dict):
            required_fields = ["virtual_balance", "frozen_balance", "total_gem_value", 
                              "available_gem_value", "total_value", "daily_limit_used", 
                              "daily_limit_max"]
            
            all_fields_present = True
            for field in required_fields:
                if field not in response:
                    print_error(f"Missing required field '{field}' in balance response")
                    all_fields_present = False
            
            if all_fields_present:
                print_success("Successfully retrieved user's economy balance")
                print_success(f"Virtual Balance: ${response['virtual_balance']}")
                print_success(f"Frozen Balance: ${response['frozen_balance']}")
                print_success(f"Total Gem Value: ${response['total_gem_value']}")
                print_success(f"Available Gem Value: ${response['available_gem_value']}")
                print_success(f"Total Value: ${response['total_value']}")
                record_test("GET /api/economy/balance", True)
                return True
            else:
                record_test("GET /api/economy/balance", False, "Missing required fields")
                return False
        else:
            print_error("Response is not a dictionary")
            record_test("GET /api/economy/balance", False, "Response is not a dictionary")
            return False
    else:
        record_test("GET /api/economy/balance", False, "Request failed")
        return False

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

def run_gems_api_tests() -> None:
    """Run all gems API tests."""
    print_header("GEMPLAY GEMS API TESTING")
    
    # Login as admin
    token = login(ADMIN_USER["email"], ADMIN_USER["password"])
    
    if not token:
        print_error("Failed to login. Cannot proceed with tests.")
        return
    
    # Test GET /api/gems/definitions
    test_get_gem_definitions(token)
    
    # Test GET /api/gems/inventory
    test_get_user_gems(token)
    
    # Test GET /api/economy/balance
    test_get_economy_balance(token)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_gems_api_tests()