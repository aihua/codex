---
name: glm-cheat-sheet
description: "将 PDF/Word/Markdown 学习资料转化为精炼的知识浓缩卡文档（双栏小字 PDF）。支持三种风格（知识点速查卡/思维导图式/Q&A式），文本提取走本地零依赖 CLI（docx 纯标准库、pdf 走 pdftotext/pypdf），渲染走 reportlab 内置 CJK CID 字体（uv run --with reportlab 免安装直跑，无需安装任何中文字体文件）。当用户说「生成知识浓缩卡」「生成 Cheatsheet」「帮我做个速查表」「把这个资料整理成一页纸」「做个知识卡片」时触发。不处理：基于材料出题（→ glm-quiz-mastery）、长期学习项目（→ glm-study-buddy）。"
metadata:
  version: "1.0.0"
---

# Cheatsheet 生成器

## 你做什么

把用户的学习资料（PDF/Word/Markdown/文本）压缩成一份**双栏、小字、信息密度高**的 Cheatsheet 文档（PDF 格式）。

**核心原则：只保留干货，砍掉废话。**

## Codex Deployment Notes（本地 Codex 插件形态）

- 插件安装根目录：`~/.codex/plugins/glm-study/`；本技能目录：
  `~/.codex/plugins/glm-study/skills/glm-cheat-sheet/`。
  下文 `scripts/` 均指该技能目录内子目录；产物写**用户工作目录**，插件目录只读。
- **零 SDK 审计**：源 skill 为纯流程指引（单 SKILL.md），对厂商 web-dev SDK 标识
  与常见 LLM SDK import 形态逐字审计命中为零，无需函数级替换；**本地亦无需部署任何 SDK**。
- **宿主 PDF skill 依赖的本地等效替换**（源 skill 调用 PDF skill 的 process/report
  两条路线，本地 Codex 不存在该宿主技能）：

| 源 skill 调用 | 本地等效 | 说明 |
|---|---|---|
| PDF skill process 路线：`pdf.py extract.text`（PDF/docx 提文本） | `scripts/extract_text.py` | `.md/.txt` 直读；`.docx` 纯标准库 zipfile；`.pdf` 优先 pdftotext（brew install poppler）其次 pypdf（`uv run --with pypdf` 免安装直跑） |
| PDF skill report 路线（ReportLab 双栏小字 PDF） | `scripts/render_cheatsheet.py` | reportlab 为唯一第三方依赖，`uv run --with reportlab python3 ...` 免安装直跑；CJK 用内置 Adobe CID 字体 STSong-Light，**无需安装任何中文 TTF/TTC 字体文件** |
| PDF skill 的 CJK 字体检查/表格溢出防护等 SKILL 规则 | 内化到渲染脚本 | 单字体族渲染（<b> 映射同族，避免混字族 CJK 缺字）；Markdown 分组渲染，无表格溢出面 |

- 源 skill 的排版规格（A4/双栏/8pt/行距1.2/边距12mm）为 `render_cheatsheet.py`
  默认值，可用 `--single-column / --font-size / --margin` 按用户要求调整。
- **同插件技能关系**：glm-study-buddy 完成学习项目后可推荐本技能；glm-quiz-mastery
  出题与本技能无直接依赖（cheatsheet 内容可作知识点来源）。

---

## ⚠️ 铁律：避免重复创建

生成 Cheatsheet 前，**先扫描输出目录**检查是否已有同主题文件：
- **已存在** → 问用户"已经有一份 [文件名] 了，覆盖 / 新建一份 / 跳过？" 等用户回复再动手
- **不存在** → 直接生成
- **绝不**未经询问直接覆盖

---

## 工作流程

### 步骤 1：接收资料

用户提供学习资料文件，支持格式：`.pdf` / `.docx` / `.md` / `.txt`（或直接粘贴文本）。

**提取文本命令（本地等效 CLI）：**

```bash
CS=~/.codex/plugins/glm-study/skills/glm-cheat-sheet/scripts

# md/txt/docx（零依赖）
python3 "$CS/extract_text.py" <资料路径> -o output/material.txt

# pdf（pdftotext 或 pypdf；两者皆缺时脚本会给出安装指引）
python3 "$CS/extract_text.py" <资料.pdf> -o output/material.txt
# pypdf 免安装直跑形态：
uv run --with pypdf python3 "$CS/extract_text.py" <资料.pdf> -o output/material.txt
```

如果用户没有提供文件而是直接贴了文本内容，跳过提取步骤，直接用文本。

---

### 步骤 2：选择风格

**必须询问用户**想要哪种风格（不要自己替用户选）：

向用户展示以下选项：
1. 📋 **知识点速查卡** — 核心概念 + 定义 + 关键公式/要点，一眼扫到，适合考前突击
2. 🌳 **思维导图式** — 按层级结构组织（大标题→子标题→要点），有大纲感，适合梳理体系
3. ❓ **Q&A 式** — 把知识点变成"问题→答案"对，适合自测复习

用户选择后进入步骤 3。

---

### 步骤 3：LLM 提炼内容

根据用户选择的风格，按以下规则从原文中提炼 cheatsheet 内容。

#### 风格 1：知识点速查卡

提炼规则：
- 提取所有核心概念、定义、公式、关键数据
- 每个知识点用 **术语：一句话解释** 的格式
- 相关知识点分组，每组有小标题（`## 分组标题`）
- 重要公式/代码片段原样保留（`` ` `` 行内代码渲染为等宽原文）
- 砍掉所有举例、过渡句、背景铺垫

输出结构：
```
# 主题

## [分组标题]
- **术语A**：一句话定义
- **术语B**：一句话定义
- 📐 公式：`公式内容`
```

#### 风格 2：思维导图式

提炼规则：
- 提取文档的层级结构（章→节→要点）
- 每个节点用最简短的语言概括
- 最多 3 级深度（再深就塞不进一页了）
- 用缩进和符号（`├─` `│` `└─`）表达层级关系

输出结构：
```
# 主题

## 一级分支
  ├─ 二级要点
  │   ├─ 细节 1
  │   └─ 细节 2
  └─ 二级要点
      └─ 细节
```

#### 风格 3：Q&A 式

提炼规则：
- 把每个知识点转化成一个问题
- 答案控制在 1-3 句话
- 问题从基础到进阶排列
- 易混淆的概念出辨析题

输出结构：
```
# 主题

## [分组]

**Q：什么是 XXX？**
A：一句话回答。

**Q：XXX 和 YYY 的区别？**
A：简短对比。
```

---

### 步骤 4：用户确认与调整

LLM 生成内容后，**先以文本形式展示给用户**，询问：

> "内容整理好了，你看看有没有要调整的？比如：
> - 某些部分要加重点标记？
> - 某些内容要删掉或补充？
> - 排版上有什么偏好？（比如字号再小一点、分区颜色区分等）"

用户确认"可以"后，进入步骤 5。
用户提出修改 → 调整内容 → 再次展示 → 等待确认。

---

### 步骤 5：生成 PDF（本地等效渲染）

把确认后的内容存为 `output/cheatsheet_content.md`（用户工作目录），然后：

```bash
CS=~/.codex/plugins/glm-study/skills/glm-cheat-sheet/scripts

# 首选：uv 免安装直跑（reportlab 唯一第三方依赖）
uv run --with reportlab python3 "$CS/render_cheatsheet.py" \
  -i output/cheatsheet_content.md \
  -o "output/知识浓缩卡_[主题]_[日期].pdf"

# 已 pip/uv 安装过 reportlab 时直接跑
python3 "$CS/render_cheatsheet.py" \
  -i output/cheatsheet_content.md \
  -o "output/知识浓缩卡_[主题]_[日期].pdf"
```

**排版规格（渲染脚本默认值）：**

| 参数 | 默认值 | 调整方式 |
|------|--------|----------|
| 页面大小 | A4 | 固定 |
| 栏数 | 双栏 | `--single-column` 切单栏 |
| 正文字号 | 8pt | `--font-size N` |
| 标题字号 | 10pt（一级）/ 9pt（二级，蓝底强调） | 随正文基准浮动 |
| 行距 | 1.2 | 固定（紧凑但可读） |
| 页边距 | 上下左右各 12mm | `--margin N` |
| 字体 | 中文拉丁同用内置 CID 字体 STSong-Light | **无需安装任何字体文件** |

未装 reportlab 直接跑 python3 形态时：exit 2 + stderr 打印 uv/pip 两条安装命令。

---

### 步骤 6：交付

输出给用户：
- 📄 PDF 文件路径（绝对路径；stderr 同时报告页数与文件大小）
- 文件大小、页数
- 提示用户可以继续调整

---

## 注意事项

### 内容质量
- **不编造内容**：所有知识点必须来自原文，不能自由发挥
- **不遗漏关键内容**：核心概念、公式、定义必须保留
- **术语保持原文用词**：不要擅自替换专业术语

### 文件操作
- 生成的 PDF 默认保存到**用户工作目录** `output/`，文件名格式：`知识浓缩卡_[主题]_[日期].pdf`
- 查重见上方"⚠️ 铁律：避免重复创建"
- Markdown 中间稿（`cheatsheet_content.md`）保留在 output/ 供后续微调重渲染

---

## 附加资源

- `scripts/extract_text.py` — md/txt/docx/pdf 文本提取（docx 纯标准库；pdf 走 pdftotext/pypdf）
- `scripts/render_cheatsheet.py` — 双栏小字 PDF 渲染（reportlab + 内置 CJK CID 字体，uv 免安装直跑）
