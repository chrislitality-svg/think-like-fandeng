# -*- coding: utf-8 -*-
"""统计主脚本：按层算覆盖率、时间占比、假设检验 H1–H9。

输入：编码-整体.csv、编码-段落.csv、编码-应答单元.csv、corpus/*.txt
输出：stdout（写入 统计结果.md 由人工/agent 整理）
所有数字可由本脚本一键复算。
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parent

def load(name):
    return list(csv.DictReader(open(BASE / name, encoding="utf-8-sig")))

def t2s(t):
    """[01:23] 或 01:23 -> 秒"""
    if not t:
        return None
    t = t.strip("[] ")
    try:
        parts = [int(x) for x in t.split(":")]
    except ValueError:
        return None
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec

def clean_text(sid):
    """去元信息行、时间戳、空白后的口播全文（他人说话无法在此步剔除）。"""
    p = REPO / "corpus" / f"{sid}.txt"
    if not p.exists():
        return ""
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#"):
            continue
        ln = re.sub(r"\[\d{1,3}:\d{2}\]", "", ln)
        out.append(ln.strip())
    return "".join(out)

def first_source(v):
    return (v or "").split(";")[0].strip()

STORY_SOURCES = {"书里的例子", "他自己的经历", "他身边人的事", "听众或用户的案例", "比喻", "笑话"}

def invalid_sids():
    """编码确认非本人说话的无效样本（样本.csv 备注含「无效样本」）。"""
    rows = list(csv.DictReader(open(BASE / "data" / "样本.csv", encoding="utf-8-sig")))
    return {r["编号"] for r in rows if "无效样本" in r.get("备注", "")}

def main():
    inv = invalid_sids()
    whole = [r for r in load("编码-整体.csv") if r["sid"] not in inv]
    segs = [r for r in load("编码-段落.csv") if r["sid"] not in inv]
    qas = [r for r in load("编码-应答单元.csv") if r["sid"] not in inv]
    print(f"（已排除无效样本 {len(inv)} 个：{sorted(inv)}）")

    print("=" * 60)
    print("一、各层样本量与单元量")
    for lay, label in [("A", "完整讲书"), ("B", "官方短视频"), ("C", "演讲"), ("D", "被采访"), ("E", "第三方切片")]:
        w = [r for r in whole if r["层"] == lay]
        s = [r for r in segs if r["sid"].startswith(lay)]
        q = [r for r in qas if r["sid"].startswith(lay)]
        print(f"  {lay} {label}: {len(w)} 期/条, 段落单元 {len(s)}, 应答单元 {len(q)}")

    # H1 讲书开头先抛生活问题
    a = [r for r in whole if r["层"] == "A"]
    h1 = Counter(r["开头前30秒"] for r in a)
    n_a = len(a)
    throw_q = sum(v for k, v in h1.items() if "抛问题" in k)
    print("\n二、假设检验")
    print(f"  H1 开头抛问题（A层）: {throw_q}/{n_a} ({throw_q/max(n_a,1):.0%})  分布: {dict(h1)}")

    # H2 观点段后跟故事/案例
    seg_by_sid = defaultdict(list)
    for r in segs:
        seg_by_sid[r["sid"]].append(r)
    for v in seg_by_sid.values():
        v.sort(key=lambda r: int(re.sub(r"\D", "", r["段号"]) or 0))
    n_op, n_op_story = 0, 0
    for sid, v in seg_by_sid.items():
        for i, r in enumerate(v):
            src = r.get("内容来源", "")
            if "书里的观点" in src:
                n_op += 1
                nxt = v[i + 1] if i + 1 < len(v) else None
                hit = bool(STORY_SOURCES & set(s.strip() for s in src.split(";"))) or \
                      (nxt is not None and bool(STORY_SOURCES & set(s.strip() for s in nxt.get("内容来源", "").split(";")))) or \
                      (nxt is not None and nxt.get("和上一段的关系", "") == "给上一段举例")
                if hit:
                    n_op_story += 1
    print(f"  H2 观点段内或下一段有故事/案例: {n_op_story}/{n_op} ({n_op_story/max(n_op,1):.0%})")

    # H3 自己经历/身边人 时间占比（A/C 层）
    for lay in ("A", "C"):
        tot, mine = 0, 0
        for r in segs:
            if not r["sid"].startswith(lay):
                continue
            d = (t2s(r.get("止时间")) or 0) - (t2s(r.get("起时间")) or 0)
            if d <= 0:
                continue
            tot += d
            if first_source(r.get("内容来源")) in ("他自己的经历", "他身边人的事"):
                mine += d
        print(f"  H3 自己/身边人时间占比（{lay}层）: {mine}s/{tot}s ({mine/max(tot,1):.0%})")

    # H4 书的顺序重排
    h4 = Counter(r["书的顺序对比"] for r in a)
    rep = sum(v for k, v in h4.items() if "重新排列" in k)
    print(f"  H4 重新排列（A层）: {rep}/{n_a} ({rep/max(n_a,1):.0%})  分布: {dict(h4)}")

    # H5 抽象落场景
    for lay in ("A", "C", "B"):
        ss = [r for r in segs if r["sid"].startswith(lay)]
        n = [r for r in ss if r.get("落场景") == "有"]
        cat = Counter(r.get("场景类别", "") for r in n)
        print(f"  H5 落到具体场景（{lay}层）: {len(n)}/{len(ss)} ({len(n)/max(len(ss),1):.0%})  场景: {dict(cat)}")

    # H6 对听众说话
    for lay in ("A", "C", "B"):
        ss = [r for r in segs if r["sid"].startswith(lay)]
        n = [r for r in ss if r.get("对听众说话") == "有"]
        forms = Counter(r.get("说话形式", "") for r in n)
        print(f"  H6 直接对听众说话（{lay}层）: {len(n)}/{len(ss)} ({len(n)/max(len(ss),1):.0%})  形式: {dict(forms)}")

    # H7 收尾
    for lay in ("A", "C", "B"):
        w = [r for r in whole if r["层"] == lay]
        c = Counter(r["结尾在做什么"] for r in w)
        act = sum(v for k, v in c.items() if "行动" in k)
        print(f"  H7 结尾行动建议（{lay}层）: {act}/{len(w)} ({act/max(len(w),1):.0%})  分布: {dict(c)}")
    qc = Counter(r.get("收尾", "") for r in qas if r["sid"].startswith("D"))
    print(f"     D层应答收尾分布: {dict(qc)}")

    # H8 被追问先讲故事
    d_q = [r for r in qas if r["sid"].startswith("D")]
    for form in ("是非问", "开放问", "挑战质疑", "求建议"):
        sub = [r for r in d_q if r.get("问题形式", "") == form]
        if not sub:
            continue
        story = sum(1 for r in sub if "讲故事" in r.get("第一句在做什么", ""))
        ans = sum(1 for r in sub if "给答案" in r.get("第一句在做什么", ""))
        print(f"  H8 第一句讲故事/给答案（D层·{form}）: 讲故事 {story}/{len(sub)}, 给答案 {ans}/{len(sub)}")

    # H9 观点段后接笑话
    n9 = 0
    hit9 = 0
    for sid, v in seg_by_sid.items():
        for i, r in enumerate(v):
            if "书里的观点" in r.get("内容来源", ""):
                n9 += 1
                nxt = v[i + 1] if i + 1 < len(v) else None
                if nxt is not None and ("笑话" in nxt.get("内容来源", "")):
                    hit9 += 1
    print(f"  H9 观点段下一段是笑话: {hit9}/{n9}")

    # 口头习惯词密度
    print("\n三、口头习惯词（每万字，分母为去时间戳去元信息字数）")
    WORDS = ["你会发现", "我跟你讲", "这本书告诉我们", "其实", "对吧", "好吗", "你知道吗"]
    for lay in ("A", "B", "C", "D"):
        sids = sorted({r["sid"] for r in whole if r["层"] == lay})
        chars = 0
        cnt = Counter()
        per_sid = {}
        for sid in sids:
            t = clean_text(sid)
            chars += len(t)
            c_sid = Counter()
            for w_ in WORDS:
                c = t.count(w_)
                cnt[w_] += c
                c_sid[w_] = c
            per_sid[sid] = sum(c_sid.values()) / max(len(t), 1) * 10000
        if chars == 0:
            continue
        dens = {w_: round(v / chars * 10000, 1) for w_, v in cnt.items()}
        rng = f"{min(per_sid.values()):.1f}–{max(per_sid.values()):.1f}" if per_sid else "—"
        print(f"  {lay}层（{chars}字）: {dens}  每期每万字范围: {rng}")

    # E层对照：预告
    e = [r for r in whole if r["层"] == "E"]
    pre = Counter(r.get("是否预告", "") for r in e)
    print(f"\n四、E层对照: 片头预告 {dict(pre)}")

if __name__ == "__main__":
    main()
