# LEARNING — 混合搜尋 / Hybrid search for Hong Kong code-mixed text

情境：虛構嘅 Harbour Lane 集團（香港總部 + 深圳子公司），文件中英夾雜，仲有六份「干擾文件」。
Scenario: the fictional Harbour Lane group (HK head office + Shenzhen subsidiary), code-mixed documents, plus six distractor documents.

---

## 繁體中文（zh-HK）

### 1. 點解中文關鍵字搜尋一開始就壞咗？
關鍵字引擎靠空格同標點分詞。中文冇空格，SQLite FTS5 預設會將成句變成**一個** token：喺「如懷疑資料外洩，須喺 24 小時內通知 Compliance Officer」入面搜「外洩」或者「資料外洩」，結果係 **0**。
解決：`cjk_tokenize.py` 將中文切成**重疊雙字**（資料外洩 → 資料 料外 外洩），唔使字典。另外：`HKD 5,000 → hkd 5000`、`FIN-07 → fin-07 fin 07`、全形轉半形。

### 2. BM25 係咩？
經典關鍵字排名公式：
- 詞出現得多 → 分高，但會**飽和**（出現 10 次唔係 10 倍好）—— 參數 k1。
- 長文件會被**長度正規化**扣分 —— 參數 b。
- **IDF**：越少文件有嘅詞越值錢（「FIN-07」好值錢，「的」唔值錢）。
FTS5 內建 `bm25()`（k1=1.2、b=0.75）。

### 3. 向量 vs BM25：各有所長
- 向量識**意思**同**跨語言**：英文問題搵中文政策（en 0.82 vs BM25 0.47）。
- BM25 識**精確字眼**：編號、金額、專有名詞（FIN-07、HKD 5,000 hit@1 = 1.00）；中文題更穩陣（zh 0.88 vs 向量 0.50，加咗干擾文件之後）。
- 兩個會喺**相反**嘅題目失手 → 混合搜尋（hybrid）兩邊都攞到：0.72 / 0.60 → **0.84**。

### 4. 混合（RRF）唔係免費
RRF 只睇排名合併兩張清單。好處：唔使理兩邊分數尺度。壞處：一邊差嘅時候會拖低另一邊 —— hash 向量 + 干擾文件，`leave-days-en` BM25 本身 2/2，混合後變 0/2。

### 5. 重排（rerank）：bi-encoder vs cross-encoder
- Bi-encoder（向量）：問題同段落**分開**變向量再比較 —— 快，可以掃晒成個語料庫。
- Cross-encoder：問題同**一段**段落**一齊**讀，直接俾相關分 —— 準好多，但慢，只可以處理少量候選。
- 所以：先用便宜方法攞候選池（pool），再 rerank。
- **陷阱**：pool 大過語料庫（本 repo 只有 15–28 個 chunk），rerank 就等於睇晒所有嘢，點都靚。用 pool 5 先見到真相：**rerank 救唔到冇被檢索到嘅 chunk**（vector+rerank 0/10）。

### 6. Query replay：唔使錢嘅「如果當時」測試
repo 3 嘅 agent 評估存低咗佢每次真正發出嘅 query。`hrag replay` 用新檢索器重跑呢啲 query，睇答案會唔會喺 top 4 出現。結果：`leak-en` 由 0/10 → 4/10。限制：更好嘅結果可能會改變 agent 下一步搜咩。

### 7. 香港文件嘅特別問題
- **中英夾雜帶來嘅運氣**：4 條成功嘅 query 都有「customer」，因為答案旁邊啱啱有句英文 "obtain the customer's consent"。用 "breach"、"notification" 嘅 query 全部失敗 —— 文件寫嘅係「資料外洩」「通知」。
- **口語縮寫**：「專票」= 增值稅專用發票，兩者冇共同雙字，關鍵字同向量都搵唔到 → 需要同義詞 / query 改寫。
- 真正穩陣嘅解決方法：**跨語言 query 擴展**（"data breach" 同時搜「資料外洩」）或更強嘅多語 embedding。

### 常見錯誤
- 中文用預設 tokenizer 做關鍵字搜尋。
- 以為混合一定好過單一方法。
- 用大過語料庫嘅 pool 去評估 reranker。
- 將 agent 層面 0.03 嘅差距當成真差異（兩次重跑都可以差 0.06–0.12）。

### 練習
1. `hrag search "FIN-07" --mode all`，比較每個模式嘅排名同原因。
2. `hrag replay --pool 20` 同 `--pool 5`，解釋點解 rerank 結果唔同。
3. 喺 `eval/keyword_qa.jsonl` 加一條用口語縮寫嘅題目，睇邊個模式搵到。
4. 試寫一個簡單 query 擴展（例如 "data breach" → 「資料外洩」），用 replay 量度 `leak-en` 有冇改善。

---

## English

### 1. Why Chinese keyword search is broken out of the box
Keyword engines split on spaces and punctuation. Chinese has none, so SQLite FTS5's default tokenizer turns a whole clause into **one** token: searching 外洩 or 資料外洩 inside "如懷疑資料外洩，須喺 24 小時內通知 Compliance Officer" returns **0** rows.
Fix: `cjk_tokenize.py` splits CJK into **overlapping bigrams** (資料外洩 → 資料 料外 外洩), no dictionary needed; plus `HKD 5,000 → hkd 5000`, `FIN-07 → fin-07 fin 07`, full-width normalisation.

### 2. What BM25 is
The classic keyword ranking formula:
- more occurrences of a term score higher, but **saturate** (10 mentions is not 10× better): parameter k1
- long documents are **length-normalised**: parameter b
- **IDF**: rare terms are worth more (FIN-07 is valuable, "the" is not)

FTS5 has `bm25()` built in (k1=1.2, b=0.75).

### 3. Vectors vs BM25: different strengths
- **Vectors know meaning and cross languages:** English questions about Chinese policies (en 0.82 vs BM25 0.47).
- **BM25 knows exact strings:** codes, amounts and names (FIN-07, HKD 5,000: hit@1 1.00). It's also steadier on Chinese questions (zh 0.88 vs vectors 0.50 once the distractors arrive).
- **They fail on opposite questions**, so hybrid gets both: 0.72 / 0.60 → **0.84**.

### 4. Hybrid (RRF) is not free
RRF merges by rank only, so score scales don't matter. But a bad list drags a good one down: with `hash` vectors and distractors, `leave-days-en` is 2/2 with BM25 alone and 0/2 with hybrid.

### 5. Reranking: bi-encoder vs cross-encoder
- **Bi-encoder (vectors):** query and passage are embedded **separately** and compared. Fast enough to scan everything.
- **Cross-encoder:** reads the query and **one** passage **together** and scores relevance. Much more accurate, far too slow for a whole corpus.
- So retrieve a cheap candidate pool first, then rerank it.
- **Trap:** with a pool larger than the corpus (this repo has only 15–28 chunks), the reranker sees everything and looks perfect. Pool 5 shows the truth: **a reranker cannot rescue a chunk that was never retrieved** (vector + rerank: 0/10).

### 6. Query replay: a free "what if" test
Repo 3's agent eval saved every query the agent actually sent. `hrag replay` re-runs them against a new retriever and checks whether the answer would have been in the top 4: `leak-en` goes from 0/10 to 4/10. Caveat: better results could have changed what the agent searched next.

### 7. Hong Kong-specific problems
- **Code-mixed luck:** all 4 successful queries contain "customer", because an English sentence ("obtain the customer's consent") happens to sit next to the answer. Queries with "breach" or "notification" all fail, because the documents say 資料外洩 and 通知.
- **Colloquial abbreviations:** 專票 means 增值稅專用發票 (special VAT invoice), but the two share no bigram, so keyword and vector search both miss it. This needs synonyms or query rewriting.
- **The robust fix is cross-lingual query expansion** (also search 資料外洩 for "data breach"), or a stronger multilingual embedder.

### Common mistakes
- Keyword search on Chinese with the default tokenizer.
- Assuming hybrid always beats a single method.
- Evaluating a reranker with a pool larger than the corpus.
- Reading a 0.03 agent-level gap as real when identical reruns differ by 0.06–0.12.

### Exercises
1. Run `hrag search "FIN-07" --mode all` and compare each mode's ranks and reasons.
2. Run `hrag replay` with `--pool 20` and with `--pool 5`, and explain why the rerank columns differ.
3. Add a colloquial-abbreviation question to `eval/keyword_qa.jsonl` and see which mode finds it.
4. Write a simple query expansion (e.g. "data breach" → 資料外洩) and measure `leak-en` with replay.
