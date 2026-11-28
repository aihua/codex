# 数据 JSON Schema（references/data-schemas.md）

> 本插件的确定性引擎 `scripts/stockcli.py` 吃这些 JSON 文件。行情/股息/
> 传闻数据由 agent（本地模型 + 用户提供的数据或联网工具结果）按 schema
> 整理成文件后交给脚本。**缺失字段填 null，不得捏造**（源技能数据纪律
> 原样保留）。按需 grep，不整读。

## StockData（个股数据，full 模式）

```json
{
  "code": "600519",              // 必填
  "market": "CN",                // CN | HK | US（缺省按代码推断）
  "timestamp": "2026-05-18T09:30:00Z",
  "name": "贵州茅台",
  "price": 1450.0,               // 缺 price 视为数据获取失败
  "prev_close": 1441.0, "open": 1442.0, "high": 1460.0, "low": 1438.0,
  "change_pct": 0.62, "change_amount": 9.0, "amplitude": 1.53,
  "volume": 3200000, "amount": 4640000000.0, "turnover": 0.25, "volume_ratio": 1.1,
  "market_cap": 1823000000000.0, "pe_ttm": 24.5, "pb": 8.2,
  "high_52w": 1815.0, "low_52w": 1245.0, "dividend_yield": 3.1,
  "ma5": 1441.0, "ma10": 1425.0, "ma20": 1398.0,
  "bias_pct": 3.7,               // 相对 MA20 乖离率 %
  "trend": "多头排列",            // 多头排列 | 空头排列 | 震荡整理
  "overbought_warning": false,   // bias_pct > 5 时 true
  "support": 1398.0, "resistance": 1480.0, "rsi": 58.0,
  "kline_recent_10": [           // 最近10日
    {"date": "2026-05-05", "open": 1435.0, "close": 1441.0, "high": 1448.0, "low": 1430.0, "volume": 2800000}
  ],
  "profit_ratio": 72.0,          // 获利比例 %
  "avg_cost": 1402.0,            // 平均成本
  "chip_concentration": 41.0,    // 筹码集中度
  "roe": 31.2, "gross_margin": 91.5, "net_margin": 49.8, "debt_ratio": 20.1,
  "eps": 68.3, "revenue_growth": 15.4,
  "main_net": 1200000000.0,      // 主力净流入金额（A股/港股）
  "main_net_pct": 2.6,           // 主力净流入占比 %
  "error": null                  // 数据获取失败时填错误信息
}
```

`mode: "quote"` 精简模式只需：name, price, prev_close, change_pct,
change_amount, volume, amount, turnover, volume_ratio, market_cap,
pe_ttm, pb。

数据校验（源技能 validateStockData 纪律）：无 price → 数据失败；无
ma5/ma20 → 技术面缺失；`overbought_warning` true → 报告必须带
「⚠️ 乖离率 X% 超过5%，严禁追高」；无 roe/pe_ttm → 基本面不完整。

## DividendData（股息数据，喂 `stockcli.py dividend`）

```json
[{
  "ticker": "JNJ", "name": "Johnson & Johnson",
  "currentPrice": 152.3, "dividendYield": 3.25, "annualDividend": 4.96,
  "trailingEps": 9.87,
  "exDividendDate": "2026-05-23", "paymentFrequency": "quarterly",
  "dividendHistory": [{"year": 2025, "total": 4.96}, {"year": 2024, "total": 4.76}],
  "consecutiveYears": 63, "dividendGrowth5y": 5.9
}]
```

评分规则（引擎内固化，无需模型计算）：派息率 = annualDividend /
trailingEps × 100；状态 safe(<40)/moderate(<60)/high(<80)/unsustainable；
安全评分基准 50，派息率 ±20、5年CAGR ±15、连续年数 ±15、收益率 >8 扣 10；
收入评级 excellent(≥80)/good(≥60)/moderate(≥40)/poor。

## RumorNews（传闻新闻，喂 `stockcli.py rumor`）

```json
[{
  "type": "ma",                  // ma | insider | analyst | regulatory | earnings | general
  "ticker": "NVDA",              // 可 null
  "headline": "…breaking: 传闻收购…",
  "source": "路透", "sentiment": "positive",  // positive | negative | neutral
  "date": "2026-05-18",
  "highEngagement": true         // 可选，市场高度关注 +2
}]
```

冲击分（引擎内固化）：ma +5 / insider +4 / analyst +3 / regulatory +3 /
earnings +2 / general +1（基准 1）；标题含 breaking|just in|alert|urgent
再 +2；highEngagement +2；上限 10。

## PricesFile / SignalsFile（watchlist 行情与信号）

```json
{"AAPL": 123.4, "600519": 1450.0, "00700.HK": 385.0}     // prices-file
{"AAPL": "买入", "600519": "观望"}                        // signals-file
```

## AnalysisResult 数组（喂 `stockcli.py report`）

```json
[{
  "code": "600519", "market": "CN", "name": "贵州茅台",
  "verdict": "买入",            // 可省略——脚本会从 analysis 文本提取
  "analysis": "…完整仪表盘 markdown…",
  "warnings": ["⚠️ 乖离率 3.7%…"],
  "outputFormat": "markdown", "generatedAt": "…"
}]
```

`--macro-file`（全球宏观速览文本）与 `--market-file`（大盘复盘文本）传
markdown 纯文本文件。

## WatchlistItem（`stock_watchlist.json`，由脚本维护）

```json
[{
  "ticker": "AAPL", "market": "US", "addedAt": "…",
  "priceAtAdd": 120.0, "targetPrice": 200.0, "stopPrice": 150.0,
  "alertOnSignal": false, "lastSignal": null, "lastCheck": null, "notes": null
}]
```
