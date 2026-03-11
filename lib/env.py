from __future__ import annotations

import os
from pathlib import Path


def _strip_quotes(s: str) -> str:
    """
    去除字符串两端的单引号或双引号。

    Args:
        s (str): 输入字符串。

    Returns:
        str: 去除引号后的字符串，如果没有引号则原样返回。
    """
    s = s.strip()
    if len(s) >= 2 and (
        (s[0] == "'" and s[-1] == "'") or (s[0] == '"' and s[-1] == '"')
    ):
        return s[1:-1]
    return s


def load_dotenv_if_present(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)  # 1 表示只按第一个等号分割
        key = key.strip()
        value = _strip_quotes(value.strip())

        # 如果 key 不为空且当前环境变量中没有这个 key，就把 key 和 value 加入到环境变量 os.environ 中
        # 也就是只有第一个有效，后面的会被忽略
        if key and key not in os.environ:
            os.environ[key] = value


def find_and_load_env() -> None:
    # 获取当前脚本所在目录
    here = Path(__file__).resolve()

    # 构建候选 .env 文件路径列表
    candidates = [
        here.parent / ".env",  # 脚本所在目录的 .env 文件
        Path.cwd() / ".env",   # 当前工作目录的 .env 文件
    ]
    for p in candidates:
        load_dotenv_if_present(p)