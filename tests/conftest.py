from pathlib import Path

import pytest

from hybridrag.config import Config
from hybridrag.embed import HashEmbedder
from hybridrag.index import build_index
from hybridrag.retrieve import Retriever
from hybridrag.store import Store

ROOT = Path(__file__).parent.parent
BASE = [ROOT / "examples" / "harbour-lane"]
FULL = BASE + [ROOT / "examples" / "distractors"]


class FakeReranker:
    """Deterministic stand-in for a cross-encoder: counts query words found in the passage."""

    name = "fake"

    def score(self, query, texts):
        words = [w for w in query.lower().split() if len(w) > 2]
        return [float(sum(w in t.lower() for w in words)) for t in texts]


@pytest.fixture
def retriever(tmp_path):
    emb = HashEmbedder()
    store = Store(tmp_path / "t.db", emb.name, emb.dim)
    build_index(FULL, Config(chunk_size=200, chunk_overlap=30), emb, store)
    yield Retriever(store, emb, FakeReranker(), pool=20)
    store.close()
