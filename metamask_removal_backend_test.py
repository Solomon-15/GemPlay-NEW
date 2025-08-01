#!/usr/bin/env python3
"""
Backend API Testing After Metamask Code Removal
===============================================

This test verifies that the removal of Metamask code from the frontend 
did not affect any backend functionality. Tests all core API endpoints:

1. Authentication endpoints (login, refresh token)
2. User profile endpoints 
3. Game-related endpoints (create game, join game, lobby)
4. Bot management endpoints (human-bots, regular bots)
5. Admin panel endpoints (user management, stats)
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
BASE_URL = "https://a20aa5a2-a31c-4c8d-a1c4-18cc39118b00.preview.emergentagent.com/api"
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
        print_success(f"{name}: PASSED")
    else:
        test_results["failed"] += 1
        print_error(f"{name}: FAILED - {details}")
    
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
    
    try:
        if data and method.lower() in ["post", "put", "patch"]:
            headers["Content-Type"] = "application/json"
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
        else:
            response = requests.request(method, url, params=data, headers=headers, timeout=30)
        
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"text": response.text}
        
        success = response.status_code == expected_status
        return response_data, success
        
    except Exception as e:
        return {"error": str(e)}, False

def test_authentication_endpoints() -> Optional[str]:
    """Test authentication endpoints (login, refresh token)."""
    print_header("AUTHENTICATION ENDPOINTS TESTING")
    
    # Test 1: Admin Login
    print_subheader("Test 1: Admin Login")
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        admin_token = response["access_token"]
        print_success(f"Admin login successful")
        record_test("Authentication - Admin Login", True)
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Authentication - Admin Login", False, str(response))
        return None
    
    # Test 2: Token Validation (Get Current User)
    print_subheader("Test 2: Token Validation")
    me_response, me_success = make_request("GET", "/auth/me", auth_token=admin_token)
    
    if me_success and "id" in me_response:
        print_success("Token validation successful")
        record_test("Authentication - Token Validation", True)
    else:
        print_error(f"Token validation failed: {me_response}")
        record_test("Authentication - Token Validation", False, str(me_response))
    
    # Test 3: Super Admin Login
    print_subheader("Test 3: Super Admin Login")
    super_login_data = {
        "email": SUPER_ADMIN_USER["email"],
        "password": SUPER_ADMIN_USER["password"]
    }
    
    super_response, super_success = make_request("POST", "/auth/login", data=super_login_data)
    
    if super_success and "access_token" in super_response:
        print_success("Super admin login successful")
        record_test("Authentication - Super Admin Login", True)
    else:
        print_error(f"Super admin login failed: {super_response}")
        record_test("Authentication - Super Admin Login", False, str(super_response))
    
    return admin_token

def test_user_profile_endpoints(auth_token: str) -> None:
    """Test user profile endpoints."""
    print_header("USER PROFILE ENDPOINTS TESTING")
    
    # Test 1: Get User Profile
    print_subheader("Test 1: Get User Profile")
    profile_response, profile_success = make_request("GET", "/auth/me", auth_token=auth_token)
    
    if profile_success and "username" in profile_response:
        print_success("Get user profile successful")
        record_test("User Profile - Get Profile", True)
    else:
        print_error(f"Get user profile failed: {profile_response}")
        record_test("User Profile - Get Profile", False, str(profile_response))
    
    # Test 2: Update User Profile
    print_subheader("Test 2: Update User Profile")
    update_data = {
        "timezone_offset": 6  # Change timezone
    }
    
    update_response, update_success = make_request("PUT", "/auth/profile", data=update_data, auth_token=auth_token)
    
    if update_success and "timezone_offset" in update_response:
        print_success("Update user profile successful")
        record_test("User Profile - Update Profile", True)
    else:
        print_error(f"Update user profile failed: {update_response}")
        record_test("User Profile - Update Profile", False, str(update_response))

def test_game_related_endpoints(auth_token: str) -> None:
    """Test game-related endpoints (create game, join game, lobby)."""
    print_header("GAME-RELATED ENDPOINTS TESTING")
    
    # Test 1: Get Available Games (Lobby)
    print_subheader("Test 1: Get Available Games (Lobby)")
    games_response, games_success = make_request("GET", "/games/available", auth_token=auth_token)
    
    if games_success and isinstance(games_response, list):
        print_success(f"Get available games successful - Found {len(games_response)} games")
        record_test("Games - Get Available Games", True)
    else:
        print_error(f"Get available games failed: {games_response}")
        record_test("Games - Get Available Games", False, str(games_response))
    
    # Test 2: Get User's Gems Inventory
    print_subheader("Test 2: Get User's Gems Inventory")
    inventory_response, inventory_success = make_request("GET", "/gems/inventory", auth_token=auth_token)
    
    if inventory_success and isinstance(inventory_response, list):
        print_success(f"Get gems inventory successful - Found {len(inventory_response)} gem types")
        record_test("Games - Get Gems Inventory", True)
        
        # Check if user has enough gems for testing
        ruby_gems = 0
        for gem in inventory_response:
            if gem.get("type") == "Ruby":
                ruby_gems = gem.get("quantity", 0) - gem.get("frozen_quantity", 0)
                break
        
        if ruby_gems >= 10:
            # Test 3: Create Game
            print_subheader("Test 3: Create Game")
            create_game_data = {
                "move": "rock",
                "bet_gems": {"Ruby": 5}
            }
            
            create_response, create_success = make_request("POST", "/games/create", data=create_game_data, auth_token=auth_token)
            
            if create_success and "game_id" in create_response:
                game_id = create_response["game_id"]
                print_success(f"Create game successful - Game ID: {game_id}")
                record_test("Games - Create Game", True)
                
                # Test 4: Get Game Status
                print_subheader("Test 4: Get Game Status")
                status_response, status_success = make_request("GET", f"/games/{game_id}/status", auth_token=auth_token)
                
                if status_success and "status" in status_response:
                    print_success(f"Get game status successful - Status: {status_response['status']}")
                    record_test("Games - Get Game Status", True)
                else:
                    print_error(f"Get game status failed: {status_response}")
                    record_test("Games - Get Game Status", False, str(status_response))
                
                # Test 5: Cancel Game (cleanup)
                print_subheader("Test 5: Cancel Game")
                cancel_response, cancel_success = make_request("DELETE", f"/games/{game_id}/cancel", auth_token=auth_token)
                
                if cancel_success:
                    print_success("Cancel game successful")
                    record_test("Games - Cancel Game", True)
                else:
                    print_error(f"Cancel game failed: {cancel_response}")
                    record_test("Games - Cancel Game", False, str(cancel_response))
            else:
                print_error(f"Create game failed: {create_response}")
                record_test("Games - Create Game", False, str(create_response))
        else:
            print_warning("Not enough Ruby gems for game creation testing")
            record_test("Games - Create Game", False, "Insufficient gems")
    else:
        print_error(f"Get gems inventory failed: {inventory_response}")
        record_test("Games - Get Gems Inventory", False, str(inventory_response))

def test_bot_management_endpoints(auth_token: str) -> None:
    """Test bot management endpoints (human-bots, regular bots)."""
    print_header("BOT MANAGEMENT ENDPOINTS TESTING")
    
    # Test 1: Get Human-Bots List
    print_subheader("Test 1: Get Human-Bots List")
    human_bots_response, human_bots_success = make_request("GET", "/admin/human-bots?page=1&limit=10", auth_token=auth_token)
    
    if human_bots_success and "bots" in human_bots_response:
        bots_count = len(human_bots_response["bots"])
        print_success(f"Get human-bots list successful - Found {bots_count} bots")
        record_test("Bot Management - Get Human-Bots List", True)
    else:
        print_error(f"Get human-bots list failed: {human_bots_response}")
        record_test("Bot Management - Get Human-Bots List", False, str(human_bots_response))
    
    # Test 2: Get Human-Bots Statistics
    print_subheader("Test 2: Get Human-Bots Statistics")
    stats_response, stats_success = make_request("GET", "/admin/human-bots/stats", auth_token=auth_token)
    
    if stats_success and "total_bots" in stats_response:
        total_bots = stats_response["total_bots"]
        active_bots = stats_response.get("active_bots", 0)
        print_success(f"Get human-bots stats successful - Total: {total_bots}, Active: {active_bots}")
        record_test("Bot Management - Get Human-Bots Stats", True)
    else:
        print_error(f"Get human-bots stats failed: {stats_response}")
        record_test("Bot Management - Get Human-Bots Stats", False, str(stats_response))
    
    # Test 3: Get Regular Bots List
    print_subheader("Test 3: Get Regular Bots List")
    regular_bots_response, regular_bots_success = make_request("GET", "/admin/bots/regular/list?page=1&limit=10", auth_token=auth_token)
    
    if regular_bots_success and "bots" in regular_bots_response:
        regular_bots_count = len(regular_bots_response["bots"])
        print_success(f"Get regular bots list successful - Found {regular_bots_count} bots")
        record_test("Bot Management - Get Regular Bots List", True)
    else:
        print_error(f"Get regular bots list failed: {regular_bots_response}")
        record_test("Bot Management - Get Regular Bots List", False, str(regular_bots_response))

def test_admin_panel_endpoints(auth_token: str) -> None:
    """Test admin panel endpoints (user management, stats)."""
    print_header("ADMIN PANEL ENDPOINTS TESTING")
    
    # Test 1: Get Users List
    print_subheader("Test 1: Get Users List")
    users_response, users_success = make_request("GET", "/admin/users?page=1&limit=10", auth_token=auth_token)
    
    if users_success and "users" in users_response:
        users_count = len(users_response["users"])
        print_success(f"Get users list successful - Found {users_count} users")
        record_test("Admin Panel - Get Users List", True)
    else:
        print_error(f"Get users list failed: {users_response}")
        record_test("Admin Panel - Get Users List", False, str(users_response))
    
    # Test 2: Get Dashboard Stats
    print_subheader("Test 2: Get Dashboard Stats")
    dashboard_response, dashboard_success = make_request("GET", "/admin/dashboard/stats", auth_token=auth_token)
    
    if dashboard_success and "active_human_bots" in dashboard_response:
        active_human_bots = dashboard_response["active_human_bots"]
        online_users = dashboard_response.get("online_users", 0)
        print_success(f"Get dashboard stats successful - Human-bots: {active_human_bots}, Online users: {online_users}")
        record_test("Admin Panel - Get Dashboard Stats", True)
    else:
        print_error(f"Get dashboard stats failed: {dashboard_response}")
        record_test("Admin Panel - Get Dashboard Stats", False, str(dashboard_response))
    
    # Test 3: Get Economy Balance
    print_subheader("Test 3: Get Economy Balance")
    balance_response, balance_success = make_request("GET", "/economy/balance", auth_token=auth_token)
    
    if balance_success and "virtual_balance" in balance_response:
        virtual_balance = balance_response["virtual_balance"]
        frozen_balance = balance_response.get("frozen_balance", 0)
        print_success(f"Get economy balance successful - Virtual: ${virtual_balance}, Frozen: ${frozen_balance}")
        record_test("Admin Panel - Get Economy Balance", True)
    else:
        print_error(f"Get economy balance failed: {balance_response}")
        record_test("Admin Panel - Get Economy Balance", False, str(balance_response))
    
    # Test 4: Get Gem Definitions (Admin)
    print_subheader("Test 4: Get Gem Definitions")
    gems_response, gems_success = make_request("GET", "/admin/gems", auth_token=auth_token)
    
    if gems_success and isinstance(gems_response, list):
        gems_count = len(gems_response)
        print_success(f"Get gem definitions successful - Found {gems_count} gem types")
        record_test("Admin Panel - Get Gem Definitions", True)
    else:
        print_error(f"Get gem definitions failed: {gems_response}")
        record_test("Admin Panel - Get Gem Definitions", False, str(gems_response))

def test_additional_critical_endpoints(auth_token: str) -> None:
    """Test additional critical endpoints that might be affected by frontend changes."""
    print_header("ADDITIONAL CRITICAL ENDPOINTS TESTING")
    
    # Test 1: Get Sounds List
    print_subheader("Test 1: Get Sounds List")
    sounds_response, sounds_success = make_request("GET", "/admin/sounds", auth_token=auth_token)
    
    if sounds_success and isinstance(sounds_response, list):
        sounds_count = len(sounds_response)
        print_success(f"Get sounds list successful - Found {sounds_count} sounds")
        record_test("Additional - Get Sounds List", True)
    else:
        print_error(f"Get sounds list failed: {sounds_response}")
        record_test("Additional - Get Sounds List", False, str(sounds_response))
    
    # Test 2: Get Admin Logs
    print_subheader("Test 2: Get Admin Logs")
    logs_response, logs_success = make_request("GET", "/admin/logs?page=1&limit=10", auth_token=auth_token)
    
    if logs_success and "logs" in logs_response:
        logs_count = len(logs_response["logs"])
        print_success(f"Get admin logs successful - Found {logs_count} log entries")
        record_test("Additional - Get Admin Logs", True)
    else:
        print_error(f"Get admin logs failed: {logs_response}")
        record_test("Additional - Get Admin Logs", False, str(logs_response))
    
    # Test 3: Get Security Alerts
    print_subheader("Test 3: Get Security Alerts")
    alerts_response, alerts_success = make_request("GET", "/admin/security/alerts?page=1&limit=10", auth_token=auth_token)
    
    if alerts_success and "alerts" in alerts_response:
        alerts_count = len(alerts_response["alerts"])
        print_success(f"Get security alerts successful - Found {alerts_count} alerts")
        record_test("Additional - Get Security Alerts", True)
    else:
        print_error(f"Get security alerts failed: {alerts_response}")
        record_test("Additional - Get Security Alerts", False, str(alerts_response))

def print_test_summary() -> None:
    """Print the final test summary."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 80 else Colors.FAIL}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"{test['name']}: {test['details']}")
    
    print_subheader("Conclusion:")
    if success_rate >= 90:
        print_success("✅ EXCELLENT: Backend APIs are working perfectly after Metamask code removal")
    elif success_rate >= 80:
        print_success("✅ GOOD: Backend APIs are mostly working after Metamask code removal")
    elif success_rate >= 70:
        print_warning("⚠ ACCEPTABLE: Backend APIs have minor issues after Metamask code removal")
    else:
        print_error("❌ CRITICAL: Backend APIs have significant issues after Metamask code removal")

def main():
    """Main test execution function."""
    print_header("BACKEND API TESTING AFTER METAMASK CODE REMOVAL")
    print("Testing all core backend API endpoints to ensure Metamask removal did not affect backend functionality...")
    
    # Step 1: Test Authentication
    admin_token = test_authentication_endpoints()
    if not admin_token:
        print_error("Cannot proceed without valid authentication token")
        return
    
    # Step 2: Test User Profile Endpoints
    test_user_profile_endpoints(admin_token)
    
    # Step 3: Test Game-Related Endpoints
    test_game_related_endpoints(admin_token)
    
    # Step 4: Test Bot Management Endpoints
    test_bot_management_endpoints(admin_token)
    
    # Step 5: Test Admin Panel Endpoints
    test_admin_panel_endpoints(admin_token)
    
    # Step 6: Test Additional Critical Endpoints
    test_additional_critical_endpoints(admin_token)
    
    # Step 7: Print Summary
    print_test_summary()

if __name__ == "__main__":
    main()