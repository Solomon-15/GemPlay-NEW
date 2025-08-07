#!/usr/bin/env python3
"""
Role-based Restrictions Testing for Edit User Modal - Russian Review
Focus: Testing the critical security fix for role assignment restrictions

CONTEXT:
We fixed a critical security vulnerability in the PUT /api/admin/users/{user_id} endpoint.
Now only SUPER_ADMIN can assign SUPER_ADMIN role to other users.

FIXED CODE:
```python
if "role" in user_data:
    # Role-based restrictions: only SUPER_ADMIN can assign SUPER_ADMIN role
    if user_data["role"] == "SUPER_ADMIN" and current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SUPER_ADMIN can assign SUPER_ADMIN role"
        )
    update_fields["role"] = user_data["role"]
```

TEST SCENARIOS:
1. ADMIN tries to assign SUPER_ADMIN role - should get 403
2. SUPER_ADMIN assigns SUPER_ADMIN role - should get 200
3. ADMIN assigns other roles (USER, MODERATOR, ADMIN) - should get 200
4. Other user update functionality still works
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://5a0f72db-7197-4535-89b4-f85be852ec00.preview.emergentagent.com/api"

ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

SUPER_ADMIN_USER = {
    "email": "superadmin@gemplay.com", 
    "password": "SuperAdmin123!"
}

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_subheader(text: str) -> None:
    """Print a subheader message."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * len(text)}{Colors.ENDC}")

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

def test_login(email: str, password: str, user_type: str) -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing Login for {user_type}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"{user_type} login successful")
        record_test(f"{user_type} Login", True)
        return response["access_token"]
    else:
        print_error(f"{user_type} login failed")
        record_test(f"{user_type} Login", False, "Login failed")
        return None

def get_test_user_id(admin_token: str) -> Optional[str]:
    """Get a test user ID for role assignment testing."""
    print_subheader("Getting Test User for Role Assignment")
    
    # Get users list
    response, success = make_request(
        "GET", "/admin/users?page=1&limit=10",
        auth_token=admin_token
    )
    
    if success and "users" in response:
        # Find a user that's not an admin
        for user in response["users"]:
            if user.get("role") == "USER":
                print_success(f"Found test user: {user['username']} (ID: {user['id']})")
                return user["id"]
        
        # If no USER found, use any non-admin user
        for user in response["users"]:
            if user.get("role") not in ["ADMIN", "SUPER_ADMIN"]:
                print_success(f"Found test user: {user['username']} (ID: {user['id']})")
                return user["id"]
    
    print_error("No suitable test user found")
    return None

def test_admin_cannot_assign_super_admin_role(admin_token: str, test_user_id: str) -> None:
    """Test that ADMIN cannot assign SUPER_ADMIN role (should get 403)."""
    print_subheader("TEST 1: ADMIN tries to assign SUPER_ADMIN role (should fail with 403)")
    
    update_data = {
        "role": "SUPER_ADMIN"
    }
    
    response, success = make_request(
        "PUT", f"/admin/users/{test_user_id}",
        data=update_data,
        auth_token=admin_token,
        expected_status=403  # Expecting 403 Forbidden
    )
    
    if success:
        # Check if the error message is correct
        if "detail" in response and "Only SUPER_ADMIN can assign SUPER_ADMIN role" in response["detail"]:
            print_success("✅ ADMIN correctly blocked from assigning SUPER_ADMIN role")
            print_success(f"✅ Correct error message: {response['detail']}")
            record_test("ADMIN blocked from assigning SUPER_ADMIN role", True, "403 with correct error message")
        else:
            print_error("❌ Got 403 but wrong error message")
            record_test("ADMIN blocked from assigning SUPER_ADMIN role", False, "403 but wrong error message")
    else:
        print_error("❌ ADMIN was not blocked from assigning SUPER_ADMIN role - SECURITY VULNERABILITY!")
        record_test("ADMIN blocked from assigning SUPER_ADMIN role", False, "Security vulnerability - ADMIN can assign SUPER_ADMIN role")

def test_super_admin_can_assign_super_admin_role(super_admin_token: str, test_user_id: str) -> None:
    """Test that SUPER_ADMIN can assign SUPER_ADMIN role (should get 200)."""
    print_subheader("TEST 2: SUPER_ADMIN assigns SUPER_ADMIN role (should succeed)")
    
    update_data = {
        "role": "SUPER_ADMIN"
    }
    
    response, success = make_request(
        "PUT", f"/admin/users/{test_user_id}",
        data=update_data,
        auth_token=super_admin_token,
        expected_status=200  # Expecting success
    )
    
    if success:
        print_success("✅ SUPER_ADMIN successfully assigned SUPER_ADMIN role")
        record_test("SUPER_ADMIN can assign SUPER_ADMIN role", True, "200 success")
        
        # Verify the role was actually updated
        user_response, user_success = make_request(
            "GET", f"/admin/users?page=1&limit=100",
            auth_token=super_admin_token
        )
        
        if user_success and "users" in user_response:
            for user in user_response["users"]:
                if user["id"] == test_user_id:
                    if user.get("role") == "SUPER_ADMIN":
                        print_success("✅ Role successfully updated in database")
                    else:
                        print_warning(f"⚠ Role in database is {user.get('role')}, not SUPER_ADMIN")
                    break
    else:
        print_error("❌ SUPER_ADMIN failed to assign SUPER_ADMIN role")
        record_test("SUPER_ADMIN can assign SUPER_ADMIN role", False, "Request failed")

def test_admin_can_assign_other_roles(admin_token: str, test_user_id: str) -> None:
    """Test that ADMIN can assign other roles (USER, MODERATOR, ADMIN)."""
    print_subheader("TEST 3: ADMIN assigns other roles (should succeed)")
    
    roles_to_test = ["USER", "MODERATOR", "ADMIN"]
    
    for role in roles_to_test:
        print(f"\n--- Testing assignment of {role} role ---")
        
        update_data = {
            "role": role
        }
        
        response, success = make_request(
            "PUT", f"/admin/users/{test_user_id}",
            data=update_data,
            auth_token=admin_token,
            expected_status=200  # Expecting success
        )
        
        if success:
            print_success(f"✅ ADMIN successfully assigned {role} role")
            record_test(f"ADMIN can assign {role} role", True, "200 success")
        else:
            print_error(f"❌ ADMIN failed to assign {role} role")
            record_test(f"ADMIN can assign {role} role", False, "Request failed")

def test_other_user_update_functionality(admin_token: str, test_user_id: str) -> None:
    """Test that other user update functionality still works."""
    print_subheader("TEST 4: Other user update functionality (username, email, balance)")
    
    # Test username update
    print("\n--- Testing username update ---")
    username_data = {
        "username": f"updated_user_{random.randint(1000, 9999)}"
    }
    
    response, success = make_request(
        "PUT", f"/admin/users/{test_user_id}",
        data=username_data,
        auth_token=admin_token,
        expected_status=200
    )
    
    if success:
        print_success("✅ Username update successful")
        record_test("Username update functionality", True, "200 success")
    else:
        print_error("❌ Username update failed")
        record_test("Username update functionality", False, "Request failed")
    
    # Test email update
    print("\n--- Testing email update ---")
    email_data = {
        "email": f"updated_{random.randint(1000, 9999)}@test.com"
    }
    
    response, success = make_request(
        "PUT", f"/admin/users/{test_user_id}",
        data=email_data,
        auth_token=admin_token,
        expected_status=200
    )
    
    if success:
        print_success("✅ Email update successful")
        record_test("Email update functionality", True, "200 success")
    else:
        print_error("❌ Email update failed")
        record_test("Email update functionality", False, "Request failed")
    
    # Test virtual balance update
    print("\n--- Testing virtual balance update ---")
    balance_data = {
        "virtual_balance": round(random.uniform(100, 1000), 2)
    }
    
    response, success = make_request(
        "PUT", f"/admin/users/{test_user_id}",
        data=balance_data,
        auth_token=admin_token,
        expected_status=200
    )
    
    if success:
        print_success("✅ Virtual balance update successful")
        record_test("Virtual balance update functionality", True, "200 success")
    else:
        print_error("❌ Virtual balance update failed")
        record_test("Virtual balance update functionality", False, "Request failed")

def test_multiple_field_updates(admin_token: str, test_user_id: str) -> None:
    """Test updating multiple fields at once."""
    print_subheader("TEST 5: Multiple field updates (username + balance + role)")
    
    update_data = {
        "username": f"multi_update_{random.randint(1000, 9999)}",
        "virtual_balance": round(random.uniform(500, 1500), 2),
        "role": "MODERATOR"  # Safe role that ADMIN can assign
    }
    
    response, success = make_request(
        "PUT", f"/admin/users/{test_user_id}",
        data=update_data,
        auth_token=admin_token,
        expected_status=200
    )
    
    if success:
        print_success("✅ Multiple field update successful")
        record_test("Multiple field update functionality", True, "200 success")
    else:
        print_error("❌ Multiple field update failed")
        record_test("Multiple field update functionality", False, "Request failed")

def print_test_summary() -> None:
    """Print test summary."""
    print_header("ROLE-BASED RESTRICTIONS TEST SUMMARY")
    
    success_rate = (test_results["passed"] / test_results["total"]) * 100 if test_results["total"] > 0 else 0
    
    print(f"Total Tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 90 else Colors.WARNING}{success_rate:.1f}%{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}DETAILED RESULTS:{Colors.ENDC}")
    for test in test_results["tests"]:
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if test["passed"] else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"{status} {test['name']}")
        if test["details"]:
            print(f"   Details: {test['details']}")
    
    # Critical security assessment
    print(f"\n{Colors.BOLD}CRITICAL SECURITY ASSESSMENT:{Colors.ENDC}")
    
    admin_blocked_test = next((t for t in test_results["tests"] if "ADMIN blocked from assigning SUPER_ADMIN role" in t["name"]), None)
    super_admin_can_assign_test = next((t for t in test_results["tests"] if "SUPER_ADMIN can assign SUPER_ADMIN role" in t["name"]), None)
    
    if admin_blocked_test and admin_blocked_test["passed"]:
        print(f"{Colors.OKGREEN}🔒 SECURITY FIX VERIFIED: ADMIN users cannot assign SUPER_ADMIN role{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}🚨 CRITICAL SECURITY VULNERABILITY: ADMIN users can still assign SUPER_ADMIN role!{Colors.ENDC}")
    
    if super_admin_can_assign_test and super_admin_can_assign_test["passed"]:
        print(f"{Colors.OKGREEN}✅ SUPER_ADMIN functionality preserved: Can assign SUPER_ADMIN role{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠ SUPER_ADMIN functionality issue: Cannot assign SUPER_ADMIN role{Colors.ENDC}")
    
    # Overall assessment
    if admin_blocked_test and admin_blocked_test["passed"] and success_rate >= 80:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ROLE-BASED RESTRICTIONS FIX: SUCCESSFUL!{Colors.ENDC}")
        print(f"{Colors.OKGREEN}The critical security vulnerability has been fixed. Only SUPER_ADMIN can assign SUPER_ADMIN role.{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ ROLE-BASED RESTRICTIONS FIX: FAILED!{Colors.ENDC}")
        print(f"{Colors.FAIL}The security fix needs attention. Please review the implementation.{Colors.ENDC}")

def main():
    """Main test execution."""
    print_header("ROLE-BASED RESTRICTIONS TESTING")
    print("Testing critical security fix for Edit User Modal")
    print("Focus: Only SUPER_ADMIN can assign SUPER_ADMIN role")
    
    # Step 1: Login as ADMIN
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "ADMIN")
    if not admin_token:
        print_error("Failed to login as ADMIN - cannot continue testing")
        return
    
    # Step 2: Login as SUPER_ADMIN
    super_admin_token = test_login(SUPER_ADMIN_USER["email"], SUPER_ADMIN_USER["password"], "SUPER_ADMIN")
    if not super_admin_token:
        print_error("Failed to login as SUPER_ADMIN - cannot continue testing")
        return
    
    # Step 3: Get a test user ID
    test_user_id = get_test_user_id(admin_token)
    if not test_user_id:
        print_error("Failed to get test user ID - cannot continue testing")
        return
    
    # Step 4: Run the critical security tests
    test_admin_cannot_assign_super_admin_role(admin_token, test_user_id)
    test_super_admin_can_assign_super_admin_role(super_admin_token, test_user_id)
    test_admin_can_assign_other_roles(admin_token, test_user_id)
    test_other_user_update_functionality(admin_token, test_user_id)
    test_multiple_field_updates(admin_token, test_user_id)
    
    # Step 5: Print summary
    print_test_summary()

if __name__ == "__main__":
    main()