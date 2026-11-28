---
name: glm-contentanalysis
description: "Unified content extraction and wisdom-extraction routing for locally deployed Codex agents: the dynamic, content-adaptive ExtractWisdom workflow detects what wisdom domains actually exist in videos, podcasts, articles and YouTube URLs, then builds custom sections (not static IDEAS/QUOTES) into tailored insight reports at five depth levels (Instant/Fast/Basic/Full/Comprehensive). 触发场景：extract wisdom / 提取干货 / 分析这个视频或播客 / key takeaways / 内容洞察报告 / what did I miss。"
metadata:
  version: "1.0.0"
---

# ContentAnalysis（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-web/`；本技能目录：
  `~/.codex/plugins/glm-web/skills/glm-contentanalysis/`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill（路由器 + ExtractWisdom 子技能
  + Extract 工作流）对厂商 web-dev SDK 标识逐字审计**命中零**。需要等效替换的
  是三处**宿主工具假设**（见 ExtractWisdom/SKILL.md 部署节总表）：
  `~/.claude/PAI/USER/…` 客户化路径 → `~/.codex/glm-contentanalysis/`；
  `fabric -y`（YouTube 字幕）→ `yt-dlp --write-auto-sub`；WebFetch →
  glm-web-reader 同插件技能 / curl。
- **用户自定义**：`~/.codex/glm-contentanalysis/` 存在时加载其中的
  `PREFERENCES.md` / `WRITINGSTYLE.md`（覆盖默认行为与声音参照）。
- 洞察报告落**用户工作目录**（建议 `output/`）；插件目录只读。

## Workflow Routing

| Request Pattern | Route To |
|---|---|
| Extract wisdom, content analysis, insight report, analyze content, analyze video/podcast, extract insights, key takeaways, what did I miss, extract from YouTube | `ExtractWisdom/SKILL.md` |
