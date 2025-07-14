#!/usr/bin/env python3
"""
Quick Bot Game Test - Test joining a bot game with correct gem combination
"""
import requests
import json
import random
import string

BASE_URL = "https://f6f5b865-a999-477a-a702-8e36f9f18ab6.preview.emergentagent.com/api"

def create_test_user():
    """Create a test user and return access token."""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    test_email = f"quicktest_{random_suffix}@test.com"
    test_username = f"quicktest_{random_suffix}"
    
    user_data = {
        "username": test_username,
        "email": test_email,
        "password": "Test123!",
        "gender": "male"
    }
    
    # Register user
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"Registration failed: {response.text}")
        return None
    
    data = response.json()
    user_id = data.get("user_id")
    verification_token = data.get("verification_token")
    
    # Verify email
    verify_response = requests.post(f"{BASE_URL}/auth/verify-email", json={"token": verification_token})
    if verify_response.status_code != 200:
        print(f"Email verification failed: {verify_response.text}")
        return None
    
    # Login user
    login_response = requests.post(f"{BASE_URL}/auth/login", json={"email": test_email, "password": "Test123!"})
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return None
    
    return login_response.json()["access_token"]

def test_bot_game_join():
    """Test joining a bot game with correct gem combination."""
    print("Creating test user...")
    token = create_test_user()
    if not token:
        print("Failed to create test user")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Getting available bot games...")
    response = requests.get(f"{BASE_URL}/bots/active-games", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get bot games: {response.text}")
        return
    
    games = response.json()
    if not games:
        print("No bot games available")
        return
    
    # Find a simple bot game
    target_game = None
    for game in games:
        if game.get("bet_amount", 0) <= 50:  # Find a reasonable bet
            target_game = game
            break
    
    if not target_game:
        target_game = games[0]  # Use first available
    
    print(f"Target game: {target_game['id']}")
    print(f"Bet amount: ${target_game['bet_amount']}")
    print(f"Required gems: {target_game['bet_gems']}")
    print(f"Bot type: {target_game.get('bot_type', 'Unknown')}")
    
    # Get user balance before
    balance_response = requests.get(f"{BASE_URL}/economy/balance", headers=headers)
    balance_before = balance_response.json()
    print(f"Balance before: Virtual=${balance_before['virtual_balance']}, Frozen=${balance_before['frozen_balance']}")
    
    # Join the game with exact same gems as required
    join_data = {
        "move": "rock",
        "gems": target_game["bet_gems"]  # Use exact same gems as the bot
    }
    
    print(f"Joining game with data: {join_data}")
    join_response = requests.post(f"{BASE_URL}/games/{target_game['id']}/join", json=join_data, headers=headers)
    
    print(f"Join response status: {join_response.status_code}")
    print(f"Join response: {json.dumps(join_response.json(), indent=2)}")
    
    if join_response.status_code == 200:
        result = join_response.json()
        print("\n🎉 SUCCESS! Bot game joined successfully!")
        print(f"Game status: {result.get('status')}")
        print(f"Result: {result.get('result')}")
        print(f"Winner: {result.get('winner_id')}")
        print(f"Commission amount: {result.get('commission_amount', 'Not specified')}")
        
        # Check if this is a Regular Bot game (should have no commission)
        if target_game.get('bot_type') == 'REGULAR':
            commission = result.get('commission_amount', None)
            if commission == 0:
                print("✅ REGULAR BOT COMMISSION TEST PASSED: Commission is 0 as expected")
            else:
                print(f"❌ REGULAR BOT COMMISSION TEST FAILED: Commission is {commission}, expected 0")
        
        # Get balance after
        balance_response = requests.get(f"{BASE_URL}/economy/balance", headers=headers)
        balance_after = balance_response.json()
        print(f"Balance after: Virtual=${balance_after['virtual_balance']}, Frozen=${balance_after['frozen_balance']}")
        
        if balance_after['frozen_balance'] == 0:
            print("✅ NO FROZEN BALANCE: Commission logic working correctly")
        else:
            print(f"❌ FROZEN BALANCE FOUND: ${balance_after['frozen_balance']} still frozen")
            
    else:
        print(f"❌ FAILED to join bot game: {join_response.text}")
        if "Failed to determine game winner" in join_response.text:
            print("🚨 CRITICAL: 'Failed to determine game winner' error still exists!")

if __name__ == "__main__":
    test_bot_game_join()