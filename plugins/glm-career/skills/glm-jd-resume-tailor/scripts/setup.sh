#!/usr/bin/env bash
# glm-jd-resume-tailor — environment check + CLI contract drills (offline)
# Usage: bash ~/.codex/plugins/glm-career/skills/glm-jd-resume-tailor/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-jd-resume-tailor"
PY="${GLM_JD_RESUME_TAILOR_PYTHON:-python3}"
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
  bad "python interpreter not found (set GLM_JD_RESUME_TAILOR_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/parse_jd.py scripts/jd_gap.py \
         references/jd_parsing_signals.md references/rewrite_principles.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "parse_jd CLI contract (pure stdlib)"
TMPD="$(mktemp -d)"
cat > "$TMPD/jd.txt" <<'EOF'
岗位职责：
- 负责用户增长相关产品规划与迭代，主导 A/B 测试落地
- 搭建数据看板，驱动业务决策
任职要求：
- 本科及以上学历，3-5 年产品经验
- 必须熟悉 SQL 与数据分析，具备跨部门协作能力
- 熟悉增长模型者优先，CET-6 及以上加分
- 接受出差
EOF
if "$PY" "$S/parse_jd.py" --jd-file "$TMPD/jd.txt" --out "$TMPD/jd_parsed.json" >/dev/null 2>&1; then
  if grep -q '"must_have"' "$TMPD/jd_parsed.json" && \
     grep -q '"skills_extracted"' "$TMPD/jd_parsed.json" && \
     grep -q '"special_requirements"' "$TMPD/jd_parsed.json" && \
     grep -q '"nice_to_have"' "$TMPD/jd_parsed.json"; then
    good "jd_parsed.json written with all four buckets"
  else
    bad "jd_parsed.json malformed"
  fi
  if grep -q '"education": "本科' "$TMPD/jd_parsed.json" && \
     grep -q '"years"' "$TMPD/jd_parsed.json" && \
     grep -q '"working_style": "出差"' "$TMPD/jd_parsed.json"; then
    good "special requirements extracted (education/years/travel)"
  else
    bad "special requirements extraction missed"
  fi
else
  bad "parse_jd drill failed"
fi
"$PY" "$S/parse_jd.py" --jd-file "$TMPD/nonexistent.txt" >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 1 ]; then
  good "missing-jd-file drill exit 1 as designed"
else
  bad "expected exit 1 for missing JD file, got $rc"
fi

section "jd_gap CLI contract (md resume, pure stdlib)"
cat > "$TMPD/resume.md" <<'EOF'
# 张三 · 产品经理

字节跳动 | 高级产品经理 | 2022-03 ~ 2026-11

- 主导信息流改版，日活提升 12%
- 用 SQL 做数据分析，搭建数据看板驱动业务决策
- 跨部门协作推动灰度对比实验落地
- 负责增长黑客玩法探索
EOF
if "$PY" "$S/jd_gap.py" --jd "$TMPD/jd_parsed.json" --resume "$TMPD/resume.md" \
     --out "$TMPD/gap.md" >/dev/null 2>&1; then
  if grep -q "Gap 分析报告" "$TMPD/gap.md" && grep -q "完美命中" "$TMPD/gap.md" && \
     grep -q "隐性命中" "$TMPD/gap.md" && grep -q "真缺口" "$TMPD/gap.md" && \
     grep -q "改写建议" "$TMPD/gap.md"; then
    good "gap report rendered (three buckets + rewrite advice)"
  else
    bad "gap report malformed"
  fi
else
  bad "jd_gap drill failed"
fi
printf 'not a pdf\n' > "$TMPD/bad.pdf"
"$PY" "$S/jd_gap.py" --jd "$TMPD/jd_parsed.json" --resume "$TMPD/bad.pdf" >/dev/null 2>&1; rc=$?
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
if grep -rqE "mcp__cowork__create_artifact|AskUserQuestion|z-ai|web-dev-sdk|clawdbot|thesethrose|web_fetch" \
     "$SKILL_DIR/SKILL.md" "$S/parse_jd.py" "$S/jd_gap.py" \
     "$SKILL_DIR/references/jd_parsing_signals.md" \
     "$SKILL_DIR/references/rewrite_principles.md" 2>/dev/null; then
  bad "host tool/SDK residue found"
else
  good "payload free of host tool/SDK references"
fi

section "knowledge anchors"
for anchor in "parse_jd.py" "jd_gap.py" "jd_parsing_signals.md" \
              "rewrite_principles.md" "Codex Deployment Notes" "不编造" \
              "完美命中" "真缺口"; do
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
note "outputs (jd_parsed.json/gap/tailored resume) land in the user working directory; plugin dir read-only."
exit 0
