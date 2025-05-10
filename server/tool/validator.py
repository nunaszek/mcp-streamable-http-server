from pydantic import BaseModel
from typing import Dict, Any

class ToolDefinitionConfig(BaseModel):
    """
    Defines the expected schema for a tool's YAML configuration file.
    """
    name: str
    description: str
    inputSchema: Dict[str, Any] # Defines the structure for tool inputs
    source: str # Path to the tool's Python handler file

    # Pydantic will automatically validate that these fields are present
    # and of the correct type when a dictionary is parsed into this model. 