#!/usr/bin/env bash
# glm-interview-prep — environment check + CLI contract drills (offline)
# Usage: bash ~/.codex/plugins/glm-career/skills/glm-interview-prep/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-interview-prep"
PY="${GLM_INTERVIEW_PREP_PYTHON:-python3}"
S="$SKILL_DIR/scripts"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_INTERVIEW_PREP_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/star_story_builder.py \
         references/answer_frameworks.md references/behavioral.md \
         references/case.md references/hr_round.md \
         references/role_finance.md references/role_internet.md \
         references/role_tech.md references/salary_negotiation.md \
         references/technical.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "star_story_builder CLI contract (md resume, pure stdlib)"
TMPD="$(mktemp -d)"
cat > "$TMPD/resume.md" <<'EOF'
# 李四 · 用户增长 PM

字节跳动 | 用户增长产品经理 | 2021-06 ~ 2026-11

- 主导 0-1 孵化裂变增长玩法，DAU 提升 18%
- 跨部门协调设计与数据团队，推动灰度实验落地
- 复盘一次失败的活动改版，沉淀防坑清单

美团 | 产品运营 | 2019-07 ~ 2021-05

- 负责拉新渠道运营，月获客成本下降 22%
EOF
if "$PY" "$S/star_story_builder.py" --resume "$TMPD/resume.md" \
     --out "$TMPD/stories.md" >/dev/null 2>&1; then
  if grep -q "故事矩阵" "$TMPD/stories.md" && \
     grep -q "STAR 拆解" "$TMPD/stories.md" && \
     grep -q "最适合回答的行为题" "$TMPD/stories.md" && \
     grep -q "## 故事 1：字节跳动" "$TMPD/stories.md"; then
    good "story matrix rendered (STAR skeleton + question mapping)"
  else
    bad "story matrix malformed"
  fi
else
  bad "star_story_builder drill failed"
fi
printf '只有一段普通段落，没有锚点行。\n' > "$TMPD/flat.txt"
if "$PY" "$S/star_story_builder.py" --resume "$TMPD/flat.txt" \
     --out "$TMPD/flat_stories.md" >/dev/null 2>&1; then
  if grep -q "未检测到经历" "$TMPD/flat_stories.md"; then
    good "no-anchor resume hits graceful fallback branch (exit 0)"
  else
    bad "no-anchor fallback text missing"
  fi
else
  bad "no-anchor drill should still exit 0"
fi
printf 'not a pdf\n' > "$TMPD/bad.pdf"
"$PY" "$S/star_story_builder.py" --resume "$TMPD/bad.pdf" >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 1 ]; then
  good "unsupported-format drill exit 1 as designed"
else
  bad "expected exit 1 for .pdf input, got $rc"
fi

section "python-docx availability (optional, .docx resume input)"
if "$PY" -c "import docx" 2>/dev/null; then
  good "python-docx present (.docx resume input fully usable)"
else
  note "python-docx absent — .docx input will exit 1 with install hint (paste/md/txt unaffected)"
fi

section "host-residue self-check"
if grep -rqE "mcp__cowork__create_artifact|AskUserQuestion|z-ai|web-dev-sdk|clawdbot|thesethrose" \
     "$SKILL_DIR/SKILL.md" "$S/star_story_builder.py" \
     "$SKILL_DIR/references/"*.md 2>/dev/null; then
  bad "host tool/SDK residue found"
else
  good "payload free of host tool/SDK references"
fi

section "knowledge anchors"
for anchor in "star_story_builder.py" "behavioral.md" "technical.md" \
              "case.md" "hr_round.md" "role_internet.md" "role_tech.md" \
              "role_finance.md" "answer_frameworks.md" \
              "salary_negotiation.md" "Codex Deployment Notes" \
              "备战手册"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

rm -rf "$TMPD"
printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "outputs (story matrix / prep handbook) land in the user working directory; plugin dir read-only."
exit 0
