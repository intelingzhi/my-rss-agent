from __future__ import annotations

from datetime import datetime

from .base import BaseTool

class DateTimeTool(BaseTool):
    """获取当前日期和时间"""

    @property
    def name(self) -> str:
        return "datetime"

    @property
    def description(self) -> str:
        return "Get the current date and time. Use this when you need to know the current time or date."

    def execute(self, **kwargs) -> tuple[bool, str]:
        """执行获取时间操作"""
        now = datetime.now()
        return False, now.strftime("%Y-%m-%d %H:%M:%S")