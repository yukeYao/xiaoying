"""确定性测试：API 层重试（不发真实请求，替换 client 的 create 方法）。"""
from types import SimpleNamespace

import openai
import pytest

try:  # 构造 openai 异常需要其底层 HTTP 库的 Request/Response：新版 SDK 用 httpx2，旧版用 httpx
    import httpx2 as httpx
except ImportError:
    import httpx

from src.agent import run_agent
from src.kb import ROOT
from src.llm import OpenAIChat
from src.tools import KnowledgeBase, ToolRunner

REQ = httpx.Request("POST", "http://localhost/v1/chat/completions")


def ok_response():
    msg = SimpleNamespace(content="hi", tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def make_llm(errors, retries=1):
    """errors：依次抛出的异常；用完后返回正常响应。"""
    llm = OpenAIChat(model="m", api_key="k", base_url="http://localhost/v1", retries=retries, retry_wait=0)
    calls = []

    def create(**kw):
        calls.append(kw)
        if len(calls) <= len(errors):
            raise errors[len(calls) - 1]
        return ok_response()

    llm.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return llm, calls


TRANSIENT = [
    openai.APITimeoutError(request=REQ),
    openai.APIConnectionError(request=REQ),
    openai.RateLimitError("rate limited", response=httpx.Response(429, request=REQ), body=None),
]


def test_sdk_auto_retry_disabled():
    assert OpenAIChat(model="m", api_key="k", base_url="http://localhost/v1").client.max_retries == 0


@pytest.mark.parametrize("err", TRANSIENT, ids=lambda e: type(e).__name__)
def test_transient_error_retried_once_then_succeeds(err):
    llm, calls = make_llm([err])
    assert llm.chat([], [])["content"] == "hi"
    assert len(calls) == 2 and len(llm.retry_log) == 1


@pytest.mark.parametrize("err", TRANSIENT, ids=lambda e: type(e).__name__)
def test_transient_error_twice_raises(err):
    llm, calls = make_llm([err, err])
    with pytest.raises(type(err)):
        llm.chat([], [])
    assert len(calls) == 2


def test_auth_error_not_retried():
    err = openai.AuthenticationError("bad key", response=httpx.Response(401, request=REQ), body=None)
    llm, calls = make_llm([err])
    with pytest.raises(openai.AuthenticationError):
        llm.chat([], [])
    assert len(calls) == 1


def test_persistent_transient_error_becomes_llm_error_in_agent():
    err = openai.APIConnectionError(request=REQ)
    llm, calls = make_llm([err, err])
    result = run_agent("问题", llm, ToolRunner(KnowledgeBase(ROOT / "data" / "docs")))
    assert result["status"] == "failed" and result["reason"] == "llm_error" and len(calls) == 2
