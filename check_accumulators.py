#!/usr/bin/env python3
"""
Check the bot_profit_accumulators collection to see if there's doubling there
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

async def check_accumulators():
    """Check the bot_profit_accumulators collection"""
    
    # Connect to MongoDB
    mongo_url = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(mongo_url)
    db = client["gemplay_db"]
    
    try:
        print("🔍 Checking bot_profit_accumulators collection...")
        
        # Get all accumulators
        accumulators_cursor = db.bot_profit_accumulators.find({})
        accumulators = await accumulators_cursor.to_list(length=100)
        
        print(f"Found {len(accumulators)} accumulators in database:")
        
        for i, acc in enumerate(accumulators):
            print(f"\n--- Accumulator {i+1} ---")
            print(f"ID: {acc.get('id')}")
            print(f"Bot ID: {acc.get('bot_id')}")
            print(f"Cycle Number: {acc.get('cycle_number')}")
            print(f"Games Completed: {acc.get('games_completed')}")
            print(f"Games Won: {acc.get('games_won')}")
            print(f"Games Lost: {acc.get('games_lost')}")
            print(f"Games Drawn: {acc.get('games_drawn')}")
            print(f"Total Spent: ${acc.get('total_spent')}")
            print(f"Total Earned: ${acc.get('total_earned')}")
            print(f"Is Cycle Completed: {acc.get('is_cycle_completed')}")
            print(f"Cycle Start Date: {acc.get('cycle_start_date')}")
            print(f"Cycle End Date: {acc.get('cycle_end_date')}")
            
            # Check if accumulator data looks correct
            games_won = acc.get('games_won', 0)
            games_lost = acc.get('games_lost', 0)
            games_drawn = acc.get('games_drawn', 0)
            total_games = games_won + games_lost + games_drawn
            
            print(f"Calculated total games: {total_games}")
            
            if total_games == 32:
                print("⚠️  WARNING: Accumulator has 32 total games (should be 16)")
            elif total_games == 16:
                print("✅ Accumulator has correct 16 total games")
            
            if games_won == 14 and games_lost == 12 and games_drawn == 6:
                print("⚠️  WARNING: Accumulator has doubled W/L/D values (14/12/6 instead of 7/6/3)")
            
            # Check if this accumulator was used to create a completed cycle
            if acc.get('is_cycle_completed'):
                print("🏁 This accumulator was used to complete a cycle")
                
                # Find the corresponding completed cycle
                completed_cycle = await db.completed_cycles.find_one({
                    "bot_id": acc.get('bot_id'),
                    "cycle_number": acc.get('cycle_number')
                })
                
                if completed_cycle:
                    print(f"  -> Completed cycle exists with {completed_cycle.get('total_bets')} total bets")
                    print(f"  -> Cycle W/L/D: {completed_cycle.get('wins_count')}/{completed_cycle.get('losses_count')}/{completed_cycle.get('draws_count')}")
                else:
                    print("  -> No corresponding completed cycle found")
        
    except Exception as e:
        print(f"❌ Error checking accumulators: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_accumulators())