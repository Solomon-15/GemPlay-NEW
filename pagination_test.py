#!/usr/bin/env python3
"""
Comprehensive Pagination System Testing
Tests the unified pagination implementation across all admin panel components
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://1d0f5194-c2ea-48bb-8046-de706bbab2f8.preview.emergentagent.com/api"
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

def log_test_result(test_name: str, passed: bool, details: str = ""):
    """Log test result."""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}"
    else:
        test_results["failed"] += 1
        status = f"{Colors.FAIL}FAIL{Colors.ENDC}"
    
    test_results["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    
    print(f"[{status}] {test_name}")
    if details:
        print(f"    {details}")

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[Optional[Dict], int, str]:
    """Make HTTP request and return response data, status code, and error message."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, params=params, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return None, 400, f"Unsupported method: {method}"
        
        try:
            response_data = response.json()
        except:
            response_data = {"message": response.text}
        
        return response_data, response.status_code, ""
        
    except requests.exceptions.Timeout:
        return None, 408, "Request timeout"
    except requests.exceptions.ConnectionError:
        return None, 503, "Connection error"
    except Exception as e:
        return None, 500, str(e)

def login_admin() -> Optional[str]:
    """Login as admin and return access token."""
    print(f"{Colors.HEADER}=== ADMIN LOGIN ==={Colors.ENDC}")
    
    response_data, status_code, error = make_request(
        "POST", 
        "/auth/login", 
        data=ADMIN_USER
    )
    
    if status_code == 200 and response_data and "access_token" in response_data:
        print(f"{Colors.OKGREEN}✓ Admin login successful{Colors.ENDC}")
        return response_data["access_token"]
    else:
        print(f"{Colors.FAIL}✗ Admin login failed: {error or response_data}{Colors.ENDC}")
        return None

def test_pagination_response_structure(response_data: Dict, test_name: str) -> bool:
    """Test if pagination response has correct structure."""
    required_fields = ["total_count", "current_page", "total_pages", "items_per_page", "has_next", "has_prev"]
    
    missing_fields = []
    for field in required_fields:
        if field not in response_data:
            missing_fields.append(field)
    
    if missing_fields:
        log_test_result(
            f"{test_name} - Response Structure",
            False,
            f"Missing pagination fields: {missing_fields}"
        )
        return False
    
    # Validate field types
    type_validations = [
        ("total_count", int),
        ("current_page", int),
        ("total_pages", int),
        ("items_per_page", int),
        ("has_next", bool),
        ("has_prev", bool)
    ]
    
    type_errors = []
    for field, expected_type in type_validations:
        if not isinstance(response_data[field], expected_type):
            type_errors.append(f"{field} should be {expected_type.__name__}, got {type(response_data[field]).__name__}")
    
    if type_errors:
        log_test_result(
            f"{test_name} - Field Types",
            False,
            f"Type validation errors: {type_errors}"
        )
        return False
    
    log_test_result(f"{test_name} - Response Structure", True, "All pagination fields present with correct types")
    return True

def test_pagination_logic(response_data: Dict, page: int, limit: int, test_name: str) -> bool:
    """Test pagination logic calculations."""
    total_count = response_data["total_count"]
    current_page = response_data["current_page"]
    total_pages = response_data["total_pages"]
    items_per_page = response_data["items_per_page"]
    has_next = response_data["has_next"]
    has_prev = response_data["has_prev"]
    
    errors = []
    
    # Test current_page matches request
    if current_page != page:
        errors.append(f"current_page ({current_page}) != requested page ({page})")
    
    # Test items_per_page matches request
    if items_per_page != limit:
        errors.append(f"items_per_page ({items_per_page}) != requested limit ({limit})")
    
    # Test total_pages calculation
    expected_total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    if total_pages != expected_total_pages:
        errors.append(f"total_pages ({total_pages}) != expected ({expected_total_pages})")
    
    # Test has_next logic
    expected_has_next = page < total_pages
    if has_next != expected_has_next:
        errors.append(f"has_next ({has_next}) != expected ({expected_has_next})")
    
    # Test has_prev logic
    expected_has_prev = page > 1
    if has_prev != expected_has_prev:
        errors.append(f"has_prev ({has_prev}) != expected ({expected_has_prev})")
    
    if errors:
        log_test_result(
            f"{test_name} - Pagination Logic",
            False,
            f"Logic errors: {errors}"
        )
        return False
    
    log_test_result(f"{test_name} - Pagination Logic", True, "All pagination calculations correct")
    return True

def test_regular_bots_pagination(token: str):
    """Test GET /api/admin/bots/regular/list pagination."""
    print(f"\n{Colors.HEADER}=== TESTING REGULAR BOTS PAGINATION ==={Colors.ENDC}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Default pagination (page=1, limit=10)
    response_data, status_code, error = make_request(
        "GET", 
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if status_code != 200:
        log_test_result("Regular Bots - Default Pagination", False, f"HTTP {status_code}: {error or response_data}")
        return
    
    log_test_result("Regular Bots - Default Pagination", True, f"HTTP 200, got {len(response_data.get('bots', []))} bots")
    
    # Test response structure
    test_pagination_response_structure(response_data, "Regular Bots - Default")
    
    # Test pagination logic
    test_pagination_logic(response_data, 1, 10, "Regular Bots - Default")
    
    # Test 2: Custom pagination parameters
    test_cases = [
        {"page": 1, "limit": 5},
        {"page": 2, "limit": 10},
        {"page": 1, "limit": 20},
    ]
    
    for case in test_cases:
        response_data, status_code, error = make_request(
            "GET", 
            "/admin/bots/regular/list",
            headers=headers,
            params=case
        )
        
        if status_code == 200:
            log_test_result(
                f"Regular Bots - Page {case['page']}, Limit {case['limit']}", 
                True, 
                f"Got {len(response_data.get('bots', []))} bots"
            )
            test_pagination_response_structure(response_data, f"Regular Bots - Page {case['page']}")
            test_pagination_logic(response_data, case['page'], case['limit'], f"Regular Bots - Page {case['page']}")
        else:
            log_test_result(
                f"Regular Bots - Page {case['page']}, Limit {case['limit']}", 
                False, 
                f"HTTP {status_code}: {error or response_data}"
            )
    
    # Test 3: Edge cases
    edge_cases = [
        {"page": 0, "limit": 10, "expected_page": 1},  # Invalid page should default to 1
        {"page": -1, "limit": 10, "expected_page": 1},  # Negative page should default to 1
        {"page": 1, "limit": 0, "expected_limit": 10},  # Invalid limit should default to 10
        {"page": 1, "limit": -5, "expected_limit": 10},  # Negative limit should default to 10
        {"page": 1, "limit": 150, "expected_limit": 10},  # Limit > 100 should default to 10
        {"page": 999, "limit": 10},  # Very large page number
    ]
    
    for case in edge_cases:
        params = {"page": case["page"], "limit": case["limit"]}
        response_data, status_code, error = make_request(
            "GET", 
            "/admin/bots/regular/list",
            headers=headers,
            params=params
        )
        
        if status_code == 200:
            expected_page = case.get("expected_page", case["page"])
            expected_limit = case.get("expected_limit", case["limit"])
            
            actual_page = response_data.get("current_page")
            actual_limit = response_data.get("items_per_page")
            
            if actual_page == expected_page and actual_limit == expected_limit:
                log_test_result(
                    f"Regular Bots - Edge Case: page={case['page']}, limit={case['limit']}", 
                    True, 
                    f"Correctly handled: page={actual_page}, limit={actual_limit}"
                )
            else:
                log_test_result(
                    f"Regular Bots - Edge Case: page={case['page']}, limit={case['limit']}", 
                    False, 
                    f"Expected page={expected_page}, limit={expected_limit}, got page={actual_page}, limit={actual_limit}"
                )
        else:
            log_test_result(
                f"Regular Bots - Edge Case: page={case['page']}, limit={case['limit']}", 
                False, 
                f"HTTP {status_code}: {error or response_data}"
            )

def test_profit_entries_pagination(token: str):
    """Test GET /api/admin/profit/entries pagination."""
    print(f"\n{Colors.HEADER}=== TESTING PROFIT ENTRIES PAGINATION ==={Colors.ENDC}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Default pagination (page=1, limit=10)
    response_data, status_code, error = make_request(
        "GET", 
        "/admin/profit/entries",
        headers=headers
    )
    
    if status_code != 200:
        log_test_result("Profit Entries - Default Pagination", False, f"HTTP {status_code}: {error or response_data}")
        return
    
    log_test_result("Profit Entries - Default Pagination", True, f"HTTP 200, got {len(response_data.get('entries', []))} entries")
    
    # Test response structure (profit entries uses slightly different field names)
    required_fields = ["total_count", "page", "limit", "total_pages"]
    missing_fields = []
    for field in required_fields:
        if field not in response_data:
            missing_fields.append(field)
    
    if missing_fields:
        log_test_result("Profit Entries - Response Structure", False, f"Missing fields: {missing_fields}")
    else:
        log_test_result("Profit Entries - Response Structure", True, "All required pagination fields present")
    
    # Test 2: Verify 10 items per page default
    if response_data.get("limit") == 10:
        log_test_result("Profit Entries - Default Limit", True, "Default limit is 10 items per page")
    else:
        log_test_result("Profit Entries - Default Limit", False, f"Expected limit=10, got {response_data.get('limit')}")
    
    # Test 3: Custom pagination parameters
    test_cases = [
        {"page": 1, "limit": 5},
        {"page": 2, "limit": 10},
        {"page": 1, "limit": 15},
    ]
    
    for case in test_cases:
        response_data, status_code, error = make_request(
            "GET", 
            "/admin/profit/entries",
            headers=headers,
            params=case
        )
        
        if status_code == 200:
            actual_page = response_data.get("page")
            actual_limit = response_data.get("limit")
            
            if actual_page == case["page"] and actual_limit == case["limit"]:
                log_test_result(
                    f"Profit Entries - Page {case['page']}, Limit {case['limit']}", 
                    True, 
                    f"Got {len(response_data.get('entries', []))} entries"
                )
            else:
                log_test_result(
                    f"Profit Entries - Page {case['page']}, Limit {case['limit']}", 
                    False, 
                    f"Expected page={case['page']}, limit={case['limit']}, got page={actual_page}, limit={actual_limit}"
                )
        else:
            log_test_result(
                f"Profit Entries - Page {case['page']}, Limit {case['limit']}", 
                False, 
                f"HTTP {status_code}: {error or response_data}"
            )
    
    # Test 4: Test with entry_type filter
    response_data, status_code, error = make_request(
        "GET", 
        "/admin/profit/entries",
        headers=headers,
        params={"page": 1, "limit": 10, "entry_type": "BET_COMMISSION"}
    )
    
    if status_code == 200:
        log_test_result("Profit Entries - With Filter", True, f"Filtered results: {len(response_data.get('entries', []))} entries")
    else:
        log_test_result("Profit Entries - With Filter", False, f"HTTP {status_code}: {error or response_data}")

def test_pagination_consistency():
    """Test consistency across different paginated endpoints."""
    print(f"\n{Colors.HEADER}=== TESTING PAGINATION CONSISTENCY ==={Colors.ENDC}")
    
    token = login_admin()
    if not token:
        log_test_result("Pagination Consistency", False, "Failed to login as admin")
        return
    
    # Test both endpoints with same parameters
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": 1, "limit": 10}
    
    # Get responses from both endpoints
    bots_response, bots_status, _ = make_request("GET", "/admin/bots/regular/list", headers=headers, params=params)
    profit_response, profit_status, _ = make_request("GET", "/admin/profit/entries", headers=headers, params=params)
    
    if bots_status == 200 and profit_status == 200:
        # Check if both use 10 as default limit
        bots_limit = bots_response.get("items_per_page")
        profit_limit = profit_response.get("limit")
        
        if bots_limit == 10 and profit_limit == 10:
            log_test_result("Pagination Consistency - Default Limit", True, "Both endpoints use 10 items per page default")
        else:
            log_test_result("Pagination Consistency - Default Limit", False, f"Bots limit: {bots_limit}, Profit limit: {profit_limit}")
        
        # Check pagination structure consistency
        bots_has_pagination = all(field in bots_response for field in ["total_count", "current_page", "total_pages"])
        profit_has_pagination = all(field in profit_response for field in ["total_count", "page", "total_pages"])
        
        if bots_has_pagination and profit_has_pagination:
            log_test_result("Pagination Consistency - Structure", True, "Both endpoints have proper pagination structure")
        else:
            log_test_result("Pagination Consistency - Structure", False, f"Bots pagination: {bots_has_pagination}, Profit pagination: {profit_has_pagination}")
    else:
        log_test_result("Pagination Consistency", False, f"Failed to get responses: Bots {bots_status}, Profit {profit_status}")

def print_test_summary():
    """Print test summary."""
    print(f"\n{Colors.HEADER}=== TEST SUMMARY ==={Colors.ENDC}")
    print(f"Total tests: {test_results['total']}")
    print(f"{Colors.OKGREEN}Passed: {test_results['passed']}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {test_results['failed']}{Colors.ENDC}")
    
    if test_results['failed'] > 0:
        print(f"\n{Colors.FAIL}Failed tests:{Colors.ENDC}")
        for test in test_results['tests']:
            if not test['passed']:
                print(f"  - {test['name']}: {test['details']}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"{Colors.OKGREEN}✓ Pagination system is working correctly!{Colors.ENDC}")
    elif success_rate >= 70:
        print(f"{Colors.WARNING}⚠ Pagination system has some issues but is mostly functional{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ Pagination system has significant issues{Colors.ENDC}")

def main():
    """Main test function."""
    print(f"{Colors.BOLD}UNIFIED PAGINATION SYSTEM TESTING{Colors.ENDC}")
    print(f"Testing pagination implementation across admin panel components")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Login as admin
    token = login_admin()
    if not token:
        print(f"{Colors.FAIL}Cannot proceed without admin authentication{Colors.ENDC}")
        sys.exit(1)
    
    # Run pagination tests
    test_regular_bots_pagination(token)
    test_profit_entries_pagination(token)
    test_pagination_consistency()
    
    # Print summary
    print_test_summary()
    
    # Exit with appropriate code
    if test_results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()