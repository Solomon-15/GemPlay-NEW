#!/usr/bin/env python3
import requests
import json
import time

# Configuration
BASE_URL = "https://2afcdb68-e337-4e72-a16b-588ed6811928.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def make_request(method, endpoint, data=None, headers=None, auth_token=None):
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
    
    return response_data, response.status_code

def create_test_user(suffix):
    """Create and verify a test user."""
    user_data = {
        "username": f"resettest_{suffix}_{int(time.time())}",
        "email": f"resettest_{suffix}_{int(time.time())}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    # Register
    response, status = make_request("POST", "/auth/register", data=user_data)
    if status != 200:
        return None, None
    
    # Verify email
    token = response.get("verification_token")
    if token:
        make_request("POST", "/auth/verify-email", data={"token": token})
    
    # Login
    login_response, login_status = make_request("POST", "/auth/login", data={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    
    if login_status == 200:
        return login_response.get("access_token"), user_data["username"]
    
    return None, None

def test_comprehensive_admin_reset():
    """Test the admin reset-all endpoint with active games."""
    print("=== COMPREHENSIVE ADMIN RESET-ALL TEST ===\n")
    
    # Step 1: Login as admin
    print("1. Admin Login")
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, status = make_request("POST", "/auth/login", data=login_data)
    
    if status != 200:
        print(f"❌ Admin login failed with status {status}")
        return
    
    admin_token = response.get("access_token")
    if not admin_token:
        print("❌ No access token in admin login response")
        return
    
    print("✅ Admin login successful\n")
    
    # Step 2: Create test users
    print("2. Creating test users")
    user1_token, user1_name = create_test_user("user1")
    user2_token, user2_name = create_test_user("user2")
    
    if not user1_token or not user2_token:
        print("❌ Failed to create test users")
        return
    
    print(f"✅ Created test users: {user1_name}, {user2_name}\n")
    
    # Step 3: Create some active games
    print("3. Creating active games")
    
    # Create a WAITING game (user1 creates, no opponent yet)
    game_data_1 = {
        "move": "rock",
        "bet_gems": {"Ruby": 5, "Emerald": 2}
    }
    
    response, status = make_request("POST", "/games/create", data=game_data_1, auth_token=user1_token)
    waiting_game_id = None
    if status == 200:
        waiting_game_id = response.get("game_id")
        print(f"✅ Created WAITING game: {waiting_game_id}")
    else:
        print(f"❌ Failed to create WAITING game: {response}")
    
    # Create an ACTIVE game (user2 creates, user1 joins)
    game_data_2 = {
        "move": "paper",
        "bet_gems": {"Ruby": 3, "Amber": 5}
    }
    
    response, status = make_request("POST", "/games/create", data=game_data_2, auth_token=user2_token)
    if status == 200:
        active_game_id = response.get("game_id")
        print(f"✅ Created game for joining: {active_game_id}")
        
        # User1 joins the game to make it ACTIVE
        join_data = {"move": "scissors"}
        response, status = make_request("POST", f"/games/{active_game_id}/join", data=join_data, auth_token=user1_token)
        if status == 200:
            print(f"✅ Game {active_game_id} is now COMPLETED (scissors beats paper)")
        else:
            print(f"❌ Failed to join game: {response}")
    else:
        print(f"❌ Failed to create second game: {response}")
    
    print()
    
    # Step 4: Check initial state before reset
    print("4. Checking initial state before reset")
    
    # Check user1 balance and gems
    response, status = make_request("GET", "/economy/balance", auth_token=user1_token)
    if status == 200:
        user1_initial_balance = response.get("virtual_balance", 0)
        user1_initial_frozen = response.get("frozen_balance", 0)
        print(f"✅ User1 initial - Balance: ${user1_initial_balance}, Frozen: ${user1_initial_frozen}")
    
    response, status = make_request("GET", "/gems/inventory", auth_token=user1_token)
    if status == 200:
        user1_frozen_gems = sum(gem.get("frozen_quantity", 0) for gem in response)
        print(f"✅ User1 has {user1_frozen_gems} frozen gems")
    
    # Check user2 balance and gems
    response, status = make_request("GET", "/economy/balance", auth_token=user2_token)
    if status == 200:
        user2_initial_balance = response.get("virtual_balance", 0)
        user2_initial_frozen = response.get("frozen_balance", 0)
        print(f"✅ User2 initial - Balance: ${user2_initial_balance}, Frozen: ${user2_initial_frozen}")
    
    response, status = make_request("GET", "/gems/inventory", auth_token=user2_token)
    if status == 200:
        user2_frozen_gems = sum(gem.get("frozen_quantity", 0) for gem in response)
        print(f"✅ User2 has {user2_frozen_gems} frozen gems")
    
    print()
    
    # Step 5: Test admin reset-all functionality
    print("5. Testing admin reset-all functionality")
    
    response, status = make_request("POST", "/admin/games/reset-all", auth_token=admin_token)
    if status == 200:
        print("✅ Admin reset-all endpoint successful")
        print(f"   - Games reset: {response.get('games_reset', 0)}")
        print(f"   - Gems returned: {response.get('gems_returned', {})}")
        print(f"   - Commission returned: ${response.get('commission_returned', 0)}")
    else:
        print(f"❌ Admin reset-all failed: {response}")
        return
    
    print()
    
    # Step 6: Verify database state changes after reset
    print("6. Verifying database state after reset")
    
    # Check that frozen balances are released
    response, status = make_request("GET", "/economy/balance", auth_token=user1_token)
    if status == 200:
        user1_final_balance = response.get("virtual_balance", 0)
        user1_final_frozen = response.get("frozen_balance", 0)
        print(f"✅ User1 after reset - Balance: ${user1_final_balance}, Frozen: ${user1_final_frozen}")
        
        if user1_final_frozen == 0:
            print("✅ User1 frozen balance correctly reset to 0")
        else:
            print(f"❌ User1 still has frozen balance: ${user1_final_frozen}")
    
    response, status = make_request("GET", "/economy/balance", auth_token=user2_token)
    if status == 200:
        user2_final_balance = response.get("virtual_balance", 0)
        user2_final_frozen = response.get("frozen_balance", 0)
        print(f"✅ User2 after reset - Balance: ${user2_final_balance}, Frozen: ${user2_final_frozen}")
        
        if user2_final_frozen == 0:
            print("✅ User2 frozen balance correctly reset to 0")
        else:
            print(f"❌ User2 still has frozen balance: ${user2_final_frozen}")
    
    # Check that frozen gem quantities are reset
    response, status = make_request("GET", "/gems/inventory", auth_token=user1_token)
    if status == 200:
        user1_final_frozen_gems = sum(gem.get("frozen_quantity", 0) for gem in response)
        if user1_final_frozen_gems == 0:
            print("✅ User1 frozen gem quantities correctly reset to 0")
        else:
            print(f"❌ User1 still has {user1_final_frozen_gems} frozen gems")
    
    response, status = make_request("GET", "/gems/inventory", auth_token=user2_token)
    if status == 200:
        user2_final_frozen_gems = sum(gem.get("frozen_quantity", 0) for gem in response)
        if user2_final_frozen_gems == 0:
            print("✅ User2 frozen gem quantities correctly reset to 0")
        else:
            print(f"❌ User2 still has {user2_final_frozen_gems} frozen gems")
    
    print()
    
    # Step 7: Test reset when no active games exist
    print("7. Testing reset when no active games exist")
    
    response, status = make_request("POST", "/admin/games/reset-all", auth_token=admin_token)
    if status == 200:
        games_reset = response.get("games_reset", 0)
        if games_reset == 0:
            print("✅ Reset correctly reports 0 games when no active games exist")
        else:
            print(f"❌ Reset reported {games_reset} games when none should exist")
    else:
        print(f"❌ Reset failed when no active games: {response}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_comprehensive_admin_reset()