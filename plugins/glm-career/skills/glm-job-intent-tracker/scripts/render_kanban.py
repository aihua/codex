#!/usr/bin/env python3
"""render_kanban.py — 求职看板渲染器（宿主聊天内 artifact 看板的本地等效）。

宿主平台的看板是聊天内 artifact；本地 Codex 无该工具，等效替换为：
解析 init_tracker.py 生成的 Markdown 追踪表，渲染一个**自包含静态 HTML**（内联
CSS、零 CDN、零 JS 依赖），用户用浏览器直接打开。

用法：
    python render_kanban.py --tracker tracker.md --out kanban.html
    python render_kanban.py --tracker tracker.md            # 默认输出 kanban.html

退出码：0 成功；1 无有效数据行；2 参数/IO 错误。
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import sys
from pathlib import Path

KANBAN_GROUPS = [
    ("投递中", ["投递"]),
    ("笔试", ["笔试"]),
    ("面试中", ["一面", "二面", "三面", "HR面"]),
    ("Offer", ["Offer"]),
    ("Reject", ["Reject"]),
    ("沉默", ["沉默"]),
]
KANBAN_COLORS = {"投递中": "#2e75b6", "笔试": "#7030a0", "面试中": "#ed7d31",
                 "Offer": "#548235", "Reject": "#7f7f7f", "沉默": "#c00000"}


def parse_tracker(path: Path):
    """Parse the markdown table produced by init_tracker.py --format md."""
    text = path.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or cells[0] in ("公司", "") or set(cells[0]) <= {"-"}:
            continue  # header / separator
        if cells[0] == "示例公司":
            continue  # sample row
        if len(cells) < 11:
            continue
        rows.append(cells[:11])
    return rows


def deadline_hint(row):
    """Deadline within 3 days (or overdue) -> urgency hint, else empty string."""
    deadline = row[7].strip()
    try:
        d = dt.date.fromisoformat(deadline)
    except ValueError:
        return ""
    days = (d - dt.date.today()).days
    if 0 <= days <= 3:
        return f"⏰ Deadline 还有 {days} 天"
    if days < 0:
        return f"⚠️ Deadline 已过 {-days} 天"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="求职投递追踪表 → 自包含 HTML 看板")
    ap.add_argument("--tracker", required=True, help="init_tracker.py 生成的 tracker.md")
    ap.add_argument("--out", default="kanban.html", help="输出 HTML 路径（默认 kanban.html）")
    args = ap.parse_args()

    src = Path(args.tracker).expanduser()
    if not src.is_file():
        print(f"✗ 找不到追踪表：{src}", file=sys.stderr)
        return 2

    rows = parse_tracker(src)
    if not rows:
        print("✗ 追踪表里没有有效数据行（只有表头/示例）", file=sys.stderr)
        return 1

    total = len(rows)
    stages = [r[5] for r in rows]
    in_interview = sum(1 for s in stages if s in ("一面", "二面", "三面", "HR面"))
    offers = stages.count("Offer")
    rejects = stages.count("Reject")
    silent = stages.count("沉默")
    pending = [r for r in rows if r[6].strip()]
    pend = len(pending)

    cards = []
    for title, group in KANBAN_GROUPS:
        items = [r for r in rows if r[5] in group]
        color = KANBAN_COLORS[title]
        card_html = []
        for r in items:
            hint = deadline_hint(r)
            note = html.escape(r[10]) if len(r) > 10 else ""
            card_html.append(
                f'<div class="card"><div class="card-title">{html.escape(r[0])}'
                f'<span class="tag" style="background:{color}">{html.escape(r[5])}</span></div>'
                f'<div class="card-sub">{html.escape(r[1])}</div>'
                f'<div class="card-action">→ {html.escape(r[6]) or "（待补充）"}</div>'
                + (f'<div class="card-hint">{hint}</div>' if hint else "")
                + (f'<div class="card-note">{note}</div>' if note else "")
                + "</div>")
        cards.append(
            f'<div class="col" data-count="{len(items)}">'
            f'<div class="col-head" style="border-top:4px solid {color}">'
            f'{title} <span class="count">{len(items)}</span></div>'
            + "".join(card_html) + "</div>")

    silent_rows = [r for r in rows if r[5] == "沉默"]
    stale_html = "".join(
        f"<li>{html.escape(r[0])} · {html.escape(r[1])}（投递日 {html.escape(r[4])}）</li>"
        for r in silent_rows)
    deadline_html = "".join(
        f"<li>{html.escape(r[0])} · {html.escape(r[6])}（Deadline {html.escape(r[7])}）</li>"
        for r in rows if deadline_hint(r))

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>求职投递看板</title>
<style>
body{{font-family:-apple-system,'PingFang SC','Noto Sans SC',sans-serif;background:#f4f6f8;margin:0;padding:24px;color:#1f2329}}
h1{{font-size:22px;margin:0 0 4px}}
.sub{{color:#7a8699;font-size:12px;margin-bottom:20px}}
.kpis{{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}}
.kpi{{background:#fff;border-radius:10px;padding:12px 18px;box-shadow:0 1px 4px rgba(0,0,0,.06);min-width:110px}}
.kpi b{{display:block;font-size:26px;margin-top:2px}}
.board{{display:flex;gap:12px;align-items:flex-start;overflow-x:auto;padding-bottom:8px}}
.col{{background:#e9edf2;border-radius:10px;padding:10px;min-width:230px;flex:1}}
.col-head{{font-weight:600;font-size:14px;padding:4px 6px 10px}}
.count{{background:#fff;border-radius:9px;padding:0 8px;font-size:12px;color:#5a6572}}
.card{{background:#fff;border-radius:8px;padding:10px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,.07)}}
.card-title{{font-weight:600;font-size:13px;display:flex;justify-content:space-between;align-items:center}}
.tag{{color:#fff;font-size:10px;border-radius:4px;padding:1px 6px;margin-left:6px}}
.card-sub{{color:#5a6572;font-size:12px;margin-top:2px}}
.card-action{{font-size:12px;margin-top:6px;color:#2e75b6}}
.card-hint{{font-size:12px;color:#c00000;margin-top:4px}}
.card-note{{font-size:11px;color:#8a94a3;margin-top:4px;border-top:1px dashed #e3e7ec;padding-top:4px}}
.warn{{background:#fff;border-left:4px solid #ed7d31;border-radius:8px;padding:12px 16px;margin-top:18px}}
.warn h3{{margin:0 0 8px;font-size:14px}}
.warn ul{{margin:0;padding-left:18px;font-size:12px;color:#4a5561}}
.warn li{{margin-bottom:4px}}
footer{{margin-top:24px;color:#a0a8b3;font-size:11px}}
</style></head><body>
<h1>求职投递看板</h1>
<div class="sub">数据源：{html.escape(src.name)} · 生成于 {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} · 静态文件，重跑 render_kanban.py 刷新</div>
<div class="kpis">
<div class="kpi">投递总数<b>{total}</b></div>
<div class="kpi">面试中<b>{in_interview}</b></div>
<div class="kpi">Offer<b>{offers}</b></div>
<div class="kpi">Reject<b>{rejects}</b></div>
<div class="kpi">沉默<b>{silent}</b></div>
<div class="kpi">待跟进<b>{pend}</b></div>
</div>
<div class="board">{"".join(cards)}</div>
<div class="warn"><h3>⚠️ 需要你处理的</h3><ul>
{deadline_html or "<li>（暂无 3 天内的 Deadline）</li>"}
</ul><h3 style="margin-top:12px">😴 沉默池（该催或该放弃）</h3><ul>
{stale_html or "<li>（无沉默条目）</li>"}
</ul></div>
<footer>本地 Codex 插件 glm-job-intent-tracker · render_kanban.py（宿主 artifact 的离线等效替换件）</footer>
</body></html>
"""
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"✓ 看板已生成：{out}（{total} 条记录）")
    print(f"  用浏览器打开即可；数据更新后重跑本脚本刷新。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
