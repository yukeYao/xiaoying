"""加载合成文档。

文档格式（Markdown）：
    doc_id: D01
    title: ...
    version_date: 2023-03-01
    scope: ...（可为空）
    ---
    段落 1

    段落 2
段落按空行切分，依次编号为 P1、P2 ...
"""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "data" / "docs"


@dataclass
class Doc:
    doc_id: str
    title: str
    version_date: str
    scope: str
    paragraphs: dict[str, str]  # {"P1": "原文", ...}


def parse_doc(text: str) -> Doc:
    text = text.replace("\r\n", "\n")
    header, body = text.split("\n---\n", 1)
    meta = {}
    for line in header.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    parts = [p.strip() for p in body.split("\n\n") if p.strip()]
    paragraphs = {f"P{i}": p for i, p in enumerate(parts, 1)}
    return Doc(meta["doc_id"], meta["title"], meta["version_date"], meta.get("scope", ""), paragraphs)


def load_docs(data_dir: str | Path = DEFAULT_DATA_DIR) -> dict[str, Doc]:
    docs = {}
    for path in sorted(Path(data_dir).glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        doc = parse_doc(path.read_text(encoding="utf-8"))
        docs[doc.doc_id] = doc
    if not docs:
        raise FileNotFoundError(f"no documents found in {data_dir}")
    return docs
