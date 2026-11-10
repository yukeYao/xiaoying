"""Agent 循环测试（脚本化 Mock 模型）。

注意：Mock 按固定脚本行动，这些测试只验证流程（循环、步数上限、校验、故障注入、trace、输出 schema），
不证明真实模型的决策效果。
"""
import json

import pytest

from src.agent import NO_TOOL_REMINDER, run_agent
from src.cli import load_cases, main, run_once
from src.kb import ROOT
from src.mock_llm import MOCK_SCRIPTS, F, R, S, ScriptedLLM
from src.tools import KnowledgeBase, ToolRunner

MAIN = ROOT / "data" / "docs"
CASES = load_cases()
RESULT_KEYS = {"status", "answer", "citations", "gaps", "reason", "steps_used"}


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(MAIN)


def run(kb, script, max_steps=10, **runner_kw):
    llm = ScriptedLLM(script)
    return run_agent("问题", llm, ToolRunner(kb, **runner_kw), max_steps=max_steps), llm


def tool_observations(llm):
    return [json.loads(m["content"]) for m in llm.last_messages if m["role"] == "tool"]


# ---------- 用例流程（Mock） ----------

def test_cases_file_covers_required_cases():
    expected = {f"C{i:02d}" for i in range(1, 15)} | {"V03", "V05"}
    assert set(CASES) == expected
    assert all(cid in MOCK_SCRIPTS for cid in CASES)


@pytest.mark.parametrize("case_id", sorted(CASES))
def test_mock_case_flow(case_id):
    case = CASES[case_id]
    result, tracer = run_once(case["question"], ScriptedLLM(MOCK_SCRIPTS[case_id]), history=case.get("history"),
                              data_dir=case.get("data_dir", "data/docs"), max_steps=case.get("max_steps", 10),
                              fail_tool=case.get("fail_tool"), fail_times=case.get("fail_times"), case_id=case_id)
    assert set(result) == RESULT_KEYS
    assert result["status"] in case["expected_status"]
    cited = {c["doc_id"] for c in result["citations"]}
    assert set(case.get("expected_citation_docs", [])) <= cited
    if case.get("expect_gaps"):
        assert result["gaps"]
    assert len(tracer.steps) == result["steps_used"]


def test_history_is_passed_to_model(kb):
    llm = ScriptedLLM(MOCK_SCRIPTS["C08"])
    history = CASES["C08"]["history"]
    run_agent("那超过3天呢？", llm, ToolRunner(kb), history=history)
    assert llm.last_messages[1:3] == history and llm.last_messages[3]["content"] == "那超过3天呢？"


# ---------- 引用校验进入循环 ----------

def test_bad_citation_rejected_then_corrected(kb):
    result, llm = run(kb, MOCK_SCRIPTS["BAD_CITATION"])
    obs = tool_observations(llm)
    assert obs[2]["error"]["type"] == "finish_rejected"  # 第一次 finish 被拒，作为 observation 返回
    assert result["status"] == "answered" and result["steps_used"] == 4
    assert result["citations"][0]["quote"] == "员工累计工作已满1年不满10年的，年休假5天"


def test_rejected_finish_counts_toward_steps(kb):
    bad = F("answered", "没有引用的回答")
    result, _ = run(kb, [bad, bad, bad], max_steps=3)
    assert result["status"] == "incomplete" and result["reason"] == "max_steps_reached" and result["steps_used"] == 3


# ---------- 无工具调用 ----------

def test_text_reply_is_reminded_and_counted(kb):
    result, llm = run(kb, MOCK_SCRIPTS["NO_TOOL_CALL"])
    assert result["status"] == "answered" and result["steps_used"] == 4  # 1 次纯文本 + 3 次工具
    assert {"role": "user", "content": NO_TOOL_REMINDER} in llm.last_messages


def test_only_text_replies_reach_step_limit(kb):
    result, _ = run(kb, [{"text": "我觉得是30天"}] * 5, max_steps=3)
    assert result["status"] == "incomplete" and result["steps_used"] == 3


# ---------- 步数上限 ----------

def test_max_steps_returns_incomplete(kb):
    result, _ = run(kb, [S("报销", "检索")] * 20, max_steps=10)
    assert result == {"status": "incomplete", "answer": "", "citations": [], "gaps": ["达到最大步数 10 仍未完成"],
                      "reason": "max_steps_reached", "steps_used": 10}


def test_multiple_tool_calls_in_one_reply_each_count(kb):
    class TwoCalls:
        name = "mock"

        def chat(self, messages, tools):
            call = {"name": "search_docs", "arguments": json.dumps({"query": "年假", "reason": "r"})}
            return {"content": None, "tool_calls": [{"id": "a", **call}, {"id": "b", **call}]}

    result = run_agent("问题", TwoCalls(), ToolRunner(kb), max_steps=3)
    assert result["status"] == "incomplete" and result["steps_used"] == 3


# ---------- 故障注入进入循环 ----------

def test_fault_injection_seen_by_model(kb):
    result, llm = run(kb, MOCK_SCRIPTS["C11"], fail_tool="search_docs", fail_times=1)
    obs = tool_observations(llm)
    assert obs[0]["error"]["type"] == "tool_unavailable" and "results" in obs[1]
    assert result["status"] == "answered"


def test_persistent_fault_leads_to_failed(kb):
    result, _ = run(kb, MOCK_SCRIPTS["C10"], fail_tool="search_docs")
    assert result["status"] == "failed" and result["gaps"]


# ---------- 其他异常 ----------

def test_invalid_json_arguments_become_observation(kb):
    class BadJSON:
        name = "mock"
        n = 0

        def chat(self, messages, tools):
            self.n += 1
            if self.n == 1:
                return {"content": None, "tool_calls": [{"id": "x", "name": "search_docs", "arguments": "{not json"}]}
            return {"content": None, "tool_calls": [{"id": "y", "name": "finish", "arguments": json.dumps(
                {"status": "failed", "answer": "参数错误", "citations": [], "gaps": ["无"], "reason": "r"})}]}

    llm = BadJSON()
    result = run_agent("问题", llm, ToolRunner(kb))
    assert result["status"] == "failed" and result["steps_used"] == 2


def test_llm_exception_returns_failed(kb):
    class Broken:
        name = "mock"

        def chat(self, messages, tools):
            raise ConnectionError("network down")

    result = run_agent("问题", Broken(), ToolRunner(kb))
    assert result["status"] == "failed" and result["reason"] == "llm_error" and "network down" in result["gaps"][0]


# ---------- Trace ----------

def test_trace_files(tmp_path):
    case = CASES["C03"]
    result, _ = run_once(case["question"], ScriptedLLM(MOCK_SCRIPTS["C03"]), case_id="C03", trace_dir=tmp_path)
    lines = [json.loads(l) for l in (tmp_path / "C03.jsonl").read_text(encoding="utf-8").splitlines()]
    assert lines[0]["type"] == "meta" and lines[0]["source"] == "mock"
    steps = [l for l in lines if l["type"] == "step"]
    assert [s["tool"] for s in steps] == ["search_docs", "read_doc", "read_doc", "search_docs", "ask_user", "finish"]
    assert all({"step", "tool", "args", "reason", "summary", "next_action"} <= set(s) for s in steps)
    assert steps[0]["next_action"] == "read_doc" and steps[-1]["next_action"] == "结束（conflict_need_confirmation）"
    assert lines[-1]["type"] == "result" and lines[-1]["status"] == result["status"]
    md = (tmp_path / "C03.md").read_text(encoding="utf-8")
    assert "MOCK 运行" in md and "不代表真实模型的决策效果" in md
    assert b"\r\n" not in (tmp_path / "C03.md").read_bytes()


def test_trace_no_tool_step_recorded(kb):
    from src.trace import Tracer
    tracer = Tracer(source="mock", question="q")
    result = run_agent("q", ScriptedLLM(MOCK_SCRIPTS["NO_TOOL_CALL"]), ToolRunner(kb), tracer=tracer)
    tracer.finalize(result)
    assert tracer.steps[0]["tool"] is None and tracer.steps[0]["text"] == "年假一般是5天。"
    assert tracer.steps[0]["next_action"] == "search_docs"


# ---------- CLI ----------

def test_cli_mock_case(capsys):
    assert main(["--case", "C12", "--mock"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "incomplete" and out["reason"] == "max_steps_reached"


def test_cli_overrides_data_dir(capsys):
    # 用替换版数据跑 C03 的 Mock 脚本：脚本引用 D02，而替换版没有 D02 → 读取报错、引用被拒，最终 incomplete
    main(["--case", "C03", "--mock", "--data-dir", "data/variant/docs"])
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "incomplete"


def test_c10_alternative_path_read_directly(kb):
    # C10 允许 answered：search_docs 一直失败时绕过检索直接读取，引用仍需通过校验
    result, llm = run(kb, MOCK_SCRIPTS["C10_READ_DIRECT"], fail_tool="search_docs")
    assert tool_observations(llm)[0]["error"]["type"] == "tool_unavailable"
    assert result["status"] == "answered" and result["status"] in CASES["C10"]["expected_status"]
