"""Re-score saved runs with a keys file. No retrieval is re-run; it reads the top-3 texts already saved in *_results.json.

Usage: python rescore.py <results.json> <keys.json>
Prints per-type counts and the list of auto-scored ids with verdicts under the given keys.
"""
import json
import sys

results_path, keys_path = sys.argv[1], sys.argv[2]
results = json.load(open(results_path, encoding="utf-8"))
keys = json.load(open(keys_path, encoding="utf-8"))


def norm(s):
    return s.replace(",", "")


by_type, auto, manual, verdicts = {}, 0, 0, {}
for r in results:
    k = keys[r["id"]]
    top = r["modes"]["hybrid+rerank"]["top"] if "modes" in r else r["top"]  # run_blind and run_dev formats
    if k["method"] == "refusal":
        v = "correct" if len(top) == 0 else "wrong"
    elif k["method"] == "keys":
        v = "correct" if any(all(norm(t) in norm(h["text"]) for t in k["keys"]) for h in top) else "wrong"
    else:
        v = "manual"
        manual += 1
    verdicts[r["id"]] = v
    if v in ("correct", "wrong"):
        auto += 1
        by_type.setdefault(r["type"], [0, 0])
        by_type[r["type"]][0] += v == "correct"
        by_type[r["type"]][1] += 1
print(f"auto {sum(c for c, _ in by_type.values())}/{auto}, manual {manual}")
print({t: f"{c}/{n}" for t, (c, n) in by_type.items()})
print("wrong:", [i for i, v in verdicts.items() if v == "wrong"])
