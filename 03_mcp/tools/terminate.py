from __future__ import annotations

from typing import Any

from .base import BaseTool


class TerminateTool(BaseTool):
    """终止 Agent Loop 并返回最终答案"""

    @property
    def name(self) -> str:
        return "terminate"

    @property
    def description(self) -> str:
        return "End the agent loop and return the final answer."

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "final": {
                    "type": "string",
                    "description": "The final answer to show the user before exiting.",
                }
            },
            "required": ["final"],
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        """执行终止操作"""
        final = str(kwargs.get("final", "")).strip()
        return True, final