#!/usr/bin/env bash
# glm-aminer-deep-search — 环境体检（离线：结构 + 离线单测 + 无 key 契约 + paper_set 状态机演练 +
# 宿主残留审计；不发起任何网络请求、不触碰 AMINER_API_KEY 值）
# Usage: bash ~/.codex/plugins/glm-academic/skills/aminer-deep-search/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-aminer-deep-search"
PY="${GLM_AMINER_DEEP_PYTHON:-python3}"
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
  bad "python interpreter not found (set GLM_AMINER_DEEP_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md SKILL.zh.md scripts/setup.sh scripts/aminer_api.py scripts/paper_set.py \
         tests/test_aminer_api.py tests/test_paper_set.py; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done
if [ -f "$SKILL_DIR/commands/aminer-deep-search.md" ]; then
  bad "Claude 宿主 commands/ 不应随包（契约已折进 SKILL.md）"
else
  good "no Claude-host commands/ in payload"
fi

section "offline unittests (mock urlopen，零网络)"
if (cd "$SKILL_DIR" && "$PY" tests/test_aminer_api.py >/dev/null 2>&1); then
  good "test_aminer_api.py passes offline"
else
  bad "test_aminer_api.py failed"
fi
if (cd "$SKILL_DIR" && "$PY" tests/test_paper_set.py >/dev/null 2>&1); then
  good "test_paper_set.py passes offline"
else
  bad "test_paper_set.py failed"
fi

section "CLI contracts"
if "$PY" "$SCRIPTS/aminer_api.py" --help >/dev/null 2>&1; then
  good "aminer_api.py --help exits 0"
else
  bad "aminer_api.py --help failed"
fi
if "$PY" "$SCRIPTS/paper_set.py" --help >/dev/null 2>&1; then
  good "paper_set.py --help exits 0"
else
  bad "paper_set.py --help failed"
fi
# 无 key 契约（离线：token 解析在发网前失败）
if env -u AMINER_API_KEY "$PY" "$SCRIPTS/aminer_api.py" search --query "x" >/dev/null 2>&1; then
  bad "missing key should exit 2"
else
  rc=$?; if [ "$rc" -eq 2 ]; then
    good "missing key exits 2 + JSON missing_aminer_api_key（stdout 结构化错误）"
  else
    bad "missing key exit=$rc (expect 2)"
  fi
fi
OUT=$(env -u AMINER_API_KEY "$PY" "$SCRIPTS/aminer_api.py" search --query "x" 2>/dev/null)
if printf '%s' "$OUT" | grep -q "missing_aminer_api_key" && ! printf '%s' "$OUT" | grep -qE "[0-9a-f]{24,}"; then
  good "error JSON carries no token-like material (token 永不落盘)"
else
  bad "error JSON leaked token-like string"
fi

section "paper_set state machine (offline drill)"
cd "$TMP"
printf '%s' '[{"id":"p1","title":"Paper One","year":2024},{"id":"p2","title":"Paper Two","year":2023},{"id":"p2","title":"Paper Two","year":2023,"source_paper_ids":["p1"]}]' \
  | "$PY" "$SCRIPTS/paper_set.py" --file state.json add > "$TMP/add.json" 2>/dev/null
if "$PY" -c "
import json
d = json.load(open('$TMP/add.json'))
assert d['added'] == 2 and d['duplicates'] == 1 and d['total'] == 2, d
sys.exit(0) if False else None
import sys
assert 'p1' in json.load(open('$TMP/state.json'))['expanded_seeds']
sys.exit(0)
"; then
  good "add: dedupe by id + source_paper_ids 自动标记 expanded_seeds"
else
  bad "add contract failed"
fi
if "$PY" "$SCRIPTS/paper_set.py" --file state.json stats 2>/dev/null | grep -q '"total": 2'; then
  good "stats: totals/by_year 正常"
else
  bad "stats contract failed"
fi
if "$PY" "$SCRIPTS/paper_set.py" --file state.json export -o final.json 2>/dev/null | grep -q '"count": 2' \
   && "$PY" -c "
import json, sys
final = json.load(open('$TMP/final.json'))
assert {item['id'] for item in final} == {'p1', 'p2'}
assert all(item.get('title') for item in final)
sys.exit(0)
"; then
  good "export: [{id,title}] 列表落盘且带标题"
else
  bad "export contract failed"
fi

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (纯标准库 urllib 直调)"
fi

section "knowledge anchors"
for anchor in "Round Protocol" "target-size" "expanded_seeds" "paper_set.py" "aminer_api.py" \
              "glm-aminer-free-academic" "Codex Deployment Notes"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
