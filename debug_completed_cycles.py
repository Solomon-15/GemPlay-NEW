#!/usr/bin/env python3
"""
Debug script to examine the actual data returned by get_bot_completed_cycles API
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://fraction-calc.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

async def debug_completed_cycles():
    """Debug the completed cycles API response"""
    session = aiohttp.ClientSession()
    
    try:
        # Admin login
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                admin_token = data.get("access_token")
                print(f"✅ Admin authenticated successfully")
            else:
                print(f"❌ Failed to authenticate: {response.status}")
                return
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get list of bots
        async with session.get(f"{BACKEND_URL}/admin/bots", headers=headers) as response:
            if response.status == 200:
                bots_data = await response.json()
                bots = bots_data.get("bots", [])
                
                # Find a bot with completed cycles
                target_bot = None
                for bot in bots:
                    if bot.get("completed_cycles", 0) > 0:
                        target_bot = bot
                        break
                
                if not target_bot:
                    print("❌ No bot with completed cycles found")
                    return
                
                bot_id = target_bot.get("id")
                bot_name = target_bot.get("name")
                print(f"\n🔍 Debugging bot: {bot_name} (ID: {bot_id})")
                print(f"Bot reports {target_bot.get('completed_cycles', 0)} completed cycles")
                
                # Get completed cycles data
                async with session.get(f"{BACKEND_URL}/admin/bots/{bot_id}/completed-cycles", headers=headers) as response:
                    if response.status == 200:
                        cycles_data = await response.json()
                        
                        print(f"\n📊 API Response Structure:")
                        print(f"bot_id: {cycles_data.get('bot_id')}")
                        print(f"bot_name: {cycles_data.get('bot_name')}")
                        print(f"total_completed_cycles: {cycles_data.get('total_completed_cycles')}")
                        
                        cycles = cycles_data.get("cycles", [])
                        print(f"\nFound {len(cycles)} cycles in response:")
                        
                        for i, cycle in enumerate(cycles):
                            print(f"\n--- Cycle {i+1} ---")
                            print(f"cycle_number: {cycle.get('cycle_number')}")
                            print(f"total_games: {cycle.get('total_games')}")
                            print(f"wins: {cycle.get('wins')}")
                            print(f"losses: {cycle.get('losses')}")
                            print(f"draws: {cycle.get('draws')}")
                            print(f"total_bet: ${cycle.get('total_bet')}")
                            print(f"total_winnings: ${cycle.get('total_winnings')}")
                            print(f"total_losses: ${cycle.get('total_losses')}")
                            print(f"profit: ${cycle.get('profit')}")
                            print(f"roi_percent: {cycle.get('roi_percent')}%")
                            print(f"completed_at: {cycle.get('completed_at')}")
                            print(f"duration: {cycle.get('duration')}")
                            
                            # Calculate expected values
                            calculated_total = cycle.get('wins', 0) + cycle.get('losses', 0) + cycle.get('draws', 0)
                            print(f"Calculated total games: {calculated_total}")
                            
                            # Check if this looks like doubled data
                            if cycle.get('total_games') == 32 or calculated_total == 32:
                                print("⚠️  WARNING: This looks like doubled data (32 games instead of 16)")
                            
                            if cycle.get('wins') == 14 and cycle.get('losses') == 12 and cycle.get('draws') == 6:
                                print("⚠️  WARNING: This looks like doubled W/L/D values (14/12/6 instead of 7/6/3)")
                            
                            if cycle.get('total_losses') == 0 and cycle.get('losses', 0) > 0:
                                print("⚠️  WARNING: total_losses is $0 but losses_count > 0")
                    else:
                        print(f"❌ Failed to get completed cycles: {response.status}")
                        error_text = await response.text()
                        print(f"Error: {error_text}")
            else:
                print(f"❌ Failed to get bots: {response.status}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(debug_completed_cycles())