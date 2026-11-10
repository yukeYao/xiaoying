"""真实模型接入：OpenAI 兼容接口（openai SDK），配置从 .env 读取。

chat() 返回统一格式，供 agent 循环使用（Mock 模型返回同样的格式）：
    {"content": str | None, "tool_calls": [{"id", "name", "arguments"(JSON 字符串)}]}
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

from .kb import ROOT


class OpenAIChat:
    def __init__(self, model: str | None = None, api_key: str | None = None, base_url: str | None = None,
                 temperature: float = 0.0, timeout: float = 60):
        load_dotenv(ROOT / ".env")
        self.model = model or os.getenv("AGENT_MODEL")
        api_key = api_key or os.getenv("AGENT_API_KEY")
        base_url = base_url or os.getenv("AGENT_BASE_URL")
        if not (self.model and api_key and base_url):
            raise RuntimeError("缺少 AGENT_MODEL / AGENT_API_KEY / AGENT_BASE_URL：请参考 .env.example 配置 .env，或使用 --mock")
        self.name = self.model
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, temperature=self.temperature)
        msg = resp.choices[0].message
        return {"content": msg.content,
                "tool_calls": [{"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                               for tc in msg.tool_calls or []]}
