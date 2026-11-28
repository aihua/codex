---
name: glm-blog-writer
description: "Blog and long-form article writing in the writer's distinctive voice - direct, opinionated, conversational, grounded in personal experience - for locally deployed Codex agents. Full workflow from research review through drafting, iteration and publication; calibrated against 7 carried example posts and a style guide. 触发场景：写博客 / 用我的风格写文章 / 写一篇 thought leadership / 按 my style 写 / 帮我把这些资料写成文章。"
metadata:
  version: "1.0.0"
---

# Blog Writer（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-content/`；本技能目录：
  `~/.codex/plugins/glm-content/skills/glm-blog-writer/`。
  下文 `references/style-guide.md`、`references/blog-examples/`、`scripts/` 均指
  本技能目录内路径。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 对厂商 web-dev SDK 标识逐字
  审计**命中零**（纯工作流 + 纯标准库脚本）——无需函数级替换。真正需要等效
  替换的是**宿主 Notion 发布集成**，见下表。
- **Notion 宿主集成等效替换表**：

| 源 skill 调用 | 本插件本地等效 | 说明 |
|---|---|---|
| Phase 4 宿主 Notion 发布（MCP/API 直达，硬性成功判据） | `scripts/notion_publish.py <post.md>` | 纯标准库；发布契约不变：TS Notes 库（data source `04a872be-…`）、Note=标题、Type=`Writing`、Project(s)=My Writing（`2a5b4629-…`），Markdown 正文转 Notion 块（>100 块自动分批追加） |
| `NOTION_TOKEN` 环境变量 | 同名沿用 | https://www.notion.so/my-integrations 建 integration 并授权库后 `export NOTION_TOKEN=…`；缺 token 时脚本 exit 2 并**自动把带日期的终稿存到 `output/blog-writer/`**，同时向用户转述引导 |
| Phase 5 终稿存 `references/blog-examples/`（skill 目录） | 终稿落**用户工作目录** `output/blog-examples/` | 插件目录只读；`scripts/manage_examples.py` 仍管理插件内示例库（列表/超限 20 篇时给出删旧 5 篇建议；`prune --execute` 才真删） |
| 示例库计数「成功判据」 | 同左（落点改为用户目录） | 上限 20 篇 + 提请删除最旧 5 篇的规则保留 |

- 脚本退出码：`notion_publish.py` 0 成功（打印页面 URL）/ 1 用法/文件错误 /
  2 NOTION_TOKEN 缺失 / 3 API 错误；`manage_examples.py` 永远 0（报告型）。
- `_meta.json`（上游市场元数据）不随包。

---

# Blog Writer

## Overview

This skill enables writing blog posts and articles that authentically capture the writer's distinctive voice and style. It draws on examples of the writer's published work to produce content that is direct, opinionated, conversational, and grounded in practical experience. The skill includes local Notion publication and maintains a growing library of finalized examples.

## When to Use This Skill

Trigger this skill when:
- The user requests blog post or article writing in "my style" or "like my other posts"
- Drafting thought leadership content on AI, productivity, marketing, or technology
- Creating articles that need the writer's authentic voice and perspective
- The user provides research materials, links, or notes to incorporate into writing

## Core Responsibilities

1. **Follow the writer's Writing Style**: Match voice, word choice, structure, and length of example posts in `references/blog-examples/`
2. **Incorporate Research**: Review and integrate any information, research material, or links provided by the user
3. **Follow User Instructions**: Adhere closely to the user's specific requests for topic, angle, and emphasis
4. **Produce Authentic Writing**: Create content that reads as genuinely the writer's voice, not generic AI-generated content

## Workflow

### Phase 1: Gather Information

Request from the user:
- Topic or subject matter
- Any specific angle or thesis to explore
- Research materials, links, or notes (if available)
- Target length preference (default: 800-1500 words)

Review all provided materials thoroughly before beginning to write.

### Phase 2: Draft the Content

Reference the style guide at `references/style-guide.md` and examples in `references/blog-examples/` for calibration.

When writing:
1. Start with a strong opening statement establishing the thesis
2. Use personal voice and first-person perspective where natural
3. Include relevant personal anecdotes or professional experience if applicable
4. Structure with clear subheadings (###) every 2-3 paragraphs
5. Keep paragraphs short (2-4 sentences)
6. Weave in research materials naturally, not as block quotes
7. End with reflection, call-to-action, or forward-looking statement

### Phase 3: Review and Iterate

Present the draft and gather feedback. Iterate until the user confirms satisfaction.

### Phase 4: Publish to Notion (REQUIRED)

When the draft is complete (even if not yet finalized), publish to the TS Notes database
with `scripts/notion_publish.py`（等效替换宿主 Notion 集成）:

```bash
python3 ~/.codex/plugins/glm-content/skills/glm-blog-writer/scripts/notion_publish.py \
  output/draft.md                      # 需 NOTION_TOKEN；同时自动存本地副本
python3 …/notion_publish.py draft.md --dry-run   # 先看载荷不发送
```

**Notion Publication Details（发布契约，与源 skill 一致）:**
- Database: "TS Notes" (data source ID: `04a872be-8bed-4f43-a448-3dfeebc0df21`)
- **Type property**: `Writing`
- **Project(s) property**: Link to "My Writing" project (page URL:
  `https://www.notion.so/2a5b4629bb3780189199f3c496980c0c`，页面 ID
  `2a5b4629-bb37-8018-9199-f3c496980c0c`）
- **Note property**: The title of the blog post
- **Content**: The full blog post content（Markdown → Notion 块）

**CRITICAL（本地化后的失败判据）**: NOTION_TOKEN 就绪时，内容未入 Notion 仍视为
**失败**——终稿必须发布。token 缺失时脚本 exit 2 并自动把带日期的终稿存到
`output/blog-writer/`：此时向用户**如实转述**「未入 Notion + 已存本地 + 配置
token 的三步指引」，不得谎报已发布；配置后重跑即可。

### Phase 5: Finalize to Examples Library (Post-Outcome)

When the user confirms the draft is **final**:

1. Save the finalized post to the user's working directory `output/blog-examples/`
   with filename format `YYYY-MM-DD-slug-title.md`.
2. Check the examples library count（`scripts/manage_examples.py` 查看插件内
   示例库状态）:
   - If exceeding 20 examples, ask user permission to remove the 5 oldest
   - Sort by filename date prefix to identify oldest files

The post-outcome is considered **successful** when the final draft is saved（本地
`output/blog-examples/`；用户显式要求时才拷贝进插件目录扩充风格库）.

## Success Criteria

| Outcome | Success | Failure |
|---------|---------|---------|
| Primary | User receives requested content AND it is added to TS Notes with Type=Writing and Project=My Writing（token 就绪时）| Content delivered but NOT added to Notion, and the user was not clearly told + locally saved |
| Post-outcome | Final draft saved to `output/blog-examples/` | Final draft not saved when user confirms it's final |

## The Writer's Writing Style Profile

### Voice & Tone
- **Direct and opinionated**: State positions clearly, even contrarian ones
- **Conversational**: Write like speaking to a colleague - accessible without being simplistic
- **First-person when sharing experience**: Use "I" naturally for personal insights
- **Authentic skepticism**: Willing to criticize trends when warranted

### Structure Patterns
- **Strong opening thesis**: Open with a clear, often bold statement
- **Subheadings throughout**: Use `###` format liberally to break up content
- **Short paragraphs**: Rarely more than 3-4 sentences
- **Personal anecdotes woven in**: Illustrate points with real examples
- **Practical takeaways**: Provide actionable insights, not just theory
- **Reflective conclusion**: End with call-to-action or forward-looking hope

### Length & Format
- Target: 800-1500 words
- Markdown format with headers and emphasis
- Minimal bullet points in prose - prefer flowing sentences

### Vocabulary Markers
- Uses "leverage" for tools/technology
- Says "that said" for transitions
- Comfortable with direct statements like "this is useless" or "boy was I wrong"
- Uses contractions naturally (I've, doesn't, won't)
- Avoids corporate jargon while maintaining professionalism

### Thematic Elements
- AI as tool, not replacement
- Practical over theoretical
- Human-centered technology
- Honest assessment of what works and what doesn't

## Resources

### references/style-guide.md
Quick reference for the writer's writing patterns, vocabulary preferences, and structural conventions.

### references/blog-examples/
Seven example blog posts demonstrating the writer's writing style. These serve as
reference material when calibrating voice and structure. New finalized posts expand
this library over time（落用户 `output/blog-examples/`）.

### scripts/
- `notion_publish.py` — Notion 发布（等效替换宿主集成；纯标准库）
- `manage_examples.py` — 示例库管理（列表 / 超限修剪建议；`prune --execute` 才删）
