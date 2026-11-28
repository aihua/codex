# 版本操作细则（glm-version-management 按需参考）

> 本文档是 SKILL.md 的深化参考，默认不读。需要 meta.json 完整结构、多入
> 口 / prototype / 固定图片导出的卡片策略、历史版本预览进阶、宿主机制
> 等效映射总表时才打开。

## 1. 宿主机制等效映射总表（原 Z.ai 宿主 → 本地 Codex 形态）

| 原宿主机制 | 本地等效 |
|---|---|
| `send_file` 工具（把版本卡片推送到对话流，含 OSS 预览链接） | 对话内版本卡片：一行「已保存为 V{n}」+ 主入口**本地绝对路径**（用户 file:// 直开）。纯对话输出，不调用任何工具 |
| OSS 预览（后端把 HTML 内 `assets/` 相对路径替换为 OSS 链接） | 本地直开：相对路径原生解析，**禁止**在源码写任何 OSS/CDN URL |
| 多文件 HTML 项目 OSS 预览不可跳转（原已知限制） | 本地形态**不存在**该限制：多页面相对链接 file:// 直开全部可用 |
| 历史版本 OSS 预览（按 tag 扫描） | §4 标准恢复后本地打开；进阶：`git worktree add` 临时挂出只读预览（见 §5），用完 `git worktree remove` |
| `upload/` 云端上传落点 | 用户给出的本地资源路径优先；工作区若有 `upload/` 目录则从中查找；都没有 → 请用户提供路径，禁止编造 |
| 评论编辑 / 参数编辑器（预览区前端生成 MD 指令） | 用户自然语言说出项目名 + 版本号（推荐句式「基于「{项目名}」V{n}版本进行编辑」）；处理规则不变（SKILL.md §3.1） |
| 对话流卡片「基于该版本编辑」按钮（前端预填输入框） | 用户直接输入同一句式；Agent 识别后走 §4.4 合并流程 |
| Design Skill + quality-gate.md | glm-visual-design-foundations / glm-ui-ux-pro-max 同插件技能；未加载自动降级跳过（references/project-conventions.md §1） |
| 云机工作区根目录 | Codex 启动时的本地 cwd |

## 2. meta.json 结构

每个项目一份，记录项目整体状态。通过 `.gitignore` 排除，不进入版本历
史。每次 commit/tag 完成后**必须同步更新**（`latest_version`、追加
`versions[]` 条目、写 `based_on`、写 `summary`），然后才输出版本卡片。

```json
{
  "project_name": "北京旅游网站",
  "latest_version": "v3",
  "is_published": false,
  "published_version": null,
  "domain": null,
  "versions": [
    {
      "id": "v1",
      "timestamp": "2026-05-01T14:30:00+08:00",
      "based_on": null,
      "summary": "首页 + 景点列表"
    },
    {
      "id": "v2",
      "timestamp": "2026-05-05T10:30:00+08:00",
      "based_on": null,
      "summary": "风格变更为国际主义"
    },
    {
      "id": "v3",
      "timestamp": "2026-05-06T14:30:00+08:00",
      "based_on": "v1",
      "summary": "基于 V1：重新设计页面布局"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| project_name | string | 项目名称，Agent 自动生成，用户可修改 |
| latest_version | string | 当前最新版本号（如 "v5"） |
| is_published / published_version / domain | 一期默认 false / null（本地无发布能力，保留字段占位） |
| versions[].id | string | 版本号（如 "v1"，与 git tag 一一对应） |
| versions[].timestamp | string | 创建时间（ISO 8601 带时区，本地时区） |
| versions[].based_on | string \| null | 仅在恢复或基于历史版本编辑时有值，指向基准版本号；普通编辑时为 null |
| versions[].summary | string | Agent 自动生成的一句话变更摘要 |

timestamp 用本地时间生成：`date +%Y-%m-%dT%H:%M:%S%z`（插入冒号成
ISO 8601 时区偏移亦可，保持项目内既有格式一致即可）。

## 3. 多入口与 prototype 双文件交付

### 3.1 多入口文件项目

当项目包含**多个独立入口 HTML 文件**时（例如 `index.html` +
`light.html`，或多个页面）：

1. **所有入口文件必须在同一 commit 中提交**（`git add .` 自然包含全
   部）
2. **版本卡片策略：**
   - 若只有一个**主入口**（其他为辅助），默认只吐主入口
   - 若有显式多交付要求，按要求逐个吐卡片
   - 禁止遗漏：所有 HTML 文件都必须被 git 追踪
3. **禁止**以"目录打包"形式描述交付（本地形态逐文件给路径）

示例（`index.html` 为主入口，`light.html` 为新增变体）：

```bash
# 同一次 commit 包含两个文件
git add index.html light.html assets/
git commit -m "V4: 新增 light 主题变体"
git tag v4
```

版本卡片只吐主入口：项目「北京旅游网站」入口
`/绝对路径/我的项目/北京旅游网站/index.html`。

### 3.2 Prototype 双文件交付（稳定规则）

当任务为原型交付且该版本包含双交付文件（可交互原型 + 流程文档）时：

1. **版本纳入范围（必做）**：本次版本必须同时纳入并提交两个 HTML 文件
   （通常为 `prototype.html` 与 `flow.html`），禁止只提交其中一个。
2. **对话流输出（必做）**：对同一版本号输出版本卡片**两次**，分别指向
   两个单文件，角色标注在项目名后：
   - `项目「企业客户管理后台-prototype」入口：…/prototype.html`
   - `项目「企业客户管理后台-flow」入口：…/flow.html`
3. **禁止项**：禁止把双文件当成目录一次性吐；禁止只吐其中一个并声称
   已完成 prototype 双交付。

### 3.3 固定图片导出项目（小红书卡片等）

对于固定图片输出目标的场景（小红书卡片、封面图、长图），典型流程：

1. **先生成 HTML**（设计阶段产物）→ 按常规保存到
   `我的项目/{项目名}/`
2. **后执行 export** 导出图片（本地截图工具链：浏览器无头截图或设计插
   件的导出能力）→ 导出产物保存到 `我的项目/{项目名}/export/`
3. **版本管理：** HTML 和 `export/` 都进 Git 追踪，同一次 commit
4. **版本卡片策略（必做）：**
   - **第一次：** 吐 HTML 文件（主入口路径）
   - **第二次：** 吐 export 产物：单张图片给图片绝对路径；多张图逐个给
     路径（或给 `export/` 目录路径并说明张数）

**关键规则：** HTML 和 export 产物**必须在同一个项目目录下**、**同一
个版本（commit）中**；禁止 export 产物散落在项目目录外。

示例（小红书长图项目，V2）：

```bash
cd 我的项目/小红书旅行攻略
git add .
git commit -m "V2: 优化封面配色与排版"
git tag v2
```

版本卡片（连续两次）：HTML 主入口路径 + export 产物路径。

## 4. 历史版本的只读预览（进阶，可选）

用户想"看一眼 V2"而不改变当前最新版本时，两种方式：

1. **worktree 挂出（推荐，不触碰工作区）：**

```bash
cd 我的项目/{项目名}
git worktree add ../{项目名}-preview-v2 v2
# 用户浏览器打开 我的项目/{项目名}-preview-v2/index.html
# 看完后清理：
git worktree remove ../{项目名}-preview-v2
```

2. **标准恢复（会消耗一个新版本号）：** 见 SKILL.md §4.3——适合用户明
   确要"回到 V2 继续用"的场景。

判断口径：用户说"看/对比" → worktree；说"恢复/回退/回到" → 标准恢复。

## 5. Git 指令全集（速查）

```bash
# 初始化（项目首次）
git init
echo -e "meta.json\nstyle-samples*.html" > .gitignore
git add . && git commit -m "V1: {摘要}" && git tag v1

# 常规新版本
LATEST_TAG=$(git tag --sort=-v:refname | head -n 1)
NEXT_NUM=$((${LATEST_TAG#v} + 1))
git add . && git commit -m "V${NEXT_NUM}: {摘要}" && git tag v${NEXT_NUM}

# 恢复 / 合并（历史版本为基准）
git checkout v{目标} -- .
# （合并流程：在此基础上编辑后一次性 commit 为 v{最新+1}）

# 查看
git log --oneline
git tag --sort=v:refname
git status
```

## 6. 附录：路径与预览（Agent 参考）

- **工作区内：** HTML 使用 `assets/xxx.png` 等相对路径；多文件项目内
  `link` / `script` 使用相对路径引用同目录或子目录代码文件
- **用户打开时：** 直接 file:// 打开本地文件，相对路径天然解析；Agent
  **不要**在源码中写任何云端地址
- **Git 追踪范围：** 代码文件 + `assets/` 资源 + `export/` 产物均进
  Git；`meta.json` 和 `style-samples*.html` 被 `.gitignore` 排除
- **本地无发布能力：** 用户说"发布/下线"时如实说明本地形态暂无线上发
  布链路，可建议用 GitHub Pages / 任意静态托管自行部署（不属于本
  Skill 流程）
