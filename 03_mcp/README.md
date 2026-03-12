# 03 MCP

这节课在上一课的基础上，引入了 MCP（Model Context Protocol）概念。

## 运行

```bash
cd exercise
uv run python 03_mcp/main.py --task "python 教程"
```

```bash
uv run python 03_mcp/main.py --task "fastapi 教程"
```

## 目录结构

```
exercise/
├── lib/                    # 公共库
│   ├── env.py             # 环境变量加载
│   ├── openai_compat.py    # OpenAI 兼容 API
│   └── log.py             # 日志模块
├── 03_mcp/
│   ├── agent.py            # Agent 核心逻辑
│   ├── main.py            # 入口
│   └── tools/             # MCP 工具模块
│       ├── __init__.py     # 导出所有工具
│       ├── base.py        # BaseTool 基类
│       ├── terminate.py    # terminate 工具
│       ├── search.py      # search 工具 (Tavily)
│       ├── context7.py    # Context7 MCP 工具
│       └── registry.py    # MCP_TOOL_REGISTRY
└── .env                   # API 配置
```

## 工具设计

每个工具都继承 `BaseTool` 基类：

```python
class BaseTool(ABC):
    @property
    def name(self) -> str: ...      # 工具名称
    
    @property
    def description(self) -> str: ...  # 工具描述
    
    def execute(self, **kwargs) -> tuple[bool, str]: ...  # 执行逻辑
    
    def schema(self) -> dict: ...   # 生成 JSON Schema
```

### 工具列表

| 工具 | 作用 | 示例 |
|------|------|------|
| `search` | 网页搜索 (Tavily) | `search(query="python 教程")` |
| `context7_resolve-library-id` | 官方文档查询 (MCP) | 查库的使用方法 |
| `terminate` | 终止 Agent Loop | `terminate(final="答案")` |

## MCP 概念

MCP（Model Context Protocol）标准化了 Agent 与外部服务的连接方式：

- **MCP Server**：提供服务（如 Context7 文档服务）
- **MCP Client**：我们的工具代码，负责与 Server 通信
- **MCP Host**：Agent 本身

通过 MCP，Agent 可以即插即用地使用各种外部服务。

## 本课重点

- 理解 MCP 协议架构
- 实现 MCP 工具调用
- 工具注册机制（MCP_TOOL_REGISTRY）

## 依赖

- `tavily` - 网页搜索客户端
- `httpx` - HTTP 客户端（用于 MCP 调用）