from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from env import find_and_load_env
from openai_compat import chat_completions, load_config_from_env
from log import init_logger, format_json

# 导入本地工具
from tools import MCP_TOOL_REGISTRY


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """执行工具调用"""
    tool = MCP_TOOL_REGISTRY.get(name)
    if tool:
        return tool.execute(**arguments)
    raise RuntimeError(f"Unknown tool: {name}")

@dataclass
class MiniManus:
    """支持 MCP 工具的 Agent"""

    max_steps: int = 8
    log_dir: Path | None = None

    def _system_prompt(self) -> str:
        tool_descriptions = []
        for name, tool in MCP_TOOL_REGISTRY.items():
            tool_descriptions.append(f"- `{tool.name}` - {tool.description}")

        tools_list = "\n".join(tool_descriptions)

        logger.info(f"====> tools_list: {tools_list}")

        return (
            "你是一个有用的AI助手，可以调用MCP工具。\n"
            "MCP（模型上下文协议）让你能够调用外部服务。\n\n"
            f"你可以使用以下MCP工具：\n{tools_list}\n\n"
            "规则：\n"
            "1) 在需要时使用适当的工具查找信息。\n"
            "2) 获取工具结果后，进行分析并形成答案。\n"
            "3) 当你得到最终答案时，调用`terminate`。\n"
        )
    


    def run(self, *, task: str) -> None:
        if self.log_dir:
            init_logger(self.log_dir)

        find_and_load_env()
        cfg = load_config_from_env()

        # MCP 工具列表
        tools = [tool.schema() for tool in MCP_TOOL_REGISTRY.values()]

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": task},
        ]

        logger.info("=" * 60)
        logger.info("Step 0: 初始上下文 (messages)")
        logger.info("=" * 60)
        logger.info(format_json(messages))
        logger.info("\nStep 0: 可用工具 (tools)")
        logger.info(format_json(tools))


        for step in range(1, self.max_steps + 1):
            logger.info("#" * 60)
            logger.info(f"# Step {step}")
            logger.info("#" * 60)

            resp = chat_completions(
                cfg=cfg, messages=messages, tools=tools, tool_choice="auto"
            )

            logger.info(f"Step {step}: LLM 原始回复")
            logger.info(format_json(resp))

            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            if tool_calls:
                # 处理多个工具调用
                for idx, call in enumerate(tool_calls):
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""

                    raw_args = fn.get("arguments") or "{}"

                    try:
                        args = (
                            json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                        )
                    except Exception as e:
                        raise RuntimeError(
                            f"Invalid tool arguments for {name}: {raw_args}"
                        ) from e

                    logger.info(f"Step {step}: 调用工具 {name}")
                    logger.info(format_json({"arguments": args}))

                    should_stop, output = execute_tool(name, args)

                    logger.info(f"Step {step}: 工具返回")
                    logger.info(output)

                    # Moonshot API workaround
                    tool_result_msg = (
                        f"[TOOL_CALL {name}] {json.dumps(args)}\n[TOOL_RESULT] {output}"
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": tool_result_msg,
                        }
                    )

                    if should_stop:
                        logger.info("*" * 60)
                        logger.info("* 最终答案 (Agent Loop 终止)")
                        logger.info("*" * 60)
                        from rich.console import Console
                        from rich.markdown import Markdown
                        console = Console()
                        console.print(Markdown(output))
                        return

                logger.info(f"Step {step}: 更新后的 messages")
                logger.info(format_json(messages))
                continue

            if content:
                logger.info("*" * 60)
                logger.info("* LLM 直接返回内容 (未调用工具)")
                logger.info("*" * 60)
                logger.info(content)
                return

        raise RuntimeError(
            f"Agent exceeded max_steps={self.max_steps} without termination."
        )





