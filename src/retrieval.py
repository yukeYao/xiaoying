"""BM25 段落检索（jieba 分词）+ 同义词扩展。"""
import json
import logging
import math
from collections import Counter
from pathlib import Path

import jieba

from .kb import ROOT, Doc

jieba.setLogLevel(logging.WARNING)

DEFAULT_SYNONYMS = ROOT / "data" / "synonyms.json"
STOPWORDS = set("的 了 吗 呢 么 啊 是 有 在 和 与 及 或 要 能 我 你 他 她 它 就 都 也 什么 怎么 多少 几".split())


def load_synonyms(path: str | Path = DEFAULT_SYNONYMS) -> list[list[str]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["groups"]


def make_tokenizer(groups: list[list[str]] | None = None) -> jieba.Tokenizer:
    """每种检索模式用独立的分词器实例；传入同义词组时，把组内词注册为整词。"""
    tk = jieba.Tokenizer()
    for group in groups or []:
        for word in group:
            tk.add_word(word)
    return tk


def tokenize(text: str, tokenizer: jieba.Tokenizer) -> list[str]:
    tokens = tokenizer.lcut(text.lower())
    return [t for t in tokens if t.strip() and t not in STOPWORDS and any(ch.isalnum() for ch in t)]


def expand_query(query: str, groups: list[list[str]]) -> list[str]:
    """查询中出现某组任一词时，返回该组中查询里没有的其他词。"""
    added = []
    for group in groups:
        if any(word in query for word in group):
            added += [w for w in group if w not in query and w not in added]
    return added


class BM25Index:
    """以段落为检索单元，标题拼进每个段落一起索引。"""

    def __init__(self, docs: dict[str, Doc], tokenizer: jieba.Tokenizer, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.units = [(doc, pid, text) for doc in docs.values() for pid, text in doc.paragraphs.items()]
        self.tfs = [Counter(tokenize(doc.title + " " + text, tokenizer)) for doc, _, text in self.units]
        self.lens = [sum(tf.values()) for tf in self.tfs]
        self.avg_len = sum(self.lens) / len(self.lens)
        df = Counter(term for tf in self.tfs for term in tf)
        n = len(self.units)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, i: int, weights: dict[str, float]) -> float:
        tf, length, s = self.tfs[i], self.lens[i], 0.0
        for t, w in weights.items():
            if t in tf:
                f = tf[t]
                s += w * self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * length / self.avg_len))
        return s

    def search(self, weights: dict[str, float], top_k: int = 5) -> list[dict]:
        """weights：查询词 -> 权重（原词 1.0，同义扩展词可降权）。"""
        scored = [(self.score(i, weights), i) for i in range(len(self.units))]
        scored = sorted([x for x in scored if x[0] > 0], key=lambda x: -x[0])[:top_k]
        results = []
        for s, i in scored:
            doc, pid, text = self.units[i]
            results.append({
                "doc_id": doc.doc_id, "title": doc.title, "version_date": doc.version_date,
                "scope": doc.scope, "paragraph_id": pid, "snippet": text, "score": round(s, 3),
            })
        return results


# ---------- 评测指标 ----------

def rank_doc_ids(hits: list[dict]) -> list[str]:
    """按段落命中顺序得到去重的文档 ID 列表。"""
    seen = []
    for h in hits:
        if h["doc_id"] not in seen:
            seen.append(h["doc_id"])
    return seen


def recall_at_k(expected: list[str], ranked: list[str], k: int) -> float:
    return len(set(expected) & set(ranked[:k])) / len(expected)


def reciprocal_rank(expected: list[str], ranked: list[str]) -> float:
    """第一个期望文档的排名倒数；未命中为 0。"""
    for i, d in enumerate(ranked, 1):
        if d in expected:
            return 1 / i
    return 0.0
