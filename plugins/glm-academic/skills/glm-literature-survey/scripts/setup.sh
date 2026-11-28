#!/usr/bin/env bash
# glm-literature-survey — environment check (offline: structure + template
# integrity + slug-CLI contract + host-residue audit)
# Usage: bash ~/.codex/plugins/glm-academic/skills/glm-literature-survey/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-literature-survey"
PY="${GLM_LITERATURE_SURVEY_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_LITERATURE_SURVEY_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh \
         references/00-incremental-execution.md references/01-bibliography-expansion.md \
         references/02-survey-figures.md references/03-survey-section-playbook.md \
         references/04-layout-discipline.md references/05-quality-gate.md \
         templates/survey/main.tex templates/survey/compile.sh; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "template integrity"
if grep -q '\\documentclass' "$SKILL_DIR/templates/survey/main.tex" && \
   grep -q 'bibliography' "$SKILL_DIR/templates/survey/main.tex"; then
  good "main.tex has documentclass + bibliography wiring"
else
  bad "main.tex missing documentclass/bibliography"
fi
if bash -n "$SKILL_DIR/templates/survey/compile.sh" 2>/dev/null; then
  good "compile.sh passes bash -n syntax check"
else
  bad "compile.sh syntax error"
fi

section "slug CLI contract (Step 2 command verbatim)"
SLUG=$("$PY" -c "import re,hashlib,sys; t=sys.argv[1]; n=re.sub(r'[\\s_]+','-',re.sub(r'[^\\w\\s-]','',t.lower().strip())).strip('-')[:40].rstrip('-'); h=hashlib.sha1(t.encode()).hexdigest()[:8]; print(f'{n}-{h}')" "federated learning in healthcare" 2>/dev/null); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$SLUG" | grep -qE '^[a-z0-9-]+-[0-9a-f]{8}$'; then
  good "slug command contract ok (e.g. '$SLUG')"
else
  bad "slug command contract broken (rc=$rc, slug='$SLUG')"
fi

section "host-residue self-check"
if grep -rqE "search_papers\(|get_paper_details\(|z-ai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR/SKILL.md"; then
  bad "host tool/SDK invocation residue found in SKILL.md"
else
  good "SKILL.md free of host tool/SDK invocations"
fi
if grep -q "工具名映射" "$SKILL_DIR/references/00-incremental-execution.md" && \
   grep -q "工具名映射" "$SKILL_DIR/references/01-bibliography-expansion.md" && \
   grep -q "工具名映射" "$SKILL_DIR/references/05-quality-gate.md"; then
  good "tool-name mapping preamble present in 00/01/05"
else
  bad "tool-name mapping preamble missing"
fi

section "knowledge anchors"
for anchor in "60+ real citations" "incremental" "taxonomy" "timeline" \
              "bibliography.bib" "quality-gate" "literature_table.md" \
              "s2_search.py" "glmws.py" "Codex Deployment Notes"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
note "academic search routes to glm-research-explorer s2_search.py; web search"
note "and page fetch route to glm-web-search glmws.py (sibling glm plugins)."
note "pdflatex/bibtex compile runs on the user machine (MacTeX/tectonic)."
exit 0
