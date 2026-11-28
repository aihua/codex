---
name: glm-auto-target-tracker
description: "Auto goal-progress tracker for Codex agents: the source skill's two external dependencies are equivalently replaced - the vlm tool for image recognition becomes a local Ollama /api/chat vision chain (images as base64, default vision model) with goal-type prompts (study/fitness/work/creative/habit), and the edit_daily note tool becomes a local Markdown goal journal (goal-journal/YYYY-MM-DD.md). Preview-by-default with --apply to write after user confirmation, JSON parse with raw fallback. 触发场景：学习打卡 / 健身记录 / 工作进度 / 创作记录 / 习惯打卡，识别图片并写入目标日记。"
metadata:
  version: "1.0.0"
---

# 自动目标进度追踪器（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-auto-target-tracker/`；本技能目录：
  `~/.codex/plugins/glm-auto-target-tracker/skills/glm-auto-target-tracker/`。
  下文 `scripts/` 指 `scripts/track.py`。
- **z-ai-web-dev-sdk / 外部工具等效替换审计结论**：源 skill（skills/
  auto-target-tracker）依赖两个外部工具——`vlm`（识别图片）与
  `edit_daily`（写入日常笔记）——本地不部署。逐项等效替换：

| 源工具调用 | 本地等效（track.py） | 说明 |
|---|---|---|
| `vlm` 工具识别图片（通用 prompt 模板） | 内置 PROMPT_HEAD（结构化 JSON：tasks/key_data/feedback） | Ollama `/api/chat` + images base64 |
| 目标类型专用 prompt（学习/健身/工作/创作/习惯） | `--type study|fitness|work|creative|habit`（auto 自动判型） | 源 prompt 表全量移植 |
| `edit_daily` 写入当日笔记 | `--journal goal-journal/2026-11-22.md` 追加条目 | 本地 Markdown 目标日记（自动建头） |
| 「反馈给用户确认再记录」流程 | 默认**预览**（stdout 打印拟记录条目），`--apply` 才落盘 | 用户确认语义保留 |
| 云端 VLM API（源隐私声明的唯一外发） | 本地 Ollama 视觉链 | 图片不出本机 |

- **模型路由**：默认 `--model` 为视觉模型；每日/每周汇总分析
  交给 glm-llm读日记文件生成。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 网络、图片或模型错误。
- 输出与日记落**用户工作目录**；插件目录只读。

## 触发条件（沿源 skill）

1. **用户发送了图片**（学习笔记、进度截图、健身记录、任务清单、创作作品等）。
2. **用户在设定的目标时间段**（如 08:30 / 10:00 / 20:00）发送了图片。
3. **用户明确说**「帮我记一下」「看下进度」「打卡」「更新一下」等。

检测时检查：图片文件名是否含目标关键词（progress/goal/task/workout/
note）；图片内容是否含目标元素（进度条、文字、代码、图表、计划表）；是否
在预定提醒时间附近；用户最近对话上下文是否涉及目标执行。

## 工作流程（沿源 skill，工具链本地化）

1. **检测图片** → 命中触发条件。
2. **调用 VLM 识别**：
   `python3 scripts/track.py <图片...> --type <类型|auto>`（预览模式）
3. **解析目标信息**：tasks 任务清单 / progress 完成度 / key_data 关键
   数据（时长、重量、字数、天数）/ feedback 执行反馈（模型输出 JSON，
   解析失败自动回退 raw 文本）。
4. **记录到目标日记**：用户确认后 `--apply` 追加到
   `goal-journal/YYYY-MM-DD.md`。
5. **反馈给用户**：预览输出即确认话术（识别结果 + 进度估算 + 建议 +
   「记录准确吗？」）。

## 记录格式（沿源 skill）

```markdown
## 20:00 打卡记录

**目标类型**: 📚 学习

**图片**: ![目标图片](notes.jpg)

**识别结果**:

| 任务/内容 | 进度/数量 | 状态 |
|---|---|---|
| 英语单词 (Unit 1) | 15 个 | 已完成 |
| 数学练习 (第3章) | 80% | 进行中 |

**关键数据**:
- 学习时长: 2小时

**备注**: 自动识别（glm-auto-target-tracker），请核对后修正
```

健身/工作/创作/习惯类型分别输出组数次数重量、完成率、完成度、连续天数
等（由 --type 的专用 prompt 决定）。

## 常见使用场景（沿源 skill）

| 场景 | 用户行为 | 识别输出 |
|---|---|---|
| 学习打卡 | 发手写笔记照片 | 知识点、学习进度、记录到学习日志 |
| 健身打卡 | 发健身记录照片 | 运动类型、组数×次数×重量、总训练量 |
| 工作进度 | 发项目进度截图 | 已完成/进行中/未开始、完成百分比 |
| 创作打卡 | 发创作作品照片 | 创作类型、关键元素、完成度 |
| 习惯打卡 | 发打卡日历截图 | 连续天数、打卡率 |

## 与目标系统的集成（本地化等效）

- **每日汇总（22:00）**：`cat goal-journal/$(date +%F).md` 交给
  glm-llm生成达成率分析与目标对比
  （`glmllm.py chat -p "汇总今日打卡并分析达成率：…" --json`）。
- **周/月报告**：读一周日记文件 → glm-llm 输出有效时长、目标覆盖、
  连续天数、动态难度调整建议（连续达标则建议提量）。
- **定时触发**：cron（如每日 22:00 提醒汇总）或 Codex 计划任务。

## Scope / Security（沿源 skill）

ONLY：识别目标相关图片并提取关键信息；记录打卡数据到本地日记文件；提供
进度反馈和建议。
NEVER：自动执行任何基于识别结果的操作；上传图片到外部服务（本地 Ollama
识别，**图片不出本机**）；访问用户未授权的图片资源；修改用户的目标计划。

## 注意事项（沿源 skill）

1. **隐私**：图片与识别结果仅本地（Ollama 视觉链在本机）。
2. **准确性**：识别内容仅供参考，字迹模糊/图质差可能偏差。
3. **及时确认**：记录后请及时核对，有偏差手动改日记文件。
4. **目标类型**：自动判型可能出错，可用 `--type` 强制。
5. **进度估算**：百分比为估算值，建议定期手动校准。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 模型不支持图像 | 视觉任务固定 `--model` 为视觉模型 |
| exit 2 + model not found | `ollama pull <目标模型名>` |
| 识别结果偏差大 | 更清晰原图；`--type` 指定类型；关键数字裁剪放大再拍 |
| JSON 解析失败 | 自动回退 raw；重试一次通常恢复 |
| 日记写错位置 | `--journal <目录>` 指定；默认 ./goal-journal |
| 误落盘 | 预览是默认模式；--apply 前先看 stdout |
