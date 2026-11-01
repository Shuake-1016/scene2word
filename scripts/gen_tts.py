# -*- coding: utf-8 -*-
"""用 edge-tts 生成单词和例句的本地音频（英式男声）"""
import asyncio, json, os, sys
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = "en-GB-RyanNeural"
RATE = "-4%"
W = os.path.join(HERE, "audio", "tts", "w")
E = os.path.join(HERE, "audio", "tts", "e")
os.makedirs(W, exist_ok=True); os.makedirs(E, exist_ok=True)

data = json.loads(open(os.path.join(HERE, "words.js"), encoding="utf-8").read()
                  .split("window.DATA = ", 1)[1].rsplit(";", 1)[0])
words = data["words"]

sem = asyncio.Semaphore(6)

async def one(text, path):
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return True
    async with sem:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
                if os.path.getsize(path) > 2000:
                    return True
            except Exception:
                await asyncio.sleep(1.5)
    return False

async def main():
    jobs = []
    for w in words:
        word = w[0]
        jobs.append(one(word, os.path.join(W, word + ".mp3")))
    done = await asyncio.gather(*jobs)
    print("单词音频", sum(done), "/", len(jobs), flush=True)

    jobs = []
    for w in words:
        word = w[0]
        for i, ex in enumerate((w[2] or [])[:3]):
            if ex:
                jobs.append(one(ex, os.path.join(E, f"{word}_{i}.mp3")))
    done = await asyncio.gather(*jobs)
    print("例句音频", sum(done), "/", len(jobs), flush=True)

    tw = [w[0] for w in words if os.path.exists(os.path.join(W, w[0] + ".mp3"))]
    te = {}
    for w in words:
        for i in range(3):
            p = os.path.join(E, f"{w[0]}_{i}.mp3")
            if os.path.exists(p): te[f"{w[0]}:{i}"] = 1
    open(os.path.join(HERE, "audio", "tts", "index.js"), "w", encoding="utf-8").write(
        "window.TTSW = " + json.dumps(tw, ensure_ascii=False) + ";\n"
        "window.TTSE = " + json.dumps(te, ensure_ascii=False) + ";\n")
    print("索引", len(tw), "词 /", len(te), "例句")

asyncio.run(main())
