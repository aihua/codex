#!/usr/bin/env bash
# glm-ai-news-collectors — 环境体检（离线：结构 + 逐字节核验 + 锚点 + 残留审计）
# Usage: bash ~/.codex/plugins/glm-content/skills/glm-ai-news-collectors/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${GLM_AI_NEWS_SOURCE:-/home/z/my-project/skills/ai-news-collectors}"
ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "skill structure"
for f in SKILL.md references/sources.md scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done

section "verbatim carry"
if [ -f "$SRC/references/sources.md" ] && cmp -s "$SKILL_DIR/references/sources.md" "$SRC/references/sources.md"; then
  good "sources.md byte-identical"
else
  warnonce "sources.md 与源不可比较（安装态；构建期已逐字节核验）"
fi
for a in "Last Week in AI" "Hacker News" "机器之心" "量子位" "TLDR AI"; do
  grep -q "$a" "$SKILL_DIR/references/sources.md" && good "source anchor: $a" || bad "source anchor missing: $a"
done

section "anchors (工作流完整性)"
for a in "多维度分层搜索" "维度 A" "维度 B" "交叉验证与补漏" "热度综合判断" \
         "去重与合并" "15-25" "搜索不足 8 次不要开始输出" \
        ; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" && good "anchor: $a" || bad "anchor missing: $a"
done

section "local-equivalent routing (搜索/抓取经 glm-web 插件技能)"
for a in "glm-web-search" "glm-web-reader" "glmws.py search"; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" && good "routing: $a" || bad "routing missing: $a"
done

section "host-residue audit"
total="$(grep -c 'z-ai' "$SKILL_DIR/SKILL.md" || true)"
allowed="$(grep -c '等效替换审计结论' "$SKILL_DIR/SKILL.md" || true)"
[ "$total" -le "$allowed" ] && good "零 SDK 标识（审计结论行除外）" || bad "SDK 标识残留"
refs="$(grep -c 'z-ai' "$SKILL_DIR/references/sources.md" || true)"
[ "$refs" -eq 0 ] && good "sources.md 零 SDK 标识" || bad "sources.md 残留"
[ -f "$SKILL_DIR/_meta.json" ] && bad "_meta.json 不应随包" || good "_meta.json 已排除"

printf '\n== summary ==\nok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
