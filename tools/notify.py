import mcp.types as types
import logging

from server.tool.base import BaseTool

logger = logging.getLogger(__name__)

class NotificationStreamTool(BaseTool):
    def __init__(self):
        super().__init__()
        logger.debug("NotificationStreamTool instance created (sends one actual test message).")

    async def _invoke(
        self, app_context, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app_context

        logger.info(
            f"NotificationStreamTool _invoke called (to send one actual test message)."
        )

        notification_msg = "This is a single test notification sent via session."
        
        await ctx.session.send_log_message(
            level="info",
            data=notification_msg,
            logger="notification_test_message_tool", # Using a distinct logger name
            related_request_id=ctx.request_id,
        )
        logger.debug(f"Sent one actual test notification via session: {notification_msg}")
        
        return [
            types.TextContent(
                type="text",
                text=(
                    f"Sent one actual test notification via session."
                ),
            )
        ] 