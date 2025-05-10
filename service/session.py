from sqlalchemy.orm import Session as DbSession
from sqlalchemy import desc
from datetime import datetime
from typing import Optional, List # Removed Tuple as it was unused
import logging
import asyncio # Added for async sleep in start/release

from models.session import ApiKey, Session
from service.database import get_db_context # Updated import
from server.service.base import BaseService # Import BaseService

logger = logging.getLogger(__name__)

class SessionService(BaseService):
    """会话管理服务，遵循BaseService接口"""
    
    def __init__(self):
        """
        Initializes the SessionService.
        """
        super().__init__() # Call BaseService constructor if it has one
        self._running = False
        logger.info("SessionService instance created.")
    
    async def start(self) -> None:
        """Starts the session service."""
        if self._running:
            logger.warning("SessionService is already running.")
            return
        
        logger.info("Starting SessionService...")
        # Simulate any async startup tasks if needed, e.g., loading configs, etc.
        # For now, it's mainly a placeholder for lifecycle management.
        await asyncio.sleep(0.01) # Small sleep to make it async
        self._running = True
        logger.info("SessionService started successfully.")

    async def release(self) -> None:
        """Releases any resources held by the session service."""
        if not self._running:
            logger.warning("SessionService is not running or already released.")
            return

        logger.info("Releasing SessionService...")
        self._running = False
        # Simulate any async cleanup tasks if needed
        await asyncio.sleep(0.01) # Small sleep to make it async
        logger.info("SessionService released successfully.")

    def get_or_create_api_key(self, key: str) -> ApiKey:
        """
        获取或创建API密钥
        
        Args:
            key: API密钥字符串
            
        Returns:
            ApiKey对象
        """
        if not self._running:
            logger.error("SessionService is not running. Cannot perform get_or_create_api_key.")
            # Or raise an exception, or return a specific error object
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db: # Acquire session here
            api_key = db.query(ApiKey).filter(ApiKey.key == key).first()
            
            if not api_key:
                logger.info(f"创建新的API密钥: {key[:4]}...") # Log partial key for security
                api_key = ApiKey(key=key, created_at=datetime.utcnow(), last_used_at=datetime.utcnow())
                db.add(api_key)
                db.commit()
                db.refresh(api_key)
            else:
                # 更新最后使用时间
                api_key.last_used_at = datetime.utcnow()
                db.commit()
            
            return api_key # Make sure to return within the context or after fetching necessary data
    
    def create_session(self, api_key_str: str, session_id: str) -> Session:
        """
        创建新会话并关联到API密钥
        
        Args:
            api_key_str: API密钥字符串
            session_id: 会话ID
            
        Returns:
            新创建的Session对象
        """
        if not self._running:
            logger.error("SessionService is not running. Cannot perform create_session.")
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            api_key_obj = self._get_or_create_api_key_internal(db, api_key_str) # Use internal helper
            
            # 检查是否已存在相同session_id的会话
            existing_session = db.query(Session).filter(Session.session_id == session_id).first()
            if existing_session:
                logger.warning(f"会话ID已存在: {session_id}, 更新关联的API密钥为 {api_key_obj.key[:4]}...")
                existing_session.api_key_id = api_key_obj.id
                existing_session.last_accessed = datetime.utcnow()
                db.commit()
                db.refresh(existing_session)
                return existing_session
            
            # 检查此API密钥关联的会话数量
            session_count = db.query(Session).filter(Session.api_key_id == api_key_obj.id).count()
            
            # 如果会话数量超过限制 (e.g., 5)，删除最旧的会话
            MAX_SESSIONS_PER_KEY = 5 
            if session_count >= MAX_SESSIONS_PER_KEY:
                oldest_session = (
                    db.query(Session)
                    .filter(Session.api_key_id == api_key_obj.id)
                    .order_by(Session.last_accessed.asc()) # Corrected to asc() for oldest
                    .first()
                )
                if oldest_session:
                    logger.info(f"API密钥 {api_key_obj.key[:4]}... 的会话数量超过限制，删除最旧的会话: {oldest_session.session_id}")
                    db.delete(oldest_session)
                    db.commit() # Commit after deletion
            
            # 创建新会话
            logger.info(f"为API密钥 {api_key_obj.key[:4]}... 创建新会话: {session_id}")
            new_session = Session(
                session_id=session_id,
                api_key_id=api_key_obj.id,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow()
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            return new_session
    
    # Internal helper to be used by methods that already have a db session
    def _get_or_create_api_key_internal(self, db: DbSession, key: str) -> ApiKey:
        api_key = db.query(ApiKey).filter(ApiKey.key == key).first()
        if not api_key:
            logger.info(f"(Internal) 创建新的API密钥: {key[:4]}...")
            api_key = ApiKey(key=key, created_at=datetime.utcnow(), last_used_at=datetime.utcnow())
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
        else:
            # 更新最后使用时间
            api_key.last_used_at = datetime.utcnow()
            db.commit()
        return api_key
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """
        根据会话ID获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Session对象，如果不存在则返回None
        """
        if not self._running:
            logger.error("SessionService is not running. Cannot perform get_session_by_id.")
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            if session:
                # Optionally update last_accessed time if a session is fetched
                # session.last_accessed = datetime.utcnow()
                # db.commit()
                pass # Decide if fetching should update last_accessed
            return session
    
    def get_api_key_by_session_id(self, session_id: str) -> Optional[str]:
        """
        根据会话ID获取API密钥的字符串值，并更新访问时间。
        
        Args:
            session_id: 会话ID
            
        Returns:
            API密钥字符串，如果不存在则返回None
        """
        if not self._running:
            logger.error("SessionService is not running. Cannot perform get_api_key_by_session_id.")
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            session = db.query(Session).join(ApiKey).filter(Session.session_id == session_id).first()
            
            if not session or not session.api_key:
                return None
            
            # 更新最后访问时间
            session.last_accessed = datetime.utcnow()
            session.api_key.last_used_at = datetime.utcnow()
            db.commit()
            
            return session.api_key.key
    
    def get_sessions_by_api_key(self, api_key_str: str) -> List[Session]:
        """
        根据API密钥获取关联的所有会话
        
        Args:
            api_key_str: API密钥字符串
            
        Returns:
            会话列表，按最近访问排序
        """
        if not self._running:
            logger.error("SessionService is not running. Cannot perform get_sessions_by_api_key.")
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            api_key_obj = db.query(ApiKey).filter(ApiKey.key == api_key_str).first()
            
            if not api_key_obj:
                return []
            
            return (
                db.query(Session)
                .filter(Session.api_key_id == api_key_obj.id)
                .order_by(Session.last_accessed.desc())
                .all()
            )
        
    def update_session_access(self, session_id: str) -> bool:
        """
        更新会话的最后访问时间及其关联API密钥的最后使用时间。
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功更新 (会话存在则为True)
        """
        if not self._running:
            logger.error("SessionService is not running. Cannot perform update_session_access.")
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            
            if not session:
                return False
            
            session.last_accessed = datetime.utcnow()
            
            if session.api_key:
                session.api_key.last_used_at = datetime.utcnow()
            
            db.commit()
            return True
        
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功删除 (会话存在并被删除则为True)
        """
        if not self._running:
            logger.error("SessionService is not running. Cannot perform delete_session.")
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            
            if not session:
                logger.warning(f"尝试删除不存在的会话: {session_id}")
                return False
            
            logger.info(f"删除会话: {session_id}")
            db.delete(session)
            db.commit()
            return True 