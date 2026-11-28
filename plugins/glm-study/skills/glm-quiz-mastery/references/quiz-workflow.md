# glm-quiz-mastery — 四命令工作流与数据流（按需加载，默认不整读）

> 本文档是 SKILL.md 的操作展开。Hard rule：用 grep 定点检索本文档，不要
> 从头到尾整读（渐进披露）。

## 命令 1：generate_from_material.py — 学习资料 → 知识点

```bash
python3 ~/.codex/plugins/glm-study/skills/glm-quiz-mastery/scripts/generate_from_material.py \
    <file_path> <document_id>
```

- 支持扩展名：`.md` `.txt` `.text` `.docx` `.pdf` `.ppt` `.pptx`
  （.docx/.pptx 为纯标准库 zip+xml 解析；.pdf 走 pymupdf → macOS Quartz →
  pdftotext 可选链；.ppt 需 python-pptx，建议另存 .pptx）。
- stdout 输出 JSON：`{"action": "extract_knowledge_points", "document_id": …,
  "prompts": {"system_prompt": …, "user_prompt": …}, "instructions": …}`。
- agent 把 prompts 发给本地模型 → 得到知识点 JSON 数组
  （`id`/`title`/`definition`/`description`/`tags`）→ 写入
  `data/knowledge_points/<document_id>.json`（结构
  `{"knowledge_points": [...]}`，可直接手写或经 service 保存）。

## 命令 2：import_quiz.py — 题目文件 → 标准化题目

```bash
python3 ~/.codex/plugins/glm-study/skills/glm-quiz-mastery/scripts/import_quiz.py \
    <file_path> <document_id> <user_id>
```

- 同样的文件支持面；stdout 输出题目解析 prompt JSON。
- 模型返回题目 JSON 数组（`type`/`prompt`/`options`/`answer`/
  `explanation`/`knowledge_point_ids`/`level`）→ 后续入库走 service
  （见命令 4 的入库形态：session 文件即题目数组载体）。

## 命令 3：run_quiz.py — 按掌握度出题

```bash
python3 ~/.codex/plugins/glm-study/skills/glm-quiz-mastery/scripts/run_quiz.py \
    <user_id> <document_id> [level] [kp_id1,kp_id2,...]
```

- 无 mastery 记录的知识点强制 L1；有记录则取所选知识点 current_level 的
  最小值（保守）；显式 level 参数覆盖。
- stdout 输出出题 prompt（含题型分配表：L1 选择70/判断30；L2 选择50/填空30/
  判断20；L3 选择40/填空20/判断20/简答20；默认 3 题，上限 15）。
- 模型产出题目 JSON 后：**先问网页版**（glm-quiz-html 联动），再逐题展示。

## 命令 4：submit_answers.py — 评分与掌握度更新

```bash
python3 ~/.codex/plugins/glm-study/skills/glm-quiz-mastery/scripts/submit_answers.py \
    <user_id> <document_id> <session_id> '<answers_json>'
```

- 前置：`data/sessions/<session_id>.json` 存在（由 import_questions 入库
  创建；出题链路下 agent 也可按 QuizSession 结构自写，字段：
  `session_id`/`user_id`/`document_id`/`level`/`knowledge_point_ids`/
  `questions`/`status`）。
- 评分规则（确定性，引擎内固化）：single_choice / true_false 精确匹配；
  fill_blank 忽略大小写与首尾空白；short_answer 恒 `needs_review` 不计分。
- 掌握度更新：按知识点聚合 → 准确率 ≥0.6 升级（封顶 L3）、否则降级
  （保底 L1）；连续两次 <0.6 或本次 <0.5 → 标薄弱；连续两次 ≥0.8 解除
  薄弱；艾宾浩斯答对推进（1/2/4/7/15 天）、答错归零。
- stdout：`{"session_id", "score", "total", "accuracy",
  "needs_review_count", "results": [...]}`。

## 数据流总览

```
学习资料/题目文件 ──脚本解析──→ 提取 prompt ──本地模型──→ 知识点/题目 JSON
     │                                              │
     │                                    （问用户：网页版？）
     │                                              ├─ 要 → glm-quiz-html 生成 HTML
     │                                              └─ 否 → 对话逐题练习
     │                                              │
     ▼                                              ▼
data/knowledge_points/<doc>.json            data/sessions/<sid>.json
     ▼                                              ▼
run_quiz.py（按掌握度定难度）──→ 出题 prompt ──→ 用户答案 ──→ submit_answers.py
     ▲                                              │
     └────── data/user_progress/<user>__<doc>.json（掌握度/薄弱/艾宾浩斯）
```

## 三模型分工（Ollama）

- **主力模型**：完整链路（资料解析 → 知识点/题目生成 → 对话练习
  → 评分转述 → USER.md 同步）是长任务，且 prompt 纪律要求高，交给主力模型。
- **轻量模型**：单步转述——跑 run_quiz.py/submit_answers.py 并
  把 JSON 结果讲给用户；生成题目请切回主力模型。
- 评分、掌握度、遗忘曲线全部由脚本引擎确定性完成，任何模型都不会算错。

## 上下游插件

| 插件 | 关系 |
|---|---|
| glm-quiz-html | 下游：题目 JSON → 网页练习页（Hard rule 4：首轮必问） |
| glm-study-buddy | 上游：学习项目/计划管理；本技能只写其 USER.md 第 3 节 |
