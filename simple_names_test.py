#!/usr/bin/env python3
"""
Simple test for Human-bot names management API endpoints
"""

import requests
import json

BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
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
    
    # Test POST version with minimal data
    test_data = {
        "names": ["TestName1", "TestName2", "TestName3"]
    }
    
    print("Testing POST endpoint...")
    post_response = requests.post(f"{BASE_URL}/admin/human-bots/names/update", json=test_data, headers=headers)
    print(f"POST Status: {post_response.status_code}")
    if post_response.status_code != 200:
        print(f"POST Error: {post_response.text}")
    else:
        print(f"POST Success: {post_response.json()}")

if __name__ == "__main__":
    test_put_endpoint()