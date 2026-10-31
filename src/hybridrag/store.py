"""Stage 4 - One SQLite file, two indexes over the same chunks.

  chunks       the text plus provenance (source, page, entity, department)
  vec_chunks   sqlite-vec vec0, cosine distance        -> semantic / vector search
  fts_chunks   FTS5 over CJK-aware tokens, BM25 ranking -> keyword search

Both indexes use rowid = chunks.id, so a chunk found by either index is the same row.
That shared key is what makes fusing the two result lists trivial.

Why FTS5 stores our tokens instead of the raw text: FTS5's default tokenizer splits on
spaces and punctuation, so a Chinese clause becomes one giant token and searching a
two-character word inside it finds nothing. We tokenize with cjk_tokenize.tokenize()
(bigrams for CJK) and give FTS5 the space-separated result.

Thread safety: an agent may call tools in parallel threads; one sqlite3 connection must
never be used by two threads at once, so every method takes the same lock.
"""

from __future__ import annotations

import sqlite3
import struct
import threading
from dataclasses import dataclass
from pathlib import Path

import sqlite_vec

from .cjk_tokenize import VERSION as TOKENIZER_VERSION
from .cjk_tokenize import tokenize


@dataclass(frozen=True)
class Row:
    id: int
    source: str
    page: int | None
    chunk_index: int
    text: str
    entity: str
    department: str
    period: str = ""


def _pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


class Store:
    def __init__(self, path: str | Path, embedder_name: str, dim: int):
        self.path = str(path)
        self.dim = dim
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)  # access is serialised by self._lock
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)
        self._init_schema(embedder_name)

    def _init_schema(self, embedder_name: str) -> None:
        try:
            self.db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)")
            self.db.execute("DROP TABLE _fts5_probe")
        except sqlite3.OperationalError as e:
            raise RuntimeError("This SQLite build has no FTS5; use a Python from python.org or uv.") from e
        self.db.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS chunks(
                id INTEGER PRIMARY KEY, source TEXT NOT NULL, page INTEGER, chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL, entity TEXT NOT NULL DEFAULT '', department TEXT NOT NULL DEFAULT '',
                period TEXT NOT NULL DEFAULT '');
            CREATE INDEX IF NOT EXISTS chunks_source ON chunks(source);
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[{self.dim}] distance_metric=cosine);
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(tokens, tokenize="unicode61 tokenchars '-_'");
            """
        )
        for key, value in (("embedder", f"{embedder_name}|{self.dim}"), ("tokenizer", TOKENIZER_VERSION),
                           ("schema", "chunks-with-period")):  # older indexes lack the period column: reset them
            row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            if row and row[0] != value:
                raise RuntimeError(f"Index was built with {key} {row[0]!r}, now {value!r}. Run `hrag reset` and re-index.")
            self.db.execute("INSERT OR REPLACE INTO meta VALUES(?, ?)", (key, value))
        self.db.commit()

    # --- write -----------------------------------------------------------------
    def add(self, chunks, vectors: list[list[float]]) -> None:
        with self._lock:
            for c, vec in zip(chunks, vectors, strict=True):
                cur = self.db.execute(
                    "INSERT INTO chunks(source, page, chunk_index, text, entity, department, period) VALUES(?,?,?,?,?,?,?)",
                    (c.source, c.page, c.index, c.text, c.entity, c.department, c.period),
                )
                self.db.execute("INSERT INTO vec_chunks(rowid, embedding) VALUES(?,?)", (cur.lastrowid, _pack(vec)))
                self.db.execute("INSERT INTO fts_chunks(rowid, tokens) VALUES(?,?)", (cur.lastrowid, " ".join(tokenize(c.text))))
            self.db.commit()

    def delete_source(self, source: str) -> None:
        with self._lock:
            ids = [(r[0],) for r in self.db.execute("SELECT id FROM chunks WHERE source=?", (source,))]
            self.db.executemany("DELETE FROM vec_chunks WHERE rowid=?", ids)
            self.db.executemany("DELETE FROM fts_chunks WHERE rowid=?", ids)
            self.db.execute("DELETE FROM chunks WHERE source=?", (source,))
            self.db.commit()

    # --- read ------------------------------------------------------------------
    def vector_search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        """(chunk id, cosine similarity), best first."""
        with self._lock:
            rows = self.db.execute(
                "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ? ORDER BY distance",
                (_pack(vector), k),
            ).fetchall()
        return [(rid, 1.0 - dist) for rid, dist in rows]

    def keyword_search(self, tokens: list[str], k: int) -> list[tuple[int, float]]:
        """(chunk id, BM25 score), best first. FTS5's bm25() is negative-is-better, so we flip it."""
        terms = list(dict.fromkeys(tokens))  # de-duplicate, keep order
        if not terms:
            return []
        query = " OR ".join(f'"{t}"' for t in terms)  # any term may match; BM25 rewards matching more of them
        with self._lock:
            rows = self.db.execute(
                "SELECT rowid, bm25(fts_chunks) FROM fts_chunks WHERE fts_chunks MATCH ? ORDER BY bm25(fts_chunks) LIMIT ?",
                (query, k),
            ).fetchall()
        return [(rid, -score) for rid, score in rows]

    def get(self, ids: list[int]) -> dict[int, Row]:
        if not ids:
            return {}
        marks = ",".join("?" * len(ids))
        with self._lock:
            rows = self.db.execute(
                f"SELECT id, source, page, chunk_index, text, entity, department, period FROM chunks WHERE id IN ({marks})", ids
            ).fetchall()
        return {r[0]: Row(*r) for r in rows}

    def count(self) -> int:
        with self._lock:
            return self.db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    def sources(self) -> list[tuple[str, str, str, int]]:
        with self._lock:
            return self.db.execute(
                "SELECT source, entity, department, COUNT(*) FROM chunks GROUP BY source, entity, department ORDER BY source"
            ).fetchall()

    def close(self) -> None:
        with self._lock:
            self.db.close()


def reset_db(path: str | Path) -> bool:
    removed = False
    for suffix in ("", "-wal", "-shm", "-journal"):
        p = Path(str(path) + suffix)
        if p.exists():
            p.unlink()
            removed = True
    return removed
