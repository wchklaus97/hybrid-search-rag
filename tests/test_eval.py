import json

from conftest import ROOT

from hybridrag.evaluate import evaluate_mode, load_qa, load_replay, replay_mode, replay_table, results_table

QA = load_qa(ROOT / "eval" / "harbour_lane_qa.jsonl")
KW = load_qa(ROOT / "eval" / "keyword_qa.jsonl")
REPLAY = load_replay(ROOT / "eval" / "agent_replay.jsonl")


def test_qa_sets_are_valid_and_evidence_exists_verbatim():
    for item in [*QA, *KW, *REPLAY]:
        text = (ROOT / "examples" / "harbour-lane" / item.source).read_text(encoding="utf-8")
        assert item.evidence in text, item.id
    assert len(QA) == 25 and len(KW) == 10 and {q.lang for q in QA + KW} == {"en", "zh"}


def test_replay_set_holds_the_real_agent_queries_for_the_known_miss():
    leak = next(i for i in REPLAY if i.id == "leak-en")
    assert leak.evidence == "24 小時內" and len(leak.queries) >= 3


def test_evaluate_mode_metrics_are_consistent(retriever):
    for mode in ("vector", "keyword", "hybrid", "hybrid+rerank"):
        r = evaluate_mode(retriever, QA, mode, k=3)
        assert 0 <= r.hit1 <= r.mrr <= r.hitk <= 1 and set(r.by_lang) == {"en", "zh"}
    assert "| keyword |" in results_table([evaluate_mode(retriever, KW, "keyword")], 3, len(KW))


def test_keyword_search_wins_the_exact_term_set(retriever):
    kw, vec = evaluate_mode(retriever, KW, "keyword", 3), evaluate_mode(retriever, KW, "vector", 3)
    assert kw.hitk >= vec.hitk and kw.hitk >= 0.8


def test_replay_counts_queries(retriever):
    r = replay_mode(retriever, REPLAY, "keyword", k=4)
    assert set(r.per_item) == {i.id for i in REPLAY}
    assert all(0 <= hit <= n == len(next(i for i in REPLAY if i.id == qid).queries) for qid, (hit, n) in r.per_item.items())
    assert "`leak-en`" in replay_table([r], REPLAY, 4)


def test_cli_eval_and_replay_run_offline(tmp_path, monkeypatch, capsys):
    from hybridrag.cli import main

    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("RERANKER", "none")
    out = tmp_path / "r.md"
    assert main(["eval", "--embed", "hash", "--corpus", "base", "--sizes", "200", "--out", str(out)]) == 0
    assert "**hybrid**" in out.read_text(encoding="utf-8")
    assert main(["replay", "--embed", "hash", "--out", str(tmp_path / "p.md")]) == 0
    assert "leak-en" in (tmp_path / "p.md").read_text(encoding="utf-8")


def test_cli_index_and_search(tmp_path, monkeypatch, capsys):
    from hybridrag.cli import main

    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("RAG_DB", str(tmp_path / "h.db"))
    monkeypatch.setenv("EMBED_PROVIDER", "hash")
    monkeypatch.setenv("RERANKER", "none")
    assert main(["index", "build", "examples/harbour-lane"]) == 0
    assert main(["search", "FIN-07", "--mode", "keyword", "-k", "1"]) == 0
    assert "expense-claims.md" in capsys.readouterr().out
