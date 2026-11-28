# 04-语言特性-顺序与Mixins（2 语言特性（2.6～2.7））

> 来源：alibaba/f2e-spec《阿里巴巴前端规约之 React 编码规约》coding/react.zh.md（MPL-2.0），本文件为其「2 语言特性（2.6～2.7）」章节切片，原文零删减。
> 本文件含规则条目 2 条；等级图例：强制＝必须遵循，推荐＝强烈建议，参考＝视情况。规则编号沿用源文档（如 1.2.1）。

---
### 2.6 顺序

- 2.6.1 `参考` 组件方法的排序规则。eslint: [react/sort-comp](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/sort-comp.md)

  React 组件内有声明周期方法、事件处理方法、render 方法等几类方法，指定这些方法按固定的顺序排序可以增强代码的一致性，方便查找和阅读。

  我们推荐的方法排序如下：

    - 可选的 `static` 方法
    - `constructor`
    - `getChildContext`
    - `componentWillMount`
    - `componentDidMount`
    - `componentWillReceiveProps`
    - `shouldComponentUpdate`
    - `componentWillUpdate`
    - `componentDidUpdate`
    - `componentWillUnmount`
    - *clickHandlers 或 eventHandlers* 比如 `onClickSubmit()` 或 `onChangeDescription()`
    - *`render` 的 getter 方法* 比如 `getSelectReason()` 或 `getFooterContent()`
    - *可选的 render 方法* 比如 `renderNavigation()` 或 `renderProfilePicture()`
    - `render`

### 2.7 Mixins

- 2.7.1 `强制` 不要使用 mixins。

  Mixins 引入了隐式依赖，可能导致命名冲突，并导致滚雪球式的复杂度。大多数使用 mixin 的场景都可以通过组件、高阶组件或工具模块以更好的方式完成。
