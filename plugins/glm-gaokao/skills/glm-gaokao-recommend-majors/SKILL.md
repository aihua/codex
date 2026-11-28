---
name: glm-gaokao-recommend-majors
description: "高考志愿推荐流水线第三步（纯 Agent 分析，无规则脚本）：基于考生画像与 API 志愿列表，分析推荐适合的专业方向、就业出口与具体专业清单，输出结构化 major_recommendation.json，并用 check_recommendation.py 校验推荐条目与 parsed.json 字段完全一致（硬性约束）。适用于高考专业推荐、选专业、就业方向分析。触发场景：推荐专业 / 选什么专业 / 高考专业推荐 / 就业方向分析 / 专业志愿怎么挑。"
metadata:
  version: "1.0.0"
---

# 推荐专业与就业方向

本 Skill 是流水线的**第三步**：纯 Agent 分析，无规则脚本。结合考生兴趣、成绩、就业意向与 `parsed.json` 中的真实专业，产出个性化专业推荐。

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-gaokao-recommend-majors/`
- 本技能目录：`~/.codex/plugins/glm-gaokao-recommend-majors/skills/glm-gaokao-recommend-majors/`
- 下文 `references/`、`examples/`、`scripts/` 均指该技能目录内的子目录；`major_recommendation.json` 等运行产物落在**用户工作目录** `output/`，插件目录只读。
- **零 SDK / 零网络**：本技能为纯 Agent 分析 + 本地一致性校验器（`scripts/check_recommendation.py`，纯 Python 标准库），无 LLM SDK、无厂商 web-dev SDK、无 API key、无网络出口。
- **流水线上下游为同门姊妹插件**（各自独立安装，未装齐时只要有输入文件仍可单独跑本步）：
  - 上游 Step1/2：glm-gaokao-collect-student-info（`student.json`）、glm-gaokao-fetch-volunteers（`parsed.json`）
  - 下游 Step4：glm-gaokao-recommend-schools 读取本步 `major_recommendation.json`；Step5：glm-gaokao-generate-report 合并渲染
- 轻量模型产出后**必须跑校验器**——字段漂移（院校名/代码与 parsed.json 不一致）是小模型高发错误，校验器会逐条拦出。

## 上下游

- **上游**：`student.json` + `parsed.json`（来自 glm-gaokao-collect-student-info、glm-gaokao-fetch-volunteers 插件）
- **下游**：glm-gaokao-recommend-schools 插件（Step4）读取 `major_recommendation.json`

## 输入

1. `student.json` — 考生完整画像
2. `parsed.json` — 冲/稳/保志愿及每校 `majors`（含 `claim` 选科要求、录取概率）

## Agent 分析任务

1. 阅读 `references/career-reference.md` 了解常见专业大类与就业出口（**参考，非硬规则**）。
2. 综合选科要求、各科成绩、兴趣、家庭、就业方向，判断 2–4 个**专业方向**（`major_directions`）。
3. 从 `parsed.json` 中挑选 **8–15 个**最契合的具体专业，写入 `recommended_majors`。
4. 撰写综合开篇 `intro` 与整体策略 `strategy`（专业优先视角）。

## 硬性约束

`recommended_majors` 每项的 `university_name`、`university_code`、`major_name`、`major_code` 必须与 `parsed.json` **完全一致**，否则最终报告无法显示 🔥 标签。

生成前在 `parsed.json` 中检索确认字段值；生成后**必跑本地校验器**：

```bash
python3 ~/.codex/plugins/glm-gaokao-recommend-majors/skills/glm-gaokao-recommend-majors/scripts/check_recommendation.py \
  --parsed output/parsed.json \
  --recommendation output/major_recommendation.json
```

exit 0 才算通过；出现 `MISMATCH` 条目时回到 `parsed.json` 核对该条目的准确字段值后修正重跑。

## 输出

保存为 `output/major_recommendation.json`（用户工作目录，绝对路径交付），结构见 `examples/major_recommendation_template.json`。

```json
{
  "student": { "...辅助画像字段..." },
  "intro": "综合测评开篇（HTML 可用 <strong>）",
  "strategy": "填报策略（专业视角）",
  "major_directions": [
    { "icon": "🧑‍💻", "title": "...", "match_level": "极高", "description": "..." }
  ],
  "recommended_majors": [
    {
      "major_name": "...",
      "major_code": "...",
      "university_name": "...",
      "university_code": "...",
      "modal": { "title": "...", "body": "<h4>...</h4><ul>...</ul>" }
    }
  ]
}
```

## 向用户交付

- 保存 JSON 绝对路径
- 用自然语言解读推荐的专业方向与 Top 专业理由

## 附加资源

- `references/career-reference.md` — 专业/职业方向参考（分析维度、常见专业大类与就业出口、城市产业表）
- `scripts/check_recommendation.py` — 推荐条目与 parsed.json 一致性校验（硬性约束拦截器）
