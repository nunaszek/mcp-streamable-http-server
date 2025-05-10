import logging
from typing import List
import importlib
import pkgutil
import inspect
import os # For path manipulation if needed
import sys # To adjust sys.path if strategies is not directly importable
from pathlib import Path

from .base import AuthStrategy
# Manual import of APIKeyAuthStrategy is removed for dynamic loading

logger = logging.getLogger(__name__)

_loaded_strategies: List[AuthStrategy] = []

def load_strategies() -> None:
    """
    Dynamically discovers and loads authentication strategies from the 'strategies' package.
    Strategies should be classes inheriting from AuthStrategy.
    """
    global _loaded_strategies
    _loaded_strategies = [] # Reset before loading

    # Determine the path to the 'strategies' package
    # Assumes 'strategies' is a top-level directory in the project root.
    # And project root is in sys.path (common with `python -m server.main` or similar)
    strategy_package_name = "strategies"

    try:
        package = importlib.import_module(strategy_package_name)
        logger.info(f"Looking for strategies in package: {strategy_package_name}")

        if not hasattr(package, '__path__'):
            logger.error(f"Package '{strategy_package_name}' does not have __path__ attribute. Is it a valid package with an __init__.py?")
            return

        prefix = package.__name__ + "."
        for _, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            if not ispkg:
                try:
                    module = importlib.import_module(modname)
                    logger.debug(f"Scanning module: {modname}")
                    for name, cls in inspect.getmembers(module, inspect.isclass):
                        # Check if it's a subclass of AuthStrategy and not AuthStrategy itself
                        # Also ensure it's defined in the current module, not imported from elsewhere (optional, but good practice)
                        if issubclass(cls, AuthStrategy) and cls is not AuthStrategy and cls.__module__ == modname:
                            try:
                                strategy_instance = cls()
                                if not any(isinstance(s, cls) for s in _loaded_strategies): # Avoid duplicates if loaded multiple times by mistake
                                    _loaded_strategies.append(strategy_instance)
                                    logger.info(f"Successfully loaded and instantiated strategy: {cls.__name__} from {modname}")
                                else:
                                    logger.debug(f"Strategy {cls.__name__} from {modname} already loaded.")
                            except Exception as e:
                                logger.error(f"Failed to instantiate strategy {cls.__name__} from {modname}: {e}", exc_info=True)
                except ImportError as e:
                    logger.error(f"Failed to import module {modname} while loading strategies: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"An unexpected error occurred while processing module {modname}: {e}", exc_info=True)
    except ImportError as e:
        logger.error(f"Could not import the strategies package '{strategy_package_name}'. Ensure it exists and is in Python's path: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during strategy discovery for package '{strategy_package_name}': {e}", exc_info=True)

    if not _loaded_strategies:
        logger.warning(
            "No authentication strategies were loaded. "
            "This might be because the 'strategies' package is empty, contains no valid strategies, "
            "or there was an error during loading. Authentication may be fully permissive or restrictive "
            "based on core.validate logic when no strategies are present."
        )
    else:
        logger.info(f"Finished loading authentication strategies. Total loaded: {len(_loaded_strategies)}")

def _get_loaded_strategies() -> List[AuthStrategy]:
    """Returns the list of loaded authentication strategies.
    This is an internal function for use within the auth package.
    """
    # Unlike before, load_strategies() is now typically called once at startup.
    # If _get_loaded_strategies() is called before load_strategies(), it will return an empty list,
    # which is handled by the core.validate function.
    return _loaded_strategies

# Note: load_strategies() should be called explicitly at server startup (e.g., in server/main.py).
# It is no longer called automatically when _get_loaded_strategies() is invoked with an empty list.

# Initial load when module is imported (can be deferred if needed)
# load_strategies() 
# Consider calling this explicitly at server startup, similar to tool_loader 