#!/bin/bash
# setup.sh — environment health check for the glm-version-management skill.
# Checks only; installs nothing.
#
# glm-version-management is a workflow skill whose only executable dependency
# is git (version tree + tags drive the whole V{n} lifecycle). Missing git is
# FAIL (no degraded mode exists). No network checks: the payload has zero
# network endpoints by design.
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

echo "== glm-version-management environment check =="

# --- git (core dependency) ---------------------------------------------------
if command -v git >/dev/null 2>&1; then
  GIT_VER="$(git --version 2>&1)"
  ok "git" "($GIT_VER)"
else
  fail "git" "not found; install git first — the whole V{n} lifecycle depends on it"
fi

# --- git identity (informational; commits need user.name/user.email) ---------
if command -v git >/dev/null 2>&1; then
  if [ -n "$(git config --global user.name 2>/dev/null)" ] || \
     [ -n "$(git config --global user.email 2>/dev/null)" ]; then
    ok "git identity (user.name/user.email)"
  else
    warn "git identity (user.name/user.email)" "not configured; first commit in a project will fail — set via 'git config --global user.name ...' if that happens"
  fi
fi

# --- skill structure ----------------------------------------------------------
REFS="project-conventions.md version-operations.md"
MISSING_REF=""
for r in $REFS; do
  [ -f "$SKILL_DIR/references/$r" ] || MISSING_REF="$MISSING_REF $r"
done
if [ -z "$MISSING_REF" ] && [ -f "$SKILL_DIR/SKILL.md" ]; then
  ok "skill structure (SKILL.md + 2 references)"
else
  fail "skill structure" "missing:$MISSING_REF — reinstall the plugin tarball"
fi

# --- design co-skills in this plugin (INFO-level: optional, auto-degrade) -----
PLUGINS_DIR="${CODEX_PLUGINS_DIR:-$HOME/.codex/plugins}"
for sib in glm-visual-design-foundations glm-ui-ux-pro-max; do
  if [ -d "$PLUGINS_DIR/glm-design/skills/$sib" ]; then
    ok "design co-skill $sib (glm-design)" "(quality discipline active)"
  else
    line "design co-skill $sib (glm-design)" "INFO — not loaded; quality step auto-skipped, version flow unchanged"
  fi
done

# --- workspace hint (informational) ------------------------------------------
WORK_DIR="$(pwd)"
if [ -d "$WORK_DIR/我的项目" ]; then
  ok "我的项目/ in current directory"
else
  line "我的项目/ in current directory" "INFO — will be created when the first web project is generated (run Codex in your web workspace)"
fi

echo "== summary: $PASS ok, $WARN warn, $FAIL fail =="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
