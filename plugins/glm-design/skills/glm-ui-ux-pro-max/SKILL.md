---
name: glm-ui-ux-pro-max
metadata:
  author: Z.AI
  version: "1.0.0"
description: >
  UI/UX design intelligence and implementation guidance for building polished
  interfaces. Use when the user asks for UI design, UX flows, information
  architecture, visual style direction, design systems/tokens, component
  specs, copy/microcopy, accessibility, or to generate/critique/refine
  frontend UI (HTML/CSS/JS, React, Next.js, Vue, Svelte, Tailwind):
  UI设计, UX设计, 界面设计, 交互设计, 视觉风格, 设计系统, 设计令牌, 组件规范,
  配色方案, 字体搭配, 落地页设计, 转化率优化, 无障碍设计, 信息架构,
  改进界面, 界面审计, design a page, critique this UI, build a design system.
  Fully local and offline: bundled BM25 search engine (pure Python stdlib)
  over 24 CSV knowledge bases (67 UI styles, 100 reasoning rules, 13 stack
  guidelines) — the CSV corpus never enters the model context, only ranked
  search results do.
license: MIT. LICENSE.txt has complete terms
---

# UI UX Pro Max

Deliver high-quality UI/UX output with minimal back-and-forth. 本文件是路由
中枢：WHEN 问什么、HOW 用哪条命令、WHAT 检查输出。所有命令在技能目录下执行
（`scripts/...` 与 `data/` 为相对路径）。细节文档按需读取，默认不读。

## Environment (run once)

```bash
bash scripts/setup.sh    # 体检 python3 / 24 个 CSV / 脚本编译 / BM25 自检；不安装任何东西
```

需要：python3（纯标准库，无 pip 包）。可用 `GLM_UIUX_PROMAX_PYTHON`
固定解释器（含 uv venv 形态）。**完全离线**——无网络出口，沙箱内不受 DNS
限制影响。

## Command table

| 目标 | 命令 |
|---|---|
| 跨域搜索（自动识别领域：style/color/chart/landing/product/ux/typography/icons/react/web） | `"${GLM_UIUX_PROMAX_PYTHON:-python3}" scripts/search.py "<query>"` |
| 指定领域搜索 | 同上追加 `--domain <domain>`；`-n 3` 控制条数（默认 3） |
| 技术栈规范搜索（html-tailwind/react/nextjs/astro/vue/nuxtjs/nuxt-ui/svelte/swiftui/react-native/flutter/shadcn/jetpack-compose） | 同上追加 `--stack <stack>` |
| 机读输出 | 同上追加 `--json` |
| 完整设计系统推荐（聚合 product+style+color+landing+typography 五域搜索 + 100 条推理规则） | `"${GLM_UIUX_PROMAX_PYTHON:-python3}" scripts/design_system.py "<project description>" -p "<Project Name>"` |
| 设计系统落盘（Master + 页面覆盖模式） | `scripts/search.py "<desc>" --design-system --persist -p "<Name>"`（`--page "dashboard"` 同时建页面级覆盖） |

## Exit codes

| Code | 含义 | 动作 |
|---|---|---|
| 0 | 成功（含"Found: 0 results"的空结果——换 query 关键词重试） | 读结果推进设计输出 |
| 2 | argparse 参数错误（未知 domain/stack 名等） | 检查命令拼写（合法值见命令表两行括号清单），修正重跑 |

## Workflow

### 1) Triage

Ask only what you must to avoid wrong work:

- Target platform: web / iOS / Android / desktop
- Stack (if code changes): React/Next/Vue/Svelte, CSS/Tailwind, component library
- Goal and constraints: conversion, speed, brand vibe, accessibility level (WCAG AA?)
- What you have: screenshot, Figma, repo, URL, user journey

If the user says "全部都要" (design + UX + code + design system), treat it as
four deliverables and ship in that order. 信息不足时才问；用户给足就别追
问——本地小模型的长对话会显著变慢。

### 2) Data lookups（先查数据，再给观点）

设计决策前先跑 Command table 的搜索——**引用数据说话**，不凭直觉。

- 找视觉风格方向（glassmorphism / brutalism / aurora …）→ `--domain style`
- 找配色 → `--domain color`（按产品类型给 hex 组合）
- 找图表选型 → `--domain chart`
- 落地页结构 → `--domain landing`
- 按产品类型整体推荐 → `--domain product`
- UX 可用性问题清单 → `--domain ux` / `--domain web`（含 Do/Don't 与好
  坏代码示例）
- 字体搭配 → `--domain typography`（含 Google Fonts URL / Tailwind 配置）
- 图标选型 → `--domain icons`
- React 性能反模式 → `--domain react`
- 技术栈落地规范（Do/Don't + 好坏代码 + 严重级别 + 官方文档 URL）→
  `--stack <stack>`

### 3) Produce Deliverables (pick what fits)

Always be concrete: name components, states, spacing, typography, and
interactions.

- **UI concept + layout**: Provide a clear visual direction, grid,
  typography, color system, key screens/sections.
- **UX flow**: Map the user journey, critical paths, error/empty/loading
  states, edge cases.
- **Design system**: Tokens (color/typography/spacing/radius/shadow),
  component rules, accessibility notes. 需要一站式 token 输出时用
  `scripts/design_system.py`（五域聚合 + 推理规则），落盘用 `--persist`
  Master + Overrides 模式。
- **Implementation plan**: Exact file-level edits, component breakdown, and
  acceptance criteria.

## Output Standards

- Default to ASCII-only tokens/variables unless the project already uses
  Unicode.
- Include: spacing scale, type scale, 2-3 font pair options, color tokens,
  component states.
- Always cover: empty/loading/error, keyboard navigation, focus states,
  contrast.

## Hard rules

1. **CSV 语料永不整读入上下文**：24 个 CSV（476K）是数据文件不是文档；
   BM25 搜索结果是唯一数据入口（每域默认 3 条、单字段截断 300 字符）。
   要更多结果就加 `-n`，不要 `cat` 整个文件。
2. **引用要可追溯**：给出风格/配色/字体推荐时注明来源（哪个域搜索/
   哪个 stack 规范），如 "（colors.csv · Financial Dashboard 行）"。
3. **Do/Don't 成对输出**：涉及 ux/web/stack 规范时，把搜索结果的
   Do/Don't 与好坏代码示例成对带给用户，不单说一边。
4. **设计系统落盘优先 Master 模式**：用户要可持久的设计系统时用
   `--persist`（design-system/<slug>/MASTER.md + pages/ 覆盖），不要把
   长 token 输出直接堆进对话。

## References（按需读取，默认不读）

| 需要 | 读 |
|---|---|
| 更多表述/完整用法/更多示例/Python 环境准备 | `references/upstream-skill-content.md` |
| 上游项目背景/版本/许可证/生态 | `references/upstream-README.md` |

默认只读本文件。没有匹配理由不打开 reference。

