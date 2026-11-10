"""检索评测：对比三种检索模式的 recall@1 / recall@3 / MRR。

模式：
  bm25        纯 BM25，不加载同义词（独立分词器，不注册同义词）
  syn_w1.0    BM25 + 同义词扩展，扩展词权重 1.0（与原词相同）
  syn_w{W}    BM25 + 同义词扩展，扩展词降权为 W（--syn-weight，默认 0.5）

指标按段落检索结果（top_k=10）去重得到文档排名后计算：
  recall@k  期望文档出现在前 k 个文档中的比例（期望有 n 份时，recall@1 上限为 1/n）
  MRR       第一个期望文档排名的倒数，取平均

另外检查冲突类问题（期望同时包含 D01 和 D02）在 search_docs(top_k=5) 时两份是否都被返回。

用法：python scripts/eval_retrieval.py [--data-dir data/docs] [--syn-weight 0.5]
结果打印到终端，并写入 examples/retrieval_eval_results.md。
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.retrieval import rank_doc_ids, recall_at_k, reciprocal_rank  # noqa: E402
from src.tools import KnowledgeBase  # noqa: E402

CONFLICT_PAIR = {"D01", "D02"}


def display_path(p):
    p = Path(p).resolve()
    return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.name


def load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def evaluate(items, modes):
    """返回 {mode: {id: {"ranked", "r1", "r3", "rr", "top5_docs"}}}"""
    out = {}
    for m, kb in modes.items():
        out[m] = {}
        for it in items:
            ranked = rank_doc_ids(kb.search_docs(it["query"], top_k=10)["results"])
            top5 = rank_doc_ids(kb.search_docs(it["query"], top_k=5)["results"])
            exp = it["expected_doc_ids"]
            out[m][it["id"]] = {"ranked": ranked, "r1": recall_at_k(exp, ranked, 1),
                                "r3": recall_at_k(exp, ranked, 3), "rr": reciprocal_rank(exp, ranked),
                                "top5_docs": top5}
    return out


def summary_table(items, res, splits):
    lines = ["| 子集 | 题数 | 模式 | recall@1 | recall@3 | MRR |", "|---|---|---|---|---|---|"]
    for split in splits:
        ids = [it["id"] for it in items if split == "all" or it["split"] == split]
        for m in res:
            avg = {k: sum(res[m][i][k] for i in ids) / len(ids) for k in ("r1", "r3", "rr")}
            lines.append(f"| {split} | {len(ids)} | {m} | {avg['r1']:.3f} | {avg['r3']:.3f} | {avg['rr']:.3f} |")
    return lines


def detail_table(items, res):
    modes = list(res)
    lines = ["| ID | 问题 | 期望 | " + " | ".join(f"{m} top3 (R@1/R@3/RR)" for m in modes) + " |",
             "|---|---|---|" + "---|" * len(modes)]
    for it in items:
        cells = []
        for m in modes:
            r = res[m][it["id"]]
            cells.append(f"{','.join(r['ranked'][:3]) or '-'} ({r['r1']:.2f}/{r['r3']:.2f}/{r['rr']:.2f})")
        lines.append(f"| {it['id']} | {it['query']} | {','.join(it['expected_doc_ids'])} | " + " | ".join(cells) + " |")
    return lines


def conflict_table(items, res):
    conflict = [it for it in items if CONFLICT_PAIR <= set(it["expected_doc_ids"])]
    lines = ["| ID | 问题 | 模式 | top_k=5 返回的文档 | D01、D02 都返回 |", "|---|---|---|---|---|"]
    for it in conflict:
        for m in res:
            docs = res[m][it["id"]]["top5_docs"]
            ok = "是" if CONFLICT_PAIR <= set(docs) else "**否**"
            lines.append(f"| {it['id']} | {it['query']} | {m} | {','.join(docs)} | {ok} |")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(ROOT / "data" / "docs"))
    ap.add_argument("--eval-file", default=str(ROOT / "data" / "retrieval_eval.jsonl"))
    ap.add_argument("--blind-file", default=str(ROOT / "data" / "retrieval_eval_blind.jsonl"))
    ap.add_argument("--syn-weight", type=float, default=0.5, help="降权模式中同义扩展词的权重")
    ap.add_argument("--out", default=str(ROOT / "examples" / "retrieval_eval_results.md"))
    args = ap.parse_args()

    modes = {"bm25": KnowledgeBase(args.data_dir, use_synonyms=False),
             "syn_w1.0": KnowledgeBase(args.data_dir, syn_weight=1.0),
             f"syn_w{args.syn_weight}": KnowledgeBase(args.data_dir, syn_weight=args.syn_weight)}

    items = load_jsonl(args.eval_file)
    res = evaluate(items, modes)
    n_hold = sum(it["split"] == "holdout" for it in items)

    lines = ["# 检索评测结果", "",
             f"数据目录：`{display_path(args.data_dir)}`。由 `scripts/eval_retrieval.py` 生成，指标定义见脚本开头注释。", "",
             "## 1. 开发集 + 留出集（data/retrieval_eval.jsonl）", "",
             f"共 {len(items)} 条，其中 holdout {n_hold} 条（同义词表定稿后编写，未参考）。", ""]
    lines += summary_table(items, res, ["all", "dev", "holdout"])
    lines += ["", "### 逐题结果", ""] + detail_table(items, res)
    lines += ["", "### 冲突类问题：search_docs(top_k=5) 是否同时返回 D01 和 D02", ""] + conflict_table(items, res)

    if Path(args.blind_file).exists():
        blind = load_jsonl(args.blind_file)
        bres = evaluate(blind, modes)
        lines += ["", "## 2. 盲测集（data/retrieval_eval_blind.jsonl）", "",
                  "问题由项目作者本人编写，Claude Code 只负责标注期望 doc_id，未据此修改同义词表。单独报告。", ""]
        lines += summary_table(blind, bres, ["all"])
        lines += ["", "### 逐题结果", ""] + detail_table(blind, bres)
        lines += ["", "### 标注说明", ""] + [f"- {it['id']}：{it.get('note', '')}" for it in blind]

    text = "\n".join(lines) + "\n"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
