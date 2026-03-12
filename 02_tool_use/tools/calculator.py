from __future__ import annotations


import math
import re
from typing import Any

from .base import BaseTool


class CalculatorTool(BaseTool):
    """ 一个简单的计算器工具 """

    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "计算数学表达式。使用 '**' 表示乘方，例如 '2**10' 表示 2 的 10 次方。"
    
    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression like '2 + 2', '2**10', 'sqrt(16)'.",
                }
            },
            "required": ["expression"],
        }
    
    def execute(self, **kwargs) -> tuple[bool, str]:
        """执行数学计算"""
        expression = kwargs.get("expression", "")

        # 安全检查：只允许数字和运算符
        allowed_chars = set("0123456789+-*/.() sqrtcosintanlogexppow^ ")
        if not all(c in allowed_chars for c in expression):
            return False, f"Error: Invalid characters in expression: {expression}"

        try:
            # 替换常见函数名和运算符
            expr = expression
            expr = re.sub(r"\bsqrt\b", "math.sqrt", expr)
            expr = re.sub(r"\bcos\b", "math.cos", expr)
            expr = re.sub(r"\bsin\b", "math.sin", expr)
            expr = re.sub(r"\btan\b", "math.tan", expr)
            expr = re.sub(r"\bint\b", "int", expr)
            expr = re.sub(r"\blog\b", "math.log", expr)
            expr = re.sub(r"\bexp\b", "math.exp", expr)
            expr = re.sub(r"\bpi\b", "math.pi", expr)
            expr = re.sub(r"\bpow\b", "math.pow", expr)
            # 替换 ^ 为 **
            expr = expr.replace("^", "**")

            result = eval(expr, {"__builtins__": {}}, {"math": math})
            return False, str(result)
        except Exception as e:
            return False, f"Error: {str(e)}"