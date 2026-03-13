"""工具注册表"""

from .mcp_client import load_mcp_tools
from .skill import SkillTool
from .terminate import TerminateTool
from .webfetch import WebFetchTool

_terminate = TerminateTool()
_skill = SkillTool()
_webfetch = WebFetchTool()

mcp_tools = load_mcp_tools()

TOOL_REGISTRY = {
    "terminate": _terminate,
    "skill": _skill,
    "webfetch": _webfetch,
    **mcp_tools,
}