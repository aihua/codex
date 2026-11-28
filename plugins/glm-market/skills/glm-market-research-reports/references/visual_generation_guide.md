# Visual Generation Guide for Market Research Reports（GLM 本地适配版）

> 等效替换说明：源技能的视觉链路是「自然语言提示词 → 宿主平台
> scientific-schematics / generate-image 子进程生成」。本地 Codex 形态下
> 两个宿主工具均不存在，等效替换为**确定性 matplotlib 渲染器**
> `scripts/generate_market_visuals.py`：同样的图表目录、同样的命名约定、
> 同样的优先级，但由参数驱动而非提示词驱动。**数据纪律：渲染器未拿到
> 调研值时会生成带「示意数据 DEMO DATA」水印的占位图；模型必须先用
> web 检索（glm-web-search 插件）或用户提供的资料收集真实数值，经
> `--data data.json` 注入后再产出正式图。**

## Overview

### Core Visuals (Generate First - Priority 1-6)

| # | 文件名 | 渲染器 | 内容 |
|---|--------|--------|------|
| 1 | `01_market_growth_trajectory.png` | `r_growth` | 柱状：历史(深蓝) vs 预测(浅蓝)，CAGR 标注，split 虚线 |
| 2 | `02_tam_sam_som.png` | `r_tam` | 同心圆 TAM/SAM/SOM |
| 3 | `03_porters_five_forces.png` | `r_porter` | 五力盒图 + HIGH/MEDIUM/LOW 评级 |
| 4 | `04_competitive_positioning.png` | `r_positioning` | 2x2 定位矩阵，气泡大小=份额 |
| 5 | `05_risk_heatmap.png` | `r_risk` | 概率 x 影响 heatmap + 风险散点 |
| 6 | `06_exec_summary.png` | `r_exec` | 高管摘要指标面板（源：generate-image 的等效为参数化面板） |

### Extended Visuals (Generate as Needed - Priority 7+)

| # | 文件名 | 渲染器 | 内容 |
|---|--------|--------|------|
| 7 | `07_regional_breakdown.png` | `r_regional` | 区域份额饼图 |
| 8 | `08_segment_growth.png` | `r_segments` | 分段增长分组柱（2024 vs 2030E） |
| 9 | `09_driver_impact.png` | `r_drivers` | 驱动因素 概率 x 影响散点 |
| 10 | `10_pestle.png` | `r_pestle` | PESTLE 六维雷达 |
| 13 | `13_market_share.png` | `r_share` | 份额横条图 |
| 16 | `16_customer_segments.png` | `r_customer` | 客户分段横条 + CAGR 标注 |
| 19 | `19_technology_roadmap.png` | `r_tech_roadmap` | 技术泳道时间线 |
| 21 | `21_regulatory_timeline.png` | `r_reg_timeline` | 监管里程碑时间线 |
| 23 | `23_opportunity_matrix.png` | `r_opportunity` | 吸引力 x 赢面 气泡矩阵 |
| 24 | `24_implementation_gantt.png` | `r_gantt` | 实施阶段甘特 |
| 26 | `26_financial_projections.png` | `r_financials` | 收入面积 + EBITDA 曲线 |
| 27 | `27_scenario_analysis.png` | `r_scenarios` | 三情景分组柱 |

（序号沿用源技能命名约定，中间缺号对应源技能中同样未本地化的少数
高度定制图型；需要时按第 5 节通用降级路径处理。）

### Tool Selection（本地形态）

- 全部 18 个图型 → `generate_market_visuals.py`（matplotlib，离线，无 SDK）
- 数值来源 → glm-web-search 插件 `glmws.py search/fetch` 或用户资料
- **不再存在**任何提示词驱动的 AI 生图：封面主视觉用 `06_exec_summary`
  面板或 LaTeX 封面排版（`assets/market_report_template.tex` 已含
  `\titlepage` 设计）替代。

## Visual Naming Convention

`figures/<序号>_<语义名>.png`，序号即优先级；`--skip-existing` 按
存在即跳过，逐图补数据重渲时直接点名输出文件再 `-o figures/`。

## 批量生成契约（沿用源 CLI 面）

```bash
# 核心 6 图（报告开工必产）
python3 ~/.codex/plugins/glm-market/skills/glm-market-research-reports/scripts/generate_market_visuals.py \
  --topic "Electric Vehicle Charging" --output-dir figures/

# 全 18 图（深入写作阶段按需）
... --all

# 已有文件跳过（补渲染时）
... --skip-existing

# 图目录速查
... --list
```

退出码：`0` 全部成功；`1` 有渲染失败（stdout 汇总 ok/fail）；`2`
参数错误 / matplotlib 缺失（stderr 附 `uv pip install matplotlib` 提示）。

## --data JSON Schema（每个渲染器一张键）

顶层键 = 输出文件名（或去掉 `.png` 的渲染器名）。未出现的键走水印演示
数据。核心 6 图的 schema：

```json
{
  "01_market_growth_trajectory": {
    "years": [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "values": [18.1, 20.9, 24.2, 27.8, 31.5, 36.4, 42.0],
    "split_year": 2025,
    "cagr": 12.4
  },
  "02_tam_sam_som": { "tam": 50, "sam": 15, "som": 3 },
  "03_porters_five_forces": {
    "forces": {
      "Rivalry":       ["HIGH",   ["因素1", "因素2", "因素3"]],
      "New Entrants":  ["MEDIUM", ["..."]],
      "Supplier Power": ["LOW",   ["..."]],
      "Buyer Power":   ["HIGH",   ["..."]],
      "Substitutes":  ["MEDIUM", ["..."]]
    }
  },
  "04_competitive_positioning": {
    "companies": [["公司A", 0.72, 0.78, 0.16], ["公司B", 0.25, 0.80, 0.09]]
  },
  "05_risk_heatmap": {
    "risks": [["R1 需求波动", 0.72, 0.78], ["R2 监管变化", 0.55, 0.88]]
  },
  "06_exec_summary": {
    "metrics": [["Market Size 2024", "$45.2B"], ["CAGR", "15.3%"]],
    "findings": ["发现1", "发现2", "发现3"]
  }
}
```

扩展 12 图 schema（同文件追加键，`--all` 时消费）：

```json
{
  "07_regional_breakdown": { "labels": ["North America", "Europe"], "values": [40.3, 26.8] },
  "08_segment_growth":     { "labels": ["Enterprise", "SMB"], "hist": [22.4, 11.8], "proj": [48.6, 24.2] },
  "09_driver_impact":     { "drivers": [["数字化渗透", 0.85, 0.78]] },
  "10_pestle":            { "dims": ["Political", "Economic"], "scores": [3.2, 4.1] },
  "13_market_share":      { "labels": ["Leader", "Player2"], "values": [23, 17] },
  "16_customer_segments": { "labels": ["大型企业"], "values": [52], "growth": [9] },
  "19_technology_roadmap": { "lanes": [["核心产品", [["2024", 0], ["2026", 2.2]]]] },
  "21_regulatory_timeline": { "events": [["2024-Q2", "数据合规办法试行"]] },
  "23_opportunity_matrix": { "opportunities": [["O1 企业级订阅", 0.82, 0.74, 0.15]] },
  "24_implementation_gantt": { "phases": [["Phase 1 市场进入", 0, 6]] },
  "26_financial_projections": { "years": [2025, 2026], "revenue": [1.8, 2.4], "ebitda": [0.2, 0.45] },
  "27_scenario_analysis": { "metrics": ["Revenue Y5"], "conservative": [4.2], "base": [5.6], "optimistic": [7.1] }
}
```

数据键语义详见渲染器源码 docstring；所有未注明的可选键都有演示默认值。

## 数据收集纪律（每图先值后图）

1. **先检索**：对每个核心图，用
   `glmws.py search "<market> market size 2024 CAGR forecast"` 收集 2-3
   个来源；页面抓取 `glmws.py fetch "<URL>" --max-chars 4000`（每图至多
   2 个 URL）。
2. **再取值**：把检索到的数值写进 `data.json` 对应键；无法取得的字段
   保留演示值并**在报告该图 caption 与正文明确标注估计/来源缺失**。
3. **后渲染**：`--data data.json --skip-existing` 补齐正式图。
4. 引用一致性：图内数值必须与 `references.bib` / 正文引用来源一致，
   禁止图正文两套数。

## 通用降级路径（未本地化的图型）

源技能个别高度定制图（如 cover hero AI 插画、战略组图谱等）本地
matplotlib 目录未覆盖时：

- 封面主视觉 → LaTeX `\titlepage` 排版（模板已内置）
- 概念插画类 → 省略或用 `06_exec_summary` 面板承担
- 极定制图 → 按 `references/report_structure_guide.md` 的章节要求
  改为表格呈现（LaTeX 表格规范见 `assets/FORMATTING_GUIDE.md`）

## 质量门槛（沿用源标准）

- 分辨率 300 DPI（渲染器已固定 `fig.savefig(..., dpi=300)`）
- 色板一致性：navy/blue/lightblue/green/orange/red 全报告统一
- 每图坐标轴、图例、数据标签齐全；caption 标注来源
- 无孤儿图（`\ref{fig:...}` 全部命中）
