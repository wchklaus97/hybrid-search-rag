# Conversation memory as RAG (prototype)

Raw turns are the source of truth. The index holds two kinds of entries:

- **window**: every turn with the two before it, as one passage. Keeps history.
- **fact**: the latest value per key, one sentence. Answers "what is it now?"

A superseded turn can carry a note, `〔已過時：… 其後於第 N 輪改為 …〕`, which is the valid_to of its fact. Facts come from the `facts` labels in `turns.jsonl`, which stand in for an extractor. The extractor (LLM or rules) is still open.

Run from the repo root: `uv run --extra local python conversation-rag/run.py` (add `RERANK=BAAI/bge-reranker-v2-m3` for the reranked run).

## Results (16 turns, 6 questions, author-written)

| variant | current top-1 (hybrid) | history top-1 (hybrid) | current top-1 (bge) | history top-1 (bge) |
|---|---|---|---|---|
| windows only | 2/4 | 2/2 | 2/4 | 0/2 |
| windows + latest | 2/4 | 0/2 | 2/4 | 0/2 |
| + stale notes | 3/4 | 0/2 | **4/4** | 1/2 |

- Adding the latest facts alone does not help: the old value still matches the query better, and facts take the history answer.
- The stale notes help most. With bge they give 4/4 on current values.
- History in English stays weak. "Before we moved" does not match the Chinese text.

## Limits

- Six questions, written by the author, facts labelled by hand. This is a demo, not evidence.
- The extractor is not built. Real conversations need one, and its errors go straight into the fact index.
- No refusal check on off-topic questions in this prototype.
