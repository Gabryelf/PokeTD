from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from . import models, schemas
from .auth import get_password_hash


# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    # Проверяем, существует ли пользователь
    existing_user = get_user_by_username(db, username=user.username)
    if existing_user:
        return None

    existing_email = get_user_by_email(db, email=user.email)
    if existing_email:
        return None

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        poke_coins=100  # Начальные монеты при регистрации
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Создаем запись в лидерборде для нового пользователя
    leaderboard_entry = models.Leaderboard(
        user_id=db_user.id,
        username=db_user.username
    )
    db.add(leaderboard_entry)
    db.commit()

    return db_user


# Game Session CRUD
def create_game_session(db: Session, session_data: schemas.GameResult, user_id: int):
    db_session = models.GameSession(
        user_id=user_id,
        score=session_data.score,
        poke_coins_earned=session_data.poke_coins_earned,
        waves_completed=session_data.waves_completed,
        pokemons_caught=session_data.pokemons_caught,
        enemies_defeated=session_data.enemies_defeated,
        game_duration=session_data.game_duration,
        victory=session_data.victory
    )
    db.add(db_session)

    # Обновляем баланс пользователя
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.poke_coins += session_data.poke_coins_earned

    db.commit()
    db.refresh(db_session)

    # Обновляем лидерборд
    leaderboard = db.query(models.Leaderboard).filter(models.Leaderboard.user_id == user_id).first()
    if leaderboard:
        if session_data.score > leaderboard.high_score:
            leaderboard.high_score = session_data.score
        leaderboard.total_waves += session_data.waves_completed
        leaderboard.total_pokemons += session_data.pokemons_caught
        leaderboard.total_enemies += session_data.enemies_defeated
        db.commit()

    return db_session


def get_user_game_sessions(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.GameSession) \
        .filter(models.GameSession.user_id == user_id) \
        .order_by(desc(models.GameSession.created_at)) \
        .offset(skip) \
        .limit(limit) \
        .all()


# Leaderboard CRUD
def get_leaderboard(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Leaderboard) \
        .order_by(desc(models.Leaderboard.high_score)) \
        .offset(skip) \
        .limit(limit) \
        .all()


def get_user_stats(db: Session, user_id: int):
    user_stats = db.query(models.Leaderboard).filter(models.Leaderboard.user_id == user_id).first()

    # Получаем последние игры пользователя
    recent_games = db.query(models.GameSession) \
        .filter(models.GameSession.user_id == user_id) \
        .order_by(desc(models.GameSession.created_at)) \
        .limit(10) \
        .all()

    # Получаем пользователя для монет
    user = db.query(models.User).filter(models.User.id == user_id).first()

    return {
        "leaderboard": user_stats,
        "recent_games": recent_games,
        "poke_coins": user.poke_coins if user else 0
    }


# Pokemon CRUD
def add_pokemon_to_user(db: Session, user_id: int, pokemon_data: schemas.PokemonCreate):
    db_pokemon = models.UserPokemon(
        user_id=user_id,
        pokemon_id=pokemon_data.pokemon_id,
        name=pokemon_data.name,
        element=pokemon_data.element,
        base_health=pokemon_data.base_health,
        base_attack=pokemon_data.base_attack,
        level=pokemon_data.level if hasattr(pokemon_data, 'level') else 1,
        experience=pokemon_data.experience if hasattr(pokemon_data, 'experience') else 0,
        is_favorite=False
    )
    db.add(db_pokemon)
    db.commit()
    db.refresh(db_pokemon)
    return db_pokemon


def get_user_pokemons(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.UserPokemon) \
        .filter(models.UserPokemon.user_id == user_id) \
        .order_by(desc(models.UserPokemon.level), desc(models.UserPokemon.experience)) \
        .offset(skip) \
        .limit(limit) \
        .all()


def update_pokemon_favorite(db: Session, pokemon_id: int, user_id: int, is_favorite: bool):
    pokemon = db.query(models.UserPokemon) \
        .filter(models.UserPokemon.id == pokemon_id, models.UserPokemon.user_id == user_id) \
        .first()

    if pokemon:
        pokemon.is_favorite = is_favorite
        db.commit()
        db.refresh(pokemon)

    return pokemon


def update_user_coins(db: Session, user_id: int, coins_change: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.poke_coins += coins_change
        # Гарантируем, что монеты не уйдут в минус
        if user.poke_coins < 0:
            user.poke_coins = 0
        db.commit()
        db.refresh(user)
    return user
