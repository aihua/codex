#!/usr/bin/env bash
# glm-interview-designer — environment check (offline, pure-documentation skill)
# Usage: bash ~/.codex/plugins/glm-career/skills/glm-interview-designer/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-interview-designer"
PY="${GLM_INTERVIEW_DESIGNER_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter (setup self-check only)"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_INTERVIEW_DESIGNER_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh references/design_rationale.md \
         references/upstream-README.md templates/interview_guide_template.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done
if [ -f "$SKILL_DIR/_meta.json" ]; then
  bad "_meta.json (upstream market metadata) must not ship"
else
  good "upstream market metadata (_meta.json) not shipped"
fi

section "interview guide template sanity"
TPL="$SKILL_DIR/templates/interview_guide_template.md"
for anchor in "{Candidate_Name}" "Competency Scorecard" "Red Flags" "Green Signals" \
              "Pressure Validation" "Future Projection"; do
  if grep -q "$anchor" "$TPL"; then
    good "template anchor present: $anchor"
  else
    bad "template anchor missing: $anchor"
  fi
done

section "design rationale sanity"
DR="$SKILL_DIR/references/design_rationale.md"
for anchor in "Geoff Smart" "Lou Adler" "Kahneman"; do
  if grep -q "$anchor" "$DR"; then
    good "critique anchor present: $anchor"
  else
    bad "critique anchor missing: $anchor"
  fi
done

section "host-residue self-check"
if grep -rqE "mcp__cowork__create_artifact|AskUserQuestion|z-ai|web-dev-sdk|clawdbot|thesethrose" \
     "$SKILL_DIR/SKILL.md" "$DR" "$TPL" 2>/dev/null; then
  bad "host tool/SDK residue found"
else
  good "payload free of host tool/SDK references (upstream-README is documentary)"
fi

section "knowledge anchors"
for anchor in "Scorecard" "Forensic" "Future Simulation" "Red Flags" \
              "Green Signals" "interview_guide_template.md" \
              "design_rationale.md" "upstream-README.md" \
              "Codex Deployment Notes" "pdftotext" "glm-interview-prep" \
             ; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "the generated interview guide lands in the user working directory; plugin dir read-only."
exit 0
