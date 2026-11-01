#!/bin/bash
cd "$(dirname "$0")"
# 等转写结束
while pgrep -f "transcribe_pick.py" > /dev/null; do sleep 30; done
echo "=== 转写完成 $(date) ==="
python3 build_vocab.py
python3 make_clips_v2.py
python3 grab_stills.py
HF_HUB_DISABLE_XET=1 python3 gen_tts.py
python3 gen_tts_phrase.py
python3 build_praise.py
python3 - <<'PY'
import json, os
items = json.load(open("audio/index.json", encoding="utf-8"))
open("audio/index.js","w",encoding="utf-8").write("window.PRAISE = " + json.dumps(items, ensure_ascii=False) + ";\n")
print("praise", len(items))
PY
echo "=== 全部完成 $(date) ==="
