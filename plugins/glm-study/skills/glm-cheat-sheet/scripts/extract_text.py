#!/usr/bin/env python3
"""学习资料文本提取（宿主 PDF skill 提取路线的本地等效，零 pip 依赖优先）。

支持：
- .md / .txt：直接读取（零依赖）
- .docx：纯标准库（zipfile + word/document.xml）提取段落文本
- .pdf：优先 pdftotext（poppler，brew install poppler）；否则尝试 pypdf
  （python -c "import pypdf" 可用时）；两者皆缺则 exit 2 给出安装指引
  （uv run --with pypdf 免安装直跑本脚本）。

用法:
    python3 extract_text.py <input.md|txt|docx|pdf> [-o out.txt]

退出码:
    0 成功（文本写 -o 或 stdout）
    1 提取失败（空内容/解析错误）
    2 工具缺失/参数错误
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def extract_plain(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text


def extract_docx(path: Path) -> str:
    """纯标准库 docx 文本提取：word/document.xml 的 w:t 串 + 段落换行。"""
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="replace")
    paragraphs = re.split(r"</w:p>", xml)
    lines: list[str] = []
    for para in paragraphs:
        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, flags=re.S)
        line = "".join(texts)
        line = (line.replace("&amp;", "&").replace("&lt;", "<")
                    .replace("&gt;", ">").replace("&quot;", '"')
                    .replace("&apos;", "'"))
        lines.append(line.strip())
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def extract_pdf(path: Path) -> tuple[str, str]:
    """返回 (text, note)。优先 pdftotext，其次 pypdf。"""
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        proc = subprocess.run(
            [pdftotext, "-layout", "-enc", "UTF-8", str(path), "-"],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout, "pdftotext (poppler)"
    try:
        import pypdf  # noqa: F401
    except ImportError:
        pass
    else:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(parts)
        if text.strip():
            return text, "pypdf"
    if pdftotext:
        return "", "pdftotext 运行失败（文件可能加密/扫描件，需要 OCR）"
    return "", (
        "PDF 提取工具缺失：brew install poppler（pdftotext），或用"
        " uv run --with pypdf python3 <本脚本> <input.pdf> 免安装直跑"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="学习资料文本提取（md/txt/docx/pdf）")
    parser.add_argument("input", type=Path, help="输入文件 (.md/.txt/.docx/.pdf)")
    parser.add_argument("-o", "--output", type=Path, help="可选：输出文本文件（默认 stdout）")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"错误: 输入文件不存在 {args.input}", file=sys.stderr)
        return 2

    suffix = args.input.suffix.lower()
    note = ""
    if suffix in (".md", ".markdown", ".txt", ".text"):
        text = extract_plain(args.input)
        note = "直读"
    elif suffix == ".docx":
        try:
            text = extract_docx(args.input)
            note = "zipfile 标准库"
        except (zipfile.BadZipFile, KeyError) as e:
            print(f"错误: docx 解析失败 — {e}", file=sys.stderr)
            return 1
    elif suffix == ".pdf":
        text, note = extract_pdf(args.input)
        if not text.strip():
            print(f"错误: {note}", file=sys.stderr)
            return 2
    else:
        print(f"错误: 不支持的格式 {suffix}（支持 .md/.txt/.docx/.pdf）", file=sys.stderr)
        return 2

    if not text.strip():
        print("错误: 提取到空文本（原件可能是扫描件/空文件）", file=sys.stderr)
        return 1

    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"已提取 {len(text)} 字符 → {args.output}（{note}）", file=sys.stderr)
    else:
        sys.stdout.write(text)
        print(f"[info] 提取方式：{note}，共 {len(text)} 字符", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
