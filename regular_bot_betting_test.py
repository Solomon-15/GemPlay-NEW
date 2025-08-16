#!/usr/bin/env python3
"""
Regular Bot Betting Issue Testing - Russian Review
Focus: Testing the issue with regular bots creating bets

Key endpoints to test:
1. POST /api/admin/bots/start-regular - start regular bots for creating bets
2. GET /api/admin/bots - get list of regular bots 
3. GET /api/admin/dashboard/stats - check stats of active bets
4. GET /api/admin/games - check created games/bets

Tests to perform:
1. Check existing regular bots: Ensure there are active regular bots in system
2. Check limit settings: Check max_active_bets_regular settings
3. Test bet creation: Call start-regular endpoint and check result
4. Check created games: Ensure games are created in database with WAITING status
5. Error logging: Check logs for errors in bet creation process

Diagnostics:
- Check if there are active bots of type REGULAR
- Check if max_active_bets_regular limit is reached
- Check recreate_timer - maybe bots can't create bets due to timer
- Check creation_mode logic (always-first, queue-based, after-all)
- Check individual limits for each bot

Expected results:
- Should have active bots of type REGULAR 
- When calling start-regular should create new games
- Games should be saved in database with WAITING status
- Limits should not block bet creation
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
BASE_URL = "https://russian-commission.preview.emergentagent.com/api"
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

def test_admin_login() -> Optional[str]:
    """Test admin login and return access token."""
    print_subheader("Admin Authentication")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    # Use JSON data for UserLogin model
    login_response, login_success = make_request(
        "POST", "/auth/login",
        data=login_data
    )
    
    if not login_success:
        print_error("❌ Admin login failed")
        record_test("Admin Login", False, "Login request failed")
        return None
    
    # Check if we got access token
    access_token = login_response.get("access_token")
    if not access_token:
        print_error("❌ Admin login response missing access_token")
        record_test("Admin Login", False, "Missing access_token")
        return None
    
    print_success("✅ Admin login successful")
    print_success(f"✅ Access token received: {access_token[:20]}...")
    record_test("Admin Login", True)
    
    return access_token

def test_regular_bot_betting_issue():
    """Test the regular bot betting issue as described in the Russian review."""
    print_header("REGULAR BOT BETTING ISSUE TESTING")
    
    # Step 1: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        return
    
    # Step 2: Check existing regular bots
    print_subheader("Step 2: Check Existing Regular Bots")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_success:
        print_error("❌ Failed to get bots list")
        record_test("Get Regular Bots List", False, "Request failed")
        return
    
    # Check if we have regular bots
    regular_bots = []
    if "bots" in bots_response:
        all_bots = bots_response["bots"]
        regular_bots = [bot for bot in all_bots if bot.get("bot_type") == "REGULAR"]
    
    if not regular_bots:
        print_error("❌ No REGULAR bots found in system")
        record_test("Regular Bots Exist", False, "No regular bots found")
        return
    
    print_success(f"✅ Found {len(regular_bots)} REGULAR bots")
    record_test("Regular Bots Exist", True)
    
    # Display bot details
    for i, bot in enumerate(regular_bots[:5]):  # Show first 5 bots
        bot_name = bot.get("name", "Unknown")
        is_active = bot.get("is_active", False)
        min_bet = bot.get("min_bet_amount", 0)
        max_bet = bot.get("max_bet_amount", 0)
        cycle_games = bot.get("cycle_games", 0)
        current_cycle_games = bot.get("current_cycle_games", 0)
        individual_limit = bot.get("individual_limit", 0)
        
        print_success(f"  Bot {i+1}: {bot_name}")
        print_success(f"    Active: {is_active}")
        print_success(f"    Bet range: ${min_bet} - ${max_bet}")
        print_success(f"    Cycle games: {current_cycle_games}/{cycle_games}")
        print_success(f"    Individual limit: {individual_limit}")
    
    # Step 3: Check bot settings and limits
    print_subheader("Step 3: Check Bot Settings and Limits")
    
    # Try to get bot settings
    bot_settings_response, bot_settings_success = make_request(
        "GET", "/admin/bots/settings",
        auth_token=admin_token
    )
    
    if bot_settings_success:
        print_success("✅ Bot settings endpoint accessible")
        
        # Check for max_active_bets_regular setting
        if "max_active_bets_regular" in bot_settings_response:
            max_active_bets_regular = bot_settings_response["max_active_bets_regular"]
            print_success(f"✅ max_active_bets_regular: {max_active_bets_regular}")
            record_test("Bot Settings - max_active_bets_regular", True)
        else:
            print_warning("⚠ max_active_bets_regular setting not found")
            record_test("Bot Settings - max_active_bets_regular", False, "Setting not found")
        
        # Check other relevant settings
        relevant_settings = [
            "recreate_timer", "creation_mode", "global_bet_limit", 
            "pause_between_games", "max_concurrent_games"
        ]
        
        for setting in relevant_settings:
            if setting in bot_settings_response:
                value = bot_settings_response[setting]
                print_success(f"✅ {setting}: {value}")
            else:
                print_warning(f"⚠ {setting} setting not found")
    else:
        print_warning("⚠ Bot settings endpoint not accessible")
        record_test("Bot Settings Access", False, "Endpoint not accessible")
    
    # Step 4: Check dashboard stats for active bets
    print_subheader("Step 4: Check Dashboard Stats")
    
    dashboard_response, dashboard_success = make_request(
        "GET", "/admin/dashboard/stats",
        auth_token=admin_token
    )
    
    if dashboard_success:
        print_success("✅ Dashboard stats endpoint accessible")
        
        # Check relevant stats
        active_regular_bots = dashboard_response.get("active_regular_bots", 0)
        active_regular_bots_games = dashboard_response.get("active_regular_bots_games", 0)
        total_active_games = dashboard_response.get("total_active_games", 0)
        
        print_success(f"✅ Active regular bots: {active_regular_bots}")
        print_success(f"✅ Active regular bot games: {active_regular_bots_games}")
        print_success(f"✅ Total active games: {total_active_games}")
        
        record_test("Dashboard Stats Access", True)
    else:
        print_error("❌ Failed to get dashboard stats")
        record_test("Dashboard Stats Access", False, "Request failed")
    
    # Step 5: Test start-regular endpoint
    print_subheader("Step 5: Test Start-Regular Endpoint")
    
    # Get initial game count
    initial_games_response, initial_games_success = make_request(
        "GET", "/admin/games",
        auth_token=admin_token
    )
    
    initial_game_count = 0
    if initial_games_success and "games" in initial_games_response:
        initial_game_count = len(initial_games_response["games"])
    
    print_success(f"✅ Initial game count: {initial_game_count}")
    
    # Call start-regular endpoint
    start_regular_response, start_regular_success = make_request(
        "POST", "/admin/bots/start-regular",
        auth_token=admin_token
    )
    
    if start_regular_success:
        print_success("✅ start-regular endpoint accessible")
        print_success(f"✅ Response: {start_regular_response}")
        record_test("Start Regular Bots", True)
        
        # Check if response indicates success
        if "success" in start_regular_response:
            success_flag = start_regular_response["success"]
            if success_flag:
                print_success("✅ start-regular returned success=True")
            else:
                print_warning("⚠ start-regular returned success=False")
                if "message" in start_regular_response:
                    print_warning(f"⚠ Message: {start_regular_response['message']}")
        
        # Check for created games count
        if "created_games" in start_regular_response:
            created_games = start_regular_response["created_games"]
            print_success(f"✅ Created games: {created_games}")
            
            if created_games > 0:
                print_success("✅ Regular bots successfully created games")
                record_test("Regular Bots Create Games", True)
            else:
                print_warning("⚠ No games created by regular bots")
                record_test("Regular Bots Create Games", False, "No games created")
        
    else:
        print_error("❌ start-regular endpoint failed")
        print_error(f"❌ Response: {start_regular_response}")
        record_test("Start Regular Bots", False, f"Request failed: {start_regular_response}")
    
    # Step 6: Wait and check for new games
    print_subheader("Step 6: Check for New Games After Start-Regular")
    
    print("Waiting 10 seconds for bots to create games...")
    time.sleep(10)
    
    # Get updated game count
    updated_games_response, updated_games_success = make_request(
        "GET", "/admin/games",
        auth_token=admin_token
    )
    
    if updated_games_success and "games" in updated_games_response:
        updated_game_count = len(updated_games_response["games"])
        games_created = updated_game_count - initial_game_count
        
        print_success(f"✅ Updated game count: {updated_game_count}")
        print_success(f"✅ Games created: {games_created}")
        
        if games_created > 0:
            print_success("✅ New games were created after start-regular")
            record_test("Games Created After Start-Regular", True)
            
            # Check game statuses
            new_games = updated_games_response["games"][-games_created:] if games_created > 0 else []
            waiting_games = 0
            
            for game in new_games:
                game_status = game.get("status", "UNKNOWN")
                creator_type = game.get("creator_type", "unknown")
                bot_type = game.get("bot_type", "unknown")
                
                if game_status == "WAITING":
                    waiting_games += 1
                
                print_success(f"  Game: status={game_status}, creator_type={creator_type}, bot_type={bot_type}")
            
            if waiting_games > 0:
                print_success(f"✅ {waiting_games} games created with WAITING status")
                record_test("Games Created with WAITING Status", True)
            else:
                print_warning("⚠ No games created with WAITING status")
                record_test("Games Created with WAITING Status", False, "No WAITING games")
        else:
            print_warning("⚠ No new games created after start-regular")
            record_test("Games Created After Start-Regular", False, "No new games")
    else:
        print_error("❌ Failed to get updated games list")
        record_test("Games Created After Start-Regular", False, "Failed to get games")
    
    # Step 7: Check available games in lobby
    print_subheader("Step 7: Check Available Games in Lobby")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        total_available = len(available_games_response)
        regular_bot_games = [
            game for game in available_games_response 
            if game.get("creator_type") == "bot" and game.get("bot_type") == "REGULAR"
        ]
        
        print_success(f"✅ Total available games: {total_available}")
        print_success(f"✅ Regular bot games available: {len(regular_bot_games)}")
        
        if regular_bot_games:
            print_success("✅ Regular bot games are available in lobby")
            record_test("Regular Bot Games Available", True)
            
            # Show some examples
            for i, game in enumerate(regular_bot_games[:3]):  # Show first 3
                game_id = game.get("game_id", "unknown")
                bet_amount = game.get("bet_amount", 0)
                creator_id = game.get("creator_id", "unknown")
                
                print_success(f"  Game {i+1}: ID={game_id}, Bet=${bet_amount}, Creator={creator_id}")
        else:
            print_warning("⚠ No regular bot games available in lobby")
            record_test("Regular Bot Games Available", False, "No games available")
    else:
        print_error("❌ Failed to get available games")
        record_test("Regular Bot Games Available", False, "Request failed")
    
    # Step 8: Diagnostic checks
    print_subheader("Step 8: Diagnostic Checks")
    
    # Check individual bot limits
    print_success("Checking individual bot limits:")
    bots_at_limit = 0
    bots_below_limit = 0
    
    for bot in regular_bots:
        bot_name = bot.get("name", "Unknown")
        current_cycle_games = bot.get("current_cycle_games", 0)
        cycle_games = bot.get("cycle_games", 12)
        individual_limit = bot.get("individual_limit", cycle_games)
        
        if current_cycle_games >= individual_limit:
            bots_at_limit += 1
            print_warning(f"  ⚠ {bot_name}: At limit ({current_cycle_games}/{individual_limit})")
        else:
            bots_below_limit += 1
            print_success(f"  ✓ {bot_name}: Below limit ({current_cycle_games}/{individual_limit})")
    
    print_success(f"Bots at limit: {bots_at_limit}")
    print_success(f"Bots below limit: {bots_below_limit}")
    
    if bots_below_limit > 0:
        print_success("✅ Some bots are below their limits and should be able to create bets")
        record_test("Bots Below Limit Available", True)
    else:
        print_warning("⚠ All bots are at their limits")
        record_test("Bots Below Limit Available", False, "All bots at limit")
    
    # Check creation mode logic
    print_success("Checking creation mode logic:")
    for bot in regular_bots[:3]:  # Check first 3 bots
        bot_name = bot.get("name", "Unknown")
        creation_mode = bot.get("creation_mode", "unknown")
        priority_order = bot.get("priority_order", 50)
        pause_between_games = bot.get("pause_between_games", 5)
        last_game_time = bot.get("last_game_time")
        
        print_success(f"  {bot_name}:")
        print_success(f"    Creation mode: {creation_mode}")
        print_success(f"    Priority order: {priority_order}")
        print_success(f"    Pause between games: {pause_between_games}s")
        print_success(f"    Last game time: {last_game_time}")
    
    # Summary
    print_subheader("Regular Bot Betting Issue Test Summary")
    
    total_tests = test_results["total"]
    passed_tests = test_results["passed"]
    failed_tests = test_results["failed"]
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print_success(f"Testing completed: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if failed_tests > 0:
        print_error(f"❌ {failed_tests} tests failed:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"  - {test['name']}: {test['details']}")
    
    # Recommendations
    print_subheader("Recommendations")
    
    if bots_below_limit == 0:
        print_warning("⚠ ISSUE: All regular bots are at their individual limits")
        print_warning("  - Check individual_limit settings for each bot")
        print_warning("  - Consider increasing individual_limit values")
        print_warning("  - Check if cycle_games settings are appropriate")
    
    if "max_active_bets_regular" in locals() and max_active_bets_regular:
        current_active_games = dashboard_response.get("active_regular_bots_games", 0) if dashboard_success else 0
        if current_active_games >= max_active_bets_regular:
            print_warning("⚠ ISSUE: Global max_active_bets_regular limit reached")
            print_warning(f"  - Current active games: {current_active_games}")
            print_warning(f"  - Max allowed: {max_active_bets_regular}")
            print_warning("  - Consider increasing max_active_bets_regular setting")
    
    if not start_regular_success:
        print_warning("⚠ ISSUE: start-regular endpoint is not working")
        print_warning("  - Check if endpoint exists and is properly implemented")
        print_warning("  - Check server logs for errors")
        print_warning("  - Verify bot creation logic is functioning")

def print_final_summary():
    """Print final test summary."""
    print_header("FINAL TEST SUMMARY")
    
    total_tests = test_results["total"]
    passed_tests = test_results["passed"]
    failed_tests = test_results["failed"]
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print_success(f"Total tests run: {total_tests}")
    print_success(f"Tests passed: {passed_tests}")
    
    if failed_tests > 0:
        print_error(f"Tests failed: {failed_tests}")
        print_error(f"Success rate: {success_rate:.1f}%")
    else:
        print_success(f"Tests failed: {failed_tests}")
        print_success(f"Success rate: {success_rate:.1f}%")
    
    print_subheader("Detailed Results")
    for test in test_results["tests"]:
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        print(f"{status}: {test['name']}")
        if test["details"] and not test["passed"]:
            print(f"    Details: {test['details']}")

if __name__ == "__main__":
    try:
        test_regular_bot_betting_issue()
        print_final_summary()
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        sys.exit(1)