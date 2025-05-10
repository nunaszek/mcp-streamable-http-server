import importlib
import logging
import os
from pathlib import Path
import sys

import yaml
import mcp.types as types

# Import BaseTool and inspect for class discovery
from server.tool.base import BaseTool
import inspect

# Import for schema validation
from pydantic import ValidationError
from .validator import ToolDefinitionConfig

logger = logging.getLogger(__name__) # 通常配置为 'server.tool.loader'

_loaded_tools_registry = {}

def _to_pascal_case(text: str) -> str:
    """Converts snake_case or kebab-case text to PascalCase."""
    if not text:
        return ""
    # Replace hyphens and underscores with spaces, then title case, then remove spaces.
    s = text.replace('-', ' ').replace('_', ' ')
    s = s.title().replace(' ', '')
    return s

def load_tools_from_directory(directory: str | Path):
    """
    Loads tool definitions from YAML files in the specified directory 
    and instantiates their corresponding handler classes.
    """
    global _loaded_tools_registry
    _loaded_tools_registry = {}

    if isinstance(directory, str):
        directory = Path(directory)

    if not directory.is_dir():
        logger.error(f"Tool definition directory (YAMLs) not found: {directory}")
        return

    project_root_dir = directory.parent.resolve()
    if str(project_root_dir) not in sys.path:
        sys.path.insert(0, str(project_root_dir))

    for yaml_file in directory.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                tool_config_raw = yaml.safe_load(f)

            if not isinstance(tool_config_raw, dict):
                logger.warning(f"Skipping invalid tool config file (not a dict): {yaml_file}")
                continue
            
            # Validate the loaded YAML data against the schema
            try:
                tool_config = ToolDefinitionConfig.model_validate(tool_config_raw)
            except ValidationError as e:
                logger.error(f"Invalid tool configuration in {yaml_file}. Schema validation failed: {e}")
                continue

            handler_file_path = Path(tool_config.source)
            file_stem = handler_file_path.stem
            expected_class_name = _to_pascal_case(file_stem)
            
            # Construct module path from handler_file_path relative to project root
            # e.g., tools/my_handler.py -> tools.my_handler
            # Assumes handler_file_path_str is like "tools/my_handler.py"
            module_path_parts = list(handler_file_path.parent.parts)
            if not module_path_parts or module_path_parts[0] == ".": # handle relative paths like ./tools/file.py
                 module_path_parts = module_path_parts[1:]
            module_path_parts.append(file_stem)
            handler_module_name = ".".join(module_path_parts)

            tool_definition_obj = types.Tool(
                name=tool_config.name,
                description=tool_config.description,
                inputSchema=tool_config.inputSchema,
            )

            try:
                module = importlib.import_module(handler_module_name)
                
                # Find the class that inherits from BaseTool
                FoundToolClass = None
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                        if FoundToolClass is not None:
                            pass # Continue using the first one found, without logging a warning
                        else: # First one found
                            FoundToolClass = obj
                
                if FoundToolClass is None:
                    logger.error(
                        f"No class inheriting from BaseTool found in module '{handler_module_name}' "
                        f"for tool '{tool_config.name}' from {yaml_file}. Searched for subclasses of BaseTool."
                    )
                    continue
                
                tool_instance = FoundToolClass()

                if not hasattr(tool_instance, "invoke") or not callable(getattr(tool_instance, "invoke")):
                    logger.error(
                        f"Tool class '{FoundToolClass.__name__}' in module '{handler_module_name}' "
                        f"does not have a callable 'invoke' method (usually provided by BaseTool)."
                    )
                    continue

                if tool_config.name in _loaded_tools_registry:
                    logger.warning(
                        f"Tool name '{tool_config.name}' is duplicated. Definition from {yaml_file} will overwrite previous."
                    )
                
                _loaded_tools_registry[tool_config.name] = {
                    "tool_definition": tool_definition_obj,
                    "instance": tool_instance,
                }

            except ImportError as e:
                logger.error(
                    f"Failed to import module '{handler_module_name}' for tool '{tool_config.name}' from {yaml_file}: {e}"
                )
            except AttributeError as e:
                logger.error(
                    f"Failed to find or instantiate class for tool '{tool_config.name}' in module '{handler_module_name}' from {yaml_file}: {e}"
                )
            except Exception as e:
                # Use tool_config.name if available, otherwise a generic message
                tool_name_for_error = tool_config.name if tool_config and hasattr(tool_config, 'name') else "<unknown tool>"
                # Corrected f-string for class name when FoundToolClass might be None
                class_name_str = FoundToolClass.__name__ if FoundToolClass else "<unknown class>"
                logger.error(
                    f"Error instantiating tool class '{class_name_str}' for tool '{tool_name_for_error}' from {yaml_file}: {e}",
                    exc_info=True
                )
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading tool from {yaml_file}: {e}", exc_info=True)

def get_tool_definitions() -> list[types.Tool]:
    return [details["tool_definition"] for details in _loaded_tools_registry.values()]

def get_tool_instance(tool_name: str):
    tool_info = _loaded_tools_registry.get(tool_name)
    if tool_info:
        return tool_info["instance"]
    logger.warning(f"Tool instance for '{tool_name}' not found.")
    return None 