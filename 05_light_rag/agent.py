
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

from tools import TOOL_REGISTRY


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    tool = TOOL_REGISTRY.get(name)
    if tool:
        return tool.execute(**arguments)
    raise RuntimeError(f"Unknown tool: {name}")



@dataclass
class MiniManus:
    max_steps: int = 10
    log_dir: Path | None = None

    def _system_prompt(self) -> str:
        tool_descriptions = []
        for name, tool in TOOL_REGISTRY.items():
            tool_descriptions.append(f"- `{tool.name}` - {tool.description}")

        tools_list = "\n".join(tool_descriptions)

        return (
            "你是 MiniManus，一个可以访问 RAG 和工具的 AI 智能体。\n\n"
            f"你可以使用以下工具：\n{tools_list}\n\n"
            "当被问及私有知识时：\n"
            "1. 使用 'rag' 工具，设置 action='query' 来搜索知识库\n"
            "2. 使用检索到的上下文来回答问题\n"
            "3. 完成后调用 terminate\n\n"
            "规则：\n"
            "1) 使用合适的工具来完成任务。\n"
            "2) 当你得到最终答案时，调用 `terminate`。\n"
        )
    
    def run(self, *, task: str) -> None:
        if self.log_dir:
            init_logger(self.log_dir)

        find_and_load_env()
        cfg = load_config_from_env()

        tools = [tool.schema() for tool in TOOL_REGISTRY.values()]

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": task},
        ]

        logger.info("=" * 60)
        logger.info("Step 0: 初始上下文")
        logger.info("=" * 60)
        logger.info(format_json(messages))
        logger.info(f"\nAvailable tools: {len(tools)}")
        logger.info(f"Tools: {[t['function']['name'] for t in tools]}")

        for step in range(1, self.max_steps + 1):
            logger.info("#" * 60)
            logger.info(f"# Step {step}")
            logger.info("#" * 60)

            resp = chat_completions(
                cfg=cfg, messages=messages, tools=tools, tool_choice="auto"
            )

            logger.info(f"Step {step}: LLM response")
            logger.info(format_json(resp))

            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            if tool_calls:
                for idx, call in enumerate(tool_calls):
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""

                    raw_args = fn.get("arguments") or "{}"

                    try:
                        args = (
                            json.loads(raw_args)
                            if isinstance(raw_args, str)
                            else dict(raw_args)
                        )
                    except Exception as e:
                        raise RuntimeError(
                            f"Invalid tool arguments for {name}: {raw_args}"
                        ) from e

                    logger.info(f"Step {step}: Calling tool {name}")
                    logger.info(format_json({"arguments": args}))

                    should_stop, output = execute_tool(name, args)

                    logger.info(f"Step {step}: Tool returned")
                    logger.info(output[:500] + "..." if len(output) > 500 else output)

                    tool_result_msg = (
                        f"[TOOL_CALL {name}] {json.dumps(args, ensure_ascii=False)}\n[TOOL_RESULT] {output}"
                    )
                    messages.append({"role": "user", "content": tool_result_msg})

                    if should_stop:
                        logger.info("*" * 60)
                        logger.info("* Final Answer (Agent Loop Terminated)")
                        logger.info("*" * 60)
                        logger.info(output)
                        return

                logger.info(f"Step {step}: Updated messages")
                logger.info(format_json(messages))
                continue

            if content:
                logger.info("*" * 60)
                logger.info("* LLM returned content directly (no tool call)")
                logger.info("*" * 60)
                logger.info(content)
                return

        raise RuntimeError(
            f"Agent exceeded max_steps={self.max_steps} without termination."
        )