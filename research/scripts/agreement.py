# -*- coding: utf-8 -*-
"""第二人复核一致率：逐列算一致率，分类列算 Cohen's kappa。

输入：research/复核任务.csv（抽样定位）、research/复核编码.csv（复核员回填，
      列与主编码表相同，另加 类型/sid/单元 列）、主编码三表。
输出：research/复核报告.md 的数据段（stdout）。
"""
import csv
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def kappa(a, b):
    """a, b: 等长标签列表（单标签化后）。返回 Cohen's kappa 或 None（无方差时）。"""
    n = len(a)
    if n == 0:
        return None
    cats = sorted(set(a) | set(b))
    idx = {c: i for i, c in enumerate(cats)}
    m = [[0] * len(cats) for _ in cats]
    for x, y in zip(a, b):
        m[idx[x]][idx[y]] += 1
    po = sum(m[i][i] for i in range(len(cats))) / n
    pe = sum((sum(m[i]) / n) * (sum(m[j][i] for j in range(len(cats))) / n)
             for i in range(len(cats)))
    if pe == 1:
        return None  # 单一类别，无方差
    return (po - pe) / (1 - pe)

def main():
    review = list(csv.DictReader(open(BASE / "复核编码.csv", encoding="utf-8-sig")))
    # 主编码表
    main_rows = {}
    for f, key in [("编码-段落.csv", "段落"), ("编码-应答单元.csv", "应答"), ("编码-整体.csv", "整体")]:
        try:
            for r in csv.DictReader(open(BASE / f, encoding="utf-8-sig")):
                unit = r.get("段号") or r.get("单元号") or "整体"
                main_rows[(r["sid"], key, unit)] = r
        except FileNotFoundError:
            pass
    # 逐列对比
    report = []
    by_col = {}
    for rr in review:
        typ = rr["类型"]
        unit = rr.get("单元") or rr.get("段号") or rr.get("单元号") or "整体"
        mrow = main_rows.get((rr["sid"], typ, unit))
        if not mrow:
            continue
        for col, v in rr.items():
            if col in ("类型", "sid", "单元", "段号", "单元号") or col not in mrow:
                continue
            by_col.setdefault((typ, col), {"n": 0, "same": 0, "a": [], "b": []})
            d = by_col[(typ, col)]
            mv = (mrow[col] or "").strip()
            rv = (v or "").strip()
            if not mv or not rv or mv in ("不确定",) or rv in ("不确定",):
                continue
            d["n"] += 1
            # 单标签化：取第一项（多选字段按主项比）
            mk = mv.split(";")[0].split("，")[0]
            rk = rv.split(";")[0].split("，")[0]
            d["a"].append(mk)
            d["b"].append(rk)
            if mk == rk:
                d["same"] += 1
    print("| 表 | 列 | n | 一致率 | kappa |")
    print("|---|---|---|---|---|")
    low = []
    for (typ, col), d in sorted(by_col.items()):
        if d["n"] == 0:
            continue
        pct = d["same"] / d["n"]
        k = kappa(d["a"], d["b"])
        ks = f"{k:.2f}" if k is not None else "—"
        print(f"| {typ} | {col} | {d['n']} | {pct:.0%} | {ks} |")
        if k is not None and k < 0.6 and d["n"] >= 5:
            low.append(f"{typ}.{col} (kappa={k:.2f})")
    if low:
        print("\nkappa<0.6 的列：", "、".join(low))
        print("→ 这些列不能用来下结论，需改规则定义后两人重编。")

if __name__ == "__main__":
    main()
