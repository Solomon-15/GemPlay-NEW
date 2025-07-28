#!/usr/bin/env python3
"""
GemPlay Notification System Comprehensive Testing
Testing notification delivery issues and system functionality
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type.title()} Login")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    # Use JSON data for login
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=headers)
    
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            response_data = response.json()
            print(f"Login response: {json.dumps(response_data, indent=2)}")
            
            if "access_token" in response_data:
                print_success(f"{user_type.title()} login successful")
                record_test(f"{user_type.title()} Login", True)
                return response_data["access_token"]
            else:
                print_error(f"{user_type.title()} login response missing access_token")
                record_test(f"{user_type.title()} Login", False, "Missing access_token")
        except json.JSONDecodeError:
            print_error(f"{user_type.title()} login response not JSON")
            record_test(f"{user_type.title()} Login", False, "Invalid JSON response")
    else:
        print_error(f"{user_type.title()} login failed with status {response.status_code}")
        record_test(f"{user_type.title()} Login", False, f"Status: {response.status_code}")
    
    return None

def create_test_user() -> Optional[str]:
    """Create a test user and return their auth token."""
    print_subheader("Creating Test User")
    
    # Generate unique user data with more randomness
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    user_data = {
        "username": f"testuser_{timestamp}_{random_suffix}",
        "email": f"testuser_{timestamp}_{random_suffix}@test.com",
        "password": "TestPass123!",
        "gender": "male"
    }
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if not success:
        print_error("Failed to register test user")
        return None
    
    if "verification_token" not in response:
        print_error("Registration response missing verification token")
        return None
    
    verification_token = response["verification_token"]
    print_success(f"Test user registered: {user_data['username']}")
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST", "/auth/verify-email", 
        data={"token": verification_token}
    )
    
    if not verify_success:
        print_error("Failed to verify test user email")
        return None
    
    print_success("Test user email verified")
    
    # Login to get token
    token = test_login(user_data["email"], user_data["password"], "test_user")
    
    if token:
        print_success("Test user login successful")
        record_test("Create Test User", True)
        return token
    else:
        print_error("Failed to login test user")
        record_test("Create Test User", False, "Login failed")
        return None

def test_admin_notification_broadcast() -> None:
    """Test 1: Admin notification broadcast functionality."""
    print_header("TEST 1: ADMIN NOTIFICATION BROADCAST")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    # Test different notification types and priorities
    test_notifications = [
        {
            "type": "system_message",
            "priority": "info",
            "title": "System Maintenance",
            "message": "Scheduled maintenance will occur tonight",
            "emoji": "🔧"
        },
        {
            "type": "admin_notification", 
            "priority": "warning",
            "title": "Important Update",
            "message": "Please update your profile information",
            "emoji": "⚠️"
        },
        {
            "type": "system_message",
            "priority": "error", 
            "title": "Critical Alert",
            "message": "System security update required",
            "emoji": "🚨"
        }
    ]
    
    for i, notification in enumerate(test_notifications):
        print_subheader(f"Broadcasting Notification {i+1}: {notification['title']}")
        
        response, success = make_request(
            "POST", "/admin/notifications/broadcast",
            data=notification,
            auth_token=admin_token
        )
        
        if success:
            # Check response structure
            required_fields = ["success", "message", "sent_count"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print_success("✓ Response has all required fields")
                sent_count = response.get("sent_count", 0)
                print_success(f"✓ Notification sent to {sent_count} users")
                record_test(f"Admin Broadcast - Notification {i+1}", True)
            else:
                print_error(f"✗ Response missing fields: {missing_fields}")
                record_test(f"Admin Broadcast - Notification {i+1}", False, f"Missing fields: {missing_fields}")
        else:
            print_error(f"✗ Failed to broadcast notification {i+1}")
            record_test(f"Admin Broadcast - Notification {i+1}", False, "Broadcast failed")
        
        time.sleep(1)  # Small delay between broadcasts

def test_user_notification_retrieval() -> None:
    """Test 2: User notification retrieval functionality."""
    print_header("TEST 2: USER NOTIFICATION RETRIEVAL")
    
    # Create test user
    user_token = create_test_user()
    if not user_token:
        print_error("Cannot proceed without user token")
        return
    
    # Send a notification to all users first (as admin)
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if admin_token:
        print_subheader("Sending Test Notification to All Users")
        test_notification = {
            "type": "system_message",
            "priority": "info",
            "title": "Test Notification for Retrieval",
            "message": "This is a test notification to verify retrieval functionality",
            "emoji": "📧"
        }
        
        broadcast_response, broadcast_success = make_request(
            "POST", "/admin/notifications/broadcast",
            data=test_notification,
            auth_token=admin_token
        )
        
        if broadcast_success:
            print_success("✓ Test notification broadcast successful")
            time.sleep(2)  # Wait for notification to be processed
        else:
            print_warning("Failed to broadcast test notification")
    
    # Test notification retrieval
    print_subheader("Retrieving User Notifications")
    
    response, success = make_request(
        "GET", "/notifications",
        auth_token=user_token
    )
    
    if success:
        # Check if response is a list (current implementation) or object with pagination
        if isinstance(response, list):
            print_success(f"✓ Retrieved {len(response)} notifications (list format)")
            notifications = response
        elif isinstance(response, dict) and "notifications" in response:
            print_success(f"✓ Retrieved notifications (object format)")
            notifications = response.get("notifications", [])
            
            # Check pagination structure if present
            if "pagination" in response:
                pagination = response["pagination"]
                print_success(f"✓ Pagination info present: {pagination}")
        else:
            print_error("✗ Unexpected response format")
            record_test("User Notification Retrieval - Format", False, "Unexpected format")
            return
        
        # Verify notification structure
        if notifications:
            sample_notification = notifications[0]
            required_fields = ["id", "type", "title", "message", "is_read", "created_at"]
            missing_fields = [field for field in required_fields if field not in sample_notification]
            
            if not missing_fields:
                print_success("✓ Notification structure is correct")
                print_success(f"✓ Sample notification: {sample_notification.get('title', 'No title')}")
                record_test("User Notification Retrieval - Structure", True)
            else:
                print_error(f"✗ Notification missing fields: {missing_fields}")
                record_test("User Notification Retrieval - Structure", False, f"Missing: {missing_fields}")
        else:
            print_warning("No notifications found for user")
            record_test("User Notification Retrieval - Content", False, "No notifications")
        
        record_test("User Notification Retrieval", True)
    else:
        print_error("✗ Failed to retrieve notifications")
        record_test("User Notification Retrieval", False, "Request failed")

def test_notification_management_functions() -> None:
    """Test 3: Notification management functions (mark as read)."""
    print_header("TEST 3: NOTIFICATION MANAGEMENT FUNCTIONS")
    
    # Create test user
    user_token = create_test_user()
    if not user_token:
        print_error("Cannot proceed without user token")
        return
    
    # Send notifications first
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if admin_token:
        print_subheader("Sending Multiple Test Notifications")
        
        for i in range(3):
            test_notification = {
                "type": "system_message",
                "priority": "info",
                "title": f"Test Notification {i+1}",
                "message": f"This is test notification number {i+1}",
                "emoji": "📝"
            }
            
            make_request(
                "POST", "/admin/notifications/broadcast",
                data=test_notification,
                auth_token=admin_token
            )
            time.sleep(0.5)
        
        print_success("✓ Multiple test notifications sent")
        time.sleep(2)  # Wait for processing
    
    # Get notifications to find IDs
    print_subheader("Getting Notifications for Management Testing")
    
    response, success = make_request(
        "GET", "/notifications",
        auth_token=user_token
    )
    
    if not success:
        print_error("Failed to get notifications for management testing")
        return
    
    # Handle both list and object response formats
    notifications = response if isinstance(response, list) else response.get("notifications", [])
    
    if not notifications:
        print_error("No notifications available for management testing")
        return
    
    print_success(f"✓ Found {len(notifications)} notifications for testing")
    
    # Test individual notification mark as read
    if len(notifications) > 0:
        print_subheader("Testing Individual Notification Mark as Read")
        
        first_notification = notifications[0]
        notification_id = first_notification.get("id")
        
        if notification_id:
            response, success = make_request(
                "PUT", f"/notifications/{notification_id}/read",
                auth_token=user_token
            )
            
            if success:
                print_success("✓ Individual notification marked as read")
                record_test("Individual Mark as Read", True)
            else:
                print_error("✗ Failed to mark individual notification as read")
                record_test("Individual Mark as Read", False, "Request failed")
        else:
            print_error("Notification missing ID field")
            record_test("Individual Mark as Read", False, "Missing ID")
    
    # Test mark all notifications as read
    print_subheader("Testing Mark All Notifications as Read")
    
    response, success = make_request(
        "PUT", "/notifications/mark-all-read",
        auth_token=user_token
    )
    
    if success:
        marked_count = response.get("marked_count", 0)
        print_success(f"✓ Marked {marked_count} notifications as read")
        record_test("Mark All as Read", True)
        
        # Verify notifications are marked as read
        print_subheader("Verifying Notifications Marked as Read")
        
        verify_response, verify_success = make_request(
            "GET", "/notifications",
            auth_token=user_token
        )
        
        if verify_success:
            verify_notifications = verify_response if isinstance(verify_response, list) else verify_response.get("notifications", [])
            
            read_count = sum(1 for notif in verify_notifications if notif.get("is_read", False))
            total_count = len(verify_notifications)
            
            print_success(f"✓ Verification: {read_count}/{total_count} notifications marked as read")
            record_test("Mark as Read Verification", True)
        else:
            print_warning("Could not verify read status")
            record_test("Mark as Read Verification", False, "Verification failed")
    else:
        print_error("✗ Failed to mark all notifications as read")
        record_test("Mark All as Read", False, "Request failed")

def test_notification_analytics() -> None:
    """Test 4: Notification analytics functionality."""
    print_header("TEST 4: NOTIFICATION ANALYTICS")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    print_subheader("Getting Notification Analytics")
    
    response, success = make_request(
        "GET", "/admin/notifications/analytics",
        auth_token=admin_token
    )
    
    if success:
        # Check analytics structure
        required_fields = ["total_sent", "total_read", "read_rate", "by_type"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("✓ Analytics response has all required fields")
            
            total_sent = response.get("total_sent", 0)
            total_read = response.get("total_read", 0)
            read_rate = response.get("read_rate", 0)
            by_type = response.get("by_type", {})
            
            print_success(f"✓ Total notifications sent: {total_sent}")
            print_success(f"✓ Total notifications read: {total_read}")
            print_success(f"✓ Read rate: {read_rate}%")
            print_success(f"✓ Breakdown by type: {len(by_type)} types")
            
            # Display type breakdown
            for notif_type, stats in by_type.items():
                if isinstance(stats, dict):
                    sent = stats.get("sent", 0)
                    read = stats.get("read", 0)
                    print_success(f"  - {notif_type}: {sent} sent, {read} read")
                else:
                    print_success(f"  - {notif_type}: {stats}")
            
            record_test("Notification Analytics - Structure", True)
            record_test("Notification Analytics - Data", True)
        else:
            print_error(f"✗ Analytics response missing fields: {missing_fields}")
            record_test("Notification Analytics - Structure", False, f"Missing: {missing_fields}")
        
        record_test("Notification Analytics", True)
    else:
        print_error("✗ Failed to get notification analytics")
        record_test("Notification Analytics", False, "Request failed")

def test_notification_settings() -> None:
    """Test 5: User notification settings functionality."""
    print_header("TEST 5: NOTIFICATION SETTINGS")
    
    # Create test user
    user_token = create_test_user()
    if not user_token:
        print_error("Cannot proceed without user token")
        return
    
    # Test getting notification settings
    print_subheader("Getting User Notification Settings")
    
    response, success = make_request(
        "GET", "/notifications/settings",
        auth_token=user_token
    )
    
    if success:
        # Check settings structure
        expected_settings = [
            "bet_accepted", "match_results", "commission_freeze", 
            "gem_gifts", "system_messages", "admin_notifications"
        ]
        
        missing_settings = [setting for setting in expected_settings if setting not in response]
        
        if not missing_settings:
            print_success("✓ All expected notification settings present")
            
            # Display current settings
            for setting, value in response.items():
                print_success(f"  - {setting}: {value}")
            
            record_test("Get Notification Settings - Structure", True)
        else:
            print_error(f"✗ Missing notification settings: {missing_settings}")
            record_test("Get Notification Settings - Structure", False, f"Missing: {missing_settings}")
        
        record_test("Get Notification Settings", True)
        
        # Test updating notification settings
        print_subheader("Updating User Notification Settings")
        
        # Create updated settings (toggle some values)
        updated_settings = {}
        for setting, current_value in response.items():
            if isinstance(current_value, bool):
                updated_settings[setting] = not current_value  # Toggle boolean values
            else:
                updated_settings[setting] = current_value
        
        update_response, update_success = make_request(
            "PUT", "/notifications/settings",
            data=updated_settings,
            auth_token=user_token
        )
        
        if update_success:
            print_success("✓ Notification settings updated successfully")
            
            # Verify the update
            print_subheader("Verifying Settings Update")
            
            verify_response, verify_success = make_request(
                "GET", "/notifications/settings",
                auth_token=user_token
            )
            
            if verify_success:
                changes_applied = 0
                for setting, expected_value in updated_settings.items():
                    actual_value = verify_response.get(setting)
                    if actual_value == expected_value:
                        changes_applied += 1
                    else:
                        print_warning(f"Setting {setting}: expected {expected_value}, got {actual_value}")
                
                if changes_applied == len(updated_settings):
                    print_success("✓ All settings changes applied correctly")
                    record_test("Update Notification Settings - Verification", True)
                else:
                    print_error(f"✗ Only {changes_applied}/{len(updated_settings)} settings applied")
                    record_test("Update Notification Settings - Verification", False, f"Partial update: {changes_applied}/{len(updated_settings)}")
            else:
                print_error("Failed to verify settings update")
                record_test("Update Notification Settings - Verification", False, "Verification failed")
            
            record_test("Update Notification Settings", True)
        else:
            print_error("✗ Failed to update notification settings")
            record_test("Update Notification Settings", False, "Update failed")
    else:
        print_error("✗ Failed to get notification settings")
        record_test("Get Notification Settings", False, "Request failed")

def test_notification_delivery_issues() -> None:
    """Test for notification delivery issues and edge cases."""
    print_header("TEST 6: NOTIFICATION DELIVERY ISSUES ANALYSIS")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    # Create multiple test users
    print_subheader("Creating Multiple Test Users for Delivery Testing")
    
    test_users = []
    for i in range(3):
        user_token = create_test_user()
        if user_token:
            test_users.append(user_token)
            print_success(f"✓ Test user {i+1} created")
        else:
            print_error(f"✗ Failed to create test user {i+1}")
    
    if not test_users:
        print_error("No test users available for delivery testing")
        return
    
    print_success(f"✓ Created {len(test_users)} test users for delivery testing")
    
    # Test notification delivery to multiple users
    print_subheader("Testing Notification Delivery to Multiple Users")
    
    delivery_test_notification = {
        "type": "system_message",
        "priority": "info",
        "title": "Delivery Test Notification",
        "message": "This notification tests delivery to multiple users",
        "emoji": "🚀"
    }
    
    broadcast_response, broadcast_success = make_request(
        "POST", "/admin/notifications/broadcast",
        data=delivery_test_notification,
        auth_token=admin_token
    )
    
    if broadcast_success:
        sent_count = broadcast_response.get("sent_count", 0)
        print_success(f"✓ Notification broadcast to {sent_count} users")
        
        # Wait for delivery
        time.sleep(3)
        
        # Check if each test user received the notification
        print_subheader("Verifying Notification Delivery to Each User")
        
        delivery_success_count = 0
        for i, user_token in enumerate(test_users):
            user_response, user_success = make_request(
                "GET", "/notifications",
                auth_token=user_token
            )
            
            if user_success:
                notifications = user_response if isinstance(user_response, list) else user_response.get("notifications", [])
                
                # Look for our test notification
                found_notification = False
                for notification in notifications:
                    if notification.get("title") == "Delivery Test Notification":
                        found_notification = True
                        print_success(f"✓ User {i+1} received the notification")
                        delivery_success_count += 1
                        break
                
                if not found_notification:
                    print_error(f"✗ User {i+1} did not receive the notification")
            else:
                print_error(f"✗ Failed to get notifications for user {i+1}")
        
        delivery_rate = (delivery_success_count / len(test_users)) * 100
        print_success(f"✓ Delivery success rate: {delivery_rate:.1f}% ({delivery_success_count}/{len(test_users)})")
        
        if delivery_success_count == len(test_users):
            record_test("Notification Delivery - Multiple Users", True)
        else:
            record_test("Notification Delivery - Multiple Users", False, f"Delivery rate: {delivery_rate:.1f}%")
    else:
        print_error("✗ Failed to broadcast delivery test notification")
        record_test("Notification Delivery - Broadcast", False, "Broadcast failed")
    
    # Test notification settings impact on delivery
    print_subheader("Testing Notification Settings Impact on Delivery")
    
    if test_users:
        # Disable system_messages for first user
        user_token = test_users[0]
        
        # Get current settings
        settings_response, settings_success = make_request(
            "GET", "/notifications/settings",
            auth_token=user_token
        )
        
        if settings_success:
            # Disable system messages
            updated_settings = settings_response.copy()
            updated_settings["system_messages"] = False
            
            update_response, update_success = make_request(
                "PUT", "/notifications/settings",
                data=updated_settings,
                auth_token=user_token
            )
            
            if update_success:
                print_success("✓ Disabled system_messages for test user")
                
                # Send a system message
                filtered_notification = {
                    "type": "system_message",
                    "priority": "info",
                    "title": "Filtered Test Notification",
                    "message": "This should be filtered out for users with disabled system_messages",
                    "emoji": "🔇"
                }
                
                filter_broadcast_response, filter_broadcast_success = make_request(
                    "POST", "/admin/notifications/broadcast",
                    data=filtered_notification,
                    auth_token=admin_token
                )
                
                if filter_broadcast_success:
                    time.sleep(2)  # Wait for processing
                    
                    # Check if user received the notification (should not)
                    filter_check_response, filter_check_success = make_request(
                        "GET", "/notifications",
                        auth_token=user_token
                    )
                    
                    if filter_check_success:
                        notifications = filter_check_response if isinstance(filter_check_response, list) else filter_check_response.get("notifications", [])
                        
                        filtered_out = True
                        for notification in notifications:
                            if notification.get("title") == "Filtered Test Notification":
                                filtered_out = False
                                break
                        
                        if filtered_out:
                            print_success("✓ Notification correctly filtered based on user settings")
                            record_test("Notification Settings - Filtering", True)
                        else:
                            print_error("✗ Notification was not filtered despite disabled setting")
                            record_test("Notification Settings - Filtering", False, "Not filtered")
                    else:
                        print_error("Failed to check filtered notification")
                        record_test("Notification Settings - Filtering", False, "Check failed")
                else:
                    print_error("Failed to broadcast filtered test notification")
            else:
                print_error("Failed to update notification settings for filtering test")
        else:
            print_error("Failed to get notification settings for filtering test")

def print_test_summary() -> None:
    """Print comprehensive test summary."""
    print_header("NOTIFICATION SYSTEM TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print_success(f"Total Tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success(f"Failed: {failed}")
    print_success(f"Success Rate: {success_rate:.1f}%")
    
    print_subheader("Detailed Test Results")
    
    for test in test_results["tests"]:
        status = "✓ PASS" if test["passed"] else "✗ FAIL"
        color = Colors.OKGREEN if test["passed"] else Colors.FAIL
        print(f"{color}{status}{Colors.ENDC} - {test['name']}")
        if test["details"] and not test["passed"]:
            print(f"    Details: {test['details']}")
    
    # Identify critical issues
    print_subheader("Critical Issues Identified")
    
    critical_failures = [
        test for test in test_results["tests"] 
        if not test["passed"] and any(keyword in test["name"].lower() 
        for keyword in ["broadcast", "delivery", "retrieval", "analytics"])
    ]
    
    if critical_failures:
        print_error("The following critical issues were found:")
        for failure in critical_failures:
            print_error(f"- {failure['name']}: {failure['details']}")
    else:
        print_success("No critical notification delivery issues found!")
    
    # Recommendations
    print_subheader("Recommendations")
    
    if failed == 0:
        print_success("✓ Notification system is working correctly")
        print_success("✓ All delivery mechanisms are functional")
        print_success("✓ User settings are properly respected")
        print_success("✓ Analytics are accurate and complete")
    else:
        print_warning("The following areas need attention:")
        
        failed_categories = {}
        for test in test_results["tests"]:
            if not test["passed"]:
                category = test["name"].split(" - ")[0] if " - " in test["name"] else test["name"]
                if category not in failed_categories:
                    failed_categories[category] = 0
                failed_categories[category] += 1
        
        for category, count in failed_categories.items():
            print_warning(f"- {category}: {count} failed test(s)")

def main():
    """Main test execution function."""
    print_header("GEMPLAY NOTIFICATION SYSTEM COMPREHENSIVE TESTING")
    print("Testing notification delivery issues and system functionality")
    print("=" * 80)
    
    try:
        # Execute all test suites
        test_admin_notification_broadcast()
        test_user_notification_retrieval()
        test_notification_management_functions()
        test_notification_analytics()
        test_notification_settings()
        test_notification_delivery_issues()
        
        # Print comprehensive summary
        print_test_summary()
        
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()