from typing import Any

def terminate_schema() -> dict[str, Any]:
    """返回 terminate 工具的 schema 定义"""
    return {
        "type": "function",
        "function": {
            "name": "terminate",
            "description": "结束 Agent 循环并返回最终答案",
            "parameters": {
                "type": "object",
                "properties": {
                    "final": {
                        "type": "string",
                        "description": "要返回给用户的最终答案"
                    }
                },
                "required": ["final"]
            }
        }
    }


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """执行工具调用。返回 (是否终止, 输出文本)"""
    if name == "terminate":
        final = str(arguments.get("final", "")).strip()
        return True, final
    raise RuntimeError(f"未知工具: {name}")