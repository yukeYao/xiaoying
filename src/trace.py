"""运行记录：每步记录 step、工具、参数、返回摘要、决策依据（reason）、下一步动作。

保存为 JSONL（第一行 meta，中间每步一行，最后一行 result）和可读的 Markdown。
meta.source 标明是 mock 还是真实模型；Mock 记录只验证流程，不代表真实模型的决策效果。
"""
import json
from pathlib import Path


def summarize(tool: str | None, obs: dict) -> str:
    if tool is None:
        return obs.get("notice", "")
    if "error" in obs:
        e = obs["error"]
        detail = "；".join(e["problems"]) if "problems" in e else e.get("message", "")
        return f"错误 {e['type']}：{detail}"
    if tool == "search_docs":
        hits = obs.get("results", [])
        if not hits:
            return "无命中"
        return f"命中 {len(hits)} 条：" + "，".join(f"{h['doc_id']}/{h['paragraph_id']}({h['score']})" for h in hits)
    if tool == "read_doc":
        pids = ",".join(p["paragraph_id"] for p in obs["paragraphs"])
        missing = f"；不存在：{','.join(obs['missing_paragraphs'])}" if obs.get("missing_paragraphs") else ""
        return f"{obs['doc_id']}《{obs['title']}》版本 {obs['version_date']}，段落 {pids}{missing}"
    if tool == "ask_user":
        return f"用户回复：{obs['user_reply']}" if "user_reply" in obs else "非交互模式，提示模型调用 finish"
    if tool == "finish":
        return "校验通过，结束"
    return json.dumps(obs, ensure_ascii=False)[:200]


class Tracer:
    def __init__(self, **meta):
        """meta 至少包含 source（"mock" 或真实模型名）和 question。"""
        self.meta = meta
        self.steps: list[dict] = []
        self.result: dict | None = None

    def add(self, step: int, tool: str | None, args: dict, reason: str, observation: dict, text: str | None = None):
        rec = {"step": step, "tool": tool, "args": args, "reason": reason,
               "summary": summarize(tool, observation), "observation": observation}
        if text is not None:
            rec["text"] = text
        self.steps.append(rec)

    def finalize(self, result: dict):
        self.result = result
        for cur, nxt in zip(self.steps, self.steps[1:] + [None]):
            cur["next_action"] = (nxt["tool"] or "（无工具调用）") if nxt else f"结束（{result['status']}）"

    def save(self, out_dir: str | Path, name: str) -> tuple[Path, Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        jsonl, md = out_dir / f"{name}.jsonl", out_dir / f"{name}.md"
        lines = [{"type": "meta", **self.meta}] + [{"type": "step", **s} for s in self.steps] + \
                [{"type": "result", **(self.result or {})}]
        jsonl.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines), encoding="utf-8", newline="\n")
        md.write_text(self.to_markdown(), encoding="utf-8", newline="\n")
        return jsonl, md

    def to_markdown(self) -> str:
        m, r = self.meta, self.result or {}
        source = m.get("source", "")
        is_mock = m.get("mode", "mock" if source == "mock" else "real") == "mock"
        label = ("**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。" if is_mock
                 else f"**真实模型运行**：`{source}`")
        out = [f"# Trace：{m.get('case_id', '')}", "", label, ""]
        for k in ("question", "history", "data_dir", "fail_tool", "fail_times", "max_steps"):
            if m.get(k) not in (None, "", []):
                out.append(f"- {k}：{json.dumps(m[k], ensure_ascii=False) if k == 'history' else m[k]}")
        out += ["", "## 步骤", "", "| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |", "|---|---|---|---|---|---|"]
        for s in self.steps:
            args = json.dumps(s["args"], ensure_ascii=False) if s["args"] else (s.get("text") or "")
            cells = [str(s["step"]), s["tool"] or "（无工具调用）", args, s["reason"], s["summary"], s.get("next_action", "")]
            out.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
        out += ["", "## 结果", "", f"- status：`{r.get('status')}`", f"- reason：`{r.get('reason')}`",
                f"- steps_used：{r.get('steps_used')}", f"- answer：{r.get('answer', '')}", "- citations："]
        out += [f"  - {c.get('doc_id')}/{c.get('paragraph_id')}：「{c.get('quote')}」" for c in r.get("citations", [])] or ["  - （无）"]
        out += ["- gaps："] + ([f"  - {g}" for g in r.get("gaps", [])] or ["  - （无）"])
        return "\n".join(out) + "\n"
