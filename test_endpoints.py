#!/usr/bin/env python3

import requests
import json

# Test the exact problematic endpoints
BASE_URL = "https://11ff6985-226e-4a25-848c-148a2fa58531.preview.emergentagent.com/api"

def test_login():
    """Test admin login"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@gemplay.com",
            "password": "Admin123!"
        })
        print(f"Login status: {response.status_code}")
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception as e:
        print(f"Login error: {e}")
    return None

def test_endpoints():
    """Test problematic endpoints"""
    token = test_login()
    if not token:
        print("Failed to get token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test specific endpoints
    endpoints = [
        ("GET", "/admin/bot-settings"),
        ("GET", "/admin/bots/regular/list"),
        ("GET", "/admin/bots/analytics"),
        ("GET", "/")
    ]
    
    for method, endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            print(f"\n=== Testing {method} {url} ===")
            
            response = requests.request(method, url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")
                except:
                    print(f"Response text: {response.text[:500]}...")
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Exception for {endpoint}: {e}")

if __name__ == "__main__":
    test_endpoints()