"""
Initialize database schema and tables.
"""
import logging
from database.models import Base # type: ignore
from database.db_manager import DatabaseManager # type: ignore
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Initializing database...")
    
    db_manager = DatabaseManager()
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


if __name__ == "__main__":
    main()