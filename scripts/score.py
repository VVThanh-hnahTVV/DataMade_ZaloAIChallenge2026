"""Chấm bộ giải sổ-bán-hàng trên các business train có cùng schema (so với answers.jsonl)."""
import json, sys, unicodedata, collections
from datetime import date
sys.path.insert(0, "src")
from ledger_solver import Ledger, solve, norm_name

def eq_str(a, b, alias):
    na = norm_name(a)
    return na == norm_name(b) or na in {norm_name(x) for x in (alias or [])}

def correct(pred, ref):
    if pred["type"] != ref["type"]:
        return False
    t = ref["type"]
    if t == "unanswerable": return True
    pa, ra = pred["answer"], ref["answer"]
    if t == "number": return abs(pa - ra) < 1e-6 or round(pa, 2) == round(ra, 2)
    if t == "percent": return round(pa, 2) == round(ra, 2)
    if t in ("date", "boolean"): return pa == ra
    if t == "string": return eq_str(pa, ra, ref.get("alias"))
    if t == "list":
        if len(pa) != len(ra): return False
        al = ref.get("alias") or [None] * len(ra)
        for x, y, i in zip(pa, ra, range(len(ra))):
            if isinstance(y, str):
                if not eq_str(str(x), y, al[i] if i < len(al) and isinstance(al[i], list) else None): return False
            elif abs(x - y) > 1e-6: return False
        return True
    return False

if __name__ == "__main__":
    bizs = sys.argv[1:]
    qs = {}
    for l in open("train/questions.jsonl"):
        x = json.loads(l); qs[x["id"]] = x
    cache = {}
    tot = collections.Counter(); bad = []
    for l in open("train/answers.jsonl"):
        ref = json.loads(l); q = qs[ref["id"]]
        if q["business_id"] not in bizs: continue
        L = cache.setdefault(q["business_id"], Ledger(f"train/data/{q['business_id']}"))
        y, m, d = map(int, q["as_of_date"].split("-"))
        try:
            pred = solve(L, q["question"], date(y, m, d))
        except Exception as e:
            pred = {"type": "abstain", "err": repr(e)}
        if pred["type"] == "abstain": tot["abstain"] += 1; bad.append(("ABS", q, ref, pred)); continue
        ok = correct(pred, ref)
        tot["right" if ok else "wrong"] += 1
        if not ok: bad.append(("WRONG", q, ref, pred))
    n = sum(tot.values())
    print(dict(tot), "PA=%.3f" % ((tot["right"] - tot["wrong"]) / n), "n=", n)
    for tag, q, ref, pred in bad:
        if tag == "WRONG" or "--abs" in sys.argv[0:1]:
            print(tag, q["business_id"][-3:], q["question"][:100], "| ref", ref["type"], str(ref["answer"])[:50], "| pred", pred["type"], str(pred.get("answer"))[:50])
    print("--- abstains:", sum(1 for b in bad if b[0] == "ABS"))
    for tag, q, ref, pred in bad:
        if tag == "ABS": print("ABS", q["question"][:110], "|", ref["type"], pred.get("err",""))
