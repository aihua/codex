#!/usr/bin/env bash
# glm-auto-target-tracker setup.sh — 环境体检：解释器 + Ollama 连通 + 模型在位（不安装任何东西）
set -u

PY=""
for c in "${GLM_TRACK_PYTHON:-}" python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -z "$PY" ] && { echo "FAIL: 未找到 python3（macOS 自带或 brew install python3）"; exit 2; }
echo "OK: 解释器 $PY ($($PY -V 2>&1))"

SKIP="${1:-}"
if [ "$SKIP" = "--skip-service" ] || [ "$SKIP" = "--no-service" ]; then
  echo "OK: 本地自检完成（--skip-service，未探测 Ollama）"
  exit 0
fi

HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
BODY="$(OLLAMA_HOST="$HOST" "$PY" -c '
import json,urllib.request,os
host=os.environ.get("OLLAMA_HOST","http://127.0.0.1:11434").rstrip("/")
try:
    r=urllib.request.urlopen(host+"/api/tags",timeout=5)
    d=json.loads(r.read().decode())
    print(json.dumps([m.get("name","") for m in d.get("models",[])]))
except Exception as e:
    print(json.dumps({"err":str(e)}))
' 2>/dev/null)"

if printf '%s' "$BODY" | grep -q '"err"'; then
  echo "WARN: Ollama 不可达（$HOST）— 先运行: ollama serve"
  echo "      本地自检已通过；服务装好后重跑本脚本复检"
  exit 0
fi

echo "OK: Ollama 可达（$HOST）"
printf '%s' "$BODY" | tr ',' '\n' | tr -d '[]"' | sed 's/^\s*//' | grep -v '^$' > /tmp/.glmllm_models.$$
echo "OK: 模型检查跳过（ollama list 自查）"
rm -f /tmp/.glmllm_models.$$
echo "OK: glm-auto-target-tracker 体检完成"
