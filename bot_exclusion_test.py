#!/usr/bin/env python3
"""
Bot Exclusion Logic Testing
Quick test for the simplified bot exclusion query in broadcast notifications
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, Tuple

# Configuration
BASE_URL = "https://25ef1535-ba83-4b7a-b8f9-a5bf1769f3a3.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
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

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

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
    print(f"Testing login for {user_type}: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"{user_type.capitalize()} login successful")
        return response["access_token"]
    else:
        print_error(f"{user_type.capitalize()} login failed: {response}")
        return None

def test_bot_exclusion_logic():
    """Test the simplified bot exclusion logic for broadcast notifications."""
    print_header("BOT EXCLUSION LOGIC TESTING")
    
    # Step 1: Login as admin
    print(f"{Colors.OKBLUE}Step 1: Admin Login{Colors.ENDC}")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with bot exclusion test")
        return False
    
    print_success("Admin logged in successfully")
    
    # Step 2: Send broadcast notification with target_users: null (all users)
    print(f"\n{Colors.OKBLUE}Step 2: Send Broadcast Notification to All Users{Colors.ENDC}")
    
    broadcast_data = {
        "target_users": None,  # null = all users
        "type": "admin_notification",
        "priority": "info",
        "title": "Bot Exclusion Test",
        "message": "Testing simplified bot exclusion query",
        "emoji": "🧪"
    }
    
    print("Sending broadcast notification with target_users: null...")
    broadcast_response, broadcast_success = make_request(
        "POST", "/admin/notifications/broadcast",
        data=broadcast_data,
        auth_token=admin_token
    )
    
    if not broadcast_success:
        print_error("Failed to send broadcast notification")
        return False
    
    # Step 3: Check sent_count in response
    print(f"\n{Colors.OKBLUE}Step 3: Check sent_count{Colors.ENDC}")
    
    sent_count = broadcast_response.get("sent_count", 0)
    notification_id = broadcast_response.get("notification_id", "")
    
    print_success(f"Broadcast notification sent successfully")
    print_success(f"Notification ID: {notification_id}")
    print_success(f"📊 SENT_COUNT: {sent_count}")
    
    # Step 4: Analyze the result
    print(f"\n{Colors.OKBLUE}Step 4: Analyze Bot Exclusion Result{Colors.ENDC}")
    
    if sent_count == 345:
        print_error("❌ ISSUE: sent_count is still 345 (includes bots)")
        print_error("❌ The simplified bot exclusion query is NOT working")
        print_error("❌ Problem is likely in the user data structure")
        print_warning("🔍 RECOMMENDATION: Check user data structure for bot_type and is_bot fields")
        return False
    elif sent_count >= 290 and sent_count <= 310:
        print_success("✅ SUCCESS: sent_count is approximately 300 (excludes bots)")
        print_success("✅ The simplified bot exclusion query is working correctly")
        print_success("✅ Bots are properly excluded from broadcast notifications")
        return True
    else:
        print_warning(f"⚠ UNEXPECTED: sent_count is {sent_count} (expected ~300)")
        print_warning("⚠ This may indicate a different issue with user data")
        
        if sent_count < 290:
            print_warning("🔍 Possible causes: Too many users excluded, database connectivity issues")
        elif sent_count > 310:
            print_warning("🔍 Possible causes: Some bots still included, user count increased")
        
        return False

def test_user_data_structure():
    """Test to examine user data structure for bot identification."""
    print_header("USER DATA STRUCTURE ANALYSIS")
    
    # Login as admin
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin")
        return
    
    # Try to get user management data to see user structure
    print(f"{Colors.OKBLUE}Examining User Data Structure{Colors.ENDC}")
    
    users_response, users_success = make_request(
        "GET", "/admin/users?page=1&limit=10",
        auth_token=admin_token
    )
    
    if users_success and "users" in users_response:
        users = users_response["users"]
        print_success(f"Retrieved {len(users)} users for analysis")
        
        # Analyze first few users
        for i, user in enumerate(users[:5]):
            user_id = user.get("id", "unknown")
            username = user.get("username", "unknown")
            role = user.get("role", "unknown")
            status = user.get("status", "unknown")
            bot_type = user.get("bot_type", "NOT_PRESENT")
            is_bot = user.get("is_bot", "NOT_PRESENT")
            
            print_success(f"User {i+1}: {username}")
            print_success(f"  ID: {user_id}")
            print_success(f"  Role: {role}")
            print_success(f"  Status: {status}")
            print_success(f"  bot_type: {bot_type}")
            print_success(f"  is_bot: {is_bot}")
            
            # Check if this looks like a bot based on naming
            if "bot" in username.lower() or "player" in username.lower():
                print_warning(f"  ⚠ Potential bot based on username")
    else:
        print_error("Failed to get user data for analysis")

def main():
    """Main test function."""
    print_header("БЫСТРАЯ ПРОВЕРКА ИСПРАВЛЕННОЙ ЛОГИКИ ИСКЛЮЧЕНИЯ БОТОВ")
    
    print("КОНТЕКСТ: Упростил запрос для исключения ботов:")
    print("""
    {
        "status": "ACTIVE",
        "role": {"$in": ["USER", "ADMIN", "SUPER_ADMIN"]},
        "bot_type": {"$exists": False},
        "is_bot": {"$ne": True}
    }
    """)
    
    print("\nТЕСТ:")
    print("1. Отправить одно broadcast уведомление с target_users: null")
    print("2. Проверить sent_count - должно быть примерно 300 (не 345)")
    print("3. Если все еще 345, то проблема в структуре данных пользователей")
    
    # Run the main test
    success = test_bot_exclusion_logic()
    
    if not success:
        print(f"\n{Colors.WARNING}Running additional analysis...{Colors.ENDC}")
        test_user_data_structure()
    
    # Final summary
    print_header("РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ")
    
    if success:
        print_success("🎉 УСПЕХ: Логика исключения ботов работает правильно!")
        print_success("✅ sent_count примерно 300 (исключает ботов)")
        print_success("✅ Упрощенный запрос функционирует корректно")
    else:
        print_error("❌ ПРОБЛЕМА: Логика исключения ботов требует доработки")
        print_error("❌ sent_count не соответствует ожидаемому значению")
        print_warning("🔧 Требуется дополнительная проверка структуры данных пользователей")

if __name__ == "__main__":
    main()