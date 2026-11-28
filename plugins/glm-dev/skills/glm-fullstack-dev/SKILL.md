---
name: glm-fullstack-dev
description: "Fullstack web development with Next.js 16, TypeScript, Tailwind CSS 4, shadcn/ui, Prisma ORM for locally deployed Codex agents. Use when: building web apps, creating UI components, setting up database schemas, implementing API routes, adding websocket/socket.io support, fullstack project scaffolding, frontend or backend development, Next.js apps. 触发场景：全栈开发 / Next.js 应用 / 建网站 / 写组件 / 数据库 schema / API 路由 / websocket 实时应用 / 前端或后端开发。"
metadata:
  version: "1.0.0"
---

# Fullstack Web Development Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-dev/`；本技能目录：
  `~/.codex/plugins/glm-dev/skills/glm-fullstack-dev/`。
- **源 skill 为云端沙箱规范**（bun + Caddy 单端口网关 + z-ai-web-dev-sdk +
  自动 dev server/dev.log + 预览面板 + Agent Browser）。本插件按**等效替换表**
  逐项改写为本地 macOS 形态：`pnpm`（pn/pnpx）管理 Node.js 依赖、直连多端口、
  本地 Ollama 充当 LLM 后端、`@playwright/cli`（用户已全局安装）承担浏览器自验。
- **z-ai-web-dev-sdk 等效替换（源 skill 明文要求 backend-only 使用该 SDK）**：
  用户本地不部署该 SDK。后端 AI 能力一律改为调用本地 Ollama 的 OpenAI 兼容端点
  `http://localhost:11434/v1/chat/completions`，在 Next.js API Route / Route Handler / 服务端
  mini service 内用 `fetch` 直调即可——**纯标准库/内置 fetch，零额外依赖**；
  不需要 AI 的功能直接写业务逻辑。**任何 LLM 调用绝不放客户端组件**（密钥与
  性能原因，沿源 skill 的 backend-only 铁律）。跨机 Ollama 用
  `http://<Ollama机IP>:11434/v1`（见 README「远程 Ollama」）。
- 环境基线（用户 macOS）：`node` 位于 `/opt/node.js/24.16.0/bin`，`pnpm/pn/pnpx`
  全局可用，包一律 `pn install` / `pnpx <bin>`；Java 用 maven、Python 用 uv、
  Go 在 `/opt/go/1.26.0`。**不用 bun**——源 skill 全部 bun 命令已替换为 pnpm。
- 运行产物（源码、`db/`、生成文件）落**用户项目目录**；插件目录只读。

### 等效替换总表（源沙箱 → 本地）

| 源 skill 沙箱机制 | 本地等效 | 说明 |
|---|---|---|
| `curl https://z-cdn.chatglm.cn/fullstack/init-fullstack.sh \| bash` | 本插件「初始化」节命令序列 | 云端初始化脚本不可达；用 pnpm 脚手架 + shadcn/ui + prisma 初始化 |
| `bun run dev`（系统自动跑） | 用户自己跑 `pnpm dev`（端口 3000） | Codex 不代跑常驻进程；可建议用户开第二个终端 |
| `bun run lint` / `bun run db:push` | `pnpm lint` / `pnpm prisma db push` | 命令名 pnpm 化 |
| `z-ai-web-dev-sdk`（backend only） | 本地 Ollama `/v1/chat/completions` fetch | 见上；零 SDK、零 API key |
| Caddy 单端口网关 + `XTransformPort` query | **直连端口** | 本地无网关；`fetch('http://localhost:3030/api/test')` 合法 |
| 预览面板 / Open in New Tab | 用户浏览器直接 `http://localhost:3000` | 本地服务用户可达 |
| `/home/z/my-project/dev.log` | dev server 终端输出 + `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` 探活 | 只看最近输出 |
| Agent Browser 交付自验 | `@playwright/cli`（`pnpx playwright ...`） | 用户已装 0.1.25；命令见「交付自验」节 |
| 「只能写 `/` 路由」 | 本地放开，可写任意路由 | 沙箱预览面板限制；保留「`/` 为唯一用户入口」的默认约定 |

---

## 初始化（动手前先做）

**已有项目**（目录里有 `package.json` + Next.js）：直接沿用，不重建脚手架。

**新项目**（等效替换源 skill 的 init 脚本）：

```bash
pnpm create next-app@latest my-app --typescript --app --tailwind --eslint --src-dir
cd my-app
pnpx shadcn@latest init -d            # shadcn/ui（New York 风格）
pnpx shadcn@latest add button card input dialog dropdown-menu  # 按需补
pn add @prisma/client prisma && pnpx prisma init --datasource-provider sqlite
pn add zustand @tanstack/react-query next-themes socket.io socket.io-client
```

栈基线（与源 skill 一致）：**Next.js 16 App Router + TypeScript 5（不可换）**；
Tailwind CSS 4 + shadcn/ui（New York + Lucide 图标）；Prisma ORM（SQLite）；
本地内存缓存（不引 Redis/MySQL）；NextAuth.js v4 可用；Zustand（客户端）+
TanStack Query（服务端状态）。用户点名其他库时先解释默认栈收益，再给栈内等价方案。

---

## 重要 UI 规则

- 优先复用 shadcn/ui 组件（`src/components/ui/` 已存在的组件不重造）。
- 卡片对齐与留白：内容 `p-4`/`p-6`、间距 `gap-4`/`gap-6` 保持一致。
- 长列表：`max-h-96 overflow-y-auto` + 自定义滚动条样式。

## 开发环境（本地形态）

- **dev server 由用户运行**：`pnpm dev`（端口 3000）。Codex 不代跑常驻进程；
  需要时提示用户开终端执行，再以 `curl` 探活。
- 代码质量用 `pnpm lint`；**不要** `pnpm build`（源 skill 同禁，dev 即验证）。
- **LLM 调用只在服务端**（API Route / Route Handler / mini service）。
  本地 Ollama 直调示例（Route Handler）：

```ts
// src/app/api/chat/route.ts
export async function POST(req: Request) {
  const { messages } = await req.json();
  const r = await fetch(process.env.OLLAMA_URL ?? "http://localhost:11434/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: process.env.OLLAMA_MODEL ?? "<本地模型名>", messages }),
  });
  return Response.json(await r.json());
}
```

- **日志查看**（等效替换源 dev.log）：看用户终端里 dev server 的最近输出；
  代码完成后探活：`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`，
  非 200 时再看终端报错。

## Prisma 与数据库

1. 编辑 `prisma/schema.prisma` 定义模型（**primitive 字段不可为 list**；schema 放
   `prisma/`，db 文件放 `db/`）。
2. `pnpm prisma db push` 推送到 SQLite。
3. 服务端用 `import { db } from '@/lib/db'` 取 Prisma Client。

## Mini Service（独立小服务）

需要时（如 websocket 服务）建在 `mini-services/`，每个小服务：

- 独立 Node 项目 + 自己的 `package.json` + 固定端口（如 `mini-services/chat-service/index.ts`）。
- `pnpm dev` 启动，命令支持文件变更自动重启（`node --watch` 或
  `tsx watch index.ts`）。
- **本地无 Caddy 网关：前端直连各服务端口**（`fetch('http://localhost:3030/api/test')`、
  `io('http://localhost:3030')` 均合法）。若日后要挂反代/网关，再用相对路径
  （`fetch('/api/test')` + 网关自己的端口转发规则，源 skill 的 `XTransformPort`
  query 只是那台沙箱网关的私有约定，本地不需要）。

## WebSocket / Socket.io

实时通信一律 socket.io：后端逻辑独立 mini service + 固定端口（如 3003），前端
`io("http://localhost:3003")` 直连。参考示例可在 `examples/` 目录放 demo。

## 代码风格

- TypeScript 严格类型贯穿；ES6+ import/export；`'use client'` / `'use server'`。
- 优先既有组件与 hooks；shadcn/ui 优先于手写实现。
- 交付前跑 `pnpm lint`。

## 样式与 UI/UX 标准（沿用源 skill）

- shadcn/ui 优先；**非用户点名不用 indigo/blue**；必须响应式（`sm:` `md:` `lg:` `xl:`）。
- 白底之上渲染；要别的底色用 wrapper 元素加 Tailwind 背景类。
- 色彩用 Tailwind 变量（`bg-primary`/`text-primary-foreground`/`bg-background`）。
- light/dark 用 `next-themes`；字号字重层级一致。
- **Sticky Footer 强制**：根容器 `min-h-screen flex flex-col` + footer `mt-auto`；
  内容超视口时 footer 自然下推（不悬浮、不遮挡）；iOS 安全区尊重 inset。
- **无障碍强制**：语义化 HTML（`main/header/nav/section/article`）、ARIA、
  `sr-only`、图片 alt、键盘可达。
- 交互元素有 loading 态（spinner/skeleton）、清晰错误信息、Toast 反馈、
  克制的 Framer Motion 过渡与 hover 反馈。
- 移动优先：触控目标 ≥ 44px。

## 交付自验（等效替换源 Agent Browser，强制）

「编译过 / dev server 起来了」**不是完成证据**。用户已全局安装 `@playwright/cli`
（`pnpx playwright`）。交付前必须：

1. **探活**：`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` 为 200。
2. **截图验渲染**（@playwright/cli）：

```bash
pnpx playwright screenshot --wait-for-timeout 3000 \
  --viewport-size "1280,800" http://localhost:3000 /tmp/page.png
pnpx playwright screenshot --viewport-size "390,844" http://localhost:3000 /tmp/page-mobile.png
```

   确认非白屏、无 Error Boundary、无 hydration 崩溃（看终端 dev server 日志）。
   Read 截图核对信息；无 Read 能力时报告文件路径让用户确认。
3. **交互金路径**：核心按钮/表单/导航逐一点过（可用 playwright codegen 生成脚本
   后执行，或明确请用户人工过一遍并列出已验/未验项）。
4. **数据与实时链路**：数据驱动功能确认前端真的收到后端数据（非永久 skeleton）；
   websocket 功能确认消息端到端流动。
5. **修复重验**：发现坏交互/报错/缺数据/布局缺陷 → 修根因 → 重跑本环，直到
   干净且每个核心交互可用。
6. **诚实报告**：确实无法在浏览器验证的流程要明说，不谎报成功。
