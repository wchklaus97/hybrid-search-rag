"""Plug this repo's retriever into the agent from agent-rag-pydantic-ai (repo 3).

Repo 3's lift-out module (tools.py) defines a tiny `Searcher` contract:

    search(query, k, department) -> list[Snippet]        sources() -> list[SourceInfo]

Anything that satisfies it can sit behind the agent's `retrieve` tool. HybridSearcher is
the proof that the contract travels between repos: same agent, same prompt, same
validator, same eval - only the search behind the tool changes.

Needs: pip install -e '.[agent]'   (installs agent-rag-pydantic-ai from GitHub)
"""

from __future__ import annotations

import threading


class HybridSearcher:
    def __init__(self, retriever, mode: str = "hybrid+rerank"):
        self.retriever = retriever
        self.mode = mode
        self._lock = threading.Lock()  # the agent runs tools in worker threads; the cross-encoder is shared

    def search(self, query: str, k: int, department: str | None = None):
        from agentrag.tools import Snippet

        with self._lock:
            hits = self.retriever.search(query, k, self.mode, department=department)
        return [
            Snippet(source=h.source, page=h.page, entity=h.entity, department=h.department, text=h.text, score=round(h.score, 4))
            for h in hits
        ]

    def sources(self):
        from agentrag.tools import SourceInfo

        return [SourceInfo(source=s, entity=e, department=d, chunks=n) for s, e, d, n in self.retriever.store.sources()]
