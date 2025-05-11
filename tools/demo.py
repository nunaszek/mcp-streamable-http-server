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
        self, context: Any, arguments: Dict[str, Any], services: dict[str, Any]
    ) -> List[types.TextContent]:
        
        input = arguments.get("input") # Get the new parameter

        session_id = getattr(meta_obj, 'session_id', "N/A") if (meta_obj := getattr(context, 'meta', None)) is not None else "N/A"
        api_key = services.get("SessionService").get_api_key_by_session_id(session_id)
        response_text = f"Session ID: {session_id}.\nInput: '{input}'.\napi_key: {api_key}"

        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]
