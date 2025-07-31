#!/usr/bin/env python3
"""
Deep dive test for concurrent games issue.
This test specifically looks for edge cases and race conditions.
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
    
    print(f"🔗 {method} {endpoint}")
    if data:
        print(f"📤 Data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"📥 Response: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        response_data = {"text": response.text}
        print(f"📥 Text: {response.text}")
    
    success = response.status_code == expected_status
    return response_data, success

def create_unique_user():
    """Create a unique test user."""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    user_data = {
        "username": f"deeptest_{random_suffix}",
        "email": f"deeptest_{random_suffix}@test.com",
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

def deep_test_concurrent_games():
    """Deep test for concurrent games issues."""
    print("🔬 DEEP CONCURRENT GAMES TESTING")
    print("=" * 60)
    
    # Create test users
    print("\n1️⃣ Creating test users...")
    user1_token, user1_id = create_unique_user()
    user2_token, user2_id = create_unique_user()
    
    if not user1_token or not user2_token:
        print("❌ Failed to create test users")
        return
    
    print(f"✅ User 1: {user1_id}")
    print(f"✅ User 2: {user2_id}")
    
    # Buy gems
    print("\n2️⃣ Setting up gems...")
    for token in [user1_token, user2_token]:
        make_request("POST", "/gems/buy?gem_type=Ruby&quantity=100", auth_token=token)
    
    # Test multiple game scenarios
    scenarios = [
        "Single game completion",
        "Multiple rapid games",
        "Game with waiting period",
        "Cross-user game joining"
    ]
    
    for i, scenario in enumerate(scenarios, 3):
        print(f"\n{i}️⃣ Testing: {scenario}")
        print("-" * 40)
        
        if scenario == "Single game completion":
            test_single_game_completion(user1_token, user1_id, user2_token, user2_id)
        elif scenario == "Multiple rapid games":
            test_multiple_rapid_games(user1_token, user1_id, user2_token, user2_id)
        elif scenario == "Game with waiting period":
            test_game_with_waiting(user1_token, user1_id, user2_token, user2_id)
        elif scenario == "Cross-user game joining":
            test_cross_user_joining(user1_token, user1_id, user2_token, user2_id)

def test_single_game_completion(user1_token, user1_id, user2_token, user2_id):
    """Test single game completion scenario."""
    print("🎯 Testing single game completion...")
    
    # User 1 creates game
    create_data = {"move": "rock", "bet_gems": {"Ruby": 10}}
    game_response, _ = make_request("POST", "/games/create", data=create_data, auth_token=user1_token)
    game_id = game_response.get("game_id")
    
    if not game_id:
        print("❌ Failed to create game")
        return
    
    # Check user status before join
    print("\n📊 User 1 status BEFORE opponent joins:")
    debug_response, _ = make_request("GET", f"/debug/user-games/{user1_id}", auth_token=user1_token)
    if debug_response:
        print(f"   Can join: {debug_response.get('can_join_games')}")
        print(f"   Active as creator: {debug_response.get('active_as_creator')}")
        print(f"   Waiting as creator: {debug_response.get('waiting_as_creator')}")
    
    # User 2 joins
    join_data = {"move": "paper", "gems": {"Ruby": 10}}
    join_response, _ = make_request("POST", f"/games/{game_id}/join", data=join_data, auth_token=user2_token)
    
    # Check user status immediately after join
    print("\n📊 User 1 status IMMEDIATELY after game completion:")
    debug_response, _ = make_request("GET", f"/debug/user-games/{user1_id}", auth_token=user1_token)
    if debug_response:
        can_join = debug_response.get('can_join_games')
        print(f"   Can join: {can_join}")
        print(f"   Active as creator: {debug_response.get('active_as_creator')}")
        print(f"   Active as opponent: {debug_response.get('active_as_opponent')}")
        
        if not can_join:
            print("🐛 POTENTIAL BUG: User cannot join immediately after completion")
            active_creator = debug_response.get('active_games_creator', [])
            active_opponent = debug_response.get('active_games_opponent', [])
            print(f"   Active creator games: {active_creator}")
            print(f"   Active opponent games: {active_opponent}")
        else:
            print("✅ User can join games after completion")

def test_multiple_rapid_games(user1_token, user1_id, user2_token, user2_id):
    """Test multiple rapid game completions."""
    print("🎯 Testing multiple rapid games...")
    
    for i in range(3):
        print(f"\n🎮 Game {i+1}/3")
        
        # Create and complete game
        create_data = {"move": "rock", "bet_gems": {"Ruby": 5}}
        game_response, _ = make_request("POST", "/games/create", data=create_data, auth_token=user1_token)
        game_id = game_response.get("game_id")
        
        if game_id:
            join_data = {"move": "scissors", "gems": {"Ruby": 5}}
            make_request("POST", f"/games/{game_id}/join", data=join_data, auth_token=user2_token)
            
            # Check status after each game
            debug_response, _ = make_request("GET", f"/debug/user-games/{user1_id}", auth_token=user1_token)
            if debug_response:
                can_join = debug_response.get('can_join_games')
                print(f"   After game {i+1}: Can join = {can_join}")
                
                if not can_join:
                    print(f"🐛 BUG DETECTED after game {i+1}")
                    return
        
        # Small delay between games
        time.sleep(0.5)
    
    print("✅ All rapid games completed successfully")

def test_game_with_waiting(user1_token, user1_id, user2_token, user2_id):
    """Test game creation with waiting period."""
    print("🎯 Testing game with waiting period...")
    
    # User 1 creates game
    create_data = {"move": "paper", "bet_gems": {"Ruby": 8}}
    game_response, _ = make_request("POST", "/games/create", data=create_data, auth_token=user1_token)
    game_id = game_response.get("game_id")
    
    if not game_id:
        print("❌ Failed to create game")
        return
    
    # Wait a bit before joining
    print("⏳ Waiting 3 seconds before join...")
    time.sleep(3)
    
    # Check status during waiting
    debug_response, _ = make_request("GET", f"/debug/user-games/{user1_id}", auth_token=user1_token)
    if debug_response:
        print(f"   During wait: Can join = {debug_response.get('can_join_games')}")
        print(f"   Waiting games: {debug_response.get('waiting_as_creator')}")
    
    # User 2 joins
    join_data = {"move": "scissors", "gems": {"Ruby": 8}}
    make_request("POST", f"/games/{game_id}/join", data=join_data, auth_token=user2_token)
    
    # Check final status
    debug_response, _ = make_request("GET", f"/debug/user-games/{user1_id}", auth_token=user1_token)
    if debug_response:
        can_join = debug_response.get('can_join_games')
        print(f"   After completion: Can join = {can_join}")
        
        if not can_join:
            print("🐛 BUG DETECTED in waiting scenario")
        else:
            print("✅ Waiting scenario completed successfully")

def test_cross_user_joining(user1_token, user1_id, user2_token, user2_id):
    """Test cross-user game joining scenarios."""
    print("🎯 Testing cross-user game joining...")
    
    # Both users create games simultaneously
    create_data1 = {"move": "rock", "bet_gems": {"Ruby": 6}}
    create_data2 = {"move": "paper", "bet_gems": {"Ruby": 6}}
    
    game1_response, _ = make_request("POST", "/games/create", data=create_data1, auth_token=user1_token)
    game2_response, _ = make_request("POST", "/games/create", data=create_data2, auth_token=user2_token)
    
    game1_id = game1_response.get("game_id")
    game2_id = game2_response.get("game_id")
    
    if not game1_id or not game2_id:
        print("❌ Failed to create games")
        return
    
    print(f"   Game 1 (User 1): {game1_id}")
    print(f"   Game 2 (User 2): {game2_id}")
    
    # User 1 tries to join User 2's game (while having own waiting game)
    join_data = {"move": "scissors", "gems": {"Ruby": 6}}
    join_response, join_success = make_request(
        "POST", f"/games/{game2_id}/join", 
        data=join_data, 
        auth_token=user1_token
    )
    
    if not join_success:
        error_detail = join_response.get("detail", "")
        if "cannot join multiple games simultaneously" in error_detail.lower():
            print("🐛 BUG DETECTED: Cannot join while having waiting game")
            print(f"   Error: {error_detail}")
        else:
            print(f"⚠️  Join failed for different reason: {error_detail}")
    else:
        print("✅ Successfully joined while having waiting game")
        
        # Check final status
        debug_response, _ = make_request("GET", f"/debug/user-games/{user1_id}", auth_token=user1_token)
        if debug_response:
            print(f"   Final can join status: {debug_response.get('can_join_games')}")

if __name__ == "__main__":
    deep_test_concurrent_games()
    print("\n" + "=" * 60)
    print("🏁 DEEP TESTING COMPLETED")
    print("Check the logs above for any detected bugs or issues.")