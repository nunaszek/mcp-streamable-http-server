import asyncio
import logging
from server.service.base import BaseService

logger = logging.getLogger(__name__)

class ExampleService(BaseService):
    """Example service for demonstration."""
    def __init__(self, name: str = "ExampleService"):
        self.name = name
        self._running = False

    async def start(self) -> None:
        """Starts the example service."""
        if self._running:
            return
        
        await asyncio.sleep(0.1)
        self._running = True

    async def release(self) -> None:
        """Releases resources held by the example service."""
        if not self._running:
            return

        self._running = False
        
        await asyncio.sleep(0.1)

    async def get_service_status(self) -> str:
        """Returns the current running status of the service."""
        status = "running" if self._running else "not running"
        return f"{self.name} is currently {status}." 