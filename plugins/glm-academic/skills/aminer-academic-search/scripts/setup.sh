#!/usr/bin/env bash
# glm-aminer-academic-search — 环境体检（离线：结构 + 纯标准库审计 + CLI 契约 + 宿主残留审计；
# 不发起任何网络请求、不触碰 AMINER_API_KEY 值）
# Usage: bash ~/.codex/plugins/glm-academic/skills/aminer-academic-search/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-aminer-academic-search"
PY="${GLM_AMINER_SEARCH_PYTHON:-python3}"
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
  bad "python interpreter not found (set GLM_AMINER_SEARCH_PYTHON to fix)"
fi
if command -v curl >/dev/null 2>&1; then
  good "curl available (直调形态一)"
else
  bad "curl not found"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/aminer_client.py \
         references/api-catalog.md evals/evals.json; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "stdlib-only audit (零 pip 依赖)"
if "$PY" -c "
import ast, pathlib, sys
bad = []
tree = ast.parse(pathlib.Path('$SKILL_DIR/scripts/aminer_client.py').read_text(encoding='utf-8'))
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        bad += [a.name for a in node.names if a.name.split('.')[0] not in
                ('argparse','json','os','sys','time','random','threading','urllib','__future__')]
    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        if node.module.split('.')[0] not in ('argparse','json','os','sys','time','random','threading','urllib','__future__','concurrent','typing'):
            bad.append(node.module)
sys.exit(1 if bad else 0)
"; then
  good "aminer_client.py imports stdlib only (urllib 直调 + 线程池)"
else
  bad "non-stdlib import detected in aminer_client.py"
fi
if "$PY" -c "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)" "$SKILL_DIR/scripts/aminer_client.py" "$TMP/aminer_client.pyc" >/dev/null 2>&1; then
  good "aminer_client.py compiles"
else
  bad "aminer_client.py syntax error"
fi

section "CLI contract"
if "$PY" "$SKILL_DIR/scripts/aminer_client.py" --help >/dev/null 2>&1; then
  good "aminer_client.py --help exits 0"
else
  bad "aminer_client.py --help failed"
fi

section "catalog integrity"
N=$("$PY" - "$SKILL_DIR/references/api-catalog.md" <<'EOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
print(len(re.findall(r"^### ", text, flags=re.M)))
EOF
)
if [ "${N:-0}" -ge 28 ]; then
  good "api-catalog.md documents $N APIs (>=28)"
else
  bad "api-catalog.md API count = ${N:-err} (expect >=28)"
fi
for path in "/api/v3/paper/qa/searchPro" "/api/person/search" "/api/paper/detail" "/api/patent/detail"; do
  if grep -q "$path" "$SKILL_DIR/references/api-catalog.md"; then
    good "catalog endpoint present: $path"
  else
    bad "catalog endpoint missing: $path"
  fi
done

section "evals integrity"
if "$PY" -c "
import json, sys
d = json.load(open('$SKILL_DIR/evals/evals.json'))
assert d.get('skill_name') == 'aminer-academic-search', d.get('skill_name')
assert isinstance(d.get('evals'), list) and len(d['evals']) >= 5
sys.exit(0)
"; then
  good "evals.json parses (skill_name + >=5 cases)"
else
  bad "evals.json invalid"
fi

section "cost & token discipline anchors"
for anchor in "¥5" "AMINER_API_KEY" "Cost Control" "never expose"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (curl/urllib 直调公网接口)"
fi

section "knowledge anchors"
for anchor in "28 APIs" "5 Combined Workflows" "paper_qa_search_pro" "glm-aminer-free-academic" \
              "glm-aminer-daily-paper" "glm-aminer-deep-search" "Codex Deployment Notes"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
