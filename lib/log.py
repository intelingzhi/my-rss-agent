from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

from loguru import logger

def init_logger(log_dir: Path | str | None = None, level: str = "INFO") -> None:
    # 移除默认处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level: <8} | {message}",
        level=level,
    )

    # 文件输出
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件名使用时间戳，避免覆盖
        from datetime import datetime

        log_file = log_dir / f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logger.add(
            log_file,
            rotation="1 day",
            retention="7 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            encoding="utf-8",
        )


def format_json(data: Any) -> str:
    """格式化 JSON 数据用于日志输出"""
    import json

    # 将 data（可以是字典、列表等 Python 数据）转换成格式化的 JSON 字符串。
    # ensure_ascii=False：保证输出的中文不会被转义成 \uXXXX，而是直接显示中文。
    # indent=2：输出的 JSON 每层缩进2个空格。

    return json.dumps(data, ensure_ascii=False, indent=2)