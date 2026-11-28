#!/usr/bin/env bash
# glm-gaokao-fetch-volunteers — 环境体检（离线：结构 + 脚本契约 + 校验规则演练 + 宿主残留审计；
# 不发起任何网络请求——公网接口连通性留给用户显式调用时验证）
# Usage: bash ~/.codex/plugins/glm-gaokao-fetch-volunteers/skills/glm-gaokao-fetch-volunteers/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-gaokao-fetch-volunteers"
PY="${GLM_GAOKAO_FETCH_PYTHON:-python3}"
SCRIPTS="$SKILL_DIR/scripts"
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
  bad "python interpreter not found (set GLM_GAOKAO_FETCH_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/fetch_volunteers.py \
         scripts/build_api_request.py scripts/province_config.py \
         references/api-reference.md references/preference-mapping.md \
         examples/api_request_template.json examples/api_request_shandong.json; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done
if [ -d "$SCRIPTS/__pycache__" ]; then
  bad "__pycache__ shipped in payload (应剔除)"
else
  good "no __pycache__ in payload"
fi

section "stdlib-only audit (零 pip 依赖)"
if "$PY" -c "
import ast, pathlib, sys
local = {p.stem for p in pathlib.Path('$SCRIPTS').glob('*.py')}
allowed = {'argparse','json','os','sys','pathlib','typing','urllib','__future__'} | local
bad = []
for p in pathlib.Path('$SCRIPTS').glob('*.py'):
    for node in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            bad += [a.name for a in node.names if a.name.split('.')[0] not in allowed]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            if node.module.split('.')[0] not in allowed:
                bad.append(node.module)
sys.exit(1 if bad else 0)
"; then
  good "scripts import stdlib + sibling modules only (urllib 直调公网接口，无 requests/jinja2)"
else
  bad "non-stdlib import detected"
fi

section "script CLI contracts"
if "$PY" "$SCRIPTS/fetch_volunteers.py" --help >/dev/null 2>&1; then
  good "fetch_volunteers.py --help exits 0"
else
  bad "fetch_volunteers.py --help failed"
fi
if "$PY" "$SCRIPTS/build_api_request.py" --help >/dev/null 2>&1; then
  good "build_api_request.py --help exits 0"
else
  bad "build_api_request.py --help failed"
fi
# 参数缺失契约：无 student/config 时 exit 1
if "$PY" "$SCRIPTS/fetch_volunteers.py" -o "$TMP/x.json" >/dev/null 2>&1; then
  bad "missing required args should exit 1"
else
  good "missing-args contract exits 1 (缺 province/classify/score 提示)"
fi

section "build_api_request contract (synthetic student)"
"$PY" -c "
import json, pathlib
pathlib.Path('$TMP/student.json').write_text(json.dumps({
  'province': '山东', 'classify': '综合', 'subjects': '物理,化学,生物',
  'score': 650, 'batch': '本科批', 'rank': None, 'gradeType': None,
  'preferred_cities': ['北京', '上海', '深圳'],
  'preferred_provinces': ['北京', '上海', '广东'],
  'preferred_universities': ['北京航空航天大学'],
  'preferred_tags': ['985', '211'],
  'preferred_major_classes': ['计算机类', '电子信息类'],
}, ensure_ascii=False), encoding='utf-8')
"
if "$PY" "$SCRIPTS/build_api_request.py" -i "$TMP/student.json" -o "$TMP/req.json" --summary "$TMP/summary.json" >/dev/null 2>&1; then
  good "built api_request.json from synthetic student (倾向→API 选填参数)"
  if "$PY" -c "
import json, sys
d = json.load(open('$TMP/req.json'))
assert d['provinces'] == '北京,上海,广东', d.get('provinces')
assert d['universitys'] == '北京航空航天大学'
assert d['majorClass'] == '计算机类,电子信息类'
sys.exit(0)
"; then
    good "preference mapping values correct (provinces/universitys/majorClass)"
  else
    bad "preference mapping values wrong"
  fi
else
  bad "build_api_request.py failed on synthetic student"
fi
# classify 反例：山东填物理应被拦截
"$PY" -c "
import json, pathlib
pathlib.Path('$TMP/bad_student.json').write_text(json.dumps({
  'province': '山东', 'classify': '物理', 'subjects': '物理,化学,生物',
  'score': 650, 'batch': '本科批', 'rank': None, 'gradeType': None,
}, ensure_ascii=False), encoding='utf-8')
"
if "$PY" "$SCRIPTS/build_api_request.py" -i "$TMP/bad_student.json" -o "$TMP/bad_req.json" >/dev/null 2>&1; then
  bad "classify=物理 for 山东 should be rejected"
else
  good "classify=物理 for 山东 rejected by validate_classify (exit 1)"
fi

section "province_config rule rehearsal"
if "$PY" -c "
import sys
sys.path.insert(0, '$SCRIPTS')
from province_config import validate_classify, get_province_mode
assert get_province_mode('山东') == '33'
assert get_province_mode('广东') == '312'
assert get_province_mode('新疆') == '老高考'
assert get_province_mode('西藏') == 'unsupported'
try:
    validate_classify('山东', '物理'); raise AssertionError('山东+物理 未拦截')
except ValueError:
    pass
validate_classify('广东', '物理')
validate_classify('新疆', '理科')
try:
    validate_classify('广东', '化学,生物'); raise AssertionError('subjects 误当 classify 未拦截')
except ValueError:
    pass
sys.exit(0)
"; then
  good "province mode + classify validation rules rehearsed (鲁/粤/新/藏)"
else
  bad "province_config rule rehearsal failed"
fi

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (公网无鉴权 HTTP + 纯标准库)"
fi

section "network egress disclosure"
if grep -q "publicapi.chatglm.cn" "$SKILL_DIR/SKILL.md" && grep -q "ZP_API_BASE_URL" "$SKILL_DIR/SKILL.md"; then
  good "API endpoint + override (ZP_API_BASE_URL) documented in SKILL.md"
else
  bad "API endpoint/override not documented"
fi
if grep -q "BASE_URL" "$SCRIPTS/fetch_volunteers.py"; then
  good "BASE_URL constant + --base-url flag present in fetch_volunteers.py"
else
  bad "BASE_URL/--base-url missing"
fi

section "knowledge anchors"
for anchor in "两阶段" "batch/list" "intelligenceVolunteer" "province_config" \
              "preference-mapping" "Codex Deployment Notes" "零 pip 依赖"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
