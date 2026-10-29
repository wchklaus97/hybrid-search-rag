corpus `base`, embedder `hash:384`, chunk 200/30

Replayed agent queries; a query counts if the evidence chunk is in the top 4 (the agent's default k).

| question | vector | keyword | hybrid | vector+rerank | hybrid+rerank |
|---|---|---|---|---|---|
| `leave-days-en` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `leave-notice-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `wfh-en` | 1/3 | 2/3 | 2/3 | 3/3 | 3/3 |
| `taxi-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `director-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `claim-deadline-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `leak-en` | 4/10 | 4/10 | 4/10 | 10/10 | 10/10 |
| `gift-zh` | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| `po-en` | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| `payrun-zh` | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 |
| **all queries** | **0.84** | **0.86** | **0.86** | **1.00** | **1.00** |
