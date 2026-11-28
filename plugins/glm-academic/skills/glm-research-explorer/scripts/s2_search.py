#!/usr/bin/env python3
"""
s2_search.py — Semantic Scholar Graph API 结构化学术检索（匿名、无 key）

等效定位：为 glm-research-explorer 提供"结构化论文元数据"检索（标题/作者/年份/
venue/引用数/URL），接替源 skill 里的宿主学术检索组件。纯 Python 标准库
（argparse/json/sys/urllib.request/urllib.parse），零第三方包、零 API key。

用法：
    python3 s2_search.py --query "federated learning survey" --limit 10
    python3 s2_search.py --query "..." --limit 10 --since-year 2023 --json
    python3 s2_search.py --query "..." --min-citations 50

退出码：
    0  成功（stdout 输出结果）
    1  API 返回为空或字段缺失导致的解析失败（可改走 web 检索降级）
    2  参数错误（argparse）或网络不可达（网络态详见 stderr 提示）

限流：匿名端点约 1 req/s，多维度检索请在两次调用之间 sleep 1 秒以上。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,authors,year,venue,citationCount,externalIds,url"
TIMEOUT = 20


def build_url(query: str, limit: int) -> str:
    q = urllib.parse.urlencode({"query": query, "limit": limit, "fields": FIELDS})
    return f"{API}?{q}"


def fetch(url: str) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": "glm-research-explorer/1.0.0 (local CLI)"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize(raw: dict) -> list[dict]:
    out = []
    for p in raw.get("data", []):
        if not p.get("title"):
            continue
        url = p.get("url") or ""
        ext = p.get("externalIds") or {}
        doi = ext.get("DOI")
        arxiv = ext.get("ArXiv")
        if not url and doi:
            url = f"https://doi.org/{doi}"
        if not url and arxiv:
            url = f"https://arxiv.org/abs/{arxiv}"
        out.append({
            "title": p["title"],
            "authors": ", ".join(a.get("name", "") for a in (p.get("authors") or [])[:6]),
            "year": p.get("year"),
            "venue": p.get("venue") or "",
            "citations": p.get("citationCount") or 0,
            "url": url,
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Semantic Scholar structured paper search")
    ap.add_argument("--query", required=True, help="检索词（英文效果最佳）")
    ap.add_argument("--limit", type=int, default=10,
                    help="返回条数（默认 10，上限 20）")
    ap.add_argument("--since-year", type=int, default=None,
                    help="只保留该年份及以后的论文（可选）")
    ap.add_argument("--min-citations", type=int, default=None,
                    help="只保留引用数不低于该值的论文（可选）")
    ap.add_argument("--json", action="store_true", help="以 JSON 数组输出")
    args = ap.parse_args()

    if not (1 <= args.limit <= 20):
        print("✗ --limit 必须在 1..20", file=sys.stderr)
        sys.exit(2)

    url = build_url(args.query, args.limit)
    try:
        raw = fetch(url)
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}（匿名端点限流或查询过频；等 2 秒重试一次）", file=sys.stderr)
        time.sleep(2)
        try:
            raw = fetch(url)
        except Exception as e2:
            print(f"✗ 重试仍失败：{e2}", file=sys.stderr)
            print("✗ 降级建议：改用 glm-web-search 插件的 glmws.py search 做通用检索", file=sys.stderr)
            sys.exit(2)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"✗ 网络不可达：{e}", file=sys.stderr)
        print("✗ 降级建议：改用 glm-web-search 插件的 glmws.py search 做通用检索", file=sys.stderr)
        sys.exit(2)

    papers = normalize(raw)
    if args.since_year is not None:
        papers = [p for p in papers if (p["year"] or 0) >= args.since_year]
    if args.min_citations is not None:
        papers = [p for p in papers if p["citations"] >= args.min_citations]

    if not papers:
        print("✗ 无可用结果（空响应或被过滤光）——改写检索词或降级 web 检索", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(papers, ensure_ascii=False, indent=2))
    else:
        for i, p in enumerate(papers, 1):
            year = p["year"] if p["year"] else "?"
            venue = p["venue"] if p["venue"] else "preprint/unknown"
            print(f"{i}. {p['title']}")
            print(f"   {venue}, {year} · cites={p['citations']} · {p['authors']}")
            print(f"   {p['url']}")
        print(f"\n# {len(papers)} papers · query={args.query!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
