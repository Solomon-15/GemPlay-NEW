from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import asyncio
import os
import logging
import uuid
from pathlib import Path
from enum import Enum
import pytz
import schedule
import time
from threading import Thread
import hashlib
import json
import secrets
from collections import defaultdict
import ipaddress

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Enhanced JWT settings with stronger security
SECRET_KEY = secrets.token_urlsafe(64)  # Generate secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security monitoring
SUSPICIOUS_ACTIVITY_THRESHOLDS = {
    "max_requests_per_minute": 60,
    "max_purchases_per_hour": 20,
    "max_gift_amount_per_day": 1000,
    "max_balance_change_per_hour": 5000,
    "unusual_login_locations": True
}

# In-memory rate limiting (in production, use Redis)
request_counts = defaultdict(lambda: defaultdict(int))
user_activity = defaultdict(lambda: defaultdict(list))

# Timezone
TIMEZONE = pytz.timezone(os.environ.get('TIMEZONE', 'Asia/Almaty'))

# Create the main app
app = FastAPI(title="GemPlay API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# ENUMS
# ==============================================================================

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BANNED = "BANNED"
    EMAIL_PENDING = "EMAIL_PENDING"

class GemType(str, Enum):
    RUBY = "Ruby"
    AMBER = "Amber"
    TOPAZ = "Topaz"
    EMERALD = "Emerald"
    AQUAMARINE = "Aquamarine"
    SAPPHIRE = "Sapphire"
    MAGIC = "Magic"

class GameStatus(str, Enum):
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class GameMove(str, Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    GIFT = "GIFT"
    COMMISSION = "COMMISSION"
    BET = "BET"
    WIN = "WIN"
    REFUND = "REFUND"
    DAILY_BONUS = "DAILY_BONUS"

class BotType(str, Enum):
    REGULAR = "REGULAR"
    HUMAN = "HUMAN"

# ==============================================================================
# MODELS
# ==============================================================================

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.EMAIL_PENDING
    gender: str = "male"  # male/female for avatar
    virtual_balance: float = 0.0
    frozen_balance: float = 0.0
    daily_limit_used: float = 0.0
    daily_limit_max: float = 1000.0
    last_daily_reset: datetime = Field(default_factory=datetime.utcnow)
    email_verification_token: Optional[str] = None
    email_verified: bool = False
    ban_reason: Optional[str] = None
    ban_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    total_games_played: int = 0
    total_games_won: int = 0
    total_amount_wagered: float = 0.0
    total_amount_won: float = 0.0

class GemDefinition(BaseModel):
    type: GemType
    name: str
    price: float
    color: str
    icon: str
    rarity: str
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserGem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    gem_type: GemType
    quantity: int = 0
    frozen_quantity: int = 0  # количество заморожено в ставках
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str
    opponent_id: Optional[str] = None
    creator_move: Optional[GameMove] = None
    opponent_move: Optional[GameMove] = None
    creator_move_hash: Optional[str] = None  # Для commit-reveal схемы
    creator_salt: Optional[str] = None
    bet_amount: float
    bet_gems: Dict[str, int]  # {"Ruby": 5, "Emerald": 2}
    status: GameStatus = GameStatus.WAITING
    winner_id: Optional[str] = None
    commission_amount: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    is_bot_game: bool = False
    bot_id: Optional[str] = None

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    transaction_type: TransactionType
    amount: float
    currency: str = "USD"  # USD для долларов, GEM для гемов
    gem_type: Optional[GemType] = None
    gem_quantity: Optional[int] = None
    balance_before: float
    balance_after: float
    description: str
    reference_id: Optional[str] = None  # ID игры, подарка и т.д.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    admin_id: Optional[str] = None  # Если транзакция создана админом

class Bot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    bot_type: BotType
    is_active: bool = True
    min_bet: float = 1.0
    max_bet: float = 1000.0
    win_rate: float = 0.6  # 60% by default
    cycle_games: int = 12  # количество игр в цикле
    current_cycle_games: int = 0
    current_cycle_wins: int = 0
    pause_between_games: int = 60  # секунд
    last_game_time: Optional[datetime] = None
    can_accept_bets: bool = False
    can_play_with_bots: bool = False
    avatar_gender: str = "male"
    simple_mode: bool = False  # Для Human ботов - простой режим
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AdminLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str
    target_type: str  # user, bot, gem, etc.
    target_id: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SecurityAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    alert_type: str  # RATE_LIMIT, SUSPICIOUS_PURCHASE, UNUSUAL_ACTIVITY, etc.
    severity: str    # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_data: Dict[str, Any] = {}
    action_taken: Optional[str] = None
    resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class SecurityMonitoring(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    ip_address: str
    endpoint: str
    request_count: int
    time_window: str  # "1m", "1h", "1d"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SuspiciousActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    activity_type: str
    description: str
    risk_score: int  # 1-100
    ip_address: Optional[str] = None
    evidence: Dict[str, Any] = {}
    status: str = "OPEN"  # OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EmailVerification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: EmailStr
    token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ==============================================================================
# RESPONSE MODELS
# ==============================================================================

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    status: UserStatus
    gender: str
    virtual_balance: float
    frozen_balance: float
    daily_limit_used: float
    daily_limit_max: float
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    total_games_played: int
    total_games_won: int
    total_amount_wagered: float
    total_amount_won: float

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class GemResponse(BaseModel):
    type: GemType
    name: str
    price: float
    color: str
    icon: str
    rarity: str
    quantity: int = 0
    frozen_quantity: int = 0

# ==============================================================================
# REQUEST MODELS
# ==============================================================================

class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str
    gender: str = "male"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class EmailVerificationRequest(BaseModel):
    token: str

class DailyBonusRequest(BaseModel):
    pass

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_verification_token() -> str:
    """Generate email verification token."""
    return str(uuid.uuid4())

# ==============================================================================
# SECURITY FUNCTIONS
# ==============================================================================

def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host

async def check_rate_limit(user_id: str, ip_address: str, endpoint: str) -> bool:
    """Check if user/IP has exceeded rate limits."""
    current_time = datetime.utcnow()
    minute_key = current_time.strftime("%Y-%m-%d-%H-%M")
    
    # Check requests per minute for this IP
    ip_key = f"{ip_address}:{minute_key}"
    request_counts[ip_key]["count"] += 1
    
    if request_counts[ip_key]["count"] > SUSPICIOUS_ACTIVITY_THRESHOLDS["max_requests_per_minute"]:
        await create_security_alert(
            user_id=user_id,
            alert_type="RATE_LIMIT_EXCEEDED",
            severity="HIGH",
            description=f"Rate limit exceeded: {request_counts[ip_key]['count']} requests in 1 minute",
            ip_address=ip_address,
            request_data={"endpoint": endpoint, "requests_count": request_counts[ip_key]["count"]}
        )
        return False
    
    return True

async def create_security_alert(
    user_id: str,
    alert_type: str,
    severity: str,
    description: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_data: Dict[str, Any] = None,
    action_taken: Optional[str] = None
):
    """Create a security alert."""
    alert = SecurityAlert(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_data=request_data or {},
        action_taken=action_taken
    )
    await db.security_alerts.insert_one(alert.dict())
    
    # Log critical alerts
    if severity in ["HIGH", "CRITICAL"]:
        logger.warning(f"SECURITY ALERT [{severity}]: {description} - User: {user_id}, IP: {ip_address}")

async def monitor_transaction_patterns(user_id: str, transaction_type: str, amount: float):
    """Monitor user transaction patterns for suspicious activity."""
    current_time = datetime.utcnow()
    hour_ago = current_time - timedelta(hours=1)
    day_ago = current_time - timedelta(days=1)
    
    # Check purchases per hour
    if transaction_type == "PURCHASE":
        recent_purchases = await db.transactions.count_documents({
            "user_id": user_id,
            "transaction_type": "PURCHASE",
            "created_at": {"$gte": hour_ago}
        })
        
        if recent_purchases > SUSPICIOUS_ACTIVITY_THRESHOLDS["max_purchases_per_hour"]:
            await create_security_alert(
                user_id=user_id,
                alert_type="EXCESSIVE_PURCHASES",
                severity="MEDIUM",
                description=f"Excessive purchases: {recent_purchases} purchases in 1 hour",
                request_data={"purchases_count": recent_purchases, "time_window": "1_hour"}
            )
    
    # Check large balance changes
    if transaction_type in ["PURCHASE", "SALE", "GIFT"]:
        recent_transactions = await db.transactions.find({
            "user_id": user_id,
            "created_at": {"$gte": hour_ago}
        }).to_list(100)
        
        total_change = sum(abs(t["amount"]) for t in recent_transactions)
        
        if total_change > SUSPICIOUS_ACTIVITY_THRESHOLDS["max_balance_change_per_hour"]:
            await create_security_alert(
                user_id=user_id,
                alert_type="LARGE_BALANCE_CHANGE",
                severity="HIGH",
                description=f"Large balance changes: ${total_change} in 1 hour",
                request_data={"total_change": total_change, "transactions_count": len(recent_transactions)}
            )

async def validate_transaction_integrity(user_id: str, operation: str, amount: float = None, gem_quantity: int = None, gem_type: str = None) -> bool:
    """Validate transaction integrity before processing."""
    user = await db.users.find_one({"id": user_id})
    if not user:
        return False
    
    if operation == "purchase" and amount:
        if user["virtual_balance"] < amount:
            await create_security_alert(
                user_id=user_id,
                alert_type="INSUFFICIENT_FUNDS_ATTEMPT",
                severity="LOW",
                description=f"Attempted purchase with insufficient funds: ${amount} requested, ${user['virtual_balance']} available",
                request_data={"requested_amount": amount, "available_balance": user["virtual_balance"]}
            )
            return False
    
    if operation == "sell" and gem_quantity and gem_type:
        user_gems = await db.user_gems.find_one({"user_id": user_id, "gem_type": gem_type})
        if not user_gems or user_gems["quantity"] < gem_quantity:
            await create_security_alert(
                user_id=user_id,
                alert_type="INSUFFICIENT_GEMS_ATTEMPT",
                severity="LOW",
                description=f"Attempted sale with insufficient gems: {gem_quantity} {gem_type} requested",
                request_data={"requested_quantity": gem_quantity, "gem_type": gem_type, "available_quantity": user_gems["quantity"] if user_gems else 0}
            )
            return False
    
    return True

def hash_move_with_salt(move: GameMove, salt: str) -> str:
    """Hash game move with salt for commit-reveal scheme."""
    combined = f"{move.value}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def verify_move_hash(move: GameMove, salt: str, hash_value: str) -> bool:
    """Verify game move hash."""
    return hash_move_with_salt(move, salt) == hash_value

# ==============================================================================
# DEPENDENCY FUNCTIONS
# ==============================================================================

async def get_current_user_with_security(request: Request, token: str = Depends(oauth2_scheme)):
    """Get current user with security monitoring."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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
    
    # Security monitoring
    ip_address = get_client_ip(request)
    endpoint = str(request.url.path)
    
    # Check rate limits
    rate_limit_ok = await check_rate_limit(user_id, ip_address, endpoint)
    if not rate_limit_ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return User(**user)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token (legacy method)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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
    return User(**user)

async def get_current_admin(current_user: User = Depends(get_current_user)):
    """Get current admin user."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_super_admin(current_user: User = Depends(get_current_user)):
    """Get current super admin user."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin permissions required"
        )
    return current_user

# ==============================================================================
# STARTUP AND BACKGROUND TASKS
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and create default data."""
    logger.info("Starting GemPlay API...")
    
    # Create default gem definitions
    default_gems = [
        {"type": GemType.RUBY, "name": "Ruby", "price": 1.0, "color": "#FF0000", "icon": "gem-red.svg", "rarity": "Common"},
        {"type": GemType.AMBER, "name": "Amber", "price": 2.0, "color": "#FFA500", "icon": "gem-orange.svg", "rarity": "Common"},
        {"type": GemType.TOPAZ, "name": "Topaz", "price": 5.0, "color": "#FFFF00", "icon": "gem-yellow.svg", "rarity": "Uncommon"},
        {"type": GemType.EMERALD, "name": "Emerald", "price": 10.0, "color": "#00FF00", "icon": "gem-green.svg", "rarity": "Rare"},
        {"type": GemType.AQUAMARINE, "name": "Aquamarine", "price": 25.0, "color": "#00FFFF", "icon": "gem-cyan.svg", "rarity": "Rare+"},
        {"type": GemType.SAPPHIRE, "name": "Sapphire", "price": 50.0, "color": "#0000FF", "icon": "gem-blue.svg", "rarity": "Epic"},
        {"type": GemType.MAGIC, "name": "Magic", "price": 100.0, "color": "#800080", "icon": "gem-purple.svg", "rarity": "Legendary"},
    ]
    
    for gem_data in default_gems:
        existing = await db.gem_definitions.find_one({"type": gem_data["type"]})
        if not existing:
            gem_def = GemDefinition(**gem_data)
            await db.gem_definitions.insert_one(gem_def.dict())
    
    # Create default admin users
    admin_users = [
        {
            "username": "admin",
            "email": os.environ.get('ADMIN_EMAIL', 'admin@gemplay.com'),
            "password": os.environ.get('ADMIN_PASSWORD', 'Admin123!'),
            "role": UserRole.ADMIN
        },
        {
            "username": "superadmin",
            "email": os.environ.get('SUPER_ADMIN_EMAIL', 'superadmin@gemplay.com'),
            "password": os.environ.get('SUPER_ADMIN_PASSWORD', 'SuperAdmin123!'),
            "role": UserRole.SUPER_ADMIN
        }
    ]
    
    for admin_data in admin_users:
        existing = await db.users.find_one({"email": admin_data["email"]})
        if not existing:
            admin_user = User(
                username=admin_data["username"],
                email=admin_data["email"],
                password_hash=get_password_hash(admin_data["password"]),
                role=admin_data["role"],
                status=UserStatus.ACTIVE,
                email_verified=True,
                virtual_balance=10000.0  # Give admins some balance
            )
            await db.users.insert_one(admin_user.dict())
    
    # Start background tasks
    start_background_scheduler()
    
    logger.info("GemPlay API started successfully!")

def start_background_scheduler():
    """Start background scheduler for daily bonuses."""
    def run_scheduler():
        schedule.every().day.at("00:00").do(reset_daily_limits)
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

def reset_daily_limits():
    """Reset daily limits for all users."""
    asyncio.create_task(reset_daily_limits_async())

async def reset_daily_limits_async():
    """Reset daily limits for all users (async)."""
    try:
        current_time = datetime.now(TIMEZONE)
        result = await db.users.update_many(
            {},
            {
                "$set": {
                    "daily_limit_used": 0.0,
                    "last_daily_reset": current_time
                }
            }
        )
        logger.info(f"Reset daily limits for {result.modified_count} users")
    except Exception as e:
        logger.error(f"Error resetting daily limits: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    client.close()
    logger.info("GemPlay API shutdown complete")

# ==============================================================================
# API ROUTES
# ==============================================================================

# Create routers
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
api_router = APIRouter(prefix="/api")

# ==============================================================================
# AUTH ROUTES
# ==============================================================================

@auth_router.post("/register", response_model=dict)
async def register(user_data: UserRegistration):
    """Register a new user."""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    verification_token = generate_verification_token()
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        gender=user_data.gender,
        email_verification_token=verification_token,
        virtual_balance=1000.0,  # Starting balance
        daily_limit_used=0.0
    )
    
    await db.users.insert_one(user.dict())
    
    # Create email verification record
    verification = EmailVerification(
        user_id=user.id,
        email=user_data.email,
        token=verification_token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    await db.email_verifications.insert_one(verification.dict())

    # Create security alert for new registration
    security_alert = SecurityAlert(
        user_id=user.id,
        alert_type="NEW_REGISTRATION",
        severity="LOW",
        description=f"New user registration: {user_data.email}",
        request_data={"email": user_data.email, "username": user_data.username}
    )
    await db.security_alerts.insert_one(security_alert.dict())
    
    # Give user initial gems worth $1000
    initial_gems = {
        GemType.RUBY: 100,     # $100
        GemType.AMBER: 100,    # $200
        GemType.TOPAZ: 40,     # $200
        GemType.EMERALD: 20,   # $200
        GemType.AQUAMARINE: 12, # $300
    }
    
    for gem_type, quantity in initial_gems.items():
        user_gem = UserGem(
            user_id=user.id,
            gem_type=gem_type,
            quantity=quantity
        )
        await db.user_gems.insert_one(user_gem.dict())
    
    return {
        "message": "User registered successfully. Please check your email for verification.",
        "user_id": user.id,
        "verification_token": verification_token  # In production, send via email
    }

@auth_router.post("/verify-email", response_model=dict)
async def verify_email(request: EmailVerificationRequest):
    """Verify user email."""
    verification = await db.email_verifications.find_one({
        "token": request.token,
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update user status
    await db.users.update_one(
        {"id": verification["user_id"]},
        {
            "$set": {
                "status": UserStatus.ACTIVE,
                "email_verified": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Mark verification as used
    await db.email_verifications.update_one(
        {"id": verification["id"]},
        {"$set": {"used": True}}
    )
    
    return {"message": "Email verified successfully"}

@auth_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user."""
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_obj = User(**user)
    
    # Check if user is banned
    if user_obj.status == UserStatus.BANNED:
        ban_message = "Account is banned"
        if user_obj.ban_until and user_obj.ban_until > datetime.utcnow():
            ban_message += f" until {user_obj.ban_until.strftime('%Y-%m-%d %H:%M:%S')}"
        elif user_obj.ban_reason:
            ban_message += f". Reason: {user_obj.ban_reason}"
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ban_message
        )
    
    # Check if email is verified
    if not user_obj.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email and verify your account."
        )
    
    # Update last login
    await db.users.update_one(
        {"id": user_obj.id},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user_obj.dict())
    )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(**current_user.dict())

@auth_router.post("/daily-bonus", response_model=dict)
async def claim_daily_bonus(current_user: User = Depends(get_current_user)):
    """Claim daily bonus of $1000."""
    # Check if user has reached daily limit
    if current_user.daily_limit_used >= current_user.daily_limit_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily limit already reached"
        )
    
    # Check if it's been 24 hours since last reset
    current_time = datetime.now(TIMEZONE)
    if current_user.last_daily_reset:
        time_since_reset = current_time - current_user.last_daily_reset.replace(tzinfo=TIMEZONE)
        if time_since_reset.total_seconds() < 86400:  # 24 hours
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily bonus not available yet"
            )
    
    # Add daily bonus
    bonus_amount = 1000.0
    new_balance = current_user.virtual_balance + bonus_amount
    
    # Update user balance
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "virtual_balance": new_balance,
                "daily_limit_used": current_user.daily_limit_used + bonus_amount,
                "last_daily_reset": current_time,
                "updated_at": current_time
            }
        }
    )
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type=TransactionType.DAILY_BONUS,
        amount=bonus_amount,
        balance_before=current_user.virtual_balance,
        balance_after=new_balance,
        description="Daily bonus claimed"
    )
    await db.transactions.insert_one(transaction.dict())
    
    return {
        "message": "Daily bonus claimed successfully",
        "amount": bonus_amount,
        "new_balance": new_balance
    }

# ==============================================================================
# ECONOMY API ROUTES
# ==============================================================================

@api_router.get("/gems/definitions", response_model=List[GemDefinition])
async def get_gem_definitions():
    """Get all available gem types and their properties."""
    gems = await db.gem_definitions.find({"enabled": True}).to_list(100)
    return [GemDefinition(**gem) for gem in gems]

@api_router.get("/gems/inventory", response_model=List[GemResponse])
async def get_user_gems(current_user: User = Depends(get_current_user)):
    """Get user's gem inventory."""
    user_gems = await db.user_gems.find({"user_id": current_user.id}).to_list(100)
    gem_definitions = await db.gem_definitions.find().to_list(100)
    
    # Create a map of gem definitions
    gem_def_map = {gem["type"]: gem for gem in gem_definitions}
    
    result = []
    for user_gem in user_gems:
        if user_gem["quantity"] > 0:  # Only return gems with positive quantity
            gem_def = gem_def_map.get(user_gem["gem_type"])
            if gem_def:
                result.append(GemResponse(
                    type=gem_def["type"],
                    name=gem_def["name"],
                    price=gem_def["price"],
                    color=gem_def["color"],
                    icon=gem_def["icon"],
                    rarity=gem_def["rarity"],
                    quantity=user_gem["quantity"],
                    frozen_quantity=user_gem["frozen_quantity"]
                ))
    
    # Sort by price ascending
    result.sort(key=lambda x: x.price)
    return result

@api_router.post("/gems/buy", response_model=dict)
async def buy_gems(request: Request, gem_type: GemType, quantity: int, current_user: User = Depends(get_current_user_with_security)):
    """Buy gems from the shop with security monitoring."""
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive"
        )
    
    # Get gem definition
    gem_def = await db.gem_definitions.find_one({"type": gem_type, "enabled": True})
    if not gem_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gem type not found or disabled"
        )
    
    total_cost = gem_def["price"] * quantity
    
    # Enhanced security validation
    validation_ok = await validate_transaction_integrity(current_user.id, "purchase", amount=total_cost)
    if not validation_ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction validation failed"
        )
    
    # Check for suspicious purchase patterns
    await monitor_transaction_patterns(current_user.id, "PURCHASE", total_cost)
    
    # Check if user has enough balance
    user = await db.users.find_one({"id": current_user.id})
    if user["virtual_balance"] < total_cost:
        await create_security_alert(
            user_id=current_user.id,
            alert_type="INSUFFICIENT_FUNDS_ATTEMPT",
            severity="LOW",
            description=f"Purchase attempt with insufficient funds: ${total_cost} requested",
            ip_address=get_client_ip(request),
            request_data={"gem_type": gem_type, "quantity": quantity, "total_cost": total_cost}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Monitor large purchases
    if total_cost > 500:  # Large purchase threshold
        await create_security_alert(
            user_id=current_user.id,
            alert_type="LARGE_PURCHASE",
            severity="MEDIUM",
            description=f"Large purchase detected: ${total_cost} for {quantity} {gem_type} gems",
            ip_address=get_client_ip(request),
            request_data={"gem_type": gem_type, "quantity": quantity, "total_cost": total_cost}
        )
    
    # Update user balance
    new_balance = user["virtual_balance"] - total_cost
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"virtual_balance": new_balance, "updated_at": datetime.utcnow()}}
    )
    
    # Add gems to user inventory
    existing_gems = await db.user_gems.find_one({"user_id": current_user.id, "gem_type": gem_type})
    if existing_gems:
        new_quantity = existing_gems["quantity"] + quantity
        await db.user_gems.update_one(
            {"user_id": current_user.id, "gem_type": gem_type},
            {
                "$set": {
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        new_gem = UserGem(
            user_id=current_user.id,
            gem_type=gem_type,
            quantity=quantity
        )
        await db.user_gems.insert_one(new_gem.dict())
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type=TransactionType.PURCHASE,
        amount=total_cost,
        currency="USD",
        gem_type=gem_type,
        gem_quantity=quantity,
        balance_before=user["virtual_balance"],
        balance_after=new_balance,
        description=f"Purchased {quantity} {gem_type} gems"
    )
    await db.transactions.insert_one(transaction.dict())
    
    return {
        "message": f"Successfully purchased {quantity} {gem_type} gems",
        "total_cost": total_cost,
        "new_balance": new_balance
    }

@api_router.post("/gems/sell", response_model=dict)
async def sell_gems(gem_type: GemType, quantity: int, current_user: User = Depends(get_current_user)):
    """Sell gems back to the shop."""
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive"
        )
    
    # Get gem definition
    gem_def = await db.gem_definitions.find_one({"type": gem_type, "enabled": True})
    if not gem_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gem type not found or disabled"
        )
    
    # Check if user has enough gems
    user_gems = await db.user_gems.find_one({"user_id": current_user.id, "gem_type": gem_type})
    if not user_gems or user_gems["quantity"] < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient gems"
        )
    
    # Check if gems are not frozen
    available_quantity = user_gems["quantity"] - user_gems["frozen_quantity"]
    if available_quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some gems are frozen in active bets"
        )
    
    total_value = gem_def["price"] * quantity
    
    # Update user balance
    user = await db.users.find_one({"id": current_user.id})
    new_balance = user["virtual_balance"] + total_value
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"virtual_balance": new_balance, "updated_at": datetime.utcnow()}}
    )
    
    # Remove gems from inventory
    new_quantity = user_gems["quantity"] - quantity
    await db.user_gems.update_one(
        {"user_id": current_user.id, "gem_type": gem_type},
        {
            "$set": {
                "quantity": new_quantity,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type=TransactionType.SALE,
        amount=total_value,
        currency="USD",
        gem_type=gem_type,
        gem_quantity=quantity,
        balance_before=user["virtual_balance"],
        balance_after=new_balance,
        description=f"Sold {quantity} {gem_type} gems"
    )
    await db.transactions.insert_one(transaction.dict())
    
    return {
        "message": f"Successfully sold {quantity} {gem_type} gems",
        "total_value": total_value,
        "new_balance": new_balance
    }

@api_router.post("/gems/gift", response_model=dict)
async def gift_gems(
    recipient_email: str, 
    gem_type: GemType, 
    quantity: int, 
    current_user: User = Depends(get_current_user)
):
    """Gift gems to another user."""
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive"
        )
    
    # Check if recipient exists
    recipient = await db.users.find_one({"email": recipient_email})
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # Can't gift to yourself
    if recipient["id"] == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot gift to yourself"
        )
    
    # Get gem definition
    gem_def = await db.gem_definitions.find_one({"type": gem_type, "enabled": True})
    if not gem_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gem type not found or disabled"
        )
    
    # Check if sender has enough gems
    sender_gems = await db.user_gems.find_one({"user_id": current_user.id, "gem_type": gem_type})
    if not sender_gems or sender_gems["quantity"] < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient gems"
        )
    
    # Check if gems are not frozen
    available_quantity = sender_gems["quantity"] - sender_gems["frozen_quantity"]
    if available_quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some gems are frozen in active bets"
        )
    
    # Calculate commission (3% of total gem value)
    gem_value = gem_def["price"] * quantity
    commission = gem_value * 0.03
    
    # Check if sender has enough balance for commission
    sender = await db.users.find_one({"id": current_user.id})
    if sender["virtual_balance"] < commission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance for gift commission (3%)"
        )
    
    # Deduct commission from sender
    new_sender_balance = sender["virtual_balance"] - commission
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"virtual_balance": new_sender_balance, "updated_at": datetime.utcnow()}}
    )
    
    # Remove gems from sender
    new_sender_quantity = sender_gems["quantity"] - quantity
    await db.user_gems.update_one(
        {"user_id": current_user.id, "gem_type": gem_type},
        {
            "$set": {
                "quantity": new_sender_quantity,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Add gems to recipient
    recipient_gems = await db.user_gems.find_one({"user_id": recipient["id"], "gem_type": gem_type})
    if recipient_gems:
        new_recipient_quantity = recipient_gems["quantity"] + quantity
        await db.user_gems.update_one(
            {"user_id": recipient["id"], "gem_type": gem_type},
            {
                "$set": {
                    "quantity": new_recipient_quantity,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        new_recipient_gem = UserGem(
            user_id=recipient["id"],
            gem_type=gem_type,
            quantity=quantity
        )
        await db.user_gems.insert_one(new_recipient_gem.dict())
    
    # Create transaction records
    # Sender transaction
    sender_transaction = Transaction(
        user_id=current_user.id,
        transaction_type=TransactionType.GIFT,
        amount=-gem_value,
        currency="GEM",
        gem_type=gem_type,
        gem_quantity=-quantity,
        balance_before=sender["virtual_balance"],
        balance_after=new_sender_balance,
        description=f"Gifted {quantity} {gem_type} gems to {recipient['username']}",
        reference_id=recipient["id"]
    )
    await db.transactions.insert_one(sender_transaction.dict())
    
    # Commission transaction
    commission_transaction = Transaction(
        user_id=current_user.id,
        transaction_type=TransactionType.COMMISSION,
        amount=commission,
        currency="USD",
        balance_before=sender["virtual_balance"],
        balance_after=new_sender_balance,
        description=f"Gift commission for {quantity} {gem_type} gems",
        reference_id=recipient["id"]
    )
    await db.transactions.insert_one(commission_transaction.dict())
    
    # Recipient transaction
    recipient_transaction = Transaction(
        user_id=recipient["id"],
        transaction_type=TransactionType.GIFT,
        amount=gem_value,
        currency="GEM",
        gem_type=gem_type,
        gem_quantity=quantity,
        balance_before=0,  # We don't track gem balance changes for recipient
        balance_after=0,
        description=f"Received {quantity} {gem_type} gems from {current_user.username}",
        reference_id=current_user.id
    )
    await db.transactions.insert_one(recipient_transaction.dict())
    
    return {
        "message": f"Successfully gifted {quantity} {gem_type} gems to {recipient['username']}",
        "gem_value": gem_value,
        "commission": commission,
        "new_balance": new_sender_balance
    }

@api_router.get("/economy/balance", response_model=dict)
async def get_economy_balance(current_user: User = Depends(get_current_user)):
    """Get user's complete economic status."""
    # Get current user data
    user = await db.users.find_one({"id": current_user.id})
    
    # Calculate total gem value
    user_gems = await db.user_gems.find({"user_id": current_user.id}).to_list(100)
    gem_definitions = await db.gem_definitions.find().to_list(100)
    gem_def_map = {gem["type"]: gem["price"] for gem in gem_definitions}
    
    total_gem_value = 0
    available_gem_value = 0
    
    for user_gem in user_gems:
        gem_price = gem_def_map.get(user_gem["gem_type"], 0)
        total_gem_value += user_gem["quantity"] * gem_price
        available_gem_value += (user_gem["quantity"] - user_gem["frozen_quantity"]) * gem_price
    
    return {
        "virtual_balance": user["virtual_balance"],
        "frozen_balance": user["frozen_balance"],
        "total_gem_value": total_gem_value,
        "available_gem_value": available_gem_value,
        "total_value": user["virtual_balance"] + total_gem_value,
        "daily_limit_used": user["daily_limit_used"],
        "daily_limit_max": user["daily_limit_max"]
    }

@api_router.get("/transactions/history", response_model=List[Transaction])
async def get_transaction_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get user's transaction history."""
    transactions = await db.transactions.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [Transaction(**transaction) for transaction in transactions]

# ==============================================================================
# BASIC API ROUTES
# ==============================================================================

@api_router.get("/", response_model=dict)
async def root():
    """API root endpoint."""
    return {"message": "GemPlay API is running!", "version": "1.0.0"}

@api_router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include routers
app.include_router(auth_router)
app.include_router(api_router)

# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Not found", "detail": "The requested resource was not found"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "detail": "An unexpected error occurred"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)