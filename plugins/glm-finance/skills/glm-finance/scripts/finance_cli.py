#!/usr/bin/env python3
"""glm-finance 金融数据 CLI：等效替换源 skill 的 Finance API 网关调用。
用户本地不部署 web-dev-ai-gateway，本脚本改用**免 key 公共端点**：

  主链  Yahoo Finance 公共接口（query1/query2/feeds，零 key、需浏览器 UA）
  兜底  腾讯行情（qt.gtimg.cn 实时 + web.ifzq.gtimg.cn 日K，零 key、国内网络友好，
        覆盖美股 usAAPL / A股 sh600519 / 港股 hk00700）

子命令（默认 Markdown 表格输出，各子命令带 --json 可切 JSON）:
  search  <query>            股票/公司检索 → 符号清单          （源: v1/markets/search）
  quote   <sym> [sym...]     实时报价（最新价/涨跌/量）          （源: v1/markets/quote 与批量 stock/quotes）
  history <sym>              历史K线（interval/range 可调）      （源: v1|v2/markets/stock/history）
  news    [sym]              市场新闻（个股 RSS / 大盘 RSS）     （源: v1|v2/markets/news）
  modules <sym> <module...>  公司资料/财报/统计等数据模块        （源: v1/markets/stock/modules）

模块别名（源 skill 模块名 → Yahoo quoteSummary 模块；两者都可直接传）:
  asset-profile→assetProfile  statistics→defaultKeyStatistics  financial-data→financialData
  income-statement→incomeStatementHistory  balance-sheet→balanceSheetHistory
  cashflow-statement→cashflowStatementHistory  calendar-events→calendarEvents
  sec-filings→secFilings  earnings→earnings  insider-transactions→insiderTransactions
  recommendation-trend  upgrade-downgrade-history  institution-ownership  fund-ownership
  net-share-purchase-activity  index-trend  sector-trend  industry-trend

provider 链：auto = Yahoo 主链、失败自动落腾讯行情兜底（quote/history）；
tencent = 直接走腾讯链（国内网络首选兜底）。
退出码: 0 成功 / 1 用法错误（未知模块、A股缺前缀等） / 2 网络或端点失败（stderr 报因，不假死）。
"""
import argparse
import datetime as _dt
import email.utils as _eu
import http.cookiejar as _cj
import json
import re
import sys
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 15

Q1 = "https://query1.finance.yahoo.com"
Q2 = "https://query2.finance.yahoo.com"
FEED = "https://feeds.finance.yahoo.com/rss/2.0/headline"
GENERAL_NEWS = "https://finance.yahoo.com/news/rssindex"
TQT = "http://qt.gtimg.cn/q="
TKLINE = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

MODULE_ALIASES = {
    "asset-profile": "assetProfile",
    "statistics": "defaultKeyStatistics",
    "financial-data": "financialData",
    "income-statement": "incomeStatementHistory",
    "balance-sheet": "balanceSheetHistory",
    "cashflow-statement": "cashflowStatementHistory",
    "calendar-events": "calendarEvents",
    "sec-filings": "secFilings",
    "earnings": "earnings",
    "insider-transactions": "insiderTransactions",
    "insider-holders": "insiderHolders",
    "recommendation-trend": "recommendationTrend",
    "upgrade-downgrade-history": "upgradeDowngradeHistory",
    "institution-ownership": "institutionOwnership",
    "fund-ownership": "fundOwnership",
    "net-share-purchase-activity": "netSharePurchaseActivity",
    "index-trend": "indexTrend",
    "sector-trend": "sectorTrend",
    "industry-trend": "industryTrend",
}
VALID_MODULES = set(MODULE_ALIASES) | set(MODULE_ALIASES.values())

RANGE_TO_COUNT = {"1d": 2, "5d": 6, "1mo": 30, "3mo": 90, "6mo": 130, "1y": 260,
                  "2y": 520, "5y": 1300, "10y": 2600, "ytd": 260, "max": 10000}


# ───────────────────────── 网络层（纯 urllib） ─────────────────────────

def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def get_json(url: str) -> dict:
    return json.loads(http_get(url).decode("utf-8", "replace"))


def net_fail(where: str, why: str) -> None:
    print(f"[net-fail] {where}: {why}", file=sys.stderr)
    print("hint: 检查网络/代理；quote/history 可用 --provider tencent 走腾讯行情"
          "兜底链（国内网络友好）；modules 受限网络可改用 quote/history 子命令。",
          file=sys.stderr)
    sys.exit(2)


# ───────────────────────── Yahoo 主链 ─────────────────────────

def yahoo_search(query: str, limit: int = 8) -> list:
    url = (Q1 + "/v1/finance/search?q=" + urllib.request.quote(query)
           + f"&quotesCount={limit}&newsCount=0")
    try:
        data = get_json(url)
    except (urllib.error.URLError, OSError, ValueError) as e:
        net_fail("search", str(e))
    out = []
    for q in data.get("quotes", []):
        if q.get("symbol"):
            out.append({"symbol": q["symbol"],
                        "name": q.get("shortname") or q.get("longname") or "",
                        "exchange": q.get("exchange") or "",
                        "type": q.get("quoteType") or ""})
    return out[:limit]


def yahoo_chart_quote(symbol: str) -> dict:
    url = f"{Q1}/v8/finance/chart/{urllib.request.quote(symbol)}?range=5d&interval=1d"
    try:
        data = get_json(url)
    except (urllib.error.URLError, OSError, ValueError) as e:
        net_fail(f"quote {symbol}", str(e))
    res = data.get("chart", {}).get("result") or []
    if not res:
        net_fail(f"quote {symbol}", "chart result empty（符号不存在或被限流）")
    meta = res[0].get("meta", {})
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        net_fail(f"quote {symbol}", "regularMarketPrice missing")
    chg = (price - prev) if (price is not None and prev is not None) else None
    return {"symbol": meta.get("symbol", symbol),
            "name": meta.get("shortName") or meta.get("longName") or "",
            "currency": meta.get("currency", ""),
            "exchange": meta.get("exchangeName", ""),
            "price": price, "previous_close": prev, "change": chg,
            "change_pct": (round(chg / prev * 100, 2) if prev else None),
            "volume": meta.get("regularMarketVolume"),
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow")}


def yahoo_history(symbol: str, interval: str = "1d", rng: str = "1y") -> list:
    url = (f"{Q1}/v8/finance/chart/{urllib.request.quote(symbol)}"
           f"?range={rng}&interval={interval}")
    try:
        data = get_json(url)
    except (urllib.error.URLError, OSError, ValueError) as e:
        net_fail(f"history {symbol}", str(e))
    res = data.get("chart", {}).get("result") or []
    if not res:
        net_fail(f"history {symbol}", "chart result empty")
    r = res[0]
    ts = r.get("timestamp") or []
    q = (r.get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    for i, t in enumerate(ts):
        row = {"date": _dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d")}
        for k in ("open", "high", "low", "close", "volume"):
            series = q.get(k) or []
            row[k] = series[i] if i < len(series) else None
        if row["close"] is not None:
            rows.append(row)
    return rows


def yahoo_news(symbol, limit: int = 10) -> list:
    url = f"{FEED}?s={urllib.request.quote(symbol)}" if symbol else GENERAL_NEWS
    try:
        xml = http_get(url).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        net_fail("news", str(e))
    items = []
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S)[:limit]:
        title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
        link = re.search(r"<link>(.*?)</link>", block, re.S)
        date = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        when = ""
        if date:
            try:
                when = _eu.parsedate_to_datetime(date.group(1)).strftime("%Y-%m-%d %H:%M")
            except Exception:
                when = date.group(1)
        items.append({"title": (title.group(1) if title else "").strip(),
                      "link": (link.group(1) if link else "").strip(),
                      "published": when})
    return items


def yahoo_quote_summary(symbol: str, modules: list) -> dict:
    """v10 quoteSummary 需要 crumb：fc.yahoo.com 取 cookie → getcrumb → 带 crumb+cookie 请求。"""
    mods = ",".join(dict.fromkeys(modules))
    cj = _cj.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", UA)]
    try:
        try:
            opener.open("https://fc.yahoo.com/", timeout=TIMEOUT)
        except urllib.error.HTTPError:
            pass  # 404/500 也发 Set-Cookie，忽略状态码
        with opener.open(Q2 + "/v1/test/getcrumb", timeout=TIMEOUT) as r:
            crumb = r.read().decode("utf-8", "replace").strip()
        if not crumb:
            net_fail("modules", "crumb 为空")
        url = (f"{Q2}/v10/finance/quoteSummary/{urllib.request.quote(symbol)}"
               f"?modules={mods}&crumb={urllib.request.quote(crumb)}")
        with opener.open(url, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        net_fail("modules", f"HTTP {e.code}（quoteSummary 需 crumb+cookie 流程；"
                           f"受限网络可改用 quote/history 子命令，或 "
                           f"uv run --with yfinance 兜底）")
    except (urllib.error.URLError, OSError, ValueError) as e:
        net_fail("modules", str(e))


# ───────────────────────── 腾讯行情兜底链 ─────────────────────────

def tencent_code(symbol: str) -> str:
    """符号归一：美股 usAAPL；A股 sh600519/sz000001（必须带前缀）；港股 hk00700。"""
    s = symbol.strip()
    if s.lower().startswith(("sh", "sz", "hk", "us")):
        return s                       # 已带交易所前缀，原样
    if s.isdigit():
        if len(s) == 5:
            return "hk" + s            # 港股 5 位纯数字 → hk00700
        print("usage: A股 6 位代码请带交易所前缀（sh600519 / sz000001）", file=sys.stderr)
        sys.exit(1)
    return "us" + s.upper()            # 其余按美股处理


def _f(v):
    try:
        return float(v) if v not in (None, "N/D", "") else None
    except (TypeError, ValueError):
        return None


def tencent_quote(symbols: list) -> list:
    codes = [tencent_code(s) for s in symbols]
    try:
        text = http_get(TQT + ",".join(codes)).decode("gbk", "replace")
    except (urllib.error.URLError, OSError) as e:
        net_fail("tencent quote", str(e))
    rows = []
    for line in text.split(";"):
        m = re.match(r'v_([^=]+)="(.*)"', line.strip())
        if not m:
            continue
        code, f = m.group(1), m.group(2).split("~")
        if len(f) < 36:
            continue
        d = f[30]                                   # 日期归一（US 带分隔符；A股为 14 位紧凑串）
        if len(d) == 14 and d.isdigit():
            d = f"{d[:4]}-{d[4:6]}-{d[6:8]} {d[8:10]}:{d[10:12]}:{d[12:14]}"
        if code.startswith("us"):
            cur = f[35] or "USD"
        elif code.startswith(("sh", "sz")):
            cur = "CNY"
        elif code.startswith("hk"):
            cur = "HKD"
        else:
            cur = f[35] or None
        rows.append({"symbol": f[2], "name": f[1], "price": _f(f[3]),
                     "previous_close": _f(f[4]), "open": _f(f[5]), "volume": _f(f[6]),
                     "date": d, "change": _f(f[31]), "change_pct": _f(f[32]),
                     "high": _f(f[33]), "low": _f(f[34]), "currency": cur})
    if not rows:
        net_fail("tencent quote", "响应无可解析行情行（符号可能不存在）")
    return rows


def tencent_history(symbol: str, rng: str = "1y", limit: int = 0) -> list:
    code = tencent_code(symbol)
    if code.startswith("us") and "." not in code:
        # 美股无后缀代码在小 count 下会混入锚定行；先经 qt 解析规范代码（AAPL → AAPL.OQ）
        try:
            canon = tencent_quote([symbol])[0]["symbol"]
            if "." in canon:
                code = "us" + canon
        except (SystemExit, IndexError):
            pass  # 解析失败则按原代码请求
    count = RANGE_TO_COUNT.get(rng, 260)
    url = f"{TKLINE}?param={code},day,,,{count},qfq"
    try:
        data = get_json(url)
    except (urllib.error.URLError, OSError, ValueError) as e:
        net_fail(f"tencent history {symbol}", str(e))
    node = (data.get("data", {}).get(code)) or {}
    k = node.get("day") or node.get("qfqday") or []
    rows = [{"date": r[0], "open": _f(r[1]), "close": _f(r[2]),
             "high": _f(r[3]), "low": _f(r[4]), "volume": _f(r[5])}
            for r in k if len(r) >= 6 and r[0]]
    if not rows:
        net_fail(f"tencent history {symbol}", "kline 数据为空（符号可能不存在）")
    return rows[-limit:] if limit else rows


# ───────────────────────── 输出格式化 ─────────────────────────

def _fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:,.2f}".rstrip("0").rstrip(".") if v == int(v) else f"{v:,.2f}"
    return str(v)


def md_table(rows: list, cols: list) -> str:
    if not rows:
        return "(no rows)"
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(_fmt(r.get(c)) for c in cols) + " |")
    return "\n".join(lines)


def emit(rows, as_json: bool, cols):
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(md_table(rows, cols) if isinstance(rows, list) else rows)


# ───────────────────────── 子命令 ─────────────────────────

YQ_COLS = ["symbol", "name", "price", "previous_close", "change", "change_pct",
           "volume", "currency", "fifty_two_week_high", "fifty_two_week_low"]
TQ_COLS = ["symbol", "name", "price", "previous_close", "change", "change_pct",
           "open", "high", "low", "volume", "date", "currency"]


def cmd_search(a) -> int:
    rows = yahoo_search(a.query, a.limit)
    emit(rows, a.json, ["symbol", "name", "exchange", "type"])
    return 0


def cmd_quote(a) -> int:
    if a.provider == "tencent":
        rows = tencent_quote(a.symbols)
        emit(rows, a.json, TQ_COLS)
        return 0
    rows = []
    yahoo_mode = True
    for s in a.symbols:
        try:  # auto：Yahoo 主链失败（net_fail 内部 exit 2）→ 腾讯行情兜底
            rows.append(yahoo_chart_quote(s))
        except SystemExit:
            print(f"[fallback] Yahoo 失败 → 腾讯行情兜底（{s}）", file=sys.stderr)
            rows += tencent_quote([s])
            yahoo_mode = False
    emit(rows, a.json, YQ_COLS if yahoo_mode else
         (YQ_COLS if all("fifty_two_week_high" in r for r in rows) else TQ_COLS))
    return 0


def cmd_history(a) -> int:
    if a.provider == "tencent":
        rows = tencent_history(a.symbol, a.range, a.limit)
    else:
        try:
            rows = yahoo_history(a.symbol, a.interval, a.range)
        except SystemExit:  # auto 兜底：Yahoo 失败 → 腾讯日K
            print(f"[fallback] Yahoo 失败 → 腾讯日K兜底（{a.symbol}，日线）",
                  file=sys.stderr)
            rows = tencent_history(a.symbol, a.range, a.limit)
    if a.limit:
        rows = rows[-a.limit:]
    emit(rows, a.json, ["date", "open", "high", "low", "close", "volume"])
    return 0


def cmd_news(a) -> int:
    rows = yahoo_news(a.symbol, a.limit)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print("\n".join(f"- [{x['title']}]({x['link']})（{x['published']}）"
                        for x in rows) or "(no items)")
    return 0


def cmd_modules(a) -> int:
    unknown = [x for x in a.modules if x not in VALID_MODULES]
    if unknown:
        print(f"unknown modules: {unknown}；可用：源模块名（asset-profile/statistics/"
              f"financial-data/income-statement/…）或 Yahoo 模块名（别名表见脚本头注释）",
              file=sys.stderr)
        return 1
    mods = [MODULE_ALIASES.get(x, x) for x in a.modules]
    data = yahoo_quote_summary(a.symbol, mods)
    result = (data.get("quoteSummary", {}).get("result")) or [data]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(
        description="glm-finance: 免 key 金融数据 CLI（Yahoo 公共端点主链 + 腾讯行情兜底，"
                    "等效替换源 Finance API 网关）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("search", help="股票/公司检索（源: v1/markets/search）")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("quote", help="实时报价（auto: Yahoo→腾讯兜底；tencent: 直接兜底链）")
    p.add_argument("symbols", nargs="+")
    p.add_argument("--provider", choices=["auto", "tencent"], default="auto")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_quote)

    p = sub.add_parser("history", help="历史K线（源: v1|v2/markets/stock/history）")
    p.add_argument("symbol")
    p.add_argument("--interval", default="1d",
                   choices=["1m", "2m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo", "3mo"],
                   help="默认 1d（腾讯链固定日线）")
    p.add_argument("--range", default="1y",
                   choices=list(RANGE_TO_COUNT), help="默认 1y")
    p.add_argument("--limit", type=int, default=0, help="只保留最近 N 根（0=全部）")
    p.add_argument("--provider", choices=["auto", "tencent"], default="auto")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("news", help="市场新闻（个股 RSS / 大盘 RSS；源: v1|v2/markets/news）")
    p.add_argument("symbol", nargs="?", default=None)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_news)

    p = sub.add_parser("modules", help="公司资料/财报/统计等数据模块（quoteSummary + crumb）")
    p.add_argument("symbol")
    p.add_argument("modules", nargs="+",
                   help="asset-profile statistics financial-data income-statement …（别名表见头注释）")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_modules)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
