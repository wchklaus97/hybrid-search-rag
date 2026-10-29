import pytest

pytest.importorskip("agentrag", reason="repo 3's agent not installed (pip install -e '.[agent]')")


def test_hybrid_searcher_satisfies_repo3_searcher_contract(retriever):
    from agentrag.tools import Snippet, SourceInfo, retrieve_snippets

    from hybridrag.agent_bridge import HybridSearcher

    searcher = HybridSearcher(retriever, "hybrid+rerank")
    out = retrieve_snippets(searcher, "taxi fare HKD 300", k=3)
    assert out and all(isinstance(s, Snippet) for s in out)
    assert all(isinstance(s, SourceInfo) for s in searcher.sources())
