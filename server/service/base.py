from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """
    Abstract base class for services.
    Services are expected to implement start and release methods for lifecycle management.
    """

    @abstractmethod
    async def start(self) -> None:
        """
        Starts the service.
        This method should contain the logic to initialize and start the service's operations.
        It can be used for tasks like establishing connections, starting background tasks, etc.
        """
        pass

    @abstractmethod
    async def release(self) -> None:
        """
        Releases any resources held by the service.
        This method should contain the logic to gracefully shut down the service
        and release any resources it holds (e.g., closing connections, stopping tasks).
        """
        pass 