# Finance API 本地等效参考（glm-finance）

本文件为源 skill `Finance_API_Doc.md` 的**本地等效版**：源文档的全部端点经
web-dev-ai-gateway 统一代理（`{GATEWAY_URL}{API_PREFIX}`，网关注入
x-rapidapi-host/x-rapidapi-key，`X-Z-AI-From: Z` 头）——用户本地不部署该
网关，本插件以 `scripts/finance_cli.py` 的**免 key 公共端点**逐项等效替换。

## 端点映射总表（源网关端点 → 本地 CLI → 公共端点）

| 源网关端点（RapidAPI 形态） | finance_cli.py 子命令 | 本地公共端点（免 key） |
|---|---|---|
| GET `v1/markets/search`（公司检索） | `search <query>` | Yahoo `query1.finance.yahoo.com/v1/finance/search` |
| GET `v1/markets/quote`（实时报价，type=STOCKS/ETF/MUTUALFUNDS） | `quote <sym>...` | Yahoo `v8/finance/chart/{sym}` meta（自动兜底→腾讯 `qt.gtimg.cn/q=`） |
| GET `v1/markets/stock/quotes`（多符号快照，逗号分隔） | `quote aapl msft goog` | 多符号循环 chart v8（腾讯链单请求多符号） |
| GET `v1/markets/stock/history` / `v2/...`（历史K线，interval 5m~3mo） | `history <sym> --interval --range --limit` | Yahoo `v8/finance/chart/{sym}?range=&interval=`（腾讯链 `web.ifzq.gtimg.cn` 日K） |
| GET `v1/markets/news` / `v2/markets/news`（市场新闻，ticker 可选） | `news [sym] --limit` | Yahoo RSS `feeds.finance.yahoo.com/rss/2.0/headline?s=`（无符号→大盘 RSS index） |
| GET `v1/markets/stock/modules`（asset-profile / statistics / financial-data / earnings / calendar-events / sec-filings / balance-sheet / income-statement / cashflow-statement / insider-transactions / recommendation-trend / upgrade-downgrade-history / institution-ownership / fund-ownership / net-share-purchase-activity / index-trend / sector-trend / industry-trend） | `modules <sym> <module>...` | Yahoo `v10/finance/quoteSummary/{sym}?modules=`（crumb+cookie 流程脚本自动处理；别名表见脚本头注释） |
| GET `v2/markets/tickers`（全市场符号分页） | `search` 按需检索代替 | 免 key 端点无全量分页清单；按名检索已覆盖「找代码」用途 |

> 说明：源文档第 5.2 节 `v1/stock/modules` 与 `v1/markets/stock/modules` 为同
> 一语义的两种路径前缀，本地统一走 `modules` 子命令；源文档的「组合查询/批量
> 优化」建议以多符号 `quote`/循环 `history` 等效实现。

## 用法（对应源文档 Usage Flow 示例）

```bash
FIN=~/.codex/plugins/glm-finance/skills/glm-finance/scripts/finance_cli.py

# 示例 1：找到公司并取实时数据（源: search → quote → asset-profile）
python3 $FIN search "Knowledge Atlas"          # 1. 检索（智谱华章 2513.HK 的推荐检索词）
python3 $FIN quote 2513.HK                     # 2. 实时报价（auto: Yahoo→腾讯兜底）
python3 $FIN modules AAPL asset-profile        # 3. 公司资料（quoteSummary + crumb）

# 示例 2：投资价值分析（源: financial-data + earnings）
python3 $FIN modules AAPL financial-data earnings

# 批量快照（源: v1/markets/stock/quotes）
python3 $FIN quote AAPL MSFT GOOGL AMZN TSLA --json

# 历史数据（源: v1/markets/stock/history?interval=1d）
python3 $FIN history AAPL --interval 1d --range 1y
python3 $FIN history AAPL --provider tencent --limit 30    # 直接走腾讯日K
```

输出：默认 Markdown 表格；各子命令 `--json` 切 JSON（字段与源接口语义对齐：
symbol/name/price/previous_close/change/change_pct/volume/currency 等）。

## provider 链与退出码

- `--provider auto`（默认）：Yahoo 主链，失败自动落**腾讯行情兜底**
  （`qt.gtimg.cn` 实时 + `web.ifzq.gtimg.cn` 日K；覆盖美股 `usAAPL`、A股
  `sh600519`/`sz000001`、港股 `hk00700`——A股 6 位代码必须带 sh/sz 前缀）。
- `--provider tencent`：直接走腾讯链（国内网络首选）。
- 退出码：`0` 成功 / `1` 用法错误（未知模块、A股缺前缀） / `2` 网络或端点失败
  （stderr 报因 + 修复 hint，不假死）。
- 腾讯链注记：A 股 `volume` 单位为「手」（×100 = 股数）；港股代码 5 位纯数字
  会自动补 `hk` 前缀。

## 使用提示（沿源文档 Best Practices）

1. **认证头 `X-Z-AI-From: Z`**：网关专属，本地公共端点**不需要任何认证头**——
   脚本已内置浏览器 User-Agent（Yahoo 端点要求）。
2. **限频**：Yahoo 公共端点对高频会 429 限流；重试或改走腾讯链（`--provider tencent`）。
3. **错误处理**：脚本退出码 + stderr 报因即「comprehensive error handling」的本地形态。
4. **批量查询**：`quote` 多符号一次调用；`modules` 可一次传多个模块。
5. **缓存**：高频场景由调用方（模型/用户）自行缓存 JSON 输出。
6. **参数校验**：未知模块名 exit 1 并列可用模块；interval/range 走白名单。
7. **响应解析**：`--json` 直接给结构化数据，无需再解析 Markdown。

## 受限网络增补（模块数据）

`modules`（quoteSummary）无腾讯等效。受限网络下：
- 改用 `quote`/`history` 子命令（腾讯链可达即可用）；
- 或走 yfinance 兜底：`uv run --with yfinance python3 -c "..."`（免安装注入，
  keyless；用户 macOS 已有 /opt/uv/0.11.17）。
