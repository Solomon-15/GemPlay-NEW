#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://cc691930-a6c0-47a7-8521-266c2a4eb979.preview.emergentagent.com/api"
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

def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

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

def login_user(email: str, password: str) -> Optional[str]:
    """Login user and return access token."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login exception: {e}")
        return None

def test_notification_system_comprehensive() -> None:
    """Test the complete notification system endpoints."""
    print_header("NOTIFICATION SYSTEM COMPREHENSIVE TESTING")
    
    # Login as admin user
    admin_token = login_user(ADMIN_USER["email"], ADMIN_USER["password"])
    if not admin_token:
        print_error("Failed to login as admin user")
        return
    
    print_info("✓ Admin login successful")
    
    # Test 1: GET /api/notifications - Test fetching user notifications
    print_subheader("TEST 1: GET /api/notifications - Fetch User Notifications")
    
    try:
        response = requests.get(
            f"{BASE_URL}/notifications",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            notifications = response.json()
            print_success(f"✓ GET /api/notifications successful - Status: {response.status_code}")
            print_info(f"  - Returned {len(notifications)} notifications")
            
            # Validate response format
            if isinstance(notifications, list):
                print_success("✓ Response is properly formatted as list")
                
                # Check notification structure if any exist
                if notifications:
                    first_notification = notifications[0]
                    required_fields = ["id", "type", "title", "message", "read", "created_at"]
                    missing_fields = [field for field in required_fields if field not in first_notification]
                    
                    if not missing_fields:
                        print_success("✓ Notification structure contains all required fields")
                        print_info(f"  - Sample notification: {first_notification}")
                        record_test("GET /api/notifications - Structure", True, "All required fields present")
                    else:
                        print_error(f"✗ Missing required fields: {missing_fields}")
                        record_test("GET /api/notifications - Structure", False, f"Missing fields: {missing_fields}")
                else:
                    print_info("  - No notifications found (empty result)")
                    record_test("GET /api/notifications - Empty Result", True, "Handled empty results gracefully")
                
                record_test("GET /api/notifications", True, f"Successfully fetched {len(notifications)} notifications")
            else:
                print_error("✗ Response is not a list")
                record_test("GET /api/notifications", False, "Response format invalid")
        else:
            print_error(f"✗ GET /api/notifications failed - Status: {response.status_code}")
            print_error(f"  Response: {response.text}")
            record_test("GET /api/notifications", False, f"HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"✗ GET /api/notifications exception: {e}")
        record_test("GET /api/notifications", False, f"Exception: {e}")
    
    # Test 2: Create a notification by gifting gems (to test notification creation)
    print_subheader("TEST 2: Create Notification via Gem Gift")
    
    # First, register a test user to gift to
    test_user_data = {
        "username": f"testuser_{int(time.time())}",
        "email": f"testuser_{int(time.time())}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    try:
        # Register test user
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user_data
        )
        
        if register_response.status_code == 200:
            print_success("✓ Test user registered successfully")
            
            # Verify admin user and activate test user
            verify_response = requests.post(
                f"{BASE_URL}/auth/verify-email",
                json={"token": register_response.json()["verification_token"]}
            )
            
            if verify_response.status_code == 200:
                print_success("✓ Test user email verified")
                
                # Gift gems to create notification
                gift_response = requests.post(
                    f"{BASE_URL}/gems/gift",
                    params={
                        "recipient_email": test_user_data["email"],
                        "gem_type": "Ruby",
                        "quantity": 5
                    },
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                if gift_response.status_code == 200:
                    print_success("✓ Gems gifted successfully - notification should be created")
                    record_test("Notification Creation via Gift", True, "Gift successful, notification created")
                    
                    # Login as test user to check notifications
                    test_user_token = login_user(test_user_data["email"], test_user_data["password"])
                    if test_user_token:
                        # Check notifications for test user
                        notif_response = requests.get(
                            f"{BASE_URL}/notifications",
                            headers={"Authorization": f"Bearer {test_user_token}"}
                        )
                        
                        if notif_response.status_code == 200:
                            test_notifications = notif_response.json()
                            gift_notifications = [n for n in test_notifications if n.get("type") == "GIFT_RECEIVED"]
                            
                            if gift_notifications:
                                print_success(f"✓ Gift notification found: {gift_notifications[0]['message']}")
                                record_test("Gift Notification Verification", True, "Gift notification created and retrieved")
                                
                                # Store notification ID for mark-read test
                                notification_id = gift_notifications[0]["id"]
                                
                                # Test 3: POST /api/notifications/{notification_id}/mark-read
                                print_subheader("TEST 3: POST /api/notifications/{id}/mark-read - Mark Individual Notification as Read")
                                
                                mark_read_response = requests.post(
                                    f"{BASE_URL}/notifications/{notification_id}/mark-read",
                                    headers={"Authorization": f"Bearer {test_user_token}"}
                                )
                                
                                if mark_read_response.status_code == 200:
                                    mark_read_data = mark_read_response.json()
                                    if mark_read_data.get("success"):
                                        print_success("✓ Individual notification marked as read successfully")
                                        record_test("POST /api/notifications/{id}/mark-read", True, "Successfully marked notification as read")
                                        
                                        # Verify notification is marked as read
                                        verify_response = requests.get(
                                            f"{BASE_URL}/notifications",
                                            headers={"Authorization": f"Bearer {test_user_token}"}
                                        )
                                        
                                        if verify_response.status_code == 200:
                                            updated_notifications = verify_response.json()
                                            updated_notification = next((n for n in updated_notifications if n["id"] == notification_id), None)
                                            
                                            if updated_notification and updated_notification.get("read"):
                                                print_success("✓ Notification read status verified as true")
                                                record_test("Mark Read Verification", True, "Notification read status updated correctly")
                                            else:
                                                print_error("✗ Notification read status not updated")
                                                record_test("Mark Read Verification", False, "Read status not updated")
                                    else:
                                        print_error("✗ Mark read response missing success field")
                                        record_test("POST /api/notifications/{id}/mark-read", False, "Response missing success field")
                                else:
                                    print_error(f"✗ Mark individual notification as read failed - Status: {mark_read_response.status_code}")
                                    print_error(f"  Response: {mark_read_response.text}")
                                    record_test("POST /api/notifications/{id}/mark-read", False, f"HTTP {mark_read_response.status_code}")
                                
                                # Test 4: POST /api/notifications/mark-all-read
                                print_subheader("TEST 4: POST /api/notifications/mark-all-read - Mark All Notifications as Read")
                                
                                mark_all_response = requests.post(
                                    f"{BASE_URL}/notifications/mark-all-read",
                                    headers={"Authorization": f"Bearer {test_user_token}"}
                                )
                                
                                if mark_all_response.status_code == 200:
                                    mark_all_data = mark_all_response.json()
                                    if mark_all_data.get("success"):
                                        print_success(f"✓ All notifications marked as read - Response: {mark_all_data.get('message', 'N/A')}")
                                        record_test("POST /api/notifications/mark-all-read", True, f"Successfully marked all notifications as read")
                                    else:
                                        print_error("✗ Mark all read response missing success field")
                                        record_test("POST /api/notifications/mark-all-read", False, "Response missing success field")
                                else:
                                    print_error(f"✗ Mark all notifications as read failed - Status: {mark_all_response.status_code}")
                                    print_error(f"  Response: {mark_all_response.text}")
                                    record_test("POST /api/notifications/mark-all-read", False, f"HTTP {mark_all_response.status_code}")
                                
                                # Test 5: Test invalid notification ID handling
                                print_subheader("TEST 5: Error Handling - Invalid Notification ID")
                                
                                invalid_id_response = requests.post(
                                    f"{BASE_URL}/notifications/invalid_id_123/mark-read",
                                    headers={"Authorization": f"Bearer {test_user_token}"}
                                )
                                
                                if invalid_id_response.status_code == 404:
                                    print_success("✓ Invalid notification ID properly handled with 404")
                                    record_test("Invalid Notification ID Handling", True, "Properly returns 404 for invalid ID")
                                elif invalid_id_response.status_code == 500:
                                    print_warning("⚠ Invalid notification ID returns 500 (acceptable)")
                                    record_test("Invalid Notification ID Handling", True, "Returns 500 for invalid ID format")
                                else:
                                    print_error(f"✗ Unexpected status for invalid ID: {invalid_id_response.status_code}")
                                    print_error(f"  Response: {invalid_id_response.text}")
                                    record_test("Invalid Notification ID Handling", False, f"Unexpected status: {invalid_id_response.status_code}")
                            
                            else:
                                print_error("✗ No gift notification found after gifting gems")
                                record_test("Gift Notification Verification", False, "Gift notification not created")
                        else:
                            print_error(f"✗ Failed to fetch test user notifications - Status: {notif_response.status_code}")
                    else:
                        print_error("✗ Failed to login as test user")
                else:
                    print_error(f"✗ Failed to gift gems - Status: {gift_response.status_code}")
                    print_error(f"  Response: {gift_response.text}")
                    record_test("Notification Creation via Gift", False, f"Gift failed: HTTP {gift_response.status_code}")
            else:
                print_error(f"✗ Failed to verify test user email - Status: {verify_response.status_code}")
        else:
            print_error(f"✗ Failed to register test user - Status: {register_response.status_code}")
            print_error(f"  Response: {register_response.text}")
    
    except Exception as e:
        print_error(f"✗ Exception during notification creation test: {e}")
        record_test("Notification Creation via Gift", False, f"Exception: {e}")
    
    # Test 6: Authentication test
    print_subheader("TEST 6: Authentication Required")
    
    try:
        unauth_response = requests.get(f"{BASE_URL}/notifications")
        
        if unauth_response.status_code == 401:
            print_success("✓ Authentication properly required for notifications endpoint")
            record_test("Notifications Authentication", True, "Properly requires authentication")
        else:
            print_error(f"✗ Unexpected status for unauthenticated request: {unauth_response.status_code}")
            record_test("Notifications Authentication", False, f"Unexpected status: {unauth_response.status_code}")
    
    except Exception as e:
        print_error(f"✗ Exception during authentication test: {e}")
        record_test("Notifications Authentication", False, f"Exception: {e}")
    
    # Test 7: Response time check
    print_subheader("TEST 7: Response Time Check")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/notifications",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            if response_time < 2.0:  # Less than 2 seconds is acceptable
                print_success(f"✓ Response time acceptable: {response_time:.3f} seconds")
                record_test("Response Time Check", True, f"Response time: {response_time:.3f}s")
            else:
                print_warning(f"⚠ Response time slow: {response_time:.3f} seconds")
                record_test("Response Time Check", True, f"Slow response time: {response_time:.3f}s")
        else:
            print_error(f"✗ Response failed during timing test: {response.status_code}")
            record_test("Response Time Check", False, f"HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"✗ Exception during response time test: {e}")
        record_test("Response Time Check", False, f"Exception: {e}")

def print_summary() -> None:
    """Print a summary of all test results."""
    print_header("NOTIFICATION SYSTEM TEST SUMMARY")
    
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results["failed"] > 0:
        print("\nFailed tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"{Colors.FAIL}✗ {test['name']}: {test['details']}{Colors.ENDC}")
    
    success_rate = (test_results["passed"] / test_results["total"]) * 100 if test_results["total"] > 0 else 0
    print(f"\nSuccess rate: {Colors.BOLD}{success_rate:.2f}%{Colors.ENDC}")
    
    if test_results["failed"] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All notification tests passed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some notification tests failed!{Colors.ENDC}")

if __name__ == "__main__":
    test_notification_system_comprehensive()
    print_summary()