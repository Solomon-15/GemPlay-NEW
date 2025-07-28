#!/usr/bin/env python3
"""
Test script to manually create ACTIVE game state and test leave functionality
"""
import requests
import json
import time
import random
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://c3094430-a67a-4704-b959-4fd10b62d970.preview.emergentagent.com/api"

def generate_unique_id():
    """Generate unique ID for test users"""
    return f"test_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

def make_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None, params: Dict = None) -> Dict:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, params=params, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
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

def setup_test_user() -> Optional[str]:
    """Setup a test user with balance and gems"""
    unique_id = generate_unique_id()
    username = f"testuser_{unique_id}"
    email = f"testuser_{unique_id}@test.com"
    
    # Register
    register_data = {
        "username": username,
        "email": email,
        "password": "Test123!",
        "gender": "male"
    }
    
    response = make_request("POST", "/auth/register", register_data)
    if not response["success"]:
        print(f"❌ Registration failed: {response['data']}")
        return None
    
    # Verify email
    verification_token = response["data"].get("verification_token")
    if verification_token:
        verify_data = {"token": verification_token}
        make_request("POST", "/auth/verify-email", verify_data)
    
    time.sleep(1)
    
    # Login
    login_data = {"email": email, "password": "Test123!"}
    response = make_request("POST", "/auth/login", login_data)
    if not response["success"]:
        print(f"❌ Login failed: {response['data']}")
        return None
    
    token = response["data"].get("access_token")
    if not token:
        return None
    
    # Add balance
    headers = {"Authorization": f"Bearer {token}"}
    balance_data = {"amount": 1000.0}
    make_request("POST", "/auth/add-balance", balance_data, headers)
    
    # Purchase gems
    params = {"gem_type": "Ruby", "quantity": 10}
    make_request("POST", "/gems/buy", headers=headers, params=params)
    
    print(f"✅ User setup: {username}")
    return token

def test_leave_with_debug():
    """Test leave functionality with debug information"""
    print("🎯 TESTING LEAVE GAME WITH DEBUG INFO")
    print("=" * 50)
    
    # Setup two test users
    print("🔧 Setting up test users...")
    creator_token = setup_test_user()
    opponent_token = setup_test_user()
    
    if not creator_token or not opponent_token:
        print("❌ Failed to setup test users")
        return
    
    # Get user IDs
    creator_info = make_request("GET", "/auth/me", headers={"Authorization": f"Bearer {creator_token}"})
    opponent_info = make_request("GET", "/auth/me", headers={"Authorization": f"Bearer {opponent_token}"})
    
    creator_id = creator_info["data"]["id"]
    opponent_id = opponent_info["data"]["id"]
    
    print(f"👤 Creator ID: {creator_id}")
    print(f"👤 Opponent ID: {opponent_id}")
    
    # Create game
    print("🎮 Creating game...")
    creator_headers = {"Authorization": f"Bearer {creator_token}"}
    create_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 1}
    }
    
    response = make_request("POST", "/games/create", create_data, creator_headers)
    if not response["success"]:
        print(f"❌ Failed to create game: {response['data']}")
        return
    
    game_id = response["data"].get("game_id")
    print(f"✅ Game created: {game_id}")
    
    # Check active games before join
    print("🔍 Checking active games before join...")
    debug_response = make_request("GET", f"/debug/user-games/{opponent_id}", headers={"Authorization": f"Bearer {opponent_token}"})
    if debug_response["success"]:
        print(f"Opponent active games before join: {debug_response['data'].get('active_as_opponent', 0)}")
    
    # Get balances before join
    creator_balance = make_request("GET", "/auth/me", headers=creator_headers)["data"]
    opponent_balance = make_request("GET", "/auth/me", headers={"Authorization": f"Bearer {opponent_token}"})["data"]
    
    print(f"💰 Creator balance before join: Virtual=${creator_balance.get('virtual_balance', 0)}, Frozen=${creator_balance.get('frozen_balance', 0)}")
    print(f"💰 Opponent balance before join: Virtual=${opponent_balance.get('virtual_balance', 0)}, Frozen=${opponent_balance.get('frozen_balance', 0)}")
    
    # Try to join game with a deliberate error to keep it ACTIVE
    print("🔄 Attempting to join game...")
    opponent_headers = {"Authorization": f"Bearer {opponent_token}"}
    
    # First, let's try a partial join by creating problematic data
    # We'll use normal join but monitor the state
    join_data = {
        "move": "paper",
        "gems": {"Ruby": 1}
    }
    
    join_response = make_request("POST", f"/games/{game_id}/join", join_data, opponent_headers)
    
    if join_response["success"]:
        print("✅ Join successful (game completed)")
        print(f"Game result: {join_response['data'].get('result', 'Unknown')}")
        
        # Check if there are any active games
        debug_response = make_request("GET", f"/debug/user-games/{opponent_id}", headers=opponent_headers)
        if debug_response["success"]:
            active_games = debug_response['data'].get('active_games_opponent', [])
            print(f"Active games after join: {len(active_games)}")
            
            if active_games:
                # There is an active game! Try to leave it
                active_game_id = active_games[0]['id']
                print(f"🚪 Found active game {active_game_id}, trying to leave...")
                
                leave_response = make_request("POST", f"/games/{active_game_id}/leave", headers=opponent_headers)
                
                if leave_response["success"]:
                    print("✅ Successfully left active game!")
                    print(f"Leave response: {leave_response['data']}")
                    
                    # Check balances after leave
                    opponent_balance_after = make_request("GET", "/auth/me", headers=opponent_headers)["data"]
                    print(f"💰 Opponent balance after leave: Virtual=${opponent_balance_after.get('virtual_balance', 0)}, Frozen=${opponent_balance_after.get('frozen_balance', 0)}")
                    
                else:
                    print(f"❌ Failed to leave active game: {leave_response['data']}")
            else:
                print("ℹ️ No active games found - normal game completion")
        
    else:
        print(f"❌ Join failed: {join_response['data']}")
        
        # Check if game is now ACTIVE due to failed join
        debug_response = make_request("GET", f"/debug/user-games/{opponent_id}", headers=opponent_headers)
        if debug_response["success"]:
            active_games = debug_response['data'].get('active_games_opponent', [])
            print(f"Active games after failed join: {len(active_games)}")
            
            if active_games:
                # Try to leave the active game
                active_game_id = active_games[0]['id']
                print(f"🚪 Trying to leave active game {active_game_id}...")
                
                leave_response = make_request("POST", f"/games/{active_game_id}/leave", headers=opponent_headers)
                
                if leave_response["success"]:
                    print("✅ Successfully left active game!")
                    print(f"Leave response: {leave_response['data']}")
                else:
                    print(f"❌ Failed to leave active game: {leave_response['data']}")
    
    # Final balance check
    print("\n📊 Final Balance Check:")
    creator_final = make_request("GET", "/auth/me", headers=creator_headers)["data"]
    opponent_final = make_request("GET", "/auth/me", headers=opponent_headers)["data"]
    
    print(f"💰 Creator final balance: Virtual=${creator_final.get('virtual_balance', 0)}, Frozen=${creator_final.get('frozen_balance', 0)}")
    print(f"💰 Opponent final balance: Virtual=${opponent_final.get('virtual_balance', 0)}, Frozen=${opponent_final.get('frozen_balance', 0)}")

if __name__ == "__main__":
    test_leave_with_debug()