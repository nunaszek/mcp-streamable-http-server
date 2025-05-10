import contextlib
import logging
from collections.abc import AsyncIterator

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from starlette.responses import JSONResponse
from starlette.requests import Request as StarletteRequest

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root)) # Allow importing config.py from root
import config
from .auth import loader as auth_loader

from .tool import loader as tool_loader
from .event import InMemoryEventStore
from .transport.streamable_http_manager import FastStreamableHTTPSessionManager

logger = logging.getLogger(__name__)

TOOLS_CONFIG_DIR = project_root / "tools"


@click.command()
@click.option(
    "--host", 
    default=None,
    help=f"Host for HTTP. Overrides HOST in .env (current: {config.HOST})"
)
@click.option(
    "--port", 
    default=None,
    type=int,
    help=f"Port for HTTP. Overrides PORT in .env (current: {config.PORT})"
)
@click.option(
    "--log-level",
    default=None,
    help=f"Logging level. Overrides LOG_LEVEL in .env (current: {config.LOG_LEVEL})",
)
@click.option(
    "--server-name",
    default=None,
    help=f"Server name. Overrides SERVER_NAME in .env (current: {config.SERVER_NAME})"
)
@click.option(
    "--json-response",
    is_flag=True,
    default=config.JSON_RESPONSE,
    help=f"Enable JSON responses. Overrides JSON_RESPONSE in .env (current: {config.JSON_RESPONSE})"
)
def run(
    host: str | None,
    port: int | None,
    log_level: str | None,
    server_name: str | None, 
    json_response: bool,
) -> int:
    final_host = host if host is not None else config.HOST
    final_port = port if port is not None else config.PORT
    final_log_level = log_level if log_level is not None else config.LOG_LEVEL
    final_server_name = server_name if server_name is not None else config.SERVER_NAME
    final_json_response = json_response

    logging.basicConfig(
        level=getattr(logging, final_log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info(f"Starting server '{final_server_name}' on {final_host}:{final_port} with log level {final_log_level}, App Version: {config.APP_VERSION}")

    auth_loader.load_strategies()
    tool_loader.load_tools_from_directory(TOOLS_CONFIG_DIR)

    app = Server(final_server_name)

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
                logger.error(f"执行工具 '{name}' 的 invoke 方法时发生错误: {e}", exc_info=True)
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

    event_store = InMemoryEventStore()

    session_manager = FastStreamableHTTPSessionManager(
        app=app,
        event_store=event_store,
        json_response=final_json_response,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app_starlette: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    async def homepage(request: StarletteRequest) -> JSONResponse:
        """Handler for the root path, providing server status and info."""
        mcp_server_name = request.app.state.mcp_server_name
        mcp_version = config.APP_VERSION
        return JSONResponse({
            "server_name": mcp_server_name,
            "version": mcp_version,
            "status": "running",
            "message": f"Welcome to {mcp_server_name}!",
            "mcp_endpoint": "/mcp"
        })

    starlette_app = Starlette(
        debug=True, # For development; consider making this configurable
        routes=[
            Route("/", endpoint=homepage),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )
    # Correctly assign mcp_server_name to app.state here
    starlette_app.state.mcp_server_name = final_server_name

    import uvicorn

    uvicorn.run(starlette_app, host=final_host, port=final_port)

    return 0
