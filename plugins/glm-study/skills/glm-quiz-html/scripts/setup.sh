#!/usr/bin/env bash
# glm-quiz-html — environment check (offline, pure-stdlib payload)
# Usage: bash ~/.codex/plugins/glm-study/skills/glm-quiz-html/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-quiz-html"
PY="${GLM_QUIZHTML_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_QUIZHTML_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/build_quiz_html.py templates/quiz_template.html; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "generator self-test (no args -> argparse exit 2)"
out="$("$PY" "$SKILL_DIR/scripts/build_quiz_html.py" 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "usage self-test exit 2 as designed (argparse missing-arg contract)"
else
  bad "expected exit 2 without args, got $rc"
fi

section "generator self-test (bad json -> exit 2)"
tmp="$(mktemp)"
printf 'not-a-json' > "$tmp"
out="$("$PY" "$SKILL_DIR/scripts/build_quiz_html.py" "$tmp" 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "bad-json self-test exit 2 as designed"
else
  bad "expected exit 2 for invalid json, got $rc"
fi
rm -f "$tmp"

section "template placeholders"
for ph in '{{TITLE}}' '{{SUBTITLE}}' '{{QUIZ_DATA}}' '{{META}}'; do
  if grep -q "$ph" "$SKILL_DIR/templates/quiz_template.html" 2>/dev/null; then
    good "placeholder $ph found"
  else
    bad "placeholder $ph missing in template"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
exit 0
