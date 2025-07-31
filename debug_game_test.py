#!/usr/bin/env python3
"""
Debug Game Test - Direct database check
"""

import requests
import json
import time
import random
import string

# Configuration
BASE_URL = "https://85245bb1-9423-4f57-ad61-2213aa95b2ae.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def make_request(method, endpoint, data=None, auth_token=None):
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"\n{method} {url}")
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    print(f"Status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        return response_data, response.status_code == 200
    except:
        print(f"Response text: {response.text}")
        return {"text": response.text}, response.status_code == 200

def main():
    """Main test function."""
    print("=" * 80)
    print("DEBUG GAME TEST - CHECKING GAME CREATION AND AVAILABILITY")
    print("=" * 80)
    
    # Step 1: Login as admin
    print("\n1. ADMIN LOGIN")
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    login_response, login_success = make_request("POST", "/auth/login", login_data)
    
    if not login_success:
        print("❌ Admin login failed")
        return False
    
    admin_token = login_response["access_token"]
    print("✅ Admin login successful")
    
    # Step 2: Create a game
    print("\n2. CREATE GAME")
    
    create_game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 5}
    }
    
    game_response, game_success = make_request("POST", "/games/create", create_game_data, admin_token)
    
    if not game_success:
        print("❌ Game creation failed")
        return False
    
    game_id = game_response.get("game_id")
    print(f"✅ Game created with ID: {game_id}")
    
    # Step 3: Create a different user to check available games
    print("\n3. CREATE DIFFERENT USER")
    
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    user_data = {
        "username": f"testuser_{random_suffix}",
        "email": f"testuser_{random_suffix}@test.com",
        "password": "Test123!",
        "gender": "female"
    }
    
    register_response, register_success = make_request("POST", "/auth/register", user_data)
    
    if not register_success:
        print("❌ User registration failed")
        return False
    
    verification_token = register_response.get("verification_token")
    verify_response, verify_success = make_request("POST", "/auth/verify-email", {"token": verification_token})
    
    if not verify_success:
        print("❌ Email verification failed")
        return False
    
    # Login as new user
    user_login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    user_login_response, user_login_success = make_request("POST", "/auth/login", user_login_data)
    
    if not user_login_success:
        print("❌ User login failed")
        return False
    
    user_token = user_login_response["access_token"]
    print("✅ User created and logged in")
    
    # Step 4: Check available games with new user
    print("\n4. CHECK AVAILABLE GAMES WITH NEW USER")
    
    available_response, available_success = make_request("GET", "/games/available", auth_token=user_token)
    
    if available_success:
        print(f"Available games count: {len(available_response)}")
        
        # Look for our game
        our_game = None
        for game in available_response:
            if game.get("game_id") == game_id:
                our_game = game
                break
        
        if our_game:
            print("✅ FOUND OUR GAME!")
            print(f"   Game ID: {our_game.get('game_id')}")
            print(f"   Status: {our_game.get('status')}")
            print(f"   Creator: {our_game.get('creator_id')}")
            print(f"   Bet amount: ${our_game.get('bet_amount')}")
            return True
        else:
            print("❌ OUR GAME NOT FOUND")
            print("Available games:")
            for i, game in enumerate(available_response):
                print(f"   {i+1}. ID: {game.get('game_id')}, Status: {game.get('status')}, Creator: {game.get('creator_id')}")
            return False
    else:
        print("❌ Failed to get available games")
        return False

if __name__ == "__main__":
    main()