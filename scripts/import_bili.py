# -*- coding: utf-8 -*-
"""把 B站客户端的缓存（~/Movies/bilibili/*.m4s）合并成可用的 mp4，放进 videos/"""
import json, os, re, subprocess, sys, time
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Movies/bilibili")
OUT = os.path.join(HERE, "videos")
FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs(OUT, exist_ok=True)

def title_of(d):
    for j in ("videoInfo.json", "entry.json"):
        p = os.path.join(d, j)
        if os.path.exists(p):
            t = open(p, encoding="utf-8", errors="ignore").read(6000)
            m = re.search(r'"(?:title|part)"\s*:\s*"([^"]{1,50})"', t)
            if m: return m.group(1)
    return os.path.basename(d)

def strip(src, dst):
    with open(src, "rb") as f:
        head = f.read(16)
        f.seek(9 if head.startswith(b"000000000") else 0)
        with open(dst, "wb") as o:
            while True:
                b = f.read(4 << 20)
                if not b: break
                o.write(b)

made = 0
for d in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, d)
    if not os.path.isdir(p): continue
    m4s = [f for f in os.listdir(p) if f.endswith(".m4s")]
    vids = [f for f in m4s if "-30280." not in f and "-30216." not in f and os.path.getsize(os.path.join(p,f)) > 3e6]
    auds = [f for f in m4s if "-30280." in f or "-30216." in f]
    if not vids or not auds: continue
    newest = max(os.path.getmtime(os.path.join(p,f)) for f in vids+auds)
    if time.time() - newest < 120:
        print("跳过（还在下载）", d); continue
    name = re.sub(r"[^\w\-]+", "_", title_of(p))[:40] or d
    out = os.path.join(OUT, name + ".mp4")
    if os.path.exists(out): continue
    tv, ta = "/tmp/_v.mp4", "/tmp/_a.mp4"
    strip(os.path.join(p, vids[0]), tv)
    strip(os.path.join(p, auds[0]), ta)
    r = subprocess.run([FF, "-y", "-i", tv, "-i", ta, "-c", "copy",
                        "-movflags", "+faststart", out], capture_output=True)
    os.remove(tv); os.remove(ta)
    ok = r.returncode == 0 and os.path.getsize(out) > 10e6
    print(("✓ " if ok else "✗ ") + name, f"{os.path.getsize(out)/1e6:.0f}MB" if ok else r.stderr[-200:])
    made += 1
print("完成", made, "个")
