# -*- coding: utf-8 -*-
"""列出已可编码的样本（转写已就绪），输出 JSON。
用法：python3 list_ready.py
"""
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(BASE / "data" / "样本.csv", encoding="utf-8-sig")))
out = []
for r in rows:
    sid = r["编号"]
    t = BASE.parent / "corpus" / f"{sid}.txt"
    if t.exists():
        out.append({
            "sid": sid, "layer": r["层"], "title": r["标题"],
            "transcript": str(t),
        })
print(json.dumps(out, ensure_ascii=False))
