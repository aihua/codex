#!/usr/bin/env bash
# glm-image-generation setup.sh — 环境体检：解释器 + Pillow 后端 + 字体（不安装任何东西）
set -u

PY=""
for c in "${GLM_GENIMG_PYTHON:-}" python3 python; do
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
  echo "OK: uv 在位 — glmgenimg.py 经 uv run --with pillow 即用即建（无需预装）"
else
  echo "WARN: 无进程内 PIL 亦无 uv — 生成会 exit 2；brew install uv 即恢复"
fi

FONT=""
for f in "/System/Library/Fonts/PingFang.ttc" "/System/Library/Fonts/Hiragino Sans GB.ttc" \
         "/System/Library/Fonts/Supplemental/Songti.ttc" \
         "/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf" \
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; do
  if [ -f "$f" ]; then FONT="$f"; break; fi
done
if [ -n "$FONT" ]; then
  echo "OK: 字体在位: $FONT"
else
  echo "WARN: 未检出可用字体 — 中文标题将无法渲染；装 PingFang/思源黑体/Noto CJK"
fi
echo "OK: glm-image-generation 体检完成"
