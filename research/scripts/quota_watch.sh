#!/bin/bash
# 額度看門狗:API 批次一旦出現欠費/額度錯誤,立即停掉並用本地 whisper 接手剩餘檔案。
LOG="$HOME/Projects/think-like-fandeng/research/scripts/transcribe_api.log"
WLOG="$HOME/Projects/think-like-fandeng/research/scripts/quota_watch.log"
API_PID="$1"
IDS="A02 A03 A04 A05 A06 A07 A08 A09 A10 C01 C03 C04 C05 C06 D04"

while true; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "$(date '+%H:%M:%S') API batch exited (normal finish), watcher exits" >> "$WLOG"
    exit 0
  fi
  # 只匹配欠費/免費額度耗盡類錯誤(FILE_403_FORBIDDEN 等歷史錯誤不算)
  if tail -50 "$LOG" | grep -qE 'Arrearage|FreeQuota|AllocationQuota|InvalidApiKey|Throttling.*exceed'; then
    echo "$(date '+%H:%M:%S') quota error detected -> killing API batch" >> "$WLOG"
    kill "$API_PID" 2>/dev/null
    sleep 3
    kill -9 "$API_PID" 2>/dev/null
    cd "$HOME/Projects/think-like-fandeng" && \
      nohup .venv/bin/python research/scripts/transcribe.py $IDS \
      >> research/scripts/transcribe.log 2>&1 < /dev/null &
    echo "$(date '+%H:%M:%S') local whisper restarted for remaining files" >> "$WLOG"
    exit 0
  fi
  sleep 60
done
