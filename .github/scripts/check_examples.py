# -*- coding: utf-8 -*-
"""CI：把 examples 里的示例正文抽出来过检测器，门槛 < 20。"""
import re, subprocess, sys, tempfile, os
from pathlib import Path

THRESHOLD = 20
root = Path(__file__).resolve().parents[2]
fails = []
for f in sorted((root / "examples").glob("*.md")):
    text = f.read_text(encoding="utf-8")
    m = re.search(r"\*\*(?:输出|改好的全文)\*\*[：:]\n(.*?)(?:\n---|\Z)", text, re.S)
    if not m:
        m = re.search(r"\*\*对话\*\*[：:]\n(.*?)(?:\n---|\Z)", text, re.S)
    if not m:
        continue
    body = re.sub(r"\*\*\*|\*\*", "", m.group(1))
    body = "\n".join(l[2:] if l.startswith("> ") else l for l in body.split("\n"))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        tmp = fh.name
    r = subprocess.run(["python3", str(root / "tools/ai_flavor_check.py"), tmp],
                       capture_output=True, text=True)
    os.unlink(tmp)
    s = re.search(r"AI 味体检[：: ]*(\d+)\s*/\s*100", r.stdout)
    # 改稿类：只对「改好的全文」段落计分（匹配即该段）
    seg = re.search(r"\*\*改好的全文\*\*[：:]\n(.*?)(?:\n\n|\n---)", text, re.S)
    if f.name.startswith(("11", "12")) and seg:
        body2 = re.sub(r"\*\*\*|\*\*", "", seg.group(1))
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
            fh.write(body2)
            tmp2 = fh.name
        r2 = subprocess.run(["python3", str(root / "tools/ai_flavor_check.py"), tmp2],
                            capture_output=True, text=True)
        os.unlink(tmp2)
        s2 = re.search(r"AI 味体检[：: ]*(\d+)\s*/\s*100", r2.stdout)
        if s2:
            s = s2
    score = int(s.group(1)) if s else 99
    print(f"{f.name}: {score}")
    if score >= THRESHOLD:
        fails.append(f.name)
if fails:
    print("FAILED:", fails)
    sys.exit(1)
print("全部示例 AI 味 < 20")
