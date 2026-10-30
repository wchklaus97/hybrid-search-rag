"""Stage 4b - Query expansion: also search in the other language.

Harbour Lane's policies are Chinese with English terms mixed in, but staff ask in either
language. "data breach" shares no token with 資料外洩, so BM25 cannot match it, and the
small multilingual embedder does not bridge the gap on its own (repo 3's agent missed it).

Expansion turns one query into several. The retriever searches with every version and
fuses all the lists, so a chunk that any version finds can enter the candidate pool:

  glossary  the company's bilingual term list (examples/glossary.csv). A term that
            appears in the query brings in the other terms of its row, in both
            languages. Free, instant and predictable, but blind to words nobody listed.
  llm       translate the whole query into the other language with a chat model
            (any OpenAI-compatible API; OpenRouter works). Covers any wording, but each
            new query costs a call and the output can drift, even at temperature 0.
            Translations are cached in a JSONL file, so evals are reproducible and
            repeated queries are free, and a translation that changes a number or a
            currency is dropped (keeps_facts), because "HKD 500" must never become
            "HKD 5,000" on its way into the search.
  glossary+llm  both: the glossary's version AND the translation.
  none      search with the original query only.
"""

from __future__ import annotations

import csv
import functools
import json
import os
import re
import threading
import time
import unicodedata
from pathlib import Path
from typing import Protocol

from ._http import post_json

EXPANDERS = ("none", "glossary", "llm", "glossary+llm")
DEFAULT_GLOSSARY = "examples/glossary.csv"
DEFAULT_LLM = "openai/gpt-4o-mini"  # OpenRouter's name for it; use "gpt-4o-mini" with api.openai.com
PROMPT_VERSION = "translate-v2"  # bump when the prompt changes so old cache lines are not reused

_CJK = "\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
_HAS_CJK = re.compile(f"[{_CJK}]")
_NOT_WORD = re.compile(f"[^0-9a-z{_CJK}]+")
_NUMBER = re.compile(r"\d[\d,]*")
_CURRENCY = {"hkd": "hkd", "港元": "hkd", "港幣": "hkd", "rmb": "rmb", "人民幣": "rmb", "usd": "usd", "美元": "usd"}
_CURRENCY_RE = re.compile(r"(?<![a-z])(?:hkd|rmb|usd)(?![a-z])|港元|港幣|人民幣|美元")


class Expander(Protocol):
    name: str

    def expand(self, query: str) -> list[str]: ...  # EXTRA queries; the original is always searched too


def has_cjk(text: str) -> bool:
    return bool(_HAS_CJK.search(text))


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def _squash(text: str) -> str:
    """Drop spaces and punctuation: '個人資料（私隱）條例' and '個人資料 私隱 條例' both -> '個人資料私隱條例'."""
    return _NOT_WORD.sub("", _norm(text))


@functools.lru_cache(maxsize=None)
def _words(term: str) -> re.Pattern:
    # whole words, each allowed a plural / -ed / -ing ending: "data breaches", "working from home"
    ending = r"(?:s|es|d|ed|ing)?"
    body = (ending + r"\s+").join(re.escape(w) for w in _norm(term).split())
    return re.compile(rf"(?<![0-9a-z]){body}{ending}(?![0-9a-z])")


def mentions(query: str, term: str) -> bool:
    if has_cjk(term):
        return _squash(term) in _squash(query)  # Chinese has no word boundaries to respect
    return _words(term).search(_norm(query)) is not None


# --- glossary -----------------------------------------------------------------
def load_glossary(path: str | Path) -> list[tuple[str, ...]]:
    """CSV with columns en,zh; variants separated by '|'; lines starting with # are comments."""
    if not Path(path).exists():
        raise FileNotFoundError(f"glossary not found: {path} (set `glossary` in hrag.toml, or use --expand none)")
    with open(path, encoding="utf-8", newline="") as f:
        rows = csv.DictReader(line for line in f if line.strip() and not line.lstrip().startswith("#"))
        entries = []
        for row in rows:
            terms = [t.strip() for col in ("en", "zh") for t in (row.get(col) or "").split("|") if t.strip()]
            if len(terms) >= 2:
                entries.append(tuple(dict.fromkeys(terms)))
    return entries


class GlossaryExpander:
    """Each row is a synonym ring across languages: any term in the query brings in the others."""

    def __init__(self, path: str | Path = DEFAULT_GLOSSARY):
        self.entries = load_glossary(path)
        self.name = f"glossary:{Path(path).name}"

    def matched(self, query: str) -> list[tuple[str, ...]]:
        return [entry for entry in self.entries if any(mentions(query, t) for t in entry)]

    def expand(self, query: str) -> list[str]:
        extra: list[str] = []
        for entry in self.matched(query):
            extra += [t for t in entry if t not in extra and not mentions(query, t)]
        return [f"{query} {' '.join(extra)}"] if extra else []


# --- LLM translation ----------------------------------------------------------
_SYSTEM = (
    "You translate search queries for the document search of a Hong Kong company. "
    "Its policies are written in Hong Kong Traditional Chinese with English terms mixed in."
)


def _messages(query: str, target: str) -> list[dict]:
    # No example values in the prompt: translate-v1 showed "HKD 5,000" as an example, and the
    # model then turned "HKD 500" and "五萬人民幣" into HKD 5,000 (eval/runs/llm_expansions-translate-v1.jsonl).
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"Translate this search query into {target}. Every code, number and currency must stay the "
            "same as in the query (Chinese numerals may be written as digits). Keep English job titles "
            "and names in English. Translate only: do not answer the query or add information. "
            'Reply with JSON: {"translation": "..."}\n\n'
            f"Query: {query}"
        )},
    ]


def facts(text: str, numbers: bool = True) -> set[str]:
    """Currencies (港元 = HKD) and, optionally, numbers (5,000 = 5000) mentioned in a text."""
    text = _norm(text)
    found = {_CURRENCY[c] for c in _CURRENCY_RE.findall(text)}
    return found | ({n.replace(",", "") for n in _NUMBER.findall(text)} if numbers else set())


def keeps_facts(query: str, translation: str) -> bool:
    """Same currencies always; same numbers when both sides use digits ('signal 8' -> 八號風球 is fine)."""
    numbers = bool(_NUMBER.search(query)) and bool(_NUMBER.search(translation))
    return facts(query, numbers) == facts(translation, numbers)


def _openai_chat(model: str, messages: list[dict]) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("LLM query expansion needs OPENAI_API_KEY (and OPENAI_BASE_URL for OpenRouter) "
                           "for queries that are not in the cache yet")
    url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    payload = {"model": model, "messages": messages, "temperature": 0, "response_format": {"type": "json_object"}}
    data = post_json(url, payload, {"Authorization": f"Bearer {key}"}, timeout=60)
    return data["choices"][0]["message"]["content"]


def _parse(reply: str) -> str:
    text = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return str(json.loads(text)["translation"]).strip()
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise RuntimeError(f"unexpected reply from the expansion model: {reply[:200]!r}") from e


class LLMExpander:
    """Query with Chinese in it -> add an English version; English-only query -> add a Chinese one."""

    def __init__(self, model: str = DEFAULT_LLM, cache_path: str | Path | None = None, chat=None):
        self.model = model
        self.name = f"llm:{model}"
        self.cache_path = Path(cache_path) if cache_path else None
        self.calls = 0  # cache misses = API calls made by this instance
        self.dropped: set[str] = set()  # queries whose translation changed a number or currency
        self._chat = chat or _openai_chat  # injectable, so tests never touch the network
        self._lock = threading.Lock()  # the agent runs tools in worker threads
        self._cache: dict[str, str] = {}
        if self.cache_path and self.cache_path.exists():
            for line in self.cache_path.read_text(encoding="utf-8").splitlines():
                if line.strip() and (r := json.loads(line))["model"] == model and r["prompt"] == PROMPT_VERSION:
                    self._cache[r["query"]] = r["translation"]

    def translate(self, query: str) -> str:
        with self._lock:
            if query not in self._cache:
                target = "English" if has_cjk(query) else "Hong Kong Traditional Chinese"
                started = time.perf_counter()
                translation = _parse(self._chat(self.model, _messages(query, target)))
                ms = round((time.perf_counter() - started) * 1000)
                self._cache[query] = translation
                self.calls += 1
                if self.cache_path:
                    self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                    line = {"model": self.model, "prompt": PROMPT_VERSION, "query": query, "translation": translation, "ms": ms}
                    with self.cache_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(line, ensure_ascii=False) + "\n")
            return self._cache[query]

    def expand(self, query: str) -> list[str]:
        if not query.strip():
            return []
        translation = self.translate(query)
        if not keeps_facts(query, translation):
            self.dropped.add(query)  # never search with a changed amount or currency
            return []
        return [translation] if _squash(translation) not in ("", _squash(query)) else []


class CombinedExpander:
    """Several expanders in turn; each contributes its own versions of the query."""

    def __init__(self, parts: list[Expander]):
        self.parts = parts
        self.name = "+".join(p.name for p in parts)

    def expand(self, query: str) -> list[str]:
        out: list[str] = []
        for part in self.parts:
            out += [v for v in part.expand(query) if v not in out]
        return out


def get_expander(name: str, glossary: str = "", model: str = "", cache: str = "") -> Expander | None:
    if name in ("", "none"):
        return None
    if "+" in name:
        return CombinedExpander([get_expander(n, glossary, model, cache) for n in name.split("+")])
    if name == "glossary":
        return GlossaryExpander(glossary or DEFAULT_GLOSSARY)
    if name == "llm":
        return LLMExpander(model or DEFAULT_LLM, cache or None)
    raise ValueError(f"unknown query expansion {name!r} ({' | '.join(EXPANDERS)})")
