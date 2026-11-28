#!/bin/bash
# setup.sh — environment health check for the glm-study-buddy skill.
# Checks only; installs nothing.
#
# glm-study-buddy is a workflow skill (no payload of its own beyond docs),
# but it orchestrates two skills in the glm-web plugin (glm-web-search / glm-web-reader
# CLIs need python3) and optionally the codex CLI for launchd/crontab
# timers. Missing glm-web skills are WARN (degraded mode exists), not FAIL.
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

echo "== glm-study-buddy environment check =="

# --- python interpreter (glm-web skill CLIs) ---------------------------------
PY="${GLM_STUDY_BUDDY_PYTHON:-python3}"
if command -v "$PY" >/dev/null 2>&1; then
  PY_VER="$("$PY" --version 2>&1)"
  ok "python interpreter ($PY)" " ($PY_VER)"
else
  fail "python interpreter ($PY)" "not found; set GLM_STUDY_BUDDY_PYTHON to a python3 path"
fi

# --- skill structure --------------------------------------------------------
REFS="reporting.md tooling.md user-md-schema.md"
MISSING_REF=""
for r in $REFS; do
  [ -f "$SKILL_DIR/references/$r" ] || MISSING_REF="$MISSING_REF $r"
done
if [ -z "$MISSING_REF" ]; then
  ok "skill structure (SKILL.md + 3 references)"
else
  fail "skill structure" "missing references:$MISSING_REF — reinstall the plugin tarball"
fi

# --- glm-web plugin skills (WARN-level: degraded mode exists) ----------------
PLUGINS_DIR="${CODEX_PLUGINS_DIR:-$HOME/.codex/plugins}"
SIB_SEARCH="$PLUGINS_DIR/glm-web/skills/glm-web-search/scripts/glmws.py"
SIB_READER="$PLUGINS_DIR/glm-web/skills/glm-web-reader/scripts/glmwr.py"
if [ -f "$SIB_SEARCH" ]; then
  ok "glm-web skill glm-web-search" "(glmws.py found)"
else
  warn "glm-web skill glm-web-search" "glmws.py not at $SIB_SEARCH; search (iron rule 1) degrades to 'ask user to paste material'"
fi
if [ -f "$SIB_READER" ]; then
  ok "glm-web skill glm-web-reader" "(glmwr.py found)"
else
  warn "glm-web skill glm-web-reader" "glmwr.py not at $SIB_READER; link-material capture (step 1.5) degrades to 'ask user to paste material'"
fi

# --- codex CLI (timers via launchd/crontab + codex exec) --------------------
if command -v codex >/dev/null 2>&1; then
  ok "codex CLI" "(timer path available: launchd/crontab + codex exec)"
else
  warn "codex CLI" "not on PATH; launchd/crontab timers cannot be configured — use the manual form (say 'morning briefing' to the model)"
fi

# --- workspace files hint (informational) -----------------------------------
WORK_DIR="$(pwd)"
if [ -f "$WORK_DIR/USER.md" ]; then
  ok "USER.md in current directory"
else
  line "USER.md in current directory" "INFO — will be created on first project generation (run Codex in your study workspace)"
fi

echo "== summary: $PASS ok, $WARN warn, $FAIL fail =="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
