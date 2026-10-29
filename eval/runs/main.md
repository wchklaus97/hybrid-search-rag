25 questions, top-k = 3.

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| base (15 chunks) · hash · 200 · **vector** | 0.52 | 0.68 | 0.59 | 0.59 | 0.88 |
| base (15 chunks) · hash · 200 · **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| base (15 chunks) · hash · 200 · **hybrid** | 0.60 | 0.72 | 0.65 | 0.65 | 0.88 |
| base (15 chunks) · hash · 200 · **vector+rerank** | 0.84 | 1.00 | 0.91 | 1.00 | 1.00 |
| base (15 chunks) · hash · 200 · **hybrid+rerank** | 0.84 | 1.00 | 0.91 | 1.00 | 1.00 |
| base (7 chunks) · hash · 400 · **vector** | 0.48 | 0.76 | 0.59 | 0.65 | 1.00 |
| base (7 chunks) · hash · 400 · **keyword** | 0.64 | 0.72 | 0.68 | 0.59 | 1.00 |
| base (7 chunks) · hash · 400 · **hybrid** | 0.60 | 0.76 | 0.67 | 0.65 | 1.00 |
| base (7 chunks) · hash · 400 · **vector+rerank** | 0.96 | 1.00 | 0.98 | 1.00 | 1.00 |
| base (7 chunks) · hash · 400 · **hybrid+rerank** | 0.96 | 1.00 | 0.98 | 1.00 | 1.00 |
| base (15 chunks) · local · 200 · **vector** | 0.52 | 0.84 | 0.65 | 0.88 | 0.75 |
| base (15 chunks) · local · 200 · **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| base (15 chunks) · local · 200 · **hybrid** | 0.52 | 0.88 | 0.68 | 0.88 | 0.88 |
| base (15 chunks) · local · 200 · **vector+rerank** | 0.84 | 1.00 | 0.91 | 1.00 | 1.00 |
| base (15 chunks) · local · 200 · **hybrid+rerank** | 0.84 | 1.00 | 0.91 | 1.00 | 1.00 |
| base (7 chunks) · local · 400 · **vector** | 0.68 | 1.00 | 0.82 | 1.00 | 1.00 |
| base (7 chunks) · local · 400 · **keyword** | 0.64 | 0.72 | 0.68 | 0.59 | 1.00 |
| base (7 chunks) · local · 400 · **hybrid** | 0.72 | 0.96 | 0.83 | 0.94 | 1.00 |
| base (7 chunks) · local · 400 · **vector+rerank** | 0.96 | 1.00 | 0.98 | 1.00 | 1.00 |
| base (7 chunks) · local · 400 · **hybrid+rerank** | 0.96 | 1.00 | 0.98 | 1.00 | 1.00 |
| full (28 chunks) · hash · 200 · **vector** | 0.32 | 0.48 | 0.39 | 0.35 | 0.75 |
| full (28 chunks) · hash · 200 · **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| full (28 chunks) · hash · 200 · **hybrid** | 0.56 | 0.64 | 0.59 | 0.53 | 0.88 |
| full (28 chunks) · hash · 200 · **vector+rerank** | 0.68 | 0.84 | 0.75 | 0.76 | 1.00 |
| full (28 chunks) · hash · 200 · **hybrid+rerank** | 0.68 | 0.84 | 0.75 | 0.76 | 1.00 |
| full (14 chunks) · hash · 400 · **vector** | 0.32 | 0.60 | 0.45 | 0.41 | 1.00 |
| full (14 chunks) · hash · 400 · **keyword** | 0.60 | 0.72 | 0.66 | 0.59 | 1.00 |
| full (14 chunks) · hash · 400 · **hybrid** | 0.56 | 0.72 | 0.64 | 0.59 | 1.00 |
| full (14 chunks) · hash · 400 · **vector+rerank** | 0.92 | 1.00 | 0.96 | 1.00 | 1.00 |
| full (14 chunks) · hash · 400 · **hybrid+rerank** | 0.92 | 1.00 | 0.96 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · **vector** | 0.48 | 0.72 | 0.58 | 0.82 | 0.50 |
| full (28 chunks) · local · 200 · **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| full (28 chunks) · local · 200 · **hybrid** | 0.44 | 0.84 | 0.61 | 0.82 | 0.88 |
| full (28 chunks) · local · 200 · **vector+rerank** | 0.80 | 1.00 | 0.89 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · **hybrid+rerank** | 0.80 | 1.00 | 0.89 | 1.00 | 1.00 |
| full (14 chunks) · local · 400 · **vector** | 0.64 | 0.88 | 0.75 | 0.88 | 0.88 |
| full (14 chunks) · local · 400 · **keyword** | 0.60 | 0.72 | 0.66 | 0.59 | 1.00 |
| full (14 chunks) · local · 400 · **hybrid** | 0.68 | 0.92 | 0.78 | 0.88 | 1.00 |
| full (14 chunks) · local · 400 · **vector+rerank** | 0.92 | 1.00 | 0.96 | 1.00 | 1.00 |
| full (14 chunks) · local · 400 · **hybrid+rerank** | 0.92 | 1.00 | 0.96 | 1.00 | 1.00 |
