# MCP Streamable HTTP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Built with Starlette](https://img.shields.io/badge/built%20with-Starlette-green.svg)](https://www.starlette.io/)
[![Linted with Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tested with Pytest](https://img.shields.io/badge/tested%20with-Pytest-blue.svg)](https://pytest.org)
[![Managed with uv](https://img.shields.io/badge/managed%20with-uv-purple.svg)](https://docs.astral.sh/uv/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-orange.svg)](https://modelcontextprotocol.io/)

[简体中文](./README.md) | [English](./README.en.md)

## 📝 Overview

The `mcp-streamable-http-server` project aims to provide a feature-rich **development template for StreamableHttp services**. It features the following core characteristics:

- 🔑 **Flexible Authentication Mechanisms**: Supports parameter passing and authentication via URL query and JWT token under the Streamable HTTP transport protocol.
- 🆔 **Context-Aware User Identification**: Capable of passing `session_id` to tools through the context, enabling tools to quickly identify the requesting user.
- 🔄 **Dynamic Service Registration and Startup**: Supports hot-registering and starting new services while the system is running, enhancing system flexibility and scalability.
- 🛡️ **Customizable Middleware**: Allows developers to define custom middleware in the project, easily implementing custom logic such as IP interception and advanced authentication.
- ⚙️ **Convenient Tool Configuration**: Supports defining tool method input parameters via YAML files, simplifying the configuration process and improving development efficiency.

## Table of Contents

- [📁 Project Structure](#project-structure)
- [⚙️ Project Logic](#project-logic)
- [🚀 Installation](#installation)
- [🔍 Inspector Debugging](#inspector-debugging)
- [💡 Development Examples](#development-examples)
- [🐳 Docker Installation](#docker-installation)
- [📚 Documentation](#documentation)
- [📜 License](#license)

## 📁 Project Structure

```
/mcp-streamable-http-server
├── middlewares/          # Custom Middlewares
│   ├── authorize.py        #   - Authorization Middleware
│   ├── demo.py             #   - Demo Middleware
│   └── __init__.py
├── models/               # Data Models
│   └── session.py          #   - Session-related Models
├── server/               # MCP Server Core
├── service/              # Business Service Implementations
│   ├── database.py         #   - Database Service/Operations
│   ├── example.py          #   - Example Service
│   ├── session.py          #   - Session Management Service
│   └── __init__.py
├── tools/                # Custom MCP Tools
│   ├── demo.py             #   - Demo tool configuration
│   ├── demo.yaml           #   - Demo function
│   ├── notify.py           #   - Notification tool configuration
│   ├── notify.yaml         #   - Notify function
│   └── __init__.py
├── config.py             # Project Configuration
├── .env                  # Environment variables file (actual local configuration)
├── .env.example          # Environment variables file example (as a configuration template)
├── database.db           # SQLite Database
├── pyproject.toml        # Python Project Definition and Dependencies
└── uv.lock               # Dependency Version Lock File
```

## ⚙️ Project Logic

This section describes the core interaction flow of `mcp-streamable-http-server`. The following sequence diagram illustrates the key steps from client connection and authentication to invoking tools and external services via the MCP server, and how the main components collaborate.

```mermaid
sequenceDiagram
    title Core Interaction Sequence Diagram for mcp-streamable-http-server

    participant Client
    participant MCP Server
    participant Database
    participant External Service

    Client->>MCP Server: connect (with key/jwttoken)
    activate MCP Server
    MCP Server->>MCP Server: Middleware processing (authentication check)
    alt Authentication Failed
        MCP Server-->>Client: Authentication failed response
    else Authentication Successful
        MCP Server->>MCP Server: Create session_id
        MCP Server->>MCP Server: Associate session_token (with original credentials)
        MCP Server-->>Client: Connection successful (returns session_id)
    end
    deactivate MCP Server // End of connection and initial authentication phase

    Client->>MCP Server: API request (with session_id)
    activate MCP Server
    MCP Server->>MCP Server: Pass session_id to tool method
    MCP Server->>Database: Check if session_id has an associated key in the database
    activate Database
    Database-->>MCP Server: Return key
    deactivate Database

    alt If key is valid and retrieved successfully
        MCP Server->>External Service: Call external service with apikey
        activate External Service
        External Service-->>MCP Server: Return query result
        deactivate External Service
        MCP Server->>MCP Server: Consolidate information
        MCP Server-->>Client: Return result
    else Key is invalid or retrieval failed
        MCP Server-->>Client: Error response (e.g., invalid key)
    end
    deactivate MCP Server
```

## 🚀 Installation

1.  **Prerequisites**:

    - Python >= 3.13
    - [uv (recommended)](https://docs.astral.sh/uv/) or pip
    - Git

2.  **Clone the project**:

    ```bash
    git clone https://github.com/purity3/mcp-streamable-http-server.git
    cd mcp-streamable-http-server
    ```

3.  **Create and activate a virtual environment** (recommended):

    - Using venv:
      ```bash
      python -m venv .venv
      source .venv/bin/activate  # Linux/macOS
      # .venv\Scripts\activate    # Windows
      ```
    - If you use `pyenv` and `pyenv-virtualenv`, refer to their documentation.

4.  **Install dependencies**:
    - Using uv (recommended):
      ```bash
      uv pip install -e .[dev] # Install the project and its development dependencies
      ```
    - Or using pip:
      ```bash
      pip install -e .[dev] # Install the project and its development dependencies
      ```
5.  **Environment Configuration**:
    - Copy the `.env.example` file to `.env` and modify the configuration items within it according to your local environment needs (e.g., `DATABASE_URL`, `HOST`, `PORT`, etc.).
    - (For SQLite) The `database.db` file is usually located in the project root directory. If the `DATABASE_URL` configured in the `.env` file points to an SQLite file (e.g., `DATABASE_URL="sqlite:///./database.db"`) and this file does not yet exist, the service will typically create it automatically upon its first attempt to access the database.

6.  **Start the service**:
    - After completing all the above configuration and installation steps, use the following command to start the MCP server:
      ```bash
      uv run server
      ```
    - Once started successfully, you can access the service according to the `HOST` and `PORT` configuration in your `.env` file (defaults to `http://0.0.0.0:3000` or `http://localhost:3000`).

## 🔍 Inspector Debugging

You can use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) tool for visual debugging.

**Debugging Steps:**

1.  **Run `mcp-streamable-http-server`**:
    Follow step 6 in the "Installation" section to start your local server (default `http://localhost:3000`).

2.  **Start MCP Inspector**:
    In a new terminal, execute:
    ```bash
    npx @modelcontextprotocol/inspector
    ```
    The Inspector UI runs by default at `http://localhost:6274`.

3.  **Connect to the Server**:
    *   Open the Inspector UI (`http://localhost:6274`).
    *   Set **Transport Type**: `streamable-http`.
    *   Set **Server URL**: Your server address, e.g., `http://localhost:3000/mcp` (the specific path like `/mcp` may need adjustment based on your server routing).
    *   If your server has authentication, fill in the credentials in the UI.

4.  **Start Debugging**:
    Once connected, you can view and invoke the server's Tools, Resources, and Prompts in the Inspector UI.

For more details, please refer to the [MCP Inspector official documentation](https://github.com/modelcontextprotocol/inspector).

## 💡 Development Examples

This section demonstrates how to add custom middleware, services, and tools to the project.

### Middleware

Custom middleware is used to execute common logic in the request processing flow and should inherit from `McpMiddleware`.

**Example: `middlewares/demo.py` (`TestMiddleware`)**

This middleware always allows requests to pass, serving as a starting point for more complex logic (like authentication, logging).

```python
# middlewares/demo.py
import logging
from typing import Optional

from server.middleware.base import McpMiddleware
from server.middleware.core import RequestCredentialsContext

logger = logging.getLogger(__name__)

class TestMiddleware(McpMiddleware):
    """A test middleware that always allows requests."""

    def __init__(self):
        super().__init__()

    def __call__(self, context: RequestCredentialsContext) -> bool:
        """Always returns True, allowing the request."""
        return True
```

**Integration:** Register the middleware in the server configuration (usually in `server/main.py` or a similar file).

### Service

Services are used to encapsulate business logic and inherit from `BaseService`.

**Example: `service/example.py` (`ExampleService`)**

Shows the basic structure of a service, including `start`, `release`, and `get_service_status` methods.

```python
# service/example.py
import asyncio
import logging
from server.service.base import BaseService

logger = logging.getLogger(__name__)

class ExampleService(BaseService):
    """Example service for demonstration."""
    def __init__(self, name: str = "ExampleService"):
        self.name = name
        self._running = False

    async def start(self) -> None:
        """Starts the example service."""
        if self._running:
            return
        
        await asyncio.sleep(0.1)
        self._running = True

    async def release(self) -> None:
        """Releases resources held by the example service."""
        if not self._running:
            return

        self._running = False
        
        await asyncio.sleep(0.1)

    async def get_service_status(self) -> str:
        """Returns the current running status of the service."""
        status = "running" if self._running else "not running"
        return f"{self.name} is currently {status}."
```

**Integration:** Services are typically instantiated when the server starts and provided to callers via dependency injection or similar mechanisms.

### Tools

Tools are specific capabilities exposed by the MCP server, consisting of Python implementations and YAML configurations, inheriting from `BaseTool`.

**Example: `tools/demo.py` and `tools/demo.yaml` (`GetSessionIdDemoTool`)**

This tool demonstrates how to get the `session_id`, call a service (like `SessionService`), and return a result combining user input.

**`tools/demo.yaml` (Tool Definition):**
```yaml
name: demo
description: A demo tool that retrieves session ID and processes a user-provided message.
inputSchema:
  type: object
  required:
    - input
  properties:
    input:
      type: string
      description: A message provided by the user.
  additionalProperties: false
source: tools/demo.py
```

**`tools/demo.py` (Tool Implementation):**
```python
# tools/demo.py
import logging
from typing import Dict, Any, List

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
        # logger.debug("GetSessionIdDemoTool instance created.") # Logging can be omitted in examples

    async def _invoke(
        self, context: Any, arguments: Dict[str, Any], services: dict[str, Any]
    ) -> List[types.TextContent]:
        
        input_param = arguments.get("input")
        session_id = getattr(meta_obj, 'session_id', "N/A") if (meta_obj := getattr(context, 'meta', None)) is not None else "N/A"
        
        api_key = "N/A"
        session_service = services.get("SessionService")
        if session_service:
            try:
                api_key = session_service.get_api_key_by_session_id(session_id)
            except Exception as e:
                logger.error(f"Error getting API key from SessionService: {e}") # Retain error logging
        
        response_text = f"Session ID: {session_id}.\\nInput: '{input_param}'.\\napi_key: {api_key}"

        return [types.TextContent(type="text", text=response_text)]
```

**Integration:** Tools are loaded automatically via YAML configuration. Ensure `source` points to the correct Python file.

**Example: `tools/notify.py` and `tools/notify.yaml` (`NotificationStreamTool` - Sending Notifications/Logs)**

This tool sends log/notification messages via `context.session.send_log_message`.

**`tools/notify.yaml` (Tool Definition):**
```yaml
name: notify
description: Sends a single test notification.
inputSchema:
  type: object
  properties: {} # No input parameters
  additionalProperties: false
source: tools/notify.py
```

**`tools/notify.py` (Tool Implementation):**
```python
# tools/notify.py
import mcp.types as types
import logging
from typing import Any

from server.tool.base import BaseTool

logger = logging.getLogger(__name__)

class NotificationStreamTool(BaseTool):
    # def __init__(self):
    #     super().__init__()
    #     logger.debug("NotificationStreamTool instance created...") # Logging can be omitted in examples

    async def _invoke(
        self, context: Any, arguments: dict, services: dict[str, Any]
    ) -> list[types.TextContent]: # Explicit return type
        
        # logger.info("NotificationStreamTool _invoke called...") # Logging can be omitted in examples
        notification_msg = "This is a single test notification sent via session."
        
        await context.session.send_log_message(
            level="info",
            data=notification_msg,
            logger="notification_test_message_tool",
            related_request_id=context.request_id,
        )
        # logger.debug(f"Sent one actual test notification...") # Logging can be omitted in examples
        
        return [types.TextContent(type="text", text="Sent one actual test notification via session.")]
```
This tool calls `context.session.send_log_message` to send messages, which can be used for asynchronous updates or debugging.

## Examples

[Provide some usage examples or API request samples here to help users better understand how to interact with your `mcp-streamable-http-server`. For example, a `curl` request.]

```bash
# Example: curl http://localhost:3000/some-stream-endpoint
```

## 🐳 Docker Installation

This project supports containerized execution via Docker, providing a `Dockerfile` and `docker-compose.yml`.

### Using Dockerfile

1.  **Build the image** (replace `mcp-streamable-http-server` with your desired image name):
    ```bash
    docker build -t mcp-streamable-http-server .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 3000:3000 --name mcp-streamable-http-container -d mcp-streamable-http-server
    ```
    *   `-p 3000:3000`: Maps the host port to the container port.
    *   `--name`: Specifies the container name.
    *   `-d`: Runs in detached mode (background).
    *   To pass environment variables (e.g., for database configuration or adjusting the port):
        ```bash
        docker run -p 3000:3000 --name mcp-streamable-http-container \
          -e DATABASE_URL="sqlite:///data/database.db" \
          -e PORT="3000" \
          # -v $(pwd)/data:/data # SQLite data persistence (optional)
          -d mcp-streamable-http-server
        ```
        *(SQLite persistence: Mount a host directory to the container's data directory; adjust paths as needed for your actual configuration.)*

### Using Docker Compose (Recommended for Local Development)

The `docker-compose.yml` file predefines the service configuration, facilitating local startup.

1.  **Start the services**:
    ```bash
    docker-compose up -d # -d for detached mode
    ```

2.  **View logs** (refer to `docker-compose.yml` for the service name):
    ```bash
    docker-compose logs -f your-service-name 
    ```

3.  **Stop the services**:
    ```bash
    docker-compose down # Stops and removes containers
    # docker-compose stop # Stops services only
    ```

**Note:**
*   Ensure Docker and Docker Compose are installed.
*   Refer to `Dockerfile` and `docker-compose.yml` for specific environment variables, ports, and volume mounts.
*   Production deployments may require more complex configurations.

## 📚 Documentation

This project is implemented based on the official Model Context Protocol (MCP) Python SDK. For more information about the MCP Python SDK, please refer to its official GitHub repository:
[modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details. 