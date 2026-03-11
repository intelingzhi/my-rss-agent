# 01 Mini Agent Loop

这节课只做一件事：写出一个最小化 Agent Loop（只有一个工具 `terminate`）。

## 运行

从项目根目录运行：

```bash
uv run python 01_mini_agent_loop/main.py --task "用三句话解释什么是 Agent Loop"
```

默认日志输出到控制台，添加 `--log-dir` 参数可将日志写入文件：

```bash
uv run python 01_mini_agent_loop/main.py --task "解释AI" --log-dir logs
```

配置来自 `exercise/.env`：
- `OPENAI_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL` (OpenAI-compatible)

## 你会看到什么

运行后，控制台和日志文件都会打印完整的 Agent Loop 执行过程：

1. **Step 0: 初始上下文 (messages)** - 发送给 LLM 的完整消息列表
2. **Step 0: 可用工具 (tools)** - 工具的 schema 定义
3. **Step N: LLM 原始回复** - 模型返回的完整 JSON（含 reasoning_content）
4. **Step N: 调用工具** - 模型选择了哪个工具、传了什么参数
5. **Step N: 工具返回** - 工具执行后的结果
6. **最终答案** - Agent Loop 终止，输出结果

通过这些日志，读者可以清晰看到 Agent Loop 的每一个环节：LLM 是如何"思考"的、为什么会调用工具、工具返回后又是如何继续推理的。

## 目录结构

```
exercise/
├── lib/                    # 公共库（各课复用）
│   ├── env.py              # 环境变量加载
│   ├── openai_compat.py    # OpenAI 兼容 API
│   └── log.py              # 日志模块
├── 01_mini_agent_loop/
│   ├── agent.py            # Agent Loop 核心逻辑
│   ├── tools.py            # 工具定义和执行
│   └── main.py             # 入口
└── .env                    # API 配置
```

## 依赖

- `openai` - 标准 OpenAI Python 库
- `loguru` - 日志库（控制台打印 + 文件记录）
