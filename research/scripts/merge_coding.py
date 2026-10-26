# -*- coding: utf-8 -*-
"""合并各编码员的切片 CSV 为三张总表，并校验完整性。

用法：python3 merge_coding.py
输入：research/编码输出/{sid}-整体.csv、{sid}-段落.csv、{sid}-应答.csv
输出：research/编码-整体.csv、编码-段落.csv、编码-应答单元.csv
退出码：0 = 全部样本都有编码；1 = 有缺失（stdout 列出缺失项）
"""
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # research/
OUT_DIR = BASE / "编码输出"
DATA = BASE / "data"

EXPECTED_SID = {}
for r in csv.DictReader(open(DATA / "样本.csv", encoding="utf-8-sig")):
    EXPECTED_SID[r["编号"]] = r["层"]

def read_slice(p):
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

def main():
    import sys
    partial = "--partial" in sys.argv
    missing, bad = [], []
    tables = {"整体": [], "段落": [], "应答": []}
    for sid, layer in EXPECTED_SID.items():
        want_unit = "应答" if layer in ("D", "E") else "段落"
        p_whole = OUT_DIR / f"{sid}-整体.csv"
        p_unit = OUT_DIR / f"{sid}-{want_unit}.csv"
        if not p_whole.exists():
            missing.append(f"{sid}-整体.csv")
        else:
            rows = read_slice(p_whole)
            if not rows:
                bad.append(f"{sid}-整体.csv 空文件")
            tables["整体"] += rows
        if not p_unit.exists():
            missing.append(f"{sid}-{want_unit}.csv")
        else:
            rows = read_slice(p_unit)
            if not rows:
                bad.append(f"{sid}-{want_unit}.csv 空文件")
            tables[want_unit] += rows
        # E 层若同时给了段落表也并入
        p_extra = OUT_DIR / f"{sid}-段落.csv"
        if layer == "E" and p_extra.exists():
            tables["段落"] += read_slice(p_extra)

    names = {"整体": "编码-整体.csv", "段落": "编码-段落.csv", "应答": "编码-应答单元.csv"}
    for key, rows in tables.items():
        if not rows:
            continue
        cols = list(rows[0].keys())
        with open(BASE / names[key], "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print(f"{names[key]}: {len(rows)} 行")

    if missing or bad:
        print("缺失:", missing)
        print("问题:", bad)
        if partial and not bad:
            miss_sids = len({m.split("-")[0] for m in missing})
            print(f"分批模式：{len(EXPECTED_SID) - miss_sids} 个样本已就绪并合并")
            sys.exit(0)
        sys.exit(1)
    print(f"完整：{len(EXPECTED_SID)} 个样本全部有编码")

if __name__ == "__main__":
    main()
