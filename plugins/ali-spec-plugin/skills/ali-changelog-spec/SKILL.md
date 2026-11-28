---
name: ali-changelog-spec
description: 阿里巴巴前端规约之更新日志规约。凡编写或评审 CHANGELOG（文件命名、版本格式、类型分类、条目写法）时必须使用本技能。
---

# 阿里巴巴前端规约之更新日志规约

alibaba/f2e-spec《更新日志规约》（MPL-2.0）全量收录，含 Ant Design 样本示例。

## 何时使用

编写或评审 CHANGELOG：文件命名与位置、版本号与排列、日期格式、条目类型与写法。

## 规约等级图例

- 强制：必须遵循，评审中映射为 P0。
- 推荐：强烈建议，评审中映射为 P1。
- 参考：视具体情况选择，评审中映射为 P2。

规则编号沿用源文档节号（如 1.1 文件命名、2.3 版本号遵循 SemVer）。

## 规则速查索引

| 编号 | 等级 | 规则摘要 | 全文位置 |
| --- | --- | --- | --- |
| 1.1 | 强制 | Changelog 文件必须取名为 `CHANGELOG.md` | references/01-规约全文.md |
| 1.2 | 强制 | Changelog 文件必须是使用标准 Markdown 语法的文本文件，并以 `.md` 作为后缀 | references/01-规约全文.md |
| 1.3 | 强制 | Changelog 文件必须存放在项目根目录下，和 `README.md`、`CONTRIBUTING.md` 等并列 | references/01-规约全文.md |
| 2.1 | 强制 | 文章标题使用「更新日志」作为固定文案。国际化场景使用英文「Change Log」作为固定文案 | references/01-规约全文.md |
| 2.2 | 强制 | Changelog 内容按版本号降序排列，最新版本放在最前面 | references/01-规约全文.md |
| 2.3 | 强制 | 版本号 `version` 需遵循 [SemVer 规范](https://semver.org/lang/zh-CN/) | references/01-规约全文.md |
| 2.4 | 推荐 | 版本号增加一个超链接，指向当前版本和上一个版本之间的 diff | references/01-规约全文.md |
| 2.5 | 强制 | 更新日期 `date` 采用 `yyyy-MM-dd` 格式 | references/01-规约全文.md |
| 2.6 | 推荐 | 更新类型 `type` 与 Git message header 中的…… | references/01-规约全文.md |
| 2.7 | 推荐 | 更新描述 `desc` 内容需要注意以下几点： | references/01-规约全文.md |

## references 导航

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| references/01-规约全文.md | 全文（文件/格式/样本示例/参考资料）（规则条目 10） | 所有 CHANGELOG 编写与评审场景 |

## 共享参考

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| ../../shared-references/common.md | 通用编码规约（2 空格缩进、行宽 100、UTF-8） | 通用代码风格问题；等级以本语言规约为准（缩进等冲突条款见文件头编者注） |
| ../../shared-references/http-json-api.md | HTTP JSON API 规范（响应信封、分页协议、排序参数） | 设计或评审涉及前后端接口契约、分页与排序参数时 |

## 使用方式

1. 编码前：按当前任务读取对应 references 文件全文，再动手。
2. 编码中：拿不准时回到速查索引定位规则编号，再读对应原文（含说明与正反例）。
3. 引用规则时给出编号（如 2.3（版本号需遵循 SemVer 规范）），便于团队溯源与评审对齐。
4. 评审场景请改用 ali-review-changelog，它按本技能的规则全文逐条走查并输出带严重级的违规清单。
