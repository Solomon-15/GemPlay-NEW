#!/usr/bin/env python3
"""
Quick test for profile update API endpoint
"""
import requests
import json
import time

# Configuration
BASE_URL = "https://2afcdb68-e337-4e72-a16b-588ed6811928.preview.emergentagent.com/api"

def test_profile_update():
    """Test profile update endpoint"""
    
    # Login as admin
    print("🔑 Logging in as admin...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@gemplay.com",
        "password": "Admin123!"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.json()}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful")
    
    # Get current user info
    print("📋 Getting current user info...")
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if me_response.status_code != 200:
        print(f"❌ Failed to get user info: {me_response.json()}")
        return
    
    user_data = me_response.json()
    print(f"Current user: {user_data['username']}")
    print(f"Current gender: {user_data['gender']}")
    print(f"Current timezone_offset: {user_data.get('timezone_offset', 0)}")
    
    # Test profile update
    print("\n🔄 Testing profile update...")
    
    new_username = f"admin_test_{int(time.time())}"
    update_data = {
        "username": new_username,
        "gender": "female" if user_data.get("gender") == "male" else "male",
        "timezone_offset": 3
    }
    
    print(f"Update data: {update_data}")
    
    update_response = requests.put(f"{BASE_URL}/auth/profile", json=update_data, headers=headers)
    
    print(f"Response status: {update_response.status_code}")
    print(f"Response data: {update_response.json()}")
    
    if update_response.status_code == 200:
        print("✅ Profile update successful!")
        
        # Verify update worked
        print("\n🔍 Verifying update...")
        verify_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if verify_response.status_code == 200:
            updated_user = verify_response.json()
            print(f"Updated username: {updated_user['username']}")
            print(f"Updated gender: {updated_user['gender']}")
            print(f"Updated timezone_offset: {updated_user.get('timezone_offset', 0)}")
            
            if updated_user['username'] == new_username:
                print("✅ Username update verified!")
            else:
                print(f"❌ Username not updated: expected {new_username}, got {updated_user['username']}")
                
    else:
        print(f"❌ Profile update failed: {update_response.json()}")

if __name__ == "__main__":
    test_profile_update()