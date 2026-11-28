#!/usr/bin/env bash
# glm-cheat-sheet — 环境体检（离线：结构 + 提取/渲染契约演练 + 宿主残留审计；零网络）
# Usage: bash ~/.codex/plugins/glm-study/skills/glm-cheat-sheet/scripts/setup.sh
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_NAME="glm-cheat-sheet"
PY="${GLM_CHEAT_SHEET_PYTHON:-python3}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

ok=0; warn=0; fail=0
section() { printf '\n== %s ==\n' "$1"; }
good()    { printf '  [ok]    %s\n' "$1"; ok=$((ok+1)); }
note()     { printf '  [info]  %s\n' "$1"; }
warnonce() { printf '  [warn]  %s\n' "$1"; warn=$((warn+1)); }
bad()     { printf '  [fail]  %s\n' "$1"; fail=$((fail+1)); }

section "python interpreter"
if command -v "$PY" >/dev/null 2>&1; then
  good "interpreter available: $PY ($("$PY" -V 2>&1))"
else
  bad "python interpreter not found (set GLM_CHEAT_SHEET_PYTHON to fix)"
fi

section "skill structure"
for f in SKILL.md scripts/setup.sh scripts/extract_text.py scripts/render_cheatsheet.py; do
  if [ -f "$SKILL_DIR/$f" ]; then good "$f present"; else bad "$f missing"; fi
done

section "render dependency (reportlab 唯一第三方依赖)"
if "$PY" -c "import reportlab" >/dev/null 2>&1; then
  good "reportlab importable by $PY"
else
  warnonce "reportlab 未安装——免安装直跑: uv run --with reportlab python3 <render 脚本> ...；或 pip install reportlab"
fi
if command -v uv >/dev/null 2>&1; then
  good "uv available ($(uv --version 2>/dev/null | head -1))"
else
  warnonce "uv 不在 PATH（用户 macOS 环境为 /opt/uv/0.11.17）——用 pip install reportlab 兜底"
fi

section "extract_text contract (offline)"
printf '# 标题\n\n- 要点A：解释\n- 要点B：解释\n' > "$TMP/sample.md"
if "$PY" "$SKILL_DIR/scripts/extract_text.py" "$TMP/sample.md" -o "$TMP/out.txt" >/dev/null 2>&1; then
  if grep -q "要点A" "$TMP/out.txt"; then
    good "md extraction round-trip (直读)"
  else
    bad "md extraction lost content"
  fi
else
  bad "md extraction failed"
fi
# docx：纯标准库 zipfile 合成并提取
"$PY" - "$TMP/sample.docx" <<'EOF'
import sys, zipfile
xml = '<?xml version="1.0"?><w:document><w:body>' \
      '<w:p><w:r><w:t>机器学习</w:t></w:r></w:p>' \
      '<w:p><w:r><w:t>监督学习：有标签训练</w:t></w:r></w:p>' \
      '</w:body></w:document>'
with zipfile.ZipFile(sys.argv[1], "w") as zf:
    zf.writestr("word/document.xml", xml)
EOF
if "$PY" "$SKILL_DIR/scripts/extract_text.py" "$TMP/sample.docx" -o "$TMP/out2.txt" >/dev/null 2>&1; then
  if grep -q "监督学习" "$TMP/out2.txt"; then
    good "docx extraction via pure-stdlib zipfile"
  else
    bad "docx extraction lost content"
  fi
else
  bad "docx extraction failed"
fi
# 不支持后缀 → exit 2
printf 'x' > "$TMP/bad.xyz"
if "$PY" "$SKILL_DIR/scripts/extract_text.py" "$TMP/bad.xyz" >/dev/null 2>&1; then
  bad "unsupported suffix should exit 2"
else
  rc=$?; if [ "$rc" -eq 2 ]; then good "unsupported suffix exits 2"; else bad "unsupported suffix exit=$rc (expect 2)"; fi
fi
# 缺文件 → exit 2
if "$PY" "$SKILL_DIR/scripts/extract_text.py" "$TMP/nope.pdf" >/dev/null 2>&1; then
  bad "missing file should exit 2"
else
  rc=$?; if [ "$rc" -eq 2 ]; then good "missing file exits 2"; else bad "missing file exit=$rc (expect 2)"; fi
fi

section "render drill (reportlab 可用时)"
if "$PY" -c "import reportlab" >/dev/null 2>&1; then
  printf '# 知识浓缩卡\n\n## 一、核心概念\n- **术语A**：一句话定义\n- **术语B**：一句话定义\n\n## 二、Q&A\n**Q：什么是过拟合？**\nA：训练误差低而泛化差。\n' > "$TMP/content.md"
  if "$PY" "$SKILL_DIR/scripts/render_cheatsheet.py" -i "$TMP/content.md" -o "$TMP/card.pdf" >/dev/null 2>&1; then
    if head -c 5 "$TMP/card.pdf" | grep -q "%PDF" && [ "$(wc -c < "$TMP/card.pdf")" -gt 1500 ]; then
      good "rendered sample cheatsheet PDF (双栏 8pt CID 字体，%PDF 头 + 非空)"
    else
      bad "rendered PDF invalid/empty"
    fi
    if "$PY" "$SKILL_DIR/scripts/render_cheatsheet.py" -i "$TMP/content.md" -o "$TMP/card1.pdf" --single-column >/dev/null 2>&1; then
      good "--single-column switch works"
    else
      bad "--single-column switch failed"
    fi
  else
    bad "render failed on sample content"
  fi
else
  note "reportlab 不可用——渲染演练跳过（uv run --with reportlab 可免安装直跑）"
fi

section "host-residue self-check"
if grep -rqE "z-ai|zai|web-dev-sdk|^import anthropic|^import openai|^from anthropic|^from openai|Aider|Claude Code / Cursor" \
     "$SKILL_DIR" --include="*.py" --include="*.md" 2>/dev/null; then
  bad "host tool/SDK invocation residue found"
else
  good "payload free of host tool/SDK invocations (本地等效 CLI + uv 直跑)"
fi

section "knowledge anchors"
for anchor in "避免重复创建" "知识点速查卡" "思维导图式" "Q&A 式" \
              "extract_text.py" "render_cheatsheet.py" "uv run --with reportlab" \
              "STSong-Light" "Codex Deployment Notes"; do
  if grep -q "$anchor" "$SKILL_DIR/SKILL.md"; then
    good "SKILL.md anchor present: $anchor"
  else
    bad "SKILL.md anchor missing: $anchor"
  fi
done

printf '\n%d ok / %d warn / %d fail\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then exit 1; fi
exit 0
