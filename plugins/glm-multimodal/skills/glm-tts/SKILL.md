---
name: glm-tts
description: "Local text-to-speech for Codex agents on macOS: the source TTS skill's z-ai-web-dev-sdk audio.tts.create() and `z-ai tts` CLI (cloud TTS) are equivalently replaced by glmtts.py driving the macOS built-in say + afconvert chain - zero-install WAV 24kHz / M4A / AIFF output, source voice names mapped to system voices (Tingting/Daniel/Samantha...), speed 0.5-2.0 mapped to say rate, volume honored via optional ffmpeg post-processing, no 1024-char cap. 触发场景：文字转语音 / 有声书 / 课程旁白 / 无障碍音频 / 播报通知。与 本地模型文本产出联动。"
metadata:
  version: "1.0.0"
---

# TTS（Text to Speech）Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-multimodal/`；本技能目录：
  `~/.codex/plugins/glm-multimodal/skills/glm-tts/`。下文 `scripts/` 指
  `scripts/glmtts.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 依赖云端
  `zai.audio.tts.create({input, voice, speed, volume, response_format})`
  （`z-ai tts` CLI 同源）——本地不部署该 SDK。等效替换为 **macOS 自带
  say + afconvert 零安装链**：

| 源 SDK / CLI 用法 | 本地等效（glmtts.py） | 说明 |
|---|---|---|
| `z-ai tts -i "…" -o ./hello.wav` | `glmtts.py speak -i "…" -o ./hello.wav` | say 产 aiff → afconvert 转 WAV LEI16@24kHz（沿源推荐采样率） |
| `--voice tongtong` 等 7 音色 | `-v/--voice tongtong`（映射 Tingting 等） | `voices` 子命令看全表；也可直接传系统语音名 |
| `--speed 0.5–2.0` | `-s/--speed`（→ say 词/分钟） | 1.0 ≈ 180wpm；区间校验沿用源 API 约束 |
| `--volume (0,10]` | `--volume`（ffmpeg 后处理增益） | 无 ffmpeg 时明确提示不生效（不假装） |
| `--format mp3 / pcm` | `-o xxx.mp3 / -f pcm`（需 ffmpeg） | wav/m4a/aiff 走系统零依赖链 |
| 1024 字符上限（分块最佳实践） | 本地链无上限 | 超长文本可直接整段合成 |
| Node SDK（Response→arrayBuffer） | 纯 Python 标准库 bash 调用 | 零 pip 依赖 |

- **Linux 注意**：本链依赖 macOS 的 `say`/`afconvert`；Linux 无 say，如需
  TTS 装 espeak-ng 自行替换（用户环境为 macOS，本插件按 macOS 设计）。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 工具缺失或合成失败。
- 输出落**用户工作目录**；插件目录只读。
- **同插件技能路由**：文本先要写好 → glm-llm 生成；音频要转回文字 → glm-asr。

---

## Core Capabilities（沿源 skill）

- 文本转语音并落盘（wav 默认 / m4a / aiff；mp3、pcm 需 ffmpeg）
- 7 个源音色键 → macOS 系统语音映射（或直接传系统语音名）
- 语速 0.5–2.0（映射 say 词/分钟）
- 音量 (0,10]（有 ffmpeg 时实际生效）
- 长文本整段合成（本地链无 1024 限制）
- 音色表查询（`voices` 子命令 + `say -v '?'`）

## 常用工作流

1. **基础合成**：`python3 scripts/glmtts.py speak -i "你好，世界" -o ./hello.wav`
2. **音色选择**：`glmtts.py voices` → `glmtts.py speak -i "Welcome" -o en.wav -v jam`
3. **语速调节**（源 generateWithSpeed 等效）：
   `glmtts.py speak -i "重要通知" -o slow.wav -s 0.8` / `… -o fast.wav -s 1.5`
4. **批量合成**（源 batchTextToSpeech 等效）：
   `for i in 1 2 3; do glmtts.py speak -i "第${i}章" -o ch$i.wav; done`
5. **长文有声书**：整段直接合成；如需分段控制节奏，按句切分多文件后拼接
   （`ffmpeg -f concat`）。
6. **中文语音包**：系统设置 → 辅助功能 → 朗读内容 → 系统声音 → 管理声音，
   下载 Tingting/Meijia/Sinji 等中文语音。

## 文本准备建议（沿源 skill）

- 合成前压缩多余空白；
- 英文缩写可展开（Dr. → Doctor 等）改善发音；
- 中文里夹英文单词时系统语音通常可双语混读（Tingting 尤佳），效果不稳可
  分段合成。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 未找到 say | 非 macOS 或系统异常；Linux 装 espeak-ng 替代 |
| 合成报语音不存在 | `say -v '?'` 查真实名；中文语音未装则到系统设置下载 |
| say 报语音含空格/引号问题 | `-v "Bad News"` 这类含空格语音名要加引号整体传给 --voice |
| exit 2 + 需要 ffmpeg | `brew install ffmpeg`（mp3/pcm/音量增益）；wav/m4a 不需要 |
| 语速听感与 speed 不完全线性 | say 的 rate 是词/分钟近似映射；微调 speed 值即可 |
| 输出音量为原始响度 | 无 ffmpeg 时 --volume 不生效（stderr 有 NOTE）；装 ffmpeg 重跑 |
| 长文本合成慢 | 正常（CPU 合成整段）；可分段并行合成 |
