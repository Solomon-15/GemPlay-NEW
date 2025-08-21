#!/usr/bin/env python3
"""
Check the database directly to see what's in the completed_cycles collection
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

async def check_db():
    """Check the database directly"""
    
    # Connect to MongoDB
    mongo_url = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(mongo_url)
    db = client["gemplay_db"]
    
    try:
        print("🔍 Checking completed_cycles collection directly...")
        
        # Get all completed cycles
        completed_cycles_cursor = db.completed_cycles.find({})
        completed_cycles = await completed_cycles_cursor.to_list(length=100)
        
        print(f"Found {len(completed_cycles)} completed cycles in database:")
        
        for i, cycle in enumerate(completed_cycles):
            print(f"\n--- Cycle {i+1} ---")
            print(f"ID: {cycle.get('id')}")
            print(f"Bot ID: {cycle.get('bot_id')}")
            print(f"Cycle Number: {cycle.get('cycle_number')}")
            print(f"Total Bets: {cycle.get('total_bets')}")
            print(f"Wins Count: {cycle.get('wins_count')}")
            print(f"Losses Count: {cycle.get('losses_count')}")
            print(f"Draws Count: {cycle.get('draws_count')}")
            print(f"Total Bet Amount: ${cycle.get('total_bet_amount')}")
            print(f"Total Winnings: ${cycle.get('total_winnings')}")
            print(f"Total Losses: ${cycle.get('total_losses')}")
            print(f"Net Profit: ${cycle.get('net_profit')}")
            print(f"ROI Active: {cycle.get('roi_active', 0)}%")
            print(f"Start Time: {cycle.get('start_time')}")
            print(f"End Time: {cycle.get('end_time')}")
            
            # Check if this data looks correct
            total_games = cycle.get('wins_count', 0) + cycle.get('losses_count', 0) + cycle.get('draws_count', 0)
            print(f"Calculated total games: {total_games}")
            
            if total_games == 32:
                print("⚠️  WARNING: This cycle has 32 total games (should be 16)")
            elif total_games == 16:
                print("✅ This cycle has correct 16 total games")
            
            if cycle.get('wins_count') == 14 and cycle.get('losses_count') == 12 and cycle.get('draws_count') == 6:
                print("⚠️  WARNING: This cycle has doubled W/L/D values (14/12/6 instead of 7/6/3)")
            
            if cycle.get('total_losses', 0) == 0 and cycle.get('losses_count', 0) > 0:
                print("⚠️  WARNING: total_losses is $0 but losses_count > 0")
        
        # Also check the bots collection to see what it reports
        print(f"\n🤖 Checking bots collection...")
        bots_cursor = db.bots.find({})
        bots = await bots_cursor.to_list(length=10)
        
        for bot in bots:
            print(f"\nBot: {bot.get('name')} (ID: {bot.get('id')})")
            print(f"  Completed Cycles: {bot.get('completed_cycles', 0)}")
            print(f"  Current Cycle Games: {bot.get('current_cycle_games', 0)}")
            print(f"  Has Completed Cycles: {bot.get('has_completed_cycles', False)}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_db())