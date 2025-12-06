from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .config import DATABASE_URL

# Определяем параметры подключения в зависимости от типа БД
if DATABASE_URL.startswith("sqlite"):
    # Для SQLite
    connect_args = {"check_same_thread": False}
    # SQLite не поддерживает пул соединений
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        echo=False  # Установите True для отладки SQL запросов
    )
    print(f"✓ Using SQLite database: {DATABASE_URL}")
else:
    # Для PostgreSQL
    # Используем пул соединений для лучшей производительности
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,  # Максимальное количество соединений в пуле
        max_overflow=20,  # Максимальное количество соединений сверх pool_size
        pool_pre_ping=True,  # Проверка соединения перед использованием
        echo=False  # Установите True для отладки SQL запросов
    )
    print(f"✓ Using PostgreSQL database with connection pool")

# Сессия БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency для получения сессии БД.
    Гарантирует закрытие сессии после использования.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
