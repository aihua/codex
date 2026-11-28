#!/usr/bin/env bash
# glm-multi-search-engine — environment check (offline: structure + CLI contracts)
# Usage: bash ~/.codex/plugins/glm-web/skills/glm-multi-search-engine/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-multi-search-engine"
PY="${GLM_MULTI_SEARCH_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_MULTI_SEARCH_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/mse.py scripts/setup.sh \
         references/international-search.md references/CHANGELOG.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "engine registry self-test (engines -> exit 0, 8 engines listed)"
out="$("$PY" "$SKILL_DIR/scripts/mse.py" engines 2>/dev/null)"; rc=$?
if [ "$rc" -eq 0 ] && [ "$(printf '%s\n' "$out" | grep -c 'https://')" -eq 8 ]; then
  good "registry lists all 8 CN engines with URL templates"
else
  bad "engines subcommand broken (rc=$rc)"
fi

section "search CLI self-test (no args -> argparse exit 2)"
out="$("$PY" "$SKILL_DIR/scripts/mse.py" 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "usage self-test exit 2 as designed"
else
  bad "expected exit 2 without args, got $rc"
fi

section "search CLI self-test (bad engine id -> argparse exit 2)"
out="$("$PY" "$SKILL_DIR/scripts/mse.py" search --engine nosuch --query x 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "bad-engine self-test exit 2 as designed"
else
  bad "expected exit 2 for unknown engine, got $rc"
fi

section "offline discipline (unreachable host -> exit 2 with hint)"
out="$("$PY" "$SKILL_DIR/scripts/mse.py" fetch "https://nonexistent.invalid.invalid/x" 2>&1)"; rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q "网络不可达"; then
  good "fetch network-failure drill exit 2 with hint"
else
  bad "fetch network-failure drill unexpected (rc=$rc)"
fi

section "heuristic parser unit drill (synthetic result page)"
wrap="$(mktemp /tmp/glmmse_drill_XXXX.py)"
cat > "$wrap" <<PYEOF
import importlib.util, sys
spec = importlib.util.spec_from_file_location("mse", "$SKILL_DIR/scripts/mse.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
page = """
<a href="https://example.com/python-tutorial-full-course">Python 教程完整版课程</a>
<a href="https://example.org/ml-notes">机器学习笔记</a>
<a href="https://cn.bing.com/self-link">内部链接应当被过滤</a>
<a href="javascript:void(0)">js</a>
"""
rs = m.extract_results(page, "https://cn.bing.com/search?q=x")
assert len(rs) == 2, f"expected 2 results, got {len(rs)}"
assert rs[0]["title"].startswith("Python 教程")
assert rs[1]["url"] == "https://example.org/ml-notes"
print("parse-drill-ok: 2 hits, self-host and js filtered")
PYEOF
out="$("$PY" "$wrap" 2>&1)"; rc=$?
rm -f "$wrap"
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q "parse-drill-ok"; then
  good "heuristic parser: external hits kept, self/js links filtered"
else
  bad "heuristic parser drill failed (rc=$rc): $out"
fi

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "runtime network: mse.py hits the chosen CN engine only when the user asks to search"
exit 0
