# -*- coding: utf-8 -*-
"""分层随机抽样：按方案第四节的层与题材分层，固定随机种子。

层定义与候选池来源（全部为公开免费内容）：
- A 完整讲书（20 分钟以上的樊登单独讲书）：YouTube 官方频道「樊登讀書」
  筛选规则：duration>=1200s，标题含「完整纯享版/合集版/樊登讀書/樊登读书」，
  排除对谈（标题含 ×/對談/对谈/采访/採訪/作者/ft.）、排除方法论系列与单集碎片（EP）。
- B 官方短视频（1–5 分钟）：B 站「帆书APP」官方账号，60s<=时长<=300s，按年份分层。
- C 演讲：B 站官方账号上传的完整演讲（标题含 演讲/直播 且 >=40 分钟）。
- D 被采访/对谈：别人提问为主。来源：YouTube 官方（鲁豫采访、对谈刘润/李东生）、
  B 站官方【樊登访谈】、第三方访谈节目（凉子访谈录、壹次访谈录、陈溥江）。
- E 第三方切片（只做对照）：B 站非官方账号上传的 1–15 分钟樊登内容切片；
  排除付费课程盗版整集（如「樊登精讲资治通鉴」——该课程为帆书付费产品）。

用法：python3 sample.py   （在 research/scripts/ 下运行）
输出：research/data/样本.csv、research/data/抽样日志.txt
"""
import csv
import json
import random
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # research/
DATA = BASE / "data"
SEED = 42

def plen(s):
    parts = [int(x) for x in s.split(":")]
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec

def iso(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else ""

def load(name):
    return json.load(open(DATA / name, encoding="utf-8"))

# ---------------- A 层候选池（人工核对过的单独讲书，id 定死） ----------------
# 频道同一本书有中英文两版标题，关键词匹配会漏，直接用视频 id。
# 亲子类完整讲书在公开渠道只找到 1 本（随他们去），亲子题材由 B 层短视频与
# C 层演讲覆盖——记为已知偏差，写入 METHODOLOGY。
yt = load("清单-YouTube官方.json")
BY_ID = {v["id"]: v for v in yt}

A_POOL = {  # id -> (书名, 题材)
    "dYK2cDUyX6M": ("人生只有一件事", "个人成长"),
    "tPtDubOGOxM": ("你的人生，他们六个说了算", "心理"),
    "CID8wIzyjjY": ("一如既往", "商业管理"),
    "RNrfQlGdS8k": ("反叛，改变世界", "商业管理"),
    "rsIi04z9HSE": ("随他们去", "亲子家庭"),
    "x17V-L5p3zI": ("普通人的24个致富常识", "商业管理"),
    "pQz4Skw6QlI": ("我可能错了", "个人成长"),
    "VBazKS4Tahg": ("活出心花怒放的人生", "心理"),
    "URuDgOqtSx0": ("袁隆平的世界", "历史人文"),
    "QWzjCdBBM2k": ("经纬华夏", "历史人文"),
    "_9VxKfrYsLE": ("人生的底气", "个人成长"),
    "HZl7p5GQiEE": ("癌症密码", "科普健康"),
}

def build_a_pool():
    pool = []
    for vid, (book, topic) in A_POOL.items():
        v = BY_ID[vid]
        pool.append({"id": vid, "title": v["title"], "dur": v["duration_sec"],
                     "date": v["date"], "book": book, "topic": topic})
    return pool

# ---------------- 补抽模式 ----------------
def replace_b(replace_ids, reason_by_id):
    """剔除指定 B 层样本（如情景短剧，非樊登本人说话），从剩余候选池
    按同一分层逻辑补抽等量新条目。同种子，排除已抽与已剔除。"""
    rng = random.Random(SEED)
    rows = list(csv.DictReader(open(DATA / "样本.csv", encoding="utf-8-sig")))
    bili = load("清单-帆书APP.json")
    drawn = {r["链接"].rstrip("/").split("/")[-1] for r in rows if r["层"] == "B"}
    b_pool = [v for v in bili
              if 60 <= plen(v["length"]) <= 300
              and v["bvid"] not in drawn
              and v["bvid"] not in replace_ids
              and not any(k in v["title"] for k in ["书友", "短剧", "剧情", "情景"])]
    by_year = {}
    for v in b_pool:
        by_year.setdefault(iso(v["created"])[:4], []).append(v)
    # 需要补的年份配额：按被剔除样本的年份分布
    need_by_year = {}
    for rid in replace_ids:
        row = next((r for r in rows if r["编号"] == rid), None)
        y = (row["发布日期"] or "")[:4] if row else ""
        need_by_year[y] = need_by_year.get(y, 0) + 1
    picks = []
    log = [f"补抽（种子 {SEED}）：剔除 {replace_ids}"]
    for rid in replace_ids:
        log.append(f"  剔除 {rid}: {reason_by_id.get(rid, '')}")
    for y, n in sorted(need_by_year.items()):
        cand = by_year.get(y, [])
        if not cand:  # 该年份无余量，从全部余量里抽
            cand = b_pool
        take = rng.sample(cand, min(n, len(cand)))
        picks += take
        log.append(f"  {y} 年补抽 {len(take)} 条: {[v['bvid'] for v in take]}")
    # 更新 样本.csv：删旧、按原编号位补新
    out_rows = []
    new_i = 0
    for r in rows:
        if r["编号"] in replace_ids:
            v = picks[new_i]
            new_i += 1
            out_rows.append({
                "编号": r["编号"], "来源平台": "B站官方",
                "链接": f"https://www.bilibili.com/video/{v['bvid']}",
                "标题": v["title"], "发布日期": iso(v["created"]), "时长": v["length"],
                "层": "B", "题材": "", "是否有稿": "是",
                "剪辑方": "本人账号", "是否有他人说话": "无", "是否商业合作": "待查",
                "备注": f"补抽替换（原样本为情景短剧，非樊登本人说话）",
            })
        else:
            out_rows.append(r)
    fieldnames = list(rows[0].keys())
    with open(DATA / "样本.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    with open(DATA / "抽样日志.txt", "a", encoding="utf-8") as fh:
        fh.write("\n\n" + time.strftime("%Y-%m-%d %H:%M") + " " + "\n".join(log) + "\n")
    print("\n".join(log))
    print("替换完成，需下载转写新编号:", [r["编号"] for r in out_rows
          if r.get("备注", "").startswith("补抽替换")])

# ---------------- 主流程 ----------------
def main():
    rng = random.Random(SEED)
    rows = []
    log = [f"抽样种子: {SEED}", f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]

    # A 层：全部 12 期都在池内（每类至多 2 期，池内各类均 <=2，全取）
    a_pool = build_a_pool()
    log.append("== A 层候选池（单独完整讲书，>=20 分钟，id 定版）==")
    for p in a_pool:
        log.append(f"  {p['book']}｜{p['topic']}｜{p['dur']//60}分钟｜{p['id']}｜{p['date']}")
    by_topic = {}
    for p in a_pool:
        by_topic.setdefault(p["topic"], []).append(p)
    a_ids = set()
    for topic, items in sorted(by_topic.items()):
        take = items if len(items) <= 2 else rng.sample(items, 2)
        for p in take:
            a_ids.add(p["id"])
            rows.append({
                "编号": "", "来源平台": "YouTube官方", "链接": f"https://www.youtube.com/watch?v={p['id']}",
                "标题": p["title"], "发布日期": p["date"], "时长": f"{p['dur']//60}:{p['dur']%60:02d}",
                "层": "A", "题材": p["topic"], "是否有稿": "是",
                "剪辑方": "本人账号", "是否有他人说话": "无", "是否商业合作": "否",
                "备注": f"书名《{p['book']}》",
            })
    log.append(f"A 层抽取: {len(a_ids)} 期，题材分布: " +
               str({t: sum(1 for r in rows if r['层']=='A' and r['题材']==t) for t in by_topic}))
    log.append("")

    # B 层：B 站官方 1–5 分钟，按年份分层随机，目标 25–30
    bili = load("清单-帆书APP.json")
    b_pool = [v for v in bili if 60 <= plen(v["length"]) <= 300]
    by_year = {}
    for v in b_pool:
        by_year.setdefault(iso(v["created"])[:4], []).append(v)
    log.append(f"== B 层候选池: {len(b_pool)} 条（1–5 分钟），年份分布 {sorted((y, len(vs)) for y, vs in by_year.items())} ==")
    target_b = 28
    years = sorted(by_year)
    picks_b = []
    # 按年份比例分配
    quota = {y: max(1, round(target_b * len(by_year[y]) / len(b_pool))) for y in years}
    while sum(quota.values()) > target_b:
        biggest = max(quota, key=lambda y: quota[y])
        if quota[biggest] > 1:
            quota[biggest] -= 1
        else:
            break
    for y in years:
        take_n = min(quota[y], len(by_year[y]))
        picks_b += rng.sample(by_year[y], take_n)
    for v in picks_b:
        rows.append({
            "编号": "", "来源平台": "B站官方", "链接": f"https://www.bilibili.com/video/{v['bvid']}",
            "标题": v["title"], "发布日期": iso(v["created"]), "时长": v["length"],
            "层": "B", "题材": "", "是否有稿": "是",
            "剪辑方": "本人账号", "是否有他人说话": "无", "是否商业合作": "待查",
            "备注": "",
        })
    log.append(f"B 层抽取: {len(picks_b)} 条，年份分布: " +
               str(sorted((y, sum(1 for v in picks_b if iso(v['created'])[:4]==y)) for y in set(iso(v['created'])[:4] for v in picks_b))))
    log.append("")

    # C 层：官方完整演讲 >=40 分钟，随机 5–6
    c_pool = [v for v in bili if plen(v["length"]) >= 2400 and
              any(k in v["title"] for k in ["演讲", "直播"])]
    log.append("== C 层候选池（官方完整演讲 >=40 分钟）==")
    for v in c_pool:
        log.append(f"  {v['length']}｜{iso(v['created'])}｜{v['title'][:50]}")
    picks_c = rng.sample(c_pool, min(6, len(c_pool)))
    for v in picks_c:
        others = "有" if any(k in v["title"] for k in ["周国平", "曹晟康", "张展辉", "任泉", "孙赛赛", "/"]) else "无"
        rows.append({
            "编号": "", "来源平台": "B站官方", "链接": f"https://www.bilibili.com/video/{v['bvid']}",
            "标题": v["title"], "发布日期": iso(v["created"]), "时长": v["length"],
            "层": "C", "题材": "", "是否有稿": "是",
            "剪辑方": "本人账号", "是否有他人说话": others, "是否商业合作": "待查",
            "备注": "多嘉宾场次，统计时只算樊登部分" if others == "有" else "",
        })
    log.append(f"C 层抽取: {len(picks_c)} 场")
    log.append("")

    # D 层：被采访/对谈，随机 5–8
    d_pool = []
    # 官方来源
    for v in bili:
        if "访谈" in v["title"] and plen(v["length"]) >= 600:
            d_pool.append({"src": "B站官方", "bvid": v["bvid"], "title": v["title"],
                           "date": iso(v["created"]), "length": v["length"], "author": v["author"]})
    for v in yt:
        t = v["title"]
        if any(k in t for k in ["採訪樊登", "采访樊登", "採訪樊登", "魯豫", "鲁豫", "對談李東生", "对谈李东生", "樊登×刘润", "樊登x刘润", "樊登×劉潤"]) and v["duration_sec"] >= 600:
            d_pool.append({"src": "YouTube官方", "bvid": v["id"], "title": t,
                           "date": v["date"], "length": v["length"], "author": "樊登讀書"})
    # 第三方访谈节目（节目方为访谈内容的第一方）
    cand = load("候选-D层E层.json")
    for v in cand:
        if v["author"] in ("凉子访谈录", "北京青年x壹次访谈录", "陈溥江") and v["duration"] >= 600:
            d_pool.append({"src": "B站第三方访谈节目", "bvid": v["bvid"], "title": v["title"],
                           "date": iso(v["pubdate"]), "length": f"{v['duration']//60}:{v['duration']%60:02d}", "author": v["author"]})
    # 去重（鲁豫采访有两个上传版本，同一场访谈同时长只留一条）；
    # 【樊登访谈】系列疑似同一档节目拆条，最多抽 1 条
    seen, dd = [], []
    for v in d_pool:
        key = "".join(ch for ch in v["title"] if ch not in "【】|｜！!？? ")[:20]
        if key in [d[0] for d in seen]:
            continue
        if "採訪樊登" in v["title"] or "采访樊登" in v["title"]:
            if any(("採訪樊登" in d[1] or "采访樊登" in d[1]) and d[2] == v["length"] for d in seen):
                log.append(f"  [D层剔除] 同场访谈重复上传: {v['title'][:40]}")
                continue
        if "樊登访谈" in v["title"] and any("樊登访谈" in d[1] for d in seen):
            log.append(f"  [D层剔除] 同系列拆条: {v['title'][:40]}")
            continue
        seen.append((key, v["title"], v["length"]))
        dd.append(v)
    log.append("== D 层候选池（被采访/对谈 >=10 分钟）==")
    for v in dd:
        log.append(f"  {v['length']}｜{v['src']}｜{v['title'][:45]}")
    picks_d = rng.sample(dd, min(6, len(dd)))
    for v in picks_d:
        link = (f"https://www.bilibili.com/video/{v['bvid']}" if "B站" in v["src"]
                else f"https://www.youtube.com/watch?v={v['bvid']}")
        rows.append({
            "编号": "", "来源平台": v["src"], "链接": link,
            "标题": v["title"], "发布日期": v["date"], "时长": v["length"],
            "层": "D", "题材": "", "是否有稿": "否",
            "剪辑方": "本人账号" if "官方" in v["src"] else "节目方",
            "是否有他人说话": "有", "是否商业合作": "待查",
            "备注": f"访谈方: {v['author']}",
        })
    log.append(f"D 层抽取: {len(picks_d)} 场")
    log.append("")

    # E 层：第三方切片 1–15 分钟，排除付费课程盗版与整集搬运，随机 12
    OFFICIAL = {"帆书APP", "樊登和他的朋友们", "一书一课", "帆书APP-原樊登读书",
                "东南卫视", "刘润商学", "凉子访谈录"}
    e_pool = [v for v in cand
              if v["author"] not in OFFICIAL
              and 60 <= v["duration"] <= 900
              and "资治通鉴" not in v["title"]]  # 付费课程盗版，排除
    log.append("== E 层候选池（第三方切片 1–15 分钟，已排除付费课程盗版）==")
    for v in e_pool:
        log.append(f"  {v['duration']//60}:{v['duration']%60:02d}｜{v['author']}｜{v['title'][:45]}")
    picks_e = rng.sample(e_pool, min(12, len(e_pool)))
    for v in picks_e:
        rows.append({
            "编号": "", "来源平台": "B站第三方", "链接": f"https://www.bilibili.com/video/{v['bvid']}",
            "标题": v["title"], "发布日期": iso(v["pubdate"]), "时长": f"{v['duration']//60}:{v['duration']%60:02d}",
            "层": "E", "题材": "", "是否有稿": "",
            "剪辑方": "第三方", "是否有他人说话": "", "是否商业合作": "",
            "备注": f"上传者: {v['author']}",
        })
    log.append(f"E 层抽取: {len(picks_e)} 条（只做对照）")
    log.append("")

    # 编号
    counters = {}
    for r in rows:
        lay = r["层"]
        counters[lay] = counters.get(lay, 0) + 1
        r["编号"] = f"{lay}{counters[lay]:02d}"

    fieldnames = ["编号", "来源平台", "链接", "标题", "发布日期", "时长", "层", "题材",
                  "是否有稿", "剪辑方", "是否有他人说话", "是否商业合作", "备注"]
    with open(DATA / "样本.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    log.append(f"合计样本: {len(rows)} 条 -> {DATA / '样本.csv'}")
    log.append("层分布: " + str(counters))
    with open(DATA / "抽样日志.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(log))
    print("\n".join(log[-6:]))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--replace-b":
        ids = sys.argv[2].split(",")
        replace_b(ids, {})
    else:
        main()
