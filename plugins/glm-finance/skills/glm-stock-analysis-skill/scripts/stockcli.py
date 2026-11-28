#!/usr/bin/env python3
"""stockcli.py — deterministic stock-analysis engine (pure stdlib).

Local equivalent of the source skill's TypeScript modules: the scoring
engines, watchlist bookkeeping, verdict extraction, and report assembly from
src/{dividend,rumorScanner,watchlist,analyzer,index}.ts are ported function-by-
function; only the cloud-SDK data fetching (host chat completions and
the host browser storage) is replaced — market data now arrives as JSON
files prepared by the Codex agent, and the watchlist persists to a local JSON
file in the user's working directory.

Commands:
  watch add <CODE> [--target P] [--stop P] [--signal] [--price P] [--notes T] [--file W]
  watch remove <CODE> [--file W]
  watch list [--prices-file F] [--file W] [--format md|json]
  watch check [--prices-file F] [--signals-file S] [--file W] [--format md|json]
  dividend <data.json> [--format md|json]
  rumor <news.json> [--format md|json]
  report <analysis.json> [--macro-file M] [--market-file M2]
  verdict <analysis.md>

Data file formats: see references/data-schemas.md in this skill directory.

Exit codes: 0 success, 1 usage/file errors, 2 data validation errors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WATCHLIST_FILENAME = "stock_watchlist.json"
VERDICTS = ("强烈买入", "买入", "观望", "卖出")


# ── shared helpers ───────────────────────────────────────────────────────────

def detect_market(code: str) -> str:
    if re.fullmatch(r"\d{6}", code):
        return "CN"
    if re.fullmatch(r"\d{4,5}\.HK", code, re.IGNORECASE):
        return "HK"
    return "US"


MARKET_LABEL = {"CN": "A股", "HK": "港股", "US": "美股"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        print(f"cannot read {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)


# ── dividend scoring engine (ported from src/dividend.ts) ───────────────────

def calc_payout_status(payout_ratio: float | None) -> str:
    if payout_ratio is None:
        return "unknown"
    if payout_ratio < 40:
        return "safe"
    if payout_ratio < 60:
        return "moderate"
    if payout_ratio < 80:
        return "high"
    return "unsustainable"


def calc_safety_score(payout_ratio: float | None, growth5y: float | None,
                      consecutive_years: int | None,
                      dividend_yield: float | None) -> tuple[int, list[str]]:
    score = 50
    factors: list[str] = []

    if payout_ratio is not None:
        if payout_ratio < 40:
            score += 20; factors.append(f"派息率健康（{payout_ratio:.0f}%）")
        elif payout_ratio < 60:
            score += 10; factors.append(f"派息率适中（{payout_ratio:.0f}%）")
        elif payout_ratio < 80:
            score -= 10; factors.append(f"派息率偏高（{payout_ratio:.0f}%）")
        else:
            score -= 20; factors.append(f"派息率不可持续（{payout_ratio:.0f}%）")

    if growth5y is not None:
        if growth5y > 10:
            score += 15; factors.append(f"股息增长强劲（{growth5y:.1f}% CAGR）")
        elif growth5y > 5:
            score += 10; factors.append(f"股息增长良好（{growth5y:.1f}% CAGR）")
        elif growth5y > 0:
            score += 5; factors.append(f"股息小幅增长（{growth5y:.1f}% CAGR）")
        else:
            score -= 15; factors.append(f"股息下降（{growth5y:.1f}% CAGR）")

    if consecutive_years is not None:
        if consecutive_years >= 25:
            score += 15; factors.append(f"股息贵族（连续{consecutive_years}年增长）")
        elif consecutive_years >= 10:
            score += 10; factors.append(f"长期稳定股息（{consecutive_years}年）")
        elif consecutive_years >= 5:
            score += 5; factors.append(f"股息稳定（{consecutive_years}年）")

    if dividend_yield is not None:
        if dividend_yield > 8:
            score -= 10; factors.append(f"收益率过高（{dividend_yield:.1f}%），需核实可持续性")
        elif dividend_yield < 1:
            factors.append(f"收益率偏低（{dividend_yield:.2f}%）")

    return max(0, min(100, score)), factors


def calc_income_rating(safety_score: int) -> str:
    if safety_score >= 80:
        return "excellent"
    if safety_score >= 60:
        return "good"
    if safety_score >= 40:
        return "moderate"
    return "poor"


def analyze_dividend(raw: dict) -> dict:
    """raw: one dividend data object per references/data-schemas.md."""
    ticker = str(raw.get("ticker", "")).upper()
    annual = raw.get("annualDividend")
    if not annual:
        return {
            "ticker": ticker, "name": raw.get("name") or ticker,
            "currentPrice": raw.get("currentPrice"), "dividendYield": None,
            "annualDividend": None, "payoutRatio": None,
            "payoutStatus": "no_dividend", "dividendGrowth5y": None,
            "consecutiveYears": None, "exDividendDate": None,
            "paymentFrequency": None, "safetyScore": 0,
            "safetyFactors": ["该股票不派息"], "incomeRating": "no_dividend",
            "dividendHistory": [], "summary": f"{ticker} 目前不派发股息。",
        }

    trailing_eps = raw.get("trailingEps")
    annual = float(annual)
    payout_ratio = None
    if trailing_eps and float(trailing_eps) > 0:
        payout_ratio = round((annual / float(trailing_eps)) * 100, 1)

    status = calc_payout_status(payout_ratio)
    growth = raw.get("dividendGrowth5y")
    years = raw.get("consecutiveYears")
    yield_ = raw.get("dividendYield")
    score, factors = calc_safety_score(
        payout_ratio,
        float(growth) if growth is not None else None,
        int(years) if years is not None else None,
        float(yield_) if yield_ is not None else None,
    )
    rating = calc_income_rating(score)

    parts = []
    if yield_ is not None:
        parts.append(f"收益率 {float(yield_):.2f}%")
    if payout_ratio:
        parts.append(f"派息率 {payout_ratio:.0f}%")
    if growth is not None:
        g = float(growth)
        parts.append(f"5年增长 {'+' if g > 0 else ''}{g:.1f}%")
    if years is not None and int(years) >= 5:
        parts.append(f"连续增长 {int(years)} 年")
    rating_label = {"excellent": "优秀", "good": "良好", "moderate": "一般",
                    "poor": "较差", "no_dividend": "无股息"}

    return {
        "ticker": ticker, "name": raw.get("name") or ticker,
        "currentPrice": raw.get("currentPrice"),
        "dividendYield": round(float(yield_), 2) if yield_ is not None else None,
        "annualDividend": annual,
        "payoutRatio": payout_ratio, "payoutStatus": status,
        "dividendGrowth5y": round(float(growth), 2) if growth is not None else None,
        "consecutiveYears": int(years) if years is not None else None,
        "exDividendDate": raw.get("exDividendDate"),
        "paymentFrequency": raw.get("paymentFrequency"),
        "safetyScore": score, "safetyFactors": factors, "incomeRating": rating,
        "dividendHistory": raw.get("dividendHistory") or [],
        "summary": (f"{ticker}（{raw.get('name') or ''}）：{'，'.join(parts)}。"
                    f"评级：{rating_label[rating]}"),
    }


def format_dividend_markdown(a: dict) -> str:
    if a["incomeRating"] == "no_dividend":
        return f"### 💰 股息分析 · {a['ticker']}\n\n该股票目前不派发股息。"
    rating_emoji = {"excellent": "🏆", "good": "✅", "moderate": "⚠️",
                    "poor": "❌", "no_dividend": "—"}
    payout_label = {"safe": "✅ 安全", "moderate": "⚠️ 适中", "high": "⚠️ 偏高",
                    "unsustainable": "❌ 不可持续", "unknown": "暂缺"}
    md = f"""### 💰 股息分析 · {a['ticker']}（{a['name']}）

| 指标 | 数值 |
|------|------|
| 股息收益率 | {f"{a['dividendYield']}%" if a['dividendYield'] is not None else '暂缺'} |
| 年度每股股息 | {f"${a['annualDividend']}" if a['annualDividend'] else '暂缺'} |
| 派息频率 | {a['paymentFrequency'] or '暂缺'} |
| 除权日 | {a['exDividendDate'] or '暂缺'} |
| 派息率 | {f"{a['payoutRatio']}%（{payout_label[a['payoutStatus']]}）" if a['payoutRatio'] else '暂缺'} |
| 5年股息增长 | {f"{'+' if (a['dividendGrowth5y'] or 0) > 0 else ''}{a['dividendGrowth5y']}%" if a['dividendGrowth5y'] is not None else '暂缺'} |
| 连续增长年数 | {a['consecutiveYears'] if a['consecutiveYears'] is not None else '暂缺'} |

**安全评分：{a['safetyScore']}/100　{rating_emoji[a['incomeRating']]} 收入评级：{a['incomeRating'].upper()}**

评分依据：
{chr(10).join(f'- {f}' for f in a['safetyFactors'])}
"""
    if a["dividendHistory"]:
        md += "\n近年股息历史：\n"
        md += "\n".join(f"- {h.get('year')}年：${h.get('total')}"
                        for h in a["dividendHistory"][:5])
    return md


def cmd_dividend(args: argparse.Namespace) -> int:
    data = load_json_file(Path(args.data))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        print("dividend data must be a non-empty JSON array of objects", file=sys.stderr)
        return 2
    results = [analyze_dividend(item) for item in data]
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    out = (f"# 💰 股息分析报告\n**生成时间：** "
           f"{datetime.now().strftime('%Y-%m-%d')}\n\n---\n\n")
    for r in results:
        out += format_dividend_markdown(r) + "\n\n---\n\n"
    out += "_以上数据仅供参考，不构成投资建议。_"
    print(out)
    return 0


# ── rumor scoring engine (ported from src/rumorScanner.ts) ───────────────────

RUMOR_TYPES = ("ma", "insider", "analyst", "regulatory", "earnings", "general")


def calc_impact_score(rtype: str, text: str, has_high_engagement: bool = False
                      ) -> tuple[int, str]:
    score = 1
    reasons: list[str] = []
    base = {"ma": (5, "并购/收购类传闻，市场冲击最大"),
            "insider": (4, "内部人交易信号，可能预示重大动向"),
            "analyst": (3, "分析师评级调整，影响机构定价"),
            "regulatory": (3, "监管动态，直接影响经营合规性"),
            "earnings": (2, "业绩预期变动")}.get(rtype, (1, ""))
    score += base[0]
    if base[1]:
        reasons.append(base[1])
    if re.search(r"breaking|just in|alert|urgent", text, re.IGNORECASE):
        score += 2; reasons.append("突发性消息")
    if has_high_engagement:
        score += 2; reasons.append("市场高度关注")
    return min(10, score), "，".join(reasons)


def cmd_rumor(args: argparse.Namespace) -> int:
    items = load_json_file(Path(args.news))
    if not isinstance(items, list):
        print("rumor news must be a JSON array of items", file=sys.stderr)
        return 2
    rumors = []
    for item in items:
        rtype = item.get("type", "general")
        if rtype not in RUMOR_TYPES:
            rtype = "general"
        text = item.get("headline", "")
        score, reason = calc_impact_score(rtype, text, bool(item.get("highEngagement")))
        rumors.append({
            "type": rtype, "ticker": item.get("ticker"),
            "headline": text, "source": item.get("source") or "finance",
            "impactScore": score, "impactReason": reason,
            "sentiment": item.get("sentiment") or "neutral",
            "date": item.get("date") or datetime.now().strftime("%Y-%m-%d"),
        })
    rumors.sort(key=lambda r: -r["impactScore"])

    counts: dict[str, int] = {}
    for r in rumors:
        if r["ticker"]:
            counts[r["ticker"]] = counts.get(r["ticker"], 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:10]

    ma = sum(1 for r in rumors if r["type"] == "ma")
    ins = sum(1 for r in rumors if r["type"] == "insider")
    ana = sum(1 for r in rumors if r["type"] == "analyst")
    summary = ("今日暂无重大传闻或早期信号。" if not rumors else
               f"共扫描到 {len(rumors)} 条信号：并购传闻 {ma} 条，内部人动态 {ins} 条，"
               f"分析师调整 {ana} 条。"
               + (f"最受关注：{'、'.join('$' + t for t, _ in top[:3])}。" if top else ""))

    if args.format == "json":
        print(json.dumps({"scannedAt": now_iso(), "rumors": rumors,
                         "topTickers": [{"ticker": t, "count": c} for t, c in top],
                         "summary": summary}, ensure_ascii=False, indent=2))
        return 0

    type_label = {"ma": "🏢 并购传闻", "insider": "👔 内部人动态",
                  "analyst": "📊 分析师调整", "regulatory": "⚖️ 监管动态",
                  "earnings": "📈 业绩预期", "general": "📰 市场信号"}
    sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}
    md = (f"## 🔮 传闻与早期信号扫描\n**扫描时间：** "
          f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n**{summary}**\n\n")
    if not rumors:
        print(md + "_今日暂无重大传闻。_")
        return 0
    grouped: dict[str, list] = {}
    for r in rumors:
        grouped.setdefault(r["type"], []).append(r)
    for rtype, group in grouped.items():
        md += f"### {type_label[rtype]}\n\n"
        for item in group[:3]:
            md += (f"**[冲击 {item['impactScore']}/10]** "
                   f"{sentiment_emoji[item['sentiment']]} {item['headline']}\n")
            if item["ticker"]:
                md += f"> 相关标的：${item['ticker']}\n"
            md += (f"> 来源：{item['source']}　｜　{item['date']}　｜　"
                   f"{item['impactReason']}\n\n")
    if top:
        md += "### 📊 传闻热度排行\n"
        md += "\n".join(f"- ${t}：被提及 {c} 次" for t, c in top) + "\n"
    print(md)
    return 0


# ── watchlist (host storage -> local JSON file) ──────────────────────────────

def watchlist_path(file_arg: str | None) -> Path:
    return Path(file_arg or WATCHLIST_FILENAME)


def load_watchlist(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = load_json_file(path)
    if not isinstance(data, list):
        print(f"watchlist file {path} must contain a JSON array", file=sys.stderr)
        sys.exit(2)
    return data


def save_watchlist(path: Path, items: list[dict]) -> None:
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_prices(args: argparse.Namespace) -> dict[str, float]:
    if not args.prices_file:
        return {}
    data = load_json_file(Path(args.prices_file))
    if not isinstance(data, dict):
        print("prices file must be a JSON object of {CODE: price}", file=sys.stderr)
        sys.exit(2)
    return {str(k).upper(): float(v) for k, v in data.items()
            if isinstance(v, (int, float))}


def cmd_watch(args: argparse.Namespace) -> int:
    path = watchlist_path(args.file)
    items = load_watchlist(path)

    if args.action == "add":
        code = args.code.upper()
        existing = next((i for i in items if i["ticker"] == code), None)
        if existing:
            if args.target is not None:
                existing["targetPrice"] = args.target
            if args.stop is not None:
                existing["stopPrice"] = args.stop
            if args.signal:
                existing["alertOnSignal"] = True
            if args.notes is not None:
                existing["notes"] = args.notes
            save_watchlist(path, items)
            print(json.dumps({"success": True, "action": "updated",
                             "message": f"已更新 {code} 的自选股设置",
                             "item": existing}, ensure_ascii=False))
            return 0
        item = {
            "ticker": code, "market": detect_market(code),
            "addedAt": now_iso(),
            "priceAtAdd": args.price,
            "targetPrice": args.target, "stopPrice": args.stop,
            "alertOnSignal": bool(args.signal), "lastSignal": None,
            "lastCheck": None, "notes": args.notes,
        }
        items.append(item)
        save_watchlist(path, items)
        desc = ", ".join(filter(None, [
            f"目标价 ${args.target}" if args.target is not None else None,
            f"止损价 ${args.stop}" if args.stop is not None else None,
            "信号变化提醒" if args.signal else None]))
        price_note = (f"（当前价 ${args.price}）" if args.price is not None
                      else "（当前价暂缺：传 --price 或稍后 watch list 补齐）")
        print(json.dumps({"success": True, "action": "added",
                          "message": f"已添加 {code} 到自选股{price_note}"
                                     + (f"，设置了：{desc}" if desc else ""),
                          "item": item}, ensure_ascii=False))
        return 0

    if args.action == "remove":
        code = args.code.upper()
        filtered = [i for i in items if i["ticker"] != code]
        if len(filtered) == len(items):
            print(json.dumps({"success": False,
                              "message": f"{code} 不在自选股列表中"},
                             ensure_ascii=False))
            return 0
        save_watchlist(path, filtered)
        print(json.dumps({"success": True,
                          "message": f"已从自选股中删除 {code}"}, ensure_ascii=False))
        return 0

    if args.action == "list":
        prices = _load_prices(args)
        rows = []
        for it in items:
            cur = prices.get(it["ticker"])
            change = (round((cur - it["priceAtAdd"]) / it["priceAtAdd"] * 100, 2)
                      if cur is not None and it.get("priceAtAdd") else None)
            to_target = (round((it["targetPrice"] - cur) / cur * 100, 2)
                         if cur is not None and it.get("targetPrice") else None)
            to_stop = (round((it["stopPrice"] - cur) / cur * 100, 2)
                       if cur is not None and it.get("stopPrice") else None)
            rows.append({**it, "currentPrice": cur, "changePct": change,
                         "toTargetPct": to_target, "toStopPct": to_stop})
        if args.format == "json":
            print(json.dumps({"items": rows, "count": len(rows)},
                             ensure_ascii=False, indent=2))
            return 0
        if not rows:
            print("## 📋 自选股列表\n\n_自选股为空。使用 watch add AAPL 添加股票。_\n")
            return 0
        md = f"## 📋 自选股列表（共 {len(rows)} 只）\n\n"
        md += "| 代码 | 当前价 | 较买入 | 目标价 | 止损价 | 距目标 | 最新信号 |\n"
        md += "|------|--------|--------|--------|--------|--------|----------|\n"
        for it in rows:
            price = f"${it['currentPrice']:.2f}" if it["currentPrice"] is not None else "暂缺"
            change = ("🟢+" if (it["changePct"] or 0) > 0 else "🔴") + \
                      f"{it['changePct']:.2f}%" if it["changePct"] is not None else "—"
            target = f"${it['targetPrice']}" if it.get("targetPrice") else "—"
            stop = f"${it['stopPrice']}" if it.get("stopPrice") else "—"
            to_t = f"{it['toTargetPct']:+.1f}%" if it["toTargetPct"] is not None else "—"
            signal = it.get("lastSignal") or "—"
            md += f"| {it['ticker']} | {price} | {change} | {target} | {stop} | {to_t} | {signal} |\n"
        triggered = [it for it in rows
                     if (it.get("targetPrice") and it["currentPrice"] is not None
                         and it["currentPrice"] >= it["targetPrice"])
                     or (it.get("stopPrice") and it["currentPrice"] is not None
                         and it["currentPrice"] <= it["stopPrice"])]
        if triggered:
            md += "\n### ⚡ 已触发提醒\n"
            for it in triggered:
                if it.get("targetPrice") and it["currentPrice"] >= it["targetPrice"]:
                    md += f"- 🎯 **{it['ticker']}** 已达目标价 ${it['targetPrice']}\n"
                if it.get("stopPrice") and it["currentPrice"] <= it["stopPrice"]:
                    md += f"- 🛑 **{it['ticker']}** 已触止损 ${it['stopPrice']}\n"
        print(md)
        return 0

    if args.action == "check":
        prices = _load_prices(args)
        signals: dict[str, str] = {}
        if args.signals_file:
            s = load_json_file(Path(args.signals_file))
            if not isinstance(s, dict):
                print("signals file must be a JSON object of {CODE: verdict}",
                      file=sys.stderr)
                return 2
            signals = {str(k).upper(): v for k, v in s.items()}
        alerts = []
        ts = now_iso()
        for it in items:
            cur = prices.get(it["ticker"])
            if cur is None:
                continue
            if it.get("targetPrice") and cur >= it["targetPrice"]:
                alerts.append({
                    "ticker": it["ticker"], "alertType": "target_hit",
                    "message": f"🎯 {it['ticker']} 已触达目标价！当前 ${cur:.2f} ≥ 目标 ${it['targetPrice']}",
                    "currentPrice": cur, "triggerValue": it["targetPrice"],
                    "timestamp": ts})
            if it.get("stopPrice") and cur <= it["stopPrice"]:
                alerts.append({
                    "ticker": it["ticker"], "alertType": "stop_hit",
                    "message": f"🛑 {it['ticker']} 已触达止损价！当前 ${cur:.2f} ≤ 止损 ${it['stopPrice']}",
                    "currentPrice": cur, "triggerValue": it["stopPrice"],
                    "timestamp": ts})
            new_signal = signals.get(it["ticker"])
            if it.get("alertOnSignal") and new_signal:
                if it.get("lastSignal") and new_signal != it["lastSignal"]:
                    alerts.append({
                        "ticker": it["ticker"], "alertType": "signal_change",
                        "message": f"📊 {it['ticker']} 信号变化：{it['lastSignal']} → {new_signal}",
                        "currentPrice": cur,
                        "triggerValue": f"{it['lastSignal']} → {new_signal}",
                        "timestamp": ts})
                it["lastSignal"] = new_signal
            it["lastCheck"] = ts
        save_watchlist(path, items)
        if args.format == "json":
            print(json.dumps({"alerts": alerts, "count": len(alerts)},
                            ensure_ascii=False, indent=2))
            return 0
        if not alerts:
            print("## 🔔 自选股提醒检查\n\n_当前没有触发任何提醒。_\n")
            return 0
        md = f"## 🔔 自选股提醒（{len(alerts)} 条触发）\n\n"
        md += "\n".join(f"- {a['message']}" for a in alerts)
        print(md)
        return 0

    print(f"unknown watch action: {args.action}", file=sys.stderr)
    return 1


# ── report assembly + verdict extraction (ported from src/{analyzer,index}.ts) ─

def extract_verdict(text: str) -> str:
    patterns = [
        r"结论[：:]\s*[💚🟢🟡🔴⚪]?\s*(强烈买入|买入|观望|卖出)",
        r"核心结论[：:]\s*[💚🟢🟡🔴⚪]?\s*(强烈买入|买入|观望|卖出)",
        r"\*\*(强烈买入|买入|观望|卖出)\*\*",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return "观望"


def cmd_report(args: argparse.Namespace) -> int:
    results = load_json_file(Path(args.analysis))
    if not isinstance(results, list) or not results:
        print("analysis must be a non-empty JSON array of result objects",
              file=sys.stderr)
        return 2
    macro = load_json_file(Path(args.macro_file)) if args.macro_file else None
    market = load_json_file(Path(args.market_file)) if args.market_file else None
    normalized = []
    for r in results:
        analysis = r.get("analysis", "")
        normalized.append({
            "code": r.get("code", ""), "market": r.get("market", "US"),
            "name": r.get("name", r.get("code", "")),
            "verdict": r.get("verdict") or extract_verdict(analysis),
            "analysis": analysis,
            "warnings": r.get("warnings") or [],
            "outputFormat": r.get("outputFormat", "markdown"),
            "generatedAt": r.get("generatedAt", now_iso()),
        })
    date = datetime.now().strftime("%Y-%m-%d")
    buy = sum(1 for r in normalized if r["verdict"] in ("买入", "强烈买入"))
    watch = sum(1 for r in normalized if r["verdict"] == "观望")
    sell = sum(1 for r in normalized if r["verdict"] == "卖出")
    out = (f"# 📈 股票智能分析报告\n**生成时间：** {date}　｜　"
           f"**分析 {len(normalized)} 只**　｜　🟢买入/强烈买入 {buy}　🟡观望 {watch}　"
           f"🔴卖出 {sell}\n\n")
    if macro:
        out += f"---\n\n## 🌍 全球宏观速览\n\n{macro}\n\n"
    if market:
        out += f"---\n\n## 🎯 大盘复盘\n\n{market}\n\n"
    out += "---\n\n## 📊 个股决策仪表盘\n\n"
    for r in normalized:
        warn = (f"\n> ⚠️ **预警：** {' | '.join(r['warnings'])}\n"
                if r["warnings"] else "")
        out += f"{warn}\n{r['analysis']}\n\n---\n"
    print(out)
    return 0


def cmd_verdict(args: argparse.Namespace) -> int:
    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except OSError as e:
        print(f"cannot read {args.file}: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"verdict": extract_verdict(text)}, ensure_ascii=False))
    return 0


# ── CLI ─────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="stockcli.py",
        description="Deterministic stock-analysis engine (scoring/watchlist/report)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("watch", help="watchlist management (local JSON persistence)")
    wa = w.add_subparsers(dest="action", required=True)

    a = wa.add_parser("add"); a.add_argument("code"); a.add_argument("--target", type=float)
    a.add_argument("--stop", type=float); a.add_argument("--signal", action="store_true")
    a.add_argument("--price", type=float, help="current price (from market data)")
    a.add_argument("--notes", default=None); a.add_argument("--file", default=None)
    a.set_defaults(func=cmd_watch)

    r = wa.add_parser("remove"); r.add_argument("code"); r.add_argument("--file", default=None)
    r.set_defaults(func=cmd_watch)

    l = wa.add_parser("list"); l.add_argument("--prices-file", default=None)
    l.add_argument("--format", choices=("md", "json"), default="md")
    l.add_argument("--file", default=None)
    l.set_defaults(func=cmd_watch)

    c = wa.add_parser("check"); c.add_argument("--prices-file", default=None)
    c.add_argument("--signals-file", default=None)
    c.add_argument("--format", choices=("md", "json"), default="md")
    c.add_argument("--file", default=None)
    c.set_defaults(func=cmd_watch)

    d = sub.add_parser("dividend"); d.add_argument("data")
    d.add_argument("--format", choices=("md", "json"), default="md")
    d.set_defaults(func=cmd_dividend)

    ru = sub.add_parser("rumor"); ru.add_argument("news")
    ru.add_argument("--format", choices=("md", "json"), default="md")
    ru.set_defaults(func=cmd_rumor)

    rep = sub.add_parser("report"); rep.add_argument("analysis")
    rep.add_argument("--macro-file", default=None)
    rep.add_argument("--market-file", default=None)
    rep.set_defaults(func=cmd_report)

    v = sub.add_parser("verdict"); v.add_argument("file")
    v.set_defaults(func=cmd_verdict)
    return ap


def main() -> int:
    ap = build_parser()
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
