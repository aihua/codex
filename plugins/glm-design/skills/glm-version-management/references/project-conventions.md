# 项目目录与资源规则（glm-version-management 按需参考）

> 本文档是 SKILL.md 的深化参考，默认不读。需要目录结构细则、资源落盘
> 规则、小样文件规则、多项目管理、提交门禁脚本原文时才打开。

## 1. 与设计同插件技能的衔接

本 Skill 与 glm-visual-design-foundations / glm-ui-ux-pro-max 设计插件
**并列协作**：设计插件负责设计产出（场景、风格、版式、quality 纪律），
本 Skill 负责落盘与版本管理。二者的协同过程：

```text
设计插件路由 → 场景（portfolio / deck / prototype 等）
→ 【写文件前】按 SKILL.md「路径硬规则」先建 我的项目/{项目名}/
→ 产出 .html / .jsx / .tsx / .vue → 文件【直接写入】我的项目/{项目名}/
→ 设计插件的 quality 纪律通过（未安装设计插件则跳过此步）
→ 本 Skill（资源校验 → git → meta.json → 版本卡片）
```

- **触发不依赖设计插件。** 本 Skill 按文件类型触发：只要产出**或修改**
  入口文件（.html / .jsx / .tsx / .vue）就必须走本 Skill，与任务是否经
  过设计路由无关——包括未走任何设计流程、直接裸改已有 HTML 文字/颜色的
  情况（此时跳过 quality 纪律，直接 资源校验 → git → meta.json → 版
  本卡片）。
- 设计同插件技能未加载（沙箱内 `~/.codex/plugins/` 下没有
  glm-visual-design-foundations / glm-ui-ux-pro-max）时**自动降级**：跳过
  quality 纪律，落盘与版本流程照常执行——版本管理不因缺设计插件而降级。
- **禁止**设计产出在质量纪律未通过时 commit 或输出版本卡片；**禁止**在
  本 Skill 未完成的情况下把 HTML 网页项目视为已交付（仅贴代码块、不落
  盘、不写 `我的项目/` 均不算交付）。

职责分界：

| 维度 | 设计插件 | 本 Skill |
|------|--------------|----------|
| 场景、风格、版式、文案语言 | ✅ | — |
| quality 纪律、设计合规注释 | ✅ | — |
| 项目目录、assets 落盘、git 版本 | — | ✅ |
| `meta.json`、版本卡片 | — | ✅ |
| 对用户表述 | 设计结果说明 | 仅「已保存为 V{n}」+ 路径 |

commit 摘要建议带上场景，便于用户识别，例如：`V2: 首页 hero 改版
（portfolio）`、`V3: 基于 V1：换国际主义风格（landing-page）`。

## 2. 目录结构与资源规则

### 2.1 项目目录结构

```
工作区根目录/（Codex 启动时的 cwd）
├── 我的项目/
│   └── {项目名}/
│       ├── .git/
│       ├── .gitignore       ← 排除 meta.json 和 style-samples*.html
│       ├── meta.json        ← 版本元数据（不进 Git）
│       ├── style-samples*.html ← 设计方向小样（不进 Git，可选，可多轮）
│       ├── index.html       ← 主入口（进 Git，路径因项目而异）
│       ├── ...              ← 其他代码文件（进 Git）
│       ├── assets/          ← 资源文件（进 Git，随版本快照一起追踪）
│       └── export/          ← export 导出产物（进 Git，固定图片类项目用）
└── （用户提供的资源所在路径，若工作区有 upload/ 目录则优先从中查找）
```

### 2.2 文件结构规则

**核心原则：项目目录自包含，所有文件（代码 + 资源 + export 产物）都进
Git 追踪。**

- **单文件 vs 多文件：** 不强制单文件（内联 JS/CSS），也不鼓励一律多文
  件。简单落地页、H5、单页展示 → 可单文件 `index.html`；需复用样式/脚
  本、组件较多 → 可多文件（如 `index.html` + `style.css` + `main.js`）。
- 代码中通过**相对路径**引用：`assets/{文件名}`，本地 file:// 直开天然
  可解析，Agent 禁止手写任何云端/OSS/CDN 地址。
- 资源使用语义化英文命名（如 `hero-banner.png`），避免中文和空格。
- `assets/` **进入 Git 追踪**——每个版本的快照包含当时的全部资源，恢复
  历史版本时代码和资源一起回退，确保任意历史版本可完整打开。

### 2.3 资源的处理（本地落盘，必做）

**禁止** HTML 写 `assets/xxx` 而磁盘无对应文件（常见裂图原因：只写了
路径，未落盘实际文件）。

1. 找源文件：用户给出的本地路径优先；工作区存在 `upload/` 目录时从中查
   找（`find upload`、`ls -lt upload` 最近放入）；都没有 → 请用户提供
   路径，**禁止编造**
2. `mkdir -p 我的项目/{项目名}/assets`
3. `cp {源路径} 我的项目/{项目名}/assets/{名}`——`{名}` 与 HTML 中
   `assets/{名}` **完全一致**（HTML 已写好则按引用名复制重命名）
4. 再写/改 HTML 引用；多张图逐步 cp
5. **提交前校验**（有 MISSING 不得 commit / 输出版本卡片）：

```bash
cd 我的项目/{项目名}
grep -ohE 'assets/[a-zA-Z0-9_.-]+' index.html 2>/dev/null | sort -u | while read -r ref; do
  [ -f "$ref" ] || echo "MISSING: $ref"
done
```

6. 无 MISSING 后按 SKILL.md §3.3 创建版本并输出版本卡片

### 2.4 资源来源（三种，落盘规则相同）

| 来源 | 典型顺序 | Agent 动作 | 是否新版本 |
|------|----------|------------|------------|
| **用户提供** | 先 HTML 后给图 / 先给图后 HTML | 从用户路径 `cp` 到 `assets/`，引用与文件名一致；后给图时按现有 HTML 引用名命名 | 只 cp、未改代码 → ❌；改了 HTML 引用 → ✅ |
| **Agent 搜图** | 用户要配图、联网找图（走 glm-web 插件中的 glm-web-search / glm-web-reader 技能（若已安装）CLI） | 下载到 `assets/{名}`（禁止仅写外链 URL）；再写/改 HTML 引用 | ✅ |
| **Agent 生图** | 用户要配图、生成图片 | 写入 `assets/{名}`（禁止只写 `assets/xxx` 不落盘）；再写 HTML | ✅ |

**共用：** 凡 HTML 含 `assets/` 引用，提交前必做上述校验；无文件则补落盘
或改引用，禁止带 MISSING commit。

**先有 HTML 无图：** 可用占位文案/样式，但**不要**写不存在的
`assets/xxx`；用户给图或 Agent 补图后再写真实引用并 cp。

### 2.5 跨版本保留用户图片（重要）

用户已引用在 `assets/` 中的图片，在后续**自然语言 / 预填句式**编辑产生
新版本时：

- 用户**未**要求去掉该模块、**未**要求换图 → **必须保留**原有
  `assets/` 文件及 HTML 中的 `assets/...` 引用，勿删除、勿改路径、勿要
  求用户重传
- 仅改样式、文案、布局等 → 只改代码文件，不动 `assets/`（除非用户明确
  要求替换资源）
- `git add .` 会自动将未改动的 `assets/` 文件纳入新版本快照（Git 自动复
  用未变文件，不重复存储），无需手动处理

### 2.6 小样文件保留规则

若正式构建前存在小样阶段（先生成一个包含多个编号设计方向的 HTML 供用
户选择），小样 HTML 必须移入 `我的项目/{项目名}/` 下保存，命名为
`style-samples.html`；用户不满意要求重新出方向时，后续轮次递增命名为
`style-samples-2.html`、`style-samples-3.html`，禁止覆盖已有小样文件。
所有小样文件禁止命名为 `index.html` 或其他入口文件名。小样以版本卡片形
式供用户预览和选择。`style-samples*.html` 已在 `.gitignore` 中通配排
除，不进 Git 版本历史、不计入项目版本号。禁止在小样文件落盘到项目目录
之前删除小样源文件/源文件夹。

## 3. 提交前路径门禁（commit / 版本卡片前最后门禁）

```bash
# 提交前路径门禁（在工作区根目录执行）
cd {工作区根目录}

# (a) 项目目录内必须存在至少一个入口文件（不限定 index.html，
#     prototype.html 等同样有效）
ls "我的项目/{项目名}/"*.html "我的项目/{项目名}/"*.jsx \
   "我的项目/{项目名}/"*.tsx "我的项目/{项目名}/"*.vue 2>/dev/null | grep -q . \
  || { echo "ERROR: 我的项目/{项目名}/ 内没有入口文件，禁止 commit / 版本卡片"; }

# (b) 工作区根目录及其他位置不得散落入口文件
find . -maxdepth 2 -not -path "./我的项目/*" \
  \( -name '*.html' -o -name '*.jsx' -o -name '*.tsx' -o -name '*.vue' \) \
  | while read -r f; do
      echo "STRAY: $f → 必须执行 mv \"$f\" \"我的项目/{项目名}/\" 后重新校验"
    done
```

任一项报 ERROR / STRAY → **禁止** commit 与版本卡片，先纠正路径再重跑门
禁（配合 `references/version-operations.md` §5 的资源校验一起跑）。

## 4. 多项目管理

### 4.1 识别当前项目

按优先级判断：

1. 用户自然语言中明确提到的项目名
2. 本 session 中最近操作的项目
3. 均无法判断 → 扫描 `我的项目/` 子目录，读各项目 `meta.json`，列出项目
   并追问

（原宿主"前端传入的当前 tab"在本地 Codex 不存在，该优先级位移除。）

### 4.2 切换项目

读取目标项目 `meta.json`，告知用户：「已切换到项目：{项目名}，当前版本
V{n}」。

### 4.3 非项目任务

非入口文件产出的任务不触发任何项目或版本操作。
