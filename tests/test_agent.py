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
RESULT_KEYS = {"status", "answer", "citations", "gaps", "conflict_check", "reason", "steps_used"}  # run_agent 的结果
OUTPUT_KEYS = RESULT_KEYS | {"mode", "model", "trace_file"}  # run_once 的最终输出


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
    assert set(result) == OUTPUT_KEYS and result["mode"] == "mock" and result["trace_file"] is None
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


def test_wrong_scope_split_rejected_then_corrected_to_true_conflict(kb):
    result, llm = run(kb, MOCK_SCRIPTS["SCOPE_SPLIT_WRONG"])
    obs = tool_observations(llm)
    assert obs[3]["error"]["type"] == "finish_rejected"
    assert any("scope_quote 不能都是“未说明”" in p for p in obs[3]["error"]["problems"])
    assert result["status"] == "conflict_need_confirmation" and result["steps_used"] == 5
    assert result["conflict_check"]["relations"][0]["type"] == "true_conflict"


def test_rejected_finish_counts_toward_steps(kb):
    bad = F("answered", "没有引用的回答")
    result, _ = run(kb, [bad, bad, bad], max_steps=3)
    assert result["status"] == "incomplete" and result["reason"] == "max_steps_reached" and result["steps_used"] == 3


# ---------- 无工具调用 ----------

def test_text_reply_is_reminded_and_counted(kb):
    result, llm = run(kb, MOCK_SCRIPTS["NO_TOOL_CALL"])
    assert result["status"] == "answered" and result["steps_used"] == 4  # 1 次纯文本 + 3 次工具
    # 提醒后附剩余步数（第 1 步用掉后剩 9 步）
    assert {"role": "user", "content": NO_TOOL_REMINDER + "剩余步数：9"} in llm.last_messages


def test_only_text_replies_reach_step_limit(kb):
    result, _ = run(kb, [{"text": "我觉得是30天"}] * 5, max_steps=3)
    assert result["status"] == "incomplete" and result["steps_used"] == 3


# ---------- 步数上限 ----------

def test_max_steps_returns_incomplete(kb):
    result, _ = run(kb, [S("报销", "检索")] * 20, max_steps=10)
    assert result == {"status": "incomplete", "answer": "", "citations": [], "gaps": ["达到最大步数 10 仍未完成"],
                      "conflict_check": None, "reason": "max_steps_reached", "steps_used": 10}


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
                {"status": "failed", "answer": "参数错误", "citations": [], "gaps": ["无"], "reason": "r",
                 "conflict_check": {"claims": [], "relations": []}})}]}

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
    main(["--case", "C03", "--mock", "--data-dir", "data/variant_a/docs"])
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "incomplete"


def test_c10_alternative_path_read_directly(kb):
    # C10 允许 answered：search_docs 一直失败时绕过检索直接读取，引用仍需通过校验
    result, llm = run(kb, MOCK_SCRIPTS["C10_READ_DIRECT"], fail_tool="search_docs")
    assert tool_observations(llm)[0]["error"]["type"] == "tool_unavailable"
    assert result["status"] == "answered" and result["status"] in CASES["C10"]["expected_status"]


# ---------- 最终输出字段 ----------

def test_output_citation_metadata_filled_by_program(tmp_path):
    # 模型提供的 title / version_date 被忽略，由程序按 doc_id 从文档库补充
    script = MOCK_SCRIPTS["C01"][:2] + [F("answered", "5天", [("D03", "P1", "员工累计工作已满1年不满10年的，年休假5天")],
                                          claims=[("D03", "5天", "未说明")])]
    script[-1]["args"]["citations"][0].update(title="编造的标题", version_date="1999-01-01")
    out, _ = run_once("工作满5年有几天年假？", ScriptedLLM(script), trace_dir=tmp_path, trace_name="x")
    c = out["citations"][0]
    assert c == {"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天",
                 "title": "年假管理制度", "version_date": "2024-01-01"}
    assert out["mode"] == "mock" and out["model"] == "mock"
    assert out["trace_file"].endswith("x.md") and (tmp_path / "x.md").exists()
    last = json.loads((tmp_path / "x.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert last["citations"][0]["title"] == "年假管理制度" and last["mode"] == "mock"


# ---------- 交互多轮 ----------

def test_chat_keeps_history_and_asks_user():
    from src.cli import chat
    from src.mock_llm import A
    script = [  # 第 1 轮：问请假审批，先追问再回答；第 2 轮：上下文追问
        A("请问请假几天？", "需要天数才能确定审批人"),
        S("请假 审批", "检索请假审批"), R("D04", "读取原文", ["P2"]),
        F("answered", "3天及以内由直属主管审批。", [("D04", "P2", "请假3天及以内的，由直属主管审批")],
          claims=[("D04", "3天及以内由直属主管审批", "未说明")]),
        S("请假 超过3天 审批", "结合上文检索"), R("D04", "读取原文", ["P3"]),
        F("answered", "超过3天还需部门负责人和人力资源部审批。",
          [("D04", "P3", "请假超过3天的，由直属主管审批后，报部门负责人和人力资源部审批")],
          claims=[("D04", "超过3天还需部门负责人和人力资源部审批", "未说明")]),
    ]
    llm = ScriptedLLM(script)
    inputs = iter(["请假要谁审批？", "2天", "那超过3天呢？", "exit"])
    prompts, printed = [], []

    def fake_input(prompt):
        prompts.append(prompt)
        return next(inputs)

    history = chat(llm, input_fn=fake_input, print_fn=printed.append)
    assert [h["role"] for h in history] == ["user", "assistant", "user", "assistant"]
    assert history[0]["content"] == "请假要谁审批？" and history[1]["content"] == "3天及以内由直属主管审批。"
    assert any("请问请假几天" in p for p in prompts)  # ask_user 真正向用户提问并读取了输入
    # 第 2 轮发给模型的消息里包含第 1 轮的问答历史
    assert {"role": "user", "content": "请假要谁审批？"} in llm.last_messages
    assert {"role": "assistant", "content": "3天及以内由直属主管审批。"} in llm.last_messages
    assert sum("[answered]" in p for p in printed) == 2


def test_chat_ask_user_reads_input(kb):
    from src.mock_llm import A
    llm = ScriptedLLM([A("您指哪类费用？", "指代不清")])
    replies = iter(["差旅费"])
    runner = ToolRunner(kb, interactive=True, input_fn=lambda p: next(replies))
    run_agent("这个能报吗？", llm, runner, max_steps=1)
    assert json.loads(llm.last_messages[-1]["content"]) == {"user_reply": "差旅费", "剩余步数": 0}


def test_cli_chat_rejects_mock():
    with pytest.raises(SystemExit):
        main(["--chat", "--mock"])


# ---------- 循环防护：剩余步数与重复调用 ----------

def test_observation_includes_remaining_steps(kb):
    _, llm = run(kb, MOCK_SCRIPTS["C01"], max_steps=10)
    assert [o["剩余步数"] for o in tool_observations(llm)] == [9, 8, 7]


def test_duplicate_call_annotated_and_still_executed(kb):
    script = [S("年假", "检索"), S("年假", "换个理由，参数相同"), S("年假 天数", "参数不同")]
    _, llm = run(kb, script, max_steps=3)
    obs = tool_observations(llm)
    assert "重复调用" not in obs[0] and "重复调用" not in obs[2]
    assert obs[1]["重复调用"] == "与第 1 步调用相同，结果未变"
    assert obs[1]["results"] == obs[0]["results"]  # 照常执行


def test_duplicate_call_with_changed_result_not_called_unchanged(kb):
    # 故障注入第 1 次失败后恢复：参数相同但结果不同，只注明重复，不说"结果未变"
    _, llm = run(kb, [S("年假", "检索"), S("年假", "重试")], max_steps=2, fail_tool="search_docs", fail_times=1)
    obs = tool_observations(llm)
    assert obs[1]["重复调用"] == "与第 1 步调用相同" and "results" in obs[1]


def test_duplicate_read_doc_annotated_in_trace(kb):
    from src.trace import Tracer
    tracer = Tracer(source="mock", question="q")
    script = [R("D03", "读"), R("D03", "再读一次")]
    run_agent("q", ScriptedLLM(script), ToolRunner(kb), max_steps=2, tracer=tracer)
    assert "与第 1 步调用相同，结果未变" in tracer.steps[1]["summary"]


def test_prompt_contains_conflict_and_scope_rules():
    from src.agent import SYSTEM_PROMPT
    for phrase in ["范围分工", "已被替代", "真冲突", "版本日期更新不代表优先适用", "不得把互相矛盾的规定并列",
                   "连续失败 2 次", "out_of_scope 时不提供文档以外的建议", "剩余步数"]:
        assert phrase in SYSTEM_PROMPT, phrase
