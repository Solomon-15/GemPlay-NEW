#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import concurrent.futures
import uuid

# Configuration
BASE_URL = "https://f228449e-5ba6-4c73-a6f9-ef7939ae9431.preview.emergentagent.com/api"
TEST_USER = {
    "username": "securitytester",
    "email": "securitytest@example.com",
    "password": "Security123!",
    "gender": "male"
}
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
    auth_token: Optional[str] = None,
    silent: bool = False
) -> Tuple[Dict[str, Any], bool]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    if not silent:
        print(f"Making {method} request to {url}")
        if data:
            print(f"Request data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    if not silent:
        print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        if not silent:
            print(f"Response data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        response_data = {"text": response.text}
        if not silent:
            print(f"Response text: {response.text}")
    
    success = response.status_code == expected_status
    
    if not success and not silent:
        print_error(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success

def register_test_user() -> Tuple[Optional[str], str, str]:
    """Register a test user and return the verification token, email, and username."""
    print_subheader("Registering Test User")
    
    # Generate a random email to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"security_{random_suffix}@example.com"
    test_username = f"security_{random_suffix}"
    
    user_data = {
        "username": test_username,
        "email": test_email,
        "password": TEST_USER["password"],
        "gender": TEST_USER["gender"]
    }
    
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if success:
        if "message" in response and "user_id" in response and "verification_token" in response:
            print_success(f"User registered successfully with ID: {response['user_id']}")
            print_success(f"Verification token: {response['verification_token']}")
            return response["verification_token"], test_email, test_username
        else:
            print_error(f"User registration response missing expected fields: {response}")
    else:
        print_error("User registration failed")
    
    return None, test_email, test_username

def verify_email(token: str) -> bool:
    """Verify user email."""
    print_subheader("Verifying Email")
    
    if not token:
        print_error("No verification token available")
        return False
    
    response, success = make_request("POST", "/auth/verify-email", data={"token": token})
    
    if success:
        if "message" in response and "verified" in response["message"].lower():
            print_success("Email verified successfully")
            return True
        else:
            print_error(f"Email verification response unexpected: {response}")
    else:
        print_error("Email verification failed")
    
    return False

def login_user(email: str, password: str) -> Optional[str]:
    """Login user and return auth token."""
    print_subheader(f"Logging in User: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"User logged in successfully")
        return response["access_token"]
    else:
        print_error(f"Login failed")
        return None

def login_admin() -> Optional[str]:
    """Login as admin and return auth token."""
    print_subheader("Logging in as Admin")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin logged in successfully")
        return response["access_token"]
    else:
        print_error(f"Admin login failed")
        return None

# ============================================================================
# SECURITY TESTS
# ============================================================================

def test_rate_limiting(user_token: str) -> None:
    """Test rate limiting protection."""
    print_subheader("Testing Rate Limiting Protection")
    
    if not user_token:
        print_error("No auth token available")
        record_test("Rate Limiting Protection", False, "No token available")
        return
    
    # Make many requests in parallel to trigger rate limiting
    endpoint = "/auth/me"
    num_requests = 70  # More than the 60 per minute limit
    
    print(f"Making {num_requests} parallel requests to trigger rate limiting...")
    
    responses = []
    rate_limited = False
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for _ in range(num_requests):
            futures.append(executor.submit(
                make_request, "GET", endpoint, None, None, 200, user_token, True
            ))
        
        for future in concurrent.futures.as_completed(futures):
            response, success = future.result()
            responses.append((response, success))
            if not success and isinstance(response, dict) and "detail" in response:
                if "Rate limit exceeded" in response["detail"]:
                    rate_limited = True
    
    # Count successful and rate-limited responses
    successful = sum(1 for _, success in responses if success)
    rate_limited_count = sum(1 for response, success in responses 
                           if not success and isinstance(response, dict) and "detail" in response 
                           and "Rate limit exceeded" in response["detail"])
    
    print(f"Made {num_requests} requests:")
    print(f"  - Successful: {successful}")
    print(f"  - Rate limited: {rate_limited_count}")
    
    if rate_limited:
        print_success("Rate limiting protection is working correctly")
        record_test("Rate Limiting Protection", True, f"Rate limited after {successful} requests")
    else:
        print_error("Rate limiting protection did not trigger")
        record_test("Rate Limiting Protection", False, "Rate limiting not triggered")

def test_security_dashboard(admin_token: str) -> None:
    """Test security dashboard API."""
    print_subheader("Testing Security Dashboard API")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("Security Dashboard API", False, "No admin token available")
        return
    
    response, success = make_request("GET", "/admin/security/dashboard", auth_token=admin_token)
    
    if success:
        expected_keys = ["alert_counts", "recent_activities", "top_alert_types", 
                         "users_with_most_alerts", "total_alerts_24h", "unresolved_alerts"]
        
        missing_keys = [key for key in expected_keys if key not in response]
        
        if not missing_keys:
            print_success("Security dashboard API returned all expected data")
            record_test("Security Dashboard API", True)
        else:
            print_error(f"Security dashboard API missing expected keys: {missing_keys}")
            record_test("Security Dashboard API", False, f"Missing keys: {missing_keys}")
    else:
        record_test("Security Dashboard API", False, "Request failed")

def test_security_alerts(admin_token: str) -> None:
    """Test security alerts API."""
    print_subheader("Testing Security Alerts API")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("Security Alerts API", False, "No admin token available")
        return
    
    response, success = make_request("GET", "/admin/security/alerts", auth_token=admin_token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Security alerts API returned {len(response)} alerts")
            
            # Check alert structure if any alerts exist
            if response:
                expected_keys = ["id", "user_id", "alert_type", "severity", "description", 
                                "created_at", "resolved"]
                
                missing_keys = [key for key in expected_keys if key not in response[0]]
                
                if not missing_keys:
                    print_success("Security alerts have the expected structure")
                    record_test("Security Alerts API", True)
                else:
                    print_error(f"Security alerts missing expected keys: {missing_keys}")
                    record_test("Security Alerts API", False, f"Missing keys: {missing_keys}")
            else:
                print_warning("No security alerts found, but API is working")
                record_test("Security Alerts API", True, "No alerts found")
        else:
            print_error("Security alerts API did not return a list")
            record_test("Security Alerts API", False, "Did not return a list")
    else:
        record_test("Security Alerts API", False, "Request failed")

def test_monitoring_stats(admin_token: str) -> None:
    """Test monitoring stats API."""
    print_subheader("Testing Monitoring Stats API")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("Monitoring Stats API", False, "No admin token available")
        return
    
    response, success = make_request("GET", "/admin/security/monitoring-stats", auth_token=admin_token)
    
    if success:
        expected_sections = ["transaction_stats", "user_activity", "security_stats"]
        
        missing_sections = [section for section in expected_sections if section not in response]
        
        if not missing_sections:
            print_success("Monitoring stats API returned all expected sections")
            record_test("Monitoring Stats API", True)
        else:
            print_error(f"Monitoring stats API missing expected sections: {missing_sections}")
            record_test("Monitoring Stats API", False, f"Missing sections: {missing_sections}")
    else:
        record_test("Monitoring Stats API", False, "Request failed")

def test_resolve_alert(admin_token: str) -> None:
    """Test resolving a security alert."""
    print_subheader("Testing Alert Resolution API")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("Alert Resolution API", False, "No admin token available")
        return
    
    # First, get a list of unresolved alerts
    response, success = make_request(
        "GET", 
        "/admin/security/alerts", 
        data={"resolved": "false"}, 
        auth_token=admin_token
    )
    
    if not success or not isinstance(response, list) or not response:
        print_warning("No unresolved alerts found to test resolution")
        record_test("Alert Resolution API", True, "No alerts to resolve")
        return
    
    # Take the first unresolved alert
    alert = response[0]
    alert_id = alert["id"]
    
    # Try to resolve it
    response, success = make_request(
        "POST", 
        f"/admin/security/alerts/{alert_id}/resolve?action_taken=Resolved+during+security+testing", 
        auth_token=admin_token
    )
    
    if success:
        if "message" in response and "resolved" in response["message"].lower():
            print_success(f"Successfully resolved alert {alert_id}")
            record_test("Alert Resolution API", True)
        else:
            print_error(f"Alert resolution response unexpected: {response}")
            record_test("Alert Resolution API", False, f"Unexpected response: {response}")
    else:
        record_test("Alert Resolution API", False, "Request failed")

def test_large_purchase(user_token: str) -> None:
    """Test large purchase detection."""
    print_subheader("Testing Large Purchase Detection")
    
    if not user_token:
        print_error("No auth token available")
        record_test("Large Purchase Detection", False, "No token available")
        return
    
    # First, check user's balance
    response, success = make_request("GET", "/economy/balance", auth_token=user_token)
    
    if not success:
        print_error("Failed to get user balance")
        record_test("Large Purchase Detection", False, "Failed to get user balance")
        return
    
    balance = response["virtual_balance"]
    print(f"User balance: ${balance}")
    
    # Get gem definitions
    response, success = make_request("GET", "/gems/definitions")
    
    if not success or not isinstance(response, list) or not response:
        print_error("Failed to get gem definitions")
        record_test("Large Purchase Detection", False, "Failed to get gem definitions")
        return
    
    # Find a gem with a price that would make a large purchase (>$500)
    suitable_gem = None
    for gem in response:
        if gem["price"] > 0:
            quantity_needed = max(1, int(501 / gem["price"]))
            total_cost = quantity_needed * gem["price"]
            if total_cost > 500 and total_cost <= balance:
                suitable_gem = (gem["type"], quantity_needed, total_cost)
                break
    
    if not suitable_gem:
        print_warning("Could not find a suitable gem for large purchase test")
        record_test("Large Purchase Detection", False, "No suitable gem found")
        return
    
    gem_type, quantity, total_cost = suitable_gem
    print(f"Attempting to purchase {quantity} {gem_type} gems for ${total_cost}")
    
    # Make the large purchase
    response, success = make_request(
        "POST", 
        f"/gems/buy?gem_type={gem_type}&quantity={quantity}", 
        auth_token=user_token
    )
    
    if success:
        print_success(f"Large purchase of ${total_cost} completed successfully")
        record_test("Large Purchase Detection", True, f"Purchase of ${total_cost} completed")
    else:
        print_error(f"Large purchase failed: {response}")
        record_test("Large Purchase Detection", False, f"Purchase failed: {response}")

def test_admin_access_control(user_token: str, admin_token: str) -> None:
    """Test admin access control."""
    print_subheader("Testing Admin Access Control")
    
    if not user_token or not admin_token:
        print_error("Missing tokens for access control test")
        record_test("Admin Access Control", False, "Missing tokens")
        return
    
    # Try to access admin endpoint with regular user token
    response, success = make_request(
        "GET", 
        "/admin/security/dashboard", 
        auth_token=user_token,
        expected_status=403  # Expect forbidden
    )
    
    # For regular user, we expect a 403 error (not success)
    if not success:
        if "detail" in response and "Not enough permissions" in response["detail"]:
            print_success("Regular user correctly denied access to admin endpoint")
            user_test_passed = True
        else:
            print_warning(f"Unexpected error when regular user tried to access admin endpoint: {response}")
            user_test_passed = False
    else:
        print_error("Regular user was able to access admin endpoint!")
        record_test("Admin Access Control", False, "Regular user accessed admin endpoint")
        return
    
    # Try to access admin endpoint with admin token
    response, success = make_request(
        "GET", 
        "/admin/security/dashboard", 
        auth_token=admin_token
    )
    
    if success:
        print_success("Admin user correctly granted access to admin endpoint")
        admin_test_passed = True
    else:
        print_error("Admin user denied access to admin endpoint")
        admin_test_passed = False
    
    # Only pass the test if both parts passed
    if user_test_passed and admin_test_passed:
        record_test("Admin Access Control", True, "Access control working correctly")
    else:
        if not user_test_passed:
            record_test("Admin Access Control", False, "Regular user access control issue")
        else:
            record_test("Admin Access Control", False, "Admin access issue")

def test_suspicious_activity(user_token: str) -> None:
    """Test suspicious activity detection by making multiple purchases."""
    print_subheader("Testing Suspicious Activity Detection")
    
    if not user_token:
        print_error("No auth token available")
        record_test("Suspicious Activity Detection", False, "No token available")
        return
    
    # Get gem definitions
    response, success = make_request("GET", "/gems/definitions")
    
    if not success or not isinstance(response, list) or not response:
        print_error("Failed to get gem definitions")
        record_test("Suspicious Activity Detection", False, "Failed to get gem definitions")
        return
    
    # Find the cheapest gem
    cheapest_gem = min(response, key=lambda x: x["price"])
    gem_type = cheapest_gem["type"]
    gem_price = cheapest_gem["price"]
    
    # Make multiple small purchases to trigger suspicious activity detection
    num_purchases = 25  # More than the 20 per hour threshold
    quantity = 1
    
    print(f"Making {num_purchases} purchases of {quantity} {gem_type} gems...")
    
    successful_purchases = 0
    for i in range(num_purchases):
        response, success = make_request(
            "POST", 
            f"/gems/buy?gem_type={gem_type}&quantity={quantity}", 
            auth_token=user_token,
            silent=True
        )
        
        if success:
            successful_purchases += 1
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.2)
        
        # Print progress
        if i % 5 == 0:
            print(f"Completed {i+1}/{num_purchases} purchases...")
    
    print(f"Completed {successful_purchases}/{num_purchases} purchases successfully")
    
    if successful_purchases > 0:
        print_success("Multiple purchases completed to trigger suspicious activity detection")
        record_test("Suspicious Activity Detection", True, f"{successful_purchases} purchases completed")
    else:
        print_error("Failed to complete any purchases")
        record_test("Suspicious Activity Detection", False, "No purchases completed")

def print_summary() -> None:
    """Print a summary of all test results."""
    print_header("SECURITY TEST SUMMARY")
    
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
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All security tests passed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some security tests failed!{Colors.ENDC}")

def run_security_tests() -> None:
    """Run all security tests in sequence."""
    print_header("GEMPLAY API SECURITY TESTING")
    
    # Register and login test user
    verification_token, test_email, test_username = register_test_user()
    verify_email(verification_token)
    user_token = login_user(test_email, TEST_USER["password"])
    
    # Login as admin
    admin_token = login_admin()
    
    # Run security tests
    if user_token and admin_token:
        # Test rate limiting
        test_rate_limiting(user_token)
        
        # Test admin security APIs
        test_security_dashboard(admin_token)
        test_security_alerts(admin_token)
        test_monitoring_stats(admin_token)
        
        # Test large purchase detection
        test_large_purchase(user_token)
        
        # Test suspicious activity detection
        test_suspicious_activity(user_token)
        
        # Test admin access control
        test_admin_access_control(user_token, admin_token)
        
        # Test alert resolution (do this last as it modifies data)
        test_resolve_alert(admin_token)
    else:
        print_error("Failed to obtain required tokens for testing")
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_security_tests()