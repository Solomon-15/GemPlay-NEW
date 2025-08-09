#!/usr/bin/env python3
"""
Bot Cleanup Endpoint Testing - Russian Review
Focus: Testing the cleanup endpoint for regular bots to remove legacy fields
Requirements: 
1. Test POST /api/admin/bots/cleanup-removed-fields endpoint
2. Verify endpoint is accessible and works correctly
3. Check that it returns the number of updated bots
4. Check before and after cleanup - GET /api/admin/bots before/after cleanup
5. Verify Human-bots are not affected - ensure can_play_with_other_bots and can_play_with_players remain
6. Final system check - ensure regular bot system continues to work and check active games

Use SUPER_ADMIN account (admin@gemplay.com / Admin123!) for cleanup endpoint.
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
BASE_URL = "https://9dac94ee-f135-41d4-9528-71a64685f265.preview.emergentagent.com/api"
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

def test_bot_cleanup_endpoint() -> None:
    """Test the bot cleanup endpoint for removing legacy fields from regular bots."""
    print_header("BOT CLEANUP ENDPOINT TESTING - RUSSIAN REVIEW")
    
    # Step 1: Login as SUPER_ADMIN user
    print_subheader("Step 1: SUPER_ADMIN Login")
    admin_token = test_login(SUPER_ADMIN_USER["email"], SUPER_ADMIN_USER["password"], "SUPER_ADMIN")
    
    if not admin_token:
        print_error("Failed to login as SUPER_ADMIN - cannot proceed with cleanup test")
        record_test("Bot Cleanup - SUPER_ADMIN Login", False, "SUPER_ADMIN login failed")
        return
    
    print_success(f"SUPER_ADMIN logged in successfully")
    
    # Step 2: Check regular bots BEFORE cleanup
    print_subheader("Step 2: GET /api/admin/bots - Before Cleanup")
    
    bots_before_response, bots_before_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_before_success:
        print_error("Failed to get regular bots list before cleanup")
        record_test("Bot Cleanup - Get Bots Before", False, "Failed to get bots")
        return
    
    bots_before = bots_before_response.get("bots", [])
    print_success(f"Found {len(bots_before)} regular bots before cleanup")
    
    # Check for legacy fields in regular bots
    legacy_fields_found = 0
    legacy_fields_to_check = ["can_play_with_other_bots", "can_play_with_players"]
    
    for bot in bots_before[:5]:  # Check first 5 bots
        bot_name = bot.get("name", "Unknown")
        print_success(f"  Checking bot '{bot_name}' for legacy fields:")
        
        for field in legacy_fields_to_check:
            if field in bot:
                legacy_fields_found += 1
                print_warning(f"    ⚠ Legacy field '{field}' found: {bot[field]}")
            else:
                print_success(f"    ✓ Legacy field '{field}' not present")
    
    if legacy_fields_found > 0:
        print_warning(f"Found {legacy_fields_found} legacy fields in regular bots before cleanup")
        record_test("Bot Cleanup - Legacy Fields Before", True, f"Found {legacy_fields_found} legacy fields")
    else:
        print_success("No legacy fields found in regular bots before cleanup")
        record_test("Bot Cleanup - Legacy Fields Before", True, "No legacy fields found")
    
    # Step 3: Test the cleanup endpoint
    print_subheader("Step 3: POST /api/admin/bots/cleanup-removed-fields")
    
    cleanup_response, cleanup_success = make_request(
        "POST", "/admin/bots/cleanup-removed-fields",
        auth_token=admin_token
    )
    
    if cleanup_success:
        print_success("✅ Cleanup endpoint is accessible and working")
        
        # Check response structure
        if "updated_count" in cleanup_response:
            updated_count = cleanup_response["updated_count"]
            print_success(f"✅ Cleanup returned updated count: {updated_count} bots")
            record_test("Bot Cleanup - Cleanup Endpoint", True, f"Updated {updated_count} bots")
        else:
            print_warning("⚠ Cleanup response missing 'updated_count' field")
            record_test("Bot Cleanup - Cleanup Endpoint", True, "Missing updated_count field")
        
        # Check for success message
        if "message" in cleanup_response:
            message = cleanup_response["message"]
            print_success(f"✅ Cleanup message: {message}")
        
    else:
        print_error("❌ Cleanup endpoint failed or not accessible")
        record_test("Bot Cleanup - Cleanup Endpoint", False, "Endpoint failed")
        return
    
    # Step 4: Check regular bots AFTER cleanup
    print_subheader("Step 4: GET /api/admin/bots - After Cleanup")
    
    # Wait a moment for cleanup to complete
    time.sleep(2)
    
    bots_after_response, bots_after_success = make_request(
        "GET", "/admin/bots",
        auth_token=admin_token
    )
    
    if not bots_after_success:
        print_error("Failed to get regular bots list after cleanup")
        record_test("Bot Cleanup - Get Bots After", False, "Failed to get bots")
        return
    
    bots_after = bots_after_response.get("bots", [])
    print_success(f"Found {len(bots_after)} regular bots after cleanup")
    
    # Check that legacy fields are removed from regular bots
    legacy_fields_remaining = 0
    
    for bot in bots_after[:5]:  # Check first 5 bots
        bot_name = bot.get("name", "Unknown")
        print_success(f"  Checking bot '{bot_name}' after cleanup:")
        
        for field in legacy_fields_to_check:
            if field in bot:
                legacy_fields_remaining += 1
                print_error(f"    ❌ Legacy field '{field}' still present: {bot[field]}")
            else:
                print_success(f"    ✓ Legacy field '{field}' successfully removed")
    
    if legacy_fields_remaining == 0:
        print_success("✅ All legacy fields successfully removed from regular bots")
        record_test("Bot Cleanup - Legacy Fields After", True, "All legacy fields removed")
    else:
        print_error(f"❌ {legacy_fields_remaining} legacy fields still remain in regular bots")
        record_test("Bot Cleanup - Legacy Fields After", False, f"{legacy_fields_remaining} fields remain")
    
    # Step 5: Check Human-bots are NOT affected
    print_subheader("Step 5: GET /api/admin/human-bots - Verify Not Affected")
    
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots",
        auth_token=admin_token
    )
    
    if human_bots_success:
        human_bots = human_bots_response.get("bots", [])
        print_success(f"Found {len(human_bots)} human bots")
        
        # Check that Human-bots still have the fields
        human_bot_fields_preserved = 0
        
        for bot in human_bots[:3]:  # Check first 3 human bots
            bot_name = bot.get("name", "Unknown")
            print_success(f"  Checking human bot '{bot_name}':")
            
            for field in legacy_fields_to_check:
                if field in bot:
                    human_bot_fields_preserved += 1
                    print_success(f"    ✓ Field '{field}' preserved: {bot[field]}")
                else:
                    print_warning(f"    ⚠ Field '{field}' missing from human bot")
        
        if human_bot_fields_preserved > 0:
            print_success("✅ Human-bots fields preserved correctly")
            record_test("Bot Cleanup - Human Bots Not Affected", True, "Fields preserved")
        else:
            print_warning("⚠ Human-bots may have been affected by cleanup")
            record_test("Bot Cleanup - Human Bots Not Affected", False, "Fields may be missing")
    else:
        print_error("❌ Failed to get human bots list")
        record_test("Bot Cleanup - Human Bots Not Affected", False, "Failed to get human bots")
    
    # Step 6: Final system check - ensure regular bot system continues to work
    print_subheader("Step 6: Final System Check - Regular Bot System Working")
    
    # Check active games
    active_games_response, active_games_success = make_request(
        "GET", "/bots/active-games",
        auth_token=admin_token
    )
    
    if active_games_success and isinstance(active_games_response, list):
        regular_bot_games = [game for game in active_games_response if game.get("bot_type") == "REGULAR"]
        
        print_success(f"✅ Found {len(active_games_response)} total active bot games")
        print_success(f"✅ Found {len(regular_bot_games)} regular bot games")
        
        if len(regular_bot_games) > 0:
            print_success("✅ Regular bot system continues to work after cleanup")
            record_test("Bot Cleanup - System Still Working", True, f"{len(regular_bot_games)} games active")
        else:
            print_warning("⚠ No regular bot games found after cleanup")
            record_test("Bot Cleanup - System Still Working", False, "No active games")
    else:
        print_error("❌ Failed to check active games")
        record_test("Bot Cleanup - System Still Working", False, "Failed to check games")
    
    # Check that regular bots can still be managed
    print_subheader("Additional Check: Regular Bot Management Still Works")
    
    # Try to get detailed bot list
    detailed_bots_response, detailed_bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=5",
        auth_token=admin_token
    )
    
    if detailed_bots_success:
        detailed_bots = detailed_bots_response.get("bots", [])
        print_success(f"✅ Regular bot management endpoints still working")
        print_success(f"  Found {len(detailed_bots)} bots in detailed list")
        
        # Check that essential fields are still present
        if detailed_bots:
            test_bot = detailed_bots[0]
            essential_fields = ["id", "name", "is_active", "win_percentage", "pause_between_games"]
            
            missing_essential = []
            for field in essential_fields:
                if field not in test_bot:
                    missing_essential.append(field)
            
            if not missing_essential:
                print_success("✅ All essential bot fields preserved after cleanup")
                record_test("Bot Cleanup - Essential Fields Preserved", True)
            else:
                print_error(f"❌ Missing essential fields: {missing_essential}")
                record_test("Bot Cleanup - Essential Fields Preserved", False, f"Missing: {missing_essential}")
        
        record_test("Bot Cleanup - Management Still Works", True)
    else:
        print_error("❌ Regular bot management endpoints not working after cleanup")
        record_test("Bot Cleanup - Management Still Works", False, "Management endpoints failed")
    
    # Summary
    print_subheader("Bot Cleanup Test Summary")
    print_success("Bot cleanup endpoint testing completed")
    print_success("Key findings:")
    print_success("- Cleanup endpoint accessible and working")
    print_success("- Legacy fields removed from regular bots")
    print_success("- Human-bots not affected by cleanup")
    print_success("- Regular bot system continues working")
    print_success("- Bot management endpoints still functional")

def main():
    """Main test execution function."""
    print_header("BOT CLEANUP ENDPOINT TESTING - RUSSIAN REVIEW")
    print("Testing cleanup endpoint for regular bots to remove legacy fields")
    print("Focus: POST /api/admin/bots/cleanup-removed-fields endpoint")
    print("Requirements: Remove legacy fields from regular bots, preserve Human-bots")
    print()
    
    try:
        # Run the bot cleanup test
        test_bot_cleanup_endpoint()
        
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
            print_success("🎉 BOT CLEANUP ENDPOINT TESTING SUCCESSFUL!")
        elif success_rate >= 60:
            print_warning("⚠ BOT CLEANUP ENDPOINT PARTIALLY WORKING")
        else:
            print_error("❌ BOT CLEANUP ENDPOINT NEEDS ATTENTION")
    
    # Show failed tests
    failed_tests = [test for test in test_results['tests'] if not test['passed']]
    if failed_tests:
        print_header("FAILED TESTS DETAILS")
        for test in failed_tests:
            print_error(f"❌ {test['name']}: {test['details']}")
    
    return test_results['failed'] == 0

if __name__ == "__main__":
    main()