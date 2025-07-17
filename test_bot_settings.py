#!/usr/bin/env python3

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add the backend directory to the path
sys.path.append('/app/backend')

async def test_bot_settings():
    """Test bot settings endpoint logic."""
    try:
        # Connect to database
        mongo_url = "mongodb://localhost:27017"
        client = AsyncIOMotorClient(mongo_url)
        db = client["gemplay_db"]
        
        # Test getting bot settings
        print("Testing bot settings retrieval...")
        settings = await db.bot_settings.find_one({"id": "bot_settings"})
        print(f"Found settings: {settings}")
        
        if not settings:
            print("Creating default settings...")
            default_settings = {
                "id": "bot_settings",
                "globalMaxActiveBets": 50,
                "globalMaxHumanBots": 30,
                "paginationSize": 10,
                "autoActivateFromQueue": True,
                "priorityType": "order"
            }
            await db.bot_settings.insert_one(default_settings)
            settings = default_settings
            print("Default settings created")
        
        # Prepare response
        response = {
            "success": True,
            "settings": {
                "globalMaxActiveBets": settings.get("globalMaxActiveBets", settings.get("max_active_bets_regular", 50)),
                "globalMaxHumanBots": settings.get("globalMaxHumanBots", settings.get("max_active_bets_human", 30)),
                "paginationSize": settings.get("paginationSize", 10),
                "autoActivateFromQueue": settings.get("autoActivateFromQueue", True),
                "priorityType": settings.get("priorityType", "order")
            }
        }
        
        print("Success! Bot settings endpoint logic working:")
        print(response)
        
        client.close()
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    asyncio.run(test_bot_settings())