---
name: glm-stock-analysis-skill
description: "A股/港股/美股个股决策仪表盘、股息安全评分、传闻与早期信号扫描、自选股管理与提醒、K线图形态分析的综合股票分析技能。触发场景：用户提到股票代码（分析600519 / AAPL值不值得买 / 帮我看看腾讯）、买卖建议、持仓成本（我持仓成本1450分析茅台）、股息分析（JNJ股息怎么样）、市场传闻或早期信号（今日有什么并购传闻）、自选股管理（关注AAPL / 检查自选股提醒）、上传K线图。确定性引擎（股息安全评分、传闻冲击分、自选股提醒、结论提取、报告组装）由本地纯 Python 脚本 stockcli.py 完成；数据由用户提供或本地模型整理。"
metadata:
  version: "1.0.0"
---

# Stock Analysis Skill（GLM 股票智能分析）

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-finance/`
- 本技能目录：`~/.codex/plugins/glm-finance/skills/glm-stock-analysis-skill/`
- 下文 `scripts/`、`references/` 均指该技能目录内的子目录。
- **数据职责划分**（源技能的云端 SDK 数据层与 LLM 层的本地等效替换）：
  - **行情/股息/传闻数据**：由用户直接提供，或 Codex 会话用可用工具（联网
    检索技能 / 用户粘贴）取得后，由模型按 `references/data-schemas.md` 整理
    成 JSON 文件。缺失字段填 null，**严禁捏造**。
  - **仪表盘/研报正文**：由当前本地模型按
    `references/dashboard-template.md`（七段式仪表盘）或
    `references/report-template.md`（结构化研报）模板直接产出。
  - **确定性计算**（评分/冲击分/提醒检查/结论提取/报告组装）：一律走
    `scripts/stockcli.py`，模型不得心算替代。
- **自选股持久化**：源技能用宿主平台的浏览器存储 API；本地等效替换为
  **用户工作目录**（Codex 启动 cwd）下的 `stock_watchlist.json`（可用
  `--file` 换路径）。插件目录只读。
- 引擎为**纯 Python 标准库**（argparse/json/re/sys/datetime/pathlib），
  零 SDK、零网络、零 pip 依赖。

## Commands & Triggers

| 命令 | 触发词示例 |
|------|-----------|
| 个股分析 | 分析600519 / AAPL值不值得买 / 帮我看看腾讯 |
| 带持仓分析 | 我持仓成本1450分析茅台 / AAPL我170买的现在怎样 |
| 股息分析 | JNJ股息怎么样 / 帮我分析这几只股的股息 KO PG JNJ |
| 传闻扫描 | 今日有什么并购传闻 / 扫描一下市场早期信号 |
| 添加自选股 | 关注AAPL / 把600519加入自选，目标价1600止损1350 |
| 查看自选股 | 我的自选股列表 / 看一下我关注的股票 |
| 检查提醒 | 检查自选股提醒 / 有没有触发止损 |
| 删除自选股 | 从自选股删除TSLA |
| K线图分析 | （上传图片）帮我分析这个K线图 |
| 大盘复盘 | 附带大盘复盘分析600519 |

## Input Schemas（个股分析）

```typescript
{
  stocks: (string | { code: string; position?: { status: "empty"|"holding"; cost?: number; shares?: number } })[],
  outputFormat?: "markdown" | "pdf" | "word",  // 默认 markdown；pdf/word 走 references/report-template.md
  mode?: "full" | "quote",                      // 默认 full
  includeMarketReview?: boolean,                // 默认 false
  includeGlobalMacro?: boolean,                 // 默认 true
  includeDividend?: boolean,                    // 美股附加股息分析，默认 false
}
```

其余命令输入见 `references/data-schemas.md`（股息/传闻/价格/信号/分析结果
数组的 JSON schema）。

## 标准工作流（Codex 形态）

### 个股分析（主流程）

1. 解析输入（代码列表 + 持仓 + 输出格式/开关）。
2. **取数**：用户提供行情 JSON，或模型用会话可用工具取数后按
   `references/data-schemas.md` 的 StockData schema 整理；无法取得的字段
   填 null / 标「暂缺」。
3. `includeGlobalMacro` 默认开：整理全球宏观速览文本（数据同上，取不到
   则整节省略并说明）；`includeMarketReview` 按需整理大盘复盘文本。
4. 模型按 `references/dashboard-template.md` 为每只股票生成七段式决策
   仪表盘（数据预警块 + 持仓块 + 数据 JSON 块 + 仪表盘模板）。
5. 把各股分析结果组装成数组 JSON，跑
   `python3 ~/.codex/plugins/glm-finance/skills/glm-stock-analysis-skill/scripts/stockcli.py report <analysis.json> [--macro-file M --market-file M2]`
   产出完整报告（标题统计行 + 宏观 + 大盘 + 仪表盘们）。
6. 若有自选股信号，静默跑一次 `watch check --signals-file`（不阻塞主流程）。

### 股息分析

1. 整理 DividendData JSON（schema 见 references/data-schemas.md）。
2. `python3 …/scripts/stockcli.py dividend <data.json>` → 评分引擎（安全
   评分/派息状态/收入评级/评分依据/股息历史）+ 完整 markdown 报告；
   `--format json` 取结构化结果。

### 传闻扫描

1. 整理 RumorNews JSON 数组（五类信号）。
2. `python3 …/scripts/stockcli.py rumor <news.json>` → 冲击评分 + 分类
   分组报告 + 热度排行；`--format json` 取结构化结果。

### 自选股管理

```bash
S=~/.codex/plugins/glm-finance/skills/glm-stock-analysis-skill/scripts/stockcli.py
python3 $S watch add AAPL --price 123.4 --target 200 --stop 150 --signal
python3 $S watch list --prices-file prices.json          # 当前价从行情 JSON 注入
python3 $S watch check --prices-file prices.json --signals-file signals.json
python3 $S watch remove TSLA
```

`watch add` 不带 `--price` 也可入库（priceAtAdd=null，之后 `watch list`
补齐）；`check` 需要 `--prices-file`（当前价），信号变化提醒需 `--signals-file`
+ 当初 `--signal` 开启。watchlist 文件默认 `./stock_watchlist.json`（用户
工作目录），`--file` 可换路径。

### K线图分析

上传图片时按 `references/dashboard-template.md` 的「K线图分析」提纲：模型
支持图像输入则直接分析；不支持则先请用户描述形态/均线/量能/价位，再按同一
提纲完成分析。

## Report Structure

```
# 股票智能分析报告

## 🌍 全球宏观速览（默认开启）
## 🎯 大盘复盘（需开启）
## 📊 个股决策仪表盘（每只）
   ### 📰 重要信息速览（舆情/业绩预期/🚨风险/✨利好/最新动态）
   ### 📌 核心结论（结论/一句话/空仓者建议/持仓者建议+盈亏）
   ### 📈 当日行情
   ### 📊 数据透视（技术面/基本面/资金面）
   ### 🎯 作战计划（狙击点位表/仓位/风控）
   ### ✅ 检查清单（综合结论）
   ### 💰 股息分析（美股，需开启 includeDividend）
```

组装由 `stockcli.py report` 确定性完成。

## Dividend Analysis Metrics

| 指标 | 说明 |
|------|------|
| 安全评分 | 0-100，综合派息率/增长/连续年数 |
| 收入评级 | excellent/good/moderate/poor |
| 派息率状态 | safe(<40%)/moderate/high/unsustainable |
| 5年CAGR | 股息复合增长率 |
| 连续增长年数 | 25年以上为股息贵族 |

评分细则（引擎内固化）：基准 50；派息率 <40 +20 / <60 +10 / <80 -10 /
≥80 -20；5年CAGR >10 +15 / >5 +10 / >0 +5 / ≤0 -15；连续年数 ≥25 +15 /
≥10 +10 / ≥5 +5；收益率 >8 -10。

## Rumor Scanner Signal Types

| 类型 | 冲击分 | 说明 |
|------|--------|------|
| 并购传闻 (ma) | +5 | M&A/收购/要约 |
| 内部人动态 (insider) | +4 | CEO/董事买卖 |
| 分析师调整 (analyst) | +3 | 评级上调/下调/目标价变动 |
| 监管动态 (regulatory) | +3 | SEC调查/合规风险 |
| 业绩预期 (earnings) | +2 | 盈利预警/上调 |

标题含 breaking/just in/alert/urgent +2；高关注度 +2；上限 10。
（以上加分全部由 `stockcli.py rumor` 确定性执行。）

## Watchlist Alert Types

| 提醒类型 | 触发条件 |
|---------|---------|
| 🎯 目标价 | 当前价 ≥ targetPrice |
| 🛑 止损价 | 当前价 ≤ stopPrice |
| 📊 信号变化 | 本次结论 ≠ 上次结论 |

## Behavior Rules

- 乖离率 > 5% → 结论不得为买入/强烈买入
- 数据缺失 → 标"暂缺"，严禁捏造
- 有持仓成本 → 必须给出盈亏分析
- 未提供持仓 → 同时给出空仓/持仓两套建议
- 每次分析后自动静默更新自选股信号（`watch check --signals-file`）

## Hard Rules

1. **确定性计算走脚本**：股息安全评分、传闻冲击分、自选股提醒检查、结论
   提取（`verdict`）、报告组装（`report`）一律用 `scripts/stockcli.py`，
   不得模型心算或手写等价逻辑。
2. **数据纪律**：行情/股息/传闻数据缺失字段填 null、报告中标「暂缺」；
   严禁编造任何价格、指标、新闻。
3. **数据来源声明**：报告中说明数据来自用户提供/会话工具获取/估计，不
   冒充实时行情终端。
4. **模板保真**：仪表盘严格按 `references/dashboard-template.md` 七段式
   结构，不增删章节；结论四选一（强烈买入/买入/观望/卖出）。
5. **自选股持久化在用户目录**：watchlist JSON 落 cwd（默认
   `stock_watchlist.json`），永不写插件安装目录。
6. **免责声明**：每份报告尾部保留「仅供参考，不构成投资建议」。
7. **PDF/Word 边界**：本地形态默认 markdown；导出 PDF/Word 由用户本地
   工具链完成（见 `references/report-template.md` 导出边界节），模型不
   虚构「文档已生成」。

## Limitations

- 行情/传闻数据质量取决于用户提供或会话可用工具；模型知识截止之外的信息
  必须显式取数，取不到就标「暂缺」
- 自选股数据持久化在用户工作目录的本地 JSON（非云端账户）
- 港股基本面数据较少
- 不支持期货、ETF、可转债
- 仅供参考，不构成投资建议
