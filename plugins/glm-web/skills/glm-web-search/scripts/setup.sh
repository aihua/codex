#!/usr/bin/env bash
# ---
# name: glm-web-search-setup
# author: Z.AI
# version: "1.1.2"
# description: Environment check for the glm-web-search skill. Non-interactive,
#   safe, zero third-party dependencies (nothing to install).
#   Usage: bash setup.sh [--skip-net | --no-install]
#   Interpreter resolution (first match wins):
#     1. GLM_WEB_SEARCH_PYTHON  fixed interpreter (must exist, otherwise exit 1)
#     2. PYTHON_BIN            fallback interpreter (must exist)
#     3. python3               from PATH
#   Network probe (unless --skip-net/--no-install): a real one-shot search
#   through the engine chain Bing -> DuckDuckGo HTML -> DuckDuckGo Lite.
#   Ollama is NOT used by this skill: search traffic goes directly from
#   this shell to the engines, never through the model server.
# ---
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
warn() { echo -e "  ${YELLOW}○${NC} $1"; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

SKIP_NET=0
for arg in "$@"; do
    case "$arg" in
        --skip-net|--no-install) SKIP_NET=1 ;;
        *) warn "unknown option: $arg" ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "  glm-web-search — Environment Check"
[ "$SKIP_NET" = "1" ] && echo "  (basic checks only, network probe skipped)"
echo "============================================"
echo ""

OS="$(uname -s)"
echo "Platform: $OS  (zero third-party dependencies)"
echo ""

HARD_ERRORS=0

# ── 0. Resolve the Python interpreter (3 levels) ──
echo "--- Python interpreter ---"
PY=""
if [ -n "${GLM_WEB_SEARCH_PYTHON:-}" ]; then
    if [ ! -x "$GLM_WEB_SEARCH_PYTHON" ]; then
        fail "GLM_WEB_SEARCH_PYTHON=$GLM_WEB_SEARCH_PYTHON does not exist or is not executable"
        info "Fix the variable, or unset it to fall back to PATH python3."
        exit 1
    fi
    PY="$GLM_WEB_SEARCH_PYTHON"
    ok "using GLM_WEB_SEARCH_PYTHON ($PY)"
elif [ -n "${PYTHON_BIN:-}" ]; then
    if [ ! -x "$PYTHON_BIN" ]; then
        fail "PYTHON_BIN=$PYTHON_BIN does not exist or is not executable"
        info "Fix the variable, or unset it to fall back to PATH python3."
        exit 1
    fi
    PY="$PYTHON_BIN"
    ok "using PYTHON_BIN ($PY)"
elif command -v python3 >/dev/null 2>&1; then
    PY="$(command -v python3)"
    ok "using PATH python3 ($PY)"
else
    fail "no python3 found on PATH"
    info "Install: brew install python3 (macOS) / sudo apt install python3 (Debian/Ubuntu)"
    exit 1
fi
PY_VER="$("$PY" --version 2>&1)"
ok "python ($PY_VER)"
echo ""

# ── 1. glmws.py self-check (compile + --help) ──
echo "--- glmws.py self-check ---"
if [ ! -f "$SCRIPT_DIR/glmws.py" ]; then
    fail "glmws.py not found next to setup.sh ($SCRIPT_DIR)"
    exit 1
fi
if "$PY" -m py_compile "$SCRIPT_DIR/glmws.py" >/dev/null 2>&1; then
    ok "glmws.py compiles cleanly"
else
    fail "glmws.py does not compile with $PY_VER"
    HARD_ERRORS=$((HARD_ERRORS + 1))
fi
if "$PY" "$SCRIPT_DIR/glmws.py" --help >/dev/null 2>&1; then
    ok "glmws.py --help exits 0"
else
    fail "glmws.py --help failed"
    HARD_ERRORS=$((HARD_ERRORS + 1))
fi
echo ""

# ── 2. Network / search engine probe ──
echo "--- Search engine connectivity ---"
if [ "$SKIP_NET" = "1" ]; then
    warn "skipped (--skip-net / --no-install)"
else
    PROBE_OUT="$("$PY" "$SCRIPT_DIR/glmws.py" search "connectivity probe" --num 1 --timeout 8 2>&1)"
    PROBE_RC=$?
    if [ "$PROBE_RC" = "0" ]; then
        ENGINE="$(printf '%s\n' "$PROBE_OUT" | grep -m1 '^engine:' || true)"
        ok "search engine reachable via engine chain (${ENGINE:-bing first})"
        info "exit code 0, results returned"
    elif [ "$PROBE_RC" = "2" ]; then
        fail "no search engine reachable (Bing and DuckDuckGo both failed)"
        info "Check: curl -I https://www.bing.com   # basic connectivity"
        info "If YOUR terminal reaches bing.com but this failed (e.g. run inside"
        info "Codex), the Codex command sandbox blocks network; fix in config.toml:"
        info "  sandbox_mode=\"workspace-write\" + network_access=true, restart Codex"
        info "Layered report: glmws.py diagnose   (details: references/fallback.md)"
        info "Corporate proxy: export HTTPS_PROXY=http://host:port"
        info "Note: DuckDuckGo is unreachable from most mainland CN networks;"
        info "      Bing HTML is the primary engine there and worked in tests."
        HARD_ERRORS=$((HARD_ERRORS + 1))
    else
        warn "engines reachable but the probe query returned no results (rc=1)"
        info "Usually transient; rerun setup.sh or try a different query."
    fi
fi
echo ""

# ── Summary ──
echo "============================================"
if [ "$HARD_ERRORS" -gt 0 ]; then
    echo "  Setup finished with $HARD_ERRORS blocking issue(s)."
    echo "  Required: python3 only. Search engine: at least one reachable."
    echo "============================================"
    exit 1
fi
echo "  Setup complete. Interpreter: $PY"
echo "  Dependencies: none (pure Python standard library)"
echo "  Engines: Bing HTML -> DuckDuckGo HTML -> DuckDuckGo Lite"
echo "  Ollama: not used by this skill - search goes directly to the engines"
echo "============================================"
