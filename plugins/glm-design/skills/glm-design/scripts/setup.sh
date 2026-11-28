#!/usr/bin/env bash
# glm-design — 环境体检（离线：语料完整性 + 锚点 + 路径改写不变量 + 残留审计）
# Usage: bash ~/.codex/plugins/glm-design/skills/glm-design/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ok=0; warn=0; fail=0
section() { printf '
== %s ==
' "$1"; }
good()    { printf '  [ok]    %s
' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s
' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s
' "$1"; fail=$((fail+1)); }

section "skill structure (路由中枢 + 四大载荷区)"
for f in SKILL.md INDEX.md landing-page.md portfolio.md prototype.md content-page.md \
         info-interactive.md web-tool.md social-card.md deck.md canvas-and-device.md \
         quality-gate.md design-system-reference.md design-system-generation.md \
         export.md design-templates/INDEX.md design-systems/INDEX.md \
         design-systems/index.json scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done

section "corpus completeness (md 语料全量携带)"
md_n="$(find "$SKILL_DIR" -name '*.md' | wc -l | tr -d ' ')"
if [ "$md_n" -ge 418 ]; then good "markdown corpus: $md_n files (source had 418)"; else bad "markdown corpus too small: $md_n < 418"; fi
ss_n="$(find "$SKILL_DIR/design-systems/style-skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
bi_n="$(find "$SKILL_DIR/design-systems/brand-inspiration" -name 'DESIGN.md' 2>/dev/null | wc -l | tr -d ' ')"
[ "$ss_n" -ge 60 ]  && good "style-skills: $ss_n"   || bad "style-skills too few: $ss_n"
[ "$bi_n" -ge 30 ]  && good "brand-inspiration: $bi_n" || bad "brand-inspiration too few: $bi_n"
tpl_n="$(find "$SKILL_DIR/design-templates" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
[ "$tpl_n" -ge 29 ] && good "design-templates SKILL.md: $tpl_n" || bad "design-templates SKILL.md too few: $tpl_n"

section "slimming audit (HTML 演示层与图片资产不随包)"
big="$(find "$SKILL_DIR" \( -name '*.html' -o -name '*.webp' -o -name '*.jpg' -o -name '*.png' \) | wc -l | tr -d ' ')"
if [ "$big" -eq 0 ]; then good "零 .html/.webp/.jpg/.png 载荷（演示层已瘦身）"; else bad "瘦身违规: $big 个资产文件残留"; fi

section "anchors (路由与工艺完整性)"
for a in "landing-page.md" "portfolio.md" "prototype.md" "content-page.md" \
         "info-interactive.md" "web-tool.md" "social-card.md" "deck.md" \
         "quality-gate.md" "界面类" "创意类" "Content Read" "Style Sampling" \
         "Design Read"; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" && good "anchor: $a" || bad "anchor missing: $a"
done

section "path-rewrite invariant (排除部署节自描述行)"
left="$(grep -rni 'skills/design/' --include='*.md' "$SKILL_DIR" 2>/dev/null | grep -v '路径改写（载体内容级' | wc -l | tr -d ' ')"
if [ "$left" -eq 0 ]; then
  good "skills/design/ 前缀已全部相对化（部署节自描述行除外）"
else
  bad "残留未相对化的 skills/design/ 路径: $left 行"
fi
vm_n="$(grep -rl 'glm-version-management 同插件技能' "$SKILL_DIR" --include='*.md' 2>/dev/null | wc -l | tr -d ' ')"
[ "$vm_n" -ge 4 ] && good "version-management 同插件技能路由: $vm_n 个文件" || bad "同插件技能路由不足: $vm_n"

section "host-residue audit (语料零容忍；部署节审计行允许文档性提及)"
zai="$(grep -rni 'z-ai-web-dev-sdk' --include='*.md' "$SKILL_DIR" 2>/dev/null | grep -v '等效替换审计结论' | wc -l | tr -d ' ')"
if [ "$zai" -eq 0 ]; then
  good "418 文件语料零 SDK 标识（审计结论行文档性提及除外）"
else
  bad "SDK 标识残留: $zai 行"
fi

printf '
== summary ==
ok=%d warn=%d fail=%d
' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
