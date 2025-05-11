import logging
from typing import Optional

from server.middleware.base import McpMiddleware
from server.middleware.core import RequestCredentialsContext

logger = logging.getLogger(__name__)

class TestMiddleware(McpMiddleware):
    """A test middleware that always allows requests."""

    def __init__(self):
        super().__init__()

    def __call__(self, context: RequestCredentialsContext) -> bool:
        """Always returns True, allowing the request."""
        return True