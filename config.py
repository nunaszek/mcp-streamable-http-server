import os
import logging

# For .env file support, ensure python-dotenv is installed (pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv not found. .env file will not be loaded.")
    load_dotenv = None # type: ignore

logger = logging.getLogger(__name__)

# --- Server Configuration ---
HOST: str = os.getenv("HOST", "0.0.0.0") # Server Host

_DEFAULT_PORT = 3000
_port_str = os.getenv("PORT")
PORT: int = _DEFAULT_PORT
if _port_str is not None:
    try:
        PORT = int(_port_str)
    except ValueError:
        logger.warning(f"Invalid PORT '{_port_str}', defaulting to {_DEFAULT_PORT}.")
        PORT = _DEFAULT_PORT

SERVER_NAME: str = os.getenv("SERVER_NAME", "mcp-streamable-http-default-server") # Server Name

# --- Feature Flags ---
_json_response_str = os.getenv("JSON_RESPONSE", "False").lower()
JSON_RESPONSE: bool = _json_response_str in ["true", "1", "t", "yes"] # JSON Response Mode

# --- Logging Configuration ---
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper() # Log Level

# --- Application Information ---
APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0_default") # Application Version

# --- Security/Auth Configuration ---
# Load valid API keys from a comma-separated environment variable
# Example in .env: ENV_VALID_API_KEYS="key1,key2,key3"
_raw_api_keys = os.getenv("ENV_VALID_API_KEYS", "")
VALID_API_KEYS: set[str] = set(key.strip() for key in _raw_api_keys.split(',') if key.strip())

if not VALID_API_KEYS and _raw_api_keys: # Log if env var was set but resulted in no keys (e.g. only commas)
    logger.warning(f"ENV_VALID_API_KEYS was set to '{_raw_api_keys}' but resulted in no valid API keys after parsing.")
elif not VALID_API_KEYS: # Log if env var was not set or was empty
    logger.info("ENV_VALID_API_KEYS is not set or is empty. No API keys loaded for APIKeyAuthStrategy.")


if __name__ == "__main__":
    print(f"Loaded Configuration:")
    print(f"  HOST: {HOST}")
    print(f"  PORT: {PORT}")
    print(f"  LOG_LEVEL: {LOG_LEVEL}")
    print(f"  SERVER_NAME: {SERVER_NAME}")
    print(f"  JSON_RESPONSE: {JSON_RESPONSE}")
    print(f"  APP_VERSION: {APP_VERSION}")
    print(f"  VALID_API_KEYS: {VALID_API_KEYS}")
