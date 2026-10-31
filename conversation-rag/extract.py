"""Automatic fact extraction for conversation memory: one LLM call per turn, cached, checked against the hand labels.

The model reads one turn and returns the facts that set or change a value. Keys are kept to a fixed
vocabulary so that "office" in turn 1 and "office" in turn 5 are the same key. That vocabulary is
supplied by hand, which is a limit: a new kind of fact still needs a new key here.

Needs OPENAI_API_KEY and OPENAI_BASE_URL (OpenRouter works), e.g. from the shell profile.
Writes:
  extracted_facts.json   the facts per turn (what run.py reads with EXTRACTED=1)
  extract_cache.jsonl    raw answers, so re-runs cost nothing
"""

import hashlib
import json
import os
import sys
from pathlib import Path

here = Path(__file__).parent
sys.path.insert(0, str(here.parent / "src"))

from hybridrag._http import post_json  # noqa: E402

MODEL = "openai/gpt-4o-mini"
PROMPT_VERSION = "conv-facts-v1"
VOCAB = {
    "office": "辦公室地址",
    "standup_time": "Standup 時間",
    "booking_lead": "會議室提前預訂日數",
    "expense_deadline": "報銷截數",
}
SYSTEM = (
    "You read ONE turn of a chat between a team member and an assistant. "
    "Return JSON: {\"facts\": [{\"key\": str, \"label\": str, \"value\": str}]}. "
    "List only facts that set or change a value the team relies on (an address, a time, a deadline, a rule). "
    "Use these keys exactly when they apply: " + json.dumps(VOCAB, ensure_ascii=False) + ". "
    "Use a new snake_case key only if none fits, with a short Chinese label. "
    "value is the value as the turn states it, copied, not translated. "
    "Return {\"facts\": []} when the turn sets no value (questions, greetings, weather, small talk)."
)


def ask(turn: dict, cache: dict, cache_path: Path) -> list[dict]:
    key = hashlib.sha256(f"{MODEL}|{PROMPT_VERSION}|{turn['role']}|{turn['text']}".encode()).hexdigest()
    if key in cache:
        return cache[key]
    url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    payload = {
        "model": MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"role: {turn['role']}\ntext: {turn['text']}"},
        ],
    }
    data = post_json(url, payload, {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}, timeout=60)
    facts = json.loads(data["choices"][0]["message"]["content"]).get("facts", [])
    cache[key] = facts
    with cache_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"key": key, "turn": turn["turn"], "model": MODEL, "prompt": PROMPT_VERSION,
                            "facts": facts, "usage": data.get("usage", {})}, ensure_ascii=False) + "\n")
    return facts


def main() -> None:
    turns = [json.loads(line) for line in (here / "turns.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    cache_path = here / "extract_cache.jsonl"
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                cache[row["key"]] = row["facts"]

    extracted = {}
    for t in turns:
        extracted[t["turn"]] = ask(t, cache, cache_path)

    (here / "extracted_facts.json").write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8")

    # Check against the hand labels. A fact matches when the key is the same and one value contains the other
    # ("每日 9:30" contains "9:30"). Turns where the assistant only repeats a known value count as extra facts.
    def same(gold_kv, got_kv):
        return gold_kv[0] == got_kv[0] and (gold_kv[1] in got_kv[1] or got_kv[1] in gold_kv[1])

    tp = fp = fn = 0
    for t in turns:
        gold = [(f["key"], f["value"]) for f in t.get("facts", [])]
        got = [(f["key"], str(f["value"])) for f in extracted[t["turn"]]]
        matched_gold = {g for g in gold for r in got if same(g, r)}
        matched_got = {r for r in got for g in gold if same(g, r)}
        tp += len(matched_gold)
        fn += len(gold) - len(matched_gold)
        fp += len(got) - len(matched_got)
        if len(matched_gold) != len(gold) or len(matched_got) != len(got):
            print(f"turn {t['turn']:>2}  gold={gold}  got={got}")
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    print(f"facts: precision {precision:.2f} ({tp}/{tp + fp})  recall {recall:.2f} ({tp}/{tp + fn})")
    print("wrote", here / "extracted_facts.json")


if __name__ == "__main__":
    main()
