# -*- coding: utf-8 -*-
"""句子层统计（手册 4.4）：对 research/句子层-标点版/*.txt 计算
- 一句话长度分布（中位数、>30字比例）
- 逗号之间长度（一口气）
- 连接词每千字次数
- 提问句占比
- 对「你」说话次数每千字

用法：python3 sentence_stats.py
"""
import re
from pathlib import Path
from statistics import median

BASE = Path(__file__).resolve().parent.parent
DIR = BASE / "句子层-标点版"

CONN = ["因为", "所以", "但是", "但", "比如", "也就是说", "换句话说", "其实", "然后", "而且", "可是", "如果", "那么"]

def main():
    for p in sorted(DIR.glob("*.txt")):
        sents, clauses = [], []
        chars = 0
        you_n = 0
        q_n = 0
        text_all = []
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.startswith("#") or not ln.strip():
                continue
            m = re.match(r"\[[0-9:]+\]\s*(.*)", ln)
            if not m:
                continue
            text = m.group(1)
            text_all.append(text)
            chars += len(re.findall(r"[一-鿿A-Za-z0-9]", text))
        full = "".join(text_all)
        # 句子
        for s in re.split(r"[。！？]+", full):
            s = s.strip()
            if re.search(r"[一-鿿A-Za-z0-9]", s):
                sents.append(s)
        # 一口气（逗号间）
        for c in re.split(r"[，,、；;：:。！？]+", full):
            c = c.strip()
            if re.search(r"[一-鿿A-Za-z0-9]", c):
                clauses.append(c)
        s_lens = sorted(len(s) for s in sents)
        c_lens = sorted(len(c) for c in clauses)
        q_n = len(re.findall(r"[？?]", full))
        you_n = len(re.findall(r"你(?!们)", full))
        conn_n = sum(full.count(w) for w in CONN)
        over30 = sum(1 for l in s_lens if l > 30)
        print(f"== {p.stem}")
        if sents:
            print(f"  句数 {len(sents)}，句长中位 {median(s_lens):.0f} 字，>30字句 {over30}/{len(sents)} ({over30/len(sents):.0%})")
        if clauses:
            print(f"  一气口 {len(clauses)} 段，逗号间长度中位 {median(c_lens):.0f} 字，P90 {c_lens[int(len(c_lens)*0.9)]} 字")
        print(f"  提问句 {q_n}；连接词每千字 {conn_n/chars*1000:.1f}；「你」每千字 {you_n/chars*1000:.1f}")

if __name__ == "__main__":
    main()
