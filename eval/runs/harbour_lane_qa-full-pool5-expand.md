25 questions, top-k = 3.

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| full (28 chunks) · local · 200 · pool 5 · **vector** | 0.48 | 0.72 | 0.58 | 0.82 | 0.50 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** | 0.40 | 0.84 | 0.60 | 0.82 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** | 0.76 | 0.84 | 0.80 | 0.88 | 0.75 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** | 0.76 | 0.88 | 0.82 | 0.88 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **vector** · glossary | 0.48 | 0.76 | 0.59 | 0.82 | 0.62 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** · glossary | 0.56 | 0.72 | 0.63 | 0.65 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** · glossary | 0.44 | 0.88 | 0.65 | 0.82 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** · glossary | 0.76 | 0.88 | 0.82 | 0.88 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** · glossary | 0.76 | 0.92 | 0.84 | 0.88 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector** · llm | 0.52 | 0.80 | 0.64 | 0.88 | 0.62 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** · llm | 0.60 | 0.88 | 0.72 | 0.82 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** · llm | 0.60 | 0.88 | 0.73 | 0.88 | 0.88 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** · llm | 0.76 | 0.96 | 0.86 | 0.94 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** · llm | 0.76 | 0.96 | 0.86 | 0.94 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector** · glossary+llm | 0.48 | 0.84 | 0.63 | 0.88 | 0.75 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** · glossary+llm | 0.60 | 0.88 | 0.73 | 0.82 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** · glossary+llm | 0.64 | 0.92 | 0.77 | 0.88 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** · glossary+llm | 0.76 | 0.96 | 0.86 | 0.94 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** · glossary+llm | 0.76 | 0.96 | 0.86 | 0.94 | 1.00 |
