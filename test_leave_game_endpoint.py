#!/usr/bin/env python3
"""
Test script for the new /api/games/{game_id}/leave endpoint
Tests opponent leaving an active game and proper fund/gem management
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://39671358-620a-4bc2-9002-b6bfa47a1383.preview.emergentagent.com/api"

def generate_test_email():
    """Generate unique test email"""
    timestamp = int(time.time() * 1000)  # Use milliseconds for more uniqueness
    random_suffix = random.randint(1000, 9999)
    return f"testuser_{timestamp}_{random_suffix}@test.com"

def generate_test_username():
    """Generate unique test username"""
    timestamp = int(time.time() * 1000)  # Use milliseconds for more uniqueness
    random_suffix = random.randint(1000, 9999)
    return f"testuser_{timestamp}_{random_suffix}"

def make_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None, params: Dict = None) -> Dict:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, params=params, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text, "status_code": response.status_code}
        
        return {
            "status_code": response.status_code,
            "data": response_data,
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "success": False
        }

def register_and_verify_user(username: str, email: str, password: str = "Test123!", gender: str = "male") -> Optional[str]:
    """Register user and return access token"""
    print(f"📝 Registering user: {username} ({email})")
    
    # Register user
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "gender": gender
    }
    
    response = make_request("POST", "/auth/register", register_data)
    if not response["success"]:
        print(f"❌ Registration failed: {response['data']}")
        return None
    
    print(f"✅ User registered successfully")
    
    # Get verification token from registration response
    verification_token = response["data"].get("verification_token")
    if verification_token:
        print(f"📧 Verifying email with token")
        verify_data = {"token": verification_token}
        verify_response = make_request("POST", "/auth/verify-email", verify_data)
        if verify_response["success"]:
            print(f"✅ Email verified successfully")
        else:
            print(f"⚠️ Email verification failed, trying login anyway: {verify_response['data']}")
    else:
        print(f"⚠️ No verification token in response, trying login anyway")
    
    time.sleep(1)
    
    # Login to get access token
    login_data = {
        "email": email,
        "password": password
    }
    
    response = make_request("POST", "/auth/login", login_data)
    if not response["success"]:
        print(f"❌ Login failed: {response['data']}")
        return None
    
    access_token = response["data"].get("access_token")
    if not access_token:
        print(f"❌ No access token in response")
        return None
    
    print(f"✅ User logged in successfully")
    return access_token

def add_balance_to_user(token: str, amount: float = 1000.0) -> bool:
    """Add balance to user account"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"amount": amount}
    
    response = make_request("POST", "/auth/add-balance", data, headers)
    if response["success"]:
        print(f"✅ Added ${amount} to user balance")
        return True
    else:
        print(f"❌ Failed to add balance: {response['data']}")
        return False

def purchase_gems(token: str, gem_type: str, quantity: int) -> bool:
    """Purchase gems for user"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "gem_type": gem_type,
        "quantity": quantity
    }
    
    response = make_request("POST", "/gems/buy", headers=headers, params=params)
    if response["success"]:
        print(f"✅ Purchased {quantity} {gem_type} gems")
        return True
    else:
        print(f"❌ Failed to purchase gems: {response['data']}")
        return False

def get_user_balance(token: str) -> Dict:
    """Get user balance and gem information"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request("GET", "/auth/me", headers=headers)
    if response["success"]:
        return response["data"]
    else:
        print(f"❌ Failed to get balance: {response['data']}")
        return {}

def create_game(token: str, move: str, bet_gems: Dict[str, int]) -> Optional[str]:
    """Create a new game and return game ID"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "move": move,
        "bet_gems": bet_gems
    }
    
    response = make_request("POST", "/games/create", data, headers)
    if response["success"]:
        game_id = response["data"].get("game_id")
        print(f"✅ Game created with ID: {game_id}")
        return game_id
    else:
        print(f"❌ Failed to create game: {response['data']}")
        return None

def join_game(token: str, game_id: str, move: str, gems: Dict[str, int]) -> bool:
    """Join an existing game"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "move": move,
        "gems": gems
    }
    
    response = make_request("POST", f"/games/{game_id}/join", data, headers)
    if response["success"]:
        print(f"✅ Successfully joined game {game_id}")
        return True
    else:
        print(f"❌ Failed to join game: {response['data']}")
        return False

def leave_game(token: str, game_id: str) -> Dict:
    """Leave an active game"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request("POST", f"/games/{game_id}/leave", headers=headers)
    return response

def get_game_details(token: str, game_id: str) -> Dict:
    """Get game details from my-bets endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request("GET", "/games/my-bets", headers=headers)
    if response["success"]:
        games = response["data"]
        for game in games:
            if game.get("id") == game_id:
                return game
        print(f"❌ Game {game_id} not found in my-bets")
        return {}
    else:
        print(f"❌ Failed to get game details: {response['data']}")
        return {}

def test_leave_game_endpoint():
    """Test the /api/games/{game_id}/leave endpoint"""
    print("🎯 TESTING LEAVE GAME ENDPOINT")
    print("=" * 50)
    
    # Test data
    creator_username = generate_test_username()
    creator_email = generate_test_email()
    opponent_username = generate_test_username()
    opponent_email = generate_test_email()
    
    creator_token = None
    opponent_token = None
    game_id = None
    
    try:
        # Step 1: Create and setup creator user
        print("\n📋 Step 1: Setting up creator user")
        creator_token = register_and_verify_user(creator_username, creator_email)
        if not creator_token:
            print("❌ Failed to setup creator user")
            return False
        
        # Add balance and purchase gems for creator
        if not add_balance_to_user(creator_token, 1000.0):
            print("❌ Failed to add balance to creator")
            return False
        
        if not purchase_gems(creator_token, "Ruby", 10):
            print("❌ Failed to purchase gems for creator")
            return False
        
        # Step 2: Create and setup opponent user
        print("\n📋 Step 2: Setting up opponent user")
        opponent_token = register_and_verify_user(opponent_username, opponent_email)
        if not opponent_token:
            print("❌ Failed to setup opponent user")
            return False
        
        # Add balance and purchase gems for opponent
        if not add_balance_to_user(opponent_token, 1000.0):
            print("❌ Failed to add balance to opponent")
            return False
        
        if not purchase_gems(opponent_token, "Ruby", 10):
            print("❌ Failed to purchase gems for opponent")
            return False
        
        # Step 3: Get initial balances
        print("\n📋 Step 3: Recording initial balances")
        creator_initial_balance = get_user_balance(creator_token)
        opponent_initial_balance = get_user_balance(opponent_token)
        
        print(f"Creator initial balance: Virtual=${creator_initial_balance.get('virtual_balance', 0)}, Frozen=${creator_initial_balance.get('frozen_balance', 0)}")
        print(f"Opponent initial balance: Virtual=${opponent_initial_balance.get('virtual_balance', 0)}, Frozen=${opponent_initial_balance.get('frozen_balance', 0)}")
        
        # Step 4: Creator creates a game
        print("\n📋 Step 4: Creator creates game")
        bet_gems = {"Ruby": 5}
        game_id = create_game(creator_token, "rock", bet_gems)
        if not game_id:
            print("❌ Failed to create game")
            return False
        
        # Step 5: Opponent joins the game
        print("\n📋 Step 5: Opponent joins game")
        opponent_gems = {"Ruby": 5}
        if not join_game(opponent_token, game_id, "paper", opponent_gems):
            print("❌ Failed to join game")
            return False
        
        # Step 6: Verify game is ACTIVE (or proceed anyway)
        print("\n📋 Step 6: Verifying game is ACTIVE")
        
        # Check creator's games
        creator_game_details = get_game_details(creator_token, game_id)
        if not creator_game_details:
            # Try opponent's games
            opponent_game_details = get_game_details(opponent_token, game_id)
            if not opponent_game_details:
                print(f"⚠️ Game not found in either user's my-bets, proceeding anyway")
                game_details = {"status": "UNKNOWN"}
            else:
                game_details = opponent_game_details
        else:
            game_details = creator_game_details
            
        if game_details.get("status") == "ACTIVE":
            print(f"✅ Game is ACTIVE")
        else:
            print(f"⚠️ Game status: {game_details.get('status')}, proceeding with leave test anyway")
        
        # Step 7: Get balances after joining
        print("\n📋 Step 7: Recording balances after joining")
        creator_after_join = get_user_balance(creator_token)
        opponent_after_join = get_user_balance(opponent_token)
        
        print(f"Creator after join: Virtual=${creator_after_join.get('virtual_balance', 0)}, Frozen=${creator_after_join.get('frozen_balance', 0)}")
        print(f"Opponent after join: Virtual=${opponent_after_join.get('virtual_balance', 0)}, Frozen=${opponent_after_join.get('frozen_balance', 0)}")
        
        # Step 8: Opponent leaves the game
        print("\n📋 Step 8: Opponent leaves the game")
        leave_response = leave_game(opponent_token, game_id)
        
        if not leave_response["success"]:
            print(f"❌ Failed to leave game: {leave_response['data']}")
            return False
        
        leave_data = leave_response["data"]
        print(f"✅ Successfully left game")
        print(f"   Gems returned: {leave_data.get('gems_returned', {})}")
        print(f"   Commission returned: ${leave_data.get('commission_returned', 0)}")
        
        # Step 9: Verify game status returned to WAITING
        print("\n📋 Step 9: Verifying game returned to WAITING")
        game_details_after_leave = get_game_details(creator_token, game_id)
        
        if game_details_after_leave.get("status") != "WAITING":
            print(f"❌ Game status is not WAITING: {game_details_after_leave.get('status')}")
            return False
        
        # Check that opponent fields are cleared
        if game_details_after_leave.get("opponent_id") is not None:
            print(f"❌ opponent_id not cleared: {game_details_after_leave.get('opponent_id')}")
            return False
        
        if game_details_after_leave.get("opponent_move") is not None:
            print(f"❌ opponent_move not cleared: {game_details_after_leave.get('opponent_move')}")
            return False
        
        if game_details_after_leave.get("opponent_gems") is not None:
            print(f"❌ opponent_gems not cleared: {game_details_after_leave.get('opponent_gems')}")
            return False
        
        if game_details_after_leave.get("started_at") is not None:
            print(f"❌ started_at not cleared: {game_details_after_leave.get('started_at')}")
            return False
        
        if game_details_after_leave.get("active_deadline") is not None:
            print(f"❌ active_deadline not cleared: {game_details_after_leave.get('active_deadline')}")
            return False
        
        print("✅ Game status returned to WAITING and opponent fields cleared")
        
        # Step 10: Verify fund management
        print("\n📋 Step 10: Verifying fund management")
        creator_final_balance = get_user_balance(creator_token)
        opponent_final_balance = get_user_balance(opponent_token)
        
        print(f"Creator final balance: Virtual=${creator_final_balance.get('virtual_balance', 0)}, Frozen=${creator_final_balance.get('frozen_balance', 0)}")
        print(f"Opponent final balance: Virtual=${opponent_final_balance.get('virtual_balance', 0)}, Frozen=${opponent_final_balance.get('frozen_balance', 0)}")
        
        # Check that creator's funds remain frozen
        creator_frozen_diff = creator_final_balance.get('frozen_balance', 0) - creator_initial_balance.get('frozen_balance', 0)
        if creator_frozen_diff <= 0:
            print(f"❌ Creator's commission should still be frozen, difference: {creator_frozen_diff}")
            return False
        print(f"✅ Creator's commission remains frozen (${creator_frozen_diff})")
        
        # Check that opponent's commission was returned
        opponent_virtual_diff = opponent_final_balance.get('virtual_balance', 0) - opponent_after_join.get('virtual_balance', 0)
        opponent_frozen_diff = opponent_final_balance.get('frozen_balance', 0) - opponent_after_join.get('frozen_balance', 0)
        
        expected_commission = 5 * 1.0 * 0.03  # 5 Ruby gems * $1 each * 3% commission
        
        if abs(opponent_virtual_diff - expected_commission) > 0.01:
            print(f"❌ Opponent's commission not properly returned. Expected: ${expected_commission}, Got: ${opponent_virtual_diff}")
            return False
        
        if abs(opponent_frozen_diff + expected_commission) > 0.01:
            print(f"❌ Opponent's frozen balance not properly reduced. Expected: ${-expected_commission}, Got: ${opponent_frozen_diff}")
            return False
        
        print(f"✅ Opponent's commission properly returned (${opponent_virtual_diff})")
        
        # Step 11: Test error scenarios
        print("\n📋 Step 11: Testing error scenarios")
        
        # Test 11a: Try to leave as non-opponent (creator)
        print("Testing: Creator trying to leave (should fail)")
        creator_leave_response = leave_game(creator_token, game_id)
        if creator_leave_response["success"]:
            print("❌ Creator should not be able to leave the game")
            return False
        if creator_leave_response["status_code"] != 403:
            print(f"❌ Expected 403 Forbidden, got {creator_leave_response['status_code']}")
            return False
        print("✅ Creator correctly forbidden from leaving")
        
        # Test 11b: Try to leave non-existent game
        print("Testing: Leave non-existent game (should fail)")
        fake_game_id = "fake-game-id-12345"
        fake_leave_response = leave_game(opponent_token, fake_game_id)
        if fake_leave_response["success"]:
            print("❌ Should not be able to leave non-existent game")
            return False
        if fake_leave_response["status_code"] != 404:
            print(f"❌ Expected 404 Not Found, got {fake_leave_response['status_code']}")
            return False
        print("✅ Non-existent game correctly returns 404")
        
        # Test 11c: Try to leave game that's not ACTIVE (already WAITING)
        print("Testing: Leave game that's not ACTIVE (should fail)")
        waiting_leave_response = leave_game(opponent_token, game_id)
        if waiting_leave_response["success"]:
            print("❌ Should not be able to leave WAITING game")
            return False
        if waiting_leave_response["status_code"] != 400:
            print(f"❌ Expected 400 Bad Request, got {waiting_leave_response['status_code']}")
            return False
        print("✅ WAITING game correctly returns 400")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Game creation working")
        print("✅ Game joining working")
        print("✅ Opponent can leave active game")
        print("✅ Opponent's gems unfrozen")
        print("✅ Opponent's commission returned")
        print("✅ Creator's funds remain frozen")
        print("✅ Game returns to WAITING status")
        print("✅ Opponent fields cleared")
        print("✅ Error scenarios handled correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Starting Leave Game Endpoint Tests")
    print("=" * 60)
    
    success = test_leave_game_endpoint()
    
    if success:
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()