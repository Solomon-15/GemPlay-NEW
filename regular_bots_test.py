#!/usr/bin/env python3
"""
Backend API Testing for Regular Bots Management New Parameters
Testing the backend APIs that support the Regular Bots Management frontend functionality
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://c3094430-a67a-4704-b959-4fd10b62d970.preview.emergentagent.com/api"
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
        print_success(f"{name}")
    else:
        test_results["failed"] += 1
        print_error(f"{name}: {details}")
    
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
    except Exception as e:
        print_error(f"Request failed with exception: {e}")
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
        print_success(f"Admin logged in successfully")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_regular_bots_list_api(token: str) -> None:
    """Test the GET /admin/bots/regular/list API that supports the frontend table."""
    print_subheader("Testing Regular Bots List API")
    
    # Test basic list endpoint
    response, success = make_request(
        "GET", "/admin/bots/regular/list",
        auth_token=token
    )
    
    if success:
        # Check response structure
        required_fields = ["bots", "total_count", "current_page", "total_pages", "items_per_page", "has_next", "has_prev"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            record_test("Regular Bots List - Response Structure", False, f"Missing fields: {missing_fields}")
        else:
            record_test("Regular Bots List - Response Structure", True)
        
        # Check bot objects have new parameters
        if "bots" in response and response["bots"]:
            bot = response["bots"][0]
            new_parameters = [
                "individual_limit",  # Лимиты column
                "profit_strategy",   # Стратегия column  
                "pause_between_games"  # Пауза column
            ]
            
            missing_params = [param for param in new_parameters if param not in bot]
            
            if missing_params:
                record_test("Regular Bots List - New Parameters", False, f"Missing parameters: {missing_params}")
            else:
                record_test("Regular Bots List - New Parameters", True)
                print_success(f"Bot has individual_limit: {bot.get('individual_limit')}")
                print_success(f"Bot has profit_strategy: {bot.get('profit_strategy')}")
                print_success(f"Bot has pause_between_games: {bot.get('pause_between_games')}")
        else:
            record_test("Regular Bots List - New Parameters", False, "No bots found to check parameters")
    else:
        record_test("Regular Bots List - Basic Request", False, "Request failed")

def test_bot_creation_api(token: str) -> Optional[str]:
    """Test bot creation API with new parameters."""
    print_subheader("Testing Bot Creation API with New Parameters")
    
    # Test creating a bot with new parameters
    bot_data = {
        "name": "Test Bot New Params",
        "bot_type": "REGULAR",
        "min_bet_amount": 5.0,
        "max_bet_amount": 25.0,
        "win_rate": 60.0,
        "cycle_games": 15,
        "individual_limit": 15,  # New parameter
        "profit_strategy": "start-positive",  # New parameter
        "pause_between_games": 3,  # New parameter
        "creation_mode": "queue-based",
        "priority_order": 50
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=bot_data,
        auth_token=token
    )
    
    if success:
        if "bot" in response or "id" in response or "created_bots" in response:
            bot_id = None
            if "bot" in response and "id" in response["bot"]:
                bot_id = response["bot"]["id"]
            elif "id" in response:
                bot_id = response["id"]
            elif "created_bots" in response and response["created_bots"]:
                bot_id = response["created_bots"][0]
            
            record_test("Bot Creation - With New Parameters", True)
            print_success(f"Bot created with ID: {bot_id}")
            return bot_id
        else:
            record_test("Bot Creation - With New Parameters", False, "No bot ID in response")
    else:
        record_test("Bot Creation - With New Parameters", False, f"Creation failed: {response}")
    
    return None

def test_bot_update_api(token: str, bot_id: str) -> None:
    """Test bot update API with new parameters."""
    print_subheader("Testing Bot Update API with New Parameters")
    
    if not bot_id:
        record_test("Bot Update - New Parameters", False, "No bot ID available")
        return
    
    # Test updating bot with new parameters
    update_data = {
        "individual_limit": 20,  # Update limit
        "profit_strategy": "balanced",  # Update strategy
        "pause_between_games": 5  # Update pause
    }
    
    response, success = make_request(
        "PUT", f"/admin/bots/{bot_id}/update",
        data=update_data,
        auth_token=token
    )
    
    if success:
        record_test("Bot Update - New Parameters", True)
        print_success("Bot updated successfully with new parameters")
    else:
        record_test("Bot Update - New Parameters", False, f"Update failed: {response}")

def test_bot_settings_api(token: str) -> None:
    """Test bot settings API that supports global bot management."""
    print_subheader("Testing Bot Settings API")
    
    # Test GET bot settings
    response, success = make_request(
        "GET", "/admin/bot-settings",
        auth_token=token
    )
    
    if success:
        # Check for expected settings fields
        expected_fields = ["globalMaxActiveBets", "globalMaxHumanBots", "paginationSize", "autoActivateFromQueue", "priorityType"]
        
        if any(field in response for field in expected_fields):
            record_test("Bot Settings - GET Request", True)
            print_success("Bot settings retrieved successfully")
        else:
            record_test("Bot Settings - GET Request", False, "Response missing expected settings fields")
    else:
        record_test("Bot Settings - GET Request", False, f"GET request failed: {response}")
    
    # Test PUT bot settings
    settings_data = {
        "globalMaxActiveBets": 100,
        "globalMaxHumanBots": 50,
        "paginationSize": 10,
        "autoActivateFromQueue": True,
        "priorityType": "manual"
    }
    
    response, success = make_request(
        "PUT", "/admin/bot-settings",
        data=settings_data,
        auth_token=token
    )
    
    if success:
        record_test("Bot Settings - PUT Request", True)
        print_success("Bot settings updated successfully")
    else:
        record_test("Bot Settings - PUT Request", False, f"PUT request failed: {response}")

def test_bot_queue_stats_api(token: str) -> None:
    """Test bot queue statistics API."""
    print_subheader("Testing Bot Queue Statistics API")
    
    response, success = make_request(
        "GET", "/admin/bot-queue-stats",
        auth_token=token
    )
    
    if success:
        # Check for expected stats fields
        expected_fields = ["totalActiveRegularBets", "totalQueuedBets", "totalRegularBots", "totalHumanBots"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if missing_fields:
            record_test("Bot Queue Stats - Response Structure", False, f"Missing fields: {missing_fields}")
        else:
            record_test("Bot Queue Stats - Response Structure", True)
            print_success(f"Total active regular bets: {response.get('totalActiveRegularBets')}")
            print_success(f"Total regular bots: {response.get('totalRegularBots')}")
    else:
        record_test("Bot Queue Stats - Request", False, f"Request failed: {response}")

def test_bot_priority_management_api(token: str) -> None:
    """Test bot priority management APIs."""
    print_subheader("Testing Bot Priority Management APIs")
    
    # First get a bot to test priority management
    bots_response, bots_success = make_request(
        "GET", "/admin/bots/regular/list?limit=2",
        auth_token=token
    )
    
    if bots_success and "bots" in bots_response and len(bots_response["bots"]) >= 2:
        bot_id = bots_response["bots"][0]["id"]
        
        # Test move up
        response, success = make_request(
            "POST", f"/admin/bots/{bot_id}/priority/move-up",
            auth_token=token
        )
        
        if success:
            record_test("Bot Priority - Move Up", True)
        else:
            record_test("Bot Priority - Move Up", False, f"Move up failed: {response}")
        
        # Test move down
        response, success = make_request(
            "POST", f"/admin/bots/{bot_id}/priority/move-down",
            auth_token=token
        )
        
        if success:
            record_test("Bot Priority - Move Down", True)
        else:
            record_test("Bot Priority - Move Down", False, f"Move down failed: {response}")
        
        # Test reset priorities
        response, success = make_request(
            "POST", "/admin/bots/priority/reset",
            auth_token=token
        )
        
        if success:
            record_test("Bot Priority - Reset", True)
        else:
            record_test("Bot Priority - Reset", False, f"Reset failed: {response}")
    else:
        record_test("Bot Priority - Setup", False, "Not enough bots for priority testing")

def test_individual_bot_limit_api(token: str) -> None:
    """Test individual bot limit update API."""
    print_subheader("Testing Individual Bot Limit API")
    
    # Get a bot to test limit update
    bots_response, bots_success = make_request(
        "GET", "/admin/bots/regular/list?limit=1",
        auth_token=token
    )
    
    if bots_success and "bots" in bots_response and bots_response["bots"]:
        bot_id = bots_response["bots"][0]["id"]
        
        # Test updating individual limit
        limit_data = {"limit": 18}
        
        response, success = make_request(
            "PUT", f"/admin/bots/{bot_id}/limit",
            data=limit_data,
            auth_token=token
        )
        
        if success:
            record_test("Individual Bot Limit - Update", True)
            print_success("Individual bot limit updated successfully")
        else:
            record_test("Individual Bot Limit - Update", False, f"Update failed: {response}")
    else:
        record_test("Individual Bot Limit - Setup", False, "No bots available for limit testing")

def main():
    """Main test function."""
    print_header("REGULAR BOTS MANAGEMENT NEW PARAMETERS - BACKEND API TESTING")
    
    # Step 1: Admin login
    token = test_admin_login()
    if not token:
        print_error("Cannot proceed without admin token")
        return
    
    # Step 2: Test regular bots list API (supports frontend table)
    test_regular_bots_list_api(token)
    
    # Step 3: Test bot creation with new parameters
    bot_id = test_bot_creation_api(token)
    
    # Step 4: Test bot update with new parameters
    if bot_id:
        test_bot_update_api(token, bot_id)
    
    # Step 5: Test bot settings API (global settings)
    test_bot_settings_api(token)
    
    # Step 6: Test bot queue statistics API
    test_bot_queue_stats_api(token)
    
    # Step 7: Test bot priority management APIs
    test_bot_priority_management_api(token)
    
    # Step 8: Test individual bot limit API
    test_individual_bot_limit_api(token)
    
    # Print final results
    print_header("TEST SUMMARY")
    
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results['failed'] > 0:
        print(f"\nFailed tests:")
        for test in test_results['tests']:
            if not test['passed']:
                print_error(f"{test['name']}: {test['details']}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
    print(f"\nSuccess rate: {Colors.BOLD}{success_rate:.2f}%{Colors.ENDC}")
    
    if test_results['failed'] > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some tests failed!{Colors.ENDC}")
        sys.exit(1)
    else:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests passed!{Colors.ENDC}")

if __name__ == "__main__":
    main()