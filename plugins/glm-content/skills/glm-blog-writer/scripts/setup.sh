#!/usr/bin/env bash
# glm-blog-writer — 环境体检（离线：结构 + 逐字节携带 + 脚本契约演练 + 残留审计）
# Usage: bash ~/.codex/plugins/glm-content/skills/glm-blog-writer/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${GLM_BLOG_WRITER_SOURCE:-/home/z/my-project/skills/blog-writer}"
PY="${GLM_BLOG_WRITER_PYTHON:-python3}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }
[ -x "$PY" ] || PY=python3

section "skill structure"
for f in SKILL.md references/style-guide.md references/upstream-README.md \
         scripts/notion_publish.py scripts/manage_examples.py scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done
n_ex="$(ls "$SKILL_DIR/references/blog-examples"/*.md 2>/dev/null | wc -l | tr -d ' ')"
[ "$n_ex" -eq 7 ] && good "7 篇示例文章" || bad "示例文章数 $n_ex != 7"

section "verbatim carry"
for f in style-guide.md; do
  if [ -f "$SRC/$f" ] && cmp -s "$SKILL_DIR/references/$f" "$SRC/$f"; then good "$f byte-identical"; else bad "$f differs"; fi
done
if [ -f "$SRC/manage_examples.py" ] && cmp -s "$SKILL_DIR/scripts/manage_examples.py" "$SRC/manage_examples.py"; then
  good "manage_examples.py byte-identical"; else bad "manage_examples.py differs"; fi
for p in "$SRC"/20*.md; do
  b="$(basename "$p")"
  cmp -s "$SKILL_DIR/references/blog-examples/$b" "$p" || bad "example $b differs"
done
good "7 篇示例逐字节核验完成"

section "script contracts (python3 演练)"
"$PY" -c "import ast,sys; ast.parse(open('$SKILL_DIR/scripts/notion_publish.py').read())" \
  && good "notion_publish.py 语法合法" || bad "notion_publish.py 语法错误"
out="$("$PY" "$SKILL_DIR/scripts/manage_examples.py" 2>/dev/null | head -4)"
case "$out" in *"Total examples: 7"*) good "manage_examples.py 报告 7 篇";; *) bad "manage_examples.py 契约异常: $out";; esac
printf '# T\n\n**b** and *i* and `c` [l](u)\n\n> q\n\n- item\n' > "$TMP/post.md"
out="$("$PY" "$SKILL_DIR/scripts/notion_publish.py" "$TMP/post.md" --dry-run 2>&1)"
case "$out" in *'"mode": "dry-run"'*|*dry-run*) good "notion_publish.py --dry-run 契约命中";; *) bad "dry-run 契约失败: $out";; esac
grep -q '"blocks": 4' <<<"$out" && good "md→块转换计数正确(4: 标题/段落/引用/列表)" || bad "块计数异常: $(grep blocks <<<"$out")"
out="$("$PY" "$SKILL_DIR/scripts/notion_publish.py" "$TMP/nonexist.md" 2>&1)"; rc=$?
[ "$rc" -eq 1 ] && good "缺文件 exit 1" || bad "缺文件 rc=$rc"
out="$( cd "$TMP" && env -u NOTION_TOKEN "$PY" "$SKILL_DIR/scripts/notion_publish.py" post.md 2>&1 )"; rc=$?
[ "$rc" -eq 2 ] && good "无 token exit 2 + 本地兜底保存" || bad "无 token rc=$rc"
ls "$TMP/output/blog-writer"/*.md >/dev/null 2>&1 && good "本地兜底副本已存（$TMP/output/blog-writer）" || bad "兜底副本未落盘"

section "anchors"
for a in "TS Notes" "04a872be-8bed-4f43-a448-3dfeebc0df21" "Writing" \
         "800-1500 words" "Phase 4" "Phase 5"; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" && good "anchor: $a" || bad "anchor missing: $a"
done

section "host-residue audit (载荷零容忍；部署节审计行允许文档性提及)"
zai="$(grep -rli 'z-ai' "$SKILL_DIR/references" "$SKILL_DIR/scripts/notion_publish.py" "$SKILL_DIR/scripts/manage_examples.py" 2>/dev/null | wc -l | tr -d ' ')"
[ "$zai" -eq 0 ] && good "载荷（references + 两脚本）零 SDK 标识" || bad "SDK 标识残留"
total="$(grep -c 'z-ai' "$SKILL_DIR/SKILL.md" || true)"
allowed="$(grep -c '等效替换审计结论' "$SKILL_DIR/SKILL.md" || true)"
[ "$total" -le "$allowed" ] && good "SKILL.md 仅审计行文档性提及" || bad "SKILL.md 超范围引用"
[ -f "$SKILL_DIR/_meta.json" ] && bad "_meta.json 不应随包" || good "_meta.json 已排除"

printf '\n== summary ==\nok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
