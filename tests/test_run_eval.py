"""确定性测试：scripts/run_eval.py 的检查逻辑与 Mock 批量运行。"""
import sys

from src.kb import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import run_eval  # noqa: E402

from src.cli import load_cases  # noqa: E402

CASES = load_cases()


def out(status, docs=(), gaps=()):
    return {"status": status, "citations": [{"doc_id": d} for d in docs], "gaps": list(gaps)}


def test_status_must_match():
    assert run_eval.check(CASES["C03"], out("answered", ["D01"])) != []
    assert run_eval.check(CASES["C03"], out("conflict_need_confirmation", ["D01", "D02"])) == []


def test_expected_citation_docs_required():
    assert "缺少" in run_eval.check(CASES["C03"], out("conflict_need_confirmation", ["D01", "D05"]))[0]


def test_expect_gaps():
    assert run_eval.check(CASES["C07"], out("out_of_scope")) == ["gaps 应非空"]
    assert run_eval.check(CASES["C07"], out("out_of_scope", gaps=["缺资料"])) == []


def test_c10_gaps_required_only_when_failed():
    assert run_eval.check(CASES["C10"], out("failed")) != []
    assert run_eval.check(CASES["C10"], out("failed", gaps=["检索不可用"])) == []
    assert run_eval.check(CASES["C10"], out("answered", ["D03"])) == []
    assert run_eval.check(CASES["C10"], out("out_of_scope", gaps=["x"])) != []


def test_path_notation():
    steps = [{"tool": "search_docs", "args": {}, "observation": {"error": {}}},
             {"tool": "read_doc", "args": {"doc_id": "D01"}, "observation": {}},
             {"tool": None, "args": {}, "observation": {}},
             {"tool": "finish", "args": {}, "observation": {"error": {}}},
             {"tool": "finish", "args": {}, "observation": {"accepted": True}}]
    assert run_eval.path_of(steps) == "S✗→R:D01→T→F✗→F"


def test_mock_batch_all_pass(tmp_path):
    from src.mock_llm import MOCK_SCRIPTS, ScriptedLLM
    results = {cid: [run_eval.run_case(c, 1, ScriptedLLM(MOCK_SCRIPTS[cid]), tmp_path)] for cid, c in CASES.items()}
    assert all(r[0]["passed"] for r in results.values()), {k: v[0]["problems"] for k, v in results.items()}
    text = run_eval.report("mock", "mock", list(CASES.values()), results, 1, 0.0)
    assert "总通过率：16/16" in text and "只验证流程" in text
    assert (tmp_path / "C03_run1.md").exists()
