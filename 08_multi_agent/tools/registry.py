from .base import BaseTool
from .terminate import TerminateTool

_terminate = TerminateTool()

TOOL_REGISTRY = {
   "terminate": _terminate,
}