# 02 Tool Use

这节课在上一课的基础上，给 Agent 增加了真正的工具：搜索、查时间、算数学。

## 运行

```bash
cd exercise
uv run python 02_tool_use/main.py --task "python 教程"
```

```bash
uv run python 02_tool_use/main.py --task "现在几点了？"
```

```bash
uv run python 02_tool_use/main.py --task "2 的 10 次方是多少？"
```

## 目录结构

```
exercise/
├── lib/                    # 公共库
│   ├── env.py             # 环境变量加载
│   ├── openai_compat.py    # OpenAI 兼容 API
│   └── log.py             # 日志模块
├── 02_tool_use/
│   ├── agent.py            # Agent 核心逻辑
│   ├── main.py            # 入口
│   └── tools/             # 工具模块
│       ├── __init__.py     # 导出所有工具
│       ├── base.py        # BaseTool 基类
│       ├── terminate.py    # terminate 工具
│       ├── datetime.py    # datetime 工具
│       ├── calculator.py  # calculator 工具
│       └── search.py      # search 工具
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
| `datetime` | 获取当前时间 | `datetime()` |
| `calculator` | 数学计算 | `calculator(expression="2**10")` |
| `terminate` | 终止 Agent Loop | `terminate(final="答案")` |

## 本课重点

- 如何定义工具的 schema（描述、参数）
- 如何实现工具执行器
- 如何让 Agent 学会"调用工具"

## 依赖

- `tavily` - 网页搜索客户端