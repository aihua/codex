#!/usr/bin/env python3
"""Cheatsheet 双栏小字 PDF 渲染（宿主 PDF skill Report 路线的本地等效）。

唯一第三方依赖 reportlab，推荐免安装直跑：
    uv run --with reportlab python3 render_cheatsheet.py -i content.md -o 知识浓缩卡_xxx.pdf
或一次性安装：pip install reportlab / uv pip install --system reportlab。

CJK 零字体文件：内置 Adobe CID 字体 STSong-Light（reportlab 注册即用，无需
安装任何中文 TTF/TTC）；拉丁字符同字体回退渲染，标题用字号/底色强调（<b> 映射
到同族，避免混字族 CJK 缺字）。

输入：LLM 提炼后的 Markdown（## 分组 / - 要点 / **加粗** / # 主题 / Q&A 行）。
排版规格（默认，可调）：A4、双栏、正文 8pt、栏距 6mm、页边距 12mm、行距 1.2。

用法:
    python3 render_cheatsheet.py -i content.md -o output.pdf \
        [--single-column] [--font-size 8] [--margin 12]

退出码:
    0 成功（stderr 报告页数/大小）
    1 渲染失败
    2 reportlab 缺失（stderr 给出 uv/pip 两条安装命令）或参数错误
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer
except ImportError:
    print(
        "错误: render_cheatsheet.py 需要 reportlab（本插件唯一第三方依赖），当前解释器未安装。\n"
        "免安装直跑（推荐，uv 在 PATH 时）：\n"
        "  uv run --with reportlab python3 <本脚本路径> -i content.md -o out.pdf\n"
        "或一次性安装：\n"
        "  pip install reportlab\n"
        "  uv pip install --system reportlab",
        file=sys.stderr,
    )
    raise SystemExit(2)

CJK_FONT = "STSong-Light"

INLINE_PATTERNS = [
    (re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>"),
    (re.compile(r"`([^`]+)`"), r"\1"),
]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_markup(text: str) -> str:
    for pattern, repl in INLINE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def build_styles(font_size: float) -> dict[str, ParagraphStyle]:
    body = ParagraphStyle(
        "body", fontName=CJK_FONT, fontSize=font_size,
        leading=font_size * 1.2, spaceAfter=font_size * 0.45,
        textColor=colors.HexColor("#1a1a1a"),
    )
    bullet = ParagraphStyle(
        "bullet", parent=body, leftIndent=font_size * 1.1,
        bulletIndent=font_size * 0.2, spaceAfter=font_size * 0.3,
    )
    h1 = ParagraphStyle(
        "h1", fontName=CJK_FONT, fontSize=font_size + 6, leading=(font_size + 6) * 1.25,
        alignment=1, spaceAfter=font_size, spaceBefore=font_size * 0.4,
        textColor=colors.HexColor("#0f172a"),
    )
    h2 = ParagraphStyle(
        "h2", fontName=CJK_FONT, fontSize=font_size + 2, leading=(font_size + 2) * 1.25,
        spaceBefore=font_size * 1.2, spaceAfter=font_size * 0.5,
        backColor=colors.HexColor("#e8eef7"), borderPadding=(2, 4, 2),
        textColor=colors.HexColor("#12325b"),
    )
    h3 = ParagraphStyle(
        "h3", fontName=CJK_FONT, fontSize=font_size + 1, leading=(font_size + 1) * 1.2,
        spaceBefore=font_size * 0.8, spaceAfter=font_size * 0.3,
        textColor=colors.HexColor("#2c4a7c"),
    )
    qa = ParagraphStyle("qa", parent=body, spaceBefore=font_size * 0.5)
    return {"body": body, "bullet": bullet, "h1": h1, "h2": h2, "h3": h3, "qa": qa}


def parse_markdown(text: str, styles: dict[str, ParagraphStyle]) -> list:
    """极简 Markdown → flowables（## / ### / - / > / **bold** / Q&A 行）。"""
    story: list = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("# ") and not line.startswith("## "):
            story.append(Paragraph(inline_markup(_escape(line[2:].strip())), styles["h1"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline_markup(_escape(line[3:].strip())), styles["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline_markup(_escape(line[4:].strip())), styles["h3"]))
        elif re.match(r"^\s*[-*]\s+", line):
            content = re.sub(r"^\s*[-*]\s+", "", line)
            story.append(Paragraph(
                inline_markup(_escape(content)), styles["bullet"],
                bulletText="•",
            ))
        elif line.startswith("> "):
            story.append(Paragraph(
                inline_markup(_escape(line[2:].strip())), styles["body"],
            ))
        else:
            style = styles["qa"] if line.lstrip().startswith("Q") else styles["body"]
            story.append(Paragraph(inline_markup(_escape(line)), style))
    if story:
        story.append(Spacer(1, 1))
    return story


def render(
    md_path: Path, pdf_path: Path, *, single_column: bool,
    font_size: float, margin_mm: float,
) -> tuple[int, int]:
    pdfmetrics.registerFont(UnicodeCIDFont(CJK_FONT))
    # <b> 映射到同族 CJK 字体：混字族 Helvetica-Bold 不含 CJK 字形会出方块，
    # 这里以字号/底色承担强调，粗体标记安全通过。
    pdfmetrics.registerFontFamily(CJK_FONT, normal=CJK_FONT, bold=CJK_FONT,
                                 italic=CJK_FONT, boldItalic=CJK_FONT)

    styles = build_styles(font_size)
    story = parse_markdown(md_path.read_text(encoding="utf-8"), styles)
    if not story:
        raise ValueError("输入 Markdown 无可渲染内容")

    page_w, page_h = A4
    margin = margin_mm * mm
    gutter = 6 * mm
    pages: list[int] = []

    def on_page(_canvas, doc) -> None:
        pages.append(doc.page)

    if single_column:
        usable_w = page_w - margin * 2
        frames = [Frame(margin, margin, usable_w, page_h - margin * 2,
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]
    else:
        col_w = (page_w - margin * 2 - gutter) / 2
        frames = [
            Frame(margin, margin, col_w, page_h - margin * 2,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
            Frame(margin + col_w + gutter, margin, col_w, page_h - margin * 2,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        ]

    doc = BaseDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin,
        title=Path(pdf_path).stem,
    )
    doc.addPageTemplates([PageTemplate(id="cols", frames=frames, onPage=on_page)])
    doc.build(story)
    return len(pages), doc.page


def main() -> int:
    parser = argparse.ArgumentParser(description="Cheatsheet 双栏小字 PDF 渲染")
    parser.add_argument("-i", "--input", type=Path, required=True, help="LLM 提炼后的 Markdown 文件")
    parser.add_argument("-o", "--output", type=Path, required=True, help="PDF 输出路径")
    parser.add_argument("--single-column", action="store_true", help="单栏（默认双栏）")
    parser.add_argument("--font-size", type=float, default=8.0, help="正文字号 pt（默认 8）")
    parser.add_argument("--margin", type=float, default=12.0, help="页边距 mm（默认 12）")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"错误: 输入文件不存在 {args.input}", file=sys.stderr)
        return 2

    pdf_path = args.output
    if not str(pdf_path).lower().endswith(".pdf"):
        pdf_path = pdf_path.with_suffix(".pdf")

    try:
        page_count, _ = render(
            args.input, pdf_path,
            single_column=args.single_column,
            font_size=args.font_size, margin_mm=args.margin,
        )
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"错误: 渲染失败 — {e}", file=sys.stderr)
        return 1

    size = pdf_path.stat().st_size
    print(f"已生成 PDF: {pdf_path}（{page_count} 页，{size / 1024:.1f} KB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
