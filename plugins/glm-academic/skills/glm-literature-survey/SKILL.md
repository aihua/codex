---
name: glm-literature-survey
description: "Comprehensive literature survey builder for a specific research topic: a complete PDF survey (6-20 pages, 60+ real citations, 100+ recommended) with LaTeX source, taxonomy figures and a classified literature table. Single-stage procedure + reference playbooks + LaTeX template, no Python runtime for the build itself; academic search routes to the glm-research-explorer plugin's keyless s2_search.py and web search/page fetch to the glm-web-search plugin. 触发场景：文献综述 / 领域综述 / 某研究方向的整体梳理 / 分类文献表 / 学位论文章或基金申请的背景章节 / 帮我 survey 一个具体课题（不含原创实验、不含选题探索）。"
metadata:
  version: "1.0.0"
---

# Literature Survey

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-academic/`
- 本技能目录：`~/.codex/plugins/glm-academic/skills/glm-literature-survey/`
- 下文 `references/`、`templates/` 均指该技能目录内的子目录；运行产物落在
  用户工作目录 `output/literature-survey/<slug>/<ts>/survey_paper/`。
- **宿主形态等效替换**（源 skill 依赖宿主工具，本地全部不存在）：
  - 学术检索（源 AMiner search_papers / get_paper_details）→
    glm-research-explorer 插件 `s2_search.py`（Semantic Scholar Graph API，
    匿名无 key，纯标准库；未安装时按其源逻辑手工执行）。
  - 通用 web 检索（源 WebSearch）→ glm-web-search 插件
    `glmws.py search`；页面抓取（源 WebFetch）→ `glmws.py fetch`。
  - LaTeX 编译（pdflatex/bibtex）→ 用户机器提供（MacTeX/tectonic）。
  - references 内出现的 WebSearch/WebFetch 字样按本映射理解。
- **零 SDK 纪律不变**：无 LLM SDK、无厂商 web-dev SDK、无 API key；
  唯一网络出口是用户显式发起的学术检索与页面抓取。
- 综述产出正文默认英文（LaTeX），会话语言默认中文——沿用源 skill 约定。

## Overview

End-to-end literature survey builder. **Single stage, full quality from the start.** The locally deployed Codex agent does the entire build using its own tools (Bash + the local equivalent CLIs of WebFetch/WebSearch: `glmws.py fetch` / `glmws.py search`, academic search via `s2_search.py`). This SKILL is procedure + reference playbooks + LaTeX template — no Python runtime, no LLM SDK.

The substantive work is decomposed into reference playbooks under `references/`:

| Reference | Topic |
|---|---|
| `references/00-incremental-execution.md` | how to actually do this without losing work: batch sizes, persistence, resume — **read first** |
| `references/01-bibliography-expansion.md` | grow `bibliography.bib` to 60+ real entries (100+ recommended) via WebFetch (no memory) |
| `references/02-survey-figures.md` | taxonomy / timeline / coverage-matrix / area-map figures |
| `references/03-survey-section-playbook.md` | per-section structure for survey-shaped papers |
| `references/04-layout-discipline.md` | tables, figures, floats, cross-refs, author + disclosure footnote |
| `references/05-quality-gate.md` | self-check before delivery |

**Read the relevant reference _before_ writing, not after.** The full pass does not fit in a single turn — `references/00-incremental-execution.md` is the only execution mode that completes.

## When to Use

- User asks for a "survey" / "review" on a specific topic.
- User has a research topic and wants a structured map of the field with citations.
- User needs background reading curated for a thesis chapter or grant section.

## When NOT to Use

- User wants original research with experiments → `paper-writer`.
- User wants only an outline / topic exploration → `research-explorer`.
- User wants experiment code → `experiment-suite`.
- Topic is too broad (e.g., "all of AI") — narrow it before starting.

## Workflow

### Step 1 — Understand the topic and scope

Confirm with the user:

- **Topic** — specific research area (e.g., "federated learning in healthcare"). If too broad, narrow it first.
- **Scope** — broad survey of a field vs. focused review of a sub-area.
- **Citation budget** — minimum 60 unique entries; aim for 100+ (push higher for a broad survey).
- **Language** — default Chinese in conversation; the LaTeX paper is English unless requested otherwise.

Always tell the user that human review by a domain expert is recommended before publication or production use.

### Step 2 — Set up the run directory

```bash
TOPIC="<topic>"
SLUG=$(python3 -c "import re,hashlib,sys; t=sys.argv[1]; n=re.sub(r'[\\s_]+','-',re.sub(r'[^\\w\\s-]','',t.lower().strip())).strip('-')[:40].rstrip('-'); h=hashlib.sha1(t.encode()).hexdigest()[:8]; print(f'{n}-{h}')" "$TOPIC")
TS=$(date +%Y-%m-%d_%H%M%S)
RUN=output/literature-survey/$SLUG/$TS/survey_paper

mkdir -p "$RUN/sections" "$RUN/figures"
cp -r ~/.codex/plugins/glm-academic/skills/glm-literature-survey/templates/survey/. "$RUN/"
ln -sfn "$TS" "output/literature-survey/$SLUG/latest"
```

In commands below `$RUN` = `output/literature-survey/<slug>/latest/survey_paper`.

### Step 3 — Build the survey (REQUIRED — this is the whole job)

Open `references/00-incremental-execution.md` first. Then carry out the five tracks below across many turns, persisting state to `$RUN/` after every batch.

#### 3.1 Bibliography — 60+ real entries (100+ recommended)

**Open:** `references/01-bibliography-expansion.md`.

**First (§0 of that reference): read the topic's temporal/scope intent and pick a search posture.** If the topic names a year or says "latest/recent" (e.g. "OpenSource LLM **2026**"), go *recency-led* — date-sorted arXiv queries carrying the explicit year, canon only as context. Otherwise span the timeline. This is what prevents "asked for 2026, got all 2024".

Then plan **12–20** query angles, weighted by the posture. For each angle, use
**structured academic search first, web search as supplement** (local
equivalents of the host AMiner/web_search chain):

- **`s2_search.py` (Semantic Scholar Graph API, anonymous, keyless)** — Use
  this FIRST for every query angle. It returns papers with structured metadata
  (title, authors, year, venue, citations, url) that is far more reliable than
  web-scraped results. Example:
  `python3 ~/.codex/plugins/glm-academic/skills/glm-research-explorer/scripts/s2_search.py --query "federated learning survey" --limit 20`
  (sort by citations via `--min-citations`; date-sorted recency via
  `--since-year`). Exit codes: `0` ok, `1` empty (rewrite query or degrade to
  web search), `2` unreachable (offline degrade; mark entries NOT
  web-verified). Anonymous endpoint is rate-limited ~1 req/s — sleep 1 between
  calls; HTTP 429 auto-retries once after 2s.
- **`glmws.py fetch`** — For key papers, pull the abstract/landing URL to
  capture full metadata (abstract, references) when the structured record is
  not enough.
- **`glmws.py search`** — Use when s2_search returns insufficient results, or
  for non-academic sources (blogs, benchmarks, datasets, tool documentation).

For each kept candidate: extract canonical title/authors/year/venue/url/citations
from the s2_search JSON response directly. For web-search-only results,
`glmws.py fetch` the abstract URL to extract metadata. Append a BibTeX entry
to `$RUN/bibliography.bib`. **Every entry must originate from a URL fetched in
this session or from an s2_search result.** Memory entries forbidden.

**Hard stop:** do not draft prose until `grep -c "^@" $RUN/bibliography.bib` ≥ 60 (aim for 100+).

#### 3.2 Figures — 6–10 survey-shaped

**Open:** `references/02-survey-figures.md`.

A survey is defined by how well it organises a field; figures carry that organisation:

- 1 taxonomy / classification diagram (TikZ hierarchy)
- 1 chronological timeline of major works
- 1 area / capability matrix (coverage heatmap)
- 1–2 representative architecture / mechanism diagrams
- 1–2 quantitative trend plots (matplotlib publication style)
- Optional: citation network, paradigm comparison

Save each into `$RUN/figures/` with reproducible source alongside.

#### 3.3 Sections — survey-shaped prose

**Open:** `references/03-survey-section-playbook.md`.

Survey sections differ in shape from research-paper sections. Order: introduction → background → methods (themed survey) → discussion → conclusion → related work → **abstract last**.

#### 3.4 Layout discipline

**Open:** `references/04-layout-discipline.md`.

Wrap every table in `\begin{table}[!t]` with booktabs; every figure in `\begin{figure}[!t]`. Use `~\cite{}` and `~\ref{}`. Set `\author{AI4S Agent}` with a `\thanks` footnote that **always** recommends human review. Surveys carry no simulated numerical experiments, so do **not** include a simulated clause.

#### 3.5 Compile + quality gate

```bash
cd "$RUN"
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

**Open:** `references/05-quality-gate.md`. Survey-specific targets: ≥ 60 bib entries (100+ recommended), ≥ 6 pages, ≥ 1 taxonomy figure, ≥ 1 timeline.

If a gate cannot honestly be met (e.g., the field is genuinely small), say so explicitly. Do not pad.

### Step 4 — Deliver

Report:

1. `output/literature-survey/<slug>/latest/survey_paper/main.pdf`
2. `output/literature-survey/<slug>/latest/survey_paper/` — complete LaTeX project (reproducible)
3. `output/literature-survey/<slug>/latest/literature_table.md` — classified literature table (write this alongside the bib build)
4. Stats per the report format in `references/05-quality-gate.md`.

## Cross-skill data flow (path convention)

A downstream skill (e.g., `paper-writer`) computing the same slug for the same topic will look here:

- `output/literature-survey/<slug>/latest/survey_paper/bibliography.bib` — bib starting point.

## Important rules

- **No LLM SDK in this skill.** No `import anthropic` / `import openai`, no vendor web-dev SDK. The skill is SKILL.md + references + LaTeX template only; its two executable dependencies are the keyless `s2_search.py` and `glmws.py` CLIs of sibling glm plugins.
- **No fabricated citations.** Every BibTeX entry must trace back to a URL fetched this session. Real or weaker claim — never fake reference.
- **Honest stop > padding.** If the field is too small for 60 real citations, say so to the user instead of inventing entries.
- **Survey scope** is 6–20 pages with 60–150 references (100+ recommended). For longer or shorter formats, adjust scope explicitly with the user up front.
