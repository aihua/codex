#!/usr/bin/env bash
# glm-job-intent-tracker — environment check + CLI contract drills (offline)
# Usage: bash ~/.codex/plugins/glm-career/skills/glm-job-intent-tracker/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-job-intent-tracker"
PY="${GLM_JOB_INTENT_TRACKER_PYTHON:-python3}"
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
  bad "python interpreter not found (set GLM_JOB_INTENT_TRACKER_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/init_tracker.py \
         scripts/profile_match.py scripts/render_kanban.py \
         references/keywords_internet.md references/keywords_tech.md \
         references/keywords_finance.md references/keywords_general.md \
         references/target_profile_template.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "init_tracker CLI contract (md mode, pure stdlib)"
TMPD="$(mktemp -d)"
if "$PY" "$S/init_tracker.py" --format md --output "$TMPD/tracker.md" >/dev/null 2>&1; then
  if grep -q "投递追踪表" "$TMPD/tracker.md" && [ "$(grep -c '^|' "$TMPD/tracker.md")" -ge 2 ]; then
    good "md tracker generated with table header"
  else
    bad "md tracker malformed"
  fi
else
  bad "init_tracker md mode failed"
fi

section "render_kanban CLI contract"
printf '%s\n' "| 测试公司 | 高级产品经理 | 内推 | https://example.com/jd/9 | 2026-11-01 | 二面 | 准备面试 | 2026-11-25 | 40-55k | 王五 |  |" >> "$TMPD/tracker.md"
if "$PY" "$S/render_kanban.py" --tracker "$TMPD/tracker.md" --out "$TMPD/kanban.html" >/dev/null 2>&1; then
  if grep -q "投递总数" "$TMPD/kanban.html" && grep -q "测试公司" "$TMPD/kanban.html" && \
     ! grep -q "<script" "$TMPD/kanban.html"; then
    good "kanban html rendered (KPI + card + self-contained)"
  else
    bad "kanban html malformed"
  fi
else
  bad "render_kanban drill failed"
fi
"$PY" "$S/render_kanban.py" --tracker "$TMPD/nonexistent.md" >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 2 ]; then
  good "missing-tracker drill exit 2 as designed"
else
  bad "expected exit 2 for missing tracker, got $rc"
fi

section "profile_match CLI contract"
out="$("$PY" "$S/profile_match.py" --skills "SQL,Python,产品规划" --library internet 2>/dev/null)"; rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q "命中率"; then
  good "profile_match report rendered (internet library)"
else
  bad "profile_match drill unexpected (rc=$rc)"
fi
out="$("$PY" "$S/profile_match.py" --skills "SQL" --library nosuch 2>/dev/null)"; rc=$?
if [ "$rc" -ne 0 ]; then
  good "bad-library drill non-zero exit as designed (rc=$rc)"
else
  bad "expected non-zero exit for unknown library"
fi

section "openpyxl availability (optional, xlsx mode)"
if "$PY" -c "import openpyxl" 2>/dev/null; then
  good "openpyxl present (xlsx mode fully usable)"
else
  note "openpyxl absent — xlsx mode will exit 1 with install hint (md mode unaffected)"
fi

section "host-residue self-check"
if grep -rqE "mcp__cowork__create_artifact|AskUserQuestion|z-ai|web-dev-sdk|clawdbot|thesethrose" \
     "$SKILL_DIR/SKILL.md" "$SKILL_DIR/scripts/init_tracker.py" \
     "$SKILL_DIR/scripts/render_kanban.py" 2>/dev/null; then
  bad "host tool/SDK residue found"
else
  good "payload free of host tool/SDK references"
fi

section "knowledge anchors"
for anchor in "投递追踪表" "target_profile_template.md" "keywords_internet.md" \
              "render_kanban.py" "自我盘点" "求职方向" "Codex Deployment Notes" \
             ; do
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
note "outputs (tracker/kanban) land in the user working directory; plugin dir read-only."
exit 0
