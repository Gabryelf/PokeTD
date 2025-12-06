from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    # Для PostgreSQL важно указывать длины строк
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    poke_coins = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Ограничения для PostgreSQL
    __table_args__ = (
        CheckConstraint('poke_coins >= 0', name='check_poke_coins_positive'),
        CheckConstraint('LENGTH(username) >= 3', name='check_username_length'),
        CheckConstraint('email ~* \'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$\'', name='check_email_format'),
    )

    # Связи
    game_sessions = relationship("GameSession", back_populates="user", cascade="all, delete-orphan")
    owned_pokemons = relationship("UserPokemon", back_populates="user", cascade="all, delete-orphan")


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, default=0, nullable=False)
    poke_coins_earned = Column(Integer, default=0, nullable=False)
    waves_completed = Column(Integer, default=0, nullable=False)
    pokemons_caught = Column(Integer, default=0, nullable=False)
    enemies_defeated = Column(Integer, default=0, nullable=False)
    game_duration = Column(Float, default=0.0, nullable=False)
    victory = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Ограничения для PostgreSQL
    __table_args__ = (
        CheckConstraint('score >= 0', name='check_score_positive'),
        CheckConstraint('poke_coins_earned >= 0', name='check_coins_earned_positive'),
        CheckConstraint('waves_completed >= 0', name='check_waves_positive'),
        CheckConstraint('pokemons_caught >= 0', name='check_pokemons_positive'),
        CheckConstraint('enemies_defeated >= 0', name='check_enemies_positive'),
        CheckConstraint('game_duration >= 0', name='check_duration_positive'),
        Index('idx_game_sessions_user_created', 'user_id', 'created_at'),
        Index('idx_game_sessions_score', 'score'),
    )

    # Связи
    user = relationship("User", back_populates="game_sessions")


class UserPokemon(Base):
    __tablename__ = "user_pokemons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pokemon_id = Column(Integer, nullable=False)
    name = Column(String(50), nullable=False)
    element = Column(String(20), nullable=False)
    base_health = Column(Integer, nullable=False)
    base_attack = Column(Integer, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    experience = Column(Integer, default=0, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    caught_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Ограничения для PostgreSQL
    __table_args__ = (
        CheckConstraint('base_health > 0', name='check_health_positive'),
        CheckConstraint('base_attack > 0', name='check_attack_positive'),
        CheckConstraint('level >= 1', name='check_level_min'),
        CheckConstraint('experience >= 0', name='check_exp_positive'),
        CheckConstraint('pokemon_id > 0', name='check_pokemon_id_positive'),
        CheckConstraint(
            'element IN (\'fire\', \'water\', \'grass\', \'electric\', \'ice\', \'fighting\', \'poison\', \'ground\', \'flying\', \'psychic\', \'bug\', \'rock\', \'ghost\', \'dark\', \'dragon\', \'steel\', \'fairy\', \'normal\')',
            name='check_valid_element'),
        Index('idx_user_pokemons_user', 'user_id'),
        Index('idx_user_pokemons_element', 'element'),
        Index('idx_user_pokemons_level', 'level'),
    )

    # Связи
    user = relationship("User", back_populates="owned_pokemons")


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    username = Column(String(50), nullable=False)
    high_score = Column(Integer, default=0, nullable=False)
    total_waves = Column(Integer, default=0, nullable=False)
    total_pokemons = Column(Integer, default=0, nullable=False)
    total_enemies = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Ограничения для PostgreSQL
    __table_args__ = (
        CheckConstraint('high_score >= 0', name='check_high_score_positive'),
        CheckConstraint('total_waves >= 0', name='check_total_waves_positive'),
        CheckConstraint('total_pokemons >= 0', name='check_total_pokemons_positive'),
        CheckConstraint('total_enemies >= 0', name='check_total_enemies_positive'),
        Index('idx_leaderboard_high_score', 'high_score', unique=False),
        Index('idx_leaderboard_total_waves', 'total_waves', unique=False),
    )

    # Связи
    user = relationship("User", foreign_keys=[user_id])
