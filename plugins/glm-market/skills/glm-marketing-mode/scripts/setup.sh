#!/usr/bin/env bash
# glm-marketing-mode — environment check (pure knowledge payload, zero runtime)
# Usage: bash ~/.codex/plugins/glm-market/skills/glm-marketing-mode/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-marketing-mode"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "skill structure"
for f in SKILL.md references/mode-prompt.md scripts/setup.sh; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "knowledge base completeness"
SKILL_LINES=$(wc -l < "$SKILL_DIR/SKILL.md" | tr -d ' ')
if [ "$SKILL_LINES" -ge 600 ]; then
  good "SKILL.md knowledge body intact ($SKILL_LINES lines >= 600)"
else
  bad "SKILL.md knowledge body shrank ($SKILL_LINES lines < 600)"
fi
for anchor in "PART 1: MARKETING STRATEGY" "PART 2: PSYCHOLOGY" "PART 3: SEO & CONTENT" \
              "PART 4: CONVERSION OPTIMIZATION" "PART 5: PAID ADVERTISING" "PART 6: EMAIL MARKETING" \
              "QUICK REFERENCE"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "section present: $anchor"
  else
    bad "section missing: $anchor"
  fi
done

section "host-residue self-check"
if grep -qiE "clawdbot|clawdhub|thesethrose|npm install|ownerId" "$SKILL_DIR/SKILL.md" \
     "$SKILL_DIR/references/mode-prompt.md" 2>/dev/null; then
  bad "host residue found in payload"
else
  good "payload free of host-platform references"
fi

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "pure knowledge payload: zero runtime, zero network, no interpreter needed"
exit 0
