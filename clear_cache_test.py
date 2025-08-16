#!/usr/bin/env python3
"""
CLEAR CACHE ENDPOINT TESTING - Russian Review
Тестирование endpoint очистки кэша в админ панели

ПРОБЛЕМА ИЗ ТЕСТ РЕЗУЛЬТАТОВ:
- Frontend сообщает что получает HTTP 500 error
- API response содержит invalid JSON format
- Нужно выяснить что вызывает эту ошибку

ТЕСТИРОВАНИЕ:
1. POST /api/admin/cache/clear
2. Нужна админ авторизация
3. Должен возвращать успешный ответ с очищенными типами кэша
4. Логировать все ошибки если они есть

ПРОВЕРИТЬ:
- Работает ли endpoint вообще
- Корректный ли JSON ответ
- Есть ли ошибки в логах
- Правильная ли авторизация

Используй admin@gemplay.com / Admin123! для входа
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://russian-commission.preview.emergentagent.com/api"
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

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str, int]:
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
            return False, None, f"Unsupported method: {method}", 0
        
        response_time = time.time() - start_time
        status_code = response.status_code
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            json_valid = True
        except json.JSONDecodeError as e:
            response_data = response.text
            json_valid = False
            print(f"   {Colors.RED}⚠️ JSON Parse Error: {str(e)}{Colors.END}")
            print(f"   {Colors.RED}Raw Response: {response_data[:500]}...{Colors.END}")
        except Exception as e:
            response_data = response.text
            json_valid = False
            print(f"   {Colors.RED}⚠️ Response Parse Error: {str(e)}{Colors.END}")
        
        success = response.status_code in [200, 201]
        details = f"Status: {status_code}, Time: {response_time:.3f}s, JSON Valid: {json_valid}"
        
        if not success:
            details += f", Error: {response_data}"
        
        return success, response_data, details, status_code
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout (30s)", 0
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error", 0
    except Exception as e:
        return False, None, f"Request error: {str(e)}", 0

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as admin user...{Colors.END}")
    
    success, response_data, details, status_code = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        user_role = response_data.get("user", {}).get("role", "Unknown")
        print(f"{Colors.GREEN}✅ Admin authentication successful - Role: {user_role}{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Admin authentication failed: {details}{Colors.END}")
        return None

def test_clear_cache_endpoint():
    """Test 1: POST /api/admin/cache/clear endpoint"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Testing Clear Cache Endpoint{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Clear Cache Endpoint - Authentication", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing POST /api/admin/cache/clear with admin authorization")
    
    # Test the clear cache endpoint
    success, response_data, details, status_code = make_request(
        "POST",
        "/admin/cache/clear",
        headers=headers
    )
    
    print(f"   📊 Response Analysis:")
    print(f"      Status Code: {status_code}")
    print(f"      Success: {success}")
    print(f"      Response Type: {type(response_data)}")
    
    if isinstance(response_data, dict):
        print(f"      Response Keys: {list(response_data.keys())}")
        print(f"      Response Data: {json.dumps(response_data, indent=2)}")
    else:
        print(f"      Raw Response: {str(response_data)[:500]}...")
    
    # Check for specific issues mentioned in test_result.md
    issues_found = []
    
    if status_code == 500:
        issues_found.append("HTTP 500 Internal Server Error")
    
    if not success:
        issues_found.append(f"Request failed with status {status_code}")
    
    if isinstance(response_data, str) and not isinstance(response_data, dict):
        issues_found.append("Response is not valid JSON")
    
    if success and isinstance(response_data, dict):
        # Check for expected cache clearing response structure
        expected_fields = ["success", "message", "cache_types_cleared"]
        missing_fields = [field for field in expected_fields if field not in response_data]
        
        if missing_fields:
            issues_found.append(f"Missing expected fields: {missing_fields}")
        
        if response_data.get("success") is True:
            print(f"   ✅ Cache clearing reported as successful")
            if "cache_types_cleared" in response_data:
                cache_types = response_data["cache_types_cleared"]
                print(f"   📋 Cleared cache types: {cache_types}")
                print(f"   📊 Total cache types cleared: {response_data.get('cleared_count', 0)}")
        else:
            issues_found.append("Response indicates cache clearing failed")
    
    if not issues_found:
        record_test(
            "Clear Cache Endpoint - Functionality",
            True,
            f"Cache clear endpoint working correctly. Status: {status_code}, Response valid JSON"
        )
    else:
        record_test(
            "Clear Cache Endpoint - Functionality", 
            False,
            f"Issues found: {'; '.join(issues_found)}"
        )
    
    return success, response_data, status_code

def test_clear_cache_authorization():
    """Test 2: Test authorization requirements for clear cache endpoint"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Testing Clear Cache Authorization Requirements{Colors.END}")
    
    print(f"   📝 Testing POST /api/admin/cache/clear without authorization")
    
    # Test without authorization header
    success, response_data, details, status_code = make_request(
        "POST",
        "/admin/cache/clear"
    )
    
    print(f"   📊 Unauthorized Request Analysis:")
    print(f"      Status Code: {status_code}")
    print(f"      Expected: 401 Unauthorized")
    print(f"      Response: {response_data}")
    
    # Should fail with 401 Unauthorized
    if status_code == 401:
        record_test(
            "Clear Cache Endpoint - Authorization Required",
            True,
            "Correctly requires admin authorization (401 Unauthorized without token)"
        )
    else:
        record_test(
            "Clear Cache Endpoint - Authorization Required",
            False,
            f"Should return 401 Unauthorized, got {status_code}"
        )
    
    # Test with invalid token
    print(f"   📝 Testing POST /api/admin/cache/clear with invalid token")
    
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
    success, response_data, details, status_code = make_request(
        "POST",
        "/admin/cache/clear",
        headers=invalid_headers
    )
    
    print(f"   📊 Invalid Token Request Analysis:")
    print(f"      Status Code: {status_code}")
    print(f"      Expected: 401 Unauthorized")
    print(f"      Response: {response_data}")
    
    if status_code == 401:
        record_test(
            "Clear Cache Endpoint - Invalid Token Rejection",
            True,
            "Correctly rejects invalid tokens (401 Unauthorized)"
        )
    else:
        record_test(
            "Clear Cache Endpoint - Invalid Token Rejection",
            False,
            f"Should return 401 Unauthorized for invalid token, got {status_code}"
        )

def check_backend_logs():
    """Test 3: Check backend logs for clear cache related errors"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Analyzing Backend Logs for Clear Cache Errors{Colors.END}")
    
    try:
        import subprocess
        
        # Get recent backend logs
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for cache-related errors
            cache_errors = []
            error_keywords = [
                "cache/clear",
                "clear_cache",
                "500",
                "Internal Server Error",
                "JSON",
                "cache",
                "admin/cache"
            ]
            
            for line in log_content.split('\n'):
                line_lower = line.lower()
                if any(keyword.lower() in line_lower for keyword in error_keywords):
                    cache_errors.append(line.strip())
            
            print(f"   📋 Cache-related log entries found: {len(cache_errors)}")
            
            if cache_errors:
                print(f"   📝 Recent cache-related log entries:")
                for error in cache_errors[-10:]:  # Show last 10 relevant lines
                    print(f"      {error}")
                
                # Look for specific error patterns
                error_patterns = {
                    "500 errors": [line for line in cache_errors if "500" in line],
                    "JSON errors": [line for line in cache_errors if "json" in line.lower()],
                    "Cache clear errors": [line for line in cache_errors if "cache" in line.lower() and "clear" in line.lower()]
                }
                
                for pattern_name, pattern_lines in error_patterns.items():
                    if pattern_lines:
                        print(f"   🔍 {pattern_name}: {len(pattern_lines)} entries")
                        for line in pattern_lines[-3:]:  # Show last 3 of each type
                            print(f"      {line}")
                
                record_test(
                    "Backend Logs - Cache Clear Errors",
                    False,
                    f"Found {len(cache_errors)} cache-related log entries indicating potential issues"
                )
            else:
                record_test(
                    "Backend Logs - Cache Clear Errors",
                    True,
                    "No cache-related errors found in recent backend logs"
                )
                
        else:
            record_test(
                "Backend Logs - Cache Clear Errors",
                False,
                f"Failed to read backend logs: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        record_test("Backend Logs - Cache Clear Errors", False, "Timeout reading backend logs")
    except Exception as e:
        record_test("Backend Logs - Cache Clear Errors", False, f"Error reading logs: {str(e)}")

def check_cache_clear_implementation():
    """Test 4: Check if cache clear endpoint exists in backend code"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Checking Cache Clear Endpoint Implementation{Colors.END}")
    
    try:
        # Check if the endpoint is implemented in server.py
        with open("/app/backend/server.py", "r") as f:
            server_content = f.read()
        
        # Look for cache clear endpoint implementation
        cache_clear_patterns = [
            "/admin/cache/clear",
            "cache/clear",
            "clear_cache",
            "admin_cache_clear",
            "@app.post(\"/api/admin/cache/clear\")",
            "def clear_cache",
            "async def clear_cache"
        ]
        
        found_patterns = []
        for pattern in cache_clear_patterns:
            if pattern in server_content:
                found_patterns.append(pattern)
        
        print(f"   📋 Cache clear implementation patterns found: {len(found_patterns)}")
        for pattern in found_patterns:
            print(f"      ✅ Found: {pattern}")
        
        if found_patterns:
            record_test(
                "Cache Clear Endpoint - Implementation Check",
                True,
                f"Cache clear endpoint appears to be implemented. Found patterns: {', '.join(found_patterns)}"
            )
        else:
            record_test(
                "Cache Clear Endpoint - Implementation Check",
                False,
                "Cache clear endpoint implementation not found in backend code"
            )
            
    except Exception as e:
        record_test(
            "Cache Clear Endpoint - Implementation Check",
            False,
            f"Error checking implementation: {str(e)}"
        )

def print_clear_cache_summary():
    """Print clear cache testing specific summary"""
    print_header("CLEAR CACHE ENDPOINT TESTING SUMMARY")
    
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
    
    requirements = [
        "POST /api/admin/cache/clear endpoint exists and responds",
        "Admin authorization required and working",
        "Returns successful response with cleared cache types",
        "No HTTP 500 Internal Server Error",
        "Valid JSON response format",
        "Backend logs show no critical errors"
    ]
    
    for i, req in enumerate(requirements, 1):
        # Find corresponding test result
        test_found = False
        for test in test_results["tests"]:
            if ("clear cache endpoint" in test["name"].lower() and "functionality" in test["name"].lower()) and i <= 3:
                status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
                print(f"   {i}. {req}: {status}")
                test_found = True
                break
            elif ("authorization" in test["name"].lower()) and i == 2:
                status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
                print(f"   {i}. {req}: {status}")
                test_found = True
                break
            elif ("backend logs" in test["name"].lower()) and i == 6:
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
    
    # Specific conclusion for Clear Cache
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: CLEAR CACHE ENDPOINT IS 100% WORKING!{Colors.END}")
        print(f"{Colors.GREEN}Clear cache functionality is operational. No HTTP 500 errors or JSON format issues.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: CLEAR CACHE ENDPOINT HAS ISSUES ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Some components work but there are issues that need attention.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: CLEAR CACHE ENDPOINT FAILED ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}CRITICAL ISSUES! Clear cache endpoint is not working correctly.{Colors.END}")
        print(f"{Colors.RED}HTTP 500 errors and/or invalid JSON format issues confirmed.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    # Check specific failure patterns
    functionality_test = next((test for test in test_results["tests"] if "functionality" in test["name"].lower()), None)
    auth_test = next((test for test in test_results["tests"] if "authorization" in test["name"].lower()), None)
    logs_test = next((test for test in test_results["tests"] if "backend logs" in test["name"].lower()), None)
    
    if functionality_test and not functionality_test["success"]:
        print(f"   🔴 CRITICAL: Clear cache endpoint is returning HTTP 500 errors")
        print(f"   🔧 URGENT: Check /api/admin/cache/clear endpoint implementation")
        print(f"   🔧 URGENT: Fix JSON response format issues")
        print(f"   🔧 URGENT: Debug server-side cache clearing logic")
    elif auth_test and not auth_test["success"]:
        print(f"   🔴 Authorization issues with clear cache endpoint")
        print(f"   🔧 Check admin role permissions for cache clearing")
    elif logs_test and not logs_test["success"]:
        print(f"   🔴 Backend logs show cache-related errors")
        print(f"   🔧 Review backend error logs for root cause")
    else:
        print(f"   🟢 Clear cache endpoint appears to be working correctly")
        print(f"   ✅ No HTTP 500 errors detected")
        print(f"   ✅ JSON response format is valid")
        print(f"   ✅ Authorization working properly")

def main():
    """Main test execution for Clear Cache endpoint"""
    print_header("CLEAR CACHE ENDPOINT TESTING")
    print(f"{Colors.BLUE}🎯 Testing Clear Cache endpoint functionality{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: POST /api/admin/cache/clear endpoint{Colors.END}")
    print(f"{Colors.BLUE}🚨 Issue: Frontend reports HTTP 500 error and invalid JSON format{Colors.END}")
    print(f"{Colors.BLUE}🔍 Goal: Identify root cause of cache clearing failures{Colors.END}")
    
    try:
        # Run Clear Cache tests
        test_clear_cache_endpoint()
        test_clear_cache_authorization()
        check_backend_logs()
        check_cache_clear_implementation()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_clear_cache_summary()

if __name__ == "__main__":
    main()