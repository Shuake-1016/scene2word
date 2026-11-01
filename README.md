# English from Shows · 从剧集里挖单词

一键把**任意剧集**变成一套带片段的背单词工具：

```
剧集视频 → 语音识别（词级时间戳）→ 对齐四六级/雅思词表 → 自动切 10 秒片段（含上下文 + 重复 + 字幕）→ 生成练习页
```

> **为什么做这个**：市面上的背单词 App 里，单词和例句是编的。这个项目的每个单词、每句例句、每个视频片段，都来自你正在看的那部剧。

![截图](docs/screenshot-vocab.png)

## 它解决什么问题

传统背单词的两个断点：

1. **记不住**——词表里的例句是造的，跟你的生活没关系
2. **听不懂**——背了单词，但在真实语流里反应不过来

这个项目把两者接上：**你听到的就是你背的**。

## 工作流

```
videos/          你把剧集放进来（mp4）
  ↓ transcribe_only.py    faster-whisper 逐词时间戳
cache/*.json     转写缓存
  ↓ build_vocab.py        与四六级/雅思词表取交集 + 难度过滤
words.js         词表（带剧中原句）
  ↓ make_clips_v2.py      按停顿切句，切「上下文 + 目标句 ×2」，烧字幕和词标签
clips/*.mp4      单词片段
  ↓ grab_stills.py        抓单词发音那一帧
clips/img/*.jpg  记忆定格
  ↓ gen_tts.py            edge-tts 生成单词与例句音频
audio/tts/*.mp3  本地音频
```

生成的 `app/index.html` 直接打开即可使用。

## 学习流程（四环节）

| 环节 | 内容 |
|---|---|
| 一 | 看片段 → 单词 → 记住 / 没记住（回车继续） |
| 二 | 一次一个例句，出现即朗读 |
| 三 | 汉译拼写，背景播放该词的切片原声 |
| 四 | 没记住 + 拼错的词，二次巩固 |

每 10 个词一组，走完自动进入下一组。

## 快速开始

```bash
# 1. 依赖
pip install faster-whisper edge-tts imageio-ffmpeg wordfreq

# 2. 放剧集
mkdir -p videos && cp /path/to/your/episode.mp4 videos/

# 3. 跑完整流水线
./scripts/pipeline.sh
```

词表来源（需自备，二选一）：
- 四级 / 雅思词表 JSONL，放到 `data/cet4.jsonl`、`data/ielts.jsonl`
- 或修改 `scripts/build_vocab.py` 顶部的路径

## 目录结构

```
app/          学习页面（纯前端，无依赖）
scripts/      流水线脚本
docs/         截图
videos/       你放的剧集（.gitignore）
cache/        转写缓存（.gitignore）
clips/        生成的片段（.gitignore）
audio/        生成的音频（.gitignore）
```

## 关于版权

**本项目不包含任何影视素材。**

- 代码是开源的（MIT）
- 视频、片段、截图由使用者自行提供并生成
- 请只在**自己合法持有**的影视文件上使用，不要传播生成的片段

## 技术要点

- **词级时间戳**：faster-whisper 的 `word_timestamps=True`，切句按停顿（>0.35s）分段
- **上下文片段**：先取目标句前两句做铺垫，再重复目标句 2 遍，符合"先听懂情境，再聚焦单词"
- **去水印**：ffmpeg `delogo` 滤镜覆盖常见水印位置
- **本地 TTS**：edge-tts 预生成 mp3，避免依赖系统语音和网络

## License

MIT
