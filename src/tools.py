"""供模型调用的检索工具：search_docs、read_doc。

返回值都是可直接序列化为 JSON 的 dict；出错时返回 {"error": {"type", "message"}}，
由模型根据错误决定下一步，而不是抛异常。
（ask_user、finish、故障注入和引用校验在阶段 3 加入。）
"""
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
        if not query or not query.strip():
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
        ids = paragraph_ids or list(doc.paragraphs)
        missing = [p for p in ids if p not in doc.paragraphs]
        if missing:
            return error("not_found", f"{doc_id} 中没有段落 {', '.join(missing)}。可用段落：{', '.join(doc.paragraphs)}")
        return {
            "doc_id": doc.doc_id, "title": doc.title, "version_date": doc.version_date, "scope": doc.scope,
            "paragraphs": [{"paragraph_id": p, "text": doc.paragraphs[p]} for p in ids],
        }
