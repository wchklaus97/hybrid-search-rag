"""Generate scoring keys from the `expected` field only. Same rule for every evaluation set.

refusal            -> method "refusal" (correct only if the system refuses)
number / version   -> method "keys" with the digit groups of expected (>= 2 digits, or with a comma or decimal point);
                      if there are none, method "manual"
lookup             -> method "manual"

Fix 2: source notes without brackets (来源：...) are cut to the end of the string, and a trailing full stop is not part of a key.
Fix: the source note was being read as answer keys (e.g. "2025", "26", "104", "451").
Usage: python make_keys.py <questions.jsonl> <keys.json>
"""
import json
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(src, encoding="utf-8") if l.strip()]
out = {}
for r in rows:
    t = r["type"]
    # Keys come from the answer only. Drop the source note in （來源：…） / (來源：…), which holds file names and page or item numbers.
    exp = re.sub(r"[（(]?(?:來源|来源)[：:].*$", "", r["expected"], flags=re.S)  # bracketed or bare note, to the end
    if t == "refusal":
        out[r["id"]] = {"type": t, "method": "refusal"}
    elif t in ("number", "version"):
        toks = [m.rstrip(".") for m in re.findall(r"\d[\d,\.]*", exp) if len(m.replace(",", "").replace(".", "")) >= 2 or "," in m or "." in m]
        out[r["id"]] = {"type": t, "method": "keys" if toks else "manual", "keys": toks}
    else:
        out[r["id"]] = {"type": t, "method": "manual"}
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(dst, len(out))
