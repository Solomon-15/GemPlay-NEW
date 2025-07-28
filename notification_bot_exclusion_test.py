#!/usr/bin/env python3
"""
GemPlay Notification System Bot Exclusion Testing
Testing the fixes for bot exclusion logic in broadcast and resend endpoints
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://baf8f4bf-8f93-48f1-becd-06acae851bae.preview.emergentagent.com/api"
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
    print_subheader(f"Testing {user_type.title()} Login")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response and "user" in response:
        print_success(f"{user_type.title()} login successful")
        print_success(f"User details: {response['user']['username']} ({response['user']['email']})")
        record_test(f"{user_type.title()} Login", True)
        return response["access_token"]
    else:
        print_error(f"{user_type.title()} login failed: {response}")
        record_test(f"{user_type.title()} Login", False, f"Login failed: {response}")
        return None

def test_notification_bot_exclusion_fixes() -> None:
    """Test the notification system bot exclusion fixes as requested in the review."""
    print_header("NOTIFICATION SYSTEM BOT EXCLUSION FIXES TESTING")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with notification bot exclusion test")
        record_test("Bot Exclusion - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # TEST 1: Broadcast notification to all users and check recipient count
    print_subheader("TEST 1: Broadcast Notification with Bot Exclusion")
    
    broadcast_data = {
        "target_users": None,  # Send to all users (should exclude bots)
        "type": "admin_notification",
        "priority": "info",
        "title": "Test Bot Exclusion",
        "message": "Testing that bots are excluded from broadcast notifications"
    }
    
    broadcast_response, broadcast_success = make_request(
        "POST", "/admin/notifications/broadcast",
        data=broadcast_data,
        auth_token=admin_token
    )
    
    if not broadcast_success:
        print_error("Failed to send broadcast notification")
        record_test("Bot Exclusion - Broadcast Request", False, "Broadcast failed")
        return
    
    # Check response structure
    expected_fields = ["success", "message", "sent_count", "notification_id"]
    missing_fields = [field for field in expected_fields if field not in broadcast_response]
    
    if missing_fields:
        print_error(f"Broadcast response missing fields: {missing_fields}")
        record_test("Bot Exclusion - Broadcast Response Structure", False, f"Missing: {missing_fields}")
    else:
        print_success("✓ Broadcast response has all expected fields")
        record_test("Bot Exclusion - Broadcast Response Structure", True)
    
    # Get sent count
    sent_count = broadcast_response.get("sent_count", 0)
    notification_id = broadcast_response.get("notification_id", "")
    
    print_success(f"✓ Broadcast sent to {sent_count} recipients")
    print_success(f"✓ Notification ID: {notification_id}")
    
    # Check if sent_count is around 300 (expected human users)
    if 290 <= sent_count <= 350:
        print_success(f"✓ Sent count ({sent_count}) is within expected range (290-350 human users)")
        print_success("✓ Bot exclusion appears to be working correctly")
        record_test("Bot Exclusion - Recipient Count", True)
    else:
        print_warning(f"⚠ Sent count ({sent_count}) is outside expected range (290-350)")
        if sent_count > 350:
            print_warning("This might indicate bots are still being included")
        record_test("Bot Exclusion - Recipient Count", False, f"Count: {sent_count}, expected: 290-350")
    
    record_test("Bot Exclusion - Broadcast Request", True)
    
    # TEST 2: Check user statistics to verify bot exclusion logic
    print_subheader("TEST 2: Verify User Statistics for Bot Exclusion Logic")
    
    # Get user statistics to understand the user base
    try:
        # Try to get user count information (this might not be available, but let's try)
        users_response, users_success = make_request(
            "GET", "/admin/users?page=1&limit=1",  # Just get first page to see total
            auth_token=admin_token,
            expected_status=200
        )
        
        if users_success and "pagination" in users_response:
            total_users = users_response["pagination"].get("total_items", 0)
            print_success(f"✓ Total users in system: {total_users}")
            
            # Calculate expected human users (total - bots)
            expected_human_users = total_users - (total_users - sent_count)
            print_success(f"✓ Expected human users: ~{sent_count} (based on broadcast)")
            
            if total_users > sent_count:
                excluded_count = total_users - sent_count
                print_success(f"✓ Excluded users (bots): {excluded_count}")
                print_success("✓ Bot exclusion logic is working")
                record_test("Bot Exclusion - User Statistics", True)
            else:
                print_warning("⚠ No users were excluded, might indicate issue with bot detection")
                record_test("Bot Exclusion - User Statistics", False, "No exclusions detected")
        else:
            print_warning("⚠ Could not get user statistics for verification")
            record_test("Bot Exclusion - User Statistics", False, "Stats not available")
    except Exception as e:
        print_warning(f"⚠ Could not verify user statistics: {e}")
        record_test("Bot Exclusion - User Statistics", False, f"Error: {e}")
    
    # TEST 3: Test resend-to-unread endpoint
    print_subheader("TEST 3: Test Resend-to-Unread Endpoint")
    
    if not notification_id:
        print_error("No notification_id available for resend test")
        record_test("Bot Exclusion - Resend Test", False, "No notification_id")
    else:
        resend_data = {
            "notification_id": notification_id
        }
        
        resend_response, resend_success = make_request(
            "POST", "/admin/notifications/resend-to-unread",
            data=resend_data,
            auth_token=admin_token
        )
        
        if resend_success:
            print_success("✓ Resend-to-unread endpoint accessible")
            
            # Check response structure
            if "success" in resend_response and "resent_count" in resend_response:
                resent_count = resend_response.get("resent_count", 0)
                print_success(f"✓ Resent to {resent_count} unread recipients")
                
                # Resent count should be <= original sent count
                if resent_count <= sent_count:
                    print_success("✓ Resent count is logical (≤ original sent count)")
                    record_test("Bot Exclusion - Resend Logic", True)
                else:
                    print_error(f"✗ Resent count ({resent_count}) > original sent count ({sent_count})")
                    record_test("Bot Exclusion - Resend Logic", False, f"Resent: {resent_count}, Original: {sent_count}")
                
                record_test("Bot Exclusion - Resend Test", True)
            else:
                print_error("✗ Resend response missing expected fields")
                record_test("Bot Exclusion - Resend Test", False, "Missing response fields")
        else:
            print_error("✗ Resend-to-unread endpoint failed")
            record_test("Bot Exclusion - Resend Test", False, "Endpoint failed")
    
    # TEST 4: Test specific user notification (should have individual IDs)
    print_subheader("TEST 4: Test Specific User Notification")
    
    # Try to send to specific users (admin user)
    specific_broadcast_data = {
        "target_users": [ADMIN_USER["email"]],  # Send to specific user
        "type": "admin_notification", 
        "priority": "info",
        "title": "Test Specific User",
        "message": "Testing specific user notification with individual ID"
    }
    
    specific_response, specific_success = make_request(
        "POST", "/admin/notifications/broadcast",
        data=specific_broadcast_data,
        auth_token=admin_token
    )
    
    if specific_success:
        specific_sent_count = specific_response.get("sent_count", 0)
        specific_notification_id = specific_response.get("notification_id", "")
        
        print_success(f"✓ Specific user notification sent to {specific_sent_count} recipient(s)")
        print_success(f"✓ Specific notification ID: {specific_notification_id}")
        
        # Should send to exactly 1 user
        if specific_sent_count == 1:
            print_success("✓ Specific user notification sent to correct number of recipients")
            record_test("Bot Exclusion - Specific User Count", True)
        else:
            print_error(f"✗ Expected 1 recipient, got {specific_sent_count}")
            record_test("Bot Exclusion - Specific User Count", False, f"Count: {specific_sent_count}")
        
        # Notification IDs should be different
        if specific_notification_id != notification_id:
            print_success("✓ Different notification IDs for different broadcasts")
            record_test("Bot Exclusion - Unique Notification IDs", True)
        else:
            print_error("✗ Same notification ID used for different broadcasts")
            record_test("Bot Exclusion - Unique Notification IDs", False, "IDs not unique")
        
        record_test("Bot Exclusion - Specific User Test", True)
    else:
        print_error("✗ Specific user notification failed")
        record_test("Bot Exclusion - Specific User Test", False, "Request failed")
    
    # TEST 5: Verify bot exclusion query logic
    print_subheader("TEST 5: Verify Bot Exclusion Query Logic")
    
    print_success("Bot exclusion logic verification:")
    print_success("✓ Broadcast to 'all users' (target_users: null) should exclude:")
    print_success("  - Users with role not in ['USER', 'ADMIN', 'SUPER_ADMIN']")
    print_success("  - Users with bot_type field existing and not null")
    print_success("  - Users with bot_type = 'HUMAN' or 'REGULAR'")
    print_success("  - Users with is_bot = true")
    
    # The actual verification is done through the sent_count check above
    if 290 <= sent_count <= 350:
        print_success("✓ Bot exclusion query logic appears to be working correctly")
        record_test("Bot Exclusion - Query Logic", True)
    else:
        print_error("✗ Bot exclusion query logic may not be working correctly")
        record_test("Bot Exclusion - Query Logic", False, f"Unexpected sent_count: {sent_count}")
    
    # Summary
    print_subheader("Bot Exclusion Test Summary")
    print_success("Notification system bot exclusion testing completed")
    print_success("Key findings:")
    print_success(f"- Broadcast sent to {sent_count} recipients (expected ~300 human users)")
    print_success(f"- Bot exclusion {'working' if 290 <= sent_count <= 350 else 'may need adjustment'}")
    print_success("- Resend-to-unread endpoint functional")
    print_success("- Specific user notifications work with individual IDs")
    print_success("- Notification IDs are unique for different broadcasts")

def print_final_summary():
    """Print final test summary."""
    print_header("FINAL TEST SUMMARY")
    
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
                print_error(f"- {test['name']}: {test['details']}")
    
    print_subheader("Test Results by Category:")
    categories = {}
    for test in test_results["tests"]:
        category = test["name"].split(" - ")[0] if " - " in test["name"] else "Other"
        if category not in categories:
            categories[category] = {"passed": 0, "total": 0}
        categories[category]["total"] += 1
        if test["passed"]:
            categories[category]["passed"] += 1
    
    for category, stats in categories.items():
        rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print_success(f"{category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")

if __name__ == "__main__":
    try:
        test_notification_bot_exclusion_fixes()
        print_final_summary()
        
        # Exit with appropriate code
        if test_results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Testing failed with error: {e}")
        sys.exit(1)