"""CJK-aware tokenizer for keyword search (BM25 / SQLite FTS5) - STANDALONE.

Pure Python, standard library only: copy this one file into any project.
(Named cjk_tokenize.py on purpose: a file called tokenize.py would shadow Python's
own `tokenize` module, which tracebacks and linecache rely on.)

Why it exists: keyword engines split text on spaces and punctuation. Chinese has no
spaces, so SQLite FTS5's default tokenizer turns a whole clause into ONE token. In
"如懷疑資料外洩，須喺 24 小時內通知 Compliance Officer", searching 外洩 (leak) or
資料外洩 (data leak) finds nothing - only the exact run 如懷疑資料外洩 matches.

What it does - no dictionary, no dependencies:
  * CJK runs -> overlapping character bigrams     資料外洩 -> 資料 料外 外洩
    (a lone character stays a unigram)
  * Latin words and numbers -> lowercase tokens   Compliance Officer -> compliance officer
  * thousands separators removed                  HKD 5,000 -> hkd 5000
  * codes keep their shape AND their parts        FIN-07 -> fin-07 fin 07
  * full-width forms normalised (NFKC)            ＨＫＤ５０００ -> hkd 5000
  * a small English stop-word list is dropped (questions are full of how / the / do)

Bigrams are the classic dictionary-free approach to CJK search (Lucene's CJKAnalyzer
does the same). They over-generate a little (料外 is not a word) but never miss a
two-character word, and most Chinese words are two characters long.
"""

from __future__ import annotations

import re
import unicodedata

VERSION = "cjk-bigram-v1"  # stored in the index: change it whenever tokenize() output changes

_CJK = "㐀-䶿一-鿿豈-﫿"
_TOKEN = re.compile(rf"[{_CJK}]+|[a-z0-9]+(?:[-_][a-z0-9]+)*")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")
_PARTS = re.compile(r"[-_]")

STOPWORDS = frozenset(
    "a an and any are as at be been by can could did do does for from had has have how i if in into is it its "
    "may me must my of on or our should so than that the their them there these they this to was we were what "
    "when where which who why will with would you your".split()
)


def _is_cjk(ch: str) -> bool:
    return "㐀" <= ch <= "䶿" or "一" <= ch <= "鿿" or "豈" <= ch <= "﫿"


def tokenize(text: str) -> list[str]:
    """Split text into keyword-search tokens. Use the SAME function for documents and queries."""
    text = _THOUSANDS.sub("", unicodedata.normalize("NFKC", text).lower())
    out: list[str] = []
    for match in _TOKEN.finditer(text):
        tok = match.group()
        if _is_cjk(tok[0]):
            out.extend([tok] if len(tok) == 1 else [tok[i : i + 2] for i in range(len(tok) - 1)])
        elif tok not in STOPWORDS:
            out.append(tok)
            if "-" in tok or "_" in tok:
                out.extend(p for p in _PARTS.split(tok) if p and p not in STOPWORDS)
    return out
