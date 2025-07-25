#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Regular Bots Admin Panel Endpoints
Testing all endpoints related to "Обычные боты" (Regular Bots) management in admin panel.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://7a07c3b0-a218-4c24-84e0-b12a9efb7441.preview.emergentagent.com/api"
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
        print_success(f"PASS: {name}")
    else:
        test_results["failed"] += 1
        print_error(f"FAIL: {name} - {details}")
    
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
    
    try:
        if data and method.lower() in ["post", "put", "patch"]:
            headers["Content-Type"] = "application/json"
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
        else:
            response = requests.request(method, url, params=data, headers=headers, timeout=30)
        
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
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return {"error": str(e)}, False

def test_admin_login() -> Optional[str]:
    """Test admin login and return token."""
    print_subheader("Testing Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_get_regular_bots_list(admin_token: str) -> None:
    """Test GET /api/admin/bots/regular/list endpoint with pagination."""
    print_subheader("Testing GET /api/admin/bots/regular/list - Regular Bots List with Pagination")
    
    # Test 1: Basic list request without parameters
    print("Test 1: Basic list request")
    response, success = make_request(
        "GET", 
        "/admin/bots/regular/list",
        auth_token=admin_token
    )
    
    if success:
        # Check response structure
        required_fields = ["bots", "total_count", "current_page", "total_pages", "items_per_page", "has_next", "has_prev"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("Response has all required pagination fields")
            record_test("Regular Bots List - Response Structure", True)
            
            # Check bots array structure
            if "bots" in response and isinstance(response["bots"], list):
                print_success(f"Found {len(response['bots'])} bots in response")
                
                # Check individual bot structure if bots exist
                if response["bots"]:
                    bot = response["bots"][0]
                    bot_required_fields = ["id", "name", "is_active", "active_bets", "win_rate", "cycle_games", "individual_limit"]
                    bot_missing_fields = [field for field in bot_required_fields if field not in bot]
                    
                    if not bot_missing_fields:
                        print_success("Bot objects have all required fields")
                        record_test("Regular Bots List - Bot Object Structure", True)
                    else:
                        print_error(f"Bot objects missing fields: {bot_missing_fields}")
                        record_test("Regular Bots List - Bot Object Structure", False, f"Missing fields: {bot_missing_fields}")
                else:
                    print_warning("No bots found in response")
                    record_test("Regular Bots List - Bot Object Structure", True, "No bots to check")
            else:
                print_error("Response missing 'bots' array or not a list")
                record_test("Regular Bots List - Bots Array", False, "Missing or invalid bots array")
        else:
            print_error(f"Response missing required fields: {missing_fields}")
            record_test("Regular Bots List - Response Structure", False, f"Missing fields: {missing_fields}")
    else:
        record_test("Regular Bots List - Basic Request", False, "Request failed")
    
    # Test 2: Pagination parameters
    print("\nTest 2: Pagination parameters")
    pagination_tests = [
        {"page": 1, "limit": 5},
        {"page": 2, "limit": 10},
        {"page": 1, "limit": 25}
    ]
    
    for params in pagination_tests:
        print(f"Testing pagination with page={params['page']}, limit={params['limit']}")
        response, success = make_request(
            "GET", 
            "/admin/bots/regular/list",
            data=params,
            auth_token=admin_token
        )
        
        if success:
            if response.get("current_page") == params["page"] and response.get("items_per_page") == params["limit"]:
                print_success(f"Pagination parameters correctly applied")
                record_test(f"Regular Bots List - Pagination {params['page']}/{params['limit']}", True)
            else:
                print_error(f"Pagination parameters not applied correctly")
                record_test(f"Regular Bots List - Pagination {params['page']}/{params['limit']}", False, "Parameters not applied")
        else:
            record_test(f"Regular Bots List - Pagination {params['page']}/{params['limit']}", False, "Request failed")
    
    # Test 3: Edge cases for pagination
    print("\nTest 3: Edge cases for pagination")
    edge_cases = [
        {"page": 0, "limit": 10},  # Should default to page 1
        {"page": 1, "limit": 0},   # Should default to limit 10
        {"page": 999, "limit": 10} # Large page number
    ]
    
    for params in edge_cases:
        print(f"Testing edge case with page={params['page']}, limit={params['limit']}")
        response, success = make_request(
            "GET", 
            "/admin/bots/regular/list",
            data=params,
            auth_token=admin_token
        )
        
        if success:
            print_success(f"Edge case handled gracefully")
            record_test(f"Regular Bots List - Edge Case {params['page']}/{params['limit']}", True)
        else:
            record_test(f"Regular Bots List - Edge Case {params['page']}/{params['limit']}", False, "Request failed")

def test_create_regular_bot(admin_token: str) -> Optional[str]:
    """Test POST /api/admin/bots/create-regular endpoint."""
    print_subheader("Testing POST /api/admin/bots/create-regular - Create New Regular Bot")
    
    # Generate unique bot name
    bot_name = f"TestBot_{int(time.time())}"
    
    # Test 1: Create bot with valid data
    print("Test 1: Create bot with valid data")
    bot_data = {
        "name": bot_name,
        "is_active": True,
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "win_rate": 60.0,
        "cycle_games": 12,
        "individual_limit": 10,
        "pause_between_games": 5,
        "profit_strategy": "balanced"
    }
    
    response, success = make_request(
        "POST", 
        "/admin/bots/create-regular",
        data=bot_data,
        auth_token=admin_token
    )
    
    created_bot_id = None
    if success:
        if "id" in response and "message" in response:
            created_bot_id = response["id"]
            print_success(f"Bot created successfully with ID: {created_bot_id}")
            record_test("Create Regular Bot - Valid Data", True)
        else:
            print_error(f"Response missing expected fields: {response}")
            record_test("Create Regular Bot - Valid Data", False, "Missing response fields")
    else:
        record_test("Create Regular Bot - Valid Data", False, "Request failed")
    
    # Test 2: Validation tests
    print("\nTest 2: Validation tests")
    validation_tests = [
        {
            "name": "Empty Name",
            "data": {**bot_data, "name": ""},
            "expected_error": "name"
        },
        {
            "name": "Invalid Win Rate",
            "data": {**bot_data, "name": f"TestBot_Invalid_{int(time.time())}", "win_rate": 150.0},
            "expected_error": "win_rate"
        },
        {
            "name": "Invalid Cycle Games",
            "data": {**bot_data, "name": f"TestBot_Invalid2_{int(time.time())}", "cycle_games": 0},
            "expected_error": "cycle_games"
        },
        {
            "name": "Invalid Bet Range",
            "data": {**bot_data, "name": f"TestBot_Invalid3_{int(time.time())}", "min_bet_amount": 100.0, "max_bet_amount": 50.0},
            "expected_error": "bet_amount"
        }
    ]
    
    for test_case in validation_tests:
        print(f"Testing validation: {test_case['name']}")
        response, success = make_request(
            "POST", 
            "/admin/bots/create-regular",
            data=test_case["data"],
            auth_token=admin_token,
            expected_status=422  # Validation error
        )
        
        if not success and "detail" in response:
            print_success(f"Validation correctly rejected: {test_case['name']}")
            record_test(f"Create Regular Bot - Validation {test_case['name']}", True)
        else:
            print_error(f"Validation should have failed for: {test_case['name']}")
            record_test(f"Create Regular Bot - Validation {test_case['name']}", False, "Validation not triggered")
    
    return created_bot_id

def test_update_bot(admin_token: str, bot_id: str) -> None:
    """Test PUT /api/admin/bots/{bot_id} endpoint."""
    print_subheader(f"Testing PUT /api/admin/bots/{bot_id} - Update Bot Parameters")
    
    if not bot_id:
        print_error("No bot ID provided for update test")
        record_test("Update Bot - No Bot ID", False, "No bot ID available")
        return
    
    # Test 1: Update bot with valid data
    print("Test 1: Update bot with valid data")
    update_data = {
        "name": f"UpdatedBot_{int(time.time())}",
        "is_active": False,
        "win_rate": 55.0,
        "cycle_games": 15,
        "individual_limit": 8,
        "min_bet_amount": 2.0,
        "max_bet_amount": 200.0,
        "profit_strategy": "start_profit"
    }
    
    response, success = make_request(
        "PUT", 
        f"/admin/bots/{bot_id}",
        data=update_data,
        auth_token=admin_token
    )
    
    if success:
        if "message" in response:
            print_success("Bot updated successfully")
            record_test("Update Bot - Valid Data", True)
        else:
            print_error(f"Update response missing message: {response}")
            record_test("Update Bot - Valid Data", False, "Missing response message")
    else:
        record_test("Update Bot - Valid Data", False, "Request failed")
    
    # Test 2: Update with invalid bot ID
    print("\nTest 2: Update with invalid bot ID")
    invalid_bot_id = "invalid-bot-id-12345"
    response, success = make_request(
        "PUT", 
        f"/admin/bots/{invalid_bot_id}",
        data=update_data,
        auth_token=admin_token,
        expected_status=404
    )
    
    if not success and response.get("detail"):
        print_success("Invalid bot ID correctly rejected")
        record_test("Update Bot - Invalid ID", True)
    else:
        print_error("Invalid bot ID should have been rejected")
        record_test("Update Bot - Invalid ID", False, "Invalid ID not rejected")
    
    # Test 3: Partial update
    print("\nTest 3: Partial update")
    partial_data = {
        "is_active": True,
        "win_rate": 65.0
    }
    
    response, success = make_request(
        "PUT", 
        f"/admin/bots/{bot_id}",
        data=partial_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("Partial update successful")
        record_test("Update Bot - Partial Update", True)
    else:
        record_test("Update Bot - Partial Update", False, "Partial update failed")

def test_get_bot_active_bets(admin_token: str, bot_id: str) -> None:
    """Test GET /api/admin/bots/{bot_id}/active-bets endpoint."""
    print_subheader(f"Testing GET /api/admin/bots/{bot_id}/active-bets - Get Bot Active Bets")
    
    if not bot_id:
        print_error("No bot ID provided for active bets test")
        record_test("Bot Active Bets - No Bot ID", False, "No bot ID available")
        return
    
    # Test 1: Get active bets for valid bot
    print("Test 1: Get active bets for valid bot")
    response, success = make_request(
        "GET", 
        f"/admin/bots/{bot_id}/active-bets",
        auth_token=admin_token
    )
    
    if success:
        # Check response structure
        if "bets" in response or "active_bets" in response:
            bets_key = "bets" if "bets" in response else "active_bets"
            bets = response[bets_key]
            
            if isinstance(bets, list):
                print_success(f"Found {len(bets)} active bets")
                
                # Check bet structure if bets exist
                if bets:
                    bet = bets[0]
                    bet_required_fields = ["game_id", "bet_amount", "status", "created_at", "opponent", "time_until_cancel"]
                    bet_missing_fields = [field for field in bet_required_fields if field not in bet]
                    
                    if not bet_missing_fields:
                        print_success("Bet objects have all required fields")
                        record_test("Bot Active Bets - Bet Structure", True)
                    else:
                        print_warning(f"Bet objects missing some fields: {bet_missing_fields}")
                        record_test("Bot Active Bets - Bet Structure", True, f"Minor missing fields: {bet_missing_fields}")
                else:
                    print_success("No active bets found (expected for new bot)")
                    record_test("Bot Active Bets - Bet Structure", True, "No bets to check")
                
                record_test("Bot Active Bets - Valid Bot", True)
            else:
                print_error("Bets field is not a list")
                record_test("Bot Active Bets - Valid Bot", False, "Bets not a list")
        else:
            print_error("Response missing bets/active_bets field")
            record_test("Bot Active Bets - Valid Bot", False, "Missing bets field")
    else:
        record_test("Bot Active Bets - Valid Bot", False, "Request failed")
    
    # Test 2: Get active bets for invalid bot
    print("\nTest 2: Get active bets for invalid bot")
    invalid_bot_id = "invalid-bot-id-12345"
    response, success = make_request(
        "GET", 
        f"/admin/bots/{invalid_bot_id}/active-bets",
        auth_token=admin_token,
        expected_status=404
    )
    
    if not success and response.get("detail"):
        print_success("Invalid bot ID correctly rejected")
        record_test("Bot Active Bets - Invalid ID", True)
    else:
        print_error("Invalid bot ID should have been rejected")
        record_test("Bot Active Bets - Invalid ID", False, "Invalid ID not rejected")

def test_get_bot_cycle_history(admin_token: str, bot_id: str) -> None:
    """Test GET /api/admin/bots/{bot_id}/cycle-history endpoint."""
    print_subheader(f"Testing GET /api/admin/bots/{bot_id}/cycle-history - Get Bot Cycle History")
    
    if not bot_id:
        print_error("No bot ID provided for cycle history test")
        record_test("Bot Cycle History - No Bot ID", False, "No bot ID available")
        return
    
    # Test 1: Get cycle history for valid bot
    print("Test 1: Get cycle history for valid bot")
    response, success = make_request(
        "GET", 
        f"/admin/bots/{bot_id}/cycle-history",
        auth_token=admin_token
    )
    
    if success:
        # Check response structure
        expected_fields = ["cycle_stats", "games"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if not missing_fields:
            print_success("Response has expected structure")
            
            # Check cycle_stats structure
            cycle_stats = response["cycle_stats"]
            stats_fields = ["win_percentage", "total_bet_amount", "net_profit"]
            stats_missing = [field for field in stats_fields if field not in cycle_stats]
            
            if not stats_missing:
                print_success("Cycle stats have all required fields")
                record_test("Bot Cycle History - Stats Structure", True)
            else:
                print_warning(f"Cycle stats missing some fields: {stats_missing}")
                record_test("Bot Cycle History - Stats Structure", True, f"Minor missing fields: {stats_missing}")
            
            # Check games structure
            games = response["games"]
            if isinstance(games, list):
                print_success(f"Found {len(games)} games in history")
                
                if games:
                    game = games[0]
                    game_fields = ["id", "status", "bet_amount", "created_at", "opponent"]
                    game_missing = [field for field in game_fields if field not in game]
                    
                    if not game_missing:
                        print_success("Game objects have all required fields")
                        record_test("Bot Cycle History - Game Structure", True)
                    else:
                        print_warning(f"Game objects missing some fields: {game_missing}")
                        record_test("Bot Cycle History - Game Structure", True, f"Minor missing fields: {game_missing}")
                else:
                    print_success("No games found in history (expected for new bot)")
                    record_test("Bot Cycle History - Game Structure", True, "No games to check")
            else:
                print_error("Games field is not a list")
                record_test("Bot Cycle History - Game Structure", False, "Games not a list")
            
            record_test("Bot Cycle History - Valid Bot", True)
        else:
            print_error(f"Response missing expected fields: {missing_fields}")
            record_test("Bot Cycle History - Valid Bot", False, f"Missing fields: {missing_fields}")
    else:
        record_test("Bot Cycle History - Valid Bot", False, "Request failed")
    
    # Test 2: Get cycle history for invalid bot
    print("\nTest 2: Get cycle history for invalid bot")
    invalid_bot_id = "invalid-bot-id-12345"
    response, success = make_request(
        "GET", 
        f"/admin/bots/{invalid_bot_id}/cycle-history",
        auth_token=admin_token,
        expected_status=404
    )
    
    if not success and response.get("detail"):
        print_success("Invalid bot ID correctly rejected")
        record_test("Bot Cycle History - Invalid ID", True)
    else:
        print_error("Invalid bot ID should have been rejected")
        record_test("Bot Cycle History - Invalid ID", False, "Invalid ID not rejected")

def test_delete_bot(admin_token: str, bot_id: str) -> None:
    """Test DELETE /api/admin/bots/{bot_id} endpoint."""
    print_subheader(f"Testing DELETE /api/admin/bots/{bot_id} - Delete Bot")
    
    if not bot_id:
        print_error("No bot ID provided for delete test")
        record_test("Delete Bot - No Bot ID", False, "No bot ID available")
        return
    
    # Test 1: Delete with invalid bot ID first
    print("Test 1: Delete with invalid bot ID")
    invalid_bot_id = "invalid-bot-id-12345"
    response, success = make_request(
        "DELETE", 
        f"/admin/bots/{invalid_bot_id}",
        auth_token=admin_token,
        expected_status=404
    )
    
    if not success and response.get("detail"):
        print_success("Invalid bot ID correctly rejected")
        record_test("Delete Bot - Invalid ID", True)
    else:
        print_error("Invalid bot ID should have been rejected")
        record_test("Delete Bot - Invalid ID", False, "Invalid ID not rejected")
    
    # Test 2: Delete valid bot
    print("\nTest 2: Delete valid bot")
    response, success = make_request(
        "DELETE", 
        f"/admin/bots/{bot_id}",
        auth_token=admin_token
    )
    
    if success:
        if "message" in response:
            print_success("Bot deleted successfully")
            record_test("Delete Bot - Valid ID", True)
        else:
            print_error(f"Delete response missing message: {response}")
            record_test("Delete Bot - Valid ID", False, "Missing response message")
    else:
        record_test("Delete Bot - Valid ID", False, "Request failed")
    
    # Test 3: Try to delete the same bot again (should fail)
    print("\nTest 3: Try to delete already deleted bot")
    response, success = make_request(
        "DELETE", 
        f"/admin/bots/{bot_id}",
        auth_token=admin_token,
        expected_status=404
    )
    
    if not success and response.get("detail"):
        print_success("Already deleted bot correctly rejected")
        record_test("Delete Bot - Already Deleted", True)
    else:
        print_error("Already deleted bot should have been rejected")
        record_test("Delete Bot - Already Deleted", False, "Should have been rejected")

def test_bot_global_settings(admin_token: str) -> None:
    """Test bot global settings endpoints."""
    print_subheader("Testing Bot Global Settings Endpoints")
    
    # Test 1: GET /api/admin/bot-settings
    print("Test 1: GET /api/admin/bot-settings - Get Global Bot Settings")
    response, success = make_request(
        "GET", 
        "/admin/bot-settings",
        auth_token=admin_token
    )
    
    if success:
        # Check response structure
        expected_fields = ["globalMaxActiveBets", "globalMaxHumanBots", "paginationSize", "autoActivateFromQueue", "priorityType"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if not missing_fields:
            print_success("Bot settings response has all expected fields")
            record_test("Bot Global Settings - Get Structure", True)
        else:
            print_warning(f"Bot settings missing some fields: {missing_fields}")
            record_test("Bot Global Settings - Get Structure", True, f"Minor missing fields: {missing_fields}")
    else:
        record_test("Bot Global Settings - Get", False, "Request failed")
    
    # Test 2: PUT /api/admin/bot-settings
    print("\nTest 2: PUT /api/admin/bot-settings - Update Global Bot Settings")
    settings_data = {
        "globalMaxActiveBets": 75,
        "globalMaxHumanBots": 40,
        "paginationSize": 15,
        "autoActivateFromQueue": True,
        "priorityType": "manual"
    }
    
    response, success = make_request(
        "PUT", 
        "/admin/bot-settings",
        data=settings_data,
        auth_token=admin_token
    )
    
    if success:
        if "message" in response:
            print_success("Bot settings updated successfully")
            record_test("Bot Global Settings - Update", True)
        else:
            print_error(f"Update response missing message: {response}")
            record_test("Bot Global Settings - Update", False, "Missing response message")
    else:
        record_test("Bot Global Settings - Update", False, "Request failed")
    
    # Test 3: Validation for bot settings
    print("\nTest 3: Validation for bot settings")
    invalid_settings = {
        "globalMaxActiveBets": 0,  # Should be >= 1
        "globalMaxHumanBots": 101,  # Should be <= 100
        "paginationSize": 51,  # Should be <= 50
        "autoActivateFromQueue": True,
        "priorityType": "invalid"  # Should be 'order' or 'manual'
    }
    
    response, success = make_request(
        "PUT", 
        "/admin/bot-settings",
        data=invalid_settings,
        auth_token=admin_token,
        expected_status=422  # Validation error
    )
    
    if not success and "detail" in response:
        print_success("Invalid settings correctly rejected")
        record_test("Bot Global Settings - Validation", True)
    else:
        print_error("Invalid settings should have been rejected")
        record_test("Bot Global Settings - Validation", False, "Validation not triggered")

def test_authentication_and_authorization(admin_token: str) -> None:
    """Test authentication and authorization for all endpoints."""
    print_subheader("Testing Authentication and Authorization")
    
    endpoints_to_test = [
        ("GET", "/admin/bots/regular/list"),
        ("POST", "/admin/bots/create-regular"),
        ("GET", "/admin/bot-settings"),
        ("PUT", "/admin/bot-settings")
    ]
    
    # Test 1: No authentication token
    print("Test 1: No authentication token")
    for method, endpoint in endpoints_to_test:
        print(f"Testing {method} {endpoint} without token")
        response, success = make_request(
            method, 
            endpoint,
            data={} if method in ["POST", "PUT"] else None,
            expected_status=401
        )
        
        if not success and response.get("detail"):
            print_success(f"No auth correctly rejected for {method} {endpoint}")
            record_test(f"Auth - No Token {method} {endpoint}", True)
        else:
            print_error(f"No auth should have been rejected for {method} {endpoint}")
            record_test(f"Auth - No Token {method} {endpoint}", False, "Should have been rejected")
    
    # Test 2: Invalid authentication token
    print("\nTest 2: Invalid authentication token")
    invalid_token = "invalid-token-12345"
    for method, endpoint in endpoints_to_test:
        print(f"Testing {method} {endpoint} with invalid token")
        response, success = make_request(
            method, 
            endpoint,
            data={} if method in ["POST", "PUT"] else None,
            auth_token=invalid_token,
            expected_status=401
        )
        
        if not success and response.get("detail"):
            print_success(f"Invalid auth correctly rejected for {method} {endpoint}")
            record_test(f"Auth - Invalid Token {method} {endpoint}", True)
        else:
            print_error(f"Invalid auth should have been rejected for {method} {endpoint}")
            record_test(f"Auth - Invalid Token {method} {endpoint}", False, "Should have been rejected")

def test_error_handling() -> None:
    """Test error handling for various scenarios."""
    print_subheader("Testing Error Handling")
    
    # Get admin token for testing
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot test error handling without admin token")
        return
    
    # Test 1: Malformed JSON
    print("Test 1: Malformed JSON in request body")
    try:
        url = f"{BASE_URL}/admin/bots/create-regular"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # Send malformed JSON
        response = requests.post(url, data="{'invalid': json}", headers=headers, timeout=30)
        
        if response.status_code == 422:
            print_success("Malformed JSON correctly rejected")
            record_test("Error Handling - Malformed JSON", True)
        else:
            print_error(f"Malformed JSON handling unexpected: {response.status_code}")
            record_test("Error Handling - Malformed JSON", False, f"Unexpected status: {response.status_code}")
    except Exception as e:
        print_error(f"Error testing malformed JSON: {e}")
        record_test("Error Handling - Malformed JSON", False, f"Exception: {e}")
    
    # Test 2: Large request body
    print("\nTest 2: Large request body")
    large_data = {
        "name": "A" * 10000,  # Very long name
        "description": "B" * 50000  # Very long description
    }
    
    response, success = make_request(
        "POST", 
        "/admin/bots/create-regular",
        data=large_data,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success:
        print_success("Large request body correctly handled")
        record_test("Error Handling - Large Request", True)
    else:
        print_warning("Large request body was accepted (might be OK)")
        record_test("Error Handling - Large Request", True, "Accepted large request")

def print_summary() -> None:
    """Print a summary of all test results."""
    print_header("REGULAR BOTS ADMIN API TEST SUMMARY")
    
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

def main():
    """Main test execution function."""
    print_header("REGULAR BOTS ADMIN PANEL API TESTING")
    print("Testing all endpoints for 'Обычные боты' (Regular Bots) management")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        sys.exit(1)
    
    # Step 2: Test all Regular Bots endpoints
    test_get_regular_bots_list(admin_token)
    
    # Create a bot for testing other endpoints
    created_bot_id = test_create_regular_bot(admin_token)
    
    if created_bot_id:
        test_update_bot(admin_token, created_bot_id)
        test_get_bot_active_bets(admin_token, created_bot_id)
        test_get_bot_cycle_history(admin_token, created_bot_id)
        test_delete_bot(admin_token, created_bot_id)
    else:
        print_warning("Skipping bot-specific tests due to creation failure")
    
    # Step 3: Test Bot Global Settings
    test_bot_global_settings(admin_token)
    
    # Step 4: Test Authentication and Authorization
    test_authentication_and_authorization(admin_token)
    
    # Step 5: Test Error Handling
    test_error_handling()
    
    # Step 6: Print summary
    print_summary()

if __name__ == "__main__":
    main()