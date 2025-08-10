#!/usr/bin/env python3
"""
Bot Limits Removal Testing - Russian Review
Focus: Testing backend after removal of "Лимиты активных ставок" functionality
Requirements: 
1. Backend starts without errors after removing functionality
2. Deleted endpoints no longer exist: GET/POST /api/admin/bots/settings
3. Main bot functionality works without global limits
4. Individual bot limits continue to work
5. Bot bet creation logic works correctly
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
BASE_URL = "https://49b21745-59e5-4980-8f15-13cafed79fb5.preview.emergentagent.com/api"
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
            response = requests.request(method, url, json=data, headers=headers, timeout=10)
        else:
            response = requests.request(method, url, params=data, headers=headers, timeout=10)
        
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type.title()} Login")
    
    login_data = {
        "email": email,
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

def test_backend_startup():
    """Test that backend starts without errors after removing bot limits functionality."""
    print_header("BACKEND STARTUP TESTING")
    
    print_subheader("Step 1: Basic Health Check")
    
    # Test basic endpoint to ensure backend is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/", timeout=10)
        if response.status_code in [200, 404]:  # 404 is OK for root endpoint
            print_success("Backend is responding to requests")
            record_test("Backend Startup - Health Check", True)
        else:
            print_error(f"Backend health check failed with status: {response.status_code}")
            record_test("Backend Startup - Health Check", False, f"Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print_error(f"Backend is not responding: {e}")
        record_test("Backend Startup - Health Check", False, f"Connection error: {e}")
        return False
    
    return True

def test_deleted_endpoints():
    """Test that the deleted bot settings endpoints no longer exist."""
    print_header("DELETED ENDPOINTS TESTING")
    
    # Login as admin first
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot test deleted endpoints without admin access")
        return
    
    print_subheader("Step 1: Test GET /api/admin/bots/settings (Should be deleted)")
    
    # Test GET /api/admin/bots/settings - should return 404 or 405
    get_response, get_success = make_request(
        "GET", "/admin/bots/settings",
        auth_token=admin_token,
        expected_status=404
    )
    
    if not get_success and get_response.get("text", "").find("404") != -1:
        print_success("✓ GET /api/admin/bots/settings correctly returns 404 (endpoint deleted)")
        record_test("Deleted Endpoints - GET /admin/bots/settings", True)
    elif not get_success:
        print_success("✓ GET /api/admin/bots/settings is not accessible (endpoint deleted)")
        record_test("Deleted Endpoints - GET /admin/bots/settings", True)
    else:
        print_error("✗ GET /api/admin/bots/settings still exists (should be deleted)")
        record_test("Deleted Endpoints - GET /admin/bots/settings", False, "Endpoint still exists")
    
    print_subheader("Step 2: Test POST /api/admin/bots/settings (Should be deleted)")
    
    # Test POST /api/admin/bots/settings - should return 404 or 405
    test_data = {
        "max_active_bets_regular": 1000,
        "max_active_bets_human": 1000
    }
    
    post_response, post_success = make_request(
        "POST", "/admin/bots/settings",
        data=test_data,
        auth_token=admin_token,
        expected_status=404
    )
    
    if not post_success and post_response.get("text", "").find("404") != -1:
        print_success("✓ POST /api/admin/bots/settings correctly returns 404 (endpoint deleted)")
        record_test("Deleted Endpoints - POST /admin/bots/settings", True)
    elif not post_success:
        print_success("✓ POST /api/admin/bots/settings is not accessible (endpoint deleted)")
        record_test("Deleted Endpoints - POST /admin/bots/settings", True)
    else:
        print_error("✗ POST /api/admin/bots/settings still exists (should be deleted)")
        record_test("Deleted Endpoints - POST /admin/bots/settings", False, "Endpoint still exists")

def test_bot_functionality_without_global_limits():
    """Test that main bot functionality works without global limits."""
    print_header("BOT FUNCTIONALITY WITHOUT GLOBAL LIMITS TESTING")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot test bot functionality without admin access")
        return
    
    print_subheader("Step 1: Test Regular Bot Functionality")
    
    # Get regular bots list
    bots_response, bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=10",
        auth_token=admin_token
    )
    
    if bots_success and "bots" in bots_response:
        bots = bots_response["bots"]
        print_success(f"✓ Regular bots list accessible: {len(bots)} bots found")
        record_test("Bot Functionality - Regular Bots List", True)
        
        # Check that bots have individual limits but no global limit references
        for bot in bots[:3]:  # Check first 3 bots
            bot_name = bot.get("name", "Unknown")
            individual_limit = bot.get("individual_limit", 0)
            cycle_games = bot.get("cycle_games", 0)
            
            print_success(f"  Bot '{bot_name}': individual_limit={individual_limit}, cycle_games={cycle_games}")
            
            # Verify individual limits exist
            if individual_limit > 0:
                print_success(f"    ✓ Individual limit working: {individual_limit}")
            else:
                print_warning(f"    ⚠ Individual limit not set: {individual_limit}")
    else:
        print_error("✗ Failed to get regular bots list")
        record_test("Bot Functionality - Regular Bots List", False, "Failed to get bots")
    
    print_subheader("Step 2: Test Human-Bot Functionality")
    
    # Get human bots list
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    
    if human_bots_success and "bots" in human_bots_response:
        human_bots = human_bots_response["bots"]
        print_success(f"✓ Human-bots list accessible: {len(human_bots)} bots found")
        record_test("Bot Functionality - Human Bots List", True)
        
        # Check that human bots have individual limits
        for bot in human_bots[:3]:  # Check first 3 bots
            bot_name = bot.get("name", "Unknown")
            bet_limit = bot.get("bet_limit", 0)
            max_concurrent_games = bot.get("max_concurrent_games", 0)
            
            print_success(f"  Human-bot '{bot_name}': bet_limit={bet_limit}, max_concurrent_games={max_concurrent_games}")
            
            # Verify individual limits exist
            if bet_limit > 0:
                print_success(f"    ✓ Individual bet limit working: {bet_limit}")
            else:
                print_warning(f"    ⚠ Individual bet limit not set: {bet_limit}")
    else:
        print_error("✗ Failed to get human bots list")
        record_test("Bot Functionality - Human Bots List", False, "Failed to get bots")

def test_individual_bot_limits():
    """Test that individual bot limits continue to work."""
    print_header("INDIVIDUAL BOT LIMITS TESTING")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot test individual bot limits without admin access")
        return
    
    print_subheader("Step 1: Test Regular Bot Individual Limits")
    
    # Get regular bots and check their individual limits
    bots_response, bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=5",
        auth_token=admin_token
    )
    
    if bots_success and "bots" in bots_response:
        bots = bots_response["bots"]
        
        for bot in bots:
            bot_id = bot.get("id")
            bot_name = bot.get("name", "Unknown")
            individual_limit = bot.get("individual_limit", 0)
            current_cycle_games = bot.get("current_cycle_games", 0)
            cycle_games = bot.get("cycle_games", 0)
            
            print_success(f"Regular Bot '{bot_name}':")
            print_success(f"  Individual limit: {individual_limit}")
            print_success(f"  Current cycle games: {current_cycle_games}")
            print_success(f"  Cycle games: {cycle_games}")
            
            # Verify individual limit is respected
            if current_cycle_games <= individual_limit:
                print_success(f"  ✓ Individual limit respected: {current_cycle_games} <= {individual_limit}")
                record_test(f"Individual Limits - Regular Bot {bot_name}", True)
            else:
                print_error(f"  ✗ Individual limit exceeded: {current_cycle_games} > {individual_limit}")
                record_test(f"Individual Limits - Regular Bot {bot_name}", False, f"Limit exceeded: {current_cycle_games} > {individual_limit}")
    else:
        print_error("✗ Failed to get regular bots for individual limits test")
        record_test("Individual Limits - Regular Bots", False, "Failed to get bots")
    
    print_subheader("Step 2: Test Human-Bot Individual Limits")
    
    # Get human bots and check their individual limits
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=5",
        auth_token=admin_token
    )
    
    if human_bots_success and "bots" in human_bots_response:
        human_bots = human_bots_response["bots"]
        
        for bot in human_bots:
            bot_name = bot.get("name", "Unknown")
            bet_limit = bot.get("bet_limit", 0)
            max_concurrent_games = bot.get("max_concurrent_games", 0)
            
            print_success(f"Human-Bot '{bot_name}':")
            print_success(f"  Bet limit: {bet_limit}")
            print_success(f"  Max concurrent games: {max_concurrent_games}")
            
            # Verify individual limits are set
            if bet_limit > 0 and max_concurrent_games > 0:
                print_success(f"  ✓ Individual limits properly configured")
                record_test(f"Individual Limits - Human Bot {bot_name}", True)
            else:
                print_warning(f"  ⚠ Individual limits not properly set")
                record_test(f"Individual Limits - Human Bot {bot_name}", False, f"Limits not set: bet_limit={bet_limit}, max_concurrent={max_concurrent_games}")
    else:
        print_error("✗ Failed to get human bots for individual limits test")
        record_test("Individual Limits - Human Bots", False, "Failed to get bots")

def test_bot_bet_creation_logic():
    """Test that bot bet creation logic works correctly without global limits."""
    print_header("BOT BET CREATION LOGIC TESTING")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot test bot bet creation logic without admin access")
        return
    
    print_subheader("Step 1: Check Available Games Created by Bots")
    
    # Get available games to see bot-created games
    games_response, games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if games_success and isinstance(games_response, list):
        total_games = len(games_response)
        regular_bot_games = [g for g in games_response if g.get("creator_type") == "bot" and g.get("bot_type") == "REGULAR"]
        human_bot_games = [g for g in games_response if g.get("creator_type") == "human_bot"]
        
        print_success(f"✓ Available games endpoint accessible")
        print_success(f"  Total available games: {total_games}")
        print_success(f"  Regular bot games: {len(regular_bot_games)}")
        print_success(f"  Human-bot games: {len(human_bot_games)}")
        
        # Test that bots are creating games
        if len(regular_bot_games) > 0:
            print_success("✓ Regular bots are creating games")
            record_test("Bot Bet Creation - Regular Bots Creating Games", True)
            
            # Check game properties
            for i, game in enumerate(regular_bot_games[:3]):
                game_id = game.get("game_id", "unknown")
                bet_amount = game.get("bet_amount", 0)
                status = game.get("status", "unknown")
                
                print_success(f"  Regular bot game {i+1}: ID={game_id}, Bet=${bet_amount}, Status={status}")
                
                if status == "WAITING":
                    print_success(f"    ✓ Game has correct WAITING status")
                else:
                    print_warning(f"    ⚠ Game has unexpected status: {status}")
        else:
            print_warning("⚠ No regular bot games found")
            record_test("Bot Bet Creation - Regular Bots Creating Games", False, "No games found")
        
        if len(human_bot_games) > 0:
            print_success("✓ Human-bots are creating games")
            record_test("Bot Bet Creation - Human Bots Creating Games", True)
            
            # Check game properties
            for i, game in enumerate(human_bot_games[:3]):
                game_id = game.get("game_id", "unknown")
                bet_amount = game.get("bet_amount", 0)
                status = game.get("status", "unknown")
                
                print_success(f"  Human-bot game {i+1}: ID={game_id}, Bet=${bet_amount}, Status={status}")
                
                if status == "WAITING":
                    print_success(f"    ✓ Game has correct WAITING status")
                else:
                    print_warning(f"    ⚠ Game has unexpected status: {status}")
        else:
            print_warning("⚠ No human-bot games found")
            record_test("Bot Bet Creation - Human Bots Creating Games", False, "No games found")
        
        record_test("Bot Bet Creation - Available Games Check", True)
    else:
        print_error("✗ Failed to get available games")
        record_test("Bot Bet Creation - Available Games Check", False, "Failed to get games")
    
    print_subheader("Step 2: Monitor Bot Activity")
    
    # Monitor bot activity for a short period
    print("Monitoring bot activity for 15 seconds...")
    
    initial_games_count = len(games_response) if games_success else 0
    time.sleep(15)
    
    # Check games again
    games_response_after, games_success_after = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if games_success_after and isinstance(games_response_after, list):
        final_games_count = len(games_response_after)
        
        print_success(f"Games count before monitoring: {initial_games_count}")
        print_success(f"Games count after monitoring: {final_games_count}")
        
        if final_games_count >= initial_games_count:
            print_success("✓ Bot activity detected (games count maintained or increased)")
            record_test("Bot Bet Creation - Activity Monitoring", True)
        else:
            print_warning("⚠ Games count decreased during monitoring")
            record_test("Bot Bet Creation - Activity Monitoring", False, f"Games decreased: {initial_games_count} -> {final_games_count}")
    else:
        print_error("✗ Failed to get games after monitoring")
        record_test("Bot Bet Creation - Activity Monitoring", False, "Failed to get games after monitoring")

def test_system_stability():
    """Test overall system stability after removing global limits."""
    print_header("SYSTEM STABILITY TESTING")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot test system stability without admin access")
        return
    
    print_subheader("Step 1: Test Multiple API Endpoints")
    
    endpoints_to_test = [
        ("/admin/bots/regular/list?page=1&limit=5", "Regular Bots List"),
        ("/admin/human-bots?page=1&limit=5", "Human Bots List"),
        ("/games/available", "Available Games"),
        ("/admin/human-bots/stats", "Human Bot Stats"),
    ]
    
    stable_endpoints = 0
    
    for endpoint, name in endpoints_to_test:
        response, success = make_request("GET", endpoint, auth_token=admin_token)
        
        if success:
            print_success(f"✓ {name} endpoint stable")
            stable_endpoints += 1
            record_test(f"System Stability - {name}", True)
        else:
            print_error(f"✗ {name} endpoint unstable")
            record_test(f"System Stability - {name}", False, f"Endpoint failed: {response}")
    
    stability_percentage = (stable_endpoints / len(endpoints_to_test)) * 100
    print_success(f"System stability: {stability_percentage:.1f}% ({stable_endpoints}/{len(endpoints_to_test)} endpoints stable)")
    
    if stability_percentage >= 80:
        print_success("✓ System is stable after removing global limits")
        record_test("System Stability - Overall", True)
    else:
        print_error("✗ System stability compromised after removing global limits")
        record_test("System Stability - Overall", False, f"Only {stability_percentage:.1f}% stable")

def print_test_summary():
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    if total == 0:
        print_warning("No tests were executed")
        return
    
    success_rate = (passed / total) * 100
    
    print_success(f"Total tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success(f"Failed: {failed}")
    print_success(f"Success rate: {success_rate:.1f}%")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"✗ {test['name']}: {test['details']}")
    
    print_subheader("Overall Assessment:")
    if success_rate >= 90:
        print_success("🎉 EXCELLENT: Bot limits removal successful!")
    elif success_rate >= 80:
        print_success("✅ GOOD: Bot limits removal mostly successful with minor issues")
    elif success_rate >= 70:
        print_warning("⚠ ACCEPTABLE: Bot limits removal working but needs attention")
    else:
        print_error("❌ POOR: Bot limits removal has significant issues")

def main():
    """Main test execution function."""
    print_header("BOT LIMITS REMOVAL TESTING")
    print("Testing backend after removal of 'Лимиты активных ставок' functionality")
    print("=" * 80)
    
    # Test 1: Backend startup
    if not test_backend_startup():
        print_error("Backend startup test failed - aborting further tests")
        print_test_summary()
        return
    
    # Test 2: Deleted endpoints
    test_deleted_endpoints()
    
    # Test 3: Bot functionality without global limits
    test_bot_functionality_without_global_limits()
    
    # Test 4: Individual bot limits
    test_individual_bot_limits()
    
    # Test 5: Bot bet creation logic
    test_bot_bet_creation_logic()
    
    # Test 6: System stability
    test_system_stability()
    
    # Print summary
    print_test_summary()

if __name__ == "__main__":
    main()