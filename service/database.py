from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session as SQLAlchemySession
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.engine import Engine
from contextlib import contextmanager
import logging
# import os # os was imported but not used
# from pathlib import Path # Path was imported but not used
from config import DATABASE_URL
from typing import Generator, Optional

from server.service.base import BaseService # Import BaseService

logger = logging.getLogger(__name__)

# --- Module-level variables to hold the initialized engine and session factory ---
_current_engine: Optional[Engine] = None
_current_session_local: Optional[sessionmaker[SQLAlchemySession]] = None

# 数据库基类
Base: DeclarativeMeta = declarative_base()

# 创建数据库引擎
# Ensure DATABASE_URL is correctly configured, e.g., "sqlite:///./sql_app.db" for a local SQLite file
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread is for SQLite
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[SQLAlchemySession, None, None]:
    """
    获取数据库会话的生成器函数.
    依赖于 DatabaseService 已经启动并初始化了 _current_session_local.
    """
    if _current_session_local is None:
        raise RuntimeError("DatabaseService has not been started or SessionLocal is not initialized.")
    db = _current_session_local()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[SQLAlchemySession, None, None]:
    """
    数据库会话上下文管理器.
    依赖于 DatabaseService 已经启动并初始化了 _current_session_local.
    """
    if _current_session_local is None:
        raise RuntimeError("DatabaseService has not been started or SessionLocal is not initialized.")
    db = _current_session_local()
    try:
        yield db
    finally:
        db.close()

def _initialize_database_tables(engine_to_use: Engine):
    """内部函数: 初始化数据库, 创建所有表."""
    # Import all modules here that define models inheriting from Base
    # so that Base.metadata.create_all(bind=engine) knows about them.
    # Example: 
    import models.session # This will make ApiKey and Session (which inherit Base) known to Base.metadata
    logger.info(f"Initializing database tables using engine: {engine_to_use}")
    Base.metadata.create_all(bind=engine_to_use)
    logger.info("Database tables initialized.")

class DatabaseService(BaseService):
    """
    服务类，用于管理数据库的连接、初始化和会话工厂。
    """
    def __init__(self):
        super().__init__()
        logger.info("DatabaseService instance created. Engine and SessionLocal will be initialized on start.")

    async def start(self) -> None:
        """
        启动数据库服务：创建引擎，会话工厂，并初始化表结构。
        """
        global _current_engine, _current_session_local
        logger.info("DatabaseService starting...")
        try:
            if _current_engine is not None or _current_session_local is not None:
                logger.warning("DatabaseService already started or not properly released. Re-initializing.")
            
            logger.info(f"Creating database engine with URL: {DATABASE_URL}")
            engine = create_engine(
                DATABASE_URL, connect_args={"check_same_thread": False} # For SQLite
            )
            _current_engine = engine

            logger.info("Creating database session factory (SessionLocal).")
            _current_session_local = sessionmaker(autocommit=False, autoflush=False, bind=_current_engine)
            
            _initialize_database_tables(_current_engine) 
            logger.info("DatabaseService started successfully. Engine and SessionLocal are now available.")
        except Exception as e:
            logger.error(f"DatabaseService failed to start: {e}", exc_info=True)
            _current_engine = None # Ensure reset on failure
            _current_session_local = None
            raise

    async def release(self) -> None:
        """
        释放数据库服务持有的资源。
        """
        global _current_engine, _current_session_local
        logger.info("DatabaseService releasing...")
        if _current_engine is not None:
            try:
                # For some database engines (like async ones), dispose might be async
                # For standard SQLAlchemy, dispose is synchronous.
                logger.info(f"Disposing database engine: {_current_engine}")
                _current_engine.dispose()
                logger.info("Database engine disposed.")
            except Exception as e:
                logger.error(f"Error disposing database engine: {e}", exc_info=True)
        else:
            logger.info("No active database engine to dispose.")
        
        _current_engine = None
        _current_session_local = None
        logger.info("DatabaseService released. Engine and SessionLocal have been reset.") 