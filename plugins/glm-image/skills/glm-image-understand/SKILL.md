---
name: glm-image-understand
description: "Local static image understanding for Codex agents: the source image-understand skill's z-ai-web-dev-sdk createVision() calls and `z-ai vision` CLI are equivalently replaced by glmimgund.py over the local Ollama /api/chat endpoint (images as base64, default vision model) with task-oriented templates - OCR, classification/tagging, alt-text, object inventory, quality assessment, multi-image diff and custom prompts - each with structured JSON output. 触发场景：图片分析 / OCR 文字提取 / 对象识别计数 / 图片分类打标 / alt 无障碍文本 / 质量评估 / 多图差异。"
metadata:
  version: "1.0.0"
---

# Image Understanding Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-image/`；本技能目录：
  `~/.codex/plugins/glm-image/skills/glm-image-understand/`。下文
  `scripts/` 指 `scripts/glmimgund.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill（skills/image-understand）
  的静态图分析全走云端 `zai.chat.completions.createVision()`（`z-ai vision`
  CLI 同源）——本地不部署。等效替换为**本地 Ollama /api/chat 任务模板 CLI**：

| 源 SDK / CLI 用法 | 本地等效（glmimgund.py） | 说明 |
|---|---|---|
| `z-ai vision -p "What's in this image?" -i x.jpg` | `glmimgund.py custom -p "…" -i x.jpg` | 自定义问题（plain 输出） |
| OCR 场景（extractText） | `glmimgund.py ocr -i doc.png` | 专用模板：保留版面、□标疑难字 |
| 分类打标（classifyImage） | `glmimgund.py classify -i x.jpg --json` | main_subject/key_objects/scene/tags 结构化 |
| alt 无障碍文本 | `glmimgund.py alttext -i banner.png` | 40 字内中文 alt 文本 |
| 对象检测与计数 | `glmimgund.py objects -i shelf.jpg` | name/count/detail 结构化清单 |
| 质量评估 | `glmimgund.py quality -i photo.jpg` | 清晰度/曝光/构图/色彩/缺陷 |
| 多图对比 | `glmimgund.py diff -i a.png -i b.png` | 区域级 differences 结构 |
| `-o out.json` | `-o out.json` | JSON 落盘 |
| base64 传输（源推荐做法） | CLI 内部一律 base64 | 与源 skill 建议一致 |

- **模型路由**：默认 `--model` 为视觉模型（多模态档）；其他本地模型是否吃图取决于构建，报错时回到视觉模型。
- JSON 任务的模型输出经宽松解析（剥出首个 JSON 对象）；解析失败附
  `parse_warning` + `raw`，不假死。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 网络、图片或模型错误。
- 输出落**用户工作目录**；插件目录只读。
- **技能路由**：视觉多轮「对话」→ glm-multimodal 插件中的 glm-vlm 技能（若已安装）；图片素材检索 →
  glm-image-search；确定性编辑 → glm-image-edit；程序化生图 →
  glm-image-generation。

---

## Core Capabilities（沿源 skill）

- Image description & scene understanding（custom 任务）
- OCR 与版面保留式文字提取（ocr 任务）
- Object detection & recognition + 计数（objects 任务）
- Image classification & categorization（classify 任务）
- Quality assessment（quality 任务）
- Accessibility alt text 生成（alttext 任务）
- 多图差异对比（diff 任务）

## 常用工作流

1. **票据/表单 OCR**：`python3 scripts/glmimgund.py ocr -i receipt.jpg`
   → 文本交给 glm-llm 提取字段做结构化（`glmllm.py chat -p "从此票据提取金额/日期…" --json`）。
2. **电商图打标**：`glmimgund.py classify -i product.png --json -o tags.json`
3. **无障碍改造**：批量 `alttext` 为页面插图生成 alt 文本。
4. **库存/货架盘点**：`glmimgund.py objects -i shelf.jpg` 得对象计数清单。
5. **投稿/质检**：`glmimgund.py quality -i shot.jpg` 快筛不合格图。
6. **前后对比**：`glmimgund.py diff -i before.png -i after.png --json`。

## 图片质量建议（沿源 skill）

- PNG 适合截图/图表/含透明图；JPEG 适合照片；GIF/WebP/BMP 均可。
- 高分辨率有益识别；>20MB 先压缩（`GLM_IMGUND_MAX_IMAGE_MB` 可调）。
- 关键小字先裁剪局部再 OCR（4B 视觉档对小字较吃力）。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 模型不支持图像 | 固定 `--model` 为视觉模型 |
| exit 2 + model not found | `ollama pull <目标模型名>` |
| OCR 漏字/错字 | 裁剪放大局部、换清晰原图；轻量档极限，可分块识别 |
| classify 输出非严格 JSON | 内置宽松解析已兜底；仍乱则 --json 关掉取 raw |
| exit 2 + 无法读取图片 | 路径检查；URL 需网络可达（Codex 沙箱禁网时先下载到本地） |
| 响应慢 | 大图压到 ~1MB；4B 推理有正常延迟 |
