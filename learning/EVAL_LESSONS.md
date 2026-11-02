# How the evaluation was built, and what went wrong

This is the story behind the numbers in `eval/RESULTS.md`, told from the public-document side. It is for learners: each section is a mistake or a decision, and what it taught.

## What the system does

`hrag` answers a question by returning the top 3 chunks, not a generated answer. "Refusal" therefore means: the system returns nothing. A question is answerable if one of the top 3 chunks contains the answer.

Fixed configuration used for every run in this folder: 400/60 chunks, the local multilingual MiniLM embedder, the bge-reranker-v2-m3 cross-encoder with a refusal cut of 0.05, glossary expansion, and hybrid + rerank with top 3. The config was fixed before the runs and not tuned on results.

## Results on the dev sets

Dev sets are written from the three public source files. They measure changes; they are not a final test.

| Set | Questions | Year check on | Numbers | Refusals |
|---|---|---|---|---|
| v1 | 20 scored | yes | 12/12 | 7/8 |
| v2 | 17 scored | yes | 6/6 | 7/11 |
| v3 | 11 scored | yes | 3/3 | 4/8 |
| v4 | 13 scored | no | 10/10 | 0/3 |
| v5 (corrected labels) | 19 scored | yes | 5/6 | 8/13 |
| v5 (corrected labels) | 19 scored | no | 6/6 | 8/13 |

The numbers are correct and the refusal misses are explained below. The dev sets include the corrected labels; see "Labels can be wrong too".

## Lessons

### 1. A scoring bug changes the story silently

The first key generator read the source note in the expected answer as answer keys. "来源：…2025/26…" turned into the keys `2025` and `26`, so correct answers scored as wrong. The fix was to cut the source note from the expected text before extracting keys.

Two more fixes followed the same pattern: a bracketed note with a page number was read as a key (`約第31頁` gave the key `31`, which was not the answer), and a trailing full stop was read as part of a number (`26.`).

**Lesson:** the scorer is part of the experiment. Generate keys by one fixed rule, check the rule against every set, and record the hash of the questions and keys next to every result.

### 2. Old result files look valid

Some saved result files were produced before a scorer fix, so their summaries showed the old, wrong numbers. Rerunning with the current keys gave different totals, and the summary files were not updated.

**Lesson:** store the question and key hashes with each run (the runner does this), and re-score saved retrieval output with the current keys before comparing numbers. `rescore.py` does this without re-running retrieval.

### 3. A score threshold measures topic, not answerability

The refusal rule returns nothing when the best reranker score is below 0.05. The reranker scores how well a chunk matches the question's topic, not whether the specific fact is in the chunk.

Measured on dev v5, with the threshold off:

- off-topic questions (population, pet leave, stock market, WeChat Pay) score 0.001 to 0.007, so the cut refuses them;
- questions about a real topic with a missing item score 0.20 to 0.89, so the cut does not refuse them. Examples: a non-existent subhead (Subhead 115, scored 0.886), a missing quarter (2025-26 Q2, 0.311), a year that is absent (2024-25 Q4, 0.736);
- answerable controls score 0.94 to 0.98.

No single cut separates the missing-item questions from the controls, and the calibration came from a small set. Raising the cut would also change behaviour on answerable questions that were not tested.

**Lesson:** a retrieval system refuses by "nothing relevant found", not by "answer absent". To refuse missing items you need a check that looks for the specific entity or value.

### 4. A rule for years can be too narrow or too broad

The year-range check refuses a question that names a year range the documents never mention, such as 2026/27 when no document contains that range. It helped on dev v1 to v3, and it refused no answerable question there.

It has two known weaknesses:

- **Open-ended ranges.** The IRD table says "2025/26 及其後" (2025/26 and later). The check did not know that covers 2028/29, so it refused an answerable question (r12, the basic allowance for 2028/29).
- **Topic-blind coverage.** A first attempt to fix this counted "2019/20 及其後" in the tax guide as covering any later year, including the annual-leave question about 2026/27 in the Employment Ordinance. That question should be refused, and the attempt answered it. The fix was kept on a separate branch and not merged.

**Lesson:** a rule that checks only one feature (here, years) can be wrong in both directions. Test the rule on both answerable and unanswerable questions, and on every document it applies to.

### 5. Labels can be wrong too

Four refusal labels were wrong: the documents do answer them. Two are in dev v5 and two in dev v3. Checking each label against the text found r12 (2028/29 allowance, answerable from "2025/26 及其後"), r14 (2030 estate duty, answerable: estate duty no longer applies to deaths on or after 2006-02-11) and h01/h02 (2026/27 allowance and 2029/30 property tax, both answerable from open-ended phrases).

**Lesson:** when a system answers a question labelled "refusal", check the label against the source before blaming the system. The corrected labels are in `dev_sets/dev_set_v5_corrected*`. The uncorrected v3 labels for h01 and h02 are kept as they were, because they were used to measure the year check.

### 6. Small sets make single items look like trends

A few refusal items can decide a threshold question. A change that fixes one item and breaks another looks like a real result on a set of 8. Dev results in this folder are small (11 to 20 questions per set) and report counts, not percentages.

**Lesson:** report the counts and the items that changed. Do not tune a threshold until a larger set confirms the direction.

### 7. Blind sets must stay blind, and AI-written sets are not third-party

Several question sets were written by AI models. Asking another AI model to write or review questions does not make them independent. They are useful for finding problems, but their results describe the system only on those questions.

Tuning on a set that was already used to see failures contaminates it. For that reason the retrieval fixes were tuned only on dev sets, and the blind sets were kept out of this repository.

**Lesson:** label each evaluation set by who wrote it (author, another model, a third party), and keep the blind set out of any public repository until it has been used once for the final result.

### 8. A full-file reader beats top-3 retrieval on refusals here

On dev v5, a model that read the whole source files answered 13 of 13 refusal items correctly, against 8 of 13 for the system. The model is not a fix for the system, and it reads far more text than retrieval does. It is a useful comparison point: when the system misses something a full reader finds, the cause is retrieval (the answer is not in the top 3) or the score cut, not the source.

## What to try next

- A check that looks for the specific entity or value (a subhead, a quarter, a bare year) before a chunk is returned.
- A year rule that understands open-ended ranges, scoped to the document where the range appears.
- A larger dev set for refusals (15 or more items) before changing any threshold.
- Index-time expansion and a listwise reranker, as listed in the README's Contributing section.
