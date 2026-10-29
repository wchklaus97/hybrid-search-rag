10 questions, top-k = 3.

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| base (15 chunks) · hash · 200 · **vector** | 0.60 | 0.80 | 0.67 | 0.83 | 0.75 |
| base (15 chunks) · hash · 200 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (15 chunks) · hash · 200 · **hybrid** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (15 chunks) · hash · 200 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (15 chunks) · hash · 200 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (7 chunks) · hash · 400 · **vector** | 0.40 | 0.50 | 0.45 | 0.50 | 0.50 |
| base (7 chunks) · hash · 400 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (7 chunks) · hash · 400 · **hybrid** | 0.80 | 1.00 | 0.88 | 1.00 | 1.00 |
| base (7 chunks) · hash · 400 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (7 chunks) · hash · 400 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (15 chunks) · local · 200 · **vector** | 0.80 | 0.90 | 0.83 | 0.83 | 1.00 |
| base (15 chunks) · local · 200 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (15 chunks) · local · 200 · **hybrid** | 0.90 | 1.00 | 0.95 | 1.00 | 1.00 |
| base (15 chunks) · local · 200 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (15 chunks) · local · 200 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (7 chunks) · local · 400 · **vector** | 0.60 | 0.80 | 0.70 | 1.00 | 0.50 |
| base (7 chunks) · local · 400 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (7 chunks) · local · 400 · **hybrid** | 0.90 | 1.00 | 0.93 | 1.00 | 1.00 |
| base (7 chunks) · local · 400 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| base (7 chunks) · local · 400 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · hash · 200 · **vector** | 0.60 | 0.60 | 0.60 | 0.67 | 0.50 |
| full (28 chunks) · hash · 200 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · hash · 200 · **hybrid** | 0.70 | 1.00 | 0.82 | 1.00 | 1.00 |
| full (28 chunks) · hash · 200 · **vector+rerank** | 0.90 | 0.90 | 0.90 | 1.00 | 0.75 |
| full (28 chunks) · hash · 200 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (14 chunks) · hash · 400 · **vector** | 0.40 | 0.50 | 0.45 | 0.50 | 0.50 |
| full (14 chunks) · hash · 400 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (14 chunks) · hash · 400 · **hybrid** | 0.60 | 0.90 | 0.75 | 1.00 | 0.75 |
| full (14 chunks) · hash · 400 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (14 chunks) · hash · 400 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · **vector** | 0.70 | 0.80 | 0.75 | 0.83 | 0.75 |
| full (28 chunks) · local · 200 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · **hybrid** | 0.80 | 1.00 | 0.88 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (14 chunks) · local · 400 · **vector** | 0.50 | 0.80 | 0.62 | 1.00 | 0.50 |
| full (14 chunks) · local · 400 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (14 chunks) · local · 400 · **hybrid** | 0.80 | 0.90 | 0.85 | 1.00 | 0.75 |
| full (14 chunks) · local · 400 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (14 chunks) · local · 400 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
