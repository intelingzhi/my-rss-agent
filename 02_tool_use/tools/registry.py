"""工具注册表 - 所有工具的集中管理"""

from .search import SearchTool
from .datetime import DateTimeTool
from .calculator import CalculatorTool
from .terminate import TerminateTool

# 工具实例
_search_tool = SearchTool()
_datetime_tool = DateTimeTool()
_calculator_tool = CalculatorTool()
_terminate_tool = TerminateTool()

# 工具注册表
TOOL_REGISTRY = {
    "search": _search_tool,
    "datetime": _datetime_tool,
    "calculator": _calculator_tool,
    "terminate": _terminate_tool,
}

# 使用方式
# tool = TOOL_REGISTRY.get(name)