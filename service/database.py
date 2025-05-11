from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session as SQLAlchemySession
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.engine import Engine
from contextlib import contextmanager
import logging
from config import DATABASE_URL
from typing import Generator, Optional

from server.service.base import BaseService

logger = logging.getLogger(__name__)

_current_engine: Optional[Engine] = None
_current_session_local: Optional[sessionmaker[SQLAlchemySession]] = None

Base: DeclarativeMeta = declarative_base()

def get_db() -> Generator[SQLAlchemySession, None, None]:
    """Gets a database session. Relies on DatabaseService being started."""
    if _current_session_local is None:
        raise RuntimeError("DatabaseService has not been started or SessionLocal is not initialized.")
    db = _current_session_local()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[SQLAlchemySession, None, None]:
    """Database session context manager. Relies on DatabaseService being started."""
    if _current_session_local is None:
        raise RuntimeError("DatabaseService has not been started or SessionLocal is not initialized.")
    db = _current_session_local()
    try:
        yield db
    finally:
        db.close()

def _initialize_database_tables():
    """Internal function to initialize database tables."""
    if _current_engine is None:
        raise RuntimeError("Database engine not initialized. Call DatabaseService.start() first.")
    import models.session 
    Base.metadata.create_all(bind=_current_engine)

class DatabaseService(BaseService):
    """Manages database connection, initialization, and session factory."""
    def __init__(self):
        super().__init__()

    async def start(self) -> None:
        """Starts the database service: creates engine, session factory, and initializes tables."""
        global _current_engine, _current_session_local
        try:
            if _current_engine is not None or _current_session_local is not None:
                pass
            
            engine_instance = create_engine(
                DATABASE_URL, connect_args={"check_same_thread": False}
            )
            _current_engine = engine_instance

            _current_session_local = sessionmaker(autocommit=False, autoflush=False, bind=_current_engine)
            
            _initialize_database_tables()
        except Exception as e:
            _current_engine = None
            _current_session_local = None
            raise

    async def release(self) -> None:
        """Releases resources held by the database service."""
        global _current_engine, _current_session_local
        if _current_engine is not None:
            try:
                _current_engine.dispose()
            except Exception as e:
                pass
        
        _current_engine = None
        _current_session_local = None 