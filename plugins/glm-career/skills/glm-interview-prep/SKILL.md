---
name: glm-interview-prep
description: "帮用户准备面试。基于目标 JD、公司、岗位方向，生成\"高频面试题 + 参考回答 + 行为面 / 技术面 / Case 面分类题库\"，并产出可打印的『面试备战手册』。当用户说\"帮我准备面试\"\"明天有面试 / 后天面试\"\"面试题\"\"面经\"\"模拟面试\"\"我要面 X 公司 Y 岗位\"\"帮我准备 STAR 故事\"\"怎么回答这道面试题\"\"自我介绍 / 离职原因 / 优缺点 怎么答\"，必须触发本 skill。请勿用本 skill 改简历（去 glm-jd-resume-tailor / glm-resume-builder 插件）或推荐方向（去 glm-job-intent-tracker 插件）。 结构化提问、JD 拆解与 docx 手册导出的宿主工具以本地等效替换（分轮提问 / glm-jd-resume-tailor 的 parse_jd.py / pandoc 或 python-docx，见 SKILL.md 部署节）；脚本 star_story_builder.py 纯标准库本地运行，产物落在用户工作目录。"
metadata:
  version: "1.0.0"
---

# Interview Prep（面试准备）

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-career/`
- 本技能目录：`~/.codex/plugins/glm-career/skills/glm-interview-prep/`
- 下文 `references/`、`scripts/` 均指该技能目录内的子目录。
- **参考资料按需打开**：九份题库 / 框架文档（behavioral.md / technical.md /
  case.md / hr_round.md / role_internet.md / role_tech.md / role_finance.md /
  answer_frameworks.md / salary_negotiation.md）按轮次与方向取用——
  小上下文模型默认只读本轮需要的 1~2 份，其余不整读。
- **宿主形态等效替换**：
  - 宿主结构化提问工具 → Codex 会话直接分轮提问（2~3 轮、每轮 2~3 问，
    节奏纪律不变）。
  - 源技能引用的 jd-resume-tailor 的 parse_jd.py → glm-jd-resume-tailor
    插件（同批交付；未安装时手工拆 JD 关键信息）。
  - 宿主 docx skill 出 .docx 手册 → 本地等效：md 手册为主体；需要 .docx 时
    `pandoc interview_prep.md -o interview_prep.docx` 或 python-docx
    （`uv run --with python-docx`）；.pdf 走
    `soffice --headless --convert-to pdf`。均不可用时交付 md 精简版。
- **运行产物**：故事矩阵 / 参考回答 / 备战手册均落在**用户工作目录**
  （Codex 启动 cwd），插件目录只读。
- 依赖口径：star_story_builder.py **纯标准库**（.docx 简历输入可选
  python-docx，缺失时 exit 1 + uv 安装提示；粘贴文本与 md/txt 不受影响）。

干 4 件事：

1. **拆解面试场景**：明确目标公司 / 岗位 / 面试轮次（一面 / 二面 / 终面 / HR 面）
2. **生成题库**：从 4 类题库（行为面、技术面、Case 面、岗位特定）中按需取题
3. **生成参考回答**：用 STAR / SCQA / MECE 等框架，结合用户简历事实
4. **产出"备战手册"**：一份可打印的 .md / .docx / .pdf，含题目 + 参考思路 + 自检清单

---

## 何时触发

强信号：
- "帮我准备面试 / 模拟面试 / 模面"
- "明天 / 下周面试"
- 提到了具体公司 + 岗位
- "高频面试题 / 经典面试题"
- "怎么回答 ___ 这个问题"
- "自我介绍怎么说 / 离职原因怎么答 / 期望薪资怎么谈"

弱信号（先确认）：
- 只说"想了解一下面试" → 问是哪个方向 / 什么轮次

---

## 工作流

### Step 1: 锁定面试场景

分 2~3 轮在会话里直接提问收集（每轮 2~3 问，不打问卷轰炸）：
- 目标公司（具体名字 / 大厂 vs 创业 vs 外资 / 公司类型）
- 目标岗位（精确到方向，如"用户增长 PM"而不是"产品经理"）
- 面试轮次（一面 / 二面 / 终面 / HR 面 / 全流程演练）
- 时间紧迫度（明天 / 这周 / 下周以上）—— 影响"广度 vs 深度"
- 用户已有材料（JD / 简历 / 公司公开信息 / 已知面试官背景）

如果用户给了 JD 和简历，先调用 glm-jd-resume-tailor 插件的 parse_jd.py 抽出岗位关键信息，避免重复拆（同批交付；未安装时手工拆 JD 关键信息）。

### Step 2: 选题策略

按"轮次 + 方向 + 时间"决定题库结构。读取对应文件：

- 行为面（任何轮次都会问）→ `references/behavioral.md`
- 技术面（技术 / 数据岗主战场）→ `references/technical.md`
- Case 面（咨询 / 战略 / 高级 PM）→ `references/case.md`
- HR 面（任何岗位的最后一公里）→ `references/hr_round.md`
- 岗位特定题库：
  - 互联网产品 / 运营 / PM → `references/role_internet.md`
  - 技术 / 研发 / 数据 → `references/role_tech.md`
  - 金融 / 咨询 / 商科 → `references/role_finance.md`

题量推荐：
- **明天就面**：每类 5~8 题，重点高频题
- **3~7 天**：每类 10~15 题
- **>1 周**：完整覆盖 + 模拟轮次

### Step 3: 生成参考回答

**关键原则：参考回答必须基于用户简历里的真实经历，不是泛答。**

调用 `scripts/star_story_builder.py`（如果有简历）：

```bash
python3 ~/.codex/plugins/glm-career/skills/glm-interview-prep/scripts/star_story_builder.py \
    --resume resume.md --out answers.md
```

或者，如果没有简历，用通用回答框架（从 references/answer_frameworks.md 读取）作为模板，让用户填空。

参考回答的格式：
```
【题目】___
【考察点】HR / 面试官想看你的什么能力
【回答框架】STAR / SCQA / MECE / 5W1H 之一
【建议长度】X 分钟（一般 1.5~3 分钟）
【参考回答 (基于你简历里的 ___ 经历)】
  S: 当时的背景 / 问题
  T: 你的任务 / 目标
  A: 你的具体动作（重点，要细节）
  R: 量化结果 + reflect
【可能的追问】1. ___ 2. ___ 3. ___
```

### Step 4: 产出"备战手册"

按下列结构生成手册（md 为主体；.docx 经 pandoc / python-docx 转出，见 Codex Deployment Notes），文件名 `interview_prep_<公司>_<岗位>`：

```
封面：公司 + 岗位 + 面试日期 + 倒计时
1. 公司 / 岗位 速览（1 页）
2. 自我介绍（中 + 英两版，针对该岗位定制）
3. 行为面题库（X 题）+ 参考回答
4. 技术面 / Case 面 题库（X 题）+ 参考思路
5. 反向提问清单（你向面试官问什么）
6. 薪资谈判脚本
7. 面试当天 Checklist（路线 / 着装 / 物品 / 心态）
```

**同时输出一份精简版 .md**，方便用户在地铁里 / 路上 review。

### Step 5: 模拟面试（可选 - 用户主动要才做）

如果用户说"模拟一下"，进入互动模式：
- 一次问 1 题
- 等用户回答（语音 / 文字）
- 给反馈：内容 / 结构 / 表达 三维度
- 如果用户说"换一题"或"再来一道难的"，继续

模拟时**保持面试官人设**：用真实面试官的口吻、追问方式、压力点（但不要变成 attacker，要 constructive）。

---

## 反模式（不要做）

- ❌ 给一份"通用 50 题"应付了事 → 必须按公司 / 岗位定制
- ❌ 参考回答全是"我具有出色的沟通能力"这种空话 → 必须用具体故事
- ❌ 不让用户自己练，全程"我替你答" → 错过模拟价值
- ❌ 编造用户没有的经历做 STAR 故事 → 用户面试时会穿帮
- ❌ HR 面问题答得太"训练痕迹重"（机械化） → 要给"3 个不同风格的版本"让用户选

## 与其他 skill 的协作

- 用户说"我简历不够强，先改简历再来面试" → 转 glm-jd-resume-tailor 插件（同批交付）或 glm-resume-builder 插件（已交付）
- 用户说"我还在犹豫要不要投" → 转 glm-job-intent-tracker 插件（已交付）
- 面试结束后用户说"我想复盘一下" → 留在本 skill，进入"面试复盘模式"，问表现、卡点、追问，帮用户为下一轮做准备
