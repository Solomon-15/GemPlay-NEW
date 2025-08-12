#!/usr/bin/env python3
"""
Manual cleanup and testing of bot fields removal
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://russian-scribe.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "admin@gemplay.com"
SUPER_ADMIN_PASSWORD = "Admin123!"

async def main():
    async with aiohttp.ClientSession() as session:
        # Authenticate
        login_data = {"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                token = data["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                print("✅ Authenticated successfully")
            else:
                print("❌ Authentication failed")
                return

        # Test current bot state
        print("\n🔍 CHECKING CURRENT BOT STATE...")
        async with session.get(f"{BACKEND_URL}/admin/bots", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                bots = data.get("bots", [])
                if bots:
                    first_bot = bots[0]
                    has_can_accept_bets = "can_accept_bets" in first_bot
                    has_can_play_with_bots = "can_play_with_bots" in first_bot
                    print(f"Bot fields before cleanup:")
                    print(f"  - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                    print(f"  - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                    
                    if has_can_accept_bets or has_can_play_with_bots:
                        print("🧹 Fields need to be cleaned up")
                    else:
                        print("✅ Fields already cleaned up")

        # Try different cleanup endpoint variations
        cleanup_endpoints = [
            "/admin/bots/cleanup-removed-fields",
            "/admin/bots/cleanup",
            "/admin/bots/migrate",
            "/admin/bots/remove-fields"
        ]
        
        print("\n🧹 TESTING CLEANUP ENDPOINTS...")
        for endpoint in cleanup_endpoints:
            print(f"\nTesting POST {endpoint}...")
            try:
                async with session.post(f"{BACKEND_URL}{endpoint}", headers=headers) as response:
                    print(f"  Status: {response.status}")
                    if response.status != 405:  # Not Method Not Allowed
                        text = await response.text()
                        print(f"  Response: {text[:200]}...")
                        if response.status == 200:
                            print("  ✅ Cleanup endpoint found and working!")
                            break
            except Exception as e:
                print(f"  Error: {e}")

        # Test bot creation without removed fields
        print("\n🤖 TESTING BOT CREATION...")
        bot_data = {
            "name": f"TestBot_NoRemovedFields_{int(asyncio.get_event_loop().time())}",
            "min_bet_amount": 1.0,
            "max_bet_amount": 100.0,
            "win_rate": 55.0,
            "cycle_games": 12,
            "individual_limit": 12,
            "pause_between_games": 5
        }
        
        async with session.post(f"{BACKEND_URL}/admin/bots/create-regular", 
                               json=bot_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                created_bot = data.get("bot", {})
                has_can_accept_bets = "can_accept_bets" in created_bot
                has_can_play_with_bots = "can_play_with_bots" in created_bot
                
                print(f"✅ New bot created successfully")
                print(f"  - can_accept_bets: {'PRESENT' if has_can_accept_bets else 'ABSENT'}")
                print(f"  - can_play_with_bots: {'PRESENT' if has_can_play_with_bots else 'ABSENT'}")
                
                if not has_can_accept_bets and not has_can_play_with_bots:
                    print("✅ New bots are created without removed fields!")
                else:
                    print("❌ New bots still contain removed fields")
                    
                # Clean up test bot
                bot_id = created_bot.get("id")
                if bot_id:
                    async with session.delete(f"{BACKEND_URL}/admin/bots/{bot_id}", headers=headers) as del_response:
                        if del_response.status == 200:
                            print(f"✅ Test bot {bot_id} cleaned up")
            else:
                error_text = await response.text()
                print(f"❌ Bot creation failed: {response.status} - {error_text}")

        # Test Human-bots still have their fields
        print("\n👥 TESTING HUMAN-BOTS...")
        async with session.get(f"{BACKEND_URL}/admin/human-bots", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                bots = data.get("bots", [])
                if bots:
                    first_bot = bots[0]
                    has_can_play_with_other_bots = "can_play_with_other_bots" in first_bot
                    has_can_play_with_players = "can_play_with_players" in first_bot
                    
                    print(f"Human-bot fields:")
                    print(f"  - can_play_with_other_bots: {'PRESENT' if has_can_play_with_other_bots else 'ABSENT'}")
                    print(f"  - can_play_with_players: {'PRESENT' if has_can_play_with_players else 'ABSENT'}")
                    
                    if has_can_play_with_other_bots and has_can_play_with_players:
                        print("✅ Human-bots correctly retain their fields")
                    else:
                        print("❌ Human-bots missing required fields")

if __name__ == "__main__":
    asyncio.run(main())