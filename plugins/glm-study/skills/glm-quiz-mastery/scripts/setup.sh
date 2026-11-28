#!/usr/bin/env bash
# glm-quiz-mastery — environment check (offline, pure-stdlib engine)
# Usage: bash ~/.codex/plugins/glm-study/skills/glm-quiz-mastery/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-quiz-mastery"
PY="${GLM_QUIZMASTERY_PYTHON:-python3}"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_QUIZMASTERY_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/generate_from_material.py scripts/import_quiz.py \
          scripts/run_quiz.py scripts/submit_answers.py \
          src/quiz_mastery/service.py src/quiz_mastery/models.py \
          src/quiz_mastery/evaluator.py src/quiz_mastery/mastery_engine.py \
          src/quiz_mastery/planner.py src/quiz_mastery/repository.py \
          src/quiz_mastery/quiz_generator.py src/quiz_mastery/quiz_extractor.py \
          src/quiz_mastery/file_parser.py src/quiz_mastery/utils.py \
          src/quiz_mastery/__init__.py references/quiz-workflow.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "engine syntax (in-memory compile, no bytecode written)"
for f in "$SKILL_DIR"/scripts/*.py "$SKILL_DIR"/src/quiz_mastery/*.py; do
  if "$PY" -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$f" 2>/dev/null; then
    good "syntax ok: $(basename "$f")"
  else
    bad "syntax error: $(basename "$f")"
  fi
done

section "usage self-test (no args -> Usage + exit 1)"
for s in generate_from_material.py import_quiz.py run_quiz.py submit_answers.py; do
  out="$("$PY" "$SKILL_DIR/scripts/$s" 2>&1)"; rc=$?
  if [ "$rc" -eq 1 ] && echo "$out" | head -1 | grep -q "Usage:"; then
    good "usage self-test $s: Usage + exit 1"
  else
    bad "usage self-test $s: expected Usage + exit 1, got rc=$rc"
  fi
done

section "plain-text parser smoke (.md)"
tmp="$(mktemp /tmp/glmqm_XXXX.md)"
printf '# Sample\n\n知识点：牛顿第二定律。\n' > "$tmp"
if "$PY" - "$tmp" "$SKILL_DIR/src" <<'PYEOF' >/dev/null 2>&1
import sys
sys.path.insert(0, sys.argv[2])
from quiz_mastery.file_parser import parse_file
assert parse_file(sys.argv[1]).strip().startswith("# Sample")
PYEOF
then good "parse_file(.md) works"; else bad "parse_file(.md) failed"; fi
rm -f "$tmp"

section "repository write smoke (data dir auto-create)"
if "$PY" - "$SKILL_DIR" <<'PYEOF' >/dev/null 2>&1
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
from quiz_mastery.repository import JsonRepository
import tempfile, shutil
tmp = Path(tempfile.mkdtemp())
repo = JsonRepository(tmp)
repo.save_json(repo.knowledge_points_path("doc_t"), {"knowledge_points": []})
assert repo.load_json(repo.knowledge_points_path("doc_t"), default=None) is not None
shutil.rmtree(tmp)
PYEOF
then good "repository read/write + dir bootstrap works"; else bad "repository smoke failed"; fi

section "optional document parsers"
if "$PY" -c "import fitz" >/dev/null 2>&1; then note "pymupdf available (.pdf best quality)"; else note "pymupdf absent (.pdf falls back to Quartz/pdftotext; optional)"; fi
if command -v pdftotext >/dev/null 2>&1; then note "pdftotext available"; else note "pdftotext absent (optional)"; fi
if "$PY" -c "import pptx" >/dev/null 2>&1; then note "python-pptx available (.ppt legacy ok)"; else note "python-pptx absent (.ppt legacy asks for .pptx; optional)"; fi

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
exit 0
