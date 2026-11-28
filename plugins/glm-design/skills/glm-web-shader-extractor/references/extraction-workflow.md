# Shader 代码提取：提取器工作流与反混淆

## 大 bundle 处理原则（无子代理环境）

本插件运行在 Codex 中，**没有子代理（subagent）可用**——原技能「启动
Agent 分析 1MB+ bundle」的做法在此环境等效替换为**工具化提取**：

```bash
# 1. 打分提取：GLSL 字符串自动识别、vertex/fragment 自动判定、落盘
"${GLM_SHADER_EXTRACTOR_PYTHON:-python3}" scripts/extract-shaders.py /tmp/main.js

# 2. 读 stdout 摘要（数量 / 类型 / uniforms / ${} 占位符 / TSL 信号）

# 3. 按需读落盘文件（小文件，可整读）
cat /tmp/extracted-shaders/shader-01-fragment-main.js.glsl

# 4. 要 bundle 局部上下文时定点 grep，绝不整读 bundle
grep -o 'uniform vec2 [a-zA-Z_]*' /tmp/main.js | sort -u
grep -oE '.{80}gl_FragColor.{120}' /tmp/main.js | head -20
```

**关键**：bundle 留在磁盘上，上下文里只进摘要与定点片段。extract-shaders.py
的打分词表覆盖 `precision` / `uniform` / `void main` / `gl_FragColor` /
`gl_Position` / `#version 300 es` / `sampler2D` 等特征；未命中的长字符串会
被过滤（minified 正则字面量的误提取因此天然排除）。

## 深度分析流程（模型侧）

拿到提取摘要后按以下顺序推进：

1. **GLSL Shader 源码**：优先读落盘的 fragment shader（视觉核心），vertex
   shader 多为标准全屏四边形，其次读。摘要里的 `template injections` 列出
   `${Vt}` 这类编译期注入占位符——bundle 里对应变量就是被注入的函数块
   （如噪声库、混合模式库），用
   `grep -oE '.{40}(Vt|fe|gt)[[:space:]]*=[[:space:]]*.{80}' /tmp/main.js`
   定点取证。
2. **渲染相关 JS 类**：canvas/renderer 创建、粒子/几何体管理、
   requestAnimationFrame 循环、鼠标交互——用定点 grep 找
   `getContext|requestAnimationFrame|addEventListener` 的邻域。
3. **符号映射表**：minified 变量名 → 原始含义（见下方速查）。
4. **配置和参数**：默认颜色、尺寸、密度等可调参数（→ config-extraction.md）。

将提取的代码整理到项目目录（如 `extracted/`），按功能分段标注来源。

## 识别 Minified 符号

通过构造参数和方法调用推断：

```javascript
new ??(40, w/h, 0.1, 1000)       → PerspectiveCamera(fov, aspect, near, far)
new ??(-1, 1, 1, -1, 0, 1)      → OrthographicCamera
new ??({canvas, antialias, ...}) → WebGLRenderer
new ??(2, 2)                     → PlaneGeometry(w, h)
new ??(data, w, h, fmt, type)    → DataTexture
new ??(w, h, {minFilter, ...})   → WebGLRenderTarget

??.setRenderTarget()  → renderer
??.getElapsedTime()   → clock
??.setAttribute()     → bufferGeometry
```

## 框架脱壳（React / Vue 等 → Vanilla JS）

Canvas 效果常被 React/Vue 等框架包装。脱壳思路：

1. **找副作用入口**：`useEffect`/`onMounted` 中的 Canvas 初始化代码就是核心逻辑
2. **收集 cleanup**：所有销毁操作（`removeEventListener`、`cancelAnimationFrame`、`observer.disconnect()`）汇总为 `destroy()` 函数
3. **丢弃响应式包装**：Canvas 状态（粒子位置、帧计数等）只在 RAF 内读写，直接用 `let` 变量，不需要 `useState`/`ref` 等响应式容器

原生 API（`IntersectionObserver`、`ResizeObserver`、`matchMedia` 等）不受框架影响，原样保留。

## 反混淆规则

1. **类名**：根据构造参数和方法调用推断
2. **变量名**：根据用途命名（`ringPos`, `particleScale`, `simMaterial`）
3. **Shader 变量**：uniform/varying 名通常未被 minify（`uTime`, `vPosition`）
4. **保留原始 GLSL**：shader 代码通常是完整字符串，直接提取
5. **字符串注入**：`${someVar.noise}` 表示噪声库被注入到 shader 中
