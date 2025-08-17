#!/usr/bin/env python3
"""
Debug script to examine the actual my-bets endpoint response
"""

import asyncio
import aiohttp
import json
import os

BACKEND_URL = "https://rusdetails-1.preview.emergentagent.com/api"

async def debug_my_bets():
    """Debug the my-bets endpoint response"""
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
        
        # Get my bets
        headers = {"Authorization": f"Bearer {admin_token}"}
        async with session.get(f"{BACKEND_URL}/games/my-bets", headers=headers) as response:
            if response.status == 200:
                bets = await response.json()
                print(f"✅ Retrieved {len(bets)} bets")
                
                if len(bets) == 0:
                    print("⚠️ No bets found, let's check some sample games")
                    
                    # Get some sample games to see their structure
                    async with session.get(f"{BACKEND_URL}/games/available", headers=headers) as resp:
                        if resp.status == 200:
                            games_data = await resp.json()
                            games = games_data.get("games", games_data) if isinstance(games_data, dict) else games_data
                            print(f"✅ Found {len(games)} available games")
                            
                            # Show structure of first few games
                            for i, game in enumerate(games[:3]):
                                print(f"\n--- GAME {i+1} STRUCTURE ---")
                                print(f"ID: {game.get('id')}")
                                print(f"Creator: {json.dumps(game.get('creator', {}), indent=2)}")
                                print(f"Opponent: {json.dumps(game.get('opponent'), indent=2)}")
                                print(f"Creator Username: {game.get('creator_username')}")
                                print(f"Creator Type: {game.get('creator_type')}")
                                print(f"Is Regular Bot: {game.get('is_regular_bot_game')}")
                else:
                    # Show structure of actual my-bets response
                    for i, bet in enumerate(bets[:3]):
                        print(f"\n--- MY-BET {i+1} STRUCTURE ---")
                        print(f"Game ID: {bet.get('game_id')}")
                        print(f"Creator: {json.dumps(bet.get('creator', {}), indent=2)}")
                        print(f"Opponent: {json.dumps(bet.get('opponent'), indent=2)}")
                        print(f"Creator Username: {bet.get('creator_username')}")
                        print(f"Is Creator: {bet.get('is_creator')}")
                        
                        # Check for missing id fields
                        creator = bet.get('creator', {})
                        opponent = bet.get('opponent')
                        
                        if 'id' not in creator:
                            print(f"❌ CREATOR MISSING ID: {creator}")
                        if opponent and 'id' not in opponent:
                            print(f"❌ OPPONENT MISSING ID: {opponent}")
            else:
                print(f"❌ Failed to get my bets: {response.status}")
                text = await response.text()
                print(f"Response: {text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(debug_my_bets())