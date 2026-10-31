"""Conversation memory as RAG: raw turns are the source of truth; the index has two kinds of entries.

  window  every turn with the two before it, as one passage (keeps history: "what was it before?")
  fact    the LATEST value per key, written as one sentence (answers "what is it now?")

Facts are supersession-aware: a newer value for the same key replaces the old one in the index,
but the old turn stays in the window passages. Facts come from the `facts` labels in turns.jsonl.
That stands in for an extractor (LLM or rules), which is still an open piece.

Variants:
  windows only          no fact entries (what plain conversation RAG does)
  windows + latest      fact entries added (this prototype)

Run from the repo venv, with the MiniLM embedder already cached:
  uv run --extra local python conversation-rag/run.py   (from the repo root)
"""

import json
import os
import sys
import tempfile
from pathlib import Path

here = Path(__file__).parent
sys.path.insert(0, str(here.parent / "src"))  # use this repo's own pipeline code

from hybridrag.chunk import Chunk  # noqa: E402
from hybridrag.embed import get_embedder  # noqa: E402
from hybridrag.retrieve import Retriever  # noqa: E402
from hybridrag.store import Store  # noqa: E402

WINDOW = 3  # the turn itself and the two before it


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def superseded_notes(turns: list[dict]) -> dict[int, list[str]]:
    """For each turn, a note per fact it set that a later turn changed (the valid_to of that fact).

    A later turn only counts when the value really changes; restating the same value is not a change.
    """
    notes: dict[int, list[str]] = {}
    for i, t in enumerate(turns):
        for f in t.get("facts", []):
            for later in turns[i + 1:]:
                newer = [g for g in later.get("facts", []) if g["key"] == f["key"] and g["value"] != f["value"]]
                if newer:
                    notes.setdefault(t["turn"], []).append(
                        f"〔已過時：{f['label']} 其後於第 {later['turn']} 輪改為 {newer[0]['value']}〕")
                    break
    return notes


def window_chunks(turns: list[dict], stale_notes: bool = False) -> list[Chunk]:
    notes = superseded_notes(turns) if stale_notes else {}
    chunks = []
    for i in range(len(turns)):
        span = turns[max(0, i - WINDOW + 1): i + 1]
        lines = []
        for t in span:
            line = f"第{t['turn']}輪 {t['role']}: {t['text']}"
            lines.append(" ".join([line, *notes.get(t["turn"], [])]))
        chunks.append(Chunk("conversation", None, i, "\n".join(lines)))
    return chunks


def latest_fact_chunks(turns: list[dict]) -> list[Chunk]:
    latest: dict[str, tuple[dict, int]] = {}
    for t in turns:  # turns are in order, so the last one wins
        for f in t.get("facts", []):
            latest[f["key"]] = (f, t["turn"])
    return [
        Chunk("facts", None, n, f"{f['label']}：{f['value']}（由第 {turn} 輪起，最新）")
        for n, (f, turn) in enumerate(latest.values())
    ]


def run_variant(name: str, chunks: list[Chunk], questions: list[dict], emb, retriever_factory, mode: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "conv.db", emb.name, emb.dim)
        store.add(chunks, emb.embed([c.text for c in chunks]))
        retriever = retriever_factory(store)
        rows = []
        for q in questions:
            hits = retriever.search(q["q"], 3, mode)
            top1 = hits[0].text if hits else ""
            rows.append({"variant": name, "id": q["id"], "kind": q["kind"],
                         "top1_ok": q["expect"] in top1, "top3_ok": any(q["expect"] in h.text for h in hits),
                         "top1": " ".join(top1.split())[:90]})
        store.close()
    return rows


def main() -> None:
    turns = load(here / "turns.jsonl")
    questions = load(here / "questions.jsonl")
    if os.environ.get("EXTRACTED"):  # facts from extract.py instead of the hand labels
        extracted = json.loads((here / "extracted_facts.json").read_text(encoding="utf-8"))
        for t in turns:
            t["facts"] = extracted.get(str(t["turn"]), [])
    emb = get_embedder("local", "")
    windows = window_chunks(turns)
    facts = latest_fact_chunks(turns)

    # RERANK=bge runs the same variants again with the bge cross-encoder on top of hybrid.
    rerank_name = os.environ.get("RERANK")
    reranker = None
    if rerank_name:
        from hybridrag.rerank import get_reranker  # noqa: E402

        reranker = get_reranker("cross-encoder", rerank_name)
    mode = "hybrid+rerank" if reranker else "hybrid"

    def factory(store):
        return Retriever(store, emb, reranker, pool=20)

    stale = window_chunks(turns, stale_notes=True)
    variants = [
        ("windows only", windows, None),
        ("windows + latest", windows + facts, None),
        ("+ stale notes", stale + facts, None),
    ]
    rows = []
    for name, chunks, _ in variants:
        rows += run_variant(name, chunks, questions, emb, factory, mode)

    print(f"mode: {mode}" + (f" ({rerank_name})" if reranker else ""))
    print(f"{'id':<18}{'kind':<9}{'variant':<20}{'top1':<7}{'top3':<7}top-1 text")
    for r in rows:
        print(f"{r['id']:<18}{r['kind']:<9}{r['variant']:<20}{str(r['top1_ok']):<7}{str(r['top3_ok']):<7}{r['top1']}")
    for variant in ("windows only", "windows + latest", "+ stale notes"):
        mine = [r for r in rows if r["variant"] == variant]
        for kind in ("current", "history"):
            sub = [r for r in mine if r["kind"] == kind]
            print(f"{variant:<20} {kind:<8} top-1 {sum(r['top1_ok'] for r in sub)}/{len(sub)}   top-3 {sum(r['top3_ok'] for r in sub)}/{len(sub)}")
    tag = ("extracted" if os.environ.get("EXTRACTED") else "labels") + "-" + (rerank_name.split("/")[-1] if rerank_name else "hybrid")
    out = here / f"run-{tag}.json"
    out.write_text(json.dumps({"turns": len(turns), "windows": len(windows), "facts": len(facts), "rows": rows},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
