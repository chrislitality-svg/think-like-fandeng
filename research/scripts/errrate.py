# -*- coding: utf-8 -*-
"""错字率估计（手册第二节）：用 FunASR Paraformer 再转一遍抽样文件，
与 faster-whisper 结果对齐比较，不一致字符占比作为错字率上限估计。

只抽 8 个文件（每层至少 1 个，短文件为主），控制计算量。
输出：research/转写质量报告.md 的数据部分 + corpus/{编号}.paraformer.txt
"""
import csv
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("MODELSCOPE_CACHE", str(Path(__file__).parent / "ms_cache"))

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent
AUDIO = BASE / "audio"
CORPUS = REPO / "corpus"

# 抽样：每层代表 + 短文件优先（B 层 3、A/D/E 层各 1-2 个短中取短）
SAMPLE_IDS = ["B01", "B03", "B07", "B18", "E02", "E05"]

def norm(t):
    return "".join(ch for ch in t if ch.isalnum())

def load_whisper_text(sid):
    p = CORPUS / f"{sid}.txt"
    if not p.exists():
        return None
    lines = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#"):
            continue
        if "] " in ln:
            lines.append(ln.split("] ", 1)[1])
    return "".join(lines)

def main():
    from funasr import AutoModel
    model = AutoModel(model="paraformer-zh", disable_update=True)
    results = []
    for sid in SAMPLE_IDS:
        audio = AUDIO / f"{sid}.m4a"
        wt = load_whisper_text(sid)
        if not audio.exists() or wt is None:
            print(f"[{sid}] skip (missing)")
            continue
        t0 = time.time()
        res = model.generate(input=str(audio), batch_size_s=300)
        pt = norm("".join(r.get("text", "") for r in res))
        wt_n = norm(wt)
        (CORPUS / f"{sid}.paraformer.txt").write_text(pt, encoding="utf-8")
        # 简单对齐比较：字符级编辑距离（Levenshtein）
        import difflib
        sm = difflib.SequenceMatcher(a=wt_n, b=pt, autojunk=False)
        eq = sum(b.size for b in sm.get_matching_blocks())
        diff = 1 - eq / max(len(wt_n), len(pt), 1)
        results.append((sid, len(wt_n), len(pt), round(diff * 100, 2), round(time.time() - t0)))
        print(f"[{sid}] whisper {len(wt_n)} chars / paraformer {len(pt)} chars / 不一致 {diff*100:.2f}% / {time.time()-t0:.0f}s", flush=True)
    out = BASE.parent / "数据-错字率对比.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["编号", "whisper字数", "paraformer字数", "不一致占比%", "耗时s"])
        w.writerows(results)
    print("saved", out)

if __name__ == "__main__":
    main()
