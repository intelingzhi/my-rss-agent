from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from openai import OpenAI
from loguru import logger
import os


@dataclass(frozen=True)
class OpenAICompatConfig:
    """
    OpenAI API 兼容配置的数据类。
    所有字段均为只读，实例创建后不可更改。
    """
    api_key: str      # OpenAI API 密钥，用于身份验证
    base_url: str     # OpenAI API 的基础 URL
    model: str        # 要使用的模型名称
    timeout_s: float = 60.0  # 请求超时时间（秒），默认 60 秒


def chat_completions(
        *,
        cfg: OpenAICompatConfig,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 1.0,
) -> dict[str, Any]:
    """
    调用 OpenAI Chat Completions API，生成对话回复。

    Args:
        cfg (OpenAICompatConfig): OpenAI API 配置。
        messages (list[dict[str, str]]): 聊天消息列表。
        tools (list[dict[str, Any]] | None): 工具列表，可选。
        tool_choice (str | dict[str, Any]): 工具选择方式，默认为 "auto"。
        temperature (float): 采样温度，默认为 1.0。

    Returns:
        dict[str, Any]: API 返回的 JSON 格式结果。

    Raises:
        RuntimeError: 调用 API 失败时抛出。
    """
    # 1. 创建 OpenAI 客户端
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url, timeout=cfg.timeout_s)

    # 2. 构建请求参数
    kwargs: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
    }

    # 3. 添加 tools 参数
    if tools is not None:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice


    # 4. 调用 OpenAI API
    try:
        # create 表示创建一次新的请求（实际发起 HTTP POST）
        # 接收返回值，是一个 ChatCompletion 对象，通常这样取内容：
        #   resp.choices[0].message.content        # 模型回复的文字
        #   resp.choices[0].message.tool_calls     # 如果调用了工具
        #   resp.usage.total_tokens                # 消耗的 token 数
        resp = client.chat.completions.create(**kwargs)

        # 将 resp 对象（ChatCompletion 类型）转换为 JSON 格式的 Python 字典，并返回。
        return resp.model_dump(mode="json")
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise RuntimeError(f"OpenAI API 调用失败: {e}")


def load_config_from_env() -> OpenAICompatConfig:
    """
    从环境变量加载 OpenAI API 配置。

    Returns:
        OpenAICompatConfig: 加载后的配置实例。

    Raises:
        RuntimeError: 如果缺少必要环境变量。
    """
    api_key   = os.environ.get("OPENAI_KEY")      or os.environ.get("OPENAI_API_KEY") or ""
    base_url  = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE")    or ""
    model     = os.environ.get("OPENAI_MODEL")    or ""
    timeout_s = float(os.environ.get("OPENAI_TIMEOUT_S") or "60")

    # 检查是否有缺失的环境变量
    missing = [
        k
        for k, v in [
            ("OPENAI_KEY", api_key),
            ("OPENAI_BASE_URL", base_url),
            ("OPENAI_MODEL", model),
        ]
        if not v
    ]
    if missing:
        raise RuntimeError(
            f"Missing env vars: {', '.join(missing)} (check exercise/.env)"
        )

    # 返回配置实例
    return OpenAICompatConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout_s=timeout_s,
    )