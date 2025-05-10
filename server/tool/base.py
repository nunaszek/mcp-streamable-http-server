import abc
import mcp.types as types
from typing import Any, Dict, List

class BaseTool(abc.ABC):
    """
    Abstract base class for all tools.
    Subclasses must implement the _invoke method.
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    async def _invoke(
        self, app_context: Any, arguments: Dict[str, Any]
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Protected method to be implemented by subclasses to perform the tool's action.
        """
        raise NotImplementedError("Subclasses must implement the \'_invoke\' method.")

    async def invoke(
        self, app_context: Any, arguments: Dict[str, Any]
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Public method called by the system to execute the tool.
        """
        return await self._invoke(app_context, arguments) 