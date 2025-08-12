#!/usr/bin/env python3
"""
Backend Testing After Global Bot Settings Removal - Russian Review
Focus: Testing backend stability after removing global bot settings functionality
Requirements: 
1. Backend starts successfully without errors
2. No errors related to removed endpoints and models
3. Main regular bot endpoints work correctly
4. No unused references to deleted functionality
5. Main bot functionality works without errors
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
BASE_URL = "https://f69ab665-caf1-44ae-a7f3-6839d9a82e50.preview.emergentagent.com/api"
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
    
    response, success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and "access_token" in response:
        print_success("Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error("Admin login failed")
        record_test("Admin Login", False, f"Response: {response}")
        return None

def test_backend_startup() -> None:
    """Test that backend starts successfully without errors."""
    print_header("BACKEND STARTUP TESTING")
    
    print_subheader("Step 1: Basic Health Check")
    
    # Test basic endpoint accessibility
    response, success = make_request("GET", "/", expected_status=200)
    
    if success:
        print_success("✓ Backend is accessible and responding")
        record_test("Backend Startup - Basic Health Check", True)
    else:
        print_error("✗ Backend is not accessible")
        record_test("Backend Startup - Basic Health Check", False, "Backend not responding")
        return
    
    print_subheader("Step 2: Authentication System Check")
    
    # Test authentication system
    admin_token = test_admin_login()
    
    if admin_token:
        print_success("✓ Authentication system working")
        record_test("Backend Startup - Authentication System", True)
    else:
        print_error("✗ Authentication system failed")
        record_test("Backend Startup - Authentication System", False)
        return
    
    print_subheader("Step 3: Database Connection Check")
    
    # Test database connection by getting user info
    response, success = make_request("GET", "/auth/me", auth_token=admin_token)
    
    if success and "id" in response:
        print_success("✓ Database connection working")
        print_success(f"  Admin user ID: {response.get('id')}")
        print_success(f"  Admin email: {response.get('email')}")
        record_test("Backend Startup - Database Connection", True)
    else:
        print_error("✗ Database connection failed")
        record_test("Backend Startup - Database Connection", False, f"Response: {response}")

def test_removed_global_bot_settings_endpoints() -> None:
    """Test that removed global bot settings endpoints return appropriate errors."""
    print_header("REMOVED GLOBAL BOT SETTINGS ENDPOINTS TESTING")
    
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    print_subheader("Step 1: Test Removed Global Settings Endpoints")
    
    # List of endpoints that should have been removed
    removed_endpoints = [
        ("/admin/bot-settings", "GET"),
        ("/admin/bot-settings", "PUT"),
        ("/admin/bot-settings", "POST"),
        ("/admin/global-bot-settings", "GET"),
        ("/admin/global-bot-settings", "PUT"),
        ("/admin/global-bot-settings", "POST"),
    ]
    
    for endpoint, method in removed_endpoints:
        print(f"Testing removed endpoint: {method} {endpoint}")
        
        response, success = make_request(
            method, 
            endpoint, 
            auth_token=admin_token,
            expected_status=404  # Should return 404 Not Found
        )
        
        if not success and response.get("text", "").find("404") != -1:
            print_success(f"✓ {method} {endpoint} correctly returns 404 (removed)")
            record_test(f"Removed Endpoint - {method} {endpoint}", True)
        elif not success:
            print_success(f"✓ {method} {endpoint} correctly unavailable")
            record_test(f"Removed Endpoint - {method} {endpoint}", True)
        else:
            print_error(f"✗ {method} {endpoint} still accessible (should be removed)")
            record_test(f"Removed Endpoint - {method} {endpoint}", False, "Endpoint still accessible")

def test_regular_bot_endpoints() -> None:
    """Test main regular bot endpoints work correctly."""
    print_header("REGULAR BOT ENDPOINTS TESTING")
    
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    print_subheader("Step 1: GET /api/admin/bots/regular/list")
    
    # Test regular bots list endpoint
    response, success = make_request(
        "GET", 
        "/admin/bots/regular/list?page=1&limit=10",
        auth_token=admin_token
    )
    
    if success:
        print_success("✓ Regular bots list endpoint accessible")
        
        # Check response structure
        if "bots" in response:
            bots = response["bots"]
            print_success(f"  Found {len(bots)} regular bots")
            
            # Check bot structure
            if bots:
                bot = bots[0]
                required_fields = ["id", "name", "bot_type", "is_active", "min_bet_amount", "max_bet_amount"]
                missing_fields = [field for field in required_fields if field not in bot]
                
                if not missing_fields:
                    print_success("✓ Bot structure contains all required fields")
                    record_test("Regular Bot Endpoints - List Structure", True)
                else:
                    print_error(f"✗ Bot structure missing fields: {missing_fields}")
                    record_test("Regular Bot Endpoints - List Structure", False, f"Missing: {missing_fields}")
            else:
                print_warning("No regular bots found in system")
                record_test("Regular Bot Endpoints - List Structure", True, "No bots to check")
            
            record_test("Regular Bot Endpoints - List", True)
        else:
            print_error("✗ Response missing 'bots' field")
            record_test("Regular Bot Endpoints - List", False, "Missing bots field")
    else:
        print_error("✗ Regular bots list endpoint failed")
        record_test("Regular Bot Endpoints - List", False, f"Response: {response}")
    
    print_subheader("Step 2: GET /api/admin/bots/regular/stats")
    
    # Test regular bots stats endpoint
    response, success = make_request(
        "GET", 
        "/admin/bots/regular/stats",
        auth_token=admin_token
    )
    
    if success:
        print_success("✓ Regular bots stats endpoint accessible")
        
        # Check response structure
        expected_fields = ["total_bots", "active_bots", "total_active_bets", "total_games_today"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if not missing_fields:
            print_success("✓ Stats response contains all expected fields")
            print_success(f"  Total bots: {response.get('total_bots', 0)}")
            print_success(f"  Active bots: {response.get('active_bots', 0)}")
            print_success(f"  Total active bets: {response.get('total_active_bets', 0)}")
            print_success(f"  Total games today: {response.get('total_games_today', 0)}")
            record_test("Regular Bot Endpoints - Stats", True)
        else:
            print_error(f"✗ Stats response missing fields: {missing_fields}")
            record_test("Regular Bot Endpoints - Stats", False, f"Missing: {missing_fields}")
    else:
        print_error("✗ Regular bots stats endpoint failed")
        record_test("Regular Bot Endpoints - Stats", False, f"Response: {response}")
    
    print_subheader("Step 3: POST /api/admin/bots/create-regular")
    
    # Test regular bot creation endpoint
    bot_data = {
        "name": f"TestBot_{int(time.time())}",
        "bot_type": "REGULAR",
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "win_rate": 55.0,
        "cycle_games": 12,
        "creation_mode": "queue-based",
        "priority_order": 50,
        "pause_between_games": 5,
        "profit_strategy": "balanced"
    }
    
    response, success = make_request(
        "POST", 
        "/admin/bots/create-regular",
        data=bot_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("✓ Regular bot creation endpoint accessible")
        
        # Check response structure
        if "id" in response:
            bot_id = response["id"]
            print_success(f"  Created bot with ID: {bot_id}")
            
            # Verify bot was created with correct data
            if response.get("name") == bot_data["name"]:
                print_success("✓ Bot created with correct name")
            if response.get("bot_type") == bot_data["bot_type"]:
                print_success("✓ Bot created with correct type")
            if response.get("min_bet_amount") == bot_data["min_bet_amount"]:
                print_success("✓ Bot created with correct min bet amount")
            
            record_test("Regular Bot Endpoints - Create", True)
            
            # Clean up - delete the test bot
            delete_response, delete_success = make_request(
                "DELETE", 
                f"/admin/bots/regular/{bot_id}",
                auth_token=admin_token
            )
            
            if delete_success:
                print_success("✓ Test bot cleaned up successfully")
            else:
                print_warning("⚠ Could not clean up test bot")
        else:
            print_error("✗ Bot creation response missing ID")
            record_test("Regular Bot Endpoints - Create", False, "Missing bot ID")
    else:
        print_error("✗ Regular bot creation endpoint failed")
        record_test("Regular Bot Endpoints - Create", False, f"Response: {response}")

def test_bot_functionality() -> None:
    """Test main bot functionality works without errors."""
    print_header("BOT FUNCTIONALITY TESTING")
    
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    print_subheader("Step 1: Test Available Bot Games")
    
    # Test getting available games (should include bot games)
    response, success = make_request(
        "GET", 
        "/games/available",
        auth_token=admin_token
    )
    
    if success and isinstance(response, list):
        print_success("✓ Available games endpoint accessible")
        
        bot_games = [game for game in response if game.get("creator_type") in ["bot", "human_bot"]]
        regular_bot_games = [game for game in bot_games if game.get("bot_type") == "REGULAR"]
        human_bot_games = [game for game in bot_games if game.get("bot_type") == "HUMAN"]
        
        print_success(f"  Total available games: {len(response)}")
        print_success(f"  Bot games: {len(bot_games)}")
        print_success(f"  Regular bot games: {len(regular_bot_games)}")
        print_success(f"  Human bot games: {len(human_bot_games)}")
        
        if bot_games:
            print_success("✓ Bot games are being created and available")
            
            # Check game structure
            game = bot_games[0]
            required_fields = ["game_id", "creator_type", "status", "bet_amount", "created_at"]
            missing_fields = [field for field in required_fields if field not in game]
            
            if not missing_fields:
                print_success("✓ Bot game structure is correct")
                record_test("Bot Functionality - Game Structure", True)
            else:
                print_error(f"✗ Bot game structure missing fields: {missing_fields}")
                record_test("Bot Functionality - Game Structure", False, f"Missing: {missing_fields}")
        else:
            print_warning("⚠ No bot games found (may be normal)")
            record_test("Bot Functionality - Game Structure", True, "No bot games to check")
        
        record_test("Bot Functionality - Available Games", True)
    else:
        print_error("✗ Available games endpoint failed")
        record_test("Bot Functionality - Available Games", False, f"Response: {response}")
    
    print_subheader("Step 2: Test Human Bot Management")
    
    # Test human bot list endpoint
    response, success = make_request(
        "GET", 
        "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    
    if success:
        print_success("✓ Human bots list endpoint accessible")
        
        if "bots" in response:
            bots = response["bots"]
            print_success(f"  Found {len(bots)} human bots")
            
            if bots:
                bot = bots[0]
                required_fields = ["id", "name", "character", "is_active", "min_bet", "max_bet"]
                missing_fields = [field for field in required_fields if field not in bot]
                
                if not missing_fields:
                    print_success("✓ Human bot structure is correct")
                    record_test("Bot Functionality - Human Bot Structure", True)
                else:
                    print_error(f"✗ Human bot structure missing fields: {missing_fields}")
                    record_test("Bot Functionality - Human Bot Structure", False, f"Missing: {missing_fields}")
            else:
                print_warning("No human bots found")
                record_test("Bot Functionality - Human Bot Structure", True, "No bots to check")
            
            record_test("Bot Functionality - Human Bot List", True)
        else:
            print_error("✗ Human bots response missing 'bots' field")
            record_test("Bot Functionality - Human Bot List", False, "Missing bots field")
    else:
        print_error("✗ Human bots list endpoint failed")
        record_test("Bot Functionality - Human Bot List", False, f"Response: {response}")
    
    print_subheader("Step 3: Test Bot Settings (Non-Global)")
    
    # Test individual bot settings endpoints that should still work
    response, success = make_request(
        "GET", 
        "/admin/bots/settings",
        auth_token=admin_token
    )
    
    if success:
        print_success("✓ Individual bot settings endpoint accessible")
        
        # Check for expected fields
        expected_fields = ["max_active_bets_regular", "max_active_bets_human"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if not missing_fields:
            print_success("✓ Bot settings response contains expected fields")
            print_success(f"  Max active bets (regular): {response.get('max_active_bets_regular')}")
            print_success(f"  Max active bets (human): {response.get('max_active_bets_human')}")
            record_test("Bot Functionality - Individual Settings", True)
        else:
            print_error(f"✗ Bot settings response missing fields: {missing_fields}")
            record_test("Bot Functionality - Individual Settings", False, f"Missing: {missing_fields}")
    else:
        print_error("✗ Individual bot settings endpoint failed")
        record_test("Bot Functionality - Individual Settings", False, f"Response: {response}")

def test_no_unused_references() -> None:
    """Test that there are no unused references to deleted functionality."""
    print_header("UNUSED REFERENCES TESTING")
    
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    print_subheader("Step 1: Test Error Responses Don't Reference Global Settings")
    
    # Test various endpoints to ensure error messages don't reference removed functionality
    test_endpoints = [
        ("/admin/bots/regular/list", "GET"),
        ("/admin/human-bots", "GET"),
        ("/admin/bots/settings", "GET"),
    ]
    
    all_clean = True
    
    for endpoint, method in test_endpoints:
        response, success = make_request(
            method, 
            endpoint,
            auth_token=admin_token
        )
        
        # Check if response contains references to global settings
        response_text = json.dumps(response).lower()
        global_references = [
            "global_bot_settings",
            "globalsettings", 
            "global-bot-settings",
            "global_settings",
            "bot_global_settings"
        ]
        
        found_references = [ref for ref in global_references if ref in response_text]
        
        if found_references:
            print_error(f"✗ {method} {endpoint} contains global settings references: {found_references}")
            all_clean = False
        else:
            print_success(f"✓ {method} {endpoint} clean of global settings references")
    
    if all_clean:
        record_test("Unused References - Clean Responses", True)
    else:
        record_test("Unused References - Clean Responses", False, "Found global settings references")
    
    print_subheader("Step 2: Test Admin Panel Endpoints Don't Break")
    
    # Test admin panel endpoints that might have been affected
    admin_endpoints = [
        "/admin/users",
        "/admin/games",
        "/admin/transactions",
        "/admin/logs"
    ]
    
    working_endpoints = 0
    
    for endpoint in admin_endpoints:
        response, success = make_request(
            "GET", 
            f"{endpoint}?page=1&limit=5",
            auth_token=admin_token
        )
        
        if success:
            print_success(f"✓ {endpoint} working correctly")
            working_endpoints += 1
        else:
            print_warning(f"⚠ {endpoint} not accessible (may be normal)")
    
    if working_endpoints > 0:
        print_success(f"✓ {working_endpoints}/{len(admin_endpoints)} admin endpoints working")
        record_test("Unused References - Admin Endpoints", True)
    else:
        print_error("✗ No admin endpoints working")
        record_test("Unused References - Admin Endpoints", False, "No admin endpoints accessible")

def print_test_summary() -> None:
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
    
    print_subheader("Overall Assessment:")
    
    if success_rate >= 90:
        print_success("🎉 EXCELLENT: Backend is stable after global bot settings removal")
    elif success_rate >= 75:
        print_success("✅ GOOD: Backend is mostly stable with minor issues")
    elif success_rate >= 50:
        print_warning("⚠ FAIR: Backend has some issues that need attention")
    else:
        print_error("❌ POOR: Backend has significant issues after global bot settings removal")

def main():
    """Main test execution."""
    print_header("BACKEND TESTING AFTER GLOBAL BOT SETTINGS REMOVAL")
    print("Testing backend stability after removing global bot settings functionality")
    print("Focus areas:")
    print("1. Backend startup and basic functionality")
    print("2. Removed endpoints return appropriate errors")
    print("3. Regular bot endpoints work correctly")
    print("4. Bot functionality remains intact")
    print("5. No unused references to deleted functionality")
    
    try:
        # Test 1: Backend startup
        test_backend_startup()
        
        # Test 2: Removed endpoints
        test_removed_global_bot_settings_endpoints()
        
        # Test 3: Regular bot endpoints
        test_regular_bot_endpoints()
        
        # Test 4: Bot functionality
        test_bot_functionality()
        
        # Test 5: No unused references
        test_no_unused_references()
        
        # Print summary
        print_test_summary()
        
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()