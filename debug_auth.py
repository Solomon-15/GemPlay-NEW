#!/usr/bin/env python3
"""
Debug Role Loading Authentication Issue
"""

import requests
import json
import jwt
import time

BASE_URL = "https://popup-manager.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def debug_authentication():
    print("🔍 DEBUGGING AUTHENTICATION ISSUE")
    print("=" * 50)
    
    # Step 1: Login
    print("1. Testing admin login...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=ADMIN_USER,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        user_info = data.get("user", {})
        print(f"Token received: {token[:50]}..." if token else "No token")
        print(f"User role: {user_info.get('role')}")
        print(f"User status: {user_info.get('status')}")
        print(f"Email verified: {user_info.get('email_verified')}")
        
        # Step 2: Test /auth/me endpoint
        print("\n2. Testing /auth/me endpoint...")
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"/auth/me Status: {me_response.status_code}")
        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"Me endpoint role: {me_data.get('role')}")
            print(f"Me endpoint status: {me_data.get('status')}")
        else:
            print(f"/auth/me Error: {me_response.text}")
        
        # Step 3: Test admin/users endpoint with detailed error
        print("\n3. Testing /admin/users endpoint...")
        users_response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        print(f"/admin/users Status: {users_response.status_code}")
        print(f"/admin/users Response: {users_response.text}")
        
        # Step 4: Try different admin endpoints
        print("\n4. Testing other admin endpoints...")
        admin_endpoints = [
            "/admin/dashboard/stats",
            "/admin/users/stats",
            "/admin/human-bots"
        ]
        
        for endpoint in admin_endpoints:
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                print(f"{endpoint}: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"  Error: {resp.text[:100]}")
            except Exception as e:
                print(f"{endpoint}: Exception - {e}")
        
        # Step 5: Decode JWT token to check payload
        print("\n5. JWT Token Analysis...")
        try:
            # Decode without verification to see payload
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"Token payload: {json.dumps(decoded, indent=2)}")
        except Exception as e:
            print(f"JWT decode error: {e}")
            
    else:
        print(f"Login failed: {response.text}")

if __name__ == "__main__":
    debug_authentication()