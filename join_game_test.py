#!/usr/bin/env python3
"""
Join Game and Check Notifications Test
"""

import requests
import json
import time

BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def make_request(method: str, endpoint: str, data=None, auth_token=None):
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
    
    print(f"{method} {url} -> {response.status_code}")
    
    try:
        result = response.json()
        return result
    except:
        print(f"Response text: {response.text}")
        return {"error": response.text, "status_code": response.status_code}

def main():
    print("=== JOIN GAME AND CHECK NOTIFICATIONS ===")
    
    # Login as admin
    print("\n1. Admin login...")
    login_response = make_request("POST", "/auth/login", {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    })
    
    if "access_token" not in login_response:
        print("❌ Admin login failed")
        return
    
    admin_token = login_response["access_token"]
    print("✅ Admin logged in")
    
    # Get available games
    print("\n2. Getting available games...")
    available_games = make_request("GET", "/games/available", auth_token=admin_token)
    
    if not isinstance(available_games, list) or len(available_games) == 0:
        print("❌ No available games found")
        return
    
    # Find a suitable game to join (preferably a user game, not human-bot)
    target_game = None
    for game in available_games:
        if game.get("creator_type") == "user" and game.get("bet_amount", 0) <= 50:
            target_game = game
            break
    
    if not target_game:
        # If no user game, try a human-bot game
        for game in available_games:
            if game.get("bet_amount", 0) <= 50:
                target_game = game
                break
    
    if not target_game:
        print("❌ No suitable game found to join")
        return
    
    game_id = target_game["game_id"]
    bet_gems = target_game["bet_gems"]
    bet_amount = target_game["bet_amount"]
    creator_type = target_game.get("creator_type", "unknown")
    
    print(f"✅ Found game to join:")
    print(f"   Game ID: {game_id}")
    print(f"   Bet amount: ${bet_amount}")
    print(f"   Creator type: {creator_type}")
    print(f"   Required gems: {bet_gems}")
    
    # Check admin's gem inventory
    print("\n3. Checking admin gem inventory...")
    inventory = make_request("GET", "/gems/inventory", auth_token=admin_token)
    
    if not isinstance(inventory, list):
        print("❌ Failed to get gem inventory")
        return
    
    # Check if admin has enough gems
    admin_gems = {}
    for gem in inventory:
        gem_type = gem.get("type")
        available = gem.get("quantity", 0) - gem.get("frozen_quantity", 0)
        admin_gems[gem_type] = available
    
    print(f"✅ Admin gem inventory: {admin_gems}")
    
    # Check if we can join
    can_join = True
    for gem_type, required in bet_gems.items():
        if admin_gems.get(gem_type, 0) < required:
            print(f"❌ Not enough {gem_type} gems: need {required}, have {admin_gems.get(gem_type, 0)}")
            can_join = False
    
    if not can_join:
        print("❌ Admin doesn't have enough gems to join this game")
        
        # Try to buy gems
        print("\n4. Trying to buy gems...")
        for gem_type, required in bet_gems.items():
            if admin_gems.get(gem_type, 0) < required:
                needed = required - admin_gems.get(gem_type, 0) + 5  # Buy a few extra
                buy_response = make_request("POST", f"/gems/buy?gem_type={gem_type}&quantity={needed}", auth_token=admin_token)
                if "success" in buy_response or "message" in buy_response:
                    print(f"✅ Bought {needed} {gem_type} gems")
                else:
                    print(f"❌ Failed to buy {gem_type} gems: {buy_response}")
                    return
    
    # Join the game
    print(f"\n5. Joining game {game_id}...")
    join_data = {
        "move": "rock",
        "gems": bet_gems
    }
    
    join_response = make_request("POST", f"/games/{game_id}/join", data=join_data, auth_token=admin_token)
    
    if "status" not in join_response:
        print(f"❌ Failed to join game: {join_response}")
        return
    
    print(f"✅ Successfully joined game")
    print(f"   Status: {join_response.get('status')}")
    print(f"   Message: {join_response.get('message')}")
    
    # Wait for game to complete
    print("\n6. Waiting for game to complete...")
    max_wait = 120  # 2 minutes
    wait_interval = 10  # Check every 10 seconds
    
    for i in range(max_wait // wait_interval):
        time.sleep(wait_interval)
        print(f"   Waiting... ({(i+1) * wait_interval}s)")
        
        # Check if game is no longer in available games (might be completed)
        current_games = make_request("GET", "/games/available", auth_token=admin_token)
        if isinstance(current_games, list):
            game_still_available = any(g.get("game_id") == game_id for g in current_games)
            if not game_still_available:
                print("✅ Game no longer in available games (likely completed)")
                break
    
    # Check notifications
    print("\n7. Checking notifications...")
    notifications = make_request("GET", "/notifications", auth_token=admin_token)
    
    if "notifications" in notifications:
        all_notifications = notifications["notifications"]
        print(f"✅ Found {len(all_notifications)} total notifications")
        
        # Look for recent MATCH_RESULT notifications
        match_results = []
        for notif in all_notifications:
            if notif.get("type") == "MATCH_RESULT":
                match_results.append(notif)
        
        print(f"✅ Found {len(match_results)} MATCH_RESULT notifications")
        
        if match_results:
            print("\n8. Analyzing notification formats...")
            
            for i, notif in enumerate(match_results[:3]):  # Check first 3
                print(f"\n   Notification {i+1}:")
                print(f"     ID: {notif.get('id')}")
                print(f"     Title: {notif.get('title')}")
                print(f"     Message: {notif.get('message')}")
                print(f"     Commission: {notif.get('commission')}")
                print(f"     Created: {notif.get('created_at')}")
                
                message = notif.get("message", "")
                
                # Check format requirements
                checks = []
                
                if "Gems" in message:
                    checks.append("✅ Uses 'Gems' format")
                else:
                    checks.append("❌ Missing 'Gems' format")
                
                if "комиссия" in message or "commission" in message.lower():
                    checks.append("✅ Contains commission info")
                else:
                    checks.append("❌ Missing commission info")
                
                if "3%" in message:
                    checks.append("✅ Contains 3% rate")
                else:
                    checks.append("❌ Missing 3% rate")
                
                if notif.get("commission") is not None:
                    checks.append(f"✅ Commission field: {notif.get('commission')}")
                else:
                    checks.append("❌ Commission field missing")
                
                if "You won against" in message or "You lost against" in message:
                    checks.append("✅ Correct win/loss format")
                else:
                    checks.append("❌ Incorrect win/loss format")
                
                for check in checks:
                    print(f"       {check}")
                
                passed = sum(1 for check in checks if check.startswith("✅"))
                total = len(checks)
                
                if passed >= 4:
                    print(f"     ✅ Format CORRECT ({passed}/{total})")
                else:
                    print(f"     ❌ Format INCORRECT ({passed}/{total})")
        else:
            print("❌ No MATCH_RESULT notifications found")
    else:
        print(f"❌ Failed to get notifications: {notifications}")

if __name__ == "__main__":
    main()