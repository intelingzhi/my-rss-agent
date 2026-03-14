from __future__ import annotations

from typing import Any

from .base import BaseTool


class TerminateTool(BaseTool):
    @property
    def name(self) -> str:
        return "terminate"
    
    @property
    def description(self) -> str:
        return """终止 Agent Loop。

当任务已完成时调用此工具，将最终答案返回给用户。
传入 'final' 参数作为最终答案。"""    

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "final": {
                    "type": "string",
                    "description": "最终答案",
                },
            },
            "required": ["final"],
        }
    
    def execute(self, **kwargs: Any) -> tuple[bool, str]:
        """执行终止 Agent Loop"""
        final_answer = kwargs.get("final", "")
        return True, final_answer
