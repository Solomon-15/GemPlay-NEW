#!/usr/bin/env python3
"""
COMPREHENSIVE ADMIN PANEL USER MANAGEMENT TESTING

This script tests all the expanded functionality for the admin panel Users section
as requested in the review request.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://629f70b8-18fb-40e8-982a-1f9a2bdf94c1.preview.emergentagent.com/api"
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
        
    except Exception as e:
        print_error(f"Request failed with exception: {e}")
        return {"error": str(e)}, False

def login_admin() -> Optional[str]:
    """Login as admin user."""
    print_subheader("Admin Login")
    
    response, success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def login_super_admin() -> Optional[str]:
    """Login as super admin user."""
    print_subheader("Super Admin Login")
    
    response, success = make_request("POST", "/auth/login", data=SUPER_ADMIN_USER)
    
    if success and "access_token" in response:
        print_success(f"Super Admin login successful")
        record_test("Super Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Super Admin login failed: {response}")
        record_test("Super Admin Login", False, f"Login failed: {response}")
        return None

def create_test_user() -> Optional[str]:
    """Create a test user for admin operations."""
    print_subheader("Creating Test User")
    
    # Generate unique user data
    timestamp = int(time.time())
    test_user = {
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    response, success = make_request("POST", "/auth/register", data=test_user)
    
    if success and "user_id" in response:
        user_id = response["user_id"]
        print_success(f"Test user created with ID: {user_id}")
        
        # Verify email to activate user
        if "verification_token" in response:
            verify_response, verify_success = make_request(
                "POST", "/auth/verify-email", 
                data={"token": response["verification_token"]}
            )
            if verify_success:
                print_success("Test user email verified")
            else:
                print_warning("Test user email verification failed")
        
        record_test("Create Test User", True)
        return user_id
    else:
        print_error(f"Test user creation failed: {response}")
        record_test("Create Test User", False, f"Creation failed: {response}")
        return None

def test_basic_user_listing_api(admin_token: str) -> None:
    """Test GET /api/admin/users with pagination, search, and filtering."""
    print_header("1. BASIC USER LISTING API TESTING")
    
    # Test 1: Basic user listing
    print_subheader("Test 1.1: Basic User Listing")
    response, success = make_request("GET", "/admin/users", auth_token=admin_token)
    
    if success:
        print_success("Basic user listing successful")
        
        # Check required fields in response
        required_fields = ["users", "total", "page", "limit"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("Response contains all required pagination fields")
            record_test("User Listing - Basic Structure", True)
        else:
            print_error(f"Response missing fields: {missing_fields}")
            record_test("User Listing - Basic Structure", False, f"Missing: {missing_fields}")
        
        # Check user data fields
        if "users" in response and response["users"]:
            user = response["users"][0]
            expected_user_fields = [
                "id", "username", "email", "role", "status", "created_at", "last_login",
                "total_gems", "total_gems_value", "active_bets_count", 
                "total_games_played", "total_games_won", "total_games_lost", "total_games_draw"
            ]
            
            missing_user_fields = [field for field in expected_user_fields if field not in user]
            
            if not missing_user_fields:
                print_success("User data contains all required fields")
                record_test("User Listing - User Data Fields", True)
            else:
                print_warning(f"User data missing fields: {missing_user_fields}")
                record_test("User Listing - User Data Fields", False, f"Missing: {missing_user_fields}")
        
    else:
        print_error(f"Basic user listing failed: {response}")
        record_test("User Listing - Basic", False, f"Request failed: {response}")
    
    # Test 2: Pagination
    print_subheader("Test 1.2: Pagination")
    response, success = make_request(
        "GET", "/admin/users", 
        data={"page": 1, "limit": 5}, 
        auth_token=admin_token
    )
    
    if success:
        if "users" in response and len(response["users"]) <= 5:
            print_success("Pagination limit working correctly")
            record_test("User Listing - Pagination", True)
        else:
            print_error("Pagination limit not working")
            record_test("User Listing - Pagination", False, "Limit not respected")
    else:
        print_error(f"Pagination test failed: {response}")
        record_test("User Listing - Pagination", False, f"Request failed")
    
    # Test 3: Search by username
    print_subheader("Test 1.3: Search by Username")
    response, success = make_request(
        "GET", "/admin/users", 
        data={"search": "admin"}, 
        auth_token=admin_token
    )
    
    if success:
        if "users" in response:
            admin_found = any("admin" in user.get("username", "").lower() for user in response["users"])
            if admin_found:
                print_success("Search by username working")
                record_test("User Listing - Search Username", True)
            else:
                print_warning("Search by username returned no admin users")
                record_test("User Listing - Search Username", False, "No admin found")
        else:
            print_error("Search response missing users field")
            record_test("User Listing - Search Username", False, "Missing users field")
    else:
        print_error(f"Search by username failed: {response}")
        record_test("User Listing - Search Username", False, f"Request failed")
    
    # Test 4: Search by email
    print_subheader("Test 1.4: Search by Email")
    response, success = make_request(
        "GET", "/admin/users", 
        data={"search": "admin@gemplay.com"}, 
        auth_token=admin_token
    )
    
    if success:
        if "users" in response:
            admin_found = any("admin@gemplay.com" in user.get("email", "") for user in response["users"])
            if admin_found:
                print_success("Search by email working")
                record_test("User Listing - Search Email", True)
            else:
                print_warning("Search by email returned no admin users")
                record_test("User Listing - Search Email", False, "No admin found")
        else:
            print_error("Search response missing users field")
            record_test("User Listing - Search Email", False, "Missing users field")
    else:
        print_error(f"Search by email failed: {response}")
        record_test("User Listing - Search Email", False, f"Request failed")
    
    # Test 5: Status filtering
    print_subheader("Test 1.5: Status Filtering")
    for status in ["ACTIVE", "BANNED", "EMAIL_PENDING"]:
        response, success = make_request(
            "GET", "/admin/users", 
            data={"status": status}, 
            auth_token=admin_token
        )
        
        if success:
            if "users" in response:
                all_correct_status = all(user.get("status") == status for user in response["users"])
                if all_correct_status or len(response["users"]) == 0:
                    print_success(f"Status filtering for {status} working")
                    record_test(f"User Listing - Filter {status}", True)
                else:
                    print_error(f"Status filtering for {status} returned wrong status users")
                    record_test(f"User Listing - Filter {status}", False, "Wrong status returned")
            else:
                print_error(f"Status filter response missing users field")
                record_test(f"User Listing - Filter {status}", False, "Missing users field")
        else:
            print_error(f"Status filtering for {status} failed: {response}")
            record_test(f"User Listing - Filter {status}", False, f"Request failed")

def test_user_detailed_information_endpoints(admin_token: str, test_user_id: str) -> None:
    """Test user detailed information endpoints."""
    print_header("2. USER DETAILED INFORMATION ENDPOINTS TESTING")
    
    # Test 1: Get user gems
    print_subheader("Test 2.1: GET /api/admin/users/{user_id}/gems")
    response, success = make_request(
        "GET", f"/admin/users/{test_user_id}/gems", 
        auth_token=admin_token
    )
    
    if success:
        print_success("User gems endpoint accessible")
        
        # Check if response is a list of gems
        if isinstance(response, list):
            print_success("Response is a list of gems")
            
            # Check gem data structure if gems exist
            if response:
                gem = response[0]
                expected_fields = ["type", "name", "price", "color", "icon", "rarity", "quantity", "frozen_quantity"]
                missing_fields = [field for field in expected_fields if field not in gem]
                
                if not missing_fields:
                    print_success("Gem data contains all required fields")
                    record_test("User Gems - Data Structure", True)
                else:
                    print_error(f"Gem data missing fields: {missing_fields}")
                    record_test("User Gems - Data Structure", False, f"Missing: {missing_fields}")
            else:
                print_success("User has no gems (expected for new user)")
                record_test("User Gems - Data Structure", True, "No gems for new user")
            
            record_test("User Gems - Endpoint", True)
        else:
            print_error("Response is not a list")
            record_test("User Gems - Endpoint", False, "Response not a list")
    else:
        print_error(f"User gems endpoint failed: {response}")
        record_test("User Gems - Endpoint", False, f"Request failed")
    
    # Test 2: Get user bets
    print_subheader("Test 2.2: GET /api/admin/users/{user_id}/bets")
    response, success = make_request(
        "GET", f"/admin/users/{test_user_id}/bets", 
        auth_token=admin_token
    )
    
    if success:
        print_success("User bets endpoint accessible")
        
        # Check if response has expected structure
        if "bets" in response:
            print_success("Response contains bets field")
            
            # Check bet data structure if bets exist
            if response["bets"]:
                bet = response["bets"][0]
                expected_fields = ["game_id", "bet_amount", "status", "created_at", "opponent"]
                missing_fields = [field for field in expected_fields if field not in bet]
                
                if not missing_fields:
                    print_success("Bet data contains all required fields")
                    record_test("User Bets - Data Structure", True)
                else:
                    print_error(f"Bet data missing fields: {missing_fields}")
                    record_test("User Bets - Data Structure", False, f"Missing: {missing_fields}")
            else:
                print_success("User has no active bets (expected for new user)")
                record_test("User Bets - Data Structure", True, "No bets for new user")
            
            record_test("User Bets - Endpoint", True)
        else:
            print_error("Response missing bets field")
            record_test("User Bets - Endpoint", False, "Missing bets field")
    else:
        print_error(f"User bets endpoint failed: {response}")
        record_test("User Bets - Endpoint", False, f"Request failed")
    
    # Test 3: Get user stats
    print_subheader("Test 2.3: GET /api/admin/users/{user_id}/stats")
    response, success = make_request(
        "GET", f"/admin/users/{test_user_id}/stats", 
        auth_token=admin_token
    )
    
    if success:
        print_success("User stats endpoint accessible")
        
        # Check comprehensive stats structure
        expected_sections = ["game_statistics", "financial_data", "activity_data", "ip_history"]
        missing_sections = [section for section in expected_sections if section not in response]
        
        if not missing_sections:
            print_success("Stats response contains all required sections")
            
            # Check game statistics
            game_stats = response.get("game_statistics", {})
            expected_game_fields = ["total", "won", "lost", "draw", "win_rate"]
            missing_game_fields = [field for field in expected_game_fields if field not in game_stats]
            
            if not missing_game_fields:
                print_success("Game statistics complete")
                record_test("User Stats - Game Statistics", True)
            else:
                print_error(f"Game statistics missing: {missing_game_fields}")
                record_test("User Stats - Game Statistics", False, f"Missing: {missing_game_fields}")
            
            # Check financial data
            financial_data = response.get("financial_data", {})
            expected_financial_fields = ["profit_loss", "gifts_sent", "gifts_received"]
            missing_financial_fields = [field for field in expected_financial_fields if field not in financial_data]
            
            if not missing_financial_fields:
                print_success("Financial data complete")
                record_test("User Stats - Financial Data", True)
            else:
                print_error(f"Financial data missing: {missing_financial_fields}")
                record_test("User Stats - Financial Data", False, f"Missing: {missing_financial_fields}")
            
            # Check activity data
            activity_data = response.get("activity_data", {})
            expected_activity_fields = ["registration_date", "last_login"]
            missing_activity_fields = [field for field in expected_activity_fields if field not in activity_data]
            
            if not missing_activity_fields:
                print_success("Activity data complete")
                record_test("User Stats - Activity Data", True)
            else:
                print_error(f"Activity data missing: {missing_activity_fields}")
                record_test("User Stats - Activity Data", False, f"Missing: {missing_activity_fields}")
            
            # Check IP history
            ip_history = response.get("ip_history", [])
            if isinstance(ip_history, list):
                print_success("IP history is a list")
                record_test("User Stats - IP History", True)
            else:
                print_error("IP history is not a list")
                record_test("User Stats - IP History", False, "Not a list")
            
            record_test("User Stats - Endpoint", True)
        else:
            print_error(f"Stats response missing sections: {missing_sections}")
            record_test("User Stats - Endpoint", False, f"Missing: {missing_sections}")
    else:
        print_error(f"User stats endpoint failed: {response}")
        record_test("User Stats - Endpoint", False, f"Request failed")

def test_user_modification_endpoints(admin_token: str, test_user_id: str) -> None:
    """Test user modification endpoints."""
    print_header("3. USER MODIFICATION ENDPOINTS TESTING")
    
    # Test 1: Edit user data
    print_subheader("Test 3.1: PUT /api/admin/users/{user_id}")
    
    # First get current user data
    response, success = make_request("GET", f"/admin/users", auth_token=admin_token)
    current_user = None
    if success and "users" in response:
        for user in response["users"]:
            if user["id"] == test_user_id:
                current_user = user
                break
    
    if current_user:
        # Update user data
        update_data = {
            "username": f"updated_{current_user['username']}",
            "email": current_user["email"],  # Keep same email
            "role": "USER",
            "balance": 2000.0
        }
        
        response, success = make_request(
            "PUT", f"/admin/users/{test_user_id}", 
            data=update_data,
            auth_token=admin_token
        )
        
        if success:
            print_success("User update successful")
            
            # Verify the update
            verify_response, verify_success = make_request("GET", f"/admin/users", auth_token=admin_token)
            if verify_success and "users" in verify_response:
                updated_user = None
                for user in verify_response["users"]:
                    if user["id"] == test_user_id:
                        updated_user = user
                        break
                
                if updated_user and updated_user["username"] == update_data["username"]:
                    print_success("User data successfully updated")
                    record_test("User Modification - Edit User", True)
                else:
                    print_error("User data not updated correctly")
                    record_test("User Modification - Edit User", False, "Data not updated")
            else:
                print_warning("Could not verify user update")
                record_test("User Modification - Edit User", True, "Update successful but verification failed")
        else:
            print_error(f"User update failed: {response}")
            record_test("User Modification - Edit User", False, f"Request failed")
    else:
        print_error("Could not find test user for update")
        record_test("User Modification - Edit User", False, "User not found")
    
    # Test 2: Ban user
    print_subheader("Test 3.2: POST /api/admin/users/{user_id}/ban")
    
    ban_data = {
        "reason": "Test ban for automated testing",
        "duration_hours": 24
    }
    
    response, success = make_request(
        "POST", f"/admin/users/{test_user_id}/ban", 
        data=ban_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("User ban successful")
        
        # Check response structure
        if "message" in response and "ban_until" in response:
            print_success("Ban response contains required fields")
            record_test("User Modification - Ban User", True)
        else:
            print_error("Ban response missing required fields")
            record_test("User Modification - Ban User", False, "Missing response fields")
    else:
        print_error(f"User ban failed: {response}")
        record_test("User Modification - Ban User", False, f"Request failed")
    
    # Test 3: Unban user
    print_subheader("Test 3.3: POST /api/admin/users/{user_id}/unban")
    
    response, success = make_request(
        "POST", f"/admin/users/{test_user_id}/unban", 
        auth_token=admin_token
    )
    
    if success:
        print_success("User unban successful")
        
        if "message" in response:
            print_success("Unban response contains message")
            record_test("User Modification - Unban User", True)
        else:
            print_error("Unban response missing message")
            record_test("User Modification - Unban User", False, "Missing message")
    else:
        print_error(f"User unban failed: {response}")
        record_test("User Modification - Unban User", False, f"Request failed")

def test_gem_management_endpoints(admin_token: str, test_user_id: str) -> None:
    """Test gem management endpoints."""
    print_header("4. GEM MANAGEMENT ENDPOINTS TESTING")
    
    # First, give the test user some gems to work with
    print_subheader("Setup: Adding gems to test user")
    
    # Login as test user to buy gems
    test_user_response, _ = make_request("GET", f"/admin/users", auth_token=admin_token)
    test_user_email = None
    if test_user_response and "users" in test_user_response:
        for user in test_user_response["users"]:
            if user["id"] == test_user_id:
                test_user_email = user["email"]
                break
    
    if test_user_email:
        # Login as test user
        test_login_data = {
            "email": test_user_email,
            "password": "Test123!"
        }
        
        login_response, login_success = make_request("POST", "/auth/login", data=test_login_data)
        
        if login_success and "access_token" in login_response:
            test_user_token = login_response["access_token"]
            
            # Buy some gems
            buy_response, buy_success = make_request(
                "POST", "/gems/buy?gem_type=Ruby&quantity=10",
                auth_token=test_user_token
            )
            
            if buy_success:
                print_success("Added Ruby gems to test user")
            else:
                print_warning("Could not add gems to test user")
    
    # Test 1: Freeze gems
    print_subheader("Test 4.1: POST /api/admin/users/{user_id}/gems/freeze")
    
    freeze_data = {
        "gem_type": "Ruby",
        "quantity": 5,
        "reason": "Admin testing freeze functionality"
    }
    
    response, success = make_request(
        "POST", f"/admin/users/{test_user_id}/gems/freeze", 
        data=freeze_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("Gem freeze successful")
        
        if "message" in response and "frozen_quantity" in response:
            print_success("Freeze response contains required fields")
            record_test("Gem Management - Freeze Gems", True)
        else:
            print_error("Freeze response missing required fields")
            record_test("Gem Management - Freeze Gems", False, "Missing response fields")
    else:
        print_error(f"Gem freeze failed: {response}")
        record_test("Gem Management - Freeze Gems", False, f"Request failed")
    
    # Test 2: Unfreeze gems
    print_subheader("Test 4.2: POST /api/admin/users/{user_id}/gems/unfreeze")
    
    unfreeze_data = {
        "gem_type": "Ruby",
        "quantity": 3
    }
    
    response, success = make_request(
        "POST", f"/admin/users/{test_user_id}/gems/unfreeze", 
        data=unfreeze_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("Gem unfreeze successful")
        
        if "message" in response and "unfrozen_quantity" in response:
            print_success("Unfreeze response contains required fields")
            record_test("Gem Management - Unfreeze Gems", True)
        else:
            print_error("Unfreeze response missing required fields")
            record_test("Gem Management - Unfreeze Gems", False, "Missing response fields")
    else:
        print_error(f"Gem unfreeze failed: {response}")
        record_test("Gem Management - Unfreeze Gems", False, f"Request failed")
    
    # Test 3: Remove gems with notification
    print_subheader("Test 4.3: DELETE /api/admin/users/{user_id}/gems")
    
    remove_data = {
        "gem_type": "Ruby",
        "quantity": 2,
        "reason": "Admin testing gem removal",
        "notify_user": True,
        "notification_text": "Your gems were removed by admin for testing purposes"
    }
    
    response, success = make_request(
        "DELETE", f"/admin/users/{test_user_id}/gems", 
        data=remove_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("Gem removal successful")
        
        if "message" in response and "removed_quantity" in response:
            print_success("Remove response contains required fields")
            
            # Check if notification was created
            if "notification_sent" in response and response["notification_sent"]:
                print_success("Notification sent to user")
                record_test("Gem Management - Remove Gems with Notification", True)
            else:
                print_warning("Notification not confirmed")
                record_test("Gem Management - Remove Gems with Notification", True, "Removal successful, notification unclear")
        else:
            print_error("Remove response missing required fields")
            record_test("Gem Management - Remove Gems with Notification", False, "Missing response fields")
    else:
        print_error(f"Gem removal failed: {response}")
        record_test("Gem Management - Remove Gems with Notification", False, f"Request failed")

def test_bet_management_endpoints(admin_token: str, test_user_id: str) -> None:
    """Test bet management endpoints."""
    print_header("5. BET MANAGEMENT ENDPOINTS TESTING")
    
    # First create a bet for the test user
    print_subheader("Setup: Creating a bet for test user")
    
    # Get test user details
    test_user_response, _ = make_request("GET", f"/admin/users", auth_token=admin_token)
    test_user_email = None
    if test_user_response and "users" in test_user_response:
        for user in test_user_response["users"]:
            if user["id"] == test_user_id:
                test_user_email = user["email"]
                break
    
    bet_id = None
    if test_user_email:
        # Login as test user
        test_login_data = {
            "email": test_user_email,
            "password": "Test123!"
        }
        
        login_response, login_success = make_request("POST", "/auth/login", data=test_login_data)
        
        if login_success and "access_token" in login_response:
            test_user_token = login_response["access_token"]
            
            # Create a game/bet
            create_game_data = {
                "move": "rock",
                "bet_gems": {"Ruby": 3}
            }
            
            game_response, game_success = make_request(
                "POST", "/games/create",
                data=create_game_data,
                auth_token=test_user_token
            )
            
            if game_success and "game_id" in game_response:
                bet_id = game_response["game_id"]
                print_success(f"Created bet with ID: {bet_id}")
            else:
                print_warning("Could not create bet for testing")
    
    # Test 1: Cancel user's bet
    print_subheader("Test 5.1: POST /api/admin/users/{user_id}/bets/{bet_id}/cancel")
    
    if bet_id:
        response, success = make_request(
            "POST", f"/admin/users/{test_user_id}/bets/{bet_id}/cancel", 
            data={"reason": "Admin cancelled for testing"},
            auth_token=admin_token
        )
        
        if success:
            print_success("Bet cancellation successful")
            
            if "message" in response and "bet_id" in response:
                print_success("Cancel response contains required fields")
                record_test("Bet Management - Cancel Bet", True)
            else:
                print_error("Cancel response missing required fields")
                record_test("Bet Management - Cancel Bet", False, "Missing response fields")
        else:
            print_error(f"Bet cancellation failed: {response}")
            record_test("Bet Management - Cancel Bet", False, f"Request failed")
    else:
        print_warning("No bet available to cancel")
        record_test("Bet Management - Cancel Bet", False, "No bet to cancel")

def test_user_deletion_super_admin_only(admin_token: str, super_admin_token: str, test_user_id: str) -> None:
    """Test user deletion (SUPER_ADMIN only)."""
    print_header("6. USER DELETION (SUPER_ADMIN ONLY) TESTING")
    
    # Test 1: Regular admin should NOT be able to delete users
    print_subheader("Test 6.1: Regular Admin Access Denied")
    
    response, success = make_request(
        "DELETE", f"/admin/users/{test_user_id}", 
        data={"reason": "Test deletion attempt by regular admin"},
        auth_token=admin_token,
        expected_status=403
    )
    
    if not success and response.get("detail") == "Super admin permissions required":
        print_success("Regular admin correctly denied user deletion")
        record_test("User Deletion - Admin Access Denied", True)
    else:
        print_error("Regular admin was not properly denied")
        record_test("User Deletion - Admin Access Denied", False, "Access not denied")
    
    # Test 2: Super admin should be able to delete users
    print_subheader("Test 6.2: Super Admin User Deletion")
    
    if super_admin_token:
        response, success = make_request(
            "DELETE", f"/admin/users/{test_user_id}", 
            data={"reason": "Test deletion by super admin"},
            auth_token=super_admin_token
        )
        
        if success:
            print_success("Super admin user deletion successful")
            
            if "message" in response and "deleted_user_id" in response:
                print_success("Deletion response contains required fields")
                record_test("User Deletion - Super Admin Success", True)
            else:
                print_error("Deletion response missing required fields")
                record_test("User Deletion - Super Admin Success", False, "Missing response fields")
        else:
            print_error(f"Super admin user deletion failed: {response}")
            record_test("User Deletion - Super Admin Success", False, f"Request failed")
    else:
        print_error("No super admin token available")
        record_test("User Deletion - Super Admin Success", False, "No super admin token")

def test_suspicious_activity_detection(admin_token: str) -> None:
    """Test suspicious activity detection."""
    print_header("7. SUSPICIOUS ACTIVITY DETECTION TESTING")
    
    # Test 1: Get users with high win rates
    print_subheader("Test 7.1: High Win Rate Detection")
    
    response, success = make_request(
        "GET", "/admin/users", 
        data={"suspicious": "high_win_rate"}, 
        auth_token=admin_token
    )
    
    if success:
        print_success("High win rate detection endpoint accessible")
        
        if "users" in response:
            # Check if any users have win rates > 80%
            suspicious_users = []
            for user in response["users"]:
                if user.get("total_games_played", 0) >= 10:
                    win_rate = (user.get("total_games_won", 0) / user.get("total_games_played", 1)) * 100
                    if win_rate > 80:
                        suspicious_users.append(user)
            
            print_success(f"Found {len(suspicious_users)} users with suspicious win rates")
            record_test("Suspicious Activity - High Win Rate", True)
        else:
            print_error("Response missing users field")
            record_test("Suspicious Activity - High Win Rate", False, "Missing users field")
    else:
        print_error(f"High win rate detection failed: {response}")
        record_test("Suspicious Activity - High Win Rate", False, f"Request failed")
    
    # Test 2: Frequent bot games detection
    print_subheader("Test 7.2: Frequent Bot Games Detection")
    
    response, success = make_request(
        "GET", "/admin/users", 
        data={"suspicious": "frequent_bot_games"}, 
        auth_token=admin_token
    )
    
    if success:
        print_success("Frequent bot games detection endpoint accessible")
        record_test("Suspicious Activity - Frequent Bot Games", True)
    else:
        print_error(f"Frequent bot games detection failed: {response}")
        record_test("Suspicious Activity - Frequent Bot Games", False, f"Request failed")
    
    # Test 3: Multiple gifts to same user detection
    print_subheader("Test 7.3: Multiple Gifts Detection")
    
    response, success = make_request(
        "GET", "/admin/users", 
        data={"suspicious": "multiple_gifts"}, 
        auth_token=admin_token
    )
    
    if success:
        print_success("Multiple gifts detection endpoint accessible")
        record_test("Suspicious Activity - Multiple Gifts", True)
    else:
        print_error(f"Multiple gifts detection failed: {response}")
        record_test("Suspicious Activity - Multiple Gifts", False, f"Request failed")

def test_notification_system_integration(admin_token: str, test_user_id: str) -> None:
    """Test notification system integration."""
    print_header("8. NOTIFICATION SYSTEM INTEGRATION TESTING")
    
    # Test 1: Create notification when admin modifies user gems
    print_subheader("Test 8.1: Admin Gem Modification Notification")
    
    # Modify user gems (this should create a notification)
    modify_data = {
        "gem_type": "Ruby",
        "quantity": 1,
        "reason": "Admin testing notification system",
        "notify_user": True,
        "notification_text": "Your gems were modified by admin for testing purposes"
    }
    
    response, success = make_request(
        "DELETE", f"/admin/users/{test_user_id}/gems", 
        data=modify_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("Gem modification with notification successful")
        
        # Check if notification was created
        if "notification_sent" in response and response["notification_sent"]:
            print_success("Notification creation confirmed")
            record_test("Notification System - Gem Modification", True)
        else:
            print_warning("Notification creation not confirmed")
            record_test("Notification System - Gem Modification", False, "Notification not confirmed")
    else:
        print_error(f"Gem modification failed: {response}")
        record_test("Notification System - Gem Modification", False, f"Request failed")
    
    # Test 2: Verify custom notification text
    print_subheader("Test 8.2: Custom Notification Text")
    
    # Get test user details to login and check notifications
    test_user_response, _ = make_request("GET", f"/admin/users", auth_token=admin_token)
    test_user_email = None
    if test_user_response and "users" in test_user_response:
        for user in test_user_response["users"]:
            if user["id"] == test_user_id:
                test_user_email = user["email"]
                break
    
    if test_user_email:
        # Login as test user
        test_login_data = {
            "email": test_user_email,
            "password": "Test123!"
        }
        
        login_response, login_success = make_request("POST", "/auth/login", data=test_login_data)
        
        if login_success and "access_token" in login_response:
            test_user_token = login_response["access_token"]
            
            # Get user notifications
            notifications_response, notifications_success = make_request(
                "GET", "/notifications",
                auth_token=test_user_token
            )
            
            if notifications_success and isinstance(notifications_response, list):
                # Look for our test notification
                test_notification_found = False
                for notification in notifications_response:
                    if "testing purposes" in notification.get("message", ""):
                        test_notification_found = True
                        print_success("Custom notification text properly sent")
                        break
                
                if test_notification_found:
                    record_test("Notification System - Custom Text", True)
                else:
                    print_warning("Custom notification text not found")
                    record_test("Notification System - Custom Text", False, "Custom text not found")
            else:
                print_error("Could not retrieve user notifications")
                record_test("Notification System - Custom Text", False, "Could not retrieve notifications")
        else:
            print_error("Could not login as test user")
            record_test("Notification System - Custom Text", False, "Could not login as test user")
    else:
        print_error("Could not find test user email")
        record_test("Notification System - Custom Text", False, "Could not find test user")

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

def main():
    """Main test execution function."""
    print_header("COMPREHENSIVE ADMIN PANEL USER MANAGEMENT TESTING")
    print("Testing all expanded functionality for the admin panel Users section")
    
    # Step 1: Login as admin and super admin
    admin_token = login_admin()
    super_admin_token = login_super_admin()
    
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    # Step 2: Create a test user for admin operations
    test_user_id = create_test_user()
    
    if not test_user_id:
        print_error("Cannot proceed without test user")
        return
    
    # Step 3: Run all test suites
    try:
        test_basic_user_listing_api(admin_token)
        test_user_detailed_information_endpoints(admin_token, test_user_id)
        test_user_modification_endpoints(admin_token, test_user_id)
        test_gem_management_endpoints(admin_token, test_user_id)
        test_bet_management_endpoints(admin_token, test_user_id)
        test_user_deletion_super_admin_only(admin_token, super_admin_token, test_user_id)
        test_suspicious_activity_detection(admin_token)
        test_notification_system_integration(admin_token, test_user_id)
        
    except Exception as e:
        print_error(f"Test execution failed with exception: {e}")
        record_test("Test Execution", False, f"Exception: {e}")
    
    # Step 4: Print summary
    print_summary()

if __name__ == "__main__":
    main()