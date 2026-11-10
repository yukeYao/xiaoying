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


def finish(runner, status="answered", citations=(), answer="回答", gaps=(), conflict_check=None):
    """conflict_check 不传时，按本次读过的文档自动生成"与问题无关"的 claims，
    使这些测试只关注引用校验；conflict_check 的规则在下方单独测试。"""
    if conflict_check is None:
        read = sorted({d for d, _ in runner.read_paragraphs})
        conflict_check = {"claims": [{"doc_id": d, "claim": "与问题无关", "scope_quote": "未说明"} for d in read],
                          "relations": []}
    args = {"status": status, "answer": answer, "gaps": list(gaps), "conflict_check": conflict_check,
            "citations": [{"doc_id": d, "paragraph_id": p, "quote": q} for d, p, q in citations]}
    return runner.call("finish", args)


def cc(claims=(), relations=()):
    return {"claims": [{"doc_id": d, "claim": c, "scope_quote": s} for d, c, s in claims],
            "relations": [{"docs": list(docs), "type": t,
                           "basis": {"doc_id": b[0], "paragraph_id": b[1], "quote": b[2]} if b else None}
                          for docs, t, b in relations]}


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
    _, final = finish(runner, status="conflict_need_confirmation", citations=[D01_P2, D02_P2],
                      conflict_check=cc([("D01", "30天", "未说明"), ("D02", "15天", "未说明")],
                                        [(("D01", "D02"), "true_conflict", None)]))
    assert final["status"] == "conflict_need_confirmation"
    assert final["conflict_check"]["relations"][0]["type"] == "true_conflict"


# ---------- conflict_check ----------

def read(runner, *doc_ids):
    for d in doc_ids:
        runner.call("read_doc", {"doc_id": d})


def test_conflict_check_required(runner):
    obs, final = runner.call("finish", {"status": "out_of_scope", "answer": "无", "citations": [], "gaps": ["缺资料"]})
    assert final is None and "conflict_check 必填" in problems(obs)


def test_conflict_check_empty_when_nothing_read(runner):
    _, final = finish(runner, status="out_of_scope", gaps=["缺资料"], conflict_check=cc())
    assert final is not None


def test_rule1_claims_must_cover_all_read_docs(runner):
    read(runner, "D01", "D02")
    obs, final = finish(runner, status="out_of_scope", gaps=["x"], conflict_check=cc([("D01", "30天", "未说明")]))
    assert final is None and "缺少本次读过的文档：D02" in problems(obs)


def test_single_relevant_doc_needs_no_relations(runner):
    read(runner, "D03")
    _, final = finish(runner, citations=[D03_P1], conflict_check=cc([("D03", "5天", "未说明")]))
    assert final is not None


def test_unrelated_docs_need_no_relations(runner):
    read(runner, "D03", "D09")
    _, final = finish(runner, citations=[D03_P1],
                      conflict_check=cc([("D03", "5天", "未说明"), ("D09", "与问题无关", "未说明")]))
    assert final is not None


def test_relevant_docs_must_be_pairwise_related(runner):
    # 修改后的要求：claim 不是"与问题无关"的文档两两都要有关系，不论结论是否不同
    read(runner, "D01", "D02", "D05")
    claims = [("D01", "30天", "未说明"), ("D02", "15天", "未说明"), ("D05", "差旅10天", "差旅费用报销")]
    obs, final = finish(runner, status="conflict_need_confirmation", citations=[D01_P2, D02_P2],
                        conflict_check=cc(claims, [(("D01", "D02"), "true_conflict", None)]))
    text = problems(obs)
    assert final is None and "D01–D05" in text and "D02–D05" in text and "D01–D02" not in text


def test_rule2_basis_required_for_scope_split_superseded_priority(runner):
    read(runner, "D06", "D07")
    for rtype in ("scope_split", "superseded", "priority"):
        obs, final = finish(runner, conflict_check=cc([("D06", "4年", "未说明"), ("D07", "3年", "未说明")],
                                                      [(("D06", "D07"), rtype, None)]),
                            citations=[("D07", "P3", "笔记本电脑使用满3年的，员工可申请更换")])
        assert final is None and f"type={rtype} 时 basis 必填" in problems(obs)


def test_rule2_basis_must_be_verbatim(runner):
    read(runner, "D06", "D07")
    obs, final = finish(runner, citations=[("D07", "P3", "笔记本电脑使用满3年的，员工可申请更换")],
                        conflict_check=cc([("D06", "4年", "未说明"), ("D07", "3年", "未说明")],
                                          [(("D06", "D07"), "superseded", ("D07", "P1", "2024版完全取代2022版的所有规定"))]))
    assert final is None and "basis" in problems(obs) and "逐字" in problems(obs)


def test_rule2_basis_must_come_from_the_pair(runner):
    read(runner, "D06", "D07", "D03")
    obs, final = finish(runner, citations=[("D07", "P3", "笔记本电脑使用满3年的，员工可申请更换")],
                        conflict_check=cc([("D06", "4年", "未说明"), ("D07", "3年", "未说明"), ("D03", "与问题无关", "未说明")],
                                          [(("D06", "D07"), "superseded", D03_P1)]))
    assert final is None and "basis 必须来自这两份文档之一" in problems(obs)


def test_superseded_with_valid_basis_accepted(runner):
    read(runner, "D06", "D07")
    _, final = finish(runner, citations=[("D07", "P3", "笔记本电脑使用满3年的，员工可申请更换")],
                      conflict_check=cc([("D06", "4年", "未说明"), ("D07", "3年", "未说明")],
                                        [(("D06", "D07"), "superseded", ("D07", "P1", "《办公设备申领规定（2022版）》同时废止"))]))
    assert final is not None


def test_rule3_scope_split_needs_a_scope_quote(runner):
    read(runner, "D01", "D02")
    obs, final = finish(runner, citations=[D01_P2, D02_P2],
                        conflict_check=cc([("D01", "30天", "未说明"), ("D02", "15天", "未说明")],
                                          [(("D01", "D02"), "scope_split", ("D02", "P1", "本指引用于说明员工在报销系统中提交费用报销的操作步骤"))]))
    assert final is None and "scope_quote 不能都是“未说明”" in problems(obs)


def test_rule3_scope_quote_must_be_verbatim(runner):
    read(runner, "D05")
    obs, final = finish(runner, citations=[("D05", "P2", "差旅费用应在出差结束之日起10天内提交报销申请")],
                        conflict_check=cc([("D05", "10天", "适用于所有出差人员")]))
    assert final is None and "scope_quote 不是该文档原文" in problems(obs)


def test_rule3_scope_quote_may_come_from_scope_field_or_paragraph(runner):
    read(runner, "D01", "D05")
    for scope_quote in ("差旅费用报销", "本规定适用于员工因公出差产生的交通、住宿及出差补助等差旅费用的报销"):
        _, final = finish(runner, citations=[D01_P2, ("D05", "P3", "本规定关于差旅费用报销期限的条款优先于公司通用报销规定执行")],
                          conflict_check=cc([("D01", "30天", "未说明"), ("D05", "差旅10天", scope_quote)],
                                            [(("D01", "D05"), "scope_split",
                                              ("D05", "P3", "本规定关于差旅费用报销期限的条款优先于公司通用报销规定执行"))]))
        assert final is not None, scope_quote


def test_rule4_true_conflict_forbids_answered(runner):
    read(runner, "D01", "D02")
    obs, final = finish(runner, status="answered", citations=[D01_P2, D02_P2],
                        conflict_check=cc([("D01", "30天", "未说明"), ("D02", "15天", "未说明")],
                                          [(("D01", "D02"), "true_conflict", None)]))
    assert final is None and "status 必须是 conflict_need_confirmation" in problems(obs)


def test_relation_type_and_docs_validated(runner):
    read(runner, "D01", "D02")
    obs, _ = finish(runner, status="conflict_need_confirmation", citations=[D01_P2, D02_P2],
                    conflict_check=cc([("D01", "30天", "未说明"), ("D02", "15天", "未说明")],
                                      [(("D01", "D01"), "true_conflict", None), (("D01", "D02"), "maybe", None)]))
    text = problems(obs)
    assert "两个不同的文档 ID" in text and "type 必须是" in text


def test_consistent_label_cannot_be_checked_semantically(runner):
    # 已知限制：不同结论被标为 consistent 时程序无法发现（需人工审核 trace）
    read(runner, "D01", "D02")
    _, final = finish(runner, citations=[D01_P2, D02_P2],
                      conflict_check=cc([("D01", "30天", "未说明"), ("D02", "15天", "未说明")],
                                        [(("D01", "D02"), "consistent", None)]))
    assert final is not None


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
