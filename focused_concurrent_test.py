#!/usr/bin/env python3
"""
Focused test for the concurrent games issue.
Tests the specific problem where completed games still block joining new games.
"""

import requests
import json
import time
import random
import string

# Configuration
BASE_URL = "https://acffc923-2545-42ed-a41d-4e93fa17c383.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def make_request(method, endpoint, data=None, auth_token=None, expected_status=200):
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        response_data = {"text": response.text}
    
    success = response.status_code == expected_status
    return response_data, success

def create_unique_user():
    """Create a unique test user."""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    user_data = {
        "username": f"testuser_{random_suffix}",
        "email": f"testuser_{random_suffix}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    # Register
    response, success = make_request("POST", "/auth/register", data=user_data)
    if not success:
        return None, None
    
    # Verify email
    if "verification_token" in response:
        make_request("POST", "/auth/verify-email", data={"token": response["verification_token"]})
    
    # Login
    login_response, login_success = make_request("POST", "/auth/login", data={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    
    if login_success and "access_token" in login_response:
        return login_response["access_token"], login_response["user"]["id"]
    
    return None, None

def test_concurrent_games_bug():
    """Test the concurrent games bug."""
    print("🔍 TESTING CONCURRENT GAMES BUG")
    print("=" * 50)
    
    # Create two test users
    print("1. Creating test users...")
    user1_token, user1_id = create_unique_user()
    user2_token, user2_id = create_unique_user()
    
    if not user1_token or not user2_token:
        print("❌ Failed to create test users")
        return
    
    print(f"✅ User 1 created: {user1_id}")
    print(f"✅ User 2 created: {user2_id}")
    
    # Buy gems for both users
    print("\n2. Setting up gems...")
    for token in [user1_token, user2_token]:
        make_request("POST", "/gems/buy?gem_type=Ruby&quantity=50", auth_token=token)
    print("✅ Gems purchased")
    
    # User 1 creates a game
    print("\n3. User 1 creates a game...")
    create_game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 10}
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create", 
        data=create_game_data, 
        auth_token=user1_token
    )
    
    if not game_success:
        print(f"❌ Failed to create game: {game_response}")
        return
    
    game_id = game_response.get("game_id")
    print(f"✅ Game created: {game_id}")
    
    # User 2 joins the game
    print("\n4. User 2 joins the game...")
    join_game_data = {
        "move": "paper",
        "gems": {"Ruby": 10}
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=user2_token
    )
    
    if not join_success:
        print(f"❌ Failed to join game: {join_response}")
        return
    
    game_status = join_response.get("status", "UNKNOWN")
    print(f"✅ Game joined, status: {game_status}")
    
    # Wait a moment for any async processing
    time.sleep(2)
    
    # Check if User 1 can join another game using debug endpoint
    print("\n5. Checking User 1's game status...")
    debug_response, debug_success = make_request(
        "GET", f"/debug/user-games/{user1_id}", 
        auth_token=user1_token
    )
    
    if debug_success:
        can_join = debug_response.get("can_join_games", True)
        active_as_creator = debug_response.get("active_as_creator", 0)
        active_as_opponent = debug_response.get("active_as_opponent", 0)
        waiting_as_creator = debug_response.get("waiting_as_creator", 0)
        
        print(f"   Can join games: {can_join}")
        print(f"   Active as creator: {active_as_creator}")
        print(f"   Active as opponent: {active_as_opponent}")
        print(f"   Waiting as creator: {waiting_as_creator}")
        
        # Show detailed game info
        active_games_creator = debug_response.get("active_games_creator", [])
        active_games_opponent = debug_response.get("active_games_opponent", [])
        
        if active_games_creator:
            print(f"   Active creator games: {active_games_creator}")
        if active_games_opponent:
            print(f"   Active opponent games: {active_games_opponent}")
        
        if not can_join:
            print("\n🐛 BUG CONFIRMED!")
            print("❌ User cannot join games after completing a game")
            print("🔍 ROOT CAUSE: check_user_concurrent_games function is incorrectly")
            print("   identifying completed games as still active")
            
            if active_games_creator or active_games_opponent:
                print(f"🔍 SPECIFIC ISSUE: User has {len(active_games_creator + active_games_opponent)} games")
                print("   marked as ACTIVE/REVEAL that should be COMPLETED")
            
            return False
        else:
            print("\n✅ NO BUG DETECTED")
            print("✅ User can join games after completion")
            return True
    else:
        print(f"❌ Failed to get debug info: {debug_response}")
        return None
    
    # Additional test: Try to actually join another game
    print("\n6. Testing actual game join...")
    
    # Create a game with User 2 for User 1 to join
    create_test_game_data = {
        "move": "scissors",
        "bet_gems": {"Ruby": 5}
    }
    
    test_game_response, test_game_success = make_request(
        "POST", "/games/create", 
        data=create_test_game_data, 
        auth_token=user2_token
    )
    
    if test_game_success:
        test_game_id = test_game_response.get("game_id")
        print(f"✅ Test game created: {test_game_id}")
        
        # User 1 tries to join
        join_test_data = {
            "move": "paper",
            "gems": {"Ruby": 5}
        }
        
        join_test_response, join_test_success = make_request(
            "POST", f"/games/{test_game_id}/join",
            data=join_test_data,
            auth_token=user1_token
        )
        
        if join_test_success:
            print("✅ User 1 successfully joined User 2's game")
            print("✅ NO CONCURRENT GAMES BUG DETECTED")
            return True
        else:
            error_detail = join_test_response.get("detail", "")
            if "cannot join multiple games simultaneously" in error_detail.lower():
                print("\n🐛 BUG CONFIRMED!")
                print("❌ User cannot join games due to 'multiple games simultaneously' error")
                print(f"❌ Error: {error_detail}")
                return False
            else:
                print(f"⚠️  Join failed for different reason: {error_detail}")
                return None
    else:
        print(f"❌ Failed to create test game: {test_game_response}")
        return None

if __name__ == "__main__":
    result = test_concurrent_games_bug()
    
    print("\n" + "=" * 50)
    if result is True:
        print("🎉 RESULT: No concurrent games bug detected")
    elif result is False:
        print("🐛 RESULT: Concurrent games bug CONFIRMED")
        print("\n📋 RECOMMENDED FIXES:")
        print("1. Check that games are properly updated to COMPLETED status")
        print("2. Verify check_user_concurrent_games only checks ACTIVE/REVEAL games")
        print("3. Ensure no race conditions in game completion logic")
    else:
        print("❓ RESULT: Test inconclusive - check logs above")