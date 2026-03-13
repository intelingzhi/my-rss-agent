# 04 Skills

这节课在上一课的基础上，引入了 **Skill** 概念，让 Agent 能够召唤其他专业 Agent。

## 运行

```bash
cd exercise

# 列出已安装的 skills
uv run python 04_skills/main.py --task "列出已安装的 skills"

# 创建一个 skill
uv run python 04_skills/main.py --task "创建一个 skill，名为 doc-writer"

# 查看所有可用的 MCP 工具
uv run python 04_skills/main.py --task "列出所有可用的MCP工具"

# 创建并使用 GitHub MCP skill（进阶）
uv run python 04_skills/main.py --task "创建一个名为 github-info 的 skill，功能是查看 GitHub 仓库信息"
uv run python 04_skills/main.py --task "加载 github-info skill，然后查看 facebook/react 仓库的基本信息"
```

## 目录结构

```
exercise/
├── lib/                    # 公共库
│   ├── env.py
│   ├── openai_compat.py
│   └── log.py
├── .claude/
│   └── skills/            # 安装的 Skills
│       ├── doc-writer/
│       │   └── SKILL.md
│       └── github-info/
│           └── SKILL.md
├── 04_skills/
│   ├── agent.py            # Agent 核心逻辑（支持 Skill）
│   ├── main.py            # 入口
│   ├── mcp_servers.json  # MCP 服务器配置
│   └── tools/             # 工具模块
│       ├── base.py
│       ├── mcp_client.py  # MCP 客户端（支持 SSE）
│       ├── registry.py
│       ├── skill.py       # Skill 管理工具
│       ├── terminate.py
│       └── webfetch.py
└── .env
```

## Skill 工具

| 操作 | 说明 |
|------|------|
| `skill(action="install", repo_url="...")` | 从 GitHub 安装 Skill |
| `skill(action="list")` | 列出已安装的 Skills |
| `skill(action="load", skill_name="...")` | 加载 Skill 到上下文 |
| `skill(action="create", skill_name="...", skill_content="...")` | 创建 Skill |

## Skill 格式

```yaml
---
name: code-reviewer
description: Expert code reviewer
version: 1.0.0
---

# Skill 主体指令
You are an expert code reviewer...

When reviewing code:
1. Check security
2. Check performance
3. Provide suggestions
```

## MCP 服务器

| 服务器 | 工具数 | 功能 |
|--------|--------|------|
| **Context7** | 2 | 文档查询（resolve-library-id, query-docs） |
| **GitHub** | 40 | 代码操作（get_file_contents, list_branches, search_repositories 等） |

### GitHub MCP 工具示例

- `get_file_contents` - 获取仓库文件/目录内容
- `list_branches` - 列出仓库分支
- `list_commits` - 获取提交历史
- `search_repositories` - 搜索仓库
- `create_pull_request` - 创建 PR
- `issue_read` / `issue_write` - 管理 Issues
- 等等...

## 本课重点

- Skill 与 MCP 的区别
- Skill 加载机制
- 多 Agent 协作模式
- Skill + MCP 联动（Skill 调用 MCP 工具）