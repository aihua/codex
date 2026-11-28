---
name: glm-web-search
metadata:
  author: Z.AI
  version: "1.1.2"
description: >
  Zero-dependency web search via a local CLI (glmws.py). Search engines: Bing HTML (primary, works behind most
  firewalls including mainland CN) with DuckDuckGo HTML/Lite fallback; plus
  a fetch mode that turns any page into plain text. Use when the user needs
  real-time information, current news, prices, releases, documentation
  beyond the knowledge cutoff, or any fact you are unsure about: 搜索, 联网
  搜索, 查一下, 最新, 今天, 近期, 现在多少, 联网查. Returns structured
  results with url, name, snippet, host_name, rank, date, favicon. No SDK,
  no API key, no third-party Python packages - safe to run anywhere python3
  exists.
license: MIT. LICENSE.txt has complete terms
---

# GLM Web Search

Search the live web with a local zero-dependency CLI. This file is only the router: it tells you WHEN to search, HOW to build the query, and WHAT to do with the results. Follow it exactly.

## Environment (run once)

```bash
bash scripts/setup.sh          # relative to this skill directory; --skip-net = offline check
```

Interpreter rule for every command below: if the environment sets `GLM_WEB_SEARCH_PYTHON`, use that interpreter; otherwise use `python3`. Example:

```bash
"${GLM_WEB_SEARCH_PYTHON:-python3}" scripts/glmws.py search "query" --num 8
```

## Mandatory 5-step workflow

Execute these five steps in order. Never skip a step.

1. **Decide.** Search only when the answer needs live web data: anything after your knowledge cutoff, anything time-sensitive (prices, versions, news, weather, release dates), or when the user explicitly asks to search. Otherwise answer directly - do not burn a search on common knowledge.
2. **Craft the query.** Short and specific (under 10 words). Drop filler words. For time-sensitive questions add a year or qualifier (`latest`, `2026`, `最新`). If the first query misses, rewrite it once (different angle, more specific, or switch language) instead of re-running the same words.
3. **Run.** Pick ONE row of the command table. Read the exit code. Default `--num 8`.
4. **Read the results.** Pick the top 3-5 results by title/snippet relevance. If a snippet is not enough to answer, fetch 1-2 URLs - never more than 2 per question. Ignore result dates inside snippets (they are page text, not publication dates) unless the `date` field itself is present.
5. **Answer with sources.** Cite the real URLs you used, as a list at the end. If the search failed or contradicts nothing, say so honestly. Never invent sources or dates.

## Command table

All commands run from the skill directory (`scripts/` paths below are relative to it).

| Goal | Command |
|---|---|
| Basic search | `"${GLM_WEB_SEARCH_PYTHON:-python3}" scripts/glmws.py search "QUERY" --num 8` |
| News / last N days only | `... search "QUERY" --num 8 --recency-days 7` |
| Machine-readable output | `... search "QUERY" --num 8 --json` |
| Markdown link list | `... search "QUERY" --num 8 --markdown` |
| Force one engine | `... search "QUERY" --engine bing` (or `ddg`, `ddg-lite`) |
| Read one page in full | `"${GLM_WEB_SEARCH_PYTHON:-python3}" scripts/glmws.py fetch "URL" --max-chars 4000` |
| Layered network diagnosis (only after exit 2) | `"${GLM_WEB_SEARCH_PYTHON:-python3}" scripts/glmws.py diagnose` |

`fetch` output starts with `URL:` / `Title:` / `Description:` / `Chars:` lines, then the page text - cite the title and URL, not the whole dump.

## Exit codes

| Code | Meaning | Your action |
|---|---|---|
| 0 | Results returned | proceed to step 4 |
| 1 | Engines reachable, zero results | rewrite the query once (step 2); if it still fails, say so |
| 2 | Network/usage error, no engine reachable | run `scripts/glmws.py diagnose` once and report its verdict and hints verbatim (they separate Codex sandbox vs proxy vs firewall); read `references/fallback.md` only if the user asks to fix the environment |

## Result fields (JSON mode)

| Field | Meaning |
|---|---|
| `url` | real destination URL (redirects already unwrapped) |
| `name` | page title |
| `snippet` | short preview text |
| `host_name` | domain of the result |
| `rank` | 1-based position |
| `date` | date fragment parsed from the snippet; often empty - never invent one |
| `favicon` | constructed icon URL (display only) |

## Hard rules

1. **Never fabricate.** If search found nothing usable, say so. No invented URLs, dates, numbers or quotes.
2. **Cite what you used.** Every factual claim that came from the web gets its source URL in the final answer.
3. **Cap fetches.** At most 2 `fetch` calls per question, each `--max-chars 4000` or less. Summaries of long pages beat full dumps.
4. **Retry policy.** At most 2 searches per query rewrite; a total of 3 searches per question unless the user asks for deeper research.
5. **Trust ranking.** Prefer official documentation, vendor sites and established outlets over low-quality aggregators when snippets conflict; cross-check surprising claims against a second independent domain.
6. **Engine errors are environment, not content.** Exit code 2 means the network blocked all engines - report that instead of guessing an answer. The stderr hint lines and `glmws.py diagnose` separate the real cause (Codex command sandbox / proxy / firewall); relay them verbatim instead of guessing a proxy cause yourself.
7. **glmws.py is the ONLY search path.** Never call any built-in or server-side web-search tool (for example a web_search tool offered by the model server), and never claim a search ran through one. If such a tool appears in your toolset, ignore it for searching and run glmws.py instead. No result may be cited unless it came from glmws.py output. The model server's built-in web_search is a metered cloud feature: calling it without a signed-in account aborts the whole session (Codex reports `stream disconnected ... This model requires an Ollama account`) - so never reach for it, even when it is advertised in the toolset.

## Deeper reference files (load ONLY when needed)

| When | Read |
|---|---|
| Multi-round research, source quality rules, citation formatting | `references/_rules.md` |
| All engines unreachable, or the user wants to fix connectivity/proxy | `references/fallback.md` |

Default for a plain question: this file is enough. Do not open a reference file without a matching reason.
