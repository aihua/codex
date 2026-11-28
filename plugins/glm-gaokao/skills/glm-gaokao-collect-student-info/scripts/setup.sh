#!/usr/bin/env bash
# glm-gaokao-collect-student-info — 环境体检（离线：结构 + 校验器契约 + 宿主残留审计）
# Usage: bash ~/.codex/plugins/glm-gaokao-collect-student-info/skills/glm-gaokao-collect-student-info/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-gaokao-collect-student-info"
PY="${GLM_GAOKAO_COLLECT_PYTHON:-python3}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_GAOKAO_COLLECT_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/student_check.py \
         references/api-quick-reference.md \
         examples/student_template.json examples/student_shandong.json; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (纯对话 + 纯标准库校验器)"
fi

section "student_check contract (examples)"
if "$PY" "$SKILL_DIR/scripts/student_check.py" -i "$SKILL_DIR/examples/student_shandong.json" >/dev/null 2>&1; then
  good "shandong example passes province-mode check (exit 0)"
else
  bad "shandong example should pass student_check.py"
fi
# 反例：山东填 classify=物理（最常见错误）应被拦截
"$PY" -c "
import json, pathlib, sys
src = json.loads(pathlib.Path('$SKILL_DIR/examples/student_shandong.json').read_text(encoding='utf-8'))
src['classify'] = '物理'
pathlib.Path('$TMP/bad_shandong.json').write_text(json.dumps(src, ensure_ascii=False), encoding='utf-8')
"
if "$PY" "$SKILL_DIR/scripts/student_check.py" -i "$TMP/bad_shandong.json" >/dev/null 2>&1; then
  bad "classify=物理 for 山东 should FAIL (未拦截最常见错误)"
else
  good "classify=物理 for 山东 correctly rejected (exit 1)"
fi
# 反例：3+1+2 只录两门再选应被拦截
"$PY" -c "
import json, pathlib
src = json.loads(pathlib.Path('$SKILL_DIR/examples/student_shandong.json').read_text(encoding='utf-8'))
src['province'] = '广东'; src['classify'] = '物理'; src['subjects'] = '化学,生物'
pathlib.Path('$TMP/bad_gd.json').write_text(json.dumps(src, ensure_ascii=False), encoding='utf-8')
"
if "$PY" "$SKILL_DIR/scripts/student_check.py" -i "$TMP/bad_gd.json" >/dev/null 2>&1; then
  bad "广东两门再选 should FAIL"
else
  good "广东 subjects=化学,生物 correctly rejected (3+1+2 须完整三科)"
fi
# 反例：非京沪津误填 gradeType 应被拦截
"$PY" -c "
import json, pathlib
src = json.loads(pathlib.Path('$SKILL_DIR/examples/student_shandong.json').read_text(encoding='utf-8'))
src['gradeType'] = '本科'
pathlib.Path('$TMP/bad_gt.json').write_text(json.dumps(src, ensure_ascii=False), encoding='utf-8')
"
if "$PY" "$SKILL_DIR/scripts/student_check.py" -i "$TMP/bad_gt.json" >/dev/null 2>&1; then
  bad "山东填 gradeType should FAIL"
else
  good "山东误填 gradeType correctly rejected (仅京沪津可填)"
fi
# 坏 JSON exit 2
printf '{broken' > "$TMP/broken.json"
if "$PY" "$SKILL_DIR/scripts/student_check.py" -i "$TMP/broken.json" >/dev/null 2>&1; then
  bad "broken JSON should exit 2"
else
  rc=$?; if [ "$rc" -eq 2 ]; then good "broken JSON correctly exits 2"; else bad "broken JSON exit code = $rc (expect 2)"; fi
fi

section "knowledge anchors"
for anchor in "还原原生描述" "完整三科" "Codex Deployment Notes" "student_check.py" \
              "glm-gaokao-fetch-volunteers" "preferred_"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
