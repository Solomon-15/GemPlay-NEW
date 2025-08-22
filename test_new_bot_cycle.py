#!/usr/bin/env python3
"""
Create a new bot and monitor its cycle completion to see if the doubling issue persists
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://roi-insights.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

async def test_new_bot():
    """Create a new bot and monitor its behavior"""
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
        
        # Create a new test bot
        bot_config = {
            "name": f"TestBot_Cycle_{int(time.time())}",
            "min_bet_amount": 1.0,
            "max_bet_amount": 10.0,  # Small bets for faster testing
            "cycle_games": 4,  # Small cycle for faster testing
            "wins_percentage": 50.0,
            "losses_percentage": 30.0,
            "draws_percentage": 20.0,
            "wins_count": 2,
            "losses_count": 1,
            "draws_count": 1,
            "pause_between_cycles": 2
        }
        
        print(f"\n🤖 Creating test bot with 4-game cycles...")
        async with session.post(
            f"{BACKEND_URL}/admin/bots/create-regular",
            json=bot_config,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                bot_id = data.get("bot_id")
                print(f"✅ Bot created: {bot_id}")
                
                # Activate the bot
                async with session.post(
                    f"{BACKEND_URL}/admin/bots/{bot_id}/toggle",
                    headers=headers
                ) as toggle_response:
                    if toggle_response.status == 200:
                        print(f"✅ Bot activated")
                    else:
                        print(f"❌ Failed to activate bot: {toggle_response.status}")
                        return
                
                # Monitor the bot for a few minutes
                print(f"\n🔍 Monitoring bot for cycle completion...")
                start_time = time.time()
                max_wait = 300  # 5 minutes
                
                while time.time() - start_time < max_wait:
                    # Check bot status
                    async with session.get(f"{BACKEND_URL}/admin/bots/{bot_id}", headers=headers) as bot_response:
                        if bot_response.status == 200:
                            bot_data = await bot_response.json()
                            current_cycle_games = bot_data.get("current_cycle_games", 0)
                            completed_cycles = bot_data.get("completed_cycles", 0)
                            
                            print(f"Bot status: {current_cycle_games}/4 games in current cycle, {completed_cycles} completed cycles")
                            
                            # Check completed cycles API
                            async with session.get(f"{BACKEND_URL}/admin/bots/{bot_id}/completed-cycles", headers=headers) as cycles_response:
                                if cycles_response.status == 200:
                                    cycles_data = await cycles_response.json()
                                    cycles = cycles_data.get("cycles", [])
                                    
                                    if cycles:
                                        print(f"📊 Found {len(cycles)} completed cycles:")
                                        for cycle in cycles:
                                            total_games = cycle.get("total_games", 0)
                                            wins = cycle.get("wins", 0)
                                            losses = cycle.get("losses", 0)
                                            draws = cycle.get("draws", 0)
                                            calculated_total = wins + losses + draws
                                            
                                            print(f"  Cycle {cycle.get('cycle_number')}: {wins}/{losses}/{draws} (W/L/D), total_games={total_games}, calculated={calculated_total}")
                                            
                                            # Check for doubling issues
                                            if total_games == 8 or calculated_total == 8:
                                                print(f"  ⚠️  WARNING: Doubled values detected (8 instead of 4)")
                                            elif total_games == 4 and calculated_total == 4:
                                                print(f"  ✅ Correct values (4 total games)")
                                        
                                        # If we found completed cycles, we can stop monitoring
                                        if len(cycles) >= 1:
                                            print(f"\n🎯 Analysis complete. Found {len(cycles)} completed cycles.")
                                            break
                    
                    await asyncio.sleep(10)  # Wait 10 seconds before next check
                
                # Final cleanup - deactivate the bot
                async with session.post(
                    f"{BACKEND_URL}/admin/bots/{bot_id}/toggle",
                    headers=headers
                ) as toggle_response:
                    print(f"🔄 Bot deactivated")
                
            else:
                error_text = await response.text()
                print(f"❌ Failed to create bot: {response.status} - {error_text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_new_bot())