#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib

# Configuration
BASE_URL = "https://741ed8e0-91a9-4add-9841-6f65748008a6.preview.emergentagent.com/api"
TEST_USER = {
    "username": "refresh_test_user",
    "email": "refresh_test@test.com",
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

def test_user_registration(user_data: Dict[str, str]) -> Tuple[Optional[str], str, str]:
    """Test user registration."""
    print_subheader(f"Testing User Registration for {user_data['username']}")
    
    # Generate a random email to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = user_data["email"].replace("@", f"+{random_suffix}@")
    test_username = f"{user_data['username']}_{random_suffix}"
    
    # Update user data with randomized values
    user_data = user_data.copy()
    user_data["email"] = test_email
    user_data["username"] = test_username
    
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if success:
        if "message" in response and "user_id" in response and "verification_token" in response:
            print_success(f"User registered successfully with ID: {response['user_id']}")
            print_success(f"Verification token: {response['verification_token']}")
            record_test(f"User Registration - {test_username}", True)
            return response["verification_token"], test_email, test_username
        else:
            print_error(f"User registration response missing expected fields: {response}")
            record_test(f"User Registration - {test_username}", False, "Response missing expected fields")
    else:
        record_test(f"User Registration - {test_username}", False, "Request failed")
    
    return None, test_email, test_username

def test_email_verification(token: str, username: str) -> None:
    """Test email verification."""
    print_subheader(f"Testing Email Verification for {username}")
    
    if not token:
        print_error("No verification token available")
        record_test(f"Email Verification - {username}", False, "No token available")
        return
    
    response, success = make_request("POST", "/auth/verify-email", data={"token": token})
    
    if success:
        if "message" in response and "verified" in response["message"].lower():
            print_success("Email verified successfully")
            record_test(f"Email Verification - {username}", True)
        else:
            print_error(f"Email verification response unexpected: {response}")
            record_test(f"Email Verification - {username}", False, f"Unexpected response: {response}")
    else:
        record_test(f"Email Verification - {username}", False, "Request failed")

def test_login_with_refresh_token(email: str, password: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """Test user login and verify refresh token is returned."""
    print_subheader(f"Testing Login with Refresh Token for {username}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success:
        if "access_token" in response and "refresh_token" in response and "user" in response:
            print_success(f"User logged in successfully")
            print_success(f"Access token received: {response['access_token'][:20]}...")
            print_success(f"Refresh token received: {response['refresh_token'][:20]}...")
            record_test(f"Login with Refresh Token - {username}", True)
            return response["access_token"], response["refresh_token"]
        elif "access_token" in response and "user" in response:
            print_error(f"Login successful but no refresh token in response")
            record_test(f"Login with Refresh Token - {username}", False, "No refresh token in response")
            return response["access_token"], None
        else:
            print_error(f"Login failed: {response}")
            record_test(f"Login with Refresh Token - {username}", False, f"Login failed: {response}")
            return None, None
    else:
        record_test(f"Login with Refresh Token - {username}", False, "Request failed")
        return None, None

def test_refresh_token_endpoint(refresh_token: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """Test refreshing access token using refresh token."""
    print_subheader(f"Testing Refresh Token Endpoint for {username}")
    
    if not refresh_token:
        print_error("No refresh token available")
        record_test(f"Refresh Token Endpoint - {username}", False, "No refresh token available")
        return None, None
    
    # Send refresh_token as a query parameter
    response, success = make_request("POST", f"/auth/refresh?refresh_token={refresh_token}")
    
    if success:
        if "access_token" in response and "refresh_token" in response and "user" in response:
            print_success(f"Token refreshed successfully")
            print_success(f"New access token received: {response['access_token'][:20]}...")
            print_success(f"New refresh token received: {response['refresh_token'][:20]}...")
            record_test(f"Refresh Token Endpoint - {username}", True)
            return response["access_token"], response["refresh_token"]
        elif "access_token" in response and "user" in response:
            print_error(f"Token refresh successful but no new refresh token in response")
            record_test(f"Refresh Token Endpoint - {username}", False, "No new refresh token in response")
            return response["access_token"], None
        else:
            print_error(f"Token refresh failed: {response}")
            record_test(f"Refresh Token Endpoint - {username}", False, f"Token refresh failed: {response}")
            return None, None
    else:
        record_test(f"Refresh Token Endpoint - {username}", False, "Request failed")
        return None, None

def test_invalid_refresh_token(username: str) -> None:
    """Test using an invalid refresh token."""
    print_subheader(f"Testing Invalid Refresh Token for {username}")
    
    # Generate a random invalid token
    invalid_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    response, success = make_request(
        "POST", 
        f"/auth/refresh?refresh_token={invalid_token}",
        expected_status=401
    )
    
    # This is actually a success case for our test - we expect a 401 error
    if not success and "detail" in response and "Invalid or expired refresh token" in response["detail"]:
        print_success("Invalid refresh token correctly rejected with 401 status")
        record_test(f"Invalid Refresh Token - {username}", True)
    else:
        print_error(f"Invalid refresh token not handled correctly: {response}")
        record_test(f"Invalid Refresh Token - {username}", False, f"Unexpected response: {response}")
    
    if not success and "detail" in response and "Invalid or expired refresh token" in response["detail"]:
        print_success("Invalid refresh token correctly rejected")
        record_test(f"Invalid Refresh Token - {username}", True)
    else:
        print_error(f"Invalid refresh token not correctly rejected: {response}")
        record_test(f"Invalid Refresh Token - {username}", False, f"Unexpected response: {response}")

def test_expired_refresh_token(username: str, refresh_token: str) -> None:
    """Test using an expired or deactivated refresh token."""
    print_subheader(f"Testing Expired/Deactivated Refresh Token for {username}")
    
    if not refresh_token:
        print_error("No refresh token available")
        record_test(f"Expired Refresh Token - {username}", False, "No refresh token available")
        return
    
    # First, get a new refresh token to deactivate the old one
    response, success = make_request("POST", f"/auth/refresh?refresh_token={refresh_token}")
    
    if not success:
        print_error(f"Failed to get new refresh token: {response}")
        record_test(f"Expired Refresh Token - {username}", False, "Failed to get new refresh token")
        return
    
    # Get the new refresh token
    new_refresh_token = response.get("refresh_token")
    if not new_refresh_token:
        print_error("No new refresh token in response")
        record_test(f"Expired Refresh Token - {username}", False, "No new refresh token in response")
        return
    
    print_success(f"Successfully obtained new refresh token: {new_refresh_token[:20]}...")
    
    # Now try to use the old refresh token, which should be deactivated
    old_token_response, old_token_success = make_request(
        "POST", 
        f"/auth/refresh?refresh_token={refresh_token}",
        expected_status=401
    )
    
    # This is actually a success case for our test - we expect a 401 error
    if not old_token_success and "detail" in old_token_response and "Invalid or expired refresh token" in old_token_response["detail"]:
        print_success("Old refresh token correctly rejected with 401 status")
        record_test(f"Expired Refresh Token - {username}", True)
    else:
        print_error(f"Old refresh token not handled correctly: {old_token_response}")
        record_test(f"Expired Refresh Token - {username}", False, f"Unexpected response: {old_token_response}")
    
    if not success and "detail" in response and "Invalid or expired refresh token" in response["detail"]:
        print_success("Deactivated refresh token correctly rejected")
        record_test(f"Expired Refresh Token - {username}", True)
    else:
        print_error(f"Deactivated refresh token not correctly rejected: {response}")
        record_test(f"Expired Refresh Token - {username}", False, f"Unexpected response: {response}")

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

def test_refresh_token_functionality() -> None:
    """Test refresh token functionality."""
    print_header("TESTING REFRESH TOKEN FUNCTIONALITY")
    
    # Register and verify test user
    token, email, username = test_user_registration(TEST_USER)
    test_email_verification(token, username)
    
    # Test 1: Login with refresh token
    access_token, refresh_token = test_login_with_refresh_token(email, TEST_USER["password"], username)
    
    if not access_token or not refresh_token:
        print_error("Failed to get tokens during login")
        return
    
    # Test 2: Refresh token endpoint
    new_access_token, new_refresh_token = test_refresh_token_endpoint(refresh_token, username)
    
    if not new_access_token or not new_refresh_token:
        print_error("Failed to refresh tokens")
        return
    
    # Test 3: Invalid refresh token
    test_invalid_refresh_token(username)
    
    # Test 4: Expired/deactivated refresh token
    test_expired_refresh_token(username, refresh_token)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    test_refresh_token_functionality()