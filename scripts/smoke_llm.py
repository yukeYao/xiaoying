"""真实模型最小调用测试：确认 .env 配置可用、模型支持 tool calling。

用法：python scripts/smoke_llm.py
从 .env 读取 AGENT_MODEL / AGENT_API_KEY / AGENT_BASE_URL，发送一个问题并提供一个假工具 search_docs，
检查模型是否返回 tool call。不打印 API key。
"""
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

FAKE_TOOL = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "在公司制度文档中检索与问题相关的段落。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索关键词"},
                "reason": {"type": "string", "description": "一句话说明为什么调用这个工具"},
            },
            "required": ["query", "reason"],
        },
    },
}


def main() -> int:
    model, key, base_url = (os.getenv(k) for k in ("AGENT_MODEL", "AGENT_API_KEY", "AGENT_BASE_URL"))
    missing = [k for k, v in [("AGENT_MODEL", model), ("AGENT_API_KEY", key), ("AGENT_BASE_URL", base_url)] if not v]
    if missing:
        print(f"[FAIL] .env 缺少：{', '.join(missing)}")
        return 1
    print(f"model    = {model}")
    print(f"base_url = {base_url}")
    print(f"api_key  = 已设置（长度 {len(key)}）")

    client = OpenAI(api_key=key, base_url=base_url, timeout=60)
    messages = [
        {"role": "system", "content": "你是企业知识问答助手。回答前必须先调用 search_docs 检索公司文档。"},
        {"role": "user", "content": "公司的报销期限是多久？"},
    ]
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(model=model, messages=messages, tools=[FAKE_TOOL], temperature=0)
    except Exception as e:  # 打印错误类型和信息，便于区分 key / 网络 / 模型问题
        print(f"[FAIL] {type(e).__name__}: {e}  （耗时 {time.perf_counter() - t0:.2f}s）")
        return 1
    elapsed = time.perf_counter() - t0

    msg = resp.choices[0].message
    print(f"耗时     = {elapsed:.2f}s")
    print(f"返回模型 = {resp.model}")
    print(f"finish_reason = {resp.choices[0].finish_reason}")
    if resp.usage:
        print(f"tokens   = prompt {resp.usage.prompt_tokens}, completion {resp.usage.completion_tokens}")
    if msg.tool_calls:
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"[OK] tool call: {tc.function.name}({json.dumps(args, ensure_ascii=False)})")
        return 0
    print(f"[FAIL] 模型没有返回 tool call，返回的文本：{msg.content!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
