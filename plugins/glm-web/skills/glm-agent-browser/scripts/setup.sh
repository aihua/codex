#!/usr/bin/env bash
# glm-agent-browser setup.sh — 环境体检：node / pnpm / agent-browser / 浏览器内核（不安装任何东西）
set -u

FAIL=0
if command -v node >/dev/null 2>&1; then
  echo "OK: node 在位 ($(node -v))"
else
  echo "FAIL: node 不在 PATH"; FAIL=1
fi

if command -v pnpm >/dev/null 2>&1; then
  echo "OK: pnpm 在位 ($(command -v pnpm))"
elif command -v pn >/dev/null 2>&1; then
  echo "OK: pn 别名在位 ($(command -v pn))"
else
  echo "WARN: pnpm/pn 不在 PATH — 可用 npm 兼容路径安装"
fi

if command -v agent-browser >/dev/null 2>&1; then
  echo "OK: agent-browser CLI 在位 ($(command -v agent-browser))"
else
  echo "WARN: agent-browser 未安装 — 执行: pn install -g agent-browser && agent-browser install"
fi

if [ "$(command -v agent-browser >/dev/null 2>&1 && echo 1 || echo 0)" = "1" ]; then
  PW_DIR="$HOME/Library/Caches/ms-playwright"
  if [ -d "$PW_DIR" ] && ls "$PW_DIR"/chromium* >/dev/null 2>&1; then
    echo "OK: Playwright 浏览器内核已就绪（与全局 @playwright/cli 共存）"
  else
    echo "WARN: 未见浏览器内核 — 执行: agent-browser install（Linux 缺系统库加 --with-deps）"
  fi
fi

[ "$FAIL" = "1" ] && { echo "FAIL: node 缺失，无法使用本插件"; exit 2; }
echo "OK: glm-agent-browser 体检完成"
