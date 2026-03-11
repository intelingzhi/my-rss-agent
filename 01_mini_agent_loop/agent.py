from __future__ import annotations
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from loguru import logger


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from tools import execute_tool, terminate_schema
from openai_compat import chat_completions, load_config_from_env
from env import find_and_load_env
from log import init_logger, format_json


@dataclass
class MiniManus:
    # 设置最大循环次数
    max_steps: int = 8

    # 日志目录，可选
    log_dir: Path | None = None

    # 设置系统提示词
    def _system_prompt(self) -> str:
        return (
            "You are a minimal agent. You have exactly one tool: `terminate(final: string)`.\n"
            "Rules:\n"
            "1) You MUST call `terminate` to return the final answer. Do NOT put the final answer in normal content.\n"
            "2) Keep the final answer concise and directly useful.\n"
        )


    # 运行 Agent
    def run(self, *, task: str) -> None:
        if self.log_dir:
            init_logger(self.log_dir)

        # 0. 加载 OpenAI 配置
        find_and_load_env()    # 把配置文件里面的环境变量设置到 os.environ 中
        cfg = load_config_from_env()  # 从环境变量加载 OpenAI API 配置


        # 1. 初始化消息容器
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": task}
        ]

        # 2. 初始化工具列表
        tools = [terminate_schema()]

        # 进入 Agent Loop
        for step in range(1, self.max_steps + 1):
            logger.info("#" * 60)
            logger.info(f"# Step {step}")
            logger.info("#" * 60)

            # 3. 调用大模型
            resp = chat_completions(cfg=cfg, messages=messages, tools=tools, tool_choice="auto")


            logger.info(f"Step {step}: 原始messages")
            logger.info(format_json(messages))
            logger.info(f"Step {step}: LLM 原始回复")
            logger.info(format_json(resp))

            # choices是一个列表，通常只取第一个元素
            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            # choices里面有：
            #   - message: 大模型的回复消息
            #       - role: 消息角色，通常是 "assistant"
            #       - content: 普通回复内容
            #       - tool_calls: 如果调用了工具，这里会有工具调用信息。
            #   - finish_reason: 完成原因，可能是 "stop"（正常结束）或 "tool_calls"（调用了工具）

            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()  # 应该为空

            # 4. 工具调用
            if tool_calls:
                call = tool_calls[0]  # 取第一个工具调用
                function_name = call.get("function") or ""  # 取 function 字典（这是LLM提供给我们的）

                if isinstance(function_name, dict):
                    name = function_name.get("name") or ""
                    raw_args = function_name.get("arguments") or "{}"
                else:
                    name = ""
                    raw_args = "{}"

                # 解析工具参数
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

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id") or "toolcall_0",
                        "content": output,
                    }
                )

                if should_stop:
                    logger.info("*" * 60)
                    logger.info("* 最终答案 (Agent Loop 终止)")
                    logger.info("*" * 60)
                    logger.info(output)
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