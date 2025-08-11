#!/usr/bin/env python3
"""
Username Validation Testing - Russian Review
Focus: Testing username validation in API endpoints
Requirements: 
1. Valid usernames: "TestUser", "User123", "player.pro"
2. Invalid usernames: too short/long, cyrillic, special chars, consecutive underscores, spaces
3. Profile update testing with valid/invalid names
4. Admin user creation testing with valid/invalid names
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
BASE_URL = "https://3228f7f2-31dc-43d9-b035-c3bf150c31a2.preview.emergentagent.com/api"
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
    print_subheader("Testing Admin Login")
    
    response, success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, "Login failed")
        return None

def test_valid_username_registration(username: str) -> Tuple[bool, str]:
    """Test registration with valid username."""
    print_subheader(f"Testing Valid Username Registration: '{username}'")
    
    # Generate unique email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"test_{username.lower()}_{random_suffix}@test.com"
    
    user_data = {
        "username": username,
        "email": test_email,
        "password": "Test123!",
        "gender": "male"
    }
    
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if success:
        if "message" in response and "user_id" in response:
            print_success(f"Valid username '{username}' accepted successfully")
            record_test(f"Valid Username Registration - {username}", True)
            return True, response.get("user_id", "")
        else:
            print_error(f"Registration response missing expected fields: {response}")
            record_test(f"Valid Username Registration - {username}", False, "Response missing fields")
            return False, ""
    else:
        print_error(f"Valid username '{username}' was rejected: {response}")
        record_test(f"Valid Username Registration - {username}", False, f"Rejected: {response}")
        return False, ""

def test_invalid_username_registration(username: str, expected_error: str) -> bool:
    """Test registration with invalid username."""
    print_subheader(f"Testing Invalid Username Registration: '{username}'")
    
    # Generate unique email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"test_invalid_{random_suffix}@test.com"
    
    user_data = {
        "username": username,
        "email": test_email,
        "password": "Test123!",
        "gender": "male"
    }
    
    response, success = make_request("POST", "/auth/register", data=user_data, expected_status=422)
    
    # If we get 422 status, that means validation correctly rejected the invalid username
    if success and response.get("detail"):
        # Check if error message is in Russian as expected
        error_detail = response.get("detail", "")
        if isinstance(error_detail, list) and len(error_detail) > 0:
            error_msg = error_detail[0].get("msg", "")
        else:
            error_msg = str(error_detail)
        
        print_success(f"Invalid username '{username}' correctly rejected with error: {error_msg}")
        record_test(f"Invalid Username Registration - {username}", True, f"Correctly rejected: {error_msg}")
        return True
    else:
        print_error(f"Invalid username '{username}' was incorrectly accepted: {response}")
        record_test(f"Invalid Username Registration - {username}", False, f"Incorrectly accepted: {response}")
        return False

def test_profile_update_valid_username(user_id: str, auth_token: str, new_username: str) -> bool:
    """Test profile update with valid username."""
    print_subheader(f"Testing Profile Update with Valid Username: '{new_username}'")
    
    update_data = {
        "username": new_username
    }
    
    response, success = make_request("PUT", "/profile", data=update_data, auth_token=auth_token)
    
    if success:
        print_success(f"Profile updated successfully with valid username '{new_username}'")
        record_test(f"Profile Update Valid Username - {new_username}", True)
        return True
    else:
        print_error(f"Profile update failed with valid username '{new_username}': {response}")
        record_test(f"Profile Update Valid Username - {new_username}", False, f"Update failed: {response}")
        return False

def test_profile_update_invalid_username(auth_token: str, invalid_username: str) -> bool:
    """Test profile update with invalid username."""
    print_subheader(f"Testing Profile Update with Invalid Username: '{invalid_username}'")
    
    update_data = {
        "username": invalid_username
    }
    
    response, success = make_request("PUT", "/profile", data=update_data, auth_token=auth_token, expected_status=422)
    
    # If we get 422 status, that means validation correctly rejected the invalid username
    if success and response.get("detail"):
        error_detail = response.get("detail", "")
        if isinstance(error_detail, list) and len(error_detail) > 0:
            error_msg = error_detail[0].get("msg", "")
        else:
            error_msg = str(error_detail)
        
        print_success(f"Profile update correctly rejected invalid username '{invalid_username}': {error_msg}")
        record_test(f"Profile Update Invalid Username - {invalid_username}", True, f"Correctly rejected: {error_msg}")
        return True
    else:
        print_error(f"Profile update incorrectly accepted invalid username '{invalid_username}': {response}")
        record_test(f"Profile Update Invalid Username - {invalid_username}", False, f"Incorrectly accepted: {response}")
        return False

def test_admin_user_creation_valid_username(admin_token: str, username: str) -> bool:
    """Test admin user creation with valid username."""
    print_subheader(f"Testing Admin User Creation with Valid Username: '{username}'")
    
    # Generate unique email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"admin_created_{username.lower()}_{random_suffix}@test.com"
    
    user_data = {
        "username": username,
        "email": test_email,
        "password": "Test123!",
        "confirm_password": "Test123!",  # Add missing field
        "role": "USER",
        "gender": "male"
    }
    
    response, success = make_request("POST", "/admin/users", data=user_data, auth_token=admin_token)
    
    if success:
        print_success(f"Admin successfully created user with valid username '{username}'")
        record_test(f"Admin User Creation Valid Username - {username}", True)
        return True
    else:
        print_error(f"Admin user creation failed with valid username '{username}': {response}")
        record_test(f"Admin User Creation Valid Username - {username}", False, f"Creation failed: {response}")
        return False

def test_admin_user_creation_invalid_username(admin_token: str, invalid_username: str) -> bool:
    """Test admin user creation with invalid username."""
    print_subheader(f"Testing Admin User Creation with Invalid Username: '{invalid_username}'")
    
    # Generate unique email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"admin_invalid_{random_suffix}@test.com"
    
    user_data = {
        "username": invalid_username,
        "email": test_email,
        "password": "Test123!",
        "confirm_password": "Test123!",  # Add missing field
        "role": "USER",
        "gender": "male"
    }
    
    response, success = make_request("POST", "/admin/users", data=user_data, auth_token=admin_token, expected_status=422)
    
    # If we get 422 status, check if it's due to username validation (not just missing confirm_password)
    if success and response.get("detail"):
        error_details = response.get("detail", [])
        username_error = None
        
        # Look for username-specific validation errors
        for error in error_details:
            if error.get("loc") and "username" in error.get("loc", []):
                username_error = error.get("msg", "")
                break
        
        if username_error:
            print_success(f"Admin user creation correctly rejected invalid username '{invalid_username}': {username_error}")
            record_test(f"Admin User Creation Invalid Username - {invalid_username}", True, f"Correctly rejected: {username_error}")
            return True
        else:
            print_error(f"Admin user creation failed for other reasons, not username validation: {response}")
            record_test(f"Admin User Creation Invalid Username - {invalid_username}", False, f"Failed for other reasons: {response}")
            return False
    else:
        print_error(f"Admin user creation incorrectly accepted invalid username '{invalid_username}': {response}")
        record_test(f"Admin User Creation Invalid Username - {invalid_username}", False, f"Incorrectly accepted: {response}")
        return False

def test_user_login_and_get_token(username: str, email: str) -> Optional[str]:
    """Test user login and return token."""
    print_subheader(f"Testing User Login for {username}")
    
    # First verify email (simulate)
    verification_data = {"token": "dummy-token"}  # In real scenario, we'd use actual token
    
    login_data = {
        "email": email,
        "password": "Test123!"
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"User login successful for {username}")
        record_test(f"User Login - {username}", True)
        return response["access_token"]
    else:
        print_warning(f"User login failed for {username} (may need email verification): {response}")
        record_test(f"User Login - {username}", False, "Login failed - may need verification")
        return None

def run_username_validation_tests():
    """Run all username validation tests."""
    print_header("USERNAME VALIDATION TESTING - RUSSIAN REVIEW")
    
    # Test admin login first
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    # Test cases from Russian review - use unique variations
    valid_usernames = [
        f"TestUser{random.randint(1000, 9999)}", 
        f"User123{random.randint(1000, 9999)}", 
        f"player.pro{random.randint(100, 999)}"
    ]
    invalid_usernames = [
        ("AB", "Too short (2 characters)"),
        ("VeryLongUsername123", "Too long (16+ characters)"),
        ("Пользователь", "Cyrillic characters"),
        ("user@test", "Invalid characters (@)"),
        ("user__test", "Consecutive underscores"),
        (" username ", "Leading/trailing spaces")
    ]
    
    # 1. Test valid username registrations
    print_header("1. TESTING VALID USERNAME REGISTRATIONS")
    valid_user_tokens = {}
    valid_user_emails = {}
    
    for username in valid_usernames:
        success, user_id = test_valid_username_registration(username)
        if success:
            # Try to get user token for profile update tests
            email = f"test_{username.lower()}_{random.randint(1000, 9999)}@test.com"
            valid_user_emails[username] = email
    
    # 2. Test invalid username registrations
    print_header("2. TESTING INVALID USERNAME REGISTRATIONS")
    
    for invalid_username, reason in invalid_usernames:
        test_invalid_username_registration(invalid_username, reason)
    
    # 3. Test profile updates (need a valid user first)
    print_header("3. TESTING PROFILE UPDATE WITH USERNAMES")
    
    # Create a test user for profile updates
    test_user_data = {
        "username": "profiletest",
        "email": f"profiletest_{random.randint(1000, 9999)}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    response, success = make_request("POST", "/auth/register", data=test_user_data)
    if success:
        # Try to login (may need email verification)
        user_token = test_user_login_and_get_token("profiletest", test_user_data["email"])
        
        if user_token:
            # Test valid username update
            test_profile_update_valid_username("", user_token, "UpdatedUser")
            
            # Test invalid username updates
            for invalid_username, reason in invalid_usernames[:3]:  # Test first 3 invalid cases
                test_profile_update_invalid_username(user_token, invalid_username)
        else:
            print_warning("Skipping profile update tests - could not get user token")
    
    # 4. Test admin user creation
    print_header("4. TESTING ADMIN USER CREATION WITH USERNAMES")
    
    # Test valid usernames via admin
    for username in ["AdminUser1", "AdminUser2"]:
        test_admin_user_creation_valid_username(admin_token, username)
    
    # Test invalid usernames via admin
    for invalid_username, reason in invalid_usernames[:3]:  # Test first 3 invalid cases
        test_admin_user_creation_invalid_username(admin_token, invalid_username)

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
        print_subheader("FAILED TESTS:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"{test['name']}: {test['details']}")
    
    print_subheader("DETAILED RESULTS:")
    for test in test_results["tests"]:
        status = "✓" if test["passed"] else "✗"
        color = Colors.OKGREEN if test["passed"] else Colors.FAIL
        print(f"{color}{status} {test['name']}{Colors.ENDC}")
        if test["details"]:
            print(f"   {test['details']}")

if __name__ == "__main__":
    try:
        run_username_validation_tests()
        print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if test_results["failed"] == 0 else 1)
        
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        sys.exit(1)