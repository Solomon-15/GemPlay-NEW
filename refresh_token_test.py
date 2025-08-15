#!/usr/bin/env python3
"""
REFRESH TOKEN FLOW TESTING - Russian Review Request
Протестировать обновление токена (refresh flow) и отсутствие самопроизвольного разлогина

BACKEND TESTS:
1) POST /api/auth/refresh (JSON): {"refresh_token":"<valid>"}
   - Ожидаю: 200 OK, JSON содержит access_token, refresh_token (новый), user
2) POST /api/auth/refresh с отсутствующим полем
   - Ожидаю: 400 Bad Request (Missing refresh_token)
3) POST /api/auth/refresh с невалидным refresh_token
   - Ожидаю: 401 Unauthorized (Invalid or expired refresh token)
4) Проверить, что старый refresh_token деактивирован после успешного обновления (повторный refresh со старым -> 401)
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
from datetime import datetime
import concurrent.futures

# Configuration
BASE_URL = "https://slavic-ai.preview.emergentagent.com/api"

# Admin user credentials for testing
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

def authenticate_admin() -> Optional[Tuple[str, str]]:
    """Authenticate admin user and return access_token and refresh_token"""
    print(f"{Colors.BLUE}👤 Authenticating admin user for refresh token testing...{Colors.END}")
    
    # Try to login with admin user
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=login_data
    )
    
    if success and response_data and "access_token" in response_data:
        access_token = response_data["access_token"]
        refresh_token = response_data.get("refresh_token")
        
        print(f"{Colors.GREEN}✅ Admin user authenticated successfully{Colors.END}")
        print(f"   Access token: {access_token[:20]}...")
        print(f"   Refresh token: {refresh_token[:20] if refresh_token else 'None'}...")
        
        return access_token, refresh_token
    else:
        print(f"{Colors.RED}❌ Failed to authenticate admin user: {details}{Colors.END}")
        return None, None

def test_refresh_token_valid():
    """Test 1: POST /api/auth/refresh с валидным refresh_token"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Valid Refresh Token{Colors.END}")
    
    # Get valid tokens first
    access_token, refresh_token = authenticate_admin()
    if not refresh_token:
        record_test("Valid Refresh Token Test", False, "Failed to get valid refresh token")
        return None, None, None
    
    print(f"   📝 Testing POST /api/auth/refresh with valid refresh_token...")
    
    # Test refresh endpoint with valid token
    refresh_data = {"refresh_token": refresh_token}
    
    success, response_data, details = make_request(
        "POST",
        "/auth/refresh",
        data=refresh_data
    )
    
    if success and response_data:
        # Check response structure
        has_access_token = "access_token" in response_data
        has_refresh_token = "refresh_token" in response_data
        has_user = "user" in response_data
        
        new_access_token = response_data.get("access_token")
        new_refresh_token = response_data.get("refresh_token")
        
        if has_access_token and has_refresh_token and has_user:
            record_test(
                "Valid Refresh Token Test",
                True,
                f"200 OK, got new access_token and refresh_token, user data included"
            )
            return new_access_token, new_refresh_token, refresh_token  # Return old refresh token too
        else:
            missing_fields = []
            if not has_access_token: missing_fields.append("access_token")
            if not has_refresh_token: missing_fields.append("refresh_token")
            if not has_user: missing_fields.append("user")
            
            record_test(
                "Valid Refresh Token Test",
                False,
                f"Response missing fields: {', '.join(missing_fields)}"
            )
    else:
        record_test(
            "Valid Refresh Token Test",
            False,
            f"Refresh failed: {details}"
        )
    
    return None, None, None

def test_refresh_token_missing_field():
    """Test 2: POST /api/auth/refresh с отсутствующим полем refresh_token"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Missing refresh_token Field{Colors.END}")
    
    print(f"   📝 Testing POST /api/auth/refresh without refresh_token field...")
    
    # Test refresh endpoint without refresh_token field
    empty_data = {}
    
    success, response_data, details = make_request(
        "POST",
        "/auth/refresh",
        data=empty_data
    )
    
    # Should get 400 Bad Request
    if not success and "400" in details:
        # Check if error message mentions missing refresh_token
        error_msg = str(response_data).lower()
        if "refresh_token" in error_msg or "missing" in error_msg:
            record_test(
                "Missing refresh_token Field Test",
                True,
                f"400 Bad Request with appropriate error message: {response_data}"
            )
        else:
            record_test(
                "Missing refresh_token Field Test",
                False,
                f"400 Bad Request but unclear error message: {response_data}"
            )
    else:
        record_test(
            "Missing refresh_token Field Test",
            False,
            f"Expected 400 Bad Request, got: {details}"
        )

def test_refresh_token_invalid():
    """Test 3: POST /api/auth/refresh с невалидным refresh_token"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Invalid refresh_token{Colors.END}")
    
    print(f"   📝 Testing POST /api/auth/refresh with invalid refresh_token...")
    
    # Test refresh endpoint with invalid token
    invalid_refresh_data = {"refresh_token": "invalid_token_12345"}
    
    success, response_data, details = make_request(
        "POST",
        "/auth/refresh",
        data=invalid_refresh_data
    )
    
    # Should get 401 Unauthorized
    if not success and "401" in details:
        # Check if error message mentions invalid or expired token
        error_msg = str(response_data).lower()
        if any(keyword in error_msg for keyword in ["invalid", "expired", "unauthorized"]):
            record_test(
                "Invalid refresh_token Test",
                True,
                f"401 Unauthorized with appropriate error message: {response_data}"
            )
        else:
            record_test(
                "Invalid refresh_token Test",
                False,
                f"401 Unauthorized but unclear error message: {response_data}"
            )
    else:
        record_test(
            "Invalid refresh_token Test",
            False,
            f"Expected 401 Unauthorized, got: {details}"
        )

def test_old_refresh_token_deactivation(old_refresh_token: str):
    """Test 4: Проверить что старый refresh_token деактивирован"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Old refresh_token Deactivation{Colors.END}")
    
    if not old_refresh_token:
        record_test("Old refresh_token Deactivation Test", False, "No old refresh token available")
        return
    
    print(f"   📝 Testing POST /api/auth/refresh with old (should be deactivated) refresh_token...")
    
    # Try to use the old refresh token
    old_refresh_data = {"refresh_token": old_refresh_token}
    
    success, response_data, details = make_request(
        "POST",
        "/auth/refresh",
        data=old_refresh_data
    )
    
    # Should get 401 Unauthorized because old token should be deactivated
    if not success and "401" in details:
        error_msg = str(response_data).lower()
        if any(keyword in error_msg for keyword in ["invalid", "expired", "unauthorized"]):
            record_test(
                "Old refresh_token Deactivation Test",
                True,
                f"401 Unauthorized - old refresh token correctly deactivated: {response_data}"
            )
        else:
            record_test(
                "Old refresh_token Deactivation Test",
                False,
                f"401 Unauthorized but unclear error message: {response_data}"
            )
    else:
        record_test(
            "Old refresh_token Deactivation Test",
            False,
            f"Expected 401 Unauthorized (old token should be deactivated), got: {details}"
        )

def test_concurrent_401_handling():
    """Test 5: Симуляция одновременных запросов получающих 401"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: Concurrent 401 Handling Simulation{Colors.END}")
    
    # Get valid tokens first
    access_token, refresh_token = authenticate_admin()
    if not access_token or not refresh_token:
        record_test("Concurrent 401 Handling Test", False, "Failed to get valid tokens")
        return
    
    print(f"   📝 Simulating 5 concurrent requests with expired access token...")
    
    # Create an intentionally expired/invalid access token for testing
    invalid_access_token = "expired_token_12345"
    headers = {"Authorization": f"Bearer {invalid_access_token}"}
    
    # Function to make a request that should get 401
    def make_401_request(request_id):
        success, response_data, details = make_request(
            "GET",
            "/user/profile",  # Protected endpoint
            headers=headers
        )
        return {
            "request_id": request_id,
            "success": success,
            "status_code": details.split(",")[0] if details else "unknown",
            "response": response_data
        }
    
    # Make 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_401_request, i+1) for i in range(5)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    unauthorized_count = sum(1 for result in results if "401" in result["status_code"])
    
    print(f"   📊 Results: {unauthorized_count}/5 requests got 401 Unauthorized")
    
    if unauthorized_count == 5:
        record_test(
            "Concurrent 401 Handling Test",
            True,
            f"All 5 concurrent requests correctly returned 401 Unauthorized with expired token"
        )
        
        # Now test if refresh token still works after concurrent 401s
        print(f"   📝 Testing if refresh token still works after concurrent 401s...")
        
        refresh_data = {"refresh_token": refresh_token}
        success, response_data, details = make_request(
            "POST",
            "/auth/refresh",
            data=refresh_data
        )
        
        if success and response_data and "access_token" in response_data:
            record_test(
                "Refresh After Concurrent 401s Test",
                True,
                "Refresh token still works correctly after concurrent 401 responses"
            )
        else:
            record_test(
                "Refresh After Concurrent 401s Test",
                False,
                f"Refresh token failed after concurrent 401s: {details}"
            )
    else:
        record_test(
            "Concurrent 401 Handling Test",
            False,
            f"Expected 5/5 requests to get 401, got {unauthorized_count}/5"
        )

def print_refresh_token_summary():
    """Print refresh token testing summary"""
    print_header("REFRESH TOKEN FLOW TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 RUSSIAN REVIEW REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each requirement
    requirements = [
        ("1. POST /api/auth/refresh с валидным токеном", "valid refresh token"),
        ("2. POST /api/auth/refresh с отсутствующим полем", "missing refresh_token field"),
        ("3. POST /api/auth/refresh с невалидным токеном", "invalid refresh_token"),
        ("4. Старый refresh_token деактивирован", "old refresh_token deactivation"),
        ("5. Одновременные 401 запросы", "concurrent 401 handling")
    ]
    
    for req_name, test_keyword in requirements:
        test = next((test for test in test_results["tests"] if test_keyword in test["name"].lower()), None)
        if test:
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
            print(f"   {req_name}: {status}")
            if test["details"]:
                print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
        else:
            print(f"   {req_name}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: REFRESH TOKEN FLOW FULLY OPERATIONAL!{Colors.END}")
        print(f"{Colors.GREEN}✅ Валидный refresh token работает корректно{Colors.END}")
        print(f"{Colors.GREEN}✅ Отсутствующие поля обрабатываются правильно (400){Colors.END}")
        print(f"{Colors.GREEN}✅ Невалидные токены отклоняются (401){Colors.END}")
        print(f"{Colors.GREEN}✅ Старые токены деактивируются после обновления{Colors.END}")
        print(f"{Colors.GREEN}✅ Одновременные 401 запросы обрабатываются корректно{Colors.END}")
        print(f"{Colors.GREEN}✅ Полный refresh flow работает без самопроизвольного разлогина{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: REFRESH TOKEN MOSTLY WORKING ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Основная функциональность refresh token работает, есть минорные проблемы.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL REFRESH TOKEN FUNCTIONALITY ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые аспекты refresh token работают, требуется дополнительная работа.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: REFRESH TOKEN FLOW HAS CRITICAL ISSUES ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Refresh token flow НЕ работает корректно. Требуется срочное исправление.{Colors.END}")

def main():
    """Main test execution for Refresh Token Flow"""
    print_header("REFRESH TOKEN FLOW TESTING - RUSSIAN REVIEW")
    print(f"{Colors.BLUE}🎯 Testing refresh token flow and preventing self-logout{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}👤 Test User: {ADMIN_USER['email']}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Testing all refresh token scenarios from Russian review{Colors.END}")
    
    try:
        # Test 1: Valid refresh token
        new_access_token, new_refresh_token, old_refresh_token = test_refresh_token_valid()
        
        # Test 2: Missing refresh_token field
        test_refresh_token_missing_field()
        
        # Test 3: Invalid refresh_token
        test_refresh_token_invalid()
        
        # Test 4: Old refresh_token deactivation (if we have old token)
        if old_refresh_token:
            test_old_refresh_token_deactivation(old_refresh_token)
        
        # Test 5: Concurrent 401 handling
        test_concurrent_401_handling()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_refresh_token_summary()

if __name__ == "__main__":
    main()