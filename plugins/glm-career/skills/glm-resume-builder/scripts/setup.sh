#!/usr/bin/env bash
# glm-resume-builder — environment check (offline, pure-stdlib ATS engine)
# Usage: bash ~/.codex/plugins/glm-career/skills/glm-resume-builder/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-resume-builder"
PY="${GLM_RESUMEBUILDER_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_RESUMEBUILDER_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/ats_check.py \
         references/export_guide.md references/intake_questions.md references/star_rewrite_guide.md \
         references/templates/internet.md references/templates/tech.md \
         references/templates/finance.md references/templates/general.md \
         references/keywords/internet.txt references/keywords/tech.txt \
         references/keywords/finance.txt references/keywords/general.txt; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "engine self-test (no args -> argparse exit 2)"
out="$("$PY" "$SKILL_DIR/scripts/ats_check.py" 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "usage self-test exit 2 as designed (argparse missing-arg contract)"
else
  bad "expected exit 2 without args, got $rc"
fi

section "engine self-test (missing resume file -> exit 1)"
out="$("$PY" "$SKILL_DIR/scripts/ats_check.py" --resume /nonexistent/resume.md --industry internet 2>&1)"; rc=$?
if [ "$rc" -eq 1 ]; then
  good "missing-file self-test exit 1 as designed"
else
  bad "expected exit 1 for missing file, got $rc"
fi

section "engine drill (synthetic .md resume -> exit 0 + report)"
tmpdir="$(mktemp -d)"
cat > "$tmpdir/resume.md" <<'EOF'
# 张三 · 高级产品经理

邮箱 zhangsan@example.com，电话 13812345678

## 工作经历

### 某互联网公司 · 高级产品经理（2022.03 至今）
- 主导 C 端 App 会员体系重构，付费转化率提升 18%，月流水增加 300 万
- 搭建 A/B 实验平台，实验迭代周期从 2 周缩短到 3 天

### 某科技公司 · 产品经理（2019.06 - 2022.02）
- 负责搜索结果页改版，点击率提升 9%
EOF
out="$("$PY" "$SKILL_DIR/scripts/ats_check.py" --resume "$tmpdir/resume.md" --industry internet 2>&1)"; rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q "简历 ATS 检查报告" && printf '%s' "$out" | grep -q "ATS 友好度评分"; then
  good "engine drill exit 0 with coverage + friendliness report"
else
  bad "engine drill failed (rc=$rc)"
fi

section "engine drill (--out report file)"
out="$("$PY" "$SKILL_DIR/scripts/ats_check.py" --resume "$tmpdir/resume.md" --industry tech --out "$tmpdir/report.md" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ] && [ -s "$tmpdir/report.md" ]; then
  good "report file written and non-empty"
else
  bad "--out drill failed (rc=$rc)"
fi
rm -rf "$tmpdir"

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "optional deps (only for .docx input / pdf export): python-docx via 'uv run --with python-docx', poppler pdftotext, LibreOffice, exiftool"
exit 0
