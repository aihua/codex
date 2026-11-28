#!/bin/bash
# setup.sh — environment health check for the glm-ui-ux-pro-max skill.
# Checks only; installs nothing. The skill is fully offline: python3 stdlib
# plus bundled CSV data. No network is required for any command.
#
# Usage: bash setup.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$SKILL_DIR/data"

PASS=0; WARN=0; FAIL=0
line() { printf '  %-46s %s\n' "$1" "$2"; }
ok()   { line "$1" "OK${2:+ $2}"; PASS=$((PASS+1)); }
warn() { line "$1" "WARN — $2"; WARN=$((WARN+1)); }
fail() { line "$1" "FAIL — $2"; FAIL=$((FAIL+1)); }

echo "== glm-ui-ux-pro-max environment check =="

# --- python interpreter ------------------------------------------------------
PY="${GLM_UIUX_PROMAX_PYTHON:-python3}"
if command -v "$PY" >/dev/null 2>&1; then
  PY_VER="$("$PY" --version 2>&1)"
  ok "python interpreter ($PY)" " ($PY_VER)"
else
  fail "python interpreter ($PY)" "not found; set GLM_UIUX_PROMAX_PYTHON to a python3 path"
fi

# --- bundled data files ------------------------------------------------------
EXPECTED_CSVS="styles.csv colors.csv charts.csv landing.csv products.csv \
ux-guidelines.csv typography.csv icons.csv react-performance.csv \
web-interface.csv ui-reasoning.csv"
MISSING=""
for f in $EXPECTED_CSVS; do
  [ -f "$DATA_DIR/$f" ] || MISSING="$MISSING $f"
done
STACK_COUNT=$(ls "$DATA_DIR/stacks" 2>/dev/null | wc -l | tr -d ' ')
if [ -z "$MISSING" ] && [ "$STACK_COUNT" -eq 13 ]; then
  ok "bundled data (11 domain CSV + 13 stack CSV)" "in skills/glm-ui-ux-pro-max/data/"
else
  fail "bundled data" "missing:$MISSING stacks found: ${STACK_COUNT:-0}/13 — reinstall the plugin tarball"
fi

# --- script syntax check ----------------------------------------------------
if command -v "$PY" >/dev/null 2>&1; then
  SYNTAX_OK=0
  for s in core.py search.py design_system.py; do
    "$PY" -m py_compile "$SCRIPT_DIR/$s" 2>/dev/null || { SYNTAX_OK=1; break; }
  done
  if [ "$SYNTAX_OK" -eq 0 ]; then
    ok "script syntax (py_compile)"
  else
    fail "script syntax (py_compile)" "scripts/core.py or search.py or design_system.py failed to compile"
  fi
fi

# --- search engine smoke test (offline BM25) --------------------------------
if command -v "$PY" >/dev/null 2>&1 && [ -z "$MISSING" ]; then
  SM_OUT="$(cd "$SCRIPT_DIR" && "$PY" search.py "dashboard color palette" -n 1 2>&1)"
  SM_RC=$?
  if [ "$SM_RC" -eq 0 ] && printf '%s' "$SM_OUT" | grep -q "Found:"; then
    ok "search.py BM25 smoke test" "(auto-domain detection works)"
  else
    fail "search.py BM25 smoke test" "rc=$SM_RC; output did not contain a results line"
  fi

  DS_OUT="$(cd "$SCRIPT_DIR" && "$PY" design_system.py "SaaS dashboard" -p "setup-check" 2>&1)"
  DS_RC=$?
  if [ "$DS_RC" -eq 0 ] && printf '%s' "$DS_OUT" | grep -q "RECOMMENDED DESIGN SYSTEM"; then
    ok "design_system.py generator smoke test"
  else
    fail "design_system.py generator smoke test" "rc=$DS_RC; expected the design-system banner"
  fi
fi

echo "== summary: $PASS ok, $WARN warn, $FAIL fail =="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
