---
name: glm-vlm
description: "Local vision chat for Codex agents: the source VLM skill's z-ai-web-dev-sdk chat.completions.createVision() and `z-ai vision` CLI are equivalently replaced by glmvlm.py, a zero-dependency CLI over the local Ollama /api/chat endpoint passing images as base64 (default vision model). Single/multiple images, local paths or URLs, multi-turn vision sessions, SDK-compatible JSON output. 触发场景：图片问答 / 多图对比 / 图文多轮对话 / 界面截图分析。"
metadata:
  version: "1.0.0"
---

# VLM（Vision Chat）Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-multimodal/`；本技能目录：
  `~/.codex/plugins/glm-multimodal/skills/glm-vlm/`。下文 `scripts/` 指
  `scripts/glmvlm.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 的全部能力依赖
  `zai.chat.completions.createVision()`（云端多模态网关）——本地不部署。
  等效替换为**本地 Ollama /api/chat 的零依赖 CLI**（messages[].images 传
  base64，与 OpenAI 兼容层无关）：

| 源 SDK / CLI 用法 | 本地等效（glmvlm.py） | 说明 |
|---|---|---|
| `createVision({messages:[…, image_url]})` | `glmvlm.py -p "…" -i ./a.jpg` | 本地图片读文件转 base64 |
| image_url 传远程 URL | `glmvlm.py -p "…" -i https://…/a.png` | CLI 自动下载后转 base64（源 skill 推荐做法的等效落地） |
| base64 data URL 输入 | `-i 本地路径`（推荐） | 源 skill「base64 更稳」最佳实践 → 本地版一律 base64 传输 |
| `z-ai vision -p … -i a.jpg -i b.jpg` 多图 | `-i a.jpg -i b.jpg`（可重复） | Ollama images 数组原生多图 |
| `--thinking` 思维链 | 不适用 | 视觉模型无思维链；如需推理用文本模型辅助 |
| `--stream` | 不适用（一次性返回） | 本地小上下文更稳 |
| VisionChatSession 多轮 | `--session v.jsonl` | JSONL 历史，图片轮次只存指令文本（不重复存图） |
| `video_url` / `file_url` 内容类型 | 不适用 | Ollama 不支持视频/文档内容；视频见姊妹 glm-video-understand 之限制说明，文档先摘文本再走 glm-llm |
| Node SDK import | 纯 Python 标准库 bash 调用 | 零 pip / 零 npm |

- **模型路由（关键）**：默认 `--model` 指定视觉模型（多模态档）。其他本地模型是否吃图取决于其 modelfile 构建方式：报「不支持图像」类错误时回到视觉模型。
- 服务地址默认 `http://127.0.0.1:11434`，`OLLAMA_HOST` 可覆盖。
- 图片上限 `GLM_VLM_MAX_IMAGE_MB`（默认 20MB）；超限先压缩。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 网络、图片或模型错误。
- 输出落**用户工作目录**；插件目录只读。
- **跨插件技能路由（glm-image 插件，若已安装）**：静态图深度分析/OCR → glm-image-understand；图片素材
  检索 → glm-image-search；生成图 → glm-image-generation；编辑 → glm-image-edit。

---

## Core Capabilities（沿源 skill）

- Single image analysis（描述、问答、识别）
- Multiple images comparison（差异对比、共同点归纳）
- Conversational vision chat（--session 追问）
- Local file / URL 双输入通道（一律转 base64 送本地模型）
- Image classification & tagging（由 prompt 驱动模型输出 JSON）
- OCR 文本提取（模型能力，配合 glm-image-understand 的专用模板更稳）

## 常用工作流

1. **单图问答**：`python3 scripts/glmvlm.py -p "这张图里有什么？" -i ./photo.jpg`
2. **URL 图分析**：`glmvlm.py -p "Describe this product" -i https://example.com/p.jpg`
3. **多图对比**（源 compareImages 等效）：
   `glmvlm.py -p "对比两张图并描述差异" -i before.jpg -i after.jpg`
4. **视觉多轮**（源 VisionChatSession 等效）：
   `glmvlm.py -p "这张图表显示什么?" -i chart.png --session v.jsonl` →
   `glmvlm.py -p "关键趋势是哪些?" --session v.jsonl`
5. **结构化打标**（源 classifyImage 等效）：
   `glmvlm.py -p "分析图片并按 JSON 输出 main_subject/key_objects/scene/tags" -i x.jpg --json -o tags.json`

## Prompt 要点（沿源 skill）

- 明确要什么信息（对象清单 / 数量 / 文本 / 情绪），不要"看看这张图"。
- 说明图片类型背景（照片、图表、截图、表单）可显著提质。
- 复杂请求用编号列表拆解。
- 小视觉模型（轻量档）计数/精确 OCR 能力有限：关键数字先截图放大或裁剪局部。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 模型不支持图像 | 视觉任务固定用 `--model` 指定视觉模型；其他模型传图前先确认其多模态构建 |
| exit 2 + model not found | `ollama pull <目标模型名>` |
| exit 2 + 无法读取图片 | 路径检查；URL 图需网络可达（Codex 命令沙箱需放行网络或先手动下载到本地再传路径） |
| 识别质量差 | 用更清晰的原图；裁剪关键区域；prompt 更具体 |
| 响应慢 | 4B 视觉模型 + 大图正常现象；把大图降到 ~1MB 再传 |
