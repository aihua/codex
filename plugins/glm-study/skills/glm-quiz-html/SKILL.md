---
name: glm-quiz-html
description: "把题目数组生成一个可独立运行的网页练习页（单文件 HTML）。当完成 glm-quiz-mastery 的「从资料出题」或「从文件提取题目」流程后，应主动询问是否需要\"在网页里练习\"，确认后调用本技能把题目注入模板生成 HTML 给用户。也支持用户直接说\"把这些题做成网页/HTML/练习页\"、\"做个HTML练习页\"、\"生成题库网页\"、\"在浏览器里练\"、\"导出HTML\"时触发。不处理：出题（→ glm-quiz-mastery）、评分（→ glm-quiz-mastery）、长期复习计划（→ glm-study-buddy）。"
metadata:
  version: "1.0.0"
---

# 网页题库生成器 (Quiz HTML Builder)

把一组题目 JSON → 一个**单文件 HTML 练习网页**，包含：
- 📂 分类筛选（学科 / 子模块）+ 学习状态筛选（已掌握 / 未做 / 错题）
- 🎯 4 种题型支持：选择 / 判断 / 填空 / 简答
- 🤖 答题自动标记，错题自动归入错题本（首次错误给一次重试机会）
- ⌨️ 完整键盘快捷键（A/B/C/D · Enter · 方向键 · Space）
- 📝 模拟考模式（限时 + 一次性提交 + 成绩页）
- 🌓 明暗主题切换 · localStorage 持久化 · 移动端适配

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-study/`
- 本技能目录：`~/.codex/plugins/glm-study/skills/glm-quiz-html/`
- 下文 `scripts/`、`templates/` 均指该技能目录内的子目录。
- 生成器脚本为**纯 Python 标准库**实现（argparse/json/re/time/webbrowser/pathlib），无任何
  SDK、无网络请求、无 pip 依赖；模板 HTML 自包含（无 CDN、无外部脚本）。
- 用户练习数据（答题状态、错题本、主题偏好）持久化在**生成的 HTML 网页内的
  localStorage**（浏览器本地），与插件目录无关。
- 输出 HTML 写到**用户工作目录**（Codex 启动 cwd，如 `~/Desktop/`），插件目录只读。

## 核心触发场景

### 场景 1：glm-quiz-mastery 出题/导入完成后主动询问 ⭐
这是本技能的**主要入口**。当 `glm-quiz-mastery` 完成以下任一流程：
- 「从资料出题」：`generate_from_material.py` → 生成题目 JSON → `service.import_questions()` 入库
- 「从题目文件提取」：`import_quiz.py` → 解析出题目 JSON → 入库

glm-quiz-mastery 出题完成、向用户展示题目前，**主动问一句**：
> "题目准备好啦～ 要不要我把它们生成一个网页练习页？你可以在浏览器里慢慢做，错题会自动记下来，还能切换主题、模拟考试 🎯"

用户说"要 / 好 / 生成网页 / 来一个 / 嗯"任一肯定意思 → 调用本技能。
用户说"不用 / 算了 / 直接在这里做" → 走原本的对话练习流程。

### 场景 2：用户直接要求生成网页
触发关键词：
- "把这些题做成网页"、"做个 HTML 练习页"、"生成一个题库网页"
- "我想在浏览器里练"、"做个网页版"
- "把题目导出成 HTML"

## 调用方式

### 一句话总结
```bash
python3 ~/.codex/plugins/glm-study/skills/glm-quiz-html/scripts/build_quiz_html.py <题目JSON文件> [--title "..." --open]
```

### 标准流程

1. **拿到题目 JSON**（数组，每项是一道题）
   - 来源 A：glm-quiz-mastery 出题后的 LLM 输出（系统已是标准格式）
   - 来源 B：用户直接粘贴的题目数组
   - 来源 C：从数据库读取的题目（glm-quiz-mastery 的
     `~/.codex/plugins/glm-study/skills/glm-quiz-mastery/data/sessions/<sid>/questions.json`）

2. **写到临时 JSON 文件**：
   ```python
   import json, tempfile
   from pathlib import Path
   tmp = Path(tempfile.mkdtemp()) / "questions.json"
   tmp.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")
   ```

3. **调用脚本**：
   ```bash
   python3 ~/.codex/plugins/glm-study/skills/glm-quiz-html/scripts/build_quiz_html.py \
       /tmp/xxx/questions.json \
       --title "📚 物理 · 热学练习" \
       --output ~/Desktop/quiz_物理热学_20260518.html \
       --open
   ```

4. **解析返回 JSON**：
   ```json
   {
     "success": true,
     "output_path": "/Users/.../quiz_xxx.html",
     "question_count": 8,
     "title": "📚 物理 · 热学练习",
     "subtitle": "共 8 题 · 选择×5 · 判断×2 · 填空×1 · 物理",
     "id": "q_1779091201",
     "size_bytes": 63752
   }
   ```

5. **告诉用户**：把 HTML 路径报给用户，提示「已经在浏览器打开了，可以开始练啦 ✨」

## 题目 JSON 字段标准

完全兼容 glm-quiz-mastery 输出格式，**新增可选字段** `category` / `memory_tip`：

| 字段 | 必填 | 说明 |
|---|---|---|
| `type` | ✅ | `single_choice` / `true_false` / `fill_blank` / `short_answer` |
| `prompt` | ✅ | 题干。也兼容 `question` 字段（自动转换） |
| `options` | 选择题必填 | `["A. xxx", "B. yyy", ...]` |
| `answer` | ✅ | 选择题填字母；判断题填 `"True"`/`"False"`；填空/简答填文本 |
| `explanation` | 推荐 | 解析（强烈建议填，K12 学生需要） |
| `knowledge_point` | 推荐 | 知识点名（侧边栏二级分组用） |
| `category` | 推荐 | 分类路径，**用"学科 / 子模块"格式**：`"物理 / 电学"`、`"数学 / 分数"` |
| `level` | 可选 | 难度 1-3 |
| `memory_tip` | 可选 | 记忆口诀，会用橙色卡片高亮显示（K12 神器） |

### 示例
```json
[
  {
    "type": "single_choice",
    "prompt": "下列关于并联电路电流规律的说法，正确的是（    ）。",
    "options": [
      "A. 干路电流等于各支路电流之差",
      "B. 干路电流等于各支路电流之和",
      "C. 各支路电流相等",
      "D. 干路电流大于任一支路电流的两倍"
    ],
    "answer": "B",
    "explanation": "并联电路中，**干路电流等于各支路电流之和**：I = I₁ + I₂ + ...",
    "knowledge_point": "并联电路电流规律",
    "category": "物理 / 电学",
    "level": 1,
    "memory_tip": "🧠 并联看路口：进多少、出多少，电流不会消失"
  }
]
```

## 设计原则

### 1. 自动 category，让筛选有意义
如果题目缺 `category` 字段，最好补上（哪怕基于学科推断）。否则所有题都堆到"通用"分类下，分类筛选就废了。

### 2. category 用"学科 / 子模块"
- ✅ `"物理 / 电学"`、`"物理 / 热学"` → 顶部出 4 个细分类 chip
- ❌ `"物理"` → 只出 1 个，子模块在侧栏体现，但筛选粒度变粗

### 3. 知识点和分类不是同一层
- `category` = 横向分类（哪个学科/章节），用于**顶部 chips 筛选**
- `knowledge_point` = 细粒度知识点，用于**左侧栏二级分组**

### 4. 输出文件命名
默认输出到题目 JSON 同目录，文件名 `quiz_<title_slug>_<时间戳>.html`。
**建议显式传 `--output`**，放到 `~/Desktop/` 或一个固定目录方便用户找。

## Hard Rules

1. **生成必须走脚本**：题目 → 网页一律调用
   `python3 ~/.codex/plugins/glm-study/skills/glm-quiz-html/scripts/build_quiz_html.py`，
   不得手写 HTML 或心算拼模板。
2. **退出码纪律**：`0` 成功；`1` 参数/文件/模板问题；`2` JSON 或题目数据非法。
   exit 2 时必须把 stderr 里被跳过的题目逐条转告用户（第几题、缺什么字段）。
3. **模板占位符不手改**：`{{TITLE}}` / `{{SUBTITLE}}` / `{{QUIZ_DATA}}` / `{{META}}`
   由脚本注入；模型不得直接编辑 `templates/quiz_template.html`。
4. **输出落在用户目录**：生成的 HTML 写到用户指定路径（推荐 `~/Desktop/`），
   永不写入插件安装目录。
5. **先问后做**：由 glm-quiz-mastery 链路进入时，先询问用户是否要网页版，
   得到肯定答复再调用（见「核心触发场景」）。
6. **评分边界**：网页里的答题状态仅供用户自查；正式 mastery 数据由
   glm-quiz-mastery 的 `submit_answers.py` 写入，两者并行不冲突。

## 工作示例（glm-quiz-mastery 衔接全流程）

```python
# 1. glm-quiz-mastery 已完成出题，拿到题目数组
questions = [
    {"type": "single_choice", "prompt": "...", "options": [...], "answer": "A",
     "explanation": "...", "knowledge_point": "...", "category": "物理 / 电学"},
    # ...
]

# 2. agent 问用户："要不要做成网页版？"
# 3. 用户："要"
# 4. agent 写临时文件 + 调用技能

import json, subprocess, tempfile
from pathlib import Path

tmp_dir = Path(tempfile.mkdtemp(prefix="quiz_"))
qjson = tmp_dir / "questions.json"
qjson.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")

output = Path.home() / "Desktop" / "quiz_物理电学.html"

result = subprocess.run([
    "python3",
    str(Path.home() / ".codex/plugins/glm-quiz-html/skills/glm-quiz-html/scripts/build_quiz_html.py"),
    str(qjson),
    "--title", "📚 物理 · 电学练习",
    "--output", str(output),
    "--open",
], capture_output=True, text=True)

info = json.loads(result.stdout)
# info["output_path"] = "/Users/.../Desktop/quiz_物理电学.html"
```

然后告诉用户：
> 「已经做好啦～ 网页已自动打开 ✨
> 路径：`~/Desktop/quiz_物理电学.html`
> 慢慢做，做完会自动记录错题，下次可以筛"错题"专门攻克 💪」

## 与其他技能的边界

| 任务 | 用谁 |
|---|---|
| 从资料出题 | **glm-quiz-mastery** |
| 从文件提取题目 | **glm-quiz-mastery** |
| 评分、掌握度追踪、艾宾浩斯安排 | **glm-quiz-mastery** |
| 把题目做成网页给用户在浏览器练 | **glm-quiz-html**（本技能） |
| 学习计划、长期跟进 | **glm-study-buddy** |

## 失败处理

- `exit 1`：参数错误 / 文件不存在 / 模板缺失 → 报错给用户，让用户检查路径
- `exit 2`：JSON 格式问题 / 题目数据非法 → 告诉用户哪几题被跳过，提示检查字段
- 部分题被 skip 但有合法题：仍会成功生成，但 stderr 会列出被跳过的题，需要在回复里告知用户「跳过了 N 题，原因 XXX」
