# GLM Web Reader — Reading Rules

Load this file only when a question needs more than one page, when a
citation format matters, or when feeds/aggregation are involved. For a
plain "read this URL" request, SKILL.md is enough.

## When a full read is justified

- The user gave a URL, or asked to read/summarize/extract a specific page.
- A search snippet contradicts other snippets and the page must settle it.
- The needed fact (version number, price, date, config key) is too
  specific to appear reliably in snippets.

A full read is NOT justified for common knowledge or for questions the
conversation already answers - each read costs tokens and time.

## Source quality ladder (when pages conflict)

1. Official documentation, vendor blogs, changelogs, RFCs.
2. Established outlets and conference/tutorial material.
3. Community answers (Q&A sites, GitHub issues) - fine for symptoms and
   workarounds, weak for specifications.
4. Aggregators, mirrors, low-effort rewrites - only as a last resort, and
   never as the single source for a surprising claim.

Cross-check surprising claims against a second independent domain before
presenting them as fact.

## Reading pattern for multi-page questions

- Read the most authoritative page first; go deeper only where it is
  still vague (hard cap: 3 reads per question, 4000 chars each).
- Prefer `--markdown` when you plan to re-structure the page as an
  outline; plain text is otherwise enough.
- When several pages look relevant but you can only afford one more read,
  pick the one with the most specific match for the question, and name
  the others as "not opened".

## Feeds and aggregation

- `read` auto-detects RSS/Atom: output lists item titles, links and
  dates; `--json` additionally carries per-item fields (`kind: "rss"`).
- Feed text is item metadata, not full articles: to actually use an
  item, `read` its link (still under the same 3-read cap).
- For "what's new on X" questions, read the feed, sort by date, and cite
  item links - do not treat the feed date as the article's publication
  time.

## Raw JSON endpoints

- `read` passes JSON bodies through verbatim (field `kind: "json"`).
  Useful for API status pages and public API responses.
- JSON is data, not prose: quote the fields you used, and say which field
  each number came from. Never invent fields you did not see.

## Citation format

- Cite the page title (or a clear label) plus the final URL, as a list
  at the end of the answer.
- Quote page fragments as short verbatim quotes; say "quote" when you
  quote, and keep quotes under ~25 words each.
- When you used metadata (publishedTime, author), cite it as metadata of
  that page, not as your own research.
- When the page was behind a paywall or the useful part was not
  extracted (exit 1), say that explicitly - do not cite what you did not
  read.

## Etiquette

One fetch per page per question; re-running the same failed URL within
one question is wasted reads. Prefer static, official pages over scraping
many pages of one site in a row. This tool fetches public pages only,
at human speed.
