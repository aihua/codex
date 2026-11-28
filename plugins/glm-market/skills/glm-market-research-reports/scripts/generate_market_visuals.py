#!/usr/bin/env python3
"""Market Research Report Visual Generator (GLM local equivalent).

The source skill shelled out to host-platform sibling skills
(scientific-schematics / generate-image). This local equivalent renders the
same catalogue with pure matplotlib: deterministic, offline, no SDK, no API
key, no subprocess chain.

CLI surface intentionally mirrors the source batch contract:
    --topic X --output-dir figures/ [--all] [--skip-existing]
    [--data data.json] [--list]

Data policy: without --data each chart renders with clearly-watermarked demo
geometry (annotated "示意数据 / DEMO DATA"); with --data the model feeds
researched values, never fabricated. Exit codes: 0 ok, 1 render failure,
2 argument or environment error (matplotlib missing).
"""
import argparse
import json
import math
import os
import sys

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
    from matplotlib.lines import Line2D
except ImportError:
    print("ERROR: matplotlib not available. Install with: "
          "uv pip install matplotlib  (or pip3 install --user matplotlib)",
          file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------------------
# CJK font autodetect (sandbox Noto Sans SC, macOS PingFang/Hiragino etc.)
# ---------------------------------------------------------------------------
_CJK_CANDIDATES = ["Noto Sans SC", "PingFang SC", "Hiragino Sans GB",
                   "Microsoft YaHei", "WenQuanYi Zen Hei",
                   "Source Han Sans SC", "Source Han Sans CN",
                   "Arial Unicode MS"]


def _setup_fonts():
    available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    picked = None
    for cand in _CJK_CANDIDATES:
        if cand in available:
            picked = cand
            break
    if picked:
        plt.rcParams["font.sans-serif"] = [picked, "DejaVu Sans"]
    else:
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return picked


CJK_FONT = _setup_fonts()
WATERMARK = ("示意数据（请以调研值经 --data 提供替换）DEMO DATA — replace via --data"
             if CJK_FONT else
             "DEMO DATA — replace with researched values via --data")

PALETTE = {"navy": "#1f3864", "blue": "#2e75b6", "lightblue": "#9dc3e6",
           "green": "#548235", "orange": "#ed7d31", "red": "#c00000",
           "yellow": "#ffc000", "purple": "#7030a0", "gray": "#7f7f7f",
           "teal": "#2e9b9b"}


def _watermark(fig):
    fig.text(0.99, 0.005, WATERMARK, ha="right", va="bottom", fontsize=6,
             color="#999999", alpha=0.85)


def _demo_note(ax, text, where="bottom right"):
    ax.annotate(text, xy=(0.99, 0.02) if where == "bottom right" else (0.99, 0.98),
                xycoords="axes fraction", ha="right", va="bottom"
                if where == "bottom right" else "top",
                fontsize=6, color="#999999", alpha=0.85)


# ---------------------------------------------------------------------------
# Core visual 1 — market growth trajectory (bar, historical vs projected)
# ---------------------------------------------------------------------------
def r_growth(topic, out, data=None):
    d = data or {}
    years = d.get("years", list(range(2020, 2035)))
    values = d.get("values", [round(18 + i * 3.6 + (i % 3) * 0.4, 1)
                              for i in range(len(years))])
    if len(values) != len(years):
        print("ERROR growth: years/values length mismatch", file=sys.stderr)
        return False
    split = d.get("split_year", 2025)
    nan = float("nan")
    hist = [v if y < split else nan for y, v in zip(years, values)]
    proj = [v if y >= split else nan for y, v in zip(years, values)]
    fig, ax = plt.subplots(figsize=(9, 5.4), constrained_layout=True)
    x = range(len(years))
    ax.bar(x, hist, color=PALETTE["navy"],
           label="Historical")
    ax.bar(x, proj, color=PALETTE["lightblue"], label="Projected")
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(y) for y in years], rotation=45)
    ax.axvline(split - years[0] - 0.5, ls="--", color=PALETTE["gray"], lw=1)
    cagr = d.get("cagr", round(((values[-1] / values[0]) ** (1 / (len(years) - 1)) - 1) * 100, 1))
    ax.set_title(f"Market Growth Trajectory — {topic}\n"
                 f"(CAGR {cagr:.1f}%, split at {split})",
                 fontsize=13, color=PALETTE["navy"])
    ax.set_ylabel("Market Size (USD Billions)")
    for xi, v in zip(x, values):
        ax.annotate(f"{v:.0f}", (xi, v), textcoords="offset points",
                    xytext=(0, 3), ha="center", fontsize=7)
    ax.legend(loc="upper left")
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Core visual 2 — TAM/SAM/SOM concentric circles
# ---------------------------------------------------------------------------
def r_tam(topic, out, data=None):
    d = data or {}
    tam, sam, som = d.get("tam", 50), d.get("sam", 15), d.get("som", 3)
    fig, ax = plt.subplots(figsize=(7.2, 7.2), constrained_layout=True)
    ax.set_aspect("equal")
    scale = 3.0 / math.sqrt(tam)
    r_t, r_s, r_o = 3.0, math.sqrt(sam) * scale, math.sqrt(som) * scale
    for r, c, lab in [(r_t, PALETTE["lightblue"], "TAM"),
                      (r_s, PALETTE["blue"], "SAM"),
                      (r_o, PALETTE["navy"], "SOM")]:
        ax.add_patch(Circle((0, 0), r, facecolor=c, alpha=0.75,
                            edgecolor="white", lw=2, zorder=1))
    ax.text(0, r_t * 0.92, f"TAM — Total Addressable Market  ${tam}B",
            ha="center", va="center", fontsize=11, color=PALETTE["navy"])
    ax.text(0, r_s * 0.6, f"SAM — Serviceable Addressable  ${sam}B",
            ha="center", va="center", fontsize=10, color="white")
    ax.text(0, 0, f"SOM\nObtainable  ${som}B", ha="center", va="center",
            fontsize=10, color="white")
    ax.set_xlim(-3.4, 3.4)
    ax.set_ylim(-3.4, 3.4)
    ax.axis("off")
    ax.set_title(f"TAM / SAM / SOM — {topic}", fontsize=13, color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Core visual 3 — Porter's Five Forces
# ---------------------------------------------------------------------------
def r_porter(topic, out, data=None):
    d = data or {}
    forces = d.get("forces", {
        "Rivalry": ("HIGH", ["集中度提升", "价格战频率", "产品同质化"]),
        "New Entrants": ("MEDIUM", ["资本门槛中等", "渠道壁垒", "品牌积累"]),
        "Supplier Power": ("LOW", ["供给分散", "切换成本低", "替代原料多"]),
        "Buyer Power": ("HIGH", ["采购集中", "信息透明", "转换成本低"]),
        "Substitutes": ("MEDIUM", ["替代技术性价比", "用户习惯", "监管偏向"]),
    })
    rating_color = {"HIGH": PALETTE["red"], "MEDIUM": PALETTE["yellow"],
                    "LOW": PALETTE["green"]}
    fig, ax = plt.subplots(figsize=(8.6, 7.4), constrained_layout=True)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(cx, cy, w, h, title, rating, factors, ec):
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                    boxstyle="round,pad=0.08",
                                    facecolor="white", edgecolor=ec, lw=2))
        ax.text(cx, cy + h / 2 - 0.42, title, ha="center", fontsize=11,
                color=PALETTE["navy"], weight="bold")
        ax.text(cx, cy + h / 2 - 0.95, rating, ha="center", fontsize=9,
                color=rating_color.get(rating, PALETTE["gray"]), weight="bold")
        for i, f in enumerate(factors):
            ax.text(cx, cy - 0.1 - i * 0.42, f"· {f}", ha="center", fontsize=8)

    c, w, h = (5, 5), 3.2, 2.6
    box(c[0], c[1], w, h, "Competitive Rivalry", *forces["Rivalry"],
        ec=PALETTE["navy"])
    box(5, 8.9, 3.4, 1.9, "Threat of New Entrants", *forces["New Entrants"],
        ec=PALETTE["blue"])
    box(1.75, 5, 3.0, 1.9, "Supplier Power", *forces["Supplier Power"],
        ec=PALETTE["blue"])
    box(8.25, 5, 3.0, 1.9, "Buyer Power", *forces["Buyer Power"],
        ec=PALETTE["blue"])
    box(5, 1.35, 3.4, 1.9, "Threat of Substitutes", *forces["Substitutes"],
        ec=PALETTE["blue"])
    for xy in [((5, 7.9), (5, 6.3)), ((3.25, 5), (3.4, 5)),
               ((6.75, 5), (6.6, 5)), ((5, 2.3), (5, 3.7))]:
        ax.add_patch(FancyArrowPatch(xy[0], xy[1], arrowstyle="-|>",
                                     mutation_scale=16, lw=1.6,
                                     color=PALETTE["gray"]))
    ax.set_title(f"Porter's Five Forces — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Core visual 4 — competitive positioning 2x2 matrix
# ---------------------------------------------------------------------------
def r_positioning(topic, out, data=None):
    d = data or {}
    companies = d.get("companies", [
        ("Alpha", 0.72, 0.78, 0.16), ("Beta", 0.25, 0.80, 0.09),
        ("Gamma", 0.70, 0.30, 0.12), ("Delta", 0.28, 0.28, 0.07),
        ("Epsilon", 0.50, 0.58, 0.11), ("Zeta", 0.86, 0.62, 0.14),
        ("Eta", 0.40, 0.85, 0.06), ("Theta", 0.62, 0.18, 0.05),
    ])
    fig, ax = plt.subplots(figsize=(8.4, 7.0), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axvline(0.5, color=PALETTE["gray"], lw=1, ls="--")
    ax.axhline(0.5, color=PALETTE["gray"], lw=1, ls="--")
    ax.set_xlabel("Market Focus  (Niche → Broad)")
    ax.set_ylabel("Solution Approach  (Product → Platform)")
    for label, x, y, s in companies:
        ax.scatter(x, y, s=max(s, 0.04) * 2400, color=PALETTE["blue"],
                   alpha=0.75, edgecolor=PALETTE["navy"], zorder=3)
        ax.annotate(label, (x, y), xytext=(0, 12), textcoords="offset points",
                    ha="center", fontsize=9)
    for (qx, qy, t) in [(0.25, 0.93, "Niche Platforms"), (0.75, 0.93, "Platform Leaders"),
                        (0.25, 0.06, "Specialists"), (0.75, 0.06, "Product Leaders")]:
        ax.text(qx, qy, t, ha="center", fontsize=9, color=PALETTE["gray"])
    ax.set_title(f"Competitive Positioning Matrix — {topic}\n"
                 "(bubble size = est. market share)", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Core visual 5 — risk heatmap
# ---------------------------------------------------------------------------
def r_risk(topic, out, data=None):
    d = data or {}
    risks = d.get("risks", [
        ("R1 需求波动", 0.72, 0.78), ("R2 监管变化", 0.55, 0.88),
        ("R3 供应链中断", 0.35, 0.82), ("R4 价格战", 0.80, 0.62),
        ("R5 技术替代", 0.28, 0.55), ("R6 汇率敞口", 0.62, 0.30),
        ("R7 人才流失", 0.45, 0.42), ("R8 数据合规", 0.20, 0.68),
        ("R9 渠道依赖", 0.68, 0.48), ("R10 融资收紧", 0.33, 0.25),
    ])
    fig, ax = plt.subplots(figsize=(8.2, 6.6), constrained_layout=True)
    grid = [[0 for _ in range(4)] for _ in range(4)]
    for gx in range(4):
        for gy in range(4):
            lvl = (gx + gy) / 6
            color = (min(lvl * 2 + 0.12, 1), 0.75 - lvl * 0.62, 0.22)
            ax.add_patch(Rectangle((gx, gy), 1, 1, facecolor=color,
                                   edgecolor="white", lw=2))
    for name, p, i in risks:
        ax.scatter(p * 4 - 0.5, i * 4 - 0.5, s=140, color=PALETTE["navy"],
                   edgecolor="white", zorder=3)
        ax.annotate(name, (p * 4 - 0.5, i * 4 - 0.5), xytext=(6, -3),
                    textcoords="offset points", fontsize=8)
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 4)
    ax.set_xticks([0.5, 1.5, 2.5, 3.5])
    ax.set_xticklabels(["Low", "Medium", "High", "Critical"])
    ax.set_yticks([0.5, 1.5, 2.5, 3.5])
    ax.set_yticklabels(["Unlikely", "Possible", "Likely", "Very likely"])
    ax.set_xlabel("Impact")
    ax.set_ylabel("Probability")
    ax.set_title(f"Risk Heatmap — {topic}", fontsize=13, color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Core visual 6 — executive summary metrics panel
# ---------------------------------------------------------------------------
def r_exec(topic, out, data=None):
    d = data or {}
    metrics = d.get("metrics", [
        ("Market Size 2024", "$45.2B"), ("Projected 2030", "$98.7B"),
        ("CAGR", "15.3%"), ("Top Player Share", "23%"),
        ("Segment Leaders", "APAC · Enterprise"), ("Risk Level", "Medium"),
    ])
    findings = d.get("findings", ["需求端结构性增长，供给端集中度提升",
                                  "头部两家厂商利润率高于行业 6-8pct",
                                  "监管变量集中于数据合规与准入"])
    fig, ax = plt.subplots(figsize=(10.4, 5.8), constrained_layout=True)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.text(6, 5.6, f"{topic} — Executive Summary", ha="center", fontsize=15,
            color=PALETTE["navy"], weight="bold")
    ax.add_patch(FancyBboxPatch((0.4, 1.6), 11.2, 3.4,
                                boxstyle="round,pad=0.15",
                                facecolor="#f2f6fb", edgecolor=PALETTE["blue"],
                                lw=1.5))
    for i, (k, v) in enumerate(metrics):
        col, row = i % 3, i // 3
        cx, cy = 2.2 + col * 3.8, 4.35 - row * 1.7
        ax.text(cx, cy, v, ha="center", fontsize=17,
                color=PALETTE["blue"], weight="bold")
        ax.text(cx, cy - 0.62, k, ha="center", fontsize=9, color=PALETTE["gray"])
    for i, f in enumerate(findings):
        ax.text(0.9, 1.15 - i * 0.34, f"- {f}", fontsize=9,
                color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Extended visuals (12) — all deterministic matplotlib primitives
# ---------------------------------------------------------------------------
def r_regional(topic, out, data=None):
    d = data or {}
    labels = d.get("labels", ["North America", "Europe", "Asia-Pacific",
                              "Rest of World"])
    values = d.get("values", [40.3, 26.8, 23.2, 9.7])
    fig, ax = plt.subplots(figsize=(7.4, 5.8), constrained_layout=True)
    colors = [PALETTE["navy"], PALETTE["blue"], PALETTE["teal"],
              PALETTE["lightblue"]]
    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors,
           textprops={"fontsize": 10}, startangle=100,
           wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax.set_title(f"Regional Market Breakdown — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_segments(topic, out, data=None):
    d = data or {}
    labels = d.get("labels", ["Enterprise", "SMB", "Consumer", "Public"])
    hist = d.get("hist", [22.4, 11.8, 7.9, 3.1])
    proj = d.get("proj", [48.6, 24.2, 14.8, 6.6])
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(8.6, 5.6), constrained_layout=True)
    ax.bar([i - 0.19 for i in x], hist, width=0.38,
           color=PALETTE["navy"], label="2024")
    ax.bar([i + 0.19 for i in x], proj, width=0.38,
           color=PALETTE["lightblue"], label="2030E")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("USD Billions")
    ax.set_title(f"Segment Growth Comparison — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    ax.legend(loc="upper right")
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_drivers(topic, out, data=None):
    d = data or {}
    drivers = d.get("drivers", [
        ("数字化渗透", 0.85, 0.78), ("政策补贴", 0.65, 0.55),
        ("成本下降", 0.75, 0.45), ("渠道扩张", 0.5, 0.72),
        ("替代旧技术", 0.45, 0.62), ("出海", 0.30, 0.38),
    ])
    fig, ax = plt.subplots(figsize=(8.2, 6.4), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axvspan(0.5, 1.0, ymin=0.5, color="#eaf1f8", alpha=0.6)
    ax.set_xlabel("Likelihood")
    ax.set_ylabel("Impact")
    ax.scatter([i for _, i, _ in drivers], [p for _, _, p in drivers],
               s=520, color=PALETTE["blue"], alpha=0.8,
               edgecolor=PALETTE["navy"])
    for name, i, p in drivers:
        ax.annotate(name, (i, p), xytext=(9, -4),
                    textcoords="offset points", fontsize=9)
    ax.set_title(f"Driver Impact Matrix — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_pestle(topic, out, data=None):
    d = data or {}
    dims = d.get("dims", ["Political", "Economic", "Social", "Technological",
                          "Legal", "Environmental"])
    scores = d.get("scores", [3.2, 4.1, 3.0, 4.6, 3.8, 2.6])
    angles = [n / float(len(dims)) * 2 * math.pi for n in range(len(dims))]
    angles += angles[:1]
    vals = scores + scores[:1]
    fig = plt.figure(figsize=(7.2, 6.4))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, vals, color=PALETTE["blue"], lw=2)
    ax.fill(angles, vals, color=PALETTE["blue"], alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, fontsize=10)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylim(0, 5)
    ax.set_title(f"PESTLE Assessment — {topic}", fontsize=13,
                 color=PALETTE["navy"], pad=18)
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_share(topic, out, data=None):
    d = data or {}
    labels = d.get("labels", ["Leader", "Player2", "Player3", "Player4",
                              "Others"])
    values = d.get("values", [23, 17, 12, 9, 39])
    fig, ax = plt.subplots(figsize=(8.6, 5.4), constrained_layout=True)
    ylabels = [f"{l} — {v}%" for l, v in zip(labels, values)]
    ax.barh(ylabels, values,
            color=[PALETTE["navy"], PALETTE["blue"], PALETTE["teal"],
                   PALETTE["lightblue"], PALETTE["gray"]])
    ax.invert_yaxis()
    ax.set_xlabel("Market Share (%)")
    ax.set_title(f"Market Share — {topic}", fontsize=13, color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_customer(topic, out, data=None):
    d = data or {}
    labels = d.get("labels", ["大型企业", "中型企业", "小型企业", "个人用户"])
    values = d.get("values", [52, 26, 15, 7])
    growth = d.get("growth", [9, 18, 24, 31])
    fig, ax = plt.subplots(figsize=(8.4, 5.6), constrained_layout=True)
    bars = ax.barh(labels, values, color=PALETTE["blue"])
    ax.invert_yaxis()
    for b, g in zip(bars, growth):
        ax.annotate(f"+{g}% CAGR", (b.get_width(), b.get_y() + b.get_height() / 2),
                    xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=9, color=PALETTE["green"])
    ax.set_xlabel("Share of market revenue (%)")
    ax.set_title(f"Customer Segmentation — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_tech_roadmap(topic, out, data=None):
    d = data or {}
    lanes = d.get("lanes", [
        ("核心产品", [("2024", 0), ("2026", 2.2), ("成熟", 4.4)]),
        ("平台化", [("2025", 1.0), ("2027", 3.2)]),
        ("AI 能力", [("2026", 2.6), ("2029", 5.0)]),
        ("国际化", [("2027", 3.8), ("2030", 6.2)]),
    ])
    fig, ax = plt.subplots(figsize=(9.6, 5.4), constrained_layout=True)
    for i, (lane, marks) in enumerate(lanes):
        y = len(lanes) - i
        ax.axhline(y, color="#e8edf3", lw=8)
        for label, x in marks:
            ax.scatter(x, y, s=140, color=PALETTE["blue"], zorder=3,
                       edgecolor=PALETTE["navy"])
            ax.annotate(label, (x, y), xytext=(0, 11),
                        textcoords="offset points", ha="center", fontsize=8)
    ax.set_yticks([len(lanes) - i for i in range(len(lanes))])
    ax.set_yticklabels([l for l, _ in lanes], fontsize=10)
    ax.set_xticks(range(0, 8))
    ax.set_xticklabels(["2024", "2025", "2026", "2027", "2028", "2029",
                        "2030", "2031"])
    ax.set_ylim(0.4, len(lanes) + 0.8)
    ax.set_title(f"Technology Roadmap — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_reg_timeline(topic, out, data=None):
    d = data or {}
    events = d.get("events", [
        ("2024-Q2", "数据合规办法试行"), ("2025-Q1", "准入负面清单更新"),
        ("2026-Q3", "行业强制标准 v2"), ("2027-Q4", "跨境数据规则"),
    ])
    fig, ax = plt.subplots(figsize=(9.4, 4.2), constrained_layout=True)
    ax.axhline(0, color=PALETTE["navy"], lw=2)
    for i, (when, what) in enumerate(events):
        x = i * 2.4 + 1
        ax.scatter(x, 0, s=180, color=PALETTE["blue"], zorder=3)
        up = i % 2 == 0
        ax.annotate(f"{when}\n{what}", (x, 0), xytext=(0, 26 if up else -42),
                    textcoords="offset points", ha="center", fontsize=9,
                    color=PALETTE["navy"])
    ax.set_xlim(0, len(events) * 2.4 + 1)
    ax.set_ylim(-1.5, 1.5)
    ax.axis("off")
    ax.set_title(f"Regulatory Timeline — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_opportunity(topic, out, data=None):
    d = data or {}
    opps = d.get("opportunities", [
        ("O1 企业级订阅", 0.82, 0.74, 0.15), ("O2 APAC 扩张", 0.7, 0.55, 0.11),
        ("O3 增值服务", 0.6, 0.78, 0.08), ("O4 平台生态", 0.45, 0.35, 0.13),
        ("O5 并购整合", 0.35, 0.5, 0.06),
    ])
    fig, ax = plt.subplots(figsize=(8.2, 6.6), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axvline(0.5, ls="--", color=PALETTE["gray"])
    ax.axhline(0.5, ls="--", color=PALETTE["gray"])
    for name, att, ab, size in opps:
        ax.scatter(att, ab, s=max(size, 0.05) * 2600, color=PALETTE["green"],
                   alpha=0.8, edgecolor=PALETTE["navy"])
        ax.annotate(name, (att, ab), xytext=(0, 13),
                    textcoords="offset points", ha="center", fontsize=9)
    ax.set_xlabel("Attractiveness")
    ax.set_ylabel("Ability to Win")
    ax.set_title(f"Opportunity Matrix — {topic}\n(bubble size = est. value)",
                 fontsize=13, color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_gantt(topic, out, data=None):
    d = data or {}
    phases = d.get("phases", [
        ("Phase 1 市场进入", 0, 6), ("Phase 2 产品本地化", 5, 10),
        ("Phase 3 渠道搭建", 9, 16), ("Phase 4 规模化", 15, 24),
    ])
    fig, ax = plt.subplots(figsize=(9.6, 4.8), constrained_layout=True)
    for i, (name, s, e) in enumerate(phases):
        ax.barh(len(phases) - i, e - s, left=s, height=0.5,
                color=PALETTE["blue"], edgecolor=PALETTE["navy"])
        ax.annotate(f"{name}  (M{s}-M{e})", (s, len(phases) - i),
                    xytext=(4, 3), textcoords="offset points", fontsize=9)
    ax.set_xlim(0, 26)
    ax.set_ylim(0.4, len(phases) + 0.6)
    ax.set_xlabel("Months from kick-off")
    ax.set_yticks([])
    ax.set_title(f"Implementation Roadmap — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_financials(topic, out, data=None):
    d = data or {}
    years = d.get("years", list(range(2025, 2031)))
    revenue = d.get("revenue", [1.8, 2.4, 3.2, 4.3, 5.6, 7.2])
    ebitda = d.get("ebitda", [0.2, 0.45, 0.9, 1.5, 2.2, 3.1])
    fig, ax = plt.subplots(figsize=(8.8, 5.4), constrained_layout=True)
    ax.fill_between(years, revenue, color=PALETTE["lightblue"], alpha=0.5,
                    label="Revenue")
    ax.plot(years, revenue, color=PALETTE["navy"], lw=2, marker="o")
    ax.plot(years, ebitda, color=PALETTE["green"], lw=2, ls="--", marker="s",
            label="EBITDA")
    ax.set_ylabel("USD Billions")
    ax.set_title(f"Financial Projections — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    ax.legend(loc="upper left")
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


def r_scenarios(topic, out, data=None):
    d = data or {}
    metrics = d.get("metrics", ["Revenue Y5", "EBITDA Y5", "Market Share",
                                "ROI"])
    cons = d.get("conservative", [4.2, 1.6, 8, 11])
    base = d.get("base", [5.6, 2.2, 11, 18])
    opt = d.get("optimistic", [7.1, 3.3, 14, 26])
    x = range(len(metrics))
    fig, ax = plt.subplots(figsize=(9.2, 5.4), constrained_layout=True)
    for off, vals, c, lab in [(-0.26, cons, PALETTE["gray"], "Conservative"),
                              (0.0, base, PALETTE["blue"], "Base Case"),
                              (0.26, opt, PALETTE["green"], "Optimistic")]:
        ax.bar([i + off for i in x], vals, width=0.24, color=c, label=lab)
    ax.set_xticks(list(x))
    ax.set_xticklabels(metrics)
    ax.set_title(f"Scenario Analysis — {topic}", fontsize=13,
                 color=PALETTE["navy"])
    ax.legend(loc="upper right")
    _watermark(fig)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Catalogue: filename -> renderer, mirroring the source naming convention
# ---------------------------------------------------------------------------
CORE = [
    ("01_market_growth_trajectory.png", r_growth,
     "Bar chart: historical vs projected, CAGR annotation"),
    ("02_tam_sam_som.png", r_tam, "Concentric circles TAM/SAM/SOM"),
    ("03_porters_five_forces.png", r_porter, "Five forces boxes + ratings"),
    ("04_competitive_positioning.png", r_positioning, "2x2 matrix, bubble share"),
    ("05_risk_heatmap.png", r_risk, "Probability x impact heatmap"),
    ("06_exec_summary.png", r_exec, "Metrics panel (source: generate-image)"),
]
EXTENDED = [
    ("07_regional_breakdown.png", r_regional, "Regional pie"),
    ("08_segment_growth.png", r_segments, "Segment grouped bars"),
    ("09_driver_impact.png", r_drivers, "Driver impact scatter"),
    ("10_pestle.png", r_pestle, "PESTLE radar"),
    ("13_market_share.png", r_share, "Share horizontal bars"),
    ("16_customer_segments.png", r_customer, "Customer segment bars"),
    ("19_technology_roadmap.png", r_tech_roadmap, "Roadmap lanes"),
    ("21_regulatory_timeline.png", r_reg_timeline, "Regulatory milestones"),
    ("23_opportunity_matrix.png", r_opportunity, "Attractiveness x ability"),
    ("24_implementation_gantt.png", r_gantt, "Phase Gantt"),
    ("26_financial_projections.png", r_financials, "Revenue/EBITDA curves"),
    ("27_scenario_analysis.png", r_scenarios, "Three-scenario bars"),
]


def _load_data(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read --data file {path}: {exc}",
              file=sys.stderr)
        sys.exit(2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate market research report visuals locally "
                    "(matplotlib equivalent of the host scientific-schematics/"
                    "generate-image chain). Default: 6 core visuals.")
    ap.add_argument("--topic", "-t", required=False,
                    help="Market topic (used in every chart title)")
    ap.add_argument("--output-dir", "-o", default="figures",
                    help="Output directory (default: figures)")
    ap.add_argument("--all", "-a", action="store_true",
                    help="Also render the 12 extended visuals")
    ap.add_argument("--skip-existing", action="store_true",
                    help="Do not re-render existing files")
    ap.add_argument("--data", default=None,
                    help="Optional JSON file with researched values "
                         "(keyed by filename or renderer name)")
    ap.add_argument("--list", action="store_true",
                    help="List the catalogue and exit")
    args = ap.parse_args(argv)

    if args.list and not args.topic:
        print("core (default):")
        for fn, _, desc in CORE:
            print(f"  {fn:34s} {desc}")
        print("extended (--all):")
        for fn, _, desc in EXTENDED:
            print(f"  {fn:34s} {desc}")
        return 0
    if not args.topic:
        ap.error("the following arguments are required: --topic/-t")
        return 2

    catalogue = CORE + (EXTENDED if args.all else [])
    if args.list:
        print("core (default):")
        for fn, _, desc in CORE:
            print(f"  {fn:34s} {desc}")
        print("extended (--all):")
        for fn, _, desc in EXTENDED:
            print(f"  {fn:34s} {desc}")
        return 0

    data_all = _load_data(args.data) if args.data else {}
    os.makedirs(args.output_dir, exist_ok=True)

    ok = fail = skipped = 0
    for fn, renderer, _ in catalogue:
        out = os.path.join(args.output_dir, fn)
        if args.skip_existing and os.path.exists(out):
            print(f"  [SKIP] {fn} exists")
            skipped += 1
            continue
        item = data_all.get(fn, data_all.get(fn.replace(".png", ""), None))
        try:
            if renderer(args.topic, out, item):
                print(f"  [OK]   {fn}")
                ok += 1
            else:
                print(f"  [FAIL] {fn}")
                fail += 1
        except Exception as exc:  # noqa: BLE001 — report and continue batch
            print(f"  [FAIL] {fn}: {exc}")
            fail += 1

    print(f"\n{ok} ok / {fail} fail / {skipped} skipped -> {args.output_dir}/")
    if not args.data:
        print("NOTE: rendered with watermarked DEMO data; feed researched "
              "values via --data data.json (see references/"
              "visual_generation_guide.md)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
