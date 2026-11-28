#!/usr/bin/env bash
# ---
# name: glmcharts-setup
# author: Z.AI
# version: "1.1"
# description: Environment setup for the glmcharts skill. Non-interactive safe.
#   Usage: bash setup.sh [--no-install]
#   Interpreter resolution (first match wins):
#     1. GLMCHARTS_PYTHON   fixed interpreter (must exist, otherwise exit 1)
#     2. PYTHON_BIN        fallback interpreter (must exist)
#     3. python3           from PATH
#   Chromium binaries are looked up in PLAYWRIGHT_BROWSERS_PATH when set,
#   otherwise the OS default cache (~/.cache/ms-playwright or
#   ~/Library/Caches/ms-playwright).
# ---
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
warn() { echo -e "  ${YELLOW}○${NC} $1"; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

NO_INSTALL=0
for arg in "$@"; do
    case "$arg" in
        --no-install) NO_INSTALL=1 ;;
        *) warn "unknown option: $arg" ;;
    esac
done

echo "============================================"
echo "  glmcharts — Environment Setup"
[ "$NO_INSTALL" = "1" ] && echo "  (check only, --no-install)"
echo "============================================"
echo ""

OS="$(uname -s)"
ARCH="$(uname -m)"
echo "Platform: $OS $ARCH"
echo ""

HARD_ERRORS=0

# ── 0. Resolve the Python interpreter (3 levels) ──
echo "--- Python interpreter ---"
PY=""
if [ -n "${GLMCHARTS_PYTHON:-}" ]; then
    if [ ! -x "$GLMCHARTS_PYTHON" ]; then
        fail "GLMCHARTS_PYTHON=$GLMCHARTS_PYTHON does not exist or is not executable"
        info "Fix the variable, or unset it to fall back to PATH python3."
        exit 1
    fi
    PY="$GLMCHARTS_PYTHON"
    ok "using GLMCHARTS_PYTHON ($PY)"
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

# ── 1. Python packages (matplotlib / seaborn / numpy / adjustText / playwright) ──
echo "--- Python packages (all render frameworks) ---"
PY_PKGS=(
    "matplotlib:matplotlib"
    "seaborn:seaborn"
    "numpy:numpy"
    "adjustText:adjustText"
    "playwright:playwright"
)

MISSING=()
for entry in "${PY_PKGS[@]}"; do
    mod="${entry%%:*}"
    pkg="${entry##*:}"
    if "$PY" -c "import $mod" >/dev/null 2>&1; then
        ver="$("$PY" -c "import $mod; print(getattr($mod, '__version__', 'installed'))" 2>/dev/null)"
        ok "$pkg ($ver)"
    else
        fail "$pkg not installed"
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    if [ "$NO_INSTALL" = "1" ]; then
        warn "--no-install set: not installing. Missing: ${MISSING[*]}"
    else
        info "installing missing packages into: $PY"
        if "$PY" -m pip install -q "${MISSING[@]}" >/dev/null 2>&1; then
            ok "installed via pip: ${MISSING[*]}"
        elif "$PY" -m pip install -q --user "${MISSING[@]}" >/dev/null 2>&1; then
            ok "installed via pip --user: ${MISSING[*]}"
        elif "$PY" -m pip install -q --break-system-packages "${MISSING[@]}" >/dev/null 2>&1; then
            ok "installed via pip --break-system-packages: ${MISSING[*]}"
        elif command -v uv >/dev/null 2>&1 \
             && uv pip install --python "$PY" "${MISSING[@]}" >/dev/null 2>&1; then
            ok "installed via uv pip --python (venv without pip): ${MISSING[*]}"
        else
            fail "auto-install failed for: ${MISSING[*]}"
            info "Try manually:  $PY -m pip install ${MISSING[*]}"
            info "Or with uv:    uv pip install --python $PY ${MISSING[*]}"
            HARD_ERRORS=$((HARD_ERRORS + 1))
        fi
    fi
fi
echo ""

# ── 2. Chromium binaries for Playwright ──
echo "--- Playwright Chromium (structural diagrams) ---"
if [ -n "${PLAYWRIGHT_BROWSERS_PATH:-}" ]; then
    PW_BROWSERS="$PLAYWRIGHT_BROWSERS_PATH"
    [ -d "$PW_BROWSERS" ] || warn "PLAYWRIGHT_BROWSERS_PATH=$PW_BROWSERS does not exist yet"
else
    case "$OS" in
        Darwin) PW_BROWSERS="$HOME/Library/Caches/ms-playwright" ;;
        *)      PW_BROWSERS="$HOME/.cache/ms-playwright" ;;
    esac
fi
info "browsers directory: $PW_BROWSERS"

CR_DIR="$(ls -d "$PW_BROWSERS"/chromium-* 2>/dev/null | tail -1 || true)"
SH_DIR="$(ls -d "$PW_BROWSERS"/chromium_headless_shell-* 2>/dev/null | tail -1 || true)"

if [ -n "$CR_DIR" ] && [ -n "$SH_DIR" ]; then
    ok "chromium ($(basename "$CR_DIR")) + headless shell ($(basename "$SH_DIR"))"
elif [ -n "$SH_DIR" ]; then
    ok "chromium headless shell only ($(basename "$SH_DIR")) — enough for headless screenshots"
elif [ -n "$CR_DIR" ]; then
    warn "chromium present ($(basename "$CR_DIR")) but headless shell missing"
    info "playwright >= 1.49 launches headless via chromium_headless_shell; install with:"
    info "  PLAYWRIGHT_BROWSERS_PATH=... $PY -m playwright install chromium"
else
    fail "no chromium binaries found"
    info "Install:  $PY -m playwright install chromium"
    info "China mirror (optional):"
    info "  PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright \\"
    info "    $PY -m playwright install chromium"
    if [ "$OS" = "Linux" ]; then
        info "System libs (needs sudo): $PY -m playwright install-deps chromium"
    fi
    HARD_ERRORS=$((HARD_ERRORS + 1))
fi
echo ""

# ── 3. Node.js (optional: only for mermaid-cli / mmdc) ──
echo "--- Node.js (optional, mermaid-cli only) ---"
if command -v node >/dev/null 2>&1; then
    ok "node ($(node --version)) — templates render via Python Playwright; node is optional"
else
    warn "node not found — optional (only needed for mermaid-cli / mmdc)"
fi
echo ""

# ── 4. CJK fonts (Chinese labels) ──
echo "--- CJK fonts (Chinese text in charts) ---"
CJK_FOUND=false
if "$PY" -c "
import matplotlib.font_manager as fm
fonts = [f.name for f in fm.fontManager.ttflist]
if 'SimHei' in fonts or 'Heiti SC' in fonts or 'Noto Sans CJK' in fonts or 'PingFang SC' in fonts or 'Noto Sans SC' in fonts:
    print('ok')
else:
    print('missing')
" 2>/dev/null | grep -q "ok"; then
    ok "CJK font registered in matplotlib"
    CJK_FOUND=true
fi
if [ "$CJK_FOUND" = false ]; then
    if [ "$OS" = "Darwin" ]; then
        if ls /System/Library/Fonts/PingFang.ttc >/dev/null 2>&1; then
            ok "macOS CJK system fonts available (PingFang)"
            CJK_FOUND=true
        fi
    elif fc-list :lang=zh >/dev/null 2>&1 && fc-list :lang=zh 2>/dev/null | head -1 | grep -q .; then
        ok "system CJK fonts available (fc-list)"
        CJK_FOUND=true
    fi
fi
if [ "$CJK_FOUND" = false ]; then
    warn "No CJK font detected — Chinese labels may render as boxes"
    if [ "$OS" = "Darwin" ]; then
        info "macOS ships with PingFang — usually fine after matplotlib font cache rebuild"
    else
        info "Install: sudo apt install fonts-noto-cjk"
    fi
fi
echo ""

# ── Summary ──
echo "============================================"
if [ "$HARD_ERRORS" -gt 0 ]; then
    echo "  Setup finished with $HARD_ERRORS blocking issue(s)."
    echo "  Data charts: matplotlib + seaborn + numpy + adjustText"
    echo "  Structural diagrams: Python Playwright + Chromium"
    echo "============================================"
    exit 1
fi
echo "  Setup complete. Interpreter: $PY"
echo "  Data charts: matplotlib + seaborn + numpy + adjustText"
echo "  Structural diagrams: Python Playwright + Chromium"
echo "  Interactive: ECharts / D3.js (rendered headless via Playwright)"
echo "============================================"
