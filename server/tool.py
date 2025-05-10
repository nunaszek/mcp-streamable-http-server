import mcp.types as types

REGISTERED_TOOLS: list[types.Tool] = []

def generate_tool_schema(
    func_obj: callable,
    tool_name: str,
    input_parameters: dict | None = None,
    required_parameters: list[str] | None = None
) -> types.Tool:
    """
    从给定的函数生成一个 types.Tool 对象。

    Args:
        func_obj: 用于生成工具定义的函数。
                  其文档字符串的第一行将用作工具描述。
        tool_name: 工具的名称。
        input_parameters: 一个描述 inputSchema 'properties' 的字典。
                          示例: {"param_name": {"type": "string", "description": "..."}}
        required_parameters: 必需参数的名称列表。

    Returns:
        一个 types.Tool 对象。
    """
    if not func_obj.__doc__:
        raise ValueError(f"函数 '{func_obj.__name__}' 必须有文档字符串以提取描述。")

    # 使用文档字符串的第一个非空行作为描述
    docstring_lines = func_obj.__doc__.strip().split('\n')
    description = ""
    for line in docstring_lines:
        stripped_line = line.strip()
        if stripped_line:
            description = stripped_line
            break

    if not description:
        raise ValueError(f"无法从函数 '{func_obj.__name__}' 的文档字符串中提取描述。")

    schema_properties = input_parameters if input_parameters is not None else {}
    current_input_schema = {
        "type": "object",
        "properties": schema_properties
    }

    if required_parameters:
        current_input_schema["required"] = required_parameters
    # 如果存在属性但未提供必需参数列表，则不添加 "required" 字段
    # (除非属性列表为空，这种情况下 "required" 字段通常被省略)

    return types.Tool(
        name=tool_name,
        description=description,
        inputSchema=current_input_schema
    )

def register_tool(
    tool_name: str,
    input_parameters: dict | None = None,
    required_parameters: list[str] | None = None
):
    """
    一个装饰器，用于将函数注册为一个工具，并根据其文档字符串和参数生成 schema。
    """
    def decorator(func: callable) -> callable:
        tool_definition = generate_tool_schema(
            func_obj=func,
            tool_name=tool_name,
            input_parameters=input_parameters,
            required_parameters=required_parameters
        )
        REGISTERED_TOOLS.append(tool_definition)
        return func  # 返回原始函数
    return decorator
