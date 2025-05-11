import logging
from typing import Optional

from server.middleware.base import McpMiddleware
from server.middleware.core import RequestCredentialsContext
from service.session import SessionService # Assuming SessionService is the correct import
from models.session import ApiKey # For type hinting if needed

logger = logging.getLogger(__name__)

class AuthorizeMiddleware(McpMiddleware):
    """Authorizes requests based on an API key."""

    def __init__(self):
        super().__init__()

    async def __call__(self, context: RequestCredentialsContext) -> bool:
        """Validates the API key and relates it to the session."""
        session_service: Optional[SessionService] = context.services.get("SessionService")
        token = self._get_verify_token(context)

        if not isinstance(session_service, SessionService):
            return False

        if not token:
            return False

        if not await self._verify_token(token):
            return False
        
        try:
            await self._relate_token_to_session(token, session_service, context)
        except Exception:
            return False
            
        return True
    
    def _get_verify_token(self, context: RequestCredentialsContext) -> Optional[str]:
        """Extracts the API key from Authorization header, then query parameters, then x-api-key header."""
        # 1. Try to get from Authorization header
        auth_header = context.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            parts = auth_header.split(' ', 1)
            if len(parts) == 2:
                return parts[1]
        
        # 2. If not in Authorization header, try query parameter 'key'
        token_from_query = context.query_params.get('key')
        if token_from_query:
            return token_from_query
            
        return None
    
    async def _verify_token(self, token: str) -> bool:
        """Verifies the token."""
        # TODO: Implement token verification logic
        return True
    
    async def _relate_token_to_session(self, token: str, session_service: SessionService, context: RequestCredentialsContext) -> None:
        """Relates the token to a user session."""
        try:
            session_service.create_session(
                api_key_str=token,
                session_id=context.session_id
            )
            
            session_service.update_session_access(context.session_id)
        except Exception as e:
            raise e
