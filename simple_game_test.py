#!/usr/bin/env python3
"""
Simple Game Join Logic Test
Testing the core game workflow using admin user
"""

import requests
import json
import time
import hashlib
import random
import string

# Configuration
BASE_URL = "https://5b5eaaef-0f5c-4beb-bd84-c46dc395886a.preview.emergentagent.com/api"
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

def hash_move_with_salt(move, salt):
    """Hash game move with salt for commit-reveal scheme."""
    combined = f"{move}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def test_game_workflow():
    """Test the complete game workflow."""
    print("=" * 80)
    print("TESTING GAME JOIN LOGIC - WAITING → ACTIVE → COMPLETED")
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
    
    # Step 2: Ensure admin has gems
    print("\n2. ENSURE ADMIN HAS GEMS")
    inventory_response, inventory_success = make_request("GET", "/gems/inventory", auth_token=admin_token)
    
    if inventory_success:
        ruby_gems = 0
        for gem in inventory_response:
            if gem["type"] == "Ruby":
                ruby_gems = gem["quantity"] - gem["frozen_quantity"]
                break
        
        print(f"Available Ruby gems: {ruby_gems}")
        
        if ruby_gems < 10:
            print("Buying more Ruby gems...")
            buy_response, buy_success = make_request("POST", "/gems/buy?gem_type=Ruby&quantity=20", auth_token=admin_token)
            if buy_success:
                print("✅ Bought 20 Ruby gems")
            else:
                print("❌ Failed to buy gems")
                return False
        else:
            print("✅ Sufficient gems available")
    
    # Step 3: Create a game (should be WAITING status)
    print("\n3. CREATE GAME (Status should be WAITING)")
    
    create_game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 5}
    }
    
    game_response, game_success = make_request("POST", "/games/create", create_game_data, admin_token)
    
    if not game_success:
        print("❌ Game creation failed")
        return False
    
    game_id = game_response.get("game_id")
    if not game_id:
        print("❌ No game_id in response")
        return False
    
    print(f"✅ Game created with ID: {game_id}")
    
    # Check initial status
    status_response, status_success = make_request("GET", f"/games/{game_id}/status", auth_token=admin_token)
    
    if status_success:
        initial_status = status_response.get("status")
        print(f"Initial game status: {initial_status}")
        
        if initial_status == "WAITING":
            print("✅ CORRECT: Game status is WAITING after creation")
        else:
            print(f"❌ INCORRECT: Expected WAITING, got {initial_status}")
            return False
    else:
        print("❌ Failed to check initial game status")
        return False
    
    # Step 4: Get available games to verify our game appears
    print("\n4. VERIFY GAME APPEARS IN AVAILABLE GAMES")
    
    available_response, available_success = make_request("GET", "/games/available", auth_token=admin_token)
    
    if available_success and isinstance(available_response, list):
        our_game = None
        for game in available_response:
            if game.get("game_id") == game_id:
                our_game = game
                break
        
        if our_game:
            print(f"✅ Game found in available games")
            print(f"   Status: {our_game.get('status')}")
            print(f"   Creator: {our_game.get('creator_id')}")
            print(f"   Bet amount: ${our_game.get('bet_amount')}")
        else:
            print("❌ Game not found in available games")
            return False
    else:
        print("❌ Failed to get available games")
        return False
    
    # Step 5: Create a second user account to join the game
    print("\n5. CREATE SECOND USER FOR JOINING")
    
    # Generate unique username and email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    second_user_data = {
        "username": f"testuser_{random_suffix}",
        "email": f"testuser_{random_suffix}@test.com",
        "password": "Test123!",
        "gender": "female"
    }
    
    register_response, register_success = make_request("POST", "/auth/register", second_user_data)
    
    if not register_success:
        print("❌ Second user registration failed")
        return False
    
    verification_token = register_response.get("verification_token")
    if not verification_token:
        print("❌ No verification token received")
        return False
    
    # Verify email
    verify_response, verify_success = make_request("POST", "/auth/verify-email", {"token": verification_token})
    
    if not verify_success:
        print("❌ Email verification failed")
        return False
    
    # Login as second user
    second_login_data = {
        "email": second_user_data["email"],
        "password": second_user_data["password"]
    }
    
    second_login_response, second_login_success = make_request("POST", "/auth/login", second_login_data)
    
    if not second_login_success:
        print("❌ Second user login failed")
        return False
    
    second_user_token = second_login_response["access_token"]
    print("✅ Second user created and logged in")
    
    # Give second user some gems
    buy_gems_response, buy_gems_success = make_request("POST", "/gems/buy?gem_type=Ruby&quantity=10", auth_token=second_user_token)
    
    if buy_gems_success:
        print("✅ Second user has gems")
    else:
        print("❌ Failed to give second user gems")
        return False
    
    # Step 6: Second user joins the game (status should change to ACTIVE)
    print("\n6. SECOND USER JOINS GAME (Status should change to ACTIVE)")
    
    join_game_data = {
        "move": "paper",
        "gems": {"Ruby": 5}
    }
    
    join_response, join_success = make_request("POST", f"/games/{game_id}/join", join_game_data, second_user_token)
    
    if not join_success:
        print("❌ Failed to join game")
        return False
    
    print("✅ Second user joined game successfully")
    
    # Check status after join (should be ACTIVE)
    time.sleep(1)  # Small delay to ensure status update
    
    active_status_response, active_status_success = make_request("GET", f"/games/{game_id}/status", auth_token=admin_token)
    
    if active_status_success:
        active_status = active_status_response.get("status")
        print(f"Game status after join: {active_status}")
        
        if active_status == "ACTIVE":
            print("✅ CORRECT: Game status changed to ACTIVE after join")
            
            # Check if active_deadline is set
            active_deadline = active_status_response.get("active_deadline")
            if active_deadline:
                print(f"✅ Active deadline set: {active_deadline}")
            else:
                print("⚠️  Active deadline not found")
                
        else:
            print(f"❌ INCORRECT: Expected ACTIVE, got {active_status}")
            return False
    else:
        print("❌ Failed to check game status after join")
        return False
    
    # Step 7: Second user chooses move (game should complete)
    print("\n7. SECOND USER CHOOSES MOVE (Game should complete)")
    
    choose_move_data = {
        "move": "paper"
    }
    
    choose_response, choose_success = make_request("POST", f"/games/{game_id}/choose-move", choose_move_data, second_user_token)
    
    if choose_success:
        print("✅ Second user chose move successfully")
        
        # Check final status (should be COMPLETED)
        time.sleep(1)  # Small delay to ensure completion
        
        final_status_response, final_status_success = make_request("GET", f"/games/{game_id}/status", auth_token=admin_token)
        
        if final_status_success:
            final_status = final_status_response.get("status")
            print(f"Final game status: {final_status}")
            
            if final_status == "COMPLETED":
                print("✅ CORRECT: Game status changed to COMPLETED")
                
                # Check winner
                winner_id = final_status_response.get("winner_id")
                if winner_id:
                    print(f"✅ Winner determined: {winner_id}")
                else:
                    print("✅ Game ended in draw")
                
                return True
            else:
                print(f"❌ INCORRECT: Expected COMPLETED, got {final_status}")
                return False
        else:
            print("❌ Failed to check final game status")
            return False
    else:
        print("❌ Failed to choose move")
        return False

def main():
    """Main test function."""
    success = test_game_workflow()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 GAME JOIN LOGIC TEST: PASSED")
        print("✅ Status correctly changes: WAITING → ACTIVE → COMPLETED")
        print("✅ Game workflow functions as expected")
    else:
        print("❌ GAME JOIN LOGIC TEST: FAILED")
        print("❌ Status changes not working correctly")
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    main()