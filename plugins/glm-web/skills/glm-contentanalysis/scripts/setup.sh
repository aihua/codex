#!/usr/bin/env bash
# glm-contentanalysis — 环境体检（离线：结构 + 锚点 + 等效替换不变量 + 残留审计）
# Usage: bash ~/.codex/plugins/glm-web/skills/glm-contentanalysis/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "skill structure"
for f in SKILL.md ExtractWisdom/SKILL.md ExtractWisdom/Workflows/Extract.md scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done

section "anchors (动态分区/深度档/口吻铁律完整性)"
for a in "Dynamic Content Extraction" "Instant" "Comprehensive" "Quotes That Hit Different" \
         "First-Time Revelations" "One-Sentence Takeaway" "If You Only Have 2 Minutes" \
         "References & Rabbit Holes" "Themes & Connections" "Spiciest Take" "Level 3" \
        ; do
  grep -q "$a" "$SKILL_DIR/ExtractWisdom/SKILL.md" && good "anchor: $a" || bad "anchor missing: $a"
done

section "local-equivalent invariants (宿主工具替换到位)"
grep -q '~/.codex/glm-contentanalysis/' "$SKILL_DIR/ExtractWisdom/SKILL.md"   && good "客户化路径已本地化" || bad "客户化路径残留"
grep -q 'yt-dlp --write-auto-sub' "$SKILL_DIR/ExtractWisdom/Workflows/Extract.md"   && good "YouTube 字幕等效(yt-dlp)到位" || bad "fabric 等效缺失"
grep -q 'glm-web-reader' "$SKILL_DIR/ExtractWisdom/Workflows/Extract.md"   && good "文章抓取等效(glm-web-reader)到位" || bad "WebFetch 等效缺失"
# 残留判定：仅拦「非表格/非箭头行」的裸引用（替换表左列与审计行允许文档性提及）
pai="$(grep -rn '\.claude/PAI' "$SKILL_DIR/SKILL.md" "$SKILL_DIR/ExtractWisdom/SKILL.md" \
       "$SKILL_DIR/ExtractWisdom/Workflows/Extract.md" 2>/dev/null | grep -v '等效替换\|客户化目录\|→' | wc -l | tr -d ' ')"
[ "$pai" -eq 0 ] && good "PAI 路径仅存在于替换表描述（零指令形态）" || bad "PAI 路径裸引用残留 $pai 行"
fab="$(grep -n 'fabric' "$SKILL_DIR/ExtractWisdom/Workflows/Extract.md" | grep -v '等效替换源 skill' | wc -l | tr -d ' ')"
[ "$fab" -eq 0 ] && good "fabric 仅在替换表左列描述性提及（零指令形态）" || bad "fabric 裸引用残留 $fab 行"

section "host-residue audit (审计行允许文档性提及)"
zai=0
for f in "$SKILL_DIR/SKILL.md" "$SKILL_DIR/ExtractWisdom/SKILL.md" "$SKILL_DIR/ExtractWisdom/Workflows/Extract.md"; do
  t="$(grep -c 'z-ai' "$f" || true)"; a="$(grep -c '等效替换审计结论\|等效替换总表' "$f" || true)"
  [ "$t" -gt "$a" ] && zai=$((zai+1))
done
[ "$zai" -eq 0 ] && good "三份载荷零 SDK 标识（审计/替换表行除外）" || bad "SDK 标识超出文档性提及"

printf '\n== summary ==\nok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
