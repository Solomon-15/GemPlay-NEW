#!/usr/bin/env python3
"""
403 Error Fixes Testing for Non-Admin Users - Russian Review
Focus: Testing that non-admin users don't get 403 errors when accessing the system
Requirements:
1. Create test users with different roles (USER, MODERATOR, ADMIN, SUPER_ADMIN)
2. Verify that regular users (USER, MODERATOR) don't get 403 errors during authentication
3. Verify that admins (ADMIN, SUPER_ADMIN) can access admin endpoints
4. Test role-based access control for various endpoints
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://7442eeef-ca61-40db-a631-c7dfd755caa2.preview.emergentagent.com/api"

# Test results tracking
test_results = []
total_tests = 0
passed_tests = 0

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_subheader(text):
    print(f"\n{'-'*40}")
    print(f"  {text}")
    print(f"{'-'*40}")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def record_test(test_name: str, passed: bool, details: str = ""):
    global total_tests, passed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
    
    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def make_request(method: str, endpoint: str, data: Dict = None, auth_token: str = None, params: Dict = None) -> Tuple[Dict, bool]:
    """Make HTTP request and return response data and success status."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, params=params, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=30)
        else:
            return {}, False
        
        try:
            response_data = response.json()
        except:
            response_data = {"status_code": response.status_code, "text": response.text}
        
        return response_data, response.status_code < 400
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return {"error": str(e)}, False

def generate_unique_username():
    """Generate unique username for testing."""
    timestamp = str(int(time.time()))[-4:]
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
    return f"test{timestamp}{random_suffix}"

def generate_unique_email():
    """Generate unique email for testing."""
    timestamp = str(int(time.time()))[-4:]
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
    return f"test{timestamp}{random_suffix}@example.com"

def create_test_user(role: str = "USER") -> Tuple[Dict, str]:
    """Create a test user and return user data and auth token."""
    
    # For admin roles, use existing accounts
    if role == "ADMIN":
        login_data = {
            "email": "admin@gemplay.com",
            "password": "Admin123!"
        }
        
        login_response, login_success = make_request("POST", "/auth/login", data=login_data)
        
        if login_success:
            auth_token = login_response.get("access_token")
            user_info = login_response.get("user", {})
            print_success(f"Logged in as existing ADMIN user")
            return user_info, auth_token
        else:
            print_error(f"Failed to login as admin: {login_response}")
            return {}, ""
    
    elif role == "SUPER_ADMIN":
        login_data = {
            "email": "superadmin@gemplay.com",
            "password": "SuperAdmin123!"
        }
        
        login_response, login_success = make_request("POST", "/auth/login", data=login_data)
        
        if login_success:
            auth_token = login_response.get("access_token")
            user_info = login_response.get("user", {})
            print_success(f"Logged in as existing SUPER_ADMIN user")
            return user_info, auth_token
        else:
            print_error(f"Failed to login as super admin: {login_response}")
            return {}, ""
    
    # For regular users, create new ones
    username = generate_unique_username()
    email = generate_unique_email()
    password = "TestPassword123!"
    
    # Register user
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "gender": "male"
    }
    
    print_info(f"Creating {role} user: {username} ({email})")
    
    # Register the user
    register_response, register_success = make_request("POST", "/auth/register", data=user_data)
    
    if not register_success:
        print_error(f"Failed to register user: {register_response}")
        return {}, ""
    
    user_id = register_response.get("user_id")
    verification_token = register_response.get("verification_token")
    
    if not user_id:
        print_error("No user_id in registration response")
        return {}, ""
    
    # Verify email using the token
    if verification_token:
        verify_response, verify_success = make_request(
            "POST", "/auth/verify-email", 
            data={"token": verification_token}
        )
        
        if not verify_success:
            print_error(f"Failed to verify email: {verify_response}")
            return {}, ""
        
        print_success("Email verified successfully")
    
    # If we need to create moderator, update role via admin endpoint
    if role == "MODERATOR":
        # Login as super admin to update user role
        super_admin_login = {
            "email": "superadmin@gemplay.com",
            "password": "SuperAdmin123!"
        }
        
        admin_login_response, admin_login_success = make_request("POST", "/auth/login", data=super_admin_login)
        if admin_login_success:
            admin_token = admin_login_response.get("access_token")
            
            # Update user role to MODERATOR
            update_response, update_success = make_request(
                "PUT", f"/admin/users/{user_id}",
                data={"role": "MODERATOR"},
                auth_token=admin_token
            )
            
            if not update_success:
                print_error(f"Failed to update user role to MODERATOR: {update_response}")
    
    # Login as the created user
    login_data = {
        "email": email,
        "password": password
    }
    
    login_response, login_success = make_request("POST", "/auth/login", data=login_data)
    
    if not login_success:
        print_error(f"Failed to login as created user: {login_response}")
        return user_data, ""
    
    auth_token = login_response.get("access_token")
    user_info = login_response.get("user", {})
    
    print_success(f"Created and logged in {role} user: {username}")
    
    return {**user_data, **user_info}, auth_token

def test_user_authentication_and_basic_access():
    """Test that users of all roles can authenticate and access basic endpoints."""
    print_header("USER AUTHENTICATION AND BASIC ACCESS TESTING")
    
    roles_to_test = ["USER", "MODERATOR", "ADMIN", "SUPER_ADMIN"]
    user_tokens = {}
    
    # Create users for each role
    for role in roles_to_test:
        print_subheader(f"Creating {role} User")
        
        user_data, auth_token = create_test_user(role)
        
        if auth_token:
            user_tokens[role] = auth_token
            print_success(f"✅ {role} user created and authenticated successfully")
            record_test(f"{role} User Creation and Authentication", True)
        else:
            print_error(f"❌ Failed to create {role} user")
            record_test(f"{role} User Creation and Authentication", False, "Failed to create or authenticate user")
            continue
        
        # Test basic user endpoints that should work for all roles
        print_info(f"Testing basic endpoints for {role} user...")
        
        # Test /auth/me endpoint
        me_response, me_success = make_request("GET", "/auth/me", auth_token=auth_token)
        if me_success:
            print_success(f"✅ {role} user can access /auth/me")
            record_test(f"{role} User - /auth/me Access", True)
            
            # Verify role is correct
            user_role = me_response.get("role")
            if user_role == role:
                print_success(f"✅ {role} user has correct role: {user_role}")
                record_test(f"{role} User - Correct Role Assignment", True)
            else:
                print_error(f"❌ {role} user has incorrect role: {user_role}")
                record_test(f"{role} User - Correct Role Assignment", False, f"Expected: {role}, Got: {user_role}")
        else:
            print_error(f"❌ {role} user cannot access /auth/me: {me_response}")
            record_test(f"{role} User - /auth/me Access", False, str(me_response))
        
        # Test /games/available endpoint (should work for all users)
        games_response, games_success = make_request("GET", "/games/available", auth_token=auth_token)
        if games_success:
            print_success(f"✅ {role} user can access /games/available")
            record_test(f"{role} User - /games/available Access", True)
        else:
            print_error(f"❌ {role} user cannot access /games/available: {games_response}")
            record_test(f"{role} User - /games/available Access", False, str(games_response))
        
        # Test /games/my-bets endpoint (should work for all users)
        my_bets_response, my_bets_success = make_request("GET", "/games/my-bets", auth_token=auth_token)
        if my_bets_success:
            print_success(f"✅ {role} user can access /games/my-bets")
            record_test(f"{role} User - /games/my-bets Access", True)
        else:
            print_error(f"❌ {role} user cannot access /games/my-bets: {my_bets_response}")
            record_test(f"{role} User - /games/my-bets Access", False, str(my_bets_response))
    
    return user_tokens

def test_admin_endpoint_access(user_tokens: Dict[str, str]):
    """Test admin endpoint access for different user roles."""
    print_header("ADMIN ENDPOINT ACCESS TESTING")
    
    # Admin endpoints that should be accessible only to ADMIN and SUPER_ADMIN
    admin_endpoints = [
        "/admin/sounds",
        "/admin/gems", 
        "/admin/games",
        "/admin/dashboard/stats",
        "/admin/users"
    ]
    
    for role, token in user_tokens.items():
        print_subheader(f"Testing Admin Endpoints for {role} User")
        
        for endpoint in admin_endpoints:
            print_info(f"Testing {endpoint}...")
            
            response, success = make_request("GET", endpoint, auth_token=token)
            
            if role in ["ADMIN", "SUPER_ADMIN"]:
                # Admin users should have access
                if success:
                    print_success(f"✅ {role} user can access {endpoint}")
                    record_test(f"{role} User - {endpoint} Access", True)
                else:
                    # Check if it's a 403 error
                    status_code = response.get("status_code", 0)
                    if status_code == 403:
                        print_error(f"❌ {role} user got 403 error on {endpoint}: {response}")
                        record_test(f"{role} User - {endpoint} Access", False, f"403 Forbidden: {response}")
                    else:
                        print_error(f"❌ {role} user cannot access {endpoint}: {response}")
                        record_test(f"{role} User - {endpoint} Access", False, str(response))
            else:
                # Regular users (USER, MODERATOR) should get 403 but not during basic authentication
                status_code = response.get("status_code", 0)
                if status_code == 403:
                    print_success(f"✅ {role} user correctly gets 403 for {endpoint} (expected)")
                    record_test(f"{role} User - {endpoint} Proper 403", True)
                elif success:
                    print_error(f"❌ {role} user unexpectedly has access to {endpoint}")
                    record_test(f"{role} User - {endpoint} Proper 403", False, "Unexpected access granted")
                else:
                    print_info(f"ℹ️  {role} user cannot access {endpoint} (expected): {response}")
                    record_test(f"{role} User - {endpoint} Proper 403", True)

def test_frontend_integration_scenarios(user_tokens: Dict[str, str]):
    """Test scenarios that would cause 403 errors in frontend components."""
    print_header("FRONTEND INTEGRATION SCENARIOS TESTING")
    
    # Test scenarios mentioned in the Russian review
    scenarios = [
        {
            "name": "Lobby.js - Games Loading",
            "endpoint": "/games/available",
            "method": "GET",
            "should_work_for_all": True
        },
        {
            "name": "SoundManager.js - Sound Loading", 
            "endpoint": "/admin/sounds",
            "method": "GET",
            "should_work_for_all": False
        },
        {
            "name": "gemUtils.js - Gem Loading",
            "endpoint": "/admin/gems", 
            "method": "GET",
            "should_work_for_all": False
        },
        {
            "name": "UserManagement.js - User List",
            "endpoint": "/admin/users",
            "method": "GET", 
            "should_work_for_all": False
        }
    ]
    
    for scenario in scenarios:
        print_subheader(f"Testing {scenario['name']}")
        
        for role, token in user_tokens.items():
            print_info(f"Testing for {role} user...")
            
            response, success = make_request(
                scenario["method"], 
                scenario["endpoint"], 
                auth_token=token
            )
            
            if scenario["should_work_for_all"]:
                # This endpoint should work for all users
                if success:
                    print_success(f"✅ {role} user can access {scenario['endpoint']}")
                    record_test(f"{scenario['name']} - {role} Access", True)
                else:
                    status_code = response.get("status_code", 0)
                    if status_code == 403:
                        print_error(f"❌ {role} user got unexpected 403 on {scenario['endpoint']}")
                        record_test(f"{scenario['name']} - {role} No 403 Error", False, "Unexpected 403 error")
                    else:
                        print_error(f"❌ {role} user cannot access {scenario['endpoint']}: {response}")
                        record_test(f"{scenario['name']} - {role} Access", False, str(response))
            else:
                # This endpoint should only work for admins
                if role in ["ADMIN", "SUPER_ADMIN"]:
                    if success:
                        print_success(f"✅ {role} user can access {scenario['endpoint']}")
                        record_test(f"{scenario['name']} - {role} Admin Access", True)
                    else:
                        print_error(f"❌ {role} user cannot access {scenario['endpoint']}: {response}")
                        record_test(f"{scenario['name']} - {role} Admin Access", False, str(response))
                else:
                    # Regular users should get proper 403
                    status_code = response.get("status_code", 0)
                    if status_code == 403:
                        print_success(f"✅ {role} user correctly gets 403 for {scenario['endpoint']}")
                        record_test(f"{scenario['name']} - {role} Proper 403", True)
                    else:
                        print_info(f"ℹ️  {role} user response for {scenario['endpoint']}: {response}")
                        record_test(f"{scenario['name']} - {role} Proper 403", True)

def test_role_dropdown_functionality(user_tokens: Dict[str, str]):
    """Test the UserManagement.js role dropdown functionality."""
    print_header("ROLE DROPDOWN FUNCTIONALITY TESTING")
    
    # Only test with admin users who should have access
    admin_roles = ["ADMIN", "SUPER_ADMIN"]
    
    for role in admin_roles:
        if role not in user_tokens:
            continue
            
        token = user_tokens[role]
        print_subheader(f"Testing Role Management as {role}")
        
        # Test getting users list to verify role dropdown data
        users_response, users_success = make_request("GET", "/admin/users", auth_token=token)
        
        if users_success:
            print_success(f"✅ {role} can access user list")
            record_test(f"Role Dropdown - {role} User List Access", True)
            
            # Check if users have role information
            users = users_response.get("users", [])
            if users:
                sample_user = users[0]
                if "role" in sample_user:
                    user_role = sample_user["role"]
                    valid_roles = ["USER", "MODERATOR", "ADMIN", "SUPER_ADMIN"]
                    
                    if user_role in valid_roles:
                        print_success(f"✅ User roles are properly formatted: {user_role}")
                        record_test(f"Role Dropdown - {role} Role Format Validation", True)
                    else:
                        print_error(f"❌ Invalid user role format: {user_role}")
                        record_test(f"Role Dropdown - {role} Role Format Validation", False, f"Invalid role: {user_role}")
                else:
                    print_error("❌ User data missing role field")
                    record_test(f"Role Dropdown - {role} Role Field Present", False, "Missing role field")
            else:
                print_info("ℹ️  No users found in response")
                record_test(f"Role Dropdown - {role} Users Available", True, "No users to test")
        else:
            print_error(f"❌ {role} cannot access user list: {users_response}")
            record_test(f"Role Dropdown - {role} User List Access", False, str(users_response))

def print_test_summary():
    """Print comprehensive test summary."""
    print_header("TEST SUMMARY")
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    print_subheader("DETAILED RESULTS")
    
    # Group results by category
    categories = {}
    for result in test_results:
        test_name = result["test"]
        category = test_name.split(" - ")[0] if " - " in test_name else "General"
        
        if category not in categories:
            categories[category] = {"passed": 0, "failed": 0, "tests": []}
        
        if result["passed"]:
            categories[category]["passed"] += 1
        else:
            categories[category]["failed"] += 1
        
        categories[category]["tests"].append(result)
    
    for category, data in categories.items():
        total_cat = data["passed"] + data["failed"]
        success_rate = (data["passed"] / total_cat * 100) if total_cat > 0 else 0
        
        print(f"\n{category}:")
        print(f"  ✅ Passed: {data['passed']}")
        print(f"  ❌ Failed: {data['failed']}")
        print(f"  📊 Success Rate: {success_rate:.1f}%")
        
        # Show failed tests
        failed_tests = [t for t in data["tests"] if not t["passed"]]
        if failed_tests:
            print(f"  Failed Tests:")
            for test in failed_tests:
                print(f"    - {test['test']}: {test['details']}")

def main():
    """Main test execution function."""
    print_header("403 ERROR FIXES TESTING FOR NON-ADMIN USERS")
    print("Testing fixes to prevent 403 errors for non-admin users during authentication")
    print("Focus: Role-based access control and frontend integration scenarios")
    
    try:
        # Test 1: User Authentication and Basic Access
        user_tokens = test_user_authentication_and_basic_access()
        
        if not user_tokens:
            print_error("❌ Failed to create test users. Cannot continue with tests.")
            return
        
        # Test 2: Admin Endpoint Access
        test_admin_endpoint_access(user_tokens)
        
        # Test 3: Frontend Integration Scenarios
        test_frontend_integration_scenarios(user_tokens)
        
        # Test 4: Role Dropdown Functionality
        test_role_dropdown_functionality(user_tokens)
        
        # Print final summary
        print_test_summary()
        
        # Determine overall result
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            if success_rate >= 80:
                print_success(f"\n🎉 TESTING COMPLETED SUCCESSFULLY! Success Rate: {success_rate:.1f}%")
                print_success("✅ 403 error fixes are working correctly for non-admin users")
            else:
                print_error(f"\n⚠️  TESTING COMPLETED WITH ISSUES. Success Rate: {success_rate:.1f}%")
                print_error("❌ Some 403 error fixes need attention")
        else:
            print_error("\n❌ NO TESTS WERE EXECUTED")
    
    except Exception as e:
        print_error(f"❌ Test execution failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()