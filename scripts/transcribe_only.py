# -*- coding: utf-8 -*-
"""只转写 videos/ 里还没缓存过的视频"""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_clips import transcribe
from faster_whisper import WhisperModel

HERE = os.path.dirname(os.path.abspath(__file__))
vids = sorted(glob.glob(os.path.join(HERE, "videos", "*.*")))
todo = [v for v in vids if not os.path.exists(os.path.join(HERE, "cache", os.path.basename(v) + ".json"))]
print("待转写", len(todo), "/", len(vids))
if not todo: sys.exit(0)
m = WhisperModel("small", device="cpu", compute_type="int8",
                 download_root=os.path.join(HERE, "models"), cpu_threads=max(2,(os.cpu_count() or 4)-1))
for v in todo:
    print("-", os.path.basename(v), flush=True)
    transcribe(v, m)
print("done")
