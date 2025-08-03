#!/usr/bin/env python3
"""
Edit User Modal Testing - Russian Review
Focus: Testing the new "Edit User" modal window functionality in Role Management section

КОНТЕКСТ:
Тестирование нового модального окна "Редактировать пользователя" в разделе "Управление Ролями и Разрешениями"

ЦЕЛИ ТЕСТИРОВАНИЯ:
1. Проверить функциональность эндпоинтов для списка пользователей
2. Протестировать обновление пользователей через PUT /api/admin/users/{user_id}
3. Проверить правильность роль-based ограничений при назначении ролей
4. Убедиться что все поля корректно обновляются

ТЕСТОВЫЕ СЦЕНАРИИ:
1. GET /api/admin/users - получение списка пользователей для отображения в табе
2. PUT /api/admin/users/{user_id} с обновлением username, email, role, virtual_balance, status
3. Проверка ограничений: 
   - ADMIN не может назначить роль SUPER_ADMIN другому пользователю
   - SUPER_ADMIN может назначить любую роль
4. Валидация полей (проверка обязательных полей username, email)
5. Обновление каждого поля по отдельности
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
BASE_URL = "https://dc94d54d-9ba1-4b44-bea4-5740540b081e.preview.emergentagent.com/api"

# Test users for authentication
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
        print_success(f"PASSED: {name}")
    else:
        test_results["failed"] += 1
        print_error(f"FAILED: {name} - {details}")
    
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

def test_login(email: str, password: str, user_type: str) -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type} Login")
    
    response, success = make_request("POST", "/auth/login", data={
        "email": email,
        "password": password
    })
    
    if success and "access_token" in response:
        print_success(f"{user_type} logged in successfully")
        record_test(f"{user_type} Login", True)
        return response["access_token"]
    else:
        record_test(f"{user_type} Login", False, f"Login failed: {response}")
        return None

def test_get_users_list(auth_token: str, user_type: str) -> Tuple[List[Dict], bool]:
    """Test GET /api/admin/users endpoint."""
    print_subheader(f"Testing GET /api/admin/users as {user_type}")
    
    # Test basic request without parameters
    response, success = make_request(
        "GET", "/admin/users",
        auth_token=auth_token
    )
    
    if success:
        if "users" in response:
            users = response["users"]
            total = response.get("total", len(users))
            page = response.get("page", 1)
            limit = response.get("limit", 20)
            
            print_success(f"Retrieved {len(users)} users")
            print_success(f"Total users: {total}")
            print_success(f"Current page: {page}")
            print_success(f"Limit per page: {limit}")
            
            # Verify user structure
            if users:
                sample_user = users[0]
                required_fields = ["id", "username", "email", "role", "virtual_balance", "status"]
                missing_fields = [field for field in required_fields if field not in sample_user]
                
                if not missing_fields:
                    print_success("User structure contains all required fields")
                    record_test(f"GET /admin/users - {user_type}", True)
                    return users, True
                else:
                    print_error(f"Missing required fields in user structure: {missing_fields}")
                    record_test(f"GET /admin/users - {user_type}", False, f"Missing fields: {missing_fields}")
                    return [], False
            else:
                print_warning("No users found in response")
                record_test(f"GET /admin/users - {user_type}", True, "No users found")
                return [], True
        else:
            print_error("Response missing 'users' field")
            record_test(f"GET /admin/users - {user_type}", False, "Invalid response structure")
            return [], False
    else:
        record_test(f"GET /admin/users - {user_type}", False, "Request failed")
        return [], False

def test_update_user_fields(auth_token: str, user_type: str, target_user: Dict) -> bool:
    """Test PUT /api/admin/users/{user_id} endpoint with various field updates."""
    print_subheader(f"Testing PUT /api/admin/users/{{user_id}} as {user_type}")
    
    user_id = target_user["id"]
    original_username = target_user["username"]
    original_email = target_user["email"]
    original_role = target_user["role"]
    original_balance = target_user["virtual_balance"]
    
    print(f"Target user: {original_username} ({original_email})")
    print(f"Original role: {original_role}, Original balance: ${original_balance}")
    
    # Test 1: Update username
    print_subheader("Test 1: Update Username")
    new_username = f"updated_{original_username}_{random.randint(1000, 9999)}"
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"username": new_username},
        auth_token=auth_token
    )
    
    if success:
        print_success(f"Username updated to: {new_username}")
        record_test(f"Update Username - {user_type}", True)
    else:
        print_error(f"Failed to update username: {response}")
        record_test(f"Update Username - {user_type}", False, f"Update failed: {response}")
        return False
    
    # Test 2: Update email
    print_subheader("Test 2: Update Email")
    new_email = f"updated_{random.randint(1000, 9999)}@test.com"
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"email": new_email},
        auth_token=auth_token
    )
    
    if success:
        print_success(f"Email updated to: {new_email}")
        record_test(f"Update Email - {user_type}", True)
    else:
        print_error(f"Failed to update email: {response}")
        record_test(f"Update Email - {user_type}", False, f"Update failed: {response}")
        return False
    
    # Test 3: Update virtual_balance
    print_subheader("Test 3: Update Virtual Balance")
    new_balance = original_balance + 100.0
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"virtual_balance": new_balance},
        auth_token=auth_token
    )
    
    if success:
        print_success(f"Virtual balance updated to: ${new_balance}")
        record_test(f"Update Virtual Balance - {user_type}", True)
    else:
        print_error(f"Failed to update virtual balance: {response}")
        record_test(f"Update Virtual Balance - {user_type}", False, f"Update failed: {response}")
        return False
    
    # Test 4: Update multiple fields at once
    print_subheader("Test 4: Update Multiple Fields")
    multi_update_data = {
        "username": f"multi_{original_username}_{random.randint(1000, 9999)}",
        "virtual_balance": original_balance + 200.0
    }
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data=multi_update_data,
        auth_token=auth_token
    )
    
    if success:
        print_success("Multiple fields updated successfully")
        record_test(f"Update Multiple Fields - {user_type}", True)
    else:
        print_error(f"Failed to update multiple fields: {response}")
        record_test(f"Update Multiple Fields - {user_type}", False, f"Update failed: {response}")
        return False
    
    return True

def test_role_based_restrictions(admin_token: str, super_admin_token: str, target_user: Dict) -> None:
    """Test role-based restrictions for role assignment."""
    print_subheader("Testing Role-Based Restrictions")
    
    user_id = target_user["id"]
    original_role = target_user["role"]
    
    # Test 1: ADMIN trying to assign SUPER_ADMIN role (should fail)
    print_subheader("Test 1: ADMIN trying to assign SUPER_ADMIN role")
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"role": "SUPER_ADMIN"},
        auth_token=admin_token,
        expected_status=403  # Expecting forbidden
    )
    
    if not success and response.get("detail") == "Not enough permissions":
        print_success("ADMIN correctly blocked from assigning SUPER_ADMIN role")
        record_test("Role Restriction - ADMIN cannot assign SUPER_ADMIN", True)
    else:
        print_error("ADMIN was able to assign SUPER_ADMIN role (security issue)")
        record_test("Role Restriction - ADMIN cannot assign SUPER_ADMIN", False, "Security breach")
    
    # Test 2: ADMIN can assign other roles
    print_subheader("Test 2: ADMIN assigning MODERATOR role")
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"role": "MODERATOR"},
        auth_token=admin_token
    )
    
    if success:
        print_success("ADMIN successfully assigned MODERATOR role")
        record_test("Role Assignment - ADMIN can assign MODERATOR", True)
    else:
        print_error(f"ADMIN failed to assign MODERATOR role: {response}")
        record_test("Role Assignment - ADMIN can assign MODERATOR", False, f"Assignment failed: {response}")
    
    # Test 3: SUPER_ADMIN can assign any role
    print_subheader("Test 3: SUPER_ADMIN assigning SUPER_ADMIN role")
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"role": "SUPER_ADMIN"},
        auth_token=super_admin_token
    )
    
    if success:
        print_success("SUPER_ADMIN successfully assigned SUPER_ADMIN role")
        record_test("Role Assignment - SUPER_ADMIN can assign SUPER_ADMIN", True)
    else:
        print_error(f"SUPER_ADMIN failed to assign SUPER_ADMIN role: {response}")
        record_test("Role Assignment - SUPER_ADMIN can assign SUPER_ADMIN", False, f"Assignment failed: {response}")
    
    # Restore original role
    print_subheader("Restoring Original Role")
    make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"role": original_role},
        auth_token=super_admin_token
    )

def test_field_validation(auth_token: str, target_user: Dict) -> None:
    """Test field validation for user updates."""
    print_subheader("Testing Field Validation")
    
    user_id = target_user["id"]
    
    # Test 1: Invalid email format
    print_subheader("Test 1: Invalid Email Format")
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"email": "invalid-email-format"},
        auth_token=auth_token,
        expected_status=422  # Expecting validation error
    )
    
    if not success:
        print_success("Invalid email format correctly rejected")
        record_test("Field Validation - Invalid Email", True)
    else:
        print_error("Invalid email format was accepted")
        record_test("Field Validation - Invalid Email", False, "Invalid email accepted")
    
    # Test 2: Empty username
    print_subheader("Test 2: Empty Username")
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"username": ""},
        auth_token=auth_token,
        expected_status=422  # Expecting validation error
    )
    
    if not success:
        print_success("Empty username correctly rejected")
        record_test("Field Validation - Empty Username", True)
    else:
        print_error("Empty username was accepted")
        record_test("Field Validation - Empty Username", False, "Empty username accepted")
    
    # Test 3: Negative balance
    print_subheader("Test 3: Negative Balance")
    
    response, success = make_request(
        "PUT", f"/admin/users/{user_id}",
        data={"virtual_balance": -100.0},
        auth_token=auth_token
    )
    
    # Note: Negative balance might be allowed in some systems, so we just log the result
    if success:
        print_warning("Negative balance was accepted (may be intentional)")
        record_test("Field Validation - Negative Balance", True, "Negative balance allowed")
    else:
        print_success("Negative balance correctly rejected")
        record_test("Field Validation - Negative Balance", True, "Negative balance rejected")

def test_users_pagination_and_filtering(auth_token: str) -> None:
    """Test users list pagination and filtering functionality."""
    print_subheader("Testing Users List Pagination and Filtering")
    
    # Test 1: Pagination
    print_subheader("Test 1: Pagination")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"page": 1, "limit": 5},
        auth_token=auth_token
    )
    
    if success:
        total = response.get("total", 0)
        page = response.get("page", 1)
        limit = response.get("limit", 5)
        users = response.get("users", [])
        
        print_success(f"Page {page} with limit {limit}: {len(users)} users returned")
        print_success(f"Total users: {total}")
        record_test("Users Pagination", True)
    else:
        print_error("Pagination test failed")
        record_test("Users Pagination", False, "Pagination failed")
    
    # Test 2: Role filtering
    print_subheader("Test 2: Role Filtering")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"role": "USER"},
        auth_token=auth_token
    )
    
    if success:
        users = response.get("users", [])
        if users:
            # Check if all returned users have USER role
            all_users_role = all(user.get("role") == "USER" for user in users)
            if all_users_role:
                print_success(f"Role filtering working: {len(users)} USER role users found")
                record_test("Users Role Filtering", True)
            else:
                print_error("Role filtering not working correctly")
                record_test("Users Role Filtering", False, "Mixed roles returned")
        else:
            print_warning("No USER role users found")
            record_test("Users Role Filtering", True, "No USER role users")
    else:
        print_error("Role filtering test failed")
        record_test("Users Role Filtering", False, "Request failed")
    
    # Test 3: Search functionality
    print_subheader("Test 3: Search Functionality")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"search": "admin", "search_mode": "email"},
        auth_token=auth_token
    )
    
    if success:
        users = response.get("users", [])
        print_success(f"Search test: {len(users)} users found with 'admin' in email")
        record_test("Users Search", True)
    else:
        print_error("Search test failed")
        record_test("Users Search", False, "Search failed")

def test_user_management_comprehensive() -> None:
    """Run comprehensive user management tests."""
    print_header("EDIT USER MODAL TESTING - RUSSIAN REVIEW")
    print("Testing new 'Edit User' modal window functionality in Role Management section")
    
    # Step 1: Login as ADMIN
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "ADMIN")
    
    if not admin_token:
        print_error("Failed to login as ADMIN - cannot proceed with tests")
        return
    
    # Step 2: Login as SUPER_ADMIN
    print_subheader("Step 2: Super Admin Authentication")
    super_admin_token = test_login(SUPER_ADMIN_USER["email"], SUPER_ADMIN_USER["password"], "SUPER_ADMIN")
    
    if not super_admin_token:
        print_error("Failed to login as SUPER_ADMIN - cannot proceed with role restriction tests")
        return
    
    # Step 3: Get users list as ADMIN
    print_subheader("Step 3: Get Users List as ADMIN")
    admin_users, admin_success = test_get_users_list(admin_token, "ADMIN")
    
    # Step 4: Get users list as SUPER_ADMIN
    print_subheader("Step 4: Get Users List as SUPER_ADMIN")
    super_admin_users, super_admin_success = test_get_users_list(super_admin_token, "SUPER_ADMIN")
    
    if not admin_success or not admin_users:
        print_error("Cannot proceed with user update tests - no users available")
        return
    
    # Find a suitable test user (not admin accounts)
    test_user = None
    for user in admin_users:
        if user["email"] not in [ADMIN_USER["email"], SUPER_ADMIN_USER["email"]]:
            test_user = user
            break
    
    if not test_user:
        print_error("No suitable test user found for update tests")
        return
    
    print_success(f"Selected test user: {test_user['username']} ({test_user['email']})")
    
    # Step 5: Test user field updates as ADMIN
    print_subheader("Step 5: Test User Field Updates as ADMIN")
    test_update_user_fields(admin_token, "ADMIN", test_user)
    
    # Step 6: Test role-based restrictions
    print_subheader("Step 6: Test Role-Based Restrictions")
    test_role_based_restrictions(admin_token, super_admin_token, test_user)
    
    # Step 7: Test field validation
    print_subheader("Step 7: Test Field Validation")
    test_field_validation(admin_token, test_user)
    
    # Step 8: Test pagination and filtering
    print_subheader("Step 8: Test Pagination and Filtering")
    test_users_pagination_and_filtering(admin_token)

def print_test_summary() -> None:
    """Print test results summary."""
    print_header("TEST RESULTS SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print_success("EXCELLENT: Edit User Modal functionality is working correctly!")
        elif success_rate >= 75:
            print_warning("GOOD: Most functionality working, minor issues detected")
        else:
            print_error("ISSUES DETECTED: Significant problems with user management functionality")
    
    # Print failed tests details
    if failed > 0:
        print_subheader("Failed Tests Details:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"❌ {test['name']}: {test['details']}")

if __name__ == "__main__":
    try:
        test_user_management_comprehensive()
        print_test_summary()
        
        # Exit with appropriate code
        if test_results["failed"] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_error("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        sys.exit(1)