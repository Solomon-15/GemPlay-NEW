#!/usr/bin/env python3
import requests
import json
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://8ca9aa1c-7c08-4491-ac01-0705f6e772c8.preview.emergentagent.com/api"
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
    """Test admin login."""
    print_subheader("Testing POST /api/auth/login (Admin)")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response and "user" in response:
        print_success(f"Admin logged in successfully")
        print_success(f"Admin details: {response['user']['username']} ({response['user']['email']})")
        print_success(f"Admin role: {response['user']['role']}")
        record_test("POST /api/auth/login (Admin)", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("POST /api/auth/login (Admin)", False, f"Login failed: {response}")
        return None

def test_get_users(admin_token: str) -> List[Dict[str, Any]]:
    """Test getting users list."""
    print_subheader("Testing GET /api/admin/users")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/admin/users", False, "No admin token available")
        return []
    
    response, success = make_request("GET", "/admin/users", auth_token=admin_token)
    
    if success:
        if "users" in response and isinstance(response["users"], list):
            print_success(f"Got users list: {len(response['users'])} users")
            print_success(f"Total users: {response['total']}")
            record_test("GET /api/admin/users", True)
            return response["users"]
        else:
            print_error(f"Users list response missing expected fields: {response}")
            record_test("GET /api/admin/users", False, "Response missing expected fields")
    else:
        record_test("GET /api/admin/users", False, "Request failed")
    
    return []

def test_get_user_stats(admin_token: str) -> Dict[str, Any]:
    """Test getting user statistics."""
    print_subheader("Testing GET /api/admin/users/stats")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/admin/users/stats", False, "No admin token available")
        return {}
    
    response, success = make_request("GET", "/admin/users/stats", auth_token=admin_token)
    
    if success:
        if "total" in response and "active" in response and "banned" in response and "new_today" in response:
            print_success(f"Got user statistics:")
            print_success(f"Total users: {response['total']}")
            print_success(f"Active users: {response['active']}")
            print_success(f"Banned users: {response['banned']}")
            print_success(f"New users today: {response['new_today']}")
            record_test("GET /api/admin/users/stats", True)
            return response
        else:
            print_error(f"User statistics response missing expected fields: {response}")
            record_test("GET /api/admin/users/stats", False, "Response missing expected fields")
    else:
        record_test("GET /api/admin/users/stats", False, "Request failed")
    
    return {}

def test_ban_user(admin_token: str, user_id: str, reason: str = "Testing ban functionality") -> bool:
    """Test banning a user."""
    print_subheader(f"Testing POST /api/admin/users/{user_id}/ban")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("POST /api/admin/users/{user_id}/ban", False, "No admin token available")
        return False
    
    data = {
        "reason": reason
    }
    
    response, success = make_request(
        "POST", 
        f"/admin/users/{user_id}/ban", 
        data=data,
        auth_token=admin_token
    )
    
    if success:
        if "message" in response and "banned" in response["message"].lower():
            print_success(f"User {user_id} banned successfully")
            record_test("POST /api/admin/users/{user_id}/ban", True)
            return True
        else:
            print_error(f"Ban user response unexpected: {response}")
            record_test("POST /api/admin/users/{user_id}/ban", False, f"Unexpected response: {response}")
    else:
        record_test("POST /api/admin/users/{user_id}/ban", False, "Request failed")
    
    return False

def test_unban_user(admin_token: str, user_id: str) -> bool:
    """Test unbanning a user."""
    print_subheader(f"Testing POST /api/admin/users/{user_id}/unban")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("POST /api/admin/users/{user_id}/unban", False, "No admin token available")
        return False
    
    response, success = make_request(
        "POST", 
        f"/admin/users/{user_id}/unban", 
        auth_token=admin_token
    )
    
    if success:
        if "message" in response and "unbanned" in response["message"].lower():
            print_success(f"User {user_id} unbanned successfully")
            record_test("POST /api/admin/users/{user_id}/unban", True)
            return True
        else:
            print_error(f"Unban user response unexpected: {response}")
            record_test("POST /api/admin/users/{user_id}/unban", False, f"Unexpected response: {response}")
    else:
        record_test("POST /api/admin/users/{user_id}/unban", False, "Request failed")
    
    return False

def verify_user_status(admin_token: str, user_id: str, expected_status: str) -> bool:
    """Verify a user's status."""
    print_subheader(f"Verifying User Status (ID: {user_id}, Expected: {expected_status})")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"Verify User Status - {expected_status}", False, "No admin token available")
        return False
    
    # Get the user details
    users = test_get_users(admin_token)
    
    user = None
    for u in users:
        if u["id"] == user_id:
            user = u
            break
    
    if not user:
        print_error(f"User {user_id} not found in users list")
        record_test(f"Verify User Status - {expected_status}", False, "User not found")
        return False
    
    if user["status"] == expected_status:
        print_success(f"User status is {user['status']} as expected")
        record_test(f"Verify User Status - {expected_status}", True)
        return True
    else:
        print_error(f"User status is {user['status']}, expected {expected_status}")
        record_test(f"Verify User Status - {expected_status}", False, f"Status mismatch: {user['status']} != {expected_status}")
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

def run_admin_api_tests() -> None:
    """Run admin API tests for the specified endpoints."""
    print_header("GEMPLAY ADMIN API TESTING")
    
    # Test 1: Admin Login
    admin_token = test_admin_login()
    
    if not admin_token:
        print_error("Admin login failed, cannot proceed with further tests")
        print_summary()
        return
    
    # Test 2: Get User Statistics
    test_get_user_stats(admin_token)
    
    # Test 3: Get Users List
    users = test_get_users(admin_token)
    
    if not users:
        print_error("Failed to get users list, cannot proceed with ban/unban tests")
        print_summary()
        return
    
    # Find a non-admin user to test ban/unban
    test_user = None
    for user in users:
        if user["role"] == "USER" and user["status"] == "ACTIVE":
            test_user = user
            break
    
    # If no regular user, use the superadmin (not ideal but works for testing)
    if not test_user:
        for user in users:
            if user["role"] == "SUPER_ADMIN" and user["status"] == "ACTIVE":
                test_user = user
                break
    
    if not test_user:
        print_error("No suitable user found for ban/unban tests")
        print_summary()
        return
    
    print_success(f"Found test user: {test_user['username']} (ID: {test_user['id']})")
    
    # Test 4: Ban User
    ban_success = test_ban_user(admin_token, test_user["id"])
    
    if ban_success:
        # Verify user is banned
        verify_user_status(admin_token, test_user["id"], "BANNED")
    
        # Test 5: Unban User
        unban_success = test_unban_user(admin_token, test_user["id"])
        
        if unban_success:
            # Verify user is active again
            verify_user_status(admin_token, test_user["id"], "ACTIVE")
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_admin_api_tests()