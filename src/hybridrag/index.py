"""Stages 1-4 glue: Ingest -> Chunk -> Embed -> Store (vector index AND keyword index)."""

from __future__ import annotations

from typing import Callable

from .chunk import chunk_documents
from .ingest import load_documents


def build_index(folders, cfg, embedder, store, log: Callable[[str], None] = lambda _m: None, batch_size: int = 64) -> int:
    docs = [d for folder in folders for d in load_documents(folder)]
    log(f"[1/4 ingest]  {len(docs)} documents from {', '.join(map(str, folders))}")
    chunks = chunk_documents(docs, cfg.chunk_size, cfg.chunk_overlap)
    log(f"[2/4 chunk]   {len(chunks)} chunks (size={cfg.chunk_size}, overlap={cfg.chunk_overlap})")
    for source in {c.source for c in chunks}:
        store.delete_source(source)
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        store.add(batch, embedder.embed([c.text for c in batch]))
    log(f"[3/4 embed]   {embedder.name}")
    log(f"[4/4 store]   {store.path}: sqlite-vec (vectors) + FTS5 (BM25 over CJK bigrams)")
    return len(chunks)
