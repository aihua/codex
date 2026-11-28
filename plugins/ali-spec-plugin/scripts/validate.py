#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ali-spec-plugin 结构校验脚本（六项检查，设计方案 8.1）。

用法：在插件根目录执行 `python3 scripts/validate.py`。
六项全部通过退出码 0；任一失败退出码 1 并逐条列出原因。

检查项：
  1 frontmatter   每个 SKILL.md 的 YAML 可解析；name 与目录名一致；description 非空且 20～500 字符
  2 结构          SKILL.md 导航表中引用的 references 文件全部存在；反向扫描未被引用的文件并告警
  3 覆盖度        等级标记计数等于源基准（SQL 21/12/4，Java 107/52/24）；前端技能规则条目数比对源文档基准
  4 残留          自撰文件（SKILL.md/README/AGENTS/清单）无 TODO/XXX/待补充/undefined/NaN/FIXME；
                  references 中仅允许白名单内的源文档原文令牌（「占位符」为手册日志规约术语，单独管控）
  5 清单          双清单合法：根 plugin.json 可解析且顶层字段全部在 Agent Plugins 十项白名单内；
                  .codex-plugin/plugin.json 的 name/version/skills 齐全且指向有效目录；两清单 name/version 一致
  6 共享参考      shared-references/ 两文件存在且被 SKILL.md 引用；common.md 恰被 18 个前端侧技能引用
                  （Java/SQL 四技能零引用）；http-json-api.md 被 22 个技能全部引用
"""
import json
import os
import re
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(PLUGIN, "skills")

SPEC_SKILLS = ["ali-sql-spec", "ali-java-spec", "ali-javascript-spec", "ali-typescript-spec",
               "ali-reactjs-spec", "ali-nodejs-spec", "ali-css-spec", "ali-html-spec",
               "ali-git-spec", "ali-markdown-spec", "ali-changelog-spec"]
REVIEW_SKILLS = [s.replace("-spec", "").replace("ali-", "ali-review-") for s in SPEC_SKILLS]
ALL_SKILLS = SPEC_SKILLS + REVIEW_SKILLS

# 覆盖度基准（源文档实测，构建期锁定）
MARKER_BASELINE = {  # 【强制】【推荐】【参考】标记计数
    "ali-sql-spec": {"强制": 21, "推荐": 12, "参考": 4},
    "ali-java-spec": {"强制": 107, "推荐": 52, "参考": 24},
}
RULEHEADING_BASELINE = {  # ### 规则标题计数（可引用规则条数）
    "ali-sql-spec": 37,
    "ali-java-spec": 182,   # 182 条规则 + 控制-3 说明行内 1 处强调 = 183 个等级标记（见 README）
}
FRONTEND_RULES_BASELINE = {  # references 内规则条目计数（- x.y.z `等级` / - `等级` / html 双形态）
    "ali-javascript-spec": 112, "ali-typescript-spec": 27, "ali-reactjs-spec": 68,
    "ali-nodejs-spec": 21, "ali-css-spec": 31, "ali-html-spec": 22,
    "ali-git-spec": 0, "ali-markdown-spec": 12, "ali-changelog-spec": 10,
}
# 残留白名单：references 中允许出现的源文档原文令牌（文件 → 令牌 → 次数上限）。
# 均为源文档自身内容：Javadoc TODO/FIXME 标签说明、JS 注释规约的 TODO/FIXME 示例、
# f2e 原文「作者署名」节、手册日志规约「占位符」术语。
RESIDUAL_ALLOWLIST = {
    "TODO": {
        "skills/ali-java-spec/references/08-注释规约.md": 1,
        "skills/ali-javascript-spec/references/05-注释.md": 3,
        "skills/ali-javascript-spec/references/01-编码风格.md": 1,
        "skills/ali-html-spec/references/03-模板语言.md": 1,
    },
    "FIXME": {
        "skills/ali-java-spec/references/08-注释规约.md": 2,
        "skills/ali-javascript-spec/references/05-注释.md": 3,
    },
    "占位符": {
        "skills/ali-java-spec/references/11-日志规约.md": 3,
    },
}
# 仅允许出现在 JS/TS/React/Node 四技能 references 的语言术语
JS_TERM_PATTERNS = {"undefined", "NaN"}
JS_SKILLS = {"ali-javascript-spec", "ali-typescript-spec", "ali-reactjs-spec", "ali-nodejs-spec"}
AGENT_FIELDS_WHITELIST = {"$schema", "name", "version", "description", "author",
                          "homepage", "repository", "license", "keywords", "extensions"}

RULE_ITEM_RE = re.compile(r"^\s*-\s+([\d.]+)?\s*`(强制|推荐|参考)`")
GRADE_LINE_RE = re.compile(r"^等级[：:]\s*\*\*(强制|推荐|参考)\*\*\s*$")
SECT_NUM_RE = re.compile(r"^###\s+[\d.]")
# 自撰文件严格扫描的令牌（「占位符」除外：规约原文自身使用该术语，如手册日志规约第 4 条）
RESIDUAL_PATTERNS = ["TODO", "XXX", "待补充", "undefined", "NaN", "FIXME"]
RESIDUAL_PATTERNS_REFS = RESIDUAL_PATTERNS + ["占位符"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def ref_files(skill):
    d = os.path.join(SKILLS, skill, "references")
    if not os.path.isdir(d):
        return []
    return sorted(os.listdir(d))


def check_1_frontmatter(errors):
    for skill in ALL_SKILLS:
        path = os.path.join(SKILLS, skill, "SKILL.md")
        if not os.path.isfile(path):
            errors.append(f"[1] 缺少 {skill}/SKILL.md")
            continue
        text = read(path)
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            errors.append(f"[1] {skill}/SKILL.md frontmatter 块缺失或不可解析")
            continue
        fm, fields = m.group(1), {}
        for ln in fm.split("\n"):
            if ":" in ln:
                k, v = ln.split(":", 1)
                fields[k.strip()] = v.strip()
        if fields.get("name") != skill:
            errors.append(f"[1] {skill}/SKILL.md name={fields.get('name')!r} 与目录名不一致")
        desc = fields.get("description", "")
        if not (20 <= len(desc) <= 500):
            errors.append(f"[1] {skill}/SKILL.md description 长度 {len(desc)} 不在 20～500 区间")


def extract_path_tokens(text):
    """从 Markdown 表格单元格与行内提取路径令牌：以 .md 结尾且含 / 的单元格。"""
    tokens = set()
    for ln in text.split("\n"):
        for cell in ln.split("|"):
            c = cell.strip().strip("`")
            if c.endswith(".md") and ("/" in c) and (" " not in c) and not c.startswith("http"):
                tokens.add(c)
    return tokens


def check_2_structure(errors, warnings):
    for skill in ALL_SKILLS:
        base = os.path.join(SKILLS, skill)
        text = read(os.path.join(base, "SKILL.md"))
        for tok in extract_path_tokens(text):
            p = os.path.normpath(os.path.join(base, tok))
            if not os.path.isfile(p):
                errors.append(f"[2] {skill}/SKILL.md 引用的 {tok} 不存在（解析为 {p}）")
        for fn in ref_files(skill):
            if fn not in text:
                warnings.append(f"[2] {skill}/references/{fn} 未在 SKILL.md 中被引用")


def check_3_coverage(errors):
    for skill, base in MARKER_BASELINE.items():
        counts = {"强制": 0, "推荐": 0, "参考": 0}
        for fn in ref_files(skill):
            t = read(os.path.join(SKILLS, skill, "references", fn))
            for g in counts:
                counts[g] += t.count(f"【{g}】")
        if counts != base:
            errors.append(f"[3] {skill} 等级标记计数 {counts} != 源基准 {base}")
    for skill, base in RULEHEADING_BASELINE.items():
        n = 0
        for fn in ref_files(skill):
            n += sum(1 for ln in read(os.path.join(SKILLS, skill, "references", fn)).split("\n")
                     if ln.startswith("### ") and re.match(r"^### [\u4e00-\u9fffA-Za-z]+-\d", ln))
        if n != base:
            errors.append(f"[3] {skill} 规则标题数 {n} != 基准 {base}")
    for skill, base in FRONTEND_RULES_BASELINE.items():
        n = 0
        for fn in ref_files(skill):
            lines = read(os.path.join(SKILLS, skill, "references", fn)).split("\n")
            for i, ln in enumerate(lines):
                if RULE_ITEM_RE.match(ln):
                    n += 1
                elif (not SECT_NUM_RE.match(ln)) and ln.startswith("### "):
                    for j in range(1, 4):
                        if i + j < len(lines) and GRADE_LINE_RE.match(lines[i + j]):
                            n += 1
                            break
        if n != base:
            errors.append(f"[3] {skill} 规则条目数 {n} != 源基准 {base}")
    for skill in REVIEW_SKILLS:
        if ref_files(skill):
            errors.append(f"[3] {skill} 不应有自己的 references（规则单一事实源），发现 {ref_files(skill)}")


def check_4_residual(errors):
    authored = [os.path.join(SKILLS, s, "SKILL.md") for s in ALL_SKILLS]
    authored += [os.path.join(PLUGIN, f) for f in ("README.md", "templates/AGENTS.md")]
    for p in authored:
        if not os.path.isfile(p):
            continue
        t = read(p)
        for pat in RESIDUAL_PATTERNS:
            if pat in t:
                errors.append(f"[4] 自撰文件 {os.path.relpath(p, PLUGIN)} 含残留占位 {pat!r}")
    for skill in SPEC_SKILLS:
        for fn in ref_files(skill):
            rel = f"skills/{skill}/references/{fn}"
            t = read(os.path.join(SKILLS, skill, "references", fn))
            for pat in RESIDUAL_PATTERNS_REFS:
                c = t.count(pat)
                if c == 0:
                    continue
                if pat in JS_TERM_PATTERNS:
                    if skill not in JS_SKILLS:
                        errors.append(f"[4] {rel} 出现非白名单令牌 {pat!r} ×{c}")
                elif pat in RESIDUAL_ALLOWLIST:
                    allow = RESIDUAL_ALLOWLIST[pat].get(rel, 0)
                    if c > allow:
                        errors.append(f"[4] {rel} 令牌 {pat!r} ×{c} 超出白名单上限 {allow}")
                else:
                    errors.append(f"[4] {rel} 出现残留占位 {pat!r} ×{c}")


def check_5_manifests(errors):
    root_p = os.path.join(PLUGIN, "plugin.json")
    codex_p = os.path.join(PLUGIN, ".codex-plugin", "plugin.json")
    if not os.path.isfile(root_p):
        errors.append("[5] 根 plugin.json 缺失")
        return
    if not os.path.isfile(codex_p):
        errors.append("[5] .codex-plugin/plugin.json 缺失")
        return
    try:
        root = json.loads(read(root_p))
    except Exception as e:
        errors.append(f"[5] 根 plugin.json 不可解析: {e}")
        return
    try:
        codex = json.loads(read(codex_p))
    except Exception as e:
        errors.append(f"[5] .codex-plugin/plugin.json 不可解析: {e}")
        return
    extra = set(root.keys()) - AGENT_FIELDS_WHITELIST
    if extra:
        errors.append(f"[5] 根 plugin.json 顶层字段超出 Agent Plugins 十项白名单: {sorted(extra)}")
    if "$schema" not in root or "name" not in root:
        errors.append("[5] 根 plugin.json 缺少必填字段 $schema / name")
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", root.get("name", "")):
        errors.append("[5] 根 plugin.json name 不符合 kebab-case")
    for k in ("name", "version", "skills"):
        if k not in codex:
            errors.append(f"[5] .codex-plugin/plugin.json 缺少字段 {k}")
    if not os.path.isdir(os.path.normpath(os.path.join(PLUGIN, codex.get("skills", "")))):
        errors.append("[5] .codex-plugin/plugin.json skills 指向的目录无效（应相对插件根，如 ./skills/）")
    if (root.get("name"), root.get("version")) != (codex.get("name"), codex.get("version")):
        errors.append("[5] 双清单 name/version 不一致")


def check_6_shared(errors):
    for fn in ("common.md", "http-json-api.md"):
        if not os.path.isfile(os.path.join(PLUGIN, "shared-references", fn)):
            errors.append(f"[6] shared-references/{fn} 缺失")
    frontend_stacks = {"javascript", "typescript", "reactjs", "nodejs", "css", "html", "git", "markdown", "changelog"}
    frontend, java_side = set(), set()
    for skill in ALL_SKILLS:
        core = skill.replace("ali-review-", "").replace("ali-", "").replace("-spec", "")
        (frontend if core in frontend_stacks else java_side).add(skill)
    common_refs, http_refs = set(), set()
    for skill in ALL_SKILLS:
        t = read(os.path.join(SKILLS, skill, "SKILL.md"))
        if "shared-references/common.md" in t:
            common_refs.add(skill)
        if "shared-references/http-json-api.md" in t:
            http_refs.add(skill)
    if common_refs != frontend or len(frontend) != 18:
        errors.append(f"[6] common.md 引用面 {len(common_refs)} 个 != 前端侧 18 个；"
                      f"多引: {sorted(common_refs - frontend)}，少引: {sorted(frontend - common_refs)}")
    if java_side & common_refs:
        errors.append(f"[6] Java/SQL 侧技能不应引用 common.md: {sorted(java_side & common_refs)}")
    if http_refs != set(ALL_SKILLS):
        errors.append(f"[6] http-json-api.md 未被全部 22 个技能引用；缺: {sorted(set(ALL_SKILLS) - http_refs)}")


def main():
    errors, warnings = [], []
    check_1_frontmatter(errors)
    check_2_structure(errors, warnings)
    check_3_coverage(errors)
    check_4_residual(errors)
    check_5_manifests(errors)
    check_6_shared(errors)

    n_refs = sum(len(ref_files(s)) for s in SPEC_SKILLS)
    print("ali-spec-plugin 校验报告")
    print(f"  技能 22 个（规约 11 + 评审 11），references 文件 {n_refs} 个，共享参考 2 个")
    print()
    items = ["1 frontmatter（name/目录一致、description 20～500 字符）",
             "2 结构（SKILL.md 引用文件全部存在；反向未引用告警）",
             "3 覆盖度（等级标记与规则条目数等于源基准）",
             "4 残留（自撰文件零容忍；references 白名单管控）",
             "5 清单（双清单合法、字段白名单、name/version 一致）",
             "6 共享参考（common 18 / http-json-api 22，Java/SQL 零引用）"]
    for i, name in enumerate(items, 1):
        tag = "FAIL" if any(e.startswith(f"[{i}]") for e in errors) else "PASS"
        print(f"  [{tag}] 检查 {name}")
    if warnings:
        print()
        for w in warnings:
            print(f"  警告: {w}")
    if errors:
        print()
        for e in errors:
            print(f"  错误: {e}")
        print()
        print(f"校验结果：失败（{len(errors)} 项错误，{len(warnings)} 项警告）")
        sys.exit(1)
    print()
    print("校验结果：六项检查全部通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
