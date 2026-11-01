# -*- coding: utf-8 -*-
"""从 cache/ 里所有转写重建词表 words.js（雅思词 ∩ 剧集台词）"""
import json, os
from wordfreq import zipf_frequency as zf

HERE = os.path.dirname(os.path.abspath(__file__))

def stem(t):
    for suf in ("ing","ed","es","s","ly"):
        if len(t) > len(suf)+3 and t.endswith(suf): return t[:-len(suf)]
    return t

def load_books():
    """雅思 + 四级，合并去重；返回 {word: info}"""
    books = [("/tmp/t.jsonl", 2.8, 4.55, "雅思"), ("/tmp/cet4.jsonl", 3.2, 5.0, "四级")]
    d = {}
    for path, lo, hi, tag in books:
        if not os.path.exists(path):
            print("缺少词表", path); continue
        part = _load_one(path, lo, hi)
        for k, v in part.items():
            if k in d:
                if tag not in d[k]["book"]: d[k]["book"] += "+" + tag
            else:
                v["book"] = tag
                d[k] = v
    return d

def _load_one(path, lo, hi):
    d = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: o = json.loads(line)
        except Exception: continue
        w = o.get("word","").strip().lower()
        tr = o.get("translations") or []
        if not w or " " in w or not tr: continue
        ph = o.get("phrases") or []
        d[w] = {"pos": tr[0].get("type",""),
                "meaning": "；".join(t.get("translation","") for t in tr[:2]),
                "phrase": (ph[0].get("phrase","") + "　" + ph[0].get("translation","")) if ph else "",
                "lo": lo, "hi": hi}
    return d

def main():
    ielts = load_books()
    occ = {}
    for cf in sorted(os.listdir(os.path.join(HERE, "cache"))):
        if not cf.endswith(".json"): continue
        words = json.load(open(os.path.join(HERE, "cache", cf), encoding="utf-8"))
        sent, sents = [], []
        for i, w in enumerate(words):
            sent.append(w)
            nxt = words[i+1] if i+1 < len(words) else None
            if nxt is None or (nxt["s"] - w["e"]) > 0.35:
                sents.append(sent); sent = []
        for s in sents:
            text = " ".join(x["w"] for x in s).strip()
            if 3 <= len(text.split()) <= 25:
                text = text[:1].upper() + text[1:] + "."
                for x in s: occ.setdefault(stem(x["w"]), set()).add(text)

    rows = []
    for w, info in ielts.items():
        hits = occ.get(stem(w))
        if not hits or len(w) < 4: continue
        if not (info.get("lo", 2.8) <= zf(w, "en") <= info.get("hi", 4.55)): continue
        ex = sorted(hits, key=lambda x: len(x.split()))[:3]
        tag = ((info["pos"] or "").strip() + ". ") if info["pos"] else ""
        rows.append([w, tag + info["meaning"], ex, info["phrase"], info.get("book", "")])
    rows.sort(key=lambda x: -zf(x[0], "en"))

    old = open(os.path.join(HERE, "words_backup_academic.js"), encoding="utf-8").read()
    phrases = json.loads(old.split("window.DATA = ",1)[1].rsplit(";",1)[0])["phrases"]
    open(os.path.join(HERE, "words.js"), "w", encoding="utf-8").write(
        "window.DATA = " + json.dumps({"words": rows, "phrases": phrases}, ensure_ascii=False) + ";\n")
    print("词表更新：", len(rows), "词")

if __name__ == "__main__":
    main()
