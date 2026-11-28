#!/usr/bin/env python3
"""PyYAML 极简等效 shim（纯标准库）。

本插件的 config.yaml 仅用到浅层嵌套映射（aminer.token / aminer.rec5_url /
search.top_k 等标量项），因此提供 safe_load / safe_dump 的受限子集实现：
- 支持：两层以内缩进映射、标量（str/int/float/bool/None）、行内注释、空文件
- 不支持：列表、锚点、多文档、流式语法（config 用不到）

优先使用真正的 PyYAML（已安装时）；仅在 import 失败时由调用方退回本 shim。
"""

from __future__ import annotations

from typing import Any

_SCALARS = {
    "null": None, "Null": None, "~": None, "": None,
    "true": True, "True": True, "false": False, "False": False,
}


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        if len(text) >= 2:
            return text[1:-1]
    if text in _SCALARS:
        return _SCALARS[text]
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _strip_comment(line: str) -> str:
    out = []
    quote = None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def safe_load(text: str | None) -> dict[str, Any]:
    """解析受限 YAML 子集（嵌套映射 + 标量），返回 dict。"""
    if not text:
        return {}
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = _strip_comment(raw_line)
        if not line.strip() or line.strip() in ("---", "..."):
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if ":" not in content:
            continue
        key, _, value = content.partition(":")
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack.append((-1, root))
        parent = stack[-1][1]
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)
    return root


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if any(ch in text for ch in ":#'\"\\\n") or text != text.strip() or not text:
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def safe_dump(data: dict[str, Any], allow_unicode: bool = True, sort_keys: bool = True) -> str:
    """把浅层嵌套映射 dump 为受限 YAML 子集文本。"""
    del allow_unicode  # 输出恒为 UTF-8，参数仅为签名兼容
    lines: list[str] = []
    keys = sorted(data.keys()) if sort_keys else list(data.keys())
    for key in keys:
        value = data[key]
        key_text = _dump_scalar(key)
        if isinstance(value, dict):
            if not value:
                lines.append(f"{key_text}: {{}}")
                continue
            lines.append(f"{key_text}:")
            sub_keys = sorted(value.keys()) if sort_keys else list(value.keys())
            for sub_key in sub_keys:
                sub_value = value[sub_key]
                if isinstance(sub_value, dict):
                    lines.append(f"  {key_text} {sub_key}: <nested>")  # 不支持更深；占位防崩
                else:
                    lines.append(f"  {sub_key}: {_dump_scalar(sub_value)}")
        else:
            lines.append(f"{key_text}: {_dump_scalar(value)}")
    return "\n".join(lines) + "\n" if lines else "{}\n"
