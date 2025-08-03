#!/usr/bin/env python3
"""
Test get_current_admin_user function specifically
"""

import requests
import json

BASE_URL = "https://dc94d54d-9ba1-4b44-bea4-5740540b081e.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def test_admin_user_function():
    print("🔍 TESTING get_current_admin_user FUNCTION")
    print("=" * 50)
    
    # Step 1: Login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=ADMIN_USER,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    data = response.json()
    token = data.get("access_token")
    user_info = data.get("user", {})
    
    print(f"✅ Login successful")
    print(f"   Role: {user_info.get('role')}")
    print(f"   Status: {user_info.get('status')}")
    print(f"   Email verified: {user_info.get('email_verified')}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Test endpoints that work
    print("\n📊 Testing working admin endpoints:")
    working_endpoints = [
        "/admin/dashboard/stats",
        "/admin/users/stats", 
        "/admin/human-bots"
    ]
    
    for endpoint in working_endpoints:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"   {endpoint}: {resp.status_code}")
    
    # Step 3: Test the problematic endpoint
    print("\n❌ Testing problematic endpoint:")
    resp = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"   /admin/users: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   Error: {resp.text}")
    
    # Step 4: Test with different parameters
    print("\n🔧 Testing /admin/users with different parameters:")
    test_params = [
        "",
        "?limit=5",
        "?page=1",
        "?limit=5&page=1"
    ]
    
    for params in test_params:
        resp = requests.get(f"{BASE_URL}/admin/users{params}", headers=headers)
        print(f"   /admin/users{params}: {resp.status_code}")
        if resp.status_code != 200:
            print(f"     Error: {resp.text[:100]}")
    
    # Step 5: Compare with a similar endpoint that works
    print("\n🔍 Comparing with working endpoint /admin/users/stats:")
    stats_resp = requests.get(f"{BASE_URL}/admin/users/stats", headers=headers)
    print(f"   /admin/users/stats: {stats_resp.status_code}")
    if stats_resp.status_code == 200:
        stats_data = stats_resp.json()
        print(f"   Stats data keys: {list(stats_data.keys())}")
        print(f"   Total users: {stats_data.get('total', 'N/A')}")

if __name__ == "__main__":
    test_admin_user_function()