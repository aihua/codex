#!/usr/bin/env bash
# glm-seo-content-writer — environment check (offline, pure-stdlib auditor)
# Usage: bash ~/.codex/plugins/glm-content/skills/glm-seo-content-writer/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-seo-content-writer"
PY="${GLM_SEO_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_SEO_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/seocheck.py \
         references/title-formulas.md references/content-structure-templates.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "auditor syntax + self-tests"
if "$PY" -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" \
     "$SKILL_DIR/scripts/seocheck.py" 2>/dev/null; then
  good "seocheck.py syntax ok (in-memory compile, no bytecode written)"
else
  bad "seocheck.py syntax error"
fi

# missing-file error path -> exit 1
if "$PY" "$SKILL_DIR/scripts/seocheck.py" /nonexistent/x.md >/dev/null 2>&1; then
  bad "missing-file should exit 1"
else
  good "missing-file self-test: exit 1"
fi

# known-good audit fixture: every deterministic check must fire
FIX="$(mktemp /tmp/glmseo_XXXX.md)"
cat > "$FIX" <<'MDEOF'
# Email Marketing Best Practices for Small Businesses

Want to know the secret behind consistent email results? It is strategy. Email delivers strong ROI for small teams when done right. This guide covers the full email marketing playbook.

## Why Email Marketing Matters

Direct channel access matters. Algorithms do not control your reach. You own the list and the relationship with every subscriber on it.

## Building a High-Quality Email List

### Use Strategic Opt-in Incentives

Offer templates and checklists that solve immediate problems.

### Implement Double Opt-in

Confirm intent and improve deliverability with a double opt-in flow.

### Nurture New Subscribers

Send a welcome sequence that teaches value and sets expectations.

## Frequently Asked Questions

### How often should small businesses send emails?

One to two emails per week is the sweet spot for most small businesses.

### What is a good open rate?

Twenty to twenty-five percent is good; track your own benchmark instead.

### Should I buy an email list?

Never; purchased lists damage sender reputation and violate regulations.

## Conclusion

These email marketing best practices compound over time. [Internal guide](/guides/email) and [Litmus](https://litmus.com) and [Campaign Monitor](https://campaignmonitor.com) provide further reading.
MDEOF
OUT="$("$PY" "$SKILL_DIR/scripts/seocheck.py" "$FIX" --keyword "email marketing" \
      --meta "Discover proven email marketing best practices that help small businesses increase open rates and drive sales. Start improving today." \
      --format json 2>/dev/null)"
RC=$?
if [ "$RC" -eq 0 ]; then
  good "audit self-test exit 0"
else
  bad "audit self-test rc=$RC"
fi
for probe in "title_len" "meta_len" "h1_unique" "kw_h1" "kw_first100" "kw_h2" \
             "faq" "chunking" "words" "links" "density" "overall_score"; do
  if echo "$OUT" | grep -q "\"$probe\""; then
    good "check fires: $probe"
  else
    bad "check missing from report: $probe"
  fi
done
if echo "$OUT" | grep -q '"overall_score": 1[0-9]*\.0\|10\.0'; then
  good "fixture scores a full pass"
fi
rm -f "$FIX"

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
exit 0
