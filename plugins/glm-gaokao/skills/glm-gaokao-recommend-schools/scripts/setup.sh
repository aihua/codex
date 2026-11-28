#!/usr/bin/env bash
# glm-gaokao-recommend-schools — 环境体检（离线：结构 + 校验器契约演练 + 宿主残留审计）
# Usage: bash ~/.codex/plugins/glm-gaokao-recommend-schools/skills/glm-gaokao-recommend-schools/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-gaokao-recommend-schools"
PY="${GLM_GAOKAO_SCHOOLS_PYTHON:-python3}"
CHK="$SKILL_DIR/scripts/check_recommendation.py"
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
  bad "python interpreter not found (set GLM_GAOKAO_SCHOOLS_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/check_recommendation.py \
         references/career-reference.md \
         examples/school_recommendation_template.json; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (纯 Agent 分析 + 纯标准库校验器)"
fi

section "check_recommendation contract (synthetic fixture)"
"$PY" -c "
import json, pathlib
parsed = {
  'stats': {'total': 3, 'chong': 1, 'wen': 1, 'bao': 1},
  'schools': [
    {'university_name': '北京航空航天大学', 'university_code': '10006', 'type': 'CHONG'},
    {'university_name': '华东师范大学', 'university_code': '10269', 'type': 'WEN'},
    {'university_name': '中山大学', 'university_code': '10558', 'type': 'BAO'}]}
good_rec = {'school_strategy': 's',
  'recommended_schools': [
    {'university_name': '北京航空航天大学', 'university_code': '10006',
     'modal': {'title': 't', 'body': '<h4>b</h4>'}},
    {'university_name': '中山大学', 'university_code': '10558',
     'modal': {'title': 't', 'body': '<h4>b</h4>'}}]}
bad_rec = {'school_strategy': 's',
  'recommended_schools': [
    {'university_name': '北京航空航天大学', 'university_code': '10006'},
    {'university_name': '中山大学', 'university_code': '10558'},
    {'university_name': '华南理工大学', 'university_code': '10561'}]}
pathlib.Path('$TMP/parsed.json').write_text(json.dumps(parsed, ensure_ascii=False), encoding='utf-8')
pathlib.Path('$TMP/good.json').write_text(json.dumps(good_rec, ensure_ascii=False), encoding='utf-8')
pathlib.Path('$TMP/bad.json').write_text(json.dumps(bad_rec, ensure_ascii=False), encoding='utf-8')
"
if "$PY" "$CHK" --parsed "$TMP/parsed.json" --recommendation "$TMP/good.json" >/dev/null 2>&1; then
  good "fully-matched recommendation passes (exit 0)"
else
  bad "fully-matched recommendation should pass"
fi
if "$PY" "$CHK" --parsed "$TMP/parsed.json" --recommendation "$TMP/bad.json" >/dev/null 2>&1; then
  bad "drifted entries should FAIL"
else
  good "drifted entries correctly rejected (exit 1) — 校验器能拦住本地模型字段漂移"
fi
if "$PY" "$CHK" --parsed "$TMP/parsed.json" --recommendation "$TMP/nope.json" >/dev/null 2>&1; then
  bad "missing file should exit 2"
else
  rc=$?; if [ "$rc" -eq 2 ]; then good "missing file exits 2"; else bad "missing file exit=$rc (expect 2)"; fi
fi

section "knowledge anchors"
for anchor in "硬性约束" "6–12" "check_recommendation.py" "Codex Deployment Notes" \
              "glm-gaokao-generate-report" "地域优势"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
