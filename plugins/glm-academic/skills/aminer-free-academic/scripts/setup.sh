#!/usr/bin/env bash
# glm-aminer-free-academic — 环境体检（离线：结构 + 免费接口目录完整性 + 宿主残留审计；
# 不发起任何网络请求、不触碰 AMINER_API_KEY 值）
# Usage: bash ~/.codex/plugins/glm-academic/skills/aminer-free-academic/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-aminer-free-academic"
PY="${GLM_AMINER_FREE_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_AMINER_FREE_PYTHON to fix)"
fi
if command -v curl >/dev/null 2>&1; then
  good "curl available (本插件调用形态：curl 直调 7 免费接口)"
else
  bad "curl not found"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh references/api-catalog.md evals/evals.json; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "free API surface integrity"
for api in paper_search paper_info person_search organization_search venue_search patent_search patent_info; do
  if grep -q "\`$api\`" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md free API listed: $api"
  else
    bad "SKILL.md free API missing: $api"
  fi
done
N=$("$PY" - "$SKILL_DIR/references/api-catalog.md" <<'EOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
print(len(re.findall(r"^### ", text, flags=re.M)))
EOF
)
if [ "${N:-0}" -ge 7 ]; then
  good "api-catalog.md documents $N free APIs (>=7)"
else
  bad "api-catalog.md API count = ${N:-err} (expect >=7)"
fi

section "evals integrity"
if "$PY" -c "
import json, sys
d = json.load(open('$SKILL_DIR/evals/evals.json'))
assert isinstance(d.get('evals'), list) and len(d['evals']) >= 3
sys.exit(0)
"; then
  good "evals.json parses (>=3 cases)"
else
  bad "evals.json invalid"
fi

section "routing & discipline anchors"
for anchor in "AMINER_API_KEY" "Routing rule" "Paid Upgrade Boundary" "glm-aminer-academic-search" \
              "先用免费接口" "Codex Deployment Notes"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (纯 curl 直调，零脚本)"
fi

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
