import logging
from typing import Optional

from server.middleware.base import McpMiddleware
from server.middleware.core import RequestCredentialsContext
from service.session import SessionService # Assuming SessionService is the correct import
from models.session import ApiKey # For type hinting if needed

logger = logging.getLogger(__name__)

class AuthorizeMiddleware(McpMiddleware):
    """
    Authorizes requests based on an API key provided in the query parameters.
    """

    def __init__(self):
        super().__init__()

    async def __call__(self, context: RequestCredentialsContext) -> bool:
        """
        Validates the API key from query parameters.

        Args:
            context: The request credentials context.

        Returns:
            True if the API key is valid and session related, False otherwise.
        """
        session_service: Optional[SessionService] = context.services.get("SessionService")
        token = self._get_verify_token(context)

        if not isinstance(session_service, SessionService):
            logger.error(f"AuthorizeMiddleware: Found 'SessionService' in context.services, but it is not an instance of SessionService. Type is {type(session_service)}. Request denied.")
            return False

        if not token:
            logger.warning("AuthorizeMiddleware: Missing API key in query parameters or 'x-api-key' header. Request denied.")
            return False

        if not await self._verify_token(token):
            logger.warning(f"AuthorizeMiddleware: Invalid token. Request denied.")
            return False
        
        try:
            await self._relate_token_to_session(token, session_service, context)
        except Exception as e:
            logger.error("AuthorizeMiddleware: Failed to relate token to session. See previous log for details. Request denied.")
            return False
            
        return True
    
    def _get_verify_token(self, context: RequestCredentialsContext) -> Optional[str]:
        """
        Verify the token from the request.
        """
        token = context.query_params.get('key') or context.headers.get('x-api-key')
        return token
    
    async def _verify_token(self, token: str) -> bool:
        """
        Verify the token.
        """
        # TODO: Implement token verification logic
        return True
    
    async def _relate_token_to_session(self, token: str,session_service: SessionService, context: RequestCredentialsContext) -> None:
        try:
            """
            Relate the token to a user by creating a session.
            """
            # 创建会话记录
            session_service.create_session(
                api_key_str=token,
                session_id=context.session_id
            )
            logger.debug(f"创建会话记录: session_id={context.session_id}, api_key: {token}")
            
            # 更新会话访问时间
            session_service.update_session_access(context.session_id)
        except Exception as e:
            logger.error(f"AuthorizeMiddleware: Error relating token to session: {e}. Request denied.")
            raise e
