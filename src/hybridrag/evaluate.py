"""Evaluation: retrieval quality per mode, plus a replay of the queries a real agent sent.

Same metric as local-rag-sqlite (repo 1), so numbers are comparable: a HIT is a retrieved
chunk from the expected source that CONTAINS the evidence string. Reported: hit@1, hit@k,
MRR@k, overall and per language.

Replay: the agent eval in agent-rag-pydantic-ai (repo 3) saved every query the agent
actually sent to its retrieve tool. `replay_mode` runs those exact queries against each
search mode and checks whether the evidence chunk comes back in the agent's default
top-4. That answers "would the agent's search have found it?" with no LLM calls - with one
caveat: a better first result could have changed what the agent searched next.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class QA:
    id: str
    lang: str
    q: str
    source: str
    evidence: str


@dataclass(frozen=True)
class ReplayItem:
    id: str
    lang: str
    question: str
    source: str
    evidence: str
    queries: tuple[str, ...]


@dataclass
class Result:
    label: str
    hit1: float
    hitk: float
    mrr: float
    by_lang: dict[str, float] = field(default_factory=dict)
    misses: list[str] = field(default_factory=list)


@dataclass
class ReplayResult:
    label: str
    per_item: dict[str, tuple[int, int]]  # id -> (queries that found the evidence, queries sent)

    @property
    def query_hit_rate(self) -> float:
        hits = sum(h for h, _ in self.per_item.values())
        total = sum(n for _, n in self.per_item.values())
        return hits / total if total else 0.0


def load_qa(path: str | Path) -> list[QA]:
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    return [QA(r["id"], r["lang"], r["q"], r["source"], r["evidence"]) for r in rows]


def load_replay(path: str | Path) -> list[ReplayItem]:
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    return [ReplayItem(r["id"], r["lang"], r["question"], r["source"], r["evidence"], tuple(r["queries"])) for r in rows]


def first_hit_rank(hits, source: str, evidence: str) -> int | None:
    for rank, h in enumerate(hits, start=1):
        if h.source == source and evidence in h.text:
            return rank
    return None


def evaluate_mode(retriever, qa: list[QA], mode: str, k: int = 3, label: str = "") -> Result:
    ranks = {q.id: first_hit_rank(retriever.search(q.q, k, mode), q.source, q.evidence) for q in qa}

    def share(items) -> float:
        items = list(items)
        return sum(1 for i in items if ranks[i.id]) / len(items) if items else 0.0

    return Result(
        label=label or mode,
        hit1=sum(1 for q in qa if ranks[q.id] == 1) / len(qa),
        hitk=share(qa),
        mrr=sum(1 / ranks[q.id] for q in qa if ranks[q.id]) / len(qa),
        by_lang={lang: share(q for q in qa if q.lang == lang) for lang in sorted({q.lang for q in qa})},
        misses=[q.id for q in qa if not ranks[q.id]],
    )


def replay_mode(retriever, items: list[ReplayItem], mode: str, k: int = 4, label: str = "") -> ReplayResult:
    per_item = {}
    for item in items:
        found = sum(1 for q in item.queries if first_hit_rank(retriever.search(q, k, mode), item.source, item.evidence))
        per_item[item.id] = (found, len(item.queries))
    return ReplayResult(label or mode, per_item)


def results_table(results: list[Result], k: int, n: int) -> str:
    langs = sorted({lang for r in results for lang in r.by_lang})
    head = f"| run | hit@1 | hit@{k} | MRR@{k} | " + " | ".join(f"hit@{k} {lang}" for lang in langs) + " |"
    sep = "|" + "---|" * (4 + len(langs))
    rows = [
        f"| {r.label} | {r.hit1:.2f} | {r.hitk:.2f} | {r.mrr:.2f} | "
        + " | ".join(f"{r.by_lang.get(lang, 0):.2f}" for lang in langs) + " |"
        for r in results
    ]
    return f"{n} questions, top-k = {k}.\n\n" + "\n".join([head, sep, *rows]) + "\n"


def replay_table(results: list[ReplayResult], items: list[ReplayItem], k: int) -> str:
    head = "| question | " + " | ".join(r.label for r in results) + " |"
    sep = "|" + "---|" * (1 + len(results))
    rows = []
    for item in items:
        cells = []
        for r in results:
            hit, n = r.per_item[item.id]
            cells.append(f"{hit}/{n}")
        rows.append(f"| `{item.id}` | " + " | ".join(cells) + " |")
    rows.append("| **all queries** | " + " | ".join(f"**{r.query_hit_rate:.2f}**" for r in results) + " |")
    return (f"Replayed agent queries; a query counts if the evidence chunk is in the top {k} "
            "(the agent's default k).\n\n" + "\n".join([head, sep, *rows]) + "\n")
