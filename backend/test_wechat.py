# -*- coding: utf-8 -*-
"""Test the computer agent with rich tools."""
import asyncio
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.agent.computer_agent import run_agent


def log_step(step_num, desc):
    print(f"  [{step_num}] {desc}", flush=True)


async def main():
    task = "打开微信，找到龙兆祥，发送一条消息：上号"
    print(f"🎯 Task: {task}", flush=True)
    print("=" * 60, flush=True)

    result = await run_agent(task, on_step=log_step)

    print("\n" + "=" * 60, flush=True)
    print(f"📝 Final: {result}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
