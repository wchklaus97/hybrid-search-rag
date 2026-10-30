10 questions, top-k = 3.

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| full (28 chunks) · local · 200 · pool 10 · **vector** | 0.70 | 0.80 | 0.75 | 0.83 | 0.75 |
| full (28 chunks) · local · 200 · pool 10 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 10 · **hybrid** | 0.80 | 1.00 | 0.88 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 10 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 10 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
