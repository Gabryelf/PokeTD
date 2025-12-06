"""
Простая утилита для миграций.
Для продакшена рекомендуется использовать Alembic.
"""
from database import Base, engine
from models import User, GameSession, UserPokemon, Leaderboard
import sqlalchemy as sa


def check_and_update_tables():
    """
    Проверяет существование таблиц и обновляет их при необходимости.
    """
    inspector = sa.inspect(engine)
    existing_tables = inspector.get_table_names()

    required_tables = [
        User.__tablename__,
        GameSession.__tablename__,
        UserPokemon.__tablename__,
        Leaderboard.__tablename__
    ]

    print("Checking database tables...")

    for table in required_tables:
        if table not in existing_tables:
            print(f"  Creating missing table: {table}")

    # Создаем отсутствующие таблицы
    Base.metadata.create_all(bind=engine)

    print("✓ Database is up to date")


if __name__ == "__main__":
    check_and_update_tables()