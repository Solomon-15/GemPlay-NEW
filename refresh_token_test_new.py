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
BASE_URL = "https://39671358-620a-4bc2-9002-b6bfa47a1383.preview.emergentagent.com/api"
TEST_USER = {
    "username": "refresh_test_user",
    "email": "refresh_test@test.com",
    "password": "Test123!",
    "gender": "male"
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

def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: Optional[int] = None,
    auth_token: Optional[str] = None
) -> Tuple[Dict[str, Any], bool, int]:
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
    
    success = True
    if expected_status is not None:
        success = response.status_code == expected_status
        if not success:
            print_error(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success, response.status_code

def test_refresh_token_functionality():
    """Test refresh token functionality."""
    print_header("TESTING REFRESH TOKEN FUNCTIONALITY")
    
    # Generate a unique username and email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    username = f"{TEST_USER['username']}_{random_suffix}"
    email = f"refresh_test+{random_suffix}@test.com"
    
    # Step 1: Register a new user
    print_subheader(f"1. Registering a new user: {username}")
    register_data = {
        "username": username,
        "email": email,
        "password": TEST_USER["password"],
        "gender": TEST_USER["gender"]
    }
    
    register_response, register_success, register_status = make_request(
        "POST", 
        "/auth/register", 
        data=register_data,
        expected_status=200
    )
    
    if not register_success:
        print_error("Failed to register user")
        return
    
    verification_token = register_response.get("verification_token")
    if not verification_token:
        print_error("No verification token in response")
        return
    
    print_success(f"User registered successfully with verification token: {verification_token}")
    
    # Step 2: Verify email
    print_subheader(f"2. Verifying email for: {username}")
    verify_data = {
        "token": verification_token
    }
    
    verify_response, verify_success, verify_status = make_request(
        "POST", 
        "/auth/verify-email", 
        data=verify_data,
        expected_status=200
    )
    
    if not verify_success:
        print_error("Failed to verify email")
        return
    
    print_success("Email verified successfully")
    
    # Step 3: Login and get refresh token
    print_subheader(f"3. Logging in with: {email}")
    login_data = {
        "email": email,
        "password": TEST_USER["password"]
    }
    
    login_response, login_success, login_status = make_request(
        "POST", 
        "/auth/login", 
        data=login_data,
        expected_status=200
    )
    
    if not login_success:
        print_error("Failed to login")
        return
    
    access_token = login_response.get("access_token")
    refresh_token = login_response.get("refresh_token")
    
    if not access_token:
        print_error("No access token in login response")
        return
    
    if not refresh_token:
        print_error("No refresh token in login response")
        return
    
    print_success(f"Login successful")
    print_success(f"Access token: {access_token[:20]}...")
    print_success(f"Refresh token: {refresh_token[:20]}...")
    
    # Step 4: Use refresh token to get a new access token
    print_subheader(f"4. Using refresh token to get a new access token")
    
    refresh_response, refresh_success, refresh_status = make_request(
        "POST", 
        f"/auth/refresh?refresh_token={refresh_token}", 
        expected_status=200
    )
    
    if not refresh_success:
        print_error("Failed to refresh token")
        return
    
    new_access_token = refresh_response.get("access_token")
    new_refresh_token = refresh_response.get("refresh_token")
    
    if not new_access_token:
        print_error("No new access token in refresh response")
        return
    
    if not new_refresh_token:
        print_error("No new refresh token in refresh response")
        return
    
    print_success(f"Token refresh successful")
    print_success(f"New access token: {new_access_token[:20]}...")
    print_success(f"New refresh token: {new_refresh_token[:20]}...")
    
    # Step 5: Try to use the old refresh token (should fail)
    print_subheader(f"5. Trying to use the old refresh token (should fail)")
    
    old_token_response, old_token_success, old_token_status = make_request(
        "POST", 
        f"/auth/refresh?refresh_token={refresh_token}"
    )
    
    if old_token_status == 401 and "detail" in old_token_response and "Invalid or expired refresh token" in old_token_response["detail"]:
        print_success("Old refresh token correctly rejected with 401 status")
    else:
        print_error(f"Old refresh token not correctly rejected. Status: {old_token_status}, Response: {old_token_response}")
        return
    
    # Step 6: Try to use an invalid refresh token
    print_subheader(f"6. Trying to use an invalid refresh token (should fail)")
    
    invalid_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    invalid_response, invalid_success, invalid_status = make_request(
        "POST", 
        f"/auth/refresh?refresh_token={invalid_token}"
    )
    
    if invalid_status == 401 and "detail" in invalid_response and "Invalid or expired refresh token" in invalid_response["detail"]:
        print_success("Invalid refresh token correctly rejected with 401 status")
    else:
        print_error(f"Invalid refresh token not correctly rejected. Status: {invalid_status}, Response: {invalid_response}")
        return
    
    print_header("REFRESH TOKEN TESTS COMPLETED SUCCESSFULLY")
    print_success("✅ Login returns both access_token and refresh_token")
    print_success("✅ Refresh endpoint returns new access_token and refresh_token")
    print_success("✅ Old refresh tokens are deactivated when new ones are created")
    print_success("✅ Invalid refresh tokens are properly rejected")

if __name__ == "__main__":
    test_refresh_token_functionality()