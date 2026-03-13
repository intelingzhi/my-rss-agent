from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from .base import BaseTool


def load_mcp_servers(config_path: str | Path | None = None) -> list[dict[str, Any]]:
    """
    读取json配置文件加载 MCP 服务器配置列表。
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "mcp_servers.json"

    config_path = Path(config_path)
    if not config_path.exists():
        return []

    with open(config_path) as f:
        data = json.load(f)
    return data.get("mcp_servers", [])


class MCPServer:
    def __init__(
        self,
        name: str,
        url: str,
        description: str = "",
        env_key: str = "",
        accept: str = "",
        auth_header: str = "",
    ):
        """
        初始化 MCPServer 实例。

        Args:
            name (str): 服务器名称。
            url (str): 服务器接口 URL。
            description (str): 服务器描述信息。
            env_key (str): 用于读取 API key 的环境变量名。
            accept (str): Accept 请求头，指定响应格式，默认 "application/json, text/event-stream"。
            auth_header (str): 授权头类型（如 "Bearer"），用于特殊认证场景。
        """
        self.name = name
        self.url = url
        self.description = description
        self.env_key = env_key
        self.accept = accept or "application/json, text/event-stream"
        self.auth_header = auth_header  # e.g., "Bearer" for GitHub MCP
        self._tools: list[dict[str, Any]] | None = None


    def _get_api_key(self) -> str:
        """
        从环境变量中获取的 API key，或空字符串。
        """
        if self.env_key:
            return os.getenv(self.env_key, "")
        return ""
    

    def _get_headers(self) -> dict[str, str]:
        """
        构建 HTTP 请求头，包含 Accept 和 Authorization（如果有）。
        """
        headers = {
            "Accept": self.accept,
        }
        api_key = self._get_api_key()
        if api_key:
            # 如果配置了 self.auth_header（自定义认证头格式），则使用该格式
            if self.auth_header:
                # Custom auth header format (e.g., "Bearer <token>")
                headers["Authorization"] = f"{self.auth_header} {api_key}"
                # 否则，将 env_key 作为头名（用于旧版 MCP 服务器）
            elif self.env_key:
                # Fallback: use env_key as header name (for backward compatibility)
                headers[self.env_key] = api_key
        return headers
    

    def _parse_response(self, resp: httpx.Response) -> dict[str, Any]:
        """解析 MCP 响应，支持 JSON 和 SSE 格式。"""
        content = resp.text.strip()

        # Check if it's SSE format (starts with "event:")
        if content.startswith("event:"):
            # Parse SSE: extract JSON from "data:" field
            for line in content.split("\n"):
                if line.startswith("data:"):
                    json_str = line[5:].strip()  # Remove "data:" prefix
                    return json.loads(json_str)

        # Standard JSON response
        return resp.json()
    

    def list_tools(self) -> list[dict[str, Any]]:
        """
        获取 MCPServer 支持的工具列表，逻辑如下：
        1. 如果 _tools 已缓存，直接返回。
        2. 从环境变量获取 API key。
        3. 如果没有 API key，返回空列表。
        4. 发送 POST 请求到 /tools/list 接口。
        5. 解析响应，提取 tools 字段。
        6. 缓存 tools 列表并返回。
        """
        if self._tools is not None:
            return self._tools

        api_key = self._get_api_key()
        if not api_key:
            return []

        try:
            with httpx.Client(headers=self._get_headers(), timeout=30.0) as client:
                resp = client.post(
                    self.url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {},
                    },
                )
                result = self._parse_response(resp)

                if "result" in result and "tools" in result["result"]:
                    self._tools = result["result"]["tools"]
                    return self._tools or []
        except Exception:
            pass

        return []
    
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        调用 MCPServer 的工具接口，发送 POST 请求到 /tools/call，参数包含工具名称和调用参数，返回解析后的响应结果。
        """
        api_key = self._get_api_key()
        if not api_key:
            return {"error": "No API key configured"}

        headers = self._get_headers()

        with httpx.Client(headers=headers, timeout=30.0) as client:
            resp = client.post(
                self.url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments,
                    },
                },
            )
            return self._parse_response(resp)
        

class MCPTool(BaseTool):
    def __init__(self, server: MCPServer, tool_schema: dict[str, Any]):
        self.server = server
        self._schema = tool_schema

    @property
    def name(self) -> str:
        return self._schema.get("name", "")

    @property
    def description(self) -> str:
        return self._schema.get("description", "")

    def _parameters_schema(self) -> dict[str, Any]:
        """
        构建工具调用的参数 JSON Schema，包含类型、属性和必填项。
        这里的正确与否，将会影响到大模型是否能获取到工具对应的参数。
        """
        input_schema = self._schema.get("inputSchema", {})
        return {
            "type": "object",
            "properties": input_schema.get("properties", {}),
            "required": input_schema.get("required", []),
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        """
        执行工具调用，发送请求到 MCPServer 并处理响应结果。
        """
        try:
            result = self.server.call_tool(self.name, kwargs)

            if "result" in result:
                content = result["result"].get("content", [])
                if content and content[0].get("type") == "text":
                    return False, content[0].get("text", "")

            if "error" in result:
                return False, f"MCP error: {result['error']}"

            return False, str(result)
        except Exception as e:
            return False, f"Error: {str(e)}"


def load_mcp_tools() -> dict[str, BaseTool]:
    from env import find_and_load_env

    find_and_load_env()

    servers = load_mcp_servers()
    tools: dict[str, BaseTool] = {}

    for server_config in servers:
        server = MCPServer(
            name=server_config["name"],
            url=server_config["url"],
            description=server_config.get("description", ""),
            env_key=server_config.get("env_key", ""),
            accept=server_config.get("accept", ""),
            auth_header=server_config.get("auth_header", ""),
        )

        tool_schemas = server.list_tools()
        for schema in tool_schemas:
            tool = MCPTool(server, schema)
            tools[tool.name] = tool

    return tools

