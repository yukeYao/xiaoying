"""端到端评测：批量运行 data/cases.jsonl 中的用例，对比期望状态与实际结果。

用法：
    python scripts/run_eval.py --mock                  # 脚本化 Mock，只验证流程
    python scripts/run_eval.py --real --repeat 3       # 真实模型，每个用例跑 3 次
    python scripts/run_eval.py --real --cases C03 C05  # 只跑部分用例（结果写入 *_subset.md）

trace：真实模型 → examples/real/，Mock → examples/mock/，文件名 {用例ID}_run{第几次}.jsonl/.md
结果：examples/eval_results_real.md / examples/eval_results_mock.md

每次运行的检查项：
- 实际状态在 expected_status 中
- 状态符合期望且用例给出 expected_citation_docs 时，引用必须覆盖这些文档
- expect_gaps：gaps 非空
- gaps_required_if_status：状态在列表中时 gaps 必须非空（如 C10 为 failed 时）
引用逐字校验由 finish 守卫完成：结果来自被接受的 finish，即表示引用校验通过。
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cli import load_cases, run_once  # noqa: E402

ABBR = {"search_docs": "S", "read_doc": "R", "ask_user": "A", "finish": "F", None: "T"}


def check(case: dict, out: dict) -> list[str]:
    problems = []
    if out["status"] not in case["expected_status"]:
        problems.append(f"状态 {out['status']} 不在期望 {case['expected_status']} 中")
    elif case.get("expected_citation_docs"):
        missing = set(case["expected_citation_docs"]) - {c["doc_id"] for c in out["citations"]}
        if missing:
            problems.append(f"缺少对 {sorted(missing)} 的引用")
    if case.get("expect_gaps") and not out["gaps"]:
        problems.append("gaps 应非空")
    if out["status"] in case.get("gaps_required_if_status", []) and not out["gaps"]:
        problems.append(f"状态为 {out['status']} 时 gaps 应非空")
    return problems


def path_of(steps: list[dict]) -> str:
    """动作路径，如 S→R:D01→R:D02→A→F✗→F。✗ 表示该步返回错误。"""
    parts = []
    for s in steps:
        p = ABBR.get(s["tool"], s["tool"])
        if s["tool"] == "read_doc" and s["args"].get("doc_id"):
            p += f":{s['args']['doc_id']}"
        if "error" in s["observation"]:
            p += "✗"
        parts.append(p)
    return "→".join(parts)


def run_case(case: dict, k: int, llm, trace_dir: Path) -> dict:
    out, tracer = run_once(case["question"], llm, history=case.get("history"),
                           data_dir=case.get("data_dir", "data/docs"), max_steps=case.get("max_steps", 10),
                           fail_tool=case.get("fail_tool"), fail_times=case.get("fail_times"),
                           case_id=case["id"], trace_dir=trace_dir, trace_name=f"{case['id']}_run{k}")
    rejected = sum(1 for s in tracer.steps if s["tool"] == "finish" and "error" in s["observation"])
    if out["reason"] == "finish_called":
        cite = f"通过（{len(out['citations'])} 条）" if out["citations"] else "通过（无引用）"
    else:
        cite = "—（未完成 finish）"
    problems = check(case, out)
    return {"run": k, "status": out["status"], "reason": out["reason"], "passed": not problems,
            "problems": problems, "steps": out["steps_used"], "cite": cite, "rejected": rejected,
            "path": path_of(tracer.steps), "trace": out["trace_file"]}


def report(mode: str, model: str, cases: list[dict], results: dict, repeat: int, elapsed: float) -> str:
    total = sum(len(r) for r in results.values())
    passed = sum(x["passed"] for r in results.values() for x in r)
    full = [cid for cid, r in results.items() if all(x["passed"] for x in r)]
    failed = [cid for cid, r in results.items() if not all(x["passed"] for x in r)]
    lines = [f"# 端到端评测结果（{'Mock' if mode == 'mock' else '真实模型'}）", ""]
    if mode == "mock":
        lines += ["> **Mock 运行**：脚本化 Mock 模型按固定脚本行动，只验证流程（循环、工具、校验、步数上限、故障注入），"
                  "不证明真实模型的决策效果。", ""]
    lines += [f"- 模型：`{model}`", f"- 运行时间：{datetime.now():%Y-%m-%d %H:%M}，耗时 {elapsed:.0f}s",
              f"- 每个用例运行次数：{repeat}", f"- trace 目录：`examples/{mode}/`（文件名 `用例ID_run次数`）",
              "- 路径记号：S=search_docs，R:Dxx=read_doc，A=ask_user，F=finish，T=无工具调用的纯文本回复，✗=该步返回错误", "",
              "## 汇总", "",
              f"- 总通过率：{passed}/{total}（{passed / total:.0%}）",
              f"- 全部运行都通过的用例：{len(full)}/{len(results)}",
              f"- 失败用例：{', '.join(failed) if failed else '无'}", "",
              "## 逐用例结果", "",
              "| 用例 | 验收点 | 期望状态 | 实际状态（各次） | 通过 | 步数 | 引用校验 | finish 被拒 | 路径（各次） |",
              "|---|---|---|---|---|---|---|---|---|"]
    for case in cases:
        r = results[case["id"]]
        lines.append("| " + " | ".join([
            case["id"], "、".join(case.get("acceptance", [])), " / ".join(case["expected_status"]),
            " / ".join(x["status"] for x in r), f"{sum(x['passed'] for x in r)}/{len(r)}",
            " / ".join(str(x["steps"]) for x in r), " / ".join(x["cite"] for x in r),
            " / ".join(str(x["rejected"]) for x in r), "<br>".join(x["path"] for x in r)]) + " |")
    fails = [(cid, x) for cid, r in results.items() for x in r if not x["passed"]]
    if fails:
        lines += ["", "## 未通过的运行", "", "| 用例 | 第几次 | 问题 | trace |", "|---|---|---|---|"]
        # 报告位于 examples/，trace 位于 examples/{mode}/，链接用相对路径
        lines += [f"| {cid} | {x['run']} | {'；'.join(x['problems'])} | [{Path(x['trace']).name}]({mode}/{Path(x['trace']).name}) |"
                  for cid, x in fails]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mock", action="store_true", help="脚本化 Mock（只验证流程）")
    g.add_argument("--real", action="store_true", help="真实模型（读取 .env）")
    ap.add_argument("--repeat", type=int, default=1, help="每个用例运行次数")
    ap.add_argument("--cases", nargs="+", help="只运行这些用例 ID")
    args = ap.parse_args()

    all_cases = load_cases()
    ids = args.cases or list(all_cases)
    unknown = [i for i in ids if i not in all_cases]
    if unknown:
        ap.error(f"未知用例：{unknown}")
    cases = [all_cases[i] for i in ids]
    mode = "mock" if args.mock else "real"
    trace_dir = ROOT / "examples" / mode
    out_file = ROOT / "examples" / (f"eval_results_{mode}.md" if not args.cases else f"eval_results_{mode}_subset.md")

    if not args.cases and trace_dir.exists():  # 全量运行前清掉旧 trace，避免残留
        for f in list(trace_dir.glob("*.jsonl")) + list(trace_dir.glob("*.md")):
            f.unlink()

    if mode == "mock":
        from src.mock_llm import MOCK_SCRIPTS, ScriptedLLM
        make_llm, model = (lambda cid: ScriptedLLM(MOCK_SCRIPTS[cid])), "mock"
    else:
        from src.llm import OpenAIChat
        real = OpenAIChat()
        make_llm, model = (lambda cid: real), real.name

    t0, results = time.perf_counter(), {}
    for case in cases:
        results[case["id"]] = []
        for k in range(1, args.repeat + 1):
            r = run_case(case, k, make_llm(case["id"]), trace_dir)
            results[case["id"]].append(r)
            print(f"{case['id']} run{k}: {r['status']:<28} {'PASS' if r['passed'] else 'FAIL'}  {r['path']}", flush=True)

    text = report(mode, model, cases, results, args.repeat, time.perf_counter() - t0)
    out_file.write_text(text, encoding="utf-8", newline="\n")
    print(f"\n结果已写入 {out_file.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
