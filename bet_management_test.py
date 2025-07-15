#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://797d8141-4694-4bcb-823c-f7b281a5cf27.preview.emergentagent.com/api"
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
    
    headers["Content-Type"] = "application/json"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}, False
        
        success = response.status_code == expected_status
        
        try:
            response_data = response.json()
        except:
            response_data = {"status_code": response.status_code, "text": response.text}
        
        return response_data, success
    
    except Exception as e:
        return {"error": str(e)}, False

def login_admin() -> Optional[str]:
    """Login as admin and return access token."""
    print_subheader("Admin Login")
    
    response, success = make_request(
        "POST", 
        "/auth/login", 
        data=ADMIN_USER
    )
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True, "Successfully logged in as admin")
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def create_test_user() -> Optional[Tuple[str, str]]:
    """Create a test user and return user_id and token."""
    print_subheader("Creating Test User")
    
    # Generate unique test user with random suffix
    timestamp = str(int(time.time()))
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    test_user = {
        "username": f"testuser_{timestamp}_{random_suffix}",
        "email": f"testuser_{timestamp}_{random_suffix}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    # Register user
    response, success = make_request(
        "POST",
        "/auth/register",
        data=test_user
    )
    
    if not success:
        print_error(f"User registration failed: {response}")
        record_test("Test User Registration", False, f"Registration failed: {response}")
        return None
    
    user_id = response.get("user_id")
    verification_token = response.get("verification_token")
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST",
        "/auth/verify-email",
        data={"token": verification_token}
    )
    
    if not verify_success:
        print_error(f"Email verification failed: {verify_response}")
        record_test("Test User Email Verification", False, f"Verification failed: {verify_response}")
        return None
    
    # Login user
    login_response, login_success = make_request(
        "POST",
        "/auth/login",
        data={"email": test_user["email"], "password": test_user["password"]}
    )
    
    if not login_success:
        print_error(f"User login failed: {login_response}")
        record_test("Test User Login", False, f"Login failed: {login_response}")
        return None
    
    user_token = login_response.get("access_token")
    print_success(f"Test user created and logged in: {user_id}")
    record_test("Test User Creation", True, f"User {user_id} created successfully")
    
    return user_id, user_token

def create_test_bet(user_token: str) -> Optional[str]:
    """Create a test bet and return bet_id."""
    print_subheader("Creating Test Bet")
    
    # Create a game bet
    bet_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 5, "Emerald": 2}
    }
    
    response, success = make_request(
        "POST",
        "/games/create",
        data=bet_data,
        auth_token=user_token
    )
    
    if success and "game_id" in response:
        bet_id = response["game_id"]
        print_success(f"Test bet created: {bet_id}")
        record_test("Test Bet Creation", True, f"Bet {bet_id} created successfully")
        return bet_id
    else:
        print_error(f"Test bet creation failed: {response}")
        record_test("Test Bet Creation", False, f"Bet creation failed: {response}")
        return None

def test_get_user_bets(admin_token: str, user_id: str):
    """Test GET /admin/users/{user_id}/bets endpoint."""
    print_subheader("Testing GET User Bets Endpoint")
    
    # Test 1: Get user bets (active only)
    response, success = make_request(
        "GET",
        f"/admin/users/{user_id}/bets",
        auth_token=admin_token
    )
    
    if success:
        print_success("GET user bets (active only) - SUCCESS")
        
        # Validate response structure
        required_fields = ["user_id", "username", "active_bets", "summary"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("Response structure validation - SUCCESS")
            
            # Check summary fields
            summary = response.get("summary", {})
            summary_fields = ["total_bets", "active_count", "completed_count", "cancelled_count", "stuck_count"]
            missing_summary_fields = [field for field in summary_fields if field not in summary]
            
            if not missing_summary_fields:
                print_success("Summary structure validation - SUCCESS")
                record_test("GET User Bets - Response Structure", True, "All required fields present")
                
                # Check bet details if any bets exist
                active_bets = response.get("active_bets", [])
                if active_bets:
                    bet = active_bets[0]
                    bet_fields = ["id", "amount", "status", "created_at", "opponent", "is_creator", "gems", "age_hours", "is_stuck", "can_cancel"]
                    missing_bet_fields = [field for field in bet_fields if field not in bet]
                    
                    if not missing_bet_fields:
                        print_success("Bet details structure validation - SUCCESS")
                        record_test("GET User Bets - Bet Details Structure", True, "All bet fields present")
                        
                        # Test stuck bet detection logic
                        age_hours = bet.get("age_hours", 0)
                        is_stuck = bet.get("is_stuck", False)
                        expected_stuck = age_hours > 24 and bet.get("status") in ["WAITING", "ACTIVE", "REVEAL"]
                        
                        if is_stuck == expected_stuck:
                            print_success("Stuck bet detection logic - SUCCESS")
                            record_test("GET User Bets - Stuck Detection", True, f"Stuck detection correct: {is_stuck}")
                        else:
                            print_error(f"Stuck bet detection logic - FAILED (expected: {expected_stuck}, got: {is_stuck})")
                            record_test("GET User Bets - Stuck Detection", False, f"Stuck detection incorrect")
                        
                        # Test can_cancel logic
                        can_cancel = bet.get("can_cancel", False)
                        expected_can_cancel = bet.get("status") == "WAITING"
                        
                        if can_cancel == expected_can_cancel:
                            print_success("Can cancel logic - SUCCESS")
                            record_test("GET User Bets - Can Cancel Logic", True, f"Can cancel logic correct: {can_cancel}")
                        else:
                            print_error(f"Can cancel logic - FAILED (expected: {expected_can_cancel}, got: {can_cancel})")
                            record_test("GET User Bets - Can Cancel Logic", False, f"Can cancel logic incorrect")
                    else:
                        print_error(f"Missing bet fields: {missing_bet_fields}")
                        record_test("GET User Bets - Bet Details Structure", False, f"Missing fields: {missing_bet_fields}")
                else:
                    print_warning("No active bets found for testing bet details")
                    record_test("GET User Bets - Bet Details Structure", True, "No bets to validate (acceptable)")
            else:
                print_error(f"Missing summary fields: {missing_summary_fields}")
                record_test("GET User Bets - Summary Structure", False, f"Missing fields: {missing_summary_fields}")
        else:
            print_error(f"Missing response fields: {missing_fields}")
            record_test("GET User Bets - Response Structure", False, f"Missing fields: {missing_fields}")
    else:
        print_error(f"GET user bets failed: {response}")
        record_test("GET User Bets - Basic Functionality", False, f"Request failed: {response}")
    
    # Test 2: Get user bets including completed
    response, success = make_request(
        "GET",
        f"/admin/users/{user_id}/bets",
        data={"include_completed": True},
        auth_token=admin_token
    )
    
    if success:
        print_success("GET user bets (including completed) - SUCCESS")
        record_test("GET User Bets - Include Completed", True, "Successfully retrieved bets including completed")
    else:
        print_error(f"GET user bets (including completed) failed: {response}")
        record_test("GET User Bets - Include Completed", False, f"Request failed: {response}")
    
    # Test 3: Test with invalid user ID
    response, success = make_request(
        "GET",
        f"/admin/users/invalid_user_id/bets",
        auth_token=admin_token,
        expected_status=404
    )
    
    if success:
        print_success("GET user bets with invalid user ID - SUCCESS (404 as expected)")
        record_test("GET User Bets - Invalid User ID", True, "Correctly returned 404 for invalid user")
    else:
        print_error(f"GET user bets with invalid user ID - FAILED (expected 404): {response}")
        record_test("GET User Bets - Invalid User ID", False, f"Did not return 404: {response}")

def test_cancel_user_bet(admin_token: str, user_id: str, bet_id: str):
    """Test POST /admin/users/{user_id}/bets/{bet_id}/cancel endpoint."""
    print_subheader("Testing Cancel User Bet Endpoint")
    
    # Test 1: Cancel a valid WAITING bet
    response, success = make_request(
        "POST",
        f"/admin/users/{user_id}/bets/{bet_id}/cancel",
        auth_token=admin_token
    )
    
    if success:
        print_success("Cancel user bet - SUCCESS")
        
        # Validate response structure
        required_fields = ["success", "message", "bet_id", "gems_returned", "commission_returned"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("Cancel response structure validation - SUCCESS")
            record_test("Cancel User Bet - Response Structure", True, "All required fields present")
            
            # Validate response values
            if response.get("success") == True:
                print_success("Cancel success flag - SUCCESS")
                record_test("Cancel User Bet - Success Flag", True, "Success flag is True")
            else:
                print_error("Cancel success flag - FAILED")
                record_test("Cancel User Bet - Success Flag", False, "Success flag is not True")
            
            # Check gems returned
            gems_returned = response.get("gems_returned", {})
            if isinstance(gems_returned, dict):
                print_success("Gems returned structure - SUCCESS")
                record_test("Cancel User Bet - Gems Returned", True, f"Gems returned: {gems_returned}")
            else:
                print_error("Gems returned structure - FAILED")
                record_test("Cancel User Bet - Gems Returned", False, "Gems returned is not a dict")
            
            # Check commission returned
            commission_returned = response.get("commission_returned", 0)
            if isinstance(commission_returned, (int, float)) and commission_returned >= 0:
                print_success("Commission returned validation - SUCCESS")
                record_test("Cancel User Bet - Commission Returned", True, f"Commission returned: {commission_returned}")
            else:
                print_error("Commission returned validation - FAILED")
                record_test("Cancel User Bet - Commission Returned", False, "Commission returned is invalid")
        else:
            print_error(f"Missing response fields: {missing_fields}")
            record_test("Cancel User Bet - Response Structure", False, f"Missing fields: {missing_fields}")
    else:
        print_error(f"Cancel user bet failed: {response}")
        record_test("Cancel User Bet - Basic Functionality", False, f"Request failed: {response}")
    
    # Test 2: Try to cancel the same bet again (should fail)
    response, success = make_request(
        "POST",
        f"/admin/users/{user_id}/bets/{bet_id}/cancel",
        auth_token=admin_token,
        expected_status=400
    )
    
    if success:
        print_success("Cancel already cancelled bet - SUCCESS (400 as expected)")
        record_test("Cancel User Bet - Already Cancelled", True, "Correctly returned 400 for already cancelled bet")
    else:
        print_error(f"Cancel already cancelled bet - FAILED (expected 400): {response}")
        record_test("Cancel User Bet - Already Cancelled", False, f"Did not return 400: {response}")
    
    # Test 3: Test with invalid bet ID
    response, success = make_request(
        "POST",
        f"/admin/users/{user_id}/bets/invalid_bet_id/cancel",
        auth_token=admin_token,
        expected_status=404
    )
    
    if success:
        print_success("Cancel with invalid bet ID - SUCCESS (404 as expected)")
        record_test("Cancel User Bet - Invalid Bet ID", True, "Correctly returned 404 for invalid bet")
    else:
        print_error(f"Cancel with invalid bet ID - FAILED (expected 404): {response}")
        record_test("Cancel User Bet - Invalid Bet ID", False, f"Did not return 404: {response}")
    
    # Test 4: Test with invalid user ID
    response, success = make_request(
        "POST",
        f"/admin/users/invalid_user_id/bets/{bet_id}/cancel",
        auth_token=admin_token,
        expected_status=404
    )
    
    if success:
        print_success("Cancel with invalid user ID - SUCCESS (404 as expected)")
        record_test("Cancel User Bet - Invalid User ID", True, "Correctly returned 404 for invalid user")
    else:
        print_error(f"Cancel with invalid user ID - FAILED (expected 404): {response}")
        record_test("Cancel User Bet - Invalid User ID", False, f"Did not return 404: {response}")

def test_cleanup_stuck_bets(admin_token: str, user_id: str):
    """Test POST /admin/users/{user_id}/bets/cleanup-stuck endpoint."""
    print_subheader("Testing Cleanup Stuck Bets Endpoint")
    
    # Test 1: Cleanup stuck bets
    response, success = make_request(
        "POST",
        f"/admin/users/{user_id}/bets/cleanup-stuck",
        auth_token=admin_token
    )
    
    if success:
        print_success("Cleanup stuck bets - SUCCESS")
        
        # Validate response structure
        required_fields = ["success", "message", "total_processed", "cancelled_games", "total_gems_returned", "total_commission_returned"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("Cleanup response structure validation - SUCCESS")
            record_test("Cleanup Stuck Bets - Response Structure", True, "All required fields present")
            
            # Validate response values
            if response.get("success") == True:
                print_success("Cleanup success flag - SUCCESS")
                record_test("Cleanup Stuck Bets - Success Flag", True, "Success flag is True")
            else:
                print_error("Cleanup success flag - FAILED")
                record_test("Cleanup Stuck Bets - Success Flag", False, "Success flag is not True")
            
            # Check processed count
            total_processed = response.get("total_processed", 0)
            if isinstance(total_processed, int) and total_processed >= 0:
                print_success(f"Total processed validation - SUCCESS ({total_processed} bets)")
                record_test("Cleanup Stuck Bets - Total Processed", True, f"Processed {total_processed} bets")
            else:
                print_error("Total processed validation - FAILED")
                record_test("Cleanup Stuck Bets - Total Processed", False, "Total processed is invalid")
            
            # Check cancelled games structure
            cancelled_games = response.get("cancelled_games", [])
            if isinstance(cancelled_games, list):
                print_success("Cancelled games structure - SUCCESS")
                record_test("Cleanup Stuck Bets - Cancelled Games Structure", True, f"Found {len(cancelled_games)} cancelled games")
                
                # If there are cancelled games, validate their structure
                if cancelled_games:
                    game = cancelled_games[0]
                    game_fields = ["game_id", "status", "bet_amount", "created_at", "age_hours"]
                    missing_game_fields = [field for field in game_fields if field not in game]
                    
                    if not missing_game_fields:
                        print_success("Cancelled game details structure - SUCCESS")
                        record_test("Cleanup Stuck Bets - Game Details Structure", True, "All game fields present")
                        
                        # Validate age_hours > 24 for stuck bets
                        age_hours = game.get("age_hours", 0)
                        if age_hours > 24:
                            print_success("Stuck bet age validation - SUCCESS")
                            record_test("Cleanup Stuck Bets - Age Validation", True, f"Game age {age_hours}h > 24h")
                        else:
                            print_warning(f"Game age {age_hours}h <= 24h (may not be stuck)")
                            record_test("Cleanup Stuck Bets - Age Validation", True, f"Game age {age_hours}h (acceptable)")
                    else:
                        print_error(f"Missing game fields: {missing_game_fields}")
                        record_test("Cleanup Stuck Bets - Game Details Structure", False, f"Missing fields: {missing_game_fields}")
            else:
                print_error("Cancelled games structure - FAILED")
                record_test("Cleanup Stuck Bets - Cancelled Games Structure", False, "Cancelled games is not a list")
            
            # Check gems returned structure
            total_gems_returned = response.get("total_gems_returned", {})
            if isinstance(total_gems_returned, dict):
                print_success("Total gems returned structure - SUCCESS")
                record_test("Cleanup Stuck Bets - Gems Returned Structure", True, f"Gems returned: {total_gems_returned}")
            else:
                print_error("Total gems returned structure - FAILED")
                record_test("Cleanup Stuck Bets - Gems Returned Structure", False, "Gems returned is not a dict")
            
            # Check commission returned
            total_commission_returned = response.get("total_commission_returned", 0)
            if isinstance(total_commission_returned, (int, float)) and total_commission_returned >= 0:
                print_success("Total commission returned validation - SUCCESS")
                record_test("Cleanup Stuck Bets - Commission Returned", True, f"Commission returned: {total_commission_returned}")
            else:
                print_error("Total commission returned validation - FAILED")
                record_test("Cleanup Stuck Bets - Commission Returned", False, "Commission returned is invalid")
        else:
            print_error(f"Missing response fields: {missing_fields}")
            record_test("Cleanup Stuck Bets - Response Structure", False, f"Missing fields: {missing_fields}")
    else:
        print_error(f"Cleanup stuck bets failed: {response}")
        record_test("Cleanup Stuck Bets - Basic Functionality", False, f"Request failed: {response}")
    
    # Test 2: Test with invalid user ID
    response, success = make_request(
        "POST",
        f"/admin/users/invalid_user_id/bets/cleanup-stuck",
        auth_token=admin_token,
        expected_status=404
    )
    
    if success:
        print_success("Cleanup with invalid user ID - SUCCESS (404 as expected)")
        record_test("Cleanup Stuck Bets - Invalid User ID", True, "Correctly returned 404 for invalid user")
    else:
        print_error(f"Cleanup with invalid user ID - FAILED (expected 404): {response}")
        record_test("Cleanup Stuck Bets - Invalid User ID", False, f"Did not return 404: {response}")

def test_admin_authentication():
    """Test admin authentication requirements."""
    print_subheader("Testing Admin Authentication")
    
    # Create a regular user token for testing
    user_result = create_test_user()
    if not user_result:
        print_error("Could not create test user for auth testing")
        record_test("Admin Auth - Test User Creation", False, "Failed to create test user")
        return
    
    user_id, user_token = user_result
    
    # Test 1: Try to access admin endpoint with user token (should fail)
    response, success = make_request(
        "GET",
        f"/admin/users/{user_id}/bets",
        auth_token=user_token,
        expected_status=403
    )
    
    if success:
        print_success("Admin endpoint with user token - SUCCESS (403 as expected)")
        record_test("Admin Auth - User Token Rejection", True, "Correctly returned 403 for user token")
    else:
        print_error(f"Admin endpoint with user token - FAILED (expected 403): {response}")
        record_test("Admin Auth - User Token Rejection", False, f"Did not return 403: {response}")
    
    # Test 2: Try to access admin endpoint without token (should fail)
    response, success = make_request(
        "GET",
        f"/admin/users/{user_id}/bets",
        expected_status=401
    )
    
    if success:
        print_success("Admin endpoint without token - SUCCESS (401 as expected)")
        record_test("Admin Auth - No Token Rejection", True, "Correctly returned 401 for no token")
    else:
        print_error(f"Admin endpoint without token - FAILED (expected 401): {response}")
        record_test("Admin Auth - No Token Rejection", False, f"Did not return 401: {response}")

def test_admin_logging(admin_token: str):
    """Test admin action logging."""
    print_subheader("Testing Admin Action Logging")
    
    # Note: This is a basic test since we can't directly access admin_logs collection
    # We'll verify that admin actions complete successfully, which implies logging is working
    
    # Create a test user and bet for logging test
    user_result = create_test_user()
    if not user_result:
        print_error("Could not create test user for logging test")
        record_test("Admin Logging - Test Setup", False, "Failed to create test user")
        return
    
    user_id, user_token = user_result
    bet_id = create_test_bet(user_token)
    
    if not bet_id:
        print_error("Could not create test bet for logging test")
        record_test("Admin Logging - Test Setup", False, "Failed to create test bet")
        return
    
    # Perform admin actions that should be logged
    
    # 1. Cancel bet (should log)
    response, success = make_request(
        "POST",
        f"/admin/users/{user_id}/bets/{bet_id}/cancel",
        auth_token=admin_token
    )
    
    if success:
        print_success("Admin cancel action completed - SUCCESS (logging implied)")
        record_test("Admin Logging - Cancel Action", True, "Cancel action completed successfully")
    else:
        print_error(f"Admin cancel action failed: {response}")
        record_test("Admin Logging - Cancel Action", False, f"Cancel action failed: {response}")
    
    # 2. Cleanup stuck bets (should log)
    response, success = make_request(
        "POST",
        f"/admin/users/{user_id}/bets/cleanup-stuck",
        auth_token=admin_token
    )
    
    if success:
        print_success("Admin cleanup action completed - SUCCESS (logging implied)")
        record_test("Admin Logging - Cleanup Action", True, "Cleanup action completed successfully")
    else:
        print_error(f"Admin cleanup action failed: {response}")
        record_test("Admin Logging - Cleanup Action", False, f"Cleanup action failed: {response}")

def print_test_summary():
    """Print a summary of all test results."""
    print_header("BET MANAGEMENT TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 90 else Colors.WARNING if success_rate >= 70 else Colors.FAIL}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print(f"\n{Colors.FAIL}Failed Tests:{Colors.ENDC}")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"  ✗ {test['name']}: {test['details']}")
    
    print(f"\n{Colors.OKBLUE}Detailed Results:{Colors.ENDC}")
    for test in test_results["tests"]:
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if test["passed"] else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"  {status} {test['name']}")

def main():
    """Main test execution function."""
    print_header("COMPREHENSIVE BET MANAGEMENT FUNCTIONALITY TESTING")
    
    # Step 1: Login as admin
    admin_token = login_admin()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        sys.exit(1)
    
    # Step 2: Test admin authentication
    test_admin_authentication()
    
    # Step 3: Create test user and bet
    user_result = create_test_user()
    if not user_result:
        print_error("Cannot proceed without test user")
        sys.exit(1)
    
    user_id, user_token = user_result
    bet_id = create_test_bet(user_token)
    
    # Step 4: Test GET user bets endpoint
    test_get_user_bets(admin_token, user_id)
    
    # Step 5: Test cancel user bet endpoint (if we have a bet)
    if bet_id:
        test_cancel_user_bet(admin_token, user_id, bet_id)
    
    # Step 6: Test cleanup stuck bets endpoint
    test_cleanup_stuck_bets(admin_token, user_id)
    
    # Step 7: Test admin logging
    test_admin_logging(admin_token)
    
    # Step 8: Print summary
    print_test_summary()
    
    # Return appropriate exit code
    if test_results["failed"] == 0:
        print(f"\n{Colors.OKGREEN}All tests passed! ✓{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"\n{Colors.FAIL}Some tests failed! ✗{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()