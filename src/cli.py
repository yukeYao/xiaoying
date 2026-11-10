"""命令行入口。

单个问题（真实模型）：
    python -m src.cli "报销期限多久？"
按用例运行（问题、历史、数据目录、故障配置、步数上限取自 data/cases.jsonl，命令行参数可覆盖）：
    python -m src.cli --case C03
    python -m src.cli --case C03 --mock              # 脚本化 Mock，只验证流程
交互多轮模式（真实模型；保留对话历史，ask_user 会真的询问）：
    python -m src.cli --chat
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
EXIT_WORDS = {"", "exit", "quit", "q", "退出"}


def load_cases(path: str | Path = CASES_FILE) -> dict[str, dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return {c["id"]: c for c in (json.loads(l) for l in lines if l.strip())}


def _rel(path: Path) -> str:
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def build_output(result: dict, llm, kb: KnowledgeBase, trace_file: str | None) -> dict:
    """最终输出：在 agent 结果上补充 mode、model、trace_file；
    引用的 title / version_date 由程序按 doc_id 从文档库补充，不由模型生成。"""
    citations = []
    for c in result.get("citations", []):
        doc = kb.docs.get(c.get("doc_id"))
        citations.append({"doc_id": c.get("doc_id"), "paragraph_id": c.get("paragraph_id"), "quote": c.get("quote"),
                          "title": doc.title if doc else None, "version_date": doc.version_date if doc else None})
    return {**result, "citations": citations, "mode": llm.mode, "model": llm.name, "trace_file": trace_file}


def run_once(question: str, llm, *, history=None, data_dir=DEFAULT_DATA_DIR, max_steps=DEFAULT_MAX_STEPS,
             fail_tool=None, fail_times=None, interactive=False, input_fn=input, case_id="",
             trace_dir=None, trace_name=None) -> tuple[dict, Tracer]:
    data_dir = Path(data_dir)
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    kb = KnowledgeBase(data_dir)
    runner = ToolRunner(kb, fail_tool=fail_tool, fail_times=fail_times, interactive=interactive, input_fn=input_fn)
    tracer = Tracer(source=llm.name, mode=llm.mode, case_id=case_id, question=question, history=history or [],
                    data_dir=_rel(data_dir), fail_tool=fail_tool, fail_times=fail_times, max_steps=max_steps)
    result = run_agent(question, llm, runner, history=history, max_steps=max_steps, tracer=tracer)
    name = trace_name or case_id or "run"
    trace_file = _rel(Path(trace_dir) / f"{name}.md") if trace_dir else None
    output = build_output(result, llm, kb, trace_file)
    tracer.finalize(output)
    if trace_dir:
        tracer.save(trace_dir, name)
    return output, tracer


def format_answer(out: dict) -> str:
    lines = [f"[{out['status']}] {out['answer']}"]
    lines += [f"  引用 {c['doc_id']}/{c['paragraph_id']}《{c['title']}》({c['version_date']})：「{c['quote']}」"
              for c in out["citations"]]
    lines += [f"  资料缺口：{g}" for g in out["gaps"]]
    lines.append(f"  （{out['reason']}，{out['steps_used']} 步）")
    return "\n".join(lines)


def chat(llm, *, input_fn=input, print_fn=print, **run_kw) -> list[dict]:
    """交互多轮：连续提问并保留对话历史；ask_user 通过 input_fn 真的询问用户。返回最终历史。"""
    history: list[dict] = []
    print_fn("交互模式：输入问题，空行或 exit 退出。")
    turn = 0
    while True:
        question = input_fn("\n你：").strip()
        if question.lower() in EXIT_WORDS:
            return history
        turn += 1
        out, _ = run_once(question, llm, history=list(history), interactive=True, input_fn=input_fn,
                          trace_name=f"chat_turn{turn}", **run_kw)
        print_fn(format_answer(out))
        history += [{"role": "user", "content": question}, {"role": "assistant", "content": out["answer"]}]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="企业知识问答 Agent")
    ap.add_argument("question", nargs="?", help="问题；与 --case / --chat 三选一")
    ap.add_argument("--case", help="用例 ID（data/cases.jsonl）")
    ap.add_argument("--chat", action="store_true", help="交互多轮模式（真实模型）")
    ap.add_argument("--mock", nargs="?", const="", metavar="SCRIPT",
                    help="使用脚本化 Mock 模型（只验证流程）；默认脚本与 --case 同名")
    ap.add_argument("--data-dir", help=f"文档目录，默认 {_rel(DEFAULT_DATA_DIR)}")
    ap.add_argument("--max-steps", type=int, help=f"最大步数，默认 {DEFAULT_MAX_STEPS}")
    ap.add_argument("--fail-tool", choices=FAULTABLE_TOOLS, help="故障注入：让该工具返回错误")
    ap.add_argument("--fail-times", type=int, help="故障注入次数；不填表示每次都失败")
    ap.add_argument("--interactive", action="store_true", help="ask_user 时真的在终端询问（--chat 下默认开启）")
    ap.add_argument("--trace-dir", help="保存 trace（JSONL + Markdown）的目录")
    args = ap.parse_args(argv)

    if args.chat and (args.mock is not None or args.case or args.question):
        ap.error("--chat 不能与 --mock、--case 或问题参数同时使用")
    case = load_cases()[args.case] if args.case else {}
    question = args.question or case.get("question")
    if not question and not args.chat:
        ap.error("请提供问题、--case 或 --chat")

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
    run_kw = dict(data_dir=args.data_dir or case.get("data_dir") or DEFAULT_DATA_DIR,
                  max_steps=args.max_steps or case.get("max_steps") or DEFAULT_MAX_STEPS,
                  fail_tool=fail_tool, fail_times=fail_times if fail_tool else None, trace_dir=args.trace_dir)
    if args.chat:
        chat(llm, **run_kw)
        return 0
    out, _ = run_once(question, llm, history=case.get("history"), interactive=args.interactive,
                      case_id=args.case or "", **run_kw)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
