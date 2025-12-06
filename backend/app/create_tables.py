from database import Base, engine
from models import User, GameSession, UserPokemon, Leaderboard
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """
    Создает все таблицы в базе данных.
    Для PostgreSQL добавляет расширения если нужно.
    """
    try:
        # Проверяем тип базы данных
        db_url = str(engine.url)

        if 'postgresql' in db_url:
            logger.info("Creating tables for PostgreSQL database...")
            # Для PostgreSQL можно добавить расширения
            with engine.connect() as conn:
                # Создаем расширение для UUID если нужно
                # conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
                pass
        else:
            logger.info("Creating tables for SQLite database...")

        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)

        logger.info("✓ Tables created successfully!")
        logger.info(f"  - {User.__tablename__}")
        logger.info(f"  - {GameSession.__tablename__}")
        logger.info(f"  - {UserPokemon.__tablename__}")
        logger.info(f"  - {Leaderboard.__tablename__}")

    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        raise


def drop_db():
    """
    Удаляет все таблицы (для тестирования).
    """
    logger.warning("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✓ All tables dropped")


if __name__ == "__main__":
    init_db()