#!/usr/bin/env bash
# glm-aminer-daily-paper — 环境体检（离线：结构 + yamlshim 契约 + 触发解析契约 +
# 无 key 错误路径演练 + 宿主残留审计；不发起任何网络请求、不触碰 AMINER_API_KEY 值）
# Usage: bash ~/.codex/plugins/glm-academic/skills/aminer-daily-paper/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-aminer-daily-paper"
PY="${GLM_AMINER_DP_PYTHON:-python3}"
SCRIPTS="$SKILL_DIR/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_AMINER_DP_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/handle_trigger.py scripts/run_pipeline.py \
         scripts/rec5_api.py scripts/common.py scripts/constants.py scripts/yamlshim.py \
         scripts/__init__.py prompts/enrich.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done
if [ -f "$SKILL_DIR/requirements.txt" ]; then
  bad "requirements.txt shipped (PyYAML 已由 yamlshim 等效替换，不应随包)"
else
  good "no requirements.txt in payload (PyYAML 等效替换完成)"
fi

section "yaml shim contract (PyYAML 等效替换)"
if "$PY" -c "
import sys
sys.path.insert(0, '$SCRIPTS')
import yamlshim
cfg = {'aminer': {'token': 't0', 'rec5_url': 'https://x/y'}, 'search': {'top_k': 10}}
text = yamlshim.safe_dump(cfg, allow_unicode=True, sort_keys=False)
back = yamlshim.safe_load(text)
assert back == cfg, (text, back)
roundtrip2 = yamlshim.safe_load(yamlshim.safe_dump({}))
assert roundtrip2 == {}
sys.exit(0)
"; then
  good "yamlshim round-trip: config.yaml 形态 dump→load 等值（含空配置）"
else
  bad "yamlshim round-trip failed"
fi
if "$PY" -c "
import sys
sys.path.insert(0, '$SCRIPTS')
try:
    import yaml
    print('real PyYAML available — 插件将优先使用')
except ImportError:
    print('PyYAML absent — 插件将退回内置 yamlshim')
import handle_trigger  # noqa: F401  （验证两条导入路径均不崩）
sys.exit(0)
" >/dev/null 2>&1; then
  good "handle_trigger imports OK (yaml 或 yamlshim 任一形态)"
else
  bad "handle_trigger import failed"
fi

section "trigger parsing contract (offline, 不发网络)"
if "$PY" -c "
import sys
sys.path.insert(0, '$SCRIPTS')
import handle_trigger as ht
p = ht.parse_trigger_text('/aminer-dp topics: 多模态, 智能体')
assert p['topics'] == ['多模态', '智能体'], p['topics']
assert p['is_trigger'] is True
p2 = ht.parse_trigger_text('/aminer-dp scholar: Jie Tang org: Tsinghua papers: OAG-Bench')
assert p2['scholar_name'] == 'Jie Tang', p2
assert p2['scholar_org'] == 'Tsinghua', p2
assert 'OAG-Bench' in p2['paper_titles'], p2
inf = ht._infer_topics_from_free_text('帮我推荐多模态智能体和 tool-use 的最近论文')
assert inf and '多模态' in inf[0], inf
sys.exit(0)
"; then
  good "parse_trigger_text: topics/scholar+org+papers/自然语言推断 全部解析正确"
else
  bad "parse_trigger_text contract failed"
fi

section "error paths (offline, 无 key → auth 阶段即失败，零网络)"
OUT=$(cd "$TMP" && env -u AMINER_API_KEY "$PY" "$SCRIPTS/handle_trigger.py" \
  --text "/aminer-dp topics: 多模态" --output-dir "$TMP/out" 2>/dev/null)
RC=$?
if [ "$RC" -eq 0 ]; then
  good "handle_trigger always exits 0 (JSON 承载结果/错误)"
else
  bad "handle_trigger exit=$RC (expect 0)"
fi
if printf '%s' "$OUT" | grep -q '"mode": "error"' && printf '%s' "$OUT" | grep -q "auth_failed"; then
  good "no-key path: mode=error + auth_failed 定位（reply_text 引导用户设置 key）"
else
  bad "no-key error path broken"
fi
OUT2=$(cd "$TMP" && env -u AMINER_API_KEY "$PY" "$SCRIPTS/handle_trigger.py" \
  --text "/aminer-dp aminer_author_id: zzz topics: x" --output-dir "$TMP/out" 2>/dev/null)
if printf '%s' "$OUT2" | grep -q '"mode": "invalid_input"'; then
  good "invalid author-id path: mode=invalid_input（24 位 hex 校验）"
else
  bad "invalid author-id path broken"
fi
OUT3=$(cd "$TMP" && env -u AMINER_API_KEY "$PY" "$SCRIPTS/handle_trigger.py" \
  --text "" --output-dir "$TMP/out" 2>/dev/null)
if printf '%s' "$OUT3" | grep -q '"mode": "help"'; then
  good "empty-profile path: mode=help（引导话术；自然语言 topics 由模型先行结构化后传入）"
else
  bad "help path broken"
fi
if [ -f "$TMP/out/runtime_config.yaml" ]; then
  good "--output-dir honored (runtime_config.yaml 落用户目录)"
else
  bad "output-dir not honored"
fi

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (urllib 直调公网接口)"
fi

section "knowledge anchors"
for anchor in "language_sort" "handle_trigger.py" "yamlshim" "输出目录" "reply_text" \
              "glm-aminer-academic-search" "Codex Deployment Notes"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
