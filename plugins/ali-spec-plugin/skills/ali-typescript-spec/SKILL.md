---
name: ali-typescript-spec
description: 阿里巴巴前端规约之 TypeScript 编码规约。凡编写或评审 TypeScript 代码（类型声明、接口、泛型、枚举、类型断言等编码风格与语言特性）时必须使用本技能。
---

# 阿里巴巴前端规约之 TypeScript 编码规约

alibaba/f2e-spec《TypeScript 编码规约》（MPL-2.0）全量收录，覆盖编码风格与配套工具。

## 何时使用

编写或评审 TypeScript 代码：类型声明、接口、泛型、枚举、类型断言、类与函数的类型约束等。

## 规约等级图例

- 强制：必须遵循，评审中映射为 P0。
- 推荐：强烈建议，评审中映射为 P1。
- 参考：视具体情况选择，评审中映射为 P2。

源文档规则未编号，TS-N 为本技能按原文顺序编排的引用号（评审与讨论时使用）。

## 规则速查索引

| 编号 | 等级 | 规则摘要 | 全文位置 |
| --- | --- | --- | --- |
| TS-1 | 强制 | 重载的函数必须写在一起 | references/01-编码风格.md |
| TS-2 | 推荐 | 简单数组类型的定义使用 `T[]`，复杂类型使用 `Array<T>` | references/01-编码风格.md |
| TS-3 | 推荐 | 使用 TypeScript 注释指令时需跟随描述说明 | references/01-编码风格.md |
| TS-4 | 强制 | 禁止使用 `// tslint:<rule-flag>` 等 tslint 注释 | references/01-编码风格.md |
| TS-5 | 推荐 | 如果类的属性是一个字面量，则推荐使用只读属性 `readonly` 而不是 `getter` | references/01-编码风格.md |
| TS-6 | 强制 | 类型断言必须使用 `as Type` | references/01-编码风格.md |
| TS-7 | 推荐 | 优先使用 `interface` 定义类型 | references/01-编码风格.md |
| TS-8 | 推荐 | 设置类成员的可访问性 | references/01-编码风格.md |
| TS-9 | 强制 | interface/type 类型中使用一致的成员分隔符 `;` | references/01-编码风格.md |
| TS-10 | 推荐 | 类的成员应按照固定的先后顺序排列 | references/01-编码风格.md |
| TS-11 | 推荐 | 接口中的方法使用属性的方式定义 | references/01-编码风格.md |
| TS-12 | 推荐 | 禁止使用容易混淆的非空断言 | references/01-编码风格.md |
| TS-13 | 推荐 | 避免定义空的接口类型 | references/01-编码风格.md |
| TS-14 | 推荐 | 初始化为 `number/string/boolean` 的变量或参数应避免显式的类型声明 | references/01-编码风格.md |
| TS-15 | 强制 | 禁止无意义的 `void` 类型 | references/01-编码风格.md |
| TS-16 | 强制 | 禁止使用 namespace 来定义命名空间 | references/01-编码风格.md |
| TS-17 | 强制 | 禁止在 `optional chaining` 之后使用 `non-null` 断言 | references/01-编码风格.md |
| TS-18 | 推荐 | 使用 ES2015 import 语法引入模块 | references/01-编码风格.md |
| TS-19 | 推荐 | 不建议将 this 赋值给其他变量 | references/01-编码风格.md |
| TS-20 | 推荐 | 当变量的值与类型声明相等时，优先使用 `as const` | references/01-编码风格.md |
| TS-21 | 强制 | 禁止使用 module 来定义命名空间 | references/01-编码风格.md |
| TS-22 | 强制 | 字符串字面量使用单引号包裹 | references/01-编码风格.md |
| TS-23 | 推荐 | 加号 `+` 连接的两侧同为数字或同为字符串 | references/01-编码风格.md |
| TS-24 | 强制 | 禁止使用三斜杠语法 `///` 导入文件 | references/01-编码风格.md |
| TS-25 | 强制 | 类型声明时应正确添加空格间距 | references/01-编码风格.md |
| TS-26 | 强制 | interface 和 type 定义时必须声明成员的类型 | references/01-编码风格.md |
| TS-27 | 推荐 | 定义函数时，优先使用参数的联合类型而不是函数的类型重载 | references/01-编码风格.md |

## references 导航

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| references/01-编码风格.md | 全文（前言 + 编码风格 + 配套工具）（规则条目 27） | 所有 TypeScript 编码与评审场景 |

## 共享参考

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| ../../shared-references/common.md | 通用编码规约（2 空格缩进、行宽 100、UTF-8） | 通用代码风格问题；等级以本语言规约为准（缩进等冲突条款见文件头编者注） |
| ../../shared-references/http-json-api.md | HTTP JSON API 规范（响应信封、分页协议、排序参数） | 设计或评审涉及前后端接口契约、分页与排序参数时 |

## 使用方式

1. 编码前：按当前任务读取对应 references 文件全文，再动手。
2. 编码中：拿不准时回到速查索引定位规则编号，再读对应原文（含说明与正反例）。
3. 引用规则时给出编号（如 TS-3（类型断言必须使用 as Type）），便于团队溯源与评审对齐。
4. 评审场景请改用 ali-review-typescript，它按本技能的规则全文逐条走查并输出带严重级的违规清单。
