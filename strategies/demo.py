import logging
from typing import Optional

from server.auth.base import AuthStrategy, RequestCredentialsContext

logger = logging.getLogger(__name__)

class TestAuthStrategy(AuthStrategy):
    """A test authentication strategy that always allows requests."""

    def __init__(self):
        super().__init__() # Call the base class __init__ if it has one
        logger.info("TestAuthStrategy initialized. This strategy will always allow requests.")

    def __call__(self, context: RequestCredentialsContext) -> bool:
        """Always returns True, effectively allowing the request."""
        logger.debug(f"TestAuthStrategy is allowing request for session: {context.session_id}, IP: {context.client_ip}")
        return True 