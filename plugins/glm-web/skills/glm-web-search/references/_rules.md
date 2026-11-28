# GLM Web Search — Deep Rules

Load this file only for multi-round research, source-quality disputes, or
when the user asks how to cite. For a plain question, SKILL.md is enough.

## When a single search is NOT enough

| Situation | Do this |
|---|---|
| Result snippets disagree with each other | Search the exact disputed term + `官方` / `official` / `site:example.com`, take the vendor or official-documentation source |
| The question spans multiple facets (price AND release date AND specs) | One search per facet; keep `--num 5` per call; answer per facet |
| Numbers matter (prices, market share, version counts) | Cross-check at least two independent domains before writing the number; if only one source has it, mark it "single source" in the answer |
| The best result is a non-English page you cannot read from the snippet | `fetch` the URL; the extractor handles CJK pages fine |
| Results look stale for a "latest" question | Re-run with `--recency-days 7` and a fresher query (add the year, `latest`, `最新`) |

## Source-quality ladder (prefer higher)

1. Official vendor/project documentation and release pages (docs.*, developer.*, *.org, *.gov)
2. Primary press or wire coverage, established outlets
3. Major tech media and encyclopedia entries
4. Aggregators, content farms, forum threads - use only as a lead, never as the citation for a number

Forum and aggregator snippets are allowed to *find* things; cite the page
they point to, not the aggregator, whenever both exist.

## Citation format

End the answer with a sources list; one line per source actually used:

```
来源 / Sources:
- [Page title](URL) — the specific claim it backs (one short phrase)
- ...
```

Rules:

- URLs come verbatim from tool output - never shorten, never "rebuild" one from memory.
- One line per source; the phrase after the dash states WHICH claim the source backs, not a generic description.
- If a claim in your answer has no source line, either the claim came from your own reasoning (say so) or drop the claim.
- Quote at most one sentence from any page; paraphrase the rest.
- Do not cite `favicon` URLs, redirect wrappers, or search result pages - cite the destination page.

## Multi-round research pattern (only when the user asks for deep research)

1. Wide search (`--num 10`) to map the landscape; note recurring domains.
2. One narrow search per sub-question (rewrite until exit code 0 and snippets are on-topic).
3. `fetch` the single most authoritative page per sub-question (`--max-chars 4000`).
4. Answer, then sources list; state clearly what is confirmed, what is single-sourced, and what stayed unanswered.

Budget: 5 searches + 4 fetches maximum for one research request. Stop early
when the remaining sub-questions are already answered by fetched pages.
