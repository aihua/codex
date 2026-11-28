---
name: ali-html-spec
description: 阿里巴巴前端规约之 HTML 编码规约。凡编写或评审 HTML 页面（文档样板、DOCTYPE、lang、meta、viewport、资源加载、编码、语义化、可访问性、模板语言）时必须使用本技能。
---

# 阿里巴巴前端规约之 HTML 编码规约

alibaba/f2e-spec《HTML 编码规约》（MPL-2.0）全量收录。缩进等级为【推荐】（以本语言规约为准，见共享参考 common.md 编者注）。

## 何时使用

编写或评审 HTML 页面：文档样板、DOCTYPE、lang、meta、viewport、资源加载、编码（缩进、注释、标签、属性）、语义化、可访问性、模板语言。

## 规约等级图例

- 强制：必须遵循，评审中映射为 P0。
- 推荐：强烈建议，评审中映射为 P1。
- 参考：视具体情况选择，评审中映射为 P2。

编号沿用源文档 x.y.z；「文件样板／模板语言」章原文未编号的规则以 HTML-N 顺序引用。

## 规则速查索引

| 编号 | 等级 | 规则摘要 | 全文位置 |
| --- | --- | --- | --- |
| HTML-1 | 强制 | 文档开头必须有 doctype | references/01-文档结构.md |
| HTML-2 | 强制 | 必须使用 HTML5 小写 doctype | references/01-文档结构.md |
| HTML-3 | 强制 | 必须有且仅有一个位于顶层的 `<html>` 元素 | references/01-文档结构.md |
| HTML-4 | 强制 | `<html>` 元素的内容必须有且仅有一个 `<head>` 和一个 `<body>` | references/01-文档结构.md |
| HTML-5 | 强制 | `<meta>` 元素必须包含在 `<head>` 元素内 | references/01-文档结构.md |
| HTML-6 | 强制 | 必须使用 UTF-8 字符编码 | references/01-文档结构.md |
| HTML-7 | 推荐 | 响应式页面应当设置 viewport | references/01-文档结构.md |
| 1.4.1 | 推荐 | 引入 CSS 和 JavaScript 时无需指定 type | references/01-文档结构.md |
| 1.4.2 | 推荐 | 在 head 标签内引入 CSS，在 body 结束标签前引入 JS | references/01-文档结构.md |
| 1.4.3 | 推荐 | 外部资源的引用地址跟随页面协议，省略协议部分 | references/01-文档结构.md |
| 1.4.4 | 推荐 | 使用 preload 预加载关键资源，[了解更多](https://developer.mozilla.org/zh-CN/do…… | references/01-文档结构.md |
| 1.4.5 | 推荐 | 使用 dns-prefetch 和 preconnect 处理 DNS 解析延迟问题，提高网页加载性能…… | references/01-文档结构.md |
| 2.1.1 | 推荐 | 统一使用 2 个空格缩进，不要使用 4 个空格或 tab 缩进 | references/02-编码.md |
| 2.2.2 | 推荐 | 单行注释，需在注释内容和注释符之间需留有一个空格，以增强可读性 | references/02-编码.md |
| 2.2.3 | 推荐 | 多行注释，注释符单独占一行，注释内容 2 个空格缩进 | references/02-编码.md |
| 2.3.2 | 推荐 | 不要省略自闭合标签结尾处的斜线，且斜线前需留有一个空格 | references/02-编码.md |
| 2.4.2 | 推荐 | 不要为 Boolean 属性添加取值 | references/02-编码.md |
| 2.4.3 | 推荐 | 自定义属性的命名：以 data- 为前缀 | references/02-编码.md |
| 2.5.1 | 参考 | 尽量根据语义使用 HTML 标签 | references/02-编码.md |
| 2.6.1 | 参考 | 注意 HTML 的可访问性（Accessibility） | references/02-编码.md |
| HTML-8 | 强制 | 变量，过滤器和关键字必须有前后空格 | references/03-模板语言.md |
| HTML-9 | 强制 | 未过滤的用户输入必须 HTML 转义 | references/03-模板语言.md |

## references 导航

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| references/01-文档结构.md | 文件样板、DOCTYPE、html 元素、lang、meta（含 viewport）（规则条目 5） | 搭建或审查页面骨架时 |
| references/02-编码.md | 2 编码（2.1～2.6）（规则条目 8） | 缩进、注释、标签、属性、语义化、可访问性时 |
| references/03-模板语言.md | 模板语言（Nunjucks 等）+ 作者署名与参考资料（规则条目 0） | 编写模板语言时 |

## 共享参考

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| ../../shared-references/common.md | 通用编码规约（2 空格缩进、行宽 100、UTF-8） | 通用代码风格问题；等级以本语言规约为准（缩进等冲突条款见文件头编者注） |
| ../../shared-references/http-json-api.md | HTTP JSON API 规范（响应信封、分页协议、排序参数） | 设计或评审涉及前后端接口契约、分页与排序参数时 |

## 使用方式

1. 编码前：按当前任务读取对应 references 文件全文，再动手。
2. 编码中：拿不准时回到速查索引定位规则编号，再读对应原文（含说明与正反例）。
3. 引用规则时给出编号（如 2.1.1（统一使用 2 个空格缩进）），便于团队溯源与评审对齐。
4. 评审场景请改用 ali-review-html，它按本技能的规则全文逐条走查并输出带严重级的违规清单。
