#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://ba8cc80b-e89e-43ed-be28-0c0321c9b61d.preview.emergentagent.com/api"
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

def admin_login() -> Optional[str]:
    """Login as admin and return the auth token."""
    print_subheader("Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success("Admin logged in successfully")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error("Admin login failed")
        record_test("Admin Login", False, "Failed to get access token")
        return None

def test_get_bots(token: str) -> List[Dict[str, Any]]:
    """Test GET /api/bots endpoint."""
    print_subheader("Testing GET /api/bots")
    
    if not token:
        print_error("No auth token available")
        record_test("GET /api/bots", False, "No token available")
        return []
    
    response, success = make_request("GET", "/bots", auth_token=token)
    
    if success:
        if isinstance(response, list):
            print_success(f"Successfully retrieved {len(response)} bots")
            
            # Verify the structure of the response
            if len(response) > 0:
                bot = response[0]
                expected_fields = [
                    "id", "name", "bot_type", "is_active", "min_bet", "max_bet", 
                    "win_rate", "cycle_games", "current_cycle_games", "current_cycle_wins",
                    "pause_between_games", "can_accept_bets", "can_play_with_bots", 
                    "avatar_gender", "simple_mode"
                ]
                
                missing_fields = [field for field in expected_fields if field not in bot]
                
                if not missing_fields:
                    print_success("Bot data structure is correct")
                    record_test("GET /api/bots - Data Structure", True)
                else:
                    print_error(f"Bot data missing fields: {missing_fields}")
                    record_test("GET /api/bots - Data Structure", False, f"Missing fields: {missing_fields}")
            
            record_test("GET /api/bots", True)
            return response
        else:
            print_error("Response is not a list")
            record_test("GET /api/bots", False, "Response is not a list")
    else:
        record_test("GET /api/bots", False, "Request failed")
    
    return []

def test_create_bot(token: str) -> Optional[str]:
    """Test POST /api/bots endpoint."""
    print_subheader("Testing POST /api/bots")
    
    if not token:
        print_error("No auth token available")
        record_test("POST /api/bots", False, "No token available")
        return None
    
    # Generate a random bot name to avoid conflicts
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    bot_name = f"TestBot_{random_suffix}"
    
    bot_data = {
        "name": bot_name,
        "bot_type": "REGULAR",
        "win_rate": 0.6,
        "min_bet": 5.0,
        "max_bet": 500.0,
        "cycle_games": 10,
        "pause_between_games": 30,
        "can_accept_bets": True,
        "can_play_with_bots": False,
        "avatar_gender": "male",
        "simple_mode": False
    }
    
    response, success = make_request("POST", "/bots", data=bot_data, auth_token=token)
    
    if success:
        if "message" in response and "bot_id" in response:
            print_success(f"Bot created successfully with ID: {response['bot_id']}")
            record_test("POST /api/bots", True)
            return response["bot_id"]
        else:
            print_error("Response missing expected fields")
            record_test("POST /api/bots", False, "Response missing expected fields")
    else:
        record_test("POST /api/bots", False, "Request failed")
    
    return None

def test_update_bot(token: str, bot_id: str) -> bool:
    """Test PUT /api/bots/{bot_id} endpoint."""
    print_subheader(f"Testing PUT /api/bots/{bot_id}")
    
    if not token or not bot_id:
        print_error("No auth token or bot ID available")
        record_test("PUT /api/bots/{bot_id}", False, "No token or bot ID available")
        return False
    
    update_data = {
        "name": f"Updated_Bot_{bot_id[:6]}",
        "win_rate": 0.7,
        "min_bet": 10.0,
        "max_bet": 600.0
    }
    
    response, success = make_request("PUT", f"/bots/{bot_id}", data=update_data, auth_token=token)
    
    if success:
        if "message" in response and "updated" in response["message"].lower():
            print_success("Bot updated successfully")
            record_test("PUT /api/bots/{bot_id}", True)
            return True
        else:
            print_error("Response missing expected message")
            record_test("PUT /api/bots/{bot_id}", False, "Response missing expected message")
    else:
        record_test("PUT /api/bots/{bot_id}", False, "Request failed")
    
    return False

def test_toggle_bot(token: str, bot_id: str) -> bool:
    """Test POST /api/bots/{bot_id}/toggle endpoint."""
    print_subheader(f"Testing POST /api/bots/{bot_id}/toggle")
    
    if not token or not bot_id:
        print_error("No auth token or bot ID available")
        record_test("POST /api/bots/{bot_id}/toggle", False, "No token or bot ID available")
        return False
    
    response, success = make_request("POST", f"/bots/{bot_id}/toggle", auth_token=token)
    
    if success:
        if "message" in response and ("deactivated" in response["message"].lower() or "activated" in response["message"].lower()):
            print_success("Bot toggled successfully")
            record_test("POST /api/bots/{bot_id}/toggle", True)
            return True
        else:
            print_error("Response missing expected message")
            record_test("POST /api/bots/{bot_id}/toggle", False, "Response missing expected message")
    else:
        record_test("POST /api/bots/{bot_id}/toggle", False, "Request failed")
    
    return False

def test_setup_bot_gems(token: str, bot_id: str) -> bool:
    """Test POST /api/bots/{bot_id}/setup-gems endpoint."""
    print_subheader(f"Testing POST /api/bots/{bot_id}/setup-gems")
    
    if not token or not bot_id:
        print_error("No auth token or bot ID available")
        record_test("POST /api/bots/{bot_id}/setup-gems", False, "No token or bot ID available")
        return False
    
    gems_data = {
        "Ruby": 100,
        "Emerald": 50,
        "Sapphire": 20
    }
    
    response, success = make_request("POST", f"/bots/{bot_id}/setup-gems", data=gems_data, auth_token=token)
    
    if success:
        if "message" in response and "setup" in response["message"].lower():
            print_success("Bot gems set up successfully")
            record_test("POST /api/bots/{bot_id}/setup-gems", True)
            return True
        else:
            print_error("Response missing expected message")
            record_test("POST /api/bots/{bot_id}/setup-gems", False, "Response missing expected message")
    else:
        record_test("POST /api/bots/{bot_id}/setup-gems", False, "Request failed")
    
    return False

def test_bot_stats(token: str, bot_id: str) -> bool:
    """Test GET /api/bots/{bot_id}/stats endpoint."""
    print_subheader(f"Testing GET /api/bots/{bot_id}/stats")
    
    if not token or not bot_id:
        print_error("No auth token or bot ID available")
        record_test("GET /api/bots/{bot_id}/stats", False, "No token or bot ID available")
        return False
    
    response, success = make_request("GET", f"/bots/{bot_id}/stats", auth_token=token)
    
    if success:
        if "bot_id" in response and "total_games" in response:
            print_success("Bot stats retrieved successfully")
            record_test("GET /api/bots/{bot_id}/stats", True)
            return True
        else:
            print_error("Response missing expected fields")
            record_test("GET /api/bots/{bot_id}/stats", False, "Response missing expected fields")
    else:
        record_test("GET /api/bots/{bot_id}/stats", False, "Request failed")
    
    return False

def test_delete_bot(token: str, bot_id: str) -> bool:
    """Test DELETE /api/bots/{bot_id} endpoint."""
    print_subheader(f"Testing DELETE /api/bots/{bot_id}")
    
    if not token or not bot_id:
        print_error("No auth token or bot ID available")
        record_test("DELETE /api/bots/{bot_id}", False, "No token or bot ID available")
        return False
    
    response, success = make_request("DELETE", f"/bots/{bot_id}", auth_token=token)
    
    if success:
        if "message" in response and "deleted" in response["message"].lower():
            print_success("Bot deleted successfully")
            record_test("DELETE /api/bots/{bot_id}", True)
            return True
        else:
            print_error("Response missing expected message")
            record_test("DELETE /api/bots/{bot_id}", False, "Response missing expected message")
    else:
        record_test("DELETE /api/bots/{bot_id}", False, "Request failed")
    
    return False

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

def run_bot_api_tests() -> None:
    """Run all bot API tests."""
    print_header("TESTING BOT MANAGEMENT APIs")
    
    # Login as admin
    admin_token = admin_login()
    if not admin_token:
        print_error("Failed to login as admin. Cannot proceed with tests.")
        return
    
    # Test GET /api/bots
    existing_bots = test_get_bots(admin_token)
    
    # Test POST /api/bots
    new_bot_id = test_create_bot(admin_token)
    if not new_bot_id:
        print_error("Failed to create a new bot. Cannot proceed with remaining tests.")
        return
    
    # Test GET /api/bots again to verify the new bot is included
    updated_bots = test_get_bots(admin_token)
    
    # Check if the number of bots increased
    if len(updated_bots) > len(existing_bots):
        print_success(f"Number of bots increased from {len(existing_bots)} to {len(updated_bots)}")
        record_test("Bot Creation Verification", True)
    else:
        print_error(f"Number of bots did not increase. Before: {len(existing_bots)}, After: {len(updated_bots)}")
        record_test("Bot Creation Verification", False, "Bot count did not increase")
    
    # Test PUT /api/bots/{bot_id}
    test_update_bot(admin_token, new_bot_id)
    
    # Test POST /api/bots/{bot_id}/toggle
    test_toggle_bot(admin_token, new_bot_id)
    
    # Test POST /api/bots/{bot_id}/setup-gems
    test_setup_bot_gems(admin_token, new_bot_id)
    
    # Test GET /api/bots/{bot_id}/stats
    test_bot_stats(admin_token, new_bot_id)
    
    # Test DELETE /api/bots/{bot_id}
    test_delete_bot(admin_token, new_bot_id)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    run_bot_api_tests()