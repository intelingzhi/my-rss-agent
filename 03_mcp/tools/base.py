from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """工具的基类"""

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
    def execute(self, **kwargs: Any) -> tuple[bool, str]:
        """执行工具的操作

        Args:
            **kwargs: 关键字参数

        Returns:
            tuple[bool, str]: 第一个元素为是否执行成功，第二个元素为执行结果或错误信息
        """
        pass


    def schema(self) -> dict[str, Any]:
        """返回工具的 JSON 模式

        Returns:
            dict[str, Any]: 工具的 JSON 模式
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._parameters_schema(),
            },
        }


    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }
