#!/usr/bin/env python3
"""seocheck.py — deterministic on-page SEO checklist auditor (pure stdlib).

Audits a markdown draft against the SEO Content Writer checklist and prints a
scored report. Read-only: never edits the draft.

Usage:
    python3 seocheck.py <draft.md> [--keyword "primary keyword"]
                        [--meta "meta description"] [--format markdown|json]

Checks (per the skill's On-Page SEO / Final SEO Review tables):
    title_len   first H1 text length <= 60 chars
    meta_len    meta description length 150-160 (skipped if --meta absent)
    h1_unique   exactly one H1 in the document
    kw_h1       primary keyword appears in the H1
    kw_first100 primary keyword appears within the first 100 body words
    kw_h2       primary keyword appears in at least one H2
    faq         FAQ section present with >= 3 question headings
    chunking    body paragraphs average 3-5 sentences (CORE-EEAT O06)
    words       word count >= 800 for substantive content
    links       internal links 2-5 and external links >= 2
    density     primary keyword density within 1-2% (guideline, not hard rule)

Exit codes: 0 audit completed (any score), 1 argument/file errors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FAQ_HEADINGS = ("frequently asked questions", "常见问题", "faq")
OK, WARN, FAIL = "✅", "⚠️", "❌"


def _words(text: str) -> list[str]:
    # CJK chars count as one word each; latin sequences as one word
    tokens: list[str] = []
    for run in re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9'-]+", text):
        tokens.append(run)
    return tokens


def audit(md: str, keyword: str | None, meta: str | None) -> dict:
    lines = md.splitlines()
    h1s = [l[2:].strip() for l in lines if re.match(r"^#\s+", l)]
    h2s = [l[3:].strip() for l in lines if re.match(r"^##\s+", l)]
    h3s = [l[4:].strip() for l in lines if re.match(r"^###\s+", l)]
    title = h1s[0] if h1s else ""
    body = "\n".join(l for l in lines if not l.lstrip().startswith("#"))

    results: list[dict] = []

    def add(item: str, status: str, notes: str) -> None:
        results.append({"item": item, "status": status, "notes": notes})

    # 1. title length
    tlen = len(title)
    add("title_len", OK if tlen <= 60 else WARN,
        f"{tlen} chars" + ("" if tlen <= 60 else " — over 60, trim for full SERP display"))

    # 2. meta description
    if meta is None:
        add("meta_len", WARN, "meta description not supplied (pass --meta to audit it)")
    else:
        mlen = len(meta)
        status = OK if 150 <= mlen <= 160 else WARN
        add("meta_len", status, f"{mlen} chars" + ("" if status == OK else " — target 150-160"))

    # 3. single H1
    add("h1_unique", OK if len(h1s) == 1 else FAIL,
        f"{len(h1s)} H1 found" + ("" if len(h1s) == 1 else " — exactly one required"))

    # keyword-dependent checks
    kw = (keyword or "").strip().lower()
    if kw:
        in_h1 = kw in title.lower()
        add("kw_h1", OK if in_h1 else FAIL, "primary keyword in H1" if in_h1 else "primary keyword missing from H1")

        first100 = " ".join(_words(body)[:100])
        in_first = kw in first100.lower()
        add("kw_first100", OK if in_first else WARN,
            "keyword within first 100 body words" if in_first else "not in first 100 words — front-load it")

        in_h2 = any(kw in h.lower() for h in h2s)
        add("kw_h2", OK if in_h2 else WARN,
            "primary keyword in an H2" if in_h2 else "no H2 carries the primary keyword")

        total_w = len(_words(body))
        kw_hits = body.lower().count(kw)
        density = (kw_hits / total_w * 100) if total_w else 0.0
        add("density", OK if 1.0 <= density <= 2.0 else WARN,
            f"{density:.2f}% (guideline 1-2%; semantic coverage beats exact counts)")
    else:
        for item in ("kw_h1", "kw_first100", "kw_h2", "density"):
            add(item, WARN, "no --keyword supplied")

    # 4. FAQ section with >= 3 questions
    faq_idx = None
    lowered = [l.lower() for l in lines]
    for i, l in enumerate(lowered):
        if re.match(r"^#{2,3}\s+", l):
            head = re.sub(r"^#{2,3}\s+", "", l).strip().rstrip("?")
            if any(f in head for f in FAQ_HEADINGS):
                faq_idx = i
                break
    if faq_idx is None:
        add("faq", FAIL, "no FAQ section found (need >= 3 questions)")
    else:
        # count question headings until the next same-or-higher level heading
        qcount = 0
        for l in lines[faq_idx + 1:]:
            m = re.match(r"^(#{2,3})\s+", l)
            if m:
                if len(m.group(1)) <= 3 and any(f in l.lower() for f in FAQ_HEADINGS):
                    continue
                if len(m.group(1)) <= 2:  # next H2 ends the FAQ block
                    break
                qcount += 1
        add("faq", OK if qcount >= 3 else WARN,
            f"{qcount} questions" + ("" if qcount >= 3 else " — need >= 3 for PAA optimization"))

    # 5. paragraph chunking (3-5 sentences average)
    paras: list[str] = []
    cur: list[str] = []
    for l in lines:
        if not l.strip():
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        if l.lstrip().startswith(("#", ">", "-", "*", "|", "```", "[")):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        cur.append(l.strip())
    if cur:
        paras.append(" ".join(cur))
    sent_counts = []
    for p in paras:
        sent_counts.append(max(1, len(re.findall(r"[.!?。！？]", p))))
    if sent_counts:
        avg = sum(sent_counts) / len(sent_counts)
        longs = sum(1 for c in sent_counts if c > 5)
        status = OK if 3 <= avg <= 5 else WARN
        add("chunking", status,
            f"avg {avg:.1f} sentences/paragraph, {longs} over 5-sentence paragraphs (O06: 3-5)")
    else:
        add("chunking", WARN, "no plain paragraphs detected")

    # 6. word count
    wc = len(_words(md))
    add("words", OK if wc >= 800 else WARN,
        f"{wc} words" + ("" if wc >= 800 else " — substantive content targets >= 800"))

    # 7. links
    internal = len(re.findall(r"\]\(/", md))
    external = len(re.findall(r"\]\(https?://", md))
    add("links", OK if (2 <= internal <= 5 and external >= 2) else WARN,
        f"internal {internal} (target 2-5), external {external} (target >= 2)")

    score_map = {OK: 1.0, WARN: 0.5, FAIL: 0.0}
    raw = sum(score_map[r["status"]] for r in results)
    overall = round(raw / len(results) * 10, 1)

    return {"checks": results, "overall_score": overall,
            "summary": f"{overall}/10 — {sum(1 for r in results if r['status'] == WARN)} warn, "
                       f"{sum(1 for r in results if r['status'] == FAIL)} fail"}


def render_markdown(rep: dict) -> str:
    out = ["### Content SEO Score", "",
           "| Factor | Status | Notes |", "|--------|--------|-------|"]
    for r in rep["checks"]:
        out.append(f"| {r['item']} | {r['status']} | {r['notes']} |")
    out.append("")
    out.append(f"**Overall SEO Score**: {rep['overall_score']}/10")
    warn = [r["item"] for r in rep["checks"] if r["status"] == WARN]
    fail = [r["item"] for r in rep["checks"] if r["status"] == FAIL]
    if fail:
        out.append("")
        out.append("**Must fix**: " + ", ".join(fail))
    if warn:
        out.append("")
        out.append("**Improvements to consider**: " + ", ".join(warn))
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic on-page SEO checklist auditor (read-only)")
    ap.add_argument("draft", type=Path, help="markdown draft path")
    ap.add_argument("--keyword", default=None, help="primary keyword")
    ap.add_argument("--meta", default=None, help="meta description text (audit its length)")
    ap.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = ap.parse_args()

    try:
        md = args.draft.read_text(encoding="utf-8")
    except OSError as e:
        print(f"cannot read {args.draft}: {e}", file=sys.stderr)
        return 1

    rep = audit(md, args.keyword, args.meta)
    if args.format == "json":
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
