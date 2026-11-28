#!/usr/bin/env bash
# glm-gaokao-generate-report — 环境体检（离线：结构 + 模板完整性 + 渲染管线演练 + 宿主残留审计）
# Usage: bash ~/.codex/plugins/glm-gaokao-generate-report/skills/glm-gaokao-generate-report/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-gaokao-generate-report"
PY="${GLM_GAOKAO_REPORT_PYTHON:-python3}"
SCRIPTS="$SKILL_DIR/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
warnonce() { printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_GAOKAO_REPORT_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/merge_analysis.py scripts/generate_html.py \
         templates/volunteer_report.html examples/analysis_merged_example.json; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "jinja2 dependency (唯一第三方依赖)"
if "$PY" -c "import jinja2" >/dev/null 2>&1; then
  good "jinja2 importable by $PY"
else
  warnonce "jinja2 未安装——免安装直跑: uv run --with jinja2 python3 <脚本> ...；或 pip install jinja2"
fi
if command -v uv >/dev/null 2>&1; then
  good "uv available ($(uv --version 2>/dev/null | head -1))"
else
  warnonce "uv 不在 PATH（用户 macOS 环境为 /opt/uv/0.11.17）——用 pip install jinja2 兜底"
fi

section "template integrity"
if grep -q '{%' "$SKILL_DIR/templates/volunteer_report.html" && grep -q '{{' "$SKILL_DIR/templates/volunteer_report.html"; then
  good "template contains Jinja2 directives ({% / {{)"
else
  bad "template missing Jinja2 directives"
fi
for anchor in "sections" "universities" "rec_modals_json" "score_display"; do
  if grep -q "$anchor" "$SKILL_DIR/templates/volunteer_report.html"; then
    good "template variable present: $anchor"
  else
    bad "template variable missing: $anchor"
  fi
done

section "merge_analysis contract (stdlib)"
if "$PY" "$SCRIPTS/merge_analysis.py" --help >/dev/null 2>&1; then
  good "merge_analysis.py --help exits 0 (纯标准库)"
else
  bad "merge_analysis.py --help failed"
fi

section "friendly jinja2 guard"
if grep -q "uv run --with jinja2" "$SCRIPTS/generate_html.py"; then
  good "generate_html.py has friendly jinja2-missing guard (exit 2 + uv/pip 提示)"
else
  bad "generate_html.py missing friendly guard"
fi

section "render pipeline rehearsal (jinja2 可用时)"
"$PY" -c "
import json, pathlib
parsed = {
  'meta': {'generated_from': 'intelligenceVolunteer', 'api_code': 200, 'api_msg': 'OK'},
  'profile': {'province': '山东', 'classify': '综合', 'subjects': '物理,化学,生物',
              'score': 650, 'rank': 5000, 'batch': '普通类一段',
              'volunteer_type': 'ACADEMY_GROUP', 'is_adjust': True},
  'stats': {'total': 2, 'chong': 1, 'wen': 1, 'bao': 0},
  'schools': [
    {'index': 1, 'university_name': '北京航空航天大学', 'university_code': '10006',
     'major_group': '01', 'type': 'CHONG', 'type_label': '冲', 'enroll_probability': 35,
     'city_name': '北京', 'province_name': '北京', 'tags': '985,211',
     'score_history': [], 'parity_scores': [],
     'majors': [{'major_name': '计算机科学与技术', 'major_code': '080901', 'claim': '物且化',
                 'type': 'CHONG', 'type_label': '冲', 'score_history': [], 'parity_scores': []}]},
    {'index': 2, 'university_name': '华东师范大学', 'university_code': '10269',
     'major_group': '02', 'type': 'WEN', 'type_label': '稳', 'enroll_probability': 72,
     'city_name': '上海', 'province_name': '上海', 'tags': '985',
     'score_history': [], 'parity_scores': [],
     'majors': [{'major_name': '数据科学与大数据技术', 'major_code': '080910', 'claim': '物且化',
                 'type': 'WEN', 'type_label': '稳', 'score_history': [], 'parity_scores': []}]}],
  'schools_by_type': {'冲': [], '稳': []},
  'raw_body': {}}
for t, s in (('冲', parsed['schools'][0]), ('稳', parsed['schools'][1])):
    parsed['schools_by_type'][t].append(s)
majors_rec = {'student': {'interests': '编程'}, 'intro': '开篇', 'strategy': '策略',
  'major_directions': [], 'recommended_majors': [
    {'university_name': '北京航空航天大学', 'university_code': '10006',
     'major_name': '计算机科学与技术', 'major_code': '080901',
     'modal': {'title': '专业推荐', 'body': '<h4>x</h4>'}}]}
schools_rec = {'school_strategy': '布局', 'recommended_schools': [
    {'university_name': '北京航空航天大学', 'university_code': '10006',
     'modal': {'title': '推荐原因', 'body': '<h4>y</h4>'}}]}
pathlib.Path('$TMP/parsed.json').write_text(json.dumps(parsed, ensure_ascii=False), encoding='utf-8')
pathlib.Path('$TMP/majors.json').write_text(json.dumps(majors_rec, ensure_ascii=False), encoding='utf-8')
pathlib.Path('$TMP/schools.json').write_text(json.dumps(schools_rec, ensure_ascii=False), encoding='utf-8')
"
if "$PY" "$SCRIPTS/merge_analysis.py" --majors "$TMP/majors.json" --schools "$TMP/schools.json" -o "$TMP/analysis.json" >/dev/null 2>&1; then
  good "merge_analysis.py merged fixture (analysis.json written)"
else
  bad "merge_analysis.py failed on fixture"
fi
if "$PY" -c "
import sys
try:
    import jinja2  # noqa: F401
except ImportError:
    sys.exit(0)  # 无 jinja2 时跳过渲染演练（guard 会在实跑时给出提示）
sys.exit(42)
"; rc=$?; [ "$rc" -eq 42 ]; then
  if "$PY" "$SCRIPTS/generate_html.py" -i "$TMP/parsed.json" -a "$TMP/analysis.json" -o "$TMP/report.html" >/dev/null 2>&1 \
     && grep -q "高考志愿智能推荐方案" "$TMP/report.html" \
     && grep -q "北京航空航天大学" "$TMP/report.html"; then
    good "generate_html.py rendered fixture report (含标题与院校名)"
  else
    bad "generate_html.py rendering failed on fixture"
  fi
else
  note "jinja2 不可用——渲染演练跳过（uv run --with jinja2 可免安装直跑）"
fi

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (离线渲染，零网络)"
fi

section "knowledge anchors"
for anchor in "uv run --with jinja2" "merge_analysis.py" "volunteer_report.html" \
              "Codex Deployment Notes" "glm-gaokao-fetch-volunteers"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
