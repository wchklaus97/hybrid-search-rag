"""Does the LLM translate the same query the same way twice?

Re-translates every query in eval/llm_expansions.jsonl once more (temperature 0, same
prompt) and compares with the cached translation that the evals used.

    uv run python eval/llm_drift.py      # needs OPENAI_API_KEY (+ OPENAI_BASE_URL for OpenRouter)

Prints how many translations came back worded differently and how many changed a number
or a currency, and writes every pair to eval/runs/llm-drift-<prompt version>.jsonl.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from hybridrag.expand import DEFAULT_LLM, PROMPT_VERSION, LLMExpander, keeps_facts

EVAL = Path(__file__).parent


def main() -> None:
    rows = [json.loads(line) for line in (EVAL / "llm_expansions.jsonl").read_text(encoding="utf-8").splitlines()]
    cached = {r["query"]: r["translation"] for r in rows if r["model"] == DEFAULT_LLM and r["prompt"] == PROMPT_VERSION}
    with ThreadPoolExecutor(8) as pool:  # a fresh, cache-less expander per query: every call hits the API
        again = dict(zip(cached, pool.map(lambda q: LLMExpander(DEFAULT_LLM).translate(q), cached)))

    pairs = [{"query": q, "cached": t, "again": again[q], "same": t == again[q],
              "cached_keeps_facts": keeps_facts(q, t), "again_keeps_facts": keeps_facts(q, again[q])}
             for q, t in cached.items()]
    out = EVAL / "runs" / f"llm-drift-{PROMPT_VERSION}.jsonl"
    out.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pairs), encoding="utf-8")

    changed = [p for p in pairs if not p["same"]]
    broken = [p for p in pairs for k in ("cached", "again") if not p[f"{k}_keeps_facts"]]
    print(f"{PROMPT_VERSION} · {DEFAULT_LLM}: {len(pairs)} queries translated twice")
    print(f"  worded differently the second time: {len(changed)}")
    print(f"  translations that changed a number or currency: {len(broken)} of {2 * len(pairs)}")
    for p in changed:
        print(f"    {p['query']}\n      1: {p['cached']}\n      2: {p['again']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
