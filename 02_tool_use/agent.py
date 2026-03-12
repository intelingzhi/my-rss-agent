

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from loguru import logger
import sys
import json



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from log import init_logger, format_json
from env import find_and_load_env
from openai_compat import chat_completions, load_config_from_env

# 导入工具
from tools import TOOL_REGISTRY

def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """执行指定名称的工具，返回是否停止和输出"""
    tool = TOOL_REGISTRY.get(name)
    if tool:
        return tool.execute(**arguments)
    else:
        raise ValueError(f"工具 {name} 不存在")


@dataclass
class MiniManus:
    """支持 Tool Use 的 Agent"""

    max_steps: int = 8
    log_dir: Path | None = None

    def _system_prompt(self) -> str:    
        return (
            "你是一个乐于助人的 AI 助手。\n"
            "你可以使用以下工具：\n"
            "- `search(query: string)` - 搜索网络以获取最新信息\n"
            "- `datetime()` - 获取当前的日期和时间\n"
            "- `calculator(expression: string)` - 计算数学表达式。使用 '**' 表示乘方，例如 '2**10' 表示 2 的 10 次方。\n"
            "- `terminate(final: string)` - 结束代理循环并返回最终答案\n\n"
            "规则：\n"
            "1) 在需要信息时使用工具。\n"
            "2) 重要：调用工具后，工具的结果将会显示给你。请使用该结果来形成你的最终答案。\n"
            "3) 一旦你从工具获得结果，请立即调用 `terminate` 并给出最终答案。不要再次调用相同的工具。\n"
            "4) 回答请保持简洁。\n"
            )
    

    def run(self, *, task: str) -> None:
        if self.log_dir:
            init_logger(self.log_dir)  # 设置log的输出格式

        find_and_load_env()
        cfg = load_config_from_env()

        # 本课新增：4 个工具
        tools = [tool.schema() for tool in TOOL_REGISTRY.values()]

        # 设置初始prompt
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
            logger.info("\n" + "=" * 60)
            logger.info(f"Step {step}: 调用 OpenAI API")
            logger.info("===> 调用 OpenAI API 时的参数：messages: {}", messages)
            logger.info("===> 调用 OpenAI API 时的参数：tools: {}", tools)
            logger.info("=" * 60)

            # 发出请求
            resp = chat_completions(
                cfg = cfg, messages=messages, tools=tools, tool_choice="auto",
            )

            logger.info(f"Step {step}: LLM 原始回复")
            logger.info(format_json(resp))

            # 解析回复
            """
            API 返回的 JSON 结构大致如下：
            {
                "id": "chatcmpl-abc123",
                "object": "chat.completion",
                "created": 1710000000,
                "model": "gpt-4o",
                "choices": [
                    {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "你好！",
                        "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": "{\"location\": \"Tokyo\"}"
                            }
                        }
                        ],
                        "refusal": null
                    },
                    "finish_reason": "stop",
                    "logprobs": null
                    }
                ],
                "usage": {
                    ...
                },
                "system_fingerprint": "fp_abc123"
            }
            """
            msg = resp.get("choices", [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            logger.info("===> 得到LLM的返回信息：tool_calls: {}", tool_calls)
            logger.info("===> 得到LLM的返回信息：content: {}", content)

            # 如果有 tool_calls，说明需要调用工具
            if tool_calls:
                # 处理多个工具调用（去重，防止返回重复）
                seen_tools = set()
                for idx, call in enumerate(tool_calls):
                    fn = call.get("function", {})
                    name = fn.get("name") or ""

                    # 去重：跳过重名的工具（防止大模型一次返回多个重复的工具调用）
                    if name in seen_tools:
                        continue
                    # 下面开始添加工具
                    logger.info("===> 正在添加工具调用：{}", name)
                    seen_tools.add(name)  # 添加工具名到已处理集合

                    raw_args = fn.get("arguments") or "" # 原始参数字符串

                    tool_call_id = call.get("id") or "" # 工具调用ID

                    try:
                        args = (
                            # 如果是字符串就解析成字典（使用 json.loads），否则直接转换为字典
                            json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                        )
                    except Exception as e:
                        raise RuntimeError(f"工具 {name} 的参数解析失败：{e}")
                    
                    logger.info(f"===> Step {step}: 尝试调用工具 {name}")
                    logger.info(format_json({"arguments": args}))

                    should_stop, output = execute_tool(name, args)

                    logger.info(f"Step {step}: 工具返回")
                    logger.info(output)

                    # [TOOL_CALL search] {"query": "天气"}
                    # [TOOL_RESULT] 晴天，25C
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
                        logger.info(output)
                        return
                    
            if content:
                logger.info("*" * 60)
                logger.info("* LLM 直接返回内容 (未调用工具)")
                logger.info("*" * 60)
                logger.info(content)
                # 没有调用 terminate，直接返回内容
                return
            
        raise RuntimeError("LLM 未返回有效内容，也未调用工具")




