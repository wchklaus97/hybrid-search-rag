import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from hybridrag.chunk import Chunk
from hybridrag.cjk_tokenize import tokenize
from hybridrag.store import Store

LEAK = "如懷疑資料外洩，須喺 24 小時內通知 Compliance Officer"


def test_why_this_repo_exists_default_fts5_cannot_find_chinese_words():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE VIRTUAL TABLE t USING fts5(body)")
    db.execute("INSERT INTO t VALUES (?)", (LEAK,))
    assert db.execute("SELECT count(*) FROM t WHERE t MATCH '\"外洩\"'").fetchone()[0] == 0  # the problem


def test_cjk_tokens_make_fts5_find_chinese_words(tmp_path):
    store = Store(tmp_path / "t.db", "test", 3)
    store.add([Chunk("c.md", None, 0, LEAK), Chunk("x.md", None, 0, "Taxi fares above HKD 300")], [[1, 0, 0], [0, 1, 0]])
    (top_id, score), *_ = store.keyword_search(tokenize("資料外洩"), 5)
    assert store.get([top_id])[top_id].source == "c.md" and score > 0
    assert store.keyword_search(tokenize("the and how"), 5) == []  # stop-words only: nothing to search


def test_both_indexes_share_ids_and_delete_together(tmp_path):
    store = Store(tmp_path / "t.db", "test", 3)
    store.add([Chunk("a.md", None, 0, "annual leave 年假"), Chunk("b.md", None, 0, "taxi HKD 300")], [[1, 0, 0], [0, 1, 0]])
    (vec_id, _), *_ = store.vector_search([1, 0, 0], 1)
    (kw_id, _), *_ = store.keyword_search(tokenize("年假"), 1)
    assert vec_id == kw_id
    store.delete_source("a.md")
    assert store.count() == 1 and store.keyword_search(tokenize("年假"), 5) == []
    assert all(store.get([i])[i].source == "b.md" for i, _ in store.vector_search([1, 0, 0], 5))


def test_refuses_mismatched_embedder(tmp_path):
    Store(tmp_path / "t.db", "model-a", 3).close()
    with pytest.raises(RuntimeError, match="reset"):
        Store(tmp_path / "t.db", "model-b", 3)


def test_concurrent_searches_are_safe(tmp_path):
    store = Store(tmp_path / "t.db", "test", 3)
    store.add([Chunk(f"{i}.md", None, 0, f"policy {i} 年假 HKD {i}00") for i in range(30)], [[1, i / 30, 0] for i in range(30)])
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda i: (store.keyword_search(tokenize("年假"), 5), store.vector_search([1, 0, 0], 5)), range(200)))
    assert all(len(kw) == 5 and len(vec) == 5 for kw, vec in results)
