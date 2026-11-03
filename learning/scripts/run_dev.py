"""Run one dev set through hybrid-search-rag with a fixed, pre-declared config, then score it.

Config (fixed before any run; do not tune it on the results):
  corpus    the three source files in --sources (EO PDF, IRD PDF, spending CSV as one row per paragraph)
  chunking  400 / 60
  embedder  local, paraphrase-multilingual-MiniLM-L12-v2
  reranker  BAAI/bge-reranker-v2-m3, refusal cut min_rerank_score 0.05
  expansion glossary (offline)
  mode      hybrid+rerank, top_k 3
  year check  --year-check on|off (the repo default is on)

Scoring: number/version correct if one top-3 chunk holds every key (commas removed);
refusal correct if nothing is returned; lookup/manual is written to a review file.

Run from the repo root:
  uv run --no-sync --extra local python learning/scripts/run_dev.py --sources learning/sources --set dev_set_v5_corrected
"""

import argparse
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEARNING = HERE.parent
REPO = LEARNING.parent
sys.path.insert(0, str(REPO / "src"))

from hybridrag.config import Config  # noqa: E402
from hybridrag.embed import get_embedder  # noqa: E402
from hybridrag.expand import get_expander  # noqa: E402
from hybridrag.index import build_index  # noqa: E402
from hybridrag.rerank import get_reranker  # noqa: E402
from hybridrag.retrieve import Retriever  # noqa: E402
from hybridrag.store import Store  # noqa: E402

CSV_NAME = "spending_data_head26_2025-26_Q4_en.csv"


def build_corpus(sources: Path, work: Path) -> Path:
    """Copy the PDFs and turn the CSV into one text row per line, so the chunker can read it."""
    corpus = work / "corpus"
    corpus.mkdir(parents=True)
    for pdf in sources.glob("*.pdf"):
        shutil.copy(pdf, corpus / pdf.name)
    lines = [
        "# Head 26 spending, 2025-26 Q4 (Census and Statistics Department)",
        "",
        "Source: data.gov.hk dataset `hk-censtatd-spending-spending-data`. Amounts are in HKD ($).",
        "",
    ]
    with open(sources / CSV_NAME, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            amount = f"{float(row['Actual ($)']):,.2f}"
            lines.append(
                f"Expenditure group: {row['Expenditure Group']}. "
                f"Subhead: {row['Subhead']} {row['Subhead Description']}. "
                f"Item: {row['Item']} {row['Item Description']}. "
                f"Actual ($): {amount}."
            )
            lines.append("")
    (corpus / "spending_data_head26_2025-26_Q4_en.md").write_text("\n".join(lines), encoding="utf-8")
    return corpus


def norm(s: str) -> str:
    return s.replace(",", "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True, type=Path)
    ap.add_argument("--set", required=True, help="dev set name, e.g. dev_set_v1 (file in learning/dev_sets)")
    ap.add_argument("--year-check", choices=["on", "off"], default="on")
    ap.add_argument("--out", type=Path, default=LEARNING / "results")
    args = ap.parse_args()

    questions = [json.loads(l) for l in (LEARNING / "dev_sets" / f"{args.set}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    keys = json.loads((LEARNING / "dev_sets" / f"{args.set}_keys.json").read_text(encoding="utf-8"))

    work = Path(tempfile.mkdtemp(prefix="hrag_dev_"))
    cfg = Config(
        db_path=str(work / "dev.db"), chunk_size=400, chunk_overlap=60, embed_provider="local", top_k=3,
        reranker="cross-encoder", reranker_model="BAAI/bge-reranker-v2-m3", expand="glossary",
        glossary=str(REPO / "examples" / "glossary.csv"), expand_cache=str(work / "expansions.jsonl"),
        min_rerank_score=0.05,
    )
    corpus = build_corpus(args.sources, work)
    emb = get_embedder(cfg.embed_provider, cfg.embed_model)
    store = Store(cfg.db_path, emb.name, emb.dim)
    print(f"index: {build_index([corpus], cfg, emb, store, log=print)} chunks")
    retriever = Retriever(
        store, emb, get_reranker(cfg.reranker, cfg.reranker_model), cfg.pool,
        expander=get_expander(cfg.expand, cfg.glossary, cfg.expand_model, cfg.expand_cache),
        min_rerank_score=cfg.min_rerank_score, refuse_unknown_period=args.year_check == "on",
    )

    results, review, verdicts = [], [], {}
    for q in questions:
        hits = retriever.search(q["q"], cfg.top_k, "hybrid+rerank")
        top = [{"source": h.source, "chunk": h.chunk_index, "text": " ".join(h.text.split())} for h in hits]
        k = keys[q["id"]]
        if k["method"] == "refusal":
            v = "correct" if not hits else "wrong"
        elif k["method"] == "keys":
            v = "correct" if any(all(norm(t) in norm(h["text"]) for t in k["keys"]) for h in top) else "wrong"
        else:
            v = "manual"
            review.append({"id": q["id"], "q": q["q"], "expected": q["expected"], "top": top})
        verdicts[q["id"]] = v
        results.append({"id": q["id"], "type": q["type"], "verdict": v, "top": top})

    args.out.mkdir(parents=True, exist_ok=True)
    stem = f"{args.set}_yearcheck_{args.year_check}"
    (args.out / f"{stem}_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / f"{stem}_manual_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    scored = [v for v in verdicts.values() if v in ("correct", "wrong")]
    print(f"{stem}: auto {sum(v == 'correct' for v in scored)}/{len(scored)}, manual {len(review)}")
    store.close()
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
