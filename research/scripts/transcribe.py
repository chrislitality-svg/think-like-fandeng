# -*- coding: utf-8 -*-
"""批量转写：faster-whisper large-v3（手册第二节参数）。

- language="zh", vad_filter=True, beam_size=5, word_timestamps=True
- 输出 corpus/{编号}.txt（每行 [分:秒] 文本，文件头含来源与参数）
- 输出 corpus/{编号}.words.json（逐词时间）
- 模型走 hf-mirror；音频按短→长排队；已存在则跳过（可续跑）
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from faster_whisper import WhisperModel

BASE = Path(__file__).resolve().parent          # research/scripts/
REPO = BASE.parent.parent                        # 仓库根
AUDIO = BASE / "audio"
CORPUS = REPO / "corpus"
CORPUS.mkdir(exist_ok=True)

import csv
META = {r["编号"]: r for r in csv.DictReader(open(BASE.parent / "data" / "样本.csv", encoding="utf-8-sig"))}

def fmt_ts(sec):
    m, s = divmod(int(sec), 60)
    return f"[{m:02d}:{s:02d}]"

def audio_seconds(path):
    p = os.path.basename(str(path))
    sid = p.split(".")[0]
    t = META.get(sid, {}).get("时长", "")
    try:
        parts = [int(x) for x in t.split(":")]
        sec = 0
        for x in parts:
            sec = sec * 60 + x
        return sec
    except Exception:
        return 99999

def main():
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    files = sorted(AUDIO.glob("*.m4a"), key=audio_seconds)
    if "--reverse" in sys.argv:
        sys.argv.remove("--reverse")
        only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
        files = files[::-1]
    if only:
        files = [f for f in files if f.stem in only]
    model = WhisperModel("large-v3", device="cpu", compute_type="int8",
                         cpu_threads=6, num_workers=1)
    print(f"model ready, {len(files)} files", flush=True)
    for f in files:
        sid = f.stem
        txt_path = CORPUS / f"{sid}.txt"
        words_path = CORPUS / f"{sid}.words.json"
        if txt_path.exists() and words_path.exists():
            print(f"skip {sid}", flush=True)
            continue
        t0 = time.time()
        segments, info = model.transcribe(
            str(f), language="zh", vad_filter=True, beam_size=5,
            word_timestamps=True, condition_on_previous_text=False,
        )
        lines, words = [], []
        for s in segments:
            text = (s.text or "").strip()
            if not text:
                continue
            lines.append(f"{fmt_ts(s.start)} {text}")
            for w in (s.words or []):
                words.append({"start": round(w.start, 2), "end": round(w.end, 2),
                              "word": w.word})
        meta = META.get(sid, {})
        header = [
            f"# {sid} {meta.get('标题', '')}",
            f"# 来源: {meta.get('来源平台', '')} {meta.get('链接', '')}",
            f"# 层: {meta.get('层', '')}  发布: {meta.get('发布日期', '')}  时长: {meta.get('时长', '')}",
            "# 转写: faster-whisper large-v3 int8 cpu, language=zh, vad=True, beam=5, word_timestamps=True",
        ]
        txt_path.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
        words_path.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
        chars = sum(len(l.split("] ", 1)[-1]) for l in lines)
        print(f"done {sid}: {len(lines)} segs {chars} chars, "
              f"audio {info.duration:.0f}s wall {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
