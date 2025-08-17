#!/usr/bin/env python3
"""
Test my-bets endpoint with real user data
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://income-bot-3.preview.emergentagent.com/api"

async def test_my_bets_with_real_user():
    """Test my-bets endpoint by creating a real user and game"""
    session = aiohttp.ClientSession()
    
    try:
        # Login as admin first
        admin_login_data = {
            "email": "admin@gemplay.com",
            "password": "Admin123!"
        }
        
        async with session.post(f"{BACKEND_URL}/auth/login", json=admin_login_data) as response:
            if response.status == 200:
                data = await response.json()
                admin_token = data["access_token"]
                print("✅ Admin login successful")
            else:
                print(f"❌ Admin login failed: {response.status}")
                return
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First verify the test user's email
        verify_data = {"user_id": "f3ac71c0-eb83-4636-9e58-2aec27ebe9c2", "verified": True}
        async with session.patch(f"{BACKEND_URL}/admin/users/f3ac71c0-eb83-4636-9e58-2aec27ebe9c2/verify-email", 
                                json=verify_data, headers=admin_headers) as verify_response:
            if verify_response.status == 200:
                print("✅ User email verified")
            else:
                print(f"⚠️ Email verification failed: {verify_response.status}")
        
        # Try to login as test user (might already exist)
        test_login_data = {
            "email": "testmybets2025@example.com",
            "password": "TestPass123!"
        }
        
        async with session.post(f"{BACKEND_URL}/auth/login", json=test_login_data) as login_response:
            if login_response.status == 200:
                login_result = await login_response.json()
                user_token = login_result["access_token"]
                user_id = login_result["user"]["id"]
                print(f"✅ Test user login successful: {user_id}")
                
                user_headers = {"Authorization": f"Bearer {user_token}"}
                
                # Add gems to user
                add_gems_data = {
                    "user_id": user_id,
                    "gem_type": "Ruby",
                    "quantity": 10
                }
                
                async with session.post(f"{BACKEND_URL}/admin/users/gems/add", 
                                       json=add_gems_data, headers=admin_headers) as add_response:
                    if add_response.status == 200:
                        print("✅ Added Ruby gems to test user")
                    else:
                        print(f"⚠️ Failed to add gems: {add_response.status}")
                
                # Create a game as test user
                game_data = {
                    "move": "rock",
                    "bet_gems": {"Ruby": 2}
                }
                
                async with session.post(f"{BACKEND_URL}/games/create", 
                                       json=game_data, headers=user_headers) as create_response:
                    if create_response.status == 201:
                        game_result = await create_response.json()
                        game_id = game_result.get("game_id")
                        print(f"✅ Test game created: {game_id}")
                        
                        # Now test my-bets endpoint with the test user
                        async with session.get(f"{BACKEND_URL}/games/my-bets", headers=user_headers) as my_bets_response:
                            if my_bets_response.status == 200:
                                bets = await my_bets_response.json()
                                print(f"✅ Retrieved {len(bets)} bets from my-bets endpoint")
                                
                                if len(bets) > 0:
                                    # Examine the first bet
                                    bet = bets[0]
                                    print(f"\n--- ACTUAL MY-BET STRUCTURE ---")
                                    print(f"Game ID: {bet.get('game_id')}")
                                    print(f"Creator: {json.dumps(bet.get('creator', {}), indent=2)}")
                                    print(f"Opponent: {json.dumps(bet.get('opponent'), indent=2)}")
                                    print(f"Creator Username: {bet.get('creator_username')}")
                                    print(f"Is Creator: {bet.get('is_creator')}")
                                    
                                    # Check for missing id fields
                                    creator = bet.get('creator', {})
                                    opponent = bet.get('opponent')
                                    
                                    print(f"\n--- FIELD VALIDATION ---")
                                    if 'id' in creator:
                                        print(f"✅ Creator has ID: {creator['id']}")
                                    else:
                                        print(f"❌ CREATOR MISSING ID: {creator}")
                                    
                                    if opponent:
                                        if 'id' in opponent:
                                            print(f"✅ Opponent has ID: {opponent['id']}")
                                        else:
                                            print(f"❌ OPPONENT MISSING ID: {opponent}")
                                    else:
                                        print("ℹ️ Opponent is None (WAITING game)")
                                        
                                    # Check creator_username requirement
                                    creator_username = bet.get('creator_username')
                                    if creator_username == "Unknown Player":
                                        print(f"❌ CREATOR USERNAME IS 'Unknown Player'")
                                    else:
                                        print(f"✅ Creator username is valid: '{creator_username}'")
                                else:
                                    print("⚠️ No bets returned from my-bets endpoint")
                            else:
                                print(f"❌ Failed to get my-bets: {my_bets_response.status}")
                                text = await my_bets_response.text()
                                print(f"Response: {text}")
                    else:
                        text = await create_response.text()
                        print(f"❌ Failed to create game: {create_response.status} - {text}")
            else:
                print(f"❌ Test user login failed: {login_response.status}")
                text = await login_response.text()
                print(f"Response: {text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_my_bets_with_real_user())