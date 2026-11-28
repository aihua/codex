#!/usr/bin/env bash
# glm-tts setup.sh — 环境体检：解释器 + say/afconvert/ffmpeg 探测（不安装任何东西）
set -u

PY=""
for c in "${GLM_TTS_PYTHON:-}" python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -z "$PY" ] && { echo "FAIL: 未找到 python3（macOS 自带或 brew install python3）"; exit 2; }
echo "OK: 解释器 $PY ($($PY -V 2>&1))"

SKIP="${1:-}"
if [ "$SKIP" = "--skip-tools" ] || [ "$SKIP" = "--no-tools" ]; then
  echo "OK: 本地自检完成（--skip-tools，未探测 TTS 工具链）"
  exit 0
fi

FAIL=0
if command -v say >/dev/null 2>&1; then
  echo "OK: say 在位（macOS 语音合成）"
else
  echo "FAIL: say 不在 PATH — 非 macOS 系统或系统异常；本插件 TTS 链为 macOS 设计"
  FAIL=1
fi

if command -v afconvert >/dev/null 2>&1; then
  echo "OK: afconvert 在位（WAV/M4A 转换，系统自带）"
else
  echo "FAIL: afconvert 不在 PATH — macOS 系统完整性异常"
  FAIL=1
fi

if command -v ffmpeg >/dev/null 2>&1; then
  echo "OK: ffmpeg 在位（mp3/pcm 输出与音量增益可用）"
else
  echo "NOTE: ffmpeg 不在 PATH — mp3/pcm 输出与 --volume 增益不可用（wav/m4a/aiff 零依赖不受影响）"
  echo "      可选安装: brew install ffmpeg"
fi

echo "中文语音包检查（可选）："
if say -v '?' 2>/dev/null | grep -q 'Tingting'; then
  echo "OK: Tingting (zh-CN) 在位"
else
  echo "NOTE: Tingting 未检出 — 系统设置 → 辅助功能 → 朗读内容 → 系统声音 → 管理声音 下载"
fi

if [ "$FAIL" = "1" ]; then
  echo "WARN: 核心工具缺失，TTS 将 exit 2；本地自检的其他项已通过"
  exit 0
fi
echo "OK: glm-tts 体检完成"
