#!/usr/bin/env python3
"""
Ongoing Battles Endpoint Testing - Russian Review
Focus: Testing the fixed endpoint /api/games/active-human-bots for "Ongoing Battles"
Requirements:
1. Test new endpoint /api/games/active-human-bots with USER and MODERATOR roles
2. Verify both roles get the same data
3. Check proper JSON structure with required fields
4. Test moderator access to admin endpoints (users, games) but NOT human-bots
5. Ensure endpoint returns active games with full information
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://opus-shop-next.preview.emergentagent.com/api"

# Test users
MODERATOR_USER = {
    "email": "moderator@test.com",
    "password": "TestMod123"
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

def test_login(email: str, password: str, role_name: str) -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {role_name} Login")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    # Use JSON data for login endpoint
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            response_data = response.json()
            access_token = response_data.get("access_token")
            user_info = response_data.get("user", {})
            user_role = user_info.get("role", "unknown")
            
            if access_token:
                print_success(f"{role_name} login successful")
                print_success(f"User role: {user_role}")
                print_success(f"Access token: {access_token[:20]}...")
                record_test(f"{role_name} Login", True)
                return access_token
            else:
                print_error(f"{role_name} login response missing access_token")
                record_test(f"{role_name} Login", False, "Missing access_token")
        except json.JSONDecodeError:
            print_error(f"{role_name} login response not valid JSON")
            record_test(f"{role_name} Login", False, "Invalid JSON response")
    else:
        print_error(f"{role_name} login failed with status {response.status_code}")
        try:
            error_data = response.json()
            print_error(f"Error details: {error_data}")
        except:
            print_error(f"Error text: {response.text}")
        record_test(f"{role_name} Login", False, f"Status: {response.status_code}")
    
    return None

def create_test_user(role: str = "USER") -> Optional[str]:
    """Create a test user and return access token."""
    print_subheader(f"Creating Test {role} User")
    
    # Generate unique user data (username max 15 chars)
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    user_data = {
        "username": f"t{role.lower()[:1]}{random_suffix}",  # Keep under 15 chars
        "email": f"test{role.lower()}_{random_suffix}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    # Register user
    register_response, register_success = make_request("POST", "/auth/register", data=user_data)
    
    if not register_success:
        print_error(f"Failed to register {role} user")
        record_test(f"Create {role} User - Registration", False, "Registration failed")
        return None
    
    user_id = register_response.get("user_id")
    verification_token = register_response.get("verification_token")
    
    if not user_id or not verification_token:
        print_error(f"{role} user registration missing required fields")
        record_test(f"Create {role} User - Registration", False, "Missing fields")
        return None
    
    print_success(f"{role} user registered with ID: {user_id}")
    
    # Verify email
    verify_response, verify_success = make_request("POST", "/auth/verify-email", data={"token": verification_token})
    
    if not verify_success:
        print_error(f"Failed to verify {role} user email")
        record_test(f"Create {role} User - Email Verification", False, "Verification failed")
        return None
    
    print_success(f"{role} user email verified")
    
    # If creating MODERATOR, need to update role via admin
    if role == "MODERATOR":
        # Login as admin to update user role
        admin_token = test_login("admin@gemplay.com", "Admin123!", "Admin")
        if admin_token:
            update_data = {"role": "MODERATOR"}
            update_response, update_success = make_request(
                "PUT", f"/admin/users/{user_id}",
                data=update_data,
                auth_token=admin_token
            )
            if update_success:
                print_success(f"User role updated to MODERATOR")
            else:
                print_error(f"Failed to update user role to MODERATOR")
                record_test(f"Create {role} User - Role Update", False, "Role update failed")
                return None
    
    # Login as the new user
    login_token = test_login(user_data["email"], user_data["password"], role)
    
    if login_token:
        record_test(f"Create {role} User", True)
        return login_token
    else:
        record_test(f"Create {role} User", False, "Login failed")
        return None

def test_ongoing_battles_endpoint():
    """Test the new /api/games/active-human-bots endpoint for Ongoing Battles."""
    print_header("ONGOING BATTLES ENDPOINT TESTING")
    
    # Step 1: Create test users
    print_subheader("Step 1: Create Test Users")
    
    # Create USER
    user_token = create_test_user("USER")
    if not user_token:
        print_error("Failed to create USER - cannot proceed")
        return
    
    # Try to login as existing MODERATOR
    print_subheader("Step 2: Login as MODERATOR")
    moderator_token = test_login(MODERATOR_USER["email"], MODERATOR_USER["password"], "MODERATOR")
    
    if not moderator_token:
        print_warning("MODERATOR login failed, creating new MODERATOR user")
        moderator_token = create_test_user("MODERATOR")
        if not moderator_token:
            print_error("Failed to create MODERATOR - cannot proceed")
            return
    
    # Step 3: Test /api/games/active-human-bots endpoint with USER
    print_subheader("Step 3: Test /api/games/active-human-bots with USER")
    
    user_response, user_success = make_request(
        "GET", "/games/active-human-bots",
        auth_token=user_token
    )
    
    if not user_success:
        print_error("USER failed to access /api/games/active-human-bots")
        record_test("Ongoing Battles - USER Access", False, "Access failed")
        return
    
    print_success("USER successfully accessed /api/games/active-human-bots")
    
    # Validate response structure
    if isinstance(user_response, list):
        user_games_count = len(user_response)
        print_success(f"USER received {user_games_count} active games")
        
        # Check structure of first game if available
        if user_games_count > 0:
            first_game = user_response[0]
            required_fields = ["id", "game_id", "creator_id", "opponent_id", "bet_amount", "status", "creator_info", "opponent_info"]
            missing_fields = [field for field in required_fields if field not in first_game]
            
            if not missing_fields:
                print_success("✓ Game structure contains all required fields")
                print_success(f"  - id: {first_game.get('id')}")
                print_success(f"  - game_id: {first_game.get('game_id')}")
                print_success(f"  - creator_id: {first_game.get('creator_id')}")
                print_success(f"  - opponent_id: {first_game.get('opponent_id')}")
                print_success(f"  - bet_amount: {first_game.get('bet_amount')}")
                print_success(f"  - status: {first_game.get('status')}")
                print_success(f"  - creator_info: {type(first_game.get('creator_info'))}")
                print_success(f"  - opponent_info: {type(first_game.get('opponent_info'))}")
                record_test("Ongoing Battles - USER Response Structure", True)
            else:
                print_error(f"✗ Game structure missing fields: {missing_fields}")
                record_test("Ongoing Battles - USER Response Structure", False, f"Missing: {missing_fields}")
            
            # Check that status is ACTIVE
            game_status = first_game.get("status")
            if game_status == "ACTIVE":
                print_success("✓ Game status is ACTIVE as expected")
                record_test("Ongoing Battles - USER Active Status", True)
            else:
                print_error(f"✗ Game status is {game_status}, expected ACTIVE")
                record_test("Ongoing Battles - USER Active Status", False, f"Status: {game_status}")
        
        record_test("Ongoing Battles - USER Access", True)
    else:
        print_error("USER response is not a list")
        record_test("Ongoing Battles - USER Access", False, "Invalid response format")
        return
    
    # Step 4: Test /api/games/active-human-bots endpoint with MODERATOR
    print_subheader("Step 4: Test /api/games/active-human-bots with MODERATOR")
    
    moderator_response, moderator_success = make_request(
        "GET", "/games/active-human-bots",
        auth_token=moderator_token
    )
    
    if not moderator_success:
        print_error("MODERATOR failed to access /api/games/active-human-bots")
        record_test("Ongoing Battles - MODERATOR Access", False, "Access failed")
        return
    
    print_success("MODERATOR successfully accessed /api/games/active-human-bots")
    
    # Validate response structure
    if isinstance(moderator_response, list):
        moderator_games_count = len(moderator_response)
        print_success(f"MODERATOR received {moderator_games_count} active games")
        
        # Check structure of first game if available
        if moderator_games_count > 0:
            first_game = moderator_response[0]
            required_fields = ["id", "game_id", "creator_id", "opponent_id", "bet_amount", "status", "creator_info", "opponent_info"]
            missing_fields = [field for field in required_fields if field not in first_game]
            
            if not missing_fields:
                print_success("✓ Game structure contains all required fields")
                record_test("Ongoing Battles - MODERATOR Response Structure", True)
            else:
                print_error(f"✗ Game structure missing fields: {missing_fields}")
                record_test("Ongoing Battles - MODERATOR Response Structure", False, f"Missing: {missing_fields}")
        
        record_test("Ongoing Battles - MODERATOR Access", True)
    else:
        print_error("MODERATOR response is not a list")
        record_test("Ongoing Battles - MODERATOR Access", False, "Invalid response format")
        return
    
    # Step 5: Compare data between USER and MODERATOR
    print_subheader("Step 5: Compare Data Between USER and MODERATOR")
    
    if user_games_count == moderator_games_count:
        print_success(f"✓ Both USER and MODERATOR received same number of games: {user_games_count}")
        record_test("Ongoing Battles - Same Data Count", True)
    else:
        print_error(f"✗ Different game counts - USER: {user_games_count}, MODERATOR: {moderator_games_count}")
        record_test("Ongoing Battles - Same Data Count", False, f"USER: {user_games_count}, MOD: {moderator_games_count}")
    
    # Compare first few games if available
    if user_games_count > 0 and moderator_games_count > 0:
        games_to_compare = min(3, user_games_count, moderator_games_count)
        identical_games = 0
        
        for i in range(games_to_compare):
            user_game = user_response[i]
            moderator_game = moderator_response[i]
            
            # Compare key fields
            user_game_id = user_game.get("game_id")
            moderator_game_id = moderator_game.get("game_id")
            
            if user_game_id == moderator_game_id:
                identical_games += 1
                print_success(f"✓ Game {i+1} identical: {user_game_id}")
            else:
                print_error(f"✗ Game {i+1} different - USER: {user_game_id}, MOD: {moderator_game_id}")
        
        if identical_games == games_to_compare:
            print_success("✓ All compared games are identical")
            record_test("Ongoing Battles - Same Data Content", True)
        else:
            print_error(f"✗ Only {identical_games}/{games_to_compare} games are identical")
            record_test("Ongoing Battles - Same Data Content", False, f"Only {identical_games}/{games_to_compare} identical")
    
    # Step 6: Test MODERATOR access to admin endpoints
    print_subheader("Step 6: Test MODERATOR Admin Access")
    
    # Test access to /api/admin/users (should work)
    users_response, users_success = make_request(
        "GET", "/admin/users",
        auth_token=moderator_token
    )
    
    if users_success:
        print_success("✓ MODERATOR can access /api/admin/users")
        users_count = users_response.get("total", 0)
        print_success(f"  Found {users_count} users")
        record_test("Ongoing Battles - MODERATOR Admin Users Access", True)
    else:
        print_error("✗ MODERATOR cannot access /api/admin/users")
        record_test("Ongoing Battles - MODERATOR Admin Users Access", False, "Access denied")
    
    # Test access to /api/admin/games (should work)
    games_response, games_success = make_request(
        "GET", "/admin/games",
        auth_token=moderator_token
    )
    
    if games_success:
        print_success("✓ MODERATOR can access /api/admin/games")
        games_count = games_response.get("total", 0) if isinstance(games_response, dict) else len(games_response)
        print_success(f"  Found {games_count} games")
        record_test("Ongoing Battles - MODERATOR Admin Games Access", True)
    else:
        print_error("✗ MODERATOR cannot access /api/admin/games")
        record_test("Ongoing Battles - MODERATOR Admin Games Access", False, "Access denied")
    
    # Test access to /api/admin/human-bots (should NOT work)
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots",
        auth_token=moderator_token,
        expected_status=403  # Expect forbidden
    )
    
    if not human_bots_success:
        print_success("✓ MODERATOR correctly denied access to /api/admin/human-bots")
        record_test("Ongoing Battles - MODERATOR Human-bots Access Denied", True)
    else:
        print_error("✗ MODERATOR incorrectly granted access to /api/admin/human-bots")
        record_test("Ongoing Battles - MODERATOR Human-bots Access Denied", False, "Access granted")
    
    # Step 7: Verify minimum game count expectation
    print_subheader("Step 7: Verify Game Count Expectation")
    
    if user_games_count >= 10:
        print_success(f"✓ Endpoint returns {user_games_count} active games (≥10 expected)")
        record_test("Ongoing Battles - Minimum Game Count", True)
    else:
        print_warning(f"⚠ Endpoint returns {user_games_count} active games (<10 expected)")
        record_test("Ongoing Battles - Minimum Game Count", False, f"Only {user_games_count} games")
    
    # Step 8: Test endpoint performance
    print_subheader("Step 8: Test Endpoint Performance")
    
    start_time = time.time()
    perf_response, perf_success = make_request(
        "GET", "/games/active-human-bots",
        auth_token=user_token
    )
    end_time = time.time()
    
    response_time = end_time - start_time
    
    if perf_success and response_time < 5.0:  # Should respond within 5 seconds
        print_success(f"✓ Endpoint responds in {response_time:.2f} seconds")
        record_test("Ongoing Battles - Performance", True)
    else:
        print_warning(f"⚠ Endpoint responds in {response_time:.2f} seconds (>5s)")
        record_test("Ongoing Battles - Performance", False, f"Response time: {response_time:.2f}s")

def print_test_summary():
    """Print test summary."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    print_success(f"Total tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success(f"Failed: {failed}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print_success(f"Success rate: {success_rate:.1f}%")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"✗ {test['name']}: {test['details']}")

if __name__ == "__main__":
    try:
        test_ongoing_battles_endpoint()
        print_test_summary()
        
        # Exit with appropriate code
        if test_results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        sys.exit(1)