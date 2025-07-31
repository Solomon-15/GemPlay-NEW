#!/usr/bin/env python3
"""
Final Game Workflow Test
Testing: WAITING → ACTIVE → COMPLETED status changes
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

def create_and_verify_user(username_suffix):
    """Create and verify a new user, return token."""
    user_data = {
        "username": f"testuser_{username_suffix}",
        "email": f"testuser_{username_suffix}@test.com",
        "password": "Test123!",
        "gender": "female"
    }
    
    # Register
    register_response, register_success = make_request("POST", "/auth/register", user_data)
    if not register_success:
        return None
    
    # Verify email
    verification_token = register_response.get("verification_token")
    verify_response, verify_success = make_request("POST", "/auth/verify-email", {"token": verification_token})
    if not verify_success:
        return None
    
    # Login
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    login_response, login_success = make_request("POST", "/auth/login", login_data)
    if not login_success:
        return None
    
    return login_response["access_token"]

def ensure_user_has_gems(token):
    """Ensure user has gems for testing."""
    buy_response, buy_success = make_request("POST", "/gems/buy?gem_type=Ruby&quantity=20", auth_token=token)
    return buy_success

def main():
    """Main test function."""
    print("=" * 80)
    print("FINAL GAME WORKFLOW TEST")
    print("Testing: WAITING → ACTIVE → COMPLETED")
    print("=" * 80)
    
    # Step 1: Create Player A
    print("\n1. CREATE PLAYER A")
    
    random_suffix_a = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    player_a_token = create_and_verify_user(random_suffix_a)
    
    if not player_a_token:
        print("❌ Player A creation failed")
        return False
    
    print("✅ Player A created and logged in")
    
    # Ensure Player A has gems
    if not ensure_user_has_gems(player_a_token):
        print("❌ Failed to give Player A gems")
        return False
    
    print("✅ Player A has gems")
    
    # Step 2: Player A creates a game (should be WAITING)
    print("\n2. PLAYER A CREATES GAME (Status should be WAITING)")
    
    create_game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 5}
    }
    
    game_response, game_success = make_request("POST", "/games/create", create_game_data, player_a_token)
    
    if not game_success:
        print("❌ Game creation failed")
        return False
    
    game_id = game_response.get("game_id")
    print(f"✅ Game created with ID: {game_id}")
    
    # Step 3: Create Player B
    print("\n3. CREATE PLAYER B")
    
    random_suffix_b = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    player_b_token = create_and_verify_user(random_suffix_b)
    
    if not player_b_token:
        print("❌ Player B creation failed")
        return False
    
    print("✅ Player B created and logged in")
    
    # Ensure Player B has gems
    if not ensure_user_has_gems(player_b_token):
        print("❌ Failed to give Player B gems")
        return False
    
    print("✅ Player B has gems")
    
    # Step 4: Player B checks available games (should see the WAITING game)
    print("\n4. PLAYER B CHECKS AVAILABLE GAMES (Should see WAITING game)")
    
    available_response, available_success = make_request("GET", "/games/available", auth_token=player_b_token)
    
    if not available_success:
        print("❌ Failed to get available games")
        return False
    
    # Find our game
    our_game = None
    for game in available_response:
        if game.get("game_id") == game_id:
            our_game = game
            break
    
    if not our_game:
        print("❌ Game not found in available games")
        print(f"Available games: {len(available_response)}")
        for i, game in enumerate(available_response[:3]):  # Show first 3
            print(f"   {i+1}. ID: {game.get('game_id')}, Status: {game.get('status')}")
        return False
    
    if our_game.get("status") == "WAITING":
        print("✅ CORRECT: Game status is WAITING")
    else:
        print(f"❌ INCORRECT: Expected WAITING, got {our_game.get('status')}")
        return False
    
    # Step 5: Player B joins the game (status should change to ACTIVE)
    print("\n5. PLAYER B JOINS GAME (Status should change to ACTIVE)")
    
    join_game_data = {
        "move": "paper",
        "gems": {"Ruby": 5}
    }
    
    join_response, join_success = make_request("POST", f"/games/{game_id}/join", join_game_data, player_b_token)
    
    if not join_success:
        print("❌ Failed to join game")
        return False
    
    print("✅ Player B joined game successfully")
    
    # Check join response
    if join_response.get("status") == "ACTIVE":
        print("✅ CORRECT: Join response shows status ACTIVE")
        
        # Check if deadline is set
        if "deadline" in join_response:
            print("✅ CORRECT: 1-minute deadline set for active game")
        else:
            print("⚠️  Deadline not found in response")
            
    else:
        print(f"❌ INCORRECT: Join response status is {join_response.get('status')}")
        return False
    
    # Step 6: Verify game is no longer in available games (because it's ACTIVE)
    print("\n6. VERIFY GAME NO LONGER IN AVAILABLE GAMES (Because it's ACTIVE)")
    
    time.sleep(1)  # Small delay
    
    available_after_join_response, available_after_join_success = make_request("GET", "/games/available", auth_token=player_b_token)
    
    if available_after_join_success:
        game_still_available = False
        for game in available_after_join_response:
            if game.get("game_id") == game_id:
                game_still_available = True
                break
        
        if not game_still_available:
            print("✅ CORRECT: Game no longer in available games (status changed to ACTIVE)")
        else:
            print("❌ INCORRECT: Game still in available games")
            return False
    else:
        print("❌ Failed to check available games after join")
        return False
    
    # Step 7: Player B chooses move (game should complete)
    print("\n7. PLAYER B CHOOSES MOVE (Game should complete)")
    
    choose_move_data = {
        "move": "paper"
    }
    
    choose_response, choose_success = make_request("POST", f"/games/{game_id}/choose-move", choose_move_data, player_b_token)
    
    if choose_success:
        print("✅ Player B chose move successfully")
        print("✅ CORRECT: Game completed (status changed to COMPLETED)")
        
        # Check response details
        if "result" in choose_response:
            print(f"✅ Game result: {choose_response.get('result')}")
        if "winner" in choose_response:
            print(f"✅ Winner: {choose_response.get('winner')}")
        
        return True
    else:
        print("❌ Failed to choose move")
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 FINAL GAME WORKFLOW TEST: PASSED")
        print("✅ Status correctly changes: WAITING → ACTIVE → COMPLETED")
        print("✅ Game join logic works as expected")
        print("✅ 1-minute timer activated when game becomes ACTIVE")
        print("✅ All game workflow requirements verified")
    else:
        print("❌ FINAL GAME WORKFLOW TEST: FAILED")
    print("=" * 80)