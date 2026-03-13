from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from loguru import logger

import httpx

from .base import BaseTool


def clone_skills_from_github(repo_url: str, target_dir: Path) -> dict[str, Any] | None:
    """
    从 GitHub 克隆指定仓库并加载skill文件，具体逻辑为：
        - 解析传入的 GitHub 仓库地址，提取用户名 / 仓库名并拼接成 API 请求地址；
        - 调用 GitHub API 获取仓库的克隆地址，通过 git 命令浅克隆（仅最新版本）到指定目录；
        - 若克隆成功则加载目标目录下的技能文件并返回结果，全程捕获异常，失败则返回 None。
    """
    if "github.com" in repo_url:
        # 去掉 repo_url 末尾的所有斜杠（/），防止多余的分隔符。
        parts = repo_url.rstrip("/").split("/")
        # 从 parts 中提取最后两个元素，即用户名和仓库名。
        repo = f"{parts[-2]}/{parts[-1]}"
    else:
        repo = repo_url

    # 构建 GitHub API 接口 URL，用于获取仓库信息。
    api_url = f"https://api.github.com/repos/{repo}"

    try:
        # 发送 GET 请求到 GitHub API，获取仓库信息。
        with httpx.Client(timeout=30) as client:
            resp = client.get(api_url)
            if resp.status_code != 200:
                raise Exception(f"Failed to get repo info from GitHub API: {resp.status_code} {resp.text}")
            
            # 解析响应 JSON 数据，提取仓库的 clone URL。
            repo_info = resp.json()
            clone_url = repo_info["clone_url"]

            # 执行 Git 克隆命令，将仓库内容克隆到指定目录。
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(target_dir)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise Exception(f"Failed to clone repo from GitHub: {result.stderr}")
            
            return load_skill_from_file(target_dir)
    except Exception:
        return None


def load_skill_from_file(skill_path: Path) -> dict[str, Any] | None:
    """
    从指定目录读取并解析 SKILL.md 文件，提取技能元信息，具体逻辑为：
        - 检查目标目录下是否存在 SKILL.md 文件，不存在则返回 None；
        - 读取文件内容，先默认以目录名作为技能名、空字符串为描述，文件全文为内容；
        - 若文件开头有 --- 分隔的前置元信息（frontmatter），则从中解析 name 和 description 字段（去除引号），剩余部分作为正文；
        - 最终返回包含技能名、描述、正文、路径的字典，解析失败 / 文件不存在时返回 None。
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text()

    # 先以目录名作为技能名、空字符串为描述，文件全文为内容
    name = skill_path.name
    description = ""
    body = content

    if content.startswith("---"):
        # 尝试解析前置元信息（frontmatter）
        # parts[0] 是空字符串，parts[1] 是元信息，parts[2] 是正文。
        parts = content.split("---", 2)

        # skill 文件格式正确，包含元信息和正文
        if len(parts) >= 3:
            frontmatter = parts[1]
            body = parts[2].strip()

            for line in frontmatter.split("\n"):
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"').strip("'")

    return {
        "name": name,
        "description": description,
        "body": body,
        "path": str(skill_path),
    }


def discover_skills(skills_dir: Path) -> list[dict[str, Any]]:
    """
    遍历指定目录下的所有子目录，批量加载并收集有效的skill信息
    """
    skills = []

    if not skills_dir.exists():
        return skills

    for item in skills_dir.iterdir():
        if item.is_dir():
            skill = load_skill_from_file(item)
            if skill:
                skills.append(skill)

    return skills


class SkillTool(BaseTool):
    def __init__(self):
        self.skills_dir = Path(__file__).parent.parent.parent / ".claude" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_skills: dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "skill"
    
    @property
    def description(self) -> str:
        return "Manage skills: install from GitHub, list installed skills, load a skill's instructions."

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: install, list, load, create",
                    "enum": ["install", "list", "load", "create"],
                },
                "repo_url": {
                    "type": "string",
                    "description": "GitHub repo URL for install",
                },
                "skill_name": {
                    "type": "string",
                    "description": "Name of skill to load or create",
                },
                "skill_content": {
                    "type": "string",
                    "description": "Skill content (markdown) for create",
                },
            },
            "required": ["action"],
        }
    
    def execute(self, **kwargs) -> tuple[bool, str]:
        """
        执行技能管理相关操作。

        Args:
            kwargs: 包含 action（install/list/load/create）及相关参数。

        Returns:
            tuple[bool, str]: (是否停止, 操作结果或错误信息)
        """
        action = kwargs.get("action", "")

        if action == "install":
            return self._install_skill(kwargs)
        elif action == "list":
            return self._list_skills(kwargs)
        elif action == "load":
            return self._load_skill(kwargs)
        elif action == "create":
            return self._create_skill(kwargs)
        else:
            return False, f"Unknown action: {action}"
        
    def _install_skill(self, kwargs: dict) -> tuple[bool, str]:
        """
        安装技能：从 GitHub 克隆指定仓库并加载 skill 文件，移动到技能目录。
        """
        repo_url = kwargs.get("repo_url", "")
        if not repo_url:
            return False, "Error: repo_url is required for install"

        with tempfile.TemporaryDirectory() as tmpdir:
            # 从 GitHub 克隆指定仓库并加载skill文件
            skill = clone_skills_from_github(repo_url, Path(tmpdir))

            if not skill:
                return False, f"Failed to install skill from {repo_url}"

            skill_name = skill["name"]
            target_dir = self.skills_dir / skill_name

            if target_dir.exists():
                shutil.rmtree(target_dir)   # 若目标目录已存在，先删除旧版本

            # 移动新克隆的 skill 目录到目标位置
            shutil.move(Path(tmpdir) / skill_name, target_dir)

            self._loaded_skills[skill_name] = skill
            return False, f"Skill '{skill_name}' installed successfully!"
        
    def _list_skills(self, kwargs: dict) -> tuple[bool, str]:
        """
        列出已安装技能：遍历技能目录，收集所有有效 skill 文件的元信息。
        """
        skills = discover_skills(self.skills_dir)

        if not skills:
            return False, "No skills installed. Use 'install' action to add skills."

        result = []
        for s in skills:
            result.append(f"- {s['name']}: {s['description']}")

        return False, "Installed skills:\n" + "\n".join(result)
    
    def _load_skill(self, kwargs: dict) -> tuple[bool, str]:
        """
        加载指定技能：根据技能名称查找技能目录并读取技能内容。
        """
        skill_name = kwargs.get("skill_name", "")
        if not skill_name:
            return False, "Error: skill_name is required for load"

        skill_path = self.skills_dir / skill_name
        if not skill_path.exists():
            return False, f"Skill '{skill_name}' not found."

        skill = load_skill_from_file(skill_path)
        if not skill:
            return False, f"Failed to load skill '{skill_name}'"

        self._loaded_skills[skill_name] = skill
        return False, f"Skill '{skill_name}' loaded!\n\nInstructions:\n{skill['body']}"

    def _create_skill(self, kwargs: dict) -> tuple[bool, str]:
        """
        创建自定义技能：根据技能名称和内容生成 skill 文件。
        """
        skill_name = kwargs.get("skill_name", "")
        content = kwargs.get("skill_content", "")

        if not skill_name or not content:
            return False, "Error: skill_name and skill_content are required for create"

        skill_dir = self.skills_dir / skill_name
        skill_dir.mkdir(exist_ok=True)

        # 生成 YAML frontmatter
        frontmatter = (
            f"---\n"
            f"name: {skill_name}\n"
            f"description: A custom skill\n"
            f"version: 1.0.0\n"
            f"---\n"
            f"\n"
            f"{content}"
        )

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(frontmatter)

        return False, f"Skill '{skill_name}' created at {skill_dir}"



























