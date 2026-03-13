# 为什么需要 Skill
## 没有 Skill 的 Agent：一个全能但平庸的助手
- 什么问题都能回答，但什么都不精
- 每次都要手把手教，效率低
- 同一个任务反复说，浪费 token

## 有 Skill 的 Agent：一个指挥调度中心
- 遇到写代码 → 召唤"程序员 Agent"
- 遇到查资料 → 召唤"研究 Agent"
- 遇到画图 → 召唤"设计师 Agent"
- 每个 Skill 都是一个专业领域的 Agent



# Claude Skill 规范
Skill 是一种结构化的 Agent 能力封装，由 Anthropic 提出标准：
```markdown
---
name: code-review
description: Automated code review with security analysis
version: 1.0.0
author: "Your Name"
---

# Skill 主体

You are an expert code reviewer. When asked to review code:

1. First clone the repository
2. Run security scans
3. Provide detailed feedback on:
   - Security vulnerabilities
   - Code quality issues
   - Performance concerns
```

核心要素：
- YAML frontmatter - 元数据（name、description、version）
- Markdown body - 技能指令（system prompt）
- 可选的辅助文件 - 脚本、模板等

# Skill 加载机制
Skill 格式规范：
| 组成部分 | 说明 |
|----------|------|
| YAML frontmatter | 元数据（name、description、version） |
| Markdown body | Skill 主体（system prompt） |

```markdown
---
name: code-reviewer
description: Expert code reviewer
version: 1.0.0
---
# Skill 主体（在这之下）
```

# Skill 存储结构（Claude Code标准）
```

.claude/skills/  # codex的话，目录就是.codex
├── doc-writer/
│   └── SKILL.md
├── python-expert/
│   └── SKILL.md
└── github-info/
    └── SKILL.md
```


# Skill 功能

| 操作 | 作用 | 示例 |
|------|------|------|
| install | 从 GitHub 克隆 Skill | `skill install <repo_url>` |
| list | 列出已安装的 Skills | `skill list` |
| load | 加载 Skill 到上下文 | `skill load python-expert` |
| create | 创建自定义 Skill | `skill create my-skill` |