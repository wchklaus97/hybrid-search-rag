corpus `full`, embedder `hash:384`, chunk 200/30

Replayed agent queries; a query counts if the evidence chunk is in the top 4 (the agent's default k).

| question | vector | keyword | hybrid | vector+rerank | hybrid+rerank |
|---|---|---|---|---|---|
| `leave-days-en` | 0/2 | 2/2 | 0/2 | 2/2 | 2/2 |
| `leave-notice-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `wfh-en` | 0/3 | 2/3 | 2/3 | 3/3 | 3/3 |
| `taxi-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `director-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `claim-deadline-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `leak-en` | 4/10 | 4/10 | 4/10 | 8/10 | 8/10 |
| `gift-zh` | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| `po-en` | 4/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| `payrun-zh` | 8/9 | 9/9 | 9/9 | 9/9 | 9/9 |
| **all queries** | **0.73** | **0.86** | **0.82** | **0.96** | **0.96** |
