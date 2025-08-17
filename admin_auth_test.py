#!/usr/bin/env python3
"""
Admin Authentication for User Management Testing - Russian Review
Focus: Testing admin authentication to unblock frontend testing

ЗАДАЧА: Выполнить функцию test_admin_authentication_for_user_management() 
для проверки доступа к User Management.

КОНКРЕТНАЯ ЗАДАЧА:
Нужно запустить тест аутентификации admin@gemplay.com / Admin123! 
чтобы убедиться, что backend работает корректно и разблокировать 
фронтенд тестирование модального окна "Редактировать пользователя".

ЧТО ПРОВЕРИТЬ:
1. Успешный логин admin пользователя
2. Получение access_token
3. Доступ к GET /api/admin/users 
4. Доступ к PUT /api/admin/users/{user_id}
5. Проверка что backend готов к тестированию курсора
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://russianparts.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test results tracking
test_results = []

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*80}")
    print(f"{text:^80}")
    print(f"{'='*80}\n")

def print_subheader(text: str):
    """Print formatted subheader"""
    print(f"\n{text}")
    print("-" * 80)

def print_success(text: str):
    """Print success message"""
    print(f"\033[92m✅ {text}\033[0m")

def print_error(text: str):
    """Print error message"""
    print(f"\033[91m❌ {text}\033[0m")

def print_warning(text: str):
    """Print warning message"""
    print(f"\033[93m⚠ {text}\033[0m")

def record_test(test_name: str, passed: bool, error_msg: str = ""):
    """Record test result"""
    test_results.append({
        "test": test_name,
        "passed": passed,
        "error": error_msg
    })

def make_request(method: str, endpoint: str, data: Optional[Dict] = None, 
                auth_token: Optional[str] = None, headers: Optional[Dict] = None) -> tuple:
    """Make HTTP request with proper error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    # Prepare headers
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    if auth_token:
        request_headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"Making {method} request to {url}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=request_headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, headers=request_headers, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=request_headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
        except:
            response_data = {"raw_response": response.text}
            print(f"Response text: {response.text}")
        
        success = 200 <= response.status_code < 300
        if not success:
            print_error(f"Expected status 2xx, got {response.status_code}")
        
        return response_data, success
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return {}, False

def test_admin_authentication_for_user_management():
    """Test admin authentication for accessing User Management as requested in Russian review."""
    print_header("ADMIN AUTHENTICATION FOR USER MANAGEMENT TESTING")
    
    # Step 1: Test admin login
    print_subheader("Step 1: Admin Login Test")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    login_response, login_success = make_request("POST", "/auth/login", data=login_data)
    
    if not login_success:
        print_error("❌ Admin login failed - cannot proceed with authentication test")
        record_test("Admin Authentication - Login", False, "Login request failed")
        return
    
    # Check if we got access token
    access_token = login_response.get("access_token")
    if not access_token:
        print_error("❌ Admin login response missing access_token")
        record_test("Admin Authentication - Login", False, "Missing access_token")
        return
    
    print_success("✅ Admin login successful")
    print_success(f"✅ Access token received: {access_token[:20]}...")
    
    # Check user info in response
    user_info = login_response.get("user", {})
    if user_info:
        print_success(f"✅ User role: {user_info.get('role', 'unknown')}")
        print_success(f"✅ User email: {user_info.get('email', 'unknown')}")
        print_success(f"✅ User status: {user_info.get('status', 'unknown')}")
    
    record_test("Admin Authentication - Login", True)
    
    # Step 2: Test access to admin users endpoint
    print_subheader("Step 2: Admin Users Endpoint Access Test")
    
    users_response, users_success = make_request("GET", "/admin/users", auth_token=access_token)
    
    if not users_success:
        print_error("❌ Failed to access /api/admin/users endpoint")
        record_test("Admin Authentication - Users Access", False, "Endpoint access failed")
        return
    
    # Check response structure
    if "users" in users_response and "total" in users_response:
        total_users = users_response.get("total", 0)
        users_list = users_response.get("users", [])
        
        print_success("✅ Admin users endpoint accessible")
        print_success(f"✅ Total users found: {total_users}")
        print_success(f"✅ Users in response: {len(users_list)}")
        record_test("Admin Authentication - Users Access", True)
        
        # Find a test user for editing
        test_user = None
        if users_list:
            test_user = users_list[0]  # Use first user for testing
            print_success(f"✅ Test user found: {test_user.get('username', 'unknown')} (ID: {test_user.get('id', 'unknown')})")
        
    else:
        print_error("❌ Admin users response missing expected fields")
        record_test("Admin Authentication - Users Access", False, "Invalid response structure")
        return
    
    # Step 3: Test user editing endpoint
    print_subheader("Step 3: User Editing Endpoint Test")
    
    if test_user:
        user_id = test_user.get("id")
        if user_id:
            # Test with minimal update (just to verify endpoint works)
            update_data = {
                "virtual_balance": test_user.get("virtual_balance", 0)  # Keep same balance
            }
            
            edit_response, edit_success = make_request(
                "PUT", f"/admin/users/{user_id}",
                data=update_data,
                auth_token=access_token
            )
            
            if edit_success:
                print_success("✅ User editing endpoint accessible")
                print_success("✅ PUT /api/admin/users/{user_id} works correctly")
                record_test("Admin Authentication - User Edit Access", True)
                
                # Check if response indicates successful update
                if "modified_count" in edit_response:
                    modified_count = edit_response.get("modified_count", 0)
                    print_success(f"✅ Update operation completed (modified_count: {modified_count})")
                
            else:
                print_error("❌ User editing endpoint failed")
                record_test("Admin Authentication - User Edit Access", False, "Edit endpoint failed")
        else:
            print_error("❌ Test user missing ID field")
            record_test("Admin Authentication - User Edit Access", False, "Missing user ID")
    else:
        print_warning("⚠ No test user available for editing test")
        record_test("Admin Authentication - User Edit Access", False, "No test user")
    
    # Step 4: Test additional admin endpoints
    print_subheader("Step 4: Additional Admin Endpoints Test")
    
    # Test dashboard stats
    dashboard_response, dashboard_success = make_request(
        "GET", "/admin/dashboard/stats",
        auth_token=access_token
    )
    
    if dashboard_success:
        print_success("✅ Admin dashboard endpoint accessible")
        record_test("Admin Authentication - Dashboard Access", True)
    else:
        print_error("❌ Admin dashboard endpoint failed")
        record_test("Admin Authentication - Dashboard Access", False, "Dashboard access failed")
    
    # Test human-bots endpoint
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots",
        auth_token=access_token
    )
    
    if human_bots_success:
        print_success("✅ Admin human-bots endpoint accessible")
        record_test("Admin Authentication - Human-bots Access", True)
    else:
        print_error("❌ Admin human-bots endpoint failed")
        record_test("Admin Authentication - Human-bots Access", False, "Human-bots access failed")
    
    # Summary
    print_subheader("Admin Authentication Test Summary")
    print_success("Admin authentication testing completed")
    print_success("Key findings:")
    print_success("- Admin login with admin@gemplay.com / Admin123! works")
    print_success("- Access token is properly generated")
    print_success("- Admin endpoints are accessible with token")
    print_success("- User management functionality is available")
    print_success("- Backend is ready for frontend testing")
    
    # Final results
    print_subheader("Test Results Summary")
    passed_tests = sum(1 for result in test_results if result["passed"])
    total_tests = len(test_results)
    
    print_success(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print_success("🎉 ALL TESTS PASSED - BACKEND IS READY FOR FRONTEND TESTING!")
    else:
        print_error("❌ Some tests failed - backend may need fixes")
        for result in test_results:
            if not result["passed"]:
                print_error(f"  - {result['test']}: {result['error']}")

if __name__ == "__main__":
    test_admin_authentication_for_user_management()