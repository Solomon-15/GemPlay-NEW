#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://7a07c3b0-a218-4c24-84e0-b12a9efb7441.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
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

def login_admin() -> Optional[str]:
    """Login as admin and return the access token."""
    print_subheader("Logging in as Admin")
    
    login_data = {
        "email": ADMIN_CREDENTIALS["email"],
        "password": ADMIN_CREDENTIALS["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin logged in successfully")
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        return None

def test_get_users_stats(admin_token: str) -> None:
    """Test GET /api/admin/users/stats endpoint."""
    print_subheader("Testing GET /api/admin/users/stats")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/admin/users/stats", False, "No admin token available")
        return
    
    response, success = make_request("GET", "/admin/users/stats", auth_token=admin_token)
    
    if success:
        # Check if the response contains the expected fields
        expected_fields = ["total", "active", "banned", "new_today"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if not missing_fields:
            print_success("Users stats endpoint returned all expected fields")
            print_success(f"Total users: {response['total']}")
            print_success(f"Active users: {response['active']}")
            print_success(f"Banned users: {response['banned']}")
            print_success(f"New users today: {response['new_today']}")
            record_test("GET /api/admin/users/stats", True)
        else:
            print_error(f"Users stats response missing fields: {missing_fields}")
            record_test("GET /api/admin/users/stats", False, f"Missing fields: {missing_fields}")
    else:
        record_test("GET /api/admin/users/stats", False, "Request failed")

def test_get_all_users(admin_token: str) -> List[Dict[str, Any]]:
    """Test GET /api/admin/users endpoint."""
    print_subheader("Testing GET /api/admin/users")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/admin/users", False, "No admin token available")
        return []
    
    # Test with default parameters
    response, success = make_request("GET", "/admin/users", auth_token=admin_token)
    
    if success:
        if "users" in response and isinstance(response["users"], list):
            print_success(f"Got users list with {len(response['users'])} users")
            print_success(f"Total users: {response['total']}")
            print_success(f"Page: {response['page']}")
            print_success(f"Limit: {response['limit']}")
            print_success(f"Total pages: {response['pages']}")
            
            # Check if pagination info is consistent
            if response["total"] > 0 and len(response["users"]) == 0:
                print_error("Pagination inconsistency: total > 0 but empty users list")
                record_test("GET /api/admin/users", False, "Pagination inconsistency")
                return []
            
            record_test("GET /api/admin/users", True)
            
            # Test pagination
            if response["pages"] > 1:
                print_subheader("Testing GET /api/admin/users with pagination")
                page2_response, page2_success = make_request(
                    "GET", 
                    "/admin/users", 
                    data={"page": 2, "limit": response["limit"]},
                    auth_token=admin_token
                )
                
                if page2_success and "users" in page2_response:
                    print_success(f"Got page 2 with {len(page2_response['users'])} users")
                    
                    # Check if page 2 users are different from page 1
                    if response["users"] and page2_response["users"]:
                        page1_ids = [user["id"] for user in response["users"]]
                        page2_ids = [user["id"] for user in page2_response["users"]]
                        
                        if set(page1_ids).intersection(set(page2_ids)):
                            print_warning("Some users appear on both page 1 and page 2")
                        else:
                            print_success("Page 1 and page 2 contain different users")
                    
                    record_test("GET /api/admin/users - Pagination", True)
                else:
                    print_error("Failed to get page 2 of users")
                    record_test("GET /api/admin/users - Pagination", False, "Failed to get page 2")
            
            # Test search functionality
            if response["users"]:
                print_subheader("Testing GET /api/admin/users with search")
                
                # Get a username to search for
                search_user = response["users"][0]
                search_term = search_user["username"][:3]  # Use first 3 chars of username
                
                search_response, search_success = make_request(
                    "GET", 
                    "/admin/users", 
                    data={"search": search_term},
                    auth_token=admin_token
                )
                
                if search_success and "users" in search_response:
                    print_success(f"Search for '{search_term}' returned {len(search_response['users'])} users")
                    
                    # Check if the search results contain the user we searched for
                    found = False
                    for user in search_response["users"]:
                        if user["id"] == search_user["id"]:
                            found = True
                            break
                    
                    if found:
                        print_success(f"Search results contain the expected user")
                        record_test("GET /api/admin/users - Search", True)
                    else:
                        print_error(f"Search results do not contain the expected user")
                        record_test("GET /api/admin/users - Search", False, "Expected user not found in search results")
                else:
                    print_error("Failed to search users")
                    record_test("GET /api/admin/users - Search", False, "Search request failed")
            
            # Test status filter
            print_subheader("Testing GET /api/admin/users with status filter")
            
            status_response, status_success = make_request(
                "GET", 
                "/admin/users", 
                data={"status": "ACTIVE"},
                auth_token=admin_token
            )
            
            if status_success and "users" in status_response:
                print_success(f"Filter for ACTIVE status returned {len(status_response['users'])} users")
                
                # Check if all returned users have ACTIVE status
                all_active = True
                for user in status_response["users"]:
                    if user["status"] != "ACTIVE":
                        all_active = False
                        break
                
                if all_active:
                    print_success("All users in filtered results have ACTIVE status")
                    record_test("GET /api/admin/users - Status Filter", True)
                else:
                    print_error("Some users in filtered results do not have ACTIVE status")
                    record_test("GET /api/admin/users - Status Filter", False, "Filter not working correctly")
            else:
                print_error("Failed to filter users by status")
                record_test("GET /api/admin/users - Status Filter", False, "Status filter request failed")
            
            return response["users"]
        else:
            print_error(f"Users response missing 'users' field or it's not a list: {response}")
            record_test("GET /api/admin/users", False, "Response format incorrect")
    else:
        record_test("GET /api/admin/users", False, "Request failed")
    
    return []

def test_update_user(admin_token: str, user_id: str) -> None:
    """Test PUT /api/admin/users/{user_id} endpoint."""
    print_subheader(f"Testing PUT /api/admin/users/{user_id}")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"PUT /api/admin/users/{user_id}", False, "No admin token available")
        return
    
    # Get current user data
    user_response, user_success = make_request("GET", f"/admin/users", auth_token=admin_token)
    
    if not user_success or "users" not in user_response or not user_response["users"]:
        print_error("Failed to get user data for update test")
        record_test(f"PUT /api/admin/users/{user_id}", False, "Failed to get user data")
        return
    
    # Find the user in the list
    user_data = None
    for user in user_response["users"]:
        if user["id"] == user_id:
            user_data = user
            break
    
    if not user_data:
        print_error(f"User with ID {user_id} not found")
        record_test(f"PUT /api/admin/users/{user_id}", False, f"User with ID {user_id} not found")
        return
    
    # Prepare update data - just update the daily_limit_max
    update_data = {
        "daily_limit_max": user_data.get("daily_limit_max", 1000) + 100
    }
    
    # Update the user
    update_response, update_success = make_request(
        "PUT", 
        f"/admin/users/{user_id}", 
        data=update_data,
        auth_token=admin_token
    )
    
    if update_success:
        print_success(f"User updated successfully")
        
        # Verify the update
        verify_response, verify_success = make_request("GET", f"/admin/users", auth_token=admin_token)
        
        if verify_success and "users" in verify_response:
            # Find the user again
            updated_user = None
            for user in verify_response["users"]:
                if user["id"] == user_id:
                    updated_user = user
                    break
            
            if updated_user:
                if updated_user.get("daily_limit_max") == update_data["daily_limit_max"]:
                    print_success("User update verified: daily_limit_max updated correctly")
                    record_test(f"PUT /api/admin/users/{user_id}", True)
                else:
                    print_error(f"User update not verified: expected daily_limit_max {update_data['daily_limit_max']}, got {updated_user.get('daily_limit_max')}")
                    record_test(f"PUT /api/admin/users/{user_id}", False, "Update not verified")
            else:
                print_error(f"Updated user not found in verification response")
                record_test(f"PUT /api/admin/users/{user_id}", False, "Updated user not found")
        else:
            print_error("Failed to verify user update")
            record_test(f"PUT /api/admin/users/{user_id}", False, "Failed to verify update")
    else:
        record_test(f"PUT /api/admin/users/{user_id}", False, "Update request failed")

def test_ban_unban_user(admin_token: str, user_id: str) -> None:
    """Test POST /api/admin/users/{user_id}/ban and POST /api/admin/users/{user_id}/unban endpoints."""
    print_subheader(f"Testing POST /api/admin/users/{user_id}/ban")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"POST /api/admin/users/{user_id}/ban", False, "No admin token available")
        return
    
    # Ban the user
    ban_data = {
        "reason": "Testing ban functionality",
        "duration_hours": 1  # Ban for 1 hour
    }
    
    ban_response, ban_success = make_request(
        "POST", 
        f"/admin/users/{user_id}/ban", 
        data=ban_data,
        auth_token=admin_token
    )
    
    if ban_success:
        print_success(f"User banned successfully")
        
        # Verify the ban
        verify_response, verify_success = make_request("GET", f"/admin/users", auth_token=admin_token)
        
        if verify_success and "users" in verify_response:
            # Find the user
            banned_user = None
            for user in verify_response["users"]:
                if user["id"] == user_id:
                    banned_user = user
                    break
            
            if banned_user:
                if banned_user.get("status") == "BANNED":
                    print_success("User ban verified: status is BANNED")
                    record_test(f"POST /api/admin/users/{user_id}/ban", True)
                else:
                    print_error(f"User ban not verified: expected status BANNED, got {banned_user.get('status')}")
                    record_test(f"POST /api/admin/users/{user_id}/ban", False, "Ban not verified")
            else:
                print_error(f"Banned user not found in verification response")
                record_test(f"POST /api/admin/users/{user_id}/ban", False, "Banned user not found")
        else:
            print_error("Failed to verify user ban")
            record_test(f"POST /api/admin/users/{user_id}/ban", False, "Failed to verify ban")
    else:
        record_test(f"POST /api/admin/users/{user_id}/ban", False, "Ban request failed")
    
    # Now test unbanning
    print_subheader(f"Testing POST /api/admin/users/{user_id}/unban")
    
    unban_response, unban_success = make_request(
        "POST", 
        f"/admin/users/{user_id}/unban", 
        auth_token=admin_token
    )
    
    if unban_success:
        print_success(f"User unbanned successfully")
        
        # Verify the unban
        verify_response, verify_success = make_request("GET", f"/admin/users", auth_token=admin_token)
        
        if verify_success and "users" in verify_response:
            # Find the user
            unbanned_user = None
            for user in verify_response["users"]:
                if user["id"] == user_id:
                    unbanned_user = user
                    break
            
            if unbanned_user:
                if unbanned_user.get("status") == "ACTIVE":
                    print_success("User unban verified: status is ACTIVE")
                    record_test(f"POST /api/admin/users/{user_id}/unban", True)
                else:
                    print_error(f"User unban not verified: expected status ACTIVE, got {unbanned_user.get('status')}")
                    record_test(f"POST /api/admin/users/{user_id}/unban", False, "Unban not verified")
            else:
                print_error(f"Unbanned user not found in verification response")
                record_test(f"POST /api/admin/users/{user_id}/unban", False, "Unbanned user not found")
        else:
            print_error("Failed to verify user unban")
            record_test(f"POST /api/admin/users/{user_id}/unban", False, "Failed to verify unban")
    else:
        record_test(f"POST /api/admin/users/{user_id}/unban", False, "Unban request failed")

def test_update_user_balance(admin_token: str, user_id: str) -> None:
    """Test POST /api/admin/users/{user_id}/balance endpoint."""
    print_subheader(f"Testing POST /api/admin/users/{user_id}/balance")
    
    if not admin_token:
        print_error("No admin token available")
        record_test(f"POST /api/admin/users/{user_id}/balance", False, "No admin token available")
        return
    
    # Get current user data
    user_response, user_success = make_request("GET", f"/admin/users", auth_token=admin_token)
    
    if not user_success or "users" not in user_response or not user_response["users"]:
        print_error("Failed to get user data for balance update test")
        record_test(f"POST /api/admin/users/{user_id}/balance", False, "Failed to get user data")
        return
    
    # Find the user in the list
    user_data = None
    for user in user_response["users"]:
        if user["id"] == user_id:
            user_data = user
            break
    
    if not user_data:
        print_error(f"User with ID {user_id} not found")
        record_test(f"POST /api/admin/users/{user_id}/balance", False, f"User with ID {user_id} not found")
        return
    
    # Prepare balance update data
    current_balance = user_data.get("virtual_balance", 0)
    balance_data = {
        "amount": 100,
        "description": "Testing balance update"
    }
    
    # Update the user's balance
    balance_response, balance_success = make_request(
        "POST", 
        f"/admin/users/{user_id}/balance", 
        data=balance_data,
        auth_token=admin_token
    )
    
    if balance_success:
        print_success(f"User balance updated successfully")
        
        # Verify the balance update
        verify_response, verify_success = make_request("GET", f"/admin/users", auth_token=admin_token)
        
        if verify_success and "users" in verify_response:
            # Find the user again
            updated_user = None
            for user in verify_response["users"]:
                if user["id"] == user_id:
                    updated_user = user
                    break
            
            if updated_user:
                expected_balance = current_balance + balance_data["amount"]
                if abs(updated_user.get("virtual_balance", 0) - expected_balance) < 0.01:  # Allow for floating point imprecision
                    print_success(f"User balance update verified: {current_balance} + {balance_data['amount']} = {updated_user.get('virtual_balance')}")
                    record_test(f"POST /api/admin/users/{user_id}/balance", True)
                else:
                    print_error(f"User balance update not verified: expected {expected_balance}, got {updated_user.get('virtual_balance')}")
                    record_test(f"POST /api/admin/users/{user_id}/balance", False, "Balance update not verified")
            else:
                print_error(f"Updated user not found in verification response")
                record_test(f"POST /api/admin/users/{user_id}/balance", False, "Updated user not found")
        else:
            print_error("Failed to verify user balance update")
            record_test(f"POST /api/admin/users/{user_id}/balance", False, "Failed to verify balance update")
    else:
        record_test(f"POST /api/admin/users/{user_id}/balance", False, "Balance update request failed")

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
    print_header("GEMPLAY ADMIN API TESTING")
    
    # Login as admin
    admin_token = login_admin()
    if not admin_token:
        print_error("Failed to login as admin. Cannot proceed with tests.")
        return
    
    # Test GET /api/admin/users/stats
    test_get_users_stats(admin_token)
    
    # Test GET /api/admin/users
    users = test_get_all_users(admin_token)
    
    if users:
        # Select a non-admin user for testing
        test_user = None
        for user in users:
            if user.get("role") == "USER":
                test_user = user
                break
        
        if not test_user:
            # If no regular user found, use the first user
            test_user = users[0]
        
        user_id = test_user["id"]
        print_success(f"Selected user {test_user.get('username')} (ID: {user_id}) for testing")
        
        # Test PUT /api/admin/users/{user_id}
        test_update_user(admin_token, user_id)
        
        # Test POST /api/admin/users/{user_id}/ban and POST /api/admin/users/{user_id}/unban
        test_ban_unban_user(admin_token, user_id)
        
        # Test POST /api/admin/users/{user_id}/balance
        test_update_user_balance(admin_token, user_id)
    else:
        print_error("No users found for testing user-specific endpoints")
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_all_tests()