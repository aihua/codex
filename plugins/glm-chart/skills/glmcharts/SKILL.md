---
name: glmcharts
metadata:
  author: Z.AI
  version: "1.0"
description: >
    Professional chart and diagram creation.
    Data charts (bar, line, pie, scatter, heatmap, radar, boxplot, histogram,
    area, waterfall, regression/distribution); structural diagrams (flowchart,
    mind map, tree, org chart, SWOT/radial, network graph); dashboards and KPI
    panels. Scene-based routing across matplotlib, seaborn, ECharts, D3.js,
    Mermaid and Playwright+CSS with anti-overlap rules and publication-ready
    output. Use when the user wants to create, draw, plot, visualize or polish
    any chart, graph, diagram or dashboard. NOT for: PDF layout (pdf skill),
    slide decks (slides skill), spreadsheets with embedded charts (xlsx skill),
    AI image generation (image_gen), posters/infographics (pdf Creative
    pipeline). FORBIDDEN: matplotlib/seaborn for mind maps, trees, org charts,
    flowcharts or any structural diagram - these MUST use Playwright+CSS.
license: Proprietary. LICENSE.txt has complete terms
---

# GLM Charts

Publication-quality charts and diagrams. This file is only the router: it picks ONE scene, ONE template file, and the template does the rest. Follow it exactly.

## Environment (run once)

```bash
bash scripts/setup.sh          # relative to this skill directory; --no-install = check only
```

Interpreter rule for every render command below: if the environment sets `GLMCHARTS_PYTHON`, use that interpreter; otherwise use `python3`. Example:

```bash
"${GLMCHARTS_PYTHON:-python3}" render_chart.py
```

## Mandatory 5-step workflow

Execute these five steps in order. Never skip a step. Never invent your own route.

1. **Classify.** Match the request to exactly ONE row of the routing table below. When two rows match, structural-diagram rows (3, 5, 6) win over data-chart rows.
2. **Load.** Read exactly ONE template file - the one named in that row. Do not open any other template file.
3. **Copy.** Copy the template's code skeleton verbatim. Change ONLY the data, labels, text and colors. Never rewrite the structure from zero.
4. **Render.** Save the script in the working directory, run it with the interpreter rule above, produce the PNG.
5. **Verify.** Run the delivery checklist at the end of this file. If any item fails, fix the data or spacing and re-render once, then deliver the image (plus code, if the user asked for code).

## Routing table

| # | User wants (examples) | Framework | Read this one template |
|---|---|---|---|
| 1 | Data chart: bar / line / scatter / pie / radar / heatmap / waterfall / academic figure（柱状图 折线图 散点图 饼图 雷达图 热力图） | matplotlib | `references/matplotlib.md` |
| 2 | Statistical: regression / distribution / boxplot / correlation | seaborn | `references/seaborn.md` |
| 3 | Flowchart with phases, or more than 6 nodes, or CJK-heavy（流程图） | Playwright + CSS, Layout C | `references/playwright-css.md` |
| 4 | Simple flat flowchart: 6 nodes or fewer, truly no phases | Mermaid | `references/mermaid.md` |
| 5 | Mind map / tree / org chart（思维导图 组织架构图） | Playwright + CSS | `references/mindmap-css.md` |
| 6 | Center-radial: SWOT / BSC / PEST / Five Forces | Playwright + CSS | `references/radial-grid.md` |
| 7 | Relationship / network graph | ECharts graph | `references/echarts.md` |
| 8 | Dashboard / KPI panel / candlestick / very large data | ECharts | `references/echarts.md` |
| 9 | Fully custom interactive visualization | D3.js | `references/d3.md` |

**Default for any flowchart request: row 3 (phased vertical, Layout C).** When in doubt, choose row 3. A phased layout with one phase still looks professional; a flat grid with phases never does.

## Hard rules

1. **User-named format wins.** If the user explicitly asks for Mermaid / markdown / ECharts / D3, use exactly that tool and deliver the requested format. Never silently switch tools. Never screenshot raw code text as the "image". When the user requests Mermaid: output the fenced ```mermaid code block AND render it to an image; if rendering fails, deliver the code block and say to paste it into mermaid.live.
2. **Structural diagrams never use matplotlib/seaborn.** Mind maps, trees, org charts, flowcharts, radial grids go to rows 3, 5 or 6 only.
3. **Never write chart code from zero.** The template file IS the code. Copy it and replace data.
4. **One template file per task.** Read no second framework file.
5. **Zero overlap.** No label, legend, annotation, connector or title may overlap any element. Place legends outside the plot area with `bbox_to_anchor`. Pie slices under 5%: leader lines or an outside legend, never forced direct labels. Radar fills always `alpha=0.25`.
6. **Low-saturation palette.** Roughly 70% neutral background, 20% secondary, 10% accent. Saturated color belongs to borders (2px), text and small elements only. Forbidden saturated backgrounds: `#3B82F6 #2563EB #1D4ED8 #10B981 #059669 #22C55E #EF4444 #DC2626 #F87171 #8B5CF6 #7C3AED #A855F7 #F59E0B #D97706`. Use pale backgrounds instead: `#EFF6FF #DBEAFE #F0FDF4 #FFF7ED #F5F3FF #EDE9FE #F8FAFC #F1F5F9`.
7. **Fonts.** At most 2 font families. Always set CJK fonts explicitly in code (`Noto Sans SC` / `SimHei` / `PingFang SC` plus a Latin fallback). Title 18-24px, body 13-15px, annotation 11-13px; never below a 10px floor. When text overflows: condense text, then enlarge the canvas; shrinking below the floor is the last resort.
8. **Titles state conclusions**, not field names ("华东区贡献 43% 营收", not "各地区销售额"). Remove non-essential elements (top/right spines, tick clutter, legend box borders).

## Mermaid upgrade triggers

If the user did NOT explicitly request Mermaid, switch to row 3 when ANY is true: total nodes above 6; any node text above 12 CJK characters; more than 3 parallel branches; subgraphs nested more than 2 levels; more than 2 connector crossings; side annotations or dashed note boxes; loop-back arrows; the process has identifiable phases.

If staying with Mermaid: `padding: 32`, `nodeSpacing: 80`, `rankSpacing: 80`; node text at most 10 CJK chars per line, wrapped with `<br>`; quote every label like `A["text"]`. Rendering pitfalls and the corrected screenshot script are in `references/mermaid.md`.

## Large datasets

| Data points | Approach |
|---|---|
| under 1,000 | matplotlib / any framework |
| 1,000 - 10,000 | matplotlib with no markers, or ECharts |
| 10,000 - 100,000 | ECharts (Canvas mode) |
| above 100,000 | ECharts `large: true` or WebGL |

## Render conventions

- Static charts: `dpi=300`; pie and radar use square `figsize=(8, 8)`. Prefer `constrained_layout=True` over `tight_layout()`. Bar Y-axis starts at 0; give data labels 15-20% headroom via `ylim`.
- Playwright screenshots: `device_scale_factor=2` (1.5 for 3000px+ images; 1-1.5 when embedding into PDF). After rendering, read the element's real bounding box and resize the viewport to fit; minimum 800px single column, 1200px multi-column. Chromium comes from the Playwright installation; respect `PLAYWRIGHT_BROWSERS_PATH` when the environment sets it.
- Export images to the current working directory with a descriptive filename (for example `sales_by_region.png`). Never silently overwrite a user file.
- Aspect ratios: when embedding images elsewhere, read the actual dimensions and scale proportionally; never hardcode both width and height.

## Delivery checklist

- [ ] Zero overlap: nodes, connectors, labels, legends - especially legend vs data, and adjacent pie/bar labels
- [ ] Hierarchy visible: primary, secondary and annotation elements clearly distinct
- [ ] Palette compliant: no forbidden saturated backgrounds anywhere
- [ ] All text at least 10px at final size; CJK characters render (no boxes)
- [ ] Legend fully visible, outside the plot area, not clipped
- [ ] Canvas large enough: checked the bounding box before screenshotting
- [ ] Mind map: every level distinct (3+ property changes), connectors visible (`#94A3B8` or darker), left-right sides balanced
- [ ] Flowchart: phases are group cards, arrows only between phases, same-hue blue-gray phase progression (never rainbow)
- [ ] Mermaid requested: code block delivered plus rendered image - never a screenshot of the code text itself
