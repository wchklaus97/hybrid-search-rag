"""Stage 5 - Retrieval: vector, keyword (BM25), hybrid, and reranked variants.

  vector          embed the query, nearest chunks by cosine            (meaning, synonyms, other languages)
  keyword         BM25 over CJK-aware tokens                           (exact terms: FIN-07, HKD 5,000, PDPO)
  hybrid          both lists merged with Reciprocal Rank Fusion        (fusion.py, copied from repo 2)
  *+rerank        a cross-encoder re-scores the top `pool` candidates  (rerank.py)

Every Hit keeps `stages`: its rank and score in each list it came from, so you can see
WHY a chunk ranked where it did.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .cjk_tokenize import tokenize
from .fusion import fuse

MODES = ("vector", "keyword", "hybrid", "vector+rerank", "hybrid+rerank")


@dataclass
class Hit:
    id: int
    source: str
    page: int | None
    chunk_index: int
    text: str
    entity: str
    department: str
    score: float
    stages: dict[str, tuple[int, float]] = field(default_factory=dict)  # stage -> (1-based rank, raw score)


class Retriever:
    def __init__(self, store, embedder, reranker=None, pool: int = 20, fusion_method: str = "rrf"):
        self.store = store
        self.embedder = embedder
        self.reranker = reranker
        self.pool = pool
        self.fusion_method = fusion_method

    def search(self, query: str, k: int = 3, mode: str = "hybrid+rerank",
               department: str | None = None, entity: str | None = None) -> list[Hit]:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if mode.endswith("+rerank") and self.reranker is None:
            raise LookupError(f"mode {mode!r} needs a reranker: pip install -e '.[local]' (or reranker = 'none' and a non-rerank mode)")
        if not query.strip() or self.store.count() == 0:
            return []

        filtering = bool(department or entity)
        depth = self.pool * (5 if filtering else 1)  # filters run after search, so dig deeper

        lists: dict[str, list[tuple[int, float]]] = {}
        if mode != "keyword":
            lists["vector"] = self.store.vector_search(self.embedder.embed([query])[0], depth)
        if mode in ("keyword", "hybrid", "hybrid+rerank"):
            lists["keyword"] = self.store.keyword_search(tokenize(query), depth)

        merged = fuse(lists, self.fusion_method)  # one list in -> same order out; two lists -> RRF
        rows = self.store.get([f.key for f in merged])
        hits = [
            Hit(r.id, r.source, r.page, r.chunk_index, r.text, r.entity, r.department, f.score, dict(f.parts))
            for f in merged
            if (r := rows.get(f.key)) and (not department or r.department == department) and (not entity or r.entity == entity)
        ]

        if mode.endswith("+rerank"):
            candidates = hits[: self.pool]
            scores = self.reranker.score(query, [h.text for h in candidates])
            ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
            for rank, (hit, s) in enumerate(ranked, start=1):
                hit.stages["rerank"] = (rank, s)
                hit.score = s
            hits = [hit for hit, _ in ranked]
        return hits[:k]
