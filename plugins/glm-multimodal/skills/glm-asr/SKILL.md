---
name: glm-asr
description: "Local speech-to-text for Codex agents: the source ASR skill's z-ai-web-dev-sdk audio.asr.create() and `z-ai asr` CLI (cloud ASR) are equivalently replaced by glmasr.py, which runs Whisper locally - primary chain faster-whisper provisioned on the fly via `uv run --with faster-whisper` (the user's uv-managed Python), fallback whisper.cpp whisper-cli; wav/mp3/m4a/flac/ogg supported, base64 input kept for CLI parity, JSON output SDK-compatible. 触发场景：音频转写 / 会议记录 / 访谈整理 / 播客转文字 / 语音笔记。"
metadata:
  version: "1.0.0"
---

# ASR（Speech to Text）Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-multimodal/`；本技能目录：
  `~/.codex/plugins/glm-multimodal/skills/glm-asr/`。下文 `scripts/` 指
  `scripts/glmasr.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 依赖云端
  `zai.audio.asr.create({file_base64})`（`z-ai asr` CLI 同源）——本地不部署
  该 SDK 且无云端 ASR 通道。等效替换为**本地 Whisper 转写**，后端链：

| 源 SDK / CLI 用法 | 本地等效（glmasr.py） | 说明 |
|---|---|---|
| `z-ai asr --file ./audio.wav` | `glmasr.py transcribe -f ./audio.wav` | 主链 faster-whisper（uv 即用即建临时环境） |
| `-o transcript.json` | `--json -o transcript.json` | `{text, language, duration, backend, model}`，`text` 字段与源响应同名 |
| `--base64 "…"`（base64 输入） | `-b/--base64 "…"`（兼容保留） | 解码落临时文件后转写，自动嗅扩展名 |
| 云端转写（无需本地模型） | 本地 Whisper（`--model tiny/base/small/medium/large-v3`） | 中文建议 `small` 起；首次运行自动下载模型 |
| Node SDK `audio.asr.create` | 纯 Python 标准库 bash 调用 | 本脚本零 pip 依赖；whisper 由 uv 临时环境承载 |

- 后端链：**faster-whisper（uv）主** → whisper.cpp `whisper-cli` 备（仅
  16kHz wav，模型 ggml-*.bin）→ 两者皆无则 exit 2 给安装指引。
  用户 mac 已有 `uv`（`/opt/uv/0.11.17`），主链开箱即用。
- 首次运行下载模型（small ~460MB）；国内网络先
  `export HF_ENDPOINT=https://hf-mirror.com`（HuggingFace 镜像）。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 后端缺失或转写失败。
- 输出落**用户工作目录**；插件目录只读。
- **同插件技能路由**：转写文本后要总结/翻译/分析 → glm-llm；
  转成语音 → glm-tts。

---

## Core Capabilities（沿源 skill）

- 单音频文件转写（wav/mp3/m4a/flac/ogg）
- base64 音频输入（源 CLI 参数兼容）
- 语言强制 / 自动检测（`--lang zh|en|…`）
- 档位选择：tiny（最快、中文弱）/ base / small（中文起步）/ medium / large-v3
- 转写 JSON（text + language + duration，供下游程序消费）

## 常用工作流

1. **单文件转写**：`python3 scripts/glmasr.py transcribe -f meeting.mp3`
2. **中文语音**：`glmasr.py transcribe -f notes.m4a --model small --lang zh`
3. **落盘 JSON**（源 -o 等效）：`… --json -o transcript.json`
4. **转写后分析**：转写 JSON → 把 text 交给 glm-llm 做纪要/摘要/待办提取
   （`glmllm.py chat -p "整理会议纪要：…" --json`）。
5. **批量目录**（源 transcribeDirectory 等效）：shell 循环
   `for f in *.wav; do glmasr.py transcribe -f "$f" --json -o "${f%.wav}.json"; done`

## 音频质量建议（沿源 skill）

- 采样率 16kHz 或更高；WAV/MP3/M4A 推荐
- 背景噪声尽量小、发音清晰、语速正常
- 超长音频先切分（`ffmpeg -i in.mp3 -f segment -segment_time 600 part%03d.mp3`）
  再逐段转写，避免超时

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 无可用本地 ASR 后端 | `brew install uv`（或官方安装脚本）；已有 uv 但 PATH 不含则修正 PATH |
| 首次卡在模型下载 | 国内网络设 `export HF_ENDPOINT=https://hf-mirror.com` 后重跑 |
| 中文识别差 | `--model small` 起步（base 对中文弱）；噪声大先降噪 |
| uv 临时环境构建慢/失败 | 首次拉包需要网络与磁盘；之后有缓存。仍失败换 whisper.cpp 后端 |
| whisper-cli 后端报格式错误 | whisper.cpp 仅吃 16kHz wav：`ffmpeg -i in.mp3 -ar 16000 out.wav` 后再转 |
| 转写结果为空 | 检查音频是否含清晰语音；`--lang` 指定正确语言 |
| 超时 exit 2 | 音频过长：切分分段；或降档 `--model base` |
