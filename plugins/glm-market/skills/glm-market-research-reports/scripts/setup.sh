#!/usr/bin/env bash
# glm-market-research-reports — environment check + CLI contract drill (offline)
# Usage: bash ~/.codex/plugins/glm-market/skills/glm-market-research-reports/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-market-research-reports"
GEN="$SKILL_DIR/scripts/generate_market_visuals.py"
PY="${GLM_MARKET_REPORTS_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_MARKET_REPORTS_PYTHON to fix)"
fi

section "matplotlib runtime"
if "$PY" -c "import matplotlib" 2>/dev/null; then
  good "matplotlib importable"
else
  bad "matplotlib missing — install with: uv pip install matplotlib"
fi

section "skill structure"
for f in SKILL.md scripts/generate_market_visuals.py scripts/setup.sh \
         references/report_structure_guide.md references/data_analysis_patterns.md \
         references/visual_generation_guide.md assets/FORMATTING_GUIDE.md \
         assets/market_research.sty assets/market_report_template.tex; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "CLI contract drills"
out="$("$PY" "$GEN" --list 2>/dev/null)"; rc=$?
if [ "$rc" -eq 0 ] && [ "$(printf '%s\n' "$out" | grep -c '\.png')" -eq 18 ]; then
  good "--list exit 0, catalogue lists 18 visuals"
else
  bad "--list drill unexpected (rc=$rc)"
fi

"$PY" "$GEN" >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 2 ]; then
  good "no-args usage drill exit 2 as designed"
else
  bad "expected exit 2 without args, got $rc"
fi

printf '%s' '{"broken' > /tmp/_glmmrr_bad.json
"$PY" "$GEN" --topic X --output-dir /tmp/_glmmrr_bad_out --data /tmp/_glmmrr_bad.json >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 2 ]; then
  good "bad --data JSON drill exit 2 as designed"
else
  bad "expected exit 2 for malformed --data, got $rc"
fi

section "render drill (core 6, watermarked demo)"
TMPD="$(mktemp -d)"
if "$PY" "$GEN" --topic "Setup Drill" --output-dir "$TMPD" >/dev/null 2>&1; then
  n=$(find "$TMPD" -name '*.png' | wc -l | tr -d ' ')
  if [ "$n" -eq 6 ]; then
    good "core render drill produced 6 PNGs"
    smallost=$(find "$TMPD" -name '*.png' -size -2k | wc -l | tr -d ' ')
    [ "$smallost" -eq 0 ] && good "no suspiciously small (<2k) renders" \
                          || bad "suspiciously small renders: $smallost"
  else
    bad "core render drill produced $n PNGs (expected 6)"
  fi
else
  bad "core render drill failed"
fi
rm -rf "$TMPD" /tmp/_glmmrr_bad.json /tmp/_glmmrr_bad_out

section "host-residue self-check"
if grep -rqE "scientific-schematics/scripts|generate-image/scripts|research_lookup\.py|generate_schematic\.py|generate_image\.py" \
     "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references/visual_generation_guide.md" 2>/dev/null; then
  bad "host sibling-tool invocation residue found"
else
  good "payload free of host sibling-tool invocations"
fi

section "knowledge anchors"
for anchor in "Porter's Five Forces" "PESTLE" "TAM/SAM/SOM" "BCG Matrix" \
              "50+ pages" "writing_outputs" "generate_market_visuals.py"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "LaTeX compile (xelatex/bibtex) runs on the user machine (MacTeX/tectonic)."
note "web data gathering routes to the glm-web-search plugin when installed."
exit 0
