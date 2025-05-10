from typing import Optional, Mapping
from pydantic import BaseModel
import logging

from . import loader # Import the loader to get strategies

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
    Validates credentials by checking against all loaded authentication strategies.
    If no strategies are loaded, the request is allowed by default.
    Otherwise, all loaded strategies must pass for the validation to be successful.

    Args:
        context: An object containing all relevant credential and request information.

    Returns:
        True if validation passes or no strategies are loaded, False otherwise.
    """
    loaded_strategies = loader._get_loaded_strategies()

    if not loaded_strategies:
        logger.warning(
            "No auth strategies loaded. Allowing request by default. "
            "For secure deployments, ensure at least one strategy is configured and loaded."
        )
        return True # Permissive by default if no strategies are configured

    for strategy in loaded_strategies:
        try:
            if not strategy(context):
                logger.info(f"Auth strategy '{strategy}' failed for session: {context.session_id}, IP: {context.client_ip}")
                return False # If any strategy fails, overall validation fails
        except Exception as e:
            logger.error(f"Error executing auth strategy '{strategy}': {e}", exc_info=True)
            return False # Treat errors in a strategy as a validation failure
    
    logger.debug(f"All {len(loaded_strategies)} auth strategies passed for session: {context.session_id}")
    return True # All strategies passed 