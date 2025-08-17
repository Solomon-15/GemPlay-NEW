#!/usr/bin/env python3
"""
Create a test bet to test the my-bets endpoint
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://russianparts.preview.emergentagent.com/api"

async def create_test_bet():
    """Create a test bet and then test my-bets endpoint"""
    session = aiohttp.ClientSession()
    
    try:
        # Login as admin
        login_data = {
            "email": "admin@gemplay.com",
            "password": "Admin123!"
        }
        
        async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                admin_token = data["access_token"]
                print("✅ Admin login successful")
            else:
                print(f"❌ Admin login failed: {response.status}")
                return
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First, add some gems to admin user
        add_gems_data = {
            "user_id": "admin",  # Will be replaced with actual admin ID
            "gem_type": "Ruby",
            "quantity": 10
        }
        
        # Get admin user info first
        async with session.get(f"{BACKEND_URL}/user/profile", headers=headers) as response:
            if response.status == 200:
                admin_profile = await response.json()
                admin_id = admin_profile["id"]
                print(f"✅ Admin ID: {admin_id}")
                
                # Add gems to admin
                add_gems_data["user_id"] = admin_id
                async with session.post(f"{BACKEND_URL}/admin/users/gems/add", 
                                       json=add_gems_data, headers=headers) as add_response:
                    if add_response.status == 200:
                        print("✅ Added Ruby gems to admin")
                    else:
                        print(f"⚠️ Failed to add gems: {add_response.status}")
                
                # Create a game
                game_data = {
                    "move": "rock",
                    "bet_gems": {"Ruby": 2}
                }
                
                async with session.post(f"{BACKEND_URL}/games/create", 
                                       json=game_data, headers=headers) as create_response:
                    if create_response.status == 201:
                        game_result = await create_response.json()
                        game_id = game_result.get("game_id")
                        print(f"✅ Test game created: {game_id}")
                        
                        # Now test my-bets endpoint
                        async with session.get(f"{BACKEND_URL}/games/my-bets", headers=headers) as my_bets_response:
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
                                else:
                                    print("⚠️ No bets returned from my-bets endpoint")
                            else:
                                print(f"❌ Failed to get my-bets: {my_bets_response.status}")
                    else:
                        text = await create_response.text()
                        print(f"❌ Failed to create game: {create_response.status} - {text}")
            else:
                print(f"❌ Failed to get admin profile: {response.status}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(create_test_bet())