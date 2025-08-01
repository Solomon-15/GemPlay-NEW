#!/usr/bin/env python3
"""
Simple test for Human-bot names management API endpoints
"""

import requests
import json

BASE_URL = "https://a20aa5a2-a31c-4c8d-a1c4-18cc39118b00.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def test_put_endpoint():
    # Login as admin
    login_response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test PUT with minimal data
    test_data = {
        "names": ["TestName1", "TestName2", "TestName3"]
    }
    
    print("Testing PUT endpoint...")
    put_response = requests.put(f"{BASE_URL}/admin/human-bots/names", json=test_data, headers=headers)
    print(f"PUT Status: {put_response.status_code}")
    if put_response.status_code != 200:
        print(f"PUT Error: {put_response.text}")
    else:
        print(f"PUT Success: {put_response.json()}")

if __name__ == "__main__":
    test_put_endpoint()