#!/usr/bin/env bash
# glm-fullstack-dev — 环境体检（默认离线：结构 + 锚点 + 宿主残留审计；--with-net 加网络探测）
# Usage: bash ~/.codex/plugins/glm-dev/skills/glm-fullstack-dev/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="${GLM_FULLSTACK_DEV_PYTHON:-python3}"
ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "skill structure"
for f in SKILL.md scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done

section "anchors (源规范迁移完整性)"
for a in "Next.js 16" "Tailwind CSS 4" "shadcn/ui" "Prisma" "pnpm dev" "pnpm lint" \
         "prisma db push" "min-h-screen flex flex-col" "playwright screenshot" \
         "localhost:11434/v1/chat/completions"; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" && good "anchor: $a" || bad "anchor missing: $a"
done

section "host-residue audit (代码块内不得出现沙箱机制指令)"
# 等效替换总表左列允许描述性提及宿主机制；审计只查 fenced code block
# （可执行指令）内是否残留 bun / z-cdn init / z-ai-web-dev-sdk / XTransformPort。
residue="$("$PY" - "$SKILL_DIR/SKILL.md" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
bad = []
for b in blocks:
    for pat in (r"(^|\s|\|`)bun (run |)dev", r"curl https://z-cdn",
                r"z-ai-web-dev-sdk", r"XTransformPort=", r"import .*z-ai"):
        if re.search(pat, b):
            bad.append(pat)
print(",".join(bad))
PYEOF
)"
if [ -n "$residue" ]; then
  bad "代码块内宿主指令残留: $residue"
else
  good "代码块零宿主指令（bun/z-cdn/z-ai-web-dev-sdk/XTransformPort）"
  good "等效替换总表内描述性提及已放行（文档性，非可执行）"
fi

section "local toolchain probe (report only)"
for bin in node pnpm pn; do
  command -v "$bin" >/dev/null 2>&1 && good "$bin available ($(command -v $bin))"     || warnonce "$bin not on this sandbox PATH (user macOS has /opt/node.js/24.16.0 + pnpm)"
done

if [ "${1:-}" = "--with-net" ]; then
  section "ollama reachability"
  code="$(curl -s -o /dev/null -m 3 -w "%{http_code}" http://localhost:11434/v1/models 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then good "Ollama reachable (v1/models 200)"
  else warnonce "Ollama not reachable (code=$code) — start: ollama serve"; fi
else
  printf '  [info]  网络探测跳过（--with-net 开启 Ollama 探活）\n'
fi

printf '\n== summary ==\nok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
