---
name: glm-gaokao-generate-report
description: "高考志愿推荐流水线第五步：合并考生信息、志愿列表、专业推荐与院校推荐，生成融合分析与冲稳保志愿列表的 HTML 志愿填报报告（Jinja2 模板渲染，模板内嵌，离线生成）。merge_analysis.py 纯标准库；generate_html.py 唯一第三方依赖 jinja2 可经 uv 免安装直跑（uv run --with jinja2）。适用于高考志愿报告生成、志愿填报方案输出、志愿表可视化。触发场景：生成志愿填报报告 / 志愿表可视化 / 出一份 HTML 志愿报告 / 高考志愿方案输出。"
metadata:
  version: "1.0.0"
---

# 生成志愿填报报告

本 Skill 是流水线的**第五步**：合并前序 JSON，渲染 HTML 报告。

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-gaokao-generate-report/`
- 本技能目录：`~/.codex/plugins/glm-gaokao-generate-report/skills/glm-gaokao-generate-report/`
- 下文 `references/`、`examples/`、`scripts/`、`templates/` 均指该技能目录内的子目录；`analysis.json`、`volunteer_report.html` 等运行产物落在**用户工作目录** `output/`，插件目录只读。
- **零 SDK / 零网络**：无 LLM SDK、无厂商 web-dev SDK、无 API key、无网络出口——报告在本地离线生成。
- **依赖等效替换（源 skill → 本插件）**：源 skill 的环境准备是 `python3 -m venv .venv && pip install -r requirements.txt`（requests + jinja2）。插件形态改造结论：requests 实际未被脚本使用，**移除**；jinja2 为 generate_html.py 真实依赖，改为**免安装直跑**形态（用户 macOS 上 uv 在 PATH）：
  - 首选：`uv run --with jinja2 python3 scripts/generate_html.py ...`（uv 临时环境注入 jinja2，不留全局包）
  - 或一次性安装：`pip install jinja2` / `uv pip install --system jinja2`
  - 未装 jinja2 直接运行时，脚本会以 exit 2 打印上述两条命令提示（不会裸抛 ImportError）
- **流水线上下游为同门姊妹插件**（各自独立安装，未装齐时只要有输入文件仍可单独跑本步）：
  - 上游 Step2/3/4：glm-gaokao-fetch-volunteers（`parsed.json`）、glm-gaokao-recommend-majors（`major_recommendation.json`）、glm-gaokao-recommend-schools（`school_recommendation.json`）
- **合并前检查发现字段不匹配时**，回到对应姊妹插件修正其 JSON，再重跑本步。

## 上下游

- **上游**：
  - `parsed.json`（志愿列表，glm-gaokao-fetch-volunteers 插件）
  - `major_recommendation.json`（专业推荐，glm-gaokao-recommend-majors 插件）
  - `school_recommendation.json`（院校推荐，glm-gaokao-recommend-schools 插件）
- **输出**：`volunteer_report.html`

## 执行步骤

### 1. 合并为 analysis.json

```bash
python3 ~/.codex/plugins/glm-gaokao-generate-report/skills/glm-gaokao-generate-report/scripts/merge_analysis.py \
  --majors output/major_recommendation.json \
  --schools output/school_recommendation.json \
  -o output/analysis.json
```

`merge_analysis.py` 将专业推荐与院校推荐合并为 `generate_html.py` 所需的 `analysis.json` 结构（纯标准库，无需任何安装）。

### 2. 生成 HTML

```bash
# 首选：uv 免安装直跑（jinja2 唯一第三方依赖）
uv run --with jinja2 python3 ~/.codex/plugins/glm-gaokao-generate-report/skills/glm-gaokao-generate-report/scripts/generate_html.py \
  -i output/parsed.json \
  -a output/analysis.json \
  -o output/volunteer_report.html

# 或：已 pip/uv 安装过 jinja2 时直接跑
python3 ~/.codex/plugins/glm-gaokao-generate-report/skills/glm-gaokao-generate-report/scripts/generate_html.py \
  -i output/parsed.json \
  -a output/analysis.json \
  -o output/volunteer_report.html
```

模板已内嵌于插件（`templates/volunteer_report.html`），默认自动加载，无需 `-t`。

### 3. 交付用户

提供 `volunteer_report.html` 的**绝对路径**，并简要说明报告结构：

1. **综合测评与建议**（专业方向 + 院校策略）
2. **志愿推荐列表**（冲/稳/保，⭐ 推荐学校 / 🔥 推荐专业可点击查看详情）

## 合并前检查

| 检查项 | 说明 |
|--------|------|
| 专业字段一致 | `recommended_majors` 的 name/code 与 `parsed.json` 一致（上游插件自带 check_recommendation.py 校验器） |
| 院校字段一致 | `recommended_schools` 的 name/code 与 `parsed.json` 一致（同上） |
| 文案完整 | `intro`、`strategy`、`school_strategy` 非空 |

若合并前发现推荐字段不匹配，应回到对应姊妹插件修正 JSON。

## 附加资源

- `examples/analysis_merged_example.json` — 合并后的完整结构示例
- `templates/volunteer_report.html` — Jinja2 报告模板（内嵌，含冲稳保分组/推荐标签/详情弹窗样式）
