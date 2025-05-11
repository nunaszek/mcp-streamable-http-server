import os
import logging

logger = logging.getLogger(__name__)

# --- .env File Support ---
from dotenv import load_dotenv # type: ignore
load_dotenv()

# ==============================================================================
# Server Configuration
# ==============================================================================
HOST: str = os.getenv("HOST", "0.0.0.0") # Host for the server to bind to

PORT: int = int(os.getenv("PORT", 3000))

SERVER_NAME: str = os.getenv("SERVER_NAME", "mcp-streamable-http-default-server") # Name of the server

# ==============================================================================
# Feature Flags
# ==============================================================================
JSON_RESPONSE: bool = os.getenv("JSON_RESPONSE", "False").lower() in ["true", "1", "t", "yes"] # Enable JSON responses instead of SSE for some tools

# ==============================================================================
# Logging Configuration
# ==============================================================================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper() # Logging level (e.g., DEBUG, INFO, WARNING, ERROR)

# ==============================================================================
# Application Information
# ==============================================================================
APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0_default") # Current version of the application

# ==============================================================================
# Database Configuration
# ==============================================================================
DATABASE_URL: str = os.getenv("DATABASE_URL") # URL for the database connection
# Example for PostgreSQL: "postgresql://user:password@host:port/database"
# Example for SQLite (file-based): "sqlite:///./your_database_name.db"
# If DATABASE_URL is not set in .env, it defaults to a local SQLite DB.

# ==============================================================================
# Main Execution Block (for direct run or testing)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 30)
    print("Loaded Configuration Settings")
    print("=" * 30)
    print(f"  Server Host (HOST):           {HOST}")
    print(f"  Server Port (PORT):           {PORT}")
    print(f"  Server Name (SERVER_NAME):    {SERVER_NAME}")
    print("-" * 30)
    print(f"  Log Level (LOG_LEVEL):        {LOG_LEVEL}")
    print(f"  App Version (APP_VERSION):    {APP_VERSION}")
    print("-" * 30)
    print(f"  JSON Response (JSON_RESPONSE):{JSON_RESPONSE}")
    print("-" * 30)
    print(f"  Database URL (DATABASE_URL):  {DATABASE_URL}")
    print("=" * 30)

    # Example of how logger might be used after basicConfig elsewhere
    # logging.basicConfig(level=LOG_LEVEL) 
    # logger.info("Configuration loaded and displayed.")
    # logger.debug(f"Debug mode with HOST: {HOST}")
