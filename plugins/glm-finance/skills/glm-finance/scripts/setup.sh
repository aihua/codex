#!/usr/bin/env bash
# glm-finance — 环境体检（默认离线：结构 + 脚本契约 + 映射表 + 残留审计；
# --with-net 走腾讯链真网实测）
# Usage: bash ~/.codex/plugins/glm-finance/skills/glm-finance/scripts/setup.sh
set -u
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="${GLM_FINANCE_PYTHON:-python3}"
ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
warnonce(){ printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }
[ -x "$PY" ] || PY=python3

section "skill structure"
for f in SKILL.md references/finance-api-local.md scripts/finance_cli.py scripts/setup.sh; do
  [ -f "$SKILL_DIR/$f" ] && good "$f present" || bad "$f missing"
done

section "script contracts (离线)"
"$PY" -c "import ast; ast.parse(open('$SKILL_DIR/scripts/finance_cli.py').read())" \
  && good "finance_cli.py 语法合法" || bad "finance_cli.py 语法错误"
"$PY" "$SKILL_DIR/scripts/finance_cli.py" --help >/dev/null 2>&1 \
  && good "--help 契约命中" || bad "--help 异常"
"$PY" "$SKILL_DIR/scripts/finance_cli.py" modules AAPL bogus-module >/dev/null 2>&1
[ $? -eq 1 ] && good "未知模块 exit 1" || bad "未知模块退出码异常"
"$PY" "$SKILL_DIR/scripts/finance_cli.py" quote 600519 >/dev/null 2>&1
[ $? -eq 1 ] && good "A股无前缀 exit 1（含前缀提示）" || bad "A股无前缀退出码异常"
# 纯函数离线单测：模块别名归一 + 腾讯代码归一 + 输出格式化
SKILL_DIR="$SKILL_DIR" "$PY" - <<'PYEOF' && good "纯函数单测（别名/代码归一/格式化）PASS" || bad "纯函数单测 FAIL"
import importlib.util, os, pathlib
spec = importlib.util.spec_from_file_location(
    "fc", pathlib.Path(os.environ["SKILL_DIR"]) / "scripts" / "finance_cli.py")
fc = importlib.util.module_from_spec(spec); spec.loader.exec_module(fc)
assert fc.MODULE_ALIASES["asset-profile"] == "assetProfile"
assert fc.MODULE_ALIASES["statistics"] == "defaultKeyStatistics"
assert fc.tencent_code("AAPL") == "usAAPL"
assert fc.tencent_code("sh600519") == "sh600519"
assert fc.tencent_code("00700") == "hk00700"
assert fc._f("N/D") is None and fc._f("342.56") == 342.56
assert fc._fmt(None) == "-" and fc._fmt(342.5) == "342.50"
assert "342.56" in fc.md_table([{"price": 342.56}], ["price"])
print("unit ok")
PYEOF

section "local-equivalent invariants"
for a in "finance_cli.py search" "finance_cli.py quote" "finance_cli.py history" \
         "finance_cli.py news" "finance_cli.py modules" "qt.gtimg.cn" \
         "web.ifzq.gtimg.cn" "query1.finance.yahoo.com" "X-Z-AI-From" "GATEWAY_URL"; do
  grep -q "$a" "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references/finance-api-local.md" 2>/dev/null \
    && good "mapping anchor: $a" || bad "mapping anchor missing: $a"
done

section "host-residue audit (代码块内零网关调用)"
# 提取 fenced code block，检查其中不得出现网关指令（X-Z-AI-From / GATEWAY_URL 调用形态）；
# 映射表与提示节中的描述性提及放行。
residue="$("$PY" - "$SKILL_DIR/references/finance-api-local.md" "$SKILL_DIR/SKILL.md" <<'PYEOF'
import re, sys
bad = []
for path in sys.argv[1:]:
    text = open(path, encoding="utf-8").read()
    for block in re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.S):
        if re.search(r"X-Z-AI-From|GATEWAY_URL|x-rapidapi", block):
            bad.append(path.rsplit("/", 1)[-1])
print(",".join(sorted(set(bad))))
PYEOF
)"
if [ -n "$residue" ]; then
  bad "代码块内网关指令残留: $residue"
else
  good "代码块零网关指令（X-Z-AI-From/GATEWAY_URL 仅映射表描述性提及）"
fi
gw="$(grep -c 'GATEWAY_URL' "$SKILL_DIR/references/finance-api-local.md" || true)"
[ "$gw" -le 3 ] && good "GATEWAY_URL 仅限映射描述（$gw 处）" || bad "网关路径残留过多"

if [ "${1:-}" = "--with-net" ]; then
  section "tencent chain live probe (真网实测)"
  out="$("$PY" "$SKILL_DIR/scripts/finance_cli.py" quote AAPL --provider tencent 2>/dev/null | head -4)"
  case "$out" in *"| symbol |"*) good "腾讯链报价真网命中（AAPL）";; *) bad "腾讯链报价失败: $out";; esac
  out="$("$PY" "$SKILL_DIR/scripts/finance_cli.py" history sh600519 --provider tencent --limit 2 2>/dev/null | head -4)"
  case "$out" in *"2026"*) good "腾讯链日K真网命中（sh600519）";; *) warnonce "日K输出需人工确认: $out";; esac
else
  printf '  [info]  真网实测跳过（--with-net 开启腾讯链实测）\n'
fi

printf '\n== summary ==\nok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
