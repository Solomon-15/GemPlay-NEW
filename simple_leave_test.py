#!/usr/bin/env python3
"""
Simple Leave Game Test
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://acffc923-2545-42ed-a41d-4e93fa17c383.preview.emergentagent.com/api"

def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    auth_token: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
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
    
    success = response.status_code == expected_status
    
    if not success:
        print(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success

def main():
    # Use existing tokens from previous test
    player_a_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNWVjNDE2Yi0yZjZhLTQyMDYtYmY3MS1mOGEyOWRjN2VlNWMiLCJleHAiOjE3NTM5NjU0Nzl9.mdNH_4Nvgro0obaOwTCYYZFNo3CyH8APVABQE6rPNpM"
    player_b_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNDNkM2U0My1mMTdmLTQ3NDktYTQ4Mi1jN2RhYTliNjBjYTMiLCJleHAiOjE3NTM5NjU0ODB9.SH45JjM3TjTgjT6S8u6LwadCrmTuJDt-nhkJ_WI5YoQ"
    
    # Create a new game
    print("Creating new game...")
    game_data = {
        "move": "rock",
        "bet_gems": {
            "Ruby": 10,
            "Emerald": 1
        }
    }
    
    response, success = make_request(
        "POST", "/games/create",
        data=game_data,
        auth_token=player_a_token
    )
    
    if not success:
        print("Failed to create game")
        return
    
    game_id = response["game_id"]
    print(f"Game created: {game_id}")
    
    # Player B joins
    print("Player B joining game...")
    join_data = {
        "move": "paper",
        "gems": {
            "Ruby": 10,
            "Emerald": 1
        }
    }
    
    response, success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_data,
        auth_token=player_b_token
    )
    
    if not success:
        print("Failed to join game")
        return
    
    print("Game joined successfully")
    
    # Player B leaves
    print("Player B leaving game...")
    response, success = make_request(
        "POST", f"/games/{game_id}/leave",
        auth_token=player_b_token
    )
    
    if success:
        print("✅ Leave game successful!")
        print(f"Response: {response}")
    else:
        print("❌ Leave game failed!")
        print(f"Response: {response}")
    
    # Check notifications for Player A
    print("Checking Player A notifications...")
    response, success = make_request(
        "GET", "/notifications",
        auth_token=player_a_token
    )
    
    if success:
        print("✅ Notifications retrieved!")
        notifications = response.get("notifications", [])
        print(f"Found {len(notifications)} notifications")
        for notif in notifications:
            print(f"- {notif.get('title', 'No title')}: {notif.get('message', 'No message')}")
    else:
        print("❌ Failed to get notifications")

if __name__ == "__main__":
    main()