#!/usr/bin/env bash
# glm-coding-agent — 环境体检（离线：结构 + 逐字节携带核验 + 锚点 + 残留审计）
# Usage: bash ~/.codex/plugins/glm-dev/skills/glm-coding-agent/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${GLM_CODING_AGENT_SOURCE:-/home/z/my-project/skills/coding-agent}"
ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "skill structure"
for f in SKILL.md planning.md execution.md verification.md state.md \
         criteria.md memory-template.md scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done

section "verbatim carry (六个辅助件与源逐字节等同)"
for f in planning.md execution.md verification.md state.md criteria.md memory-template.md; do
  if [ -f "$SRC/$f" ]; then
    if cmp -s "$SKILL_DIR/$f" "$SRC/$f"; then good "$f byte-identical"
    else bad "$f differs from source"; fi
  else
    warnonce "source $f not comparable on this machine (install-time carry was verbatim)"
  fi
done

section "anchors (工作流纪律完整性)"
for a in "Request -> Plan -> Execute -> Verify -> Deliver" "~/code/memory.md" \
         "Plan Before Code" "Verify Everything" "Check Memory First" \
        ; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" && good "anchor: $a" || bad "anchor missing: $a"
done

section "host-residue audit (payload 零容忍；部署节审计行允许文档性提及)"
refs_hit="$(grep -rliE "z-ai" "$SKILL_DIR"/planning.md "$SKILL_DIR"/execution.md "$SKILL_DIR"/verification.md "$SKILL_DIR"/state.md "$SKILL_DIR"/criteria.md "$SKILL_DIR"/memory-template.md 2>/dev/null | wc -l)"
if [ "$refs_hit" -eq 0 ]; then good "六个辅助参考件零 SDK 标识"; else bad "辅助件残留: $(grep -rliE z-ai "$SKILL_DIR"/{planning,execution,verification,state,criteria,memory-template}.md)"; fi
audit_line='z-ai-web-dev-sdk 等效替换审计结论'
total="$(grep -c "z-ai" "$SKILL_DIR/SKILL.md" || true)"
allowed="$(grep -c "$audit_line" "$SKILL_DIR/SKILL.md" || true)"
if [ "$total" -eq "$allowed" ]; then good "SKILL.md 仅审计结论行文档性提及（$allowed 处，非执行形态）"; else bad "SKILL.md 存在超出审计行的 z-ai 引用（total=$total allowed=$allowed）"; fi
if [ -f "$SKILL_DIR/_meta.json" ]; then bad "_meta.json 不应随包"; else good "_meta.json 已排除"; fi

printf '\n== summary ==\nok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
