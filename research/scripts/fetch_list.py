# -*- coding: utf-8 -*-
"""拉取 B 站用户视频列表（wbi 签名版），输出 JSON。

用法：python3 fetch_list.py <mid> <输出文件名>
零第三方依赖，只用标准库。
"""
import json
import sys
import time
import urllib.request
from hashlib import md5
from urllib.parse import urlencode

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Chrome/120.0)",
      "Referer": "https://space.bilibili.com/"}

MIXIN_KEY_ENC_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
                     33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
                     61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
                     36, 20, 34, 44, 52]


_OPENER = None


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    if _OPENER is not None:
        return _OPENER.open(req, timeout=20)
    return urllib.request.urlopen(req, timeout=20)


def get_wbi_keys():
    url = "https://api.bilibili.com/x/web-interface/nav"
    data = json.load(_get(url))["data"]["wbi_img"]
    img = data["img_url"].rsplit("/", 1)[1].split(".")[0]
    sub = data["sub_url"].rsplit("/", 1)[1].split(".")[0]
    raw = img + sub
    return "".join(raw[i] for i in MIXIN_KEY_ENC_TAB)[:32]


def wbi_sign(params, key):
    params = dict(sorted(params.items()))
    params["wts"] = int(time.time())
    qs = urlencode(params)
    params["w_rid"] = md5((qs + key).encode()).hexdigest()
    return params


def fetch_page(page, mid, key):
    base = "https://api.bilibili.com/x/space/wbi/arc/search"
    p = {"mid": mid, "pn": page, "ps": 30, "tid": 0, "order": "pubdate", "platform": "web"}
    url = base + "?" + urlencode(wbi_sign(p, key))
    return json.load(_get(url))


def make_opener():
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    # finger/spi 拿 buvid3/buvid4，再访问主页补齐其余 cookie
    try:
        req = urllib.request.Request("https://api.bilibili.com/x/frontend/finger/spi", headers=UA)
        d = json.load(opener.open(req, timeout=20))["data"]
        for name, val in (("buvid3", d["b_3"]), ("buvid4", d["b_4"])):
            ck = http.cookiejar.Cookie(0, name, val, None, False, ".bilibili.com", True,
                                       False, "/", False, False, None, False, None, None, {})
            cj.set_cookie(ck)
    except Exception as e:
        print(f"finger/spi failed: {e}")
    req = urllib.request.Request("https://www.bilibili.com", headers=UA)
    try:
        opener.open(req, timeout=20).read(1024)
    except Exception:
        pass
    return opener


def main():
    mid = sys.argv[1]
    out = sys.argv[2]
    opener = make_opener()
    global _OPENER
    _OPENER = opener
    key = get_wbi_keys()
    all_v = []
    page = 1
    fail_streak = 0
    while True:
        try:
            d = fetch_page(page, mid, key)
        except Exception as e:
            print(f"page {page} error: {e}, retry once after 5s", flush=True)
            time.sleep(5)
            key = get_wbi_keys()
            d = fetch_page(page, mid, key)
        if d.get("code") != 0:
            if d.get("code") == -352 and fail_streak < 3:
                fail_streak += 1
                print(f"page {page}: -352, wait {5*fail_streak}s and refresh keys", flush=True)
                time.sleep(5 * fail_streak)
                opener2 = make_opener()
                _OPENER = opener2
                key = get_wbi_keys()
                continue
            print("API error:", d.get("code"), d.get("message"))
            break
        vlist = d["data"]["list"]["vlist"]
        if not vlist:
            break
        all_v.extend(vlist)
        fail_streak = 0
        pages = d["data"]["page"]["count"] // d["data"]["page"]["ps"] + 1
        print(f"page {page}/{pages}: {len(vlist)} videos (total {len(all_v)})", flush=True)
        if page >= pages:
            break
        page += 1
        time.sleep(2)
    keep = []
    for v in all_v:
        keep.append({
            "bvid": v["bvid"],
            "title": v["title"],
            "description": v.get("description", ""),
            "created": v["created"],
            "created_iso": time.strftime("%Y-%m-%d", time.localtime(v["created"])),
            "length": v["length"],
            "play": v.get("play", 0),
            "mid": mid,
            "author": v.get("author", ""),
        })
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(keep, fh, ensure_ascii=False, indent=1)
    print(f"saved {len(keep)} videos -> {out}")


if __name__ == "__main__":
    main()
