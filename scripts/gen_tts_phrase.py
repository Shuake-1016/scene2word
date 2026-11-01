# -*- coding: utf-8 -*-
"""短语 + 例句的本地音频"""
import asyncio, json, os
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = "en-GB-RyanNeural"; RATE = "-4%"
OUT = os.path.join(HERE, "audio", "tts", "p")
os.makedirs(OUT, exist_ok=True)

data = json.loads(open(os.path.join(HERE, "words.js"), encoding="utf-8").read()
                  .split("window.DATA = ", 1)[1].rsplit(";", 1)[0])
items = data.get("phrases", [])

async def one(text, path):
    if os.path.exists(path) and os.path.getsize(path) > 2000: return True
    for _ in range(3):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
            if os.path.getsize(path) > 2000: return True
        except Exception:
            await asyncio.sleep(1.2)
    return False

async def main():
    jobs = []
    for i, p in enumerate(items):
        jobs.append(one(p[0], os.path.join(OUT, f"{i}_0.mp3")))
        if len(p) > 2 and p[2]:
            jobs.append(one(p[2], os.path.join(OUT, f"{i}_1.mp3")))
    res = await asyncio.gather(*jobs)
    idx = [i for i, p in enumerate(items)
           if os.path.exists(os.path.join(OUT, f"{i}_0.mp3"))]
    open(os.path.join(HERE, "audio", "tts", "phrase_index.js"), "w", encoding="utf-8").write(
        "window.TTSP = " + json.dumps(idx) + ";\n")
    print("短语音频", sum(res), "/", len(jobs), "| 可用短语", len(idx))

asyncio.run(main())
