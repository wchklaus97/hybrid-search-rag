import pytest

from hybridrag.retrieve import MODES


def test_keyword_mode_nails_exact_codes(retriever):
    (top, *_) = retriever.search("FIN-07", 3, "keyword")
    assert top.source == "hk-hq/finance/expense-claims.md" and "keyword" in top.stages


def test_keyword_beats_lookalike_codes_and_amounts(retriever):
    (top, *_) = retriever.search("RMB 50,000", 3, "keyword")
    assert top.source == "sz-subsidiary/operations/supplier-onboarding.md"  # not the HKD 50,000 purchasing doc


def test_hybrid_merges_both_lists_and_records_why(retriever):
    hits = retriever.search("年假申請要提前幾多日", 5, "hybrid")
    assert hits and any({"vector", "keyword"} <= set(h.stages) for h in hits)


def test_rerank_reorders_and_records_rerank_stage(retriever):
    hits = retriever.search("taxi fare approval HKD 300", 3, "hybrid+rerank")
    assert all("rerank" in h.stages for h in hits)
    assert [h.stages["rerank"][0] for h in hits] == [1, 2, 3]
    assert "HKD 300" in hits[0].text


def test_refusal_threshold_empties_rerank_results_only(retriever):
    retriever.min_rerank_score = 1e9  # above any score the fake reranker can give
    assert retriever.search("taxi fare approval HKD 300", 3, "hybrid+rerank") == []
    assert retriever.search("FIN-07", 3, "keyword")  # keyword modes have no reranker score: never refused


def test_refusal_threshold_off_by_default(retriever):
    assert retriever.min_rerank_score is None
    assert retriever.search("taxi fare approval HKD 300", 3, "hybrid+rerank")


def test_department_filter(retriever):
    hits = retriever.search("approval", 5, "hybrid", department="finance")
    assert hits and all(h.department == "finance" for h in hits)


def test_every_mode_runs_and_empty_query_is_safe(retriever):
    for mode in MODES:
        assert retriever.search("annual leave", 2, mode)
    assert retriever.search("   ", 3, "hybrid") == []


def test_rerank_mode_without_reranker_explains(retriever):
    retriever.reranker = None
    with pytest.raises(LookupError, match="reranker"):
        retriever.search("anything", 3, "hybrid+rerank")
    with pytest.raises(ValueError):
        retriever.search("anything", 3, "bogus")


def test_period_metadata_is_returned_with_hits(retriever):
    hits = retriever.search("FIN-07", 3, "keyword")
    assert hits and all(isinstance(h.period, str) for h in hits)
