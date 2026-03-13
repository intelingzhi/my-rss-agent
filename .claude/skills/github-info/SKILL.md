---
name: github-info
description: A custom skill
version: 1.0.0
---

# GitHub Info Skill

查看 GitHub 仓库信息的技能。

## 功能

这个 skill 提供了查看 GitHub 仓库各种信息的能力。

## 使用方法

### 1. 获取仓库基本信息

使用 `get_file_contents` 工具查看仓库的基本信息：

```python
get_file_contents(owner="仓库所有者", repo="仓库名称")
```

这将返回仓库的根目录内容。

### 2. 获取仓库的 commit 列表

```python
list_commits(owner="仓库所有者", repo="仓库名称", perPage=30)
```

### 3. 获取仓库的分支列表

```python
list_branches(owner="仓库所有者", repo="仓库名称")
```

### 4. 获取仓库的发布版本

```python
list_releases(owner="仓库所有者", repo="仓库名称")
```

### 5. 获取仓库的最新发布版本

```python
get_latest_release(owner="仓库所有者", repo="仓库名称")
```

### 6. 获取仓库的标签

```python
list_tags(owner="仓库所有者", repo="仓库名称")
```

### 7. 搜索仓库

```python
search_repositories(query="搜索关键词", sort="stars", order="desc")
```

### 8. 搜索代码

```python
search_code(query="搜索内容", repo="所有者/仓库")
```

### 9. 搜索用户

```python
search_users(query="用户名或名称")
```

## 常用查询示例

查看用户自己的信息：
```python
get_me()
```

查看特定 issue：
```python
issue_read(issue_number=1, method="get", owner="所有者", repo="仓库")
```

查看 pull request：
```python
pull_request_read(method="get", owner="所有者", pullNumber=1, repo="仓库")
```

## 注意事项

- 确保在使用前了解仓库的所有者和名称
- 使用适当的分页参数来处理大量数据
- 注意 API 调用限制