17 questions per run.

| run | pass | cite | fact | lang | refuse | tool | pass: inventory | pass: lookup | pass: multi | pass: out_of_scope | tool calls / q | s / q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| run 1 · **vector** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.5 | 0.0 |
| run 1 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.3 | 0.0 |
| run 2 · **vector** | 0.88 | 0.85 | 0.85 | 1.00 | 1.00 | 1.00 | 1.00 | 0.80 | 1.00 | 1.00 | 1.6 | 0.0 |
| run 2 · **hybrid+rerank** | 0.94 | 0.92 | 1.00 | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 | 1.4 | 0.0 |

**Failures - run 2 · **vector**:** leak-en: cite, fact; payrun-zh: cite, fact

**Failures - run 2 · **hybrid+rerank**:** sz-docs-en: cite


## With query expansion (glossary+llm), re-scored after repo 3 commit 553371d

17 questions per run.

| run | pass | cite | fact | lang | refuse | tool | pass: inventory | pass: lookup | pass: multi | pass: out_of_scope | tool calls / q | s / q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| run 1 · **hybrid+rerank** · glossary+llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.3 | 0.0 |
| run 2 · **hybrid+rerank** · glossary+llm | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.4 | 0.0 |
