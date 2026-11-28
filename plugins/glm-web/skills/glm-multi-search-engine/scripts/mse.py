#!/usr/bin/env python3
"""
mse.py — 8 个国内搜索引擎统一 CLI（无 API key、纯 Python 标准库）

等效定位：接替源 skill 的宿主页面抓取组件（对 8 引擎 URL 的 fetch 调用）。
构造引擎 URL → 伪装 UA 抓取 → 启发式提取结果链接。通用高质量检索走
glm-web-search 插件的 glmws.py（Bing 主引擎）；本 CLI 覆盖国内引擎面：
百度 / 必应CN / 必应INT / 360 / 搜狗 / 微信公众号 / 头条 / 集思录。

用法：
    python3 mse.py engines
    python3 mse.py search --engine baidu --query "python 教程" [--max 8] [--json]
    python3 mse.py fetch "<URL>" [--max-chars 4000] [--raw]

退出码：
    0  成功
    1  检索无可用结果（换引擎 / 改写查询）
    2  参数错误或网络不可达 / 目标引擎拒绝（反爬、验证码页）

解析为启发式（各引擎页面结构差异大）；结果标题+链接，快照正文用
fetch 逐条获取。反爬视目标站点而定：微信/搜狗常带验证码页，
命中时 exit 2 并建议换引擎。
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ENGINES = {
    "baidu":   ("Baidu",   "https://www.baidu.com/s?wd={keyword}"),
    "bingcn":  ("Bing CN", "https://cn.bing.com/search?q={keyword}&ensearch=0"),
    "bingint": ("Bing INT", "https://cn.bing.com/search?q={keyword}&ensearch=1"),
    "so360":   ("360",     "https://www.so.com/s?q={keyword}"),
    "sogou":   ("Sogou",   "https://sogou.com/web?query={keyword}"),
    "wechat":  ("WeChat",  "https://wx.sogou.com/weixin?type=2&query={keyword}"),
    "toutiao": ("Toutiao", "https://so.toutiao.com/search?keyword={keyword}"),
    "jisilu":  ("Jisilu",  "https://www.jisilu.cn/explore/?keyword={keyword}"),
}

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 20
SELF_HOSTS = {
    "www.baidu.com", "cn.bing.com", "www.so.com", "sogou.com", "wx.sogou.com",
    "so.toutiao.com", "www.jisilu.cn", "www.baidu.com/s",
}


def decode_body(resp) -> str:
    raw = resp.read()
    charset = None
    ctype = resp.headers.get("Content-Type", "")
    m = re.search(r"charset=([\w-]+)", ctype, re.I)
    if m:
        charset = m.group(1)
    for cs in filter(None, [charset, "utf-8", "gbk", "gb18030"]):
        try:
            return raw.decode(cs)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return decode_body(resp)


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return html_mod.unescape(re.sub(r"\s+", " ", s)).strip()


def extract_results(html: str, engine_url: str) -> list[dict]:
    out, seen = [], set()
    engine_host = urllib.parse.urlsplit(engine_url).netloc
    for href, inner in re.findall(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S):
        href = href.strip()
        if href.startswith("//"):
            href = "https:" + href
        if not href.startswith(("http://", "https://")):
            continue
        title = strip_tags(inner)
        if not (6 <= len(title) <= 200):
            continue
        host = urllib.parse.urlsplit(href).netloc
        if not host or host == engine_host or host in SELF_HOSTS:
            continue
        if href in seen:
            continue
        seen.add(href)
        out.append({"title": title, "url": href})
        if len(out) >= 24:
            break
    return out


def looks_like_captcha(html: str) -> bool:
    low = html.lower()
    return any(k in low for k in (
        "验证码", "verify", "captcha", "antirobot", "访问异常", "异常流量"))


def cmd_engines() -> int:
    for i, (eid, (name, url)) in enumerate(ENGINES.items(), 1):
        print(f"{i}. {eid:<8} {name:<9} {url}")
    print(f"\n# {len(ENGINES)} engines · all keyless", file=sys.stderr)
    return 0


def cmd_search(args) -> int:
    q = urllib.parse.quote_plus(args.query)
    url = ENGINES[args.engine][1].format(keyword=q)
    try:
        html = get(url)
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}（引擎拒绝或限流）——建议换引擎或改用 glm-web-search 的 glmws.py",
              file=sys.stderr)
        return 2
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"✗ 网络不可达：{e}——检查 Codex 沙箱网络授权", file=sys.stderr)
        return 2

    if looks_like_captcha(html):
        print("✗ 命中验证码/反爬页——建议换引擎（bingcn 较稳）或改用 glm-web-search",
              file=sys.stderr)
        return 2

    results = extract_results(html, url)[: args.max]
    if not results:
        print("✗ 无可用结果——改写查询或换引擎（mse.py engines 查看全部）", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['title']}")
            print(f"   {r['url']}")
        print(f"\n# {len(results)} results · engine={args.engine} · heuristic parse", file=sys.stderr)
    return 0


def cmd_fetch(args) -> int:
    try:
        html = get(args.url)
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}", file=sys.stderr)
        return 2
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"✗ 网络不可达：{e}", file=sys.stderr)
        return 2
    if args.raw:
        print(html[: args.max_chars])
    else:
        text = strip_tags(html)
        print(text[: args.max_chars])
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="8 CN search engines, keyless, pure stdlib")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("engines", help="列出引擎注册表")

    sp = sub.add_parser("search", help="引擎检索（启发式解析）")
    sp.add_argument("--engine", required=True, choices=list(ENGINES))
    sp.add_argument("--query", required=True)
    sp.add_argument("--max", type=int, default=8, help="返回条数（默认 8）")
    sp.add_argument("--json", action="store_true")

    fp = sub.add_parser("fetch", help="抓取任意 URL 为纯文本")
    fp.add_argument("url")
    fp.add_argument("--max-chars", type=int, default=4000)
    fp.add_argument("--raw", action="store_true", help="输出原始 HTML 截断")

    args = ap.parse_args()
    if args.cmd == "engines":
        sys.exit(cmd_engines())
    if args.cmd == "search":
        sys.exit(cmd_search(args))
    sys.exit(cmd_fetch(args))


if __name__ == "__main__":
    main()
