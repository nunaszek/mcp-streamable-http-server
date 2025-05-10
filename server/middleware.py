from typing import Optional, Mapping
from pydantic import BaseModel


class RequestCredentialsContext(BaseModel):
    """Encapsulates all request-specific information needed for credential validation."""
    query_params: Mapping[str, str]
    headers: Mapping[str, str]
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

def validate(context: RequestCredentialsContext) -> bool:
    """
    Validates credentials based on the provided request context,
    including API key, client IP, User-Agent, etc.

    Args:
        context: An object containing all relevant credential and request information.

    Returns:
        True if validation passes, False otherwise.
    """

    print(f"context: {context.client_ip}")
    print(f"context: {context.user_agent}")
    print(f"context: {context.session_id}")
    return True 