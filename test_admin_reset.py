#!/usr/bin/env python3
import requests
import json
import time

# Configuration
BASE_URL = "https://4d8b46bc-dff3-4e9b-b563-ac723d805b5c.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def make_request(method, endpoint, data=None, headers=None, auth_token=None):
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
    
    return response_data, response.status_code

def test_admin_reset_endpoint():
    """Test the admin reset-all endpoint."""
    print("=== TESTING ADMIN RESET-ALL ENDPOINT ===\n")
    
    # Step 1: Login as admin
    print("1. Admin Login")
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, status = make_request("POST", "/auth/login", data=login_data)
    
    if status != 200:
        print(f"❌ Admin login failed with status {status}")
        return
    
    admin_token = response.get("access_token")
    if not admin_token:
        print("❌ No access token in admin login response")
        return
    
    print("✅ Admin login successful\n")
    
    # Step 2: Test non-admin access (create a regular user first)
    print("2. Testing non-admin access")
    
    # Register a test user
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"testuser_{int(time.time())}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    response, status = make_request("POST", "/auth/register", data=test_user)
    if status == 200:
        # Verify email
        token = response.get("verification_token")
        if token:
            make_request("POST", "/auth/verify-email", data={"token": token})
        
        # Login as regular user
        login_response, login_status = make_request("POST", "/auth/login", data={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        if login_status == 200:
            user_token = login_response.get("access_token")
            
            # Try to access admin endpoint with regular user token
            response, status = make_request("POST", "/admin/games/reset-all", auth_token=user_token)
            
            if status == 403:
                print("✅ Non-admin access correctly denied (403 Forbidden)")
            else:
                print(f"❌ Non-admin access not properly denied (got status {status})")
        else:
            print("⚠️ Could not login as regular user to test non-admin access")
    else:
        print("⚠️ Could not create regular user to test non-admin access")
    
    print()
    
    # Step 3: Test admin access
    print("3. Testing admin access to reset-all endpoint")
    
    response, status = make_request("POST", "/admin/games/reset-all", auth_token=admin_token)
    
    if status == 200:
        print("✅ Admin reset-all endpoint accessible")
        
        # Check response format
        expected_fields = ["message", "games_reset", "gems_returned", "commission_returned"]
        missing_fields = [field for field in expected_fields if field not in response]
        
        if not missing_fields:
            print("✅ Response contains all expected fields")
            print(f"   - Games reset: {response.get('games_reset', 0)}")
            print(f"   - Gems returned: {response.get('gems_returned', {})}")
            print(f"   - Commission returned: ${response.get('commission_returned', 0)}")
        else:
            print(f"❌ Response missing fields: {missing_fields}")
    else:
        print(f"❌ Admin reset-all failed with status {status}")
        print(f"   Response: {response}")
    
    print()
    
    # Step 4: Test again to ensure it works when no active games exist
    print("4. Testing reset when no active games exist")
    
    response, status = make_request("POST", "/admin/games/reset-all", auth_token=admin_token)
    
    if status == 200:
        games_reset = response.get("games_reset", 0)
        if games_reset == 0:
            print("✅ Reset correctly reports 0 games when no active games exist")
        else:
            print(f"⚠️ Reset reported {games_reset} games when none should exist")
    else:
        print(f"❌ Reset failed when no active games with status {status}")

if __name__ == "__main__":
    test_admin_reset_endpoint()