#!/usr/bin/env bash
# ---
# name: glm-web-reader-setup
# author: Z.AI
# version: "1.0.2"
# description: Environment check for the glm-web-reader skill. Non-interactive,
#   safe, zero third-party dependencies (nothing to install).
#   Usage: bash setup.sh [--skip-net | --no-install]
#   Interpreter resolution (first match wins):
#     1. GLM_WEB_READER_PYTHON  fixed interpreter (must exist, otherwise exit 1)
#     2. PYTHON_BIN            fallback interpreter (must exist)
#     3. python3               from PATH
#   Network probe (unless --skip-net/--no-install): one real page read of
#   https://www.bing.com through glmwr.py - the same path a question takes.
#   Ollama is NOT used by this skill: page traffic goes directly from
#   this shell to the site, never through the model server.
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
echo "  glm-web-reader — Environment Check"
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
if [ -n "${GLM_WEB_READER_PYTHON:-}" ]; then
    if [ ! -x "$GLM_WEB_READER_PYTHON" ]; then
        fail "GLM_WEB_READER_PYTHON=$GLM_WEB_READER_PYTHON does not exist or is not executable"
        info "Fix the variable, or unset it to fall back to PATH python3."
        exit 1
    fi
    PY="$GLM_WEB_READER_PYTHON"
    ok "using GLM_WEB_READER_PYTHON ($PY)"
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

# ── 1. glmwr.py self-check (compile + --help) ──
echo "--- glmwr.py self-check ---"
if [ ! -f "$SCRIPT_DIR/glmwr.py" ]; then
    fail "glmwr.py not found next to setup.sh ($SCRIPT_DIR)"
    exit 1
fi
if "$PY" -m py_compile "$SCRIPT_DIR/glmwr.py" >/dev/null 2>&1; then
    ok "glmwr.py compiles cleanly"
else
    fail "glmwr.py does not compile with $PY_VER"
    HARD_ERRORS=$((HARD_ERRORS + 1))
fi
if "$PY" "$SCRIPT_DIR/glmwr.py" --help >/dev/null 2>&1; then
    ok "glmwr.py --help exits 0"
else
    fail "glmwr.py --help failed"
    HARD_ERRORS=$((HARD_ERRORS + 1))
fi
echo ""

# ── 2. Network / page-read probe ──
echo "--- Page fetch connectivity ---"
if [ "$SKIP_NET" = "1" ]; then
    warn "skipped (--skip-net / --no-install)"
else
    PROBE_OUT="$("$PY" "$SCRIPT_DIR/glmwr.py" read https://www.bing.com --max-chars 200 --timeout 10 2>&1)"
    PROBE_RC=$?
    if [ "$PROBE_RC" = "0" ]; then
        TITLE="$(printf '%s\n' "$PROBE_OUT" | grep -m1 '^Title:' || true)"
        ok "page read works (probe: https://www.bing.com ${TITLE:-redirects fine})"
        info "exit code 0, text extracted"
    elif [ "$PROBE_RC" = "1" ]; then
        warn "network reachable but the probe page yielded no text (rc=1)"
        info "Bing markup may have changed, or the page redirected oddly;"
        info "try a real URL from a question - rc=1 is page-specific, not setup."
    else
        fail "page fetch unreachable (network error, exit 2)"
        info "Check: curl -I https://www.bing.com   # basic connectivity"
        info "If YOUR terminal reaches bing.com but this failed (e.g. run inside"
        info "Codex), the Codex command sandbox blocks network; fix in config.toml:"
        info "  sandbox_mode=\"workspace-write\" + network_access=true, restart Codex"
        info "  macOS caveat: network_access can be silently ignored (seatbelt);"
        info "  then start codex with --sandbox danger-full-access"
        info "Layered report: glmwr.py diagnose   (details: references/fallback.md)"
        info "Corporate proxy: export HTTPS_PROXY=http://host:port"
        HARD_ERRORS=$((HARD_ERRORS + 1))
    fi
fi
echo ""

# ── Summary ──
echo "============================================"
if [ "$HARD_ERRORS" -gt 0 ]; then
    echo "  Setup finished with $HARD_ERRORS blocking issue(s)."
    echo "  Required: python3 only. Network: outbound HTTPS to target pages."
    echo "============================================"
    exit 1
fi
echo "  Setup complete. Interpreter: $PY"
echo "  Dependencies: none (pure Python standard library)"
echo "  Reads: any http(s) URL - HTML pages, RSS/Atom feeds, JSON endpoints"
echo "  Ollama: not used by this skill - pages are fetched directly"
echo "============================================"
