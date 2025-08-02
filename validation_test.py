#!/usr/bin/env python3
"""
Quick validation test to see what happens with invalid values
"""

import requests
import json

BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def test_validation():
    # Login as admin
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if response.status_code != 200:
        print("Failed to login")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with invalid delay value
    test_data = {
        "name": "ValidationTest",
        "character": "BALANCED",
        "min_bet": 10.0,
        "max_bet": 100.0,
        "bot_min_delay_seconds": 20  # Below minimum of 30
    }
    
    print("Testing with bot_min_delay_seconds: 20 (should fail)")
    response = requests.post(f"{BASE_URL}/admin/human-bots", json=test_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test with invalid max concurrent games
    test_data2 = {
        "name": "ValidationTest2",
        "character": "BALANCED", 
        "min_bet": 10.0,
        "max_bet": 100.0,
        "max_concurrent_games": 5  # Above maximum of 3
    }
    
    print("\nTesting with max_concurrent_games: 5 (should fail)")
    response = requests.post(f"{BASE_URL}/admin/human-bots", json=test_data2, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_validation()