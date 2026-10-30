25 questions, top-k = 3.

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| full (28 chunks) · local · 200 · pool 15 · **vector** | 0.48 | 0.72 | 0.58 | 0.82 | 0.50 |
| full (28 chunks) · local · 200 · pool 15 · **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| full (28 chunks) · local · 200 · pool 15 · **hybrid** | 0.44 | 0.84 | 0.61 | 0.82 | 0.88 |
| full (28 chunks) · local · 200 · pool 15 · **vector+rerank** | 0.80 | 1.00 | 0.89 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 15 · **hybrid+rerank** | 0.80 | 1.00 | 0.89 | 1.00 | 1.00 |
