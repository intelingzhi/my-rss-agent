from __future__ import annotations

import json
from dataclasses import dataclass, field
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
    skill_context: str = ""

    def _system_prompt(self) -> str:
        tool_descriptions = []
        for name, tool in TOOL_REGISTRY.items():
            tool_descriptions.append(f"- `{tool.name}` - {tool.description}")

        tools_list = "\n".join(tool_descriptions)

        skill_instruction = ""
        if self.skill_context:
            skill_instruction = f"\n\n# 已激活的 Skill 上下文\n{self.skill_context}\n"

        return (
            "你是 MiniManus，一个可以访问 Skills 和 MCP 工具的 AI 智能体。\n"
            "Skills 让你能够安装和加载特定领域的专业知识。\n\n"
            f"你可以使用以下工具：\n{tools_list}\n\n"
            "Skills 管理：\n"
            "- 使用 `skill` 工具来安装（install）、列出（list）、加载（load）或创建（create）skills\n"
            "- Skills 可以包含指令、辅助工具，甚至可以内部调用 MCP 工具\n\n"
            f"{skill_instruction}"
            "规则：\n"
            "1) 使用合适的工具来完成任务。\n"
            "2) 需要时使用 skills 来扩展你的能力。\n"
            "3) 当你得到最终答案时，调用 `terminate`。\n"
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

            # 调用 LLM 生成回复
            resp = chat_completions(
                cfg=cfg, messages=messages, tools=tools, tool_choice="auto"
            )

            logger.info(f"Step {step}: LLM 原始回复")
            logger.info(format_json(resp))

            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            # agent 加载了新 skill 之后，system prompt（messages[0]）需要更新，把新技能说明加进去。
            # 检测到"已经有 skill 被加载过了 + 这轮又调用了 skill load"，就刷新一次 system prompt。
            # 第一层：遍历历史消息，找有没有 [SKILL_CONTEXT] 标记
            for msg_in_history in messages:
                if isinstance(msg_in_history.get("content"), str):
                    # 判断：system prompt 里有没有已经注入过skill
                    # 如果有，说明之前某一轮已经加载过 skill 了
                    if "[SKILL_CONTEXT]" in msg_in_history["content"]:
                        # 第二层：看这轮 LLM 的 tool_calls 里有没有再次调用 skill
                        for t_call in tool_calls:
                            fn = t_call.get("function") or {}
                            if fn.get("name") == "skill":
                                skill_instruction = fn.get("arguments", "{}")
                                if "load" in skill_instruction:
                                    # 两个条件都满足，刷新 system prompt
                                    logger.info("Skill loaded, updating context...")
                                    messages[0]["content"] = self._system_prompt()

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

                    # 检查是否是 skill load
                    if name == "skill" and args.get("action") == "load":
                        # 将 skill 内容作为系统提示的一部分
                        self.skill_context = (
                            f"## Skill: {args.get('skill_name')}\n{output}"
                        )
                        messages[0]["content"] = self._system_prompt()
                        tool_result_msg = f"[SKILL_LOADED]\n{output}"
                    else:
                        tool_result_msg = f"[TOOL_CALL {name}] {json.dumps(args, ensure_ascii=False)}\n[TOOL_RESULT] {output}"

                    messages.append({"role": "user", "content": tool_result_msg})

                    if should_stop:
                        logger.info("*" * 60)
                        logger.info("* Final Answer (Agent Loop Terminated)")
                        logger.info("*" * 60)
                        from rich.console import Console
                        from rich.markdown import Markdown
                        console = Console()
                        console.print(Markdown(output))
                        return

                logger.info(f"Step {step}: Updated messages")
                logger.info(format_json(messages))
                continue

            if content:
                logger.info("*" * 60)
                logger.info("* LLM returned content directly (no tool call)")
                logger.info("*" * 60)
                # logger.info(content)
                from rich.console import Console
                from rich.markdown import Markdown
                console = Console()
                console.print(Markdown(content))
                return

        raise RuntimeError(
            f"Agent exceeded max_steps={self.max_steps} without termination."
        )