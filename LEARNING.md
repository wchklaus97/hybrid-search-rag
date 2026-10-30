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
- 真正穩陣嘅解決方法：**跨語言 query 擴展**（"data breach" 同時搜「資料外洩」）或更強嘅多語 embedding。見第 8 節。

### 8. 跨語言 query 擴展（query expansion）
問題根源：英文問題同中文答案**冇共同字眼**。"data breach" 喺一份寫「資料外洩」嘅政策入面一個字都搵唔到。
做法：`--expand` 為每條 query 加一個**另一種語言**嘅版本。每個檢索器對每個版本都搜一次，RRF 合併所有清單，最後 reranker 用**用戶原本嘅字眼**排序。
- **glossary（公司詞彙表）**：`examples/glossary.csv`，87 行中英對照（資料外洩 = data breach、出糧 = pay day、專票 = 增值稅專用發票）。免費、即時、結果穩定，但只識有人寫低咗嘅字。
- **llm（翻譯）**：gpt-4o-mini 譯成另一種語言。乜嘢講法都識，但每條新 query 要等大約 1.6 秒、要少少錢，而且輸出會變。
- **glossary+llm**：兩樣一齊用。

結果（28 個 chunk，reranker 睇嘅候選數目相同）：`leak-en` 冇擴展係 4/10，pool 加倍都係 4/10；用 glossary 9/10、用 LLM 7/10、兩樣一齊 **10/10**。但 repo 1 嘅 25 條題，pool 加倍（1.00）反而好過擴展（0.96）：剩低嘅錯只係排第 6–10，唔係用字問題。**深度解決「差少少」，第二種語言解決「用字唔同」。**

三個教訓：
1. **RRF 鍾意「多數票」。** 擴展後嘅 BM25 將答案排第 1，但四張清單融合之後，答案跌到第 3–6：其他 chunk 喺幾張清單都有份，票數多啲。pool 固定 5 個嘅話，答案會俾人擠出去。所以每多一個 query 版本，reranker 就多睇 5 個候選。
2. **LLM 譯到語言，譯唔到公司用字。** 佢將 "data breach" 譯做「資料洩漏」「數據洩漏」，但政策同私隱專員公署（PCPD）都用「資料外洩」；"working from home" 譯做「在家工作」，手冊就寫「喺家工作」。BM25 只認一模一樣嘅字。詞彙表記低公司用字，LLM 就補詞彙表冇寫到嘅講法（例如佢自己識「專票」即係 special invoice）。
3. **LLM 改寫會飄，仲試過改金額。** temperature 0 都會變：84 條 query 譯第二次，有 9 條字眼唔同。第一版 prompt 有個 "HKD 5,000" 做例子，結果「HKD 500」被譯成「HKD 5,000」，「五萬人民幣」變咗「HKD 50,000」。解決：prompt 唔放例子數值；`keeps_facts` 檢查貨幣同數字，唔啱就唔用個翻譯；所有翻譯存入 cache，評估先可以重現；reranker 永遠用用戶原本嘅問題。

### 常見錯誤
- 中文用預設 tokenizer 做關鍵字搜尋。
- 以為混合一定好過單一方法。
- 用大過語料庫嘅 pool 去評估 reranker。
- 將 agent 層面 0.03 嘅差距當成真差異（兩次重跑都可以差 0.06–0.12）。
- 比較擴展同唔擴展嗰陣，冇固定 reranker 睇嘅候選數目。
- 以為 LLM 翻譯一定會保留金額同貨幣。
- 用 LLM 翻譯代替公司詞彙表。

### 練習
1. `hrag search "FIN-07" --mode all`，比較每個模式嘅排名同原因。
2. `hrag replay --pool 20` 同 `--pool 5`，解釋點解 rerank 結果唔同。
3. 喺 `eval/keyword_qa.jsonl` 加一條用口語縮寫嘅題目，睇邊個模式搵到。
4. 喺 `examples/glossary.csv` 嘅 data breach 嗰行加 `breach`，再跑 `hrag replay --corpus full --pool 5 --expand none,glossary`，睇 `leak-en` 會唔會由 9/10 變 10/10。
5. 用同一個 reranker 預算比較：`--pool 10 --expand none` 對 `--pool 5 --expand glossary`。點解 replay 同 25 條題會得出唔同結論？
6. 跑 `uv run python eval/llm_drift.py`（要 API key），睇同一條 query 譯兩次有幾多條唔同。

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
- **The robust fix is cross-lingual query expansion** (also search 資料外洩 for "data breach"), or a stronger multilingual embedder. See section 8.

### 8. Cross-lingual query expansion
The root problem: the question and its answer **share no words**. "data breach" never appears in a policy that says 資料外洩.
The fix: `--expand` adds a version of each query in **the other language**. Each retriever runs on every version, RRF fuses all the lists, and the reranker still orders the results with **the user's own words**.
- **glossary (the company's term list):** `examples/glossary.csv`, 87 bilingual rows (資料外洩 = data breach, 出糧 = pay day, 專票 = special VAT invoice). Free, instant and stable, but it only knows words someone wrote down.
- **llm (translation):** gpt-4o-mini translates into the other language. It knows any phrasing, but each new query waits about 1.6 s, costs a little, and the output varies.
- **glossary+llm:** both.

Results (28 chunks, same number of candidates for the reranker): `leak-en` is 4/10 without expansion and still 4/10 with a doubled pool. It is 9/10 with the glossary, 7/10 with the LLM, and **10/10** with both. On repo 1's 25 questions, though, a doubled pool (1.00) beats expansion (0.96): the remaining misses rank 6th–10th, which is not a vocabulary problem. **Depth fixes near misses; a second language fixes vocabulary gaps.**

Three lessons:
1. **RRF rewards agreement.** BM25 on the expanded query ranks the answer #1, but after fusing four lists it drops to 3rd–6th: other chunks appear in several lists and collect more votes. With a fixed pool of 5, the answer gets pushed out. So each query version adds 5 candidates for the reranker.
2. **An LLM translates the language, not the company's vocabulary.** It wrote 資料洩漏 and 數據洩漏 for "data breach", but the policy and the PCPD say 資料外洩. It wrote 在家工作 where the handbook says 喺家工作. BM25 only matches identical characters. The glossary records the house vocabulary; the LLM covers what the glossary misses (it knew 專票 means "special invoice").
3. **LLM rewrites drift, and once changed an amount.** Even at temperature 0, 9 of 84 queries were worded differently on a second pass. The first prompt showed "HKD 5,000" as an example, and the model turned HKD 500 into HKD 5,000 and 五萬人民幣 into HKD 50,000. The fixes: no example values in the prompt; `keeps_facts` drops a translation whose currencies or numbers changed; every translation is cached so evals are reproducible; and the reranker always uses the user's original question.

### Common mistakes
- Keyword search on Chinese with the default tokenizer.
- Assuming hybrid always beats a single method.
- Evaluating a reranker with a pool larger than the corpus.
- Reading a 0.03 agent-level gap as real when identical reruns differ by 0.06–0.12.
- Comparing expansion with no expansion without fixing the reranker budget.
- Trusting an LLM rewrite to keep amounts and currencies.
- Using LLM translation in place of the company's own vocabulary.

### Exercises
1. Run `hrag search "FIN-07" --mode all` and compare each mode's ranks and reasons.
2. Run `hrag replay` with `--pool 20` and with `--pool 5`, and explain why the rerank columns differ.
3. Add a colloquial-abbreviation question to `eval/keyword_qa.jsonl` and see which mode finds it.
4. Add `breach` to the data breach row of `examples/glossary.csv`, run `hrag replay --corpus full --pool 5 --expand none,glossary`, and check whether `leak-en` goes from 9/10 to 10/10.
5. Compare at the same reranker budget: `--pool 10 --expand none` against `--pool 5 --expand glossary`. Why do the replay and the 25 questions disagree?
6. Run `uv run python eval/llm_drift.py` (needs an API key) and count how many queries translate differently the second time.
