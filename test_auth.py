#!/usr/bin/env python3
"""
Simple authentication test for the admin panel
"""
import requests
import json

BASE_URL = "http://localhost:8001"

# Test different admin credentials
admin_credentials = [
    {"email": "admin@example.com", "password": "admin123"},
    {"email": "admin@admin.com", "password": "admin123"},
    {"email": "admin", "password": "admin123"},
    {"email": "super@admin.com", "password": "admin123"},
    {"email": "smukhammedali@gmail.com", "password": "admin123"},
]

def test_login(email, password):
    """Test login with given credentials"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_admin_endpoint(token):
    """Test admin endpoint with token"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/human-bots",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

def main():
    print("Testing admin authentication...")
    
    # Try to find working admin credentials
    for creds in admin_credentials:
        print(f"\nTesting: {creds['email']} / {creds['password']}")
        token = test_login(creds['email'], creds['password'])
        
        if token:
            print(f"✅ Login successful! Token: {token[:50]}...")
            
            # Test admin endpoint
            success, data = test_admin_endpoint(token)
            if success:
                print("✅ Admin endpoint accessible!")
                print(f"Human bots count: {len(data.get('human_bots', []))}")
                
                # Test games endpoint
                try:
                    games_response = requests.get(
                        f"{BASE_URL}/api/admin/games?page=1&limit=5",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if games_response.status_code == 200:
                        games_data = games_response.json()
                        print(f"✅ Games endpoint working! Total games: {games_data.get('total', 0)}")
                    else:
                        print(f"❌ Games endpoint failed: {games_response.status_code}")
                except Exception as e:
                    print(f"❌ Games endpoint error: {e}")
                
                # Test bots endpoint
                try:
                    bots_response = requests.get(
                        f"{BASE_URL}/api/admin/bots?page=1&limit=5",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if bots_response.status_code == 200:
                        bots_data = bots_response.json()
                        print(f"✅ Bots endpoint working! Total bots: {bots_data.get('total', 0)}")
                    else:
                        print(f"❌ Bots endpoint failed: {bots_response.status_code}")
                except Exception as e:
                    print(f"❌ Bots endpoint error: {e}")
                
                break
            else:
                print(f"❌ Admin endpoint failed: {data}")
        else:
            print("❌ Login failed")

if __name__ == "__main__":
    main()