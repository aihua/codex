---
name: ali-git-spec
description: 阿里巴巴前端规约之 Git 规约。凡编写提交git信息(type/scope/description/body/footer)、选择工作流、命名分支与标签时必须使用本技能。
---

# 阿里巴巴前端规约之 Git 规约

alibaba/f2e-spec《Git 规约》（MPL-2.0）全量收录，覆盖提交消息、工作流、分支命名与标签命名四章。

## 何时使用

编写提交信息（type/scope/description/body/footer）、选择工作流（No Flow / GitHub Flow / Git Flow）、命名分支与标签、管理版本号时。

## 规约等级图例

- 强制：必须遵循，评审中映射为 P0。
- 推荐：强烈建议，评审中映射为 P1。
- 参考：视具体情况选择，评审中映射为 P2。

源文档为散文式规约（无全局规则编号），速查索引按四章主题给出要点，引用时以「章节名 + 要点」定位。

## 规则速查索引

| 编号 | 等级 | 规则摘要 | 全文位置 |
| --- | --- | --- | --- |
| 提交消息-格式 | 推荐 | 使用《约定式提交》格式：<类型>[范围]: <描述> + 正文 + 脚注 | references/01-提交消息.md |
| 提交消息-语言 | 推荐 | 国际化项目用英文；其他项目用团队最普遍语言；不要用拼音与不常见缩写 | references/01-提交消息.md |
| 提交消息-类型 | — | feat/fix/docs/style/test/refactor/chore/revert 八类 | references/01-提交消息.md |
| 提交消息-正文脚注 | — | 正文说明动机与对比；脚注标明 BREAKING CHANGE 与 Issue 关联 | references/01-提交消息.md |
| 工作流 | — | No Flow（单人）/ GitHub Flow / One Flow（单维护分支）/ Git Flow（多维护分支），按项目选型 | references/02-工作流与分支标签命名.md |
| 分支-常驻 | — | main（+feature/next/x.y 视模式而定） | references/02-工作流与分支标签命名.md |
| 分支-临时 | — | 格式 <类型>/[问题编号][处理人]<描述>，如 feat/1023-crash-on-search | references/02-工作流与分支标签命名.md |
| 标签-版本号 | 强制 | 版本号必须符合《语义化版本》约定；正式 Tag 必须位于主分支 | references/02-工作流与分支标签命名.md |
| 标签-前缀 | 推荐 | 版本 Tag 推荐 v 开头（v1.2.3）；独立发包的包加包名前缀 @foo/bar@1.2.2 | references/02-工作流与分支标签命名.md |

## references 导航

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| references/01-提交消息.md | 提交消息/Commit Message（格式、语言、类型、范围、正文、脚注）（规则条目 0） | 编写或评审提交信息时 |
| references/02-工作流与分支标签命名.md | 工作流 + 分支命名 + 标签命名 + 参考资料（规则条目 0） | 选工作流、命名分支与标签时 |

## 共享参考

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| ../../shared-references/common.md | 通用编码规约（2 空格缩进、行宽 100、UTF-8） | 通用代码风格问题；等级以本语言规约为准（缩进等冲突条款见文件头编者注） |
| ../../shared-references/http-json-api.md | HTTP JSON API 规范（响应信封、分页协议、排序参数） | 设计或评审涉及前后端接口契约、分页与排序参数时 |

## 使用方式

1. 编码前：按当前任务读取对应 references 文件全文，再动手。
2. 编码中：拿不准时回到速查索引定位规则编号，再读对应原文（含说明与正反例）。
3. 引用规则时给出编号（如 提交消息-类型（feat/fix/docs/style/test/refactor/chore/revert）），便于团队溯源与评审对齐。
4. 评审场景请改用 ali-review-git，它按本技能的规则全文逐条走查并输出带严重级的违规清单。
