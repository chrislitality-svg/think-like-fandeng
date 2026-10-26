# -*- coding: utf-8 -*-
"""第二人复核抽样：每层抽 20% 单元，生成复核任务表。

用法：python3 review_sample.py
输入：research/编码-段落.csv、编码-应答单元.csv、编码-整体.csv
输出：research/复核任务.csv（只含单元定位信息，不含主编码结果，
      复核 agent 只读编码规则与转写，独立编码后回填）
"""
import csv
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEED = 42

def main():
    rng = random.Random(SEED)
    out = []
    # 整体表：每层抽 20% 的期/条
    whole = list(csv.DictReader(open(BASE / "编码-整体.csv", encoding="utf-8-sig")))
    by_layer = {}
    for r in whole:
        by_layer.setdefault(r["层"], []).append(r)
    for layer, rows in sorted(by_layer.items()):
        take = rng.sample(rows, max(1, round(len(rows) * 0.2)))
        for r in take:
            out.append({"类型": "整体", "sid": r["sid"], "层": layer,
                        "定位": "整期/整条", "任务": "填整体表全部字段"})
    # 段落表与应答表：每层抽 20% 单元
    for name, f in [("段落", "编码-段落.csv"), ("应答", "编码-应答单元.csv")]:
        try:
            rows = list(csv.DictReader(open(BASE / f, encoding="utf-8-sig")))
        except FileNotFoundError:
            continue
        by_layer = {}
        for r in rows:
            by_layer.setdefault(r["sid"][0], []).append(r)
        for layer, lrows in sorted(by_layer.items()):
            take = rng.sample(lrows, max(1, round(len(lrows) * 0.2)))
            for r in take:
                unit = r.get("段号") or r.get("单元号")
                out.append({"类型": name, "sid": r["sid"], "层": layer,
                            "定位": f"{unit} {r.get('起时间','')}-{r.get('止时间','')}",
                            "任务": f"独立编码该{name}单元全部字段"})
    with open(BASE / "复核任务.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["类型", "sid", "层", "定位", "任务"])
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print("复核任务:", len(out), "条", dict(Counter((r["层"], r["类型"]) for r in out)))

if __name__ == "__main__":
    main()
