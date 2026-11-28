#!/usr/bin/env bash
# glm-content-strategy — 环境体检（离线：结构 + 锚点 + 残留审计）
# Usage: bash ~/.codex/plugins/glm-market/skills/glm-content-strategy/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "skill structure"
for f in SKILL.md scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done

section "anchors (八步法完整性)"
for a in "Define Your Content Goals" "Research Your Audience" "Build Content Pillars" \
         "Choose Your Content Formats" "Build a Content Calendar" \
         "Distribution and Amplification" "Repurpose Everything" \
         "Measure What Matters" "Content Strategy Mistakes" \
        ; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" && good "anchor: $a" || bad "anchor missing: $a"
done

section "host-residue audit"
total="$(grep -c 'z-ai' "$SKILL_DIR/SKILL.md" || true)"
allowed="$(grep -c '等效替换审计结论' "$SKILL_DIR/SKILL.md" || true)"
[ "$total" -le "$allowed" ] && good "零 SDK 标识（审计结论行文档性提及除外）" || bad "SDK 标识残留"
[ -f "$SKILL_DIR/_meta.json" ] && bad "_meta.json 不应随包" || good "_meta.json 已排除"

printf '\n== summary ==\nok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
