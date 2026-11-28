# 环境故障排查（网络 / Playwright / WebGL）

## Cause #1 — Codex 命令沙箱禁网

**症状**：Codex 内 `curl` / `fetch-rendered-dom.mjs` 全部报
`Could not resolve host`，而同一命令在用户自己的终端正常；对话本身流畅。

**定性**：Codex 命令沙箱默认禁网（macOS Seatbelt / Linux Landlock）。
Codex 到模型 provider 的连接不受影响，只有工具命令被拦。

**修复**（config.toml）：

```toml
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true
```

重启 Codex 后在会话内复测 `curl -I https://www.bing.com`。**macOS 注意**
（openai/codex#10390）：部分版本 Seatbelt 会静默忽略 `network_access`；
复测仍失败即命中该 bug，改用 `codex --sandbox danger-full-access` 启动
（`--full-auto` 不放行网络）。

## Cause #2 — Playwright / Chromium 安装失败

**症状**：`fetch-rendered-dom.mjs` 首次运行卡在安装阶段，或报
`playwright package still not importable after install`。

**处置**（按序尝试）：

1. npm 权限问题 → 脚本已安装到用户缓存目录
   `~/.cache/playwright-runner/`（`--prefix` 等效），不需要 root；
2. 网络/镜像 → 脚本已自动重试 npmmirror 镜像；仍失败则手动执行：
   ```bash
   cd ~/.cache/playwright-runner
   pnpm add playwright                # 或 npm install playwright
   pnx playwright install chromium    # 或 npx playwright install chromium
   PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright \
     npx playwright install chromium   # Chromium 下载慢时的镜像形态
   ```
3. 全局已有 playwright 库（NODE_PATH 可解析）时脚本自动跳过安装直接使用。

**降级**：Playwright 彻底装不上 → 纯 curl 模式（跳过 DOM 渲染，仅静态
HTML + JS bundle 分析），Phase 2 标注可能缺 canvas-info（dataEngine 拿
不到，技术栈识别退回 bundle 特征扫描）。

## Cause #3 — Headless 无 GPU，WebGL 上下文创建失败

**症状**：console.log 出现
`WebGL context could not be created` / `Error creating Curtains instance`；
canvas-info.json 里 `0 canvas(es) found`；截图纯黑。

**定性**：headless Chromium 缺 GPU 是**环境问题**，先怀疑环境再怀疑提取
逻辑。处置：加 `--swiftshader` 重跑（软件渲染 GL）：

```bash
node scripts/fetch-rendered-dom.mjs 'URL' --swiftshader
```

验证顺序：看 console 是 shader/runtime 错误还是 WebGL context 创建失败
→ 看 DOM 是否真的生成 canvas → swiftshader 截图 → 与原站首屏构图对比。

## Cause #4 — 纯前端渲染页面 curl 拿不到内容

**症状**：`/tmp/page.html` 只有骨架 `<div id="app"></div>`，无内嵌配置。

**处置**：这是预期形态（JS-only 页面）。渲染态内容靠
fetch-rendered-dom.mjs 的 dom.html；bundle 靠 network.json 抓取后下载分析。
Playwright 也不可用时，从 Google/Bing 的静态缓存页或站点 sitemap 拿入口
JS URL，其余步骤照常（bundle 分析不依赖 DOM 渲染）。

## Cause #5 — 会话报 403 / stream disconnected（模型后端层）

**症状**：会话启动或进行中报
`403 Forbidden: {"error":"Codex proxy only accepts loopback requests"}` 或
`stream disconnected ... This model requires an Ollama account`。

**定性**：均为**模型后端层**问题（Codex → Ollama 连接），与本插件载荷无关
——提取脚本只连用户给的目标 URL，从不连接模型服务（`localhost`/
`11434`/`/api/` 零引用）。跨机访问 Ollama 的 codex 代理端点会被回环门槛
403 拒绝；触发 Ollama 内置 web 工具会因未登录账号断流。

**处置**（简表，细节见 glm-web-search / glm-web-reader 插件 README 的
「远程 Ollama」节）：方案 A 改通用 `/v1` 端点 + `wire_api = "responses"`；
方案 B `ssh -L 11434:127.0.0.1:11434 user@ollama机` 隧道；方案 C Mac 上
socat/caddy 反代。工具断流则删 `[tools]` 的 `web_search = true`，不要
`ollama signin`。

## Cause #6 — CDN importmap 模板版本核对

**症状**：移植项目加载报 404 或 shader 行为随版本变化（如
`getIBLVolumeRefraction` 签名不匹配）。

**处置**：CDN 模板里的版本必须与提取目标实际使用的一致（canvas-info 的
dataEngine 或 bundle 特征可确认）；核对命令
`curl -sI '<cdn-url>' | head -3`。签名差异案例见 shader-injection.md。
