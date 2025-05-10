import logging
from typing import List
import importlib
import pkgutil
import inspect
import os # For path manipulation if needed
import sys # To adjust sys.path if middlewares is not directly importable
from pathlib import Path

from .base import McpMiddleware
# Manual import of APIKeyAuthMiddleware is removed for dynamic loading

logger = logging.getLogger(__name__)

_loaded_middlewares: List[McpMiddleware] = []
_initialized = False

def _discover_and_load_middlewares(middleware_dir: str = "server/middleware/middlewares"):
    global _loaded_middlewares, _initialized
    if _initialized:
        return

    # Middlewares should be classes inheriting from McpMiddleware.
    package_path = middleware_dir.replace("/", ".")

    if not os.path.exists(middleware_dir):
        logger.warning(f"Middlewares directory '{middleware_dir}' not found. No custom middlewares will be loaded.")
        _initialized = True
        return
    
    middleware_package_name = "middlewares"

    try:
        package = importlib.import_module(middleware_package_name, package=package_path)
        logger.info(f"Looking for middlewares in package: {package_path}.{middleware_package_name}")

        if not hasattr(package, '__path__'):
            logger.error(f"Package '{package_path}.{middleware_package_name}' does not have __path__ attribute. Is it a valid package with an __init__.py?")
            _initialized = True
            return

        for _, modname, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            if ispkg:
                continue 
            try:
                module = importlib.import_module(modname)
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a subclass of McpMiddleware and not McpMiddleware itself
                    # Also ensure the class is defined in the current module, not imported
                    if issubclass(cls, McpMiddleware) and cls is not McpMiddleware and cls.__module__ == modname:
                        if not any(isinstance(s, cls) for s in _loaded_middlewares): # Avoid duplicate loading
                            middleware_instance = cls()
                            # Here you could pass configuration to the middleware if needed
                            _loaded_middlewares.append(middleware_instance)
                            logger.info(f"Successfully loaded and instantiated middleware: {cls.__name__} from {modname}")
                        else:
                            logger.debug(f"Middleware {cls.__name__} from {modname} already loaded.")
            except ImportError as e:
                logger.error(f"Could not import module {modname}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Failed to instantiate middleware {cls.__name__} from {modname}: {e}", exc_info=True)

    except ImportError as e:
        logger.error(f"Could not import the middlewares package '{package_path}.{middleware_package_name}'. Ensure it exists and is in Python's path: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during middleware discovery for package '{package_path}.{middleware_package_name}': {e}", exc_info=True)
    finally:
        _initialized = True

    if not _loaded_middlewares:
        logger.warning("No authentication middlewares were loaded. This might be an issue if authentication is expected.")

def _get_loaded_middlewares() -> List[McpMiddleware]:
    if not _initialized:
        _discover_and_load_middlewares()
    return _loaded_middlewares

# Example to explicitly load during module initialization if needed:
# _discover_and_load_middlewares() 

# Note: _discover_and_load_middlewares() should be called explicitly at server startup (e.g., in server/main.py).
# It is no longer called automatically when _get_loaded_middlewares() is invoked with an empty list.

# Initial load when module is imported (can be deferred if needed)
# _discover_and_load_middlewares()
# Consider calling this explicitly at server startup, similar to tool_loader 