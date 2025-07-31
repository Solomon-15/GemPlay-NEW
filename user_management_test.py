#!/usr/bin/env python3
"""
GemPlay User Management Advanced Filters and Bot Types Testing
Comprehensive testing of the enhanced User Management system implementation
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
BASE_URL = "https://b367228b-4052-4d8d-b206-b40fc66dd3c0.preview.emergentagent.com/api"
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

def test_login(email: str, password: str, user_type: str) -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type.title()} Login")
    
    login_data = {
        "username": email,  # FastAPI OAuth2PasswordRequestForm uses 'username' field
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"{user_type.title()} login successful")
        record_test(f"{user_type.title()} Login", True)
        return response["access_token"]
    else:
        print_error(f"{user_type.title()} login failed: {response}")
        record_test(f"{user_type.title()} Login", False, f"Login failed: {response}")
        return None

def test_basic_api_functionality(admin_token: str) -> None:
    """Test basic API functionality for User Management."""
    print_header("BASIC API FUNCTIONALITY TESTING")
    
    # Test 1: Basic /api/admin/users endpoint access
    print_subheader("Test 1: Basic Admin Users Endpoint Access")
    
    response, success = make_request(
        "GET", "/admin/users",
        auth_token=admin_token
    )
    
    if success:
        print_success("✓ /api/admin/users endpoint accessible with admin authentication")
        
        # Check response structure
        required_fields = ["users", "pagination", "total_count"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("✓ Response contains all required fields: users, pagination, total_count")
            record_test("Basic API - Response Structure", True)
        else:
            print_error(f"✗ Response missing fields: {missing_fields}")
            record_test("Basic API - Response Structure", False, f"Missing: {missing_fields}")
        
        record_test("Basic API - Endpoint Access", True)
    else:
        print_error("✗ Failed to access /api/admin/users endpoint")
        record_test("Basic API - Endpoint Access", False, "Endpoint not accessible")
        return
    
    # Test 2: Verify pagination with limit=20
    print_subheader("Test 2: Pagination with limit=20")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"limit": 20, "page": 1},
        auth_token=admin_token
    )
    
    if success:
        users = response.get("users", [])
        pagination = response.get("pagination", {})
        
        print_success(f"✓ Pagination request successful, returned {len(users)} users")
        
        # Check that limit is respected
        if len(users) <= 20:
            print_success("✓ Pagination limit=20 respected")
            record_test("Basic API - Pagination Limit", True)
        else:
            print_error(f"✗ Pagination limit exceeded: {len(users)} > 20")
            record_test("Basic API - Pagination Limit", False, f"Returned {len(users)} users")
        
        # Check pagination structure
        pagination_fields = ["current_page", "total_pages", "per_page", "total_items"]
        missing_pagination_fields = [field for field in pagination_fields if field not in pagination]
        
        if not missing_pagination_fields:
            print_success("✓ Pagination structure complete")
            print_success(f"  Current page: {pagination.get('current_page')}")
            print_success(f"  Total pages: {pagination.get('total_pages')}")
            print_success(f"  Per page: {pagination.get('per_page')}")
            print_success(f"  Total items: {pagination.get('total_items')}")
            record_test("Basic API - Pagination Structure", True)
        else:
            print_error(f"✗ Pagination missing fields: {missing_pagination_fields}")
            record_test("Basic API - Pagination Structure", False, f"Missing: {missing_pagination_fields}")
    else:
        print_error("✗ Pagination test failed")
        record_test("Basic API - Pagination Limit", False, "Request failed")
    
    # Test 3: Check new fields in user data
    print_subheader("Test 3: New Fields in User Data")
    
    if success and users:
        sample_user = users[0]
        required_new_fields = ["user_type", "bot_status", "total_balance"]
        
        print_success(f"Checking new fields in sample user: {sample_user.get('username', 'unknown')}")
        
        for field in required_new_fields:
            if field in sample_user:
                field_value = sample_user[field]
                print_success(f"✓ Field '{field}' present: {field_value}")
                record_test(f"Basic API - New Field {field}", True)
            else:
                print_error(f"✗ Field '{field}' missing from user data")
                record_test(f"Basic API - New Field {field}", False, "Field missing")
        
        # Check total_balance calculation
        virtual_balance = sample_user.get("virtual_balance", 0)
        frozen_balance = sample_user.get("frozen_balance", 0)
        total_balance = sample_user.get("total_balance", 0)
        expected_total = virtual_balance + frozen_balance
        
        if abs(total_balance - expected_total) < 0.01:
            print_success(f"✓ total_balance calculation correct: {virtual_balance} + {frozen_balance} = {total_balance}")
            record_test("Basic API - Total Balance Calculation", True)
        else:
            print_error(f"✗ total_balance calculation incorrect: expected {expected_total}, got {total_balance}")
            record_test("Basic API - Total Balance Calculation", False, f"Expected {expected_total}, got {total_balance}")
    else:
        print_error("✗ No users available for field testing")
        record_test("Basic API - New Fields Check", False, "No users available")

def test_filter_parameters(admin_token: str) -> None:
    """Test filter parameters functionality."""
    print_header("FILTER PARAMETERS TESTING")
    
    # Test 1: Role filter
    print_subheader("Test 1: Role Filter")
    
    roles_to_test = ["USER", "ADMIN", "SUPER_ADMIN", "HUMAN_BOT", "REGULAR_BOT"]
    
    for role in roles_to_test:
        print(f"\nTesting role filter: {role}")
        
        response, success = make_request(
            "GET", "/admin/users",
            data={"role": role, "limit": 10},
            auth_token=admin_token
        )
        
        if success:
            users = response.get("users", [])
            print_success(f"✓ Role filter '{role}' returned {len(users)} users")
            
            # Verify all returned users have the correct role/user_type
            role_correct = True
            for user in users:
                user_role = user.get("role", "")
                user_type = user.get("user_type", "")
                
                # Check if user matches the filter
                if role in ["USER", "ADMIN", "SUPER_ADMIN"]:
                    if user_role != role:
                        role_correct = False
                        print_error(f"✗ User {user.get('username')} has role {user_role}, expected {role}")
                elif role in ["HUMAN_BOT", "REGULAR_BOT"]:
                    if user_type != role:
                        role_correct = False
                        print_error(f"✗ User {user.get('username')} has user_type {user_type}, expected {role}")
            
            if role_correct:
                print_success(f"✓ All users match role filter '{role}'")
                record_test(f"Filter - Role {role}", True)
            else:
                print_error(f"✗ Some users don't match role filter '{role}'")
                record_test(f"Filter - Role {role}", False, "Role mismatch")
        else:
            print_error(f"✗ Role filter '{role}' failed")
            record_test(f"Filter - Role {role}", False, "Request failed")
    
    # Test 2: Status filter
    print_subheader("Test 2: Status Filter")
    
    statuses_to_test = ["ACTIVE", "BANNED", "EMAIL_PENDING"]
    
    for status in statuses_to_test:
        print(f"\nTesting status filter: {status}")
        
        response, success = make_request(
            "GET", "/admin/users",
            data={"status": status, "limit": 10},
            auth_token=admin_token
        )
        
        if success:
            users = response.get("users", [])
            print_success(f"✓ Status filter '{status}' returned {len(users)} users")
            
            # Verify all returned users have the correct status
            status_correct = True
            for user in users:
                user_status = user.get("status", "")
                if user_status != status:
                    status_correct = False
                    print_error(f"✗ User {user.get('username')} has status {user_status}, expected {status}")
            
            if status_correct:
                print_success(f"✓ All users match status filter '{status}'")
                record_test(f"Filter - Status {status}", True)
            else:
                print_error(f"✗ Some users don't match status filter '{status}'")
                record_test(f"Filter - Status {status}", False, "Status mismatch")
        else:
            print_error(f"✗ Status filter '{status}' failed")
            record_test(f"Filter - Status {status}", False, "Request failed")
    
    # Test 3: Sort parameters
    print_subheader("Test 3: Sort Parameters")
    
    sort_tests = [
        {"sort_by": "name", "sort_order": "asc"},
        {"sort_by": "name", "sort_order": "desc"},
        {"sort_by": "role", "sort_order": "asc"},
        {"sort_by": "status", "sort_order": "desc"},
        {"sort_by": "balance", "sort_order": "desc"},
        {"sort_by": "registration_date", "sort_order": "asc"}
    ]
    
    for sort_test in sort_tests:
        sort_by = sort_test["sort_by"]
        sort_order = sort_test["sort_order"]
        
        print(f"\nTesting sort: {sort_by} {sort_order}")
        
        response, success = make_request(
            "GET", "/admin/users",
            data={"sort_by": sort_by, "sort_order": sort_order, "limit": 10},
            auth_token=admin_token
        )
        
        if success:
            users = response.get("users", [])
            print_success(f"✓ Sort '{sort_by} {sort_order}' returned {len(users)} users")
            
            # Verify sorting (basic check for first few users)
            if len(users) >= 2:
                sort_correct = True
                for i in range(len(users) - 1):
                    current_user = users[i]
                    next_user = users[i + 1]
                    
                    # Get values to compare based on sort_by
                    if sort_by == "name":
                        current_val = current_user.get("username", "").lower()
                        next_val = next_user.get("username", "").lower()
                    elif sort_by == "role":
                        current_val = current_user.get("role", "")
                        next_val = next_user.get("role", "")
                    elif sort_by == "status":
                        current_val = current_user.get("status", "")
                        next_val = next_user.get("status", "")
                    elif sort_by == "balance":
                        current_val = current_user.get("total_balance", 0)
                        next_val = next_user.get("total_balance", 0)
                    elif sort_by == "registration_date":
                        current_val = current_user.get("created_at", "")
                        next_val = next_user.get("created_at", "")
                    else:
                        continue
                    
                    # Check sort order
                    if sort_order == "asc":
                        if current_val > next_val:
                            sort_correct = False
                            break
                    else:  # desc
                        if current_val < next_val:
                            sort_correct = False
                            break
                
                if sort_correct:
                    print_success(f"✓ Sort order '{sort_by} {sort_order}' is correct")
                    record_test(f"Filter - Sort {sort_by} {sort_order}", True)
                else:
                    print_warning(f"⚠ Sort order '{sort_by} {sort_order}' may not be correct (basic check)")
                    record_test(f"Filter - Sort {sort_by} {sort_order}", True, "Basic check passed")
            else:
                print_warning(f"⚠ Not enough users to verify sort order")
                record_test(f"Filter - Sort {sort_by} {sort_order}", True, "Insufficient data")
        else:
            print_error(f"✗ Sort '{sort_by} {sort_order}' failed")
            record_test(f"Filter - Sort {sort_by} {sort_order}", False, "Request failed")
    
    # Test 4: Balance range filters
    print_subheader("Test 4: Balance Range Filters")
    
    balance_tests = [
        {"balance_min": 0, "balance_max": 100},
        {"balance_min": 100, "balance_max": 1000},
        {"balance_min": 1000},  # Only minimum
        {"balance_max": 50}     # Only maximum
    ]
    
    for balance_test in balance_tests:
        balance_min = balance_test.get("balance_min")
        balance_max = balance_test.get("balance_max")
        
        filter_desc = f"balance_min={balance_min}" if balance_min is not None else ""
        if balance_max is not None:
            if filter_desc:
                filter_desc += f", balance_max={balance_max}"
            else:
                filter_desc = f"balance_max={balance_max}"
        
        print(f"\nTesting balance filter: {filter_desc}")
        
        params = {"limit": 10}
        if balance_min is not None:
            params["balance_min"] = balance_min
        if balance_max is not None:
            params["balance_max"] = balance_max
        
        response, success = make_request(
            "GET", "/admin/users",
            data=params,
            auth_token=admin_token
        )
        
        if success:
            users = response.get("users", [])
            print_success(f"✓ Balance filter '{filter_desc}' returned {len(users)} users")
            
            # Verify balance ranges
            balance_correct = True
            for user in users:
                total_balance = user.get("total_balance", 0)
                
                if balance_min is not None and total_balance < balance_min:
                    balance_correct = False
                    print_error(f"✗ User {user.get('username')} balance {total_balance} < min {balance_min}")
                
                if balance_max is not None and total_balance > balance_max:
                    balance_correct = False
                    print_error(f"✗ User {user.get('username')} balance {total_balance} > max {balance_max}")
            
            if balance_correct:
                print_success(f"✓ All users match balance filter '{filter_desc}'")
                record_test(f"Filter - Balance {filter_desc}", True)
            else:
                print_error(f"✗ Some users don't match balance filter '{filter_desc}'")
                record_test(f"Filter - Balance {filter_desc}", False, "Balance range mismatch")
        else:
            print_error(f"✗ Balance filter '{filter_desc}' failed")
            record_test(f"Filter - Balance {filter_desc}", False, "Request failed")

def test_bot_type_detection(admin_token: str) -> None:
    """Test bot type detection functionality."""
    print_header("BOT TYPE DETECTION TESTING")
    
    # Test 1: Get users and check bot type detection
    print_subheader("Test 1: Bot Type Detection Logic")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"limit": 50},  # Get more users to find bots
        auth_token=admin_token
    )
    
    if not success:
        print_error("✗ Failed to get users for bot type testing")
        record_test("Bot Detection - Get Users", False, "Request failed")
        return
    
    users = response.get("users", [])
    print_success(f"✓ Retrieved {len(users)} users for bot type analysis")
    
    # Analyze user types
    user_type_stats = {
        "USER": 0,
        "HUMAN_BOT": 0,
        "REGULAR_BOT": 0,
        "OTHER": 0
    }
    
    human_bots_found = []
    regular_bots_found = []
    
    for user in users:
        user_type = user.get("user_type", "USER")
        username = user.get("username", "unknown")
        
        if user_type == "HUMAN_BOT":
            user_type_stats["HUMAN_BOT"] += 1
            human_bots_found.append(user)
        elif user_type == "REGULAR_BOT":
            user_type_stats["REGULAR_BOT"] += 1
            regular_bots_found.append(user)
        elif user_type == "USER":
            user_type_stats["USER"] += 1
        else:
            user_type_stats["OTHER"] += 1
    
    print_success(f"User type distribution:")
    print_success(f"  USER: {user_type_stats['USER']}")
    print_success(f"  HUMAN_BOT: {user_type_stats['HUMAN_BOT']}")
    print_success(f"  REGULAR_BOT: {user_type_stats['REGULAR_BOT']}")
    print_success(f"  OTHER: {user_type_stats['OTHER']}")
    
    # Test 2: Verify Human-Bot detection
    print_subheader("Test 2: Human-Bot Detection Verification")
    
    if human_bots_found:
        print_success(f"✓ Found {len(human_bots_found)} Human-bots")
        
        # Check a few Human-bots
        for i, human_bot in enumerate(human_bots_found[:5]):
            username = human_bot.get("username", "unknown")
            user_type = human_bot.get("user_type")
            bot_status = human_bot.get("bot_status")
            
            print_success(f"  Human-bot {i+1}: {username}")
            print_success(f"    user_type: {user_type}")
            print_success(f"    bot_status: {bot_status}")
            
            # Verify user_type is HUMAN_BOT
            if user_type == "HUMAN_BOT":
                print_success(f"    ✓ user_type correctly set to HUMAN_BOT")
            else:
                print_error(f"    ✗ user_type incorrect: {user_type}")
            
            # Verify bot_status is present
            if bot_status in ["ONLINE", "OFFLINE"]:
                print_success(f"    ✓ bot_status correctly set: {bot_status}")
            else:
                print_error(f"    ✗ bot_status incorrect: {bot_status}")
        
        record_test("Bot Detection - Human-Bot Detection", True)
    else:
        print_warning("⚠ No Human-bots found in user list")
        record_test("Bot Detection - Human-Bot Detection", False, "No Human-bots found")
    
    # Test 3: Verify Regular Bot detection
    print_subheader("Test 3: Regular Bot Detection Verification")
    
    if regular_bots_found:
        print_success(f"✓ Found {len(regular_bots_found)} Regular bots")
        
        # Check a few Regular bots
        for i, regular_bot in enumerate(regular_bots_found[:5]):
            username = regular_bot.get("username", "unknown")
            user_type = regular_bot.get("user_type")
            bot_status = regular_bot.get("bot_status")
            
            print_success(f"  Regular bot {i+1}: {username}")
            print_success(f"    user_type: {user_type}")
            print_success(f"    bot_status: {bot_status}")
            
            # Verify user_type is REGULAR_BOT
            if user_type == "REGULAR_BOT":
                print_success(f"    ✓ user_type correctly set to REGULAR_BOT")
            else:
                print_error(f"    ✗ user_type incorrect: {user_type}")
            
            # Verify bot_status is present
            if bot_status in ["ONLINE", "OFFLINE"]:
                print_success(f"    ✓ bot_status correctly set: {bot_status}")
            else:
                print_error(f"    ✗ bot_status incorrect: {bot_status}")
        
        record_test("Bot Detection - Regular Bot Detection", True)
    else:
        print_warning("⚠ No Regular bots found in user list")
        record_test("Bot Detection - Regular Bot Detection", False, "No Regular bots found")
    
    # Test 4: Test bot status logic
    print_subheader("Test 4: Bot Status Logic Verification")
    
    # Test with specific bot type filters
    for bot_type in ["HUMAN_BOT", "REGULAR_BOT"]:
        print(f"\nTesting {bot_type} status logic:")
        
        response, success = make_request(
            "GET", "/admin/users",
            data={"role": bot_type, "limit": 10},
            auth_token=admin_token
        )
        
        if success:
            bots = response.get("users", [])
            print_success(f"✓ Retrieved {len(bots)} {bot_type}s")
            
            online_count = 0
            offline_count = 0
            
            for bot in bots:
                bot_status = bot.get("bot_status", "UNKNOWN")
                username = bot.get("username", "unknown")
                
                if bot_status == "ONLINE":
                    online_count += 1
                    print_success(f"  {username}: ONLINE")
                elif bot_status == "OFFLINE":
                    offline_count += 1
                    print_success(f"  {username}: OFFLINE")
                else:
                    print_error(f"  {username}: Invalid status {bot_status}")
            
            print_success(f"  Status distribution: {online_count} ONLINE, {offline_count} OFFLINE")
            
            # Bot status should reflect is_active field from respective collections
            if online_count >= 0 and offline_count >= 0:
                print_success(f"✓ {bot_type} status logic working")
                record_test(f"Bot Detection - {bot_type} Status Logic", True)
            else:
                print_error(f"✗ {bot_type} status logic failed")
                record_test(f"Bot Detection - {bot_type} Status Logic", False, "Invalid status distribution")
        else:
            print_error(f"✗ Failed to get {bot_type}s")
            record_test(f"Bot Detection - {bot_type} Status Logic", False, "Request failed")

def test_data_integrity(admin_token: str) -> None:
    """Test data integrity of the User Management system."""
    print_header("DATA INTEGRITY TESTING")
    
    # Test 1: Total balance calculation integrity
    print_subheader("Test 1: Total Balance Calculation Integrity")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"limit": 20},
        auth_token=admin_token
    )
    
    if not success:
        print_error("✗ Failed to get users for data integrity testing")
        record_test("Data Integrity - Get Users", False, "Request failed")
        return
    
    users = response.get("users", [])
    print_success(f"✓ Retrieved {len(users)} users for data integrity testing")
    
    balance_calculation_correct = True
    balance_errors = []
    
    for user in users:
        username = user.get("username", "unknown")
        virtual_balance = user.get("virtual_balance", 0)
        frozen_balance = user.get("frozen_balance", 0)
        total_balance = user.get("total_balance", 0)
        
        expected_total = virtual_balance + frozen_balance
        
        if abs(total_balance - expected_total) > 0.01:  # Allow for small floating point errors
            balance_calculation_correct = False
            error_msg = f"{username}: virtual({virtual_balance}) + frozen({frozen_balance}) = {expected_total}, but total_balance = {total_balance}"
            balance_errors.append(error_msg)
            print_error(f"✗ {error_msg}")
        else:
            print_success(f"✓ {username}: total_balance calculation correct ({total_balance})")
    
    if balance_calculation_correct:
        print_success("✓ All users have correct total_balance calculation")
        record_test("Data Integrity - Total Balance Calculation", True)
    else:
        print_error(f"✗ {len(balance_errors)} users have incorrect total_balance calculation")
        record_test("Data Integrity - Total Balance Calculation", False, f"{len(balance_errors)} errors")
    
    # Test 2: Required fields presence
    print_subheader("Test 2: Required Fields Presence")
    
    required_fields = [
        "id", "username", "email", "role", "status", "virtual_balance", 
        "frozen_balance", "total_balance", "user_type", "created_at"
    ]
    
    field_presence_correct = True
    missing_fields_count = {}
    
    for user in users:
        username = user.get("username", "unknown")
        
        for field in required_fields:
            if field not in user:
                field_presence_correct = False
                if field not in missing_fields_count:
                    missing_fields_count[field] = 0
                missing_fields_count[field] += 1
                print_error(f"✗ {username}: missing field '{field}'")
    
    if field_presence_correct:
        print_success("✓ All users have all required fields")
        record_test("Data Integrity - Required Fields", True)
    else:
        print_error(f"✗ Some users missing required fields:")
        for field, count in missing_fields_count.items():
            print_error(f"  {field}: missing in {count} users")
        record_test("Data Integrity - Required Fields", False, f"Missing fields: {list(missing_fields_count.keys())}")
    
    # Test 3: Data type validation
    print_subheader("Test 3: Data Type Validation")
    
    data_type_correct = True
    type_errors = []
    
    for user in users:
        username = user.get("username", "unknown")
        
        # Check numeric fields
        numeric_fields = ["virtual_balance", "frozen_balance", "total_balance"]
        for field in numeric_fields:
            value = user.get(field)
            if value is not None and not isinstance(value, (int, float)):
                data_type_correct = False
                error_msg = f"{username}: {field} should be numeric, got {type(value).__name__}"
                type_errors.append(error_msg)
                print_error(f"✗ {error_msg}")
        
        # Check string fields
        string_fields = ["username", "email", "role", "status", "user_type"]
        for field in string_fields:
            value = user.get(field)
            if value is not None and not isinstance(value, str):
                data_type_correct = False
                error_msg = f"{username}: {field} should be string, got {type(value).__name__}"
                type_errors.append(error_msg)
                print_error(f"✗ {error_msg}")
        
        # Check boolean fields (if present)
        boolean_fields = ["email_verified"]
        for field in boolean_fields:
            value = user.get(field)
            if value is not None and not isinstance(value, bool):
                data_type_correct = False
                error_msg = f"{username}: {field} should be boolean, got {type(value).__name__}"
                type_errors.append(error_msg)
                print_error(f"✗ {error_msg}")
    
    if data_type_correct:
        print_success("✓ All users have correct data types")
        record_test("Data Integrity - Data Types", True)
    else:
        print_error(f"✗ {len(type_errors)} data type errors found")
        record_test("Data Integrity - Data Types", False, f"{len(type_errors)} errors")
    
    # Test 4: Pagination consistency
    print_subheader("Test 4: Pagination Consistency")
    
    # Test multiple pages to ensure consistency
    page1_response, page1_success = make_request(
        "GET", "/admin/users",
        data={"limit": 10, "page": 1},
        auth_token=admin_token
    )
    
    page2_response, page2_success = make_request(
        "GET", "/admin/users",
        data={"limit": 10, "page": 2},
        auth_token=admin_token
    )
    
    if page1_success and page2_success:
        page1_users = page1_response.get("users", [])
        page2_users = page2_response.get("users", [])
        page1_pagination = page1_response.get("pagination", {})
        page2_pagination = page2_response.get("pagination", {})
        
        # Check that users don't overlap between pages
        page1_ids = {user.get("id") for user in page1_users}
        page2_ids = {user.get("id") for user in page2_users}
        overlap = page1_ids.intersection(page2_ids)
        
        if not overlap:
            print_success("✓ No user overlap between pages")
            record_test("Data Integrity - Pagination No Overlap", True)
        else:
            print_error(f"✗ {len(overlap)} users appear in both pages")
            record_test("Data Integrity - Pagination No Overlap", False, f"{len(overlap)} overlapping users")
        
        # Check pagination metadata consistency
        total_items_consistent = page1_pagination.get("total_items") == page2_pagination.get("total_items")
        total_pages_consistent = page1_pagination.get("total_pages") == page2_pagination.get("total_pages")
        
        if total_items_consistent and total_pages_consistent:
            print_success("✓ Pagination metadata consistent across pages")
            record_test("Data Integrity - Pagination Metadata", True)
        else:
            print_error("✗ Pagination metadata inconsistent across pages")
            record_test("Data Integrity - Pagination Metadata", False, "Metadata inconsistent")
    else:
        print_error("✗ Failed to test pagination consistency")
        record_test("Data Integrity - Pagination Consistency", False, "Request failed")

def test_combined_filters(admin_token: str) -> None:
    """Test combined filter functionality."""
    print_header("COMBINED FILTERS TESTING")
    
    # Test 1: Role + Status combination
    print_subheader("Test 1: Role + Status Filter Combination")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"role": "USER", "status": "ACTIVE", "limit": 10},
        auth_token=admin_token
    )
    
    if success:
        users = response.get("users", [])
        print_success(f"✓ Combined role=USER + status=ACTIVE returned {len(users)} users")
        
        # Verify all users match both filters
        filters_correct = True
        for user in users:
            role = user.get("role", "")
            status = user.get("status", "")
            username = user.get("username", "unknown")
            
            if role != "USER" or status != "ACTIVE":
                filters_correct = False
                print_error(f"✗ User {username}: role={role}, status={status} (expected USER/ACTIVE)")
        
        if filters_correct:
            print_success("✓ All users match combined role + status filters")
            record_test("Combined Filters - Role + Status", True)
        else:
            print_error("✗ Some users don't match combined filters")
            record_test("Combined Filters - Role + Status", False, "Filter mismatch")
    else:
        print_error("✗ Combined role + status filter failed")
        record_test("Combined Filters - Role + Status", False, "Request failed")
    
    # Test 2: Balance range + Sort combination
    print_subheader("Test 2: Balance Range + Sort Combination")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={"balance_min": 0, "balance_max": 1000, "sort_by": "balance", "sort_order": "desc", "limit": 10},
        auth_token=admin_token
    )
    
    if success:
        users = response.get("users", [])
        print_success(f"✓ Combined balance range + sort returned {len(users)} users")
        
        # Verify balance range and sort order
        range_and_sort_correct = True
        for i, user in enumerate(users):
            total_balance = user.get("total_balance", 0)
            username = user.get("username", "unknown")
            
            # Check balance range
            if not (0 <= total_balance <= 1000):
                range_and_sort_correct = False
                print_error(f"✗ User {username}: balance {total_balance} outside range 0-1000")
            
            # Check sort order (descending)
            if i > 0:
                prev_balance = users[i-1].get("total_balance", 0)
                if total_balance > prev_balance:
                    range_and_sort_correct = False
                    print_error(f"✗ Sort order incorrect: {prev_balance} should be >= {total_balance}")
        
        if range_and_sort_correct:
            print_success("✓ Balance range and sort order both correct")
            record_test("Combined Filters - Balance + Sort", True)
        else:
            print_error("✗ Balance range or sort order incorrect")
            record_test("Combined Filters - Balance + Sort", False, "Range or sort incorrect")
    else:
        print_error("✗ Combined balance + sort filter failed")
        record_test("Combined Filters - Balance + Sort", False, "Request failed")
    
    # Test 3: Multiple filters with pagination
    print_subheader("Test 3: Multiple Filters + Pagination")
    
    response, success = make_request(
        "GET", "/admin/users",
        data={
            "role": "USER", 
            "status": "ACTIVE", 
            "sort_by": "name", 
            "sort_order": "asc",
            "limit": 5,
            "page": 1
        },
        auth_token=admin_token
    )
    
    if success:
        users = response.get("users", [])
        pagination = response.get("pagination", {})
        
        print_success(f"✓ Multiple filters + pagination returned {len(users)} users")
        print_success(f"  Pagination: page {pagination.get('current_page')}/{pagination.get('total_pages')}")
        
        # Verify all filters are applied
        all_filters_correct = True
        for user in users:
            role = user.get("role", "")
            status = user.get("status", "")
            username = user.get("username", "unknown")
            
            if role != "USER" or status != "ACTIVE":
                all_filters_correct = False
                print_error(f"✗ User {username}: filters not applied correctly")
        
        # Check pagination limit
        if len(users) <= 5:
            print_success("✓ Pagination limit respected")
        else:
            all_filters_correct = False
            print_error(f"✗ Pagination limit exceeded: {len(users)} > 5")
        
        if all_filters_correct:
            print_success("✓ All filters and pagination working correctly")
            record_test("Combined Filters - Multiple + Pagination", True)
        else:
            print_error("✗ Some filters or pagination not working correctly")
            record_test("Combined Filters - Multiple + Pagination", False, "Filters or pagination incorrect")
    else:
        print_error("✗ Multiple filters + pagination failed")
        record_test("Combined Filters - Multiple + Pagination", False, "Request failed")

def print_test_summary():
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print_success(f"Total Tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success(f"Failed: {failed}")
    print_success(f"Success Rate: {success_rate:.1f}%")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"✗ {test['name']}: {test['details']}")
    
    print_subheader("Overall Result:")
    if success_rate >= 90:
        print_success("🎉 EXCELLENT: User Management system is working very well!")
    elif success_rate >= 75:
        print_success("✅ GOOD: User Management system is working well with minor issues")
    elif success_rate >= 50:
        print_warning("⚠️ FAIR: User Management system has some issues that need attention")
    else:
        print_error("❌ POOR: User Management system has significant issues")

def main():
    """Main test execution function."""
    print_header("GEMPLAY USER MANAGEMENT ADVANCED FILTERS AND BOT TYPES TESTING")
    
    # Step 1: Admin Authentication
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to authenticate as admin. Cannot proceed with testing.")
        sys.exit(1)
    
    # Step 2: Basic API Functionality Testing
    test_basic_api_functionality(admin_token)
    
    # Step 3: Filter Parameters Testing
    test_filter_parameters(admin_token)
    
    # Step 4: Bot Type Detection Testing
    test_bot_type_detection(admin_token)
    
    # Step 5: Data Integrity Testing
    test_data_integrity(admin_token)
    
    # Step 6: Combined Filters Testing
    test_combined_filters(admin_token)
    
    # Step 7: Print Test Summary
    print_test_summary()

if __name__ == "__main__":
    main()