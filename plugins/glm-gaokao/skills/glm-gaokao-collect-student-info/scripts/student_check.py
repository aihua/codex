#!/usr/bin/env python3
"""student.json 交付前体检：按省份选科模式校验 API 必填项与字段一致性。

用法:
    python3 student_check.py -i output/student.json

退出码:
    0  体检通过（可有非阻断提示）
    1  发现必改问题（逐条给出修正建议）
    2  文件/参数错误
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ---- 省份选科模式表（与 glm-gaokao-fetch-volunteers 的 province_config.py 同源）----

PROVINCES_REQUIRING_GRADE_TYPE = frozenset({"北京", "上海", "天津"})
UNSUPPORTED_PROVINCES = frozenset({"西藏"})
MODE_33 = frozenset({"上海", "北京", "天津", "山东", "浙江", "海南"})
MODE_312 = frozenset({
    "广东", "江苏", "河北", "湖北", "湖南", "福建", "辽宁", "重庆", "甘肃",
    "黑龙江", "吉林", "安徽", "江西", "贵州", "广西", "云南", "内蒙古",
    "四川", "宁夏", "山西", "河南", "陕西", "青海",
})
MODE_OLD = frozenset({"新疆"})

VALID_CLASSIFY_BY_MODE: dict[str, frozenset[str]] = {
    "33": frozenset({"综合"}),
    "312": frozenset({"物理", "历史"}),
    "老高考": frozenset({"文科", "理科"}),
}
MODE_LABELS: dict[str, str] = {"33": "3+3", "312": "3+1+2", "老高考": "老高考"}

SUBJECTS_312_ELECTIVES = frozenset({"化学", "生物", "政治", "地理"})
SUBJECTS_33_POOL = frozenset({"物理", "历史", "化学", "生物", "政治", "地理"})
SUBJECTS_33_ZHEJIANG = SUBJECTS_33_POOL | frozenset({"技术"})

KNOWN_PROVINCES = MODE_33 | MODE_312 | MODE_OLD | UNSUPPORTED_PROVINCES


def get_province_mode(province: str | None) -> str:
    if not province:
        return "unknown"
    if province in UNSUPPORTED_PROVINCES:
        return "unsupported"
    if province in MODE_OLD:
        return "老高考"
    if province in MODE_33:
        return "33"
    if province in MODE_312:
        return "312"
    return "unknown"


def parse_subjects_list(subjects: Any) -> list[str]:
    if subjects in (None, "", "null", "NULL"):
        return []
    return [s.strip() for s in str(subjects).split(",") if s.strip()]


def check_student(student: dict[str, Any]) -> tuple[list[str], list[str]]:
    """返回 (problems, warnings)。problems 必改；warnings 提示。"""
    problems: list[str] = []
    warnings: list[str] = []

    province = student.get("province")
    classify = student.get("classify")
    subjects = student.get("subjects")
    grade_type = student.get("gradeType")
    score = student.get("score")
    rank = student.get("rank")
    batch = student.get("batch")

    # --- 基础必填 ---
    if not province:
        problems.append("缺少 province（高考省份，API 必填）")
    elif province not in KNOWN_PROVINCES:
        warnings.append(f"province={province!r} 不在 31 省已知名单内，请核对写法（如「内蒙古」非「内蒙」）")

    mode = get_province_mode(province)

    if score is None:
        problems.append("缺少 score（高考成绩整数，API 必填；新疆仅位次无效）")
    elif not isinstance(score, int) or isinstance(score, bool):
        problems.append(f"score 应为整数，当前为 {score!r}（如 650）")

    if province == "新疆" and score is None and rank is not None:
        problems.append("新疆无一分一段表，仅传 rank 无效——必须采集 score")

    if not classify:
        if mode in VALID_CLASSIFY_BY_MODE:
            valid = "/".join(sorted(VALID_CLASSIFY_BY_MODE[mode]))
            problems.append(f"缺少 classify：{province} 为{MODE_LABELS[mode]}模式，应填 {valid}")
        else:
            problems.append("缺少 classify（文科/理科/物理/历史/综合）")
    elif mode in VALID_CLASSIFY_BY_MODE and classify not in VALID_CLASSIFY_BY_MODE[mode]:
        valid = "/".join(sorted(VALID_CLASSIFY_BY_MODE[mode]))
        problems.append(
            f"classify 与省份不匹配：{province} 为{MODE_LABELS[mode]}模式，"
            f"classify 应为 {valid}，当前为 {classify!r}——错误 classify 会导致下游批次接口返回空列表"
        )

    if not batch:
        warnings.append("未填 batch：可留空由下游 batch/list 自动解析，或填考生口中的「本科批」/「专科批」")

    if mode == "unsupported":
        problems.append(
            f"省份 {province}：测试环境不支持志愿/批次接口（平台未接入该省数据），采集时应告知用户"
        )

    # --- subjects 按模式校验 ---
    parts = parse_subjects_list(subjects)
    if mode == "老高考":
        if parts:
            problems.append(f"{province}（老高考）不传 subjects，当前为 {subjects!r}（应为 null）")
    elif mode == "312":
        if not parts:
            problems.append(
                f"缺少 subjects：{province}（3+1+2）需传完整三科，如 物理,化学,生物"
            )
        else:
            if len(parts) != 3:
                problems.append(
                    f"subjects 格式错误：{province}（3+1+2）须传完整三科（首选+两门再选），"
                    f"当前为 {subjects!r}（{len(parts)} 科）——不能只传两门再选"
                )
            if classify in ("物理", "历史") and classify not in parts:
                problems.append(
                    f"subjects 与 classify 不一致：classify={classify!r}，"
                    f"subjects 须包含首选科目 {classify!r}，当前为 {subjects!r}"
                )
            if classify in ("物理", "历史"):
                electives = [p for p in parts if p != classify]
                invalid = [p for p in electives if p not in SUBJECTS_312_ELECTIVES]
                if invalid:
                    problems.append(
                        f"subjects 含无效再选科目 {invalid}：3+1+2 再选仅限化学/生物/政治/地理"
                    )
                if len(electives) != 2:
                    problems.append(
                        f"subjects 格式错误：{province}（3+1+2）除首选外还须两门再选，当前为 {subjects!r}"
                    )
    elif mode == "33":
        if province in PROVINCES_REQUIRING_GRADE_TYPE and grade_type == "专科":
            if parts:
                warnings.append(
                    f"{province}（专科）按下游契约 subjects 传字符串 'null' 即可，当前 {subjects!r} 将由下游规范化处理"
                )
        else:
            if not parts:
                problems.append(
                    f"缺少 subjects：{province}（3+3）需传完整三科，如 物理,化学,生物"
                )
            elif len(parts) != 3:
                problems.append(
                    f"subjects 格式错误：{province}（3+3）须传完整三科，当前为 {subjects!r}（{len(parts)} 科）"
                )
            else:
                pool = SUBJECTS_33_ZHEJIANG if province == "浙江" else SUBJECTS_33_POOL
                invalid = [p for p in parts if p not in pool]
                if invalid:
                    hint = "（浙江可选「技术」）" if province == "浙江" else ""
                    problems.append(
                        f"subjects 含无效科目 {invalid}：{province} 选考范围见模式表{hint}"
                    )

    # --- gradeType ---
    if grade_type is not None:
        if province not in PROVINCES_REQUIRING_GRADE_TYPE:
            problems.append(
                f"gradeType 仅北京/上海/天津可填（本科/专科），{province} 应为 null / 不传——"
                f"误传会导致下游志愿接口 500"
            )
        elif grade_type not in ("本科", "专科"):
            problems.append(f"gradeType 取值应为 本科 / 专科，当前为 {grade_type!r}")
    elif province in PROVINCES_REQUIRING_GRADE_TYPE:
        warnings.append(
            f"{province} 未填 gradeType：下游脚本会按分数/批次推断（score≤450→专科），建议采集时问清本科还是专科"
        )

    # --- 辅助画像字段 ---
    text_fields = ("interests", "family_situation", "career_direction")
    missing_text = [f for f in text_fields if not str(student.get(f) or "").strip()]
    if missing_text:
        warnings.append(
            f"辅助画像字段为空：{missing_text}——下游专业/院校推荐依赖这些原话，建议逐项询问补齐"
        )

    for key in ("preferred_cities", "preferred_provinces", "preferred_universities",
                "preferred_tags", "preferred_major_classes"):
        value = student.get(key)
        if value is not None and not isinstance(value, list):
            problems.append(f"{key} 应为数组（如 [\"北京\", \"上海\"]），当前为 {value!r}")

    notes = str(student.get("notes") or "").strip()
    exclusion_hints = ("不要", "不接受", "排除", "别去", "不想去")
    in_province_field = any(
        h in str(student.get("preferred_provinces") or "")
        for h in exclusion_hints
    )
    if in_province_field:
        problems.append(
            "preferred_provinces 中疑似混入排斥性表述——排斥偏好应写 notes 原话，preferred_* 只放正向意向"
        )
    if not notes:
        warnings.append("notes 为空：考生禁忌/特殊诉求（如不接受偏远地区）用原话记录在 notes")

    return problems, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="student.json 按省份模式体检")
    parser.add_argument("-i", "--input", type=Path, required=True, help="student.json 路径")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"错误: 文件不存在 {args.input}", file=sys.stderr)
        return 2
    try:
        student = json.loads(args.input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 — {e}", file=sys.stderr)
        return 2
    if not isinstance(student, dict):
        print("错误: student.json 应为 JSON 对象", file=sys.stderr)
        return 2

    problems, warnings = check_student(student)

    province = student.get("province") or "?"
    mode = get_province_mode(province)
    mode_label = MODE_LABELS.get(mode, "未知模式")
    print(f"== student.json 体检（{province} / {mode_label}）==")

    if warnings:
        print("\n-- 提示（非阻断）--")
        for w in warnings:
            print(f"  [warn] {w}")

    if problems:
        print("\n-- 问题（必改）--")
        for p in problems:
            print(f"  [fix] {p}")
        print(f"\n体检未通过：{len(problems)} 个必改问题；修正后重跑本脚本。", file=sys.stderr)
        return 1

    print("\n体检通过：classify/subjects/gradeType 与省份模式一致，API 必填项齐全。")
    print("可将 output/student.json 交给 Step2（glm-gaokao-fetch-volunteers）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
