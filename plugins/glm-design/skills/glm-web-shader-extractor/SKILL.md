---
name: glm-web-shader-extractor
metadata:
  author: Z.AI
  version: "1.0.0"
description: >
  Extract WebGL / Canvas / Shader visual effects from a web page,
  de-obfuscate them, and port them into a standalone native JS project. Use
  when the user provides a URL and asks to extract shaders, effects,
  animations, canvas visuals, or to replicate a site's background / visual
  effect: 提取shader, 提取特效, 提取动画效果, 提取canvas效果, 复刻某网站的
  视觉效果, 把这个网站的背景效果扒下来, extract the shader from this site,
  replicate this visual effect. Fully local: no SDK, no API key, no cloud
  calls. One-MB-plus bundles never enter the model context - a
  zero-dependency extractor CLI scores and lands them to disk first.
license: MIT. LICENSE.txt has complete terms
---

# GLM Web Shader Extractor

从网页提取 WebGL/Canvas/Shader 特效，反混淆并移植为独立项目。本文件是路由
中枢：WHEN 用哪条命令、HOW 执行、WHAT 检查退出码。所有命令在技能目录下执行
（`scripts/...` 为相对路径）。细节文档按需读取，默认不读。

核心原则：

- **先 1:1 复刻，确认正确后再考虑简化框架**
- **全程自主执行，不中断用户** —— 提取是只读操作。除 Phase 6 简化提议与
  Phase 7 报告询问外，所有步骤自动完成；遇到问题自行判断最佳方案继续推进。

## Environment (run once)

```bash
bash scripts/setup.sh        # 体检 node / python3 / playwright / 网络；不安装任何东西
```

需要：node ≥ 18（渲染路径）、python3（提取器路径）、curl。Playwright 缺失
不阻断 —— 首次运行 `fetch-rendered-dom.mjs` 会自动安装（优先探测全局已装，
否则 pnpm 优先、npm 兜底安装到 `~/.cache/playwright-runner/`）。

## Command table

| 目标 | 命令 |
|---|---|
| 渲染后 DOM + canvas 元数据（首选） | `node scripts/fetch-rendered-dom.mjs 'URL' [/tmp/rendered]` |
| 无 GPU / 截图全黑 / WebGL 报错时的兜底 | 同上追加 `--swiftshader` |
| 原始静态 HTML | `curl -s -L --compressed 'URL' > /tmp/page.html` |
| bundle 关键词 + 技术栈扫描 | `bash scripts/scan-bundle.sh /tmp/main.js [更多.js...]` |
| GLSL 提取（大 bundle 不进上下文） | `"${GLM_SHADER_EXTRACTOR_PYTHON:-python3}" scripts/extract-shaders.py /tmp/main.js [更多.js...]` |
| 提取器落盘目录指定 | 同上追加 `--out /tmp/extracted` |

## Exit codes

| Code | 含义 | 动作 |
|---|---|---|
| 0 | 成功 | 读摘要输出，按 Phase 推进 |
| 1 | 运行错误（fetch：URL 不可达 / 浏览器启动失败；scan / extract：文件不存在或无命中） | fetch 失败 → 先 `--swiftshader` 重试一次；仍失败 → 降级为纯 curl 模式（跳过 DOM 渲染，仅静态 HTML + JS bundle 分析，Phase 2 标注可能缺 canvas-info）。不要停下来询问用户 |
| 2 | extract-shaders.py：目标文件读不到 | 检查路径/权限后重试一次；连续失败即报告，不轰炸 |

## Workflow（Phase 0–7）

### Phase 0 环境检查（首次）
`bash scripts/setup.sh`。失败项自行修复（用户目录安装、国内镜像），不询问。

### Phase 1 获取源码（并行执行）

```bash
node scripts/fetch-rendered-dom.mjs 'URL'
# → /tmp/rendered/: dom.html, canvas-info.json, webgl-info.json,
#    console.log, screenshot.png, network.json
curl -s -L --compressed 'URL' > /tmp/page.html
```

fetch 失败 → 先重跑一次（触发自动修复安装）；再失败 → `--swiftshader`
一次；仍失败 → 降级纯 curl 模式继续工作。从 network.json 与 page.html 交叉
提取 JS URL，批量下载到 /tmp/（grep 组合见 references/config-extraction.md）。

### Phase 2 技术栈识别

canvas-info.json 的 `dataEngine` 字段：

- `"three.js rXXX"` → Three.js（r170+ 可能是 TSL → references/tsl-extraction.md）
- `"Babylon.js vX.X"` → Babylon.js
- `null` → bundle 含 createShader/shaderSource → Raw WebGL / PixiJS；
  含 `getContext('2d')` 且无 WebGL 调用 → 2D Canvas（→ references/porting-strategy.md § 2D Canvas）
- 无 canvas → CSS/SVG 动画

URL 或 HTML 特征命中已知平台 → 直接跳转专用工作流（跳过通用 Phase 3–4）：

- `unicorn.studio` → references/unicorn-studio.md（Firestore REST 直取配置 + shader）
- `shaders.com` → references/shaders-com.md（Nuxt payload + XOR 解码 + TSL→GLSL）

扫描确认：`bash scripts/scan-bundle.sh /tmp/*.js` → 特征速查
references/tech-signatures.md。

### Phase 3 配置提取

1. 搜索公开 API → 直接获取（返回可能编码 → references/encoded-definitions.md）
2. Nuxt payload / `__NEXT_DATA__` / HTML 内嵌 JSON
3. JS bundle 默认值

详见 references/config-extraction.md。**配置值必须从源站提取，不猜测。**

### Phase 4 Shader 代码提取（大 bundle 不进上下文）

```bash
"${GLM_SHADER_EXTRACTOR_PYTHON:-python3}" scripts/extract-shaders.py /tmp/main.js
```

stdout 只输出紧凑摘要（数量 / vertex-fragment 判定 / uniforms 清单 / `${}`
模板占位符 / TSL 信号），完整 shader 已落盘到 `--out` 目录。按摘要决定读哪些
落盘文件；要 bundle 局部上下文时用定点 grep（如
`grep -o 'uniform vec2 [a-zA-Z_]*' /tmp/main.js | sort -u`），**绝不整读
1MB+ bundle**。反混淆规则与 minified 符号推断 → references/extraction-workflow.md。

### Phase 5 移植

纯 2D 全屏 shader → 原生 WebGL2（零依赖）；3D / PBR / GPGPU → 保留原始框架
（CDN importmap）；不确定 → 先用原始框架，Phase 6 再评估。
详见 references/porting-strategy.md。

### Phase 6 简化评估（唯一用户决策点之一）

移植完成后自行验证（打开页面截图对比原站）。效果正确且存在简化空间 →
**向用户提议**简化方案，由用户决定；绝不自动执行。

### Phase 7 提取报告（询问用户）

完成后**询问**是否生成 `EXTRACTION-REPORT.md`（会消耗额外 token 回顾历史）。
结构：目标效果一句话 / 提取思路与时间线（每迭代问题→修复）/ 场景结构 /
最终渲染管线（pass 列表）/ 关键资源文件 / 关键经验表（经验/影响/沉淀位置）/
剩余已知差异 / 技术栈（原始 vs 移植）。报告放项目目录内。

## Hard rules

1. **先 1:1 复刻再简化**：Phase 6 之前禁止任何顺手优化。
2. **全程自主**：仅 Phase 6 提议、Phase 7 询问两个用户触点，其余步骤不中断。
3. **配置值、参数必须来自源站/源码**：不猜测、不编造（猜错实例：颜色差 60 倍、图案完全不同）。
4. **禁止手动调参补偿视觉差异**：排查颜色空间、噪声实现、时间基准等根因；
   手动调参在其他参数组合下会崩溃。
5. **大 bundle 永不整读入上下文**：extract-shaders.py 摘要 + 落盘文件 +
   定点 grep 三件套是唯一打开方式。
6. **产物可追溯**：提取出的 shader / 配置标注来源（URL / 文件 / 特征定位）。

## References（按需读取，默认不读）

| 需要 | 读 |
|---|---|
| 识别框架（Three.js / WebGL / PixiJS 特征） | `references/tech-signatures.md` |
| 反混淆规则 + 提取工作流 + 符号推断 | `references/extraction-workflow.md` |
| 配置参数提取（API / payload / 内嵌） | `references/config-extraction.md` |
| Three.js TSL 节点 shader 重建 | `references/tsl-extraction.md` |
| 编码 / 加密配置解码 | `references/encoded-definitions.md` |
| onBeforeCompile GLSL 注入陷阱 | `references/shader-injection.md` |
| 移植框架选择 + 项目结构 | `references/porting-strategy.md` |
| **Unicorn Studio** 专用流程 | `references/unicorn-studio.md` |
| **shaders.com** 专用流程 | `references/shaders-com.md` |
| 环境故障（网络 / Playwright / WebGL） | `references/fallback.md` |

默认只读本文件。没有匹配理由不打开 reference。
