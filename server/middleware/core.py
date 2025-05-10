from typing import Optional, Mapping
from pydantic import BaseModel
import logging

from . import loader # Import the loader to get middlewares

logger = logging.getLogger(__name__)

class RequestCredentialsContext(BaseModel):
    """Encapsulates all request-specific information needed for credential validation."""
    query_params: Mapping[str, str]
    headers: Mapping[str, str]
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

def validate(context: RequestCredentialsContext) -> bool:
    """
    Validates credentials by checking against all loaded authentication middlewares.
    If no middlewares are loaded, the request is allowed by default.
    Otherwise, all loaded middlewares must pass for the validation to be successful.

    Args:
        context: An object containing all relevant credential and request information.

    Returns:
        True if validation passes or no middlewares are loaded, False otherwise.
    """
    loaded_middlewares = loader._get_loaded_middlewares()

    if not loaded_middlewares:
        logger.warning(
            "Authentication is disabled or no middlewares are loaded. "
            "For secure deployments, ensure at least one middleware is configured and loaded."
        )
        return True # No middlewares to check, so validation passes

    for middleware in loaded_middlewares:
        try:
            if not middleware(context):
                logger.info(f"Auth middleware '{middleware}' failed for session: {context.session_id}, IP: {context.client_ip}")
                return False # If any middleware fails, overall validation fails
        except Exception as e:
            logger.error(f"Error executing auth middleware '{middleware}': {e}", exc_info=True)
            return False # Treat errors in a middleware as a validation failure
    
    logger.info(f"All auth middlewares passed for session: {context.session_id}, IP: {context.client_ip}")
    return True # All middlewares passed