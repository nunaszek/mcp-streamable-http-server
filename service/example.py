import asyncio
import logging
from server.service.base import BaseService

logger = logging.getLogger(__name__)

class ExampleService(BaseService):
    """
    An example service implementation for demonstration and testing purposes.
    """
    def __init__(self, name: str = "ExampleService"):
        self.name = name
        self._running = False
        self._internal_task = None
        logger.info(f"{self.name} instance created.")

    async def start(self) -> None:
        """Starts the example service, simulating some startup work and a background task."""
        if self._running:
            logger.warning(f"{self.name} is already running.")
            return
        
        logger.info(f"Starting {self.name}...")
        await asyncio.sleep(0.1)  # Simulate initial startup work
        self._running = True
        # Example of a simple background task
        # self._internal_task = asyncio.create_task(self._run_background_work())
        logger.info(f"{self.name} started successfully.")

    async def _run_background_work(self):
        """Simulates a background task performed by the service."""
        try:
            count = 0
            while self._running:
                count += 1
                logger.debug(f"{self.name} background task running, iteration {count}.")
                await asyncio.sleep(5) # Perform work every 5 seconds
        except asyncio.CancelledError:
            logger.info(f"{self.name} background task was cancelled.")
        except Exception as e:
            logger.error(f"{self.name} background task encountered an error: {e}", exc_info=True)
        finally:
            logger.info(f"{self.name} background task finished.")

    async def release(self) -> None:
        """Releases resources held by the example service."""
        if not self._running:
            logger.warning(f"{self.name} is not running, no release needed or already released.")
            return

        logger.info(f"Releasing {self.name}...")
        self._running = False # Signal background tasks to stop
        
        if self._internal_task:
            logger.debug(f"Cancelling internal task for {self.name}...")
            self._internal_task.cancel()
            try:
                await self._internal_task
            except asyncio.CancelledError:
                logger.info(f"Internal task for {self.name} successfully cancelled during release.")
            self._internal_task = None
        
        await asyncio.sleep(0.1)  # Simulate cleanup work
        logger.info(f"{self.name} released successfully.")

    async def get_service_status(self) -> str:
        """Returns the current running status of the service."""
        status = "running" if self._running else "not running"
        logger.debug(f"{self.name} status requested: {status}")
        return f"{self.name} is currently {status}." 