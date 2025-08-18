"""
Утилиты для аутентификации и авторизации
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from google.auth.transport import requests
from google.oauth2 import id_token
import logging

logger = logging.getLogger(__name__)

# JWT settings - Use consistent key from environment
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Google OAuth settings
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

# Security
security = HTTPBearer()

# Default role permissions
ROLE_PERMISSIONS = {
    'USER': [
        'VIEW_PROFILE', 'EDIT_PROFILE', 'CREATE_GAME', 'JOIN_GAME', 'VIEW_GAMES'
    ],
    'MODERATOR': [
        'VIEW_PROFILE', 'EDIT_PROFILE', 'CREATE_GAME', 'JOIN_GAME', 'VIEW_GAMES',
        'VIEW_ADMIN_PANEL', 'MANAGE_USERS', 'MANAGE_GAMES'
    ],
    'ADMIN': [
        'VIEW_PROFILE', 'EDIT_PROFILE', 'CREATE_GAME', 'JOIN_GAME', 'VIEW_GAMES',
        'VIEW_ADMIN_PANEL', 'MANAGE_USERS', 'MANAGE_GAMES', 'MANAGE_BOTS', 
        'MANAGE_ECONOMY', 'VIEW_ANALYTICS', 'MANAGE_SOUNDS'
    ],
    'SUPER_ADMIN': [
        'VIEW_PROFILE', 'EDIT_PROFILE', 'CREATE_GAME', 'JOIN_GAME', 'VIEW_GAMES',
        'VIEW_ADMIN_PANEL', 'MANAGE_USERS', 'MANAGE_GAMES', 'MANAGE_BOTS', 
        'MANAGE_ECONOMY', 'VIEW_ANALYTICS', 'MANAGE_SOUNDS', 'MANAGE_ROLES', 
        'SYSTEM_SETTINGS'
    ]
}

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def hash_token(token: str) -> str:
    """Hash token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str, expected_type: str = "access") -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_google_token(token: str) -> Optional[dict]:
    """Verify Google ID token"""
    try:
        if not GOOGLE_CLIENT_ID:
            logger.warning("Google Client ID not configured")
            return None
            
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID)
            
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        return {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'given_name': idinfo.get('given_name', ''),
            'family_name': idinfo.get('family_name', ''),
            'picture': idinfo.get('picture', ''),
            'email_verified': idinfo.get('email_verified', False)
        }
    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        return None

def check_account_lockout(user: dict) -> bool:
    """Check if account is locked due to failed attempts"""
    if user.get('locked_until'):
        if datetime.utcnow() < user['locked_until']:
            return True
        # Lock expired, reset counters
        return False
    return False

def should_lock_account(failed_attempts: int) -> bool:
    """Check if account should be locked"""
    return failed_attempts >= 5

def calculate_lockout_time(failed_attempts: int) -> datetime:
    """Calculate lockout time based on failed attempts"""
    if failed_attempts >= 10:
        return datetime.utcnow() + timedelta(hours=24)
    elif failed_attempts >= 7:
        return datetime.utcnow() + timedelta(hours=1)
    else:
        return datetime.utcnow() + timedelta(minutes=15)

def has_permission(user_role: str, required_permission: str) -> bool:
    """Check if user role has required permission"""
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in role_perms

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get user from dependencies
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not has_permission(user.get('role', 'USER'), permission):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get user from database
        client = AsyncIOMotorClient(os.environ['MONGO_URL'])
        db = client[os.environ['DB_NAME']]
        user = await db.users.find_one({"id": user_id})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        if user.get('status') == 'BANNED':
            raise HTTPException(status_code=403, detail="Account is banned")
            
        if user.get('status') == 'EMAIL_PENDING':
            raise HTTPException(status_code=403, detail="Email verification required")
        
        # Check account lockout
        if check_account_lockout(user):
            raise HTTPException(status_code=403, detail="Account is temporarily locked")
        
        client.close()
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """Get current user and ensure admin privileges"""
    if not has_permission(current_user.get('role', 'USER'), 'VIEW_ADMIN_PANEL'):
        raise HTTPException(
            status_code=403, 
            detail="Admin privileges required"
        )
    return current_user

async def get_current_super_admin(current_user: dict = Depends(get_current_user)):
    """Get current user and ensure super admin privileges"""
    if current_user.get('role') != 'SUPER_ADMIN':
        raise HTTPException(
            status_code=403, 
            detail="Super admin privileges required"
        )
    return current_user

def get_user_permissions(user_role: str) -> List[str]:
    """Get all permissions for a user role"""
    return ROLE_PERMISSIONS.get(user_role, [])

def can_access_admin_panel(user_role: str) -> bool:
    """Check if user can access admin panel"""
    return has_permission(user_role, 'VIEW_ADMIN_PANEL')

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded headers (proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"