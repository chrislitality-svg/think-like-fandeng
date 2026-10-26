# -*- coding: utf-8 -*-
"""按 样本.csv 下载公开音频：yt-dlp -f bestaudio -x --audio-format m4a。
音频只存本地 research/scripts/audio/，不进仓库。
"""
import csv
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent  # research/scripts/
AUDIO = BASE / "audio"
AUDIO.mkdir(exist_ok=True)
YTDLP = str(BASE.parent.parent / ".venv/bin/yt-dlp")

def main():
    rows = list(csv.DictReader(open(BASE.parent / "data" / "样本.csv", encoding="utf-8-sig")))
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    ok, fail = 0, []
    for r in rows:
        sid = r["编号"]
        if only and sid not in only:
            continue
        out = AUDIO / f"{sid}.m4a"
        if out.exists() and out.stat().st_size > 10000:
            ok += 1
            continue
        url = r["链接"]
        print(f"[{sid}] downloading {url}", flush=True)
        t0 = time.time()
        p = subprocess.run([
            YTDLP, "-f", "bestaudio/best", "-x", "--audio-format", "m4a",
            "--no-warnings", "--retries", "3", "--socket-timeout", "30",
            "-o", str(AUDIO / f"{sid}.%(ext)s"), url,
        ], capture_output=True, text=True)
        if p.returncode == 0 and out.exists():
            ok += 1
            print(f"[{sid}] ok {out.stat().st_size//1024}KB {time.time()-t0:.0f}s", flush=True)
        else:
            fail.append(sid)
            print(f"[{sid}] FAIL: {p.stderr[-200:]}", flush=True)
        time.sleep(1)
    print(f"\ndone. ok={ok} fail={fail}")
    if fail:
        sys.exit(1)

if __name__ == "__main__":
    main()
