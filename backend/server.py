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
import random

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
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days for refresh tokens

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

# Bot behavior tracking
bot_activity_tracker = {}

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

class ProfitEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entry_type: str  # "BET_COMMISSION", "GIFT_COMMISSION", "ADMIN_ADJUSTMENT"
    amount: float
    source_user_id: str  # Пользователь, с которого взята комиссия
    reference_id: Optional[str] = None  # ID игры, подарка и т.д.
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    admin_id: Optional[str] = None  # Если создано админом

class FrozenBalance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float
    reason: str  # "BET_COMMISSION", "MAINTENANCE", etc.
    reference_id: Optional[str] = None  # ID игры
    created_at: datetime = Field(default_factory=datetime.utcnow)
    released_at: Optional[datetime] = None
    is_active: bool = True

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
    refresh_token: Optional[str] = None

class RefreshToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class GemResponse(BaseModel):
    type: GemType
    name: str
    price: float
    color: str
    icon: str
    rarity: str
    quantity: int = 0
    frozen_quantity: int = 0

class GemCombinationStrategy(str, Enum):
    SMALL = "small"    # Предпочитает дешевые гемы
    SMART = "smart"    # Сбалансированный подход
    BIG = "big"        # Предпочитает дорогие гемы

class GemCombinationRequest(BaseModel):
    bet_amount: float = Field(..., gt=0, le=3000, description="Target bet amount in dollars")
    strategy: GemCombinationStrategy = Field(..., description="Gem selection strategy")

class GemCombinationItem(BaseModel):
    type: GemType
    name: str
    price: float
    quantity: int
    total_value: float

class GemCombinationResponse(BaseModel):
    success: bool
    total_amount: float
    combinations: List[GemCombinationItem]
    message: Optional[str] = None

class AddBalanceRequest(BaseModel):
    amount: float = Field(..., gt=0, le=1000, description="Amount to add to balance (max $1000)")

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

class CreateGameRequest(BaseModel):
    move: GameMove
    bet_gems: Dict[str, int]

class JoinGameRequest(BaseModel):
    move: GameMove

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

async def create_refresh_token(user_id: str) -> str:
    """Create and store refresh token."""
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Deactivate old refresh tokens for this user
    await db.refresh_tokens.update_many(
        {"user_id": user_id, "is_active": True},
        {"$set": {"is_active": False}}
    )
    
    # Create new refresh token
    token_obj = RefreshToken(
        user_id=user_id,
        token=refresh_token,
        expires_at=expires_at
    )
    await db.refresh_tokens.insert_one(token_obj.dict())
    
    return refresh_token

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
    
    # Clean up old entries (keep only current minute data)
    current_minute_keys = set()
    for i in range(2):  # Keep current and previous minute
        key_time = current_time - timedelta(minutes=i)
        current_minute_keys.add(key_time.strftime("%Y-%m-%d-%H-%M"))
    
    # Remove old entries
    keys_to_remove = []
    for key in list(request_counts.keys()):
        if key.split(":")[-1] not in current_minute_keys:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del request_counts[key]
    
    # Check requests per minute for this IP and user
    ip_key = f"{ip_address}:{minute_key}"
    user_key = f"{user_id}:{minute_key}"
    
    # Initialize if not exists
    if ip_key not in request_counts:
        request_counts[ip_key] = {"count": 0}
    if user_key not in request_counts:
        request_counts[user_key] = {"count": 0}
    
    # Increment counters
    request_counts[ip_key]["count"] += 1
    request_counts[user_key]["count"] += 1
    
    # Check IP rate limit
    if request_counts[ip_key]["count"] > SUSPICIOUS_ACTIVITY_THRESHOLDS["max_requests_per_minute"]:
        await create_security_alert(
            user_id=user_id,
            alert_type="IP_RATE_LIMIT_EXCEEDED",
            severity="HIGH",
            description=f"IP rate limit exceeded: {request_counts[ip_key]['count']} requests in 1 minute",
            ip_address=ip_address,
            request_data={"endpoint": endpoint, "requests_count": request_counts[ip_key]["count"], "limit_type": "IP"}
        )
        return False
    
    # Check user rate limit  
    if request_counts[user_key]["count"] > SUSPICIOUS_ACTIVITY_THRESHOLDS["max_requests_per_minute"]:
        await create_security_alert(
            user_id=user_id,
            alert_type="USER_RATE_LIMIT_EXCEEDED", 
            severity="HIGH",
            description=f"User rate limit exceeded: {request_counts[user_key]['count']} requests in 1 minute",
            ip_address=ip_address,
            request_data={"endpoint": endpoint, "requests_count": request_counts[user_key]["count"], "limit_type": "USER"}
        )
        return False
    
    # Store monitoring data
    monitoring = SecurityMonitoring(
        user_id=user_id,
        ip_address=ip_address,
        endpoint=endpoint,
        request_count=request_counts[user_key]["count"],
        time_window="1m"
    )
    
    # Save to database (fire and forget)
    try:
        await db.security_monitoring.insert_one(monitoring.dict())
    except Exception as e:
        logger.warning(f"Failed to save monitoring data: {e}")
    
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
# GEM COMBINATION CALCULATION FUNCTIONS
# ==============================================================================

async def calculate_gem_combination(user_id: str, target_amount: float, strategy: GemCombinationStrategy) -> GemCombinationResponse:
    """
    Рассчитать точную комбинацию гемов для заданной суммы используя указанную стратегию.
    
    Args:
        user_id: ID пользователя
        target_amount: Целевая сумма ставки
        strategy: Стратегия подбора гемов
    
    Returns:
        GemCombinationResponse с результатом расчета
    """
    # Получаем инвентарь пользователя
    user_gems = await db.user_gems.find({"user_id": user_id}).to_list(100)
    gem_definitions = await db.gem_definitions.find({"enabled": True}).to_list(100)
    
    # Создаем карту определений гемов
    gem_def_map = {gem["type"]: gem for gem in gem_definitions}
    
    # Создаем список доступных гемов с их количеством
    available_gems = []
    for user_gem in user_gems:
        gem_def = gem_def_map.get(user_gem["gem_type"])
        if gem_def and user_gem["quantity"] > user_gem["frozen_quantity"]:
            available_quantity = user_gem["quantity"] - user_gem["frozen_quantity"]
            available_gems.append({
                "type": user_gem["gem_type"],
                "name": gem_def["name"],
                "price": gem_def["price"],
                "available_quantity": available_quantity
            })
    
    if not available_gems:
        return GemCombinationResponse(
            success=False,
            total_amount=0.0,
            combinations=[],
            message="У вас нет доступных гемов для создания ставки"
        )
    
    # Сортируем гемы согласно стратегии
    if strategy == GemCombinationStrategy.SMALL:
        # Small = мелкие гемы (Ruby, Amber, Topaz) - дешевые первыми
        available_gems.sort(key=lambda x: x["price"])
    elif strategy == GemCombinationStrategy.BIG:
        # Big = крупные дорогие гемы (Magic, Sapphire, Aquamarine) - дорогие первыми
        available_gems.sort(key=lambda x: x["price"], reverse=True)
    else:  # SMART
        # Сбалансированный подход - средние цены вперед
        available_gems.sort(key=lambda x: abs(x["price"] - 25.0))  # 25 - примерная средняя цена
    
    # Пытаемся найти точную комбинацию
    result = find_exact_combination(available_gems, target_amount)
    
    if result["success"]:
        # Конвертируем результат в правильный формат
        combination_items = []
        for item in result["combination"]:
            combination_items.append(GemCombinationItem(
                type=item["type"],
                name=item["name"],
                price=item["price"],
                quantity=item["quantity"],
                total_value=item["price"] * item["quantity"]
            ))
        
        return GemCombinationResponse(
            success=True,
            total_amount=result["total_amount"],
            combinations=combination_items,
            message=f"Найдена точная комбинация на сумму ${result['total_amount']}"
        )
    else:
        return GemCombinationResponse(
            success=False,
            total_amount=0.0,
            combinations=[],
            message="Недостаточно доступных гемов для формирования ставки на указанную сумму"
        )

def find_exact_combination(available_gems: List[Dict], target_amount: float) -> Dict:
    """
    Найти точную комбинацию гемов для заданной суммы используя жадный алгоритм с приоритетом.
    
    Args:
        available_gems: Список доступных гемов (уже отсортированный по стратегии)
        target_amount: Целевая сумма
    
    Returns:
        Dict с результатом поиска
    """
    target_cents = int(target_amount * 100)  # Работаем с центами для точности
    
    # Расширяем список доступных гемов с учетом количества каждого
    expanded_gems = []
    for gem in available_gems:
        price_cents = int(gem["price"] * 100)
        for i in range(gem["available_quantity"]):
            expanded_gems.append({
                "type": gem["type"],
                "name": gem["name"],
                "price": gem["price"],
                "price_cents": price_cents,
                "original_gem": gem
            })
    
    # Пытаемся найти точную комбинацию, используя жадный подход с приоритетом
    def find_combination_greedy(gems_list, target):
        """Жадный алгоритм, который учитывает порядок приоритетов"""
        result = []
        remaining = target
        used_gems = {}
        
        # Группируем гемы по типу для контроля количества
        gems_by_type = {}
        for gem in gems_list:
            gem_type = gem["type"]
            if gem_type not in gems_by_type:
                gems_by_type[gem_type] = []
            gems_by_type[gem_type].append(gem)
        
        # Пытаемся найти точную комбинацию
        while remaining > 0:
            found = False
            
            # Проходим по гемам в порядке приоритета
            for gem_type, gems in gems_by_type.items():
                if not gems:
                    continue
                    
                gem = gems[0]
                price_cents = gem["price_cents"]
                
                # Если этот гем может быть использован
                if price_cents <= remaining:
                    # Используем гем
                    result.append(gem)
                    remaining -= price_cents
                    
                    # Убираем использованный гем из списка
                    gems.pop(0)
                    
                    # Обновляем счетчик использованных гемов
                    if gem_type not in used_gems:
                        used_gems[gem_type] = 0
                    used_gems[gem_type] += 1
                    
                    found = True
                    break
            
            if not found:
                # Если не можем найти подходящий гем, пробуем DP
                return find_combination_dp(gems_list, target)
        
        # Конвертируем результат в нужный формат
        combination = []
        for gem_type, quantity in used_gems.items():
            gem_info = next((g for g in expanded_gems if g["type"] == gem_type), None)
            if gem_info:
                combination.append({
                    "type": gem_type,
                    "name": gem_info["name"],
                    "price": gem_info["price"],
                    "quantity": quantity
                })
        
        return combination
    
    def find_combination_dp(gems_list, target):
        """Fallback к DP алгоритму если жадный не работает"""
        # DP table: dp[i] = True if we can make amount i
        dp = [False] * (target + 1)
        dp[0] = True
        
        # parent[i] = информация о том, как получить сумму i
        parent = [None] * (target + 1)
        
        # Заполняем DP таблицу
        for i, gem in enumerate(gems_list):
            price_cents = gem["price_cents"]
            
            # Идем в обратном порядке, чтобы не использовать один гем дважды
            for amount in range(target, price_cents - 1, -1):
                if dp[amount - price_cents]:
                    dp[amount] = True
                    parent[amount] = {
                        "gem_index": i,
                        "prev_amount": amount - price_cents
                    }
        
        # Если точная сумма не найдена
        if not dp[target]:
            return []
        
        # Восстанавливаем путь
        result = []
        current_amount = target
        
        while current_amount > 0 and parent[current_amount]:
            gem_index = parent[current_amount]["gem_index"]
            gem = gems_list[gem_index]
            result.append(gem)
            current_amount = parent[current_amount]["prev_amount"]
        
        # Конвертируем в формат с количеством
        gem_counts = {}
        for gem in result:
            gem_type = gem["type"]
            if gem_type not in gem_counts:
                gem_counts[gem_type] = 0
            gem_counts[gem_type] += 1
        
        combination = []
        for gem_type, quantity in gem_counts.items():
            gem_info = next((g for g in expanded_gems if g["type"] == gem_type), None)
            if gem_info:
                combination.append({
                    "type": gem_type,
                    "name": gem_info["name"],
                    "price": gem_info["price"],
                    "quantity": quantity
                })
        
        return combination
    
    # Пытаемся найти комбинацию
    combination = find_combination_greedy(expanded_gems, target_cents)
    
    if not combination:
        return {"success": False, "combination": [], "total_amount": 0.0}
    
    # Вычисляем итоговую сумму
    total_amount = sum(item["price"] * item["quantity"] for item in combination)
    
    return {
        "success": True,
        "combination": combination,
        "total_amount": total_amount
    }

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
    
    # Create refresh token
    refresh_token = await create_refresh_token(user_obj.id)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        user=UserResponse(**user_obj.dict())
    )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(**current_user.dict())

@auth_router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        # Find and validate refresh token
        token_doc = await db.refresh_tokens.find_one({
            "token": refresh_token,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not token_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user
        user = await db.users.find_one({"id": token_doc["user_id"]})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_obj = User(**user)
        
        # Check if user is still active
        if user_obj.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_obj.id}, expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token = await create_refresh_token(user_obj.id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=new_refresh_token,
            user=UserResponse(**user_obj.dict())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )

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

@auth_router.post("/add-balance", response_model=dict)
async def add_balance(
    request: AddBalanceRequest,
    current_user: User = Depends(get_current_user)
):
    """Add virtual dollars to user balance (within daily limit)."""
    # Check if user has reached daily limit
    remaining_limit = current_user.daily_limit_max - current_user.daily_limit_used
    if remaining_limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily limit already reached"
        )
    
    # Check if requested amount exceeds remaining limit
    if request.amount > remaining_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount exceeds remaining daily limit of ${remaining_limit:.2f}"
        )
    
    # Add balance
    new_balance = current_user.virtual_balance + request.amount
    current_time = datetime.now(TIMEZONE)
    
    # Update user balance
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "virtual_balance": new_balance,
                "daily_limit_used": current_user.daily_limit_used + request.amount,
                "updated_at": current_time
            }
        }
    )
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type=TransactionType.DEPOSIT,
        amount=request.amount,
        balance_before=current_user.virtual_balance,
        balance_after=new_balance,
        description=f"Manual balance addition of ${request.amount:.2f}"
    )
    await db.transactions.insert_one(transaction.dict())
    
    return {
        "message": "Balance added successfully",
        "amount": request.amount,
        "new_balance": new_balance,
        "remaining_daily_limit": remaining_limit - request.amount
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
    
    # Record profit from gift commission
    profit_entry = ProfitEntry(
        entry_type="GIFT_COMMISSION",
        amount=commission,
        source_user_id=current_user.id,
        reference_id=recipient["id"],
        description=f"3% commission from gift: {quantity} {gem_type} gems to {recipient['username']}"
    )
    await db.profit_entries.insert_one(profit_entry.dict())
    
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

@api_router.post("/gems/calculate-combination", response_model=GemCombinationResponse)
async def calculate_gem_combination_endpoint(
    request: GemCombinationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Рассчитать точную комбинацию гемов для заданной суммы ставки.
    
    Этот endpoint принимает целевую сумму и стратегию подбора гемов,
    а возвращает точную комбинацию гемов из инвентаря пользователя.
    """
    if request.bet_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bet amount must be positive"
        )
    
    if request.bet_amount > 3000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bet amount cannot exceed $3000"
        )
    
    # Проверяем, что у пользователя достаточно комиссии для создания ставки
    user = await db.users.find_one({"id": current_user.id})
    commission_amount = request.bet_amount * 0.06  # 6% комиссия
    
    if user["virtual_balance"] < commission_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance for commission. Required: ${commission_amount:.2f}"
        )
    
    # Вызываем функцию расчета комбинации
    result = await calculate_gem_combination(
        user_id=current_user.id,
        target_amount=request.bet_amount,
        strategy=request.strategy
    )
    
    return result

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
# PVP GAME API ROUTES
# ==============================================================================

@api_router.post("/games/create", response_model=dict)
async def create_game(
    request: Request,
    game_data: CreateGameRequest,
    current_user: User = Depends(get_current_user_with_security)
):
    """Create a new PvP game with gem stakes."""
    try:
        # Validate bet gems format
        if not game_data.bet_gems or not isinstance(game_data.bet_gems, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bet gems format"
            )
        
        # Calculate total bet amount and validate gems
        total_bet_amount = 0
        gem_definitions = await db.gem_definitions.find().to_list(100)
        gem_def_map = {gem["type"]: gem for gem in gem_definitions}
        
        for gem_type, quantity in game_data.bet_gems.items():
            if quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid quantity for {gem_type}"
                )
            
            gem_def = gem_def_map.get(gem_type)
            if not gem_def:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid gem type: {gem_type}"
                )
            
            total_bet_amount += gem_def["price"] * quantity
        
        # Check minimum and maximum bet limits
        if total_bet_amount < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum bet is $1"
            )
        if total_bet_amount > 3000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum bet is $3000"
            )
        
        # Check if user has enough gems
        for gem_type, quantity in game_data.bet_gems.items():
            user_gems = await db.user_gems.find_one({"user_id": current_user.id, "gem_type": gem_type})
            if not user_gems:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"You don't have any {gem_type} gems"
                )
            
            available_quantity = user_gems["quantity"] - user_gems["frozen_quantity"]
            if available_quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient {gem_type} gems. Available: {available_quantity}, Required: {quantity}"
                )
        
        # Check if user has enough balance for commission (6% of bet amount)
        commission_required = total_bet_amount * 0.06
        user = await db.users.find_one({"id": current_user.id})
        if user["virtual_balance"] < commission_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance for commission. Required: ${commission_required:.2f}"
            )
        
        # Generate salt and hash the move (commit-reveal scheme)
        salt = str(uuid.uuid4())
        move_hash = hash_move_with_salt(game_data.move, salt)
        
        # Freeze gems for the bet
        for gem_type, quantity in game_data.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": current_user.id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Freeze commission balance
        new_balance = user["virtual_balance"] - commission_required
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$set": {
                    "virtual_balance": new_balance,
                    "frozen_balance": user["frozen_balance"] + commission_required,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Create the game
        game = Game(
            creator_id=current_user.id,
            creator_move=game_data.move,
            creator_move_hash=move_hash,
            creator_salt=salt,
            bet_amount=total_bet_amount,
            bet_gems=game_data.bet_gems,
            status=GameStatus.WAITING
        )
        
        await db.games.insert_one(game.dict())
        
        # Create transaction for freezing gems
        transaction = Transaction(
            user_id=current_user.id,
            transaction_type=TransactionType.BET,
            amount=-total_bet_amount,
            currency="GEM",
            balance_before=0,  # We track gem balance separately
            balance_after=0,
            description=f"Created PvP game with ${total_bet_amount} bet",
            reference_id=game.id
        )
        await db.transactions.insert_one(transaction.dict())
        
        # Monitor for suspicious betting patterns
        await monitor_transaction_patterns(current_user.id, "BET", total_bet_amount)
        
        return {
            "message": "Game created successfully",
            "game_id": game.id,
            "bet_amount": total_bet_amount,
            "commission_reserved": commission_required,
            "new_balance": new_balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create game"
        )

@api_router.post("/games/{game_id}/join", response_model=dict)
async def join_game(
    request: Request,
    game_id: str,
    join_data: JoinGameRequest,
    current_user: User = Depends(get_current_user_with_security)
):
    """Join an existing PvP game."""
    try:
        # Get the game
        game = await db.games.find_one({"id": game_id})
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        game_obj = Game(**game)
        
        # Validate game state
        if game_obj.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not available for joining"
            )
        
        if game_obj.creator_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot join your own game"
            )
        
        if game_obj.opponent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game already has an opponent"
            )
        
        # Check if user has enough gems to match the bet
        for gem_type, quantity in game_obj.bet_gems.items():
            user_gems = await db.user_gems.find_one({"user_id": current_user.id, "gem_type": gem_type})
            if not user_gems:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"You don't have any {gem_type} gems"
                )
            
            available_quantity = user_gems["quantity"] - user_gems["frozen_quantity"]
            if available_quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient {gem_type} gems. Available: {available_quantity}, Required: {quantity}"
                )
        
        # Check if user has enough balance for commission
        commission_required = game_obj.bet_amount * 0.06
        user = await db.users.find_one({"id": current_user.id})
        if user["virtual_balance"] < commission_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance for commission. Required: ${commission_required:.2f}"
            )
        
        # Freeze user's gems
        for gem_type, quantity in game_obj.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": current_user.id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Freeze commission balance
        new_balance = user["virtual_balance"] - commission_required
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$set": {
                    "virtual_balance": new_balance,
                    "frozen_balance": user["frozen_balance"] + commission_required,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update game with opponent
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "opponent_id": current_user.id,
                    "opponent_move": join_data.move,
                    "status": GameStatus.ACTIVE,
                    "started_at": datetime.utcnow()
                }
            }
        )
        
        # Determine winner immediately
        result = await determine_game_winner(game_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join game"
        )

async def determine_game_winner(game_id: str) -> dict:
    """Determine the winner of a PvP game and distribute rewards."""
    try:
        # Get updated game
        game = await db.games.find_one({"id": game_id})
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        game_obj = Game(**game)
        
        # Verify move hash (commit-reveal)
        if not verify_move_hash(game_obj.creator_move, game_obj.creator_salt, game_obj.creator_move_hash):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Move verification failed"
            )
        
        # Determine winner using rock-paper-scissors logic
        creator_move = game_obj.creator_move
        opponent_move = game_obj.opponent_move
        
        winner_id = None
        result_status = "draw"
        
        if creator_move == opponent_move:
            result_status = "draw"
        elif (
            (creator_move == GameMove.ROCK and opponent_move == GameMove.SCISSORS) or
            (creator_move == GameMove.SCISSORS and opponent_move == GameMove.PAPER) or
            (creator_move == GameMove.PAPER and opponent_move == GameMove.ROCK)
        ):
            winner_id = game_obj.creator_id
            result_status = "creator_wins"
        else:
            winner_id = game_obj.opponent_id
            result_status = "opponent_wins"
        
        # Calculate commission
        total_pot = game_obj.bet_amount * 2  # Both players' bets
        commission_amount = total_pot * 0.03 if winner_id else 0  # 3% only if there's a winner
        
        # Update game status
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "status": GameStatus.COMPLETED,
                    "winner_id": winner_id,
                    "commission_amount": commission_amount,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Distribute rewards
        await distribute_game_rewards(game_obj, winner_id, commission_amount)
        
        # Update bot cycle tracking if applicable
        if game_obj.is_bot_game and game_obj.bot_id:
            await update_bot_cycle_tracking(game_obj.bot_id, winner_id == game_obj.bot_id)
        
        # Get user details for response
        creator = await db.users.find_one({"id": game_obj.creator_id})
        if not creator:
            # Creator might be a bot
            creator = await db.bots.find_one({"id": game_obj.creator_id})
            if creator:
                creator = {"id": creator["id"], "username": creator["name"]}
        
        opponent = await db.users.find_one({"id": game_obj.opponent_id})
        if not opponent:
            # Opponent might be a bot
            opponent = await db.bots.find_one({"id": game_obj.opponent_id})
            if opponent:
                opponent = {"id": opponent["id"], "username": opponent["name"]}
        
        return {
            "game_id": game_id,
            "result": result_status,
            "creator_move": creator_move.value,
            "opponent_move": opponent_move.value,
            "winner_id": winner_id,
            "creator": {
                "id": creator["id"],
                "username": creator["username"]
            },
            "opponent": {
                "id": opponent["id"], 
                "username": opponent["username"]
            },
            "bet_amount": game_obj.bet_amount,
            "total_pot": total_pot,
            "commission": commission_amount,
            "gems_won": game_obj.bet_gems if winner_id else None
        }
        
    except Exception as e:
        logger.error(f"Error determining game winner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to determine game winner"
        )

async def distribute_game_rewards(game: Game, winner_id: str, commission_amount: float):
    """Distribute gems and handle commissions after game completion."""
    try:
        # Unfreeze gems for both players
        for player_id in [game.creator_id, game.opponent_id]:
            for gem_type, quantity in game.bet_gems.items():
                await db.user_gems.update_one(
                    {"user_id": player_id, "gem_type": gem_type},
                    {
                        "$inc": {"frozen_quantity": -quantity},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
        
        if winner_id:
            # Winner gets all gems (double the bet)
            for gem_type, quantity in game.bet_gems.items():
                await db.user_gems.update_one(
                    {"user_id": winner_id, "gem_type": gem_type},
                    {
                        "$inc": {"quantity": quantity},  # Winner keeps their gems + gets opponent's
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                
                # Remove gems from loser
                loser_id = game.opponent_id if winner_id == game.creator_id else game.creator_id
                await db.user_gems.update_one(
                    {"user_id": loser_id, "gem_type": gem_type},
                    {
                        "$inc": {"quantity": -quantity},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            
            # Handle commission for winner
            winner = await db.users.find_one({"id": winner_id})
            if winner:
                # Winner is a human player
                commission_to_deduct = commission_amount  # 3% of total pot
                
                new_winner_balance = winner["virtual_balance"]
                new_winner_frozen = winner["frozen_balance"] - (game.bet_amount * 0.06)  # Unfreeze winner's commission
                
                # Deduct actual commission from winner's balance
                if new_winner_frozen >= commission_to_deduct:
                    new_winner_frozen -= commission_to_deduct
                else:
                    remaining = commission_to_deduct - new_winner_frozen
                    new_winner_balance -= remaining
                    new_winner_frozen = 0
                
                await db.users.update_one(
                    {"id": winner_id},
                    {
                        "$set": {
                            "virtual_balance": new_winner_balance,
                            "frozen_balance": new_winner_frozen,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Record commission transaction
                commission_transaction = Transaction(
                    user_id=winner_id,
                    transaction_type=TransactionType.COMMISSION,
                    amount=commission_amount,
                    currency="USD",
                    balance_before=winner["virtual_balance"],
                    balance_after=new_winner_balance,
                    description=f"PvP game commission (3% of ${game.bet_amount * 2})",
                    reference_id=game.id
                )
                await db.transactions.insert_one(commission_transaction.dict())
                
                # Record profit entry from bet commission
                profit_entry = ProfitEntry(
                    entry_type="BET_COMMISSION",
                    amount=commission_amount,
                    source_user_id=winner_id,
                    reference_id=game.id,
                    description=f"6% commission from PvP game victory: ${game.bet_amount * 2} total pot"
                )
                await db.profit_entries.insert_one(profit_entry.dict())
            
            # Handle commission for loser
            loser_id = game.opponent_id if winner_id == game.creator_id else game.creator_id
            loser = await db.users.find_one({"id": loser_id})
            
            if loser:
                # Loser is a human player - return frozen commission
                await db.users.update_one(
                    {"id": loser_id},
                    {
                        "$set": {
                            "virtual_balance": loser["virtual_balance"] + (game.bet_amount * 0.06),
                            "frozen_balance": loser["frozen_balance"] - (game.bet_amount * 0.06),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
        else:
            # Draw - return frozen commissions to both players (only human players)
            for player_id in [game.creator_id, game.opponent_id]:
                player = await db.users.find_one({"id": player_id})
                if player:  # Only process human players
                    commission_to_return = game.bet_amount * 0.06
                    
                    await db.users.update_one(
                        {"id": player_id},
                        {
                            "$set": {
                                "virtual_balance": player["virtual_balance"] + commission_to_return,
                                "frozen_balance": player["frozen_balance"] - commission_to_return,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
        
        # Record game result transactions (only for human players)
        result_description = "Draw - gems returned" if not winner_id else f"{'Won' if winner_id == game.creator_id else 'Lost'} PvP game"
        
        for player_id in [game.creator_id, game.opponent_id]:
            player = await db.users.find_one({"id": player_id})
            if player:  # Only create transactions for human players
                is_winner = player_id == winner_id
                gem_change = game.bet_amount if is_winner else (-game.bet_amount if winner_id else 0)
                
                transaction = Transaction(
                    user_id=player_id,
                    transaction_type=TransactionType.WIN if is_winner else TransactionType.BET,
                    amount=gem_change,
                    currency="GEM",
                    balance_before=0,
                    balance_after=0,
                    description=result_description,
                    reference_id=game.id
                )
                await db.transactions.insert_one(transaction.dict())
            
    except Exception as e:
        logger.error(f"Error distributing game rewards: {e}")
        raise

@api_router.get("/games/available", response_model=List[dict])
async def get_available_games(current_user: User = Depends(get_current_user)):
    """Get list of available games for joining."""
    try:
        # Get waiting games (exclude user's own games)
        games = await db.games.find({
            "status": GameStatus.WAITING,
            "creator_id": {"$ne": current_user.id}
        }).sort("created_at", -1).limit(50).to_list(50)
        
        result = []
        for game in games:
            # Get creator info
            creator = await db.users.find_one({"id": game["creator_id"]})
            if not creator:
                continue
                
            # Calculate time remaining (24 hour limit)
            created_time = game["created_at"]
            time_remaining = created_time + timedelta(hours=24) - datetime.utcnow()
            
            if time_remaining.total_seconds() <= 0:
                # Game expired, mark as cancelled
                await db.games.update_one(
                    {"id": game["id"]},
                    {
                        "$set": {
                            "status": GameStatus.CANCELLED,
                            "cancelled_at": datetime.utcnow()
                        }
                    }
                )
                continue
            
            result.append({
                "game_id": game["id"],
                "creator": {
                    "id": creator["id"],
                    "username": creator["username"],
                    "gender": creator["gender"]
                },
                "bet_amount": game["bet_amount"],
                "bet_gems": game["bet_gems"],
                "created_at": game["created_at"],
                "time_remaining_hours": time_remaining.total_seconds() / 3600
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting live games: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get live games"
        )

@api_router.get("/games/my-bets", response_model=List[dict])
async def get_my_bets(current_user: User = Depends(get_current_user)):
    """Get user's active and recent bets."""
    try:
        # Get user's games (created or joined)
        games = await db.games.find({
            "$or": [
                {"creator_id": current_user.id},
                {"opponent_id": current_user.id}
            ]
        }).sort("created_at", -1).limit(20).to_list(20)
        
        result = []
        for game in games:
            # Get opponent info
            opponent_id = game["opponent_id"] if game["creator_id"] == current_user.id else game["creator_id"]
            opponent = None
            if opponent_id:
                opponent = await db.users.find_one({"id": opponent_id})
            
            is_creator = game["creator_id"] == current_user.id
            
            game_data = {
                "game_id": game["id"],
                "is_creator": is_creator,
                "bet_amount": game["bet_amount"],
                "bet_gems": game["bet_gems"],
                "status": game["status"],
                "created_at": game["created_at"],
                "opponent": {
                    "id": opponent["id"],
                    "username": opponent["username"],
                    "gender": opponent["gender"]
                } if opponent else None
            }
            
            # Add result info if completed
            if game["status"] == GameStatus.COMPLETED:
                game_data.update({
                    "winner_id": game.get("winner_id"),
                    "creator_move": game.get("creator_move"),
                    "opponent_move": game.get("opponent_move"),
                    "commission": game.get("commission_amount", 0),
                    "completed_at": game.get("completed_at")
                })
            
            result.append(game_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting user bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user bets"
        )

@api_router.delete("/games/{game_id}/cancel", response_model=dict)
async def cancel_game(game_id: str, current_user: User = Depends(get_current_user)):
    """Cancel a waiting game."""
    try:
        # Get the game
        game = await db.games.find_one({"id": game_id})
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        game_obj = Game(**game)
        
        # Validate permissions
        if game_obj.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only game creator can cancel the game"
            )
        
        if game_obj.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel waiting games"
            )
        
        # Unfreeze creator's gems
        for gem_type, quantity in game_obj.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": current_user.id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Return frozen commission
        user = await db.users.find_one({"id": current_user.id})
        commission_to_return = game_obj.bet_amount * 0.06
        
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$set": {
                    "virtual_balance": user["virtual_balance"] + commission_to_return,
                    "frozen_balance": user["frozen_balance"] - commission_to_return,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update game status
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "status": GameStatus.CANCELLED,
                    "cancelled_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Game cancelled successfully",
            "gems_returned": game_obj.bet_gems,
            "commission_returned": commission_to_return
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel game"
        )

# ==============================================================================
# ADMIN SECURITY MONITORING API
# ==============================================================================

@api_router.get("/admin/security/alerts", response_model=List[SecurityAlert])
async def get_security_alerts(
    limit: int = 50,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    current_admin: User = Depends(get_current_admin)
):
    """Get security alerts for admin monitoring."""
    query = {}
    if severity:
        query["severity"] = severity
    if resolved is not None:
        query["resolved"] = resolved
    
    alerts = await db.security_alerts.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [SecurityAlert(**alert) for alert in alerts]

@api_router.get("/admin/security/dashboard", response_model=dict)
async def get_security_dashboard(current_admin: User = Depends(get_current_admin)):
    """Get security monitoring dashboard data."""
    try:
        current_time = datetime.utcnow()
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(days=1)
        week_ago = current_time - timedelta(days=7)
        
        # Count alerts by severity (last 24h)
        alert_counts = {
            "critical": await db.security_alerts.count_documents({
                "severity": "CRITICAL",
                "created_at": {"$gte": day_ago}
            }),
            "high": await db.security_alerts.count_documents({
                "severity": "HIGH",
                "created_at": {"$gte": day_ago}
            }),
            "medium": await db.security_alerts.count_documents({
                "severity": "MEDIUM",
                "created_at": {"$gte": day_ago}
            }),
            "low": await db.security_alerts.count_documents({
                "severity": "LOW",
                "created_at": {"$gte": day_ago}
            })
        }
        
        # Recent suspicious activities
        recent_activities = await db.security_alerts.find({
            "created_at": {"$gte": hour_ago}
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # Top alert types (last 7 days) - simplified query
        alert_types_cursor = db.security_alerts.find({
            "created_at": {"$gte": week_ago}
        })
        
        alert_types_dict = {}
        async for alert in alert_types_cursor:
            alert_type = alert.get("alert_type", "UNKNOWN")
            alert_types_dict[alert_type] = alert_types_dict.get(alert_type, 0) + 1
        
        top_alert_types = [
            {"_id": alert_type, "count": count}
            for alert_type, count in sorted(alert_types_dict.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Users with most alerts (last 7 days) - simplified query
        user_alerts_cursor = db.security_alerts.find({
            "created_at": {"$gte": week_ago}
        })
        
        user_alerts_dict = {}
        async for alert in user_alerts_cursor:
            user_id = alert.get("user_id", "UNKNOWN")
            user_alerts_dict[user_id] = user_alerts_dict.get(user_id, 0) + 1
        
        users_with_alerts = [
            {"_id": user_id, "count": count}
            for user_id, count in sorted(user_alerts_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Get user details for top alerting users
        for user_alert in users_with_alerts:
            try:
                user = await db.users.find_one({"id": user_alert["_id"]})
                user_alert["username"] = user["username"] if user else "Unknown"
                user_alert["email"] = user["email"] if user else "Unknown"
            except Exception:
                user_alert["username"] = "Unknown"
                user_alert["email"] = "Unknown"
        
        return {
            "alert_counts": alert_counts,
            "recent_activities": recent_activities,
            "top_alert_types": top_alert_types,
            "users_with_most_alerts": users_with_alerts,
            "total_alerts_24h": sum(alert_counts.values()),
            "unresolved_alerts": await db.security_alerts.count_documents({"resolved": False})
        }
    
    except Exception as e:
        logger.error(f"Error in security dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching security dashboard data: {str(e)}"
        )

@api_router.post("/admin/reset-all-games")
async def reset_all_games(current_admin: User = Depends(get_current_admin)):
    """Reset all active games and unfreeze all funds."""
    try:
        # Get all active games (WAITING and ACTIVE status)
        active_games = await db.games.find({
            "status": {"$in": [GameStatus.WAITING, GameStatus.ACTIVE]}
        }).to_list(1000)
        
        games_cancelled = 0
        total_gems_unfrozen = 0
        total_balance_unfrozen = 0.0
        
        for game in active_games:
            game_obj = Game(**game)
            
            # Unfreeze creator's gems
            for gem_type, quantity in game_obj.bet_gems.items():
                await db.user_gems.update_one(
                    {"user_id": game_obj.creator_id, "gem_type": gem_type},
                    {"$inc": {"frozen_quantity": -quantity}},
                    upsert=False
                )
                total_gems_unfrozen += quantity
            
            # Unfreeze creator's commission
            creator_commission = game_obj.bet_amount * 0.06
            await db.users.update_one(
                {"id": game_obj.creator_id},
                {
                    "$inc": {
                        "frozen_balance": -creator_commission,
                        "virtual_balance": creator_commission
                    }
                }
            )
            total_balance_unfrozen += creator_commission
            
            # If game has opponent, unfreeze their funds too
            if game_obj.opponent_id:
                opponent_commission = game_obj.bet_amount * 0.06
                await db.users.update_one(
                    {"id": game_obj.opponent_id},
                    {
                        "$inc": {
                            "frozen_balance": -opponent_commission,
                            "virtual_balance": opponent_commission
                        }
                    }
                )
                total_balance_unfrozen += opponent_commission
            
            # Mark game as cancelled
            await db.games.update_one(
                {"id": game_obj.id},
                {
                    "$set": {
                        "status": GameStatus.CANCELLED,
                        "cancelled_at": datetime.utcnow()
                    }
                }
            )
            games_cancelled += 1
        
        # Reset all users' frozen quantities to 0 (safety measure)
        await db.user_gems.update_many(
            {"frozen_quantity": {"$gt": 0}},
            {"$set": {"frozen_quantity": 0}}
        )
        
        # Reset all users' frozen balance to 0 (safety measure)
        users_with_frozen = await db.users.find({"frozen_balance": {"$gt": 0}}).to_list(1000)
        for user in users_with_frozen:
            await db.users.update_one(
                {"id": user["id"]},
                {
                    "$inc": {"virtual_balance": user["frozen_balance"]},
                    "$set": {"frozen_balance": 0}
                }
            )
        
        return {
            "success": True,
            "message": f"All games reset successfully",
            "games_cancelled": games_cancelled,
            "total_gems_unfrozen": total_gems_unfrozen,
            "total_balance_unfrozen": round(total_balance_unfrozen, 2)
        }
        
    except Exception as e:
        logger.error(f"Error resetting all games: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset games: {str(e)}"
        )

@api_router.post("/admin/security/alerts/{alert_id}/resolve", response_model=dict)
async def resolve_security_alert(
    alert_id: str,
    action_taken: str,
    current_admin: User = Depends(get_current_admin)
):
    """Resolve a security alert."""
    result = await db.security_alerts.update_one(
        {"id": alert_id},
        {
            "$set": {
                "resolved": True,
                "resolved_at": datetime.utcnow(),
                "resolved_by": current_admin.id,
                "action_taken": action_taken
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security alert not found"
        )
    
    # Log admin action
    admin_log = AdminLog(
        admin_id=current_admin.id,
        action="RESOLVE_SECURITY_ALERT",
        target_type="security_alert",
        target_id=alert_id,
        details={"action_taken": action_taken}
    )
    await db.admin_logs.insert_one(admin_log.dict())
    
    return {"message": "Security alert resolved successfully"}

@api_router.get("/admin/security/suspicious-activities", response_model=List[SuspiciousActivity])
async def get_suspicious_activities(
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_admin: User = Depends(get_current_admin)
):
    """Get suspicious activities for investigation."""
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    activities = await db.suspicious_activities.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [SuspiciousActivity(**activity) for activity in activities]

@api_router.get("/admin/security/monitoring-stats", response_model=dict)
async def get_monitoring_stats(current_admin: User = Depends(get_current_admin)):
    """Get security monitoring statistics."""
    current_time = datetime.utcnow()
    day_ago = current_time - timedelta(days=1)
    
    # Transaction monitoring
    recent_transactions = await db.transactions.find({
        "created_at": {"$gte": day_ago}
    }).to_list(1000)
    
    # Calculate stats
    total_volume = sum(abs(t["amount"]) for t in recent_transactions)
    purchase_volume = sum(t["amount"] for t in recent_transactions if t["transaction_type"] == "PURCHASE")
    gift_volume = sum(abs(t["amount"]) for t in recent_transactions if t["transaction_type"] == "GIFT")
    
    # High-value transactions (>$100)
    high_value_transactions = [t for t in recent_transactions if abs(t["amount"]) > 100]
    
    # User activity stats
    active_users_24h = len(set(t["user_id"] for t in recent_transactions))
    
    # Rate limiting stats (from memory - in production use Redis)
    total_requests_blocked = sum(
        1 for ip_data in request_counts.values()
        for count_data in ip_data.values()
        if count_data.get("count", 0) > SUSPICIOUS_ACTIVITY_THRESHOLDS["max_requests_per_minute"]
    )
    
    return {
        "transaction_stats": {
            "total_volume_24h": total_volume,
            "purchase_volume_24h": purchase_volume,
            "gift_volume_24h": gift_volume,
            "transaction_count_24h": len(recent_transactions),
            "high_value_transactions_24h": len(high_value_transactions)
        },
        "user_activity": {
            "active_users_24h": active_users_24h
        },
        "security_stats": {
            "requests_blocked_24h": total_requests_blocked,
            "rate_limit_threshold": SUSPICIOUS_ACTIVITY_THRESHOLDS["max_requests_per_minute"]
        }
    }

# ==============================================================================
# BASIC API ROUTES
# ==============================================================================

@api_router.get("/", response_model=dict)
async def root():
    """API root endpoint."""
    return {"message": "GemPlay API is running!", "version": "1.0.0"}

@api_router.get("/leaderboard/{category}", response_model=dict)
async def get_leaderboard(category: str, current_user: User = Depends(get_current_user)):
    """Get leaderboard by category (winnings, wins, winrate, games)."""
    try:
        # Define sort criteria based on category
        sort_criteria = {
            "winnings": {"total_amount_won": -1},
            "wins": {"total_games_won": -1},
            "winrate": {"win_rate": -1},
            "games": {"total_games_played": -1}
        }
        
        if category not in sort_criteria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category. Use: winnings, wins, winrate, games"
            )
        
        # Get top users
        users = await db.users.find(
            {"status": "ACTIVE"},
            {
                "username": 1,
                "total_amount_won": 1,
                "total_games_won": 1,
                "total_games_played": 1,
                "created_at": 1
            }
        ).sort(sort_criteria[category]).limit(100).to_list(100)
        
        # Calculate win rates and add ranks
        leaderboard = []
        for idx, user_data in enumerate(users):
            win_rate = 0
            if user_data.get("total_games_played", 0) > 0:
                win_rate = round((user_data.get("total_games_won", 0) / user_data["total_games_played"]) * 100, 1)
            
            leaderboard.append({
                "rank": idx + 1,
                "user_id": user_data["id"],
                "username": user_data["username"],
                "total_winnings": user_data.get("total_amount_won", 0),
                "games_won": user_data.get("total_games_won", 0),
                "games_played": user_data.get("total_games_played", 0),
                "win_rate": win_rate,
                "level": min(user_data.get("total_games_played", 0) // 10 + 1, 50),  # Level based on games played
                "favorite_gem": ["Ruby", "Emerald", "Sapphire", "Diamond", "Topaz"][idx % 5]  # Mock favorite gem
            })
        
        # Find current user's rank
        user_rank = None
        for idx, entry in enumerate(leaderboard):
            if entry["user_id"] == current_user.id:
                user_rank = idx + 1
                break
        
        if user_rank is None:
            # User not in top 100, calculate approximate rank
            user_rank = 101  # Placeholder
        
        return {
            "leaderboard": leaderboard,
            "user_rank": user_rank,
            "category": category
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaderboard"
        )

@api_router.get("/games/history", response_model=dict)
async def get_game_history(
    status_filter: str = None,
    date_filter: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's game history with optional filters."""
    try:
        # Build query filter
        query = {
            "$or": [
                {"creator_id": current_user.id},
                {"opponent_id": current_user.id}
            ]
        }
        
        # Add status filter
        if status_filter and status_filter != "all":
            if status_filter in ["won", "lost", "draw"]:
                # We need to determine win/loss based on user perspective
                pass  # Will handle in processing
            else:
                query["status"] = status_filter.upper()
        
        # Add date filter
        if date_filter and date_filter != "all":
            now = datetime.utcnow()
            if date_filter == "today":
                start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query["created_at"] = {"$gte": start_of_day}
            elif date_filter == "week":
                start_of_week = now - timedelta(days=7)
                query["created_at"] = {"$gte": start_of_week}
            elif date_filter == "month":
                start_of_month = now - timedelta(days=30)
                query["created_at"] = {"$gte": start_of_month}
        
        # Get games
        games = await db.games.find(query).sort("created_at", -1).limit(200).to_list(200)
        
        # Process games and determine results from user perspective
        processed_games = []
        stats = {
            "total_games": 0,
            "total_won": 0,
            "total_lost": 0,
            "total_draw": 0,
            "total_winnings": 0,
            "total_losses": 0
        }
        
        for game in games:
            if game["status"] != "COMPLETED":
                continue
            
            # Determine user's role and result
            is_creator = game["creator_id"] == current_user.id
            opponent_id = game["opponent_id"] if is_creator else game["creator_id"]
            my_move = game["creator_move"] if is_creator else game["opponent_move"]
            opponent_move = game["opponent_move"] if is_creator else game["creator_move"]
            
            # Get opponent info
            opponent = await db.users.find_one({"id": opponent_id})
            opponent_username = opponent["username"] if opponent else "Unknown"
            
            # Determine result
            result = "draw"  # Default
            if game.get("winner_id"):
                if game["winner_id"] == current_user.id:
                    result = "won"
                    stats["total_won"] += 1
                    stats["total_winnings"] += game["bet_amount"] * 1.94  # After 3% commission
                else:
                    result = "lost"
                    stats["total_lost"] += 1
                    stats["total_losses"] += game["bet_amount"]
            else:
                stats["total_draw"] += 1
            
            # Apply status filter if specified
            if status_filter and status_filter != "all" and status_filter != result:
                continue
            
            game_data = {
                "id": game["id"],
                "opponent_username": opponent_username,
                "opponent_id": opponent_id,
                "is_bot_game": game.get("is_bot_game", False),
                "my_move": my_move,
                "opponent_move": opponent_move,
                "bet_amount": game["bet_amount"],
                "bet_gems": game["bet_gems"],
                "status": game["status"],
                "result": result,
                "winnings": game["bet_amount"] * 1.94 if result == "won" else 0,
                "created_at": game["created_at"],
                "completed_at": game.get("completed_at", game["created_at"]),
                "game_duration": 120  # Mock duration in seconds
            }
            
            processed_games.append(game_data)
            stats["total_games"] += 1
        
        return {
            "games": processed_games,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch game history"
        )

@api_router.get("/bots", response_model=List[dict])
async def get_bots(current_user: User = Depends(get_current_admin)):
    """Get all bots (admin only)."""
    try:
        bots = await db.bots.find().to_list(100)
        # Clean up the bot data to ensure JSON serialization
        cleaned_bots = []
        for bot in bots:
            cleaned_bot = {
                "id": bot.get("id"),
                "name": bot.get("name"),
                "bot_type": bot.get("bot_type"),
                "is_active": bot.get("is_active", True),
                "min_bet": bot.get("min_bet", 1.0),
                "max_bet": bot.get("max_bet", 1000.0),
                "win_rate": bot.get("win_rate", 0.6),
                "cycle_games": bot.get("cycle_games", 12),
                "current_cycle_games": bot.get("current_cycle_games", 0),
                "current_cycle_wins": bot.get("current_cycle_wins", 0),
                "pause_between_games": bot.get("pause_between_games", 60),
                "last_game_time": bot.get("last_game_time"),
                "can_accept_bets": bot.get("can_accept_bets", False),
                "can_play_with_bots": bot.get("can_play_with_bots", False),
                "avatar_gender": bot.get("avatar_gender", "male"),
                "simple_mode": bot.get("simple_mode", False),
                "created_at": bot.get("created_at")
            }
            cleaned_bots.append(cleaned_bot)
        return cleaned_bots
    except Exception as e:
        logger.error(f"Error fetching bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bots"
        )

@api_router.post("/bots", response_model=dict)
async def create_bot(
    bot_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Create a new bot (admin only)."""
    try:
        # Validate bot data
        required_fields = ["name", "bot_type", "win_rate"]
        for field in required_fields:
            if field not in bot_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Create bot
        bot = Bot(
            name=bot_data["name"],
            bot_type=bot_data["bot_type"],
            win_rate=min(max(bot_data["win_rate"], 0.1), 0.9),  # 10% to 90%
            min_bet=bot_data.get("min_bet", 1.0),
            max_bet=bot_data.get("max_bet", 1000.0),
            cycle_games=bot_data.get("cycle_games", 12),
            pause_between_games=bot_data.get("pause_between_games", 60),
            can_accept_bets=bot_data.get("can_accept_bets", False),
            can_play_with_bots=bot_data.get("can_play_with_bots", False),
            avatar_gender=bot_data.get("avatar_gender", "male"),
            simple_mode=bot_data.get("simple_mode", False)
        )
        
        await db.bots.insert_one(bot.dict())
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="CREATE_BOT",
            target_type="bot",
            target_id=bot.id,
            details={"bot_name": bot.name, "bot_type": bot.bot_type}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "Bot created successfully", "bot_id": bot.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bot"
        )

@api_router.put("/bots/{bot_id}", response_model=dict)
async def update_bot(
    bot_id: str,
    bot_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update bot settings (admin only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Update fields
        update_fields = {}
        if "name" in bot_data:
            update_fields["name"] = bot_data["name"]
        if "is_active" in bot_data:
            update_fields["is_active"] = bot_data["is_active"]
        if "win_rate" in bot_data:
            update_fields["win_rate"] = min(max(bot_data["win_rate"], 0.1), 0.9)
        if "min_bet" in bot_data:
            update_fields["min_bet"] = bot_data["min_bet"]
        if "max_bet" in bot_data:
            update_fields["max_bet"] = bot_data["max_bet"]
        if "cycle_games" in bot_data:
            update_fields["cycle_games"] = bot_data["cycle_games"]
        if "pause_between_games" in bot_data:
            update_fields["pause_between_games"] = bot_data["pause_between_games"]
        if "can_accept_bets" in bot_data:
            update_fields["can_accept_bets"] = bot_data["can_accept_bets"]
        if "can_play_with_bots" in bot_data:
            update_fields["can_play_with_bots"] = bot_data["can_play_with_bots"]
        if "avatar_gender" in bot_data:
            update_fields["avatar_gender"] = bot_data["avatar_gender"]
        if "simple_mode" in bot_data:
            update_fields["simple_mode"] = bot_data["simple_mode"]
        
        update_fields["updated_at"] = datetime.utcnow()
        
        # Update bot
        await db.bots.update_one(
            {"id": bot_id},
            {"$set": update_fields}
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="UPDATE_BOT",
            target_type="bot",
            target_id=bot_id,
            details={"updated_fields": list(update_fields.keys())}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "Bot updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot"
        )

@api_router.delete("/bots/{bot_id}", response_model=dict)
async def delete_bot(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Delete a bot (admin only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if bot has active games
        active_games = await db.games.find({
            "$or": [
                {"creator_id": bot_id, "status": {"$in": ["WAITING", "ACTIVE"]}},
                {"opponent_id": bot_id, "status": {"$in": ["WAITING", "ACTIVE"]}}
            ]
        }).to_list(1)
        
        if active_games:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete bot with active games"
            )
        
        # Delete bot
        await db.bots.delete_one({"id": bot_id})
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="DELETE_BOT",
            target_type="bot",
            target_id=bot_id,
            details={"bot_name": bot["name"]}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "Bot deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bot"
        )

@api_router.post("/bots/{bot_id}/toggle", response_model=dict)
async def toggle_bot_status(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Toggle bot active status (admin only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Toggle status
        new_status = not bot["is_active"]
        await db.bots.update_one(
            {"id": bot_id},
            {
                "$set": {
                    "is_active": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="TOGGLE_BOT_STATUS",
            target_type="bot",
            target_id=bot_id,
            details={"new_status": new_status, "bot_name": bot["name"]}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "message": f"Bot {'activated' if new_status else 'deactivated'} successfully",
            "is_active": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling bot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle bot status"
        )

@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# ==============================================================================
# BOT GAME LOGIC AND ALGORITHMS
# ==============================================================================

class BotGameLogic:
    """Bot game logic and decision-making algorithms."""
    
    @staticmethod
    def calculate_bot_move(bot: Bot, game_context: dict = None) -> GameMove:
        """Calculate bot's move based on its type and settings."""
        import random
        
        if bot.bot_type == BotType.REGULAR:
            # Regular bot: Simple random selection
            return random.choice([GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS])
        
        elif bot.bot_type == BotType.HUMAN:
            # Human bot: More sophisticated decision making
            if bot.simple_mode:
                # Simple human mode: slight bias towards rock
                choices = [GameMove.ROCK, GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
                return random.choice(choices)
            else:
                # Complex human mode: pattern-based decisions
                # In a real implementation, this could analyze opponent patterns
                # For now, we'll use weighted random selection
                weights = [0.35, 0.35, 0.30]  # Rock, Paper, Scissors
                moves = [GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
                return random.choices(moves, weights=weights)[0]
        
        return GameMove.ROCK  # Default fallback
    
    @staticmethod
    def should_bot_win(bot: Bot) -> bool:
        """Determine if bot should win based on win rate and cycle management."""
        import random
        
        # Check if we're in a cycle management mode
        if bot.cycle_games > 0:
            # Calculate current win rate in cycle
            if bot.current_cycle_games > 0:
                current_win_rate = bot.current_cycle_wins / bot.current_cycle_games
                target_win_rate = bot.win_rate
                
                # If we're behind target, increase win probability
                if current_win_rate < target_win_rate:
                    adjusted_win_rate = min(0.9, target_win_rate + 0.1)
                    return random.random() < adjusted_win_rate
                # If we're ahead, decrease win probability
                elif current_win_rate > target_win_rate:
                    adjusted_win_rate = max(0.1, target_win_rate - 0.1)
                    return random.random() < adjusted_win_rate
        
        # Standard win rate check
        return random.random() < bot.win_rate
    
    @staticmethod
    def get_bot_move_against_player(bot: Bot, player_move: GameMove) -> GameMove:
        """Get bot move specifically to beat or lose to player move."""
        should_win = BotGameLogic.should_bot_win(bot)
        
        if should_win:
            # Bot should win
            if player_move == GameMove.ROCK:
                return GameMove.PAPER
            elif player_move == GameMove.PAPER:
                return GameMove.SCISSORS
            else:  # SCISSORS
                return GameMove.ROCK
        else:
            # Bot should lose
            if player_move == GameMove.ROCK:
                return GameMove.SCISSORS
            elif player_move == GameMove.PAPER:
                return GameMove.ROCK
            else:  # SCISSORS
                return GameMove.PAPER
    
    @staticmethod
    async def setup_bot_gems(bot_id: str, db):
        """Ensure bot has adequate gems for gameplay."""
        # Check bot's current gems
        bot_gems = await db.user_gems.find({"user_id": bot_id}).to_list(100)
        
        # Define minimum required gems for each type
        required_gems = {gem_type.value: 100 for gem_type in GemType}
        
        for gem_type, min_quantity in required_gems.items():
            existing_gem = next((g for g in bot_gems if g["gem_type"] == gem_type), None)
            
            if not existing_gem:
                # Create new gem entry
                new_gem = UserGem(
                    user_id=bot_id,
                    gem_type=gem_type,
                    quantity=min_quantity
                )
                await db.user_gems.insert_one(new_gem.dict())
            elif existing_gem["quantity"] < min_quantity:
                # Top up existing gems
                await db.user_gems.update_one(
                    {"user_id": bot_id, "gem_type": gem_type},
                    {
                        "$set": {
                            "quantity": min_quantity,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

@api_router.post("/bots/{bot_id}/setup-gems", response_model=dict)
async def setup_bot_gems(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Setup gems for a bot (admin only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Setup gems
        await BotGameLogic.setup_bot_gems(bot_id, db)
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="SETUP_BOT_GEMS",
            target_type="bot",
            target_id=bot_id,
            details={"bot_name": bot["name"]}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "Bot gems setup successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up bot gems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup bot gems"
        )

@api_router.post("/bots/{bot_id}/create-game", response_model=dict)
async def bot_create_game(
    bot_id: str,
    game_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Make a bot create a game (admin only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        bot_obj = Bot(**bot)
        
        if not bot_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not active"
            )
        
        # Validate bet amount is within bot's limits
        bet_amount = game_data.get("bet_amount", 10.0)
        if bet_amount < bot_obj.min_bet or bet_amount > bot_obj.max_bet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bet amount must be between {bot_obj.min_bet} and {bot_obj.max_bet}"
            )
        
        # Ensure bot has gems
        await BotGameLogic.setup_bot_gems(bot_id, db)
        
        # Generate bot's move and bet gems
        bot_move = BotGameLogic.calculate_bot_move(bot_obj)
        bet_gems = game_data.get("bet_gems", {"Ruby": 1, "Emerald": 1})
        
        # Create game as bot
        game = Game(
            creator_id=bot_id,
            creator_move=bot_move,
            creator_move_hash=hashlib.sha256(f"{bot_move.value}{secrets.token_hex(32)}".encode()).hexdigest(),
            creator_salt=secrets.token_hex(32),
            bet_amount=bet_amount,
            bet_gems=bet_gems,
            is_bot_game=True,
            bot_id=bot_id
        )
        
        await db.games.insert_one(game.dict())
        
        # Update bot cycle tracking
        await db.bots.update_one(
            {"id": bot_id},
            {
                "$set": {
                    "last_game_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Bot game created successfully", "game_id": game.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bot game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bot game"
        )

@api_router.get("/bots/active", response_model=List[dict])
async def get_active_bots(current_user: User = Depends(get_current_user)):
    """Get all active bots that can play games."""
    try:
        # Find active bots
        bots = await db.bots.find({"is_active": True}).to_list(100)
        
        result = []
        for bot in bots:
            bot_data = {
                "id": bot["id"],
                "name": bot["name"],
                "bot_type": bot["bot_type"],
                "avatar_gender": bot["avatar_gender"],
                "min_bet": bot["min_bet"],
                "max_bet": bot["max_bet"],
                "can_accept_bets": bot.get("can_accept_bets", False),
                "last_game_time": bot.get("last_game_time"),
                "current_cycle_games": bot.get("current_cycle_games", 0),
                "current_cycle_wins": bot.get("current_cycle_wins", 0)
            }
            result.append(bot_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching active bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active bots"
        )

@api_router.get("/bots/{bot_id}/stats", response_model=dict)
async def get_bot_stats(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Get detailed bot statistics (admin only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Get bot's game statistics
        total_games = await db.games.count_documents({
            "$or": [
                {"creator_id": bot_id},
                {"opponent_id": bot_id}
            ],
            "status": "COMPLETED"
        })
        
        won_games = await db.games.count_documents({
            "winner_id": bot_id,
            "status": "COMPLETED"
        })
        
        # Get recent games
        recent_games = await db.games.find({
            "$or": [
                {"creator_id": bot_id},
                {"opponent_id": bot_id}
            ],
            "status": "COMPLETED"
        }).sort("completed_at", -1).limit(10).to_list(10)
        
        return {
            "bot_id": bot_id,
            "name": bot["name"],
            "bot_type": bot["bot_type"],
            "is_active": bot["is_active"],
            "win_rate_setting": bot["win_rate"],
            "total_games": total_games,
            "won_games": won_games,
            "actual_win_rate": won_games / total_games if total_games > 0 else 0,
            "current_cycle_games": bot.get("current_cycle_games", 0),
            "current_cycle_wins": bot.get("current_cycle_wins", 0),
            "last_game_time": bot.get("last_game_time"),
            "recent_games": len(recent_games)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bot stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot stats"
        )

# ==============================================================================
# ADMIN STATISTICS AND MANAGEMENT API
# ==============================================================================

@api_router.get("/admin/users/stats", response_model=dict)
async def get_users_stats(current_user: User = Depends(get_current_admin)):
    """Get user statistics for admin dashboard."""
    try:
        # Get total users count
        total_users = await db.users.count_documents({})
        
        # Get active users count
        active_users = await db.users.count_documents({"status": "ACTIVE"})
        
        # Get banned users count
        banned_users = await db.users.count_documents({"status": "BANNED"})
        
        # Get new users today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_users_today = await db.users.count_documents({
            "created_at": {"$gte": today}
        })
        
        return {
            "total": total_users,
            "active": active_users,
            "banned": banned_users,
            "new_today": new_users_today
        }
        
    except Exception as e:
        logger.error(f"Error fetching users stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users stats"
        )

@api_router.get("/admin/games/stats", response_model=dict)
async def get_games_stats(current_user: User = Depends(get_current_admin)):
    """Get game statistics for admin dashboard."""
    try:
        # Get total games count
        total_games = await db.games.count_documents({})
        
        # Get active games count
        active_games = await db.games.count_documents({"status": "ACTIVE"})
        
        # Get waiting games count
        waiting_games = await db.games.count_documents({"status": "WAITING"})
        
        # Get completed games count
        completed_games = await db.games.count_documents({"status": "COMPLETED"})
        
        # Get games today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        games_today = await db.games.count_documents({
            "created_at": {"$gte": today}
        })
        
        return {
            "total": total_games,
            "active": active_games,
            "waiting": waiting_games,
            "completed": completed_games,
            "today": games_today
        }
        
    except Exception as e:
        logger.error(f"Error fetching games stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch games stats"
        )

@api_router.get("/admin/users", response_model=dict)
async def get_all_users(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_admin)
):
    """Get all users with pagination and filtering."""
    try:
        # Build query
        query = {}
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        if status:
            query["status"] = status
        
        # Get total count
        total = await db.users.count_documents(query)
        
        # Get users with pagination
        skip = (page - 1) * limit
        users = await db.users.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
        
        # Clean user data
        cleaned_users = []
        for user in users:
            cleaned_user = {
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role"),
                "status": user.get("status"),
                "gender": user.get("gender"),
                "virtual_balance": user.get("virtual_balance", 0),
                "total_games_played": user.get("total_games_played", 0),
                "total_games_won": user.get("total_games_won", 0),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login"),
                "ban_reason": user.get("ban_reason"),
                "ban_until": user.get("ban_until")
            }
            cleaned_users.append(cleaned_user)
        
        return {
            "users": cleaned_users,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

@api_router.put("/admin/users/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update user information (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check for unique email and username if they are being updated
        if "email" in user_data and user_data["email"] != user.get("email"):
            existing_email = await db.users.find_one({"email": user_data["email"]})
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        if "username" in user_data and user_data["username"] != user.get("username"):
            existing_username = await db.users.find_one({"username": user_data["username"]})
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
        
        # Update fields
        update_fields = {}
        if "username" in user_data:
            update_fields["username"] = user_data["username"]
        if "email" in user_data:
            update_fields["email"] = user_data["email"]
        if "role" in user_data:
            update_fields["role"] = user_data["role"]
        if "virtual_balance" in user_data:
            update_fields["virtual_balance"] = float(user_data["virtual_balance"])
        
        update_fields["updated_at"] = datetime.utcnow()
        
        # Update user
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_fields}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes were made"
            )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="UPDATE_USER",
            target_type="user",
            target_id=user_id,
            details={"updated_fields": list(update_fields.keys())}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "User updated successfully", "modified_count": result.modified_count}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@api_router.post("/admin/users/{user_id}/ban", response_model=dict)
async def ban_user(
    user_id: str,
    ban_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Ban a user (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Parse ban duration
        ban_until = None
        if ban_data.get("duration"):
            duration_map = {
                "1hour": timedelta(hours=1),
                "1day": timedelta(days=1),
                "1week": timedelta(weeks=1),
                "1month": timedelta(days=30)
            }
            
            if ban_data["duration"] in duration_map:
                ban_until = datetime.utcnow() + duration_map[ban_data["duration"]]
        
        # Update user
        update_fields = {
            "status": UserStatus.BANNED,
            "ban_reason": ban_data.get("reason", "No reason provided"),
            "ban_until": ban_until,
            "updated_at": datetime.utcnow()
        }
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_fields}
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="BAN_USER",
            target_type="user",
            target_id=user_id,
            details={
                "reason": ban_data.get("reason"),
                "duration": ban_data.get("duration"),
                "ban_until": ban_until.isoformat() if ban_until else None
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "User banned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )

@api_router.post("/admin/users/{user_id}/unban", response_model=dict)
async def unban_user(
    user_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Unban a user (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user
        update_fields = {
            "status": UserStatus.ACTIVE,
            "ban_reason": None,
            "ban_until": None,
            "updated_at": datetime.utcnow()
        }
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_fields}
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="UNBAN_USER",
            target_type="user",
            target_id=user_id,
            details={"username": user.get("username")}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "User unbanned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unban user"
        )

@api_router.post("/admin/users/{user_id}/balance", response_model=dict)
async def update_user_balance(
    user_id: str,
    balance_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update user balance (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        new_balance = balance_data.get("balance", 0)
        old_balance = user.get("virtual_balance", 0)
        
        # Update user balance
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "virtual_balance": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            transaction_type=TransactionType.GIFT,
            amount=new_balance - old_balance,
            currency="USD",
            balance_before=old_balance,
            balance_after=new_balance,
            description=f"Admin balance adjustment",
            admin_id=current_user.id
        )
        await db.transactions.insert_one(transaction.dict())
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="UPDATE_USER_BALANCE",
            target_type="user",
            target_id=user_id,
            details={
                "old_balance": old_balance,
                "new_balance": new_balance,
                "difference": new_balance - old_balance
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {"message": "User balance updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user balance"
        )

# ==============================================================================
# ADMIN PROFIT TRACKING API
# ==============================================================================

@api_router.get("/admin/profit/stats", response_model=dict)
async def get_profit_stats(current_admin: User = Depends(get_current_admin)):
    """Get profit statistics for admin dashboard."""
    try:
        current_time = datetime.utcnow()
        day_ago = current_time - timedelta(days=1)
        week_ago = current_time - timedelta(weeks=1)
        month_ago = current_time - timedelta(days=30)
        
        # Get total profits
        total_profit = await db.profit_entries.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        total_profit = total_profit[0]["total"] if total_profit else 0
        
        # Get profits by type
        profit_by_type = await db.profit_entries.aggregate([
            {"$group": {"_id": "$entry_type", "total": {"$sum": "$amount"}}}
        ]).to_list(10)
        
        # Get recent profits (last 24 hours)
        recent_profit = await db.profit_entries.aggregate([
            {"$match": {"created_at": {"$gte": day_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        recent_profit = recent_profit[0]["total"] if recent_profit else 0
        
        # Get weekly profit
        weekly_profit = await db.profit_entries.aggregate([
            {"$match": {"created_at": {"$gte": week_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        weekly_profit = weekly_profit[0]["total"] if weekly_profit else 0
        
        # Get monthly profit
        monthly_profit = await db.profit_entries.aggregate([
            {"$match": {"created_at": {"$gte": month_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        monthly_profit = monthly_profit[0]["total"] if monthly_profit else 0
        
        return {
            "total_profit": total_profit,
            "recent_profit": recent_profit,
            "weekly_profit": weekly_profit,
            "monthly_profit": monthly_profit,
            "profit_by_type": {item["_id"]: item["total"] for item in profit_by_type}
        }
        
    except Exception as e:
        logger.error(f"Error fetching profit stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profit stats"
        )

@api_router.get("/admin/profit/entries", response_model=dict)
async def get_profit_entries(
    page: int = 1,
    limit: int = 50,
    entry_type: Optional[str] = None,
    current_admin: User = Depends(get_current_admin)
):
    """Get profit entries with pagination."""
    try:
        query = {}
        if entry_type:
            query["entry_type"] = entry_type
        
        skip = (page - 1) * limit
        
        # Get profit entries
        entries = await db.profit_entries.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Get user info for each entry
        for entry in entries:
            user = await db.users.find_one({"id": entry["source_user_id"]})
            entry["source_user"] = {
                "username": user["username"] if user else "Unknown",
                "email": user["email"] if user else "Unknown"
            }
        
        # Get total count
        total_count = await db.profit_entries.count_documents(query)
        
        return {
            "entries": entries,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching profit entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profit entries"
        )

@api_router.get("/admin/profit/commission-settings", response_model=dict)
async def get_commission_settings(current_admin: User = Depends(get_current_admin)):
    """Get current commission settings."""
    try:
        # These could be stored in database in the future
        return {
            "bet_commission": 6.0,  # 6% commission on bets
            "gift_commission": 3.0,  # 3% commission on gifts
            "min_bet": 1.0,
            "max_bet": 3000.0,
            "daily_deposit_limit": 1000.0
        }
    except Exception as e:
        logger.error(f"Error fetching commission settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch commission settings"
        )

async def update_bot_cycle_tracking(bot_id: str, bot_won: bool):
    """Update bot's cycle tracking after a game."""
    try:
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            return
        
        # Update cycle tracking
        new_cycle_games = bot.get("current_cycle_games", 0) + 1
        new_cycle_wins = bot.get("current_cycle_wins", 0) + (1 if bot_won else 0)
        
        # Reset cycle if we've reached the limit
        if new_cycle_games >= bot.get("cycle_games", 12):
            new_cycle_games = 0
            new_cycle_wins = 0
        
        await db.bots.update_one(
            {"id": bot_id},
            {
                "$set": {
                    "current_cycle_games": new_cycle_games,
                    "current_cycle_wins": new_cycle_wins,
                    "last_game_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Bot {bot_id} cycle updated: {new_cycle_games} games, {new_cycle_wins} wins")
        
    except Exception as e:
        logger.error(f"Error updating bot cycle tracking: {e}")

async def bot_automation_task():
    """Background task for bot automation - creates and joins games."""
    while True:
        try:
            # Get active bots
            active_bots = await db.bots.find({"is_active": True}).to_list(100)
            
            for bot in active_bots:
                bot_obj = Bot(**bot)
                
                # Check if bot should take action
                if await should_bot_take_action(bot_obj):
                    # Randomly decide between creating a game or joining one
                    if random.choice([True, False]):
                        await bot_create_game_automatically(bot_obj)
                    else:
                        await bot_join_game_automatically(bot_obj)
            
            # Wait before next cycle
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in bot automation task: {e}")
            await asyncio.sleep(60)  # Wait longer if error occurred

async def should_bot_take_action(bot: Bot) -> bool:
    """Determine if bot should take action based on timing and settings."""
    if not bot.is_active:
        return False
    
    # Check if enough time has passed since last game
    if bot.last_game_time:
        time_since_last = datetime.utcnow() - bot.last_game_time
        if time_since_last.total_seconds() < bot.pause_between_games:
            return False
    
    # Add randomness to bot behavior
    return random.random() < 0.3  # 30% chance to act when conditions are met

async def bot_create_game_automatically(bot: Bot):
    """Make bot create a game automatically."""
    try:
        # Ensure bot has gems
        await BotGameLogic.setup_bot_gems(bot.id, db)
        
        # Generate random bet amount within bot's limits
        bet_amount = random.uniform(bot.min_bet, min(bot.max_bet, 100))
        bet_amount = round(bet_amount, 2)
        
        # Select random gems to bet
        gem_types = list(GemType)
        selected_gems = random.sample(gem_types, random.randint(1, min(3, len(gem_types))))
        bet_gems = {gem_type.value: random.randint(1, 5) for gem_type in selected_gems}
        
        # Generate bot's move
        bot_move = BotGameLogic.calculate_bot_move(bot)
        salt = secrets.token_hex(32)
        
        # Create game
        game = Game(
            creator_id=bot.id,
            creator_move=bot_move,
            creator_move_hash=hashlib.sha256(f"{bot_move.value}{salt}".encode()).hexdigest(),
            creator_salt=salt,
            bet_amount=bet_amount,
            bet_gems=bet_gems,
            is_bot_game=True,
            bot_id=bot.id
        )
        
        await db.games.insert_one(game.dict())
        
        # Update bot's last game time
        await db.bots.update_one(
            {"id": bot.id},
            {"$set": {"last_game_time": datetime.utcnow()}}
        )
        
        logger.info(f"Bot {bot.name} created game {game.id} with bet ${bet_amount}")
        
    except Exception as e:
        logger.error(f"Error in bot auto-create game: {e}")

async def bot_join_game_automatically(bot: Bot):
    """Make bot join an available game automatically."""
    try:
        if not bot.can_accept_bets:
            return
        
        # Find available games that bot can join
        available_games = await db.games.find({
            "status": GameStatus.WAITING,
            "creator_id": {"$ne": bot.id},  # Don't join own games
            "bet_amount": {"$gte": bot.min_bet, "$lte": bot.max_bet}
        }).to_list(10)
        
        if not available_games:
            return
        
        # Select random game
        game_to_join = random.choice(available_games)
        game_obj = Game(**game_to_join)
        
        # Check if bot can play with other bots
        if game_obj.is_bot_game and not bot.can_play_with_bots:
            return
        
        # Ensure bot has required gems
        await BotGameLogic.setup_bot_gems(bot.id, db)
        
        # Check if bot has enough gems
        for gem_type, quantity in game_obj.bet_gems.items():
            bot_gems = await db.user_gems.find_one({"user_id": bot.id, "gem_type": gem_type})
            if not bot_gems or bot_gems["quantity"] < quantity:
                return  # Bot doesn't have enough gems
        
        # Freeze bot's gems
        for gem_type, quantity in game_obj.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": bot.id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Calculate bot's move using strategy
        creator_move = game_obj.creator_move
        if creator_move:
            # Bot knows creator's move (for testing/balancing)
            bot_move = BotGameLogic.get_bot_move_against_player(bot, creator_move)
        else:
            # Standard move calculation
            bot_move = BotGameLogic.calculate_bot_move(bot)
        
        # Update game with bot as opponent
        await db.games.update_one(
            {"id": game_obj.id},
            {
                "$set": {
                    "opponent_id": bot.id,
                    "opponent_move": bot_move,
                    "status": GameStatus.ACTIVE,
                    "started_at": datetime.utcnow()
                }
            }
        )
        
        # Update bot's last game time
        await db.bots.update_one(
            {"id": bot.id},
            {"$set": {"last_game_time": datetime.utcnow()}}
        )
        
        # Determine winner
        await determine_game_winner(game_obj.id)
        
        logger.info(f"Bot {bot.name} joined game {game_obj.id}")
        
    except Exception as e:
        logger.error(f"Error in bot auto-join game: {e}")

# ==============================================================================
# ADMIN GAME MANAGEMENT
# ==============================================================================

@api_router.post("/admin/games/reset-all", response_model=dict)
async def reset_all_bets(current_user: User = Depends(get_current_admin)):
    """Reset all bets for all players and bots (admin only)."""
    try:
        # Get all active games (WAITING, ACTIVE)
        active_games = await db.games.find({
            "status": {"$in": [GameStatus.WAITING, GameStatus.ACTIVE]}
        }).to_list(1000)
        
        reset_count = 0
        total_gems_returned = {}
        total_commission_returned = 0.0
        
        # Process each active game
        for game in active_games:
            game_obj = Game(**game)
            
            # Unfreeze creator's gems
            for gem_type, quantity in game_obj.bet_gems.items():
                await db.user_gems.update_one(
                    {"user_id": game_obj.creator_id, "gem_type": gem_type},
                    {
                        "$inc": {"frozen_quantity": -quantity},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                
                # Track returned gems
                if gem_type not in total_gems_returned:
                    total_gems_returned[gem_type] = 0
                total_gems_returned[gem_type] += quantity
            
            # Return frozen commission to creator
            creator = await db.users.find_one({"id": game_obj.creator_id})
            if creator:
                commission_to_return = game_obj.bet_amount * 0.06
                await db.users.update_one(
                    {"id": game_obj.creator_id},
                    {
                        "$inc": {
                            "virtual_balance": commission_to_return,
                            "frozen_balance": -commission_to_return
                        },
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                total_commission_returned += commission_to_return
            
            # If game is ACTIVE, also handle opponent's gems
            if game_obj.status == GameStatus.ACTIVE and game_obj.opponent_id:
                # Unfreeze opponent's gems
                for gem_type, quantity in game_obj.bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": game_obj.opponent_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    total_gems_returned[gem_type] += quantity
                
                # Return frozen commission to opponent
                opponent = await db.users.find_one({"id": game_obj.opponent_id})
                if opponent:
                    commission_to_return = game_obj.bet_amount * 0.06
                    await db.users.update_one(
                        {"id": game_obj.opponent_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_to_return,
                                "frozen_balance": -commission_to_return
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    total_commission_returned += commission_to_return
            
            reset_count += 1
        
        # Update all active games to CANCELLED
        await db.games.update_many(
            {"status": {"$in": [GameStatus.WAITING, GameStatus.ACTIVE]}},
            {
                "$set": {
                    "status": GameStatus.CANCELLED,
                    "cancelled_at": datetime.utcnow()
                }
            }
        )
        
        # Release any remaining frozen balances
        users_with_frozen = await db.users.find({"frozen_balance": {"$gt": 0}}).to_list(1000)
        for user in users_with_frozen:
            new_balance = user["virtual_balance"] + user["frozen_balance"]
            await db.users.update_one(
                {"id": user["id"]},
                {
                    "$set": {
                        "virtual_balance": new_balance,
                        "frozen_balance": 0.0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        # Also reset any negative frozen balances to 0 (floating point precision issues)
        await db.users.update_many(
            {"frozen_balance": {"$ne": 0.0}},
            {
                "$set": {"frozen_balance": 0.0, "updated_at": datetime.utcnow()}
            }
        )
        
        # Reset all frozen gem quantities
        await db.user_gems.update_many(
            {"frozen_quantity": {"$gt": 0}},
            {
                "$set": {"frozen_quantity": 0, "updated_at": datetime.utcnow()}
            }
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="RESET_ALL_BETS",
            target_type="games",
            target_id="all",
            details={
                "games_reset": reset_count,
                "gems_returned": total_gems_returned,
                "commission_returned": total_commission_returned
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "message": "All bets have been reset successfully",
            "games_reset": reset_count,
            "gems_returned": total_gems_returned,
            "commission_returned": round(total_commission_returned, 2)
        }
        
    except Exception as e:
        logger.error(f"Error resetting all bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset all bets"
        )

# Start bot automation background task
async def start_bot_automation():
    """Start the bot automation background task."""
    asyncio.create_task(bot_automation_task())

# Include routers
app.include_router(auth_router)
app.include_router(api_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize bot automation on startup."""
    logger.info("Starting bot automation system...")
    await start_bot_automation()
    logger.info("Bot automation system started successfully")

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