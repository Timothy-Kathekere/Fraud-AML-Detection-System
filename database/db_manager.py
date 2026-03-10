"""
Database manager for connection pooling and session management.
"""
import logging
from typing import Optional, List, Any
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config.settings import settings
from database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        """Initialize database manager."""
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        self._initialize_db()
    
    def _create_engine(self):
        """Create database engine with connection pooling."""
        engine = create_engine(
            settings.database.url,
            poolclass=QueuePool,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.database.echo,
            connect_args={'timeout': 30}
        )
        
        # Log SQL if debug enabled
        if settings.is_development:
            @event.listens_for(engine, "before_cursor_execute")
            def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                logger.debug(f"EXECUTE: {statement}")
        
        logger.info("Database engine created")
        return engine
    
    def _initialize_db(self):
        """Initialize database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: dict = None) -> List[Any]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results
        """
        session = self.get_session()
        try:
            result = session.execute(query, params or {})
            return result.fetchall()
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close database connection pool."""
        self.engine.dispose()
        logger.info("Database connections closed")
    
    def get_stats(self) -> dict:
        """Get database connection pool statistics."""
        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in_connections': pool.checkedin(),
            'checked_out_connections': pool.checkedout(),
        }