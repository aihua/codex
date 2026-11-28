---
name: glm-llm
description: "Local chat completions for Codex agents: the source LLM skill's z-ai-web-dev-sdk chat.completions.create() and `z-ai chat` CLI are equivalently replaced by glmllm.py, a zero-dependency CLI over the local Ollama /api/chat endpoint. Single-turn QA, system prompts, thinking mode, streaming, multi-turn JSONL sessions, retry discipline. 触发场景：单轮问答 / 多轮对话 / system 人设 / 思维链 / 流式输出 / 代码生成与解释。"
metadata:
  version: "1.0.0"
---

# LLM Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-multimodal/`；本技能目录：
  `~/.codex/plugins/glm-multimodal/skills/glm-llm/`。下文 `scripts/` 指
  `scripts/glmllm.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 的全部能力依赖
  `ZAI.create()` + `zai.chat.completions.create()`（云端网关，本地不部署）。
  等效替换为**本地 Ollama /api/chat 的零依赖 CLI**：

| 源 SDK / CLI 用法 | 本地等效（glmllm.py） | 说明 |
|---|---|---|
| `zai.chat.completions.create({messages})` | `glmllm.py chat -p "…" [-s system]` | /api/chat；`choices[0].message.content` 同名对齐 |
| `z-ai chat --prompt "…" -o r.json` | `glmllm.py chat -p "…" --json -o r.json` | JSON 形状与源 SDK 兼容（含 usage 映射） |
| `--system "你是…"` | `-s/--system` | 映射为 role:system 消息（Ollama 原生支持） |
| `--thinking`（思维链） | `--think` | Ollama `think:true`；模型不支持思考时会忽略或报错，去掉该开关即可 |
| `--stream` | `--stream` | /api/chat NDJSON 增量打印 |
| ConversationManager / 多轮历史 | `--session s.jsonl` | JSONL 追加式会话历史 |
| 指数退避重试（最佳实践） | 内置 `--retries`（默认 2，2s/4s） | 仅网络类错误重试 |
| Node SDK 代码内调用 | bash 执行 python3 | Codex 工具调用即可，无需 Node |

- 模型路由：`--model` 默认主力模型（多轮、长文、代码）；轻量单轮可用 `--model` 换轻量模型。
  服务地址默认 `http://127.0.0.1:11434`，可用 `OLLAMA_HOST` 覆盖。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 网络或模型服务错误（stderr 报因不假死）。
- 输出落**用户工作目录**（模型转述或存 `output/`）；插件目录只读。
- **技能路由**：图像理解 → glm-image 插件中的 glm-image-understand 技能（若已安装）；视觉对话 → 同插件技能 glm-vlm；
  联网检索 → glm-web 插件中的 glm-web-search 技能（若已安装）；语音转文字 → 同插件技能 glm-asr、文字转语音 → 同插件技能 glm-tts。

---

## Core Capabilities（沿源 skill）

- Single-turn Q&A 与 system 人设问答
- Multi-turn conversation（JSONL 会话历史，等效 ConversationManager）
- Thinking / chain-of-thought（--think，需模型支持）
- Streaming 输出（--stream）
- 内容生成 / 数据摘要 / 代码生成与调试（由 prompt 驱动，模型本地完成）
- 错误处理与重试纪律（网络错误自动退避重试）

## 常用工作流

1. **单轮问答**：`python3 scripts/glmllm.py chat -p "法国的首都是哪里？"`
2. **人设问答**（源 customAssistant 等效）：
   `glmllm.py chat -p "Review: function add(a,b){return a-b;}" -s "You are an expert code reviewer"`
3. **多轮会话**（源 ConversationManager 等效）：
   `glmllm.py chat -p "我叫 John" --session s.jsonl` →
   `glmllm.py chat -p "我叫什么名字？" --session s.jsonl`
4. **思维链**：`glmllm.py chat -p "120km/2h 的均速?" --think`
5. **结构化输出**（源 getStructuredResponse 等效）：
   `glmllm.py chat -p "列出三种语言及用途，仅 JSON" --json -o langs.json`
6. **长文/代码**：交给主力模型，`--timeout` 保持默认 600s（本地推理慢是正常）。

## 模型选择速查

| 场景 | 模型 |
|---|---|
| 多轮、代码、长文、思维链 | 主力模型（默认） |
| 单轮快查、轻量改写 | 轻量模型 |
| 备用轻量档 | 轻量模型 |

## Prompt 要点（沿源 skill 最佳实践）

- 具体、结构化：给受众 / 格式 / 长度约束，而非"讲讲 AI"。
- 多轮会话注意裁剪历史（glmllm 不自动裁剪；超长可新建会话文件）。
- 要求 JSON 时明确"仅输出 JSON"。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + cannot reach Ollama | `ollama serve` 未起或 `OLLAMA_HOST` 指错；`curl -s 127.0.0.1:11434/api/tags` 自检 |
| exit 2 + model not found | `ollama pull <目标模型名>`（或目标模型名） |
| `--think` 报不支持 | 该模型无思维链能力，去掉开关 |
| 响应慢 | 本地大模型正常现象；`--model` 换轻量模型提速，勿调小 timeout |
| Codex 内命令连不上网 | 本插件走 127.0.0.1 回环，通常不受沙箱禁网影响；若被拦见 README 网络节 |
