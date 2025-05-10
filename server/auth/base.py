from abc import ABC, abstractmethod
from typing import Any

# Assuming RequestCredentialsContext will be in .core or moved here.
# For now, let's assume it can be imported from .core
from .core import RequestCredentialsContext

class AuthStrategy(ABC):
    """
    Abstract base class for an authentication/verification strategy.
    Instances of this class are callable.
    """

    @abstractmethod
    def __call__(self, context: RequestCredentialsContext) -> bool:
        """
        Verifies the request based on the given context when the strategy instance is called.

        Args:
            context: The request credentials context.

        Returns:
            True if verification is successful, False otherwise.
        """
        pass

    def __str__(self) -> str:
        return self.__class__.__name__ 