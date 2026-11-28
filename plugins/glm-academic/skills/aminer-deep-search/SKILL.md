---
name: aminer-deep-search
description: "Activate this skill when the user wants deep, multi-round academic paper collection for a survey or literature review. The host model (the model running this skill) drives the loop itself: it expands queries, judges relevance, snowballs backward references, and decides when to stop. The bundled scripts are pure tool commands that call documented AMiner Open Platform endpoints and print JSON tool results only — no extra LLM configuration is needed. Use this skill for broad topic exploration, survey bibliography construction, and collecting hundreds of candidate papers with AMiner IDs and titles. Not intended for single-paper lookup or lightweight recommendations; use aminer-free-academic or aminer-daily-paper for those. 触发场景：综述文献收集 / 深度多轮论文收集 / 帮我收集几百篇候选论文 /aminer-deep-search / survey 参考文献构建（需 AMINER_API_KEY）。\n"
metadata:
  version: "2.0.0"
  author: "AMiner"
  contact: "report@aminer.cn"
  openclaw: '{"requires": {"bins": ["python3"], "env": ["AMINER_API_KEY"]}, "primaryEnv": "AMINER_API_KEY"}'
---

# AMiner Deep Search

Host-model-driven survey paper collection. You (the model reading this) are the controller: run the tool scripts, read their JSON output, judge relevance yourself, and iterate until the collection target is met.

## Codex Deployment Notes（本地 Codex 插件形态）

- 插件安装根目录：`~/.codex/plugins/glm-academic/`；本技能目录：
  `~/.codex/plugins/glm-academic/skills/aminer-deep-search/`。
  下文 `scripts/`、`tests/` 均指该技能目录内子目录；状态文件与导出（`outputs/paper_set.json`、
  `outputs/final_papers.json`）落在**用户工作目录**（相对 cwd），插件目录只读。
- **零 SDK 审计**：源 skill 全部脚本对厂商 web-dev SDK 标识与常见 LLM SDK import 形态
  逐字审计命中为零——两个工具脚本均为纯标准库 urllib 直调 AMiner 开放平台公网接口，**不依赖
  任何厂商 web-dev SDK，也零 pip 依赖**。`X-Platform: openclaw` 头为接口网关契约，
  按接口文档保留；frontmatter 里的 `metadata.openclaw` 为源宿主平台元数据，本地不消费。
- **唯一外部依赖**：环境变量 `AMINER_API_KEY`（open.aminer.cn 控制台申请）。
- **本模型即控制器**：脚本只输出 JSON tool-result，查询扩展、相关性判断、
  滚雪球、终止决策全部由你（宿主模型）完成——本地 Ollama 模型天然适配此形态。
- **调用契约**（源 commands/aminer-deep-search.md 的 Claude 宿主形态已折进本节）：
  显式触发词 `/aminer-deep-search topic: <研究主题> target-size: 400 max-rounds: 12`，
  或自然语言（“帮我收集 400 篇联邦学习候选论文”）；参数解析→Pre-flight（查 key）→
  按 Round Protocol 执行→export 后报告篇数/总成本/导出路径。
- `tests/` 为离线单测（mock urlopen，零网络）：`python3 tests/test_aminer_api.py`、
  `python3 tests/test_paper_set.py` 可直接跑，setup.sh 会执行。
- **同插件技能路由**：免费轻量查询 → glm-aminer-free-academic；个性化推荐 →
  glm-aminer-daily-paper；付费深度分析 → glm-aminer-academic-search；本插件承担
  综述级多轮收集档。中文版规范见 SKILL.zh.md（Codex 部署节同上）。

## Scope

- Use for: survey bibliography collection (hundreds of papers), keyword expansion, backward-citation snowballing.
- Do not use for: single-paper lookup or Q&A (route to `aminer-free-academic`), personalized recommendations (route to `aminer-daily-paper`).

## Pre-flight

1. Check the key without printing it:

```bash
[ -z "${AMINER_API_KEY:-}" ] && echo "AMINER_API_KEY missing" || echo "AMINER_API_KEY exists"
```

If missing, stop and ask the user to set `AMINER_API_KEY` (console: https://open.aminer.cn/open/board?tab=control). Never print the key.

2. Confirm the `topic` and the `target-size` (default 400). If your round plan is estimated to cost ¥5 or more, tell the user the estimate and get confirmation before starting.

## Tools

Both scripts live in `scripts/` under this skill directory. They print exactly one JSON document to stdout (the tool result); diagnostics and a `[cost]` line go to stderr. They never score relevance — that is your job.

### `scripts/aminer_api.py` — AMiner API calls

| Subcommand | Endpoint | Price |
|---|---|---|
| `search --query Q [--size 20] [--year YYYY] [--order n_citation\|year] [--max-pages 3]` | GET `/api/paper/search/pro` + free `paper/info` enrichment | ¥0.01/page |
| `qa-search [--query "natural language question"] [--topic-high '[["termA","termB"],["termC"]]'] [--size 20] [--year-from Y] [--year-to Y] [--citation-sort]` | POST `/api/paper/qa/search` (always `use_topic=true`; the backend ignores `query` when `use_topic=false`) + free enrichment | ¥0.05/call |
| `info --ids id1 id2 ...` | POST `/api/paper/info` (batched ≤100 ids) | Free |
| `references --ids id1 id2 ... [--per-seed 20]` | GET `/api/paper/relation` per seed + free enrichment | ¥0.10/seed |

Output shape: `search`/`qa-search`/`info` print `[{id, title, year?, venue?, abstract_slice?}]`; `references` additionally includes `source_paper_ids` (which seeds cited the paper). Seeds themselves are excluded from `references` output.

### `scripts/paper_set.py` — cross-round state file (no network)

State file defaults to `outputs/paper_set.json` relative to the working directory.

```bash
# Merge kept results (pipe the filtered JSON array in), dedupe by id
python3 scripts/aminer_api.py search --query "..." | python3 scripts/paper_set.py add
# → {"added": N, "duplicates": M, "total": T}

python3 scripts/paper_set.py stats     # totals, expanded_seeds, by_year
python3 scripts/paper_set.py mark-expanded --ids id1 id2   # record snowballed seeds
python3 scripts/paper_set.py export -o outputs/final_papers.json
```

`add` also accepts `--ids id1 id2 ...` for bare IDs. Items carrying `source_paper_ids` (from `references`) automatically mark those seeds as expanded.

If you want to filter before adding, read the search output first, then pipe only the kept items:

```bash
printf '%s' '[{"id":"...","title":"..."}]' | python3 scripts/paper_set.py add
```

## Round Protocol (core)

### Round 0 — plan

- Derive 4–8 seed queries from the topic: synonyms, subfields, method names, datasets/benchmarks, common English abbreviations.
- Estimate rounds and cost (searches ≈ ¥0.01–0.05 each, references ≈ ¥0.10/seed). If the estimate is ≥¥5, confirm with the user first.

### Each round (default budget: 12 rounds), five fixed steps

1. **Search**: run 1–4 `search` / `qa-search` calls from the pending query queue. Prefer `search` (cheaper); use `qa-search` when the query is a natural-language question.
2. **Filter & add**: read the stdout results, judge relevance to the topic yourself, and pipe only the kept items into `paper_set.py add`. Never add papers you consider off-topic.
3. **Check**: run `stats` to see the total and this round's increment.
4. **Snowball**: from this round's relevant additions pick ≤5 strong seeds (highly relevant, ranked high under `--order n_citation`, not in `expanded_seeds`) and run `references --ids ...`. Filter the output for relevance, then add it. Run `mark-expanded` for seeds that yielded nothing addable.
5. **Decide**: choose the next move —
   - a search returned <5 results or poor quality → replace it with a reformulated query (max 2 variants per direction, then switch to snowballing);
   - references are yielding many relevant papers → keep snowballing from fresh seeds;
   - reached `target-size`, or results are exhausted, or 2 consecutive rounds added <5 papers → terminate.

### Wrap-up

Run `export`, then report: final paper count, total cost (sum the `[cost]` stderr lines), and the output path.

## Rules

1. Never fabricate paper IDs or titles; only cite data actually returned by the tools.
2. Free first: metadata always comes from the free `paper/info` (the scripts already do this); never call the paid `paper/detail` for bulk metadata.
3. Keep the raw tool output out of your final answer; report counts and the exported file path instead.
4. Never print or log `AMINER_API_KEY`.
5. If AMiner returns fewer papers than the target, report the real count instead of inventing papers.
