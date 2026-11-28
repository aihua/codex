---
name: glm-web-reader
metadata:
  author: Z.AI
  version: "1.0.2"
description: >
  Zero-dependency web page reading via a local CLI (glmwr.py). Turn any URL into clean text: title,
  description, author, publication time, main paragraphs with heading
  structure, plus link listing. Auto-detects RSS/Atom feeds and raw JSON
  endpoints. Use when the user gives a link to read, summarize, or
  extract facts from, when a search snippet is not enough and the full
  page must be opened, or when feeds or API responses need turning into
  text: 读这个链接, 读网页, 网页正文, 抓取页面, 提取内容, 总结这篇文章,
  read this page, open this URL, extract the content. No SDK, no API key,
  no third-party Python packages - safe to run anywhere python3 exists.
license: MIT. LICENSE.txt has complete terms
---

# GLM Web Reader

Read one web page into clean text with a local zero-dependency CLI. This
file is only the router: it tells you WHEN to read a page, HOW to run the
command, and WHAT to do with the extracted content. Follow it exactly.

## Environment (run once)

```bash
bash scripts/setup.sh          # relative to this skill directory; --skip-net = offline check
```

Interpreter rule for every command below: if the environment sets `GLM_WEB_READER_PYTHON`, use that interpreter; otherwise use `python3`. Example:

```bash
"${GLM_WEB_READER_PYTHON:-python3}" scripts/glmwr.py read "https://example.com/post" --max-chars 4000
```

## Mandatory 5-step workflow

Execute these five steps in order. Never skip a step.

1. **Decide.** Read a page only when its content is needed: the user gave a URL, a search snippet is not enough to answer, or the user asks to read/summarize/extract a page. Do not read a page for questions you can answer from context you already have.
2. **Pick the command.** One row of the command table below. `read` for a page (or feed, or JSON endpoint); `links` only when the user asks what a page links to. Default `--max-chars 4000`.
3. **Run.** Read the exit code before anything else.
4. **Use the content.** Quote or summarize from the extracted text with the page title as context. If the `Published:` line or `publishedTime` field is empty, the page does not declare a date - you may still quote a date visible in the body text, citing it as page content, not metadata.
5. **Answer with the source.** Name the title and URL of every page you used. If the read failed, say so honestly and stop - never describe a page you could not open.

## Command table

All commands run from the skill directory (`scripts/` paths below are relative to it).

| Goal | Command |
|---|---|
| Read a page (default text view) | `"${GLM_WEB_READER_PYTHON:-python3}" scripts/glmwr.py read "URL" --max-chars 4000` |
| Machine-readable result (SDK-compatible schema) | `... read "URL" --json` |
| Markdown document (title + description + headings) | `... read "URL" --markdown` |
| News feed / Atom feed | `... read "FEED-URL" --max-items 10` |
| Raw JSON endpoint (API response) | `... read "API-URL" --max-chars 2000` |
| List hyperlinks on a page | `... links "URL" --limit 30` |
| Only links pointing off-site | `... links "URL" --host '!@'` (exclude the page's own host) |
| Layered network diagnosis (only after exit 2) | `"${GLM_WEB_READER_PYTHON:-python3}" scripts/glmwr.py diagnose` |

`read` output starts with `URL:` / `Title:` / `Description:` / `Published:` / `Author:` / `Chars:` lines (whenever the page provides them), then the page text. Feed output starts with `Kind: RSS/Atom feed` and lists items. JSON endpoint output starts with `Kind: raw json endpoint`.

## Exit codes

| Code | Meaning | Your action |
|---|---|---|
| 0 | Page read, text extracted | proceed to step 4 |
| 1 | Fetched but no text (HTTP 4xx/5xx, JavaScript-only page, or zero links for `links`) | do not retry blindly; report the page as unreadable; suggest an alternative URL if one is known |
| 2 | Network/usage error (unreachable host, DNS, timeout) | run `scripts/glmwr.py diagnose` once and report its verdict and hints verbatim (they separate Codex sandbox vs proxy vs firewall); read `references/fallback.md` only if the user asks to fix the environment |

## Result fields (`read --json`, inside `data`)

| Field | Meaning |
|---|---|
| `url` | final URL after redirects (canonical link when the page declares one) |
| `title` | page title |
| `description` | meta description |
| `publishedTime` | publication time from page metadata; often empty - never invent one |
| `author` | author from page metadata; often empty |
| `lang` | declared page language |
| `text` | extracted main text (nav/footer/boilerplate removed, headings kept as separate paragraphs) |
| `html` | simplified article HTML rebuilt from the extracted paragraphs - structure summary, not the raw page markup |
| `linksCount` | number of hyperlinks found on the page |
| `usage.tokens` | always 0: extraction is local, nothing is metered |
| `kind` | `rss` for feeds, `json`/`text` for raw endpoints (HTML pages omit it) |

## Hard rules

1. **Never fabricate.** If the page could not be read (exit 1/2), say so. No invented quotes, dates, numbers, authors or page content.
2. **Cite what you used.** Every factual claim that came from a page gets its title and URL in the final answer.
3. **Cap reads.** At most 3 `read` calls per question, each `--max-chars 4000` or less; at most 1 `links` call. Summaries beat full dumps for long pages.
4. **Metadata over guessing.** Trust `publishedTime`/`author` from metadata; treat dates found in body text as page claims, not established facts.
5. **Respect the source.** Quote short fragments, not whole pages; note paywalls or access-blocked pages instead of working around them.
6. **Engine errors are environment, not content.** Exit code 2 means the network blocked the fetch - report that instead of describing the page from memory. The stderr hint lines and `glmwr.py diagnose` separate the real cause (Codex command sandbox / proxy / firewall); relay them verbatim instead of guessing a proxy cause yourself.
7. **glmwr.py is the ONLY page-reading path.** Never call any built-in or server-side page-fetch tool (for example a web_fetch tool offered by the model server), and never claim a read ran through one. If such a tool appears in your toolset, ignore it for reading and run glmwr.py instead. The model server's built-in web_fetch is a metered cloud feature: calling it without a signed-in account aborts the whole session (Codex reports `stream disconnected ... This model requires an Ollama account`) - so never reach for it, even when it is advertised in the toolset.

## Deeper reference files (load ONLY when needed)

| When | Read |
|---|---|
| Multi-page research, source quality rules, citation formatting, feed handling | `references/_rules.md` |
| All reads fail with exit 2, or the user wants to fix connectivity/proxy | `references/fallback.md` |

Default for a plain "read this URL" request: this file is enough. Do not open a reference file without a matching reason.
