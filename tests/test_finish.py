"""确定性测试：finish 引用校验、ask_user、故障注入、工具参数错误。不依赖模型。"""
import pytest

from src.kb import ROOT
from src.tools import KnowledgeBase, ToolRunner

MAIN = ROOT / "data" / "docs"


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(MAIN)


@pytest.fixture
def runner(kb):
    return ToolRunner(kb)


def finish(runner, status="answered", citations=(), answer="回答", gaps=()):
    args = {"status": status, "answer": answer, "gaps": list(gaps),
            "citations": [{"doc_id": d, "paragraph_id": p, "quote": q} for d, p, q in citations]}
    return runner.call("finish", args)


D03_P1 = ("D03", "P1", "员工累计工作已满1年不满10年的，年休假5天")
D01_P2 = ("D01", "P2", "员工应在费用发生之日起30天内提交报销申请")
D02_P2 = ("D02", "P2", "员工须在费用发生后15天内通过报销系统提交报销单")


def problems(obs):
    return " ".join(obs["error"]["problems"])


# ---------- 引用校验 ----------

def test_valid_answer_accepted(runner):
    runner.call("read_doc", {"doc_id": "D03", "paragraph_ids": ["P1"]})
    obs, final = finish(runner, citations=[D03_P1])
    assert obs == {"accepted": True}
    assert final["status"] == "answered" and final["citations"][0]["doc_id"] == "D03"


def test_fabricated_quote_rejected(runner):
    runner.call("read_doc", {"doc_id": "D03"})
    obs, final = finish(runner, citations=[("D03", "P1", "工作满5年的员工可享受年假7天")])
    assert final is None and obs["error"]["type"] == "finish_rejected"
    assert "逐字" in problems(obs)


def test_quote_whitespace_difference_allowed(runner):
    runner.call("read_doc", {"doc_id": "D03"})
    _, final = finish(runner, citations=[("D03", "P1", "员工累计工作 已满1年\n不满10年的，年休假5天")])
    assert final is not None


def test_quote_punctuation_difference_rejected(runner):
    runner.call("read_doc", {"doc_id": "D03"})
    obs, final = finish(runner, citations=[("D03", "P1", "员工累计工作已满1年不满10年的,年休假5天")])  # 半角逗号
    assert final is None and "逐字" in problems(obs)


def test_quote_shorter_than_8_chars_rejected(runner):
    runner.call("read_doc", {"doc_id": "D03"})
    obs, final = finish(runner, citations=[("D03", "P1", "年休假5天")])
    assert final is None and "至少 8 个字" in problems(obs)


def test_quote_8_chars_without_whitespace_accepted(runner):
    runner.call("read_doc", {"doc_id": "D03"})
    _, final = finish(runner, citations=[("D03", "P1", "不满10年的，年")])  # 恰好 8 个字
    assert final is not None


def test_paragraph_not_read_rejected_even_if_verbatim(runner):
    obs, final = finish(runner, citations=[D03_P1])
    assert final is None and "read_doc" in problems(obs)


def test_paragraph_seen_only_via_search_rejected(runner):
    runner.call("search_docs", {"query": "年假天数"})
    obs, final = finish(runner, citations=[D03_P1])
    assert final is None and "read_doc" in problems(obs)


def test_read_doc_registers_whole_document(runner):
    # read_doc 总是返回全文：请求 P2 也会登记 P1，因此可以引用 P1
    runner.call("read_doc", {"doc_id": "D03", "paragraph_ids": ["P2"]})
    assert {("D03", p) for p in ("P1", "P2", "P3", "P4")} <= runner.read_paragraphs
    _, final = finish(runner, citations=[D03_P1])
    assert final is not None


def test_reading_other_document_does_not_count(runner):
    runner.call("read_doc", {"doc_id": "D01"})
    obs, final = finish(runner, citations=[D03_P1])
    assert final is None and "read_doc" in problems(obs)


def test_read_with_missing_paragraph_ids_still_registers_full_text(runner):
    obs, _ = runner.call("read_doc", {"doc_id": "D03", "paragraph_ids": ["P8", "P9"]})
    assert obs["missing_paragraphs"] == ["P8", "P9"] and len(obs["paragraphs"]) == 4
    assert ("D03", "P1") in runner.read_paragraphs


def test_failed_read_registers_nothing(runner):
    obs, _ = runner.call("read_doc", {"doc_id": "D99"})
    assert obs["error"]["type"] == "not_found" and not runner.read_paragraphs


def test_unknown_doc_and_paragraph_rejected(runner):
    obs, _ = finish(runner, citations=[("D99", "P1", "这是一段不存在的文档引用"), ("D03", "P9", "这是一段不存在的段落引用")])
    text = problems(obs)
    assert "D99 不存在" in text and "没有段落 P9" in text


@pytest.mark.parametrize("status", ["incomplete", "ok", None])
def test_invalid_status_rejected(runner, status):
    obs, final = finish(runner, status=status)
    assert final is None and "status 必须是" in problems(obs)


def test_answered_requires_citation(runner):
    obs, final = finish(runner, status="answered")
    assert final is None and "至少需要 1 条引用" in problems(obs)


def test_conflict_requires_two_different_docs(runner):
    runner.call("read_doc", {"doc_id": "D01"})
    obs, final = finish(runner, status="conflict_need_confirmation",
                        citations=[D01_P2, ("D01", "P4", "单笔报销金额超过5000元的")])
    assert final is None and "2 条来自不同文档" in problems(obs)


def test_conflict_with_two_docs_accepted(runner):
    runner.call("read_doc", {"doc_id": "D01"})
    runner.call("read_doc", {"doc_id": "D02"})
    _, final = finish(runner, status="conflict_need_confirmation", citations=[D01_P2, D02_P2])
    assert final["status"] == "conflict_need_confirmation"


@pytest.mark.parametrize("status", ["out_of_scope", "need_clarification", "failed"])
def test_statuses_without_citations_accepted(runner, status):
    _, final = finish(runner, status=status, gaps=["缺少资料"])
    assert final is not None and final["gaps"] == ["缺少资料"]


def test_empty_answer_rejected(runner):
    obs, _ = finish(runner, status="out_of_scope", answer="  ")
    assert "answer 不能为空" in problems(obs)


def test_bad_citation_and_gap_types_rejected(runner):
    obs, _ = runner.call("finish", {"status": "out_of_scope", "answer": "x", "citations": "D01", "gaps": "无"})
    text = problems(obs)
    assert "citations 必须是对象列表" in text and "gaps 必须是字符串列表" in text


def test_reports_all_problems_at_once(runner):
    obs, _ = finish(runner, status="answered", citations=[("D03", "P1", "短"), D03_P1])
    assert len(obs["error"]["problems"]) == 2  # 太短 + 未读取


# ---------- ask_user ----------

def test_ask_user_non_interactive_returns_notice(runner):
    obs, final = runner.call("ask_user", {"question": "适用哪份制度？"})
    assert final is None and "finish" in obs["notice"]


def test_ask_user_interactive_uses_input(kb):
    r = ToolRunner(kb, interactive=True, input_fn=lambda prompt: "适用 D01")
    obs, _ = r.call("ask_user", {"question": "适用哪份制度？"})
    assert obs == {"user_reply": "适用 D01"}


def test_ask_user_empty_question(runner):
    assert runner.call("ask_user", {"question": ""})[0]["error"]["type"] == "invalid_argument"


# ---------- 故障注入 ----------

def test_fault_always(kb):
    r = ToolRunner(kb, fail_tool="search_docs")
    for _ in range(3):
        assert r.call("search_docs", {"query": "年假"})[0]["error"]["type"] == "tool_unavailable"
    assert "error" not in r.call("read_doc", {"doc_id": "D03"})[0]  # 其他工具不受影响


def test_fault_first_n_times_then_recovers(kb):
    r = ToolRunner(kb, fail_tool="search_docs", fail_times=2)
    results = [r.call("search_docs", {"query": "年假"})[0] for _ in range(3)]
    assert ["error" in x for x in results] == [True, True, False]


def test_fault_read_doc(kb):
    r = ToolRunner(kb, fail_tool="read_doc", fail_times=1)
    assert r.call("read_doc", {"doc_id": "D03"})[0]["error"]["type"] == "tool_unavailable"
    assert (("D03", "P1") not in r.read_paragraphs)
    r.call("read_doc", {"doc_id": "D03"})
    assert ("D03", "P1") in r.read_paragraphs


def test_fault_only_on_retrieval_tools(kb):
    with pytest.raises(ValueError):
        ToolRunner(kb, fail_tool="finish")


# ---------- 参数错误 ----------

def test_unknown_tool(runner):
    assert runner.call("delete_docs", {})[0]["error"]["type"] == "unknown_tool"


def test_bad_argument_type(runner):
    assert runner.call("search_docs", {"query": "年假", "top_k": "很多"})[0]["error"]["type"] == "invalid_arguments"
