#!/usr/bin/env bash
# glm-research-explorer — environment check (offline: structure + CLI contracts)
# Usage: bash ~/.codex/plugins/glm-academic/skills/glm-research-explorer/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-research-explorer"
PY="${GLM_RESEARCH_EXPLORER_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_RESEARCH_EXPLORER_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/s2_search.py scripts/setup.sh references/equivalents.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "search CLI self-test (no args -> argparse exit 2)"
out="$("$PY" "$SKILL_DIR/scripts/s2_search.py" 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "usage self-test exit 2 as designed (argparse missing-arg contract)"
else
  bad "expected exit 2 without args, got $rc"
fi

section "search CLI self-test (--limit out of range -> exit 2)"
out="$("$PY" "$SKILL_DIR/scripts/s2_search.py" --query x --limit 99 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "bad-limit self-test exit 2 as designed"
else
  bad "expected exit 2 for bad limit, got $rc"
fi

section "offline discipline (simulated unreachable host -> exit 2 + degrade hint)"
wrap="$(mktemp /tmp/glmre_drill_XXXX.py)"
cat > "$wrap" <<PYEOF
import importlib.util, sys
spec = importlib.util.spec_from_file_location("s2", "$SKILL_DIR/scripts/s2_search.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.API = "https://nonexistent.invalid.invalid/graph/v1/paper/search"
sys.argv = ["s2_search.py", "--query", "test"]
try:
    m.main()
except SystemExit as e:
    sys.exit(e.code)
PYEOF
out="$("$PY" "$wrap" 2>&1)"; rc=$?
rm -f "$wrap"
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q "降级建议"; then
  good "network-failure drill exit 2 with degrade hint"
else
  bad "network-failure drill unexpected (rc=$rc)"
fi

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "runtime network: s2_search.py hits api.semanticscholar.org only when the user asks for exploration"
exit 0
