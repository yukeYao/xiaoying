"""命令行入口。

单个问题（真实模型）：
    python -m src.cli "报销期限多久？"
按用例运行（问题、历史、数据目录、故障配置、步数上限取自 data/cases.jsonl，命令行参数可覆盖）：
    python -m src.cli --case C03
    python -m src.cli --case C03 --mock              # 脚本化 Mock，只验证流程
常用参数：--data-dir、--max-steps、--fail-tool、--fail-times、--interactive、--trace-dir
"""
import argparse
import json
import sys
from pathlib import Path

from .agent import DEFAULT_MAX_STEPS, run_agent
from .kb import DEFAULT_DATA_DIR, ROOT
from .tools import FAULTABLE_TOOLS, KnowledgeBase, ToolRunner
from .trace import Tracer

CASES_FILE = ROOT / "data" / "cases.jsonl"


def load_cases(path: str | Path = CASES_FILE) -> dict[str, dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return {c["id"]: c for c in (json.loads(l) for l in lines if l.strip())}


def run_once(question: str, llm, *, history=None, data_dir=DEFAULT_DATA_DIR, max_steps=DEFAULT_MAX_STEPS,
             fail_tool=None, fail_times=None, interactive=False, case_id="", trace_dir=None) -> tuple[dict, Tracer]:
    data_dir = Path(data_dir)
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    runner = ToolRunner(KnowledgeBase(data_dir), fail_tool=fail_tool, fail_times=fail_times, interactive=interactive)
    shown_dir = data_dir.resolve().relative_to(ROOT).as_posix() if data_dir.resolve().is_relative_to(ROOT) else str(data_dir)
    tracer = Tracer(source=llm.name, case_id=case_id, question=question, history=history or [], data_dir=shown_dir,
                    fail_tool=fail_tool, fail_times=fail_times, max_steps=max_steps)
    result = run_agent(question, llm, runner, history=history, max_steps=max_steps, tracer=tracer)
    tracer.finalize(result)
    if trace_dir:
        tracer.save(trace_dir, case_id or "run")
    return result, tracer


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="企业知识问答 Agent")
    ap.add_argument("question", nargs="?", help="问题；与 --case 二选一")
    ap.add_argument("--case", help="用例 ID（data/cases.jsonl）")
    ap.add_argument("--mock", nargs="?", const="", metavar="SCRIPT",
                    help="使用脚本化 Mock 模型（只验证流程）；默认脚本与 --case 同名")
    ap.add_argument("--data-dir", help=f"文档目录，默认 {DEFAULT_DATA_DIR.relative_to(ROOT).as_posix()}")
    ap.add_argument("--max-steps", type=int, help=f"最大步数，默认 {DEFAULT_MAX_STEPS}")
    ap.add_argument("--fail-tool", choices=FAULTABLE_TOOLS, help="故障注入：让该工具返回错误")
    ap.add_argument("--fail-times", type=int, help="故障注入次数；不填表示每次都失败")
    ap.add_argument("--interactive", action="store_true", help="ask_user 时真的在终端询问")
    ap.add_argument("--trace-dir", help="保存 trace（JSONL + Markdown）的目录")
    args = ap.parse_args(argv)

    case = load_cases()[args.case] if args.case else {}
    question = args.question or case.get("question")
    if not question:
        ap.error("请提供问题或 --case")

    if args.mock is not None:
        from .mock_llm import MOCK_SCRIPTS, ScriptedLLM
        script = args.mock or args.case
        if script not in MOCK_SCRIPTS:
            ap.error(f"没有名为 {script!r} 的 Mock 脚本，可用：{', '.join(MOCK_SCRIPTS)}")
        llm = ScriptedLLM(MOCK_SCRIPTS[script])
    else:
        from .llm import OpenAIChat
        llm = OpenAIChat()

    fail_tool = args.fail_tool or case.get("fail_tool")
    fail_times = args.fail_times if args.fail_times is not None else case.get("fail_times")
    result, _ = run_once(
        question, llm, history=case.get("history"),
        data_dir=args.data_dir or case.get("data_dir") or DEFAULT_DATA_DIR,
        max_steps=args.max_steps or case.get("max_steps") or DEFAULT_MAX_STEPS,
        fail_tool=fail_tool, fail_times=fail_times if fail_tool else None,
        interactive=args.interactive, case_id=args.case or "", trace_dir=args.trace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
