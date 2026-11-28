#!/usr/bin/env bash
# glm-image-search setup.sh — 环境体检：解释器 + Bing 连通（不安装任何东西）
set -u
PY=""
for c in "${GLM_IMGSEARCH_PYTHON:-}" python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -z "$PY" ] && { echo "FAIL: 未找到 python3（macOS 自带或 brew install python3）"; exit 2; }
echo "OK: 解释器 $PY ($($PY -V 2>&1))"
SKIP="${1:-}"
if [ "$SKIP" = "--skip-net" ] || [ "$SKIP" = "--no-net" ]; then
  echo "OK: 本地自检完成（--skip-net，未做网络探测）"
  exit 0
fi
CODE="$("$PY" -c '
import urllib.request
try:
    r = urllib.request.urlopen("https://www.bing.com", timeout=8)
    print(r.status)
except Exception as e:
    print("err:" + str(e))
' 2>/dev/null)"
if [ "$CODE" = "200" ] || [ "$CODE" = "301" ] || [ "$CODE" = "302" ]; then
  echo "OK: www.bing.com 可达（状态 $CODE）"
else
  echo "WARN: www.bing.com 不可达（$CODE）— 检查网络/代理；大陆网络通常可达"
  echo "      Codex 命令沙箱需放行网络（network_access / danger-full-access）"
fi
echo "OK: glm-image-search 体检完成"
