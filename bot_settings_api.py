#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from datetime import datetime
from jose import JWTError, jwt
from pydantic import BaseModel, Field

# Bot Settings Request model
class BotSettingsRequest(BaseModel):
    globalMaxActiveBets: int = Field(ge=1, le=200)
    globalMaxHumanBots: int = Field(ge=1, le=100)
    paginationSize: int = Field(ge=5, le=50)
    autoActivateFromQueue: bool = True
    priorityType: str = Field(default="order")

# Initialize FastAPI app
app = FastAPI(title="Bot Settings API")

# MongoDB connection
mongo_url = "mongodb://localhost:27017"
client = AsyncIOMotorClient(mongo_url)
db = client["gemplay_db"]

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT settings
SECRET_KEY = "your-super-secret-jwt-key-change-in-production"
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Get current admin user."""
    if current_user.get("role") not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    return current_user

@app.get("/api/admin/bot-settings")
async def get_bot_settings(current_user: dict = Depends(get_current_admin)):
    """Get bot settings."""
    try:
        # Get bot settings from database
        settings = await db.bot_settings.find_one({"id": "bot_settings"})
        
        if not settings:
            # Create default settings if not exists
            default_settings = {
                "id": "bot_settings",
                "globalMaxActiveBets": 50,
                "globalMaxHumanBots": 30,
                "paginationSize": 10,
                "autoActivateFromQueue": True,
                "priorityType": "order",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.bot_settings.insert_one(default_settings)
            settings = default_settings
        
        return {
            "success": True,
            "settings": {
                "globalMaxActiveBets": settings.get("globalMaxActiveBets", settings.get("max_active_bets_regular", 50)),
                "globalMaxHumanBots": settings.get("globalMaxHumanBots", settings.get("max_active_bets_human", 30)),
                "paginationSize": settings.get("paginationSize", 10),
                "autoActivateFromQueue": settings.get("autoActivateFromQueue", True),
                "priorityType": settings.get("priorityType", "order")
            }
        }
        
    except Exception as e:
        print(f"Error fetching bot settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch bot settings: {str(e)}"
        )

@app.put("/api/admin/bot-settings")
async def update_bot_settings(
    settings: BotSettingsRequest,
    current_user: dict = Depends(get_current_admin)
):
    """Update bot settings."""
    try:
        # Update settings in database
        await db.bot_settings.update_one(
            {"id": "bot_settings"},
            {
                "$set": {
                    "globalMaxActiveBets": settings.globalMaxActiveBets,
                    "globalMaxHumanBots": settings.globalMaxHumanBots,
                    "paginationSize": settings.paginationSize,
                    "autoActivateFromQueue": settings.autoActivateFromQueue,
                    "priorityType": settings.priorityType,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Bot settings updated successfully"
        }
        
    except Exception as e:
        print(f"Error updating bot settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update bot settings: {str(e)}"
        )

@app.get("/")
async def root():
    return {"message": "Bot Settings API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)