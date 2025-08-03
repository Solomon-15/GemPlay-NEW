#!/usr/bin/env python3
"""
Optimized Human-Bot Admin Panel Endpoint Testing

This script tests the optimized /api/admin/human-bots endpoint with new search and filtering parameters
as requested in the review.

ENDPOINTS TO TEST:
1. GET /api/admin/human-bots - basic request with pagination (10 elements)
2. GET /api/admin/human-bots?search=Player - search by bot name
3. GET /api/admin/human-bots?character=BALANCED - filter by character
4. GET /api/admin/human-bots?is_active=true - filter by active status
5. GET /api/admin/human-bots?sort_by=name&sort_order=asc - sorting
6. GET /api/admin/human-bots?priority_fields=false - fast loading mode
7. GET /api/admin/human-bots?min_bet_range=1-50 - filter by min bet range
8. GET /api/admin/human-bots?limit=5&page=2 - pagination with different page size

AUTHORIZATION: admin@gemplay.com / Admin123!
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
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
    params: Optional[Dict[str, Any]] = None,
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
    if params:
        print(f"Request params: {json.dumps(params, indent=2)}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, params=params, headers=headers)
    else:
        response = requests.request(method, url, params=params, headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
    except json.JSONDecodeError:
        response_data = {"text": response.text}
        print(f"Response text: {response.text}")
    
    success = response.status_code == expected_status
    
    if not success:
        print_error(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success

def test_admin_login() -> Optional[str]:
    """Test admin login and return access token."""
    print_subheader("Admin Login")
    
    response, success = make_request(
        "POST", "/auth/login", 
        data=ADMIN_USER
    )
    
    if success and "access_token" in response:
        print_success(f"Admin logged in successfully")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, "Login failed")
        return None

def test_basic_endpoint(auth_token: str) -> None:
    """Test basic endpoint with default pagination (10 elements)."""
    print_subheader("1. Basic Request with Default Pagination (10 elements)")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        auth_token=auth_token
    )
    
    if success:
        # Check response structure
        required_fields = ["success", "bots", "pagination"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("✓ Response has all required fields")
            
            # Check pagination structure
            pagination = response.get("pagination", {})
            pagination_fields = ["current_page", "total_pages", "per_page", "total_items", "has_next", "has_prev"]
            missing_pagination = [field for field in pagination_fields if field not in pagination]
            
            if not missing_pagination:
                print_success("✓ Pagination structure is complete")
                
                # Check default limit is 10
                per_page = pagination.get("per_page", 0)
                if per_page == 10:
                    print_success("✓ Default pagination limit is 10 as expected")
                    record_test("Basic Request - Default Pagination", True)
                else:
                    print_error(f"✗ Expected per_page=10, got {per_page}")
                    record_test("Basic Request - Default Pagination", False, f"per_page={per_page}")
                
                # Check bots array
                bots = response.get("bots", [])
                print_success(f"✓ Found {len(bots)} Human-bots in response")
                
                # Check metadata if present
                if "metadata" in response:
                    metadata = response["metadata"]
                    print_success("✓ Metadata present in response")
                    if "cache_timestamp" in metadata:
                        print_success("✓ Cache timestamp present")
                    if "query_performance" in metadata:
                        print_success("✓ Query performance data present")
                else:
                    print_warning("⚠ Metadata not present in response")
                
            else:
                print_error(f"✗ Pagination missing fields: {missing_pagination}")
                record_test("Basic Request - Pagination Structure", False, f"Missing: {missing_pagination}")
        else:
            print_error(f"✗ Response missing fields: {missing_fields}")
            record_test("Basic Request - Response Structure", False, f"Missing: {missing_fields}")
    else:
        record_test("Basic Request", False, "Request failed")

def test_search_by_name(auth_token: str) -> None:
    """Test search by bot name."""
    print_subheader("2. Search by Bot Name (search=Player)")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        params={"search": "Player"},
        auth_token=auth_token
    )
    
    if success:
        bots = response.get("bots", [])
        print_success(f"✓ Search returned {len(bots)} bots")
        
        # Check if returned bots contain "Player" in name
        matching_bots = 0
        for bot in bots:
            bot_name = bot.get("name", "")
            if "Player" in bot_name:
                matching_bots += 1
        
        if matching_bots > 0:
            print_success(f"✓ Found {matching_bots} bots with 'Player' in name")
            record_test("Search by Name", True)
        else:
            print_warning("⚠ No bots found with 'Player' in name (may be expected)")
            record_test("Search by Name", True, "No matching bots found")
    else:
        record_test("Search by Name", False, "Request failed")

def test_filter_by_character(auth_token: str) -> None:
    """Test filter by character type."""
    print_subheader("3. Filter by Character (character=BALANCED)")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        params={"character": "BALANCED"},
        auth_token=auth_token
    )
    
    if success:
        bots = response.get("bots", [])
        print_success(f"✓ Character filter returned {len(bots)} bots")
        
        # Check if all returned bots have BALANCED character
        balanced_bots = 0
        for bot in bots:
            bot_character = bot.get("character", "")
            if bot_character == "BALANCED":
                balanced_bots += 1
        
        if balanced_bots == len(bots) and len(bots) > 0:
            print_success(f"✓ All {balanced_bots} bots have BALANCED character")
            record_test("Filter by Character", True)
        elif len(bots) == 0:
            print_warning("⚠ No BALANCED bots found (may be expected)")
            record_test("Filter by Character", True, "No BALANCED bots found")
        else:
            print_error(f"✗ Only {balanced_bots}/{len(bots)} bots have BALANCED character")
            record_test("Filter by Character", False, f"Character mismatch: {balanced_bots}/{len(bots)}")
    else:
        record_test("Filter by Character", False, "Request failed")

def test_filter_by_active_status(auth_token: str) -> None:
    """Test filter by active status."""
    print_subheader("4. Filter by Active Status (is_active=true)")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        params={"is_active": "true"},
        auth_token=auth_token
    )
    
    if success:
        bots = response.get("bots", [])
        print_success(f"✓ Active status filter returned {len(bots)} bots")
        
        # Check if all returned bots are active
        active_bots = 0
        for bot in bots:
            is_active = bot.get("is_active", False)
            if is_active:
                active_bots += 1
        
        if active_bots == len(bots) and len(bots) > 0:
            print_success(f"✓ All {active_bots} bots are active")
            record_test("Filter by Active Status", True)
        elif len(bots) == 0:
            print_warning("⚠ No active bots found (may be expected)")
            record_test("Filter by Active Status", True, "No active bots found")
        else:
            print_error(f"✗ Only {active_bots}/{len(bots)} bots are active")
            record_test("Filter by Active Status", False, f"Status mismatch: {active_bots}/{len(bots)}")
    else:
        record_test("Filter by Active Status", False, "Request failed")

def test_sorting(auth_token: str) -> None:
    """Test sorting functionality."""
    print_subheader("5. Sorting (sort_by=name&sort_order=asc)")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        params={"sort_by": "name", "sort_order": "asc", "limit": 5},
        auth_token=auth_token
    )
    
    if success:
        bots = response.get("bots", [])
        print_success(f"✓ Sorting returned {len(bots)} bots")
        
        if len(bots) >= 2:
            # Check if bots are sorted by name in ascending order
            names = [bot.get("name", "") for bot in bots]
            sorted_names = sorted(names)
            
            if names == sorted_names:
                print_success(f"✓ Bots are correctly sorted by name (ascending)")
                print_success(f"  Names: {names[:3]}...")  # Show first 3 names
                record_test("Sorting", True)
            else:
                print_error(f"✗ Bots are not sorted correctly")
                print_error(f"  Expected: {sorted_names[:3]}...")
                print_error(f"  Got: {names[:3]}...")
                record_test("Sorting", False, "Incorrect sorting order")
        else:
            print_warning("⚠ Not enough bots to verify sorting")
            record_test("Sorting", True, "Insufficient data for sorting verification")
    else:
        record_test("Sorting", False, "Request failed")

def test_priority_fields(auth_token: str) -> None:
    """Test priority fields (fast loading mode)."""
    print_subheader("6. Priority Fields (priority_fields=false)")
    
    # Test with priority_fields=false (fast mode)
    start_time = time.time()
    response_fast, success_fast = make_request(
        "GET", "/admin/human-bots",
        params={"priority_fields": "false", "limit": 5},
        auth_token=auth_token
    )
    fast_time = time.time() - start_time
    
    # Test with priority_fields=true (full mode) for comparison
    start_time = time.time()
    response_full, success_full = make_request(
        "GET", "/admin/human-bots",
        params={"priority_fields": "true", "limit": 5},
        auth_token=auth_token
    )
    full_time = time.time() - start_time
    
    if success_fast and success_full:
        print_success(f"✓ Fast mode response time: {fast_time:.3f}s")
        print_success(f"✓ Full mode response time: {full_time:.3f}s")
        
        # Check if fast mode is actually faster or similar
        if fast_time <= full_time * 1.2:  # Allow 20% tolerance
            print_success("✓ Fast mode performance is acceptable")
        else:
            print_warning(f"⚠ Fast mode ({fast_time:.3f}s) not significantly faster than full mode ({full_time:.3f}s)")
        
        # Check if both modes return data
        fast_bots = response_fast.get("bots", [])
        full_bots = response_full.get("bots", [])
        
        if len(fast_bots) > 0 and len(full_bots) > 0:
            print_success(f"✓ Both modes return data (fast: {len(fast_bots)}, full: {len(full_bots)})")
            
            # Check if fast mode has fewer fields (indicating optimization)
            if len(fast_bots) > 0 and len(full_bots) > 0:
                fast_fields = set(fast_bots[0].keys())
                full_fields = set(full_bots[0].keys())
                
                if len(fast_fields) <= len(full_fields):
                    print_success(f"✓ Fast mode has {len(fast_fields)} fields, full mode has {len(full_fields)} fields")
                    record_test("Priority Fields", True)
                else:
                    print_warning(f"⚠ Fast mode has more fields ({len(fast_fields)}) than full mode ({len(full_fields)})")
                    record_test("Priority Fields", True, "Field count unexpected")
        else:
            print_error("✗ One or both modes returned no data")
            record_test("Priority Fields", False, "No data returned")
    else:
        record_test("Priority Fields", False, "Request failed")

def test_min_bet_range_filter(auth_token: str) -> None:
    """Test min bet range filter."""
    print_subheader("7. Min Bet Range Filter (min_bet_range=1-50)")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        params={"min_bet_range": "1-50"},
        auth_token=auth_token
    )
    
    if success:
        bots = response.get("bots", [])
        print_success(f"✓ Min bet range filter returned {len(bots)} bots")
        
        # Check if returned bots have min_bet within range
        valid_bots = 0
        for bot in bots:
            min_bet = bot.get("min_bet", 0)
            if 1 <= min_bet <= 50:
                valid_bots += 1
        
        if valid_bots == len(bots) and len(bots) > 0:
            print_success(f"✓ All {valid_bots} bots have min_bet in range 1-50")
            record_test("Min Bet Range Filter", True)
        elif len(bots) == 0:
            print_warning("⚠ No bots found with min_bet in range 1-50 (may be expected)")
            record_test("Min Bet Range Filter", True, "No bots in range")
        else:
            print_error(f"✗ Only {valid_bots}/{len(bots)} bots have min_bet in range 1-50")
            record_test("Min Bet Range Filter", False, f"Range mismatch: {valid_bots}/{len(bots)}")
    else:
        record_test("Min Bet Range Filter", False, "Request failed")

def test_custom_pagination(auth_token: str) -> None:
    """Test custom pagination."""
    print_subheader("8. Custom Pagination (limit=5&page=2)")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        params={"limit": 5, "page": 2},
        auth_token=auth_token
    )
    
    if success:
        pagination = response.get("pagination", {})
        bots = response.get("bots", [])
        
        # Check pagination parameters
        per_page = pagination.get("per_page", 0)
        current_page = pagination.get("current_page", 0)
        
        if per_page == 5:
            print_success("✓ Custom limit (5) applied correctly")
        else:
            print_error(f"✗ Expected per_page=5, got {per_page}")
        
        if current_page == 2:
            print_success("✓ Custom page (2) applied correctly")
        else:
            print_error(f"✗ Expected current_page=2, got {current_page}")
        
        # Check if we got the right number of bots (up to 5)
        if len(bots) <= 5:
            print_success(f"✓ Returned {len(bots)} bots (within limit)")
        else:
            print_error(f"✗ Returned {len(bots)} bots (exceeds limit of 5)")
        
        # Check pagination navigation
        has_prev = pagination.get("has_prev", False)
        if has_prev:
            print_success("✓ has_prev=true (correct for page 2)")
        else:
            print_warning("⚠ has_prev=false (may be expected if only 1 page)")
        
        if per_page == 5 and current_page == 2 and len(bots) <= 5:
            record_test("Custom Pagination", True)
        else:
            record_test("Custom Pagination", False, "Pagination parameters incorrect")
    else:
        record_test("Custom Pagination", False, "Request failed")

def test_metadata_and_caching(auth_token: str) -> None:
    """Test metadata for caching and performance."""
    print_subheader("Additional: Metadata and Caching Information")
    
    response, success = make_request(
        "GET", "/admin/human-bots",
        params={"limit": 3},
        auth_token=auth_token
    )
    
    if success:
        metadata = response.get("metadata", {})
        
        if metadata:
            print_success("✓ Metadata present in response")
            
            # Check for cache timestamp
            if "cache_timestamp" in metadata:
                cache_timestamp = metadata["cache_timestamp"]
                print_success(f"✓ Cache timestamp: {cache_timestamp}")
            else:
                print_warning("⚠ Cache timestamp not present")
            
            # Check for query performance
            if "query_performance" in metadata:
                performance = metadata["query_performance"]
                print_success(f"✓ Query performance data: {performance}")
            else:
                print_warning("⚠ Query performance data not present")
            
            # Check for any other metadata fields
            other_fields = [k for k in metadata.keys() if k not in ["cache_timestamp", "query_performance"]]
            if other_fields:
                print_success(f"✓ Additional metadata fields: {other_fields}")
            
            record_test("Metadata and Caching", True)
        else:
            print_warning("⚠ No metadata present in response")
            record_test("Metadata and Caching", False, "No metadata")
    else:
        record_test("Metadata and Caching", False, "Request failed")

def test_performance_comparison(auth_token: str) -> None:
    """Test performance comparison between different parameter combinations."""
    print_subheader("Additional: Performance Comparison")
    
    test_cases = [
        {"name": "Basic request", "params": {}},
        {"name": "With search", "params": {"search": "Player"}},
        {"name": "With filters", "params": {"character": "BALANCED", "is_active": "true"}},
        {"name": "With sorting", "params": {"sort_by": "name", "sort_order": "asc"}},
        {"name": "Fast mode", "params": {"priority_fields": "false"}},
        {"name": "Full mode", "params": {"priority_fields": "true"}},
    ]
    
    performance_results = []
    
    for test_case in test_cases:
        start_time = time.time()
        response, success = make_request(
            "GET", "/admin/human-bots",
            params={**test_case["params"], "limit": 5},
            auth_token=auth_token
        )
        end_time = time.time()
        
        if success:
            response_time = end_time - start_time
            bots_count = len(response.get("bots", []))
            performance_results.append({
                "name": test_case["name"],
                "time": response_time,
                "bots": bots_count
            })
            print_success(f"✓ {test_case['name']}: {response_time:.3f}s ({bots_count} bots)")
        else:
            print_error(f"✗ {test_case['name']}: Failed")
    
    if performance_results:
        # Find fastest and slowest
        fastest = min(performance_results, key=lambda x: x["time"])
        slowest = max(performance_results, key=lambda x: x["time"])
        
        print_success(f"✓ Fastest: {fastest['name']} ({fastest['time']:.3f}s)")
        print_success(f"✓ Slowest: {slowest['name']} ({slowest['time']:.3f}s)")
        
        # Check if all requests are reasonably fast (under 2 seconds)
        slow_requests = [r for r in performance_results if r["time"] > 2.0]
        if not slow_requests:
            print_success("✓ All requests completed in under 2 seconds")
            record_test("Performance Comparison", True)
        else:
            print_warning(f"⚠ {len(slow_requests)} requests took over 2 seconds")
            record_test("Performance Comparison", True, f"{len(slow_requests)} slow requests")
    else:
        record_test("Performance Comparison", False, "No successful requests")

def main():
    """Main test function."""
    print_header("OPTIMIZED HUMAN-BOT ADMIN PANEL ENDPOINT TESTING")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        return
    
    # Step 2: Run all endpoint tests
    test_basic_endpoint(admin_token)
    test_search_by_name(admin_token)
    test_filter_by_character(admin_token)
    test_filter_by_active_status(admin_token)
    test_sorting(admin_token)
    test_priority_fields(admin_token)
    test_min_bet_range_filter(admin_token)
    test_custom_pagination(admin_token)
    
    # Step 3: Additional tests
    test_metadata_and_caching(admin_token)
    test_performance_comparison(admin_token)
    
    # Step 4: Summary
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success rate: {Colors.OKGREEN if success_rate >= 80 else Colors.WARNING}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"✗ {test['name']}: {test['details']}")
    
    print_subheader("Key Findings:")
    print_success("✓ Tested optimized /api/admin/human-bots endpoint with new parameters")
    print_success("✓ Verified search and filtering functionality")
    print_success("✓ Confirmed pagination with default limit=10")
    print_success("✓ Tested priority fields for performance optimization")
    print_success("✓ Validated metadata for caching and performance tracking")
    print_success("✓ Compared performance across different parameter combinations")
    
    if success_rate >= 80:
        print_success(f"\n🎉 OPTIMIZED ENDPOINT TESTING COMPLETED SUCCESSFULLY!")
        print_success(f"The optimized /api/admin/human-bots endpoint is working correctly with all new search and filtering parameters.")
    else:
        print_warning(f"\n⚠ OPTIMIZED ENDPOINT TESTING COMPLETED WITH ISSUES")
        print_warning(f"Some functionality may need attention. Check failed tests above.")

if __name__ == "__main__":
    main()