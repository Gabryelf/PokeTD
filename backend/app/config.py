import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Базовые настройки
    PROJECT_NAME: str = "PokeTD"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Настройки базы данных
    DATABASE_URL: Optional[str] = None

    # JWT настройки
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_database_url() -> str:
    """
    Возвращает URL для подключения к базе данных.
    Приоритет:
    1. Переменная окружения DATABASE_URL
    2. PostgreSQL на Render
    3. SQLite локально
    """
    settings = Settings()

    # Если указана переменная окружения - используем ее
    if settings.DATABASE_URL:
        # Исправляем URL для PostgreSQL если нужно
        if settings.DATABASE_URL.startswith("postgres://"):
            settings.DATABASE_URL = settings.DATABASE_URL.replace(
                "postgres://", "postgresql://", 1
            )
        return settings.DATABASE_URL

    # Проверяем, находимся ли на Render
    is_render = os.getenv("RENDER") is not None

    if is_render:
        # На Render используем PostgreSQL
        # Создаем базу в Render и добавьте DATABASE_URL в переменные окружения
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL не установлена для среды Render")

        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return db_url
    else:
        # Локально используем SQLite
        return "sqlite:///./game.db4"


# Создаем глобальный объект настроек
settings = Settings()
DATABASE_URL = get_database_url()
