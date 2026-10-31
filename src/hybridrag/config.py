"""Configuration from hrag.toml, overridden by env vars (values are cast to the field's type)."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass
class Config:
    db_path: str = "hrag.db"
    chunk_size: int = 400
    chunk_overlap: int = 60
    embed_provider: str = "local"
    embed_model: str = ""
    top_k: int = 3
    mode: str = "hybrid+rerank"
    pool: int = 20
    reranker: str = "cross-encoder"
    reranker_model: str = ""
    expand: str = "glossary"
    glossary: str = "examples/glossary.csv"
    expand_model: str = "openai/gpt-4o-mini"
    expand_cache: str = "eval/llm_expansions.jsonl"
    # Refusal: for +rerank modes, return nothing when the top reranker score is below this.
    # Calibrated for bge-reranker-v2-m3 only (eval/RESULTS.md section 8). None = never refuse.
    min_rerank_score: float | None = None


_ENV = {"RAG_DB": "db_path", "EMBED_PROVIDER": "embed_provider", "EMBED_MODEL": "embed_model",
        "SEARCH_MODE": "mode", "RERANKER": "reranker", "RERANKER_MODEL": "reranker_model",
        "EXPAND": "expand", "EXPAND_MODEL": "expand_model", "EXPAND_CACHE": "expand_cache"}


def load_config(path: str | os.PathLike | None = None) -> Config:
    path = Path(path or os.environ.get("HRAG_CONFIG", "hrag.toml"))
    values = tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    known = {f.name for f in fields(Config)}
    cfg = Config(**{k: v for k, v in values.items() if k in known})
    for env, attr in _ENV.items():
        if os.environ.get(env):
            setattr(cfg, attr, type(getattr(cfg, attr))(os.environ[env]))
    return cfg
