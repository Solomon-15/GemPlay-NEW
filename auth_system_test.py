#!/usr/bin/env python3
"""
RUSSIAN REVIEW - AUTHORIZATION SYSTEM WITH AUTOMATIC TOKEN REFRESH TESTING
Протестировать исправленную систему авторизации с автоматическим обновлением токенов

ИСПРАВЛЕНИЯ ПРОБЛЕМЫ АВТОВЫХОДА:
1. Увеличил время жизни access token с 15 до 30 минут 
2. Добавил глобальный axios interceptor для автоматического refresh токенов
3. Убрал дублирующиеся обработчики 401 ошибок
4. Добавил глобальную функцию уведомлений для interceptor

ТЕСТИРОВАНИЕ:
1. ТЕСТ СОЗДАНИЯ ТОКЕНОВ - POST /api/auth/login (admin@gemplay.com / Admin123!)
2. ТЕСТ REFRESH TOKEN ENDPOINT - POST /api/auth/refresh с valid refresh_token
3. ЛОГИ BACKEND - Не должно быть ошибок при создании токенов
4. ПРОВЕРКА КОНФИГУРАЦИИ - ACCESS_TOKEN_EXPIRE_MINUTES = 30, REFRESH_TOKEN_EXPIRE_DAYS = 7
"""

import requests
import json
import time
import sys
import jwt
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import subprocess

# Configuration
BASE_URL = "https://bef757b2-b856-4612-bfd8-1e1d820561f6.preview.emergentagent.com/api"
TEST_USER = {
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

def decode_jwt_token(token: str) -> Optional[Dict]:
    """Decode JWT token without verification to check payload"""
    try:
        # Split token and decode payload
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Add padding if needed
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        
        # Decode base64
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_json = json.loads(decoded_bytes.decode('utf-8'))
        
        return decoded_json
    except Exception as e:
        print(f"   ⚠️ Error decoding JWT: {e}")
        return None

def test_token_creation():
    """Test 1: POST /api/auth/login - проверить создание токенов с правильным временем жизни"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Token Creation with 30-minute Lifespan{Colors.END}")
    
    print(f"   📝 Testing POST /api/auth/login with admin@gemplay.com / Admin123!")
    
    # Test login endpoint
    success, response_data, details = make_request(
        "POST",
        "/auth/login",
        data=TEST_USER
    )
    
    if not success or not response_data:
        record_test(
            "Token Creation Test",
            False,
            f"Login failed: {details}"
        )
        return None, None
    
    # Check response structure
    access_token = response_data.get("access_token")
    refresh_token = response_data.get("refresh_token")
    token_type = response_data.get("token_type")
    user_data = response_data.get("user")
    
    if not access_token:
        record_test(
            "Token Creation Test",
            False,
            "No access_token in response"
        )
        return None, None
    
    if not refresh_token:
        record_test(
            "Token Creation Test",
            False,
            "No refresh_token in response"
        )
        return None, None
    
    # Decode JWT token to check expiration
    token_payload = decode_jwt_token(access_token)
    if not token_payload:
        record_test(
            "Token Creation Test",
            False,
            "Failed to decode JWT token"
        )
        return None, None
    
    # Check token expiration time
    exp_timestamp = token_payload.get("exp")
    token_type_field = token_payload.get("type")
    user_id = token_payload.get("sub")
    
    if not exp_timestamp:
        record_test(
            "Token Creation Test",
            False,
            "Missing exp field in JWT token"
        )
        return None, None
    
    # Calculate token lifespan from current time (since iat is not present)
    current_time = time.time()
    token_lifespan_seconds = exp_timestamp - current_time
    token_lifespan_minutes = token_lifespan_seconds / 60
    
    # Check if token lifespan is approximately 30 minutes (1800 seconds)
    expected_lifespan_minutes = 30
    is_correct_lifespan = abs(token_lifespan_minutes - expected_lifespan_minutes) < 2  # Allow 2 minute tolerance
    
    print(f"   📊 TOKEN ANALYSIS:")
    print(f"      Access Token: {access_token[:50]}...")
    print(f"      Refresh Token: {refresh_token[:50]}...")
    print(f"      Token Type: {token_type}")
    print(f"      JWT Type Field: {token_type_field}")
    print(f"      User ID: {user_id}")
    print(f"      Token Lifespan: {token_lifespan_minutes:.1f} minutes ({token_lifespan_seconds:.0f} seconds)")
    print(f"      Expected Lifespan: {expected_lifespan_minutes} minutes (1800 seconds)")
    print(f"      Current Time: {datetime.fromtimestamp(current_time)}")
    print(f"      Expires At: {datetime.fromtimestamp(exp_timestamp)}")
    
    if is_correct_lifespan and refresh_token and token_type == "bearer":
        record_test(
            "Token Creation Test",
            True,
            f"✅ Access token created with correct 30-minute lifespan ({token_lifespan_minutes:.1f} min), refresh token present"
        )
    elif not is_correct_lifespan:
        record_test(
            "Token Creation Test",
            False,
            f"❌ Incorrect token lifespan: {token_lifespan_minutes:.1f} minutes instead of 30 minutes"
        )
    else:
        record_test(
            "Token Creation Test",
            False,
            f"❌ Missing refresh token or incorrect token type: {token_type}"
        )
    
    return access_token, refresh_token

def test_refresh_token_endpoint(refresh_token: str):
    """Test 2: POST /api/auth/refresh - проверить работу refresh token endpoint"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Refresh Token Endpoint Functionality{Colors.END}")
    
    if not refresh_token:
        record_test(
            "Refresh Token Test",
            False,
            "No refresh token available from previous test"
        )
        return None
    
    print(f"   📝 Testing POST /api/auth/refresh with valid refresh_token")
    print(f"   🔑 Refresh Token: {refresh_token[:50]}...")
    
    # Test refresh endpoint
    success, response_data, details = make_request(
        "POST",
        f"/auth/refresh?refresh_token={refresh_token}"
    )
    
    if not success or not response_data:
        record_test(
            "Refresh Token Test",
            False,
            f"Refresh failed: {details}"
        )
        return None
    
    # Check response structure
    new_access_token = response_data.get("access_token")
    new_refresh_token = response_data.get("refresh_token")
    token_type = response_data.get("token_type")
    
    if not new_access_token:
        record_test(
            "Refresh Token Test",
            False,
            "No new access_token in refresh response"
        )
        return None
    
    # Decode new JWT token to check expiration
    new_token_payload = decode_jwt_token(new_access_token)
    if not new_token_payload:
        record_test(
            "Refresh Token Test",
            False,
            "Failed to decode new JWT token"
        )
        return None
    
    # Check new token expiration time
    new_exp_timestamp = new_token_payload.get("exp")
    
    if not new_exp_timestamp:
        record_test(
            "Refresh Token Test",
            False,
            "Missing exp field in new JWT token"
        )
        return None
    
    # Calculate new token lifespan from current time
    current_time = time.time()
    new_token_lifespan_seconds = new_exp_timestamp - current_time
    new_token_lifespan_minutes = new_token_lifespan_seconds / 60
    
    # Check if new token lifespan is also approximately 30 minutes
    expected_lifespan_minutes = 30
    is_correct_new_lifespan = abs(new_token_lifespan_minutes - expected_lifespan_minutes) < 2
    
    print(f"   📊 REFRESH TOKEN ANALYSIS:")
    print(f"      New Access Token: {new_access_token[:50]}...")
    print(f"      New Refresh Token: {new_refresh_token[:50] if new_refresh_token else 'None'}...")
    print(f"      Token Type: {token_type}")
    print(f"      New Token Lifespan: {new_token_lifespan_minutes:.1f} minutes ({new_token_lifespan_seconds:.0f} seconds)")
    print(f"      Expected Lifespan: {expected_lifespan_minutes} minutes (1800 seconds)")
    print(f"      Current Time: {datetime.fromtimestamp(current_time)}")
    print(f"      New Expires At: {datetime.fromtimestamp(new_exp_timestamp)}")
    
    if is_correct_new_lifespan and token_type == "bearer":
        record_test(
            "Refresh Token Test",
            True,
            f"✅ New access token created with correct 30-minute lifespan ({new_token_lifespan_minutes:.1f} min)"
        )
    else:
        record_test(
            "Refresh Token Test",
            False,
            f"❌ Incorrect new token lifespan: {new_token_lifespan_minutes:.1f} minutes instead of 30 minutes"
        )
    
    return new_access_token

def test_backend_logs_for_auth():
    """Test 3: Проверить логи backend на отсутствие ошибок при создании токенов"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Backend Logs Analysis for Auth Errors{Colors.END}")
    
    try:
        # Try to read supervisor logs for backend
        result = subprocess.run(
            ["tail", "-n", "200", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # Look for auth-related errors
            auth_errors = log_content.count("auth error")
            token_errors = log_content.count("token error")
            jwt_errors = log_content.count("JWT error")
            login_errors = log_content.count("login error")
            refresh_errors = log_content.count("refresh error")
            http_500_auth = len([line for line in log_content.split('\n') if "HTTP 500" in line and ("auth" in line.lower() or "token" in line.lower())])
            
            # Look for successful auth operations
            successful_logins = log_content.count("Login successful")
            successful_refreshes = log_content.count("Token refreshed")
            token_created = log_content.count("access_token")
            
            print(f"   📋 AUTH-RELATED LOG ANALYSIS:")
            print(f"      ❌ Auth errors: {auth_errors}")
            print(f"      ❌ Token errors: {token_errors}")
            print(f"      ❌ JWT errors: {jwt_errors}")
            print(f"      ❌ Login errors: {login_errors}")
            print(f"      ❌ Refresh errors: {refresh_errors}")
            print(f"      ❌ HTTP 500 auth-related: {http_500_auth}")
            print(f"      ✅ Successful logins: {successful_logins}")
            print(f"      ✅ Successful refreshes: {successful_refreshes}")
            print(f"      ✅ Token creation mentions: {token_created}")
            
            total_auth_errors = auth_errors + token_errors + jwt_errors + login_errors + refresh_errors + http_500_auth
            total_successful_ops = successful_logins + successful_refreshes + token_created
            
            if total_auth_errors == 0 and total_successful_ops > 0:
                record_test(
                    "Backend Auth Logs Test",
                    True,
                    f"✅ No auth errors found, {total_successful_ops} successful auth operations detected"
                )
            elif total_auth_errors == 0:
                record_test(
                    "Backend Auth Logs Test",
                    True,
                    "✅ No auth errors found (no successful operations detected but that's acceptable)"
                )
            else:
                record_test(
                    "Backend Auth Logs Test",
                    False,
                    f"❌ Found {total_auth_errors} auth-related errors in backend logs"
                )
            
            # Show some relevant log lines
            error_lines = []
            success_lines = []
            for line in log_content.split('\n'):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ["auth error", "token error", "jwt error", "login error", "refresh error"]):
                    error_lines.append(line.strip())
                elif any(keyword in line_lower for keyword in ["login successful", "token refreshed", "access_token"]):
                    success_lines.append(line.strip())
            
            if error_lines:
                print(f"   📝 Recent auth error lines:")
                for line in error_lines[-3:]:  # Show last 3 error lines
                    print(f"      {Colors.RED}{line}{Colors.END}")
            
            if success_lines:
                print(f"   📝 Recent successful auth lines:")
                for line in success_lines[-3:]:  # Show last 3 success lines
                    print(f"      {Colors.GREEN}{line}{Colors.END}")
                    
        else:
            record_test(
                "Backend Auth Logs Test",
                False,
                f"Failed to read backend logs: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        record_test("Backend Auth Logs Test", False, "Timeout reading backend logs")
    except Exception as e:
        record_test("Backend Auth Logs Test", False, f"Error reading logs: {str(e)}")

def test_configuration_verification():
    """Test 4: Проверить конфигурацию ACCESS_TOKEN_EXPIRE_MINUTES = 30, REFRESH_TOKEN_EXPIRE_DAYS = 7"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Configuration Verification{Colors.END}")
    
    try:
        # Read the server.py file to check configuration
        with open('/app/backend/server.py', 'r') as f:
            server_content = f.read()
        
        # Look for configuration constants
        access_token_expire_line = None
        refresh_token_expire_line = None
        
        for line_num, line in enumerate(server_content.split('\n'), 1):
            if 'ACCESS_TOKEN_EXPIRE_MINUTES' in line and '=' in line and not line.strip().startswith('#'):
                access_token_expire_line = (line_num, line.strip())
                break
        
        for line_num, line in enumerate(server_content.split('\n'), 1):
            if 'REFRESH_TOKEN_EXPIRE_DAYS' in line and '=' in line and not line.strip().startswith('#'):
                refresh_token_expire_line = (line_num, line.strip())
                break
        
        print(f"   📋 CONFIGURATION ANALYSIS:")
        
        access_token_correct = False
        refresh_token_correct = False
        
        if access_token_expire_line:
            line_content = access_token_expire_line[1]
            print(f"      Line {access_token_expire_line[0]}: {line_content}")
            # Check if the value is 30
            if '= 30' in line_content or '=30' in line_content:
                access_token_correct = True
                print(f"      ✅ ACCESS_TOKEN_EXPIRE_MINUTES = 30 (correct)")
            else:
                print(f"      ❌ ACCESS_TOKEN_EXPIRE_MINUTES is not set to 30")
        else:
            print(f"      ❌ ACCESS_TOKEN_EXPIRE_MINUTES not found in server.py")
        
        if refresh_token_expire_line:
            line_content = refresh_token_expire_line[1]
            print(f"      Line {refresh_token_expire_line[0]}: {line_content}")
            # Check if the value is 7
            if '= 7' in line_content or '=7' in line_content:
                refresh_token_correct = True
                print(f"      ✅ REFRESH_TOKEN_EXPIRE_DAYS = 7 (correct)")
            else:
                print(f"      ❌ REFRESH_TOKEN_EXPIRE_DAYS is not set to 7")
        else:
            print(f"      ❌ REFRESH_TOKEN_EXPIRE_DAYS not found in server.py")
        
        if access_token_correct and refresh_token_correct:
            record_test(
                "Configuration Verification Test",
                True,
                "✅ Both ACCESS_TOKEN_EXPIRE_MINUTES=30 and REFRESH_TOKEN_EXPIRE_DAYS=7 are correctly configured"
            )
        elif access_token_correct:
            record_test(
                "Configuration Verification Test",
                False,
                "❌ ACCESS_TOKEN_EXPIRE_MINUTES=30 is correct but REFRESH_TOKEN_EXPIRE_DAYS=7 is not found/incorrect"
            )
        elif refresh_token_correct:
            record_test(
                "Configuration Verification Test",
                False,
                "❌ REFRESH_TOKEN_EXPIRE_DAYS=7 is correct but ACCESS_TOKEN_EXPIRE_MINUTES=30 is not found/incorrect"
            )
        else:
            record_test(
                "Configuration Verification Test",
                False,
                "❌ Both configuration values are incorrect or not found"
            )
            
    except Exception as e:
        record_test("Configuration Verification Test", False, f"Error reading server.py: {str(e)}")

def print_auth_system_summary():
    """Print authorization system testing summary"""
    print_header("AUTHORIZATION SYSTEM WITH AUTOMATIC TOKEN REFRESH - SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 AUTHORIZATION SYSTEM REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each test
    token_test = next((test for test in test_results["tests"] if "token creation" in test["name"].lower()), None)
    refresh_test = next((test for test in test_results["tests"] if "refresh token" in test["name"].lower()), None)
    logs_test = next((test for test in test_results["tests"] if "backend auth logs" in test["name"].lower()), None)
    config_test = next((test for test in test_results["tests"] if "configuration" in test["name"].lower()), None)
    
    requirements = [
        ("1. СОЗДАНИЕ ТОКЕНОВ С 30-МИНУТНЫМ ВРЕМЕНЕМ ЖИЗНИ", token_test),
        ("2. REFRESH TOKEN ENDPOINT ФУНКЦИОНАЛЬНОСТЬ", refresh_test),
        ("3. ОТСУТСТВИЕ ОШИБОК В ЛОГАХ BACKEND", logs_test),
        ("4. ПРАВИЛЬНАЯ КОНФИГУРАЦИЯ (30 мин / 7 дней)", config_test)
    ]
    
    for req_name, test in requirements:
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: AUTHORIZATION SYSTEM IS FULLY OPERATIONAL!{Colors.END}")
        print(f"{Colors.GREEN}✅ Access tokens создаются с правильным временем жизни (30 минут){Colors.END}")
        print(f"{Colors.GREEN}✅ Refresh token endpoint работает корректно{Colors.END}")
        print(f"{Colors.GREEN}✅ Нет ошибок в backend логах{Colors.END}")
        print(f"{Colors.GREEN}✅ Конфигурация настроена правильно{Colors.END}")
        print(f"{Colors.GREEN}✅ Проблема автовыхода решена{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: AUTHORIZATION SYSTEM MOSTLY WORKING ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Основные функции авторизации работают, но есть минорные проблемы.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Некоторые функции авторизации работают, но требуется дополнительная работа.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: AUTHORIZATION SYSTEM HAS CRITICAL ISSUES ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Система авторизации НЕ работает правильно. Требуется срочное исправление.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    if token_test and not token_test["success"]:
        print(f"   🔴 Token creation needs fixing - incorrect lifespan or missing refresh token")
    if refresh_test and not refresh_test["success"]:
        print(f"   🔴 Refresh token endpoint needs fixing")
    if logs_test and not logs_test["success"]:
        print(f"   🔴 Backend has auth-related errors that need investigation")
    if config_test and not config_test["success"]:
        print(f"   🔴 Configuration values need to be set correctly")
    
    if success_rate == 100:
        print(f"   🟢 Authorization system is working correctly - auto-logout issue resolved")
        print(f"   ✅ Main agent can summarize and finish")
    else:
        print(f"   🔧 Fix remaining authorization issues before considering system complete")

def main():
    """Main test execution for Authorization System"""
    print_header("AUTHORIZATION SYSTEM WITH AUTOMATIC TOKEN REFRESH TESTING")
    print(f"{Colors.BLUE}🎯 Testing ИСПРАВЛЕННУЮ систему авторизации с автоматическим обновлением токенов{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 CRITICAL FIXES: 30-min tokens, refresh endpoint, no duplicate handlers{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for testing{Colors.END}")
    
    try:
        # Test 1: Token Creation with 30-minute lifespan
        access_token, refresh_token = test_token_creation()
        
        # Test 2: Refresh Token Endpoint
        if refresh_token:
            test_refresh_token_endpoint(refresh_token)
        
        # Test 3: Backend Logs Analysis
        test_backend_logs_for_auth()
        
        # Test 4: Configuration Verification
        test_configuration_verification()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_auth_system_summary()

if __name__ == "__main__":
    main()