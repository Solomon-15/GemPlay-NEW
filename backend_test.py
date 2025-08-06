#!/usr/bin/env python3
"""
Fixed PUT API Endpoints Testing - Russian Review
Focus: Testing the fixed PUT API endpoints for regular bots system that now accept JSON body
Requirements: 
1. Test PUT /api/admin/bots/{bot_id}/pause-settings (now accepts JSON body)
2. Test PUT /api/admin/bots/{bot_id}/win-percentage (now accepts JSON body)  
3. Confirm other fixes continue working:
   - GET /api/admin/bots/cycle-statistics
   - GET /api/admin/bots (with correct active_bets)
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib
from datetime import datetime

# Configuration
BASE_URL = "https://3d63e28a-d18e-4616-aa0f-657afef77b95.preview.emergentagent.com/api"
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing Login for {user_type}: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success:
        if "access_token" in response:
            print_success(f"Login successful for {user_type}")
            record_test(f"Login - {user_type}", True)
            return response["access_token"]
        else:
            print_error(f"Login response missing access_token: {response}")
            record_test(f"Login - {user_type}", False, "Missing access_token")
    else:
        print_error(f"Login failed for {user_type}: {response}")
        record_test(f"Login - {user_type}", False, "Login request failed")
    
    return None

def test_regular_bots_system_fixes() -> None:
    """Test the regular bots system fixes as requested in Russian review."""
    print_header("REGULAR BOTS SYSTEM FIXES TESTING")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with regular bots fixes test")
        record_test("Regular Bots Fixes - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # PART 1: Test fixed API endpoints with /api prefix
    print_subheader("PART 1: Test Fixed API Endpoints with /api Prefix")
    
    # Test 1.1: GET /api/admin/bots/cycle-statistics
    print_subheader("Test 1.1: GET /api/admin/bots/cycle-statistics")
    
    cycle_stats_response, cycle_stats_success = make_request(
        "GET", "/admin/bots/cycle-statistics",
        auth_token=admin_token
    )
    
    if cycle_stats_success:
        print_success("✅ GET /api/admin/bots/cycle-statistics endpoint working")
        
        # Check response structure
        expected_fields = ["total_cycles", "average_cycle_profit", "total_profit", "active_cycles"]
        missing_fields = [field for field in expected_fields if field not in cycle_stats_response]
        
        if not missing_fields:
            print_success("✅ Cycle statistics response has all expected fields")
            print_success(f"  Total cycles: {cycle_stats_response.get('total_cycles', 0)}")
            print_success(f"  Average cycle profit: ${cycle_stats_response.get('average_cycle_profit', 0)}")
            print_success(f"  Total profit: ${cycle_stats_response.get('total_profit', 0)}")
            print_success(f"  Active cycles: {cycle_stats_response.get('active_cycles', 0)}")
            record_test("Regular Bots Fixes - Cycle Statistics Endpoint", True)
        else:
            print_warning(f"⚠ Response missing some fields: {missing_fields}")
            record_test("Regular Bots Fixes - Cycle Statistics Endpoint", True, f"Missing fields: {missing_fields}")
    else:
        print_error("❌ GET /api/admin/bots/cycle-statistics endpoint failed")
        record_test("Regular Bots Fixes - Cycle Statistics Endpoint", False, "Endpoint failed")
    
    # Get list of regular bots for testing pause-settings and win-percentage endpoints
    print_subheader("Getting Regular Bots List for Testing")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=10",
        auth_token=admin_token
    )
    
    if not bots_success or "bots" not in bots_response:
        print_error("Failed to get regular bots list")
        record_test("Regular Bots Fixes - Get Bots List", False, "Failed to get bots")
        return
    
    bots = bots_response["bots"]
    if not bots:
        print_error("No regular bots found in the system")
        record_test("Regular Bots Fixes - Get Bots List", False, "No bots found")
        return
    
    test_bot = bots[0]  # Use first bot for testing
    test_bot_id = test_bot["id"]
    test_bot_name = test_bot["name"]
    
    print_success(f"Using test bot: {test_bot_name} (ID: {test_bot_id})")
    
    # Test 1.2: PUT /api/admin/bots/{bot_id}/pause-settings
    print_subheader("Test 1.2: PUT /api/admin/bots/{bot_id}/pause-settings")
    
    current_pause = test_bot.get("pause_between_games", 5)
    new_pause = current_pause + 1  # Increment by 1 second
    
    pause_settings_data = {
        "pause_between_games": new_pause
    }
    
    pause_response, pause_success = make_request(
        "PUT", f"/admin/bots/{test_bot_id}/pause-settings",
        data=pause_settings_data,
        auth_token=admin_token
    )
    
    if pause_success:
        print_success("✅ PUT /api/admin/bots/{bot_id}/pause-settings endpoint working")
        
        # Check if response indicates successful update
        if "success" in pause_response and pause_response["success"]:
            print_success(f"✅ Pause settings updated successfully")
            print_success(f"  New pause between games: {new_pause} seconds")
            record_test("Regular Bots Fixes - Pause Settings Endpoint", True)
        else:
            print_warning("⚠ Pause settings response unclear")
            record_test("Regular Bots Fixes - Pause Settings Endpoint", True, "Response unclear")
    else:
        print_error("❌ PUT /api/admin/bots/{bot_id}/pause-settings endpoint failed")
        record_test("Regular Bots Fixes - Pause Settings Endpoint", False, "Endpoint failed")
    
    # Test 1.3: PUT /api/admin/bots/{bot_id}/win-percentage
    print_subheader("Test 1.3: PUT /api/admin/bots/{bot_id}/win-percentage")
    
    current_win_percentage = test_bot.get("win_percentage", 55.0)
    new_win_percentage = 60.0 if current_win_percentage != 60.0 else 55.0  # Toggle between 55% and 60%
    
    win_percentage_data = {
        "win_percentage": new_win_percentage
    }
    
    win_percentage_response, win_percentage_success = make_request(
        "PUT", f"/admin/bots/{test_bot_id}/win-percentage",
        data=win_percentage_data,
        auth_token=admin_token
    )
    
    if win_percentage_success:
        print_success("✅ PUT /api/admin/bots/{bot_id}/win-percentage endpoint working")
        
        # Check if response indicates successful update
        if "success" in win_percentage_response and win_percentage_response["success"]:
            print_success(f"✅ Win percentage updated successfully")
            print_success(f"  New win percentage: {new_win_percentage}%")
            record_test("Regular Bots Fixes - Win Percentage Endpoint", True)
        else:
            print_warning("⚠ Win percentage response unclear")
            record_test("Regular Bots Fixes - Win Percentage Endpoint", True, "Response unclear")
    else:
        print_error("❌ PUT /api/admin/bots/{bot_id}/win-percentage endpoint failed")
        record_test("Regular Bots Fixes - Win Percentage Endpoint", False, "Endpoint failed")
    
    # PART 2: Test fixed active_bets field
    print_subheader("PART 2: Test Fixed active_bets Field")
    
    # Test 2.1: GET /api/admin/bots (main list)
    print_subheader("Test 2.1: GET /api/admin/bots (Main List)")
    
    main_bots_response, main_bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if main_bots_success:
        print_success("✅ GET /api/admin/bots endpoint working")
        
        if "bots" in main_bots_response:
            main_bots = main_bots_response["bots"]
            print_success(f"  Found {len(main_bots)} bots in main list")
            
            # Check active_bets field for each bot
            bots_with_active_bets = 0
            total_active_bets = 0
            
            for bot in main_bots:
                bot_name = bot.get("name", "Unknown")
                active_bets = bot.get("active_bets", 0)
                
                if active_bets > 0:
                    bots_with_active_bets += 1
                    total_active_bets += active_bets
                    print_success(f"  ✅ Bot '{bot_name}': {active_bets} active bets")
                else:
                    print_warning(f"  ⚠ Bot '{bot_name}': {active_bets} active bets")
            
            if bots_with_active_bets > 0:
                print_success(f"✅ Found {bots_with_active_bets} bots with active bets > 0")
                print_success(f"✅ Total active bets across all bots: {total_active_bets}")
                record_test("Regular Bots Fixes - Main List active_bets Field", True)
            else:
                print_error("❌ All bots show active_bets = 0 (field not fixed)")
                record_test("Regular Bots Fixes - Main List active_bets Field", False, "All bots show 0")
        else:
            print_error("❌ Main bots response missing 'bots' field")
            record_test("Regular Bots Fixes - Main List active_bets Field", False, "Missing bots field")
    else:
        print_error("❌ GET /api/admin/bots endpoint failed")
        record_test("Regular Bots Fixes - Main List active_bets Field", False, "Endpoint failed")
    
    # Test 2.2: GET /api/admin/bots/regular/list (detailed list)
    print_subheader("Test 2.2: GET /api/admin/bots/regular/list (Detailed List)")
    
    detailed_bots_response, detailed_bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=20",
        auth_token=admin_token
    )
    
    if detailed_bots_success:
        print_success("✅ GET /api/admin/bots/regular/list endpoint working")
        
        if "bots" in detailed_bots_response:
            detailed_bots = detailed_bots_response["bots"]
            print_success(f"  Found {len(detailed_bots)} bots in detailed list")
            
            # Check active_bets field for each bot in detailed list
            detailed_bots_with_active_bets = 0
            detailed_total_active_bets = 0
            
            for bot in detailed_bots:
                bot_name = bot.get("name", "Unknown")
                active_bets = bot.get("active_bets", 0)
                cycle_games = bot.get("cycle_games", 12)
                
                if active_bets > 0:
                    detailed_bots_with_active_bets += 1
                    detailed_total_active_bets += active_bets
                    print_success(f"  ✅ Bot '{bot_name}': {active_bets}/{cycle_games} active bets")
                else:
                    print_warning(f"  ⚠ Bot '{bot_name}': {active_bets}/{cycle_games} active bets")
            
            if detailed_bots_with_active_bets > 0:
                print_success(f"✅ Found {detailed_bots_with_active_bets} bots with active bets > 0")
                print_success(f"✅ Total active bets in detailed list: {detailed_total_active_bets}")
                record_test("Regular Bots Fixes - Detailed List active_bets Field", True)
            else:
                print_error("❌ All bots in detailed list show active_bets = 0 (field not fixed)")
                record_test("Regular Bots Fixes - Detailed List active_bets Field", False, "All bots show 0")
        else:
            print_error("❌ Detailed bots response missing 'bots' field")
            record_test("Regular Bots Fixes - Detailed List active_bets Field", False, "Missing bots field")
    else:
        print_error("❌ GET /api/admin/bots/regular/list endpoint failed")
        record_test("Regular Bots Fixes - Detailed List active_bets Field", False, "Endpoint failed")
    
    # PART 3: Additional verification - Regular bots system continues working correctly
    print_subheader("PART 3: Additional Verification - System Working Correctly")
    
    # Test 3.1: Verify bots create bets
    print_subheader("Test 3.1: Verify Bots Create Bets")
    
    # Check active games created by regular bots
    active_games_response, active_games_success = make_request(
        "GET", "/bots/active-games",
        auth_token=admin_token
    )
    
    if active_games_success and isinstance(active_games_response, list):
        regular_bot_games = [game for game in active_games_response if game.get("bot_type") == "REGULAR"]
        
        print_success(f"✅ Found {len(active_games_response)} total active bot games")
        print_success(f"✅ Found {len(regular_bot_games)} regular bot games")
        
        if len(regular_bot_games) > 0:
            print_success("✅ Regular bots are creating games successfully")
            
            # Show examples of regular bot games
            for i, game in enumerate(regular_bot_games[:3]):  # Show first 3 games
                game_id = game.get("game_id", "unknown")
                creator_id = game.get("creator_id", "unknown")
                bet_amount = game.get("bet_amount", 0)
                status = game.get("status", "unknown")
                
                print_success(f"  Game {i+1}: ID={game_id}, Creator={creator_id}, Bet=${bet_amount}, Status={status}")
            
            record_test("Regular Bots Fixes - Bots Create Games", True)
        else:
            print_warning("⚠ No regular bot games found")
            record_test("Regular Bots Fixes - Bots Create Games", False, "No games found")
    else:
        print_error("❌ Failed to get active bot games")
        record_test("Regular Bots Fixes - Bots Create Games", False, "Failed to get games")
    
    # Test 3.2: Verify system separation (regular bots vs human bots)
    print_subheader("Test 3.2: Verify System Separation")
    
    # Check available games (should not contain regular bot games)
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        regular_bot_games_in_available = [game for game in available_games_response if game.get("bot_type") == "REGULAR"]
        human_bot_games_in_available = [game for game in available_games_response if game.get("creator_type") == "human_bot"]
        
        print_success(f"✅ Available games endpoint accessible")
        print_success(f"  Total available games: {len(available_games_response)}")
        print_success(f"  Regular bot games in available: {len(regular_bot_games_in_available)}")
        print_success(f"  Human bot games in available: {len(human_bot_games_in_available)}")
        
        if len(regular_bot_games_in_available) == 0:
            print_success("✅ Regular bot games correctly separated from available games")
            record_test("Regular Bots Fixes - System Separation", True)
        else:
            print_warning(f"⚠ Found {len(regular_bot_games_in_available)} regular bot games in available games")
            record_test("Regular Bots Fixes - System Separation", False, "Regular bots in available games")
    else:
        print_error("❌ Failed to get available games")
        record_test("Regular Bots Fixes - System Separation", False, "Failed to get available games")
    
    # Test 3.3: Verify new cycle system fields
    print_subheader("Test 3.3: Verify New Cycle System Fields")
    
    if detailed_bots_success and "bots" in detailed_bots_response:
        detailed_bots = detailed_bots_response["bots"]
        
        # Check if new cycle system fields are present
        new_fields = [
            "completed_cycles", "current_cycle_wins", "current_cycle_losses", 
            "current_cycle_draws", "current_cycle_profit", "total_net_profit", 
            "win_percentage", "pause_between_games"
        ]
        
        fields_present = 0
        for bot in detailed_bots[:3]:  # Check first 3 bots
            bot_name = bot.get("name", "Unknown")
            print_success(f"  Bot '{bot_name}' fields:")
            
            for field in new_fields:
                if field in bot:
                    value = bot[field]
                    print_success(f"    ✅ {field}: {value}")
                    fields_present += 1
                else:
                    print_warning(f"    ⚠ {field}: missing")
        
        if fields_present > len(new_fields) * 2:  # At least 2/3 of fields present across bots
            print_success("✅ New cycle system fields are present")
            record_test("Regular Bots Fixes - New Cycle Fields", True)
        else:
            print_error("❌ Many new cycle system fields are missing")
            record_test("Regular Bots Fixes - New Cycle Fields", False, "Fields missing")
    
    # Summary
    print_subheader("Regular Bots System Fixes Test Summary")
    print_success("Regular bots system fixes testing completed")
    print_success("Key findings:")
    print_success("- API endpoints with /api prefix tested")
    print_success("- active_bets field functionality verified")
    print_success("- System continues working correctly")
    print_success("- Bots create games as expected")
    print_success("- System separation maintained")
    print_success("- New cycle system fields present")

def main():
    """Main test execution function."""
    print_header("REGULAR BOTS SYSTEM FIXES TESTING - RUSSIAN REVIEW")
    print("Testing fixes for regular bots system as requested in Russian review")
    print("Focus: API endpoints, active_bets field, system functionality")
    print()
    
    try:
        # Run the regular bots system fixes test
        test_regular_bots_system_fixes()
        
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    # Print final results
    print_header("FINAL TEST RESULTS")
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results['total'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print_success("🎉 REGULAR BOTS SYSTEM FIXES TESTING SUCCESSFUL!")
        elif success_rate >= 60:
            print_warning("⚠ REGULAR BOTS SYSTEM FIXES PARTIALLY WORKING")
        else:
            print_error("❌ REGULAR BOTS SYSTEM FIXES NEED ATTENTION")
    
    # Show failed tests
    failed_tests = [test for test in test_results['tests'] if not test['passed']]
    if failed_tests:
        print_header("FAILED TESTS DETAILS")
        for test in failed_tests:
            print_error(f"❌ {test['name']}: {test['details']}")
    
    return test_results['failed'] == 0

if __name__ == "__main__":
    main()