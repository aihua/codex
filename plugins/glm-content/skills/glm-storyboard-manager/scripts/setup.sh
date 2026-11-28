#!/bin/bash
# setup.sh — environment health check for the glm-storyboard-manager skill.
# Checks only; installs nothing.
#
# The skill's executable payload is two pure-stdlib Python analyzers
# (timeline_tracker.py / consistency_checker.py). Missing python3 is FAIL (no
# degraded mode). No network checks: the payload has zero network endpoints by
# design (works inside the Codex command sandbox with networking blocked).
#
# Usage: bash setup.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

PASS=0; WARN=0; FAIL=0
line() { printf '  %-46s %s\n' "$1" "$2"; }
ok()   { line "$1" "OK${2:+ $2}"; PASS=$((PASS+1)); }
warn() { line "$1" "WARN — $2"; WARN=$((WARN+1)); }
fail() { line "$1" "FAIL — $2"; FAIL=$((FAIL+1)); }

echo "== glm-storyboard-manager environment check =="

# --- python interpreter (the two analyzers) -----------------------------------
PY="${GLM_STORYBOARD_PYTHON:-python3}"
if command -v "$PY" >/dev/null 2>&1; then
  PY_VER="$("$PY" --version 2>&1)"
  ok "python interpreter ($PY)" "($PY_VER)"
else
  fail "python interpreter ($PY)" "not found; set GLM_STORYBOARD_PYTHON to a python3 path"
fi

# --- skill structure ----------------------------------------------------------
REFS="story_structures.md character_development.md"
SRCS="timeline_tracker.py consistency_checker.py"
MISSING=""
for r in $REFS; do
  [ -f "$SKILL_DIR/references/$r" ] || MISSING="$MISSING references/$r"
done
for s in $SRCS; do
  [ -f "$SKILL_DIR/scripts/$s" ] || MISSING="$MISSING scripts/$s"
done
[ -f "$SKILL_DIR/SKILL.md" ] || MISSING="$MISSING SKILL.md"
if [ -z "$MISSING" ]; then
  ok "skill structure (SKILL.md + 2 scripts + 2 references)"
else
  fail "skill structure" "missing:$MISSING — reinstall the plugin tarball"
fi

# --- analyzer syntax + usage self-test ---------------------------------------
if command -v "$PY" >/dev/null 2>&1; then
  for s in $SRCS; do
    if "$PY" -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" \
         "$SCRIPT_DIR/$s" 2>/dev/null; then
      ok "syntax check scripts/$s"
    else
      fail "syntax check scripts/$s" "syntax error — reinstall the plugin tarball"
    fi
  done
  for s in $SRCS; do
    OUT="$("$PY" "$SCRIPT_DIR/$s" 2>&1)"
    RC=$?
    case "$OUT" in
      Usage:*) if [ "$RC" -eq 1 ]; then
                 ok "usage self-test scripts/$s" "(no args -> usage + exit 1)"
               else
                 fail "usage self-test scripts/$s" "usage text but rc=$RC (expected 1)"
               fi ;;
      *)       fail "usage self-test scripts/$s" "unexpected output: ${OUT%%$'\n'*}" ;;
    esac
  done
fi

# --- story project hint (informational) ---------------------------------------
WORK_DIR="$(pwd)"
if [ -d "$WORK_DIR/characters" ] || [ -d "$WORK_DIR/chapters" ]; then
  ok "story project markers in current directory"
else
  line "story project markers in current directory" "INFO — run Codex inside your writing project (characters/, chapters/, story-planning/); the analyzers take that directory as '.' "
fi

echo "== summary: $PASS ok, $WARN warn, $FAIL fail =="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
