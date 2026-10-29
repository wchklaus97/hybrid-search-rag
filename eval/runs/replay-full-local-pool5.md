corpus `full` (28 chunks), embedder `local:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, chunk 200/30, candidate pool 5 per retriever

Replayed agent queries; a query counts if the evidence chunk is in the top 4 (the agent's default k).

| question | vector | keyword | hybrid | vector+rerank | hybrid+rerank |
|---|---|---|---|---|---|
| `leave-days-en` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `leave-notice-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `wfh-en` | 2/3 | 2/3 | 2/3 | 3/3 | 2/3 |
| `taxi-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `director-en` | 2/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| `claim-deadline-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `leak-en` | 0/10 | 4/10 | 4/10 | 0/10 | 4/10 |
| `gift-zh` | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| `po-en` | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| `payrun-zh` | 2/9 | 9/9 | 4/9 | 4/9 | 9/9 |
| **all queries** | **0.61** | **0.86** | **0.76** | **0.67** | **0.86** |
