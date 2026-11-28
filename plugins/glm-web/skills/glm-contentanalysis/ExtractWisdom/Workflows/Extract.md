# Extract Workflow

Extract dynamic, content-adaptive wisdom from any content source.

## Input Sources

| Source | Method |
|--------|--------|
| YouTube URL | `yt-dlp --write-auto-sub --skip-download --sub-langs "en.*" -o "%(id)s"` to get the transcript（等效替换源 skill 的 `fabric -y`）；下载 .en.vtt 后剥离时间轴行取纯文本 |
| Article URL | glm-web-reader 同插件技能抓正文（等效替换 WebFetch）；兜底 `curl -L <url>` |
| File path | Read the file directly |
| Pasted text | Use directly |

## Execution Steps

### Step 1: Get the Content

Obtain the full text/transcript. For YouTube:

```bash
yt-dlp --write-auto-sub --skip-download --sub-langs "en.*" -o "%(id)s" "https://www.youtube.com/watch?v=..."
# 剥离 .vtt 时间轴（纯标准库）：python3 -c "...（见下）"
```

vtt→纯文本一行（去时间轴/坐标行）：

```bash
python3 - <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "*.en.vtt")
t = p.read_text(encoding="utf-8", errors="replace")
lines = [l for l in t.splitlines() if l and not re.match(r"^(WEBVTT|\d|$|-->)", l.strip())]
print("\n".join(dict.fromkeys(l for l in lines if l.strip())))
PY
```

Save to a working file if large. For articles, fetch with glm-web-reader (sibling
plugin) or `curl -L <url>` and strip tags.

### Step 2: Deep Read

Read the entire content. Don't extract yet. Notice:
- What domains of wisdom are present?
- What made you stop and think?
- What's genuinely novel vs. commonly known?
- What would the voice owner highlight if he were reading this?
- What quotes land perfectly?

### Step 3: Select Dynamic Sections

Based on your deep read, pick 5-12 section names. Rules:
- Section names must be conversational, not academic
- Each must have at least 3 quality bullets
- Always include "Quotes That Hit Different" if source has quotable moments
- Always include "First-Time Revelations" if genuinely new ideas exist
- Be SPECIFIC — "Agentic Engineering Philosophy" not "Technology Insights"

### Step 4: Extract Per Section

For each section, extract 3-15 bullets. Apply tone rules from SKILL.md:
- 8-20 words, flexible for clarity
- Specific details, not vague summaries
- Speaker's words when they're good
- No hedging language
- Every bullet worth telling someone about

### Step 5: Add Closing Sections

Always append:
1. **One-Sentence Takeaway** (15-20 words)
2. **If You Only Have 2 Minutes** (5-7 essential points)
3. **References & Rabbit Holes** (people, projects, books, tools mentioned)

### Step 6: Quality Check

Run the quality checklist from SKILL.md before delivering.

### Step 7: Output

Present the complete extraction in the format specified in SKILL.md.
