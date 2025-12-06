from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# User schemas
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

    @validator('password')
    def validate_password(cls, v):
        byte_length = len(v.encode('utf-8'))
        if byte_length > 72:
            truncated = v.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            return truncated
        return v

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters long')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers and underscores')
        return v

    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    poke_coins: int = 100
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Game schemas
class PokemonData(BaseModel):
    id: int
    name: str
    element: str
    health: int = Field(..., ge=1)
    attack: int = Field(..., ge=1)
    sprite_url: str


class GameState(BaseModel):
    player_health: int = Field(..., ge=0)
    player_level: int = Field(..., ge=1)
    player_exp: int = Field(..., ge=0)
    player_max_exp: int = Field(..., ge=1)
    pokeballs: int = Field(..., ge=0)
    poke_coins: int = Field(..., ge=0)
    hand: List[PokemonData]
    field: List[Dict[str, Any]]
    enemies: List[Dict[str, Any]]
    wave: int = Field(..., ge=1)
    score: int = Field(..., ge=0)


class GameAction(BaseModel):
    action_type: str
    data: Optional[Dict[str, Any]] = None

    @validator('action_type')
    def validate_action_type(cls, v):
        valid_actions = ["open_pokeball", "play_card", "end_turn", "upgrade_card",
                         "sell_card", "reroll_shop", "buy_pokeball", "use_item"]
        if v not in valid_actions:
            raise ValueError(f'Invalid action type. Must be one of: {valid_actions}')
        return v


class GameResult(BaseModel):
    victory: bool
    score: int = Field(..., ge=0)
    poke_coins_earned: int = Field(..., ge=0)
    waves_completed: int = Field(..., ge=0)
    pokemons_caught: int = Field(..., ge=0)
    enemies_defeated: int = Field(..., ge=0)
    game_duration: float = Field(..., ge=0.0)

    @validator('poke_coins_earned')
    def validate_coins(cls, v, values):
        if v < 0:
            raise ValueError('Poke coins earned cannot be negative')
        if values.get('victory', False) and v < 50:
            return 50
        return v


# Leaderboard schemas
class LeaderboardEntry(BaseModel):
    username: str
    high_score: int = Field(..., ge=0)
    total_waves: int = Field(..., ge=0)
    rank: Optional[int] = Field(None, ge=1)

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    user_rank: Optional[int] = None
    total_pages: int = 1
    current_page: int = 1


# Pokemon schemas для коллекции
class PokemonBase(BaseModel):
    pokemon_id: int = Field(..., ge=1)
    name: str
    element: str
    base_health: int = Field(..., ge=1)
    base_attack: int = Field(..., ge=1)


class PokemonCreate(PokemonBase):  # ← ЭТОТ КЛАСС БЫЛ ОТСУТСТВОВАЛ
    level: int = Field(1, ge=1)
    experience: int = Field(0, ge=0)


class PokemonResponse(PokemonBase):
    id: int
    user_id: int
    level: int
    experience: int
    is_favorite: bool
    caught_at: datetime

    class Config:
        from_attributes = True


# Shop schemas
class ShopItem(BaseModel):
    id: int
    name: str
    description: str
    price: int = Field(..., ge=0)
    item_type: str
    rarity: Optional[str] = 'common'

    class Config:
        from_attributes = True


class PurchaseRequest(BaseModel):
    item_id: int
    quantity: int = Field(1, ge=1, le=10)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v > 10:
            raise ValueError('Cannot purchase more than 10 items at once')
        return v


# Stats schemas
class UserStats(BaseModel):
    total_games: int = Field(0, ge=0)
    wins: int = Field(0, ge=0)
    losses: int = Field(0, ge=0)
    total_score: int = Field(0, ge=0)
    total_coins_earned: int = Field(0, ge=0)
    total_pokemons_caught: int = Field(0, ge=0)
    total_enemies_defeated: int = Field(0, ge=0)
    average_score: float = Field(0.0, ge=0.0)
    win_rate: float = Field(0.0, ge=0.0, le=100.0)

    class Config:
        from_attributes = True


class Achievement(BaseModel):
    id: int
    name: str
    description: str
    achieved: bool
    achieved_at: Optional[datetime]
    progress: Optional[float] = 0.0

    class Config:
        from_attributes = True


# Алиасы для обратной совместимости
User = UserResponse  # Алиас для обратной совместимости
UserPokemonCreate = PokemonCreate  # Алиас для crud.py