---
name: ali-reactjs-spec
description: 阿里巴巴前端规约之 React 编码规约。凡编写或评审 React 组件（JSX 编码风格、方法、Props、State、Refs、组件顺序、命名、Hooks、无障碍）时必须使用本技能。
---

# 阿里巴巴前端规约之 React 编码规约

alibaba/f2e-spec《React 编码规约》（MPL-2.0）全量收录（React 16.x 时代规约，Hooks 与无障碍独立成章）。

## 何时使用

编写或评审 React 组件：JSX 编码风格（缩进、空格、引号、小括号、标签）、基本与方法、Props、State、Refs、组件顺序、Mixins、命名、Hooks、无障碍。

## 规约等级图例

- 强制：必须遵循，评审中映射为 P0。
- 推荐：强烈建议，评审中映射为 P1。
- 参考：视具体情况选择，评审中映射为 P2。

规则编号沿用源文档节号（如 1.1 缩进、2.3 Props），规则条目为 x.y.z 编号（如 2.1.1）。

## 规则速查索引

| 编号 | 等级 | 规则摘要 | 全文位置 |
| --- | --- | --- | --- |
| 1.1.1 | 强制 | JSX 语法使用 2 个空格缩进 | references/01-编码风格.md |
| 1.2.1 | 强制 | 自闭合标签的斜线前有且仅有一个空格 | references/01-编码风格.md |
| 1.2.2 | 强制 | JSX 行内属性之间仅有一个空格 | references/01-编码风格.md |
| 1.2.3 | 强制 | JSX 属性的大括号内部两侧无空格 | references/01-编码风格.md |
| 1.2.4 | 强制 | 不要在 JSX 属性的等号两边加空格 | references/01-编码风格.md |
| 1.3.1 | 强制 | JSX 属性使用双引号，不要使用单引号 | references/01-编码风格.md |
| 1.4.1 | 强制 | 多行的 JSX 标签需用小括号包裹 | references/01-编码风格.md |
| 1.5.1 | 强制 | 无子元素的标签需写成自闭合标签 | references/01-编码风格.md |
| 1.5.2 | 强制 | 标签属性的换行 | references/01-编码风格.md |
| 1.5.3 | 强制 | 标签的属性有多行时，结束标签需另起一行 | references/01-编码风格.md |
| 1.5.4 | 强制 | 禁止在有子节点的组件或 DOM 元素中使用 dangerouslySetInnerHTML 属性 | references/01-编码风格.md |
| 1.5.5 | 强制 | HTML 自闭标签不能有子节点 | references/01-编码风格.md |
| 1.5.6 | 推荐 | 不要使用危险属性 | references/01-编码风格.md |
| 1.5.7 | 强制 | JSX 语句的文本节点中不要使用注释字符串（例如，以//或/ *开头） | references/01-编码风格.md |
| 1.5.8 | 强制 | 标签中禁止出现无意义字符，比如 > " } ' | references/01-编码风格.md |
| 2.1.1 | 参考 | 使用 `JSX` 语法时，防止 `React` 变量被标记为未使用…… | references/02-语言特性-基本与方法.md |
| 2.1.2 | 强制 | 不要使用未声明的组件 | references/02-语言特性-基本与方法.md |
| 2.1.3 | 强制 | 每个文件只包含一个 React 组件 | references/02-语言特性-基本与方法.md |
| 2.1.4 | 强制 | 不要在函数组件中使用 this | references/02-语言特性-基本与方法.md |
| 2.1.5 | 强制 | 使用 ES6 class 创建组件 ，而不是 [createReactClass](https://reactjs.org/do…… | references/02-语言特性-基本与方法.md |
| 2.1.6 | 参考 | 如果组件没有内部状态或 refs ，应使用函数组件，而不是类组件 | references/02-语言特性-基本与方法.md |
| 2.1.7 | 强制 | 不要使用 React.createElement，除非你不是用 JSX 文件初始化应用程序 | references/02-语言特性-基本与方法.md |
| 2.2.1 | 推荐 | 不要在 JSX 属性中使用 .bind() | references/02-语言特性-基本与方法.md |
| 2.2.2 | 强制 | render 方法必须要有返回值 | references/02-语言特性-基本与方法.md |
| 2.2.3 | 强制 | 禁止使用 ReactDOM.render 的返回值 | references/02-语言特性-基本与方法.md |
| 2.2.4 | 强制 | 在扩展 React.PureComponent 时禁止使用 shouldComponentUpdate | references/02-语言特性-基本与方法.md |
| 2.2.5 | 强制 | 禁止使用已经废弃的方法 | references/02-语言特性-基本与方法.md |
| 2.2.6 | 强制 | 不要使用 findDOMNode | references/02-语言特性-基本与方法.md |
| 2.2.7 | 强制 | 不要使用 componentWillMount、componentWillReceiveProps…… | references/02-语言特性-基本与方法.md |
| 2.2.8 | 强制 | 不要在 componentWillUpdate 内改变 state 值 | references/02-语言特性-基本与方法.md |
| 2.3.1 | 强制 | 采用小驼峰风格命名 prop  | references/03-语言特性-Props-State-Refs.md |
| 2.3.2 | 强制 | 声明的 prop 必须被使用 | references/03-语言特性-Props-State-Refs.md |
| 2.3.3 | 参考 | props，state 优先使用解构赋值 | references/03-语言特性-Props-State-Refs.md |
| 2.3.4 | 强制 | prop 值为 true 时，可以省略它的值 | references/03-语言特性-Props-State-Refs.md |
| 2.3.5 | 推荐 | prop 需要 propTypes 验证 | references/03-语言特性-Props-State-Refs.md |
| 2.3.6 | 推荐 | 不要使用模糊的类型检查器 | references/03-语言特性-Props-State-Refs.md |
| 2.3.7 | 参考 | 属性需要指定 defaultProps，除了 isRequired 的属性 | references/03-语言特性-Props-State-Refs.md |
| 2.3.8 | 强制 | 如果属性有 isRequired 类型检查，不要在 defaultProps 内对其赋值 | references/03-语言特性-Props-State-Refs.md |
| 2.3.9 | 推荐 | 不要用数组的索引值作为 map 生成元素的 key | references/03-语言特性-Props-State-Refs.md |
| 2.3.10 | 强制 | 禁止将 children 作为属性名 | references/03-语言特性-Props-State-Refs.md |
| 2.3.11 | 强制 | 不要声明重复的属性名 | references/03-语言特性-Props-State-Refs.md |
| 2.3.12 | 强制 | style 的属性值必须是一个对象 | references/03-语言特性-Props-State-Refs.md |
| 2.3.13 | 推荐 | 不要单独使用 target='_blank' | references/03-语言特性-Props-State-Refs.md |
| 2.4.1 | 强制 | 不要在 setState 中使用 this.state | references/03-语言特性-Props-State-Refs.md |
| 2.4.2 | 强制 | 声明的 state 必须被使用 | references/03-语言特性-Props-State-Refs.md |
| 2.5.1 | 强制 | 使用 ref 回调函数或 React.createRef()，不要使用字符串 | references/03-语言特性-Props-State-Refs.md |
| 2.6.1 | 参考 | 组件方法的排序规则 | references/04-语言特性-顺序与Mixins.md |
| 2.7.1 | 强制 | 不要使用 mixins | references/04-语言特性-顺序与Mixins.md |
| 3.1 | 强制 | 文件扩展名： 使用 .jsx、.tsx、.js 或 .ts 作为 React 组件的文件扩展名 | references/05-命名.md |
| 3.2 | 强制 | 引用名：使用大驼峰风格命名引用的组件，使用小驼峰风格命名引用组件的实例 | references/05-命名.md |
| 3.3 | 推荐 | 高阶组件命名：将高阶组件名和传入组件名组合作为 displayName | references/05-命名.md |
| 4.1 | 强制 | 只在最顶层调用 Hooks，不要在循环、条件和嵌套函数中调用 Hooks | references/06-Hooks.md |
| 4.2 | 强制 | Hooks 命名必须以 `use` 开头，小驼峰形式 | references/06-Hooks.md |
| 4.3 | 强制 | 只在 React 函数组件和自定义 Hooks 中调用 Hooks，不能在普通的 JavaScript 函数中调用 Hooks | references/06-Hooks.md |
| 4.4 | 推荐 | `useEffect` 及[类似 Hooks ](https://github.com/facebook/react/blob/…… | references/06-Hooks.md |
| 5.1 | 推荐 | img 标签应包含 alt 属性 | references/07-无障碍.md |
| 5.2 | 推荐 | img 标签的 alt 属性不要使用 "image"，"photo"，"picture" 之类的关键词 | references/07-无障碍.md |
| 5.3 | 推荐 | 锚元素(即 `<a>` 元素)必须含有内容，且内容必须对屏幕阅读器可见(这里指内容不能通过设置 `aria-hidden`…… | references/07-无障碍.md |
| 5.4 | 推荐 | 禁止使用无效的 ARIA 属性，只能使用列在 [WAI-ARIA States and Properties…… | references/07-无障碍.md |
| 5.5 | 推荐 | ARIA 属性、状态的值必须为有效值 | references/07-无障碍.md |
| 5.6 | 推荐 | 禁止特定元素包含 `role` 和 `aria-*` 属性。一些保留的 DOM 元素不支持设置 ARIA 角色或者属性…… | references/07-无障碍.md |
| 5.7 | 推荐 | 仅使用有效的、非抽象的 ARIA roles，[了解更多](https://www.w3.org/TR/wai-aria/#ro…… | references/07-无障碍.md |
| 5.8 | 推荐 | 有 ARIA role 的元素必须也声明该 role 需要的属性…… | references/07-无障碍.md |
| 5.9 | 推荐 | 强制拥有显式或隐式 role 的元素，只能含有该 role 支持的 `aria-*` 属性 | references/07-无障碍.md |
| 5.10 | 推荐 | `<iframe>` 元素必须有一个唯一的 title 属性，表示其内容 | references/07-无障碍.md |
| 5.11 | 推荐 | 不要使用 accessKey 属性。accessKey 属性提供了为当前元素生成快捷键的方式…… | references/07-无障碍.md |
| 5.12 | 推荐 | 禁止使用会造成视觉分散的元素。一些会引起视觉注意力分散的元素对视觉障碍的用户会造成问题…… | references/07-无障碍.md |
| 5.13 | 推荐 | scope 属性只能在 `<th>` 元素上使用，[了解更多](https://developer.mozilla.org/en…… | references/07-无障碍.md |

## references 导航

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| references/01-编码风格.md | 1 编码风格（1.1～1.5）（规则条目 15） | JSX 缩进、空格、引号、小括号、标签时 |
| references/02-语言特性-基本与方法.md | 2 语言特性（2.1～2.2）（规则条目 15） | 组件基本写法与方法时 |
| references/03-语言特性-Props-State-Refs.md | 2 语言特性（2.3～2.5）（规则条目 16） | Props、State、Refs 设计时 |
| references/04-语言特性-顺序与Mixins.md | 2 语言特性（2.6～2.7）（规则条目 2） | 组件成员顺序与 Mixins 时 |
| references/05-命名.md | 3 命名（规则条目 3） | 组件与实例命名时 |
| references/06-Hooks.md | 4 Hooks（规则条目 4） | 编写 Hooks 时 |
| references/07-无障碍.md | 5 无障碍 + 配套工具与参考资料（规则条目 13） | 无障碍改造与评审时 |

## 共享参考

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| ../../shared-references/common.md | 通用编码规约（2 空格缩进、行宽 100、UTF-8） | 通用代码风格问题；等级以本语言规约为准（缩进等冲突条款见文件头编者注） |
| ../../shared-references/http-json-api.md | HTTP JSON API 规范（响应信封、分页协议、排序参数） | 设计或评审涉及前后端接口契约、分页与排序参数时 |

## 使用方式

1. 编码前：按当前任务读取对应 references 文件全文，再动手。
2. 编码中：拿不准时回到速查索引定位规则编号，再读对应原文（含说明与正反例）。
3. 引用规则时给出编号（如 2.1.1（Props 使用 camelCase 命名……见原文）），便于团队溯源与评审对齐。
4. 评审场景请改用 ali-review-reactjs，它按本技能的规则全文逐条走查并输出带严重级的违规清单。
