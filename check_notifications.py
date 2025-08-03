#!/usr/bin/env python3
"""
Check Notifications Directly
"""

import requests
import json

BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def make_request(method: str, endpoint: str, data=None, auth_token=None):
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
    
    print(f"{method} {url} -> {response.status_code}")
    
    try:
        result = response.json()
        if isinstance(result, dict) and len(str(result)) > 500:
            print("Response: [Large response - truncated]")
        else:
            print(f"Response: {json.dumps(result, indent=2)}")
        return result
    except:
        print(f"Response text: {response.text}")
        return {"error": response.text, "status_code": response.status_code}

def main():
    print("=== CHECKING NOTIFICATIONS ===")
    
    # Login as admin
    print("\n1. Admin login...")
    login_response = make_request("POST", "/auth/login", {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    })
    
    if "access_token" not in login_response:
        print("❌ Admin login failed")
        return
    
    admin_token = login_response["access_token"]
    print("✅ Admin logged in")
    
    # Check admin notifications endpoint
    print("\n2. Checking admin notifications...")
    admin_notifications = make_request("GET", "/admin/notifications", auth_token=admin_token)
    
    # Check if we can get all notifications
    print("\n3. Checking all notifications...")
    all_notifications = make_request("GET", "/admin/notifications/all", auth_token=admin_token)
    
    # Try to get recent games
    print("\n4. Checking recent games...")
    games = make_request("GET", "/admin/games?page=1&limit=10", auth_token=admin_token)
    
    # Check available games
    print("\n5. Checking available games...")
    available_games = make_request("GET", "/games/available", auth_token=admin_token)
    
    # Check completed games specifically
    print("\n6. Checking completed games...")
    completed_games = make_request("GET", "/admin/games?status=COMPLETED&page=1&limit=10", auth_token=admin_token)
    
    # Try to create a test notification
    print("\n7. Creating test notification...")
    test_notification = make_request("POST", "/admin/notifications/broadcast", {
        "type": "MATCH_RESULT",
        "title": "Test Match Result",
        "message": "You won against TestPlayer! Received: 35.00 Gems\n-3% комиссия. $1.05",
        "commission": 1.05
    }, auth_token=admin_token)

if __name__ == "__main__":
    main()