"""Stage 5 - Retrieval: vector, keyword (BM25), hybrid, and reranked variants.

  vector          embed the query, nearest chunks by cosine            (meaning, synonyms, other languages)
  keyword         BM25 over CJK-aware tokens                           (exact terms: FIN-07, HKD 5,000, PDPO)
  hybrid          both lists merged with Reciprocal Rank Fusion        (fusion.py, copied from repo 2)
  *+rerank        a cross-encoder re-scores the top `pool` candidates  (rerank.py)

With an expander (expand.py), each retriever also runs on every expanded query, and all
the lists are fused together: `keyword:x1` is BM25 on the first expansion. Expansion only
widens the candidate pool (which grows by `pool` per query version). The reranker still
scores against the ORIGINAL query, so a loose translation can bring a chunk in but cannot
decide the final order.

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
    period: str = ""  # e.g. "2025-26", from the document's opening text (metadata, not used for ranking)


def _list_name(retriever: str, n: int) -> str:
    return retriever if n == 0 else f"{retriever}:x{n}"


class Retriever:
    def __init__(self, store, embedder, reranker=None, pool: int = 20, fusion_method: str = "rrf", expander=None,
                 min_rerank_score: float | None = None):
        self.store = store
        self.embedder = embedder
        self.reranker = reranker
        self.pool = pool
        self.fusion_method = fusion_method
        self.expander = expander
        self.min_rerank_score = min_rerank_score  # None = never refuse; see Config.min_rerank_score

    def queries(self, query: str) -> list[str]:
        """The original query first, then its expansions (none without an expander)."""
        return [query, *(self.expander.expand(query) if self.expander else [])]

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

        queries = self.queries(query)
        lists: dict[str, list[tuple[int, float]]] = {}
        if mode != "keyword":
            for n, vec in enumerate(self.embedder.embed(queries)):
                lists[_list_name("vector", n)] = self.store.vector_search(vec, depth)
        if mode in ("keyword", "hybrid", "hybrid+rerank"):
            for n, q in enumerate(queries):
                lists[_list_name("keyword", n)] = self.store.keyword_search(tokenize(q), depth)

        merged = fuse(lists, self.fusion_method)  # one list in -> same order out; several lists -> RRF
        rows = self.store.get([f.key for f in merged])
        hits = [
            Hit(r.id, r.source, r.page, r.chunk_index, r.text, r.entity, r.department, f.score, dict(f.parts), r.period)
            for f in merged
            if (r := rows.get(f.key)) and (not department or r.department == department) and (not entity or r.entity == entity)
        ]

        if mode.endswith("+rerank"):
            # Each query version brings its own pool. With a fixed pool, RRF's taste for chunks that
            # several lists agree on pushes a chunk found by ONE expanded list just past the cut.
            candidates = hits[: self.pool * len(queries)]
            scores = self.reranker.score(query, [h.text for h in candidates])  # the user's words, not the expansions
            ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
            for rank, (hit, s) in enumerate(ranked, start=1):
                hit.stages["rerank"] = (rank, s)
                hit.score = s
            hits = [hit for hit, _ in ranked]
            if self.min_rerank_score is not None and hits and hits[0].score < self.min_rerank_score:
                return []  # nothing in the corpus matches well enough: refuse rather than return a near miss
        return hits[:k]
