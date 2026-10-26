# -*- coding: utf-8 -*-
"""用樊登语料实测 ai_flavor_check.py 的基准常数。

从 corpus/*.txt（去元信息/时间戳/空白）统计：
- 书面套话/宏大空词 各词每万字频次
- 人称、设问、数字、逻辑词每千字频次
- 分句（一口气）长度分布
结果打印为 Python 字典片段，供更新 tools/ai_flavor_check.py 的 BASE / HUMAN_BASE。

用法：python3 baseline.py [层过滤，如 A 只用完整讲书]
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

WORDS = ["首先", "其次", "此外", "与此同时", "综上所述", "总而言之", "总之", "值得注意的是",
         "需要指出的是", "不难看出", "由此可见", "换言之", "毋庸置疑", "显而易见", "总的来说", "众所周知",
         "赋能", "助力", "抓手", "全方位", "多维度", "深度融合", "降本增效", "数字化转型",
         "时代浪潮", "日新月异", "前所未有", "一蹴而就", "保驾护航", "至关重要", "不可或缺",
         "显著", "有效地", "切实", "在当今", "随着"]

def clean(sid):
    p = REPO / "corpus" / f"{sid}.txt"
    if not p.exists():
        return ""
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#"):
            continue
        out.append(re.sub(r"\[\d{1,3}:\d{2}\]", "", ln).strip())
    return "".join(out)

def main():
    lay = sys.argv[1] if len(sys.argv) > 1 else ""
    sids = [p.stem for p in (REPO / "corpus").glob("*.txt")
            if not p.name.endswith(".words.json") and "paraformer" not in p.name
            and (not lay or p.stem.startswith(lay))]
    text = "".join(clean(s) for s in sids)
    n = len(re.findall(r"[一-鿿A-Za-z0-9]", text))
    print(f"# 样本 {len(sids)} 个（层 {lay or '全部'}），口播字数 {n}")
    print("BASE = {")
    for w in WORDS:
        c = text.count(w)
        print(f'    "{w}": {round(c / n * 10000, 2)},')
    print("}")
    person = len(re.findall(r"你|我|我们", text))
    quest = len(re.findall(r"吗|呢", text))
    nums = len(re.findall(r"\d+(?:\.\d+)?%?|[一二两三四五六七八九十百千万亿]+(?=[个次年天岁倍字小时分钟秒万亿元块条件位家款种步样遍])", text))
    logic = len(re.findall(r"因为|所以|但|如果|那么|的话|也就是说|换句话说|之所以|对于|所谓|只有|它", text))
    print("HUMAN_BASE = {")
    print(f'    "人称（你/我/我们）": {round(person / n * 1000, 1)},')
    print(f'    "设问（吗/呢）": {round(quest / n * 1000, 1)},')
    print(f'    "数字": {round(nums / n * 1000, 1)},')
    print(f'    "逻辑词（因为/所以/但/如果/那么/它…）": {round(logic / n * 1000, 1)},')
    print("}")
    # 分句长度（转写无标点，用顿住的空行/常见口头断句近似不可行；改报字符长度/行）
    lines = [re.sub(r"\[\d{1,3}:\d{2}\]", "", ln).strip()
             for s in sids for ln in (REPO / "corpus" / f"{s}.txt").read_text(encoding="utf-8").splitlines()
             if not ln.startswith("#") and ln.strip()]
    lens = sorted(len(re.findall(r"[一-鿿A-Za-z0-9]", l)) for l in lines)
    if lens:
        med = lens[len(lens) // 2]
        p90 = lens[int(len(lens) * 0.9)]
        print(f"# 转写行（近似气口）中位 {med} 字，P90 {p90} 字（供分句阈值参考）")

if __name__ == "__main__":
    main()
