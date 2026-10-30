# Hybrid search evaluation - Harbour Lane

**Setup**
- **Corpora:**
  - `base`: the same 4 documents as repos 1 and 3.
  - `full`: `base` plus 6 *distractor* documents (IT security, payroll, office services, sales, HK purchasing, Shenzhen staff rules). They share vocabulary with the real answers but answer none of the questions.
- **Metric:** same as repo 1. A hit means a retrieved chunk from the expected source that contains the evidence string.
- **Embedders:** `hash` (keyword-like) and `paraphrase-multilingual-MiniLM-L12-v2`.
- **Reranker:** `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`.
- **Candidate pool:** chunks taken from **each** retriever before fusion and reranking.
- **Query expansion:** off unless a table says otherwise. Section 2 turns it on.

## 1. Did hybrid search fix the agent's `leak-en` miss?

Repo 3's agent missed *"How quickly must a suspected customer data leak be reported?"* (answer: 如懷疑資料外洩，須喺 24 小時內通知 Compliance Officer). Its eval recorded every query the agent sent. `hrag replay` re-runs those exact queries in the agent's own setting: base corpus, multilingual embedder, chunk 200, top 4.

**Pool 20.** That's bigger than the 15-chunk corpus, so the reranker sees everything:

| question | vector | keyword | hybrid | vector+rerank | hybrid+rerank |
|---|---|---|---|---|---|
| `leave-days-en` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `leave-notice-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `wfh-en` | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| `taxi-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `director-en` | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `claim-deadline-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `leak-en` | 0/10 | 4/10 | 4/10 | 10/10 | 10/10 |
| `gift-zh` | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| `po-en` | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| `payrun-zh` | 5/9 | 9/9 | 9/9 | 9/9 | 9/9 |
| **all queries** | **0.69** | **0.86** | **0.88** | **1.00** | **1.00** |

**Pool 5.** This is realistic: the reranker sees only what the first stage retrieved.

| question | vector | keyword | hybrid | vector+rerank | hybrid+rerank |
|---|---|---|---|---|---|
| `leave-days-en` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `leave-notice-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `wfh-en` | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| `taxi-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `director-en` | 2/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| `claim-deadline-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `leak-en` | 0/10 | 4/10 | 2/10 | 0/10 | 4/10 |
| `gift-zh` | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| `po-en` | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| `payrun-zh` | 5/9 | 9/9 | 7/9 | 6/9 | 9/9 |
| **all queries** | **0.69** | **0.86** | **0.80** | **0.71** | **0.88** |

**Verdict: hybrid + rerank is a real but partial fix.** `leak-en` goes from 0/10 to 4/10, not 10/10.

- **A reranker cannot rescue a chunk that was never retrieved.** `vector+rerank` stays at 0/10 with a realistic pool. The 10/10 with pool 20 is an artefact of the pool covering the whole corpus.
- **The 4 successes all contain the word "customer".** BM25 matches it in a neighbouring English sentence of the same chunk ("Direct marketing: obtain the customer's consent"), then the cross-encoder puts the chunk at #1.
- **The 6 failures use "breach", "notification" and "timeline".** None of those words appear in any document, which say 資料外洩 and 通知.
- **The partial win depends on a code-mixed English word sitting near the answer.** A robust fix needs cross-lingual query expansion (also search 資料外洩) or a stronger multilingual embedder. Repo 3's agent never searched in Chinese, even though its prompt suggests it. Section 2 measures the expansion fix.

With distractors (`full`, pool 5):

| question | vector | keyword | hybrid | vector+rerank | hybrid+rerank |
|---|---|---|---|---|---|
| `leave-days-en` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `leave-notice-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `wfh-en` | 2/3 | 2/3 | 2/3 | 3/3 | 2/3 |
| `taxi-en` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| `director-en` | 2/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| `claim-deadline-zh` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| `leak-en` | 0/10 | 4/10 | 4/10 | 0/10 | 4/10 |
| `gift-zh` | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| `po-en` | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| `payrun-zh` | 2/9 | 9/9 | 4/9 | 4/9 | 9/9 |
| **all queries** | **0.61** | **0.86** | **0.76** | **0.67** | **0.86** |

### Live check: repo 3's agent with this search behind its tool

`hrag agent-eval` runs repo 3's own agent, prompt, language validator and scorer, and only swaps the `Searcher` behind the `retrieve` tool. Setup: base corpus, chunk 200, pool 5, gpt-4o-mini via OpenRouter, 2 runs per mode. Answers are saved in `eval/runs/` and re-scored with repo 3's scorer, after fixing one refusal phrase it was missing ("沒有明確…").

17 questions per run.

| run | pass | cite | fact | lang | refuse | tool | pass: inventory | pass: lookup | pass: multi | pass: out_of_scope | tool calls / q | s / q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| run 1 · **vector** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.5 | 0.0 |
| run 1 · **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.3 | 0.0 |
| run 2 · **vector** | 0.88 | 0.85 | 0.85 | 1.00 | 1.00 | 1.00 | 1.00 | 0.80 | 1.00 | 1.00 | 1.6 | 0.0 |
| run 2 · **hybrid+rerank** | 0.94 | 0.92 | 1.00 | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 | 1.4 | 0.0 |

**Failures, run 2, vector:** leak-en: cite, fact; payrun-zh: cite, fact

**Failures, run 2, hybrid+rerank:** sz-docs-en: cite

- **Every vector failure is a retrieval miss** (`leak-en`, `payrun-zh`). The only hybrid failure is an inventory answer that named the document but not its path; it never searched.
- **Hybrid needs fewer searches** (1.3–1.4 vs 1.5–1.6 per question): the first search succeeds more often, so the agent retries less.
- `leak-en` passed in both hybrid runs with a single query containing "customer", as the replay predicted. Vector's one pass came from a guessed `department="compliance"` filter that happened to narrow the search to the right chunks.
- With 17 questions and 2 runs, the overall gap (0.94 vs 0.97) is within run-to-run noise. The retrieval-level results above are the stronger evidence.

## 2. Query expansion: search in both languages

Every failure above has one root: the question and its answer share no words. "data breach" never appears in a policy that says 資料外洩, and the small multilingual embedder does not bridge the gap for this chunk. `--expand` adds a version of the query in the other language. Each retriever runs on every version, RRF fuses all the lists, and the reranker scores the candidates against the **original** query.

- **`glossary`:** [examples/glossary.csv](../examples/glossary.csv), 87 rows such as `data breach|data leak ↔ 資料外洩`. They were written from the ten documents, with the usual Hong Kong translations (the PCPD's 資料外洩 for "data breach") and everyday variants staff type (出糧, 糧單, 的士, 專票). Free and instant. The rows were written after seeing which questions failed, so read the glossary numbers as "what a maintained term list buys you", not as a blind test.
- **`llm`:** gpt-4o-mini via OpenRouter translates the query: English into Hong Kong Traditional Chinese, Chinese into English. Every translation behind these tables is cached in [llm_expansions.jsonl](llm_expansions.jsonl), so `hrag replay` and `hrag eval` reproduce them without an API key.
- **`glossary+llm`:** both versions.

### Same reranker budget, spent on depth or on a second language

The reranker's pool grows by `pool` for each query version (5 → 10 → 15 here), so a fair comparison holds that budget fixed. Replay of the agent's queries, **hybrid + rerank**, `full` corpus (28 chunks), chunk 200:

| expansion | candidates per list | reranker sees | `leak-en` | all agent queries |
|---|---|---|---|---|
| none | 5 | 5 | 4/10 | 0.86 |
| none | 10 | 10 | 4/10 | 0.88 |
| **glossary** | 5 | 10 | **9/10** | **0.98** |
| **llm** | 5 | 10 | **7/10** | **0.94** |
| none | 15 | 15 | 6/10 | 0.92 |
| **glossary + llm** | 5 | 15 | **10/10** | **1.00** |

Every mode and question: [replay-full-local-pool5-expand.md](runs/replay-full-local-pool5-expand.md). On the `base` corpus the pattern repeats (`leak-en` 4 → 9, 7 and 10 of 10, [replay-base-local-pool5-expand.md](runs/replay-base-local-pool5-expand.md)), but there 15 candidates are the whole 15-chunk corpus, and even no expansion reaches 10/10.

- **Depth doesn't fix a vocabulary gap.** Doubling the pool leaves `leak-en` at 4/10: for the "data breach" queries, the answer is not in the top 10 of either list.
- **A second language does.** The glossary adds 資料外洩, and BM25 ranks the answer chunk #1 for all 9 queries it matches. Its one miss, "breach notification requirements", contains no glossary term.
- **The glossary and the LLM miss different queries,** so together they reach 10/10, just as vectors and BM25 fail on opposite questions (section 3).

### Where the answer got lost: RRF rewards agreement

The first version reranked a fixed pool of 5. On the `base` corpus with the glossary, the expanded BM25 list ranked the answer #1 for all 9 matched queries, yet after fusing four lists (vector and BM25, for each version) RRF placed it 3rd to 6th. A chunk that several lists agree on collects several votes: one #1 vote is worth 1/61 = 0.0164, while two votes at ranks 4 and 5 are worth 1/64 + 1/65 = 0.0310. Three times the answer landed 6th, just outside the pool, and the reranker never saw it. Whenever the reranker did see it, it ranked it #1. Hence the rule above: each query version brings its own `pool` of candidates.

### The LLM translates the language, not the company's vocabulary

| the agent searched | gpt-4o-mini wrote | the documents say |
|---|---|---|
| data breach notification | 資料**洩漏**通知 | 資料**外洩** |
| customer data leak reporting time | 客戶**數據洩漏**報告時間 | 資料外洩 |
| breach notification requirements | **違規**通知要求 (a rule violation) | 資料外洩 |
| working from home policy | **在家**工作政策 | **喺家**工作 |

All are correct Chinese, but none uses the documents' term. Hong Kong policies follow the PCPD's 資料外洩 and use written Cantonese such as 喺. The model writes standard written Chinese, sometimes with mainland terms (數據). BM25 matches characters exactly. Of the LLM's 7 of 10, four were already found by the English query (through "customer"), and three came through characters the translation happens to share with the answer (資料, 通知). The vector lists barely helped: even with a Chinese translation, the answer chunk reached the vector top 5 only once. A glossary carries the house vocabulary. The LLM covers phrasing nobody listed; it decoded the colloquial 專票 as "special invoice" on its own.

### LLM output drifts, and once it changed the amount

- **translate-v1** showed "HKD 5,000" as an example in the prompt. A CLI bug (since fixed) translated the 35 eval questions twice. 7 came back worded differently, and **3 of the 70 translations changed an amount or currency**: 五萬人民幣 became HKD 50,000 and HKD 5,000, and HKD 500 became HKD 5,000. The prompt's example leaked into the output. Evidence: [llm_expansions-translate-v1.jsonl](runs/llm_expansions-translate-v1.jsonl).
- **translate-v2** has no example values and states the rule. [llm_drift.py](llm_drift.py) translated all 84 queries a second time. 9 came back worded differently: 3 only in capitalisation, 1 only in 超過 vs Simplified 超过 (both passes had slipped into Simplified 采购订单 for 採購訂單), and 1 left "corporate client" in English. **None of the 168 translations changed a number or currency** ([llm-drift-translate-v2.jsonl](runs/llm-drift-translate-v2.jsonl)).
- **Guard the rewrite.** `keeps_facts` drops a translation whose currencies differ from the query's, or whose numbers differ when both sides write digits. It catches all 3 v1 errors and still lets "signal 8" become 八號風球. A dropped translation only means searching without expansion.
- **Cache the rewrite.** Even at temperature 0 the output varies, so the cache is what makes evals reproducible. It also removes the wait for repeated queries: a new translation took 1.6 s median (p90 2.3 s) through OpenRouter, while the glossary adds no measurable time.

### Repo 1's 25 questions and the exact-term set

`full` corpus, chunk 200, 5 candidates per list, hit@3 ([harbour_lane_qa-full-pool5-expand.md](runs/harbour_lane_qa-full-pool5-expand.md)):

| expansion | BM25 (English questions) | hybrid | hybrid + rerank (reranker sees) |
|---|---|---|---|
| none | 0.60 (0.47) | 0.84 | 0.88 (5) |
| none, 10 per list | 0.60 (0.47) | 0.84 | **1.00** (10) |
| glossary | 0.72 (0.65) | 0.88 | 0.92 (10) |
| llm | **0.88 (0.82)** | 0.88 | 0.96 (10) |
| glossary + llm | **0.88 (0.82)** | **0.92** | 0.96 (15) |

- **BM25 gains the most.** With a Chinese version of each English question, BM25's English hit@3 goes from 0.47 to 0.82.
- **`vat-invoice-zh` (專票) is fixed**, by the glossary row 專票 = 增值稅專用發票 and by the LLM's "special invoice", which BM25 matches against "VAT invoice".
- **Here a deeper pool wins (1.00 vs 0.96).** The remaining misses (`claim-payday-en`, `supplier-payrun-en`, crowded out by the payroll distractor) sit just below the top 5 in the original lists. They are near misses, not vocabulary gaps, and depth fixes those. Expansion is the tool for vocabulary gaps.
- **No harm to exact terms.** On the 10 exact-term questions, BM25 and hybrid + rerank stay at 1.00 with every expansion ([keyword_qa-full-pool5-expand.md](runs/keyword_qa-full-pool5-expand.md)).

### Live check: repo 3's agent with glossary + llm

`hrag agent-eval --modes hybrid+rerank --expand glossary+llm`, with the same setup as the live check in section 1: base corpus, chunk 200, pool 5, gpt-4o-mini, 2 runs. Answers: [agent-base-pool5-expand-run1.jsonl](runs/agent-base-pool5-expand-run1.jsonl), [run2](runs/agent-base-pool5-expand-run2.jsonl).

| run | pass | cite | fact | lang | refuse | tool calls / q |
|---|---|---|---|---|---|---|
| no expansion, run 1 (section 1) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.3 |
| no expansion, run 2 (section 1) | 0.94 | 0.92 | 1.00 | 1.00 | 1.00 | 1.4 |
| glossary + llm, run 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.3 |
| glossary + llm, run 2 | 0.94 | 1.00 | 1.00 | 1.00 | 0.67 | 1.4 |

- **Run 2's one failure is a scorer miss.** For `parking-zh` the agent answered 「無法確定公司是否提供員工泊車位津貼。所有相關文檔似乎沒有直接提到…」, a correct refusal whose wording repo 3's scorer doesn't recognise. Read as a person would, both runs pass 17/17.
- **`leak-en` passed with one search in both runs,** but both of the agent's queries contained "customer", which hybrid + rerank already handled. The agent drew easy queries this time, so this eval can't show the expansion gain; the replay above can.
- **End to end, expansion broke nothing** and kept the agent at 1.3–1.4 searches per question. 17 questions × 2 runs is too small to show a gain.

## 3. Repo 1's 25 questions, realistic setting (`full` corpus, multilingual, chunk 200, pool 5)

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| **vector** | 0.48 | 0.72 | 0.58 | 0.82 | 0.50 |
| **keyword** | 0.52 | 0.60 | 0.56 | 0.47 | 0.88 |
| **hybrid** | 0.40 | 0.84 | 0.60 | 0.82 | 0.88 |
| **vector+rerank** | 0.76 | 0.84 | 0.80 | 0.88 | 0.75 |
| **hybrid+rerank** | 0.76 | 0.88 | 0.82 | 0.88 | 0.88 |

- **Vector and BM25 fail on opposite questions.** Vectors win English questions about Chinese text (en 0.82 vs 0.47). BM25 wins Chinese questions (zh 0.88 vs 0.50 once the distractors arrive). Hybrid gets both: 0.72 and 0.60 become **0.84**.
- **`hybrid+rerank` is best:** hit@3 0.88, MRR 0.82. Against `vector+rerank`, Chinese questions go from 0.75 to 0.88, because BM25 puts the right chunks into the pool.
- **Remaining misses:**
  - `claim-payday-en` and `supplier-payrun-en` are taken by the *payroll* distractor ("pay day").
  - `vat-invoice-zh` asks about **專票**, everyday shorthand for 增值稅專用發票. The abbreviation shares no bigram with the full term, so keyword and vector search both miss it. That needs synonym or query expansion, not better fusion.

## 4. Exact terms (10 questions designed around codes and amounts)

| run | hit@1 | hit@3 | MRR@3 | hit@3 en | hit@3 zh |
|---|---|---|---|---|---|
| **vector** | 0.70 | 0.80 | 0.75 | 0.83 | 0.75 |
| **keyword** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| **hybrid** | 0.80 | 1.00 | 0.88 | 1.00 | 1.00 |
| **vector+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| **hybrid+rerank** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

BM25 is perfect on `FIN-07`, `HKD 5,000`, `RMB 50,000` and `增值稅專用發票`, with hit@1 1.00 in every configuration of the grid below. This set is deliberately keyword-friendly; it shows what vectors blur, not a typical question mix.

## 5. Full grid with pool 20 - read with care

With pool 20 and a 7–28 chunk corpus, the reranker usually sees **every chunk**. That's why `vector+rerank` and `hybrid+rerank` are nearly always identical here: the rerank rows measure the cross-encoder as a full ranker, not as a re-ranker of a small candidate pool. The non-rerank rows are fine to compare.

<details><summary>25 questions (repo 1's set)</summary>

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

</details>

<details><summary>10 exact-term questions</summary>

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

</details>

## What we learned

1. **Keyword search needs a tokenizer that understands Chinese.** With SQLite's default tokenizer, 外洩 matches nothing; with character bigrams it works.
2. **BM25 and vectors are complementary.** Hybrid fixes the failures of both, but can also drag a strong retriever down: base corpus at chunk 400 went from vector 1.00 to hybrid 0.96. With weak `hash` vectors on the distractor corpus, fusion pushed a good BM25 hit out of the top 4 (`leave-days-en` 2/2 → 0/2).
3. **A reranker only reorders what it is given.** Gains in hit@1 are large, but recall is capped by the candidate pool. A pool as big as the corpus makes any reranker look perfect.
4. **Hong Kong-specific failures need language work, not fusion.** Cross-lingual queries ("data breach" vs 資料外洩) and colloquial abbreviations (專票) defeat both retrievers. Query expansion fixes them (section 2).
5. **Small corpus, small sets.** 25, 10 and 10 questions over 15–28 chunks: one question is 0.04–0.10. Read differences accordingly.
6. **Depth and breadth fix different failures.** A deeper pool fixes near misses; a second language fixes vocabulary gaps. Compare them at the same reranker budget.
7. **Translate into the company's words, not just its language.** gpt-4o-mini wrote 資料洩漏 and 數據洩漏; the policy says 資料外洩. A glossary records the house vocabulary, and the LLM covers the rest.
8. **Never trust an LLM rewrite with an amount.** Cache it, check it (`keeps_facts`), and let the reranker judge with the user's own words.

## Reproduce

```bash
uv sync --extra local
uv run hrag replay --corpus base --embed local --chunk-size 200 --pool 5
uv run hrag eval --qa eval/harbour_lane_qa.jsonl --embed local --corpus full --sizes 200 --pool 5 --show-misses
uv run hrag eval --qa eval/keyword_qa.jsonl --embed hash,local --corpus base,full --sizes 200,400

# Section 2: query expansion. LLM translations come from eval/llm_expansions.jsonl, no API key needed.
uv run hrag replay --corpus full --embed local --chunk-size 200 --pool 5 --expand none,glossary,llm,glossary+llm
uv run hrag replay --corpus full --embed local --chunk-size 200 --pool 10      # same reranker budget, no expansion
uv run hrag eval --qa eval/harbour_lane_qa.jsonl --embed local --corpus full --sizes 200 --pool 5 --expand none,glossary,llm,glossary+llm --show-misses
uv run python eval/llm_drift.py                                                # needs an API key: translates every query again
```
