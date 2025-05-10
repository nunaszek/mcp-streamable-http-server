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
from .middleware import loader as middleware_loader

from .tool import loader as tool_loader
from .event import InMemoryEventStore
from .transport.streamable_http_manager import FastStreamableHTTPSessionManager
from server.service.loader import ServiceLoader

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

    def _setup_logging(log_level_str: str, server_name_str: str, host_str: str, port_int: int, app_version_str: str):
        logging.basicConfig(
            level=getattr(logging, log_level_str.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logger.info(
            f"Starting server '{server_name_str}' on {host_str}:{port_int} "
            f"with log level {log_level_str}, App Version: {app_version_str}"
        )

    def _prepare_services(loader: ServiceLoader) -> dict:
        prepared_services: dict = {}
        if loader.service_instances:
            for service_instance in loader.service_instances:
                service_class_name = type(service_instance).__name__
                prepared_services[service_class_name] = service_instance
                # logger.info(f"Service '{service_class_name}' prepared for lifespan state.")
        # else:
            # logger.info("No service instances found to add to lifespan state.")
        return prepared_services

    final_host = host if host is not None else config.HOST
    final_port = port if port is not None else config.PORT
    final_log_level = log_level if log_level is not None else config.LOG_LEVEL
    final_server_name = server_name if server_name is not None else config.SERVER_NAME
    final_json_response = json_response

    _setup_logging(final_log_level, final_server_name, final_host, final_port, config.APP_VERSION)

    middleware_loader._discover_and_load_middlewares(middleware_dir="middlewares")
    tool_loader.load_tools_from_directory(TOOLS_CONFIG_DIR)

    service_loader = ServiceLoader(services_package_name="service")
    service_loader.discover_and_load_services()
    # logger.info(f"ServiceLoader initialized for 'service' package and services discovered. Found {len(service_loader.service_instances)} services.")

    services = _prepare_services(service_loader)

    app = Server(final_server_name)

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        tool_instance = tool_loader.get_tool_instance(name) 
        
        if tool_instance:
            try:
                # Assuming tool_instance.invoke can now use ctx.lifespan_context if needed
                return await tool_instance.invoke(ctx, arguments, services)
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
    async def lifespan(starlette_app_instance: Starlette) -> AsyncIterator[dict]:
        """
        Manages service lifecycle (start/stop) and yields the application state
        containing active services.
        """
        _service_loader: ServiceLoader | None = getattr(starlette_app_instance.state, 'service_loader', None)
        _services: dict = getattr(starlette_app_instance.state, 'services', {})
        
        logger.info("Lifespan context manager entered.")

        async with contextlib.AsyncExitStack() as stack:
            # Start session manager
            await stack.enter_async_context(session_manager.run())
            logger.info("Application started with StreamableHTTP session manager (lifespan)!")

            if _service_loader:
                # logger.info("Starting managed services (lifespan)...")
                await _service_loader.start_all()
                # Ensure services are released when the stack unwinds
                stack.push_async_callback(_service_loader.release_all)
                # logger.info("Managed services started and release registered (lifespan).")
            else:
                logger.warning("ServiceLoader not found in app state during lifespan. Services will not be started/stopped.")
            
            try:
                # logger.info(f"Lifespan yielding services with keys: {list(_services.keys())}")
                yield _services # Yield the pre-prepared map of services
            finally:
                logger.info("Application shutting down (lifespan)...")

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
        debug=True, 
        routes=[
            Route("/", endpoint=homepage),
            Mount("/mcp", app=handle_streamable_http), # app here is our Server instance wrapped by handle_streamable_http
        ],
        lifespan=lifespan,
    )
    # Store necessary components in Starlette app's state
    starlette_app.state.mcp_server_name = final_server_name
    starlette_app.state.service_loader = service_loader  # For lifespan to start/stop services
    starlette_app.state.services = services # For lifespan to yield

    import uvicorn

    uvicorn.run(starlette_app, host=final_host, port=final_port)

    return 0
