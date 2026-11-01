# -*- coding: utf-8 -*-
"""重新生成词帧截图：去水印、无文字标签"""
import json, os, subprocess
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(HERE, "clips", "img")
os.makedirs(OUT, exist_ok=True)

def stem(t):
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(t) > len(suf) + 3 and t.endswith(suf): return t[:-len(suf)]
    return t

data = json.loads(open(os.path.join(HERE, "words.js"), encoding="utf-8").read()
                  .split("window.DATA = ", 1)[1].rsplit(";", 1)[0])
want = {stem(w[0].lower()): w[0].lower() for w in data["words"]}

found = {}
for cf in sorted(os.listdir(os.path.join(HERE, "cache"))):
    if not cf.endswith(".json"): continue
    src = cf[:-5]
    vpath = os.path.join(HERE, "videos", src)
    if not os.path.exists(vpath): continue
    for w in json.load(open(os.path.join(HERE, "cache", cf), encoding="utf-8")):
        k = stem(w["w"])
        if k in want and want[k] not in found:
            found[want[k]] = (vpath, w["s"])

VF = ("scale=-2:1080,delogo=x=1:y=1:w=380:h=92,delogo=x=1019:y=1:w=260:h=92,scale=-2:720")
ok = 0
for word, (vpath, t) in found.items():
    dst = os.path.join(OUT, word + ".jpg")
    r = subprocess.run([FF, "-y", "-ss", f"{max(0,t+0.15):.2f}", "-i", vpath,
                        "-frames:v", "1", "-vf", VF, "-q:v", "3", dst], capture_output=True)
    if r.returncode == 0: ok += 1
print("词帧截图", ok, "/", len(found))
