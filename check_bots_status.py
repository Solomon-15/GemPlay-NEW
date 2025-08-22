#!/usr/bin/env python3
"""
Check bots status and completed cycles data
"""

import asyncio
import aiohttp
import json

# Configuration
BACKEND_URL = "https://fraction-calc.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

async def check_bots():
    """Check all bots and their status"""
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
                
                print(f"\n📊 Found {len(bots)} bots:")
                
                for i, bot in enumerate(bots):
                    print(f"\n--- Bot {i+1} ---")
                    print(f"ID: {bot.get('id')}")
                    print(f"Name: {bot.get('name')}")
                    print(f"Active: {bot.get('is_active')}")
                    print(f"Completed Cycles: {bot.get('completed_cycles', 0)}")
                    print(f"Current Cycle Games: {bot.get('current_cycle_games', 0)}")
                    print(f"Total Net Profit: ${bot.get('total_net_profit', 0)}")
                    
                    # Try to get completed cycles for this bot
                    bot_id = bot.get('id')
                    async with session.get(f"{BACKEND_URL}/admin/bots/{bot_id}/completed-cycles", headers=headers) as cycles_response:
                        if cycles_response.status == 200:
                            cycles_data = await cycles_response.json()
                            cycles = cycles_data.get("cycles", [])
                            print(f"API Completed Cycles: {len(cycles)}")
                            
                            if cycles:
                                # Show first cycle details
                                cycle = cycles[0]
                                print(f"  First cycle: {cycle.get('wins')}/{cycle.get('losses')}/{cycle.get('draws')} (W/L/D)")
                                print(f"  Total games: {cycle.get('total_games')}")
                                print(f"  Total losses: ${cycle.get('total_losses')}")
                                print(f"  ROI: {cycle.get('roi_percent')}%")
                        else:
                            print(f"Failed to get cycles: {cycles_response.status}")
                
                # If no bots with completed cycles, let's activate one and wait
                active_bots = [bot for bot in bots if bot.get("is_active", False)]
                if active_bots and not any(bot.get("completed_cycles", 0) > 0 for bot in bots):
                    print(f"\n🔄 No bots with completed cycles. Let's check if we can create some test data...")
                    
                    # Check if there are any completed cycles in the database directly
                    print("Checking for any completed cycles in the system...")
                    
            else:
                print(f"❌ Failed to get bots: {response.status}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(check_bots())