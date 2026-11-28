# ali-spec-plugin

阿里巴巴编码规约 Codex 插件：把《阿里巴巴 Java 开发手册（终极版 1.3.0）》与
alibaba/f2e-spec 前端规约做成 **11 个规约技能 + 11 个评审技能 + 2 份共享参考**，
在编码与评审场景按需渐进加载，规则原文零删减、逐条可溯源。

## 是什么

| 组件 | 数量 | 说明 |
| --- | --- | --- |
| 规约技能（ali-*-spec） | 11 | 规则原文全量承载（SKILL.md 速查索引 + references 全文），编码时自动触发遵循 |
| 评审技能（ali-review-*） | 11 | 五步评审流程 + 标准化报告（P0/P1/P2 违规清单），与规约技能一一对应 |
| 共享参考（shared-references/） | 2 | common.md（前端侧 18 技能引用）+ http-json-api.md（全部 22 技能引用） |
| AGENTS.md 模板 | 1 | 项目级集成：技术栈启用矩阵 + 四阶段工作流（templates/AGENTS.md） |
| 校验脚本 | 1 | scripts/validate.py 六项自动检查 |

规则规模：Java 手册 220 个等级标记（ali-sql-spec 37 条：建表/索引/SQL；
ali-java-spec 182 条规则 + 前言与附录）；前端九规约共 303 条规则条目
（JavaScript 112 / React 68 / CSS 31 / HTML 22 / Node.js 21 / TypeScript 27 /
文档 12 / CHANGELOG 10）。

适用人群：使用 Codex / ChatGPT 的研发团队，希望在编码与代码评审中直接对齐
阿里巴巴编码规约，产出可溯源、可比较的评审报告。

## 使用

### 四阶段工作流（推荐写入项目 AGENTS.md，模板见 templates/AGENTS.md）

1. **编码前**：按任务语言读对应规约技能的相关 references 章节（如写建表 DDL
   先读 ali-sql-spec 的 01-建表规约.md）。
2. **编码中**：命名、格式、实现方式遵循规约；拿不准时查 SKILL.md 速查索引定位
   规则编号再读原文。
3. **提交前**：对变更文件运行对应评审技能走查（如 `$ali-review-java`），
   P0 项必须修复后提交。
4. **提交与 MR**：提交信息按 ali-git-spec（type(scope): subject 格式）；
   CHANGELOG 按 ali-changelog-spec 更新；MR 描述引用评审报告结论。

### 触发示例问句

| 问句 | 预期触发 |
| --- | --- |
| 帮我设计一个订单表：主键、订单号、金额、状态、创建时间 | ali-sql-spec（is_deleted unsigned tinyint、gmt_create 等必备字段） |
| 看看这条 SQL：select * from user where id = 1 | ali-review-sql（按 SQL-N 指出禁用 select * 等） |
| 写一个线程安全的计数器工具类 | ali-java-spec（命名后缀与并发规约） |
| 帮我写提交信息：修复了登录页空指针 | ali-git-spec（fix(login): ... 格式） |
| 把这个 CSS 文件的缩进改成阿里规约 | ali-css-spec + common.md（2 空格缩进，推荐级） |
| 设计一个用户列表的分页接口 | http-json-api.md（currentPage/pageSize/total 契约）+ 后端联动条款 |

调用方式：ChatGPT 端 `@ali-sql-spec` / `@ali-spec-plugin`；Codex 端 `$ali-sql-spec`
（兼容清单）或 `$ali-spec-plugin:ali-sql-spec`（便携式清单命名空间）。

### 本地校验

```bash
python3 scripts/validate.py   # 六项检查：frontmatter / 结构 / 覆盖度 / 残留 / 清单 / 共享参考
```

## 来源与版权

| 来源 | 版本 | 许可/声明 |
| --- | --- | --- |
| 《阿里巴巴 Java 开发手册》 | 终极版 1.3.0（2017-09-19 发布） | 版权归阿里巴巴集团所有，官方 PDF 标注「仅供大家交流、学习及研究使用，禁止用于商业用途，违者必究」 |
| alibaba/f2e-spec（前端规约九份 + 通用编码规约 + HTTP JSON API 规范） | 仓库快照（docs/coding 与 docs/engineering） | MPL-2.0，许可证副本见 LICENSE-NOTICE.md |

本插件定位：团队内部学习与协作用途。分发时必须保留 LICENSE-NOTICE.md 中的
MPL-2.0 许可证副本与源头标注；《阿里巴巴 Java 开发手册》内容禁止用于商业用途。
手册「法律声明」原文：本手册为阿里巴巴集团技术部的技术分享，版权归阿里巴巴集团
所有，仅供大家交流、学习及研究使用，禁止用于商业用途，违者必究。
