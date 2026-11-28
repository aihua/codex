---
name: glm-agent-browser
description: "Headless browser automation CLI skill for Codex agents on the user's pnpm-managed Node environment: ports the agent-browser CLI reference (Vercel Labs Rust binary with Node fallback over Playwright) with install commands adapted to pnpm/pn and the already-global @playwright/cli, plus Codex deployment notes. 触发场景：自动化网页操作 / 结构化数据抓取 / 表单填写 / Web UI 测试 / 截图取证。原技能不依赖 z-ai-web-dev-sdk（纯 CLI），等效改造为安装链与部署形态适配，无 SDK 替换点。"
metadata:
  version: "1.0.0"
---

# Browser Automation with agent-browser（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-web/`；本技能目录：
  `~/.codex/plugins/glm-web/skills/glm-agent-browser/`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill（skills/agent-browser）
  为纯 CLI 技能（Vercel Labs agent-browser：Rust 主体 + Node 回退，
  底层 Playwright），**不依赖 z-ai-web-dev-sdk**——无 SDK 替换点；本插件
  的改造是**安装链与部署形态适配**：
  - 安装命令从 npm 改为用户实际的 **pnpm**（`pn install -g agent-browser`；
    npm 兼容亦可）。
  - 用户已全局安装 `@playwright/cli 0.1.25`——`agent-browser install`
    会下载 Playwright 浏览器内核，与现有 Playwright 共存无冲突。
- 多步流程规划与单步执行均由本地模型承担。命令输出务必配合 `--json` 解析。
- 输出落**用户工作目录**（截图/PDF/状态文件）；插件目录只读。
- **技能路由**：纯抓正文（无需交互）→ 同插件技能 glm-web-search 的 fetch；
  深度新闻聚合 → glm-content 插件中的 glm-ai-news-collectors 技能（若已安装）。

## 安装（适配 pnpm 环境）

```bash
# 推荐（用户用 pnpm 管理全局包；pn 是 pnpm 别名）
pn install -g agent-browser     # 或: pnpm install -g agent-browser
agent-browser install            # 下载 Playwright 浏览器内核（一次性）
agent-browser install --with-deps   # Linux 缺系统依赖时

# npm 兼容路径（等效）
npm install -g agent-browser && agent-browser install

# 从源码（Rust 主体需 pnpm build）
git clone https://github.com/vercel-labs/agent-browser
cd agent-browser && pnpm install && pnpm build && agent-browser install
```

## Quick start

```bash
agent-browser open <url>        # 导航
agent-browser snapshot -i       # 交互元素快照（带 @e1/@e2 ref）
agent-browser click @e1         # 按 ref 点击
agent-browser fill @e2 "text"   # 按 ref 填写
agent-browser close             # 关闭
```

## Core workflow

1. Navigate: `agent-browser open <url>`
2. Snapshot: `agent-browser snapshot -i`（返回带 `@e1` 等 ref 的元素表）
3. 用快照里的 ref 交互
4. 导航或 DOM 大改后**重新快照**（ref 随页面重载而变）

## Commands（沿源 skill 全量）

### Navigation
`open <url>` · `back` · `forward` · `reload` · `close`

### Snapshot
```bash
agent-browser snapshot            # 完整可达性树
agent-browser snapshot -i         # 仅交互元素（推荐）
agent-browser snapshot -c         # 紧凑输出
agent-browser snapshot -d 3       # 深度限制 3
agent-browser snapshot -s "#main" # CSS 选择器范围
```

### Interactions（用快照的 @refs）
`click @e1` · `dblclick @e1` · `focus @e1` · `fill @e2 "text"`（清空再输，
推荐）· `type @e2 "text"`（不清空）· `press Enter` / `press Control+a` ·
`keydown/keyup Shift` · `hover @e1` · `check/uncheck @e1` ·
`select @e1 "value"` · `scroll down 500` · `scrollintoview @e1` ·
`drag @e1 @e2` · `upload @e1 file.pdf`

### Get information
`get text @e1` · `get html @e1` · `get value @e1` · `get attr @e1 href` ·
`get title` · `get url` · `get count ".item"` · `get box @e1`

### Check state
`is visible @e1` · `is enabled @e1` · `is checked @e1`

### Screenshots & PDF
`screenshot [path.png]`（`--full` 全页）· `pdf output.pdf`

### Video recording
`record start ./demo.webm` → 操作 → `record stop`（保留会话
cookies/存储；先探索再录制更流畅）· `record restart ./take2.webm`

### Wait
`wait @e1` · `wait 2000`（毫秒）· `wait --text "Success"` ·
`wait --url "/dashboard"` · `wait --load networkidle` ·
`wait --fn "window.ready"`

### Mouse control
`mouse move 100 200` · `mouse down/up left` · `mouse wheel 100`

### Semantic locators（ref 之外的替代定位）
`find role button click --name "Submit"` · `find text "Sign In" click` ·
`find label "Email" fill "user@test.com"` · `find first ".item" click` ·
`find nth 2 "a" text`

### Browser settings
`set viewport 1920 1080` · `set device "iPhone 14"` ·
`set geo 37.7749 -122.4194` · `set offline on` ·
`set headers '{"X-Key":"v"}'` · `set credentials user pass` ·
`set media dark`

### Cookies & Storage
`cookies` · `cookies set name value` · `cookies clear` ·
`storage local [key]` · `storage local set k v` · `storage local clear`

### Network
`network route <url>`（拦截）· `network route <url> --abort`（阻断）·
`network route <url> --body '{}'`（mock）· `network unroute [url]` ·
`network requests [--filter api]`

### Tabs & Windows & Frames
`tab` / `tab new [url]` / `tab 2` / `tab close` · `window new` ·
`frame "#iframe"` / `frame main`

### Dialogs & JavaScript
`dialog accept [text]` / `dialog dismiss` · `eval "document.title"`

### State management
`state save auth.json` / `state load auth.json`（登录态复用）

## Example: Form submission

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# 输出: textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Submit" [ref=e3]
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i
```

## Example: 登录态复用

```bash
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "username"; agent-browser fill @e2 "password"
agent-browser click @e3; agent-browser wait --url "/dashboard"
agent-browser state save auth.json
# 之后: agent-browser state load auth.json && agent-browser open https://app.example.com/dashboard
```

## Sessions（并行浏览器）
`agent-browser --session test1 open site-a.com` ·
`agent-browser --session test2 open site-b.com` · `agent-browser session list`

## JSON 输出（模型解析用）
`--json` 追加：`agent-browser snapshot -i --json` · `get text @e1 --json`

## Debugging
`open example.com --headed`（有头调试）· `console` / `console --clear` ·
`errors` / `errors --clear` · `highlight @e1` · `trace start/stop` ·
`record start ./debug.webm` · `--cdp 9222 snapshot`（CDP 接入）

## Options
`--session <name>`（隔离会话）· `--json` · `--full` · `--headed` ·
`--timeout <ms>` · `--cdp <port>`

## Notes（沿源 skill）

- ref 在单次页面加载内稳定，导航后必变——**导航后重新快照**。
- 输入框一律用 `fill`（清空再输）而非 `type`。
- 元素找不到时先 `snapshot` 找正确 ref。
- 页面未加载完时导航后加 `wait`。
- Linux ARM64 找不到命令时用 bin 目录全路径。

## Reporting Issues
- Skill: https://github.com/TheSethRose/Agent-Browser-CLI
- CLI: https://github.com/vercel-labs/agent-browser
