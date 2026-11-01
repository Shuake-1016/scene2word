# -*- coding: utf-8 -*-
"""从转写缓存生成「句子重复3遍 + 标出目标词」的片段

规则：
  1. 找到目标词所在的句子（按停顿切分，0.35s 以上算停顿）
  2. 句长限制 2.5–8 秒，太长就围绕单词收窄
  3. 同一句重复 3 遍拼接
  4. 左上角常驻「本词 xxx」标签
"""
import glob, json, os, re, subprocess
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(HERE, "clips")


def flush_index():
    open(os.path.join(OUT, "index.js"), "w", encoding="utf-8").write(
        "window.CLIPS = " + json.dumps(made, ensure_ascii=False) + ";\n")
os.makedirs(OUT, exist_ok=True)
PAUSE = 0.35
MIN_S, MAX_S = 2.5, 8.0

def stem(t):
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            return t[:-len(suf)]
    return t

src = open(os.path.join(HERE, "words.js"), encoding="utf-8").read()
data = json.loads(re.search(r"window\.DATA\s*=\s*(\{.*\});?\s*$", src, re.S).group(1))
targets = {stem(w[0].lower()): w[0].lower() for w in data["words"]}
ORDER = {w[0].lower(): i for i, w in enumerate(data["words"])}

def duration_of(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if not m: return 0
    h, mi, s = m.groups(); return int(h)*3600 + int(mi)*60 + float(s)

def sentences_of(words):
    """按停顿切句，返回 [[i0,i1], ...]（词下标区间）"""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        nxt = words[i+1] if i+1 < len(words) else None
        if nxt is None or (nxt["s"] - w["e"]) > PAUSE:
            out.append((cur[0], cur[-1])); cur = []
    return out

def sent_index(sents, i):
    for k, (a, b) in enumerate(sents):
        if a <= i <= b: return k
    return 0

def sentence_span(words, i):
    """以停顿为界，返回包含第 i 个词的句子起止"""
    s, e = words[i]["s"], words[i]["e"]
    j = i
    while j > 0 and (words[j]["s"] - words[j-1]["e"]) < PAUSE:
        j -= 1; s = words[j]["s"]
    k = i
    while k < len(words)-1 and (words[k+1]["s"] - words[k]["e"]) < PAUSE:
        k += 1; e = words[k]["e"]
    if e - s < MIN_S:
        s = max(0, s - (MIN_S - (e-s))/2); e = e + (MIN_S - (e-s))/2
    if e - s > MAX_S:                      # 太长：以单词为中心收窄
        mid = (words[i]["s"] + words[i]["e"]) / 2
        s, e = max(0, mid - MAX_S/2), mid + MAX_S/2
    return s, e

def fmt_ts(t):
    ms = int(round(max(0, t) * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def write_srt(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, text) in enumerate(items, 1):
            f.write(f"{i}\n{fmt_ts(a)} --> {fmt_ts(b)}\n{text}\n\n")


STYLE = ("FontName=Helvetica,FontSize=19,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
         "BorderStyle=1,Outline=1.2,Shadow=0,MarginV=16,Alignment=2")


def _cut(vpath, a, b, out, label, with_label=True, srt=None):
    vf = ("scale=-2:1080,"
          "delogo=x=1:y=1:w=380:h=92,"
          "delogo=x=1019:y=1:w=260:h=92")
    if srt:
        vf += ",subtitles='" + srt + "':force_style='" + STYLE + "'"
    if with_label:
        vf += (",drawtext=text='" + label + "':fontsize=78:fontcolor=white:"
               "box=1:boxcolor=0x000000@0.55:boxborderw=22:x=(w-text_w)/2:y=26")
    r = subprocess.run([FF, "-y", "-ss", f"{a:.2f}", "-t", f"{max(0.3, b-a):.2f}", "-i", vpath,
        "-vf", vf, "-c:v", "h264_videotoolbox", "-b:v", "2600k", "-allow_sw", "1",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out], capture_output=True)
    return r.returncode == 0

def build(word, vpath, s, e, dst, ctx_start=None, ctx_items=None, sent_text="", with_srt=True):
    """上下文(1段) + 目标句(重复3遍)，都烧英文字幕"""
    label = word.replace("'", "").replace(":", "")
    segs = []
    if ctx_start is not None:
        ctx_start = max(ctx_start, s - 8.5)
    if ctx_start is not None and ctx_start < s - 1.0 and ctx_items:
        write_srt("/tmp/_ctx.srt", [(a - ctx_start, b - ctx_start, t) for a, b, t in ctx_items])
        a = "/tmp/_ctx.mp4"
        if _cut(vpath, ctx_start, s - 0.05, a, label, with_label=False,
                srt=("/tmp/_ctx.srt" if with_srt else None)):
            segs.append(a)
    write_srt("/tmp/_sent.srt", [(0.0, max(1.0, (e + 0.45) - max(0, s-0.35)), sent_text)])
    b = "/tmp/_sent.mp4"
    if not _cut(vpath, max(0, s-0.35), e+0.45, b, label,
                srt=("/tmp/_sent.srt" if with_srt else None)):
        return False
    segs += [b, b]
    with open("/tmp/_list.txt", "w") as f:
        for x in segs:
            f.write("file '" + x + "'\n")
    r2 = subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", "/tmp/_list.txt",
                         "-c", "copy", "-movflags", "+faststart", dst], capture_output=True)
    return r2.returncode == 0

IMG = os.path.join(OUT, "img")
os.makedirs(IMG, exist_ok=True)

def grab_frame(vpath, t, word):
    dst = os.path.join(IMG, word + ".jpg")
    subprocess.run([FF, "-y", "-ss", f"{max(0,t):.2f}", "-i", vpath, "-frames:v", "1",
                    "-vf", "scale=-2:540", "-q:v", "3", dst], capture_output=True)

hits = {}
for cf in sorted(glob.glob(os.path.join(HERE, "cache", "*.json"))):
    name = os.path.basename(cf)[:-5]
    vpath = os.path.join(HERE, "videos", name)
    if not os.path.exists(vpath): continue
    words = json.load(open(cf, encoding="utf-8"))
    sents = sentences_of(words)
    def stext(span):
        t = " ".join(x["w"] for x in words[span[0]:span[1]+1]).strip()
        return (t[:1].upper() + t[1:] + ".") if t else ""
    for i, wd in enumerate(words):
        base = stem(wd["w"])
        if base in targets:
            k = sent_index(sents, i)
            ctx, ctx_items = None, []
            if k >= 1:
                lo = max(0, k-2)
                pick = sents[lo:k]
                if pick:
                    ctx = max(0, words[pick[0][0]]["s"] - 0.3)
                    ctx_items = [(words[a]["s"], words[b]["e"], stext((a, b))) for a, b in pick]
            hits.setdefault(targets[base], []).append(
                (vpath, words, i, ctx, ctx_items, stext(sents[k])))

made, durs = {}, {}
for word, occ in sorted(hits.items(), key=lambda kv: ORDER.get(kv[0], 99999)):
    vpath, words, i, ctx, ctx_items, sent_text = occ[0]
    if vpath not in durs: durs[vpath] = duration_of(vpath)
    s, e = sentence_span(words, i)
    e = min(e, durs[vpath])
    dst = os.path.join(OUT, word + ".mp4")
    if os.path.exists(dst) and os.path.getsize(dst) > 50000:
        made[word] = 1
        if len(made) % 25 == 0: flush_index()
        continue
    need_sub = not os.path.basename(vpath).startswith("S01E")
    if build(word, vpath, s, e, dst, ctx, ctx_items, sent_text, with_srt=need_sub):
        made[word] = 1
        grab_frame(vpath, words[i]["s"] + 0.2, word)
        if len(made) % 25 == 0:
            flush_index()
        print(f"✓ {word:<12} {e-s:4.1f}s ×3  ← {os.path.basename(vpath)}")

flush_index()
print(f"\n共 {len(made)} 个词，均已重复 3 遍并标注")
