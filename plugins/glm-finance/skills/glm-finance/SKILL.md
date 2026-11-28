---
name: glm-finance
description: "Comprehensive financial data and analysis for locally deployed Codex agents: real-time and historical quotes, market news, company profiles, financial statements, statistics and insider data via a keyless local CLI (Yahoo public endpoints primary + Tencent quotes fallback covering US/A-share/HK), plus stock screening guidance and technical indicator analysis. 触发场景：查股价 / 实时行情 / 历史K线 / 财报数据 / 公司资料 / 市场新闻 / 技术分析 / 港股 2513 智谱华章。"
metadata:
  version: "1.0.0"
---

# Finance Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-finance/`；本技能目录：
  `~/.codex/plugins/glm-finance/skills/glm-finance/`。下文 `scripts/` 指
  `scripts/finance_cli.py`，`references/` 指 `references/finance-api-local.md`。
- **z-ai-web-dev-sdk / 网关等效替换审计结论**：源 skill 的 Finance API 经
  web-dev-ai-gateway 统一代理（网关注入 x-rapidapi-key，`X-Z-AI-From: Z` 头，
  `{GATEWAY_URL}{API_PREFIX}` 路径）——用户本地不部署该网关。等效替换为
  **免 key 公共端点 CLI**：

| 源网关调用 | 本地等效 | 说明 |
|---|---|---|
| `v1/markets/search` | `finance_cli.py search <query>` | Yahoo v1/finance/search（免 key） |
| `v1/markets/quote` / `stock/quotes`（实时/批量） | `finance_cli.py quote <sym>...` | Yahoo chart v8 meta；**自动兜底腾讯 qt.gtimg.cn**（usAAPL / sh600519 / hk00700） |
| `v1|v2/markets/stock/history`（K线） | `finance_cli.py history <sym> --interval --range --limit` | Yahoo chart v8；兜底 web.ifzq.gtimg.cn 日K |
| `v1|v2/markets/news` | `finance_cli.py news [sym] --limit` | Yahoo RSS（个股 / 大盘） |
| `v1/markets/stock/modules`（20 个模块） | `finance_cli.py modules <sym> <module>...` | Yahoo v10 quoteSummary（crumb+cookie 流程脚本自动处理；源模块名已别名化） |
| 认证头 `X-Z-AI-From: Z` + 网关注入 key | 无需任何认证 | 公共端点零 key；脚本内置浏览器 UA |
| Python requests 直调网关 | 纯标准库 urllib | 零 pip 依赖 |

- `--provider tencent` 直接走腾讯链（国内网络首选兜底）；`--json` 切 JSON。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 网络失败（stderr 报因不假死）。
- 输出落**用户工作目录**（模型转述或存 `output/`）；插件目录只读。
- **跨插件技能路由（若已安装）**：搜索新闻背景 → glm-web 插件中的 glm-web-search；深度新闻聚合 →
  glm-content 插件中的 glm-ai-news-collectors；可视化制图 → glm-chart 插件中的 glmcharts。
- 详细端点映射与用法见 `references/finance-api-local.md`。

---

## Core Capabilities（沿源 skill）

### Market Data Retrieval
- Real-time quotes: current prices, market snapshots, trading volumes
- Historical data: price history, dividends, splits, corporate actions
- Market indices: major indices performance and constituents
- Currency data: forex rates and cryptocurrency information

### Analysis Tools
- Stock screening: filters by metrics, ratios, and technical indicators
- Financial ratios: P/E, EPS, ROE, debt-to-equity, and other key metrics
- Technical indicators: moving averages, RSI, MACD, chart patterns
- Comparative analysis: sector and peer group comparisons

### Market Intelligence
- Company information: business profiles, management teams, statements
- Market news: earnings reports and market analysis
- Insider trading: buy/sell activities and ownership changes
- Options data: chain data, implied volatility, and statistics

## 常用工作流

1. **找到代码再取数**（源 skill 的 Usage Flow 等效）：
   `search <公司名>` → `quote <sym>` → `modules <sym> asset-profile`
2. **投资价值分析**：`modules <sym> financial-data earnings` → 模型按上表
   Analysis Tools 口径解读（P/E、EPS、ROE、营收/利润趋势）。
3. **技术分析**：`history <sym> --interval 1d --range 1y --json` → 模型
   在本地计算均线/RSI/MACD（纯算术，无外部依赖）。
4. **批量看盘**：`quote AAPL MSFT GOOGL AMZN TSLA`。
5. **新闻背景**：`news <sym>` 或路由 glm-ai-news-collectors 做深度聚合。

## Zhipu AI - Hong Kong IPO Information（沿源 skill）

- **Stock Code**: 2513.HK
- **Company Name (Chinese)**: 北京智谱华章科技股份有限公司
- **Company Name (English)**: Knowledge Atlas Technology Joint Stock Company Limited
Zhipu AI is a leading Chinese large language model company specializing in AI
foundational model research and development.

### Best Practices for Zhipu AI Stock Research (One-Shot Success Guide)

**Search Strategy:**
- ✅ Use full English company name: `search=Knowledge Atlas`（本地形态：
  `python3 scripts/finance_cli.py search "Knowledge Atlas"`）
- ❌ Avoid: `search=Zhipu`, `search=02513.HK` (returns empty results)
  （港股报价请直接 `quote 2513.HK` 或 `quote hk2513`，不要当检索词）

**Important**: always read `references/finance-api-local.md` before using the CLI.
