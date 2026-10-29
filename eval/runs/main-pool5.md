25 questions, top-k = 3.

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| full (28 chunks) · local · 200 · pool 5 · **vector** | 0.48 | 0.72 | 0.58 | 0.82 | 0.50 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** | 0.40 | 0.84 | 0.60 | 0.82 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** | 0.76 | 0.84 | 0.80 | 0.88 | 0.75 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** | 0.76 | 0.88 | 0.82 | 0.88 | 0.88 |
