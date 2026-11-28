#!/usr/bin/env python3
"""校验 major_recommendation.json 的 recommended_majors 与 parsed.json 完全一致（硬性约束）。

用法:
    python3 check_recommendation.py --parsed output/parsed.json \
        --recommendation output/major_recommendation.json

退出码:
    0  全部条目命中 parsed.json（硬性约束满足）
    1  存在 MISMATCH 条目（逐条列出，须回 parsed.json 核对修正）
    2  文件/参数错误
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise RuntimeError(f"无法读取 {path}: {e}") from e
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} 应为 JSON 对象")
    return data


def collect_parsed_keys(parsed: dict[str, Any]) -> tuple[set[tuple], set[tuple]]:
    """返回 (院校键集合, 专业键集合)。键：university_name/university_code(+major_name/major_code)。"""
    school_keys: set[tuple] = set()
    major_keys: set[tuple] = set()
    for school in parsed.get("schools") or []:
        uni_key = (
            str(school.get("university_name") or ""),
            str(school.get("university_code") or ""),
        )
        school_keys.add(uni_key)
        for major in school.get("majors") or []:
            major_keys.add(
                (
                    uni_key[0],
                    uni_key[1],
                    str(major.get("major_name") or ""),
                    str(major.get("major_code") or ""),
                )
            )
    return school_keys, major_keys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="recommended_majors 与 parsed.json 一致性校验（硬性约束）"
    )
    parser.add_argument("--parsed", type=Path, required=True, help="parsed.json 路径")
    parser.add_argument("--recommendation", type=Path, required=True, help="major_recommendation.json 路径")
    parser.add_argument(
        "--min", dest="minimum", type=int, default=8,
        help="recommended_majors 建议下限（默认 8，低于仅提示不阻断）",
    )
    parser.add_argument(
        "--max", dest="maximum", type=int, default=15,
        help="recommended_majors 建议上限（默认 15，超出仅提示不阻断）",
    )
    args = parser.parse_args()

    try:
        parsed = load_json(args.parsed)
        rec = load_json(args.recommendation)
    except RuntimeError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 2

    _, major_keys = collect_parsed_keys(parsed)
    if not major_keys:
        print("错误: parsed.json 中未找到任何专业条目（schools[].majors 为空）", file=sys.stderr)
        return 2

    recommended = rec.get("recommended_majors") or []
    if not recommended:
        print("错误: major_recommendation.json 中 recommended_majors 为空", file=sys.stderr)
        return 1

    ok = 0
    mismatch = 0
    missing_fields = 0
    bad_modal = 0

    print(f"== recommended_majors 一致性校验（parsed.json 含 {len(major_keys)} 个专业条目）==\n")

    for i, item in enumerate(recommended, start=1):
        uni_name = str(item.get("university_name") or "")
        uni_code = str(item.get("university_code") or "")
        major_name = str(item.get("major_name") or "")
        major_code = str(item.get("major_code") or "")
        label = f"[{i}] {uni_name} · {major_name}"

        field_missing = [k for k, v in (
            ("university_name", uni_name),
            ("university_code", uni_code),
            ("major_name", major_name),
            ("major_code", major_code),
        ) if not v]
        if field_missing:
            print(f"  MISMATCH {label} — 缺字段 {field_missing}")
            missing_fields += 1
            mismatch += 1
            continue

        key = (uni_name, uni_code, major_name, major_code)
        if key in major_keys:
            modal = item.get("modal") or {}
            if str(modal.get("title") or "").strip() and str(modal.get("body") or "").strip():
                print(f"  OK       {label}")
                ok += 1
            else:
                print(f"  OK*      {label} — modal.title/body 不完整（报告弹窗内容缺失）")
                ok += 1
                bad_modal += 1
        else:
            print(f"  MISMATCH {label}（code={uni_code}/{major_code}）— 在 parsed.json 中不存在")
            mismatch += 1

    print(f"\n合计: {ok} OK（其中 {bad_modal} 条 modal 不完整）/ {mismatch} MISMATCH / 共 {len(recommended)} 条")

    hints: list[str] = []
    n = len(recommended)
    if n < args.minimum:
        hints.append(f"数量 {n} 低于建议下限 {args.minimum}（覆盖冲/稳/保，优先「稳」档核心专业）")
    if n > args.maximum:
        hints.append(f"数量 {n} 超过建议上限 {args.maximum}")
    for hint in hints:
        print(f"  [warn] {hint}")

    for field in ("intro", "strategy"):
        if not str(rec.get(field) or "").strip():
            print(f"  [warn] {field} 为空——报告综合测评区将缺文案")
    directions = rec.get("major_directions") or []
    if not (2 <= len(directions) <= 4):
        print(f"  [warn] major_directions 当前 {len(directions)} 条，建议 2–4 条")

    if mismatch:
        print(
            "\n校验未通过：MISMATCH 条目的四个字段必须与 parsed.json 完全一致"
            "（回 parsed.json 检索准确值后修正，再重跑本脚本）。",
            file=sys.stderr,
        )
        return 1

    print("\n校验通过：全部推荐专业均来自 parsed.json，可交给 Step4（glm-gaokao-recommend-schools）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
