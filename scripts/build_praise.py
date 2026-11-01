# -*- coding: utf-8 -*-
"""从剧里提取「夸赞词」的原声，做成本地音效"""
import json, os, re, subprocess
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(HERE, "audio")
os.makedirs(OUT, exist_ok=True)

PRAISE = {"wonderful", "perfect", "beautiful", "great", "marvelous", "brilliant", "excellent", "amazing"}
def dims(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Video:.*?,\s*(\d+)x(\d+)", out)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

clips = []
for cf in sorted(os.listdir(os.path.join(HERE, "cache"))):
    if not cf.endswith(".json"): continue
    src = cf[:-5]
    vpath = os.path.join(HERE, "videos", src)
    if not os.path.exists(vpath): continue
    w_, h_ = dims(vpath)
    if w_ and h_ and h_ > w_:      # 竖屏素材有标题条和大黑边，不要
        continue
    for w in json.load(open(os.path.join(HERE, "cache", cf), encoding="utf-8")):
        t = w["w"].strip().lower().strip(".,!?")
        if t in PRAISE and (w["e"] - w["s"]) >= 0.25:
            clips.append((t, src, w["s"], w["e"]))

made = []
for i, (word, src, s, e) in enumerate(clips[:16]):
    dst = os.path.join(OUT, f"praise_{i:02d}.m4a")
    r = subprocess.run([FF, "-y", "-ss", f"{max(0,s-0.7):.2f}", "-to", f"{e+0.9:.2f}",
                        "-i", os.path.join(HERE, "videos", src), "-vn",
                        "-c:a", "aac", "-b:a", "96k", dst], capture_output=True)
    if r.returncode == 0 and os.path.getsize(dst) > 4000:
        img = f"praise_{i:02d}.jpg"
        subprocess.run([FF, "-y", "-ss", f"{s+0.15:.2f}", "-i", os.path.join(HERE, "videos", src),
                        "-frames:v", "1", "-vf", "scale=-2:540", "-q:v", "3",
                        os.path.join(OUT, img)], capture_output=True)
        made.append({"f": f"praise_{i:02d}.m4a", "w": word, "img": img})

json.dump(made, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("夸赞音效", len(made), "段：", sorted({m["w"] for m in made}))
