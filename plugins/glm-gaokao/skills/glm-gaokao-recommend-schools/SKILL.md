---
name: glm-gaokao-recommend-schools
description: "高考志愿推荐流水线第四步（纯 Agent 分析，无规则脚本）：基于推荐专业列表、考生画像与志愿列表，由 Agent 分析推荐院校并给出个性化理由（地域优势/院校层次/专业契合/录取性价比），输出结构化 school_recommendation.json，并用 check_recommendation.py 校验推荐条目与 parsed.json 字段完全一致（硬性约束）。适用于高考院校推荐、选大学、冲稳保院校布局。触发场景：推荐院校 / 选大学 / 高考院校推荐 / 冲稳保院校布局 / 怎么排志愿梯度。"
metadata:
  version: "1.0.0"
---

# 推荐院校与理由

本 Skill 是流水线的**第四步**：在已确定专业方向的基础上，从 `parsed.json` 中推荐院校并说明理由。

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-gaokao-recommend-schools/`
- 本技能目录：`~/.codex/plugins/glm-gaokao-recommend-schools/skills/glm-gaokao-recommend-schools/`
- 下文 `references/`、`examples/`、`scripts/` 均指该技能目录内的子目录；`school_recommendation.json` 等运行产物落在**用户工作目录** `output/`，插件目录只读。
- **零 SDK / 零网络**：本技能为纯 Agent 分析 + 本地一致性校验器（`scripts/check_recommendation.py`，纯 Python 标准库），无 LLM SDK、无厂商 web-dev SDK、无 API key、无网络出口。
- **流水线上下游为同门姊妹插件**（各自独立安装，未装齐时只要有输入文件仍可单独跑本步）：
  - 上游 Step1/2/3：glm-gaokao-collect-student-info（`student.json`）、glm-gaokao-fetch-volunteers（`parsed.json`）、glm-gaokao-recommend-majors（`major_recommendation.json`）
  - 下游 Step5：glm-gaokao-generate-report 合并渲染
- 轻量模型产出后**必须跑校验器**——院校名/代码与 parsed.json 不一致是小模型高发错误，校验器会逐条拦出。

## 上下游

- **上游**：`student.json` + `parsed.json` + `major_recommendation.json`（来自 glm-gaokao-collect-student-info、glm-gaokao-fetch-volunteers、glm-gaokao-recommend-majors 插件）
- **下游**：glm-gaokao-generate-report 插件（Step5）

## 输入

1. `student.json` — 意向城市、家庭、就业方向等
2. `parsed.json` — 院校标签、城市、冲稳保档位、录取概率
3. `major_recommendation.json` — 已推荐专业及方向，用于判断院校专业契合度

## Agent 分析任务

1. 优先推荐**包含已推荐专业**或**优势学科与专业方向契合**的院校。
2. 结合 `preferred_cities`、城市产业机会（可参考 `references/career-reference.md` 城市表）、院校层次（985/211/双一流等）。
3. 兼顾冲/稳/保布局：核心目标放稳档，冲顶名校与保底院校均需有代表。
4. 挑选 **6–12 所**院校，每所撰写个性化 `modal` 推荐理由。

## 推荐理由应覆盖

- **地域优势**：城市产业与实习就业资源
- **院校层次**：标签与社会认可度
- **专业契合**：与 `major_recommendation.json` 的关联
- **录取性价比**：档位与概率是否匹配考生诉求

## 硬性约束

`recommended_schools` 每项的 `university_name`、`university_code` 必须与 `parsed.json` **完全一致**。

生成前在 `parsed.json` 中检索确认字段值；生成后**必跑本地校验器**：

```bash
python3 ~/.codex/plugins/glm-gaokao-recommend-schools/skills/glm-gaokao-recommend-schools/scripts/check_recommendation.py \
  --parsed output/parsed.json \
  --recommendation output/school_recommendation.json
```

exit 0 才算通过；出现 `MISMATCH` 条目时回到 `parsed.json` 核对该条目的准确字段值后修正重跑。

## 输出

保存为 `output/school_recommendation.json`（用户工作目录，绝对路径交付），结构见 `examples/school_recommendation_template.json`。

```json
{
  "school_strategy": "院校布局策略（冲/稳/保如何分配）",
  "recommended_schools": [
    {
      "university_name": "...",
      "university_code": "...",
      "modal": {
        "title": "学校推荐原因：...",
        "body": "<h4>推荐原因</h4><ul><li>...</li></ul>"
      }
    }
  ]
}
```

## 向用户交付

- 保存 JSON 绝对路径
- 用自然语言解读院校推荐逻辑与梯度布局

## 附加资源

- `references/career-reference.md` — 城市产业与院校层次参考（分析维度、常见专业大类、城市产业表、院校层次速查）
- `scripts/check_recommendation.py` — 推荐条目与 parsed.json 一致性校验（硬性约束拦截器）
