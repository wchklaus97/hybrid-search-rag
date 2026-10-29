"""Stage 6 - Reranking with a cross-encoder.

A bi-encoder (embed.py) turns the query and each passage into vectors SEPARATELY and
compares them. That is fast enough to scan the whole corpus, but the model never sees
the two texts side by side.

A cross-encoder reads the query and ONE passage TOGETHER and outputs a relevance score.
It is much more accurate - and far too slow to run over a whole corpus. So hybrid search
retrieves a cheap candidate pool first (vector + BM25), then reranks only that pool.

Default model: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 - multilingual, trained on
mMARCO (MS MARCO machine-translated into 14 languages, Chinese included).
"""

from __future__ import annotations

import sys
from typing import Protocol

DEFAULT_RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


class Reranker(Protocol):
    name: str

    def score(self, query: str, texts: list[str]) -> list[float]: ...


class CrossEncoderReranker:
    def __init__(self, model: str = DEFAULT_RERANKER):
        from sentence_transformers import CrossEncoder  # optional dependency: pip install -e '.[local]'

        self._model = CrossEncoder(model)
        self.name = f"cross-encoder:{model}"

    def score(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        return [float(s) for s in self._model.predict([(query, t) for t in texts])]


def get_reranker(name: str, model: str = "") -> Reranker | None:
    """Returns None (with an explanation) when reranking is off or unavailable."""
    if name == "none":
        return None
    if name == "cross-encoder":
        try:
            return CrossEncoderReranker(model or DEFAULT_RERANKER)
        except ImportError:
            print("note: reranking skipped - sentence-transformers not installed (pip install -e '.[local]')", file=sys.stderr)
            return None
    raise ValueError(f"unknown reranker {name!r} (cross-encoder | none)")
