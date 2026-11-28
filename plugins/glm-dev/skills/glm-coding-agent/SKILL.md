---
name: glm-coding-agent
description: "Coding workflow discipline with planning, implementation, verification, and testing for clean software development, for locally deployed Codex agents. Consult when the user explicitly requests code implementation: the agent provides planning, execution guidance, verification and state-tracking workflows, and stores user-stated preferences in ~/code/memory.md only on explicit request. 触发场景：写代码 / 实现功能 / 编码工作流 / 规划实现步骤 / 验证改动 / 记住我的编码偏好。"
metadata:
  version: "1.0.0"
---

## Codex Deployment Notes（本地 Codex 插件形态）

- 插件安装根目录：`~/.codex/plugins/glm-dev/`；本技能目录：
  `~/.codex/plugins/glm-dev/skills/glm-coding-agent/`。
  下文 `planning.md` 等参考文件均指本技能目录内文件（相对布局与源一致）。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill（SKILL.md + 六个参考文件）
  对厂商 web-dev SDK 标识与常见 LLM SDK import 形态逐字审计**命中零**——纯
  流程指引，无脚本、无网络出口，**无需任何函数级替换**。
- 用户偏好记忆 `~/code/memory.md` 沿用源约定（macOS 本地可用）；
  `mkdir -p ~/code` 首用时创建。
- 源 frontmatter 的 clawdbot 元数据（emoji/requires/os）与 clawic.com homepage
  为上游宿主平台字段，不随包；本插件以 Agent Plugins 1.0.0 清单承载身份。
- **同插件技能路由**：验证环节的「截图建议」可配同插件技能 glm-fullstack-dev 的
  `@playwright/cli` 截图命令；UI 类交付的完整规范走同插件技能 glm-fullstack-dev；
  本插件只管编码工作流纪律。

## When to Use

User explicitly requests code implementation. Agent provides planning, execution guidance, and verification workflows.

## Architecture

User preferences stored in `~/code/` when user explicitly requests.

```
~/code/
  - memory.md    # User-provided preferences only
```

Create on first use: `mkdir -p ~/code`

## Quick Reference

| Topic | File |
|-------|------|
| Memory setup | `memory-template.md` |
| Task breakdown | `planning.md` |
| Execution flow | `execution.md` |
| Verification | `verification.md` |
| Multi-task state | `state.md` |
| User criteria | `criteria.md` |

## Scope

This skill ONLY:
- Provides coding workflow guidance
- Stores preferences user explicitly provides in `~/code/`
- Reads included reference files

This skill NEVER:
- Executes code automatically
- Makes network requests
- Accesses files outside `~/code/` and the user's project
- Modifies its own SKILL.md or auxiliary files
- Takes autonomous action without user awareness

## Core Rules

### 1. Check Memory First
Read `~/code/memory.md` for user's stated preferences if it exists.

### 2. User Controls Execution
- This skill provides GUIDANCE, not autonomous execution
- User decides when to proceed to next step
- Sub-agent delegation requires user's explicit request

### 3. Plan Before Code
- Break requests into testable steps
- Each step independently verifiable
- See `planning.md` for patterns

### 4. Verify Everything
| After | Do |
|-------|-----|
| Each function | Suggest running tests |
| UI changes | Suggest taking screenshot |
| Before delivery | Suggest full test suite |

### 5. Store Preferences on Request
| User says | Action |
|-----------|--------|
| "Remember I prefer X" | Add to memory.md |
| "Never do Y again" | Add to memory.md Never section |

Only store what user explicitly asks to save.

## Workflow

```
Request -> Plan -> Execute -> Verify -> Deliver
```

## Common Traps

- **Delivering untested code** -> always verify first
- **Huge PRs** -> break into testable chunks
- **Ignoring preferences** -> check memory.md first

## Self-Modification

This skill NEVER modifies its own SKILL.md or auxiliary files.
User data stored only in `~/code/memory.md` after explicit request.

## External Endpoints

This skill makes NO network requests.

| Endpoint | Data Sent | Purpose |
|----------|-----------|---------|
| None | None | N/A |

## Security & Privacy

**Data that stays local:**
- Only preferences user explicitly asks to save
- Stored in `~/code/memory.md`

**Data that leaves your machine:**
- None. This skill makes no network requests.

**This skill does NOT:**
- Execute code automatically
- Access network or external services  
- Access files outside `~/code/` and user's project
- Take autonomous actions without user awareness
- Delegate to sub-agents without user's explicit request
