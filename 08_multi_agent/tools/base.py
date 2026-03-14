from __future__ import annotations


from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """工具的名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具的描述"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> tuple[bool, str]:
        """
        执行工具

        Returns:
            (should_stop, result): 是否终止 Agent Loop，结果字符串
        """
        pass

    def schema(self) -> dict[str, Any]:
        """返回工具的 JSON Schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._parameters_schema(),
            },
        }
    

    def _parameters_schema(self) -> dict[str, Any]:
        """返回参数的 JSON Schema"""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }
    
