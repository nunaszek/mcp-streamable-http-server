import contextlib
import logging
from collections.abc import AsyncIterator

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# 更新导入以指向 server.tool.loader
from .tool import loader as tool_loader
from pathlib import Path

from .event import InMemoryEventStore
from .transport.streamable_http_manager import FastStreamableHTTPSessionManager

# Configure logging
logger = logging.getLogger(__name__)

TOOLS_CONFIG_DIR = Path(__file__).resolve().parent.parent / "tools"


@click.command()
@click.option("--port", default=3000, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
def run(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # tool_loader 现在是从 server.tool.loader 导入的
    tool_loader.load_tools_from_directory(TOOLS_CONFIG_DIR)

    app = Server("mcp-streamable-http-demo")

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        tool_instance = tool_loader.get_tool_instance(name) 
        
        if tool_instance:
            try:
                return await tool_instance.invoke(ctx, arguments)
            except Exception as e:
                return [
                    types.TextContent(
                        type="text",
                        text=f"执行工具 '{name}' 时发生内部错误。请检查服务器日志。"
                    )
                ]
        else:
            logger.warning(f"未找到工具 '{name}' 的实例或定义。")
            return [
                types.TextContent(
                    type="text",
                    text=f"错误: 未找到名为 '{name}' 的工具。",
                )
            ]

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return tool_loader.get_tool_definitions()

    # Create event store for resumability
    event_store = InMemoryEventStore()

    # Create the session manager with our app and event store
    session_manager = FastStreamableHTTPSessionManager(
        app=app,
        event_store=event_store,  # Enable resumability
        json_response=json_response,
    )

    # ASGI handler for streamable HTTP connections
    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application using the transport
    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0