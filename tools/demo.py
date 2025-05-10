import logging
from typing import Dict, Any, List

# 从你的项目结构中导入 BaseTool 和 MCP 类型
from server.tool.base import BaseTool
import mcp.types as types

logger = logging.getLogger(__name__)

class GetSessionIdDemoTool(BaseTool):
    """
    A demo tool to retrieve the session_id from the application context
    and process a user-provided message.
    """

    def __init__(self):
        super().__init__()
        logger.debug("GetSessionIdDemoTool instance created.")

    async def _invoke(
        self, app_context: Any, arguments: Dict[str, Any]
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        test = arguments.get("test") # Get the new parameter
        session_id = app_context.meta.session_id if hasattr(app_context, 'meta') and app_context.meta is not None and hasattr(app_context.meta, 'session_id') else "N/A"
        session_id_info = f"Session ID: {session_id}"
        response_text = f"{session_id_info}. Input: '{test}'"

        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]
