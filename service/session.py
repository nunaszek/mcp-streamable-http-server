from sqlalchemy.orm import Session as DbSession
from sqlalchemy import desc
from datetime import datetime
from typing import Optional, List
import logging
import asyncio

from models.session import ApiKey, Session
from service.database import get_db_context
from server.service.base import BaseService

logger = logging.getLogger(__name__)

class SessionService(BaseService):
    """Session management service."""
    
    def __init__(self):
        super().__init__()
        self._running = False
    
    async def start(self) -> None:
        """Starts the session service."""
        if self._running:
            return
        
        await asyncio.sleep(0.01)
        self._running = True

    async def release(self) -> None:
        """Releases resources held by the session service."""
        if not self._running:
            return

        self._running = False
        await asyncio.sleep(0.01)

    def get_or_create_api_key(self, key: str) -> ApiKey:
        """Gets or creates an API key."""
        if not self._running:
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            api_key = db.query(ApiKey).filter(ApiKey.key == key).first()
            
            if not api_key:
                api_key = ApiKey(key=key, created_at=datetime.utcnow(), last_used_at=datetime.utcnow())
                db.add(api_key)
                db.commit()
                db.refresh(api_key)
            else:
                api_key.last_used_at = datetime.utcnow()
                db.commit()
            
            return api_key
    
    def create_session(self, api_key_str: str, session_id: str) -> Session:
        """Creates a new session and associates it with an API key."""
        if not self._running:
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            api_key_obj = self._get_or_create_api_key_internal(db, api_key_str)
            
            existing_session = db.query(Session).filter(Session.session_id == session_id).first()
            if existing_session:
                existing_session.api_key_id = api_key_obj.id
                existing_session.last_accessed = datetime.utcnow()
                db.commit()
                db.refresh(existing_session)
                return existing_session
            
            session_count = db.query(Session).filter(Session.api_key_id == api_key_obj.id).count()
            
            MAX_SESSIONS_PER_KEY = 5 
            if session_count >= MAX_SESSIONS_PER_KEY:
                oldest_session = (
                    db.query(Session)
                    .filter(Session.api_key_id == api_key_obj.id)
                    .order_by(Session.last_accessed.asc())
                    .first()
                )
                if oldest_session:
                    db.delete(oldest_session)
                    db.commit()
            
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
    
    def _get_or_create_api_key_internal(self, db: DbSession, key: str) -> ApiKey:
        """Internal helper to get or create API key with existing DB session."""
        api_key = db.query(ApiKey).filter(ApiKey.key == key).first()
        if not api_key:
            api_key = ApiKey(key=key, created_at=datetime.utcnow(), last_used_at=datetime.utcnow())
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
        else:
            api_key.last_used_at = datetime.utcnow()
            db.commit()
        return api_key
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Gets a session by its ID."""
        if not self._running:
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            return session
    
    def get_api_key_by_session_id(self, session_id: str) -> Optional[str]:
        """Gets the API key string for a given session ID."""
        if not self._running:
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            session = db.query(Session).join(ApiKey).filter(Session.session_id == session_id).first()
            
            if not session or not session.api_key:
                return None
            
            session.last_accessed = datetime.utcnow()
            session.api_key.last_used_at = datetime.utcnow()
            db.commit()
            
            return session.api_key.key
    
    def get_sessions_by_api_key(self, api_key_str: str) -> List[Session]:
        """Gets all sessions associated with an API key."""
        if not self._running:
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
        """Updates the last access time for a session and its API key."""
        if not self._running:
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
        """Deletes a session."""
        if not self._running:
            raise RuntimeError("SessionService is not active.")

        with get_db_context() as db:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            
            if not session:
                return False
            
            db.delete(session)
            db.commit()
            return True 