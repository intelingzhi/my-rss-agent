from .search import SearchTool
from .terminate import TerminateTool
from .mcp_client import load_mcp_tools

_search = SearchTool()
_terminate = TerminateTool()
# 加载 MCP 工具
mcp_tools = load_mcp_tools()
MCP_TOOL_REGISTRY = {
    "search": _search,
    "terminate": _terminate,
    **mcp_tools,
}