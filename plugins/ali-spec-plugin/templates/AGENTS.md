# AGENTS.md 模板（ali-spec-plugin 项目级集成）

> 用途：将本文件复制到你的项目根目录并重命名为 AGENTS.md，按项目技术栈勾选启用项，
> 即可让 Codex 在该仓库内自动遵循阿里巴巴编码规约。矩阵与定制区中不适用的行按需删除。

## 快速开始

1. 复制 `templates/AGENTS.md` 到项目根目录，重命名为 `AGENTS.md`。
2. 在下方「技术栈启用矩阵」中保留本项目用到的行，删除其余行。
3. 在「团队定制区」补充分支策略例外、规则豁免审批口径、强制等级约定。
4. 安装 ali-spec-plugin 插件后，技能通过 `$ali-spec-plugin:技能名`（便携式清单）或
   `$技能名`（Codex 兼容清单）调用；也可在对话中以 @技能名 显式点名。

## 技术栈启用矩阵

| 项目技术栈 | 启用的规约技能 | 启用的评审技能 |
| --- | --- | --- |
| Java 后端 | ali-java-spec + ali-sql-spec | ali-review-java + ali-review-sql |
| Node.js 后端 | ali-nodejs-spec + ali-javascript-spec | ali-review-nodejs |
| React 前端（JS） | ali-reactjs-spec + ali-javascript-spec + ali-css-spec + ali-html-spec | ali-review-reactjs 等 |
| React 前端（TS） | ali-reactjs-spec + ali-typescript-spec + ali-css-spec + ali-html-spec | ali-review-reactjs + ali-review-typescript 等 |
| 所有仓库通用 | ali-git-spec + ali-markdown-spec + ali-changelog-spec | ali-review-git + ali-review-markdown + ali-review-changelog |

全栈仓库（monorepo）按目录分别启用，示例：

```
# services/java/**     → ali-java-spec + ali-sql-spec
# services/node/**     → ali-nodejs-spec
# web/**               → ali-reactjs-spec + ali-typescript-spec + ali-css-spec + ali-html-spec
# docs/** 与 *.md      → ali-markdown-spec；CHANGELOG.md → ali-changelog-spec
```

## 四阶段工作流

| 阶段 | 动作 | 涉及技能 |
| --- | --- | --- |
| 编码前 | 按任务涉及语言，先读对应规约技能的相关 references 章节，再动手 | ali-*-spec |
| 编码中 | 命名、格式、实现方式遵循规约；拿不准时查速查索引定位规则原文 | ali-*-spec |
| 提交前 | 对变更文件运行对应评审技能走查，P0 项必须修复后提交 | ali-review-* |
| 提交与 MR | 提交信息按 ali-git-spec（type(scope): subject）；CHANGELOG 按规约更新；MR 描述引用评审报告结论 | ali-git-spec、ali-changelog-spec 等 |

## 技能索引（22 个）

规约技能（编码前/编码中使用）：

| 技能 | 一句话用途 |
| --- | --- |
| ali-sql-spec | MySQL 建表/索引/SQL 语句规约（37 条） |
| ali-java-spec | Java 手册其余全部规约（182 条 + 前言/附录） |
| ali-javascript-spec | JavaScript 编码规约（ES6+，112 条） |
| ali-typescript-spec | TypeScript 编码规约（27 条） |
| ali-reactjs-spec | React 组件规约（68 条，含 Hooks 与无障碍） |
| ali-nodejs-spec | Node.js 开发规约（21 条） |
| ali-css-spec | CSS/Sass/Less 规约（31 条） |
| ali-html-spec | HTML 页面规约（22 条） |
| ali-git-spec | Git 规约（提交消息/工作流/分支/标签） |
| ali-markdown-spec | 中文文档通用规约（12 条） |
| ali-changelog-spec | CHANGELOG 规约（10 条） |

评审技能（提交前走查使用，报告含 P0/P1/P2 违规清单）：

| 技能 | 一句话用途 |
| --- | --- |
| ali-review-sql | SQL/DDL 规约走查 |
| ali-review-java | Java 代码规约走查 |
| ali-review-javascript | JavaScript 规约走查 |
| ali-review-typescript | TypeScript 规约走查 |
| ali-review-reactjs | React 组件规约走查 |
| ali-review-nodejs | Node.js 规约走查 |
| ali-review-css | 样式规约走查 |
| ali-review-html | HTML 规约走查 |
| ali-review-git | 提交信息与分支标签走查 |
| ali-review-markdown | 文档书写规范走查 |
| ali-review-changelog | CHANGELOG 走查 |

共享参考（由技能按需加载，用户一般无需直接调用）：

- shared-references/common.md：通用编码规约（2 空格缩进、行宽 100、UTF-8；前端侧 18 技能引用）。
- shared-references/http-json-api.md：HTTP JSON API 规范（响应信封、分页协议；全部 22 技能引用）。

## 团队定制区

<!-- 以下内容由各团队按需修改；未填写时按规约默认执行 -->

### 分支策略例外

<!-- 例：本项目采用 trunk-based，临时分支一律 feature/ 前缀，不使用 next 分支 -->

### 规则豁免审批

<!-- 例：豁免【强制】级规则需技术负责人在 MR 中书面批准并注明原因与恢复计划 -->

### 强制等级约定

<!-- 例：本项目将【推荐】级的「单行 120 字符」升格为 P0 执行 -->

（完，模板结束）
