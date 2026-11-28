#!/usr/bin/env bash
# glm-stock-analysis-skill — environment check (offline, pure-stdlib engine)
# Usage: bash ~/.codex/plugins/glm-finance/skills/glm-stock-analysis-skill/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-stock-analysis-skill"
PY="${GLM_STOCK_PYTHON:-python3}"
CLI="$SKILL_DIR/scripts/stockcli.py"

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()    { printf '  [info]  %s\n' "$1"; }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_STOCK_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/stockcli.py \
         references/dashboard-template.md references/report-template.md \
         references/data-schemas.md; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "engine syntax (in-memory compile, no bytecode written)"
if "$PY" -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$CLI" 2>/dev/null; then
  good "stockcli.py syntax ok"
else
  bad "stockcli.py syntax error"
fi

section "usage self-test (no args -> argparse exit 2)"
out="$("$PY" "$CLI" 2>&1)"; rc=$?
if [ "$rc" -eq 2 ]; then
  good "usage self-test exit 2 as designed (argparse missing-command contract)"
else
  bad "expected exit 2 without args, got $rc"
fi

section "engine drill (dividend / rumor / watchlist / report / verdict)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# dividend scoring: JNJ-style data must yield a high safety score
cat > "$WORK/div.json" <<'EOF'
[{"ticker":"JNJ","name":"Johnson & Johnson","currentPrice":152.3,"dividendYield":3.25,
  "annualDividend":4.96,"trailingEps":9.87,"exDividendDate":"2026-05-23",
  "paymentFrequency":"quarterly","dividendHistory":[{"year":2025,"total":4.96}],
  "consecutiveYears":63,"dividendGrowth5y":5.9}]
EOF
DOUT="$("$PY" "$CLI" dividend "$WORK/div.json" --format json 2>/dev/null)"
echo "$DOUT" | "$PY" -c "
import json, sys
r = json.load(sys.stdin)[0]
# payout = 4.96/9.87*100 = 50.3 -> moderate (+10); growth 5.9 -> +10; years 63 -> +15; base 50
assert r['payoutRatio'] == 50.3 and r['payoutStatus'] == 'moderate', r
assert r['safetyScore'] == 85 and r['incomeRating'] == 'excellent', r
print('  [ok]    dividend drill: payout 50.3 moderate / score 85 / excellent (JNJ fixture)')
" || bad "dividend drill failed"
ok=$((ok+1))

# rumor scoring: ma + breaking + engagement = 1+5+2+2 = 10 (capped)
cat > "$WORK/news.json" <<'EOF'
[{"type":"ma","ticker":"NVDA","headline":"Breaking: NVDA acquisition talks reported",
  "source":"reuters","sentiment":"positive","date":"2026-05-18","highEngagement":true},
 {"type":"earnings","ticker":null,"headline":"Sector earnings guidance raised",
  "source":"bb","sentiment":"neutral","date":"2026-05-18"}]
EOF
ROUT="$("$PY" "$CLI" rumor "$WORK/news.json" --format json 2>/dev/null)"
echo "$ROUT" | "$PY" -c "
import json, sys
d = json.load(sys.stdin)
assert d['rumors'][0]['impactScore'] == 10, d['rumors'][0]
assert d['topTickers'][0] == {'ticker': 'NVDA', 'count': 1}
print('  [ok]    rumor drill: ma+breaking+engagement capped at 10')
" || bad "rumor drill failed"
ok=$((ok+1))

# watchlist add -> check (target hit) -> remove
cd "$WORK"
"$PY" "$CLI" watch add AAPL --price 123.4 --target 200 --stop 100 >/dev/null 2>&1 || bad "watch add failed"
good "watch add: persisted to ./stock_watchlist.json"
printf '{"AAPL": 205.0}' > prices.json
COUT="$("$PY" "$CLI" watch check --prices-file prices.json --format json 2>/dev/null)"
echo "$COUT" | "$PY" -c "
import json, sys
d = json.load(sys.stdin)
assert d['count'] == 1 and d['alerts'][0]['alertType'] == 'target_hit', d
print('  [ok]    watch check drill: target_hit fired at 205.0 >= 200')
" || bad "watch check drill failed"
ok=$((ok+1))
if grep -q '"ticker": "AAPL"' "$WORK/stock_watchlist.json" 2>/dev/null; then
  good "watchlist persistence: local JSON file written"
else
  bad "watchlist file not written"
fi
"$PY" "$CLI" watch remove AAPL >/dev/null 2>&1 || bad "watch remove failed"
good "watch remove: cleaned up"

# report assembly + verdict extraction
cat > "$WORK/analysis.json" <<'EOF'
[{"code":"600519","market":"CN","name":"贵州茅台",
  "analysis":"## 决策仪表盘 · 贵州茅台(600519)\n\n**结论：买入** 核心逻辑……",
  "warnings":["⚠️ 乖离率 3.7% 接近警戒"]}]
EOF
"$PY" "$CLI" report "$WORK/analysis.json" > "$WORK/report.md" 2>/dev/null || bad "report drill failed"
if grep -q "🟢买入/强烈买入 1" "$WORK/report.md" && grep -q "⚠️ \*\*预警" "$WORK/report.md"; then
  good "report drill: header stats + warnings block assembled"
else
  bad "report drill output wrong"
fi
printf '**结论：强烈买入**\n' > "$WORK/v.md"
VOUT="$("$PY" "$CLI" verdict "$WORK/v.md" 2>/dev/null)"
echo "$VOUT" | "$PY" -c "
import json, sys
assert json.load(sys.stdin)['verdict'] == '强烈买入'
print('  [ok]    verdict drill: extract_verdict matched 强烈买入')
" || bad "verdict drill failed"
ok=$((ok+1))

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ] || exit 1

note "install check: plugin dir expected at ~/.codex/plugins/$PLUGIN_NAME/"
exit 0
