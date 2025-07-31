#!/usr/bin/env python3
import requests
import json
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://85245bb1-9423-4f57-ad61-2213aa95b2ae.preview.emergentagent.com/api"
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

def test_admin_login() -> Optional[str]:
    """Test admin login."""
    print_subheader("Testing POST /api/auth/login (Admin)")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response and "user" in response:
        print_success(f"Admin logged in successfully")
        print_success(f"Admin details: {response['user']['username']} ({response['user']['email']})")
        print_success(f"Admin role: {response['user']['role']}")
        record_test("POST /api/auth/login (Admin)", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("POST /api/auth/login (Admin)", False, f"Login failed: {response}")
        return None

def test_profit_stats(admin_token: str) -> Dict[str, Any]:
    """Test getting profit statistics."""
    print_subheader("Testing GET /api/admin/profit/stats")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/admin/profit/stats", False, "No admin token available")
        return {}
    
    response, success = make_request("GET", "/admin/profit/stats", auth_token=admin_token)
    
    if success:
        print_success(f"Got profit statistics")
        for profit_type, amount in response.items():
            print_success(f"{profit_type}: ${amount}")
        record_test("GET /api/admin/profit/stats", True)
        return response
    else:
        record_test("GET /api/admin/profit/stats", False, "Request failed")
    
    return {}

def test_profit_commission_settings(admin_token: str) -> Dict[str, Any]:
    """Test getting profit commission settings."""
    print_subheader("Testing GET /api/admin/profit/commission-settings")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/admin/profit/commission-settings", False, "No admin token available")
        return {}
    
    response, success = make_request("GET", "/admin/profit/commission-settings", auth_token=admin_token)
    
    if success:
        print_success(f"Got profit commission settings")
        for setting_name, value in response.items():
            print_success(f"{setting_name}: {value}")
        record_test("GET /api/admin/profit/commission-settings", True)
        return response
    else:
        record_test("GET /api/admin/profit/commission-settings", False, "Request failed")
    
    return {}

def test_profit_entries(admin_token: str) -> Dict[str, Any]:
    """Test getting profit entries."""
    print_subheader("Testing GET /api/admin/profit/entries")
    
    if not admin_token:
        print_error("No admin token available")
        record_test("GET /api/admin/profit/entries", False, "No admin token available")
        return {}
    
    response, success = make_request("GET", "/admin/profit/entries", auth_token=admin_token)
    
    if success:
        if isinstance(response, dict) and "entries" in response:
            entries = response["entries"]
            print_success(f"Got profit entries: {len(entries)} entries")
            print_success(f"Total entries: {response['total_count']}")
            print_success(f"Page: {response['page']}")
            print_success(f"Limit: {response['limit']}")
            print_success(f"Total pages: {response['total_pages']}")
            
            if entries and len(entries) > 0:
                for entry in entries[:3]:  # Show first 3 entries
                    print_success(f"Entry: {entry['entry_type']} - ${entry['amount']} - {entry['description']}")
            else:
                print_success("No profit entries found (empty list)")
                
            record_test("GET /api/admin/profit/entries", True)
            return response
        else:
            print_error(f"Profit entries response missing expected fields: {response}")
            record_test("GET /api/admin/profit/entries", False, "Response missing expected fields")
    else:
        record_test("GET /api/admin/profit/entries", False, "Request failed")
    
    return {}

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

def run_profit_api_tests() -> None:
    """Run profit API tests."""
    print_header("GEMPLAY PROFIT API TESTING")
    
    # Test 1: Admin Login
    admin_token = test_admin_login()
    
    if not admin_token:
        print_error("Admin login failed, cannot proceed with further tests")
        print_summary()
        return
    
    # Test 2: Get Profit Stats
    test_profit_stats(admin_token)
    
    # Test 3: Get Profit Commission Settings
    test_profit_commission_settings(admin_token)
    
    # Test 4: Get Profit Entries
    test_profit_entries(admin_token)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_profit_api_tests()