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
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        test = arguments.get("test") # Get the new parameter
        session_id = context.meta.session_id if hasattr(context, 'meta') and context.meta is not None and hasattr(context.meta, 'session_id') else "N/A"
        session_id_info = f"Session ID: {session_id}"

        # 获取当前时间
        # example = context.lifespan_context.get("ExampleService") # 旧的获取方式, lifespan_context 不再直接可用
        example_service = services.get("ExampleService") # 使用 services 获取服务
        
        # print(example)
        service_status_message = "ExampleService not found or not active."
        if example_service:
            # example_status = await example_service.get_service_status()
            # print(example_status)
            # 假设 ExampleService 有一个 get_info 方法
            service_status_message = f"ExampleService Info: {await example_service.get_service_status()}" 

        response_text = f"{session_id_info}. Input: '{test}'. {service_status_message}"

        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]
