#!/usr/bin/env python3
"""
LOGIN ENDPOINT AUTHENTICATION TESTING - Russian Review
Тестирование работы login endpoint для пользователя admin@gemplay.com

ПРОБЛЕМА: Frontend не может авторизоваться - остается на странице логина даже после нажатия кнопки LOGIN.
Backend URL настроен как внешний: https://53b51271-d84e-45ed-b769-9b3ed6d4038f.preview.emergentagent.com

ТЕСТИРОВАТЬ:
1. Проверить доступность login endpoint
2. Проверить авторизацию админа admin@gemplay.com с паролем Admin123!
3. Проверить /auth/me endpoint  
4. Убедиться что токен возвращается правильно
5. Выполнить полную проверку auth процесса чтобы понять почему не работает логин в интерфейсе

ПРИОРИТЕТ: Критически важно - пользователь не может войти в систему
ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ: Login должен работать корректно, токен должен возвращаться, /auth/me должен работать
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
BASE_URL = "https://53b51271-d84e-45ed-b769-9b3ed6d4038f.preview.emergentagent.com/api"
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
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with colors"""
    status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if success else f"{Colors.RED}❌ FAILED{Colors.END}"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {Colors.YELLOW}Details: {details}{Colors.END}")

def record_test(test_name: str, success: bool, details: str = "", response_data: Any = None):
    """Record test result"""
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": test_name,
        "success": success,
        "details": details,
        "response_data": response_data,
        "timestamp": datetime.now().isoformat()
    })
    
    print_test_result(test_name, success, details)

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str]:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return False, None, f"Unsupported method: {method}"
        
        response_time = time.time() - start_time
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        success = response.status_code in [200, 201]
        details = f"Status: {response.status_code}, Time: {response_time:.3f}s"
        
        if not success:
            details += f", Error: {response_data}"
        
        return success, response_data, details
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout (30s)"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error"
    except Exception as e:
        return False, None, f"Request error: {str(e)}"

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as admin user...{Colors.END}")
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print(f"{Colors.GREEN}✅ Admin authentication successful{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Admin authentication failed: {details}{Colors.END}")
        return None

def generate_unique_bot_name() -> str:
    """Generate unique bot name for testing"""
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"TestRegularBot_{timestamp}_{random_suffix}"

def test_login_endpoint_availability():
    """Test 1: Проверить доступность login endpoint"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Testing login endpoint availability{Colors.END}")
    
    # Test endpoint availability with OPTIONS request first
    url = f"{BASE_URL}/auth/login"
    
    try:
        # Test with OPTIONS to check CORS
        options_response = requests.options(url, timeout=10)
        print(f"   OPTIONS /auth/login: {options_response.status_code}")
        
        # Test with GET to see if endpoint exists (should return 405 Method Not Allowed)
        get_response = requests.get(url, timeout=10)
        print(f"   GET /auth/login: {get_response.status_code}")
        
        # Endpoint should exist (not 404)
        if options_response.status_code != 404 and get_response.status_code != 404:
            record_test(
                "Login endpoint availability",
                True,
                f"Endpoint exists - OPTIONS: {options_response.status_code}, GET: {get_response.status_code}"
            )
        else:
            record_test(
                "Login endpoint availability", 
                False,
                f"Endpoint not found - OPTIONS: {options_response.status_code}, GET: {get_response.status_code}"
            )
            
    except requests.exceptions.Timeout:
        record_test("Login endpoint availability", False, "Request timeout (10s)")
    except requests.exceptions.ConnectionError:
        record_test("Login endpoint availability", False, "Connection error - endpoint unreachable")
    except Exception as e:
        record_test("Login endpoint availability", False, f"Request error: {str(e)}")

def test_admin_login_authentication():
    """Test 2: Проверить авторизацию админа admin@gemplay.com"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Testing admin authentication{Colors.END}")
    
    login_data = {
        "email": "admin@gemplay.com",
        "password": "Admin123!"
    }
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=login_data
    )
    
    if success and response_data:
        # Check for required fields in response
        has_access_token = "access_token" in response_data
        has_token_type = "token_type" in response_data
        has_user = "user" in response_data
        
        if has_access_token and has_token_type:
            # Check user role
            user_data = response_data.get("user", {})
            user_role = user_data.get("role", "")
            user_email = user_data.get("email", "")
            
            if user_role in ["ADMIN", "SUPER_ADMIN"] and user_email == "admin@gemplay.com":
                record_test(
                    "Admin authentication",
                    True,
                    f"Successfully authenticated admin with role: {user_role}, token_type: {response_data.get('token_type')}"
                )
                return response_data.get("access_token")
            else:
                record_test(
                    "Admin authentication",
                    False,
                    f"Authentication successful but wrong role/email: role={user_role}, email={user_email}"
                )
        else:
            record_test(
                "Admin authentication",
                False,
                f"Missing required fields in response. Has token: {has_access_token}, Has type: {has_token_type}"
            )
    else:
        record_test(
            "Admin authentication",
            False,
            f"Login failed: {details}"
        )
    
    return None

def test_auth_me_endpoint(token: str):
    """Test 3: Проверить /auth/me endpoint"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Testing /auth/me endpoint{Colors.END}")
    
    if not token:
        record_test("Auth me endpoint", False, "No token available for testing")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/auth/me",
        headers=headers
    )
    
    if success and response_data:
        # Check user data structure
        required_fields = ["id", "email", "role", "username"]
        found_fields = [field for field in required_fields if field in response_data]
        
        user_email = response_data.get("email", "")
        user_role = response_data.get("role", "")
        
        if len(found_fields) >= 3 and user_email == "admin@gemplay.com":
            record_test(
                "Auth me endpoint",
                True,
                f"Successfully retrieved user data: email={user_email}, role={user_role}, fields={found_fields}"
            )
        else:
            record_test(
                "Auth me endpoint",
                False,
                f"Invalid user data: email={user_email}, found_fields={found_fields}"
            )
    else:
        record_test(
            "Auth me endpoint",
            False,
            f"Failed to get user data: {details}"
        )

def test_token_format_and_validity(token: str):
    """Test 4: Проверить формат и валидность токена"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Testing token format and validity{Colors.END}")
    
    if not token:
        record_test("Token format and validity", False, "No token available for testing")
        return
    
    # Check token format (JWT should have 3 parts separated by dots)
    token_parts = token.split('.')
    
    if len(token_parts) == 3:
        # Token has correct JWT format
        token_length = len(token)
        
        # Test token with a simple authenticated endpoint
        headers = {"Authorization": f"Bearer {token}"}
        success, response_data, details = make_request(
            "GET",
            "/auth/me",
            headers=headers
        )
        
        if success:
            record_test(
                "Token format and validity",
                True,
                f"Token is valid JWT format (3 parts, {token_length} chars) and works with API"
            )
        else:
            record_test(
                "Token format and validity",
                False,
                f"Token has correct format but fails API validation: {details}"
            )
    else:
        record_test(
            "Token format and validity",
            False,
            f"Token has invalid format: {len(token_parts)} parts instead of 3 (JWT standard)"
        )

def test_cors_headers():
    """Test 5: Проверить CORS headers для frontend"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: Testing CORS headers{Colors.END}")
    
    url = f"{BASE_URL}/auth/login"
    
    try:
        # Test OPTIONS request with Origin header (simulating frontend request)
        headers = {
            "Origin": "https://53b51271-d84e-45ed-b769-9b3ed6d4038f.preview.emergentagent.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        
        response = requests.options(url, headers=headers, timeout=10)
        
        # Check CORS headers in response
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
        }
        
        has_cors_origin = cors_headers["Access-Control-Allow-Origin"] is not None
        has_cors_methods = cors_headers["Access-Control-Allow-Methods"] is not None
        
        if has_cors_origin and has_cors_methods:
            record_test(
                "CORS headers",
                True,
                f"CORS properly configured: Origin={cors_headers['Access-Control-Allow-Origin']}, Methods={cors_headers['Access-Control-Allow-Methods']}"
            )
        else:
            record_test(
                "CORS headers",
                False,
                f"CORS headers missing or incomplete: {cors_headers}"
            )
            
    except Exception as e:
        record_test("CORS headers", False, f"Error testing CORS: {str(e)}")

def test_login_with_wrong_credentials():
    """Test 6: Проверить обработку неверных учетных данных"""
    print(f"\n{Colors.MAGENTA}🧪 Test 6: Testing login with wrong credentials{Colors.END}")
    
    # Test with wrong password
    wrong_data = {
        "email": "admin@gemplay.com",
        "password": "WrongPassword123!"
    }
    
    success, response_data, details = make_request(
        "POST",
        "/auth/login", 
        data=wrong_data
    )
    
    # Should fail with proper error message
    if not success:
        # Check if it's a proper authentication error (401 or 400)
        if "401" in details or "400" in details or "Invalid" in str(response_data):
            record_test(
                "Login with wrong credentials",
                True,
                f"Correctly rejected wrong credentials: {details}"
            )
        else:
            record_test(
                "Login with wrong credentials",
                False,
                f"Wrong credentials rejected but with unexpected error: {details}"
            )
    else:
        record_test(
            "Login with wrong credentials",
            False,
            "Should have rejected wrong credentials but login succeeded"
        )

def test_admin_panel_access(token: str):
    """Test 7: Проверить доступ к админ-панели с полученным токеном"""
    print(f"\n{Colors.MAGENTA}🧪 Test 7: Testing admin panel access{Colors.END}")
    
    if not token:
        record_test("Admin panel access", False, "No token available for testing")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test access to admin endpoints
    admin_endpoints = [
        "/admin/dashboard",
        "/admin/users",
        "/admin/bots"
    ]
    
    successful_endpoints = []
    failed_endpoints = []
    
    for endpoint in admin_endpoints:
        success, response_data, details = make_request(
            "GET",
            endpoint,
            headers=headers
        )
        
        if success:
            successful_endpoints.append(endpoint)
        else:
            failed_endpoints.append(f"{endpoint}: {details}")
    
    if len(successful_endpoints) >= 2:
        record_test(
            "Admin panel access",
            True,
            f"Successfully accessed {len(successful_endpoints)} admin endpoints: {successful_endpoints}"
        )
    else:
        record_test(
            "Admin panel access",
            False,
            f"Failed to access admin endpoints. Success: {successful_endpoints}, Failed: {failed_endpoints}"
        )

def test_complete_auth_flow():
    """Test 8: Полный тест auth flow как в frontend"""
    print(f"\n{Colors.MAGENTA}🧪 Test 8: Testing complete auth flow (frontend simulation){Colors.END}")
    
    # Step 1: Login
    login_data = {
        "email": "admin@gemplay.com", 
        "password": "Admin123!"
    }
    
    success, login_response, details = make_request(
        "POST",
        "/auth/login",
        data=login_data
    )
    
    if not success or not login_response:
        record_test(
            "Complete auth flow",
            False,
            f"Step 1 (Login) failed: {details}"
        )
        return
    
    token = login_response.get("access_token")
    if not token:
        record_test(
            "Complete auth flow",
            False,
            "Step 1 (Login) succeeded but no access_token in response"
        )
        return
    
    # Step 2: Verify token with /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    success, me_response, details = make_request(
        "GET",
        "/auth/me",
        headers=headers
    )
    
    if not success or not me_response:
        record_test(
            "Complete auth flow",
            False,
            f"Step 2 (/auth/me) failed: {details}"
        )
        return
    
    # Step 3: Access admin panel
    success, admin_response, details = make_request(
        "GET",
        "/admin/dashboard",
        headers=headers
    )
    
    if success:
        record_test(
            "Complete auth flow",
            True,
            "Complete auth flow successful: Login → Token → /auth/me → Admin access"
        )
    else:
        record_test(
            "Complete auth flow",
            False,
            f"Step 3 (Admin access) failed: {details}"
        )

def print_auth_summary():
    """Print authentication-specific summary"""
    print_header("LOGIN ENDPOINT AUTHENTICATION TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 AUTHENTICATION REQUIREMENTS STATUS:{Colors.END}")
    
    requirements = [
        "Login endpoint доступность",
        "Авторизация admin@gemplay.com / Admin123!",
        "/auth/me endpoint функциональность",
        "Токен формат и валидность",
        "CORS headers для frontend",
        "Обработка неверных учетных данных",
        "Доступ к админ-панели",
        "Полный auth flow"
    ]
    
    for i, req in enumerate(requirements, 1):
        # Find corresponding test result
        test_found = False
        for test in test_results["tests"]:
            if str(i) in test["name"] or any(keyword in test["name"].lower() for keyword in req.lower().split()[:2]):
                status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
                print(f"   {i}. {req}: {status}")
                test_found = True
                break
        
        if not test_found:
            print(f"   {i}. {req}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Specific conclusion for auth issues
    if success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: LOGIN SYSTEM IS {success_rate:.1f}% FUNCTIONAL!{Colors.END}")
        print(f"{Colors.GREEN}Authentication is working correctly. Frontend login issues may be due to client-side problems.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: LOGIN SYSTEM HAS ISSUES ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Some authentication components are working but there are issues that need attention.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: LOGIN SYSTEM NEEDS IMMEDIATE ATTENTION ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Critical authentication issues found that prevent proper login functionality.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR FRONTEND LOGIN ISSUES:{Colors.END}")
    
    # Check specific failure patterns
    login_test = next((test for test in test_results["tests"] if "authentication" in test["name"].lower()), None)
    me_test = next((test for test in test_results["tests"] if "auth me" in test["name"].lower()), None)
    cors_test = next((test for test in test_results["tests"] if "cors" in test["name"].lower()), None)
    
    if login_test and not login_test["success"]:
        print(f"   🔴 Login endpoint is failing - check backend server status")
    elif me_test and not me_test["success"]:
        print(f"   🔴 Token validation is failing - check JWT configuration")
    elif cors_test and not cors_test["success"]:
        print(f"   🔴 CORS issues detected - check CORS middleware configuration")
    else:
        print(f"   🟢 Backend authentication appears to be working")
        print(f"   🔍 Check frontend console for JavaScript errors")
        print(f"   🔍 Check network tab for failed requests")
        print(f"   🔍 Verify frontend is using correct backend URL")

def main():
    """Main test execution for authentication"""
    print_header("LOGIN ENDPOINT AUTHENTICATION TESTING")
    print(f"{Colors.BLUE}🎯 Testing login functionality for admin@gemplay.com{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Login endpoint, token validation, admin access{Colors.END}")
    
    # Store token for subsequent tests
    admin_token = None
    
    try:
        # Run all authentication tests
        test_login_endpoint_availability()
        admin_token = test_admin_login_authentication()
        test_auth_me_endpoint(admin_token)
        test_token_format_and_validity(admin_token)
        test_cors_headers()
        test_login_with_wrong_credentials()
        test_admin_panel_access(admin_token)
        test_complete_auth_flow()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_auth_summary()

if __name__ == "__main__":
    main()