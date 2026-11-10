"""确定性测试：文档加载、分词与同义词扩展、BM25 检索、search_docs / read_doc 工具。不依赖模型。"""
import json

import pytest

from src.kb import ROOT, parse_doc, load_docs
from src.retrieval import (expand_query, load_synonyms, make_tokenizer, rank_doc_ids, recall_at_k,
                           reciprocal_rank, tokenize)
from src.tools import KnowledgeBase

MAIN = ROOT / "data" / "docs"
VARIANT = ROOT / "data" / "variant" / "docs"


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(MAIN)


def top_docs(kb, query, k=3):
    return rank_doc_ids(kb.search_docs(query, top_k=10)["results"])[:k]


# ---------- 文档加载 ----------

def test_parse_doc_metadata_and_paragraph_numbering():
    doc = parse_doc("doc_id: X1\ntitle: 测试\nversion_date: 2024-01-01\nscope:\n---\n第一段\n\n第二段\n")
    assert (doc.doc_id, doc.title, doc.version_date, doc.scope) == ("X1", "测试", "2024-01-01", "")
    assert doc.paragraphs == {"P1": "第一段", "P2": "第二段"}


def test_parse_doc_handles_crlf():
    doc = parse_doc("doc_id: X1\r\ntitle: t\r\nversion_date: d\r\n---\r\n甲\r\n\r\n乙\r\n")
    assert doc.paragraphs == {"P1": "甲", "P2": "乙"}


def test_main_dataset_loads_all_docs_with_metadata():
    docs = load_docs(MAIN)
    assert list(docs) == [f"D{i:02d}" for i in range(1, 11)]
    for d in docs.values():
        assert d.title and d.version_date and d.paragraphs


def test_variant_dataset_differs_as_documented():
    main, variant = load_docs(MAIN), load_docs(VARIANT)
    assert "D02" in main and "D02" not in variant
    assert "30天内" in main["D01"].paragraphs["P2"] and "20天内" in variant["D01"].paragraphs["P2"]
    assert any("优先于" in p for p in main["D05"].paragraphs.values())
    assert not any("优先于" in p for p in variant["D05"].paragraphs.values())


def test_load_docs_empty_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_docs(tmp_path)


# ---------- 分词与同义词扩展 ----------

def test_tokenize_drops_stopwords_and_punctuation():
    tokens = tokenize("年假有多少天？", make_tokenizer(load_synonyms()))
    assert "年假" in tokens and "？" not in tokens and "多少" not in tokens


def test_baseline_tokenizer_has_no_synonym_words():
    # 纯 BM25 基线用独立分词器，不注册同义词："年假"被切开；同义词模式下是整词
    assert tokenize("年假几天", make_tokenizer()) == ["年", "假", "几天"]
    assert tokenize("年假几天", make_tokenizer(load_synonyms())) == ["年假", "几天"]


def test_baseline_tokenization_independent_of_creation_order():
    q = "我入职五年了，带薪休假一年能休多少天"
    before = tokenize(q, KnowledgeBase(MAIN, use_synonyms=False).tokenizer)
    KnowledgeBase(MAIN, use_synonyms=True)  # 创建同义词模式不应影响之后的基线
    after = tokenize(q, KnowledgeBase(MAIN, use_synonyms=False).tokenizer)
    assert before == after


def test_expand_query_adds_group_members():
    assert expand_query("带薪休假能休几天", [["年假", "年休假", "带薪休假"]]) == ["年假", "年休假"]


def test_expand_query_no_match_is_unchanged():
    assert expand_query("股票期权怎么行权", [["年假", "年休假"]]) == []


def test_baseline_does_not_expand():
    assert KnowledgeBase(MAIN, use_synonyms=False).search_docs("年假几天")["expanded_terms"] == []


def test_syn_weight_applies_only_to_expanded_terms():
    kb_w = KnowledgeBase(MAIN, syn_weight=0.5)
    weights, added = kb_w.query_weights("年假几天")
    assert weights["年假"] == 1.0 and weights["几天"] == 1.0
    assert "年休假" in added and weights["年休假"] == 0.5


def test_synonym_expansion_lets_colloquial_term_match_document_term():
    # "年假"不在 D03 原文里（原文是"年休假"），扩展后应命中 D03 第一条
    kb_syn = KnowledgeBase(MAIN, use_synonyms=True)
    hits = kb_syn.search_docs("年假几天", top_k=3)
    assert "年休假" in hits["expanded_terms"]
    assert hits["results"][0]["doc_id"] == "D03"


# ---------- search_docs ----------

def test_search_clear_answer_question(kb):
    assert top_docs(kb, "工作满5年有几天年假")[0] == "D03"


def test_search_conflict_question_returns_both_conflicting_docs(kb):
    assert {"D01", "D02"} <= set(top_docs(kb, "报销期限多久"))


def test_search_result_fields(kb):
    r = kb.search_docs("报销期限多久", top_k=2)["results"][0]
    assert set(r) == {"doc_id", "title", "version_date", "scope", "paragraph_id", "snippet", "score"}
    assert r["score"] > 0


def test_search_respects_top_k(kb):
    assert len(kb.search_docs("报销", top_k=2)["results"]) == 2
    assert len(kb.search_docs("报销", top_k=100)["results"]) <= 10


def test_search_out_of_scope_returns_empty_with_hint(kb):
    out = kb.search_docs("股票期权怎么行权")
    assert out["results"] == [] and "hint" in out


def test_search_empty_query_returns_error(kb):
    assert kb.search_docs("  ")["error"]["type"] == "invalid_argument"


def test_search_results_follow_data_dir():
    # 替换文档后检索结果随之改变：variant 中没有 D02
    kb_v = KnowledgeBase(VARIANT)
    assert "D02" not in top_docs(kb_v, "报销期限多久", k=10)


# ---------- read_doc ----------

def test_read_doc_full(kb):
    out = kb.read_doc("D01")
    assert out["version_date"] == "2023-03-01"
    assert [p["paragraph_id"] for p in out["paragraphs"]] == ["P1", "P2", "P3", "P4", "P5"]


def test_read_doc_selected_paragraphs(kb):
    out = kb.read_doc("D05", ["P3"])
    assert out["scope"] == "差旅费用报销"
    assert out["paragraphs"] == [{"paragraph_id": "P3", "text": "本规定关于差旅费用报销期限的条款优先于公司通用报销规定执行。"}]


def test_read_doc_unknown_doc(kb):
    assert kb.read_doc("D99")["error"]["type"] == "not_found"


def test_read_doc_unknown_paragraph(kb):
    err = kb.read_doc("D01", ["P9"])["error"]
    assert err["type"] == "not_found" and "P9" in err["message"]


# ---------- 检索评测集 ----------

def test_retrieval_eval_file_shape():
    items = [json.loads(l) for l in (ROOT / "data" / "retrieval_eval.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert 15 <= len(items) <= 20
    assert sum(it["split"] == "holdout" for it in items) == 5
    docs = load_docs(MAIN)
    assert all(d in docs for it in items for d in it["expected_doc_ids"])


def test_blind_eval_file_shape():
    items = [json.loads(l) for l in (ROOT / "data" / "retrieval_eval_blind.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(items) == 5 and all(it["split"] == "blind" for it in items)
    docs = load_docs(MAIN)
    assert all(d in docs for it in items for d in it["expected_doc_ids"])


# ---------- 评测指标 ----------

def test_recall_at_k():
    assert recall_at_k(["D01", "D02"], ["D05", "D02", "D01"], 1) == 0.0
    assert recall_at_k(["D01", "D02"], ["D05", "D02", "D01"], 2) == 0.5
    assert recall_at_k(["D01", "D02"], ["D05", "D02", "D01"], 3) == 1.0


def test_reciprocal_rank():
    assert reciprocal_rank(["D01", "D02"], ["D05", "D02", "D01"]) == 0.5
    assert reciprocal_rank(["D09"], ["D03", "D02"]) == 0.0
