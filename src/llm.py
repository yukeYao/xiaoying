"""真实模型接入：OpenAI 兼容接口（openai SDK），配置从 .env 读取。

chat() 返回统一格式，供 agent 循环使用（Mock 模型返回同样的格式）：
    {"content": str | None, "tool_calls": [{"id", "name", "arguments"(JSON 字符串)}]}

API 层重试：对超时、连接错误、429 限流这类临时错误，短暂等待后重试 1 次；仍失败则抛出，
由 agent 返回 status=failed, reason=llm_error。其他错误（如 401 key 无效、400 参数错误）不重试。
这是"调用模型"这一步的传输层重试，和"工具失败时由模型决定下一步"是两回事：
工具错误会作为 observation 交给模型决策，模型调用失败则无法让模型决策。
SDK 自带的自动重试关闭（max_retries=0），重试行为只由这里控制。
"""
import os
import time

import openai
from dotenv import load_dotenv
from openai import OpenAI

from .kb import ROOT

RETRYABLE_ERRORS = (openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)


class OpenAIChat:
    mode = "real"

    def __init__(self, model: str | None = None, api_key: str | None = None, base_url: str | None = None,
                 temperature: float = 0.0, timeout: float = 60, retries: int = 1, retry_wait: float = 2.0):
        load_dotenv(ROOT / ".env")  # 不覆盖已存在的环境变量：AGENT_MODEL=xxx 可临时换模型
        self.model = model or os.getenv("AGENT_MODEL")
        api_key = api_key or os.getenv("AGENT_API_KEY")
        base_url = base_url or os.getenv("AGENT_BASE_URL")
        if not (self.model and api_key and base_url):
            raise RuntimeError("缺少 AGENT_MODEL / AGENT_API_KEY / AGENT_BASE_URL：请参考 .env.example 配置 .env，或使用 --mock")
        self.name = self.model
        self.temperature = temperature
        self.retries, self.retry_wait = retries, retry_wait
        self.retry_log: list[str] = []  # 记录发生过的重试，便于排查
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=0)

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        for attempt in range(self.retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, messages=messages, tools=tools, temperature=self.temperature)
                break
            except RETRYABLE_ERRORS as e:
                if attempt == self.retries:
                    raise
                self.retry_log.append(f"{type(e).__name__}: {e}")
                time.sleep(self.retry_wait)
        msg = resp.choices[0].message
        return {"content": msg.content,
                "tool_calls": [{"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                               for tc in msg.tool_calls or []]}
