#!/usr/bin/env bash
# glm-asr setup.sh — 环境体检：解释器 + ASR 后端（uv / whisper-cli）探测（不安装任何东西）
set -u

PY=""
for c in "${GLM_ASR_PYTHON:-}" python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -z "$PY" ] && { echo "FAIL: 未找到 python3（macOS 自带或 brew install python3）"; exit 2; }
echo "OK: 解释器 $PY ($($PY -V 2>&1))"

SKIP="${1:-}"
if [ "$SKIP" = "--skip-backend" ] || [ "$SKIP" = "--no-backend" ]; then
  echo "OK: 本地自检完成（--skip-backend，未探测 ASR 后端）"
  exit 0
fi

HAVE_BACKEND=0
if command -v uv >/dev/null 2>&1; then
  echo "OK: uv 在位 ($(command -v uv)) — faster-whisper 主链开箱即用"
  HAVE_BACKEND=1
else
  echo "WARN: uv 不在 PATH — faster-whisper 主链不可用（brew install uv）"
fi

if command -v whisper-cli >/dev/null 2>&1; then
  echo "OK: whisper-cli 在位 — 备链可用（仅 16kHz wav）"
  HAVE_BACKEND=1
else
  echo "WARN: whisper-cli 不在 PATH — 备链不可用（brew install whisper-cpp，可选）"
fi

[ "$HAVE_BACKEND" = "0" ] && {
  echo "WARN: 两个 ASR 后端都缺位 — 转写会 exit 2 并给指引；装 uv 即恢复主链"
  exit 0
}

if [ -z "${HF_ENDPOINT:-}" ]; then
  echo "NOTE: 未设 HF_ENDPOINT — 首次下载 Whisper 模型国内网络建议:"
  echo "      export HF_ENDPOINT=https://hf-mirror.com"
else
  echo "OK: HF_ENDPOINT=$HF_ENDPOINT（模型下载走镜像）"
fi
echo "OK: glm-asr 体检完成"
