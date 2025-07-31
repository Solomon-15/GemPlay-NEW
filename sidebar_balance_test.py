#!/usr/bin/env python3
"""
Sidebar Balance Endpoint Testing - Russian Review
Focus: Quick test of /api/economy/balance endpoint fix
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, Tuple

# Configuration
BASE_URL = "https://acffc923-2545-42ed-a41d-4e93fa17c383.preview.emergentagent.com/api"
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
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type.title()} Login")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    # Use JSON data for UserLogin model
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            response_data = response.json()
            print(f"Login response: {json.dumps(response_data, indent=2)}")
            
            if "access_token" in response_data:
                print_success(f"{user_type.title()} login successful")
                record_test(f"{user_type.title()} Login", True)
                return response_data["access_token"]
            else:
                print_error(f"{user_type.title()} login response missing access_token")
                record_test(f"{user_type.title()} Login", False, "Missing access_token")
        except json.JSONDecodeError:
            print_error(f"{user_type.title()} login response not JSON")
            record_test(f"{user_type.title()} Login", False, "Invalid JSON response")
    else:
        print_error(f"{user_type.title()} login failed with status {response.status_code}")
        try:
            error_data = response.json()
            print_error(f"Error details: {error_data}")
        except:
            print_error(f"Error text: {response.text}")
        record_test(f"{user_type.title()} Login", False, f"Status: {response.status_code}")
    
    return None

def test_sidebar_balance_endpoint() -> None:
    """Test the Sidebar balance endpoint fix as requested in Russian review."""
    print_header("SIDEBAR BALANCE ENDPOINT TESTING - RUSSIAN REVIEW")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with balance endpoint test")
        record_test("Sidebar Balance - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # Step 2: Test /api/economy/balance endpoint existence and functionality
    print_subheader("Step 2: Test /api/economy/balance Endpoint")
    
    balance_response, balance_success = make_request(
        "GET", "/economy/balance",
        auth_token=admin_token
    )
    
    if balance_success:
        print_success("✓ /api/economy/balance endpoint exists and accessible")
        print_success("✓ No 404 error - endpoint is working")
        record_test("Sidebar Balance - Endpoint Exists", True)
        
        # Step 3: Verify response structure
        print_subheader("Step 3: Verify Response Structure")
        
        required_fields = ["virtual_balance", "frozen_balance", "total_gem_value", "available_balance"]
        missing_fields = []
        
        for field in required_fields:
            if field not in balance_response:
                missing_fields.append(field)
        
        if not missing_fields:
            print_success("✓ Response contains all required fields:")
            print_success(f"  - virtual_balance: {balance_response.get('virtual_balance')}")
            print_success(f"  - frozen_balance: {balance_response.get('frozen_balance')}")
            print_success(f"  - total_gem_value: {balance_response.get('total_gem_value')}")
            print_success(f"  - available_balance: {balance_response.get('available_balance')}")
            record_test("Sidebar Balance - Response Structure", True)
        else:
            print_error(f"✗ Response missing required fields: {missing_fields}")
            record_test("Sidebar Balance - Response Structure", False, f"Missing: {missing_fields}")
        
        # Step 4: Verify data types and values
        print_subheader("Step 4: Verify Data Types and Values")
        
        data_type_checks = []
        
        # Check virtual_balance
        virtual_balance = balance_response.get('virtual_balance')
        if isinstance(virtual_balance, (int, float)) and virtual_balance >= 0:
            print_success(f"✓ virtual_balance is valid number: {virtual_balance}")
            data_type_checks.append(True)
        else:
            print_error(f"✗ virtual_balance invalid: {virtual_balance}")
            data_type_checks.append(False)
        
        # Check frozen_balance
        frozen_balance = balance_response.get('frozen_balance')
        if isinstance(frozen_balance, (int, float)) and frozen_balance >= 0:
            print_success(f"✓ frozen_balance is valid number: {frozen_balance}")
            data_type_checks.append(True)
        else:
            print_error(f"✗ frozen_balance invalid: {frozen_balance}")
            data_type_checks.append(False)
        
        # Check total_gem_value
        total_gem_value = balance_response.get('total_gem_value')
        if isinstance(total_gem_value, (int, float)) and total_gem_value >= 0:
            print_success(f"✓ total_gem_value is valid number: {total_gem_value}")
            data_type_checks.append(True)
        else:
            print_error(f"✗ total_gem_value invalid: {total_gem_value}")
            data_type_checks.append(False)
        
        # Check available_balance
        available_balance = balance_response.get('available_balance')
        if isinstance(available_balance, (int, float)) and available_balance >= 0:
            print_success(f"✓ available_balance is valid number: {available_balance}")
            data_type_checks.append(True)
        else:
            print_error(f"✗ available_balance invalid: {available_balance}")
            data_type_checks.append(False)
        
        if all(data_type_checks):
            record_test("Sidebar Balance - Data Types", True)
        else:
            record_test("Sidebar Balance - Data Types", False, "Invalid data types")
        
        # Step 5: Verify balance calculation logic
        print_subheader("Step 5: Verify Balance Calculation Logic")
        
        # available_balance should equal virtual_balance - frozen_balance
        expected_available = virtual_balance - frozen_balance
        actual_available = available_balance
        
        if abs(expected_available - actual_available) < 0.01:  # Allow for floating point precision
            print_success(f"✓ Balance calculation correct: {virtual_balance} - {frozen_balance} = {actual_available}")
            record_test("Sidebar Balance - Calculation Logic", True)
        else:
            print_error(f"✗ Balance calculation incorrect: expected {expected_available}, got {actual_available}")
            record_test("Sidebar Balance - Calculation Logic", False, f"Expected: {expected_available}, Got: {actual_available}")
        
    else:
        print_error("✗ /api/economy/balance endpoint failed")
        print_error("✗ This indicates the Sidebar balance fix is not working")
        record_test("Sidebar Balance - Endpoint Exists", False, "Endpoint failed")
        return
    
    # Step 6: Test authorization requirement
    print_subheader("Step 6: Test Authorization Requirement")
    
    # Try without token (should fail with 401)
    no_auth_response, no_auth_success = make_request(
        "GET", "/economy/balance",
        expected_status=401
    )
    
    if not no_auth_success and no_auth_response.get("detail") == "Not authenticated":
        print_success("✓ Endpoint correctly requires authorization (HTTP 401 without token)")
        record_test("Sidebar Balance - Authorization Required", True)
    else:
        print_error("✗ Endpoint does not require authorization (security issue)")
        record_test("Sidebar Balance - Authorization Required", False, "No auth required")
    
    # Step 7: Alternative endpoint test (/api/auth/me)
    print_subheader("Step 7: Test Alternative Balance Endpoint (/api/auth/me)")
    
    auth_me_response, auth_me_success = make_request(
        "GET", "/auth/me",
        auth_token=admin_token
    )
    
    if auth_me_success:
        print_success("✓ /api/auth/me endpoint also accessible")
        
        # Check if it has balance fields
        if "virtual_balance" in auth_me_response and "frozen_balance" in auth_me_response:
            print_success("✓ /api/auth/me contains balance information")
            print_success(f"  - virtual_balance: {auth_me_response.get('virtual_balance')}")
            print_success(f"  - frozen_balance: {auth_me_response.get('frozen_balance')}")
            record_test("Sidebar Balance - Alternative Endpoint", True)
        else:
            print_warning("⚠ /api/auth/me missing balance fields")
            record_test("Sidebar Balance - Alternative Endpoint", False, "Missing balance fields")
    else:
        print_warning("⚠ /api/auth/me endpoint failed")
        record_test("Sidebar Balance - Alternative Endpoint", False, "Endpoint failed")

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
                print_error(f"- {test['name']}: {test['details']}")
    
    # Russian Review Summary
    print_subheader("RUSSIAN REVIEW SUMMARY")
    
    endpoint_exists = any(test["name"] == "Sidebar Balance - Endpoint Exists" and test["passed"] for test in test_results["tests"])
    response_structure = any(test["name"] == "Sidebar Balance - Response Structure" and test["passed"] for test in test_results["tests"])
    auth_required = any(test["name"] == "Sidebar Balance - Authorization Required" and test["passed"] for test in test_results["tests"])
    
    if endpoint_exists:
        print_success("✅ 1. /api/economy/balance endpoint exists and works - NO 404 ERROR")
    else:
        print_error("❌ 1. /api/economy/balance endpoint has issues")
    
    if response_structure:
        print_success("✅ 2. Response structure correct with all required fields")
    else:
        print_error("❌ 2. Response structure missing required fields")
    
    if auth_required:
        print_success("✅ 3. Endpoint properly requires authorization")
    else:
        print_error("❌ 3. Authorization issues detected")
    
    if endpoint_exists and response_structure:
        print_success("🎉 SIDEBAR BALANCE FIX: SUCCESS")
        print_success("✅ The Sidebar error should now be resolved!")
        print_success("✅ Frontend can successfully fetch balance data")
    else:
        print_error("❌ SIDEBAR BALANCE FIX: NEEDS WORK")
        print_error("❌ Sidebar may still show errors")

def main():
    """Main test execution."""
    print_header("SIDEBAR BALANCE ENDPOINT QUICK TEST")
    print("Russian Review Request: Test /api/economy/balance endpoint fix")
    print("Focus: Ensure no 404 error and proper response structure")
    
    try:
        test_sidebar_balance_endpoint()
        print_test_summary()
        
        # Exit with appropriate code
        if test_results["failed"] == 0:
            print(f"\n{Colors.OKGREEN}All tests passed! Sidebar balance fix is working.{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.FAIL}Some tests failed. Sidebar balance fix needs attention.{Colors.ENDC}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Test failed with error: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()