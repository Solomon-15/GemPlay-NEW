#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://a78c0fab-d8eb-432e-b63e-77400f683f91.preview.emergentagent.com/api"
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!",
    "gender": "male"
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

def test_api_root() -> None:
    """Test the API root endpoint."""
    print_subheader("Testing API Root Endpoint")
    
    response, success = make_request("GET", "/")
    
    if success:
        expected = {"message": "GemPlay API is running!", "version": "1.0.0"}
        if response == expected:
            print_success("API root endpoint returned correct response")
            record_test("API Root Endpoint", True)
        else:
            print_error(f"API root endpoint returned unexpected response: {response}")
            record_test("API Root Endpoint", False, f"Expected {expected}, got {response}")
    else:
        record_test("API Root Endpoint", False, "Request failed")

def test_health_check() -> None:
    """Test the health check endpoint."""
    print_subheader("Testing Health Check Endpoint")
    
    response, success = make_request("GET", "/health")
    
    if success:
        if "status" in response and response["status"] == "healthy":
            print_success("Health check endpoint returned healthy status")
            record_test("Health Check Endpoint", True)
        else:
            print_error(f"Health check endpoint returned unexpected response: {response}")
            record_test("Health Check Endpoint", False, f"Expected status 'healthy', got {response}")
    else:
        record_test("Health Check Endpoint", False, "Request failed")

def test_user_registration() -> None:
    """Test user registration."""
    print_subheader("Testing User Registration")
    
    # Generate a random email to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"test_{random_suffix}@example.com"
    test_username = f"testuser_{random_suffix}"
    
    user_data = {
        "username": test_username,
        "email": test_email,
        "password": TEST_USER["password"],
        "gender": TEST_USER["gender"]
    }
    
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if success:
        if "message" in response and "user_id" in response and "verification_token" in response:
            print_success(f"User registered successfully with ID: {response['user_id']}")
            print_success(f"Verification token: {response['verification_token']}")
            record_test("User Registration", True)
            return response["verification_token"], test_email, test_username
        else:
            print_error(f"User registration response missing expected fields: {response}")
            record_test("User Registration", False, "Response missing expected fields")
    else:
        record_test("User Registration", False, "Request failed")
    
    return None, test_email, test_username

def test_duplicate_registration(email: str, username: str) -> None:
    """Test registering with a duplicate email."""
    print_subheader("Testing Duplicate Registration")
    
    # Try to register with the same email
    user_data = {
        "username": username + "_new",
        "email": email,
        "password": TEST_USER["password"],
        "gender": TEST_USER["gender"]
    }
    
    response, success = make_request("POST", "/auth/register", data=user_data, expected_status=400)
    
    if success:
        print_success("Server correctly rejected duplicate email registration")
        record_test("Duplicate Email Registration", True)
    else:
        if "detail" in response and "Email already registered" in response["detail"]:
            print_success("Server correctly rejected duplicate email registration")
            record_test("Duplicate Email Registration", True)
        else:
            print_error("Server did not properly handle duplicate email registration")
            record_test("Duplicate Email Registration", False, "Unexpected response")
    
    # Try to register with the same username
    user_data = {
        "username": username,
        "email": email + ".new",
        "password": TEST_USER["password"],
        "gender": TEST_USER["gender"]
    }
    
    response, success = make_request("POST", "/auth/register", data=user_data, expected_status=400)
    
    if success:
        print_success("Server correctly rejected duplicate username registration")
        record_test("Duplicate Username Registration", True)
    else:
        if "detail" in response and "Username already taken" in response["detail"]:
            print_success("Server correctly rejected duplicate username registration")
            record_test("Duplicate Username Registration", True)
        else:
            print_error("Server did not properly handle duplicate username registration")
            record_test("Duplicate Username Registration", False, "Unexpected response")

def test_email_verification(token: str) -> None:
    """Test email verification."""
    print_subheader("Testing Email Verification")
    
    if not token:
        print_error("No verification token available")
        record_test("Email Verification", False, "No token available")
        return
    
    response, success = make_request("POST", "/auth/verify-email", data={"token": token})
    
    if success:
        if "message" in response and "verified" in response["message"].lower():
            print_success("Email verified successfully")
            record_test("Email Verification", True)
        else:
            print_error(f"Email verification response unexpected: {response}")
            record_test("Email Verification", False, f"Unexpected response: {response}")
    else:
        record_test("Email Verification", False, "Request failed")

def test_login(email: str, password: str, expected_success: bool = True) -> Optional[str]:
    """Test user login."""
    print_subheader(f"Testing User Login {'(Expected Success)' if expected_success else '(Expected Failure)'}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    expected_status = 200 if expected_success else 401
    print(f"Attempting login with email: {email}, password: {password}")
    print(f"Expected status: {expected_status}")
    
    response, success = make_request("POST", "/auth/login", data=login_data, expected_status=expected_status)
    
    # For invalid login test
    if not expected_success:
        if response.get("detail") == "Incorrect email or password" and not success:
            print_success("Login correctly failed with invalid credentials")
            record_test("Invalid Login Attempt", True)
            return None
    
    # For valid login test
    if expected_success and success:
        if "access_token" in response and "user" in response:
            print_success(f"User logged in successfully")
            print_success(f"User details: {response['user']['username']} ({response['user']['email']})")
            print_success(f"Balance: ${response['user']['virtual_balance']}")
            record_test("User Login", True)
            return response["access_token"]
        else:
            print_error(f"Login response missing expected fields: {response}")
            record_test("User Login", False, "Response missing expected fields")
            return None
    
    if expected_success and not success:
        record_test("User Login", False, f"Login failed: {response}")
        return None
    
    # This should not happen
    print_error("Unexpected test result - please check test logic")
    record_test("Test Logic Error", False, "Unexpected test result")
    return None

def test_get_current_user(token: str) -> None:
    """Test getting current user info."""
    print_subheader("Testing Get Current User Info")
    
    if not token:
        print_error("No auth token available")
        record_test("Get Current User", False, "No token available")
        return
    
    response, success = make_request("GET", "/auth/me", auth_token=token)
    
    if success:
        if "id" in response and "username" in response and "email" in response:
            print_success(f"Got user info: {response['username']} ({response['email']})")
            print_success(f"Balance: ${response['virtual_balance']}")
            print_success(f"Gems: {response.get('gems', 'Not included in response')}")
            record_test("Get Current User", True)
        else:
            print_error(f"User info response missing expected fields: {response}")
            record_test("Get Current User", False, "Response missing expected fields")
    else:
        record_test("Get Current User", False, "Request failed")

def test_daily_bonus(token: str) -> None:
    """Test claiming daily bonus."""
    print_subheader("Testing Daily Bonus Claim")
    
    if not token:
        print_error("No auth token available")
        record_test("Daily Bonus Claim", False, "No token available")
        return
    
    response, success = make_request("POST", "/auth/daily-bonus", auth_token=token)
    
    if success:
        if "message" in response and "amount" in response and "new_balance" in response:
            print_success(f"Daily bonus claimed: ${response['amount']}")
            print_success(f"New balance: ${response['new_balance']}")
            record_test("Daily Bonus Claim", True)
        else:
            print_error(f"Daily bonus response missing expected fields: {response}")
            record_test("Daily Bonus Claim", False, "Response missing expected fields")
    else:
        record_test("Daily Bonus Claim", False, "Request failed")

def test_admin_users_exist() -> None:
    """Test that admin users exist by trying to login."""
    print_subheader("Testing Admin Users Existence")
    
    # Try to login as admin
    admin_token = test_login("admin@gemplay.com", "Admin123!", True)
    if admin_token:
        print_success("Admin user exists and login works")
        record_test("Admin User Exists", True)
    else:
        print_error("Admin user login failed")
        record_test("Admin User Exists", False, "Login failed")
    
    # Try to login as superadmin
    superadmin_token = test_login("superadmin@gemplay.com", "SuperAdmin123!", True)
    if superadmin_token:
        print_success("Super Admin user exists and login works")
        record_test("Super Admin User Exists", True)
    else:
        print_error("Super Admin user login failed")
        record_test("Super Admin User Exists", False, "Login failed")

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

def run_all_tests() -> None:
    """Run all tests in sequence."""
    print_header("GEMPLAY API TESTING")
    
    # Test basic endpoints
    test_api_root()
    test_health_check()
    
    # Test authentication flow
    verification_token, test_email, test_username = test_user_registration()
    test_duplicate_registration(test_email, test_username)
    test_email_verification(verification_token)
    
    # Test login with wrong password
    test_login(test_email, "WrongPassword123!", False)
    
    # Test login with correct password
    auth_token = test_login(test_email, TEST_USER["password"])
    
    # Test user info and daily bonus
    if auth_token:
        test_get_current_user(auth_token)
        test_daily_bonus(auth_token)
    
    # Test admin users
    test_admin_users_exist()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_all_tests()