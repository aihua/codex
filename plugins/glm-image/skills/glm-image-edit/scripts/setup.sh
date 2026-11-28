#!/usr/bin/env bash
# glm-image-edit setup.sh — 环境体检：解释器 + Pillow 后端（进程内 PIL 或 uv）（不安装任何东西）
set -u

PY=""
for c in "${GLM_IMGEDIT_PYTHON:-}" python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -z "$PY" ] && { echo "FAIL: 未找到 python3（macOS 自带或 brew install python3）"; exit 2; }
echo "OK: 解释器 $PY ($($PY -V 2>&1))"

SKIP="${1:-}"
if [ "$SKIP" = "--skip-backend" ] || [ "$SKIP" = "--no-backend" ]; then
  echo "OK: 本地自检完成（--skip-backend，未探测 Pillow 后端）"
  exit 0
fi

if "$PY" -c 'import PIL' >/dev/null 2>&1; then
  echo "OK: 进程内 PIL 可用（直跑路径）"
elif command -v uv >/dev/null 2>&1; then
  echo "OK: uv 在位 — glmimgedit.py 经 uv run --with pillow 即用即建（无需预装）"
else
  echo "WARN: 无进程内 PIL 亦无 uv — 编辑会 exit 2；brew install uv 即恢复"
fi

for f in "/System/Library/Fonts/PingFang.ttc" "/System/Library/Fonts/Hiragino Sans GB.ttc"; do
  if [ -f "$f" ]; then
    echo "OK: 中文字体在位（水印/标注）: $f"
    break
  fi
done
if [ ! -f "/System/Library/Fonts/PingFang.ttc" ] && [ ! -f "/System/Library/Fonts/Hiragino Sans GB.ttc" ]; then
  echo "NOTE: 未检出 macOS 中文字体 — 中文水印可能回退；Linux 装 Noto Sans CJK"
fi
echo "OK: glm-image-edit 体检完成"
