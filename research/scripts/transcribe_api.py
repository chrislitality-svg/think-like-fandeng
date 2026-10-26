# -*- coding: utf-8 -*-
"""批量转写(阿里云百炼 API):paraformer-realtime-v2 串流识别,本地文件直读。

- ffmpeg 转 16k mono pcm → 超过 SEG_SEC 切段 → 逐段 Recognition.call()
- 输出格式与 transcribe.py 完全一致:
  corpus/{编号}.txt        每行 [分:秒] 文本,头部 4 行元信息(标注 API 引擎)
  corpus/{编号}.words.json 逐词时间 [{"start","end","word"}]
- 已存在则跳过,可续跑;DASHSCOPE_API_KEY 环境变量必填
- 串流单连接有时长上限,故按 SEG_SEC 分段,段内时间戳加偏移后合并
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback

KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not KEY:
    sys.exit("请设置 DASHSCOPE_API_KEY 环境变量")
dashscope.api_key = KEY
MODEL = "paraformer-realtime-v2"
SEG_SEC = 50 * 60            # 串流单段时长上限(留余量)
MAX_PARALLEL = 2             # 并行识别的文件数

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent
AUDIO = BASE / "audio"
CORPUS = REPO / "corpus"
CORPUS.mkdir(exist_ok=True)
TMP = Path(tempfile.mkdtemp(prefix="asr_api_"))

import csv
META = {r["编号"]: r for r in csv.DictReader(open(BASE.parent / "data" / "样本.csv", encoding="utf-8-sig"))}

print_lock = threading.Lock()


def log(msg):
    with print_lock:
        print(msg, flush=True)


def fmt_ts(sec):
    m, s = divmod(int(sec), 60)
    return f"[{m:02d}:{s:02d}]"


def recognize_pcm(pcm_path, offset_sec=0.0):
    """一段 pcm → 句子列表(时间戳已加偏移,单位秒)"""
    class CB(RecognitionCallback):
        pass
    rec = Recognition(model=MODEL, format="pcm", sample_rate=16000,
                      callback=CB(), language_hints=["zh"])
    res = rec.call(str(pcm_path))
    if res.status_code != 200:
        raise RuntimeError(f"ASR {res.status_code}: {str(res.message)[:300]}")
    sents = []
    for s in res.output.get("sentence", []):
        if not s.get("sentence_end"):
            continue
        sents.append({
            "begin": (s["begin_time"] / 1000) + offset_sec,
            "end": (s["end_time"] / 1000) + offset_sec,
            "text": (s.get("text") or "").strip(),
            "words": [{"start": (w["begin_time"] / 1000) + offset_sec,
                       "end": (w["end_time"] / 1000) + offset_sec,
                       "word": (w.get("text", "") + w.get("punctuation", ""))}
                      for w in s.get("words", [])],
        })
    return sents


def transcribe(sid):
    src = AUDIO / f"{sid}.m4a"
    t0 = time.time()
    wav_path = TMP / f"{sid}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-ar", "16000", "-ac", "1", "-f", "wav", str(wav_path)],
                   check=True)
    w = wave.open(str(wav_path))
    n_frames, frame_rate = w.getnframes(), w.getframerate()
    total_sec = n_frames / frame_rate
    seg_len = SEG_SEC * frame_rate
    segs = []
    for i, start in enumerate(range(0, n_frames, seg_len)):
        w.setpos(start)
        frames = w.readframes(min(seg_len, n_frames - start))
        seg_path = TMP / f"{sid}.p{i}.pcm"
        seg_path.write_bytes(frames)
        segs.append((i, start / frame_rate, len(frames) / 2 / frame_rate, seg_path))
    w.close()
    wav_path.unlink(missing_ok=True)
    audio_sec = sum(s[2] for s in segs)

    from concurrent.futures import ThreadPoolExecutor

    def run_seg(args):
        i, off, seg_sec, seg_path = args
        for attempt in range(3):
            try:
                sents = recognize_pcm(seg_path, offset_sec=off)
                seg_path.unlink(missing_ok=True)
                log(f"  {sid} seg{i}: {seg_sec/60:.0f}min -> {len(sents)} sents "
                    f"(wall {time.time()-t0:.0f}s)")
                return (off, sents)
            except Exception as e:
                if attempt == 2:
                    raise
                log(f"  {sid} seg{i} attempt{attempt} failed ({str(e)[:120]}), retrying")
                time.sleep(10)

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(run_seg, segs))
    results.sort(key=lambda r: r[0])
    all_sents = [s for _, sents in results for s in sents]

    lines, words = [], []
    for s in all_sents:
        if not s["text"]:
            continue
        lines.append(f"{fmt_ts(s['begin'])} {s['text']}")
        words.extend(s["words"])
    meta = META.get(sid, {})
    header = [
        f"# {sid} {meta.get('标题', '')}",
        f"# 来源: {meta.get('来源平台', '')} {meta.get('链接', '')}",
        f"# 层: {meta.get('层', '')}  发布: {meta.get('发布日期', '')}  时长: {meta.get('时长', '')}",
        f"# 转写: 阿里云百炼 {MODEL} API(串流), language=zh, 句级+词级时间戳",
    ]
    (CORPUS / f"{sid}.txt").write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    (CORPUS / f"{sid}.words.json").write_text(
        json.dumps(words, ensure_ascii=False), encoding="utf-8")
    chars = sum(len(l.split("] ", 1)[-1]) for l in lines)
    log(f"done {sid}: {len(lines)} segs {chars} chars, audio {audio_sec:.0f}s "
        f"wall {time.time()-t0:.0f}s")


def main():
    only = set(sys.argv[1:]) or None
    files = sorted(AUDIO.glob("*.m4a"), key=lambda p: p.stat().st_size)
    todo = [f.stem for f in files
            if not (CORPUS / f"{f.stem}.txt").exists()
            and (not only or f.stem in only)]
    log(f"todo {len(todo)}: {' '.join(todo)}")
    fails = []
    sem = threading.Semaphore(MAX_PARALLEL)

    def run(sid):
        with sem:
            try:
                transcribe(sid)
            except Exception as e:
                import re
                if re.search(r"Arrearage|FreeQuota|AllocationQuota|InvalidApiKey", str(e)):
                    log(f"QUOTA-ABORT at {sid}: {str(e)[:200]}")
                    os._exit(1)
                log(f"FAIL {sid}: {type(e).__name__} {str(e)[:300]}")
                fails.append(sid)

    threads = [threading.Thread(target=run, args=(s,)) for s in todo]
    for t in threads: t.start()
    for t in threads: t.join()
    log(f"all done, failed: {fails or '无'}")


if __name__ == "__main__":
    main()
