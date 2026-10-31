# Conversation memory as RAG (prototype)

Raw turns are the source of truth. The index holds two kinds of entries:

- **window**: every turn with the two before it, as one passage. Keeps history.
- **fact**: the latest value per key, one sentence. Answers "what is it now?"

A turn whose value was later changed carries a note, `〔已過時：… 其後於第 N 輪改為 …〕`. That note is the valid_to of the fact. A restatement of the same value is not a change.

Facts come from one of two sources:

- `turns.jsonl` hand labels (default), or
- `extract.py`, which asks gpt-4o-mini (via OpenRouter) once per turn and caches the answer in `extract_cache.jsonl`. Run with `EXTRACTED=1`.

`extract.py` keeps keys to a fixed vocabulary (office, standup_time, booking_lead, expense_deadline). A new kind of fact needs a new key added by hand, so this is a limit.

Run from the repo root:

    uv run --extra local python conversation-rag/run.py                       # hand labels, hybrid
    EXTRACTED=1 RERANK=BAAI/bge-reranker-v2-m3 uv run --extra local python conversation-rag/run.py
    OPENAI_API_KEY=... OPENAI_BASE_URL=https://openrouter.ai/api/v1 uv run --extra local python conversation-rag/extract.py

## Extraction check (against the hand labels)

Extraction recall is 7/7. Precision is 7/13, but the 6 "extra" facts are the assistant repeating a value it already stated (turns 2, 6, 10, 12, 14), which the hand labels do not list. No value is wrong.

## Results (16 turns, 6 questions, author-written)

Top-1 is the first passage the search returns. Current answers: 4 questions. History answers: 2 questions.

| variant | labels, hybrid | labels, bge | extracted, hybrid | extracted, bge |
|---|---|---|---|---|
| windows only | cur 2/4, hist 2/2 | cur 2/4, hist 0/2 | cur 2/4, hist 2/2 | cur 2/4, hist 0/2 |
| windows + latest | cur 2/4, hist 0/2 | cur 2/4, hist 0/2 | cur 2/4, hist 0/2 | cur 2/4, hist 0/2 |
| + stale notes | cur 4/4, hist 1/2 | cur 4/4, hist 1/2 | cur 4/4, hist 0/2 | cur 4/4, hist 1/2 |

- Latest facts alone do not help. The old value still matches the query, and the fact line takes the history answer.
- The stale notes give 4/4 current answers, with either hand labels or extracted facts.
- History in English stays weak. "Before we moved" does not match the Chinese text.

## Bugs fixed while building the extractor

The first version of `superseded_notes` kept only one note per turn, so a turn with two facts lost one. It also counted a restatement of the same value as a change. Both are fixed, and every number above is from the fixed code. Earlier numbers in this README came from the buggy version, and the 4/4 there was partly luck.

## Limits

- Six questions, written by the author. This is a demo, not evidence.
- The key vocabulary is supplied by hand.
- No refusal check on off-topic questions in this prototype.
