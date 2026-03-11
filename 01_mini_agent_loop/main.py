import argparse
from pathlib import Path

from agent import MiniManus


def main() -> int:
    # 设置程序说明
    parser = argparse.ArgumentParser(
        description="Lesson 01: 最小 Agent 循环 (只有一个 terminate 工具)"
    )
    # 要求用户输入任务内容
    parser.add_argument(
        "--task", required=True, help="The user task for the agent to solve."
    )
    # 要求用户输入最大循环次数（可选，默认为8）
    parser.add_argument(
        "--max-steps", type=int, default=8, help="Safety brake for the agent loop."
    )
    # 可选参数，设置日志目录。
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory for log files (default: ./logs in lesson dir).",
    )
    args = parser.parse_args()

    if args.log_dir:
        log_dir = Path(args.log_dir)
    else:
        log_dir = Path(__file__).parent / "logs"


    # 主程序
    agent = MiniManus(max_steps=args.max_steps, log_dir=log_dir)
    agent.run(task=args.task)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())