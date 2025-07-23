from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
import random
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
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days for refresh tokens

# Security monitoring
SUSPICIOUS_ACTIVITY_THRESHOLDS = {
    "max_requests_per_minute": 60,
    "max_purchases_per_hour": 20,
    "max_gift_amount_per_day": 1000,
    "max_balance_change_per_hour": 5000,
    "unusual_login_locations": True
}
# Gem prices
GEM_PRICES = {
    "Ruby": 1.0,
    "Amber": 2.0,
    "Topaz": 5.0,
    "Emerald": 10.0,
    "Aquamarine": 25.0,
    "Sapphire": 50.0,
    "Magic": 100.0
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

class BotType(str, Enum):
    REGULAR = "REGULAR"
    HUMAN = "HUMAN"

class HumanBotCharacter(str, Enum):
    STABLE = "STABLE"           # Стабильный
    AGGRESSIVE = "AGGRESSIVE"   # Агрессивный
    CAUTIOUS = "CAUTIOUS"      # Осторожный
    BALANCED = "BALANCED"       # Балансированный
    IMPULSIVE = "IMPULSIVE"     # Импульсивный
    ANALYST = "ANALYST"         # Аналитик
    MIMIC = "MIMIC"            # Мимик

class BotMode(str, Enum):
    SIMPLE = "SIMPLE"      # Простой рандом
    ALGORITHMIC = "ALGORITHMIC"  # С алгоритмом побед

# Bot Settings model
class BotSettings(BaseModel):
    id: str = Field(default="bot_settings")
    max_active_bets_regular: int = 50  # Максимальное количество активных ставок для обычных ботов
    max_active_bets_human: int = 100    # Максимальное количество активных ставок для Human ботов (обновлено с 30 до 100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Bot Settings Request model
class BotSettingsRequest(BaseModel):
    globalMaxActiveBets: int = Field(ge=1, le=200)
    globalMaxHumanBots: int = Field(ge=1, le=1000)  # Увеличен лимит до 1000
    paginationSize: int = Field(ge=5, le=50)
    autoActivateFromQueue: bool = True
    priorityType: str = Field(default="order")  # 'order' or 'manual'

# Human Bot Settings Request model - новая модель для настроек Human-ботов
class HumanBotSettingsRequest(BaseModel):
    max_active_bets_human: int = Field(ge=1, le=1000, description="Максимальное количество активных ставок для всех Human ботов")

# Interface Settings model
class InterfaceSettings(BaseModel):
    live_players: dict = Field(default={
        "my_bets": 10,
        "available_bets": 10,
        "ongoing_battles": 10
    })
    bot_players: dict = Field(default={
        "available_bots": 10,
        "ongoing_bot_battles": 10
    })
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Bot Queue Stats model
class BotQueueStats(BaseModel):
    totalActiveRegularBets: int = 0
    totalQueuedBets: int = 0
    totalRegularBots: int = 0
    totalHumanBots: int = 0

# Bot model
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
    REVEAL = "REVEAL"  # Фаза ожидания reveal хода
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"  # Игра завершена по таймауту

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

class SoundCategory(str, Enum):
    GAMING = "GAMING"           # Игровые действия
    UI = "UI"                   # UI элементы  
    SYSTEM = "SYSTEM"           # Системные уведомления
    BACKGROUND = "BACKGROUND"   # Фоновые звуки/музыка

class GameType(str, Enum):
    HUMAN_VS_HUMAN = "HUMAN_VS_HUMAN"
    HUMAN_VS_BOT = "HUMAN_VS_BOT" 
    ALL = "ALL"

class SoundPriority(str, Enum):
    LOW = "LOW"           # 1-2
    MEDIUM = "MEDIUM"     # 3-5
    HIGH = "HIGH"         # 6-8
    CRITICAL = "CRITICAL" # 9-10

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
    creator_type: str = "user"  # "user", "bot", "human_bot"
    opponent_id: Optional[str] = None
    creator_move: Optional[GameMove] = None
    opponent_move: Optional[GameMove] = None
    creator_move_hash: Optional[str] = None  # Для commit-reveal схемы
    creator_salt: Optional[str] = None
    bet_amount: float
    bet_gems: Dict[str, int]  # {"Ruby": 5, "Emerald": 2} - Creator's gems
    opponent_gems: Optional[Dict[str, int]] = None  # {"Ruby": 3, "Sapphire": 1} - Opponent's gems
    status: GameStatus = GameStatus.WAITING
    winner_id: Optional[str] = None
    commission_amount: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    reveal_deadline: Optional[datetime] = None  # Крайний срок для reveal
    is_bot_game: bool = False
    bot_id: Optional[str] = None
    bot_type: Optional[str] = None  # "REGULAR", "HUMAN"
    is_regular_bot_game: bool = False  # Флаг для игр против обычных ботов (без комиссии)

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

class BotProfitAccumulator(BaseModel):
    """Модель для накопления прибыли от ботов"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bot_id: str
    cycle_number: int
    total_spent: float  # Общая сумма, потраченная ботом на цикл
    total_earned: float  # Общая сумма, заработанная ботом в цикле
    games_completed: int  # Количество завершенных игр в цикле
    games_won: int  # Количество выигранных игр
    cycle_start_date: datetime
    cycle_end_date: Optional[datetime] = None
    is_cycle_completed: bool = False
    profit_transferred: float = 0  # Сумма прибыли, переданная в "Доход от ботов"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
    
    # Настройки ставок (обновлены согласно спецификации)
    min_bet_amount: float = 1.0  # 1-10000
    max_bet_amount: float = 100.0  # 1-10000
    win_rate: float = 0.55  # 0-100% (по умолчанию 55%)
    
    # Циклы и лимиты (обновлены согласно спецификации)
    cycle_games: int = 12  # 1-66 (по умолчанию 12)
    current_cycle_games: int = 0
    current_cycle_wins: int = 0
    current_cycle_gem_value_won: float = 0.0  # Новое поле для стоимости выигранных гемов
    current_cycle_gem_value_total: float = 0.0  # Новое поле для общей стоимости ставок
    current_limit: Optional[int] = None  # 1-66 (по умолчанию = cycle_games)
    individual_limit: int = 12  # 1-66 (индивидуальный лимит активных ставок)
    
    # Поведенческие настройки (новые поля)
    creation_mode: str = "queue-based"  # "always-first", "queue-based", "after-all"
    priority_order: int = 50  # 1-100
    pause_between_games: int = 5  # 1-300 секунд (по умолчанию 5)
    
    # Стратегии прибыли (новое поле)
    profit_strategy: str = "balanced"  # "start-positive", "balanced", "start-negative"
    
    # Временные метки
    last_game_time: Optional[datetime] = None
    last_bet_time: Optional[datetime] = None  # Новое поле
    
    # Старые поля (совместимость)
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

class HumanBot(BaseModel):
    """Модель для Human-ботов с характерами и настройками поведения"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Уникальное имя бота
    character: HumanBotCharacter  # Тип характера (1 из 7)
    is_active: bool = True
    
    # Диапазон ставок
    min_bet: float = Field(ge=1.0, le=10000.0)  # 1-10000
    max_bet: float = Field(ge=1.0, le=10000.0)  # 1-10000
    
    # Лимит ставок (максимальное количество одновременных ставок)
    bet_limit: int = Field(default=12, ge=1, le=100)  # 1-100
    
    # Распределение исходов (в процентах, сумма должна быть 100%)
    win_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    loss_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    draw_percentage: float = Field(default=20.0, ge=0.0, le=100.0)
    
    # Интервал между действиями (в секундах)
    min_delay: int = Field(default=30, ge=1, le=300)   # 1-300 секунд
    max_delay: int = Field(default=120, ge=1, le=300)  # 1-300 секунд
    
    # Настройки commit-reveal
    use_commit_reveal: bool = True
    
    # Уровень логирования
    logging_level: str = Field(default="INFO")  # INFO, DEBUG
    
    # Статистика
    total_games_played: int = 0
    total_games_won: int = 0  
    total_amount_wagered: float = 0.0
    total_amount_won: float = 0.0
    
    # Временные метки
    last_action_time: Optional[datetime] = None
    last_bet_time: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class HumanBotLog(BaseModel):
    """Модель для логирования действий Human-ботов"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    human_bot_id: str
    action_type: str  # "CREATE_BET", "JOIN_BET", "WIN", "LOSS", "DRAW"
    description: str
    game_id: Optional[str] = None
    bet_amount: Optional[float] = None
    outcome: Optional[str] = None  # "WIN", "LOSS", "DRAW"
    move_played: Optional[str] = None  # "rock", "paper", "scissors"
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

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # ADMIN_ACTION, GIFT_RECEIVED, etc.
    title: str
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Sound(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Название звука
    category: SoundCategory  # Категория звука
    event_trigger: str  # Событие-триггер (создание_ставки, победа, hover и т.д.)
    game_type: GameType = GameType.ALL  # Тип игры
    is_enabled: bool = True  # Включен/выключен
    priority: int = Field(default=5, ge=1, le=10)  # Приоритет 1-10
    volume: float = Field(default=0.5, ge=0.0, le=1.0)  # Громкость 0.0-1.0
    delay: int = Field(default=0, ge=0)  # Задержка в миллисекундах
    can_repeat: bool = True  # Можно ли воспроизводить повторно
    audio_data: Optional[str] = None  # Base64 данные аудиофайла
    file_format: Optional[str] = None  # mp3/wav/ogg
    file_size: Optional[int] = None  # Размер файла в байтах
    is_default: bool = False  # Дефолтный звук (программный)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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

class CancelGameResponse(BaseModel):
    success: bool
    message: str
    gems_returned: Dict[str, int]
    commission_returned: float

# Removed gem combination models - logic moved to frontend

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
    gems: Dict[str, int]  # Player's selected gems combination

# Human Bot Request Models
class CreateHumanBotRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    character: HumanBotCharacter
    min_bet: float = Field(..., ge=1.0, le=10000.0)
    max_bet: float = Field(..., ge=1.0, le=10000.0)
    bet_limit: int = Field(default=12, ge=1, le=100)
    win_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    loss_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    draw_percentage: float = Field(default=20.0, ge=0.0, le=100.0)
    min_delay: int = Field(default=30, ge=1, le=300)
    max_delay: int = Field(default=120, ge=1, le=300)
    use_commit_reveal: bool = True
    logging_level: str = Field(default="INFO")

class UpdateHumanBotRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    character: Optional[HumanBotCharacter] = None
    is_active: Optional[bool] = None
    min_bet: Optional[float] = Field(None, ge=1.0, le=10000.0)
    max_bet: Optional[float] = Field(None, ge=1.0, le=10000.0)
    bet_limit: Optional[int] = Field(None, ge=1, le=100)
    win_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    loss_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    draw_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    min_delay: Optional[int] = Field(None, ge=1, le=300)
    max_delay: Optional[int] = Field(None, ge=1, le=300)
    use_commit_reveal: Optional[bool] = None
    logging_level: Optional[str] = None

class ToggleAllRequest(BaseModel):
    activate: bool

class BulkCreateHumanBotsRequest(BaseModel):
    count: int = Field(..., ge=1, le=50)  # Максимум 50 ботов за раз
    character: HumanBotCharacter
    min_bet_range: List[float] = Field(..., min_length=2, max_length=2)  # [min, max]
    max_bet_range: List[float] = Field(..., min_length=2, max_length=2)  # [min, max]  
    bet_limit_range: List[int] = Field(default=[12, 12], min_length=2, max_length=2)  # [min, max] лимит ставок
    win_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    loss_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    draw_percentage: float = Field(default=20.0, ge=0.0, le=100.0)
    delay_range: List[int] = Field(default=[30, 120], min_length=2, max_length=2)  # [min, max] секунды
    use_commit_reveal: bool = True
    logging_level: str = Field(default="INFO")

class CreateSoundRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: SoundCategory
    event_trigger: str = Field(..., min_length=1, max_length=50)
    game_type: GameType = GameType.ALL
    is_enabled: bool = True
    priority: int = Field(default=5, ge=1, le=10)
    volume: float = Field(default=0.5, ge=0.0, le=1.0)
    delay: int = Field(default=0, ge=0, le=5000)  # Max 5 seconds delay
    can_repeat: bool = True

class UpdateSoundRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[SoundCategory] = None
    event_trigger: Optional[str] = Field(None, min_length=1, max_length=50)
    game_type: Optional[GameType] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    delay: Optional[int] = Field(None, ge=0, le=5000)
    can_repeat: Optional[bool] = None

class UploadSoundFileRequest(BaseModel):
    file_data: str  # Base64 encoded audio file
    file_format: str = Field(..., pattern="^(mp3|wav|ogg)$")  # Only these formats
    file_size: int = Field(..., gt=0, le=5242880)  # Max 5MB

class SoundResponse(BaseModel):
    id: str
    name: str
    category: SoundCategory
    event_trigger: str
    game_type: GameType
    is_enabled: bool
    priority: int
    volume: float
    delay: int
    can_repeat: bool
    has_audio_file: bool  # Whether audio_data exists
    file_format: Optional[str] = None
    file_size: Optional[int] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime

class HumanBotResponse(BaseModel):
    id: str
    name: str
    character: HumanBotCharacter
    is_active: bool
    min_bet: float
    max_bet: float
    bet_limit: int
    win_percentage: float
    loss_percentage: float
    draw_percentage: float
    min_delay: int
    max_delay: int
    use_commit_reveal: bool
    logging_level: str
    total_games_played: int
    total_games_won: int
    total_amount_wagered: float
    total_amount_won: float
    win_rate: float  # Calculated field
    last_action_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class HumanBotLogResponse(BaseModel):
    id: str
    human_bot_id: str
    action_type: str
    description: str
    game_id: Optional[str]
    bet_amount: Optional[float]
    outcome: Optional[str]
    move_played: Optional[str]
    created_at: datetime

class HumanBotsStatsResponse(BaseModel):
    total_bots: int
    active_bots: int
    total_games_24h: int
    total_bets: int
    total_revenue_24h: float
    avg_revenue_per_bot: float
    most_active_bots: List[Dict[str, Any]]
    character_distribution: Dict[str, int]

class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    per_page: int
    total_items: int
    has_next: bool
    has_prev: bool

class HumanBotsListResponse(BaseModel):
    success: bool
    bots: List[Dict[str, Any]]
    pagination: PaginationInfo

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

async def generate_unique_human_bot_name() -> str:
    """Generate unique human bot name in format Player1, Player2, etc."""
    counter = 1
    while True:
        bot_name = f"Player{counter}"
        existing_bot = await db.human_bots.find_one({"name": bot_name})
        if not existing_bot:
            return bot_name
        counter += 1

# ==============================================================================
# HUMAN BOT BEHAVIOR ALGORITHMS
# ==============================================================================

class HumanBotBehavior:
    """Алгоритмы поведения для Human-ботов с разными характерами"""
    
    @staticmethod
    def get_bet_amount(character: HumanBotCharacter, min_bet: float, max_bet: float) -> float:
        """Определить размер ставки на основе характера"""
        bet_range = max_bet - min_bet
        
        if character == HumanBotCharacter.STABLE:
            # Стабильные ставки в нижней трети диапазона
            return min_bet + (bet_range * random.uniform(0.1, 0.4))
            
        elif character == HumanBotCharacter.AGGRESSIVE:
            # Крупные ставки в верхней половине диапазона
            return min_bet + (bet_range * random.uniform(0.6, 1.0))
            
        elif character == HumanBotCharacter.CAUTIOUS:
            # Минимальные ставки
            return min_bet + (bet_range * random.uniform(0.0, 0.2))
            
        elif character == HumanBotCharacter.BALANCED:
            # Равномерно по всему диапазону
            return min_bet + (bet_range * random.uniform(0.2, 0.8))
            
        elif character == HumanBotCharacter.IMPULSIVE:
            # Случайные всплески - или очень мало, или очень много
            if random.random() < 0.3:
                return min_bet + (bet_range * random.uniform(0.8, 1.0))  # Всплеск
            else:
                return min_bet + (bet_range * random.uniform(0.0, 0.3))  # Обычно мало
                
        elif character == HumanBotCharacter.ANALYST:
            # Адаптивные ставки (пока используем средние значения)
            return min_bet + (bet_range * random.uniform(0.3, 0.7))
            
        elif character == HumanBotCharacter.MIMIC:
            # Копирует средние ставки (пока используем центральные значения)
            return min_bet + (bet_range * random.uniform(0.4, 0.6))
        
        # Fallback
        return min_bet + (bet_range * 0.5)

    @staticmethod
    def get_action_decision(character: HumanBotCharacter) -> str:
        """Решить, создать ставку или присоединиться к существующей"""
        if character == HumanBotCharacter.AGGRESSIVE:
            return "create" if random.random() < 0.7 else "join"  # Любят создавать ставки
        elif character == HumanBotCharacter.CAUTIOUS:
            return "join" if random.random() < 0.7 else "create"  # Предпочитают присоединяться
        else:
            return "create" if random.random() < 0.5 else "join"  # 50/50

    @staticmethod
    def get_move_choice(character: HumanBotCharacter) -> GameMove:
        """Выбор хода в зависимости от характера (расширенная стратегия)"""
        moves = [GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
        
        if character == HumanBotCharacter.AGGRESSIVE:
            # Агрессивные: предпочитают рискованные ходы (ножницы), атакующая стратегия
            return random.choices(moves, weights=[0.2, 0.3, 0.5])[0]
            
        elif character == HumanBotCharacter.CAUTIOUS:
            # Осторожные: предпочитают "безопасный" камень, консервативная стратегия  
            return random.choices(moves, weights=[0.6, 0.25, 0.15])[0]
            
        elif character == HumanBotCharacter.BALANCED:
            # Сбалансированные: равномерное распределение
            return random.choice(moves)
            
        elif character == HumanBotCharacter.IMPULSIVE:
            # Импульсивные: полностью случайные, но с всплесками одного хода
            if random.random() < 0.3:  # 30% шанс "зацикливания" на одном ходу
                favorite_move = random.choice(moves)
                return favorite_move
            else:
                return random.choice(moves)
                
        elif character == HumanBotCharacter.ANALYST:
            # Аналитики: стратегия на основе "мета-анализа" - адаптивная стратегия
            # Симулируем анализ предыдущих игр (пока используем взвешенную логику)
            return random.choices(moves, weights=[0.35, 0.4, 0.25])[0]  # Чуть больше бумаги
            
        elif character == HumanBotCharacter.STABLE:
            # Стабильные: предсказуемые паттерны, предпочитают камень
            return random.choices(moves, weights=[0.5, 0.3, 0.2])[0]
            
        elif character == HumanBotCharacter.MIMIC:
            # Мимики: пытаются копировать успешные стратегии (пока сбалансированно)
            # В будущем можно добавить анализ успешных ходов других игроков
            return random.choice(moves)
            
        else:
            # Default: сбалансированный подход
            return random.choice(moves)

    @staticmethod
    def should_win_game(character: HumanBotCharacter, win_percentage: float, loss_percentage: float, 
                       draw_percentage: float, game_value: float = 0) -> str:
        """Определить исход игры на основе характера и настроек"""
        
        # Базовые вероятности
        rand = random.uniform(0, 100)
        
        # Модификации на основе характера
        win_mod = 0
        loss_mod = 0
        
        if character == HumanBotCharacter.AGGRESSIVE and game_value > 100:
            win_mod = 10  # Агрессивные боты чаще выигрывают дорогие игры
        elif character == HumanBotCharacter.CAUTIOUS and game_value > 100:
            win_mod = -10  # Осторожные боты реже выигрывают дорогие игры
        elif character == HumanBotCharacter.ANALYST:
            # Аналитик адаптируется (пока простая логика)
            if game_value > 50:
                win_mod = 5
        
        adjusted_win = win_percentage + win_mod
        adjusted_loss = loss_percentage + loss_mod
        adjusted_draw = 100 - adjusted_win - adjusted_loss
        
        if rand <= adjusted_win:
            return "WIN"
        elif rand <= adjusted_win + adjusted_loss:
            return "LOSS"
        else:
            return "DRAW"

    @staticmethod
    def get_delay_time(character: HumanBotCharacter, min_delay: int, max_delay: int) -> int:
        """Получить время задержки между действиями"""
        
        if character == HumanBotCharacter.IMPULSIVE:
            # Импульсивные боты иногда действуют очень быстро
            if random.random() < 0.3:
                return min(min_delay, 10)  # Очень быстро
            else:
                return random.randint(min_delay, max_delay)
                
        elif character == HumanBotCharacter.CAUTIOUS:
            # Осторожные боты действуют медленнее
            delay_range = max_delay - min_delay
            return min_delay + int(delay_range * random.uniform(0.6, 1.0))
            
        else:
            # Обычная задержка
            return random.randint(min_delay, max_delay)

async def generate_unique_bot_name() -> str:
    """Generate unique bot name in format Bot#1, Bot#2, etc."""
    counter = 1
    while True:
        bot_name = f"Bot#{counter}"
        existing_bot = await db.bots.find_one({"name": bot_name})
        if not existing_bot:
            return bot_name
        counter += 1

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
# GEM COMBINATION CALCULATION FUNCTIONS - REMOVED
# Frontend now handles all gem combination logic
# ==============================================================================

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
    
    # Create default sounds if they don't exist
    default_sounds = [
        # Gaming sounds
        {"name": "Создание ставки", "category": SoundCategory.GAMING, "event_trigger": "создание_ставки", "game_type": GameType.ALL, "priority": 7, "is_default": True},
        {"name": "Принятие ставки", "category": SoundCategory.GAMING, "event_trigger": "принятие_ставки", "game_type": GameType.ALL, "priority": 6, "is_default": True},
        {"name": "Выбор хода", "category": SoundCategory.GAMING, "event_trigger": "выбор_хода", "game_type": GameType.ALL, "priority": 5, "is_default": True},
        {"name": "Раскрытие хода", "category": SoundCategory.GAMING, "event_trigger": "reveal", "game_type": GameType.ALL, "priority": 8, "is_default": True},
        {"name": "Победа (Human vs Human)", "category": SoundCategory.GAMING, "event_trigger": "победа", "game_type": GameType.HUMAN_VS_HUMAN, "priority": 9, "volume": 0.8, "is_default": True},
        {"name": "Победа (Human vs Bot)", "category": SoundCategory.GAMING, "event_trigger": "победа", "game_type": GameType.HUMAN_VS_BOT, "priority": 8, "volume": 0.7, "is_default": True},
        {"name": "Поражение (Human vs Human)", "category": SoundCategory.GAMING, "event_trigger": "поражение", "game_type": GameType.HUMAN_VS_HUMAN, "priority": 6, "volume": 0.4, "is_default": True},
        {"name": "Поражение (Human vs Bot)", "category": SoundCategory.GAMING, "event_trigger": "поражение", "game_type": GameType.HUMAN_VS_BOT, "priority": 5, "volume": 0.3, "is_default": True},
        {"name": "Ничья", "category": SoundCategory.GAMING, "event_trigger": "ничья", "game_type": GameType.ALL, "priority": 4, "volume": 0.5, "is_default": True},
        
        # Gems sounds  
        {"name": "Покупка гема", "category": SoundCategory.GAMING, "event_trigger": "покупка_гема", "game_type": GameType.ALL, "priority": 6, "is_default": True},
        {"name": "Продажа гема", "category": SoundCategory.GAMING, "event_trigger": "продажа_гема", "game_type": GameType.ALL, "priority": 5, "is_default": True},
        {"name": "Подарок гемов", "category": SoundCategory.GAMING, "event_trigger": "подарок_гемов", "game_type": GameType.ALL, "priority": 7, "volume": 0.7, "is_default": True},
        
        # UI sounds
        {"name": "Hover эффект", "category": SoundCategory.UI, "event_trigger": "hover", "game_type": GameType.ALL, "priority": 2, "volume": 0.3, "can_repeat": False, "is_default": True},
        {"name": "Открытие модального окна", "category": SoundCategory.UI, "event_trigger": "открытие_модала", "game_type": GameType.ALL, "priority": 3, "volume": 0.4, "is_default": True},
        {"name": "Закрытие модального окна", "category": SoundCategory.UI, "event_trigger": "закрытие_модала", "game_type": GameType.ALL, "priority": 3, "volume": 0.4, "is_default": True},
        
        # System sounds
        {"name": "Системное уведомление", "category": SoundCategory.SYSTEM, "event_trigger": "уведомление", "game_type": GameType.ALL, "priority": 6, "volume": 0.6, "is_default": True},
        {"name": "Ошибка", "category": SoundCategory.SYSTEM, "event_trigger": "ошибка", "game_type": GameType.ALL, "priority": 8, "volume": 0.5, "is_default": True},
        {"name": "Таймер истекает", "category": SoundCategory.SYSTEM, "event_trigger": "таймер_reveal", "game_type": GameType.ALL, "priority": 9, "volume": 0.7, "is_default": True},
        {"name": "Получение награды", "category": SoundCategory.SYSTEM, "event_trigger": "награда", "game_type": GameType.ALL, "priority": 8, "volume": 0.8, "is_default": True}
    ]
    
    # Insert default sounds
    for sound_data in default_sounds:
        existing = await db.sounds.find_one({
            "event_trigger": sound_data["event_trigger"], 
            "game_type": sound_data["game_type"],
            "is_default": True
        })
        if not existing:
            sound = Sound(**sound_data)
            await db.sounds.insert_one(sound.dict())
            logger.info(f"Created default sound: {sound_data['name']}")
    
    # Start background tasks
    start_background_scheduler()
    
    logger.info("GemPlay API started successfully with background tasks!")

def start_background_scheduler():
    """Start background scheduler for daily bonuses and bot automation."""
    def run_scheduler():
        schedule.every().day.at("00:00").do(reset_daily_limits)
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    # Start daily scheduler
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start bot automation using asyncio create_task
    asyncio.create_task(bot_automation_loop())
    
    # Start human bot simulation background task
    asyncio.create_task(human_bot_simulation_task())

async def bot_automation_loop():
    """Run bot automation loop every 5 seconds."""
    while True:
        try:
            await maintain_all_bots_active_bets()
            await asyncio.sleep(5)  # Каждые 5 секунд
        except Exception as e:
            logger.error(f"Error in bot automation loop: {e}")
            await asyncio.sleep(5)  # Пауза даже при ошибке

async def maintain_all_bots_active_bets():
    """Поддерживает количество активных ставок для всех активных ботов."""
    try:
        # Получаем всех активных обычных ботов
        active_bots = await db.bots.find({
            "is_active": True,
            "bot_type": "REGULAR"
        }).to_list(1000)
        
        if not active_bots:
            return
            
        logger.info(f"🤖 Checking {len(active_bots)} active bots for bet maintenance")
        
        # Проверяем каждого бота
        for bot_doc in active_bots:
            try:
                bot_id = bot_doc["id"]
                cycle_games = bot_doc.get("cycle_games", 12)
                
                # Подсчитываем текущие активные ставки
                current_active_bets = await db.games.count_documents({
                    "creator_id": bot_id,
                    "status": "WAITING"
                })
                
                # Если активных ставок меньше цикла, создаем новые
                if current_active_bets < cycle_games:
                    needed_bets = cycle_games - current_active_bets
                    logger.info(f"🎯 Bot {bot_doc['name']} needs {needed_bets} more bets ({current_active_bets}/{cycle_games})")
                    
                    # Создаем объект Bot из документа базы данных
                    bot_obj = Bot(
                        id=bot_doc["id"],
                        name=bot_doc["name"],
                        bot_type=bot_doc.get("bot_type", "REGULAR"),
                        min_bet_amount=bot_doc.get("min_bet_amount", bot_doc.get("min_bet", 1.0)),
                        max_bet_amount=bot_doc.get("max_bet_amount", bot_doc.get("max_bet", 100.0)),
                        win_rate=bot_doc.get("win_rate_percent", 60.0),
                        cycle_games=bot_doc.get("cycle_games", 12),
                        pause_between_games=bot_doc.get("pause_between_games", 5),
                        is_active=bot_doc.get("is_active", True),
                        can_accept_bets=bot_doc.get("can_accept_bets", True),
                        can_play_with_bots=bot_doc.get("can_play_with_bots", True),
                        created_at=bot_doc.get("created_at", datetime.utcnow()),
                        bot_behavior=bot_doc.get("bot_behavior", "balanced"),
                        profit_strategy=bot_doc.get("profit_strategy", "balanced")
                    )
                    
                    # Поддерживаем активные ставки на уровне цикла
                    await maintain_bot_active_bets_count(bot_id, cycle_games)
                    
            except Exception as e:
                logger.error(f"Error maintaining bets for bot {bot_doc.get('name', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in maintain_all_bots_active_bets: {e}")

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
# HUMAN BOT SIMULATION TASKS
# ==============================================================================

async def human_bot_simulation_task():
    """Background task for Human bot simulation."""
    logger.info("🤖 Human bot simulation task started")
    
    while True:
        try:
            # Get active human bots
            active_human_bots = await db.human_bots.find({"is_active": True}).to_list(100)
            
            if not active_human_bots:
                await asyncio.sleep(60)  # No active bots, wait 1 minute
                continue
            
            logger.info(f"🤖 Checking {len(active_human_bots)} active Human bots for actions")
            
            for bot_data in active_human_bots:
                try:
                    human_bot = HumanBot(**bot_data)
                    
                    # Check if bot should take action based on delay
                    if await should_human_bot_take_action(human_bot):
                        # Decide action: create bet or join existing bet
                        action = HumanBotBehavior.get_action_decision(human_bot.character)
                        
                        if action == "create":
                            await create_human_bot_bet(human_bot)
                        else:
                            await join_human_bot_bet(human_bot)
                        
                        # Log action
                        await log_human_bot_action(
                            human_bot.id,
                            "ACTION_DECISION",
                            f"Bot decided to {action}",
                            None,
                            None,
                            None,
                            None
                        )
                
                except Exception as e:
                    logger.error(f"Error processing human bot {bot_data.get('id')}: {e}")
            
            # Wait before next cycle (shorter interval for human bots)
            await asyncio.sleep(15)  # Check every 15 seconds
            
        except Exception as e:
            logger.error(f"Error in human bot simulation task: {e}")
            await asyncio.sleep(60)  # Wait longer if error occurred

async def should_human_bot_take_action(human_bot: HumanBot) -> bool:
    """Determine if human bot should take action based on timing and character."""
    if not human_bot.is_active:
        return False
    
    # Check if enough time has passed since last action
    if human_bot.last_action_time:
        time_since_last = datetime.utcnow() - human_bot.last_action_time
        min_delay = HumanBotBehavior.get_delay_time(human_bot.character, human_bot.min_delay, human_bot.max_delay)
        
        if time_since_last.total_seconds() < min_delay:
            return False
    
    # Character-based probability to act
    if human_bot.character == HumanBotCharacter.IMPULSIVE:
        return random.random() < 0.8  # 80% chance - very active
    elif human_bot.character == HumanBotCharacter.AGGRESSIVE:
        return random.random() < 0.6  # 60% chance - quite active
    elif human_bot.character == HumanBotCharacter.CAUTIOUS:
        return random.random() < 0.2  # 20% chance - less active
    else:
        return random.random() < 0.4  # 40% chance - moderate activity

async def create_human_bot_bet(human_bot: HumanBot):
    """Create a bet as a human bot (only if bet_limit allows)."""
    try:
        # Check current active bets count vs bet_limit
        current_active_bets = await get_human_bot_active_bets_count(human_bot.id)
        bot_limit = human_bot.bet_limit or 12  # Default to 12 if not set
        
        if current_active_bets >= bot_limit:
            logger.debug(f"Human bot {human_bot.name} has reached bet limit ({current_active_bets}/{bot_limit}), skipping bet creation")
            return
        
        logger.info(f"Creating bet for Human bot {human_bot.name} (active: {current_active_bets}/{bot_limit})")
        
        # Ensure bot has gems (setup if needed)
        await setup_human_bot_gems(human_bot.id)
        
        # Generate gem combination and bet amount based on character
        bet_gems, bet_amount = await generate_human_bot_gem_combination_and_amount(
            human_bot.character,
            human_bot.min_bet,
            human_bot.max_bet
        )
        
        # Generate bot's move
        bot_move = HumanBotBehavior.get_move_choice(human_bot.character)
        
        # Create commit-reveal if enabled
        if human_bot.use_commit_reveal:
            salt = secrets.token_hex(32)
            move_hash = hash_move_with_salt(bot_move, salt)
        else:
            salt = None
            move_hash = None
        
        # Create game
        game = Game(
            creator_id=human_bot.id,
            creator_type="human_bot",
            # Всегда сохраняем реальный ход, даже при commit-reveal
            creator_move=bot_move,
            creator_move_hash=move_hash,
            creator_salt=salt,
            bet_amount=bet_amount,
            bet_gems=bet_gems,
            is_bot_game=True,
            bot_id=human_bot.id,
            bot_type="HUMAN",
            metadata={
                "character": human_bot.character,
                "human_bot": True,
                "auto_created": True
            }
        )
        
        await db.games.insert_one(game.dict())
        
        # Update human bot's last action time and statistics
        await db.human_bots.update_one(
            {"id": human_bot.id},
            {
                "$set": {
                    "last_action_time": datetime.utcnow(),
                    "last_bet_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "total_amount_wagered": bet_amount
                }
            }
        )
        
        # Log the action
        await log_human_bot_action(
            human_bot.id,
            "CREATE_BET",
            f"Created bet with amount ${bet_amount}",
            game.id,
            bet_amount,
            None,
            bot_move.value
        )
        
        logger.info(f"🤖 Human bot {human_bot.name} ({human_bot.character}) created bet ${bet_amount}")
        
    except Exception as e:
        logger.error(f"Error creating human bot bet: {e}")

async def join_human_bot_bet(human_bot: HumanBot):
    """Join an existing bet as a human bot (only if bet_limit allows)."""
    try:
        # Check current active bets count vs bet_limit
        current_active_bets = await get_human_bot_active_bets_count(human_bot.id)
        bot_limit = human_bot.bet_limit or 12  # Default to 12 if not set
        
        if current_active_bets >= bot_limit:
            logger.debug(f"Human bot {human_bot.name} has reached bet limit ({current_active_bets}/{bot_limit}), skipping join attempt")
            return
        
        logger.info(f"Human bot {human_bot.name} attempting to join existing bet (active: {current_active_bets}/{bot_limit})")
        
        # Find available games that human bot can join
        available_games = await db.games.find({
            "status": GameStatus.WAITING,
            "creator_id": {"$ne": human_bot.id},  # Don't join own games
            "bet_amount": {"$gte": human_bot.min_bet, "$lte": human_bot.max_bet},
            # Human bots can join both human and regular bot games
        }).to_list(20)
        
        if not available_games:
            logger.info(f"🤖 No available games for human bot {human_bot.name}")
            return
        
        # Filter games based on character preferences
        suitable_games = []
        for game_data in available_games:
            game = Game(**game_data)
            
            # Character-based game selection
            if human_bot.character == HumanBotCharacter.CAUTIOUS:
                # Prefer lower value games
                if game.bet_amount <= (human_bot.min_bet + human_bot.max_bet) / 2:
                    suitable_games.append(game)
            elif human_bot.character == HumanBotCharacter.AGGRESSIVE:
                # Prefer higher value games
                if game.bet_amount >= (human_bot.min_bet + human_bot.max_bet) / 2:
                    suitable_games.append(game)
            else:
                # All games are suitable for other characters
                suitable_games.append(game)
        
        if not suitable_games:
            logger.info(f"🤖 No suitable games for human bot {human_bot.name} ({human_bot.character})")
            return
        
        # Select random game
        selected_game = random.choice(suitable_games)
        
        # Ensure bot has required gems
        await setup_human_bot_gems(human_bot.id)
        
        # Check if bot has enough gems
        for gem_type, quantity in selected_game.bet_gems.items():
            bot_gems = await db.user_gems.find_one({"user_id": human_bot.id, "gem_type": gem_type})
            if not bot_gems or bot_gems["quantity"] < quantity:
                logger.info(f"🤖 Human bot {human_bot.name} doesn't have enough {gem_type} gems")
                return
        
        # Freeze bot's gems
        for gem_type, quantity in selected_game.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": human_bot.id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Generate bot's move based on character
        bot_move = HumanBotBehavior.get_move_choice(human_bot.character)
        
        # Freeze commission (for human bots, commission applies)
        commission_amount = selected_game.bet_amount * 0.03  # 3% commission
        
        # Check if human bot has enough balance for commission
        bot_user = await db.users.find_one({"id": human_bot.id})
        if not bot_user:
            # Create user profile for human bot if it doesn't exist
            await create_human_bot_user_profile(human_bot)
            bot_user = await db.users.find_one({"id": human_bot.id})
            
        # Double check if user was created successfully
        if not bot_user:
            logger.error(f"Could not create or find user profile for human bot {human_bot.id}")
            return
        
        if bot_user.get("virtual_balance", 0) < commission_amount:
            # Give human bot some balance for commission
            await db.users.update_one(
                {"id": human_bot.id},
                {"$inc": {"virtual_balance": 1000.0}}  # Add $1000 balance
            )
        
        # Freeze commission
        await db.users.update_one(
            {"id": human_bot.id},
            {
                "$inc": {
                    "frozen_balance": commission_amount,
                    "virtual_balance": -commission_amount
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Update game with bot as opponent
        await db.games.update_one(
            {"id": selected_game.id},
            {
                "$set": {
                    "opponent_id": human_bot.id,
                    "opponent_move": bot_move,
                    "opponent_gems": selected_game.bet_gems,  # Same gems as creator
                    "status": GameStatus.REVEAL if selected_game.creator_move_hash else GameStatus.ACTIVE,
                    "started_at": datetime.utcnow(),
                    "reveal_deadline": datetime.utcnow() + timedelta(minutes=5) if selected_game.creator_move_hash else None
                }
            }
        )
        
        # Update human bot's last action time and statistics
        await db.human_bots.update_one(
            {"id": human_bot.id},
            {
                "$set": {
                    "last_action_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "total_amount_wagered": selected_game.bet_amount,
                    "total_games_played": 1
                }
            }
        )
        
        # Log the action
        await log_human_bot_action(
            human_bot.id,
            "JOIN_BET",
            f"Joined game with bet amount ${selected_game.bet_amount}",
            selected_game.id,
            selected_game.bet_amount,
            None,
            bot_move.value
        )
        
        logger.info(f"🤖 Human bot {human_bot.name} ({human_bot.character}) joined game {selected_game.id}")
        
        # If not using commit-reveal, determine winner immediately
        if not selected_game.creator_move_hash:
            await determine_game_winner(selected_game.id)
        
    except Exception as e:
        logger.error(f"Error joining human bot bet: {e}")

async def setup_human_bot_gems(human_bot_id: str):
    """Ensure human bot has adequate gems for betting."""
    try:
        # Define gem types and minimum quantities
        gem_types = ["Ruby", "Amber", "Topaz", "Emerald", "Aquamarine", "Sapphire", "Magic"]
        min_quantities = [50, 25, 10, 5, 2, 1, 1]  # Minimum quantities for each gem type
        
        for gem_type, min_qty in zip(gem_types, min_quantities):
            # Check current gem quantity
            user_gem = await db.user_gems.find_one({
                "user_id": human_bot_id,
                "gem_type": gem_type
            })
            
            if not user_gem:
                # Create new gem entry
                new_gem = UserGem(
                    user_id=human_bot_id,
                    gem_type=GemType(gem_type),
                    quantity=min_qty * 2  # Give double the minimum
                )
                await db.user_gems.insert_one(new_gem.dict())
            elif user_gem["quantity"] < min_qty:
                # Top up gems if below minimum
                await db.user_gems.update_one(
                    {"user_id": human_bot_id, "gem_type": gem_type},
                    {
                        "$inc": {"quantity": min_qty * 2 - user_gem["quantity"]},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
        
    except Exception as e:
        logger.error(f"Error setting up human bot gems: {e}")

async def generate_human_bot_gem_combination_and_amount(character: HumanBotCharacter, min_bet: float, max_bet: float) -> tuple:
    """Generate gem combination and bet amount based on character personality."""
    # Validate input parameters
    if min_bet <= 0:
        min_bet = 1  # Default minimum
    if max_bet <= min_bet:
        max_bet = max(min_bet * 2, 100)  # Ensure valid range
    
    logger.info(f"Generating bet for character {character}, range: ${min_bet}-${max_bet}")
    
    # Gem values
    gem_values = {
        "Ruby": 1, "Amber": 2, "Topaz": 5, "Emerald": 10,
        "Aquamarine": 25, "Sapphire": 50, "Magic": 100
    }
    
    # Character-based bet amount selection
    bet_range = max_bet - min_bet
    target_amount = 0
    
    if character == HumanBotCharacter.AGGRESSIVE:
        # 70-100% of range (high bets)
        min_pct, max_pct = 0.7, 1.0
        target_amount = min_bet + (bet_range * random.uniform(min_pct, max_pct))
        gem_pool = ["Emerald", "Aquamarine", "Sapphire", "Magic"]  # Prefer high-value gems
        logger.debug(f"AGGRESSIVE bot choosing from ${min_bet + bet_range * min_pct:.2f}-${max_bet}")
        
    elif character == HumanBotCharacter.CAUTIOUS:
        # 0-30% of range (low bets)
        min_pct, max_pct = 0.0, 0.3
        target_amount = min_bet + (bet_range * random.uniform(min_pct, max_pct))
        gem_pool = ["Ruby", "Amber", "Topaz"]  # Prefer low-value gems
        logger.debug(f"CAUTIOUS bot choosing from ${min_bet}-${min_bet + bet_range * max_pct:.2f}")
        
    elif character == HumanBotCharacter.BALANCED:
        # 0-100% of range (equal distribution)
        target_amount = random.uniform(min_bet, max_bet)
        gem_pool = list(gem_values.keys())  # All gems available
        logger.debug(f"BALANCED bot choosing from ${min_bet}-${max_bet}")
        
    elif character == HumanBotCharacter.IMPULSIVE:
        # 0-100% chaotic (can jump between extremes)
        choices = [
            random.uniform(min_bet, min_bet + bet_range * 0.2),  # Low bet
            random.uniform(min_bet + bet_range * 0.4, min_bet + bet_range * 0.6),  # Mid bet
            random.uniform(min_bet + bet_range * 0.8, max_bet)  # High bet
        ]
        target_amount = random.choice(choices)
        gem_pool = list(gem_values.keys())  # All gems, chaotic selection
        logger.debug(f"IMPULSIVE bot chaotically chose ${target_amount:.2f}")
        
    elif character == HumanBotCharacter.ANALYST:
        # 40-70% of range ("optimal" bets)
        min_pct, max_pct = 0.4, 0.7
        target_amount = min_bet + (bet_range * random.uniform(min_pct, max_pct))
        gem_pool = ["Topaz", "Emerald", "Aquamarine"]  # "Optimal" middle-tier gems
        logger.debug(f"ANALYST bot choosing optimal ${min_bet + bet_range * min_pct:.2f}-${min_bet + bet_range * max_pct:.2f}")
        
    elif character == HumanBotCharacter.STABLE:
        # 30-70% of range (stable middle bets)
        min_pct, max_pct = 0.3, 0.7
        target_amount = min_bet + (bet_range * random.uniform(min_pct, max_pct))
        gem_pool = ["Ruby", "Amber", "Topaz", "Emerald"]  # Stable, predictable gems
        logger.debug(f"STABLE bot choosing stable ${min_bet + bet_range * min_pct:.2f}-${min_bet + bet_range * max_pct:.2f}")
        
    elif character == HumanBotCharacter.MIMIC:
        # Copy recent successful bet patterns (for now, use balanced approach)
        target_amount = random.uniform(min_bet, max_bet)
        gem_pool = list(gem_values.keys())
        logger.debug(f"MIMIC bot mimicking patterns, chose ${target_amount:.2f}")
        
    else:
        # Default: balanced approach
        target_amount = random.uniform(min_bet, max_bet)
        gem_pool = list(gem_values.keys())
        logger.debug(f"DEFAULT character choosing ${target_amount:.2f}")
    
    # Ensure target amount is within bounds
    target_amount = max(min_bet, min(target_amount, max_bet))
    target_int = int(target_amount)
    
    logger.info(f"Character {character} selected bet amount: ${target_amount:.2f}")
    
    # Generate gem combination for the target amount
    combination = {}
    remaining = target_int
    
    # Character-specific gem selection strategy
    if character == HumanBotCharacter.AGGRESSIVE:
        # Start with high-value gems, less quantity
        gem_types_order = ["Magic", "Sapphire", "Aquamarine", "Emerald"]
        max_per_type = 2
    elif character == HumanBotCharacter.CAUTIOUS:
        # Start with low-value gems, more quantity for safety
        gem_types_order = ["Ruby", "Amber", "Topaz", "Emerald"]
        max_per_type = 10
    elif character == HumanBotCharacter.IMPULSIVE:
        # Random order, chaotic quantities
        gem_types_order = random.sample(list(gem_values.keys()), len(gem_values))
        max_per_type = random.randint(1, 5)
    elif character == HumanBotCharacter.ANALYST:
        # Optimal middle gems, calculated quantities
        gem_types_order = ["Emerald", "Topaz", "Aquamarine", "Ruby"]
        max_per_type = 3
    else:
        # Balanced/Stable/Default: standard descending order
        gem_types_order = ["Magic", "Sapphire", "Aquamarine", "Emerald", "Topaz", "Amber", "Ruby"]
        max_per_type = 5
    
    # Generate combination using character strategy
    for gem_type in gem_types_order:
        if remaining <= 0:
            break
            
        gem_value = gem_values[gem_type]
        if remaining >= gem_value:
            max_quantity = min(remaining // gem_value, max_per_type)
            if max_quantity > 0:
                # Add some randomness based on character
                if character == HumanBotCharacter.IMPULSIVE:
                    quantity = random.randint(1, max_quantity) if max_quantity > 1 else 1
                else:
                    quantity = max_quantity
                    
                combination[gem_type] = quantity
                remaining -= quantity * gem_value
    
    # Handle remaining value with Ruby gems (always small denomination)
    if remaining > 0:
        combination["Ruby"] = combination.get("Ruby", 0) + remaining
    
    # Calculate final amount
    final_amount = sum(gem_values[gem_type] * quantity for gem_type, quantity in combination.items())
    
    logger.info(f"Generated combination for {character}: {combination}, total: ${final_amount}")
    
    return combination, float(final_amount)

async def generate_human_bot_gem_combination(target_amount: float) -> dict:
    """Generate a realistic gem combination for the target amount."""
    # Gem values
    gem_values = {
        "Ruby": 1, "Amber": 2, "Topaz": 5, "Emerald": 10,
        "Aquamarine": 25, "Sapphire": 50, "Magic": 100
    }
    
    target_int = int(target_amount)
    combination = {}
    remaining = target_int
    
    # Start with larger gems for efficiency
    gem_types_desc = ["Magic", "Sapphire", "Aquamarine", "Emerald", "Topaz", "Amber", "Ruby"]
    
    for gem_type in gem_types_desc:
        if remaining <= 0:
            break
            
        gem_value = gem_values[gem_type]
        if remaining >= gem_value:
            quantity = remaining // gem_value
            # Limit quantity to make it realistic
            max_quantity = min(quantity, 3) if gem_type in ["Magic", "Sapphire"] else min(quantity, 5)
            if max_quantity > 0:
                combination[gem_type] = max_quantity
                remaining -= max_quantity * gem_value
    
    # If there's remaining value, add Ruby gems
    if remaining > 0:
        combination["Ruby"] = combination.get("Ruby", 0) + remaining
    
    return combination

async def create_human_bot_user_profile(human_bot: HumanBot):
    """Create a user profile for human bot if it doesn't exist."""
    try:
        # Check if user profile already exists
        existing_user = await db.users.find_one({"id": human_bot.id})
        if existing_user:
            return
        
        # Create user profile
        bot_user = User(
            id=human_bot.id,
            username=human_bot.name,
            email=f"{human_bot.name.lower().replace(' ', '_')}@example.com",  # Use valid domain
            password_hash="",  # Human bots don't need passwords
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            email_verified=True,
            virtual_balance=2000.0,  # Give initial balance
            gender=random.choice(["male", "female"])
        )
        
        await db.users.insert_one(bot_user.dict())
        logger.info(f"Created user profile for human bot: {human_bot.name}")
        
    except Exception as e:
        logger.error(f"Error creating human bot user profile: {e}")

async def log_human_bot_action(
    human_bot_id: str,
    action_type: str,
    description: str,
    game_id: Optional[str] = None,
    bet_amount: Optional[float] = None,
    outcome: Optional[str] = None,
    move_played: Optional[str] = None
):
    """Log human bot action."""
    try:
        log_entry = HumanBotLog(
            human_bot_id=human_bot_id,
            action_type=action_type,
            description=description,
            game_id=game_id,
            bet_amount=bet_amount,
            outcome=outcome,
            move_played=move_played
        )
        
        await db.human_bot_logs.insert_one(log_entry.dict())
        
    except Exception as e:
        logger.error(f"Error logging human bot action: {e}")

async def apply_human_bot_outcome(game_obj: Game) -> Optional[Dict[str, str]]:
    """Apply Human bot outcome logic based on their win/loss percentages."""
    try:
        # Check if any human bots are involved
        creator_human_bot = None
        opponent_human_bot = None
        
        if game_obj.creator_id:
            creator_human_bot = await db.human_bots.find_one({"id": game_obj.creator_id})
        
        if game_obj.opponent_id:
            opponent_human_bot = await db.human_bots.find_one({"id": game_obj.opponent_id})
        
        # If no human bots involved, return None
        if not creator_human_bot and not opponent_human_bot:
            return None
        
        # Determine outcome based on human bot settings
        if creator_human_bot and opponent_human_bot:
            # Both are human bots - use creator's settings for simplicity
            human_bot = creator_human_bot
        elif creator_human_bot:
            human_bot = creator_human_bot
        else:
            human_bot = opponent_human_bot
        
        # Get the human bot's outcome preferences
        win_percentage = human_bot.get("win_percentage", 40.0)
        loss_percentage = human_bot.get("loss_percentage", 40.0)
        draw_percentage = human_bot.get("draw_percentage", 20.0)
        
        # Use the HumanBotBehavior to determine outcome
        character = HumanBotCharacter(human_bot.get("character", "BALANCED"))
        outcome = HumanBotBehavior.should_win_game(
            character, 
            win_percentage, 
            loss_percentage, 
            draw_percentage, 
            game_obj.bet_amount
        )
        
        # Map outcome to winner_id and result_status
        if outcome == "WIN":
            if creator_human_bot:
                return {"winner_id": game_obj.creator_id, "result_status": "creator_wins"}
            else:
                return {"winner_id": game_obj.opponent_id, "result_status": "opponent_wins"}
        elif outcome == "LOSS":
            if creator_human_bot:
                return {"winner_id": game_obj.opponent_id, "result_status": "opponent_wins"}
            else:
                return {"winner_id": game_obj.creator_id, "result_status": "creator_wins"}
        else:  # DRAW
            return {"winner_id": None, "result_status": "draw"}
            
    except Exception as e:
        logger.error(f"Error applying human bot outcome for game {game_obj.id}: {e}")
        logger.error(f"Game creator_id: {game_obj.creator_id}, opponent_id: {game_obj.opponent_id}")
        logger.error(f"Error traceback:", exc_info=True)
        return None

def determine_rps_winner(creator_move: GameMove, opponent_move: GameMove, creator_id: str, opponent_id: str) -> tuple:
    """Determine winner using rock-paper-scissors logic."""
    winner_id = None
    result_status = "draw"
    
    if creator_move == opponent_move:
        result_status = "draw"
    elif (
        (creator_move == GameMove.ROCK and opponent_move == GameMove.SCISSORS) or
        (creator_move == GameMove.SCISSORS and opponent_move == GameMove.PAPER) or
        (creator_move == GameMove.PAPER and opponent_move == GameMove.ROCK)
    ):
        winner_id = creator_id
        result_status = "creator_wins"
    else:
        winner_id = opponent_id
        result_status = "opponent_wins"
    
    return winner_id, result_status

async def get_player_info(player_id: str) -> Dict[str, str]:
    """Get player information (user, bot, or human bot)."""
    # Try to find as user first
    user = await db.users.find_one({"id": player_id})
    if user:
        return {
            "id": user["id"],
            "username": user["username"]
        }
    
    # Try to find as regular bot
    bot = await db.bots.find_one({"id": player_id})
    if bot:
        return {
            "id": bot["id"],
            "username": bot["name"]
        }
    
    # Try to find as human bot
    human_bot = await db.human_bots.find_one({"id": player_id})
    if human_bot:
        return {
            "id": human_bot["id"],
            "username": human_bot["name"]
        }
    
    # Fallback if not found
    return {
        "id": player_id,
        "username": "Unknown Player"
    }

async def process_human_bot_game_outcome(game_id: str, winner_id: Optional[str]):
    """Process game outcome for human bots and update statistics."""
    try:
        # Get game details
        game = await db.games.find_one({"id": game_id})
        if not game:
            return
        
        # Check if any human bots are involved
        human_bot_ids = []
        
        # Check creator
        creator_bot = await db.human_bots.find_one({"id": game["creator_id"]})
        if creator_bot:
            human_bot_ids.append(game["creator_id"])
        
        # Check opponent
        if game.get("opponent_id"):
            opponent_bot = await db.human_bots.find_one({"id": game["opponent_id"]})
            if opponent_bot:
                human_bot_ids.append(game["opponent_id"])
        
        # Process outcome for each human bot
        for bot_id in human_bot_ids:
            outcome = "DRAW"
            if winner_id == bot_id:
                outcome = "WIN"
            elif winner_id and winner_id != bot_id:
                outcome = "LOSS"
            
            # Update human bot statistics
            update_data = {"updated_at": datetime.utcnow()}
            
            if outcome == "WIN":
                update_data["$inc"] = {
                    "total_games_won": 1,
                    "total_amount_won": game["bet_amount"] * 2  # Winner takes all
                }
            
            await db.human_bots.update_one(
                {"id": bot_id},
                {"$set": update_data}
            )
            
            # Log the outcome
            await log_human_bot_action(
                bot_id,
                outcome,
                f"Game {game_id} ended with outcome: {outcome}",
                game_id,
                game["bet_amount"],
                outcome,
                None
            )
            
            logger.info(f"🎯 Human bot {bot_id} game outcome: {outcome} for ${game['bet_amount']}")
        
    except Exception as e:
        logger.error(f"Error processing human bot game outcome: {e}")

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

@api_router.get("/notifications", response_model=List[dict])
async def get_user_notifications(current_user: User = Depends(get_current_user)):
    """Get user notifications."""
    try:
        notifications = await db.notifications.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).limit(20).to_list(20)
        
        return [
            {
                "id": str(notification.get("_id")),
                "type": notification.get("type", "INFO"),
                "title": notification.get("title", ""),
                "message": notification.get("message", ""),
                "read": notification.get("read", False),
                "created_at": notification.get("created_at").isoformat()
            }
            for notification in notifications
        ]
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch notifications"
        )

@api_router.post("/notifications/{notification_id}/mark-read", response_model=dict)
async def mark_notification_read(
    notification_id: str, 
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read."""
    try:
        from bson import ObjectId
        
        result = await db.notifications.update_one(
            {
                "_id": ObjectId(notification_id),
                "user_id": current_user.id
            },
            {"$set": {"read": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )
        
        return {"success": True, "message": "Notification marked as read"}
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to mark notification as read"
        )

@api_router.post("/notifications/mark-all-read", response_model=dict)
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read."""
    try:
        result = await db.notifications.update_many(
            {"user_id": current_user.id, "read": False},
            {"$set": {"read": True}}
        )
        
        return {
            "success": True, 
            "message": f"Marked {result.modified_count} notifications as read"
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to mark notifications as read"
        )

@api_router.get("/users/search", response_model=List[dict])
async def search_users(query: str, current_user: User = Depends(get_current_user)):
    """Search users by email or username for gifting."""
    try:
        # Исключаем текущего пользователя из результатов
        # Ищем по email или username (case-insensitive)
        search_filter = {
            "$and": [
                {"id": {"$ne": current_user.id}},  # Исключаем себя
                {
                    "$or": [
                        {"email": {"$regex": f"^{query}", "$options": "i"}},
                        {"username": {"$regex": f"^{query}", "$options": "i"}}
                    ]
                }
            ]
        }
        
        users = await db.users.find(
            search_filter,
            {"username": 1, "email": 1, "id": 1}  # Возвращаем только нужные поля
        ).limit(5).to_list(5)
        
        return [
            {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search users"
        )

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
    
    # Create notification for recipient
    notification = {
        "user_id": recipient["id"],
        "type": "GIFT_RECEIVED",
        "title": "Gift Received!",
        "message": f"You received a gift from {current_user.username} — {quantity} {gem_type} gems worth ${gem_value:.2f}.",
        "read": False,
        "created_at": datetime.utcnow()
    }
    await db.notifications.insert_one(notification)
    
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

@api_router.get("/admin/profit/bot-integration", response_model=dict)
async def get_bot_profit_integration(current_admin: User = Depends(get_current_admin)):
    """Get detailed bot profit integration data for main profit dashboard."""
    try:
        current_time = datetime.utcnow()
        day_ago = current_time - timedelta(days=1)
        week_ago = current_time - timedelta(weeks=1)
        month_ago = current_time - timedelta(days=30)
        
        # Get bot revenue by time periods
        bot_revenue_today = await db.profit_entries.aggregate([
            {"$match": {"entry_type": "BOT_REVENUE", "created_at": {"$gte": day_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        bot_revenue_today = bot_revenue_today[0]["total"] if bot_revenue_today else 0
        
        bot_revenue_week = await db.profit_entries.aggregate([
            {"$match": {"entry_type": "BOT_REVENUE", "created_at": {"$gte": week_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        bot_revenue_week = bot_revenue_week[0]["total"] if bot_revenue_week else 0
        
        bot_revenue_month = await db.profit_entries.aggregate([
            {"$match": {"entry_type": "BOT_REVENUE", "created_at": {"$gte": month_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        bot_revenue_month = bot_revenue_month[0]["total"] if bot_revenue_month else 0
        
        # Get total bot revenue
        bot_revenue_total = await db.profit_entries.aggregate([
            {"$match": {"entry_type": "BOT_REVENUE"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        bot_revenue_total = bot_revenue_total[0]["total"] if bot_revenue_total else 0
        
        # Get bot revenue by creation mode
        bot_revenue_by_mode = await db.profit_entries.aggregate([
            {"$match": {"entry_type": "BOT_REVENUE"}},
            {"$lookup": {"from": "bots", "localField": "source_id", "foreignField": "id", "as": "bot"}},
            {"$unwind": {"path": "$bot", "preserveNullAndEmptyArrays": True}},
            {"$group": {
                "_id": "$bot.creation_mode",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }}
        ]).to_list(10)
        
        # Get bot revenue by behavior
        bot_revenue_by_behavior = await db.profit_entries.aggregate([
            {"$match": {"entry_type": "BOT_REVENUE"}},
            {"$lookup": {"from": "bots", "localField": "source_id", "foreignField": "id", "as": "bot"}},
            {"$unwind": {"path": "$bot", "preserveNullAndEmptyArrays": True}},
            {"$group": {
                "_id": "$bot.bot_behavior",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }}
        ]).to_list(10)
        
        # Get active bots count
        active_bots = await db.bots.count_documents({"type": "REGULAR", "is_active": True})
        
        # Get bot win rate statistics
        bot_win_stats = await db.bots.aggregate([
            {"$match": {"type": "REGULAR"}},
            {"$group": {
                "_id": None,
                "avg_win_rate": {"$avg": "$win_rate_percent"},
                "total_bots": {"$sum": 1},
                "active_bots": {"$sum": {"$cond": ["$is_active", 1, 0]}}
            }}
        ]).to_list(1)
        bot_win_stats = bot_win_stats[0] if bot_win_stats else {}
        
        # Get recent bot transactions
        recent_bot_transactions = await db.profit_entries.find({
            "entry_type": "BOT_REVENUE"
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # Calculate bot efficiency
        total_games = await db.games.count_documents({
            "creator_type": "bot",
            "bot_type": "REGULAR",
            "status": "COMPLETED"
        })
        
        bot_efficiency = {
            "revenue_per_game": bot_revenue_total / total_games if total_games > 0 else 0,
            "revenue_per_bot": bot_revenue_total / active_bots if active_bots > 0 else 0,
            "games_per_bot": total_games / active_bots if active_bots > 0 else 0
        }
        
        # Format creation mode data
        creation_mode_data = {}
        for item in bot_revenue_by_mode:
            mode = item["_id"] or "queue-based"
            creation_mode_data[mode] = {
                "revenue": item["total"],
                "transactions": item["count"]
            }
        
        # Format behavior data
        behavior_data = {}
        for item in bot_revenue_by_behavior:
            behavior = item["_id"] or "balanced"
            behavior_data[behavior] = {
                "revenue": item["total"],
                "transactions": item["count"]
            }
        
        return {
            "bot_revenue": {
                "today": bot_revenue_today,
                "week": bot_revenue_week,
                "month": bot_revenue_month,
                "total": bot_revenue_total
            },
            "bot_stats": {
                "active_bots": active_bots,
                "total_bots": bot_win_stats.get("total_bots", 0),
                "avg_win_rate": bot_win_stats.get("avg_win_rate", 0),
                "total_games": total_games
            },
            "creation_modes": creation_mode_data,
            "behaviors": behavior_data,
            "efficiency": bot_efficiency,
            "recent_transactions": [
                {
                    "id": str(tx["_id"]),
                    "amount": tx["amount"],
                    "created_at": tx["created_at"],
                    "description": tx.get("description", ""),
                    "source_id": tx.get("source_id", "")
                }
                for tx in recent_bot_transactions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching bot profit integration data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot profit integration data"
        )

@api_router.get("/admin/bots/{bot_id}/win-rate-analysis", response_model=dict)
async def get_bot_win_rate_analysis(bot_id: str, current_user: User = Depends(get_current_admin)):
    """Get detailed win rate analysis for a bot."""
    try:
        # Получаем бота
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Получаем игры бота
        bot_games = await db.games.find({
            "creator_id": bot_id,
            "creator_type": "bot",
            "status": "COMPLETED"
        }).sort("created_at", -1).limit(100).to_list(100)
        
        # Анализируем win rate
        total_games = len(bot_games)
        total_wins = sum(1 for game in bot_games if game.get("result") == "WIN")
        actual_win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        # Получаем настройки бота
        target_win_rate = bot.get("win_rate_percent", 60)
        bot_behavior = bot.get("bot_behavior", "balanced")
        profit_strategy = bot.get("profit_strategy", "balanced")
        
        # Анализируем цикл
        cycle_games = bot.get("cycle_games", 12)
        current_cycle_games = bot.get("current_cycle_games", 0)
        current_cycle_wins = bot.get("current_cycle_wins", 0)
        current_cycle_win_rate = (current_cycle_wins / current_cycle_games * 100) if current_cycle_games > 0 else 0
        
        # Прогнозируем оставшиеся игры
        remaining_games = cycle_games - current_cycle_games
        needed_wins = int(target_win_rate / 100 * cycle_games) - current_cycle_wins
        needed_win_rate = (needed_wins / remaining_games * 100) if remaining_games > 0 else 0
        
        # Анализируем поведение
        behavior_stats = {
            "aggressive": {
                "description": "Более агрессивная игра с большим разбросом результатов",
                "win_rate_variance": "±15%",
                "bet_pattern": "Непредсказуемые суммы ставок"
            },
            "balanced": {
                "description": "Сбалансированная игра со стабильными результатами",
                "win_rate_variance": "±10%",
                "bet_pattern": "Равномерные суммы ставок"
            },
            "cautious": {
                "description": "Осторожная игра с минимальными рисками",
                "win_rate_variance": "±5%",
                "bet_pattern": "Консервативные суммы ставок"
            }
        }.get(bot_behavior, {})
        
        # Стратегия прибыли
        strategy_stats = {
            "start_profit": {
                "description": "Старт с прибыли - выигрыши в начале цикла",
                "pattern": "Фронт-лоадинг выигрышей"
            },
            "balanced": {
                "description": "Сбалансированная стратегия - равномерные выигрыши",
                "pattern": "Случайное распределение выигрышей"
            },
            "end_loss": {
                "description": "Принятие поражений в конце цикла",
                "pattern": "Бэк-лоадинг проигрышей"
            }
        }.get(profit_strategy, {})
        
        return {
            "bot_id": bot_id,
            "bot_name": bot.get("name", "Unknown"),
            "target_win_rate": target_win_rate,
            "actual_win_rate": round(actual_win_rate, 2),
            "win_rate_difference": round(actual_win_rate - target_win_rate, 2),
            "total_games": total_games,
            "total_wins": total_wins,
            "current_cycle": {
                "games_played": current_cycle_games,
                "games_won": current_cycle_wins,
                "win_rate": round(current_cycle_win_rate, 2),
                "total_games": cycle_games,
                "remaining_games": remaining_games,
                "needed_wins": max(0, needed_wins),
                "needed_win_rate": round(needed_win_rate, 2)
            },
            "behavior": {
                "type": bot_behavior,
                "stats": behavior_stats
            },
            "strategy": {
                "type": profit_strategy,
                "stats": strategy_stats
            },
            "performance": {
                "is_on_target": abs(actual_win_rate - target_win_rate) <= 5,
                "cycle_progress": round(current_cycle_games / cycle_games * 100, 2),
                "predicted_final_win_rate": round(
                    (current_cycle_wins + needed_wins) / cycle_games * 100, 2
                ) if cycle_games > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting bot win rate analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot win rate analysis"
        )

# Endpoint removed - Frontend now handles gem combination logic

@api_router.post("/admin/bots/{bot_id}/toggle-status", response_model=dict)
async def toggle_extended_bot_status(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Переключить статус расширенного бота."""
    try:
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        new_status = not bot.get("is_active", False)
        
        await db.bots.update_one(
            {"id": bot_id},
            {"$set": {
                "is_active": new_status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Логирование действия
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="TOGGLE_BOT_STATUS",
            target_type="bot",
            target_id=bot_id,
            details={
                "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
                "new_status": new_status
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "success": True,
            "message": f"Бот {'включен' if new_status else 'отключен'}",
            "is_active": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling bot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при изменении статуса бота"
        )

@api_router.post("/admin/bots/{bot_id}/force-complete-cycle", response_model=dict)
async def force_complete_bot_cycle(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Принудительно завершить цикл бота."""
    try:
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        # Отменяем все активные ставки бота
        cancelled_bets = await db.games.update_many(
            {"creator_id": bot_id, "status": "waiting"},
            {"$set": {
                "status": "cancelled",
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Подсчитываем прибыль/убыток за текущий цикл
        completed_games = await db.games.find({
            "creator_id": bot_id,
            "status": "completed"
        }).to_list(None)
        
        total_bet_amount = sum(game.get("bet_amount", 0) for game in completed_games)
        total_winnings = sum(game.get("winnings", 0) for game in completed_games if game.get("winner_id") == bot_id)
        cycle_profit = total_winnings - total_bet_amount
        
        # Обновляем статистику бота
        await db.bots.update_one(
            {"id": bot_id},
            {"$set": {
                "current_cycle_games": 0,
                "current_cycle_wins": 0,
                "current_cycle_losses": 0,
                "bot_profit_amount": bot.get("bot_profit_amount", 0) + cycle_profit,
                "bot_profit_percent": ((bot.get("bot_profit_amount", 0) + cycle_profit) / max(total_bet_amount, 1)) * 100,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Логирование действия
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="FORCE_COMPLETE_CYCLE",
            target_type="bot",
            target_id=bot_id,
            details={
                "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
                "cancelled_bets": cancelled_bets.modified_count,
                "cycle_profit": cycle_profit
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "success": True,
            "message": f"Цикл бота завершен принудительно. Прибыль: ${cycle_profit:.2f}",
            "profit": cycle_profit,
            "cancelled_bets": cancelled_bets.modified_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error force completing cycle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при принудительном завершении цикла"
        )

@api_router.get("/admin/bots/{bot_id}/cycle-bets", response_model=dict)
async def get_bot_cycle_bets(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Получить ставки текущего цикла бота."""
    try:
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        # Получаем все игры бота за текущий цикл
        cycle_games = await db.games.find({
            "creator_id": bot_id,
            "is_bot_game": True
        }).sort("created_at", -1).limit(bot.get("cycle_games", 12)).to_list(None)
        
        # Форматируем данные для отображения
        formatted_bets = []
        for i, game in enumerate(cycle_games):
            bet_info = {
                "position": i + 1,
                "amount": game.get("bet_amount", 0),
                "gems": game.get("bet_gems", {}),
                "status": game.get("status", "waiting"),
                "result": None,
                "created_at": game.get("created_at"),
                "opponent": game.get("opponent_name", "Ожидание")
            }
            
            if game.get("status") == "completed":
                if game.get("winner_id") == bot_id:
                    bet_info["result"] = "win"
                elif game.get("winner_id"):
                    bet_info["result"] = "loss"
                else:
                    bet_info["result"] = "draw"
            
            formatted_bets.append(bet_info)
        
        return {
            "success": True,
            "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
            "current_cycle": len([b for b in formatted_bets if b["status"] == "completed"]),
            "cycle_total": bot.get("cycle_games", 12),
            "cycle_total_amount": bot.get("cycle_total_amount", 0),
            "win_rate_percent": bot.get("win_rate_percent", 60),
            "bets": formatted_bets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cycle bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении ставок цикла"
        )

@api_router.post("/admin/bots/create-extended", response_model=dict)
async def create_extended_bot(
    bot_config: dict,
    current_user: User = Depends(get_current_admin)
):
    """Create extended bot with new system (admin only)."""
    try:
        name = bot_config.get("name", "")
        creation_mode = bot_config.get("creation_mode", "queue-based")
        cycle_games = bot_config.get("cycle_games", 12)
        bot_behavior = bot_config.get("bot_behavior", "balanced")
        bot_type = bot_config.get("bot_type", "type-1")
        custom_min_bet = bot_config.get("custom_min_bet", 1)
        custom_max_bet = bot_config.get("custom_max_bet", 10)
        cycle_total_amount = bot_config.get("cycle_total_amount", 0)
        win_rate_percent = bot_config.get("win_rate_percent", 60)
        profit_strategy = bot_config.get("profit_strategy", "balanced")
        can_accept_bets = bot_config.get("can_accept_bets", False)
        can_play_with_bots = bot_config.get("can_play_with_bots", True)
        
        # Определение диапазона ставок из bot_type
        bot_types_map = {
            'type-1': {'min': 1, 'max': 2, 'name': 'Type 1: 1–2 $'},
            'type-2': {'min': 1, 'max': 5, 'name': 'Type 2: 1–5 $'},
            'type-3': {'min': 1, 'max': 10, 'name': 'Type 3: 1–10 $'},
            'type-4': {'min': 5, 'max': 20, 'name': 'Type 4: 5–20 $'},
            'type-5': {'min': 10, 'max': 50, 'name': 'Type 5: 10–50 $'},
            'type-6': {'min': 10, 'max': 100, 'name': 'Type 6: 10–100 $'},
            'type-7': {'min': 25, 'max': 200, 'name': 'Type 7: 25–200 $'},
            'type-8': {'min': 50, 'max': 500, 'name': 'Type 8: 50–500 $'},
            'type-9': {'min': 100, 'max': 1000, 'name': 'Type 9: 100–1000 $'},
            'type-10': {'min': 100, 'max': 2000, 'name': 'Type 10: 100–2000 $'},
            'type-11': {'min': 100, 'max': 3000, 'name': 'Type 11: 100–3000 $'},
            'custom': {'min': custom_min_bet, 'max': custom_max_bet, 'name': 'Custom'}
        }
        
        if bot_type not in bot_types_map:
            raise HTTPException(status_code=400, detail="Invalid bot type")
            
        bot_type_info = bot_types_map[bot_type]
        min_bet = bot_type_info['min']
        max_bet = bot_type_info['max']
        
        # Валидация расширенной системы
        validation_errors = []
        
        if not name or len(name.strip()) < 3:
            validation_errors.append("Имя бота должно содержать минимум 3 символа")
        
        if cycle_games < 1 or cycle_games > 100:
            validation_errors.append("Количество игр в цикле должно быть от 1 до 100")
        
        if win_rate_percent < 0 or win_rate_percent > 100:
            validation_errors.append("Процент выигрыша должен быть от 0% до 100%")
        
        if creation_mode not in ['always-first', 'queue-based', 'after-all']:
            validation_errors.append("Неверный режим создания ставок")
        
        if bot_behavior not in ['aggressive', 'balanced', 'cautious']:
            validation_errors.append("Неверное поведение бота")
        
        if profit_strategy not in ['start-positive', 'balanced', 'start-negative']:
            validation_errors.append("Неверная стратегия прибыли")
        
        if cycle_total_amount <= 0:
            validation_errors.append("Сумма за цикл должна быть больше 0")
        
        if bot_type == 'custom':
            if custom_min_bet <= 0:
                validation_errors.append("Минимальная ставка должна быть больше 0")
            if custom_max_bet <= custom_min_bet:
                validation_errors.append("Максимальная ставка должна быть больше минимальной")
        
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Ошибки валидации: {'; '.join(validation_errors)}"
            )
        
        # Создание расширенного бота
        bot_data = {
            "id": str(uuid.uuid4()),
            "type": "REGULAR",
            "name": name.strip(),
            "mode": "ALGORITHMIC", 
            "is_active": True,
            "bot_type": "REGULAR",
            
            # Параметры расширенной системы
            "creation_mode": creation_mode,
            "cycle_games": cycle_games,
            "bot_behavior": bot_behavior,
            "bot_type_id": bot_type,
            "bot_type_name": bot_type_info['name'],
            "custom_min_bet": custom_min_bet if bot_type == 'custom' else None,
            "custom_max_bet": custom_max_bet if bot_type == 'custom' else None,
            "cycle_total_amount": cycle_total_amount,
            "win_rate_percent": win_rate_percent,
            "profit_strategy": profit_strategy,
            
            # Диапазон ставок
            "min_bet_amount": min_bet,
            "max_bet_amount": max_bet,
            
            # Дополнительные настройки
            "can_accept_bets": can_accept_bets,
            "can_play_with_bots": can_play_with_bots,
            
            # Статистика
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "games_draw": 0,
            "current_cycle_games": 0,
            "current_cycle_wins": 0,
            "current_cycle_losses": 0,
            "total_bet_amount": 0.0,
            "bot_profit_amount": 0.0,
            "bot_profit_percent": 0.0,
            
            # Состояние
            "last_game_time": None,
            "last_bet_time": None,
            "current_bet_id": None,
            "active_bets": 0,
            
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.bots.insert_one(bot_data)
        
        created_bot_id = bot_data["id"]
        
        # Генерируем начальные ставки для бота используя расширенную систему
        try:
            if creation_mode == 'queue-based':
                # Создаем ставки сразу для queue-based ботов
                await generate_bot_cycle_bets(
                    bot_id=created_bot_id,
                    cycle_length=cycle_games,
                    cycle_total_amount=cycle_total_amount,
                    win_percentage=win_rate_percent,
                    min_bet=min_bet,
                    avg_bet=max_bet,
                    bet_distribution="medium"
                )
                logger.info(f"Generated initial bets for extended bot {created_bot_id}")
            else:
                # Для always-first и after-all режимов создаем ставки по расписанию
                logger.info(f"Extended bot {created_bot_id} created with {creation_mode} mode, bets will be generated according to schedule")
        except Exception as e:
            logger.error(f"Error generating initial bets for extended bot {created_bot_id}: {e}")
            # Не блокируем создание бота из-за ошибки генерации ставок
        
        # Логирование действия администратора
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="CREATE_EXTENDED_BOT",
            target_type="bot",
            target_id=created_bot_id,
            details={
                "bot_name": name,
                "config": bot_config,
                "validation_passed": True
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "message": f"Расширенный бот {name} создан успешно",
            "bot_id": created_bot_id,
            "bot_name": name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating extended bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create extended bot"
        )

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
    
    # Calculate available balance for spending
    available_balance = user["virtual_balance"] - user["frozen_balance"]
    
    return {
        "virtual_balance": user["virtual_balance"],  # Total balance
        "frozen_balance": user["frozen_balance"],    # Frozen from total balance
        "available_balance": available_balance,       # Available for new operations
        "total_gem_value": total_gem_value,
        "available_gem_value": available_gem_value,
        "total_value": user["virtual_balance"] + total_gem_value,  # Updated: only count virtual_balance once
        "daily_limit_used": user["daily_limit_used"],
        "daily_limit_max": user["daily_limit_max"],
        "balance_breakdown": {
            "description": "Balance breakdown",
            "total_dollars": user["virtual_balance"],
            "frozen_dollars": user["frozen_balance"], 
            "available_dollars": available_balance,
            "total_gems_value": total_gem_value,
            "available_gems_value": available_gem_value
        }
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

@api_router.get("/debug/balance/{user_id}")
async def debug_user_balance(user_id: str):
    """Debug endpoint to check user balance details."""
    try:
        user = await db.users.find_one({"id": user_id})
        if not user:
            return {"error": "User not found"}
        
        return {
            "user_id": user_id,
            "virtual_balance": user.get("virtual_balance", 0),
            "frozen_balance": user.get("frozen_balance", 0),
            "available_balance": user.get("virtual_balance", 0) - user.get("frozen_balance", 0),
            "total_balance": user.get("virtual_balance", 0),
            "updated_at": user.get("updated_at")
        }
    except Exception as e:
        return {"error": str(e)}

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
    logger.info(f"🎮 CREATE_GAME called for user {current_user.id}")
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
        
        # Check if user has enough balance for commission (3% of bet amount)
        commission_required = total_bet_amount * 0.03
        user = await db.users.find_one({"id": current_user.id})
        
        logger.info(f"💰 COMMISSION DEBUG - User: {current_user.id}")
        logger.info(f"💰 Total bet amount: ${total_bet_amount}")
        logger.info(f"💰 Commission required: ${commission_required} (3%)")
        logger.info(f"💰 User virtual_balance before: ${user['virtual_balance']}")
        logger.info(f"💰 User frozen_balance before: ${user['frozen_balance']}")
        
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
        
        # Freeze commission balance - ПРАВИЛЬНАЯ ЛОГИКА: списываем с virtual_balance и добавляем к frozen_balance
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$inc": {
                    "virtual_balance": -commission_required,  # Списываем с virtual_balance
                    "frozen_balance": commission_required     # Добавляем к frozen_balance
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        logger.info(f"💰 User virtual_balance after: ${user['virtual_balance'] - commission_required}")
        logger.info(f"💰 User frozen_balance after: ${user['frozen_balance'] + commission_required}")
        logger.info(f"💰 Commission frozen: ${commission_required}")
        logger.info(f"💰 Commission deducted from virtual_balance: ${commission_required}")

        # Create the game
        game = Game(
            creator_id=current_user.id,
            creator_type="user",  # User created game
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
        
        # Create transaction for commission freeze
        commission_transaction = Transaction(
            user_id=current_user.id,
            transaction_type=TransactionType.COMMISSION,
            amount=-commission_required,
            currency="USD",
            balance_before=user["virtual_balance"],
            balance_after=user["virtual_balance"] - commission_required,  # ИСПРАВЛЕНО: virtual_balance изменяется
            description=f"Commission frozen for PvP game creation (${commission_required})",
            reference_id=game.id
        )
        await db.transactions.insert_one(commission_transaction.dict())
        
        # Monitor for suspicious betting patterns
        await monitor_transaction_patterns(current_user.id, "BET", total_bet_amount)
        
        return {
            "message": "Game created successfully",
            "game_id": game.id,
            "bet_amount": total_bet_amount,
            "commission_reserved": commission_required,
            "new_balance": user["virtual_balance"] - commission_required,  # ИСПРАВЛЕНО: virtual_balance изменяется
            "debug_info": {
                "original_balance": user["virtual_balance"],
                "original_frozen": user["frozen_balance"],
                "commission_calculated": commission_required,
                "balance_after_commission": user["virtual_balance"] - commission_required,  # ИСПРАВЛЕНО: изменяется
                "frozen_after_commission": user["frozen_balance"] + commission_required,
                "expected_difference": -commission_required,  # ИСПРАВЛЕНО: есть разница в virtual_balance
                "actual_difference": -commission_required     # ИСПРАВЛЕНО: есть разница в virtual_balance
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create game"
        )

async def check_user_concurrent_games(user_id: str) -> bool:
    """Check if user can join another game (no active games as creator or opponent)."""
    try:
        # Only consider truly active statuses: ACTIVE and REVEAL
        # WAITING games don't prevent joining others (users can create and join simultaneously)
        # COMPLETED, CANCELLED, TIMEOUT games are finished and don't block joining
        active_statuses = [GameStatus.ACTIVE, GameStatus.REVEAL]
        
        # Check if user is already in an active game as opponent
        active_as_opponent = await db.games.find_one({
            "opponent_id": user_id,
            "status": {"$in": active_statuses}
        })
        
        # Check if user is already in an active game as creator
        active_as_creator = await db.games.find_one({
            "creator_id": user_id,
            "status": {"$in": active_statuses}
        })
        
        # User can join if they have no truly active games
        can_join = active_as_opponent is None and active_as_creator is None
        
        # Detailed logging for debugging
        if not can_join:
            logger.warning(f"User {user_id} blocked from joining games:")
            if active_as_opponent:
                logger.warning(f"  - Has active game as opponent: {active_as_opponent.get('id')} (status: {active_as_opponent.get('status')})")
            if active_as_creator:
                logger.warning(f"  - Has active game as creator: {active_as_creator.get('id')} (status: {active_as_creator.get('status')})")
        else:
            logger.info(f"User {user_id} can join games - no active games found")
        
        return can_join
        
    except Exception as e:
        logger.error(f"Error checking concurrent games for user {user_id}: {e}")
        # In case of error, be conservative and allow joining
        return True

async def handle_game_timeout(game_id: str):
    """Handle game timeout - return funds and potentially recreate bet."""
    try:
        game = await db.games.find_one({"id": game_id})
        if not game:
            return
            
        game_obj = Game(**game)
        
        # Only handle timeout for REVEAL phase
        if game_obj.status != GameStatus.REVEAL:
            return
            
        # Get both players
        creator = await db.users.find_one({"id": game_obj.creator_id})
        opponent = await db.users.find_one({"id": game_obj.opponent_id})
        
        if not creator or not opponent:
            return
            
        # Return gems to opponent (who joined but didn't reveal)
        for gem_type, quantity in game_obj.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": game_obj.opponent_id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
        # Return commission to opponent
        commission = game_obj.bet_amount * 0.03
        await db.users.update_one(
            {"id": game_obj.opponent_id},
            {
                "$inc": {
                    "virtual_balance": commission,
                    "frozen_balance": -commission
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Recreate bet for creator - change status back to WAITING
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "status": GameStatus.WAITING,
                    "opponent_id": None,
                    "opponent_move": None,
                    "started_at": None,
                    "reveal_deadline": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Game {game_id} timeout handled - bet recreated for creator")
        
    except Exception as e:
        logger.error(f"Error handling game timeout: {e}")

@api_router.get("/games/can-join")
async def can_join_games(current_user: User = Depends(get_current_user)):
    """Check if user can join games and get their current game status."""
    try:
        # Check if user can join games
        can_join = await check_user_concurrent_games(current_user.id)
        
        # Get user's current games for debugging
        active_as_opponent = await db.games.find_one({
            "opponent_id": current_user.id,
            "status": {"$in": [GameStatus.ACTIVE, GameStatus.REVEAL]}
        })
        
        active_as_creator = await db.games.find_one({
            "creator_id": current_user.id,
            "status": {"$in": [GameStatus.ACTIVE, GameStatus.REVEAL]}
        })
        
        # Get waiting games count
        waiting_games_count = await db.games.count_documents({
            "creator_id": current_user.id,
            "status": GameStatus.WAITING
        })
        
        return {
            "can_join_games": can_join,
            "has_active_as_opponent": active_as_opponent is not None,
            "has_active_as_creator": active_as_creator is not None,
            "waiting_games_count": waiting_games_count,
            "active_game_opponent_id": active_as_opponent["id"] if active_as_opponent else None,
            "active_game_creator_id": active_as_creator["id"] if active_as_creator else None
        }
        
    except Exception as e:
        logger.error(f"Error checking can join games for user {current_user.id}: {e}")
        return {
            "can_join_games": True,  # Default to allowing joins on error
            "error": "Failed to check game status"
        }

@api_router.get("/debug/user-games/{user_id}")
async def debug_user_games(user_id: str, current_user: User = Depends(get_current_user)):
    """Debug endpoint to check user's active games."""
    try:
        # Get all games for this user
        games_as_creator = await db.games.find({"creator_id": user_id}).to_list(100)
        games_as_opponent = await db.games.find({"opponent_id": user_id}).to_list(100)
        
        # Filter active games
        active_as_creator = [g for g in games_as_creator if g["status"] in ["ACTIVE", "REVEAL"]]
        active_as_opponent = [g for g in games_as_opponent if g["status"] in ["ACTIVE", "REVEAL"]]
        
        # Filter waiting games
        waiting_as_creator = [g for g in games_as_creator if g["status"] == "WAITING"]
        
        can_join = await check_user_concurrent_games(user_id)
        
        return {
            "user_id": user_id,
            "can_join_games": can_join,
            "active_as_creator": len(active_as_creator),
            "active_as_opponent": len(active_as_opponent),
            "waiting_as_creator": len(waiting_as_creator),
            "active_games_creator": [{"id": g["id"], "status": g["status"], "created_at": g["created_at"]} for g in active_as_creator],
            "active_games_opponent": [{"id": g["id"], "status": g["status"], "created_at": g["created_at"]} for g in active_as_opponent],
            "waiting_games_creator": [{"id": g["id"], "status": g["status"], "created_at": g["created_at"]} for g in waiting_as_creator]
        }
        
    except Exception as e:
        logger.error(f"Error in debug_user_games: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Debug check failed"
        )

@api_router.post("/games/{game_id}/join", response_model=dict)
async def join_game(
    request: Request,
    game_id: str,
    join_data: JoinGameRequest,
    current_user: User = Depends(get_current_user_with_security)
):
    """Join an existing PvP game."""
    logger.info(f"🤝 JOIN_GAME called for user {current_user.id}, game {game_id}")
    try:
        # Check if user can join another game (no active games as opponent)
        can_join = await check_user_concurrent_games(current_user.id)
        if not can_join:
            # Get detailed information about user's active games for better error message
            active_games = []
            
            # Check for active games as opponent
            active_as_opponent = await db.games.find_one({
                "opponent_id": current_user.id,
                "status": {"$in": [GameStatus.ACTIVE, GameStatus.REVEAL]}
            })
            if active_as_opponent:
                active_games.append(f"opponent in game {active_as_opponent['id'][:8]} (status: {active_as_opponent['status']})")
            
            # Check for active games as creator
            active_as_creator = await db.games.find_one({
                "creator_id": current_user.id,
                "status": {"$in": [GameStatus.ACTIVE, GameStatus.REVEAL]}
            })
            if active_as_creator:
                active_games.append(f"creator of game {active_as_creator['id'][:8]} (status: {active_as_creator['status']})")
            
            error_detail = "You cannot join multiple games simultaneously. Please complete your current game first."
            if active_games:
                error_detail += f" Active games: {', '.join(active_games)}"
            
            logger.warning(f"User {current_user.id} blocked from joining game {game_id}: {error_detail}")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        
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
        
        # Check if user has enough gems for THEIR OWN combination (not creator's)
        total_gems_value = 0.0
        
        # Validate user's selected gems combination
        for gem_type, quantity in join_data.gems.items():
            if quantity <= 0:
                continue
                
            # Get gem definition for price
            gem_def = await db.gem_definitions.find_one({"type": gem_type})
            if not gem_def:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid gem type: {gem_type}"
                )
            
            # Check user's inventory for this gem type
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
            
            # Add to total value
            total_gems_value += gem_def["price"] * quantity
        
        # Check if total value matches the bet amount
        if abs(total_gems_value - game_obj.bet_amount) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Gem combination value (${total_gems_value:.2f}) must match bet amount (${game_obj.bet_amount:.2f})"
            )
        
        # Check if user has enough balance for commission
        commission_required = game_obj.bet_amount * 0.03
        user = await db.users.find_one({"id": current_user.id})
        
        # Check if the game creator is a regular bot
        is_regular_bot_game = False
        if game_obj.creator_type == "bot":
            creator_bot = await db.bots.find_one({"id": game_obj.creator_id})
            if creator_bot and creator_bot.get("bot_type") == "REGULAR":
                is_regular_bot_game = True
        
        # For regular bot games, no commission is required
        if not is_regular_bot_game:
            if user["virtual_balance"] < commission_required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient balance for commission. Required: ${commission_required:.2f}"
                )
        else:
            # For regular bot games, commission is set to 0
            commission_required = 0.0
            logger.info(f"🤖 Playing against regular bot - no commission required for user {current_user.id}")
        
        # Freeze user's own selected gems (not creator's gems)
        for gem_type, quantity in join_data.gems.items():
            if quantity > 0:
                await db.user_gems.update_one(
                    {"user_id": current_user.id, "gem_type": gem_type},
                    {
                        "$inc": {"frozen_quantity": quantity},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
        
        # Freeze commission balance only if not playing against regular bot
        if not is_regular_bot_game and commission_required > 0:
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
            logger.info(f"💰 Commission ${commission_required} frozen for user {current_user.id}")
        else:
            logger.info(f"🤖 No commission frozen for regular bot game - user {current_user.id}")
        
        # ATOMIC UPDATE: Try to update game with opponent only if it still has no opponent
        # This prevents race conditions where multiple users try to join the same game
        update_result = await db.games.update_one(
            {
                "id": game_id,
                "opponent_id": None,  # Only update if opponent_id is still None
                "status": "WAITING"   # And status is still WAITING
            },
            {
                "$set": {
                    "opponent_id": current_user.id,
                    "opponent_move": join_data.move,
                    "opponent_gems": join_data.gems,  # Save opponent's gem combination
                    "started_at": datetime.utcnow(),
                    "status": "ACTIVE",  # Mark as active immediately
                    "is_regular_bot_game": is_regular_bot_game  # Mark if this is a regular bot game
                }
            }
        )
        
        # Check if the update was successful
        if update_result.modified_count == 0:
            # The game was already taken by another player or changed state
            # Refund the user's gems and balance
            for gem_type, quantity in join_data.gems.items():
                if quantity > 0:
                    await db.user_gems.update_one(
                        {"user_id": current_user.id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
            
            # Refund balance only if commission was actually charged
            if not is_regular_bot_game and commission_required > 0:
                await db.users.update_one(
                    {"id": current_user.id},
                    {
                        "$set": {
                            "virtual_balance": user["virtual_balance"],  # Restore original balance
                            "frozen_balance": user["frozen_balance"],     # Restore original frozen balance
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is no longer available - another player may have joined it"
            )
        
        # АСИНХРОННОЕ ЗАВЕРШЕНИЕ: Сразу определяем результат игры
        logger.info(f"Determining game result immediately for game {game_id}")
        game_result = await determine_game_winner(game_id)
        
        # Return complete game result (асинхронная система)
        return {
            "success": True,
            "game_id": game_id,
            "status": "COMPLETED",
            "message": "Game completed successfully!",
            "result": game_result["result"],
            "creator_move": game_result["creator_move"],
            "opponent_move": game_result["opponent_move"], 
            "winner_id": game_result["winner_id"],
            "bet_amount": game_result["bet_amount"],
            "commission": game_result["commission"],
            "creator": game_result["creator"],
            "opponent": game_result["opponent"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining game: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error traceback:", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join game: {str(e)}"
        )

@api_router.post("/games/{game_id}/reveal", response_model=dict)
async def reveal_game(
    request: Request,
    game_id: str,
    current_user: User = Depends(get_current_user_with_security)
):
    """Reveal moves and complete the game."""
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
        if game_obj.status != GameStatus.REVEAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in reveal phase"
            )
        
        # Check if user is part of this game
        if current_user.id != game_obj.creator_id and current_user.id != game_obj.opponent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not part of this game"
            )
        
        # Check if reveal deadline has passed
        if game_obj.reveal_deadline and datetime.utcnow() > game_obj.reveal_deadline:
            await handle_game_timeout(game_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time is up. Your move was not made. The bet has been cancelled."
            )
        
        # Complete the game
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "status": GameStatus.ACTIVE,
                    "reveal_deadline": None
                }
            }
        )
        
        # Determine winner
        result = await determine_game_winner(game_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revealing game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reveal game"
        )

@api_router.post("/admin/bots/{bot_id}/reset-bets", response_model=dict)
async def reset_bot_bets(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Сбросить все ставки бота и пересоздать цикл."""
    try:
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        # Отменяем все активные ставки бота
        cancelled_result = await db.games.update_many(
            {"creator_id": bot_id, "status": {"$in": ["WAITING", "ACTIVE"]}},
            {"$set": {
                "status": "CANCELLED",
                "updated_at": datetime.utcnow(),
                "cancel_reason": "Bot bets reset by admin"
            }}
        )
        
        # Сбрасываем статистику текущего цикла
        await db.bots.update_one(
            {"id": bot_id},
            {"$set": {
                "current_cycle_games": 0,
                "current_cycle_wins": 0,
                "current_cycle_losses": 0,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Пересоздаем ставки для бота
        try:
            await generate_bot_cycle_bets(
                bot_id=bot_id,
                cycle_length=bot.get("cycle_games", 12),
                cycle_total_amount=bot.get("cycle_total_amount", 500.0),
                win_percentage=bot.get("win_rate_percent", 60),
                min_bet=bot.get("min_bet_amount", 1.0),
                avg_bet=bot.get("max_bet_amount", 100.0),
                bet_distribution=bot.get("bet_distribution", "medium")
            )
        except Exception as e:
            logger.error(f"Error regenerating bets for bot {bot_id}: {e}")
            # Не блокируем операцию из-за ошибки генерации
        
        # Логирование действия
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="RESET_BOT_BETS",
            target_type="bot",
            target_id=bot_id,
            details={
                "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
                "cancelled_bets": cancelled_result.modified_count
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "success": True,
            "message": f"Ставки бота сброшены и пересозданы",
            "cancelled_bets": cancelled_result.modified_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting bot bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при сбросе ставок бота"
        )

async def timeout_checker_task():
    """Background task to check for game timeouts."""
    while True:
        try:
            current_time = datetime.utcnow()
            
            # Find games in REVEAL phase that have exceeded deadline
            expired_games = await db.games.find({
                "status": GameStatus.REVEAL,
                "reveal_deadline": {"$lt": current_time}
            }).to_list(100)
            
            for game_data in expired_games:
                try:
                    await handle_game_timeout(game_data["id"])
                except Exception as e:
                    logger.error(f"Error handling timeout for game {game_data['id']}: {e}")
            
            # Sleep for 10 seconds before next check
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in timeout checker: {e}")
            await asyncio.sleep(30)  # Wait longer on error

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
        
        # Check if this is a bot game and identify bot types
        is_bot_game = False
        is_regular_bot_game = False
        has_human_bot = False
        
        # Check if creator is a bot
        creator_regular_bot = None
        creator_human_bot = None
        if game_obj.creator_id:
            creator_regular_bot = await db.bots.find_one({"id": game_obj.creator_id})
            creator_human_bot = await db.human_bots.find_one({"id": game_obj.creator_id})
            if creator_regular_bot:
                is_bot_game = True
                is_regular_bot_game = True
            elif creator_human_bot:
                is_bot_game = True
                has_human_bot = True
        
        # Check if opponent is a bot
        opponent_regular_bot = None
        opponent_human_bot = None
        if game_obj.opponent_id:
            opponent_regular_bot = await db.bots.find_one({"id": game_obj.opponent_id})
            opponent_human_bot = await db.human_bots.find_one({"id": game_obj.opponent_id})
            if opponent_regular_bot:
                is_bot_game = True
                if creator_regular_bot:  # Both are regular bots
                    is_regular_bot_game = True
            elif opponent_human_bot:
                is_bot_game = True
                has_human_bot = True
        
        # For Human bot games, apply their outcome logic
        if has_human_bot:
            # Check if we need to apply Human bot outcome override
            human_bot_override = await apply_human_bot_outcome(game_obj)
            if human_bot_override:
                winner_id = human_bot_override["winner_id"]
                result_status = human_bot_override["result_status"]
            else:
                # Apply normal rock-paper-scissors logic
                if not game_obj.creator_move or not game_obj.opponent_move:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Missing move data for Human bot game"
                    )
                winner_id, result_status = determine_rps_winner(game_obj.creator_move, game_obj.opponent_move, game_obj.creator_id, game_obj.opponent_id)
        else:
            # Apply normal rock-paper-scissors logic
            if not game_obj.creator_move or not game_obj.opponent_move:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing move data for regular game"
                )
            winner_id, result_status = determine_rps_winner(game_obj.creator_move, game_obj.opponent_move, game_obj.creator_id, game_obj.opponent_id)
        
        # Verify move hash (commit-reveal) - only for human vs human games
        if not is_bot_game:
            # For human vs human games, strict hash verification is required
            if not game_obj.creator_move_hash or not game_obj.creator_salt:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing hash verification data for human game"
                )
            
            if not verify_move_hash(game_obj.creator_move, game_obj.creator_salt, game_obj.creator_move_hash):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Move verification failed"
                )
        else:
            # For bot games, ensure we have the necessary data
            if not game_obj.creator_move or not game_obj.opponent_move:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Bot game missing move data"
                )
            
            # For bot games, verify hash if available (more lenient)
            if game_obj.creator_move_hash and game_obj.creator_salt:
                if not verify_move_hash(game_obj.creator_move, game_obj.creator_salt, game_obj.creator_move_hash):
                    logger.warning(f"Bot game {game_id} move hash verification failed, but proceeding")
            else:
                logger.info(f"Bot game {game_id} has no hash verification data, proceeding without verification")
        
        # Calculate commission
        # Each player pays 6% commission on their bet amount
        # For regular bot games, no commission is charged
        commission_amount = 0
        if winner_id and not is_regular_bot_game:
            commission_amount = game_obj.bet_amount * 0.03  # 3% from winner only
        
        total_pot = game_obj.bet_amount * 2  # Both players' bets
        
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
        
        # Refresh game object to get latest data
        updated_game = await db.games.find_one({"id": game_id})
        if updated_game:
            game_obj = Game(**updated_game)
        
        # Distribute rewards
        await distribute_game_rewards(game_obj, winner_id, commission_amount)
        
        # Update bot cycle tracking if applicable
        if game_obj.is_bot_game and game_obj.bot_id:
            await update_bot_cycle_tracking(game_obj.bot_id, winner_id == game_obj.bot_id)
        
        # Process human bot game outcome
        if has_human_bot:
            await process_human_bot_game_outcome(game_id, winner_id)
        
        # Get user details for response
        creator = await get_player_info(game_obj.creator_id)
        opponent = await get_player_info(game_obj.opponent_id)
        
        return {
            "game_id": game_id,
            "result": result_status,
            "creator_move": game_obj.creator_move.value,
            "opponent_move": game_obj.opponent_move.value,
            "winner_id": winner_id,
            "creator": creator,
            "opponent": opponent,
            "bet_amount": game_obj.bet_amount,
            "total_pot": total_pot,
            "commission": commission_amount,
            "gems_won": game_obj.bet_gems if winner_id else None
        }
        
    except Exception as e:
        logger.error(f"Error determining game winner for game {game_id}: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error traceback:", exc_info=True)
        
        # Try to get game data for debugging
        try:
            game_debug = await db.games.find_one({"id": game_id})
            if game_debug:
                logger.error(f"Game debug data: status={game_debug.get('status')}, "
                           f"creator_move={game_debug.get('creator_move')}, "
                           f"opponent_move={game_debug.get('opponent_move')}, "
                           f"creator_id={game_debug.get('creator_id')}, "
                           f"opponent_id={game_debug.get('opponent_id')}")
        except Exception as debug_e:
            logger.error(f"Could not fetch game debug data: {debug_e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to determine game winner: {str(e)}"
        )

async def distribute_game_rewards(game: Game, winner_id: str, commission_amount: float):
    """Distribute gems and handle commissions after game completion."""
    try:
        # Check if this is a regular bot game (no commission)
        is_regular_bot_game = getattr(game, 'is_regular_bot_game', False)
        
        # Дополнительная проверка: если один из участников - обычный бот
        if not is_regular_bot_game:
            # Проверяем создателя игры
            creator_bot = await db.bots.find_one({"id": game.creator_id})
            creator_is_regular_bot = creator_bot and creator_bot.get("bot_type") == "REGULAR"
            
            # Проверяем оппонента
            opponent_is_regular_bot = False
            if game.opponent_id:
                opponent_bot = await db.bots.find_one({"id": game.opponent_id})
                opponent_is_regular_bot = opponent_bot and opponent_bot.get("bot_type") == "REGULAR"
            
            # Если хотя бы один из участников - обычный бот, игра без комиссии
            is_regular_bot_game = creator_is_regular_bot or opponent_is_regular_bot
        
        if is_regular_bot_game:
            logger.info(f"💰 REGULAR BOT GAME - No commission will be charged for game {game.id}")
            # Override commission amount to 0 for regular bot games
            commission_amount = 0
            
            # Накопление прибыли для обычных ботов
            await accumulate_bot_profit(game, winner_id)
        
        # Unfreeze gems for both players using their respective gem combinations
        
        # Unfreeze creator's gems
        for gem_type, quantity in game.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": game.creator_id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Unfreeze opponent's gems (use opponent_gems if available, otherwise bet_gems)
        opponent_gems = game.opponent_gems if game.opponent_gems else game.bet_gems
        for gem_type, quantity in opponent_gems.items():
            await db.user_gems.update_one(
                {"user_id": game.opponent_id, "gem_type": gem_type},
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
                if is_regular_bot_game:
                    # For regular bot games, no commission was frozen, so no need to unfreeze
                    new_winner_frozen = winner["frozen_balance"]  # No commission changes
                    new_winner_balance = winner["virtual_balance"]  # No commission deducted
                    
                    logger.info(f"💰 REGULAR BOT GAME - Winner {winner_id} gets full payout, no commission involved")
                else:
                    # Normal human vs human game with commission
                    # ПРАВИЛЬНАЯ ЛОГИКА: Просто списываем комиссию из frozen_balance как плату за игру
                    commission_to_deduct = game.bet_amount * 0.06  # 6% от ставки победителя
                    
                    new_winner_frozen = winner["frozen_balance"] - commission_to_deduct
                    new_winner_balance = winner["virtual_balance"]  # virtual_balance не изменяется
                
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
                
                # Record commission transaction only if commission was charged
                if not is_regular_bot_game and commission_amount > 0:
                    commission_transaction = Transaction(
                        user_id=winner_id,
                        transaction_type=TransactionType.COMMISSION,
                        amount=commission_amount,
                        currency="USD",
                        balance_before=winner["virtual_balance"],
                        balance_after=new_winner_balance,
                        description=f"PvP game commission (6% of ${game.bet_amount} bet)",
                        reference_id=game.id
                    )
                    await db.transactions.insert_one(commission_transaction.dict())
                
                # Record profit entry from bet commission (only if commission was charged)
                if not is_regular_bot_game and commission_amount > 0:
                    profit_entry = ProfitEntry(
                        entry_type="BET_COMMISSION",
                        amount=commission_amount,
                        source_user_id=winner_id,
                        reference_id=game.id,
                        description=f"6% commission from PvP game winner (${game.bet_amount} bet)"
                    )
                    await db.profit_entries.insert_one(profit_entry.dict())
            
            # Check if this is a bot game and record bot revenue
            if game.is_bot_game:
                loser_id = game.opponent_id if winner_id == game.creator_id else game.creator_id
                loser = await db.users.find_one({"id": loser_id})
                
                # If human player lost to bot, record this as bot revenue
                if loser and winner_id != loser_id:
                    bot_revenue = game.bet_amount  # Bot wins the full bet amount
                    
                    profit_entry = ProfitEntry(
                        entry_type="BOT_REVENUE",
                        amount=bot_revenue,
                        source_user_id=loser_id,
                        reference_id=game.id,
                        description=f"Bot victory revenue: ${bot_revenue} from player {loser.get('username', 'Unknown')}"
                    )
                    await db.profit_entries.insert_one(profit_entry.dict())
            
            # Handle commission for loser - ПРАВИЛЬНАЯ ЛОГИКА: просто убираем комиссию как плату за игру
            if not is_regular_bot_game:
                loser_id = game.opponent_id if winner_id == game.creator_id else game.creator_id
                loser = await db.users.find_one({"id": loser_id})
                
                if loser:
                    # Loser is a human player - комиссия просто списывается как плата за игру
                    commission_to_deduct = game.bet_amount * 0.06
                    await db.users.update_one(
                        {"id": loser_id},
                        {
                            "$inc": {
                                "frozen_balance": -commission_to_deduct   # Просто убираем комиссию из frozen_balance
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
            
        else:
            # Draw - return frozen commissions to both players (only if commission was charged)
            if not is_regular_bot_game:
                for player_id in [game.creator_id, game.opponent_id]:
                    player = await db.users.find_one({"id": player_id})
                    if player:  # Only process human players
                        commission_to_return = game.bet_amount * 0.06
                        
                        # ПРАВИЛЬНАЯ ЛОГИКА: При ничьей возвращаем комиссию из frozen_balance в virtual_balance
                        await db.users.update_one(
                            {"id": player_id},
                            {
                                "$inc": {
                                    "virtual_balance": commission_to_return,    # Возвращаем в virtual_balance
                                    "frozen_balance": -commission_to_return     # Убираем из frozen_balance
                                },
                                "$set": {"updated_at": datetime.utcnow()}
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
        
        # Автоматическое создание новой ставки для бота при принятии существующей
        # await maintain_bot_active_bets(game)  # УДАЛЕНО - заменено на новую систему
            
    except Exception as e:
        logger.error(f"Error distributing game rewards: {e}")
        raise

# ==============================================================================
# НОВАЯ СИСТЕМА ОБЫЧНЫХ БОТОВ
# ==============================================================================

class RegularBotSystem:
    """Единая система управления обычными ботами с централизованными проверками лимитов."""
    
    def __init__(self):
        self.db = db
        self.logger = logger
    
    # ==========================================================================
    # МОДЕЛЬ ДАННЫХ ОБЫЧНОГО БОТА
    # ==========================================================================
    
    class RegularBotData(BaseModel):
        """Модель данных для обычного бота."""
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        name: Optional[str] = None
        bot_type: str = "REGULAR"
        is_active: bool = True
        
        # Настройки ставок
        min_bet_amount: float = 1.0
        max_bet_amount: float = 100.0
        win_rate: float = 0.55  # 55%
        
        # Циклы и лимиты
        cycle_games: int = 12
        current_cycle_games: int = 0
        current_cycle_wins: int = 0
        current_cycle_gem_value_won: float = 0.0
        current_cycle_gem_value_total: float = 0.0
        current_limit: int = 12  # Индивидуальный лимит активных ставок
        
        # Поведенческие настройки
        creation_mode: str = "queue-based"  # "always-first", "queue-based", "after-all"
        priority_order: int = 50  # 1-100
        pause_between_games: int = 5  # секунды
        
        # Стратегии прибыли
        profit_strategy: str = "balanced"  # "start-positive", "balanced", "start-negative"
        
        # Временные метки
        last_game_time: Optional[datetime] = None
        last_bet_time: Optional[datetime] = None
        created_at: datetime = Field(default_factory=datetime.utcnow)
        updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # ==========================================================================
    # ГЛОБАЛЬНЫЕ НАСТРОЙКИ
    # ==========================================================================
    
    async def get_global_settings(self):
        """Получение глобальных настроек системы ботов."""
        settings = await self.db.bot_settings.find_one({"id": "bot_settings"})
        if not settings:
            # Создаем дефолтные настройки если их нет
            default_settings = {
                "id": "bot_settings",
                "max_active_bets_regular": 50,
                "max_active_bets_human": 30,
                "auto_queue_activation": True,
                "priority_system_enabled": True,
                "default_pause_between_games": 5,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.db.bot_settings.insert_one(default_settings)
            return default_settings
        return settings
    
    # ==========================================================================
    # ПРОВЕРКА ЛИМИТОВ
    # ==========================================================================
    
    async def check_global_limits(self, bot_type: str = "REGULAR"):
        """Проверка глобальных лимитов системы."""
        settings = await self.get_global_settings()
        
        if bot_type == "REGULAR":
            max_limit = settings.get("max_active_bets_regular", 50)
            current_bets = await self.db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "REGULAR"},
                    {"metadata.bot_type": "REGULAR"}
                ]
            })
        else:  # HUMAN
            max_limit = settings.get("max_active_bets_human", 30)
            current_bets = await self.db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "HUMAN"},
                    {"metadata.bot_type": "HUMAN"}
                ]
            })
        
        return {
            "passed": current_bets < max_limit,
            "current": current_bets,
            "max": max_limit,
            "reason": f"Global limit reached: {current_bets}/{max_limit}" if current_bets >= max_limit else None
        }
    
    async def check_individual_limits(self, bot_id: str):
        """Проверка индивидуальных лимитов бота."""
        bot = await self.db.bots.find_one({"id": bot_id})
        if not bot:
            return {"passed": False, "reason": "Bot not found"}
        
        individual_limit = bot.get("current_limit") or bot.get("cycle_games", 12)
        if individual_limit is None:
            individual_limit = 12  # fallback для старых ботов
        
        current_bets = await self.db.games.count_documents({
            "creator_id": bot_id,
            "status": "WAITING"
        })
        
        return {
            "passed": current_bets < individual_limit,
            "current": current_bets,
            "max": individual_limit,
            "reason": f"Individual limit reached: {current_bets}/{individual_limit}" if current_bets >= individual_limit else None
        }
    
    async def check_timing_constraints(self, bot_id: str):
        """Проверка временных ограничений."""
        bot = await self.db.bots.find_one({"id": bot_id})
        if not bot:
            return {"passed": False, "reason": "Bot not found"}
        
        last_bet_time = bot.get("last_bet_time")
        if last_bet_time:
            pause_between_games = bot.get("pause_between_games", 5)
            if pause_between_games is None:
                pause_between_games = 5  # fallback для старых ботов
            
            time_since_last = (datetime.utcnow() - last_bet_time).total_seconds()
            
            if time_since_last < pause_between_games:
                return {
                    "passed": False, 
                    "reason": f"Timing constraint: {time_since_last:.1f}s < {pause_between_games}s"
                }
        
        return {"passed": True, "reason": None}
    
    async def validate_bet_creation(self, bot_id: str):
        """Полная валидация перед созданием ставки."""
        # Проверка глобальных лимитов
        global_check = await self.check_global_limits("REGULAR")
        if not global_check["passed"]:
            return global_check
        
        # Проверка индивидуальных лимитов
        individual_check = await self.check_individual_limits(bot_id)
        if not individual_check["passed"]:
            return individual_check
        
        # Проверка временных ограничений
        timing_check = await self.check_timing_constraints(bot_id)
        if not timing_check["passed"]:
            return timing_check
        
        return {"passed": True, "reason": None}
    
    # ==========================================================================
    # СТРАТЕГИИ ПРИБЫЛИ И ПРИНЯТИЕ РЕШЕНИЙ
    # ==========================================================================
    
    async def calculate_win_need(self, bot_id: str):
        """Расчет необходимости победы на основе стратегии прибыли."""
        bot = await self.db.bots.find_one({"id": bot_id})
        if not bot:
            return {"should_win": False, "reason": "Bot not found"}
        
        # Получаем статистику текущего цикла
        cycle_stats = {
            "current_games": bot.get("current_cycle_games", 0),
            "total_games": bot.get("cycle_games", 12),
            "won_value": bot.get("current_cycle_gem_value_won", 0.0),
            "total_value": bot.get("current_cycle_gem_value_total", 0.0),
            "target_win_rate": bot.get("win_rate", 0.55)
        }
        
        # Текущий процент по стоимости
        current_win_rate = cycle_stats["won_value"] / max(cycle_stats["total_value"], 1) if cycle_stats["total_value"] > 0 else 0
        
        # Позиция в цикле (от 0 до 1)
        cycle_position = cycle_stats["current_games"] / cycle_stats["total_games"]
        
        # Расчет целевого процента на основе стратегии
        target_rate = await self.get_target_rate_by_strategy(
            bot.get("profit_strategy", "balanced"),
            cycle_position,
            cycle_stats["target_win_rate"]
        )
        
        # Принятие решения
        should_win = current_win_rate < target_rate
        
        self.logger.info(f"Bot {bot_id} win decision: current={current_win_rate:.2f}, target={target_rate:.2f}, decision={'WIN' if should_win else 'LOSE'}")
        
        return {
            "should_win": should_win,
            "current_win_rate": current_win_rate,
            "target_rate": target_rate,
            "cycle_position": cycle_position,
            "strategy": bot.get("profit_strategy", "balanced")
        }
    
    async def get_target_rate_by_strategy(self, strategy: str, cycle_position: float, base_rate: float):
        """Получение целевого процента на основе стратегии прибыли."""
        if strategy == "start-positive":
            # В начале цикла высокий процент, к концу - низкий
            if cycle_position < 0.33:  # Первая треть
                return base_rate + 0.15  # +15%
            elif cycle_position < 0.66:  # Вторая треть
                return base_rate
            else:  # Последняя треть
                return base_rate - 0.15  # -15%
        
        elif strategy == "start-negative":
            # В начале цикла низкий процент, к концу - высокий
            if cycle_position < 0.33:  # Первая треть
                return base_rate - 0.15  # -15%
            elif cycle_position < 0.66:  # Вторая треть
                return base_rate
            else:  # Последняя треть
                return base_rate + 0.15  # +15%
        
        else:  # balanced
            # Равномерное распределение
            return base_rate
    
    async def determine_bot_move(self, bot_id: str, player_move: str, bet_amount: float):
        """Определение хода бота с учетом логики подстройки."""
        win_decision = await self.calculate_win_need(bot_id)
        
        if win_decision["should_win"]:
            # Выбираем выигрышный ход
            if player_move == "ROCK":
                bot_move = "PAPER"
            elif player_move == "PAPER":
                bot_move = "SCISSORS"
            else:  # SCISSORS
                bot_move = "ROCK"
            result = "WIN"
        else:
            # Выбираем проигрышный ход
            if player_move == "ROCK":
                bot_move = "SCISSORS"
            elif player_move == "PAPER":
                bot_move = "ROCK"
            else:  # SCISSORS
                bot_move = "PAPER"
            result = "LOSE"
        
        # Логируем решение для админов
        await self.log_bot_decision(bot_id, {
            "player_move": player_move,
            "bot_move": bot_move,
            "decision": result,
            "bet_amount": bet_amount,
            "win_decision_data": win_decision
        })
        
        return {
            "move": bot_move,
            "expected_result": result,
            "decision_data": win_decision
        }
    
    # ==========================================================================
    # СОЗДАНИЕ СТАВОК И УПРАВЛЕНИЕ ЦИКЛАМИ
    # ==========================================================================
    
    async def create_bot_bet_with_validation(self, bot_id: str):
        """Единственная функция для создания ставки бота с полной валидацией."""
        try:
            # 1. Полная валидация
            validation = await self.validate_bet_creation(bot_id)
            if not validation["passed"]:
                self.logger.info(f"🚫 Bot {bot_id} bet creation blocked: {validation['reason']}")
                return {"success": False, "reason": validation["reason"]}
            
            # 2. Получение данных бота
            bot = await self.db.bots.find_one({"id": bot_id})
            if not bot:
                return {"success": False, "reason": "Bot not found"}
            
            # 3. Генерация параметров ставки
            bet_params = await self.generate_bet_parameters(bot)
            
            # 4. Создание Commit-Reveal данных
            initial_move = random.choice(["ROCK", "PAPER", "SCISSORS"])
            salt = secrets.token_hex(32)
            move_hash = hashlib.sha256(f"{initial_move}{salt}".encode()).hexdigest()
            
            # 5. Создание игры
            game = Game(
                id=str(uuid.uuid4()),
                creator_id=bot_id,
                creator_type="bot",
                creator_move_hash=move_hash,
                creator_salt=salt,
                bet_amount=bet_params["total_value"],
                bet_gems=bet_params["bet_gems"],
                status=GameStatus.WAITING,
                is_bot_game=True,
                bot_type="REGULAR",
                metadata={
                    "initial_move": initial_move,
                    "gem_based_bet": True,
                    "auto_created": True,
                    "bot_strategy": bot.get("profit_strategy", "balanced")
                }
            )
            
            # 6. Сохранение в базу данных
            await self.db.games.insert_one(game.dict())
            
            # 7. Обновление статистики бота
            await self.update_bot_after_bet_creation(bot_id, bet_params["total_value"])
            
            # 8. Логирование
            await self.log_bot_action(bot_id, "BET_CREATED", {
                "game_id": game.id,
                "bet_amount": bet_params["total_value"],
                "gems": bet_params["bet_gems"],
                "initial_move": initial_move
            })
            
            self.logger.info(f"✅ Bot {bot_id} created bet {game.id} for ${bet_params['total_value']}")
            
            return {
                "success": True,
                "game_id": game.id,
                "bet_amount": bet_params["total_value"],
                "gems": bet_params["bet_gems"]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error creating bot bet: {e}")
            return {"success": False, "reason": str(e)}
    
    async def generate_bet_parameters(self, bot: dict):
        """Генерация параметров ставки на основе настроек бота."""
        # Диапазон сумм ставки
        min_bet = bot.get("min_bet_amount", 1.0)
        max_bet = bot.get("max_bet_amount", 100.0)
        
        # Генерируем комбинацию гемов сначала, потом рассчитываем сумму
        gem_combination, actual_bet_amount = await self.generate_gem_combination_and_amount(min_bet, max_bet)
        
        return {
            "bet_amount": actual_bet_amount,
            "bet_gems": gem_combination,
            "total_value": actual_bet_amount  # Сумма всегда точная по гемам
        }
    
    async def generate_gem_combination_and_amount(self, min_bet: float, max_bet: float):
        """Generate gem combination first, then calculate exact bet amount."""
        gem_values = {
            'Ruby': 1, 'Amber': 2, 'Topaz': 5, 'Emerald': 10,
            'Aquamarine': 25, 'Sapphire': 50, 'Magic': 100
        }
        
        gem_types = list(gem_values.keys())
        attempts = 0
        max_attempts = 50
        
        while attempts < max_attempts:
            combination = {}
            
            # Random selection of gem types (1-4 types)
            selected_types = random.sample(gem_types, random.randint(1, 4))
            
            for gem_type in selected_types:
                # Random quantity (1-5 gems per type)
                max_quantity = 5 if gem_type in ['Ruby', 'Amber'] else 3
                quantity = random.randint(1, max_quantity)
                combination[gem_type] = quantity
            
            # Calculate total value
            total_value = sum(gem_values[gem_type] * quantity for gem_type, quantity in combination.items())
            
            # Check if it's within the bet range
            if min_bet <= total_value <= max_bet:
                return combination, float(total_value)
            
            attempts += 1
        
        # Fallback: generate simple combination within range
        target_amount = random.uniform(min_bet, max_bet)
        target_int = int(target_amount)
        combination = {}
        remaining = target_int
        
        # Use efficient algorithm as fallback
        gem_types_desc = ["Magic", "Sapphire", "Aquamarine", "Emerald", "Topaz", "Amber", "Ruby"]
        
        for gem_type in gem_types_desc:
            if remaining <= 0:
                break
                
            gem_value = gem_values[gem_type]
            if remaining >= gem_value:
                quantity = remaining // gem_value
                # Limit quantity to make it realistic
                max_quantity = min(quantity, 3) if gem_type in ["Magic", "Sapphire"] else min(quantity, 5)
                if max_quantity > 0:
                    combination[gem_type] = max_quantity
                    remaining -= max_quantity * gem_value
        
        # If there's remaining value, add Ruby gems
        if remaining > 0:
            combination["Ruby"] = combination.get("Ruby", 0) + remaining
        
        # Calculate final amount
        final_amount = sum(gem_values[gem_type] * quantity for gem_type, quantity in combination.items())
        return combination, float(final_amount)
    
    async def generate_gem_combination(self, target_amount: float):
        """Генерация комбинации гемов для заданной суммы."""
        gem_values = {
            'Ruby': 1, 'Amber': 2, 'Topaz': 5, 'Emerald': 10,
            'Aquamarine': 25, 'Sapphire': 50, 'Magic': 100
        }
        
        gem_types = list(gem_values.keys())
        bet_gems = {}
        remaining_amount = target_amount
        
        # Распределяем ставку по гемам
        for i, gem_type in enumerate(gem_types):
            if remaining_amount <= 0:
                break
                
            gem_price = gem_values[gem_type]
            max_quantity = int(remaining_amount / gem_price)
            
            if max_quantity > 0:
                if i == len(gem_types) - 1:  # Последний гем
                    quantity = max_quantity
                else:
                    quantity = random.randint(0, min(max_quantity, 3))
                
                if quantity > 0:
                    bet_gems[gem_type] = quantity
                    remaining_amount -= quantity * gem_price
        
        return bet_gems
    
    def calculate_total_gem_value(self, gem_combination: dict):
        """Расчет общей стоимости комбинации гемов."""
        gem_values = {
            'Ruby': 1, 'Amber': 2, 'Topaz': 5, 'Emerald': 10,
            'Aquamarine': 25, 'Sapphire': 50, 'Magic': 100
        }
        
        total_value = 0
        for gem_type, quantity in gem_combination.items():
            total_value += gem_values.get(gem_type, 0) * quantity
        
        return total_value
    
    # ==========================================================================
    # ОБНОВЛЕНИЕ СТАТИСТИКИ И ЛОГИРОВАНИЕ
    # ==========================================================================
    
    async def update_bot_after_bet_creation(self, bot_id: str, bet_amount: float):
        """Обновление статистики бота после создания ставки."""
        current_time = datetime.utcnow()
        
        await self.db.bots.update_one(
            {"id": bot_id},
            {
                "$set": {
                    "last_bet_time": current_time,
                    "updated_at": current_time
                },
                "$inc": {
                    "current_cycle_games": 1,
                    "current_cycle_gem_value_total": bet_amount
                }
            }
        )
    
    async def update_bot_after_game_result(self, bot_id: str, won: bool, bet_amount: float):
        """Обновление статистики бота после результата игры."""
        current_time = datetime.utcnow()
        
        update_data = {
            "$set": {
                "last_game_time": current_time,
                "updated_at": current_time
            }
        }
        
        if won:
            update_data["$inc"] = {
                "current_cycle_wins": 1,
                "current_cycle_gem_value_won": bet_amount
            }
        
        await self.db.bots.update_one({"id": bot_id}, update_data)
        
        # Проверяем завершение цикла
        await self.check_cycle_completion(bot_id)
    
    async def check_cycle_completion(self, bot_id: str):
        """Проверка и обработка завершения цикла."""
        bot = await self.db.bots.find_one({"id": bot_id})
        if not bot:
            return
        
        current_games = bot.get("current_cycle_games", 0)
        cycle_games = bot.get("cycle_games", 12)
        
        if current_games >= cycle_games:
            # Цикл завершен
            cycle_stats = {
                "total_games": current_games,
                "wins": bot.get("current_cycle_wins", 0),
                "total_value": bot.get("current_cycle_gem_value_total", 0.0),
                "won_value": bot.get("current_cycle_gem_value_won", 0.0),
                "profit": bot.get("current_cycle_gem_value_won", 0.0) - bot.get("current_cycle_gem_value_total", 0.0),
                "completed_at": datetime.utcnow()
            }
            
            # Логируем завершение цикла
            await self.log_bot_action(bot_id, "CYCLE_COMPLETED", cycle_stats)
            
            # Сбрасываем статистику цикла
            await self.db.bots.update_one(
                {"id": bot_id},
                {
                    "$set": {
                        "current_cycle_games": 0,
                        "current_cycle_wins": 0,
                        "current_cycle_gem_value_won": 0.0,
                        "current_cycle_gem_value_total": 0.0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            self.logger.info(f"🔄 Bot {bot_id} completed cycle: {cycle_stats}")
    
    async def log_bot_action(self, bot_id: str, action: str, details: dict):
        """Логирование действий бота."""
        log_entry = {
            "bot_id": bot_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow()
        }
        
        await self.db.bot_action_logs.insert_one(log_entry)
    
    async def log_bot_decision(self, bot_id: str, decision_data: dict):
        """Специальное логирование решений бота для админов."""
        log_entry = {
            "bot_id": bot_id,
            "action": "DECISION_MADE",
            "details": decision_data,
            "timestamp": datetime.utcnow()
        }
        
        await self.db.bot_decision_logs.insert_one(log_entry)
    
    # ==========================================================================
    # ФОНОВЫЕ ЗАДАЧИ
    # ==========================================================================
    
    async def process_bots_automation(self):
        """Основная функция фоновой автоматизации ботов."""
        try:
            # Получаем всех активных ботов
            active_bots = await self.db.bots.find({"is_active": True, "bot_type": "REGULAR"}).to_list(1000)
            
            if not active_bots:
                return
            
            # Сортируем по приоритету
            sorted_bots = await self.sort_bots_by_priority(active_bots)
            
            # Обрабатываем каждого бота
            for bot in sorted_bots:
                try:
                    result = await self.create_bot_bet_with_validation(bot["id"])
                    if result["success"]:
                        self.logger.info(f"✅ Bot {bot['id']} created bet successfully")
                    else:
                        self.logger.debug(f"⏭️ Bot {bot['id']} skipped: {result['reason']}")
                except Exception as e:
                    self.logger.error(f"❌ Error processing bot {bot['id']}: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error in bots automation: {e}")
    
    async def sort_bots_by_priority(self, bots: list):
        """Сортировка ботов по приоритету и режиму создания."""
        always_first = []
        queue_based = []
        after_all = []
        
        for bot in bots:
            creation_mode = bot.get("creation_mode", "queue-based")
            
            if creation_mode == "always-first":
                always_first.append(bot)
            elif creation_mode == "after-all":
                after_all.append(bot)
            else:  # queue-based
                queue_based.append(bot)
        
        # Сортировка queue-based по приоритету
        queue_based.sort(key=lambda x: x.get("priority_order", 50))
        
        # Финальный порядок
        return always_first + queue_based + after_all


# Создаем глобальный экземпляр системы
regular_bot_system = RegularBotSystem()

# ==============================================================================
# НОВАЯ ФОНОВАЯ ЗАДАЧА ДЛЯ АВТОМАТИЗАЦИИ БОТОВ
# ==============================================================================

async def new_bot_automation_task():
    """Новая фоновая задача для автоматизации обычных ботов."""
    logger.info("🤖 Starting new bot automation system...")
    
    while True:
        try:
            # Обрабатываем ботов через новую систему
            await regular_bot_system.process_bots_automation()
            
            # Пауза между циклами (5 секунд согласно спецификации)
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ Error in new bot automation: {e}")
            # Пауза при ошибке (10 секунд согласно спецификации)
            await asyncio.sleep(10)

# СТАРЫЕ ФУНКЦИИ - ПОМЕЧЕНЫ ДЛЯ УДАЛЕНИЯ

async def maintain_bot_active_bets(game: Game):
    """Поддерживает количество активных ставок бота равным параметру cycle_games."""
    try:
        # Определяем, какой бот участвует в игре
        bot_id = None
        
        # Проверяем создателя игры
        creator_bot = await db.bots.find_one({"id": game.creator_id})
        if creator_bot and creator_bot.get("bot_type") == "REGULAR":
            bot_id = game.creator_id
        
        # Проверяем оппонента
        if not bot_id and game.opponent_id:
            opponent_bot = await db.bots.find_one({"id": game.opponent_id})
            if opponent_bot and opponent_bot.get("bot_type") == "REGULAR":
                bot_id = game.opponent_id
        
        if not bot_id:
            return  # Не бот или Human бот, ничего не делаем
        
        # Получаем бота
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            return
        
        bot_obj = Bot(**bot)
        
        # ============ ПРОВЕРКА ГЛОБАЛЬНЫХ ЛИМИТОВ ============
        # Получаем глобальные настройки
        bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_active_bets_regular = bot_settings.get("max_active_bets_regular", 50) if bot_settings else 50
        max_active_bets_human = bot_settings.get("max_active_bets_human", 30) if bot_settings else 30
        
        # Определяем тип бота
        bot_type = bot.get("bot_type", "REGULAR")
        
        # Подсчитываем текущие активные ставки по типу бота
        if bot_type == "REGULAR":
            current_global_bets = await db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "REGULAR"},
                    {"metadata.bot_type": "REGULAR"}
                ]
            })
            max_limit = max_active_bets_regular
        else:  # HUMAN
            current_global_bets = await db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "HUMAN"},
                    {"metadata.bot_type": "HUMAN"}
                ]
            })
            max_limit = max_active_bets_human
        
        # Проверяем глобальный лимит
        if current_global_bets >= max_limit:
            logger.info(f"🚫 Global limit reached, skipping bet creation for {bot_type} bot {bot_id}: {current_global_bets}/{max_limit}")
            return
        
        # Получаем текущее количество активных ставок конкретного бота
        current_active_bets = await db.games.count_documents({
            "creator_id": bot_id,
            "status": "WAITING"
        })
        
        # Получаем целевое количество активных ставок (cycle_games)
        target_active_bets = bot_obj.cycle_games
        
        # Проверяем индивидуальный лимит бота
        individual_limit = bot.get("current_limit") or bot.get("cycle_games", 12)
        if current_active_bets >= individual_limit:
            logger.info(f"🚫 Individual limit reached for bot {bot_id}: {current_active_bets}/{individual_limit}")
            return
        
        # Если активных ставок меньше целевого количества, создаём новые
        needed_bets = min(target_active_bets - current_active_bets, individual_limit - current_active_bets)
        
        if needed_bets > 0:
            logger.info(f"🎯 Bot {bot_id} needs {needed_bets} new bets to maintain {target_active_bets} active bets")
            
            for _ in range(needed_bets):
                try:
                    await bot_create_game_automatically(bot_obj)
                    logger.info(f"✅ Created new bet for bot {bot_id}")
                except Exception as e:
                    logger.error(f"Failed to create new bet for bot {bot_id}: {e}")
            
            # Обновляем количество активных ставок в базе данных
            new_active_count = await db.games.count_documents({
                "creator_id": bot_id,
                "status": "WAITING"
            })
            
            await db.bots.update_one(
                {"id": bot_id},
                {
                    "$set": {
                        "active_bets": new_active_count,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"🎯 Bot {bot_id} now has {new_active_count} active bets (target: {target_active_bets})")
        
    except Exception as e:
        logger.error(f"Error maintaining bot active bets: {e}")

async def accumulate_bot_profit(game: Game, winner_id: str):
    """Накопление прибыли от обычных ботов в защищённом контейнере."""
    try:
        # Определяем, какой бот участвует в игре
        bot_id = None
        bot_won = False
        
        # Проверяем создателя игры
        creator_bot = await db.bots.find_one({"id": game.creator_id})
        if creator_bot and creator_bot.get("bot_type") == "REGULAR":
            bot_id = game.creator_id
            bot_won = (winner_id == game.creator_id)
        
        # Проверяем оппонента
        if game.opponent_id:
            opponent_bot = await db.bots.find_one({"id": game.opponent_id})
            if opponent_bot and opponent_bot.get("bot_type") == "REGULAR":
                bot_id = game.opponent_id
                bot_won = (winner_id == game.opponent_id)
        
        if not bot_id:
            logger.warning(f"No regular bot found in game {game.id}")
            return
        
        # Получаем или создаём аккумулятор прибыли для текущего цикла
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            logger.error(f"Bot {bot_id} not found")
            return
        
        cycle_length = bot.get("cycle_length", 12)  # По умолчанию 12 игр
        
        # Ищем активный аккумулятор прибыли для этого бота
        accumulator = await db.bot_profit_accumulators.find_one({
            "bot_id": bot_id,
            "is_cycle_completed": False
        })
        
        if not accumulator:
            # Создаём новый аккумулятор для нового цикла
            cycle_number = 1
            # Найдём последний цикл для определения номера
            last_accumulator = await db.bot_profit_accumulators.find_one(
                {"bot_id": bot_id},
                sort=[("cycle_number", -1)]
            )
            if last_accumulator:
                cycle_number = last_accumulator["cycle_number"] + 1
            
            accumulator = BotProfitAccumulator(
                bot_id=bot_id,
                cycle_number=cycle_number,
                total_spent=0,
                total_earned=0,
                games_completed=0,
                games_won=0,
                cycle_start_date=datetime.utcnow()
            )
            await db.bot_profit_accumulators.insert_one(accumulator.dict())
        else:
            accumulator = BotProfitAccumulator(**accumulator)
        
        # Обновляем данные аккумулятора
        bet_amount = game.bet_amount
        
        # Бот всегда тратит сумму ставки (независимо от результата)
        new_total_spent = accumulator.total_spent + bet_amount
        
        # Если бот выиграл, добавляем к заработанному
        new_total_earned = accumulator.total_earned
        if bot_won:
            new_total_earned += bet_amount * 2  # Бот получает свою ставку + ставку противника
            new_games_won = accumulator.games_won + 1
        else:
            new_games_won = accumulator.games_won
        
        new_games_completed = accumulator.games_completed + 1
        
        # Обновляем аккумулятор
        await db.bot_profit_accumulators.update_one(
            {"id": accumulator.id},
            {
                "$set": {
                    "total_spent": new_total_spent,
                    "total_earned": new_total_earned,
                    "games_completed": new_games_completed,
                    "games_won": new_games_won,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"🤖 Bot {bot_id} cycle update: {new_games_completed}/{cycle_length} games, "
                   f"spent: ${new_total_spent}, earned: ${new_total_earned}")
        
        # Проверяем, завершён ли цикл
        if new_games_completed >= cycle_length:
            await complete_bot_cycle(accumulator.id, new_total_spent, new_total_earned, bot_id)
        
    except Exception as e:
        logger.error(f"Error accumulating bot profit: {e}")

async def complete_bot_cycle(accumulator_id: str, total_spent: float, total_earned: float, bot_id: str):
    """Завершение цикла бота и перевод излишка в прибыль."""
    try:
        # Рассчитываем прибыль: заработанное - потраченное
        profit = total_earned - total_spent
        
        # Обновляем аккумулятор как завершённый
        await db.bot_profit_accumulators.update_one(
            {"id": accumulator_id},
            {
                "$set": {
                    "is_cycle_completed": True,
                    "cycle_end_date": datetime.utcnow(),
                    "profit_transferred": profit,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Если есть прибыль, переводим её в "Доход от ботов"
        if profit > 0:
            bot = await db.bots.find_one({"id": bot_id})
            bot_name = bot.get("name", "Unknown Bot") if bot else "Unknown Bot"
            
            profit_entry = ProfitEntry(
                entry_type="BOT_REVENUE",
                amount=profit,
                source_user_id=bot_id,
                description=f"Прибыль от цикла бота {bot_name}: ${profit:.2f} (заработано: ${total_earned:.2f}, потрачено: ${total_spent:.2f})",
                reference_id=accumulator_id
            )
            await db.profit_entries.insert_one(profit_entry.dict())
            
            logger.info(f"🎯 Bot {bot_id} cycle completed: profit ${profit:.2f} transferred to BOT_REVENUE")
        else:
            logger.info(f"🎯 Bot {bot_id} cycle completed: no profit (deficit: ${abs(profit):.2f})")
        
        # Сбрасываем счётчики бота для нового цикла
        await db.bots.update_one(
            {"id": bot_id},
            {
                "$set": {
                    "current_cycle_games": 0,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error completing bot cycle: {e}")

@api_router.get("/admin/bots/profit-accumulators", response_model=List[dict])
async def get_bot_profit_accumulators(
    page: int = 1,
    limit: int = 20,
    bot_id: Optional[str] = None,
    is_completed: Optional[bool] = None,
    current_user: User = Depends(get_current_admin)
):
    """Получить накопители прибыли ботов (только для админа)."""
    try:
        # Построение фильтра
        filter_query = {}
        
        if bot_id:
            filter_query["bot_id"] = bot_id
        
        if is_completed is not None:
            filter_query["is_cycle_completed"] = is_completed
        
        # Подсчёт общего количества
        total_count = await db.bot_profit_accumulators.count_documents(filter_query)
        
        # Получение данных с пагинацией
        skip = (page - 1) * limit
        accumulators = await db.bot_profit_accumulators.find(filter_query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Обогащение данных информацией о ботах
        result = []
        for acc in accumulators:
            bot = await db.bots.find_one({"id": acc["bot_id"]})
            bot_name = bot.get("name", "Unknown Bot") if bot else "Unknown Bot"
            
            acc_dict = dict(acc)
            acc_dict["bot_name"] = bot_name
            acc_dict["profit"] = acc["total_earned"] - acc["total_spent"]
            acc_dict["win_rate"] = (acc["games_won"] / acc["games_completed"]) * 100 if acc["games_completed"] > 0 else 0
            
            result.append(acc_dict)
        
        return {
            "accumulators": result,
            "pagination": {
                "total_count": total_count,
                "current_page": page,
                "total_pages": (total_count + limit - 1) // limit,
                "items_per_page": limit,
                "has_next": skip + limit < total_count,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting bot profit accumulators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot profit accumulators"
        )

@api_router.post("/admin/bots/{bot_id}/force-complete-cycle-v2", response_model=dict)
async def force_complete_bot_cycle_v2(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Принудительно завершить текущий цикл бота (только для админа)."""
    try:
        # Найти активный аккумулятор
        accumulator = await db.bot_profit_accumulators.find_one({
            "bot_id": bot_id,
            "is_cycle_completed": False
        })
        
        if not accumulator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active cycle found for this bot"
            )
        
        # Завершить цикл
        await complete_bot_cycle(
            accumulator["id"],
            accumulator["total_spent"],
            accumulator["total_earned"],
            bot_id
        )
        
        return {
            "message": f"Bot cycle completed successfully",
            "bot_id": bot_id,
            "cycle_number": accumulator["cycle_number"],
            "total_spent": accumulator["total_spent"],
            "total_earned": accumulator["total_earned"],
            "profit": accumulator["total_earned"] - accumulator["total_spent"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error force completing bot cycle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete bot cycle"
        )

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
            # Get creator info (user or human bot)
            creator = await db.users.find_one({"id": game["creator_id"]})
            if not creator:
                # Try to find as human bot
                human_bot = await db.human_bots.find_one({"id": game["creator_id"]})
                if human_bot:
                    creator = {
                        "id": human_bot["id"],
                        "username": human_bot["name"],
                        "gender": "male"  # Default gender for human bots
                    }
                else:
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
                    "gender": creator.get("gender", "male")
                },
                "bet_amount": game["bet_amount"],
                "bet_gems": game["bet_gems"],
                "created_at": game["created_at"],
                "time_remaining_hours": time_remaining.total_seconds() / 3600,
                "is_human_bot": game.get("creator_type") == "human_bot"  # Add flag for identification
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

@api_router.delete("/games/{game_id}/cancel", response_model=CancelGameResponse)
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
        
        # Return frozen commission - ПРАВИЛЬНАЯ ЛОГИКА: возвращаем из frozen_balance в virtual_balance
        commission_to_return = game_obj.bet_amount * 0.06
        
        # ПРАВИЛЬНАЯ ЛОГИКА: При отмене игры комиссия возвращается из frozen_balance в virtual_balance
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$inc": {
                    "virtual_balance": commission_to_return,    # Возвращаем в virtual_balance
                    "frozen_balance": -commission_to_return     # Убираем из frozen_balance
                },
                "$set": {"updated_at": datetime.utcnow()}
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
        
        return CancelGameResponse(
            success=True,
            message="Game cancelled successfully",
            gems_returned=game_obj.bet_gems,
            commission_returned=commission_to_return
        )
        
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
            creator_commission = game_obj.bet_amount * 0.03
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
                opponent_commission = game_obj.bet_amount * 0.03
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
        """Calculate bot's move based on its type and settings with gem value consideration."""
        import random
        
        if bot.bot_type == BotType.REGULAR:
            # Regular bot: Enhanced random selection with gem value consideration
            moves = [GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
            
            # If we have game context, consider gem value for decision making
            if game_context and game_context.get('total_gems_value', 0) > 0:
                total_value = game_context['total_gems_value']
                
                # For high-value games, apply slight patterns
                if total_value >= 100:  # High-value game
                    # Slightly favor rock for stability in high-value games
                    weighted_moves = [GameMove.ROCK, GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
                    return random.choice(weighted_moves)
                elif total_value >= 50:  # Medium-value game
                    # Slightly favor paper for medium-value games
                    weighted_moves = [GameMove.ROCK, GameMove.PAPER, GameMove.PAPER, GameMove.SCISSORS]
                    return random.choice(weighted_moves)
            
            # Default random selection
            return random.choice(moves)
        
        elif bot.bot_type == BotType.HUMAN:
            # Human bot: More sophisticated decision making with gem value consideration
            if bot.simple_mode:
                # Simple human mode: slight bias towards rock, influenced by gem value
                if game_context and game_context.get('total_gems_value', 0) >= 100:
                    # High-value games: more conservative (favor rock)
                    choices = [GameMove.ROCK, GameMove.ROCK, GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
                else:
                    # Standard simple mode
                    choices = [GameMove.ROCK, GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
                return random.choice(choices)
            else:
                # Complex human mode: pattern-based decisions with gem value consideration
                if game_context and game_context.get('total_gems_value', 0) > 0:
                    total_value = game_context['total_gems_value']
                    
                    if total_value >= 100:  # High-value game
                        # More conservative weights for high-value games
                        weights = [0.45, 0.30, 0.25]  # Rock, Paper, Scissors (favor rock)
                    elif total_value >= 50:  # Medium-value game
                        # Balanced but slightly favor paper
                        weights = [0.30, 0.40, 0.30]  # Rock, Paper, Scissors
                    else:
                        # Low-value game: standard weights
                        weights = [0.35, 0.35, 0.30]  # Rock, Paper, Scissors
                else:
                    # Default weights
                    weights = [0.35, 0.35, 0.30]  # Rock, Paper, Scissors
                
                moves = [GameMove.ROCK, GameMove.PAPER, GameMove.SCISSORS]
                return random.choices(moves, weights=weights)[0]
        
        return GameMove.ROCK  # Default fallback
    
    @staticmethod
    def should_bot_win(bot: Bot, game_context: dict = None) -> bool:
        """Determine if bot should win based on win rate, cycle management, and gem value consideration."""
        import random
        
        # Get bot data from database for additional fields
        bot_data = getattr(bot, '_bot_data', {})
        bot_behavior = bot_data.get('bot_behavior', 'balanced')
        profit_strategy = bot_data.get('profit_strategy', 'balanced')
        
        # Base win probability calculation
        base_win_probability = 0.5  # Default 50/50
        
        # Gem value consideration - higher value games may influence decision
        gem_value_modifier = 0.0
        if game_context and game_context.get('total_gems_value', 0) > 0:
            total_value = game_context['total_gems_value']
            bet_amount = game_context.get('bet_amount', total_value)
            
            # For high-value games, bot may be more strategic
            if total_value >= 100:  # High-value game (Magic gem or equivalent)
                # More careful consideration for high-value games
                if profit_strategy == 'start_profit':
                    gem_value_modifier = 0.1  # Slightly more likely to win high-value games early
                elif profit_strategy == 'end_loss':
                    gem_value_modifier = -0.05  # Slightly more likely to lose high-value games early
                    
            elif total_value >= 50:  # Medium-value game (Sapphire or equivalent)
                # Moderate consideration
                if profit_strategy == 'start_profit':
                    gem_value_modifier = 0.05
                elif profit_strategy == 'end_loss':
                    gem_value_modifier = -0.025
                    
            # Behavioral adjustments based on gem value
            if bot_behavior == 'aggressive':
                # Aggressive bots more likely to go for high-value wins
                gem_value_modifier += min(0.1, total_value / 1000)
            elif bot_behavior == 'cautious':
                # Cautious bots more conservative with high-value games
                gem_value_modifier -= min(0.05, total_value / 2000)
        
        # Check if we're in a cycle management mode
        if bot.cycle_games > 0:
            current_games = bot.current_cycle_games
            current_wins = bot.current_cycle_wins
            target_win_rate = bot.win_rate
            remaining_games = bot.cycle_games - current_games
            
            if current_games > 0:
                current_win_rate = current_wins / current_games
                
                # Advanced win rate logic with behavior consideration
                if remaining_games > 0:
                    # Calculate required wins to achieve target
                    total_target_wins = int(target_win_rate * bot.cycle_games)
                    required_wins = total_target_wins - current_wins
                    
                    # Behavioral adjustments
                    behavior_multiplier = {
                        'aggressive': 1.15,  # More aggressive win seeking
                        'balanced': 1.0,     # Standard logic
                        'cautious': 0.85     # More conservative
                    }.get(bot_behavior, 1.0)
                    
                    # Strategy-based win probability adjustment
                    if profit_strategy == 'start_profit':
                        # Try to win early in cycle
                        early_game_bonus = max(0, (bot.cycle_games - current_games) / bot.cycle_games * 0.2)
                        behavior_multiplier += early_game_bonus
                    elif profit_strategy == 'balanced':
                        # Even distribution throughout cycle
                        pass  # No adjustment
                    elif profit_strategy == 'end_loss':
                        # Accept losses early, win later
                        late_game_bonus = max(0, current_games / bot.cycle_games * 0.2)
                        behavior_multiplier += late_game_bonus
                    
                    # Calculate win probability based on remaining games
                    if remaining_games <= 3:
                        # End of cycle - force exact win rate
                        win_probability = required_wins / remaining_games if remaining_games > 0 else 0
                        win_probability = max(0, min(1, win_probability))
                    else:
                        # Normal cycle progression with behavioral adjustments
                        if current_wins < (current_games * target_win_rate):
                            # Behind target - increase probability
                            win_probability = min(0.95, target_win_rate + (0.3 * behavior_multiplier))
                        elif current_wins > (current_games * target_win_rate):
                            # Ahead of target - decrease probability
                            win_probability = max(0.05, target_win_rate - (0.3 * behavior_multiplier))
                        else:
                            # On target - maintain rate with behavioral adjustment
                            win_probability = target_win_rate * behavior_multiplier
                    
                    # Apply behavioral variance
                    if bot_behavior == 'aggressive':
                        # More volatile - bigger swings
                        variance = random.uniform(-0.1, 0.1)
                        win_probability += variance
                    elif bot_behavior == 'cautious':
                        # More stable - smaller swings
                        variance = random.uniform(-0.05, 0.05)
                        win_probability += variance
                    
                    # Apply gem value modifier to win probability
                    win_probability += gem_value_modifier
                    
                    # Ensure probability stays within bounds
                    win_probability = max(0.05, min(0.95, win_probability))
                    
                    return random.random() < win_probability
        
        # Standard win rate check with behavioral adjustment
        base_win_rate = bot.win_rate
        behavior_adjustment = {
            'aggressive': 0.05,   # Slightly higher base win rate
            'balanced': 0.0,      # No adjustment
            'cautious': -0.05     # Slightly lower base win rate
        }.get(bot_behavior, 0.0)
        
        # Apply gem value modifier to base win rate
        adjusted_win_rate = max(0.1, min(0.9, base_win_rate + behavior_adjustment + gem_value_modifier))
        return random.random() < adjusted_win_rate
    
    @staticmethod
    def calculate_game_gems_value(game: Game) -> dict:
        """Calculate total gem value for both players in a game."""
        # Gem price mapping
        gem_prices = {
            GemType.RUBY.value: 1.0,
            GemType.AMBER.value: 2.0,
            GemType.TOPAZ.value: 5.0,
            GemType.EMERALD.value: 10.0,
            GemType.AQUAMARINE.value: 25.0,
            GemType.SAPPHIRE.value: 50.0,
            GemType.MAGIC.value: 100.0
        }
        
        # Calculate creator's gems value
        creator_gems_value = 0
        if game.bet_gems:
            for gem_type, quantity in game.bet_gems.items():
                price = gem_prices.get(gem_type, 0)
                creator_gems_value += price * quantity
        
        # Calculate opponent's gems value (if available)
        opponent_gems_value = 0
        if game.opponent_gems:
            for gem_type, quantity in game.opponent_gems.items():
                price = gem_prices.get(gem_type, 0)
                opponent_gems_value += price * quantity
        
        total_gems_value = creator_gems_value + opponent_gems_value
        
        return {
            "creator_gems_value": creator_gems_value,
            "opponent_gems_value": opponent_gems_value,
            "total_gems_value": total_gems_value,
            "bet_amount": game.bet_amount
        }
    
    @staticmethod
    def get_bot_move_against_player(bot: Bot, player_move: GameMove, game: Game = None) -> GameMove:
        """Get bot move specifically to beat or lose to player move with gem value consideration."""
        
        # Calculate game context for decision making
        game_context = {}
        if game:
            game_context = BotGameLogic.calculate_game_gems_value(game)
        
        # Enhanced decision making with gem value consideration
        should_win = BotGameLogic.should_bot_win(bot, game_context)
        
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

@api_router.get("/bots/active-games", response_model=List[dict])
async def get_active_bot_games(current_user: User = Depends(get_current_user)):
    """Get all active games created by bots."""
    try:
        # Get display limits from interface settings
        settings_doc = await db.admin_settings.find_one({"type": "interface_settings"})
        max_bots_limit = 100  # Default limit
        
        if settings_doc and settings_doc.get("display_limits"):
            max_bots_limit = settings_doc["display_limits"].get("bot_players", {}).get("max_available_bots", 100)
        
        # Find active bots to get their IDs
        active_bots = await db.bots.find({"is_active": True}).to_list(100)
        bot_ids = [bot["id"] for bot in active_bots]
        
        if not bot_ids:
            return []
        
        # Find games created by active bots with status WAITING
        # Use the dynamic limit from settings
        bot_games = await db.games.find({
            "creator_id": {"$in": bot_ids},
            "status": "WAITING"
        }).sort("created_at", -1).to_list(max_bots_limit)
        
        result = []
        for game in bot_games:
            # Get bot info
            bot = next((b for b in active_bots if b["id"] == game["creator_id"]), None)
            if not bot:
                continue
                
            game_data = {
                "id": game["id"],
                "game_id": game["id"],
                "creator_id": game["creator_id"],
                "creator_username": bot["name"],
                "creator": {
                    "username": bot["name"],
                    "gender": bot.get("avatar_gender", "male")
                },
                "bet_amount": game["bet_amount"],
                "bet_gems": game["bet_gems"],
                "status": game["status"],
                "created_at": game["created_at"],
                "is_bot": True,
                "is_bot_game": True,
                "bot_id": bot["id"],
                "bot_type": bot["bot_type"],
                "can_accept_bets": bot.get("can_accept_bets", False)
            }
            result.append(game_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching active bot games: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active bot games"
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

GEM_PRICES = {
    "Ruby": 1.0,
    "Amber": 2.0,
    "Topaz": 5.0,
    "Emerald": 10.0,
    "Aquamarine": 25.0,
    "Sapphire": 50.0,
    "Magic": 100.0
}

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
            user_id = user.get("id")
            
            # Calculate gem statistics from user_gems collection
            total_gems = 0
            total_gems_value = 0.0
            
            # Get gems from user_gems collection
            user_gems = await db.user_gems.find({"user_id": user_id}).to_list(100)
            for gem_doc in user_gems:
                gem_type = gem_doc.get("gem_type")
                quantity = gem_doc.get("quantity", 0)
                price = GEM_PRICES.get(gem_type, 0)
                total_gems += quantity
                total_gems_value += quantity * price
            
            # Calculate active bets count
            active_bets_pipeline = [
                {"$match": {
                    "$or": [
                        {"creator_id": user_id},
                        {"opponent_id": user_id}
                    ],
                    "status": {"$in": ["WAITING", "ACTIVE"]}
                }},
                {"$count": "active_bets"}
            ]
            active_bets_result = await db.games.aggregate(active_bets_pipeline).to_list(1)
            active_bets_count = active_bets_result[0]["active_bets"] if active_bets_result else 0
            
            # Calculate game statistics
            total_games_played = user.get("total_games_played", 0)
            total_games_won = user.get("total_games_won", 0)
            total_games_lost = total_games_played - total_games_won
            total_games_draw = user.get("total_games_draw", 0)
            
            cleaned_user = {
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role"),
                "status": user.get("status"),
                "gender": user.get("gender"),
                "virtual_balance": user.get("virtual_balance", 0),
                "total_games_played": total_games_played,
                "total_games_won": total_games_won,
                "total_games_lost": total_games_lost,
                "total_games_draw": total_games_draw,
                "total_gems": total_gems,
                "total_gems_value": round(total_gems_value, 2),
                "active_bets_count": active_bets_count,
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
        
        # Get profits by type
        profit_by_type = await db.profit_entries.aggregate([
            {"$group": {"_id": "$entry_type", "total": {"$sum": "$amount"}}}
        ]).to_list(10)
        
        profit_breakdown = {}
        for item in profit_by_type:
            profit_breakdown[item["_id"]] = item["total"]
        
        # Extract specific commission types
        bet_commission = profit_breakdown.get("BET_COMMISSION", 0)
        gift_commission = profit_breakdown.get("GIFT_COMMISSION", 0)
        bot_revenue = profit_breakdown.get("BOT_REVENUE", 0)
        
        # Get total from all entries
        total_profit = sum(profit_breakdown.values())
        
        # Calculate periods
        today_profit = await db.profit_entries.aggregate([
            {"$match": {"created_at": {"$gte": day_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        today_profit = today_profit[0]["total"] if today_profit else 0
        
        week_profit = await db.profit_entries.aggregate([
            {"$match": {"created_at": {"$gte": week_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        week_profit = week_profit[0]["total"] if week_profit else 0
        
        month_profit = await db.profit_entries.aggregate([
            {"$match": {"created_at": {"$gte": month_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        month_profit = month_profit[0]["total"] if month_profit else 0
        
        # Get frozen funds from all users
        frozen_funds_result = await db.users.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$frozen_balance"}}}
        ]).to_list(1)
        frozen_funds = frozen_funds_result[0]["total"] if frozen_funds_result else 0
        
        # Calculate expenses (для будущего использования)
        total_expenses = profit_breakdown.get("REFUND", 0) + profit_breakdown.get("BONUS", 0) + profit_breakdown.get("EXPENSE", 0)
        
        return {
            # Main metrics for new design
            "bet_commission": bet_commission,           # Комиссия от ставок
            "gift_commission": gift_commission,         # Комиссия от подарков
            "bot_revenue": bot_revenue,                 # Доход от ботов
            "frozen_funds": frozen_funds,               # Замороженные средства
            "total_profit": total_profit,               # Общая прибыль
            "total_expenses": total_expenses,           # Расходы
            
            # Period statistics
            "today_profit": today_profit,
            "week_profit": week_profit,
            "month_profit": month_profit,
            
            # Full breakdown for compatibility
            "profit_by_type": profit_breakdown
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
    limit: int = 10,
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
        
        # Get user info for each entry and clean ObjectIds
        for entry in entries:
            # Convert ObjectId to string if present
            if "_id" in entry:
                entry["_id"] = str(entry["_id"])
            
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
        # Try to get settings from database
        settings_doc = await db.admin_settings.find_one({"type": "commission_settings"})
        
        if settings_doc:
            return {
                "bet_commission_rate": settings_doc.get("bet_commission_rate", 3.0),
                "gift_commission_rate": settings_doc.get("gift_commission_rate", 3.0),
                "min_bet": 1.0,
                "max_bet": 3000.0,
                "daily_deposit_limit": 1000.0
            }
        else:
            # Return default values if no settings found
            return {
                "bet_commission_rate": 3.0,
                "gift_commission_rate": 3.0,
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

@api_router.put("/admin/profit/commission-settings", response_model=dict)
async def update_commission_settings(
    settings: dict,
    current_admin: User = Depends(get_current_admin)
):
    """Update commission settings."""
    try:
        # Validate input
        bet_commission_rate = settings.get("bet_commission_rate", 3.0)
        gift_commission_rate = settings.get("gift_commission_rate", 3.0)
        
        # Validate ranges
        if not (0 <= bet_commission_rate <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bet commission rate must be between 0 and 100"
            )
        
        if not (0 <= gift_commission_rate <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gift commission rate must be between 0 and 100"
            )
        
        # For now, we'll store these in a collection. In a real app, you might want a dedicated settings collection
        settings_doc = {
            "type": "commission_settings",
            "bet_commission_rate": bet_commission_rate,
            "gift_commission_rate": gift_commission_rate,
            "updated_at": datetime.now(),
            "updated_by": current_admin.id
        }
        
        # Update or create settings document
        await db.admin_settings.update_one(
            {"type": "commission_settings"},
            {"$set": settings_doc},
            upsert=True
        )
        
        logger.info(f"Commission settings updated by {current_admin.email}: bet={bet_commission_rate}%, gift={gift_commission_rate}%")
        
        return {
            "success": True,
            "message": "Commission settings updated successfully",
            "bet_commission_rate": bet_commission_rate,
            "gift_commission_rate": gift_commission_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating commission settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update commission settings"
        )

@api_router.get("/admin/interface-settings", response_model=dict)
async def get_interface_settings(current_admin: User = Depends(get_current_admin)):
    """Get current interface settings."""
    try:
        # Try to get settings from database
        settings_doc = await db.admin_settings.find_one({"type": "interface_settings"})
        
        if settings_doc:
            return {
                "live_players": settings_doc.get("live_players", {
                    "my_bets": 10,
                    "available_bets": 10,
                    "ongoing_battles": 10
                }),
                "bot_players": settings_doc.get("bot_players", {
                    "available_bots": 10,
                    "ongoing_bot_battles": 10
                }),
                "display_limits": settings_doc.get("display_limits", {
                    "live_players": {
                        "max_my_bets": 50,
                        "max_available_bets": 50,
                        "max_ongoing_battles": 50
                    },
                    "bot_players": {
                        "max_available_bots": 100,
                        "max_ongoing_bot_battles": 100
                    }
                })
            }
        else:
            # Return default values if no settings found
            return {
                "live_players": {
                    "my_bets": 10,
                    "available_bets": 10,
                    "ongoing_battles": 10
                },
                "bot_players": {
                    "available_bots": 10,
                    "ongoing_bot_battles": 10
                },
                "display_limits": {
                    "live_players": {
                        "max_my_bets": 50,
                        "max_available_bets": 50,
                        "max_ongoing_battles": 50
                    },
                    "bot_players": {
                        "max_available_bots": 100,
                        "max_ongoing_bot_battles": 100
                    }
                }
            }
    except Exception as e:
        logger.error(f"Error fetching interface settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch interface settings"
        )

@api_router.put("/admin/interface-settings", response_model=dict)
async def update_interface_settings(
    settings: dict,
    current_admin: User = Depends(get_current_admin)
):
    """Update interface settings."""
    try:
        # Validate the settings structure
        live_players = settings.get("live_players", {})
        bot_players = settings.get("bot_players", {})
        display_limits = settings.get("display_limits", {})
        
        # Validate live_players settings
        for key in ["my_bets", "available_bets", "ongoing_battles"]:
            value = live_players.get(key, 10)
            if not isinstance(value, int) or value < 5 or value > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid value for live_players.{key}. Must be between 5 and 100."
                )
        
        # Validate bot_players settings
        for key in ["available_bots", "ongoing_bot_battles"]:
            value = bot_players.get(key, 10)
            if not isinstance(value, int) or value < 5 or value > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid value for bot_players.{key}. Must be between 5 and 100."
                )
        
        # Validate display_limits settings
        if display_limits:
            live_limits = display_limits.get("live_players", {})
            bot_limits = display_limits.get("bot_players", {})
            
            # Validate live_players display limits
            for key in ["max_my_bets", "max_available_bets", "max_ongoing_battles"]:
                value = live_limits.get(key, 50)
                if not isinstance(value, int) or value < 10 or value > 500:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid value for display_limits.live_players.{key}. Must be between 10 and 500."
                    )
            
            # Validate bot_players display limits
            for key in ["max_available_bots", "max_ongoing_bot_battles"]:
                value = bot_limits.get(key, 100)
                if not isinstance(value, int) or value < 10 or value > 500:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid value for display_limits.bot_players.{key}. Must be between 10 and 500."
                    )
        
        # Prepare settings document
        settings_doc = {
            "type": "interface_settings",
            "live_players": live_players,
            "bot_players": bot_players,
            "display_limits": display_limits,
            "updated_at": datetime.utcnow(),
            "updated_by": current_admin.id
        }
        
        # Update or create settings document
        await db.admin_settings.update_one(
            {"type": "interface_settings"},
            {"$set": settings_doc},
            upsert=True
        )
        
        logger.info(f"Interface settings updated by {current_admin.email}: {settings}")
        
        return {
            "success": True,
            "message": "Interface settings updated successfully",
            "settings": {
                "live_players": live_players,
                "bot_players": bot_players
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating interface settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update interface settings"
        )

@api_router.get("/admin/profit/bot-revenue-details", response_model=dict)
async def get_bot_revenue_details(
    period: str = "month",  # day, week, month, all
    current_admin: User = Depends(get_current_admin)
):
    """Get detailed information about bot revenue."""
    try:
        # Calculate date filter based on period
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # "all"
            start_date = None
        
        # Get all regular bots with their accumulated profits
        bots = await db.bots.find({"is_regular": True}).to_list(None)
        
        bot_details = []
        total_revenue = 0
        
        for bot in bots:
            bot_revenue = 0
            
            # Get completed cycles for this bot with period filter
            query = {
                "type": "BOT_REVENUE",
                "bot_id": bot["id"]
            }
            if start_date:
                query["created_at"] = {"$gte": start_date}
            
            profit_entries = await db.profit_history.find(query).to_list(None)
            
            for entry in profit_entries:
                bot_revenue += entry.get("amount", 0)
            
            total_revenue += bot_revenue
            
            # Get bot statistics (for all time)
            games_played = bot.get("total_games_played", 0)
            games_won = bot.get("total_games_won", 0)
            current_cycle_games = bot.get("current_cycle_games", 0)
            current_cycle_wins = bot.get("current_cycle_wins", 0)
            
            bot_details.append({
                "bot_id": bot["id"],
                "bot_name": bot.get("username", f"Bot_{bot['id'][:8]}"),
                "total_revenue": bot_revenue,
                "games_played": games_played,
                "games_won": games_won,
                "win_rate": (games_won / games_played * 100) if games_played > 0 else 0,
                "current_cycle_games": current_cycle_games,
                "current_cycle_wins": current_cycle_wins,
                "cycles_completed": len(profit_entries),
                "avg_revenue_per_cycle": bot_revenue / len(profit_entries) if len(profit_entries) > 0 else 0,
                "status": "active" if bot.get("is_active", False) else "inactive"
            })
        
        # Sort by total revenue descending
        bot_details.sort(key=lambda x: x["total_revenue"], reverse=True)
        
        return {
            "success": True,
            "period": period,
            "total_revenue": total_revenue,
            "active_bots": len([b for b in bot_details if b["status"] == "active"]),
            "total_bots": len(bot_details),
            "avg_revenue_per_bot": total_revenue / len(bot_details) if len(bot_details) > 0 else 0,
            "entries": bot_details
        }
        
    except Exception as e:
        logger.error(f"Error fetching bot revenue details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot revenue details"
        )

@api_router.get("/admin/profit/frozen-funds-details", response_model=dict)
async def get_frozen_funds_details(
    period: str = "month",  # day, week, month, all
    current_admin: User = Depends(get_current_admin)
):
    """Get detailed information about frozen funds."""
    try:
        # Calculate date filter based on period
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # all
            start_date = None
            
        # Get all active games (where funds are frozen)
        query = {"status": {"$in": ["waiting_for_opponent", "in_progress", "reveal_phase"]}}
        if start_date:
            query["created_at"] = {"$gte": start_date}
            
        active_games = await db.games.find(query).to_list(None)
        
        frozen_details = []
        total_frozen = 0
        
        for game in active_games:
            # Calculate frozen commission for this game
            bet_amount = game.get("bet_amount", 0)
            commission_rate = 0.06  # 6% commission
            frozen_commission = bet_amount * commission_rate
            
            total_frozen += frozen_commission
            
            # Get player information
            creator = await db.users.find_one({"id": game.get("player1_id")})
            opponent = await db.users.find_one({"id": game.get("player2_id")}) if game.get("player2_id") else None
            
            frozen_details.append({
                "game_id": game["id"],
                "bet_amount": bet_amount,
                "frozen_commission": frozen_commission,
                "commission_rate": commission_rate,
                "status": game["status"],
                "created_at": game.get("created_at"),
                "creator": {
                    "id": creator["id"] if creator else None,
                    "username": creator.get("username", "Unknown") if creator else "Unknown"
                },
                "opponent": {
                    "id": opponent["id"] if opponent else None,
                    "username": opponent.get("username", "Waiting") if opponent else "Waiting"
                } if opponent else None,
                "estimated_release_time": None  # Could be calculated based on game rules
            })
        
        # Sort by frozen commission descending
        frozen_details.sort(key=lambda x: x["frozen_commission"], reverse=True)
        
        return {
            "success": True,
            "period": period,
            "total_frozen": total_frozen,
            "active_games": len(active_games),
            "avg_frozen_per_game": total_frozen / len(active_games) if len(active_games) > 0 else 0,
            "entries": frozen_details
        }
        
    except Exception as e:
        logger.error(f"Error fetching frozen funds details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch frozen funds details"
        )

@api_router.get("/admin/profit/total-revenue-breakdown", response_model=dict)
async def get_total_revenue_breakdown(
    period: str = "month",  # day, week, month, all
    current_admin: User = Depends(get_current_admin)
):
    """Get detailed breakdown of total revenue by source."""
    try:
        # Calculate date filter based on period
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # "all"
            start_date = None
        
        # Get revenue breakdown by type with period filter
        revenue_breakdown = []
        
        # Get commission from bets
        query = {"type": "BET_COMMISSION"}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        
        bet_commission_total = 0
        bet_commission_entries = await db.profit_history.find(query).to_list(None)
        bet_commission_count = len(bet_commission_entries)
        for entry in bet_commission_entries:
            bet_commission_total += entry.get("amount", 0)
        
        # Get commission from gifts
        query = {"type": "GIFT_COMMISSION"}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        
        gift_commission_total = 0
        gift_commission_entries = await db.profit_history.find(query).to_list(None)
        gift_commission_count = len(gift_commission_entries)
        for entry in gift_commission_entries:
            gift_commission_total += entry.get("amount", 0)
        
        # Get bot revenue
        query = {"type": "BOT_REVENUE"}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        
        bot_revenue_total = 0
        bot_revenue_entries = await db.profit_history.find(query).to_list(None)
        bot_revenue_count = len(bot_revenue_entries)
        for entry in bot_revenue_entries:
            bot_revenue_total += entry.get("amount", 0)
        
        # Build breakdown
        revenue_breakdown = [
            {
                "source": "bet_commission",
                "name": "Комиссия от ставок",
                "amount": bet_commission_total,
                "percentage": 0,  # Will be calculated below
                "transactions": bet_commission_count,
                "avg_per_transaction": bet_commission_total / bet_commission_count if bet_commission_count > 0 else 0,
                "color": "green",
                "icon": "percent"
            },
            {
                "source": "gift_commission",
                "name": "Комиссия от подарков",
                "amount": gift_commission_total,
                "percentage": 0,
                "transactions": gift_commission_count,
                "avg_per_transaction": gift_commission_total / gift_commission_count if gift_commission_count > 0 else 0,
                "color": "purple",
                "icon": "gift"
            },
            {
                "source": "bot_revenue",
                "name": "Доход от ботов",
                "amount": bot_revenue_total,
                "percentage": 0,
                "transactions": bot_revenue_count,
                "avg_per_transaction": bot_revenue_total / bot_revenue_count if bot_revenue_count > 0 else 0,
                "color": "blue",
                "icon": "bot"
            }
        ]
        
        # Calculate total and percentages
        total_revenue = sum(item["amount"] for item in revenue_breakdown)
        
        for item in revenue_breakdown:
            item["percentage"] = (item["amount"] / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            "success": True,
            "period": period,
            "total_revenue": total_revenue,
            "breakdown": revenue_breakdown,
            "summary": {
                "total_transactions": sum(item["transactions"] for item in revenue_breakdown),
                "avg_revenue_per_transaction": total_revenue / sum(item["transactions"] for item in revenue_breakdown) if sum(item["transactions"] for item in revenue_breakdown) > 0 else 0,
                "top_source": max(revenue_breakdown, key=lambda x: x["amount"])["source"] if revenue_breakdown else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching total revenue breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch total revenue breakdown"
        )

@api_router.get("/admin/profit/expenses-details", response_model=dict)
async def get_expenses_details(
    period: str = "month",  # day, week, month, all
    current_admin: User = Depends(get_current_admin)
):
    """Get detailed information about expenses."""
    try:
        # Calculate date filter based on period
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # "all"
            start_date = None
        
        # Get current expense settings
        settings_doc = await db.admin_settings.find_one({"type": "expense_settings"})
        if settings_doc:
            expense_percentage = settings_doc.get("percentage", 60)
            manual_expenses = settings_doc.get("manual_amount", 0)
        else:
            expense_percentage = 60  # Default 60%
            manual_expenses = 0
        
        # Calculate total revenue for the period
        total_revenue = 0
        query = {"type": {"$in": ["BET_COMMISSION", "GIFT_COMMISSION", "BOT_REVENUE"]}}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        
        revenue_entries = await db.profit_history.find(query).to_list(None)
        
        for entry in revenue_entries:
            total_revenue += entry.get("amount", 0)
        
        # Calculate expenses
        percentage_expenses = (total_revenue * expense_percentage) / 100
        total_expenses = percentage_expenses + manual_expenses
        
        # Build expense breakdown
        expense_breakdown = [
            {
                "category": "operational",
                "name": "Операционные расходы",
                "amount": percentage_expenses,
                "percentage": expense_percentage,
                "calculation": f"{expense_percentage}% от общей прибыли",
                "type": "percentage",
                "color": "red"
            },
            {
                "category": "manual",
                "name": "Дополнительные расходы",
                "amount": manual_expenses,
                "percentage": 0,
                "calculation": "Фиксированная сумма",
                "type": "fixed",
                "color": "orange"
            }
        ]
        
        # Get expense history (if tracked) for the period
        expense_history = []
        query = {"type": "EXPENSE"}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        
        expense_entries = await db.profit_history.find(query).to_list(None)
        for entry in expense_entries:
            expense_history.append({
                "date": entry.get("created_at"),
                "amount": entry.get("amount", 0),
                "description": entry.get("description", ""),
                "category": entry.get("category", "operational")
            })
        
        return {
            "success": True,
            "period": period,
            "total_expenses": total_expenses,
            "total_revenue": total_revenue,
            "expense_percentage": expense_percentage,
            "breakdown": expense_breakdown,
            "settings": {
                "percentage": expense_percentage,
                "manual_amount": manual_expenses,
                "can_modify": True
            },
            "entries": expense_history[-50:] if expense_history else [],  # Last 50 entries
            "statistics": {
                "expense_ratio": (total_expenses / total_revenue * 100) if total_revenue > 0 else 0,
                "monthly_avg": total_expenses / 12 if total_expenses > 0 else 0,
                "efficiency_score": max(0, 100 - (total_expenses / total_revenue * 100)) if total_revenue > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching expenses details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch expenses details"
        )

@api_router.get("/admin/profit/net-profit-analysis", response_model=dict)
async def get_net_profit_analysis(
    period: str = "month",  # day, week, month, all
    current_admin: User = Depends(get_current_admin)
):
    """Get detailed net profit analysis."""
    try:
        # Calculate date filter based on period
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # "all"
            start_date = None
        
        # Calculate total revenue for the period
        total_revenue = 0
        revenue_by_type = {}
        
        query = {"type": {"$in": ["BET_COMMISSION", "GIFT_COMMISSION", "BOT_REVENUE"]}}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        
        revenue_entries = await db.profit_history.find(query).to_list(None)
        
        for entry in revenue_entries:
            amount = entry.get("amount", 0)
            entry_type = entry.get("type")
            total_revenue += amount
            revenue_by_type[entry_type] = revenue_by_type.get(entry_type, 0) + amount
        
        # Calculate expenses
        settings_doc = await db.admin_settings.find_one({"type": "expense_settings"})
        if settings_doc:
            expense_percentage = settings_doc.get("percentage", 60)
            manual_expenses = settings_doc.get("manual_amount", 0)
        else:
            expense_percentage = 60
            manual_expenses = 0
        
        total_expenses = (total_revenue * expense_percentage / 100) + manual_expenses
        net_profit = total_revenue - total_expenses
        
        # Avoid division by zero
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        expense_ratio = (total_expenses / total_revenue * 100) if total_revenue > 0 else 0
        
        # Build detailed analysis
        analysis = {
            "revenue_analysis": {
                "bet_commission": revenue_by_type.get("BET_COMMISSION", 0),
                "gift_commission": revenue_by_type.get("GIFT_COMMISSION", 0),
                "bot_revenue": revenue_by_type.get("BOT_REVENUE", 0),
                "total": total_revenue
            },
            "expense_analysis": {
                "operational_percentage": expense_percentage,
                "operational_amount": total_revenue * expense_percentage / 100,
                "manual_amount": manual_expenses,
                "total": total_expenses
            },
            "profit_analysis": {
                "gross_profit": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "profit_margin": profit_margin,
                "expense_ratio": expense_ratio
            },
            "trends": {
                "is_profitable": net_profit > 0,
                "efficiency_rating": "high" if net_profit > total_expenses else "medium" if net_profit > 0 else "low",
                "growth_potential": "high" if profit_margin > 30 else "medium" if profit_margin > 10 else "low"
            }
        }
        
        # Calculate step-by-step breakdown
        calculation_steps = [
            {
                "step": 1,
                "description": "Комиссия от ставок",
                "amount": revenue_by_type.get("BET_COMMISSION", 0),
                "running_total": revenue_by_type.get("BET_COMMISSION", 0)
            },
            {
                "step": 2,
                "description": "Комиссия от подарков",
                "amount": revenue_by_type.get("GIFT_COMMISSION", 0),
                "running_total": revenue_by_type.get("BET_COMMISSION", 0) + revenue_by_type.get("GIFT_COMMISSION", 0)
            },
            {
                "step": 3,
                "description": "Доход от ботов",
                "amount": revenue_by_type.get("BOT_REVENUE", 0),
                "running_total": total_revenue
            },
            {
                "step": 4,
                "description": f"Операционные расходы ({expense_percentage}%)",
                "amount": -(total_revenue * expense_percentage / 100),
                "running_total": total_revenue - (total_revenue * expense_percentage / 100)
            },
            {
                "step": 5,
                "description": "Дополнительные расходы",
                "amount": -manual_expenses,
                "running_total": net_profit
            }
        ]
        
        return {
            "success": True,
            "period": period,
            "analysis": analysis,
            "calculation_steps": calculation_steps,
            "summary": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "profit_margin": profit_margin,
                "is_profitable": net_profit > 0,
                "efficiency_score": max(0, 100 - expense_ratio) if total_revenue > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching net profit analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch net profit analysis"
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
                        # Check global limits before creating a game
                        success = await bot_create_game_automatically(bot_obj)
                        if not success:
                            logger.info(f"Bot {bot_obj.id} skipped due to global limits")
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

async def maintain_bot_active_bets_count(bot_id: str, target_count: int):
    """Поддерживает количество активных ставок равным target_count."""
    try:
        # ============ ПРОВЕРКА ГЛОБАЛЬНЫХ ЛИМИТОВ ============
        # Получаем глобальные настройки
        bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_active_bets_regular = bot_settings.get("max_active_bets_regular", 50) if bot_settings else 50
        max_active_bets_human = bot_settings.get("max_active_bets_human", 30) if bot_settings else 30
        
        # Получаем информацию о боте
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            return
            
        bot_type = bot.get("bot_type", "REGULAR")
        
        # Подсчитываем текущие активные ставки по типу бота
        if bot_type == "REGULAR":
            current_global_bets = await db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "REGULAR"},
                    {"metadata.bot_type": "REGULAR"}
                ]
            })
            max_limit = max_active_bets_regular
        else:  # HUMAN
            current_global_bets = await db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "HUMAN"},
                    {"metadata.bot_type": "HUMAN"}
                ]
            })
            max_limit = max_active_bets_human
        
        # Получаем текущее количество активных ставок конкретного бота
        current_active_bets = await db.games.count_documents({
            "creator_id": bot_id,
            "status": "WAITING"
        })
        
        # Если активных ставок меньше целевого количества, создаём новые
        if current_active_bets < target_count:
            needed_bets = target_count - current_active_bets
            
            # Проверяем, сколько ставок можно создать с учетом глобального лимита
            available_global_slots = max_limit - current_global_bets
            
            # Также проверяем индивидуальный лимит бота
            individual_limit = bot.get("current_limit") or bot.get("cycle_games", 12)
            available_individual_slots = individual_limit - current_active_bets
            
            # Берем минимум между всеми лимитами
            actual_needed_bets = min(needed_bets, available_global_slots, available_individual_slots)
            
            if actual_needed_bets > 0:
                bot_obj = Bot(**bot)
                
                for i in range(actual_needed_bets):
                    try:
                        # Проверяем глобальный лимит перед каждой попыткой создания
                        current_check = await db.games.count_documents({
                            "creator_type": "bot",
                            "is_bot_game": True,
                            "status": "WAITING",
                            "$or": [
                                {"bot_type": bot_type},
                                {"metadata.bot_type": bot_type}
                            ]
                        })
                        
                        if current_check >= max_limit:
                            logger.info(f"🚫 Global limit reached during creation, stopping at {i+1}/{actual_needed_bets}")
                            break
                        
                        success = await bot_create_game_automatically(bot_obj)
                        if not success:
                            logger.info(f"🚫 Failed to create bet for bot {bot_id} due to limits")
                            break
                    except Exception as e:
                        logger.error(f"Failed to create bet for bot {bot_id}: {e}")
                        
                logger.info(f"🎯 Created {actual_needed_bets} additional bets for bot {bot_id} (requested: {needed_bets})")
            else:
                logger.info(f"🚫 Cannot create bets for bot {bot_id}: global limit reached {current_global_bets}/{max_limit}")
        
        # Если активных ставок больше целевого количества, удаляем лишние
        elif current_active_bets > target_count:
            excess_bets = current_active_bets - target_count
            
            # Получаем лишние ставки
            excess_games = await db.games.find({
                "creator_id": bot_id,
                "status": "WAITING"
            }).limit(excess_bets).to_list(excess_bets)
            
            for game in excess_games:
                try:
                    await db.games.delete_one({"id": game["id"]})
                    logger.info(f"🗑️ Deleted excess bet {game['id']} for bot {bot_id}")
                except Exception as e:
                    logger.error(f"Failed to delete excess bet {game['id']}: {e}")
        
        # Обновляем количество активных ставок в базе данных
        final_active_count = await db.games.count_documents({
            "creator_id": bot_id,
            "status": "WAITING"
        })
        
        await db.bots.update_one(
            {"id": bot_id},
            {
                "$set": {
                    "active_bets": final_active_count,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"🎯 Bot {bot_id} now has {final_active_count} active bets (target: {target_count})")
        
    except Exception as e:
        logger.error(f"Error maintaining active bets count: {e}")

async def bot_create_game_automatically(bot: Bot):
    """Make bot create a game automatically using gem-based betting."""
    try:
        # ============ ПРОВЕРКА ГЛОБАЛЬНЫХ ЛИМИТОВ ============
        # Получаем глобальные настройки
        bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_active_bets_regular = bot_settings.get("max_active_bets_regular", 50) if bot_settings else 50
        max_active_bets_human = bot_settings.get("max_active_bets_human", 30) if bot_settings else 30
        
        # Определяем тип бота
        bot_doc = await db.bots.find_one({"id": bot.id})
        bot_type = bot_doc.get("bot_type", "REGULAR") if bot_doc else "REGULAR"
        
        # Подсчитываем текущие активные ставки по типу бота
        if bot_type == "REGULAR":
            current_active_bets = await db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "REGULAR"},
                    {"metadata.bot_type": "REGULAR"}
                ]
            })
            max_limit = max_active_bets_regular
        else:  # HUMAN
            current_active_bets = await db.games.count_documents({
                "creator_type": "bot", 
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "HUMAN"},
                    {"metadata.bot_type": "HUMAN"}
                ]
            })
            max_limit = max_active_bets_human
        
        # Проверяем глобальный лимит
        if current_active_bets >= max_limit:
            logger.info(f"🚫 Global limit reached for {bot_type} bots: {current_active_bets}/{max_limit}")
            return False
        
        # Ensure bot has gems
        await BotGameLogic.setup_bot_gems(bot.id, db)
        
        # Define gem values (must match frontend definitions)
        gem_values = {
            'Ruby': 1,
            'Amber': 2,
            'Topaz': 5,
            'Emerald': 10,
            'Aquamarine': 25,
            'Sapphire': 50,
            'Magic': 100
        }
        gem_types_list = list(gem_values.keys())
        
        def generate_gem_based_bet(min_amount: float, max_amount: float):
            """Generate a valid gem combination within the specified amount range."""
            target_min = int(min_amount)
            target_max = int(max_amount)
            
            attempts = 0
            max_attempts = 50
            
            while attempts < max_attempts:
                # Randomly select 1-3 gem types
                num_gem_types = random.randint(1, 3)
                selected_gem_types = random.sample(gem_types_list, num_gem_types)
                
                # Generate quantities for each gem type
                gem_combination = {}
                total_value = 0
                
                for gem_type in selected_gem_types:
                    # Start with 1-2 gems of each type for single bets
                    quantity = random.randint(1, 2)
                    gem_combination[gem_type] = quantity
                    total_value += gem_values[gem_type] * quantity
                
                # Adjust to fit target range
                while total_value < target_min and attempts < max_attempts:
                    gem_to_add = random.choice(selected_gem_types)
                    if total_value + gem_values[gem_to_add] <= target_max:
                        gem_combination[gem_to_add] += 1
                        total_value += gem_values[gem_to_add]
                    else:
                        break
                
                while total_value > target_max and attempts < max_attempts:
                    reducible_gems = [gt for gt in selected_gem_types if gem_combination[gt] > 1]
                    if not reducible_gems:
                        break
                    gem_to_reduce = random.choice(reducible_gems)
                    gem_combination[gem_to_reduce] -= 1
                    total_value -= gem_values[gem_to_reduce]
                    if gem_combination[gem_to_reduce] == 0:
                        del gem_combination[gem_to_reduce]
                        selected_gem_types.remove(gem_to_reduce)
                
                # Check if valid
                if target_min <= total_value <= target_max:
                    return gem_combination, total_value
                
                attempts += 1
            
            # Fallback: simple Ruby combination
            fallback_amount = max(target_min, min(target_max, 5))
            return {'Ruby': fallback_amount}, fallback_amount
        
        # Generate gem-based bet within bot's limits
        bet_gems, bet_amount = generate_gem_based_bet(bot.min_bet_amount, bot.max_bet_amount)
        
        # Generate bot's move
        bot_move = BotGameLogic.calculate_bot_move(bot)
        salt = secrets.token_hex(32)
        
        # Create game
        game = Game(
            creator_id=bot.id,
            creator_move=bot_move,
            creator_move_hash=hashlib.sha256(f"{bot_move.value}{salt}".encode()).hexdigest(),
            creator_salt=salt,
            bet_amount=float(bet_amount),  # Convert to float for compatibility
            bet_gems=bet_gems,
            is_bot_game=True,
            bot_id=bot.id,
            is_regular_bot_game=bot.bot_type == "REGULAR",  # Отмечаем игры обычных ботов
            metadata={
                "gem_based_bet": True,  # Mark as gem-based bet
                "auto_created": True
            }
        )
        
        await db.games.insert_one(game.dict())
        
        # Update bot's last game time
        await db.bots.update_one(
            {"id": bot.id},
            {"$set": {"last_game_time": datetime.utcnow()}}
        )
        
        logger.info(f"Bot {bot.name} created gem-based game {game.id} with bet ${bet_amount} (gems: {bet_gems})")
        return True
        
    except Exception as e:
        logger.error(f"Error in bot auto-create game: {e}")
        return False

async def bot_join_game_automatically(bot: Bot):
    """Make bot join an available game automatically."""
    try:
        if not bot.can_accept_bets:
            return
            
        # НОВОЕ ПРАВИЛО: Обычные боты не могут присоединяться к играм живых игроков
        if bot.bot_type == BotType.REGULAR:
            logger.info(f"🚫 Regular bot {bot.name} cannot join live player games")
            return
        
        # Find available games that bot can join
        available_games = await db.games.find({
            "status": GameStatus.WAITING,
            "creator_id": {"$ne": bot.id},  # Don't join own games
            "bet_amount": {"$gte": bot.min_bet_amount, "$lte": bot.max_bet_amount}
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
            # Bot knows creator's move (for testing/balancing) - Enhanced with gem value consideration
            bot_move = BotGameLogic.get_bot_move_against_player(bot, creator_move, game_obj)
        else:
            # Standard move calculation with game context
            game_context = BotGameLogic.calculate_game_gems_value(game_obj)
            bot_move = BotGameLogic.calculate_bot_move(bot, game_context)
        
        # For REGULAR bots, return commission to creator (no commission charged)
        commission_returned = 0
        if bot.bot_type == "REGULAR":
            commission_amount = game_obj.bet_amount * 0.06
            
            # Проверяем, была ли игра создана обычным ботом (тогда комиссия не была заморожена)
            creator_bot = await db.bots.find_one({"id": game_obj.creator_id})
            creator_is_regular_bot = creator_bot and creator_bot.get("bot_type") == "REGULAR"
            
            if not creator_is_regular_bot:
                # Игра была создана человеком или Human-ботом, возвращаем комиссию
                await db.users.update_one(
                    {"id": game_obj.creator_id},
                    {
                        "$inc": {
                            "virtual_balance": commission_amount,
                            "frozen_balance": -commission_amount
                        },
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                commission_returned = commission_amount
                logger.info(f"💰 REGULAR BOT GAME - Returned commission ${commission_amount} to creator {game_obj.creator_id}")
            else:
                # Игра была создана обычным ботом, комиссия не была заморожена
                logger.info(f"💰 REGULAR BOT vs REGULAR BOT - No commission was frozen, nothing to return")
        
        # Update game with bot as opponent and move to REVEAL phase
        await db.games.update_one(
            {"id": game_obj.id},
            {
                "$set": {
                    "opponent_id": bot.id,
                    "opponent_move": bot_move,
                    "status": GameStatus.REVEAL,  # Changed from ACTIVE to REVEAL
                    "started_at": datetime.utcnow(),
                    "reveal_deadline": datetime.utcnow() + timedelta(minutes=1),  # Give 1 minute for reveal
                    # НЕ ПЕРЕЗАПИСЫВАЕМ is_regular_bot_game - оставляем как было при создании игры
                    "commission_returned": commission_returned  # Track returned commission
                }
            }
        )
        
        # Update bot's last game time
        await db.bots.update_one(
            {"id": bot.id},
            {"$set": {"last_game_time": datetime.utcnow()}}
        )
        
        # For bot games, automatically trigger reveal and determine winner after a short delay
        # This simulates the bot "revealing" immediately
        import asyncio
        
        # Wait a short moment to ensure the game is properly updated
        await asyncio.sleep(0.1)
        
        # Automatically complete the reveal phase for bot games
        await auto_complete_bot_game_reveal(game_obj.id)
        
        logger.info(f"Bot {bot.name} joined game {game_obj.id} and moved to REVEAL phase")
        
    except Exception as e:
        logger.error(f"Error in bot auto-join game: {e}")

async def auto_complete_bot_game_reveal(game_id: str):
    """Automatically complete the reveal phase for bot games."""
    try:
        # Update game status to ACTIVE (simulating successful reveal)
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "status": GameStatus.ACTIVE,
                    "reveal_deadline": None
                }
            }
        )
        
        # Determine winner
        await determine_game_winner(game_id)
        
        logger.info(f"Automatically completed reveal for bot game {game_id}")
        
    except Exception as e:
        logger.error(f"Error auto-completing bot game reveal: {e}")

# ==============================================================================
# ADMIN GAME MANAGEMENT
# ==============================================================================

@api_router.post("/admin/users/reset-all-balances", response_model=dict)
async def reset_all_user_balances_admin(current_user: User = Depends(get_current_admin)):
    """Reset all user balances and gems to zero (admin only)."""
    try:
        # Reset all user balances and frozen balances to 0
        user_balance_result = await db.users.update_many(
            {},  # All users
            {
                "$set": {
                    "virtual_balance": 0.0,
                    "frozen_balance": 0.0,
                    "daily_limit_used": 0.0,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Reset all user gems to zero
        user_gems_result = await db.user_gems.update_many(
            {},  # All user gems
            {
                "$set": {
                    "quantity": 0,
                    "frozen_quantity": 0,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Reset all active games (cancel them)
        games_result = await db.games.update_many(
            {"status": {"$in": [GameStatus.WAITING, GameStatus.ACTIVE]}},
            {
                "$set": {
                    "status": GameStatus.CANCELLED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Clear transaction history (optional - keep for audit)
        # transactions_result = await db.transactions.delete_many({})
        
        # Get final counts
        total_users = await db.users.count_documents({})
        total_gems_records = await db.user_gems.count_documents({})
        cancelled_games = games_result.modified_count
        
        return {
            "success": True,
            "message": "All user balances and gems have been reset to zero",
            "details": {
                "users_affected": user_balance_result.modified_count,
                "total_users": total_users,
                "gem_records_reset": user_gems_result.modified_count,
                "total_gem_records": total_gems_records,
                "games_cancelled": cancelled_games,
                "reset_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error resetting all user balances: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset user balances: {str(e)}"
        )

# ==============================================================================
# NEW EXTENDED ADMIN USER MANAGEMENT ENDPOINTS
# ==============================================================================

@api_router.get("/admin/users/{user_id}/gems", response_model=dict)
async def get_user_gems(
    user_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Get detailed gem inventory for a specific user."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user's gems
        gems_data = []
        for gem_type, gem_data in user.get("gems", {}).items():
            if isinstance(gem_data, dict) and gem_data.get("quantity", 0) > 0:
                price = GEM_PRICES.get(gem_type, 0)
                gems_data.append({
                    "type": gem_type,
                    "quantity": gem_data.get("quantity", 0),
                    "frozen_quantity": gem_data.get("frozen_quantity", 0),
                    "price": price,
                    "total_value": gem_data.get("quantity", 0) * price,
                    "frozen": gem_data.get("frozen_quantity", 0) > 0
                })
        
        return {
            "user_id": user_id,
            "username": user.get("username"),
            "gems": gems_data,
            "total_gems": sum(gem["quantity"] for gem in gems_data),
            "total_value": sum(gem["total_value"] for gem in gems_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user gems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user gems"
        )

@api_router.get("/admin/users/{user_id}/bets", response_model=dict)
async def get_user_bets(
    user_id: str,
    include_completed: bool = False,
    current_user: User = Depends(get_current_admin)
):
    """Get bets for a specific user (active by default, optionally include completed)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build query based on parameters
        if include_completed:
            # Include all games
            status_filter = {"$in": ["WAITING", "ACTIVE", "REVEAL", "COMPLETED", "CANCELLED"]}
        else:
            # Only active games
            status_filter = {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        
        # Get user's bets
        bets = await db.games.find({
            "$or": [
                {"creator_id": user_id},
                {"opponent_id": user_id}
            ],
            "status": status_filter
        }).sort("created_at", -1).to_list(100)
        
        # Process bets data
        bets_data = []
        for bet in bets:
            opponent_id = bet.get("opponent_id") if bet.get("creator_id") == user_id else bet.get("creator_id")
            opponent = None
            if opponent_id:
                # Check if opponent is a user
                opponent_doc = await db.users.find_one({"id": opponent_id})
                if opponent_doc:
                    opponent = opponent_doc.get("username")
                else:
                    # Check if opponent is a bot
                    bot_doc = await db.bots.find_one({"id": opponent_id})
                    if bot_doc:
                        opponent = f"Bot: {bot_doc.get('name', 'Unknown')}"
                    else:
                        opponent = "Unknown"
            
            # Calculate bet age in hours
            bet_age_hours = (datetime.utcnow() - bet.get("created_at")).total_seconds() / 3600
            
            bets_data.append({
                "id": bet.get("id"),
                "amount": bet.get("bet_amount"),
                "status": bet.get("status"),
                "created_at": bet.get("created_at"),
                "completed_at": bet.get("completed_at"),
                "cancelled_at": bet.get("cancelled_at"),
                "opponent": opponent,
                "is_creator": bet.get("creator_id") == user_id,
                "gems": bet.get("bet_gems", {}),
                "opponent_gems": bet.get("opponent_gems", {}),
                "winner_id": bet.get("winner_id"),
                "age_hours": round(bet_age_hours, 1),
                "is_stuck": bet_age_hours > 24 and bet.get("status") in ["WAITING", "ACTIVE", "REVEAL"],
                "can_cancel": bet.get("status") == "WAITING"
            })
        
        # Count different types
        active_count = len([b for b in bets_data if b["status"] in ["WAITING", "ACTIVE", "REVEAL"]])
        completed_count = len([b for b in bets_data if b["status"] == "COMPLETED"])
        cancelled_count = len([b for b in bets_data if b["status"] == "CANCELLED"])
        stuck_count = len([b for b in bets_data if b["is_stuck"]])
        
        return {
            "user_id": user_id,
            "username": user.get("username"),
            "active_bets": bets_data,
            "summary": {
                "total_bets": len(bets_data),
                "active_count": active_count,
                "completed_count": completed_count,
                "cancelled_count": cancelled_count,
                "stuck_count": stuck_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user bets"
        )

@api_router.post("/admin/users/{user_id}/bets/{bet_id}/cancel", response_model=dict)
async def cancel_user_bet(
    user_id: str,
    bet_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Cancel a specific bet for a user (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Find the bet/game
        game = await db.games.find_one({"id": bet_id})
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bet not found"
            )
        
        # Check if user is involved in this game
        if game.get("creator_id") != user_id and game.get("opponent_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not involved in this bet"
            )
        
        # Check if bet can be cancelled (only WAITING games can be cancelled)
        if game.get("status") not in ["WAITING"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel bet with status: {game.get('status')}. Only WAITING bets can be cancelled."
            )
        
        # Cancel the game
        await db.games.update_one(
            {"id": bet_id},
            {
                "$set": {
                    "status": "CANCELLED",
                    "cancelled_at": datetime.utcnow(),
                    "cancelled_by": "admin",
                    "cancel_reason": f"Cancelled by admin {current_user.username}"
                }
            }
        )
        
        # Return gems to the creator (since it's a WAITING game, only creator has bet)
        creator_id = game.get("creator_id")
        bet_gems = game.get("bet_gems", {})
        
        for gem_type, quantity in bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": creator_id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Return commission balance
        commission_amount = game.get("bet_amount", 0) * 0.06
        creator_user = await db.users.find_one({"id": creator_id})
        if creator_user:
            await db.users.update_one(
                {"id": creator_id},
                {
                    "$inc": {
                        "virtual_balance": commission_amount,
                        "frozen_balance": -commission_amount
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "cancel_user_bet",
            "target_user_id": user_id,
            "bet_id": bet_id,
            "details": {
                "bet_amount": game.get("bet_amount"),
                "bet_status": game.get("status"),
                "gems_returned": bet_gems,
                "commission_returned": commission_amount
            },
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Bet cancelled successfully",
            "bet_id": bet_id,
            "gems_returned": bet_gems,
            "commission_returned": commission_amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling user bet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel bet"
        )

@api_router.post("/admin/users/{user_id}/bets/cleanup-stuck", response_model=dict)
async def cleanup_stuck_bets(
    user_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Clean up stuck/hanging bets for a user (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Define cutoff time (24 hours ago)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Find stuck bets - games that are in problematic states for more than 24 hours
        stuck_games = await db.games.find({
            "$or": [
                {"creator_id": user_id},
                {"opponent_id": user_id}
            ],
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]},
            "created_at": {"$lt": cutoff_time}
        }).to_list(100)
        
        cleanup_results = {
            "total_processed": 0,
            "cancelled_games": [],
            "total_gems_returned": {},
            "total_commission_returned": 0
        }
        
        for game in stuck_games:
            game_id = game.get("id")
            game_status = game.get("status")
            creator_id = game.get("creator_id")
            opponent_id = game.get("opponent_id")
            bet_amount = game.get("bet_amount", 0)
            bet_gems = game.get("bet_gems", {})
            opponent_gems = game.get("opponent_gems", {})
            
            # Cancel the game
            await db.games.update_one(
                {"id": game_id},
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": datetime.utcnow(),
                        "cancelled_by": "admin_cleanup",
                        "cancel_reason": f"Auto-cancelled by admin cleanup - stuck for >24h in status {game_status}"
                    }
                }
            )
            
            commission_returned = 0
            
            # Return resources based on game status
            if game_status == "WAITING":
                # Only creator has bet, return their resources
                for gem_type, quantity in bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": creator_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    cleanup_results["total_gems_returned"][gem_type] = cleanup_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return commission to creator
                commission_amount = bet_amount * 0.06
                creator_user = await db.users.find_one({"id": creator_id})
                if creator_user:
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                    
            elif game_status in ["ACTIVE", "REVEAL"]:
                # Both players have bet, return resources to both
                
                # Return creator's resources
                for gem_type, quantity in bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": creator_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    cleanup_results["total_gems_returned"][gem_type] = cleanup_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return opponent's resources (use opponent_gems if available, otherwise bet_gems)
                opponent_bet_gems = opponent_gems if opponent_gems else bet_gems
                for gem_type, quantity in opponent_bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": opponent_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    cleanup_results["total_gems_returned"][gem_type] = cleanup_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return commission to both players
                commission_amount = bet_amount * 0.06
                
                # Return to creator
                creator_user = await db.users.find_one({"id": creator_id})
                if creator_user:
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                
                # Return to opponent (if they're a user, not a bot)
                if opponent_id:
                    opponent_user = await db.users.find_one({"id": opponent_id})
                    if opponent_user:
                        await db.users.update_one(
                            {"id": opponent_id},
                            {
                                "$inc": {
                                    "virtual_balance": commission_amount,
                                    "frozen_balance": -commission_amount
                                },
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        commission_returned += commission_amount
            
            cleanup_results["cancelled_games"].append({
                "game_id": game_id,
                "status": game_status,
                "bet_amount": bet_amount,
                "created_at": game.get("created_at"),
                "age_hours": (datetime.utcnow() - game.get("created_at")).total_seconds() / 3600
            })
            cleanup_results["total_commission_returned"] += commission_returned
            cleanup_results["total_processed"] += 1
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "cleanup_stuck_bets",
            "target_user_id": user_id,
            "details": cleanup_results,
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Cleaned up {cleanup_results['total_processed']} stuck bets",
            **cleanup_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up stuck bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup stuck bets"
        )

@api_router.get("/admin/bets/stats", response_model=dict)
async def get_all_bets_stats(current_user: User = Depends(get_current_admin)):
    """Get comprehensive statistics for all bets in the system."""
    try:
        # Get total counts by status
        total_bets = await db.games.count_documents({})
        active_bets = await db.games.count_documents({"status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}})
        completed_bets = await db.games.count_documents({"status": "COMPLETED"})
        cancelled_bets = await db.games.count_documents({"status": "CANCELLED"})
        
        # Get stuck bets (older than 24 hours and still in problematic states)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        stuck_bets = await db.games.count_documents({
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]},
            "created_at": {"$lt": cutoff_time}
        })
        
        # Calculate total bet value
        pipeline = [
            {"$group": {
                "_id": None,
                "total_value": {"$sum": "$bet_amount"},
                "average_bet": {"$avg": "$bet_amount"}
            }}
        ]
        
        result = await db.games.aggregate(pipeline).to_list(1)
        total_bets_value = result[0]["total_value"] if result else 0
        average_bet = result[0]["average_bet"] if result else 0
        
        return {
            "total_bets": total_bets,
            "total_bets_value": total_bets_value,
            "active_bets": active_bets,
            "completed_bets": completed_bets,
            "cancelled_bets": cancelled_bets,
            "stuck_bets": stuck_bets,
            "average_bet": average_bet
        }
        
    except Exception as e:
        logger.error(f"Error fetching bets stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bets statistics"
        )

@api_router.get("/admin/bets/list", response_model=dict)
async def get_all_bets(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    include_bots: bool = True,
    current_user: User = Depends(get_current_admin)
):
    """Get paginated list of all bets in the system."""
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
        
        # Build query
        query = {}
        if status:
            query["status"] = status
        if user_id:
            query["$or"] = [
                {"creator_id": user_id},
                {"opponent_id": user_id}
            ]
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count
        total_count = await db.games.count_documents(query)
        
        # Get games with pagination
        games = await db.games.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        
        # Process games data
        bets_data = []
        for game in games:
            creator_id = game.get("creator_id")
            opponent_id = game.get("opponent_id")
            
            # Get creator info
            creator_info = {"id": creator_id, "username": "Unknown", "email": "", "type": "user"}
            if creator_id:
                user_doc = await db.users.find_one({"id": creator_id})
                if user_doc:
                    creator_info.update({
                        "username": user_doc.get("username", "Unknown"),
                        "email": user_doc.get("email", ""),
                        "type": "user"
                    })
                else:
                    # Check if it's a bot
                    bot_doc = await db.bots.find_one({"id": creator_id})
                    if bot_doc:
                        creator_info.update({
                            "username": f"Bot: {bot_doc.get('name', 'Unknown')}",
                            "email": "",
                            "type": "bot"
                        })
            
            # Get opponent info
            opponent_info = None
            if opponent_id:
                opponent_info = {"id": opponent_id, "username": "Unknown", "email": "", "type": "user"}
                user_doc = await db.users.find_one({"id": opponent_id})
                if user_doc:
                    opponent_info.update({
                        "username": user_doc.get("username", "Unknown"),
                        "email": user_doc.get("email", ""),
                        "type": "user"
                    })
                else:
                    # Check if it's a bot
                    bot_doc = await db.bots.find_one({"id": opponent_id})
                    if bot_doc:
                        opponent_info.update({
                            "username": f"Bot: {bot_doc.get('name', 'Unknown')}",
                            "email": "",
                            "type": "bot"
                        })
            
            # Calculate bet age in hours
            bet_age_hours = (datetime.utcnow() - game.get("created_at")).total_seconds() / 3600
            
            bets_data.append({
                "id": game.get("id"),
                "bet_amount": game.get("bet_amount"),
                "status": game.get("status"),
                "created_at": game.get("created_at"),
                "completed_at": game.get("completed_at"),
                "cancelled_at": game.get("cancelled_at"),
                "creator": creator_info,
                "opponent": opponent_info,
                "bet_gems": game.get("bet_gems", {}),
                "opponent_gems": game.get("opponent_gems", {}),
                "winner_id": game.get("winner_id"),
                "commission_amount": game.get("commission_amount", game.get("bet_amount", 0) * 0.06),
                "age_hours": round(bet_age_hours, 1),
                "is_stuck": bet_age_hours > 24 and game.get("status") in ["WAITING", "ACTIVE", "REVEAL"],
                "can_cancel": game.get("status") == "WAITING",
                "creator_move": game.get("creator_move"),
                "opponent_move": game.get("opponent_move"),
                "is_bot_game": creator_info["type"] == "bot" or (opponent_info and opponent_info["type"] == "bot")
            })
        
        # Calculate pagination info
        if limit <= 0:
            limit = 10  # Безопасное значение по умолчанию
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        # Calculate summary for current page
        stuck_count = len([b for b in bets_data if b["is_stuck"]])
        bot_games_count = len([b for b in bets_data if b["is_bot_game"]])
        
        return {
            "bets": bets_data,
            "pagination": {
                "total_count": total_count,
                "current_page": page,
                "total_pages": total_pages,
                "items_per_page": limit,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "summary": {
                "page_count": len(bets_data),
                "stuck_count": stuck_count,
                "bot_games_count": bot_games_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bets list"
        )

@api_router.post("/admin/bets/{bet_id}/cancel", response_model=dict)
async def cancel_any_bet(
    bet_id: str,
    cancel_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Cancel any bet in the system (admin only)."""
    try:
        # Find the bet/game
        game = await db.games.find_one({"id": bet_id})
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bet not found"
            )
        
        # Check if bet can be cancelled (only WAITING games can be cancelled)
        if game.get("status") not in ["WAITING"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel bet with status: {game.get('status')}. Only WAITING bets can be cancelled."
            )
        
        cancel_reason = cancel_data.get("reason", f"Cancelled by admin {current_user.username}")
        
        # Cancel the game
        await db.games.update_one(
            {"id": bet_id},
            {
                "$set": {
                    "status": "CANCELLED",
                    "cancelled_at": datetime.utcnow(),
                    "cancelled_by": "admin",
                    "cancel_reason": cancel_reason
                }
            }
        )
        
        # Return gems to the creator (since it's a WAITING game, only creator has bet)
        creator_id = game.get("creator_id")
        bet_gems = game.get("bet_gems", {})
        
        for gem_type, quantity in bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": creator_id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Return commission balance (only if creator is a user, not a bot)
        commission_amount = game.get("bet_amount", 0) * 0.06
        creator_user = await db.users.find_one({"id": creator_id})
        if creator_user:
            await db.users.update_one(
                {"id": creator_id},
                {
                    "$inc": {
                        "virtual_balance": commission_amount,
                        "frozen_balance": -commission_amount
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "cancel_bet",
            "target_bet_id": bet_id,
            "details": {
                "bet_amount": game.get("bet_amount"),
                "bet_status": game.get("status"),
                "creator_id": creator_id,
                "gems_returned": bet_gems,
                "commission_returned": commission_amount if creator_user else 0,
                "reason": cancel_reason
            },
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Bet cancelled successfully",
            "bet_id": bet_id,
            "gems_returned": bet_gems,
            "commission_returned": commission_amount if creator_user else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling bet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel bet"
        )

@api_router.post("/admin/bets/cleanup-stuck", response_model=dict)
async def cleanup_all_stuck_bets(current_user: User = Depends(get_current_admin)):
    """Clean up all stuck/hanging bets in the system (admin only)."""
    try:
        # Define cutoff time (24 hours ago)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Find stuck bets - games that are in problematic states for more than 24 hours
        stuck_games = await db.games.find({
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]},
            "created_at": {"$lt": cutoff_time}
        }).to_list(1000)  # Limit to 1000 to prevent memory issues
        
        cleanup_results = {
            "total_processed": 0,
            "cancelled_games": [],
            "total_gems_returned": {},
            "total_commission_returned": 0
        }
        
        for game in stuck_games:
            game_id = game.get("id")
            game_status = game.get("status")
            creator_id = game.get("creator_id")
            opponent_id = game.get("opponent_id")
            bet_amount = game.get("bet_amount", 0)
            bet_gems = game.get("bet_gems", {})
            opponent_gems = game.get("opponent_gems", {})
            
            # Cancel the game
            await db.games.update_one(
                {"id": game_id},
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": datetime.utcnow(),
                        "cancelled_by": "admin_cleanup",
                        "cancel_reason": f"Auto-cancelled by admin cleanup - stuck for >24h in status {game_status}"
                    }
                }
            )
            
            commission_returned = 0
            
            # Return resources based on game status
            if game_status == "WAITING":
                # Only creator has bet, return their resources
                for gem_type, quantity in bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": creator_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    cleanup_results["total_gems_returned"][gem_type] = cleanup_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return commission to creator (only if it's a user)
                commission_amount = bet_amount * 0.06
                creator_user = await db.users.find_one({"id": creator_id})
                if creator_user:
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                    
            elif game_status in ["ACTIVE", "REVEAL"]:
                # Both players have bet, return resources to both
                
                # Return creator's resources
                for gem_type, quantity in bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": creator_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    cleanup_results["total_gems_returned"][gem_type] = cleanup_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return opponent's resources (use opponent_gems if available, otherwise bet_gems)
                opponent_bet_gems = opponent_gems if opponent_gems else bet_gems
                for gem_type, quantity in opponent_bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": opponent_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    cleanup_results["total_gems_returned"][gem_type] = cleanup_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return commission to both players (only if they're users)
                commission_amount = bet_amount * 0.06
                
                # Return to creator
                creator_user = await db.users.find_one({"id": creator_id})
                if creator_user:
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                
                # Return to opponent (if they're a user, not a bot)
                if opponent_id:
                    opponent_user = await db.users.find_one({"id": opponent_id})
                    if opponent_user:
                        await db.users.update_one(
                            {"id": opponent_id},
                            {
                                "$inc": {
                                    "virtual_balance": commission_amount,
                                    "frozen_balance": -commission_amount
                                },
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        commission_returned += commission_amount
            
            cleanup_results["cancelled_games"].append({
                "game_id": game_id,
                "status": game_status,
                "bet_amount": bet_amount,
                "created_at": game.get("created_at"),
                "age_hours": (datetime.utcnow() - game.get("created_at")).total_seconds() / 3600
            })
            cleanup_results["total_commission_returned"] += commission_returned
            cleanup_results["total_processed"] += 1
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "cleanup_all_stuck_bets",
            "details": cleanup_results,
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Cleaned up {cleanup_results['total_processed']} stuck bets",
            **cleanup_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up stuck bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup stuck bets"
        )

@api_router.post("/admin/bets/reset-all", response_model=dict)
async def reset_all_bets(current_user: User = Depends(get_current_super_admin)):
    """Reset all active bets in the system (SUPER_ADMIN only)."""
    try:
        # Find all active games
        active_games = await db.games.find({
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        }).to_list(10000)  # Limit to prevent memory issues
        
        reset_results = {
            "total_processed": 0,
            "cancelled_games": [],
            "total_gems_returned": {},
            "total_commission_returned": 0,
            "users_affected": set(),
            "bots_affected": set()
        }
        
        for game in active_games:
            game_id = game.get("id")
            game_status = game.get("status")
            creator_id = game.get("creator_id")
            opponent_id = game.get("opponent_id")
            bet_amount = game.get("bet_amount", 0)
            bet_gems = game.get("bet_gems", {})
            opponent_gems = game.get("opponent_gems", {})
            
            # Cancel the game
            await db.games.update_one(
                {"id": game_id},
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": datetime.utcnow(),
                        "cancelled_by": "admin_reset_all",
                        "cancel_reason": f"Reset all bets by admin {current_user.username}"
                    }
                }
            )
            
            commission_returned = 0
            
            # Return resources based on game status
            if game_status == "WAITING":
                # Only creator has bet, return their resources
                for gem_type, quantity in bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": creator_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    reset_results["total_gems_returned"][gem_type] = reset_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return commission to creator (only if it's a user)
                commission_amount = bet_amount * 0.06
                creator_user = await db.users.find_one({"id": creator_id})
                if creator_user:
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                    reset_results["users_affected"].add(creator_id)
                else:
                    reset_results["bots_affected"].add(creator_id)
                    
            elif game_status in ["ACTIVE", "REVEAL"]:
                # Both players have bet, return resources to both
                
                # Return creator's resources
                for gem_type, quantity in bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": creator_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    reset_results["total_gems_returned"][gem_type] = reset_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return opponent's resources
                opponent_bet_gems = opponent_gems if opponent_gems else bet_gems
                for gem_type, quantity in opponent_bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": opponent_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    reset_results["total_gems_returned"][gem_type] = reset_results["total_gems_returned"].get(gem_type, 0) + quantity
                
                # Return commission to both players
                commission_amount = bet_amount * 0.06
                
                # Return to creator
                creator_user = await db.users.find_one({"id": creator_id})
                if creator_user:
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                    reset_results["users_affected"].add(creator_id)
                else:
                    reset_results["bots_affected"].add(creator_id)
                
                # Return to opponent
                if opponent_id:
                    opponent_user = await db.users.find_one({"id": opponent_id})
                    if opponent_user:
                        await db.users.update_one(
                            {"id": opponent_id},
                            {
                                "$inc": {
                                    "virtual_balance": commission_amount,
                                    "frozen_balance": -commission_amount
                                },
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        commission_returned += commission_amount
                        reset_results["users_affected"].add(opponent_id)
                    else:
                        reset_results["bots_affected"].add(opponent_id)
            
            reset_results["cancelled_games"].append({
                "game_id": game_id,
                "status": game_status,
                "bet_amount": bet_amount,
                "created_at": game.get("created_at")
            })
            reset_results["total_commission_returned"] += commission_returned
            reset_results["total_processed"] += 1
        
        # Convert sets to lists for JSON serialization
        reset_results["users_affected"] = list(reset_results["users_affected"])
        reset_results["bots_affected"] = list(reset_results["bots_affected"])
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "reset_all_bets",
            "details": reset_results,
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Successfully reset {reset_results['total_processed']} active bets",
            **reset_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting all bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset all bets"
        )

@api_router.post("/admin/users/{user_id}/reset-bets", response_model=dict)
async def reset_user_bets(
    user_id: str,
    current_user: User = Depends(get_current_super_admin)
):
    """Reset all bets for a specific user (SUPER_ADMIN only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Find user's active games
        active_games = await db.games.find({
            "$or": [
                {"creator_id": user_id},
                {"opponent_id": user_id}
            ],
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        }).to_list(1000)
        
        reset_results = {
            "total_processed": 0,
            "cancelled_games": [],
            "total_gems_returned": {},
            "total_commission_returned": 0
        }
        
        for game in active_games:
            game_id = game.get("id")
            game_status = game.get("status")
            creator_id = game.get("creator_id")
            opponent_id = game.get("opponent_id")
            bet_amount = game.get("bet_amount", 0)
            bet_gems = game.get("bet_gems", {})
            opponent_gems = game.get("opponent_gems", {})
            
            # Cancel the game
            await db.games.update_one(
                {"id": game_id},
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": datetime.utcnow(),
                        "cancelled_by": "admin_user_reset",
                        "cancel_reason": f"Reset user {user.get('username')} bets by admin {current_user.username}"
                    }
                }
            )
            
            commission_returned = 0
            
            # Return resources based on game status and user role
            if game_status == "WAITING":
                if creator_id == user_id:
                    # User created the game, return their resources
                    for gem_type, quantity in bet_gems.items():
                        await db.user_gems.update_one(
                            {"user_id": user_id, "gem_type": gem_type},
                            {
                                "$inc": {"frozen_quantity": -quantity},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        reset_results["total_gems_returned"][gem_type] = reset_results["total_gems_returned"].get(gem_type, 0) + quantity
                    
                    # Return commission
                    commission_amount = bet_amount * 0.06
                    await db.users.update_one(
                        {"id": user_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                    
            elif game_status in ["ACTIVE", "REVEAL"]:
                # Return user's resources regardless of their role
                if creator_id == user_id:
                    # User is creator
                    for gem_type, quantity in bet_gems.items():
                        await db.user_gems.update_one(
                            {"user_id": user_id, "gem_type": gem_type},
                            {
                                "$inc": {"frozen_quantity": -quantity},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        reset_results["total_gems_returned"][gem_type] = reset_results["total_gems_returned"].get(gem_type, 0) + quantity
                    
                    commission_amount = bet_amount * 0.06
                    await db.users.update_one(
                        {"id": user_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
                    
                elif opponent_id == user_id:
                    # User is opponent
                    opponent_bet_gems = opponent_gems if opponent_gems else bet_gems
                    for gem_type, quantity in opponent_bet_gems.items():
                        await db.user_gems.update_one(
                            {"user_id": user_id, "gem_type": gem_type},
                            {
                                "$inc": {"frozen_quantity": -quantity},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        reset_results["total_gems_returned"][gem_type] = reset_results["total_gems_returned"].get(gem_type, 0) + quantity
                    
                    commission_amount = bet_amount * 0.06
                    await db.users.update_one(
                        {"id": user_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    commission_returned += commission_amount
            
            reset_results["cancelled_games"].append({
                "game_id": game_id,
                "status": game_status,
                "bet_amount": bet_amount,
                "user_role": "creator" if creator_id == user_id else "opponent"
            })
            reset_results["total_commission_returned"] += commission_returned
            reset_results["total_processed"] += 1
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "reset_user_bets",
            "target_user_id": user_id,
            "target_username": user.get("username"),
            "details": reset_results,
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Successfully reset {reset_results['total_processed']} bets for user {user.get('username')}",
            **reset_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting user bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset user bets"
        )

@api_router.post("/admin/bots/{bot_id}/reset-bets", response_model=dict)
async def reset_bot_bets_super_admin(
    bot_id: str,
    current_user: User = Depends(get_current_super_admin)
):
    """Reset all bets for a specific bot (SUPER_ADMIN only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Find bot's active games
        active_games = await db.games.find({
            "$or": [
                {"creator_id": bot_id},
                {"opponent_id": bot_id}
            ],
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        }).to_list(1000)
        
        reset_results = {
            "total_processed": 0,
            "cancelled_games": []
        }
        
        for game in active_games:
            game_id = game.get("id")
            game_status = game.get("status")
            creator_id = game.get("creator_id")
            opponent_id = game.get("opponent_id")
            bet_amount = game.get("bet_amount", 0)
            bet_gems = game.get("bet_gems", {})
            opponent_gems = game.get("opponent_gems", {})
            
            # Cancel the game
            await db.games.update_one(
                {"id": game_id},
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": datetime.utcnow(),
                        "cancelled_by": "admin_bot_reset",
                        "cancel_reason": f"Reset bot {bot.get('name')} bets by admin {current_user.username}"
                    }
                }
            )
            
            # Return resources to users (if any involved)
            if game_status == "WAITING":
                if creator_id != bot_id:  # Creator is a user
                    for gem_type, quantity in bet_gems.items():
                        await db.user_gems.update_one(
                            {"user_id": creator_id, "gem_type": gem_type},
                            {
                                "$inc": {"frozen_quantity": -quantity},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                    
                    commission_amount = bet_amount * 0.06
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    
            elif game_status in ["ACTIVE", "REVEAL"]:
                # Return resources to users involved
                if creator_id != bot_id:  # Creator is a user
                    for gem_type, quantity in bet_gems.items():
                        await db.user_gems.update_one(
                            {"user_id": creator_id, "gem_type": gem_type},
                            {
                                "$inc": {"frozen_quantity": -quantity},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                    
                    commission_amount = bet_amount * 0.06
                    await db.users.update_one(
                        {"id": creator_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                
                if opponent_id != bot_id and opponent_id:  # Opponent is a user
                    opponent_bet_gems = opponent_gems if opponent_gems else bet_gems
                    for gem_type, quantity in opponent_bet_gems.items():
                        await db.user_gems.update_one(
                            {"user_id": opponent_id, "gem_type": gem_type},
                            {
                                "$inc": {"frozen_quantity": -quantity},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                    
                    commission_amount = bet_amount * 0.06
                    await db.users.update_one(
                        {"id": opponent_id},
                        {
                            "$inc": {
                                "virtual_balance": commission_amount,
                                "frozen_balance": -commission_amount
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
            
            reset_results["cancelled_games"].append({
                "game_id": game_id,
                "status": game_status,
                "bet_amount": bet_amount,
                "bot_role": "creator" if creator_id == bot_id else "opponent"
            })
            reset_results["total_processed"] += 1
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "reset_bot_bets",
            "target_bot_id": bot_id,
            "target_bot_name": bot.get("name"),
            "details": reset_results,
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Successfully reset {reset_results['total_processed']} bets for bot {bot.get('name')}",
            **reset_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting bot bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset bot bets"
        )

@api_router.post("/admin/users/reset-all-balances", response_model=dict)
async def reset_all_user_balances(current_user: User = Depends(get_current_super_admin)):
    """Reset all user balances and inventories to default values (SUPER_ADMIN only)."""
    try:
        # Default starting values
        default_balance = 1000.0
        default_gems = {
            "Ruby": 20,      # $100 worth
            "Emerald": 15,   # $150 worth  
            "Sapphire": 10,  # $200 worth
            "Diamond": 8,    # $240 worth
            "Amber": 35,     # $105 worth
            "Topaz": 25,     # $125 worth
            "Onyx": 16       # $80 worth
        }  # Total: ~$1000 worth of gems
        
        # Find all users
        users = await db.users.find({}).to_list(10000)
        
        reset_results = {
            "total_users_processed": 0,
            "users_reset": [],
            "default_balance": default_balance,
            "default_gems": default_gems
        }
        
        for user in users:
            user_id = user.get("id")
            username = user.get("username")
            
            # Reset user balance
            await db.users.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "virtual_balance": default_balance,
                        "frozen_balance": 0.0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Clear existing gems
            await db.user_gems.delete_many({"user_id": user_id})
            
            # Add default gems
            for gem_type, quantity in default_gems.items():
                await db.user_gems.insert_one({
                    "user_id": user_id,
                    "gem_type": gem_type,
                    "quantity": quantity,
                    "frozen_quantity": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
            
            reset_results["users_reset"].append({
                "user_id": user_id,
                "username": username,
                "new_balance": default_balance,
                "new_gems": default_gems
            })
            reset_results["total_users_processed"] += 1
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "reset_all_user_balances",
            "details": reset_results,
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Successfully reset balances and inventories for {reset_results['total_users_processed']} users",
            **reset_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting all user balances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset all user balances"
        )

@api_router.post("/admin/users/{user_id}/reset-balance", response_model=dict)
async def reset_user_balance(
    user_id: str,
    current_user: User = Depends(get_current_super_admin)
):
    """Reset specific user balance and inventory to default values (SUPER_ADMIN only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Default starting values
        default_balance = 1000.0
        default_gems = {
            "Ruby": 20,      # $100 worth
            "Emerald": 15,   # $150 worth  
            "Sapphire": 10,  # $200 worth
            "Diamond": 8,    # $240 worth
            "Amber": 35,     # $105 worth
            "Topaz": 25,     # $125 worth
            "Onyx": 16       # $80 worth
        }  # Total: ~$1000 worth of gems
        
        # Reset user balance
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "virtual_balance": default_balance,
                    "frozen_balance": 0.0,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Clear existing gems
        await db.user_gems.delete_many({"user_id": user_id})
        
        # Add default gems
        for gem_type, quantity in default_gems.items():
            await db.user_gems.insert_one({
                "user_id": user_id,
                "gem_type": gem_type,
                "quantity": quantity,
                "frozen_quantity": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        
        # Log admin action
        admin_log = {
            "admin_id": current_user.id,
            "admin_username": current_user.username,
            "action": "reset_user_balance",
            "target_user_id": user_id,
            "target_username": user.get("username"),
            "details": {
                "new_balance": default_balance,
                "new_gems": default_gems
            },
            "timestamp": datetime.utcnow()
        }
        await db.admin_logs.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Successfully reset balance and inventory for user {user.get('username')}",
            "new_balance": default_balance,
            "new_gems": default_gems
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting user balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset user balance"
        )

# Add SUPER_ADMIN dependency function
async def get_current_super_admin(token: str = Depends(oauth2_scheme)):
    """Get current user and verify SUPER_ADMIN role."""
    try:
        # Decode token to get user ID
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Convert to User object and check SUPER_ADMIN role
    user_obj = User(**user)
    if user_obj.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUPER_ADMIN access required"
        )
    
    return user_obj

@api_router.post("/games/{game_id}/force-complete", response_model=dict)
async def force_complete_game(
    game_id: str,
    current_user: User = Depends(get_current_user)
):
    """Force complete a stuck game (for debugging and recovery)."""
    try:
        # Get the game
        game = await db.games.find_one({"id": game_id})
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        game_obj = Game(**game)
        
        # Check if user is part of this game
        if current_user.id != game_obj.creator_id and current_user.id != game_obj.opponent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not part of this game"
            )
        
        # Check if game is in a problematic state
        if game_obj.status not in [GameStatus.ACTIVE, GameStatus.REVEAL]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in a state that needs force completion"
            )
        
        # If game is stuck in REVEAL phase, handle timeout
        if game_obj.status == GameStatus.REVEAL:
            await handle_game_timeout(game_id)
            return {"message": "Game timeout handled, bet recreated"}
        
        # If game is stuck in ACTIVE phase with missing moves, try to complete it
        if game_obj.status == GameStatus.ACTIVE:
            # Check if we have both moves
            if not game_obj.creator_move or not game_obj.opponent_move:
                # Cancel the game and return resources
                await cancel_stuck_game(game_id)
                return {"message": "Stuck game cancelled, resources returned"}
            else:
                # Try to determine winner
                try:
                    result = await determine_game_winner(game_id)
                    return {"message": "Game completed successfully", "result": result}
                except Exception as e:
                    logger.error(f"Error force completing game: {e}")
                    # If winner determination fails, cancel the game
                    await cancel_stuck_game(game_id)
                    return {"message": "Game cancelled due to completion error, resources returned"}
        
        return {"message": "Game processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error force completing game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to force complete game"
        )

async def cancel_stuck_game(game_id: str):
    """Cancel a stuck game and return all resources to players."""
    try:
        game = await db.games.find_one({"id": game_id})
        if not game:
            return
        
        game_obj = Game(**game)
        
        # Return creator's resources
        for gem_type, quantity in game_obj.bet_gems.items():
            await db.user_gems.update_one(
                {"user_id": game_obj.creator_id, "gem_type": gem_type},
                {
                    "$inc": {"frozen_quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Return creator's commission
        commission = game_obj.bet_amount * 0.03
        await db.users.update_one(
            {"id": game_obj.creator_id},
            {
                "$inc": {
                    "virtual_balance": commission,
                    "frozen_balance": -commission
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Return opponent's resources if they exist
        if game_obj.opponent_id:
            # Check if opponent is a user (not a bot)
            opponent_user = await db.users.find_one({"id": game_obj.opponent_id})
            if opponent_user:
                # Return opponent's gems
                opponent_gems = game_obj.opponent_gems or game_obj.bet_gems
                for gem_type, quantity in opponent_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": game_obj.opponent_id, "gem_type": gem_type},
                        {
                            "$inc": {"frozen_quantity": -quantity},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                
                # Return opponent's commission
                await db.users.update_one(
                    {"id": game_obj.opponent_id},
                    {
                        "$inc": {
                            "virtual_balance": commission,
                            "frozen_balance": -commission
                        },
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
        
        # Update game status to cancelled
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "status": "CANCELLED",
                    "cancelled_at": datetime.utcnow(),
                    "cancel_reason": "Force cancelled due to stuck state"
                }
            }
        )
        
        logger.info(f"Cancelled stuck game {game_id}")
        
    except Exception as e:
        logger.error(f"Error cancelling stuck game {game_id}: {e}")

@api_router.get("/admin/users/{user_id}/stats", response_model=dict)
async def get_user_stats(
    user_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Get comprehensive statistics for a specific user."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Game statistics
        total_games = user.get("total_games_played", 0)
        games_won = user.get("total_games_won", 0)
        games_lost = total_games - games_won
        games_draw = user.get("total_games_draw", 0)
        win_rate = round((games_won / total_games * 100), 1) if total_games > 0 else 0
        
        # Financial statistics (simplified for demo)
        profit = user.get("total_profit", 0.0)
        gifts_sent = user.get("gifts_sent_count", 0)
        gifts_received = user.get("gifts_received_count", 0)
        
        # IP history (simplified for demo)
        ip_history = user.get("ip_history", [user.get("last_ip", "192.168.1.1")])
        if len(ip_history) == 0:
            ip_history = ["192.168.1.1"]
        
        return {
            "user_id": user_id,
            "username": user.get("username"),
            "email": user.get("email"),
            "game_stats": {
                "total_games": total_games,
                "games_won": games_won,
                "games_lost": games_lost,
                "games_draw": games_draw,
                "win_rate": win_rate
            },
            "financial_stats": {
                "current_balance": user.get("virtual_balance", 0),
                "total_profit": profit,
                "gifts_sent": gifts_sent,
                "gifts_received": gifts_received
            },
            "activity_stats": {
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login"),
                "last_ip": user.get("last_ip"),
                "status": user.get("status")
            },
            "ip_history": ip_history[:50]  # Last 50 IPs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user stats"
        )

# ==============================================================================
# ADDITIONAL ADMIN USER MANAGEMENT ENDPOINTS
# ==============================================================================

@api_router.post("/admin/users/{user_id}/gems/freeze", response_model=dict)
async def freeze_user_gems(
    user_id: str,
    freeze_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Freeze specific gems for a user (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        gem_type = freeze_data.get("gem_type")
        quantity = freeze_data.get("quantity", 0)
        reason = freeze_data.get("reason", "Admin action")
        
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0"
            )
        
        # Get user's gem data
        user_gem = await db.user_gems.find_one({"user_id": user_id, "gem_type": gem_type})
        if not user_gem or user_gem.get("quantity", 0) < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient gems to freeze"
            )
        
        # Check available (non-frozen) gems
        available_quantity = user_gem.get("quantity", 0) - user_gem.get("frozen_quantity", 0)
        if available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient available gems to freeze"
            )
        
        # Freeze the gems
        await db.user_gems.update_one(
            {"user_id": user_id, "gem_type": gem_type},
            {
                "$inc": {"frozen_quantity": quantity},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="FREEZE_USER_GEMS",
            target_type="user_gems",
            target_id=user_id,
            details={
                "gem_type": gem_type,
                "quantity": quantity,
                "reason": reason
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        # Send notification to user
        notification = Notification(
            user_id=user_id,
            type="ADMIN_ACTION",
            title="Гемы заморожены",
            message=f"Администратор заморозил {quantity} {gem_type} гемов. Причина: {reason}"
        )
        await db.notifications.insert_one(notification.dict())
        
        return {
            "message": f"Successfully froze {quantity} {gem_type} gems",
            "gem_type": gem_type,
            "quantity": quantity,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error freezing user gems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to freeze user gems"
        )

@api_router.post("/admin/users/{user_id}/gems/unfreeze", response_model=dict)
async def unfreeze_user_gems(
    user_id: str,
    unfreeze_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Unfreeze specific gems for a user (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        gem_type = unfreeze_data.get("gem_type")
        quantity = unfreeze_data.get("quantity", 0)
        reason = unfreeze_data.get("reason", "Admin action")
        
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0"
            )
        
        # Get user's gem data
        user_gem = await db.user_gems.find_one({"user_id": user_id, "gem_type": gem_type})
        if not user_gem or user_gem.get("frozen_quantity", 0) < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient frozen gems to unfreeze"
            )
        
        # Unfreeze the gems
        await db.user_gems.update_one(
            {"user_id": user_id, "gem_type": gem_type},
            {
                "$inc": {"frozen_quantity": -quantity},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="UNFREEZE_USER_GEMS",
            target_type="user_gems",
            target_id=user_id,
            details={
                "gem_type": gem_type,
                "quantity": quantity,
                "reason": reason
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        # Send notification to user
        notification = Notification(
            user_id=user_id,
            type="ADMIN_ACTION",
            title="Гемы разморожены",
            message=f"Администратор разморозил {quantity} {gem_type} гемов. Причина: {reason}"
        )
        await db.notifications.insert_one(notification.dict())
        
        return {
            "message": f"Successfully unfroze {quantity} {gem_type} gems",
            "gem_type": gem_type,
            "quantity": quantity,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfreezing user gems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unfreeze user gems"
        )

@api_router.delete("/admin/users/{user_id}/gems/{gem_type}", response_model=dict)
async def delete_user_gems(
    user_id: str,
    gem_type: str,
    quantity: int,
    reason: str = "Admin action",
    current_user: User = Depends(get_current_admin)
):
    """Delete specific gems from user inventory (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0"
            )
        
        # Get user's gem data
        user_gem = await db.user_gems.find_one({"user_id": user_id, "gem_type": gem_type})
        if not user_gem or user_gem.get("quantity", 0) < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient gems to delete"
            )
        
        # Calculate available (non-frozen) quantity
        available_quantity = user_gem.get("quantity", 0) - user_gem.get("frozen_quantity", 0)
        if available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete frozen gems. Unfreeze them first."
            )
        
        # Delete the gems
        new_quantity = user_gem.get("quantity", 0) - quantity
        if new_quantity <= 0:
            await db.user_gems.delete_one({"user_id": user_id, "gem_type": gem_type})
        else:
            await db.user_gems.update_one(
                {"user_id": user_id, "gem_type": gem_type},
                {
                    "$inc": {"quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="DELETE_USER_GEMS",
            target_type="user_gems",
            target_id=user_id,
            details={
                "gem_type": gem_type,
                "quantity": quantity,
                "reason": reason
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        # Send notification to user
        notification = Notification(
            user_id=user_id,
            type="ADMIN_ACTION",
            title="Гемы удалены",
            message=f"Администратор удалил {quantity} {gem_type} гемов из вашего инвентаря. Причина: {reason}"
        )
        await db.notifications.insert_one(notification.dict())
        
        return {
            "message": f"Successfully deleted {quantity} {gem_type} gems",
            "gem_type": gem_type,
            "quantity": quantity,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user gems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user gems"
        )

@api_router.post("/admin/users/{user_id}/gems/modify", response_model=dict)
async def modify_user_gems(
    user_id: str,
    modify_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Modify (increase/decrease) specific gems for a user (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        gem_type = modify_data.get("gem_type")
        change = modify_data.get("change", 0)  # positive to increase, negative to decrease
        reason = modify_data.get("reason", "Admin action")
        notification_message = modify_data.get("notification", "")
        
        if change == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Change amount must not be zero"
            )
        
        # Get user's gem data
        user_gem = await db.user_gems.find_one({"user_id": user_id, "gem_type": gem_type})
        
        if change < 0:  # Decreasing gems
            if not user_gem or user_gem.get("quantity", 0) < abs(change):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient gems to decrease"
                )
            
            # Check if trying to decrease below frozen amount
            frozen_quantity = user_gem.get("frozen_quantity", 0)
            new_total = user_gem.get("quantity", 0) + change
            if new_total < frozen_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot decrease below frozen amount"
                )
        
        # Apply the change
        if not user_gem and change > 0:
            # Create new gem entry
            new_gem = {
                "user_id": user_id,
                "gem_type": gem_type,
                "quantity": change,
                "frozen_quantity": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.user_gems.insert_one(new_gem)
        else:
            # Update existing gem
            new_quantity = user_gem.get("quantity", 0) + change
            if new_quantity <= 0:
                await db.user_gems.delete_one({"user_id": user_id, "gem_type": gem_type})
            else:
                await db.user_gems.update_one(
                    {"user_id": user_id, "gem_type": gem_type},
                    {
                        "$inc": {"quantity": change},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="MODIFY_USER_GEMS",
            target_type="user_gems",
            target_id=user_id,
            details={
                "gem_type": gem_type,
                "change": change,
                "reason": reason
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        # Send notification to user
        action_word = "добавил" if change > 0 else "удалил"
        default_message = f"Администратор {action_word} {abs(change)} {gem_type} гемов"
        
        notification = Notification(
            user_id=user_id,
            type="ADMIN_ACTION",
            title="Изменение гемов",
            message=notification_message or default_message
        )
        await db.notifications.insert_one(notification.dict())
        
        return {
            "message": f"Successfully modified {gem_type} gems by {change}",
            "gem_type": gem_type,
            "change": change,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying user gems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to modify user gems"
        )

@api_router.post("/admin/users/{user_id}/flag-suspicious", response_model=dict)
async def flag_user_suspicious(
    user_id: str,
    flag_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Flag or unflag user as suspicious (admin only)."""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        is_suspicious = flag_data.get("is_suspicious", False)
        reason = flag_data.get("reason", "Admin action")
        
        # Update user's suspicious flag
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "is_suspicious": is_suspicious,
                    "suspicious_reason": reason if is_suspicious else None,
                    "suspicious_flagged_at": datetime.utcnow() if is_suspicious else None,
                    "suspicious_flagged_by": current_user.id if is_suspicious else None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="FLAG_SUSPICIOUS" if is_suspicious else "UNFLAG_SUSPICIOUS",
            target_type="user",
            target_id=user_id,
            details={
                "is_suspicious": is_suspicious,
                "reason": reason
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        # Send notification to user if flagged
        if is_suspicious:
            notification = Notification(
                user_id=user_id,
                type="ADMIN_WARNING",
                title="Аккаунт отмечен",
                message=f"Ваш аккаунт отмечен администрацией за подозрительную активность. Причина: {reason}"
            )
            await db.notifications.insert_one(notification.dict())
        
        action = "flagged as suspicious" if is_suspicious else "unflagged"
        return {
            "message": f"User successfully {action}",
            "user_id": user_id,
            "is_suspicious": is_suspicious,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error flagging user as suspicious: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to flag user"
        )

# ==============================================================================
# BOT MANAGEMENT SYSTEM ENDPOINTS
# ==============================================================================

@api_router.post("/admin/bots/toggle-all", response_model=dict)
async def toggle_all_bots(
    toggle_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Enable or disable all bots (admin only)."""
    try:
        enabled = toggle_data.get("enabled", True)
        
        # Update all bots
        result = await db.bots.update_many(
            {},
            {
                "$set": {
                    "is_active": enabled,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="TOGGLE_ALL_BOTS",
            target_type="bots",
            target_id="all",
            details={
                "enabled": enabled,
                "bots_affected": result.modified_count
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        action = "включены" if enabled else "отключены"
        return {
            "message": f"Все боты {action}",
            "enabled": enabled,
            "bots_affected": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error toggling all bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle bots"
        )

@api_router.get("/admin/bets/stats", response_model=dict)
async def get_bets_stats(current_user: User = Depends(get_current_admin)):
    """Get comprehensive betting statistics."""
    try:
        # Total bets
        total_bets = await db.games.count_documents({})
        total_bets_value = await db.games.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$bet_amount"}}}
        ]).to_list(1)
        total_value = total_bets_value[0]["total"] if total_bets_value else 0
        
        # Active bets
        active_bets = await db.games.count_documents({"status": "WAITING"})
        
        # Completed bets
        completed_bets = await db.games.count_documents({"status": "COMPLETED"})
        
        # Cancelled bets
        cancelled_bets = await db.games.count_documents({"status": "CANCELLED"})
        
        # Expired bets (older than 24 hours in WAITING status)
        yesterday = datetime.utcnow() - timedelta(days=1)
        expired_bets = await db.games.count_documents({
            "status": "WAITING",
            "created_at": {"$lt": yesterday}
        })
        
        # Average bet amount
        avg_bet = await db.games.aggregate([
            {"$group": {"_id": None, "avg": {"$avg": "$bet_amount"}}}
        ]).to_list(1)
        average_bet = avg_bet[0]["avg"] if avg_bet else 0
        
        return {
            "total_bets": total_bets,
            "total_bets_value": round(total_value, 2),
            "active_bets": active_bets,
            "completed_bets": completed_bets,
            "cancelled_bets": cancelled_bets,
            "expired_bets": expired_bets,
            "average_bet": round(average_bet, 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching bet stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bet statistics"
        )

@api_router.post("/admin/bots/create-regular", response_model=dict)
async def create_regular_bots(
    bot_config: dict,
    current_user: User = Depends(get_current_admin)
):
    """Create regular bots (admin only) - ОБНОВЛЕНО для новой системы."""
    try:
        # Параметры согласно новой спецификации (убрано поле count)
        min_bet = bot_config.get("min_bet_amount", 1.0)  # 1-10000
        max_bet = bot_config.get("max_bet_amount", 50.0)  # 1-10000
        win_rate = bot_config.get("win_percentage", 55.0) / 100.0  # 0-100% -> 0.0-1.0
        cycle_games = bot_config.get("cycle_games", 12)  # 1-66
        individual_limit = bot_config.get("individual_limit", cycle_games)  # 1-66
        creation_mode = bot_config.get("creation_mode", "queue-based")
        priority_order = bot_config.get("priority_order", 50)  # 1-100
        pause_between_games = bot_config.get("pause_between_games", 5)  # 1-300
        profit_strategy = bot_config.get("profit_strategy", "balanced")
        
        # Генерация уникального имени бота
        bot_name = bot_config.get("name", "").strip()
        if not bot_name:
            # Автоматически генерируем уникальное имя Bot#
            bot_name = await generate_unique_bot_name()
        else:
            # Проверяем, что имя не дублируется
            existing_bot = await db.bots.find_one({"name": bot_name})
            if existing_bot:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Бот с именем '{bot_name}' уже существует"
                )
        
        created_bots = []
        
        # Создаем только одного бота (убрано поле count)
        bot = Bot(
            name=bot_name,
            bot_type=BotType.REGULAR,
            min_bet_amount=min_bet,
            max_bet_amount=max_bet,
            win_rate=win_rate,
            cycle_games=cycle_games,
            current_limit=individual_limit,
            individual_limit=individual_limit,
            creation_mode=creation_mode,
            priority_order=priority_order,
            pause_between_games=pause_between_games,
            profit_strategy=profit_strategy,
            is_active=True
        )
        
        await db.bots.insert_one(bot.dict())
        created_bots.append(bot.id)
        
        # Логируем создание через новую систему
        await regular_bot_system.log_bot_action(bot.id, "BOT_CREATED", {
            "config": bot_config,
            "admin_id": current_user.id
        })
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="CREATE_REGULAR_BOT",
            target_type="bots",
            target_id=bot.id,
            details={
                "bot_name": bot_name,
                "config": bot_config
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        logger.info(f"✅ Created regular bot '{bot_name}' with new system")
        
        return {
            "message": f"Создан обычный бот '{bot_name}'",
            "created_bots": created_bots,
            "bot_name": bot_name
        }
        
    except Exception as e:
        logger.error(f"Error creating regular bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create regular bot"
        )

@api_router.post("/admin/bots/start-regular", response_model=dict)
async def start_regular_bots(
    current_user: User = Depends(get_current_admin)
):
    """Start all regular bots to create bets."""
    try:
        # Получаем настройки ботов
        settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_active_bets = settings.get("max_active_bets_regular", 50) if settings else 50
        
        # Проверяем текущее количество активных ставок обычных ботов
        current_active_bets = await db.games.count_documents({
            "creator_type": "bot",
            "is_bot_game": True,
            "status": "WAITING",
            "$or": [
                {"bot_type": "REGULAR"},
                {"metadata.bot_type": "REGULAR"}
            ]
        })
        
        if current_active_bets >= max_active_bets:
            return {
                "message": f"Лимит активных ставок достигнут ({current_active_bets}/{max_active_bets})",
                "started_bots": 0,
                "current_active_bets": current_active_bets,
                "max_active_bets": max_active_bets,
                "limit_reached": True
            }
        
        # Получаем всех активных обычных ботов с учетом режимов создания ставок
        active_bots = await db.bots.find({
            "type": "REGULAR",
            "is_active": True
        }).to_list(100)
        
        if not active_bots:
            # Создаем ботов если их нет
            await create_regular_bots(
                {"count": 5, "min_bet_amount": 1.0, "max_bet_amount": 50.0},
                current_user
            )
            active_bots = await db.bots.find({
                "type": "REGULAR",
                "is_active": True
            }).to_list(100)
        
        # Сортируем ботов по режимам создания ставок и приоритетам
        def sort_bots_by_creation_mode(bots):
            """Сортировка ботов по режимам создания ставок и приоритету."""
            always_first_bots = []
            queue_based_bots = []
            after_all_bots = []
            
            for bot in bots:
                creation_mode = bot.get("creation_mode", "queue-based")
                if creation_mode == "always-first":
                    always_first_bots.append(bot)
                elif creation_mode == "after-all":
                    after_all_bots.append(bot)
                else:  # queue-based
                    queue_based_bots.append(bot)
            
            # Сортируем каждую группу по приоритету
            always_first_bots.sort(key=lambda x: x.get("priority_order", 999))
            queue_based_bots.sort(key=lambda x: x.get("priority_order", 999))
            after_all_bots.sort(key=lambda x: x.get("priority_order", 999))
            
            # Возвращаем отсортированный список: Always-first -> Queue-based -> After-all
            return always_first_bots + queue_based_bots + after_all_bots
        
        sorted_bots = sort_bots_by_creation_mode(active_bots)
        
        started_bots = 0
        available_slots = max_active_bets - current_active_bets
        
        # Обрабатываем ботов в отсортированном порядке
        for bot_doc in sorted_bots:
            if started_bots >= available_slots:
                break  # Достигнут лимит активных ставок
                
            bot = Bot(**bot_doc)
            creation_mode = bot_doc.get("creation_mode", "queue-based")
            
            # Проверяем, не создавал ли бот ставку недавно
            now = datetime.utcnow()
            if bot.last_bet_time:
                time_since_last_bet = (now - bot.last_bet_time).total_seconds()
                if time_since_last_bet < bot.recreate_timer:
                    continue
            
            # Специальная логика для режима "after-all"
            if creation_mode == "after-all":
                # Проверяем, что все always-first и queue-based боты уже активны
                other_bots_active = await db.games.count_documents({
                    "creator_type": "bot",
                    "bot_type": "REGULAR",
                    "status": {"$in": ["WAITING", "ACTIVE"]},
                    "creator_id": {"$ne": bot.id}
                })
                
                # Получаем количество always-first и queue-based ботов
                priority_bots_count = await db.bots.count_documents({
                    "type": "REGULAR",
                    "is_active": True,
                    "creation_mode": {"$in": ["always-first", "queue-based"]},
                    "id": {"$ne": bot.id}
                })
                
                # Если есть приоритетные боты, но они еще не создали ставки, пропускаем
                if priority_bots_count > 0 and other_bots_active < priority_bots_count:
                    continue
            
            # Создаем ставку для бота
            success = await create_bot_bet(bot)
            if success:
                started_bots += 1
                
                # Обновляем время последней ставки
                await db.bots.update_one(
                    {"id": bot.id},
                    {
                        "$set": {
                            "last_bet_time": now,
                            "updated_at": now
                        }
                    }
                )
        
        # Обновляем статистику активных ставок
        final_active_bets = current_active_bets + started_bots
        
        return {
            "message": f"Запущено {started_bots} ботов",
            "started_bots": started_bots,
            "total_active_bots": len(active_bots),
            "current_active_bets": final_active_bets,
            "max_active_bets": max_active_bets,
            "available_slots": max(0, max_active_bets - final_active_bets),
            "limit_reached": final_active_bets >= max_active_bets
        }
        
    except Exception as e:
        logger.error(f"Error starting regular bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start regular bots"
        )

async def create_bot_bet(bot: Bot) -> bool:
    """Create a bet for a bot with creation mode support."""
    try:
        import random
        
        # ============ ПРОВЕРКА ГЛОБАЛЬНЫХ ЛИМИТОВ ============
        # Получаем глобальные настройки
        bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_active_bets_regular = bot_settings.get("max_active_bets_regular", 50) if bot_settings else 50
        max_active_bets_human = bot_settings.get("max_active_bets_human", 30) if bot_settings else 30
        
        # Получаем информацию о боте из базы данных для режима создания ставок
        bot_doc = await db.bots.find_one({"id": bot.id})
        creation_mode = bot_doc.get("creation_mode", "queue-based") if bot_doc else "queue-based"
        bot_type = bot_doc.get("bot_type", "REGULAR") if bot_doc else "REGULAR"
        
        # Подсчитываем текущие активные ставки по типу бота
        if bot_type == "REGULAR":
            current_active_bets = await db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "REGULAR"},
                    {"metadata.bot_type": "REGULAR"}
                ]
            })
            max_limit = max_active_bets_regular
        else:  # HUMAN
            current_active_bets = await db.games.count_documents({
                "creator_type": "bot",
                "is_bot_game": True,
                "status": "WAITING",
                "$or": [
                    {"bot_type": "HUMAN"},
                    {"metadata.bot_type": "HUMAN"}
                ]
            })
            max_limit = max_active_bets_human
        
        # Проверяем глобальный лимит
        if current_active_bets >= max_limit:
            logger.info(f"🚫 Global limit reached for {bot_type} bots: {current_active_bets}/{max_limit}")
            return False
        
        # ============ ПРОВЕРКА ИНДИВИДУАЛЬНЫХ ЛИМИТОВ ============
        # Получаем текущие активные ставки этого конкретного бота
        bot_active_bets = await db.games.count_documents({
            "creator_id": bot.id,
            "status": "WAITING"
        })
        
        # Проверяем индивидуальный лимит бота
        individual_limit = bot_doc.get("current_limit") or bot_doc.get("cycle_games", 12)
        if bot_active_bets >= individual_limit:
            logger.info(f"🚫 Individual limit reached for bot {bot.id}: {bot_active_bets}/{individual_limit}")
            return False
        
        # Передаем данные поведения бота в объект для should_bot_win
        if bot_doc:
            bot._bot_data = bot_doc
        
        # Для режима "always-first" проверяем дополнительные условия
        if creation_mode == "always-first":
            # Всегда создаем ставку для always-first ботов (в рамках лимитов)
            logger.info(f"Creating bet for always-first bot {bot.id}")
        
        # Для режима "queue-based" используем стандартную логику
        elif creation_mode == "queue-based":
            # Проверяем приоритет в очереди
            logger.info(f"Creating bet for queue-based bot {bot.id} with priority {bot_doc.get('priority_order', 999)}")
        
        # Для режима "after-all" дополнительных проверок уже было выше
        elif creation_mode == "after-all":
            logger.info(f"Creating bet for after-all bot {bot.id}")
        
        # Генерируем размер ставки
        bet_amount = round(random.uniform(bot.min_bet_amount, bot.max_bet_amount), 2)
        
        # Создаем случайную комбинацию гемов для ставки
        gem_types = ["RUBY", "EMERALD", "SAPPHIRE", "DIAMOND"]
        bet_gems = {}
        total_value = 0.0
        
        # Распределяем ставку по гемам
        remaining_amount = bet_amount
        for i, gem_type in enumerate(gem_types):
            if i == len(gem_types) - 1:  # Последний гем получает остаток
                gem_value = remaining_amount
            else:
                max_for_this_gem = remaining_amount * 0.7  # Максимум 70% от остатка
                gem_value = round(random.uniform(0.1, max_for_this_gem), 2)
            
            if gem_value > 0:
                gem_price = GEM_PRICES.get(gem_type, 1.0)
                quantity = max(1, int(gem_value / gem_price))
                bet_gems[gem_type] = quantity
                total_value += quantity * gem_price
                remaining_amount -= quantity * gem_price
                
                if remaining_amount <= 0:
                    break
        
        # Создаем игру/ставку
        game = Game(
            creator_id=bot.id,
            creator_type="bot",
            bet_amount=total_value,
            bet_gems=bet_gems,
            status=GameStatus.WAITING,
            commission=round(total_value * 0.06, 2),
            bot_type="REGULAR" if bot.type == BotType.REGULAR else "HUMAN"
        )
        
        
        # Save to database
        await db.games.insert_one(game.dict())
        
        # Update bot stats
        await db.bots.update_one(
            {"id": bot.id},
            {
                "$set": {
                    "current_bet_id": game.id,
                    "updated_at": datetime.utcnow(),
                    "last_game_time": datetime.utcnow()
                },
                "$inc": {
                    "total_bet_amount": total_value
                }
            }
        )
        
        logger.info(f"Bot {bot.name} created gem-based bet {game.id} with total ${total_value} (gems: {bet_gems})")
        return True
        
    except Exception as e:
        logger.error(f"Error creating bot bet: {e}")
        return False

async def get_next_bot_in_queue() -> dict:
    """Get the next bot in queue based on creation mode and priority."""
    try:
        # Получаем глобальные настройки
        bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_active_bets = bot_settings.get("max_active_bets_regular", 50) if bot_settings else 50
        
        # Проверяем текущие активные ставки
        current_active_bets = await db.games.count_documents({
            "creator_type": "bot",
            "bot_type": "REGULAR",
            "status": {"$in": ["WAITING", "ACTIVE"]}
        })
        
        if current_active_bets >= max_active_bets:
            return {"message": "Global bet limit reached", "bot": None}
        
        # Получаем всех активных ботов
        all_bots = await db.bots.find({
            "type": "REGULAR",
            "is_active": True
        }).to_list(100)
        
        # Фильтруем ботов по режимам создания ставок
        always_first_bots = []
        queue_based_bots = []
        after_all_bots = []
        
        for bot in all_bots:
            # Проверяем индивидуальные лимиты бота
            max_individual_bets = bot.get("max_individual_bets", 12)
            current_bot_bets = await db.games.count_documents({
                "creator_id": bot["id"],
                "creator_type": "bot",
                "status": {"$in": ["WAITING", "ACTIVE"]}
            })
            
            if current_bot_bets >= max_individual_bets:
                continue  # Бот достиг своего лимита
            
            # Проверяем время последней ставки
            if bot.get("last_bet_time"):
                time_since_last_bet = (datetime.utcnow() - bot["last_bet_time"]).total_seconds()
                if time_since_last_bet < bot.get("recreate_timer", 30):
                    continue  # Бот еще не готов к новой ставке
            
            creation_mode = bot.get("creation_mode", "queue-based")
            if creation_mode == "always-first":
                always_first_bots.append(bot)
            elif creation_mode == "after-all":
                after_all_bots.append(bot)
            else:
                queue_based_bots.append(bot)
        
        # Сортируем по приоритету
        always_first_bots.sort(key=lambda x: x.get("priority_order", 999))
        queue_based_bots.sort(key=lambda x: x.get("priority_order", 999))
        after_all_bots.sort(key=lambda x: x.get("priority_order", 999))
        
        # Выбираем следующего бота
        if always_first_bots:
            return {"message": "Always-first bot selected", "bot": always_first_bots[0]}
        elif queue_based_bots:
            return {"message": "Queue-based bot selected", "bot": queue_based_bots[0]}
        elif after_all_bots:
            # Проверяем, что все приоритетные боты уже создали ставки
            priority_bots_count = len(always_first_bots) + len(queue_based_bots)
            if priority_bots_count == 0:
                return {"message": "After-all bot selected", "bot": after_all_bots[0]}
            else:
                return {"message": "Waiting for priority bots", "bot": None}
        else:
            return {"message": "No bots available", "bot": None}
            
    except Exception as e:
        logger.error(f"Error getting next bot in queue: {e}")
        return {"message": "Error occurred", "bot": None}

@api_router.get("/admin/bots/settings", response_model=dict)
async def get_bot_global_settings_old(current_user: User = Depends(get_current_admin)):
    """Get bot settings."""
    try:
        settings = await db.bot_settings.find_one({"id": "bot_settings"})
        
        if not settings:
            # Create default settings if not exists
            default_settings = {
                "id": "bot_settings",
                "max_active_bets_regular": 50,
                "max_active_bets_human": 30,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.bot_settings.insert_one(default_settings)
            settings = default_settings
        
        return {
            "max_active_bets_regular": settings.get("max_active_bets_regular", 50),
            "max_active_bets_human": settings.get("max_active_bets_human", 30)
        }
        
    except Exception as e:
        logger.error(f"Error fetching bot settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot settings"
        )

@api_router.get("/admin/bots/queue-status", response_model=dict)
async def get_bots_queue_status(current_user: User = Depends(get_current_admin)):
    """Get detailed bot queue status with creation modes."""
    try:
        # Получаем общую информацию о ставках
        total_active_bets = await db.games.count_documents({
            "creator_type": "bot",
            "bot_type": "REGULAR",
            "status": {"$in": ["WAITING", "ACTIVE"]}
        })
        
        # Получаем настройки
        bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_active_bets = bot_settings.get("max_active_bets_regular", 50) if bot_settings else 50
        
        # Получаем всех активных ботов
        all_bots = await db.bots.find({
            "type": "REGULAR",
            "is_active": True
        }).to_list(100)
        
        # Группируем ботов по режимам создания ставок
        modes_info = {
            "always-first": {"bots": [], "active_bets": 0},
            "queue-based": {"bots": [], "active_bets": 0},
            "after-all": {"bots": [], "active_bets": 0}
        }
        
        for bot in all_bots:
            creation_mode = bot.get("creation_mode", "queue-based")
            
            # Подсчитываем активные ставки для каждого бота
            bot_active_bets = await db.games.count_documents({
                "creator_id": bot["id"],
                "creator_type": "bot",
                "status": {"$in": ["WAITING", "ACTIVE"]}
            })
            
            bot_info = {
                "id": bot["id"],
                "name": bot["name"],
                "priority_order": bot.get("priority_order", 999),
                "active_bets": bot_active_bets,
                "max_individual_bets": bot.get("max_individual_bets", 12),
                "last_bet_time": bot.get("last_bet_time"),
                "recreate_timer": bot.get("recreate_timer", 30)
            }
            
            modes_info[creation_mode]["bots"].append(bot_info)
            modes_info[creation_mode]["active_bets"] += bot_active_bets
        
        # Сортируем ботов по приоритету в каждом режиме
        for mode in modes_info:
            modes_info[mode]["bots"].sort(key=lambda x: x["priority_order"])
        
        # Получаем информацию о следующем боте в очереди
        next_bot_info = await get_next_bot_in_queue()
        
        return {
            "total_active_bets": total_active_bets,
            "max_active_bets": max_active_bets,
            "available_slots": max(0, max_active_bets - total_active_bets),
            "modes": modes_info,
            "next_bot": next_bot_info,
            "queue_summary": {
                "always_first_count": len(modes_info["always-first"]["bots"]),
                "queue_based_count": len(modes_info["queue-based"]["bots"]),
                "after_all_count": len(modes_info["after-all"]["bots"]),
                "total_bots": len(all_bots)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting bot queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot queue status"
        )

@api_router.post("/admin/bots/settings", response_model=dict)
async def update_bot_global_settings_old(
    settings_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update bot settings."""
    try:
        max_active_bets_regular = settings_data.get("max_active_bets_regular", 50)
        max_active_bets_human = settings_data.get("max_active_bets_human", 30)
        
        # Validation
        if max_active_bets_regular < 0 or max_active_bets_regular > 1000:
            raise HTTPException(status_code=400, detail="Max active bets for regular bots must be between 0 and 1000")
        
        if max_active_bets_human < 0 or max_active_bets_human > 1000:
            raise HTTPException(status_code=400, detail="Max active bets for human bots must be between 0 and 1000")
        
        # Update settings
        await db.bot_settings.update_one(
            {"id": "bot_settings"},
            {
                "$set": {
                    "max_active_bets_regular": max_active_bets_regular,
                    "max_active_bets_human": max_active_bets_human,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="UPDATE_BOT_SETTINGS",
            target_type="bot_settings",
            target_id="bot_settings",
            details={
                "max_active_bets_regular": max_active_bets_regular,
                "max_active_bets_human": max_active_bets_human
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "message": "Настройки ботов обновлены",
            "max_active_bets_regular": max_active_bets_regular,
            "max_active_bets_human": max_active_bets_human
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot settings"
        )

@api_router.get("/admin/bots/stats/active-bets", response_model=dict)
async def get_active_bets_stats(current_user: User = Depends(get_current_admin)):
    """Get current active bets count for different bot types."""
    try:
        # Count active bets created by regular bots
        regular_bots_active_bets = await db.games.count_documents({
            "creator_type": "bot",
            "bot_type": "REGULAR", 
            "status": {"$in": ["WAITING", "ACTIVE"]}
        })
        
        # Count active bets created by human bots
        human_bots_active_bets = await db.games.count_documents({
            "creator_type": "human_bot",
            "bot_type": "HUMAN",
            "status": {"$in": ["WAITING", "ACTIVE"]}
        })
        
        # Get current settings
        settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_regular = settings.get("max_active_bets_regular", 50) if settings else 50
        max_human = settings.get("max_active_bets_human", 30) if settings else 30
        
        return {
            "regular_bots": {
                "current": regular_bots_active_bets,
                "max": max_regular,
                "available": max(0, max_regular - regular_bots_active_bets),
                "percentage": round((regular_bots_active_bets / max_regular * 100), 1) if max_regular > 0 else 0
            },
            "human_bots": {
                "current": human_bots_active_bets,
                "max": max_human,
                "available": max(0, max_human - human_bots_active_bets),
                "percentage": round((human_bots_active_bets / max_human * 100), 1) if max_human > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching active bets stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active bets stats"
        )

@api_router.post("/admin/bots/create-individual", response_model=dict)
async def create_individual_bot(
    bot_config: dict,
    current_user: User = Depends(get_current_admin)
):
    """Create individual bot with custom settings (admin only)."""
    try:
        name = bot_config.get("name", "Bot #001")
        pause_timer = bot_config.get("pause_timer", 5)  # теперь секунды
        recreate_interval = bot_config.get("recreate_interval", 30)  # секунды
        cycle_games = bot_config.get("cycle_games", 12)
        cycle_total_amount = bot_config.get("cycle_total_amount", 500.0)
        win_percentage = bot_config.get("win_percentage", 60.0)
        min_bet = bot_config.get("min_bet_amount", 1.0)
        avg_bet = bot_config.get("avg_bet_amount", 50.0)  # новое поле
        can_accept_bets = bot_config.get("can_accept_bets", False)
        can_play_with_bots = bot_config.get("can_play_with_bots", False)
        bet_distribution = bot_config.get("bet_distribution", "medium")  # новое поле
        
        # Валидация математики
        validation_errors = []
        
        # Проверка: (Сумма за цикл) / (Игр в цикле) <= Сред. ставка ($)
        avg_bet_from_cycle = cycle_total_amount / cycle_games
        if avg_bet_from_cycle > avg_bet:
            validation_errors.append(f"Средняя ставка (${avg_bet}) должна быть >= {avg_bet_from_cycle:.2f} (Сумма за цикл / Игр в цикле)")
        
        # Проверка: Мин. ставка <= Сред. ставка
        if min_bet > avg_bet:
            validation_errors.append(f"Минимальная ставка (${min_bet}) должна быть <= средней ставки (${avg_bet})")
        
        # Проверка: Процент выигрыша должен быть реалистичным
        if win_percentage < 0 or win_percentage > 100:
            validation_errors.append("Процент выигрыша должен быть от 0% до 100%")
        
        # Проверка: Количество игр в цикле должно быть больше 0
        if cycle_games <= 0:
            validation_errors.append("Количество игр в цикле должно быть больше 0")
        
        # Проверка: Сумма за цикл должна быть больше 0
        if cycle_total_amount <= 0:
            validation_errors.append("Сумма за цикл должна быть больше 0")
        
        # Проверка: Можно ли создать валидный набор ставок
        max_possible_sum = cycle_games * avg_bet
        if cycle_total_amount > max_possible_sum:
            validation_errors.append(f"Сумма за цикл (${cycle_total_amount}) не может быть больше максимально возможной суммы (${max_possible_sum})")
        
        min_possible_sum = cycle_games * min_bet
        if cycle_total_amount < min_possible_sum:
            validation_errors.append(f"Сумма за цикл (${cycle_total_amount}) не может быть меньше минимально возможной суммы (${min_possible_sum})")
        
        # Проверка таймеров
        if pause_timer < 1 or pause_timer > 3600:
            validation_errors.append("Таймер паузы должен быть от 1 до 3600 секунд")
        
        if recreate_interval < 1:
            validation_errors.append("Интервал пересоздания должен быть минимум 1 секунда")
        
        # Проверка распределения ставок
        if bet_distribution not in ["small", "medium", "large"]:
            validation_errors.append("Характер распределения ставок должен быть 'small', 'medium' или 'large'")
        
        # Если есть ошибки валидации, вернуть их
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Ошибки валидации: {'; '.join(validation_errors)}"
            )
        
        # Создаем бота с новыми полями
        bot_data = {
            "id": str(uuid.uuid4()),
            "type": "REGULAR",
            "name": name,
            "mode": "ALGORITHMIC", 
            "is_active": True,
            "bot_type": "REGULAR",
            
            # User-defined parameters (обновленные)
            "min_bet_amount": min_bet,
            "avg_bet_amount": avg_bet,  # новое поле вместо max_bet_amount
            "win_percentage": win_percentage,
            "cycle_length": cycle_games,
            "cycle_total_amount": cycle_total_amount,
            "pause_timer": pause_timer,  # теперь в секундах
            "recreate_timer": recreate_interval,
            "can_accept_bets": can_accept_bets,
            "can_play_with_bots": can_play_with_bots,
            "bet_distribution": bet_distribution,  # новое поле
            
            # Statistics
            "games_played": 0,
            "games_won": 0,
            "current_cycle_games": 0,
            "current_cycle_wins": 0,
            "current_cycle_losses": 0,
            "total_bet_amount": 0.0,
            
            # State
            "last_game_time": None,
            "last_bet_time": None,
            "current_bet_id": None,
            
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.bots.insert_one(bot_data)
        
        created_bot_id = bot_data["id"]
        
        # Создаём активные ставки для нового бота
        try:
            bot_obj = Bot(**bot_data)
            for _ in range(cycle_games):
                try:
                    await bot_create_game_automatically(bot_obj)
                except Exception as e:
                    logger.error(f"Failed to create initial bet for bot {created_bot_id}: {e}")
            
            # Обновляем количество активных ставок
            active_count = await db.games.count_documents({
                "creator_id": created_bot_id,
                "status": "WAITING"
            })
            
            await db.bots.update_one(
                {"id": created_bot_id},
                {
                    "$set": {
                        "active_bets": active_count,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"🎯 Created {active_count} initial bets for bot {created_bot_id}")
            
        except Exception as e:
            logger.error(f"Error creating initial bets for bot {created_bot_id}: {e}")
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="CREATE_INDIVIDUAL_BOT",
            target_type="bot",
            target_id=created_bot_id,
            details={
                "bot_name": name,
                "config": bot_config,
                "validation_passed": True
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "message": f"Бот {name} создан успешно",
            "bot_id": created_bot_id,
            "bot_name": name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating individual bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create individual bot"
        )

@api_router.get("/admin/bots/regular/list", response_model=dict)
async def get_regular_bots_list(
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_admin)
):
    """Get detailed list of regular bots with pagination."""
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count
        total_count = await db.bots.count_documents({
            "bot_type": "REGULAR"
        })
        
        # Get bots with pagination and sorting
        bots = await db.bots.find({
            "bot_type": "REGULAR"
        }).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        
        bot_details = []
        
        for bot_doc in bots:
            bot = Bot(**bot_doc)
            
            # Count active bets for this bot
            active_bets = await db.games.count_documents({
                "creator_id": bot.id,
                "status": {"$in": ["WAITING", "ACTIVE"]}
            })
            
            # Get game statistics
            total_games = await db.games.count_documents({
                "creator_id": bot.id,
                "status": "COMPLETED"
            })
            
            wins = await db.games.count_documents({
                "creator_id": bot.id,
                "status": "COMPLETED",
                "winner_id": bot.id
            })
            
            losses = await db.games.count_documents({
                "creator_id": bot.id,
                "status": "COMPLETED",
                "winner_id": {"$ne": bot.id}
            })
            
            draws = 0  # Assuming no draws for now
            
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            # Рассчитываем прибыль бота
            total_bet_amount = await db.games.aggregate([
                {"$match": {"creator_id": bot.id, "status": "COMPLETED"}},
                {"$group": {"_id": None, "total": {"$sum": "$bet_amount"}}}
            ]).to_list(1)
            
            total_winnings = await db.games.aggregate([
                {"$match": {"creator_id": bot.id, "status": "COMPLETED", "winner_id": bot.id}},
                {"$group": {"_id": None, "total": {"$sum": {"$multiply": ["$bet_amount", 2]}}}}
            ]).to_list(1)
            
            total_bet_sum = total_bet_amount[0]['total'] if total_bet_amount else 0
            total_win_sum = total_winnings[0]['total'] if total_winnings else 0
            bot_profit_amount = total_win_sum - total_bet_sum
            bot_profit_percent = (bot_profit_amount / total_bet_sum * 100) if total_bet_sum > 0 else 0
            
            # Текущий цикл
            cycle_games = bot_doc.get('cycle_games', 12)
            if cycle_games <= 0:
                cycle_games = 12  # Значение по умолчанию
            
            # Считаем только отыгранные ставки (победы + поражения, исключая ничьи)
            played_games = await db.games.count_documents({
                "creator_id": bot.id,
                "status": "COMPLETED",
                "winner_id": {"$ne": None}  # Исключаем ничьи (когда winner_id = None)
            })
            
            # Отыгранные ставки в текущем цикле
            current_cycle_played = played_games % cycle_games
            
            # Прогресс цикла (X/12 где X = отыгранные ставки без ничьих)
            cycle_progress = f"{current_cycle_played}/{cycle_games}"
            
            # Оставшиеся ставки для активных ставок (12 - X)
            remaining_slots = max(0, cycle_games - current_cycle_played)
            
            bot_details.append({
                "id": bot.id,
                "name": bot.name or f"Bot #{bot.id[:8]}",
                "status": "Активен" if bot.is_active else "Отключён",
                "is_active": bot.is_active,
                "active_bets": active_bets,
                "games_stats": {
                    "wins": wins,
                    "losses": losses,
                    "draws": draws,
                    "total": total_games
                },
                "win_rate": round(win_rate, 1),
                "bot_profit_amount": round(bot_profit_amount, 2),
                "bot_profit_percent": round(bot_profit_percent, 1),
                "current_cycle_games": current_cycle_played,
                "cycle_games": cycle_games,
                "cycle_progress": cycle_progress,
                "remaining_slots": remaining_slots,
                "cycle_total_amount": bot_doc.get('cycle_total_amount', 500.0),
                "bot_type_name": bot_doc.get('bot_type_name', 'Type 1'),
                "bot_type_id": bot_doc.get('bot_type_id', 'type-1'),
                "creation_mode": bot_doc.get('creation_mode', 'queue-based'),
                "bot_behavior": bot_doc.get('bot_behavior', 'balanced'),
                "win_rate_percent": bot_doc.get('win_rate_percent', 60),
                "profit_strategy": bot_doc.get('profit_strategy', 'balanced'),
                "min_bet": bot_doc.get('min_bet_amount', 1.0),
                "max_bet": bot_doc.get('max_bet_amount', 100.0),
                "min_bet_amount": bot_doc.get('min_bet_amount', 1.0),
                "max_bet_amount": bot_doc.get('max_bet_amount', 100.0),
                "individual_limit": bot_doc.get('individual_limit', bot_doc.get('cycle_games', 12)),
                "current_limit": bot_doc.get('current_limit', bot_doc.get('cycle_games', 12)),
                "pause_timer": bot_doc.get('pause_timer', 5),
                "recreate_timer": bot_doc.get('recreate_timer', 30),
                "pause_between_games": bot_doc.get('pause_between_games', 5),
                "win_percentage": bot_doc.get('win_percentage', bot_doc.get('win_rate', 0.55) * 100),
                "can_accept_bets": bot_doc.get('can_accept_bets', False),
                "can_play_with_bots": bot_doc.get('can_play_with_bots', False),
                "created_at": bot.created_at,
                "last_game_time": bot.last_game_time
            })
        
        # Calculate pagination info
        if limit <= 0:
            limit = 10  # Безопасное значение по умолчанию
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "bots": bot_details,
            "total_count": total_count,
            "current_page": page,
            "total_pages": total_pages,
            "items_per_page": limit,
            "has_next": has_next,
            "has_prev": has_prev
        }
        
    except Exception as e:
        logger.error(f"Error fetching regular bots list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch regular bots list"
        )

@api_router.get("/admin/bots/{bot_id}", response_model=dict)
async def get_bot_details(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Get detailed bot information with all saved parameters."""
    try:
        bot_doc = await db.bots.find_one({"id": bot_id})
        if not bot_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Count active bets for this bot
        active_bets = await db.games.count_documents({
            "creator_id": bot_id,
            "status": {"$in": ["WAITING", "ACTIVE"]}
        })
        
        # Get game statistics
        total_games = await db.games.count_documents({
            "creator_id": bot_id,
            "status": "COMPLETED"
        })
        
        wins = await db.games.count_documents({
            "creator_id": bot_id,
            "status": "COMPLETED",
            "winner_id": bot_id
        })
        
        losses = await db.games.count_documents({
            "creator_id": bot_id,
            "status": "COMPLETED",
            "winner_id": {"$ne": bot_id}
        })
        
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        # Return all saved parameters exactly as they were stored
        return {
            "bot": {
                "id": bot_doc["id"],
                "name": bot_doc.get("name", ""),
                "status": "Активен" if bot_doc.get("is_active", True) else "Отключён",
                "is_active": bot_doc.get("is_active", True),
                "bot_type": bot_doc.get("bot_type", "REGULAR"),
                
                # User-defined parameters - return exactly as saved, not defaults!
                "pause_timer": bot_doc.get("pause_timer"),
                "recreate_timer": bot_doc.get("recreate_timer"),
                "cycle_games": bot_doc.get("cycle_length"),
                "cycle_total_amount": bot_doc.get("cycle_total_amount"),
                "win_percentage": bot_doc.get("win_percentage"),
                "min_bet_amount": bot_doc.get("min_bet_amount"),
                "max_bet_amount": bot_doc.get("max_bet_amount"),
                "can_accept_bets": bot_doc.get("can_accept_bets", False),
                "can_play_with_bots": bot_doc.get("can_play_with_bots", False),
                
                # Statistics
                "active_bets": active_bets,
                "games_stats": {
                    "wins": wins,
                    "losses": losses,
                    "draws": 0,
                    "total": total_games
                },
                "win_rate": round(win_rate, 1),
                "created_at": bot_doc.get("created_at"),
                "last_game_time": bot_doc.get("last_game_time"),
                "last_bet_time": bot_doc.get("last_bet_time")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bot details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot details"
        )

@api_router.post("/admin/bots/{bot_id}/recalculate-bets", response_model=dict)
async def recalculate_bot_bets(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Recalculate active bets for a bot based on its cycle parameters."""
    try:
        # Find the bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Get bot parameters
        cycle_length = bot.get("cycle_length", 12)
        cycle_total_amount = bot.get("cycle_total_amount", 500.0)
        win_percentage = bot.get("win_percentage", 60)
        min_bet_amount = bot.get("min_bet_amount", 5.0)
        max_bet_amount = bot.get("max_bet_amount", 100.0)
        
        # Cancel existing active bets for this bot
        await db.games.delete_many({
            "creator_id": bot_id,
            "status": "WAITING"
        })
        
        # Generate new bet structure
        new_bets = await generate_bot_cycle_bets(
            bot_id=bot_id,
            cycle_length=cycle_length,
            cycle_total_amount=cycle_total_amount,
            win_percentage=win_percentage,
            min_bet=min_bet_amount,
            avg_bet=bot.get("avg_bet_amount", 50.0),
            bet_distribution=bot.get("bet_distribution", "medium")
        )
        
        # Count active bets after generation
        active_bets_count = len(new_bets)
        
        return {
            "message": f"Пересчитаны ставки для бота {bot.get('name', bot_id[:8])}",
            "bot_id": bot_id,
            "generated_bets": active_bets_count,
            "cycle_parameters": {
                "cycle_length": cycle_length,
                "cycle_total_amount": cycle_total_amount,
                "win_percentage": win_percentage,
                "min_bet": min_bet_amount,
                "max_bet": max_bet_amount
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating bot bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recalculate bot bets"
        )


async def generate_extended_bot_cycle_bets(bot_id: str, cycle_length: int, cycle_total_amount: float, 
                                          win_rate_percent: int, min_bet: float, max_bet: float, 
                                          bot_behavior: str = "balanced", profit_strategy: str = "balanced"):
    """Generate optimized bet amounts for extended bot system with advanced behavior logic."""
    try:
        # Ensure bot has sufficient gems
        await BotGameLogic.setup_bot_gems(bot_id, db)
        
        # Define gem values (must match frontend definitions)
        gem_values = {
            'Ruby': 1,
            'Amber': 2,
            'Topaz': 5,
            'Emerald': 10,
            'Aquamarine': 25,
            'Sapphire': 50,
            'Magic': 100
        }
        gem_types_list = list(gem_values.keys())
        
        # Calculate number of winning and losing bets
        winning_bets_count = int((win_rate_percent / 100.0) * cycle_length)
        losing_bets_count = cycle_length - winning_bets_count
        
        # Behavior-based gem selection preferences
        behavior_gem_preferences = {
            'aggressive': {
                'preferred_gems': ['Magic', 'Sapphire', 'Aquamarine', 'Emerald'],
                'avoid_gems': ['Ruby', 'Amber'],
                'risk_factor': 1.3,
                'bet_variance': 0.4
            },
            'balanced': {
                'preferred_gems': ['Emerald', 'Aquamarine', 'Topaz', 'Sapphire'],
                'avoid_gems': [],
                'risk_factor': 1.0,
                'bet_variance': 0.3
            },
            'cautious': {
                'preferred_gems': ['Ruby', 'Amber', 'Topaz', 'Emerald'],
                'avoid_gems': ['Magic', 'Sapphire'],
                'risk_factor': 0.7,
                'bet_variance': 0.2
            }
        }
        
        behavior_config = behavior_gem_preferences.get(bot_behavior, behavior_gem_preferences['balanced'])
        
        def generate_behavior_based_gem_combination(target_min: int, target_max: int, behavior_config):
            """Generate gem combination based on bot behavior."""
            attempts = 0
            max_attempts = 50
            
            while attempts < max_attempts:
                gem_combination = {}
                total_value = 0
                
                # Start with preferred gems based on behavior
                if behavior_config['preferred_gems']:
                    primary_gem = random.choice(behavior_config['preferred_gems'])
                    if primary_gem not in behavior_config['avoid_gems']:
                        base_quantity = random.randint(1, 2)
                        gem_combination[primary_gem] = base_quantity
                        total_value += gem_values[primary_gem] * base_quantity
                
                # Add secondary gems if needed
                remaining_value = target_max - total_value
                if remaining_value > 0:
                    available_gems = [g for g in gem_types_list if g not in behavior_config['avoid_gems']]
                    
                    while remaining_value > 0 and len(available_gems) > 0:
                        gem = random.choice(available_gems)
                        gem_value = gem_values[gem]
                        
                        if gem_value <= remaining_value:
                            quantity = random.randint(1, max(1, remaining_value // gem_value))
                            if gem in gem_combination:
                                gem_combination[gem] += quantity
                            else:
                                gem_combination[gem] = quantity
                            total_value += gem_value * quantity
                            remaining_value = target_max - total_value
                        else:
                            available_gems.remove(gem)
                
                # Check if valid
                if target_min <= total_value <= target_max:
                    return gem_combination, int(total_value)
                
                attempts += 1
            
            # Fallback
            fallback_quantity = max(1, min(int(target_max), int(target_min)))
            return {'Ruby': fallback_quantity}, fallback_quantity
        
        # Generate bet amounts using behavior-based logic
        bet_data = []
        total_generated = 0
        
        # Calculate target range with behavior modifications
        avg_bet = cycle_total_amount / cycle_length
        risk_factor = behavior_config['risk_factor']
        bet_variance = behavior_config['bet_variance']
        
        # Profit strategy affects bet order
        bet_outcomes = ['win'] * winning_bets_count + ['lose'] * losing_bets_count
        
        if profit_strategy == 'start-positive':
            # Front-load wins
            bet_outcomes = ['win'] * min(winning_bets_count, cycle_length // 2) + \
                          ['lose'] * losing_bets_count + \
                          ['win'] * (winning_bets_count - min(winning_bets_count, cycle_length // 2))
        elif profit_strategy == 'start-negative':
            # Front-load losses
            bet_outcomes = ['lose'] * min(losing_bets_count, cycle_length // 2) + \
                          ['win'] * winning_bets_count + \
                          ['lose'] * (losing_bets_count - min(losing_bets_count, cycle_length // 2))
        else:
            # Balanced distribution
            random.shuffle(bet_outcomes)
        
        for i in range(cycle_length):
            if i == cycle_length - 1:  # Last bet: use remaining amount
                remaining = int(cycle_total_amount - total_generated)
                target_min = max(int(min_bet), remaining - 10)
                target_max = max(int(max_bet), remaining + 10)
                gem_combination, bet_amount = generate_behavior_based_gem_combination(
                    target_min, target_max, behavior_config
                )
                
                # Force exact remaining amount
                if bet_amount != remaining and remaining >= int(min_bet):
                    bet_amount = remaining
                    if remaining <= 10:
                        gem_combination = {'Ruby': remaining}
                    else:
                        gem_combination = {'Ruby': remaining}
            else:
                # Calculate bet range with behavior modifications
                base_variance = avg_bet * bet_variance
                behavior_modifier = random.uniform(0.8, 1.2) * risk_factor
                
                target_center = avg_bet * behavior_modifier
                target_min = max(int(min_bet), int(target_center - base_variance))
                target_max = min(int(max_bet), int(target_center + base_variance))
                
                gem_combination, bet_amount = generate_behavior_based_gem_combination(
                    target_min, target_max, behavior_config
                )
            
            bet_data.append((gem_combination, bet_amount))
            total_generated += bet_amount
        
        # Fine-tune total to match cycle_total_amount
        difference = int(cycle_total_amount - total_generated)
        if abs(difference) > 0:
            # Adjust largest bets
            adjustable_bets = [(i, amount) for i, (_, amount) in enumerate(bet_data)]
            adjustable_bets.sort(key=lambda x: x[1], reverse=True)
            
            for i, _ in adjustable_bets[:min(3, len(adjustable_bets))]:
                if difference == 0:
                    break
                
                gems, current_amount = bet_data[i]
                if difference > 0:
                    add_amount = min(difference, 5)
                    gems['Ruby'] = gems.get('Ruby', 0) + add_amount
                    bet_data[i] = (gems, current_amount + add_amount)
                    difference -= add_amount
                elif difference < 0 and current_amount > int(min_bet):
                    subtract_amount = min(abs(difference), current_amount - int(min_bet))
                    if gems.get('Ruby', 0) >= subtract_amount:
                        gems['Ruby'] -= subtract_amount
                        if gems['Ruby'] == 0:
                            del gems['Ruby']
                        bet_data[i] = (gems, current_amount - subtract_amount)
                        difference += subtract_amount
        
        # Create game entries with extended metadata
        created_bets = []
        for i, ((gem_combination, bet_amount), outcome) in enumerate(zip(bet_data, bet_outcomes)):
            bot = await db.bots.find_one({"id": bot_id})
            bot_move = BotGameLogic.calculate_bot_move(Bot(**bot))
            salt = secrets.token_hex(32)
            
            game = Game(
                creator_id=bot_id,
                creator_type="bot",
                bot_type=bot.bot_type,
                creator_move=bot_move,
                is_regular_bot_game=(bot.bot_type == "REGULAR"),
                creator_move_hash=hashlib.sha256(f"{bot_move.value}{salt}".encode()).hexdigest(),
                creator_salt=salt,
                bet_amount=float(bet_amount),
                bet_gems=gem_combination,
                is_bot_game=True,
                bot_id=bot_id,
                metadata={
                    "cycle_position": i + 1,
                    "intended_outcome": outcome,
                    "cycle_id": f"{bot_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "gem_based_bet": True,
                    "bot_behavior": bot_behavior,
                    "profit_strategy": profit_strategy,
                    "win_rate_percent": win_rate_percent,
                    "extended_system": True
                }
            )
            
            await db.games.insert_one(game.dict())
            created_bets.append(game.dict())
        
        final_total = sum(bet_amount for _, bet_amount in bet_data)
        logger.info(f"Generated {len(created_bets)} extended bot bets for {bot_id} with total ${final_total} using {bot_behavior} behavior")
        return created_bets
        
    except Exception as e:
        logger.error(f"Error generating extended bot cycle bets: {e}")
        raise
async def generate_bot_cycle_bets(bot_id: str, cycle_length: int, cycle_total_amount: float, 
                                win_percentage: int, min_bet: float, avg_bet: float, bet_distribution: str = "medium",
                                bot_behavior: str = "balanced", profit_strategy: str = "balanced"):
    """Generate optimized bet amounts for a bot's cycle using new distribution logic with behavioral support."""
    try:
        # Ensure bot has sufficient gems
        await BotGameLogic.setup_bot_gems(bot_id, db)
        
        # Get bot data for additional behavioral context
        bot_data = await db.bots.find_one({"id": bot_id})
        if bot_data:
            bot_behavior = bot_data.get("bot_behavior", bot_behavior)
            profit_strategy = bot_data.get("profit_strategy", profit_strategy)
        
        # Define gem values (must match frontend definitions)
        gem_values = {
            'Ruby': 1,
            'Amber': 2,
            'Topaz': 5,
            'Emerald': 10,
            'Aquamarine': 25,
            'Sapphire': 50,
            'Magic': 100
        }
        gem_types_list = list(gem_values.keys())
        
        # Calculate number of winning and losing bets with behavioral adjustments
        base_winning_bets = int((win_percentage / 100.0) * cycle_length)
        
        # Behavioral adjustments to win distribution
        if bot_behavior == 'aggressive':
            # Aggressive bots might cluster wins early or late
            winning_bets_count = base_winning_bets
        elif bot_behavior == 'cautious':
            # Cautious bots spread wins evenly
            winning_bets_count = base_winning_bets
        else:  # balanced
            winning_bets_count = base_winning_bets
            
        losing_bets_count = cycle_length - winning_bets_count
        
        def generate_valid_gem_combination(target_min: int, target_max: int):
            """Generate a gem combination that results in a valid integer bet amount."""
            attempts = 0
            max_attempts = 100
            
            while attempts < max_attempts:
                # Randomly select 1-3 gem types
                num_gem_types = random.randint(1, 3)
                selected_gem_types = random.sample(gem_types_list, num_gem_types)
                
                # Generate quantities for each gem type
                gem_combination = {}
                total_value = 0
                
                for gem_type in selected_gem_types:
                    # Start with 1-3 gems of each type
                    base_quantity = random.randint(1, 3)
                    gem_combination[gem_type] = base_quantity
                    total_value += gem_values[gem_type] * base_quantity
                
                # Adjust quantities to get closer to target range
                if total_value < target_min:
                    # Add more gems to reach minimum
                    while total_value < target_min and attempts < max_attempts:
                        # Choose a random gem type to add
                        gem_to_add = random.choice(selected_gem_types)
                        # Add gems that don't exceed target_max too much
                        if total_value + gem_values[gem_to_add] <= target_max * 1.2:  # Allow 20% overage
                            gem_combination[gem_to_add] += 1
                            total_value += gem_values[gem_to_add]
                        else:
                            break
                
                elif total_value > target_max:
                    # Remove gems to get under maximum
                    while total_value > target_max and attempts < max_attempts:
                        # Find a gem type we can reduce
                        reducible_gems = [gt for gt in selected_gem_types if gem_combination[gt] > 1]
                        if not reducible_gems:
                            break
                        gem_to_reduce = random.choice(reducible_gems)
                        gem_combination[gem_to_reduce] -= 1
                        total_value -= gem_values[gem_to_reduce]
                        if gem_combination[gem_to_reduce] == 0:
                            del gem_combination[gem_to_reduce]
                            selected_gem_types.remove(gem_to_reduce)
                
                # Check if the combination is valid
                if target_min <= total_value <= target_max and total_value == int(total_value):
                    return gem_combination, int(total_value)
                
                attempts += 1
            
            # Fallback: generate simple combination with Ruby gems
            fallback_quantity = max(1, min(int(target_max), int(target_min)))
            return {'Ruby': fallback_quantity}, fallback_quantity
        
        def get_bet_range_for_distribution(bet_distribution: str, min_bet: float, avg_bet: float, bot_behavior: str = "balanced"):
            """Определяет диапазон ставок на основе типа распределения и поведения бота."""
            base_range = avg_bet - min_bet
            
            # Базовые настройки распределения
            if bet_distribution == "small":
                # Больше маленьких ставок - ближе к минимальной
                bias_min = min_bet
                bias_max = min_bet + base_range * 0.6  # 60% от диапазона
            elif bet_distribution == "large":
                # Больше крупных ставок - ближе к средней
                bias_min = min_bet + base_range * 0.4  # 40% от диапазона
                bias_max = avg_bet
            else:  # medium
                # Равномерное распределение
                bias_min = min_bet + base_range * 0.2  # 20% от диапазона
                bias_max = min_bet + base_range * 0.8  # 80% от диапазона
            
            # Поведенческие корректировки
            if bot_behavior == 'aggressive':
                # Агрессивные боты делают более разнообразные ставки
                variance_multiplier = 1.2
                bias_min *= 0.9  # Немного снижаем минимум
                bias_max *= 1.1  # Немного повышаем максимум
            elif bot_behavior == 'cautious':
                # Осторожные боты более консервативны
                variance_multiplier = 0.8
                bias_min *= 1.1  # Немного повышаем минимум
                bias_max *= 0.9  # Немного снижаем максимум
            else:  # balanced
                variance_multiplier = 1.0
            
            # Убеждаемся, что диапазон разумный
            bias_min = max(min_bet, bias_min)
            bias_max = min(avg_bet, bias_max)
            
            return bias_min, bias_max, variance_multiplier
        
        # Generate bet amounts using new distribution logic
        bet_data = []  # Will store (gem_combination, bet_amount) tuples
        total_generated = 0
        
        # Get bias range based on distribution type and bot behavior
        bias_min, bias_max, variance_multiplier = get_bet_range_for_distribution(bet_distribution, min_bet, avg_bet, bot_behavior)
        
        # Apply profit strategy to win/loss pattern
        outcomes = []
        if profit_strategy == "start_profit":
            # Front-load wins for early profit
            outcomes = ['win'] * winning_bets_count + ['loss'] * losing_bets_count
        elif profit_strategy == "end_loss":
            # Back-load losses for late deficit
            outcomes = ['loss'] * losing_bets_count + ['win'] * winning_bets_count
        else:  # balanced
            # Mix wins and losses throughout cycle
            outcomes = ['win'] * winning_bets_count + ['loss'] * losing_bets_count
            random.shuffle(outcomes)
        
        # Generate bet amounts with behavioral variance
        for i in range(cycle_length):
            if i == cycle_length - 1:  # Last bet: use remaining amount
                remaining = int(cycle_total_amount - total_generated)
                target_min = max(int(min_bet), remaining - 10)  # Small tolerance
                target_max = max(int(avg_bet), remaining + 10)
                gem_combination, bet_amount = generate_valid_gem_combination(target_min, target_max)
                # Force exact remaining amount for last bet
                if bet_amount != remaining and remaining >= int(min_bet):
                    bet_amount = remaining
                    # Adjust gem combination to match the amount
                    if remaining <= 5:
                        gem_combination = {'Ruby': remaining}
                    elif remaining <= 10:
                        gem_combination = {'Amber': remaining // 2, 'Ruby': remaining % 2}
                    else:
                        # Try to create a reasonable combination
                        gem_combination = {'Ruby': remaining}  # Fallback
            else:
                # Generate bet within bias range based on distribution and behavior
                if bet_distribution == "small":
                    # Концентрация на малых ставках
                    variance = (bias_max - bias_min) * 0.3 * variance_multiplier
                    target_center = bias_min + (bias_max - bias_min) * 0.3
                elif bet_distribution == "large":
                    # Концентрация на крупных ставках
                    variance = (bias_max - bias_min) * 0.3 * variance_multiplier
                    target_center = bias_min + (bias_max - bias_min) * 0.7
                else:  # medium
                    # Равномерное распределение
                    variance = (bias_max - bias_min) * 0.4
                    target_center = (bias_min + bias_max) / 2
                
                target_min = max(int(min_bet), int(target_center - variance))
                target_max = min(int(avg_bet), int(target_center + variance))
                gem_combination, bet_amount = generate_valid_gem_combination(target_min, target_max)
            
            bet_data.append((gem_combination, bet_amount))
            total_generated += bet_amount
        
        # Adjust total if needed by modifying the largest bets
        if abs(total_generated - cycle_total_amount) > 0:
            difference = int(cycle_total_amount - total_generated)
            if difference != 0:
                # Sort bets by amount to find candidates for adjustment
                adjustable_bets = [(i, amount) for i, (_, amount) in enumerate(bet_data)]
                adjustable_bets.sort(key=lambda x: x[1], reverse=True)
                
                # Distribute the difference across the largest bets
                for i, _ in adjustable_bets[:min(3, len(adjustable_bets))]:  # Adjust up to 3 bets
                    if difference == 0:
                        break
                    
                    gems, current_amount = bet_data[i]
                    if difference > 0:  # Need to add
                        add_amount = min(difference, 5)  # Add up to 5
                        gems['Ruby'] = gems.get('Ruby', 0) + add_amount
                        bet_data[i] = (gems, current_amount + add_amount)
                        difference -= add_amount
                    elif difference < 0 and current_amount > int(min_bet):  # Need to subtract
                        subtract_amount = min(abs(difference), current_amount - int(min_bet))
                        # Remove Ruby gems first
                        if gems.get('Ruby', 0) >= subtract_amount:
                            gems['Ruby'] -= subtract_amount
                            if gems['Ruby'] == 0:
                                del gems['Ruby']
                            bet_data[i] = (gems, current_amount - subtract_amount)
                            difference += subtract_amount
        
        # Randomly assign winning/losing outcome respecting win_percentage
        bet_outcomes = ['win'] * winning_bets_count + ['lose'] * losing_bets_count
        random.shuffle(bet_outcomes)
        
        # Create actual game entries
        created_bets = []
        for i, ((gem_combination, bet_amount), outcome) in enumerate(zip(bet_data, bet_outcomes)):
            # Generate bot's move
            bot = await db.bots.find_one({"id": bot_id})
            bot_move = BotGameLogic.calculate_bot_move(Bot(**bot))
            salt = secrets.token_hex(32)
            
            # Create game with metadata about intended outcome
            game = Game(
                creator_id=bot_id,
                creator_move=bot_move,
                creator_move_hash=hashlib.sha256(f"{bot_move.value}{salt}".encode()).hexdigest(),
                creator_salt=salt,
                bet_amount=float(bet_amount),  # Convert to float for compatibility
                bet_gems=gem_combination,
                is_bot_game=True,
                bot_id=bot_id,
                metadata={
                    "cycle_position": i + 1,
                    "intended_outcome": outcome,
                    "cycle_id": f"{bot_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "gem_based_bet": True,  # Mark as gem-based bet
                    "bet_distribution": bet_distribution,  # Store distribution type
                    "win_percentage": win_percentage  # Store target win percentage
                }
            )
            
            await db.games.insert_one(game.dict())
            created_bets.append(game.dict())
        
        final_total = sum(bet_amount for _, bet_amount in bet_data)
        logger.info(f"Generated {len(created_bets)} gem-based bets for bot {bot_id} with total ${final_total} using {bet_distribution} distribution")
        return created_bets
        
    except Exception as e:
        logger.error(f"Error generating bot cycle bets: {e}")
        raise

@api_router.put("/admin/bots/{bot_id}", response_model=dict)
async def update_individual_bot_settings(
    bot_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update bot settings with user-defined parameters."""
    try:
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Validate parameters
        pause_timer = update_data.get("pause_timer")
        recreate_timer = update_data.get("recreate_timer")
        cycle_games = update_data.get("cycle_games")
        cycle_total_amount = update_data.get("cycle_total_amount")
        win_percentage = update_data.get("win_percentage")
        min_bet_amount = update_data.get("min_bet_amount")
        avg_bet_amount = update_data.get("avg_bet_amount")  # новое поле
        bet_distribution = update_data.get("bet_distribution")  # новое поле
        
        # Validation with new math
        if pause_timer is not None and (pause_timer < 1 or pause_timer > 3600):
            raise HTTPException(status_code=400, detail="Pause timer must be between 1 and 3600 seconds")
        
        if recreate_timer is not None and recreate_timer < 1:
            raise HTTPException(status_code=400, detail="Recreate timer must be at least 1 second")
            
        if cycle_games is not None and cycle_games < 1:
            raise HTTPException(status_code=400, detail="Cycle games must be at least 1")
        
        # Новая валидация математики
        if min_bet_amount is not None and avg_bet_amount is not None:
            if min_bet_amount > avg_bet_amount:
                raise HTTPException(status_code=400, detail="Min bet must be less than or equal to avg bet")
        
        if cycle_total_amount is not None and cycle_games is not None and avg_bet_amount is not None:
            avg_bet_from_cycle = cycle_total_amount / cycle_games
            if avg_bet_from_cycle > avg_bet_amount:
                raise HTTPException(status_code=400, detail=f"Average bet ({avg_bet_amount}) must be >= {avg_bet_from_cycle:.2f} (cycle total / cycle games)")
        
        if bet_distribution is not None and bet_distribution not in ["small", "medium", "large"]:
            raise HTTPException(status_code=400, detail="Bet distribution must be 'small', 'medium', or 'large'")
        
        # Prepare update data - only update provided fields
        update_fields = {"updated_at": datetime.utcnow()}
        
        if "name" in update_data:
            update_fields["name"] = update_data["name"]
        if pause_timer is not None:
            update_fields["pause_timer"] = pause_timer
        if recreate_timer is not None:
            update_fields["recreate_timer"] = recreate_timer
        if cycle_games is not None:
            update_fields["cycle_length"] = cycle_games
        if cycle_total_amount is not None:
            update_fields["cycle_total_amount"] = cycle_total_amount
        if win_percentage is not None:
            update_fields["win_percentage"] = win_percentage
        if min_bet_amount is not None:
            update_fields["min_bet_amount"] = min_bet_amount
        if avg_bet_amount is not None:
            update_fields["avg_bet_amount"] = avg_bet_amount  # новое поле
        if bet_distribution is not None:
            update_fields["bet_distribution"] = bet_distribution  # новое поле
        if "can_accept_bets" in update_data:
            update_fields["can_accept_bets"] = update_data["can_accept_bets"]
        if "can_play_with_bots" in update_data:
            update_fields["can_play_with_bots"] = update_data["can_play_with_bots"]
        
        # Update bot in database
        await db.bots.update_one(
            {"id": bot_id},
            {"$set": update_fields}
        )
        
        # Check if cycle parameters were changed - if so, recalculate bets
        cycle_params_changed = any(field in update_fields for field in [
            "cycle_length", "cycle_total_amount", "win_percentage", 
            "min_bet_amount", "avg_bet_amount", "bet_distribution"  # обновленные поля
        ])
        
        generated_bets = 0
        if cycle_params_changed and bot.get("is_active", False):
            try:
                # Get updated bot data
                updated_bot = await db.bots.find_one({"id": bot_id})
                new_bets = await generate_bot_cycle_bets(
                    bot_id=bot_id,
                    cycle_length=updated_bot.get("cycle_length", 12),
                    cycle_total_amount=updated_bot.get("cycle_total_amount", 500.0),
                    win_percentage=updated_bot.get("win_percentage", 60),
                    min_bet=updated_bot.get("min_bet_amount", 5.0),
                    avg_bet=updated_bot.get("avg_bet_amount", 50.0),
                    bet_distribution=updated_bot.get("bet_distribution", "medium")
                )
                generated_bets = len(new_bets)
                
                # Поддерживаем правильное количество активных ставок
                await maintain_bot_active_bets_count(bot_id, updated_bot.get("cycle_length", 12))
                
            except Exception as e:
                logger.warning(f"Failed to auto-recalculate bets for bot {bot_id}: {e}")
        
        # Если изменился cycle_length, но не другие параметры, все равно поддерживаем активные ставки
        elif "cycle_length" in update_fields and bot.get("is_active", False):
            try:
                await maintain_bot_active_bets_count(bot_id, update_fields["cycle_length"])
            except Exception as e:
                logger.warning(f"Failed to maintain active bets count for bot {bot_id}: {e}")
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="UPDATE_BOT_SETTINGS",
            target_type="bot",
            target_id=bot_id,
            details={
                "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
                "updated_fields": update_fields,
                "auto_recalculated_bets": generated_bets if cycle_params_changed else None
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        response_data = {
            "message": f"Настройки бота обновлены",
            "bot_id": bot_id,
            "updated_fields": list(update_fields.keys())
        }
        
        if cycle_params_changed:
            response_data["recalculated_bets"] = generated_bets
            response_data["message"] += f" и пересчитано {generated_bets} ставок"
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot settings"
        )

@api_router.post("/admin/bots/{bot_id}/toggle", response_model=dict)
async def toggle_bot_status_admin(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Toggle bot active status."""
    try:
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        new_status = not bot.get("is_active", True)
        
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
            details={
                "new_status": new_status,
                "bot_name": bot.get("name", f"Bot #{bot_id[:8]}")
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        status_text = "включен" if new_status else "отключен"
        return {
            "message": f"Бот {status_text}",
            "bot_id": bot_id,
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

@api_router.get("/admin/bots/{bot_id}/active-bets", response_model=dict)
async def get_bot_active_bets(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Get detailed list of bot's active bets."""
    try:
        # Find the bot first
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Get active games created by this bot
        active_games = await db.games.find({
            "creator_id": bot_id,
            "status": {"$in": ["WAITING", "ACTIVE"]}
        }).sort("created_at", -1).to_list(100)
        
        bets_details = []
        for game in active_games:
            game_obj = Game(**game)
            
            # Get opponent info if exists
            opponent_info = None
            if game_obj.opponent_id:
                opponent = await db.users.find_one({"id": game_obj.opponent_id})
                if opponent:
                    opponent_info = {
                        "id": opponent["id"],
                        "username": opponent["username"]
                    }
            
            # Calculate time until auto-cancel (if applicable)
            # Assuming 24 hours auto-cancel for waiting games
            time_until_cancel = None
            if game_obj.status == GameStatus.WAITING:
                created_time = game_obj.created_at
                cancel_time = created_time + timedelta(hours=24)
                remaining = cancel_time - datetime.utcnow()
                if remaining.total_seconds() > 0:
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    time_until_cancel = f"{hours}ч {minutes}м"
            
            bet_detail = {
                "game_id": game_obj.id,
                "bet_amount": game_obj.bet_amount,
                "bet_gems": game_obj.bet_gems,
                "status": "Ожидает" if game_obj.status == GameStatus.WAITING else "В процессе",
                "created_at": game_obj.created_at,
                "opponent": opponent_info,
                "time_until_cancel": time_until_cancel
            }
            bets_details.append(bet_detail)
        
        return {
            "bot_id": bot_id,
            "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
            "active_bets_count": len(bets_details),
            "bets": bets_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bot active bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot active bets"
        )

@api_router.get("/admin/bots/{bot_id}/cycle-history", response_model=dict)
async def get_bot_cycle_history(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Get detailed cycle history for a bot."""
    try:
        # Find the bot first
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Get bot's current cycle settings
        cycle_length = bot.get("cycle_length", 12)
        current_cycle_games = bot.get("current_cycle_games", 0)
        current_cycle_wins = bot.get("current_cycle_wins", 0)
        
        # Get recent completed games for current cycle
        # We'll fetch more games and then filter for current cycle
        completed_games = await db.games.find({
            "creator_id": bot_id,
            "status": "COMPLETED"
        }).sort("completed_at", -1).limit(cycle_length * 2).to_list(cycle_length * 2)
        
        cycle_games = []
        total_bet_amount = 0.0
        total_winnings = 0.0
        total_losses = 0.0
        wins_count = 0
        losses_count = 0
        draws_count = 0
        
        # Take only the most recent games up to cycle_length
        recent_games = completed_games[:cycle_length] if len(completed_games) >= cycle_length else completed_games
        
        for i, game in enumerate(recent_games):
            game_obj = Game(**game)
            
            # Get opponent info
            opponent_info = "Не найден"
            if game_obj.opponent_id:
                opponent = await db.users.find_one({"id": game_obj.opponent_id})
                if opponent:
                    opponent_info = opponent["username"]
            
            # Determine result and calculate winnings/losses
            result = "Ничья"
            winnings = 0.0
            
            if game_obj.winner_id == bot_id:
                result = "Победа"
                winnings = game_obj.bet_amount * 1.94  # After commission
                total_winnings += winnings
                wins_count += 1
            elif game_obj.winner_id and game_obj.winner_id != bot_id:
                result = "Поражение"
                winnings = -game_obj.bet_amount
                total_losses += game_obj.bet_amount
                losses_count += 1
            else:
                draws_count += 1
                # Draws don't count towards cycle progress
            
            total_bet_amount += game_obj.bet_amount
            
            game_detail = {
                "game_number": i + 1,
                "game_id": game_obj.id,
                "bet_amount": game_obj.bet_amount,
                "bet_gems": game_obj.bet_gems,
                "opponent": opponent_info,
                "result": result,
                "winnings": winnings,
                "completed_at": game_obj.completed_at or game_obj.created_at
            }
            cycle_games.append(game_detail)
        
        # Calculate statistics
        win_percentage = (wins_count / (wins_count + losses_count) * 100) if (wins_count + losses_count) > 0 else 0
        net_profit = total_winnings - total_losses
        
        # Current cycle progress (excluding draws)
        completed_cycle_games = wins_count + losses_count
        
        return {
            "bot_id": bot_id,
            "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
            "cycle_info": {
                "cycle_length": cycle_length,
                "completed_games": completed_cycle_games,
                "current_wins": wins_count,
                "current_losses": losses_count,
                "draws": draws_count,
                "progress": f"{completed_cycle_games}/{cycle_length}"
            },
            "cycle_stats": {
                "total_bet_amount": round(total_bet_amount, 2),
                "total_winnings": round(total_winnings, 2),
                "total_losses": round(total_losses, 2),
                "net_profit": round(net_profit, 2),
                "win_percentage": round(win_percentage, 1)
            },
            "games": cycle_games
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bot cycle history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot cycle history"
        )

@api_router.delete("/admin/bots/{bot_id}/delete", response_model=dict)
async def delete_bot_admin(
    bot_id: str,
    delete_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Delete bot completely (admin only)."""
    try:
        # Find bot
        bot = await db.bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        reason = delete_data.get("reason", "No reason provided")
        
        # Cancel all bot's active games first
        active_games = await db.games.find({
            "creator_id": bot_id,
            "status": {"$in": ["WAITING", "ACTIVE"]}
        }).to_list(100)
        
        for game in active_games:
            # Cancel the game
            await db.games.update_one(
                {"id": game["id"]},
                {"$set": {"status": "CANCELLED", "cancelled_at": datetime.utcnow()}}
            )
        
        # Delete the bot
        await db.bots.delete_one({"id": bot_id})
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="DELETE_BOT",
            target_type="bot",
            target_id=bot_id,
            details={
                "deleted_bot": {
                    "name": bot.get("name", f"Bot #{bot_id[:8]}"),
                    "bot_type": bot.get("bot_type", "REGULAR")
                },
                "reason": reason,
                "cancelled_games": len(active_games)
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "message": "Бот удален успешно",
            "deleted_bot_id": bot_id,
            "bot_name": bot.get("name", f"Bot #{bot_id[:8]}"),
            "reason": reason,
            "cancelled_games": len(active_games)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bot"
        )

@api_router.get("/admin/bots/regular/stats", response_model=dict)
async def get_regular_bots_stats(current_user: User = Depends(get_current_admin)):
    """Get regular bots statistics."""
    try:
        # Total active regular bots
        active_bots = await db.bots.count_documents({
            "bot_type": "REGULAR",
            "is_active": True
        })
        
        # Bets created in last 24h
        yesterday = datetime.utcnow() - timedelta(days=1)
        bets_24h = await db.games.count_documents({
            "creator_type": "bot",
            "bot_type": "REGULAR",
            "created_at": {"$gte": yesterday}
        })
        
        # Wins in last 24h
        wins_24h = await db.games.count_documents({
            "creator_type": "bot", 
            "bot_type": "REGULAR",
            "status": "COMPLETED",
            "winner_type": "bot",
            "created_at": {"$gte": yesterday}
        })
        
        # Win percentage
        total_bot_games = await db.games.count_documents({
            "creator_type": "bot",
            "bot_type": "REGULAR",
            "status": "COMPLETED"
        })
        bot_wins = await db.games.count_documents({
            "creator_type": "bot",
            "bot_type": "REGULAR", 
            "status": "COMPLETED",
            "winner_type": "bot"
        })
        win_percentage = (bot_wins / total_bot_games * 100) if total_bot_games > 0 else 0
        
        # Total bet value
        total_bet_value = await db.games.aggregate([
            {"$match": {"creator_type": "bot", "bot_type": "REGULAR"}},
            {"$group": {"_id": None, "total": {"$sum": "$bet_amount"}}}
        ]).to_list(1)
        total_value = total_bet_value[0]["total"] if total_bet_value else 0
        
        # Most active bots
        most_active = await db.bots.find({
            "type": "REGULAR",
            "is_active": True
        }).sort("games_played", -1).limit(3).to_list(3)
        
        return {
            "active_bots": active_bots,
            "bets_24h": bets_24h,
            "wins_24h": wins_24h,
            "win_percentage": round(win_percentage, 1),
            "total_bet_value": round(total_value, 2),
            "errors": 0,  # TODO: implement error tracking
            "most_active": [{"id": bot.get("id"), "games": bot.get("games_played", 0)} for bot in most_active]
        }
        
    except Exception as e:
        logger.error(f"Error fetching regular bot stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch regular bot statistics"
        )

@api_router.get("/admin/bots/human/stats", response_model=dict)
async def get_human_bots_stats(current_user: User = Depends(get_current_admin)):
    """Get human bots statistics."""
    try:
        # Total active human bots
        active_bots = await db.bots.count_documents({
            "type": "HUMAN",
            "is_active": True
        })
        
        # Bets created in last 24h
        yesterday = datetime.utcnow() - timedelta(days=1)
        bets_24h = await db.games.count_documents({
            "creator_type": "human_bot",
            "created_at": {"$gte": yesterday}
        })
        
        # Wins in last 24h
        wins_24h = await db.games.count_documents({
            "creator_type": "human_bot",
            "status": "COMPLETED",
            "winner_type": "human_bot",
            "created_at": {"$gte": yesterday}
        })
        
        # Win percentage
        total_human_bot_games = await db.games.count_documents({
            "creator_type": "human_bot",
            "status": "COMPLETED"
        })
        human_bot_wins = await db.games.count_documents({
            "creator_type": "human_bot",
            "status": "COMPLETED",
            "winner_type": "human_bot"
        })
        win_percentage = (human_bot_wins / total_human_bot_games * 100) if total_human_bot_games > 0 else 0
        
        # Total bet value
        total_bet_value = await db.games.aggregate([
            {"$match": {"creator_type": "human_bot"}},
            {"$group": {"_id": None, "total": {"$sum": "$bet_amount"}}}
        ]).to_list(1)
        total_value = total_bet_value[0]["total"] if total_bet_value else 0
        
        # Most active human bots
        most_active = await db.bots.find({
            "type": "HUMAN",
            "is_active": True
        }).sort("games_played", -1).limit(3).to_list(3)
        
        return {
            "active_bots": active_bots,
            "bets_24h": bets_24h,
            "wins_24h": wins_24h,
            "win_percentage": round(win_percentage, 1),
            "total_bet_value": round(total_value, 2),
            "errors": 0,  # TODO: implement error tracking
            "most_active": [{"id": bot.get("id"), "name": bot.get("name", "Unknown"), "games": bot.get("games_played", 0)} for bot in most_active]
        }
        
    except Exception as e:
        logger.error(f"Error fetching human bot stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch human bot statistics"
        )

@api_router.delete("/admin/users/{user_id}", response_model=dict)
async def delete_user_account(
    user_id: str,
    delete_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Delete user account completely (super admin only)."""
    try:
        # Check if current user is super admin
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can delete user accounts"
            )
        
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        reason = delete_data.get("reason", "No reason provided")
        
        # Don't allow deletion of other admins
        if user.get("role") in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete admin accounts"
            )
        
        # Cancel all user's active games first
        active_games = await db.games.find({
            "$or": [
                {"creator_id": user_id, "status": {"$in": [GameStatus.WAITING, GameStatus.ACTIVE]}},
                {"opponent_id": user_id, "status": {"$in": [GameStatus.WAITING, GameStatus.ACTIVE]}}
            ]
        }).to_list(100)
        
        for game in active_games:
            game_obj = Game(**game)
            # Cancel the game and return gems/commissions
            await db.games.update_one(
                {"id": game_obj.id},
                {"$set": {"status": GameStatus.CANCELLED, "cancelled_at": datetime.utcnow()}}
            )
            
            # Unfreeze gems and return commissions (simplified)
            if game_obj.creator_id == user_id:
                for gem_type, quantity in game_obj.bet_gems.items():
                    await db.user_gems.update_one(
                        {"user_id": user_id, "gem_type": gem_type},
                        {"$inc": {"frozen_quantity": -quantity}}
                    )
        
        # Delete user's data
        await db.user_gems.delete_many({"user_id": user_id})
        await db.notifications.delete_many({"user_id": user_id})
        await db.refresh_tokens.delete_many({"user_id": user_id})
        
        # Delete the user
        await db.users.delete_one({"id": user_id})
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_user.id,
            action="DELETE_USER_ACCOUNT",
            target_type="user",
            target_id=user_id,
            details={
                "deleted_user": {
                    "username": user.get("username"),
                    "email": user.get("email"),
                    "balance": user.get("virtual_balance", 0)
                },
                "reason": reason
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        return {
            "message": "User account deleted successfully",
            "deleted_user_id": user_id,
            "username": user.get("username"),
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )

@api_router.get("/admin/bots/{bot_id}/active-bets", response_model=dict)
async def get_bot_active_bets(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Get active bets for a specific bot and manage them according to remaining_slots."""
    try:
        # Получаем бота
        bot_doc = await db.bots.find_one({"id": bot_id})
        if not bot_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        bot = Bot(**bot_doc)
        
        # Вычисляем remaining_slots (как в /admin/bots/regular/list)
        cycle_games = bot_doc.get('cycle_games', 12)
        if cycle_games <= 0:
            cycle_games = 12
        
        # Считаем отыгранные ставки (победы + поражения, исключая ничьи)
        played_games = await db.games.count_documents({
            "creator_id": bot_id,
            "status": "COMPLETED",
            "winner_id": {"$ne": None}
        })
        
        current_cycle_played = played_games % cycle_games
        remaining_slots = max(0, cycle_games - current_cycle_played)
        
        # Получаем текущие активные ставки
        active_games = await db.games.find({
            "creator_id": bot_id,
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        }).to_list(100)
        
        current_active_count = len(active_games)
        
        # Если активных ставок больше, чем remaining_slots - удаляем лишние
        if current_active_count > remaining_slots:
            excess_games = current_active_count - remaining_slots
            games_to_cancel = active_games[:excess_games]
            
            for game in games_to_cancel:
                game_obj = Game(**game)
                
                # Возвращаем гемы создателю
                if game_obj.bet_amount > 0:
                    await db.users.update_one(
                        {"id": game_obj.creator_id},
                        {"$inc": {"gems": game_obj.bet_amount}}
                    )
                
                # Удаляем игру
                await db.games.delete_one({"id": game_obj.id})
                
                logger.info(f"Cancelled excess game {game_obj.id} for bot {bot_id}")
        
        # Если активных ставок меньше, чем remaining_slots - создаем новые
        elif current_active_count < remaining_slots:
            needed_games = remaining_slots - current_active_count
            
            for _ in range(needed_games):
                # Создаем новую ставку для бота
                bet_amount = random.uniform(bot.min_bet_amount, bot.max_bet_amount)
                bet_amount = round(bet_amount, 2)
                
                # Убеждаемся, что у бота достаточно гемов
                bot_user = await db.users.find_one({"id": bot_id})
                if not bot_user or bot_user.get("gems", 0) < bet_amount:
                    # Если у бота нет гемов, добавляем их
                    await db.users.update_one(
                        {"id": bot_id},
                        {"$inc": {"gems": bet_amount}}
                    )
                
                # Создаем новую игру
                new_game = Game(
                    creator_id=bot_id,
                    bet_amount=bet_amount,
                    status=GameStatus.WAITING,
                    is_bot_game=True,
                    is_regular_bot_game=True
                )
                
                await db.games.insert_one(new_game.dict())
                
                # Списываем гемы
                await db.users.update_one(
                    {"id": bot_id},
                    {"$inc": {"gems": -bet_amount}}
                )
                
                logger.info(f"Created new game {new_game.id} for bot {bot_id}")
        
        # Получаем обновленный список активных ставок
        updated_active_games = await db.games.find({
            "creator_id": bot_id,
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        }).to_list(100)
        
        # Получаем статистику завершенных игр
        completed_games = await db.games.find({
            "creator_id": bot_id,
            "status": "COMPLETED"
        }).to_list(1000)
        
        # Подготавливаем данные для ответа
        bets_data = []
        for game in updated_active_games:
            bets_data.append({
                "id": game["id"],
                "created_at": game["created_at"],
                "bet_amount": game["bet_amount"],
                "status": game["status"].lower(),
                "opponent_name": game.get("opponent_name", "—"),
                "move": game.get("move", "—"),
                "selected_gem": game.get("selected_gem", "—"),
                "result": game.get("result", "—")
            })
        
        # Статистика
        total_bets = len(bets_data)
        total_bet_amount = sum(bet["bet_amount"] for bet in bets_data)
        
        # Статистика завершенных игр
        bot_wins = len([g for g in completed_games if g.get("winner_id") == bot_id])
        player_wins = len([g for g in completed_games if g.get("winner_id") and g.get("winner_id") != bot_id])
        draws = len([g for g in completed_games if not g.get("winner_id")])
        
        return {
            "bets": bets_data,
            "totalBets": total_bets,
            "totalBetAmount": total_bet_amount,
            "gamesPlayed": len(completed_games),
            "botWins": bot_wins,
            "playerWins": player_wins,
            "draws": draws,
            "remaining_slots": remaining_slots,
            "current_cycle_played": current_cycle_played,
            "cycle_games": cycle_games,
            "actions_taken": {
                "cancelled": max(0, current_active_count - remaining_slots),
                "created": max(0, remaining_slots - current_active_count)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing bot active bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to manage bot active bets"
        )

@api_router.post("/admin/games/reset-all", response_model=dict)
async def reset_all_bets_admin(current_user: User = Depends(get_current_admin)):
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

# Start NEW bot automation background task
async def start_bot_automation():
    """Start the NEW bot automation background task."""
    asyncio.create_task(new_bot_automation_task())

# ==============================================================================
# BOT SETTINGS API
# ==============================================================================

@api_router.get("/test-simple")
async def test_simple():
    """Test simple endpoint."""
    return {"message": "simple test working"}

@api_router.get("/admin/bot-settings-v2", response_model=dict)
async def get_bot_settings_v2(current_user: User = Depends(get_current_admin)):
    """Get bot settings - version 2 with unique name."""
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
        logger.error(f"Error fetching bot settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch bot settings: {str(e)}"
        )

@api_router.put("/admin/bot-settings-v2", response_model=dict)
async def update_bot_settings_v2(
    settings: BotSettingsRequest,
    current_user: User = Depends(get_current_admin)
):
    """Update bot settings - version 2 with unique name."""
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
        logger.error(f"Error updating bot settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update bot settings: {str(e)}"
        )

@api_router.get("/admin/bot-queue-stats", response_model=dict)
async def get_bot_queue_stats(current_user: User = Depends(get_current_admin)):
    """Get bot queue statistics."""
    try:
        # Count active regular bot bets
        active_regular_bets = await db.games.count_documents({
            "status": GameStatus.WAITING,
            "is_bot_game": True,
            "$or": [
                {"is_regular_bot_game": True},
                {"metadata.bot_type": "REGULAR"}
            ]
        })
        
        # Count active human bot bets
        active_human_bets = await db.games.count_documents({
            "status": GameStatus.WAITING,
            "is_bot_game": True,
            "$or": [
                {"is_regular_bot_game": False},
                {"metadata.bot_type": "HUMAN"}
            ]
        })
        
        # Count total regular bots
        total_regular_bots = await db.bots.count_documents({
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        })
        
        # Count total human bots
        total_human_bots = await db.bots.count_documents({
            "is_active": True,
            "$or": [
                {"type": "HUMAN"},
                {"bot_type": "HUMAN"}
            ]
        })
        
        # Get bot settings for max limits
        bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        max_regular_bets = bot_settings.get("globalMaxActiveBets", 50) if bot_settings else 50
        
        # Calculate queued bets (this is a simplified calculation)
        total_queued_bets = max(0, active_regular_bets - max_regular_bets)
        
        return {
            "success": True,
            "stats": {
                "totalActiveRegularBets": active_regular_bets,
                "totalQueuedBets": total_queued_bets,
                "totalRegularBots": total_regular_bots,
                "totalHumanBots": total_human_bots
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching bot queue stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch bot queue statistics"
        )

@api_router.put("/admin/bots/{bot_id}/limit", response_model=dict)
async def update_bot_limit(
    bot_id: str,
    limit_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update individual bot bet limit."""
    try:
        max_individual_bets = limit_data.get('maxIndividualBets', 12)
        
        # Validate limit
        if max_individual_bets < 1 or max_individual_bets > 50:
            raise HTTPException(
                status_code=400,
                detail="Individual bot limit must be between 1 and 50"
            )
        
        # Get global settings
        global_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        global_max = global_settings.get("globalMaxActiveBets", 50) if global_settings else 50
        
        # Get all other active bots to check global limit
        other_bots = await db.bots.find({
            "id": {"$ne": bot_id},
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        }).to_list(None)
        
        # Calculate total limit of other bots
        other_bots_total = sum(bot.get("max_individual_bets", 12) for bot in other_bots)
        
        # Check if new limit would exceed global limit
        if other_bots_total + max_individual_bets > global_max:
            raise HTTPException(
                status_code=400,
                detail=f"Total bots limit would exceed global limit {global_max}. Available: {global_max - other_bots_total}"
            )
        
        # Update bot limit
        result = await db.bots.update_one(
            {"id": bot_id},
            {
                "$set": {
                    "max_individual_bets": max_individual_bets,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Bot not found"
            )
        
        return {
            "success": True,
            "message": "Bot limit updated successfully",
            "bot_id": bot_id,
            "new_limit": max_individual_bets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot limit: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update bot limit"
        )

@api_router.post("/admin/bots/{bot_id}/priority/move-up", response_model=dict)
async def move_bot_priority_up(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Move bot priority up (decrease priority_order number)."""
    try:
        # Get current bot
        current_bot = await db.bots.find_one({"id": bot_id})
        if not current_bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        current_priority = current_bot.get("priority_order", 0)
        
        # Find bot with the next higher priority (lower number)
        higher_priority_bot = await db.bots.find_one({
            "priority_order": {"$lt": current_priority},
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        }, sort=[("priority_order", -1)])
        
        if not higher_priority_bot:
            return {
                "success": False,
                "message": "Bot is already at highest priority"
            }
        
        # Swap priorities
        higher_priority = higher_priority_bot.get("priority_order", 0)
        
        # Update both bots
        await db.bots.update_one(
            {"id": bot_id},
            {"$set": {"priority_order": higher_priority, "updated_at": datetime.utcnow()}}
        )
        
        await db.bots.update_one(
            {"id": higher_priority_bot["id"]},
            {"$set": {"priority_order": current_priority, "updated_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "message": "Bot priority moved up successfully",
            "bot_id": bot_id,
            "new_priority": higher_priority
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving bot priority up: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to move bot priority up"
        )

@api_router.post("/admin/bots/{bot_id}/priority/move-down", response_model=dict)
async def move_bot_priority_down(
    bot_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Move bot priority down (increase priority_order number)."""
    try:
        # Get current bot
        current_bot = await db.bots.find_one({"id": bot_id})
        if not current_bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        current_priority = current_bot.get("priority_order", 0)
        
        # Find bot with the next lower priority (higher number)
        lower_priority_bot = await db.bots.find_one({
            "priority_order": {"$gt": current_priority},
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        }, sort=[("priority_order", 1)])
        
        if not lower_priority_bot:
            return {
                "success": False,
                "message": "Bot is already at lowest priority"
            }
        
        # Swap priorities
        lower_priority = lower_priority_bot.get("priority_order", 0)
        
        # Update both bots
        await db.bots.update_one(
            {"id": bot_id},
            {"$set": {"priority_order": lower_priority, "updated_at": datetime.utcnow()}}
        )
        
        await db.bots.update_one(
            {"id": lower_priority_bot["id"]},
            {"$set": {"priority_order": current_priority, "updated_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "message": "Bot priority moved down successfully",
            "bot_id": bot_id,
            "new_priority": lower_priority
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving bot priority down: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to move bot priority down"
        )

@api_router.post("/admin/bots/priority/reset", response_model=dict)
async def reset_bot_priorities(current_user: User = Depends(get_current_admin)):
    """Reset all bot priorities to default order (by creation date)."""
    try:
        # Get all active regular bots sorted by creation date
        bots = await db.bots.find({
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        }).sort("created_at", 1).to_list(None)
        
        # Update priorities in order
        for index, bot in enumerate(bots, 1):
            await db.bots.update_one(
                {"id": bot["id"]},
                {
                    "$set": {
                        "priority_order": index,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        return {
            "success": True,
            "message": f"Reset priorities for {len(bots)} bots",
            "bots_updated": len(bots)
        }
        
    except Exception as e:
        logger.error(f"Error resetting bot priorities: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to reset bot priorities"
        )

@api_router.get("/admin/bots/analytics", response_model=dict)
async def get_bot_analytics(
    timeRange: str = "24h",  # 24h, 7d, 30d
    botId: Optional[str] = None,
    current_user: User = Depends(get_current_admin)
):
    """Get detailed analytics for bot queue and performance."""
    try:
        # Calculate time range
        now = datetime.now()
        if timeRange == "24h":
            start_time = now - timedelta(hours=24)
        elif timeRange == "7d":
            start_time = now - timedelta(days=7)
        elif timeRange == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)
        
        # Base query for filtering
        base_query = {"created_at": {"$gte": start_time}}
        if botId:
            base_query["creator_id"] = botId
        
        # Generate time series data
        queue_wait_times = []
        bot_loading_stats = []
        
        # Calculate intervals based on time range
        if timeRange == "24h":
            intervals = 24
            interval_duration = timedelta(hours=1)
        elif timeRange == "7d":
            intervals = 7
            interval_duration = timedelta(days=1)
        else:  # 30d
            intervals = 30
            interval_duration = timedelta(days=1)
        
        # Generate analytics data for each interval
        for i in range(intervals):
            interval_start = start_time + (i * interval_duration)
            interval_end = start_time + ((i + 1) * interval_duration)
            
            # Query games in this interval
            interval_query = {
                **base_query,
                "created_at": {"$gte": interval_start, "$lt": interval_end}
            }
            
            # Get games created in this interval
            games = await db.games.find(interval_query).to_list(None)
            
            # Calculate wait time (mock calculation)
            total_wait_time = 0
            game_count = len(games)
            
            for game in games:
                # Mock wait time calculation (in real implementation, this would be actual queue time)
                wait_time = random.randint(30, 300)  # 30 seconds to 5 minutes
                total_wait_time += wait_time
            
            avg_wait_time = (total_wait_time / game_count / 60) if game_count > 0 else 0  # Convert to minutes
            
            queue_wait_times.append({
                "timestamp": interval_start.isoformat(),
                "avgWaitTime": round(avg_wait_time, 1),
                "gameCount": game_count
            })
            
            # Calculate loading percentage
            active_bots = await db.bots.count_documents({
                "is_active": True,
                "$or": [
                    {"type": "REGULAR"},
                    {"bot_type": "REGULAR"}
                ]
            })
            
            # Get bot settings for max capacity
            bot_settings = await db.bot_settings.find_one({"id": "bot_settings"})
            max_capacity = bot_settings.get("globalMaxActiveBets", 50) if bot_settings else 50
            
            current_active_bets = await db.games.count_documents({
                "status": "waiting",
                "is_bot_game": True,
                "created_at": {"$gte": interval_start, "$lt": interval_end}
            })
            
            load_percentage = (current_active_bets / max_capacity * 100) if max_capacity > 0 else 0
            
            bot_loading_stats.append({
                "timestamp": interval_start.isoformat(),
                "loadPercentage": round(load_percentage, 1),
                "activeBets": current_active_bets,
                "maxCapacity": max_capacity
            })
        
        # Calculate priority effectiveness
        priority_effectiveness = {}
        bots = await db.bots.find({
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        }).to_list(None)
        
        for bot in bots:
            priority = bot.get("priority_order", 999)
            
            # Count successful activations for this bot
            successful_activations = await db.games.count_documents({
                "creator_id": bot["id"],
                "status": {"$in": ["active", "completed"]},
                "created_at": {"$gte": start_time}
            })
            
            # Count total attempts
            total_attempts = await db.games.count_documents({
                "creator_id": bot["id"],
                "created_at": {"$gte": start_time}
            })
            
            activation_rate = (successful_activations / total_attempts * 100) if total_attempts > 0 else 0
            
            if priority not in priority_effectiveness:
                priority_effectiveness[priority] = {
                    "activationRate": 0,
                    "totalAttempts": 0,
                    "successfulActivations": 0
                }
            
            priority_effectiveness[priority]["activationRate"] += activation_rate
            priority_effectiveness[priority]["totalAttempts"] += total_attempts
            priority_effectiveness[priority]["successfulActivations"] += successful_activations
        
        # Calculate average activation rate per priority
        for priority in priority_effectiveness:
            if priority_effectiveness[priority]["totalAttempts"] > 0:
                priority_effectiveness[priority]["activationRate"] = round(
                    priority_effectiveness[priority]["successfulActivations"] / 
                    priority_effectiveness[priority]["totalAttempts"] * 100, 1
                )
        
        # Calculate activation statistics
        successful_activations = []
        failed_activations = []
        
        for i in range(intervals):
            interval_start = start_time + (i * interval_duration)
            interval_end = start_time + ((i + 1) * interval_duration)
            
            successful = await db.games.count_documents({
                "status": {"$in": ["active", "completed"]},
                "created_at": {"$gte": interval_start, "$lt": interval_end},
                "is_bot_game": True
            })
            
            failed = await db.games.count_documents({
                "status": "cancelled",
                "created_at": {"$gte": interval_start, "$lt": interval_end},
                "is_bot_game": True
            })
            
            successful_activations.append(successful)
            failed_activations.append(failed)
        
        return {
            "success": True,
            "data": {
                "queueWaitTimes": queue_wait_times,
                "botLoadingStats": bot_loading_stats,
                "priorityEffectiveness": priority_effectiveness,
                "activationStats": {
                    "successful": successful_activations,
                    "failed": failed_activations
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching bot analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch bot analytics"
        )

@api_router.post("/admin/bots/reports/generate", response_model=dict)
async def generate_bot_report(
    request: dict,
    current_user: User = Depends(get_current_admin)
):
    """Generate a comprehensive bot report."""
    try:
        report_type = request.get("type", "queue_performance")
        time_range = request.get("timeRange", "7d")
        
        # Calculate time range
        now = datetime.now()
        if time_range == "24h":
            start_time = now - timedelta(hours=24)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        elif time_range == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=7)
        
        # Generate report based on type
        if report_type == "queue_performance":
            report = await generate_queue_performance_report(start_time, now)
        elif report_type == "priority_effectiveness":
            report = await generate_priority_effectiveness_report(start_time, now)
        elif report_type == "bot_utilization":
            report = await generate_bot_utilization_report(start_time, now)
        elif report_type == "system_health":
            report = await generate_system_health_report(start_time, now)
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        # Add common report metadata
        report.update({
            "id": str(uuid.uuid4()),
            "type": report_type,
            "timeRange": time_range,
            "generated_at": now.isoformat(),
            "period": f"{start_time.strftime('%Y-%m-%d')} - {now.strftime('%Y-%m-%d')}"
        })
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Error generating bot report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate bot report"
        )

@api_router.post("/admin/bots/reports/export", response_model=dict)
async def export_bot_report(
    request: dict,
    current_user: User = Depends(get_current_admin)
):
    """Export bot report in specified format."""
    try:
        report_id = request.get("reportId")
        format_type = request.get("format", "pdf")
        
        if not report_id:
            raise HTTPException(status_code=400, detail="Report ID is required")
        
        # For now, return success - in real implementation, this would generate actual files
        return {
            "success": True,
            "message": f"Report exported in {format_type.upper()} format",
            "download_url": f"/reports/{report_id}.{format_type}"
        }
        
    except Exception as e:
        logger.error(f"Error exporting bot report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to export bot report"
        )

async def generate_queue_performance_report(start_time: datetime, end_time: datetime) -> dict:
    """Generate queue performance analysis report."""
    try:
        # Get queue-related statistics
        total_games = await db.games.count_documents({
            "created_at": {"$gte": start_time, "$lt": end_time},
            "is_bot_game": True
        })
        
        waiting_games = await db.games.count_documents({
            "status": "waiting",
            "is_bot_game": True,
            "created_at": {"$gte": start_time, "$lt": end_time}
        })
        
        active_games = await db.games.count_documents({
            "status": "active",
            "is_bot_game": True,
            "created_at": {"$gte": start_time, "$lt": end_time}
        })
        
        completed_games = await db.games.count_documents({
            "status": "completed",
            "is_bot_game": True,
            "created_at": {"$gte": start_time, "$lt": end_time}
        })
        
        # Calculate average wait time (mock calculation)
        avg_wait_time = random.uniform(1.5, 4.0)  # 1.5 to 4 minutes
        
        # Calculate queue efficiency
        queue_efficiency = (completed_games / total_games * 100) if total_games > 0 else 0
        
        return {
            "name": "Производительность очереди",
            "metrics": {
                "avg_wait_time": round(avg_wait_time, 1),
                "queue_efficiency": round(queue_efficiency, 1),
                "total_games": total_games,
                "waiting_games": waiting_games,
                "active_games": active_games,
                "completed_games": completed_games
            },
            "insights": [
                "Среднее время ожидания в пределах нормы",
                "Эффективность очереди соответствует стандартам",
                "Рекомендуется мониторинг пиковых периодов"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating queue performance report: {e}")
        raise e

async def generate_priority_effectiveness_report(start_time: datetime, end_time: datetime) -> dict:
    """Generate priority system effectiveness report."""
    try:
        # Get bots with priorities
        bots = await db.bots.find({
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        }).to_list(None)
        
        priority_stats = {}
        
        for bot in bots:
            priority = bot.get("priority_order", 999)
            
            games_count = await db.games.count_documents({
                "creator_id": bot["id"],
                "created_at": {"$gte": start_time, "$lt": end_time}
            })
            
            successful_games = await db.games.count_documents({
                "creator_id": bot["id"],
                "status": {"$in": ["active", "completed"]},
                "created_at": {"$gte": start_time, "$lt": end_time}
            })
            
            success_rate = (successful_games / games_count * 100) if games_count > 0 else 0
            
            if priority not in priority_stats:
                priority_stats[priority] = {
                    "priority": priority,
                    "bots_count": 0,
                    "total_games": 0,
                    "successful_games": 0,
                    "success_rate": 0
                }
            
            priority_stats[priority]["bots_count"] += 1
            priority_stats[priority]["total_games"] += games_count
            priority_stats[priority]["successful_games"] += successful_games
        
        # Calculate average success rates
        for priority in priority_stats:
            stats = priority_stats[priority]
            stats["success_rate"] = round(
                (stats["successful_games"] / stats["total_games"] * 100) if stats["total_games"] > 0 else 0, 1
            )
        
        return {
            "name": "Эффективность приоритетов",
            "priority_stats": list(priority_stats.values()),
            "insights": [
                "Высокоприоритетные боты показывают лучшие результаты",
                "Система приоритетов работает эффективно",
                "Рекомендуется регулярный пересмотр приоритетов"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating priority effectiveness report: {e}")
        raise e

async def generate_bot_utilization_report(start_time: datetime, end_time: datetime) -> dict:
    """Generate bot utilization analysis report."""
    try:
        # Get bot utilization statistics
        active_bots = await db.bots.count_documents({
            "is_active": True,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        })
        
        inactive_bots = await db.bots.count_documents({
            "is_active": False,
            "$or": [
                {"type": "REGULAR"},
                {"bot_type": "REGULAR"}
            ]
        })
        
        # Calculate utilization metrics
        total_capacity = await db.bot_settings.find_one({"id": "bot_settings"})
        max_capacity = total_capacity.get("globalMaxActiveBets", 50) if total_capacity else 50
        
        current_usage = await db.games.count_documents({
            "status": "waiting",
            "is_bot_game": True
        })
        
        utilization_rate = (current_usage / max_capacity * 100) if max_capacity > 0 else 0
        
        return {
            "name": "Использование ботов",
            "utilization": {
                "active_bots": active_bots,
                "inactive_bots": inactive_bots,
                "total_capacity": max_capacity,
                "current_usage": current_usage,
                "utilization_rate": round(utilization_rate, 1)
            },
            "insights": [
                f"Система использует {utilization_rate:.1f}% от доступной мощности",
                f"Активных ботов: {active_bots}, неактивных: {inactive_bots}",
                "Рекомендуется оптимизация загрузки"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating bot utilization report: {e}")
        raise e

async def generate_system_health_report(start_time: datetime, end_time: datetime) -> dict:
    """Generate system health analysis report."""
    try:
        # Get system health metrics
        total_errors = await db.games.count_documents({
            "status": "cancelled",
            "created_at": {"$gte": start_time, "$lt": end_time}
        })
        
        total_operations = await db.games.count_documents({
            "created_at": {"$gte": start_time, "$lt": end_time}
        })
        
        error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
        success_rate = 100 - error_rate
        
        # System stability metrics
        uptime = 99.8  # Mock uptime percentage
        response_time = random.uniform(0.1, 0.5)  # Mock response time
        
        return {
            "name": "Здоровье системы",
            "health_metrics": {
                "success_rate": round(success_rate, 1),
                "error_rate": round(error_rate, 1),
                "system_uptime": uptime,
                "avg_response_time": round(response_time, 2),
                "total_operations": total_operations,
                "total_errors": total_errors
            },
            "insights": [
                f"Система работает стабильно с {success_rate:.1f}% успешностью",
                f"Время безотказной работы: {uptime}%",
                "Система готова к увеличению нагрузки"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating system health report: {e}")
        raise e

# ==============================================================================
# SIMPLE TEST ENDPOINT
# ==============================================================================

@api_router.get("/test-new-endpoint")
async def test_new_endpoint():
    """Test new endpoint to verify duplicates are fixed."""
    return {"message": "New endpoint working", "status": "success"}

# ==============================================================================
# SOUNDS API ENDPOINTS  
# ==============================================================================

@api_router.get("/admin/sounds", response_model=List[SoundResponse])
async def get_sounds(current_user: User = Depends(get_current_admin)):
    """Get all sounds (admin only)."""
    try:
        sounds = await db.sounds.find().to_list(1000)
        response_sounds = []
        
        for sound in sounds:
            sound_response = SoundResponse(
                id=sound["id"],
                name=sound["name"],
                category=sound["category"],
                event_trigger=sound["event_trigger"],
                game_type=sound["game_type"],
                is_enabled=sound["is_enabled"],
                priority=sound["priority"],
                volume=sound["volume"],
                delay=sound["delay"],
                can_repeat=sound["can_repeat"],
                has_audio_file=bool(sound.get("audio_data")),
                file_format=sound.get("file_format"),
                file_size=sound.get("file_size"),
                is_default=sound.get("is_default", False),
                created_at=sound["created_at"],
                updated_at=sound["updated_at"]
            )
            response_sounds.append(sound_response)
            
        return response_sounds
        
    except Exception as e:
        logger.error(f"Error getting sounds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sounds"
        )

@api_router.post("/admin/sounds", response_model=SoundResponse)
async def create_sound(sound_data: CreateSoundRequest, current_user: User = Depends(get_current_admin)):
    """Create a new sound (admin only)."""
    try:
        # Create new sound
        new_sound = Sound(
            name=sound_data.name,
            category=sound_data.category,
            event_trigger=sound_data.event_trigger,
            game_type=sound_data.game_type,
            is_enabled=sound_data.is_enabled,
            priority=sound_data.priority,
            volume=sound_data.volume,
            delay=sound_data.delay,
            can_repeat=sound_data.can_repeat
        )
        
        await db.sounds.insert_one(new_sound.dict())
        
        return SoundResponse(
            id=new_sound.id,
            name=new_sound.name,
            category=new_sound.category,
            event_trigger=new_sound.event_trigger,
            game_type=new_sound.game_type,
            is_enabled=new_sound.is_enabled,
            priority=new_sound.priority,
            volume=new_sound.volume,
            delay=new_sound.delay,
            can_repeat=new_sound.can_repeat,
            has_audio_file=False,
            is_default=new_sound.is_default,
            created_at=new_sound.created_at,
            updated_at=new_sound.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating sound: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sound"
        )

@api_router.put("/admin/sounds/{sound_id}", response_model=SoundResponse)
async def update_sound(sound_id: str, sound_data: UpdateSoundRequest, current_user: User = Depends(get_current_admin)):
    """Update a sound (admin only)."""
    try:
        # Check if sound exists
        existing_sound = await db.sounds.find_one({"id": sound_id})
        if not existing_sound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sound not found"
            )
        
        # Prepare update data
        update_data = {}
        if sound_data.name is not None:
            update_data["name"] = sound_data.name
        if sound_data.category is not None:
            update_data["category"] = sound_data.category
        if sound_data.event_trigger is not None:
            update_data["event_trigger"] = sound_data.event_trigger
        if sound_data.game_type is not None:
            update_data["game_type"] = sound_data.game_type
        if sound_data.is_enabled is not None:
            update_data["is_enabled"] = sound_data.is_enabled
        if sound_data.priority is not None:
            update_data["priority"] = sound_data.priority
        if sound_data.volume is not None:
            update_data["volume"] = sound_data.volume
        if sound_data.delay is not None:
            update_data["delay"] = sound_data.delay
        if sound_data.can_repeat is not None:
            update_data["can_repeat"] = sound_data.can_repeat
            
        update_data["updated_at"] = datetime.utcnow()
        
        # Update sound
        await db.sounds.update_one(
            {"id": sound_id},
            {"$set": update_data}
        )
        
        # Get updated sound
        updated_sound = await db.sounds.find_one({"id": sound_id})
        
        return SoundResponse(
            id=updated_sound["id"],
            name=updated_sound["name"],
            category=updated_sound["category"],
            event_trigger=updated_sound["event_trigger"],
            game_type=updated_sound["game_type"],
            is_enabled=updated_sound["is_enabled"],
            priority=updated_sound["priority"],
            volume=updated_sound["volume"],
            delay=updated_sound["delay"],
            can_repeat=updated_sound["can_repeat"],
            has_audio_file=bool(updated_sound.get("audio_data")),
            file_format=updated_sound.get("file_format"),
            file_size=updated_sound.get("file_size"),
            is_default=updated_sound.get("is_default", False),
            created_at=updated_sound["created_at"],
            updated_at=updated_sound["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sound: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update sound"
        )

@api_router.delete("/admin/sounds/{sound_id}", response_model=dict)
async def delete_sound(sound_id: str, current_user: User = Depends(get_current_admin)):
    """Delete a sound (admin only)."""
    try:
        # Check if sound exists
        existing_sound = await db.sounds.find_one({"id": sound_id})
        if not existing_sound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sound not found"
            )
        
        # Don't allow deleting default sounds
        if existing_sound.get("is_default", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete default sounds"
            )
        
        # Delete sound
        await db.sounds.delete_one({"id": sound_id})
        
        return {"success": True, "message": "Sound deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sound: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sound"
        )

@api_router.post("/admin/sounds/{sound_id}/upload", response_model=SoundResponse)
async def upload_sound_file(sound_id: str, file_data: UploadSoundFileRequest, current_user: User = Depends(get_current_admin)):
    """Upload audio file for a sound (admin only)."""
    try:
        # Check if sound exists
        existing_sound = await db.sounds.find_one({"id": sound_id})
        if not existing_sound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sound not found"
            )
        
        # Check file size (5MB max)
        if file_data.file_size > 5242880:  # 5MB in bytes
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 5MB limit"
            )
        
        # Update sound with file data
        update_data = {
            "audio_data": file_data.file_data,
            "file_format": file_data.file_format,
            "file_size": file_data.file_size,
            "updated_at": datetime.utcnow()
        }
        
        await db.sounds.update_one(
            {"id": sound_id},
            {"$set": update_data}
        )
        
        # Get updated sound
        updated_sound = await db.sounds.find_one({"id": sound_id})
        
        return SoundResponse(
            id=updated_sound["id"],
            name=updated_sound["name"],
            category=updated_sound["category"],
            event_trigger=updated_sound["event_trigger"],
            game_type=updated_sound["game_type"],
            is_enabled=updated_sound["is_enabled"],
            priority=updated_sound["priority"],
            volume=updated_sound["volume"],
            delay=updated_sound["delay"],
            can_repeat=updated_sound["can_repeat"],
            has_audio_file=True,
            file_format=updated_sound["file_format"],
            file_size=updated_sound["file_size"],
            is_default=updated_sound.get("is_default", False),
            created_at=updated_sound["created_at"],
            updated_at=updated_sound["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading sound file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload sound file"
        )

# ==============================================================================
# HUMAN BOTS API
# ==============================================================================

async def get_human_bot_active_bets_count(bot_id: str) -> int:
    """Get count of active bets for a human bot (only WAITING, ACTIVE, REVEAL statuses)."""
    try:
        count = await db.games.count_documents({
            "creator_id": bot_id,
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        })
        return count
    except Exception as e:
        logger.error(f"Error counting active bets for human bot {bot_id}: {e}")
        return 0

@api_router.get("/admin/human-bots", response_model=HumanBotsListResponse)
async def list_human_bots(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin)
):
    """List human bots with pagination."""
    try:
        skip = (page - 1) * limit
        
        # Get total count
        total_bots = await db.human_bots.count_documents({})
        
        # Get bots
        bots_cursor = db.human_bots.find({}).sort("created_at", -1).skip(skip).limit(limit)
        bots_list = await bots_cursor.to_list(length=limit)
        
        # Format response bots with active bets count
        response_bots = []
        for bot in bots_list:
            # Calculate win rate
            win_rate = (bot.get("total_games_won", 0) / max(bot.get("total_games_played", 1), 1)) * 100
            
            # Get active bets count
            active_bets_count = await get_human_bot_active_bets_count(bot["id"])
            
            response_bot = HumanBotResponse(
                id=bot["id"],
                name=bot["name"],
                character=bot["character"],
                is_active=bot["is_active"],
                min_bet=bot["min_bet"],
                max_bet=bot["max_bet"],
                bet_limit=bot.get("bet_limit", 12),  # Default to 12 if missing
                win_percentage=bot["win_percentage"],
                loss_percentage=bot["loss_percentage"],
                draw_percentage=bot["draw_percentage"],
                min_delay=bot["min_delay"],
                max_delay=bot["max_delay"],
                use_commit_reveal=bot["use_commit_reveal"],
                logging_level=bot["logging_level"],
                total_games_played=bot.get("total_games_played", 0),
                total_games_won=bot.get("total_games_won", 0),
                total_amount_wagered=bot.get("total_amount_wagered", 0.0),
                total_amount_won=bot.get("total_amount_won", 0.0),
                win_rate=round(win_rate, 2),
                last_action_time=bot.get("last_action_time"),
                created_at=bot["created_at"],
                updated_at=bot["updated_at"]
            )
            
            # Add active bets count as additional field
            response_bot_dict = response_bot.dict()
            response_bot_dict["active_bets_count"] = active_bets_count
            response_bots.append(response_bot_dict)
        
        # Calculate pagination
        total_pages = (total_bots + limit - 1) // limit
        
        return HumanBotsListResponse(
            success=True,
            bots=response_bots,
            pagination=PaginationInfo(
                current_page=page,
                total_pages=total_pages,
                per_page=limit,
                total_items=total_bots,
                has_next=page < total_pages,
                has_prev=page > 1
            )
        )
        
    except Exception as e:
        logger.error(f"Error listing human bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list human bots"
        )

@api_router.post("/admin/human-bots", response_model=HumanBotResponse)
async def create_human_bot(
    bot_data: CreateHumanBotRequest,
    current_admin: User = Depends(get_current_admin)
):
    """Create a new human bot."""
    try:
        # Validate percentages sum to 100
        total_percentage = bot_data.win_percentage + bot_data.loss_percentage + bot_data.draw_percentage
        if abs(total_percentage - 100.0) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Win, loss, and draw percentages must sum to 100%"
            )
        
        # Check if name is unique
        existing_bot = await db.human_bots.find_one({"name": bot_data.name})
        if existing_bot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot name already exists"
            )
        
        # Validate bet range
        if bot_data.min_bet >= bot_data.max_bet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum bet must be less than maximum bet"
            )
        
        # Validate delay range
        if bot_data.min_delay >= bot_data.max_delay:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum delay must be less than maximum delay"
            )
        
        # Validate bet_limit against global limit
        bet_limit = bot_data.bet_limit or 12  # Default bet_limit
        
        # Get global settings for max limit
        global_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        global_max = global_settings.get("max_active_bets_human", 100) if global_settings else 100
        
        # Get all existing human bots to check total limit
        existing_bots = await db.human_bots.find({}).to_list(None)
        
        # Calculate total limit of existing bots
        existing_bots_total = sum(bot.get("bet_limit", 12) for bot in existing_bots)
        
        # Check if new bot limit would exceed global limit
        if existing_bots_total + bet_limit > global_max:
            available = global_max - existing_bots_total
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bot limit ({bet_limit}) would exceed global limit. Available: {available}/{global_max}"
            )
        
        # Create human bot
        human_bot = HumanBot(**bot_data.dict())
        await db.human_bots.insert_one(human_bot.dict())
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_admin.id,
            action="CREATE_HUMAN_BOT",
            target_type="human_bot",
            target_id=human_bot.id,
            details={
                "name": human_bot.name,
                "character": human_bot.character,
                "bet_range": f"${human_bot.min_bet}-${human_bot.max_bet}"
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        # Return response
        response = HumanBotResponse(
            **human_bot.dict(),
            win_rate=0.0  # New bot has no games yet
        )
        
        logger.info(f"Human bot created: {human_bot.name} ({human_bot.character})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating human bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create human bot"
        )

@api_router.put("/admin/human-bots/{bot_id}", response_model=HumanBotResponse)
async def update_human_bot(
    bot_id: str,
    bot_data: UpdateHumanBotRequest,
    current_admin: User = Depends(get_current_admin)
):
    """Update a human bot."""
    try:
        # Find existing bot
        existing_bot = await db.human_bots.find_one({"id": bot_id})
        if not existing_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Human bot not found"
            )
        
        # Prepare update data
        update_data = {}
        for field, value in bot_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # Validate percentages if any are provided
        if any(key in update_data for key in ["win_percentage", "loss_percentage", "draw_percentage"]):
            current_bot = HumanBot(**existing_bot)
            win_pct = update_data.get("win_percentage", current_bot.win_percentage)
            loss_pct = update_data.get("loss_percentage", current_bot.loss_percentage)
            draw_pct = update_data.get("draw_percentage", current_bot.draw_percentage)
            
            total_percentage = win_pct + loss_pct + draw_pct
            if abs(total_percentage - 100.0) > 0.01:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Win, loss, and draw percentages must sum to 100%"
                )
        
        # Check name uniqueness if name is being changed
        if "name" in update_data and update_data["name"] != existing_bot["name"]:
            name_exists = await db.human_bots.find_one({"name": update_data["name"]})
            if name_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bot name already exists"
                )
        
        # Validate bet range if being updated
        min_bet = update_data.get("min_bet", existing_bot["min_bet"])
        max_bet = update_data.get("max_bet", existing_bot["max_bet"])
        if min_bet >= max_bet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum bet must be less than maximum bet"
            )
        
        # Validate delay range if being updated
        min_delay = update_data.get("min_delay", existing_bot["min_delay"])
        max_delay = update_data.get("max_delay", existing_bot["max_delay"])
        if min_delay >= max_delay:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum delay must be less than maximum delay"
            )
        
        # Validate bet_limit if being updated
        if "bet_limit" in update_data:
            new_bet_limit = update_data["bet_limit"]
            
            # Get global settings for max limit
            global_settings = await db.bot_settings.find_one({"id": "bot_settings"})
            global_max = global_settings.get("max_active_bets_human", 100) if global_settings else 100
            
            # Get all other human bots to check total limit
            other_bots = await db.human_bots.find({
                "id": {"$ne": bot_id}
            }).to_list(None)
            
            # Calculate total limit of other bots
            other_bots_total = sum(bot.get("bet_limit", 12) for bot in other_bots)
            
            # Check if new limit would exceed global limit
            if other_bots_total + new_bet_limit > global_max:
                available = global_max - other_bots_total
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bot limit ({new_bet_limit}) would exceed global limit. Available: {available}/{global_max}"
                )
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update bot
        await db.human_bots.update_one(
            {"id": bot_id},
            {"$set": update_data}
        )
        
        # Get updated bot
        updated_bot_data = await db.human_bots.find_one({"id": bot_id})
        updated_bot = HumanBot(**updated_bot_data)
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_admin.id,
            action="UPDATE_HUMAN_BOT",
            target_type="human_bot",
            target_id=bot_id,
            details={"updated_fields": list(update_data.keys())}
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        # Return response
        response = HumanBotResponse(
            **updated_bot.dict(),
            win_rate=(updated_bot.total_games_won / updated_bot.total_games_played * 100) if updated_bot.total_games_played > 0 else 0
        )
        
        logger.info(f"Human bot updated: {bot_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating human bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update human bot"
        )

@api_router.delete("/admin/human-bots/{bot_id}", response_model=dict)
async def delete_human_bot(
    bot_id: str,
    force_delete: bool = False,
    current_admin: User = Depends(get_current_admin)
):
    """Delete a human bot. If force_delete=true, will cancel active games and refund players."""
    try:
        # Find existing bot
        existing_bot = await db.human_bots.find_one({"id": bot_id})
        if not existing_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Human bot not found"
            )
        
        # Get active games details
        active_games_cursor = db.games.find({
            "creator_id": bot_id,
            "status": {"$in": ["WAITING", "ACTIVE", "REVEAL"]}
        })
        active_games_list = await active_games_cursor.to_list(None)
        active_games_count = len(active_games_list)
        
        # If has active games and not force delete - return detailed info
        if active_games_count > 0 and not force_delete:
            games_info = []
            total_frozen_balance = 0
            for game in active_games_list:
                # Calculate frozen balance (commission)
                commission = game.get('total_bet_amount', 0) * 0.06
                total_frozen_balance += commission
                
                games_info.append({
                    "game_id": game.get("id", ""),
                    "bet_amount": game.get('total_bet_amount', 0),
                    "status": game.get('status', ''),
                    "opponent": game.get('opponent_name', 'Не найден'),
                    "created_at": game.get('created_at', '').isoformat() if game.get('created_at') else ''
                })
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Cannot delete bot with active games",
                    "active_games_count": active_games_count,
                    "total_frozen_balance": total_frozen_balance,
                    "games": games_info[:5],  # Show only first 5 games
                    "force_delete_required": True
                }
            )
        
        # If force delete - cancel all active games and refund players
        cancelled_games = 0
        refunded_amount = 0
        
        if active_games_count > 0 and force_delete:
            for game in active_games_list:
                try:
                    game_id = game.get("id")
                    opponent_id = game.get("opponent_id")
                    total_bet_amount = game.get("total_bet_amount", 0)
                    commission_amount = total_bet_amount * 0.06
                    
                    # Cancel the game
                    await db.games.update_one(
                        {"id": game_id},
                        {
                            "$set": {
                                "status": "CANCELLED",
                                "cancelled_reason": "Bot deleted by admin",
                                "cancelled_at": datetime.utcnow(),
                                "cancelled_by": "ADMIN"
                            }
                        }
                    )
                    
                    # Refund opponent if exists
                    if opponent_id and opponent_id != bot_id:
                        opponent = await db.users.find_one({"id": opponent_id})
                        if opponent:
                            # Return bet amount + commission to opponent
                            refund_amount = total_bet_amount / 2  # Opponent's bet share
                            await db.users.update_one(
                                {"id": opponent_id},
                                {"$inc": {"balance": refund_amount}}
                            )
                            
                            # Also return commission if it was frozen
                            if commission_amount > 0:
                                await db.users.update_one(
                                    {"id": opponent_id},
                                    {"$inc": {"balance": commission_amount}}
                                )
                            
                            refunded_amount += refund_amount + commission_amount
                            
                            # Log the refund
                            logger.info(f"Refunded ${refund_amount + commission_amount:.2f} to user {opponent_id} for cancelled game {game_id}")
                    
                    cancelled_games += 1
                    
                except Exception as game_error:
                    logger.error(f"Error cancelling game {game_id}: {game_error}")
                    continue
        
        # Delete bot
        await db.human_bots.delete_one({"id": bot_id})
        
        # Delete bot logs
        await db.human_bot_logs.delete_many({"human_bot_id": bot_id})
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_admin.id,
            action="DELETE_HUMAN_BOT",
            target_type="human_bot",
            target_id=bot_id,
            details={
                "name": existing_bot["name"],
                "force_delete": force_delete,
                "cancelled_games": cancelled_games,
                "refunded_amount": refunded_amount
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        success_message = f"Human bot deleted successfully"
        if cancelled_games > 0:
            success_message += f". Cancelled {cancelled_games} active games, refunded ${refunded_amount:.2f} to players"
        
        logger.info(f"Human bot deleted: {bot_id}, cancelled games: {cancelled_games}, refunded: ${refunded_amount:.2f}")
        
        return {
            "success": True, 
            "message": success_message,
            "cancelled_games": cancelled_games,
            "refunded_amount": refunded_amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting human bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete human bot"
        )

@api_router.post("/admin/human-bots/bulk-create", response_model=dict)
async def bulk_create_human_bots(
    bulk_data: BulkCreateHumanBotsRequest,
    current_admin: User = Depends(get_current_admin)
):
    """Create multiple human bots at once."""
    try:
        # Validate percentages sum to 100
        total_percentage = bulk_data.win_percentage + bulk_data.loss_percentage + bulk_data.draw_percentage
        if abs(total_percentage - 100.0) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Win, loss, and draw percentages must sum to 100%"
            )
        
        # Validate ranges
        if bulk_data.min_bet_range[0] >= bulk_data.min_bet_range[1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid min bet range"
            )
        
        if bulk_data.max_bet_range[0] >= bulk_data.max_bet_range[1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid max bet range"
            )
        
        if bulk_data.bet_limit_range[0] > bulk_data.bet_limit_range[1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bet limit range"
            )
        
        if bulk_data.delay_range[0] >= bulk_data.delay_range[1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid delay range"
            )
        
        # Validate total bet_limit against global limit
        # Get global settings for max limit
        global_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        global_max = global_settings.get("max_active_bets_human", 100) if global_settings else 100
        
        # Get all existing human bots to check total limit
        existing_bots = await db.human_bots.find({}).to_list(None)
        existing_bots_total = sum(bot.get("bet_limit", 12) for bot in existing_bots)
        
        # Calculate expected total limits for new bots (use average of range)
        expected_avg_bet_limit = (bulk_data.bet_limit_range[0] + bulk_data.bet_limit_range[1]) / 2
        expected_total_new_limits = expected_avg_bet_limit * bulk_data.count
        
        # Check if bulk creation would exceed global limit
        if existing_bots_total + expected_total_new_limits > global_max:
            available = global_max - existing_bots_total
            max_possible_bots = int(available / expected_avg_bet_limit)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bulk creation would exceed global limit. Available capacity: {available:.0f}, can create max {max_possible_bots} bots with these limits"
            )
        
        # Create bots
        created_bots = []
        failed_bots = []
        
        for i in range(bulk_data.count):
            try:
                # Generate unique name
                bot_name = await generate_unique_human_bot_name()
                
                # Generate random values within ranges
                min_bet = random.uniform(bulk_data.min_bet_range[0], bulk_data.min_bet_range[1])
                max_bet = random.uniform(bulk_data.max_bet_range[0], bulk_data.max_bet_range[1])
                
                # Ensure min_bet < max_bet
                if min_bet >= max_bet:
                    min_bet, max_bet = max_bet * 0.5, max_bet
                
                min_delay = random.randint(bulk_data.delay_range[0], bulk_data.delay_range[1] // 2)
                max_delay = random.randint(min_delay + 1, bulk_data.delay_range[1])
                
                # Generate bet_limit within range
                bet_limit = random.randint(bulk_data.bet_limit_range[0], bulk_data.bet_limit_range[1])
                
                # Create bot
                human_bot = HumanBot(
                    name=bot_name,
                    character=bulk_data.character,
                    min_bet=round(min_bet, 2),
                    max_bet=round(max_bet, 2),
                    bet_limit=bet_limit,
                    win_percentage=bulk_data.win_percentage,
                    loss_percentage=bulk_data.loss_percentage,
                    draw_percentage=bulk_data.draw_percentage,
                    min_delay=min_delay,
                    max_delay=max_delay,
                    use_commit_reveal=bulk_data.use_commit_reveal,
                    logging_level=bulk_data.logging_level
                )
                
                await db.human_bots.insert_one(human_bot.dict())
                created_bots.append({
                    "id": human_bot.id,
                    "name": human_bot.name,
                    "character": human_bot.character,
                    "bet_range": f"${human_bot.min_bet}-${human_bot.max_bet}"
                })
                
            except Exception as e:
                failed_bots.append({
                    "index": i,
                    "error": str(e)
                })
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_admin.id,
            action="BULK_CREATE_HUMAN_BOTS",
            target_type="human_bot",
            target_id="bulk",
            details={
                "character": bulk_data.character,
                "requested_count": bulk_data.count,
                "created_count": len(created_bots),
                "failed_count": len(failed_bots)
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        logger.info(f"Bulk created {len(created_bots)} human bots ({bulk_data.character})")
        
        return {
            "success": True,
            "message": f"Created {len(created_bots)} human bots",
            "created_count": len(created_bots),
            "failed_count": len(failed_bots),
            "created_bots": created_bots,
            "failed_bots": failed_bots
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk creating human bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create human bots"
        )

@api_router.post("/admin/human-bots/{bot_id}/toggle-status", response_model=dict)
async def toggle_human_bot_status(
    bot_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """Toggle human bot active status."""
    try:
        # Find bot
        bot_data = await db.human_bots.find_one({"id": bot_id})
        if not bot_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Human bot not found"
            )
        
        # Toggle status
        new_status = not bot_data["is_active"]
        
        await db.human_bots.update_one(
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
            admin_id=current_admin.id,
            action="TOGGLE_HUMAN_BOT_STATUS",
            target_type="human_bot",
            target_id=bot_id,
            details={
                "name": bot_data["name"],
                "new_status": "active" if new_status else "inactive"
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        logger.info(f"Human bot {bot_id} status changed to {'active' if new_status else 'inactive'}")
        
        return {
            "success": True,
            "message": f"Bot {'activated' if new_status else 'deactivated'} successfully",
            "new_status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling human bot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle human bot status"
        )

@api_router.get("/admin/human-bots/stats", response_model=HumanBotsStatsResponse)
async def get_human_bots_stats(current_admin: User = Depends(get_current_admin)):
    """Get human bots statistics."""
    try:
        # Basic counts
        total_bots = await db.human_bots.count_documents({})
        active_bots = await db.human_bots.count_documents({"is_active": True})
        
        # Get all human bot IDs
        bot_ids = []
        all_bots = await db.human_bots.find({}).to_list(None)
        bot_ids = [bot["id"] for bot in all_bots]
        
        # Count total bets (games) created by Human-bots
        total_bets = await db.games.count_documents({
            "creator_id": {"$in": bot_ids}
        })
        
        # Calculate character distribution
        character_distribution = {}
        total_games_24h = 0
        total_revenue_24h = 0.0
        
        # Calculate date for 24h ago
        day_ago = datetime.utcnow() - timedelta(days=1)
        
        for bot in all_bots:
            character = bot["character"]
            character_distribution[character] = character_distribution.get(character, 0) + 1
            
            # Count games in last 24h
            games_24h = await db.human_bot_logs.count_documents({
                "human_bot_id": bot["id"],
                "created_at": {"$gte": day_ago}
            })
            total_games_24h += games_24h
            
            # Calculate revenue (simplified for now)
            revenue_24h = bot.get("total_amount_won", 0) * 0.03  # Assume 3% commission
            total_revenue_24h += revenue_24h
        
        # Find most active bots
        most_active_bots = []
        for bot in all_bots[:5]:  # Top 5
            games_count = await db.human_bot_logs.count_documents({
                "human_bot_id": bot["id"],
                "created_at": {"$gte": day_ago}
            })
            
            most_active_bots.append({
                "id": bot["id"],
                "name": bot["name"],
                "character": bot["character"],
                "games_24h": games_count,
                "total_games": bot.get("total_games_played", 0)
            })
        
        # Sort by activity
        most_active_bots.sort(key=lambda x: x["games_24h"], reverse=True)
        
        return HumanBotsStatsResponse(
            total_bots=total_bots,
            active_bots=active_bots,
            total_games_24h=total_games_24h,
            total_bets=total_bets,
            total_revenue_24h=total_revenue_24h,
            avg_revenue_per_bot=total_revenue_24h / active_bots if active_bots > 0 else 0,
            most_active_bots=most_active_bots[:3],
            character_distribution=character_distribution
        )
        
    except Exception as e:
        logger.error(f"Error fetching human bots stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch human bots stats"
        )

@api_router.get("/admin/human-bots/settings")
async def get_human_bots_settings(current_admin: User = Depends(get_current_admin)):
    """Get human bots global settings."""
    try:
        # Get bot settings from database
        settings = await db.bot_settings.find_one({"id": "bot_settings"})
        
        if not settings:
            # Create default settings if not exists
            default_settings = {
                "id": "bot_settings",
                "max_active_bets_human": 100,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.bot_settings.insert_one(default_settings)
            settings = default_settings
        
        # Get current usage statistics
        all_bots = await db.human_bots.find({}).to_list(None)
        total_individual_limits = sum(bot.get("bet_limit", 12) for bot in all_bots)
        max_limit = settings.get("max_active_bets_human", 100)
        
        return JSONResponse(content={
            "success": True,
            "settings": {
                "max_active_bets_human": max_limit,
                "current_usage": {
                    "total_individual_limits": total_individual_limits,
                    "max_limit": max_limit,
                    "available": max_limit - total_individual_limits,
                    "usage_percentage": round((total_individual_limits / max_limit) * 100, 1) if max_limit > 0 else 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching human bots settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch human bots settings"
        )

@api_router.post("/admin/human-bots/update-settings", response_model=dict)
async def update_human_bots_settings(
    settings: HumanBotSettingsRequest,
    current_admin: User = Depends(get_current_admin)
):
    """Update human bots global settings with automatic proportional adjustment of individual limits."""
    try:
        # Get current bot settings
        current_settings = await db.bot_settings.find_one({"id": "bot_settings"})
        current_max = current_settings.get("max_active_bets_human", 100) if current_settings else 100
        new_max = settings.max_active_bets_human
        
        # Get all human bots
        all_bots = await db.human_bots.find({}).to_list(None)
        current_total_limits = sum(bot.get("bet_limit", 12) for bot in all_bots)
        
        # If new limit is lower than current total, need to adjust individual limits proportionally
        adjusted_bots = []
        if new_max < current_total_limits:
            # Calculate proportional adjustment factor
            adjustment_factor = new_max / current_total_limits
            
            # Adjust each bot's individual limit proportionally
            for bot in all_bots:
                old_limit = bot.get("bet_limit", 12)
                new_limit = max(1, round(old_limit * adjustment_factor))  # Ensure at least 1
                
                if new_limit != old_limit:
                    await db.human_bots.update_one(
                        {"id": bot["id"]},
                        {
                            "$set": {
                                "bet_limit": new_limit,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    adjusted_bots.append({
                        "bot_id": bot["id"],
                        "bot_name": bot["name"],
                        "old_limit": old_limit,
                        "new_limit": new_limit
                    })
        
        # Update global settings
        await db.bot_settings.update_one(
            {"id": "bot_settings"},
            {
                "$set": {
                    "max_active_bets_human": new_max,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_admin.id,
            action="UPDATE_HUMAN_BOTS_SETTINGS",
            target_type="settings",
            target_id="human_bots_settings",
            details={
                "old_max_limit": current_max,
                "new_max_limit": new_max,
                "adjusted_bots_count": len(adjusted_bots),
                "adjusted_bots": adjusted_bots[:10]  # Limit to first 10 for logs
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        response = {
            "success": True,
            "message": f"Human bots settings updated successfully",
            "old_max_limit": current_max,
            "new_max_limit": new_max
        }
        
        if adjusted_bots:
            response["adjusted_bots_count"] = len(adjusted_bots)
            response["message"] += f". {len(adjusted_bots)} bot limits were automatically adjusted proportionally."
            response["adjusted_bots"] = adjusted_bots
        
        return response
        
    except Exception as e:
        logger.error(f"Error updating human bots settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update human bots settings"
        )

@api_router.get("/admin/human-bots/{bot_id}/logs", response_model=dict)
async def get_human_bot_logs(
    bot_id: str,
    page: int = 1,
    limit: int = 20,
    action_type: Optional[str] = None,
    current_admin: User = Depends(get_current_admin)
):
    """Get logs for a specific human bot."""
    try:
        # Find bot
        bot = await db.human_bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(status_code=404, detail="Human bot not found")
        
        # Build query
        query = {"human_bot_id": bot_id}
        if action_type:
            query["action"] = action_type
        
        # Get total count
        total = await db.human_bot_logs.count_documents(query)
        
        # Get logs with pagination
        skip = (page - 1) * limit
        logs = await db.human_bot_logs.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log.get("id", ""),
                "action": log.get("action", ""),
                "details": log.get("details", {}),
                "created_at": log.get("created_at").isoformat() if log.get("created_at") else "",
            })
        
        return {
            "success": True,
            "logs": formatted_logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching human bot logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch human bot logs"
        )

@api_router.get("/admin/human-bots/{bot_id}/active-bets", response_model=dict)
async def get_human_bot_active_bets(
    bot_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """Get active bets for a specific Human-bot (only WAITING, ACTIVE, REVEAL statuses)."""
    try:
        # Find bot
        bot = await db.human_bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(status_code=404, detail="Human bot not found")
        
        # Get only active bets (WAITING, ACTIVE, REVEAL)
        active_statuses = ["WAITING", "ACTIVE", "REVEAL"]
        active_bets_cursor = db.games.find({
            "creator_id": bot_id,
            "status": {"$in": active_statuses}
        }).sort("created_at", -1)
        
        active_bets_list = await active_bets_cursor.to_list(None)
        
        # Calculate statistics
        total_active_bets = len(active_bets_list)
        total_bet_amount = sum(game.get('bet_amount', 0) for game in active_bets_list)
        
        # Get win/loss statistics from all completed games
        completed_games_cursor = db.games.find({
            "creator_id": bot_id,
            "status": "COMPLETED"
        })
        completed_games_list = await completed_games_cursor.to_list(None)
        
        bot_wins = sum(1 for game in completed_games_list if game.get('winner_id') == bot_id)
        player_wins = sum(1 for game in completed_games_list if game.get('winner_id') and game.get('winner_id') != bot_id)
        
        # Format active bets for display
        formatted_bets = []
        for game in active_bets_list:
            # Get opponent info
            opponent_id = game.get('opponent_id', '')
            opponent_name = '—'
            if opponent_id:
                opponent = await db.users.find_one({"id": opponent_id})
                if opponent:
                    opponent_name = opponent.get('username', opponent.get('email', opponent_id))
            
            formatted_bets.append({
                "id": game.get("id", ""),
                "created_at": game.get("created_at").isoformat() if game.get("created_at") else "",
                "bet_amount": game.get("bet_amount", 0),
                "total_bet_amount": game.get("bet_amount", 0),
                "creator_gem": game.get("creator_gem", ""),
                "selected_gem": game.get("creator_gem", ""),
                "status": game.get("status", ""),
                "opponent_id": opponent_id,
                "opponent_name": opponent_name,
                "winner_id": game.get("winner_id", ""),
                "result": game.get("result", "")
            })
        
        return {
            "success": True,
            "bot_id": bot_id,
            "bot_name": bot.get("name", ""),
            "activeBets": total_active_bets,
            "totalBets": total_active_bets,  # For active-only view
            "totalBetAmount": total_bet_amount,
            "botWins": bot_wins,
            "playerWins": player_wins,
            "bets": formatted_bets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching human bot active bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch human bot active bets"
        )

@api_router.get("/admin/human-bots/{bot_id}/all-bets", response_model=dict)
async def get_human_bot_all_bets(
    bot_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """Get all bets for a specific Human-bot (active + completed + cancelled + archived)."""
    try:
        # Find bot
        bot = await db.human_bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(status_code=404, detail="Human bot not found")
        
        # Get all bets
        all_bets_cursor = db.games.find({
            "creator_id": bot_id
        }).sort("created_at", -1)
        
        all_bets_list = await all_bets_cursor.to_list(None)
        
        # Separate active and completed bets
        active_statuses = ["WAITING", "ACTIVE", "REVEAL"]
        active_bets = [game for game in all_bets_list if game.get('status') in active_statuses]
        completed_bets = [game for game in all_bets_list if game.get('status') not in active_statuses]
        
        # Calculate statistics
        total_active_bets = len(active_bets)
        total_all_bets = len(all_bets_list)
        total_bet_amount = sum(game.get('bet_amount', 0) for game in all_bets_list)
        
        # Calculate win/loss statistics from completed games
        completed_games = [game for game in all_bets_list if game.get('status') == 'COMPLETED']
        bot_wins = sum(1 for game in completed_games if game.get('winner_id') == bot_id)
        player_wins = sum(1 for game in completed_games if game.get('winner_id') and game.get('winner_id') != bot_id)
        
        # Format all bets for display
        formatted_bets = []
        for game in all_bets_list:
            # Get opponent info
            opponent_id = game.get('opponent_id', '')
            opponent_name = '—'
            if opponent_id:
                opponent = await db.users.find_one({"id": opponent_id})
                if opponent:
                    opponent_name = opponent.get('username', opponent.get('email', opponent_id))
            
            formatted_bets.append({
                "id": game.get("id", ""),
                "created_at": game.get("created_at").isoformat() if game.get("created_at") else "",
                "bet_amount": game.get("bet_amount", 0),
                "total_bet_amount": game.get("bet_amount", 0),
                "creator_gem": game.get("creator_gem", ""),
                "selected_gem": game.get("creator_gem", ""),
                "status": game.get("status", ""),
                "opponent_id": opponent_id,
                "opponent_name": opponent_name,
                "winner_id": game.get("winner_id", ""),
                "result": game.get("result", "")
            })
        
        return {
            "success": True,
            "bot_id": bot_id,
            "bot_name": bot.get("name", ""),
            "activeBets": total_active_bets,
            "totalBets": total_all_bets,  # All bets including completed
            "totalBetAmount": total_bet_amount,
            "botWins": bot_wins,
            "playerWins": player_wins,
            "completedBetsCount": len(completed_bets),
            "bets": formatted_bets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching human bot all bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch human bot all bets"
        )

@api_router.post("/admin/human-bots/{bot_id}/clear-completed-bets", response_model=dict)
async def clear_human_bot_completed_bets(
    bot_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """Clear completed bets for a specific Human-bot by changing status to ARCHIVED."""
    try:
        # Find bot
        bot = await db.human_bots.find_one({"id": bot_id})
        if not bot:
            raise HTTPException(status_code=404, detail="Human bot not found")
        
        # Get completed and cancelled bets
        clearable_statuses = ["COMPLETED", "CANCELLED"]
        clearable_bets_cursor = db.games.find({
            "creator_id": bot_id,
            "status": {"$in": clearable_statuses}
        })
        
        clearable_bets_list = await clearable_bets_cursor.to_list(None)
        cleared_count = len(clearable_bets_list)
        
        if cleared_count > 0:
            # Update status to ARCHIVED instead of deleting
            result = await db.games.update_many(
                {
                    "creator_id": bot_id,
                    "status": {"$in": clearable_statuses}
                },
                {
                    "$set": {
                        "status": "ARCHIVED",
                        "archived_at": datetime.utcnow(),
                        "archived_by": current_admin.id
                    }
                }
            )
            
            # Log admin action
            admin_log = AdminLog(
                admin_id=current_admin.id,
                action="CLEAR_HUMAN_BOT_COMPLETED_BETS",
                target_type="human_bot",
                target_id=bot_id,
                details={
                    "bot_name": bot.get("name", ""),
                    "cleared_count": cleared_count,
                    "modified_count": result.modified_count
                }
            )
            await db.admin_logs.insert_one(admin_log.dict())
            
            logger.info(f"Cleared {cleared_count} completed bets for Human-bot {bot_id}")
        
        return {
            "success": True,
            "message": f"Cleared {cleared_count} completed bets",
            "cleared_count": cleared_count,
            "bot_id": bot_id,
            "bot_name": bot.get("name", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing human bot completed bets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear human bot completed bets"
        )

@api_router.post("/admin/human-bots/toggle-all", response_model=dict)
async def toggle_all_human_bots(
    request: ToggleAllRequest,
    current_admin: User = Depends(get_current_admin)
):
    """Toggle all human bots active status."""
    try:
        # Update all bots
        result = await db.human_bots.update_many(
            {},
            {
                "$set": {
                    "is_active": request.activate,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log admin action
        admin_log = AdminLog(
            admin_id=current_admin.id,
            action="TOGGLE_ALL_HUMAN_BOTS",
            target_type="human_bot",
            target_id="all",
            details={
                "action": "activate" if request.activate else "deactivate",
                "affected_count": result.modified_count
            }
        )
        await db.admin_logs.insert_one(admin_log.dict())
        
        logger.info(f"All human bots {'activated' if request.activate else 'deactivated'}: {result.modified_count} bots")
        
        return {
            "success": True,
            "message": f"All human bots {'activated' if request.activate else 'deactivated'} successfully",
            "affected_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error toggling all human bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle all human bots"
        )



# ==============================================================================
# INCLUDE ROUTERS
# ==============================================================================

# Include routers in the main app
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