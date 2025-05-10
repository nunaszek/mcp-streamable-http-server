import logging
from typing import Optional

from server.middleware.base import McpMiddleware
from server.middleware.core import RequestCredentialsContext

logger = logging.getLogger(__name__)

class TestMiddleware(McpMiddleware):
    """A test authentication middleware that always allows requests."""

    def __init__(self):
        super().__init__() # Call the base class __init__ if it has one
        logger.info("TestMiddleware initialized. This middleware will always allow requests.")

    def __call__(self, context: RequestCredentialsContext) -> bool:
        """Always returns True, effectively allowing the request."""
        logger.debug(f"TestMiddleware is allowing request for session: {context.session_id}, IP: {context.client_ip}")
        return True 