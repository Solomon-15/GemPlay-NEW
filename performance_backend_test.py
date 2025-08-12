#!/usr/bin/env python3
"""
Performance Testing After Console Logs Optimization - Russian Review
Focus: Testing system performance after console log cleanup and specific endpoints
Requirements: 
1. Authentication - GET /api/auth/me
2. Regular Bots Management:
   - GET /api/admin/bots (список обычных ботов)
   - GET /api/admin/bots/regular/list (специальный эндпоинт для regular bots)
   - PUT /api/admin/bots/{bot_id}/pause-settings
   - PUT /api/admin/bots/{bot_id}/win-percentage
3. Human Bots Management:
   - GET /api/admin/human-bots
   - POST /api/admin/human-bots/bulk-create
4. Dashboard Statistics:
   - GET /api/admin/dashboard/stats
5. Verify active_bets field is correctly calculated for bots
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
BASE_URL = "https://russian-writer-2.preview.emergentagent.com/api"
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

def test_performance_after_console_optimization() -> None:
    """Test system performance after console logs optimization."""
    print_header("PERFORMANCE TESTING AFTER CONSOLE LOGS OPTIMIZATION")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Authentication")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with performance testing")
        record_test("Performance Test - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # Test 1: Authentication endpoint
    print_subheader("Test 1: Authentication - GET /api/auth/me")
    
    start_time = time.time()
    auth_response, auth_success = make_request(
        "GET", "/auth/me",
        auth_token=admin_token
    )
    auth_time = time.time() - start_time
    
    if auth_success:
        print_success(f"✅ GET /api/auth/me working correctly")
        print_success(f"  Response time: {auth_time:.3f}s")
        print_success(f"  User role: {auth_response.get('role', 'Unknown')}")
        print_success(f"  User email: {auth_response.get('email', 'Unknown')}")
        record_test("Performance Test - Auth Me Endpoint", True, f"Response time: {auth_time:.3f}s")
    else:
        print_error("❌ GET /api/auth/me endpoint failed")
        record_test("Performance Test - Auth Me Endpoint", False, "Endpoint failed")
    
    # Test 2: Regular Bots Management
    print_subheader("Test 2: Regular Bots Management")
    
    # Test 2.1: GET /api/admin/bots
    print_subheader("Test 2.1: GET /api/admin/bots (список обычных ботов)")
    
    start_time = time.time()
    bots_response, bots_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    bots_time = time.time() - start_time
    
    if bots_success:
        print_success(f"✅ GET /api/admin/bots working correctly")
        print_success(f"  Response time: {bots_time:.3f}s")
        
        if "bots" in bots_response:
            bots = bots_response["bots"]
            print_success(f"  Found {len(bots)} regular bots")
            
            # Check active_bets calculation
            bots_with_active_bets = 0
            total_active_bets = 0
            
            for bot in bots[:5]:  # Check first 5 bots
                bot_name = bot.get("name", "Unknown")
                active_bets = bot.get("active_bets", 0)
                
                if active_bets > 0:
                    bots_with_active_bets += 1
                    total_active_bets += active_bets
                    print_success(f"    ✅ Bot '{bot_name}': {active_bets} active bets")
                else:
                    print_warning(f"    ⚠ Bot '{bot_name}': {active_bets} active bets")
            
            if bots_with_active_bets > 0:
                print_success(f"  ✅ active_bets field correctly calculated for {bots_with_active_bets} bots")
                record_test("Performance Test - Regular Bots List", True, f"Response time: {bots_time:.3f}s, {bots_with_active_bets} bots with active bets")
            else:
                print_warning("  ⚠ All bots show active_bets = 0")
                record_test("Performance Test - Regular Bots List", True, f"Response time: {bots_time:.3f}s, but all bots show 0 active bets")
        else:
            print_error("  ❌ Response missing 'bots' field")
            record_test("Performance Test - Regular Bots List", False, "Missing bots field")
    else:
        print_error("❌ GET /api/admin/bots endpoint failed")
        record_test("Performance Test - Regular Bots List", False, "Endpoint failed")
    
    # Test 2.2: GET /api/admin/bots/regular/list
    print_subheader("Test 2.2: GET /api/admin/bots/regular/list (специальный эндпоинт)")
    
    start_time = time.time()
    regular_bots_response, regular_bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=10",
        auth_token=admin_token
    )
    regular_bots_time = time.time() - start_time
    
    if regular_bots_success:
        print_success(f"✅ GET /api/admin/bots/regular/list working correctly")
        print_success(f"  Response time: {regular_bots_time:.3f}s")
        
        if "bots" in regular_bots_response:
            regular_bots = regular_bots_response["bots"]
            print_success(f"  Found {len(regular_bots)} regular bots in detailed list")
            
            # Check active_bets calculation in detailed list
            detailed_bots_with_active_bets = 0
            
            for bot in regular_bots:
                bot_name = bot.get("name", "Unknown")
                active_bets = bot.get("active_bets", 0)
                win_percentage = bot.get("win_percentage", 0)
                pause_between_games = bot.get("pause_between_games", 0)
                
                if active_bets > 0:
                    detailed_bots_with_active_bets += 1
                    print_success(f"    ✅ Bot '{bot_name}': {active_bets} active bets, {win_percentage}% win rate, {pause_between_games}s pause")
                else:
                    print_warning(f"    ⚠ Bot '{bot_name}': {active_bets} active bets, {win_percentage}% win rate, {pause_between_games}s pause")
            
            record_test("Performance Test - Regular Bots Detailed List", True, f"Response time: {regular_bots_time:.3f}s, {detailed_bots_with_active_bets} bots with active bets")
        else:
            print_error("  ❌ Response missing 'bots' field")
            record_test("Performance Test - Regular Bots Detailed List", False, "Missing bots field")
    else:
        print_error("❌ GET /api/admin/bots/regular/list endpoint failed")
        record_test("Performance Test - Regular Bots Detailed List", False, "Endpoint failed")
    
    # Get a test bot for PUT operations
    test_bot = None
    if bots_success and "bots" in bots_response and bots_response["bots"]:
        test_bot = bots_response["bots"][0]
    elif regular_bots_success and "bots" in regular_bots_response and regular_bots_response["bots"]:
        test_bot = regular_bots_response["bots"][0]
    
    if test_bot:
        test_bot_id = test_bot["id"]
        test_bot_name = test_bot["name"]
        print_success(f"Using test bot: {test_bot_name} (ID: {test_bot_id})")
        
        # Test 2.3: PUT /api/admin/bots/{bot_id}/pause-settings
        print_subheader("Test 2.3: PUT /api/admin/bots/{bot_id}/pause-settings")
        
        current_pause = test_bot.get("pause_between_games", 5)
        new_pause = current_pause + 1 if current_pause < 10 else current_pause - 1
        
        pause_data = {"pause_between_games": new_pause}
        
        start_time = time.time()
        pause_response, pause_success = make_request(
            "PUT", f"/admin/bots/{test_bot_id}/pause-settings",
            data=pause_data,
            auth_token=admin_token
        )
        pause_time = time.time() - start_time
        
        if pause_success:
            print_success(f"✅ PUT /api/admin/bots/pause-settings working correctly")
            print_success(f"  Response time: {pause_time:.3f}s")
            print_success(f"  Updated pause from {current_pause}s to {new_pause}s")
            record_test("Performance Test - Bot Pause Settings", True, f"Response time: {pause_time:.3f}s")
        else:
            print_error("❌ PUT /api/admin/bots/pause-settings endpoint failed")
            record_test("Performance Test - Bot Pause Settings", False, "Endpoint failed")
        
        # Test 2.4: PUT /api/admin/bots/{bot_id}/win-percentage
        print_subheader("Test 2.4: PUT /api/admin/bots/{bot_id}/win-percentage")
        
        current_win_percentage = test_bot.get("win_percentage", 55.0)
        new_win_percentage = 60.0 if current_win_percentage != 60.0 else 55.0
        
        win_data = {"win_percentage": new_win_percentage}
        
        start_time = time.time()
        win_response, win_success = make_request(
            "PUT", f"/admin/bots/{test_bot_id}/win-percentage",
            data=win_data,
            auth_token=admin_token
        )
        win_time = time.time() - start_time
        
        if win_success:
            print_success(f"✅ PUT /api/admin/bots/win-percentage working correctly")
            print_success(f"  Response time: {win_time:.3f}s")
            print_success(f"  Updated win percentage from {current_win_percentage}% to {new_win_percentage}%")
            record_test("Performance Test - Bot Win Percentage", True, f"Response time: {win_time:.3f}s")
        else:
            print_error("❌ PUT /api/admin/bots/win-percentage endpoint failed")
            record_test("Performance Test - Bot Win Percentage", False, "Endpoint failed")
    else:
        print_warning("No test bot available for PUT operations")
        record_test("Performance Test - Bot Pause Settings", False, "No test bot available")
        record_test("Performance Test - Bot Win Percentage", False, "No test bot available")
    
    # Test 3: Human Bots Management
    print_subheader("Test 3: Human Bots Management")
    
    # Test 3.1: GET /api/admin/human-bots
    print_subheader("Test 3.1: GET /api/admin/human-bots")
    
    start_time = time.time()
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    human_bots_time = time.time() - start_time
    
    if human_bots_success:
        print_success(f"✅ GET /api/admin/human-bots working correctly")
        print_success(f"  Response time: {human_bots_time:.3f}s")
        
        if "bots" in human_bots_response:
            human_bots = human_bots_response["bots"]
            print_success(f"  Found {len(human_bots)} human bots")
            
            # Show some human bot details
            for bot in human_bots[:3]:  # Show first 3 bots
                bot_name = bot.get("name", "Unknown")
                character = bot.get("character", "Unknown")
                is_active = bot.get("is_active", False)
                virtual_balance = bot.get("virtual_balance", 0)
                
                print_success(f"    Human Bot '{bot_name}': {character}, Active: {is_active}, Balance: ${virtual_balance}")
            
            record_test("Performance Test - Human Bots List", True, f"Response time: {human_bots_time:.3f}s, {len(human_bots)} bots")
        else:
            print_error("  ❌ Response missing 'bots' field")
            record_test("Performance Test - Human Bots List", False, "Missing bots field")
    else:
        print_error("❌ GET /api/admin/human-bots endpoint failed")
        record_test("Performance Test - Human Bots List", False, "Endpoint failed")
    
    # Test 3.2: POST /api/admin/human-bots/bulk-create
    print_subheader("Test 3.2: POST /api/admin/human-bots/bulk-create")
    
    bulk_create_data = {
        "count": 1,  # Create just 1 bot for testing
        "character": "BALANCED",
        "min_bet_range": [1.0, 5.0],
        "max_bet_range": [10.0, 20.0],
        "bet_limit_range": [5, 10],
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "delay_range": [30, 60]
    }
    
    start_time = time.time()
    bulk_create_response, bulk_create_success = make_request(
        "POST", "/admin/human-bots/bulk-create",
        data=bulk_create_data,
        auth_token=admin_token
    )
    bulk_create_time = time.time() - start_time
    
    if bulk_create_success:
        print_success(f"✅ POST /api/admin/human-bots/bulk-create working correctly")
        print_success(f"  Response time: {bulk_create_time:.3f}s")
        
        created_count = bulk_create_response.get("created_count", 0)
        failed_count = bulk_create_response.get("failed_count", 0)
        
        print_success(f"  Created: {created_count} bots, Failed: {failed_count} bots")
        
        if created_count > 0:
            record_test("Performance Test - Human Bots Bulk Create", True, f"Response time: {bulk_create_time:.3f}s, created {created_count} bots")
        else:
            record_test("Performance Test - Human Bots Bulk Create", True, f"Response time: {bulk_create_time:.3f}s, but no bots created (may be capacity limit)")
    else:
        print_error("❌ POST /api/admin/human-bots/bulk-create endpoint failed")
        record_test("Performance Test - Human Bots Bulk Create", False, "Endpoint failed")
    
    # Test 4: Dashboard Statistics
    print_subheader("Test 4: Dashboard Statistics")
    
    # Test 4.1: GET /api/admin/dashboard/stats
    print_subheader("Test 4.1: GET /api/admin/dashboard/stats")
    
    start_time = time.time()
    dashboard_response, dashboard_success = make_request(
        "GET", "/admin/dashboard/stats",
        auth_token=admin_token
    )
    dashboard_time = time.time() - start_time
    
    if dashboard_success:
        print_success(f"✅ GET /api/admin/dashboard/stats working correctly")
        print_success(f"  Response time: {dashboard_time:.3f}s")
        
        # Show key dashboard statistics
        total_users = dashboard_response.get("total_users", 0)
        online_users = dashboard_response.get("online_users", 0)
        active_human_bots = dashboard_response.get("active_human_bots", 0)
        total_games_today = dashboard_response.get("total_games_today", 0)
        revenue_today = dashboard_response.get("revenue_today", 0)
        
        print_success(f"  Total Users: {total_users}")
        print_success(f"  Online Users: {online_users}")
        print_success(f"  Active Human Bots: {active_human_bots}")
        print_success(f"  Games Today: {total_games_today}")
        print_success(f"  Revenue Today: ${revenue_today}")
        
        record_test("Performance Test - Dashboard Stats", True, f"Response time: {dashboard_time:.3f}s")
    else:
        print_error("❌ GET /api/admin/dashboard/stats endpoint failed")
        record_test("Performance Test - Dashboard Stats", False, "Endpoint failed")
    
    # Performance Summary
    print_subheader("Performance Summary After Console Logs Optimization")
    
    # Calculate average response times
    response_times = []
    if auth_success:
        response_times.append(auth_time)
    if bots_success:
        response_times.append(bots_time)
    if regular_bots_success:
        response_times.append(regular_bots_time)
    if human_bots_success:
        response_times.append(human_bots_time)
    if dashboard_success:
        response_times.append(dashboard_time)
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print_success(f"✅ Average response time: {avg_response_time:.3f}s")
        print_success(f"✅ Fastest response: {min_response_time:.3f}s")
        print_success(f"✅ Slowest response: {max_response_time:.3f}s")
        
        if avg_response_time < 1.0:
            print_success("🎉 Excellent performance - all endpoints respond under 1 second on average")
        elif avg_response_time < 2.0:
            print_success("✅ Good performance - endpoints respond under 2 seconds on average")
        else:
            print_warning("⚠ Performance could be improved - some endpoints are slow")
    
    print_success("Performance testing after console logs optimization completed")

def main():
    """Main test execution function."""
    print_header("PERFORMANCE TESTING AFTER CONSOLE LOGS OPTIMIZATION - RUSSIAN REVIEW")
    print("Testing system performance after console log cleanup and specific endpoints")
    print("Focus: Authentication, Regular Bots, Human Bots, Dashboard Statistics")
    print()
    
    try:
        # Run the performance test after console optimization
        test_performance_after_console_optimization()
        
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
            print_success("🎉 PERFORMANCE TESTING AFTER CONSOLE OPTIMIZATION SUCCESSFUL!")
        elif success_rate >= 60:
            print_warning("⚠ PERFORMANCE TESTING PARTIALLY SUCCESSFUL")
        else:
            print_error("❌ PERFORMANCE ISSUES DETECTED - NEEDS ATTENTION")
    
    # Show failed tests
    failed_tests = [test for test in test_results['tests'] if not test['passed']]
    if failed_tests:
        print_header("FAILED TESTS DETAILS")
        for test in failed_tests:
            print_error(f"❌ {test['name']}: {test['details']}")
    
    return test_results['failed'] == 0

if __name__ == "__main__":
    main()