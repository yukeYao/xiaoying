"""供模型调用的工具：search_docs、read_doc、ask_user、finish。

返回值都是可直接序列化为 JSON 的 dict；出错时返回 {"error": {"type", "message"}}，
由模型根据错误决定下一步，而不是抛异常。

- KnowledgeBase：文档检索与读取（与运行状态无关）
- ToolRunner：一次运行的工具执行器，记录本次 read_doc 读过的段落、执行故障注入、校验 finish
"""
import re
from pathlib import Path

from .kb import DEFAULT_DATA_DIR, load_docs
from .retrieval import DEFAULT_SYNONYMS, BM25Index, expand_query, load_synonyms, make_tokenizer, tokenize


def error(type_: str, message: str) -> dict:
    return {"error": {"type": type_, "message": message}}


class KnowledgeBase:
    """use_synonyms=False 为纯 BM25 基线：不加载同义词、分词器也不注册同义词。
    syn_weight：同义扩展词在 BM25 打分中的权重（原查询词为 1.0）。"""

    def __init__(self, data_dir: str | Path = DEFAULT_DATA_DIR, synonyms_path: str | Path = DEFAULT_SYNONYMS,
                 use_synonyms: bool = True, syn_weight: float = 1.0):
        self.groups = load_synonyms(synonyms_path) if use_synonyms else []
        self.syn_weight = syn_weight
        self.tokenizer = make_tokenizer(self.groups)
        self.docs = load_docs(data_dir)
        self.index = BM25Index(self.docs, self.tokenizer)

    def query_weights(self, query: str) -> tuple[dict[str, float], list[str]]:
        weights = {t: 1.0 for t in tokenize(query, self.tokenizer)}
        added = expand_query(query, self.groups)
        for word in added:
            for t in tokenize(word, self.tokenizer):
                weights.setdefault(t, self.syn_weight)
        return weights, added

    def search_docs(self, query: str, top_k: int = 5) -> dict:
        if not isinstance(query, str) or not query.strip():
            return error("invalid_argument", "query 不能为空")
        top_k = max(1, min(int(top_k), 10))
        weights, added = self.query_weights(query)
        results = self.index.search(weights, top_k)
        out = {"query": query, "expanded_terms": added, "results": results}
        if not results:
            out["hint"] = "没有命中任何文档段落。可以换关键词或同义说法再检索；仍无结果说明资料库可能不包含该主题。"
        return out

    def read_doc(self, doc_id: str, paragraph_ids: list[str] | None = None) -> dict:
        doc = self.docs.get(doc_id)
        if doc is None:
            return error("not_found", f"文档 {doc_id} 不存在。可用文档：{', '.join(self.docs)}")
        # 总是返回全文：适用范围、优先级、废止说明常在其他段落，只读命中段落容易漏掉。
        # paragraph_ids 只用于标注请求的段落（requested_paragraphs），不限制返回内容。
        out = {
            "doc_id": doc.doc_id, "title": doc.title, "version_date": doc.version_date, "scope": doc.scope,
            "paragraphs": [{"paragraph_id": p, "text": t} for p, t in doc.paragraphs.items()],
        }
        if paragraph_ids:
            out["requested_paragraphs"] = [p for p in paragraph_ids if p in doc.paragraphs]
            missing = [p for p in paragraph_ids if p not in doc.paragraphs]
            if missing:
                out["missing_paragraphs"] = missing
                out["note"] = f"{doc_id} 中没有段落 {', '.join(missing)}，已返回全文（可用段落：{', '.join(doc.paragraphs)}）"
        return out


# ---------------------------------------------------------------------------
# 工具 schema（OpenAI function calling 格式）
# ---------------------------------------------------------------------------

STATUSES = ["answered", "conflict_need_confirmation", "need_clarification", "out_of_scope", "failed"]
MIN_QUOTE_CHARS = 8
FAULTABLE_TOOLS = ["search_docs", "read_doc"]

_REASON = {"type": "string", "description": "一句话说明为什么采取这个动作（决策依据）"}


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": {**properties, "reason": _REASON},
                       "required": required + ["reason"]}}}


TOOL_SCHEMAS = [
    _tool("search_docs", "在公司制度和产品 FAQ 中检索相关段落，返回文档 ID、标题、版本日期、适用范围、段落编号、片段和分数。",
          {"query": {"type": "string", "description": "检索语句或关键词"},
           "top_k": {"type": "integer", "description": "返回段落数，1-10，默认 5"}},
          ["query"]),
    _tool("read_doc", "读取文档全文（带段落编号、标题、版本日期、适用范围）。总是返回整篇文档，"
                      "便于核对适用范围、优先级、废止/替代说明。引用前必须先用它读取对应文档。",
          {"doc_id": {"type": "string", "description": "文档 ID，如 D01"},
           "paragraph_ids": {"type": "array", "items": {"type": "string"},
                             "description": "可选：重点关注的段落编号，如 [\"P2\"]；只做标注，仍返回全文"}},
          ["doc_id"]),
    _tool("ask_user", "向用户追问或请用户确认（如问题指代不清、资料冲突需确认适用制度）。",
          {"question": {"type": "string", "description": "要问用户的问题"}},
          ["question"]),
    _tool("finish", "结束任务并输出结构化结果。引用会被校验：quote 必须逐字来自本次 read_doc 读过的段落，且至少 8 个字。",
          {"status": {"type": "string", "enum": STATUSES},
           "answer": {"type": "string", "description": "给用户的回答；需确认或澄清时写明要问用户的问题"},
           "citations": {"type": "array", "description": "引用列表", "items": {
               "type": "object",
               "properties": {"doc_id": {"type": "string"}, "paragraph_id": {"type": "string"},
                              "quote": {"type": "string", "description": "从原文逐字复制的片段"}},
               "required": ["doc_id", "paragraph_id", "quote"]}},
           "gaps": {"type": "array", "items": {"type": "string"}, "description": "资料缺口；没有则为空列表"}},
          ["status", "answer", "citations", "gaps"]),
]

NON_INTERACTIVE_NOTICE = (
    "当前为非交互模式，无法询问用户。请调用 finish 结束：资料冲突需用户确认适用制度时用 conflict_need_confirmation"
    "（附上冲突各方的引用）；问题不清楚时用 need_clarification。把要问用户的问题写进 answer。"
)


def _no_ws(text: str) -> str:
    return re.sub(r"\s+", "", text)


class ToolRunner:
    """一次 Agent 运行的工具执行器。

    fail_tool / fail_times：故障注入。fail_times=None 表示该工具每次都失败；N 表示前 N 次失败后恢复。
    interactive：True 时 ask_user 真的询问（input_fn）；False 时返回提示，让模型调用 finish。
    """

    def __init__(self, kb: KnowledgeBase, fail_tool: str | None = None, fail_times: int | None = None,
                 interactive: bool = False, input_fn=input):
        if fail_tool and fail_tool not in FAULTABLE_TOOLS:
            raise ValueError(f"fail_tool 只能是 {FAULTABLE_TOOLS}")
        self.kb = kb
        self.fail_tool, self.fail_remaining = fail_tool, fail_times
        self.interactive, self.input_fn = interactive, input_fn
        self.read_paragraphs: set[tuple[str, str]] = set()

    def _inject_fault(self, name: str) -> bool:
        if name != self.fail_tool:
            return False
        if self.fail_remaining is None:
            return True
        if self.fail_remaining > 0:
            self.fail_remaining -= 1
            return True
        return False

    def call(self, name: str, args: dict) -> tuple[dict, dict | None]:
        """执行工具，返回 (observation, final_result)。final_result 只在 finish 校验通过时非空。"""
        if self._inject_fault(name):
            return error("tool_unavailable", f"{name} 服务暂时不可用（注入故障），请稍后重试或换用其他方式"), None
        try:
            if name == "search_docs":
                return self.kb.search_docs(args.get("query", ""), args.get("top_k", 5)), None
            if name == "read_doc":
                out = self.kb.read_doc(args.get("doc_id", ""), args.get("paragraph_ids"))
                if "error" not in out:
                    self.read_paragraphs |= {(out["doc_id"], p["paragraph_id"]) for p in out["paragraphs"]}
                return out, None
            if name == "ask_user":
                return self.ask_user(args.get("question", "")), None
            if name == "finish":
                problems = self.validate_finish(args)
                if problems:
                    return {"error": {"type": "finish_rejected", "message": "finish 未通过校验，请修正后重新调用",
                                      "problems": problems}}, None
                result = {k: args.get(k, []) for k in ("status", "answer", "citations", "gaps")}
                return {"accepted": True}, result
        except (TypeError, ValueError, AttributeError) as e:
            return error("invalid_arguments", f"{type(e).__name__}: {e}"), None
        return error("unknown_tool", f"没有名为 {name} 的工具"), None

    def ask_user(self, question: str) -> dict:
        if not isinstance(question, str) or not question.strip():
            return error("invalid_argument", "question 不能为空")
        if not self.interactive:
            return {"notice": NON_INTERACTIVE_NOTICE}
        return {"user_reply": self.input_fn(f"[Agent 提问] {question}\n> ")}

    def validate_finish(self, args: dict) -> list[str]:
        """返回问题列表；空列表表示通过。只校验格式与引用真实性，不判断引用是否支持回答。"""
        problems = []
        status, answer = args.get("status"), args.get("answer")
        citations, gaps = args.get("citations", []), args.get("gaps", [])
        if status not in STATUSES:
            problems.append(f"status 必须是 {STATUSES} 之一，收到 {status!r}")
        if not isinstance(answer, str) or not answer.strip():
            problems.append("answer 不能为空")
        if not isinstance(gaps, list) or not all(isinstance(g, str) for g in gaps):
            problems.append("gaps 必须是字符串列表")
        if not isinstance(citations, list) or not all(isinstance(c, dict) for c in citations):
            return problems + ["citations 必须是对象列表，每项包含 doc_id、paragraph_id、quote"]

        for i, c in enumerate(citations, 1):
            doc_id, pid, quote = c.get("doc_id"), c.get("paragraph_id"), c.get("quote")
            tag = f"引用 {i}（{doc_id}/{pid}）"
            q = _no_ws(quote) if isinstance(quote, str) else ""
            if len(q) < MIN_QUOTE_CHARS:
                problems.append(f"{tag}：quote 至少 {MIN_QUOTE_CHARS} 个字（不计空白），当前 {len(q)} 个")
                continue
            doc = self.kb.docs.get(doc_id)
            if doc is None:
                problems.append(f"{tag}：文档 {doc_id} 不存在")
            elif pid not in doc.paragraphs:
                problems.append(f"{tag}：{doc_id} 中没有段落 {pid}")
            elif (doc_id, pid) not in self.read_paragraphs:
                problems.append(f"{tag}：本次运行中尚未用 read_doc 读取该段落，请先读取原文")
            elif q not in _no_ws(doc.paragraphs[pid]):
                problems.append(f"{tag}：quote 不是该段原文的逐字片段（只允许空白差异），请从 read_doc 返回的原文复制")

        if status == "answered" and not citations:
            problems.append("status=answered 时至少需要 1 条引用")
        if status == "conflict_need_confirmation" and len({c.get("doc_id") for c in citations}) < 2:
            problems.append("status=conflict_need_confirmation 时至少需要 2 条来自不同文档的引用")
        return problems
