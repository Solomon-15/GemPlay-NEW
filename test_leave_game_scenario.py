#!/usr/bin/env python3
"""
Test script to create a scenario where game remains ACTIVE and test leave functionality
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional
import random

# Configuration
BASE_URL = "https://2afcdb68-e337-4e72-a16b-588ed6811928.preview.emergentagent.com/api"

def generate_test_email():
    """Generate unique test email"""
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    return f"testuser_{timestamp}_{random_suffix}@test.com"

def generate_test_username():
    """Generate unique test username"""
    timestamp = int(time.time() * 1000)
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

def register_and_login_user(username: str, email: str, password: str = "Test123!") -> Optional[str]:
    """Register and login user"""
    # Register
    register_data = {
        "username": username,
        "email": email,
        "password": password,
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
    login_data = {"email": email, "password": password}
    response = make_request("POST", "/auth/login", login_data)
    if not response["success"]:
        print(f"❌ Login failed: {response['data']}")
        return None
    
    return response["data"].get("access_token")

def setup_user_with_balance_and_gems(token: str) -> bool:
    """Setup user with balance and gems"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add balance
    balance_data = {"amount": 1000.0}
    response = make_request("POST", "/auth/add-balance", balance_data, headers)
    if not response["success"]:
        print(f"❌ Failed to add balance: {response['data']}")
        return False
    
    # Purchase gems
    params = {"gem_type": "Ruby", "quantity": 10}
    response = make_request("POST", "/gems/buy", headers=headers, params=params)
    if not response["success"]:
        print(f"❌ Failed to purchase gems: {response['data']}")
        return False
    
    return True

def create_game_directly_in_db(creator_id: str, move: str, gems: Dict[str, int]) -> Optional[str]:
    """Create a game directly bypassing normal flow to test ACTIVE state"""
    # This would need to be implemented via admin API or database manipulation
    # For now, we'll use normal creation
    pass

def test_leave_game_scenario():
    """Test leaving a game that remains in ACTIVE state"""
    print("🎯 TESTING LEAVE GAME SCENARIO")
    print("=" * 50)
    
    # Setup users
    creator_username = generate_test_username()
    creator_email = generate_test_email()
    opponent_username = generate_test_username()
    opponent_email = generate_test_email()
    
    print(f"👤 Creator: {creator_username} ({creator_email})")
    print(f"👤 Opponent: {opponent_username} ({opponent_email})")
    
    # Register and setup creator
    creator_token = register_and_login_user(creator_username, creator_email)
    if not creator_token:
        print("❌ Failed to setup creator")
        return
    
    if not setup_user_with_balance_and_gems(creator_token):
        print("❌ Failed to setup creator balance/gems")
        return
    
    # Register and setup opponent
    opponent_token = register_and_login_user(opponent_username, opponent_email)
    if not opponent_token:
        print("❌ Failed to setup opponent")
        return
    
    if not setup_user_with_balance_and_gems(opponent_token):
        print("❌ Failed to setup opponent balance/gems")
        return
    
    print("✅ Both users setup successfully")
    
    # Create game
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
    
    # Get balances before join
    creator_balance_before = make_request("GET", "/auth/me", headers=creator_headers)
    opponent_balance_before = make_request("GET", "/auth/me", headers={"Authorization": f"Bearer {opponent_token}"})
    
    print(f"Creator balance before join: Virtual=${creator_balance_before['data'].get('virtual_balance', 0)}, Frozen=${creator_balance_before['data'].get('frozen_balance', 0)}")
    print(f"Opponent balance before join: Virtual=${opponent_balance_before['data'].get('virtual_balance', 0)}, Frozen=${opponent_balance_before['data'].get('frozen_balance', 0)}")
    
    # Try to join game with invalid data to potentially cause error
    opponent_headers = {"Authorization": f"Bearer {opponent_token}"}
    
    # First try normal join
    join_data = {
        "move": "paper",
        "gems": {"Ruby": 1}
    }
    
    print(f"🔄 Opponent attempting to join game...")
    response = make_request("POST", f"/games/{game_id}/join", join_data, opponent_headers)
    
    if response["success"]:
        print("✅ Join successful (game likely completed)")
        print(f"Join response: {response['data']}")
        
        # Check if game completed successfully
        print("🔍 Checking game completion...")
        
        # Get balances after join
        creator_balance_after = make_request("GET", "/auth/me", headers=creator_headers)
        opponent_balance_after = make_request("GET", "/auth/me", headers={"Authorization": f"Bearer {opponent_token}"})
        
        print(f"Creator balance after join: Virtual=${creator_balance_after['data'].get('virtual_balance', 0)}, Frozen=${creator_balance_after['data'].get('frozen_balance', 0)}")
        print(f"Opponent balance after join: Virtual=${opponent_balance_after['data'].get('virtual_balance', 0)}, Frozen=${opponent_balance_after['data'].get('frozen_balance', 0)}")
        
        # Try to leave anyway to test error handling
        print("🚪 Testing leave endpoint on completed game...")
        leave_response = make_request("POST", f"/games/{game_id}/leave", headers=opponent_headers)
        
        if leave_response["success"]:
            print("✅ Leave endpoint worked (unexpected)")
            print(f"Leave response: {leave_response['data']}")
        else:
            print(f"❌ Leave endpoint failed as expected: {leave_response['data']}")
        
    else:
        print(f"❌ Join failed: {response['data']}")
        
        # If join failed, the game might be in ACTIVE state
        # Try to leave
        print("🚪 Testing leave endpoint on failed join...")
        leave_response = make_request("POST", f"/games/{game_id}/leave", headers=opponent_headers)
        
        if leave_response["success"]:
            print("✅ Leave endpoint worked after failed join")
            print(f"Leave response: {leave_response['data']}")
        else:
            print(f"❌ Leave endpoint failed: {leave_response['data']}")

if __name__ == "__main__":
    test_leave_game_scenario()