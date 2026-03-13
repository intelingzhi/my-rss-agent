# 06 Context Engineering

这节课在上一课的基础上，引入了**上下文工程**，让 Agent 能够记住多轮对话历史，并通过压缩技术避免 token 爆炸。

## 运行

```bash
cd exercise

# 第一轮对话
uv run python 06_context_engineering/main.py --task "帮我写一个 Python 函数，计算斐波那契数列"

# 第二轮对话（记住上文）
uv run python 06_context_engineering/main.py --task "改成迭代版本"

# 多轮对话后观察压缩
uv run python 06_context_engineering/main.py --task "继续优化性能" --max-tokens 2000
```

## 目录结构

```
exercise/
├── lib/                    # 公共库
│   ├── env.py
│   ├── openai_compat.py
│   └── log.py
├── 06_context_engineering/
│   ├── agent.py            # Agent 核心逻辑（支持消息存储+压缩）
│   ├── main.py            # 入口
│   ├── messages.db        # SQLite 消息存储
│   ├── tools/             # 工具模块
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── search.py      # 搜索工具
│   │   └── terminate.py
│   └── message/           # 消息模块
│       ├── __init__.py
│       ├── message_store.py  # SQLite 存储
│       └── compression.py   # LLM 压缩
└── .env
```

## 核心功能

| 功能 | 说明 |
|------|------|
| **消息存储** | SQLite 持久化对话历史 |
| **压缩** | LLM 摘要压缩长对话 |
| **多轮对话** | Agent 记住之前聊了什么 |

## 技术栈

- **消息存储**: SQLite
- **压缩方式**: LLM 摘要（有损）

## 本课重点

- 上下文工程的三个概念：消息、记忆、压缩
- SQLite 消息存储
- LLM 摘要压缩
- RAG vs 上下文工程

## 观察压缩

运行带低阈值的命令观察压缩过程：

```bash
# 设置 max-tokens 200 强制触发压缩
uv run python 06_context_engineering/main.py --task "优化性能" --max-tokens 200
```

日志中会显示：
- `[压缩] 需要压缩！当前 374 tokens > 200 tokens`
- `[压缩] 压缩完成！374 tokens -> 15 tokens (节省 359 tokens)`
- `[压缩] 消息数量: 4 条 -> 3 条`

压缩后的消息会包含 `[历史摘要]` 作为 system 消息。