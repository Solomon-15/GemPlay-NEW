#!/usr/bin/env python3
"""
Find a user with existing bets to test my-bets endpoint
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://49b21745-59e5-4980-8f15-13cafed79fb5.preview.emergentagent.com/api"

async def find_user_with_bets():
    """Find a user with existing bets"""
    session = aiohttp.ClientSession()
    
    try:
        # Login as admin
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
        
        # Get all games to find users who have created games
        async with session.get(f"{BACKEND_URL}/admin/games", headers=admin_headers) as response:
            if response.status == 200:
                games_data = await response.json()
                games = games_data.get("games", [])
                print(f"✅ Found {len(games)} games")
                
                # Find games created by real users (not bots)
                user_games = []
                for game in games:
                    creator_type = game.get("creator_type", "")
                    if creator_type == "user":
                        user_games.append(game)
                
                print(f"✅ Found {len(user_games)} games created by real users")
                
                if len(user_games) > 0:
                    # Get the first user game
                    test_game = user_games[0]
                    creator_id = test_game.get("creator_id")
                    print(f"✅ Testing with user: {creator_id}")
                    
                    # Get user info
                    async with session.get(f"{BACKEND_URL}/admin/users/{creator_id}", headers=admin_headers) as user_response:
                        if user_response.status == 200:
                            user_data = await user_response.json()
                            user_email = user_data.get("email")
                            print(f"✅ User email: {user_email}")
                            
                            # Try to login as this user (we don't know password, so this will likely fail)
                            # Instead, let's use admin token to simulate the my-bets call
                            
                            # Create a temporary token for this user (admin privilege)
                            # Actually, let's just examine the game structure directly
                            print(f"\n--- GAME STRUCTURE FROM ADMIN LIST ---")
                            print(f"Game ID: {test_game.get('id')}")
                            print(f"Creator: {json.dumps(test_game.get('creator', {}), indent=2)}")
                            print(f"Opponent: {json.dumps(test_game.get('opponent'), indent=2)}")
                            print(f"Creator Username: {test_game.get('creator_username')}")
                            print(f"Creator Type: {test_game.get('creator_type')}")
                            
                            # Check for missing id fields
                            creator = test_game.get('creator', {})
                            opponent = test_game.get('opponent')
                            
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
                            creator_username = test_game.get('creator_username')
                            if creator_username == "Unknown Player":
                                print(f"❌ CREATOR USERNAME IS 'Unknown Player'")
                            else:
                                print(f"✅ Creator username is valid: '{creator_username}'")
                        else:
                            print(f"❌ Failed to get user info: {user_response.status}")
                else:
                    print("⚠️ No games created by real users found")
            else:
                print(f"❌ Failed to get games list: {response.status}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(find_user_with_bets())