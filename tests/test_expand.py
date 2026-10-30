import json

import pytest
from conftest import ROOT, FakeReranker

from hybridrag.evaluate import first_hit_rank
from hybridrag.expand import (
    DEFAULT_LLM,
    CombinedExpander,
    GlossaryExpander,
    LLMExpander,
    get_expander,
    has_cjk,
    keeps_facts,
    load_glossary,
    mentions,
)

GLOSSARY = ROOT / "examples" / "glossary.csv"
LEAK = ("hk-hq/compliance/personal-data-and-aml.md", "24 小時內")


def test_every_glossary_row_pairs_english_with_chinese():
    entries = load_glossary(GLOSSARY)
    assert len(entries) >= 50
    assert all(any(has_cjk(t) for t in e) and any(not has_cjk(t) for t in e) for e in entries)


def test_english_terms_match_whole_words_with_simple_endings():
    assert mentions("reporting timeline for data breaches", "data breach")
    assert mentions("Working from home policy", "work from home")
    assert not mentions("incident report", "PO")  # 'po' inside 'report' is not the word PO
    assert not mentions("breach notification", "data breach")


def test_chinese_terms_ignore_spaces_and_punctuation():
    assert mentions("收供應商 禮物 登記", "禮物")
    assert mentions("《個人資料（私隱）條例》", "個人資料（私隱）條例")
    assert mentions("個人資料 私隱 條例", "個人資料（私隱）條例")


def test_glossary_adds_the_other_terms_of_every_matched_row():
    g = GlossaryExpander(GLOSSARY)
    assert g.expand("data breach notification") == ["data breach notification data leak 資料外洩"]
    assert g.expand("年假 申請") == ["年假 申請 annual leave"]
    assert g.expand("breach notification requirements") == []  # it only knows what someone wrote down


def fake_chat(log):
    def chat(model, messages):
        log.append(messages[-1]["content"])
        to_english = "into English" in log[-1]
        return json.dumps({"translation": "data breach" if to_english else "懷疑資料外洩要幾快通報？"})
    return chat


def test_llm_translates_into_the_other_language(tmp_path):
    log = []
    exp = LLMExpander("m", tmp_path / "cache.jsonl", chat=fake_chat(log))
    assert exp.expand("How fast must a data leak be reported?") == ["懷疑資料外洩要幾快通報？"]
    assert exp.expand("資料外洩") == ["data breach"]
    assert "into Hong Kong Traditional Chinese" in log[0] and "into English" in log[1]


def test_llm_translations_are_cached_on_disk_per_model(tmp_path):
    log, cache = [], tmp_path / "cache.jsonl"
    exp = LLMExpander("m", cache, chat=fake_chat(log))
    exp.expand("資料外洩")
    exp.expand("資料外洩")
    assert exp.calls == 1 and len(cache.read_text(encoding="utf-8").splitlines()) == 1
    again = LLMExpander("m", cache, chat=lambda *_: pytest.fail("should come from the cache"))
    assert again.expand("資料外洩") == ["data breach"] and again.calls == 0
    LLMExpander("another-model", cache, chat=fake_chat(log)).expand("資料外洩")
    assert len(log) == 2  # a different model is a cache miss


def test_llm_translation_equal_to_the_query_adds_nothing():
    exp = LLMExpander("m", chat=lambda *_: '{"translation": "FIN-07"}')
    assert exp.expand("FIN-07") == [] and exp.expand("   ") == []


@pytest.mark.parametrize("query, translation, ok", [
    # real translate-v1 outputs (eval/runs/llm_expansions-translate-v1.jsonl)
    ("HKD 500 以上嘅禮物要點處理？", "How to handle gifts over HKD 5,000?", False),
    ("深圳張訂單超過五萬人民幣要邊個批？", "Which person needs to approve orders over HKD 50,000 in Shenzhen?", False),
    ("Do I have to go to the office when typhoon signal 8 is up?", "當八號風球懸掛時，我需要去辦公室嗎？", True),
    ("深圳張訂單超過五萬人民幣要邊個批？", "Who approves Shenzhen orders over RMB 50,000?", True),
    ("taxi fare over HKD 300", "超過 300 港元嘅的士車費", True),
])
def test_keeps_facts_catches_changed_amounts_and_currencies(query, translation, ok):
    assert keeps_facts(query, translation) is ok


def test_llm_translation_that_changes_an_amount_is_dropped():
    exp = LLMExpander("m", chat=lambda *_: '{"translation": "How to handle gifts over HKD 5,000?"}')
    assert exp.expand("HKD 500 以上嘅禮物要點處理？") == [] and exp.dropped == {"HKD 500 以上嘅禮物要點處理？"}


def test_combined_expanders_share_one_translator(monkeypatch):
    from hybridrag.cli import _expanders
    from hybridrag.config import Config

    exps = dict(_expanders("none,llm,glossary+llm", Config(glossary=str(GLOSSARY), expand_cache="")))
    assert exps["none"] is None and isinstance(exps["glossary+llm"], CombinedExpander)
    assert exps["glossary+llm"].parts[1] is exps["llm"]  # one cache, one bill, one translation per query
    exps["llm"]._chat = lambda *_: '{"translation": "年假有幾多日？"}'
    assert exps["glossary+llm"].expand("annual leave days") == ["annual leave days 年假", "年假有幾多日？"]


def test_llm_errors_are_clear(monkeypatch):
    with pytest.raises(RuntimeError, match="unexpected reply"):
        LLMExpander("m", chat=lambda *_: "Sure! Here it is.").expand("annual leave")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        LLMExpander("m").expand("annual leave")


def test_committed_translations_cover_every_eval_query():
    """`hrag eval/replay --expand llm` reproduce eval/RESULTS.md without an API key."""
    from hybridrag.evaluate import load_qa, load_replay

    exp = LLMExpander(DEFAULT_LLM, ROOT / "eval" / "llm_expansions.jsonl", chat=lambda *_: pytest.fail("not cached"))
    queries = [q.q for name in ("harbour_lane_qa", "keyword_qa") for q in load_qa(ROOT / "eval" / f"{name}.jsonl")]
    queries += [q for item in load_replay(ROOT / "eval" / "agent_replay.jsonl") for q in item.queries]
    assert all(exp.translate(q) for q in queries) and exp.calls == 0


def test_get_expander():
    assert get_expander("none") is None
    assert isinstance(get_expander("glossary", str(GLOSSARY)), GlossaryExpander)
    with pytest.raises(ValueError, match="glossary"):
        get_expander("thesaurus")


def test_expansion_finds_the_chinese_answer_to_an_english_query(retriever):
    query = "data breach notification"  # no word of it appears in the answer: 如懷疑資料外洩，須喺 24 小時內通知 ...
    assert first_hit_rank(retriever.search(query, 4, "keyword"), *LEAK) is None
    retriever.expander = GlossaryExpander(GLOSSARY)
    hits = retriever.search(query, 4, "keyword")
    rank = first_hit_rank(hits, *LEAK)
    assert rank is not None and set(hits[rank - 1].stages) == {"keyword:x1"}  # only the expanded query found it


def test_reranker_judges_with_the_original_query_only(retriever):
    seen = []

    class SpyReranker(FakeReranker):
        def score(self, query, texts):
            seen.append(query)
            return super().score(query, texts)

    retriever.reranker, retriever.expander = SpyReranker(), GlossaryExpander(GLOSSARY)
    assert retriever.queries("annual leave") == ["annual leave", "annual leave 年假"]
    retriever.search("annual leave", 3, "hybrid+rerank")
    assert seen == ["annual leave"]


def test_cli_search_and_replay_with_glossary_offline(tmp_path, monkeypatch, capsys):
    from hybridrag.cli import main

    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("RERANKER", "none")
    out = tmp_path / "replay.md"
    assert main(["replay", "--embed", "hash", "--expand", "none,glossary", "--out", str(out)]) == 0
    assert "**Query expansion: none**" in out.read_text(encoding="utf-8")
    assert "**Query expansion: glossary**" in out.read_text(encoding="utf-8")

    monkeypatch.setenv("RAG_DB", str(tmp_path / "h.db"))
    monkeypatch.setenv("EMBED_PROVIDER", "hash")
    assert main(["index", "build", "examples/harbour-lane"]) == 0
    capsys.readouterr()
    assert main(["search", "data breach notification", "--mode", "keyword", "--expand", "glossary", "-k", "1"]) == 0
    printed = capsys.readouterr().out
    assert "expanded x1: data breach notification data leak 資料外洩" in printed
    assert "personal-data-and-aml.md" in printed
