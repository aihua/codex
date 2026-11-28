#!/bin/bash
# setup.sh — environment health check for the glm-web-shader-extractor skill.
# Checks only; installs nothing (first run of fetch-rendered-dom.mjs performs
# the one-time Playwright setup on demand).
#
# Usage: bash setup.sh [--skip-net]

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

PASS=0; WARN=0; FAIL=0
line() { printf '  %-42s %s\n' "$1" "$2"; }
ok()   { line "$1" "OK${2:+ $2}"; PASS=$((PASS+1)); }
warn() { line "$1" "WARN — $2"; WARN=$((WARN+1)); }
fail() { line "$1" "FAIL — $2"; FAIL=$((FAIL+1)); }

echo "== glm-web-shader-extractor environment check =="

# --- node (rendered-DOM path) -----------------------------------------------
if command -v node >/dev/null 2>&1; then
  NODE_VER="$(node --version 2>/dev/null)"
  case "$NODE_VER" in
    v18.*|v19.*|v2[0-9].*) ok "node" " ($NODE_VER)";;
    *) warn "node" "found $NODE_VER, prefer >= 18 for Playwright";;
  esac
else
  warn "node" "not found; rendered-DOM capture unavailable, curl-only fallback works"
fi

# --- python3 (extractor path) ----------------------------------------------
PY="${GLM_SHADER_EXTRACTOR_PYTHON:-python3}"
if command -v "$PY" >/dev/null 2>&1; then
  PY_VER="$("$PY" --version 2>&1)"
  ok "python interpreter ($PY)" " ($PY_VER)"
else
  fail "python interpreter ($PY)" "not found; set GLM_SHADER_EXTRACTOR_PYTHON to a python3 path"
fi

# --- curl -------------------------------------------------------------------
if command -v curl >/dev/null 2>&1; then ok "curl"; else fail "curl" "not found"; fi

# --- playwright resolution --------------------------------------------------
RUNNER_DIR="$HOME/.cache/playwright-runner"
GLOBAL_PW="no"
if command -v node >/dev/null 2>&1; then
  if node -e "import('playwright').then(()=>process.exit(0)).catch(()=>process.exit(1))" 2>/dev/null; then
    GLOBAL_PW="yes"
    ok "playwright" "globally importable"
  elif [ -d "$RUNNER_DIR/node_modules/playwright" ]; then
    ok "playwright" "cached in $RUNNER_DIR"
  else
    warn "playwright" "not installed yet; auto-installs on first fetch-rendered-dom.mjs run (pnpm preferred, npm fallback)"
  fi
else
  warn "playwright" "cannot probe without node"
fi

# --- chromium binaries ------------------------------------------------------
if [ -d "$HOME/.cache/ms-playwright" ] && ls "$HOME/.cache/ms-playwright" 2>/dev/null | grep -q chromium; then
  ok "chromium binaries" "present in ~/.cache/ms-playwright"
else
  if [ "$GLOBAL_PW" = "yes" ]; then
    warn "chromium binaries" "not in ~/.cache/ms-playwright; first fetch run installs them"
  else
    warn "chromium binaries" "not found; installed together with playwright"
  fi
fi

# --- extractor self-test (fast, offline) ------------------------------------
if command -v "$PY" >/dev/null 2>&1; then
  TMPB="$(mktemp -t glmwse-selftest-XXXX).js"
  printf 'const s="%s";\n' "precision mediump float;uniform float uTime;void main(){gl_FragColor=vec4(0.5);}" > "$TMPB"
  if "$PY" "$SCRIPT_DIR/extract-shaders.py" "$TMPB" --out "${TMPB%.js}-out" >/dev/null 2>&1; then
    ok "extract-shaders.py self-test"
  else
    fail "extract-shaders.py self-test" "returned non-zero on a minimal synthetic bundle"
  fi
  rm -f "$TMPB" "${TMPB%.js}-out"/shader-* "${TMPB%.js}-out"/summary.json
  rmdir "${TMPB%.js}-out" 2>/dev/null || true
fi

# --- network (optional) -----------------------------------------------------
if [ "${1:-}" = "--skip-net" ] || [ "${1:-}" = "--no-install" ]; then
  line "network probe" "skipped (--skip-net)"
else
  if command -v curl >/dev/null 2>&1; then
    if curl -s -m 8 -o /dev/null -I https://www.bing.com 2>/dev/null; then
      ok "network" "outbound HTTPS reachable"
    else
      warn "network" "no outbound HTTPS from this shell; if Codex sandbox blocks DNS, see references/fallback.md"
    fi
  fi
fi

echo "== summary: $PASS ok, $WARN warn, $FAIL fail =="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
