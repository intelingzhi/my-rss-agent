from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import httpx

from .base import BaseTool


def load_mcp_servers(config_path: str | Path | None = None) -> list[dict[str, Any]]:
    """
    加载 MCP 服务器配置列表。

    Args:
        config_path (str | Path | None): 配置文件路径，默认为项目根目录下的 mcp_servers.json。

    Returns:
        list[dict[str, Any]]: MCP 服务器信息的字典列表。如果文件不存在或无内容，返回空列表。
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "mcp_servers.json"

    config_path = Path(config_path)
    if not config_path.exists():
        return []

    with open(config_path) as f:
        data = json.load(f)
    return data.get("mcp_servers", [])



# MCP 集成的核心，负责和远程 MCP 服务器做 HTTP 通信
class MCPServer:
    def __init__(self, name: str, url: str, description: str = "", env_key: str = ""):
        """
        初始化 MCPServer 实例。

        Args:
            name (str): 服务器名称。
            url (str): 服务器接口 URL。
            description (str): 服务器描述。
            env_key (str): API key 的环境变量名。
        """
        self.name = name
        self.url = url
        self.description = description
        self.env_key = env_key
        self._tools: list[dict[str, Any]] | None = None

        """
        "mcp_servers": [
            {
            "name": "context7",
            "url": "https://mcp.context7.com/mcp",
            "description": "Query official documentation",
            "env_key": "CONTEXT7_API_KEY"
            }
        ]
        """

    def _get_api_key(self) -> str:
        """
        获取当前 MCPServer 的 API 密钥。

        Returns:
            str: 从环境变量中读取的 API 密钥，如果未设置则返回空字符串。
        """

        if self.env_key:
            return os.getenv(self.env_key, "") 
        return ""


    def list_tools(self) -> list[dict[str, Any]]:
        """
        获取当前 MCPServer 支持的工具列表。

        Returns:
            list[dict[str, Any]]: 工具信息的字典列表。
        """

        # 如果定义了工具列表，直接返回
        if self._tools is not None:
            return self._tools
        
        api_key = self._get_api_key()
        if not api_key:
            return []
        
        # 构造 HTTP 请求的 headers（请求头），用于访问 MCPServer 的接口。
        headers = {
            self.env_key: api_key,
            "Accept": "application/json, text/event-stream"
        }

        try:
            # 创建一个 HTTP 客户端，类似浏览器，用于发送 HTTP 请求
            with httpx.Client(headers=headers, timeout=30.0) as client:
                # 发一个 HTTP POST 请求，获取工具列表
                resp = client.post(
                    self.url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {}
                    },
                )
                result = resp.json()

                if "result" in result and "tools" in result["result"]:
                    self._tools = result["result"]["tools"]
                    return self._tools or []

        except Exception as e:
            raise RuntimeError(f"Failed to list tools from {self.name}: {e}")
        return []


        
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        调用指定的工具。

        Args:
            tool_name (str): 要调用的工具名称。
            arguments (dict[str, Any]): 工具调用的参数。

        Returns:
            dict[str, Any]: 工具调用的结果。
        """

        api_key = self._get_api_key()
        if not api_key:
            raise ValueError(f"API key for {self.name} is not set.")
        
        headers = {
            self.env_key: api_key,
            "Accept": "application/json, text/event-stream"
        }

        
        with httpx.Client(headers=headers, timeout=30.0) as client:
            resp = client.post(
                self.url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",  
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                },
            )
            return resp.json()



class MCPTool(BaseTool):
    def __init__(self, server: MCPServer, tool_schema: dict[str, Any]):
        """
        初始化 MCPTool 实例。

        Args:
            server (MCPServer): 所属的 MCPServer。
            tool_schema (dict[str, Any]): 工具的 schema 信息。
        """
        self.server = server
        self._schema = tool_schema

    @property
    def name(self) -> str:
        """
        工具名称。
        Returns:
            str: 工具名称。
        """
        return self._schema.get("name", "")
    
    @property
    def description(self) -> str:
        """
        工具描述。
        Returns:
            str: 工具描述。
        """
        return self._schema.get("description", "")
    
    def _parameters_schema(self) -> dict[str, Any]:
        """
        生成传给 OpenAI API 的 tools 参数格式，告诉 LLM 这个工具接受什么参数

        Args:
            arguments (str): 参数字符串。

        Returns:
            dict[str, Any]: 参数 schema 字典。
        """
        """
        解析工具调用的参数字符串为字典。
        """
        input_schema = self._schema.get("inputSchema", {})
        return {
            "type": "object",
            "properties": input_schema.get("properties", {}),
            "required": input_schema.get("required", []),
        }
    

    def execute(self, **kwargs) -> tuple[bool, str]:
        """
        真正去调用工具，并把结果整理成统一格式返回。

        Args:
            kwargs: 工具调用参数。

        Returns:
            tuple[bool, str]: (是否停止, 工具返回内容)
        """
        try:
            # 向 MCP 服务器发送请求，告诉它："帮我执行工具 xxx，参数是 kwargs"。这一步是真正发生网络/进程通信的地方。
            result = self.server.call_tool(self.name, kwargs)

            # MCP 协议规定，工具执行成功时返回的结构大概长这样：
            # 这个嵌套结构 result → content → [{type, text}] 也是 MCP 协议规定的返回格式，不是随意设计的。
            # """"
            # {
            #     "result": {
            #         "content": [
            #             { "type": "text", "text": "今天天气晴，25°C" }
            #         ]
            #     }
            # }
            # """

            if "result" in result:
                content = result["result"].get("content", [])
                if content and content[0].get("type") == "text":
                    return False, content[0].get("text", "")

            # 如果服务器返回了错误，把错误信息包装成字符串返回。
            if "error" in result:
                return False, f"MCP error: {result['error']}"

            return False, str(result)
        except Exception as e:
            return False, f"Error: {str(e)}"
        

def load_mcp_tools() -> dict[str, BaseTool]:
    """
    启动时自动发现并注册所有 MCP 服务器上的工具，统一收集到一个 tools 字典里供 agent 使用。
    有了这个：
    - agent 不需要知道工具在哪个服务器上，只管从 tools 字典里按名字取用
    - 新增 MCP 服务器只需改配置，agent 代码不用改
    - 不同服务器的工具都被包装成同一个 MCPTool 类，调用方式一致
    - list_tools() 是 MCP 协议规定的标准接口，任何 MCP 服务器都必须实现它

    Returns:
        dict[str, BaseTool]: 工具名称到工具对象的映射。
    """
    from env import find_and_load_env
    find_and_load_env()


    # 加载服务器配置列表
    # 从配置文件（比如 mcp_servers.json）中读取所有 MCP 服务器的信息，每一项大概长这样：
    # { "name": "weather", "url": "http://localhost:8001", "env_key": "WEATHER_API_KEY" }

    servers = load_mcp_servers()
    tools: dict[str, BaseTool] = {}

    # 遍历每个服务器，注册工具
    for server_config in servers:
        # 创建服务器连接对象
        
        server = MCPServer(
            name=server_config["name"],
            url=server_config["url"],
            description=server_config.get("description", ""),
            env_key=server_config.get("env_key", ""),
        )
        # 获取服务器上的所有工具 schema
        tool_schemas = server.list_tools()

        for schema in tool_schemas:
            tool = MCPTool(server, schema)  # 把每个工具包装成统一的对象
            tools[tool.name] = tool  # 存入字典，key 是工具名

    return tools
