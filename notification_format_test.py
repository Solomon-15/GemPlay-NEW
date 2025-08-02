#!/usr/bin/env python3
"""
GemPlay API Notification Format Testing
Focus: Testing new notification formats for match results
Russian Review Requirements: Test new notification message formats with commission field
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
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
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
    """Test user login and return token."""
    print_subheader(f"Testing Login for {user_type}: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"{user_type.capitalize()} logged in successfully")
        record_test(f"Login - {user_type}", True)
        return response["access_token"]
    else:
        print_error(f"{user_type.capitalize()} login failed: {response}")
        record_test(f"Login - {user_type}", False, f"Login failed: {response}")
        return None

def test_user_registration(username: str, email: str, password: str) -> Tuple[Optional[str], str]:
    """Test user registration and return verification token."""
    print_subheader(f"Testing User Registration for {username}")
    
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "gender": "male"
    }
    
    response, success = make_request("POST", "/auth/register", data=user_data)
    
    if success:
        if "message" in response and "user_id" in response and "verification_token" in response:
            print_success(f"User registered successfully with ID: {response['user_id']}")
            print_success(f"Verification token: {response['verification_token']}")
            record_test(f"User Registration - {username}", True)
            return response["verification_token"], response["user_id"]
        else:
            print_error(f"User registration response missing expected fields: {response}")
            record_test(f"User Registration - {username}", False, "Response missing expected fields")
    else:
        record_test(f"User Registration - {username}", False, "Request failed")
    
    return None, None

def test_email_verification(token: str, username: str) -> bool:
    """Test email verification."""
    print_subheader(f"Testing Email Verification for {username}")
    
    if not token:
        print_error("No verification token available")
        record_test(f"Email Verification - {username}", False, "No token available")
        return False
    
    response, success = make_request("POST", "/auth/verify-email", data={"token": token})
    
    if success:
        if "message" in response and "verified" in response["message"].lower():
            print_success("Email verified successfully")
            record_test(f"Email Verification - {username}", True)
            return True
        else:
            print_error(f"Email verification response unexpected: {response}")
            record_test(f"Email Verification - {username}", False, f"Unexpected response: {response}")
    else:
        record_test(f"Email Verification - {username}", False, "Request failed")
    
    return False

def buy_gems_for_user(token: str, gem_type: str, quantity: int) -> bool:
    """Buy gems for a user."""
    print_subheader(f"Buying {quantity} {gem_type} gems")
    
    response, success = make_request(
        "POST", f"/gems/buy?gem_type={gem_type}&quantity={quantity}",
        auth_token=token
    )
    
    if success:
        print_success(f"Successfully bought {quantity} {gem_type} gems")
        return True
    else:
        print_error(f"Failed to buy gems: {response}")
        return False

def test_notification_formats() -> None:
    """Test new notification formats for match results."""
    print_header("NOTIFICATION FORMAT TESTING - RUSSIAN REVIEW")
    
    # Step 1: Admin login
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with notification test")
        record_test("Notification Format - Admin Login", False, "Admin login failed")
        return
    
    # Step 2: Create two test users
    print_subheader("Step 2: Create Test Users")
    
    # Generate unique usernames and emails
    timestamp = int(time.time())
    player1_username = f"player1_{timestamp}"
    player1_email = f"player1_{timestamp}@test.com"
    player2_username = f"player2_{timestamp}"
    player2_email = f"player2_{timestamp}@test.com"
    
    # Register Player 1
    token1, user_id1 = test_user_registration(player1_username, player1_email, "Test123!")
    if not token1:
        print_error("Failed to register Player 1")
        return
    
    # Verify Player 1 email
    if not test_email_verification(token1, player1_username):
        print_error("Failed to verify Player 1 email")
        return
    
    # Register Player 2
    token2, user_id2 = test_user_registration(player2_username, player2_email, "Test123!")
    if not token2:
        print_error("Failed to register Player 2")
        return
    
    # Verify Player 2 email
    if not test_email_verification(token2, player2_username):
        print_error("Failed to verify Player 2 email")
        return
    
    # Step 3: Login both players
    print_subheader("Step 3: Login Test Players")
    
    player1_token = test_login(player1_email, "Test123!", "Player 1")
    if not player1_token:
        print_error("Failed to login Player 1")
        return
    
    player2_token = test_login(player2_email, "Test123!", "Player 2")
    if not player2_token:
        print_error("Failed to login Player 2")
        return
    
    # Step 4: Add balance to both players
    print_subheader("Step 4: Add Balance to Players")
    
    # Add balance to Player 1
    balance_response1, balance_success1 = make_request(
        "POST", f"/admin/users/{user_id1}/add-balance",
        data={"amount": 100.0},
        auth_token=admin_token
    )
    
    if balance_success1:
        print_success("Added $100 balance to Player 1")
    else:
        print_error("Failed to add balance to Player 1")
    
    # Add balance to Player 2
    balance_response2, balance_success2 = make_request(
        "POST", f"/admin/users/{user_id2}/add-balance",
        data={"amount": 100.0},
        auth_token=admin_token
    )
    
    if balance_success2:
        print_success("Added $100 balance to Player 2")
    else:
        print_error("Failed to add balance to Player 2")
    
    # Step 5: Buy gems for both players
    print_subheader("Step 5: Buy Gems for Players")
    
    # Player 1 buys gems
    if not buy_gems_for_user(player1_token, "Ruby", 20):
        print_error("Failed to buy gems for Player 1")
        return
    
    if not buy_gems_for_user(player1_token, "Emerald", 5):
        print_error("Failed to buy gems for Player 1")
        return
    
    # Player 2 buys gems
    if not buy_gems_for_user(player2_token, "Ruby", 20):
        print_error("Failed to buy gems for Player 2")
        return
    
    if not buy_gems_for_user(player2_token, "Emerald", 5):
        print_error("Failed to buy gems for Player 2")
        return
    
    # Step 6: Player 1 creates a game
    print_subheader("Step 6: Player 1 Creates Game")
    
    # Use gems worth $35 (15 Ruby + 2 Emerald = $15 + $20 = $35)
    bet_gems = {"Ruby": 15, "Emerald": 2}
    expected_bet_amount = 15 * 1.0 + 2 * 10.0  # $35
    expected_commission = expected_bet_amount * 0.03  # 3% = $1.05
    
    create_game_data = {
        "move": "rock",
        "bet_gems": bet_gems
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=player1_token
    )
    
    if not game_success:
        print_error("Failed to create game")
        record_test("Notification Format - Create Game", False, "Game creation failed")
        return
    
    game_id = game_response.get("game_id")
    if not game_id:
        print_error("Game creation response missing game_id")
        record_test("Notification Format - Create Game", False, "Missing game_id")
        return
    
    print_success(f"Game created with ID: {game_id}")
    print_success(f"Bet amount: ${expected_bet_amount}")
    print_success(f"Expected commission: ${expected_commission}")
    record_test("Notification Format - Create Game", True)
    
    # Step 7: Player 2 joins the game
    print_subheader("Step 7: Player 2 Joins Game")
    
    join_game_data = {
        "move": "paper",
        "gems": bet_gems  # Same gems as Player 1
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=player2_token
    )
    
    if not join_success:
        print_error("Failed to join game")
        record_test("Notification Format - Join Game", False, "Game join failed")
        return
    
    print_success("Player 2 successfully joined the game")
    print_success(f"Game status: {join_response.get('status', 'UNKNOWN')}")
    record_test("Notification Format - Join Game", True)
    
    # Step 8: Wait for game completion
    print_subheader("Step 8: Wait for Game Completion")
    
    print("Waiting for game to complete...")
    max_wait_time = 120  # 2 minutes
    wait_interval = 5    # Check every 5 seconds
    
    game_completed = False
    winner_id = None
    loser_id = None
    
    for i in range(max_wait_time // wait_interval):
        time.sleep(wait_interval)
        
        # Check game status
        status_response, status_success = make_request(
            "GET", f"/games/{game_id}/status",
            auth_token=admin_token,
            expected_status=200
        )
        
        if status_success:
            game_status = status_response.get("status", "UNKNOWN")
            print(f"Game status check {i+1}: {game_status}")
            
            if game_status == "COMPLETED":
                game_completed = True
                winner_id = status_response.get("winner_id")
                
                # Determine loser
                if winner_id == user_id1:
                    loser_id = user_id2
                elif winner_id == user_id2:
                    loser_id = user_id1
                
                print_success(f"Game completed! Winner: {winner_id}")
                break
        else:
            print_warning(f"Failed to get game status on attempt {i+1}")
    
    if not game_completed:
        print_error("Game did not complete within expected time")
        record_test("Notification Format - Game Completion", False, "Game timeout")
        return
    
    record_test("Notification Format - Game Completion", True)
    
    # Step 9: Check notifications for both players
    print_subheader("Step 9: Check Notifications")
    
    # Wait a bit for notifications to be created
    time.sleep(3)
    
    # Get notifications for Player 1
    print("Checking notifications for Player 1...")
    notifications1_response, notifications1_success = make_request(
        "GET", "/notifications",
        auth_token=player1_token
    )
    
    # Get notifications for Player 2
    print("Checking notifications for Player 2...")
    notifications2_response, notifications2_success = make_request(
        "GET", "/notifications",
        auth_token=player2_token
    )
    
    if not notifications1_success or not notifications2_success:
        print_error("Failed to get notifications")
        record_test("Notification Format - Get Notifications", False, "Failed to get notifications")
        return
    
    # Step 10: Analyze notification formats
    print_subheader("Step 10: Analyze Notification Formats")
    
    # Find match result notifications
    player1_notifications = notifications1_response.get("notifications", [])
    player2_notifications = notifications2_response.get("notifications", [])
    
    print_success(f"Player 1 has {len(player1_notifications)} notifications")
    print_success(f"Player 2 has {len(player2_notifications)} notifications")
    
    # Look for MATCH_RESULT notifications
    match_result_notifications = []
    
    for notification in player1_notifications:
        if notification.get("type") == "MATCH_RESULT":
            notification["player"] = "Player 1"
            notification["player_id"] = user_id1
            match_result_notifications.append(notification)
    
    for notification in player2_notifications:
        if notification.get("type") == "MATCH_RESULT":
            notification["player"] = "Player 2"
            notification["player_id"] = user_id2
            match_result_notifications.append(notification)
    
    print_success(f"Found {len(match_result_notifications)} MATCH_RESULT notifications")
    
    if len(match_result_notifications) == 0:
        print_error("No MATCH_RESULT notifications found")
        record_test("Notification Format - Find Match Results", False, "No notifications found")
        return
    
    record_test("Notification Format - Find Match Results", True)
    
    # Step 11: Validate notification formats
    print_subheader("Step 11: Validate Notification Formats")
    
    format_tests_passed = 0
    format_tests_total = 0
    
    for notification in match_result_notifications:
        format_tests_total += 1
        
        player = notification["player"]
        player_id = notification["player_id"]
        message = notification.get("message", "")
        title = notification.get("title", "")
        
        print_success(f"\n{player} notification:")
        print_success(f"  Title: {title}")
        print_success(f"  Message: {message}")
        
        # Check if this player won or lost
        is_winner = (player_id == winner_id)
        
        # Expected format patterns
        if is_winner:
            # Winner format: "You won against {opponent_name}! Received: {amount_won:.2f} Gems\n-3% комиссия. ${commission:.2f}"
            expected_patterns = [
                "You won against",
                "Received:",
                "Gems",
                "-3% комиссия",
                f"${expected_commission:.2f}"
            ]
            
            print_success(f"  Expected: Winner format")
            
        else:
            # Loser format: "You lost against {opponent_name}. Lost: {amount_lost:.2f} Gems\n-3% комиссия. ${commission:.2f}"
            expected_patterns = [
                "You lost against",
                "Lost:",
                "Gems",
                "-3% комиссия",
                f"${expected_commission:.2f}"
            ]
            
            print_success(f"  Expected: Loser format")
        
        # Check if all patterns are present
        patterns_found = 0
        for pattern in expected_patterns:
            if pattern in message:
                patterns_found += 1
                print_success(f"    ✓ Found pattern: '{pattern}'")
            else:
                print_error(f"    ✗ Missing pattern: '{pattern}'")
        
        # Check for commission field in notification data
        commission_field = notification.get("commission")
        if commission_field is not None:
            print_success(f"    ✓ Commission field present: {commission_field}")
            
            # Verify commission amount
            if abs(float(commission_field) - expected_commission) < 0.01:
                print_success(f"    ✓ Commission amount correct: ${commission_field}")
                patterns_found += 1
            else:
                print_error(f"    ✗ Commission amount incorrect: expected ${expected_commission}, got ${commission_field}")
        else:
            print_error(f"    ✗ Commission field missing from notification")
        
        # Check if format is correct
        if patterns_found == len(expected_patterns) + 1:  # +1 for commission field
            print_success(f"  ✅ {player} notification format CORRECT")
            format_tests_passed += 1
            record_test(f"Notification Format - {player} Format", True)
        else:
            print_error(f"  ❌ {player} notification format INCORRECT ({patterns_found}/{len(expected_patterns) + 1} patterns found)")
            record_test(f"Notification Format - {player} Format", False, f"Missing patterns: {len(expected_patterns) + 1 - patterns_found}")
    
    # Step 12: Test notification API endpoints
    print_subheader("Step 12: Test Notification API Endpoints")
    
    # Test mark as read
    if match_result_notifications:
        first_notification = match_result_notifications[0]
        notification_id = first_notification.get("id")
        
        if notification_id:
            # Get the correct token for this notification's owner
            owner_token = player1_token if first_notification["player"] == "Player 1" else player2_token
            
            mark_read_response, mark_read_success = make_request(
                "POST", f"/notifications/{notification_id}/read",
                auth_token=owner_token
            )
            
            if mark_read_success:
                print_success("Successfully marked notification as read")
                record_test("Notification Format - Mark as Read", True)
            else:
                print_error("Failed to mark notification as read")
                record_test("Notification Format - Mark as Read", False, "Mark read failed")
        else:
            print_error("No notification ID found for testing")
            record_test("Notification Format - Mark as Read", False, "No notification ID")
    
    # Test admin notification endpoints
    admin_notifications_response, admin_notifications_success = make_request(
        "GET", "/admin/notifications",
        auth_token=admin_token
    )
    
    if admin_notifications_success:
        print_success("Admin notifications endpoint accessible")
        record_test("Notification Format - Admin Notifications", True)
    else:
        print_error("Failed to access admin notifications")
        record_test("Notification Format - Admin Notifications", False, "Admin endpoint failed")
    
    # Step 13: Summary
    print_subheader("Step 13: Test Summary")
    
    print_success("NOTIFICATION FORMAT TESTING RESULTS:")
    print_success(f"✅ Game created and completed successfully")
    print_success(f"✅ Found {len(match_result_notifications)} MATCH_RESULT notifications")
    print_success(f"✅ Format validation: {format_tests_passed}/{format_tests_total} notifications correct")
    
    if format_tests_passed == format_tests_total and format_tests_total > 0:
        print_success("🎉 ALL NOTIFICATION FORMATS CORRECT!")
        print_success("✅ New format includes 'Gems' instead of '$'")
        print_success("✅ Commission information (3%) included in messages")
        print_success("✅ Commission field present in notification data")
        print_success("✅ API endpoints working correctly")
        record_test("Notification Format - Overall Success", True)
    else:
        print_error("❌ NOTIFICATION FORMAT ISSUES DETECTED")
        print_error(f"Only {format_tests_passed}/{format_tests_total} notifications have correct format")
        record_test("Notification Format - Overall Success", False, f"Format issues: {format_tests_total - format_tests_passed}")

def print_final_results():
    """Print final test results."""
    print_header("FINAL TEST RESULTS")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    print_success(f"Total tests: {total}")
    print_success(f"Passed: {passed}")
    print_error(f"Failed: {failed}")
    
    if failed == 0:
        print_success("🎉 ALL TESTS PASSED!")
    else:
        print_error(f"❌ {failed} TESTS FAILED")
    
    # Print failed tests details
    if failed > 0:
        print_subheader("Failed Tests Details:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"❌ {test['name']}: {test['details']}")

if __name__ == "__main__":
    print_header("GEMPLAY NOTIFICATION FORMAT TESTING")
    print("Testing new notification formats for match results as requested in Russian review")
    print("Focus: Commission field and 'Gems' format in MATCH_RESULT notifications")
    
    try:
        test_notification_formats()
        print_final_results()
        
        # Exit with appropriate code
        if test_results["failed"] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        sys.exit(1)