---
name: glm-research-explorer
description: "Use when the user has a vague research direction and wants to explore feasible specific topics. Outputs a structured analysis with candidate topics, innovation/feasibility scoring, and a pre-survey of 20-30 representative works. 研究方向探索：当用户只有模糊的大方向（\"我想研究 X\" / \"X 有什么热点\" / \"帮我把大方向收窄成 5-10 个可做的题\" / \"给我一份 X 的研究版图\"）时触发，产出选题分析、主题矩阵与 20-30 篇代表性文献预调研三份文档。"
metadata:
  version: "1.0.0"
---

# GLM Research Explorer

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-academic/`
- 本技能目录：`~/.codex/plugins/glm-academic/skills/glm-research-explorer/`
- 下文 `scripts/`、`references/` 均指该技能目录内的子目录。
- **宿主工具等效替换**（源 skill 的联网检索组件在本环境不可用，改走本地实现）：
  - 结构化学术检索（源宿主学术组件） → `scripts/s2_search.py`（Semantic
    Scholar Graph API，匿名无 key，纯标准库；返回 title/authors/year/venue/
    citations/url）
  - 通用 web 检索（源宿主搜索组件） → glm-web-search 插件的
    `glmws.py search`（已交付插件；Bing HTML 主引擎 + DDG 降级）
  - 页面全文抓取（源宿主抓取组件） → glm-web-search 插件的
    `glmws.py fetch`（或 glm-web-reader 插件）
- **网络出口声明**：本技能的检索属功能性联网（用户显式发起研究探索），
  全部经 Codex 命令沙箱网络授权执行；无 SDK、无 API key。若沙箱禁网，
  s2_search.py / glmws.py 均以 exit 2 明确报错，可转纯模型知识模式
  （预调研文献标注"未经联网核实"）。
- 产出目录落在**用户工作目录**的 `output/research-explorer/` 下，插件目录只读。

## Overview

Research-topic exploration SKILL. Takes a broad direction, performs
multi-dimensional structured academic search + web search via the local
equivalents above, and produces three structured Markdown deliverables.
**Single stage, full quality from the start.** No LLM SDK, no API key.

## When to Use

- User says "I want to research X" / "我想研究 X" without a specific topic.
- User wants to know "what are the hot topics in X" / "X 有什么热点".
- User needs help narrowing a broad field into 5-10 candidate topics.
- User asks for "research landscape overview" / "研究版图".

## When NOT to Use

- User already has a specific research question → use `glm-literature-survey`
  (同环境插件；未安装时按其源 skill 逻辑手工执行系统性综述)。
- User wants a quick fact-check → run glm-web-search directly.

## Workflow

### Step 1 — Understand the direction

Confirm with the user:

- **Direction** — the broad area of interest (e.g., "federated learning",
  "NLP for healthcare").
- **Constraints** — theory vs. applied, specific methods, target venue,
  compute budget, time horizon.
- **Language** — conversation language follows the user; deliverables in
  English unless requested otherwise (检索词一律用英文，检索效果最佳).

### Step 2 — Set up the run directory

```bash
DIRECTION="<direction>"
SLUG=$(python3 -c "import re,hashlib,sys; t=sys.argv[1]; n=re.sub(r'[\\s_]+','-',re.sub(r'[^\\w\\s-]','',t.lower().strip())).strip('-')[:40].rstrip('-'); h=hashlib.sha1(t.encode()).hexdigest()[:8]; print(f'{n}-{h}')" "$DIRECTION")
TS=$(date +%Y-%m-%d_%H%M%S)
RUN=output/research-explorer/$SLUG/$TS

mkdir -p "$RUN"
ln -sfn "$TS" "output/research-explorer/$SLUG/latest"
```

In commands below `$RUN` = `output/research-explorer/<slug>/latest`.

### Step 3 — Multi-dimensional exploration

Run **structured academic search** (s2_search.py) and **web search**
(glmws.py) across the following dimensions (one query per dimension, more if
returns are thin):

1. **Hot topics** — "<direction> 2024 2025 hot topics" / "recent advances".
2. **Open problems** — "<direction> open problems" / "challenges".
3. **Surveys** — "<direction> survey 2024" / "<direction> review".
4. **Benchmarks** — "<direction> benchmark" / "<direction> evaluation dataset".
5. **Applications** — "<direction> applications" / "<direction> industry use cases".
6. **Cross-field** — "<direction> + <adjacent field>" (pick 1-2 adjacent fields).
7. **Recent breakthroughs** — papers from the last 6-12 months at top venues.

**Search strategy (structured first, generic web as supplement):**

- **s2_search.py — use FIRST for every dimension.** It returns papers with
  structured metadata (citations, venue, authors, year) that plain web search
  cannot provide. English queries work best. Example:

  ```bash
  python3 ~/.codex/plugins/glm-academic/skills/glm-research-explorer/scripts/s2_search.py \
      --query "federated learning survey" --limit 10 --since-year 2022
  ```

  Anonymous endpoint is rate-limited (~1 req/s): sleep >=1s between calls.
  Add `--json` when downstream parsing is needed. Author-side discovery:
  scan the `authors` field of top-cited hits instead of a separate author API.
- **glmws.py search — supplement** when s2_search returns thin results or for
  non-academic sources (blogs, documentation, benchmark leaderboards):

  ```bash
  python3 ~/.codex/plugins/glm-web/skills/glm-web-search/scripts/glmws.py \
      search "<direction> benchmark leaderboard" --num 8
  ```
- **glmws.py fetch — page enrichment.** For s2_search/web results whose
  snippet is not enough, fetch at most 2 URLs per question:

  ```bash
  python3 ~/.codex/plugins/glm-web/skills/glm-web-search/scripts/glmws.py \
      fetch "<URL>" --max-chars 4000
  ```

For each kept candidate, take canonical title / authors / year / venue /
citation count from the s2_search output. For web-only results, fetch the
abstract page and extract metadata manually. Persist intermediate notes to
`$RUN/search_notes.md` after every dimension so the work resumes cleanly.

**Offline mode (sandbox denies network):** s2_search.py and glmws.py exit 2
with explicit hints. Fall back to model knowledge only: produce the three
deliverables from internal knowledge and mark every literature entry
"NOT web-verified this session"; state this limitation to the user up front.

### Step 4 — Produce the three deliverables

Write these in `$RUN/`:

#### 4.1 `research_exploration.md`

Structured analysis containing:

- **Direction recap & constraints**.
- **Landscape map** — main subfields and the relationships between them.
- **5-10 candidate topics**, each with:
  - Title (specific enough to be a paper title).
  - Motivation (why this matters now).
  - Innovation angle (what would be new).
  - Feasibility score (low / medium / high) with a brief justification (data
    availability, compute requirements, prior work density).
  - Risk / open question.
- **Recommendation** — which 1-3 the user should pursue and why.

#### 4.2 `topic_matrix.md`

A hierarchical Markdown outline of the topic space:

```
# <Direction>
## Subfield A
### Topic A.1
### Topic A.2
## Subfield B
### Topic B.1
```

This file is directly consumable by the glmcharts plugin (mindmap route) to
produce a visual mindmap of the topic space.

#### 4.3 `literature_pre_survey.md`

A pre-survey table of **20-30 representative works** discovered above, with
columns: title, authors, year, venue, URL, one-sentence relevance note. Every
entry must have a URL obtained from this session's search output (s2_search
url field or fetched web result). Offline-mode entries must carry the
"NOT web-verified" marker instead.

### Step 5 — Optional handoff

If the user picks a topic, suggest the next step:

- For a systematic survey: the `glm-literature-survey` plugin (同批插件；
  未安装时按其源 skill 逻辑手工执行 LaTeX 综述流程).
- For a paper draft: no dedicated local plugin yet — offer to draft an outline
  from `research_exploration.md` directly in-chat.
- For an experiment package: no dedicated local plugin yet — offer to write the
  experiment plan Markdown in-chat.
- For a visual topic map: the glmcharts plugin consuming `topic_matrix.md`
  (mindmap route).

## Cross-skill data flow (path convention)

A downstream skill can locate this exploration via the slug:

- `output/research-explorer/<slug>/latest/topic_matrix.md`
- `output/research-explorer/<slug>/latest/literature_pre_survey.md`

If the user picks one topic from the matrix, downstream skills compute their
own slug from the **topic** (not the original direction), so the slug paths
diverge from this skill onward — which is correct.

## Important rules

- **No LLM SDK in this skill.** Procedure + `SKILL.md` + one pure-stdlib
  search CLI; the only network exits are the two user-visible search
  commands, both keyless.
- **Candidates are suggestions, not guaranteed novel** — the user must verify
  originality before committing.
- **Feasibility scores are heuristic** — flag uncertainty explicitly when
  relevant.
- Every literature entry must have a URL from this session's search output; no
  memory-only entries (offline mode is the single sanctioned exception and
  must be marked).
