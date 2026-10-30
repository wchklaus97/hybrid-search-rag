10 questions, top-k = 3.

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| full (28 chunks) · local · 200 · pool 5 · **vector** | 0.70 | 0.80 | 0.75 | 0.83 | 0.75 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** | 0.80 | 1.00 | 0.88 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector** · glossary | 0.70 | 0.80 | 0.75 | 0.83 | 0.75 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** · glossary | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** · glossary | 0.90 | 1.00 | 0.93 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** · glossary | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** · glossary | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector** · llm | 0.80 | 0.80 | 0.80 | 0.83 | 0.75 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** · llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** · llm | 0.80 | 1.00 | 0.88 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** · llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** · llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector** · glossary+llm | 0.80 | 0.80 | 0.80 | 0.83 | 0.75 |
| full (28 chunks) · local · 200 · pool 5 · **keyword** · glossary+llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid** · glossary+llm | 0.80 | 1.00 | 0.88 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **vector+rerank** · glossary+llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| full (28 chunks) · local · 200 · pool 5 · **hybrid+rerank** · glossary+llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
