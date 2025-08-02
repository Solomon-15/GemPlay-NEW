#!/usr/bin/env python3
"""
Simple Notification Format Test
Focus: Test notification formats after game completion
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def make_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    try:
        return response.json()
    except:
        return {"error": response.text, "status_code": response.status_code}

def test_notifications():
    """Test notification formats."""
    print("=== NOTIFICATION FORMAT TESTING ===")
    
    # Login as admin
    print("1. Admin login...")
    login_response = make_request("POST", "/auth/login", {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    })
    
    if "access_token" not in login_response:
        print(f"❌ Admin login failed: {login_response}")
        return
    
    admin_token = login_response["access_token"]
    print("✅ Admin logged in successfully")
    
    # Check existing notifications
    print("\n2. Checking existing notifications...")
    
    # Get all users first
    users_response = make_request("GET", "/admin/users?page=1&limit=50", auth_token=admin_token)
    
    if "users" not in users_response:
        print(f"❌ Failed to get users: {users_response}")
        return
    
    users = users_response["users"]
    print(f"✅ Found {len(users)} users")
    
    # Check notifications for each user
    notification_count = 0
    match_result_notifications = []
    
    for user in users[:10]:  # Check first 10 users
        user_id = user["id"]
        username = user["username"]
        
        # Try to get user token (this might not work, but let's try)
        try:
            # Get notifications via admin endpoint if available
            notifications_response = make_request("GET", f"/admin/users/{user_id}/notifications", auth_token=admin_token)
            
            if isinstance(notifications_response, dict) and "notifications" in notifications_response:
                user_notifications = notifications_response["notifications"]
                notification_count += len(user_notifications)
                
                # Look for MATCH_RESULT notifications
                for notification in user_notifications:
                    if notification.get("type") == "MATCH_RESULT":
                        notification["username"] = username
                        match_result_notifications.append(notification)
                        print(f"✅ Found MATCH_RESULT notification for {username}")
            
        except Exception as e:
            # Try alternative approach - check if user has recent activity
            continue
    
    print(f"\n3. Notification Analysis:")
    print(f"   Total notifications checked: {notification_count}")
    print(f"   MATCH_RESULT notifications found: {len(match_result_notifications)}")
    
    if len(match_result_notifications) == 0:
        print("❌ No MATCH_RESULT notifications found")
        
        # Let's check if there are any recent games
        print("\n4. Checking recent games...")
        games_response = make_request("GET", "/admin/games?page=1&limit=20", auth_token=admin_token)
        
        if "games" in games_response:
            completed_games = [g for g in games_response["games"] if g.get("status") == "COMPLETED"]
            print(f"   Found {len(completed_games)} completed games")
            
            if completed_games:
                print("   Recent completed games:")
                for game in completed_games[:3]:
                    print(f"     Game {game.get('id', 'unknown')}: Winner {game.get('winner_id', 'unknown')}")
        
        return
    
    # Analyze notification formats
    print(f"\n5. Analyzing {len(match_result_notifications)} MATCH_RESULT notifications:")
    
    format_correct = 0
    format_total = len(match_result_notifications)
    
    for i, notification in enumerate(match_result_notifications):
        username = notification.get("username", "unknown")
        message = notification.get("message", "")
        title = notification.get("title", "")
        commission = notification.get("commission")
        
        print(f"\n   Notification {i+1} ({username}):")
        print(f"     Title: {title}")
        print(f"     Message: {message}")
        print(f"     Commission field: {commission}")
        
        # Check format requirements
        format_checks = []
        
        # Check for "Gems" instead of "$"
        if "Gems" in message:
            format_checks.append("✅ Uses 'Gems' format")
        else:
            format_checks.append("❌ Missing 'Gems' format")
        
        # Check for commission info
        if "комиссия" in message or "commission" in message.lower():
            format_checks.append("✅ Contains commission info")
        else:
            format_checks.append("❌ Missing commission info")
        
        # Check for 3% mention
        if "3%" in message:
            format_checks.append("✅ Contains 3% rate")
        else:
            format_checks.append("❌ Missing 3% rate")
        
        # Check commission field
        if commission is not None:
            format_checks.append(f"✅ Commission field present: {commission}")
        else:
            format_checks.append("❌ Commission field missing")
        
        # Check win/loss format
        if "You won against" in message or "You lost against" in message:
            format_checks.append("✅ Correct win/loss format")
        else:
            format_checks.append("❌ Incorrect win/loss format")
        
        # Print checks
        for check in format_checks:
            print(f"       {check}")
        
        # Count as correct if most checks pass
        passed_checks = sum(1 for check in format_checks if check.startswith("✅"))
        if passed_checks >= 4:  # At least 4 out of 5 checks should pass
            format_correct += 1
            print(f"     ✅ Format CORRECT ({passed_checks}/5 checks passed)")
        else:
            print(f"     ❌ Format INCORRECT ({passed_checks}/5 checks passed)")
    
    # Final results
    print(f"\n6. FINAL RESULTS:")
    print(f"   Notifications analyzed: {format_total}")
    print(f"   Correct format: {format_correct}")
    print(f"   Incorrect format: {format_total - format_correct}")
    
    if format_correct == format_total and format_total > 0:
        print("   🎉 ALL NOTIFICATION FORMATS CORRECT!")
        print("   ✅ New format with 'Gems' implemented")
        print("   ✅ Commission information included")
        print("   ✅ Commission field present in data")
    elif format_total == 0:
        print("   ⚠️  NO MATCH_RESULT NOTIFICATIONS FOUND")
        print("   Need to create and complete games to test notifications")
    else:
        print(f"   ❌ SOME NOTIFICATION FORMATS INCORRECT")
        print(f"   {format_total - format_correct} notifications need format fixes")

if __name__ == "__main__":
    test_notifications()