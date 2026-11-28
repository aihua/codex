# 01-CSS-编码风格与选择器（导语 + 1 CSS（1.1～1.2））

> 来源：alibaba/f2e-spec《阿里巴巴前端规约之 CSS 编码规约》coding/css.zh.md（MPL-2.0），本文件为其「导语 + 1 CSS（1.1～1.2）」章节切片，原文零删减。
> 本文件含规则条目 16 条；等级图例：强制＝必须遵循，推荐＝强烈建议，参考＝视情况。规则编号沿用源文档（如 1.2.1）。

---
本规约涉及 CSS 及其预编译语言（Sass、Less）的编码风格和最佳实践，部分规则可通过 [stylelint](https://stylelint.io/) 工具落地。

## 1 CSS

### 1.1 编码风格

![示例代码标注图](https://img.alicdn.com/tfs/TB1TOLiTpP7gK0jSZFjXXc5aXXa-753-427.svg)

上图是一张符合规约要求编码风格的速览图，详细规则如下：

- 1.1.1 `强制` 所有声明都应该以分号结尾，不能省略。stylelint: [declaration-block-trailing-semicolon](https://stylelint.io/user-guide/rules/declaration-block-trailing-semicolon)

  虽然 CSS 语法中最后一条声明的分号是可选的，但是使用分号可以增加代码的一致性和易用性。

  ```css
  /* bad */
  .selector {
    margin-top: 10px;
    padding-left: 15px
  }

  /* good */
  .selector {
    margin-top: 10px;
    padding-left: 15px;
  }
  ```

- 1.1.2 `推荐` 使用 2 个空格缩进，不要使用 4 个空格或 tab 缩进。stylelint: [indentation](https://stylelint.io/user-guide/rules/indentation)

  ```css
  /* bad */
  .selector {
      padding-left: 15px;
  }

  /* good */
  .selector {
    padding-left: 15px;
  }
  ```

- 1.1.3 `推荐` 选择器和 `{` 之间保留一个空格。stylelint: [block-opening-brace-space-before](https://stylelint.io/user-guide/rules/block-opening-brace-space-before)

  ```css
  /* bad */
  .selector{
    padding-left: 15px;
  }

  /* good */
  .selector {
    padding-left: 15px;
  }
  ```

- 1.1.4 `推荐` 属性名和 `:` 之前无空格，`:` 和属性值之间保留一个空格。stylelint: [declaration-colon-space-after](https://stylelint.io/user-guide/rules/declaration-colon-space-after) [declaration-colon-space-before](https://stylelint.io/user-guide/rules/declaration-colon-space-before)

  ```css
  /* bad */
  .selector {
    margin-top : 10px;
    padding-left:15px;
  }

  /* good */
  .selector {
    margin-top: 10px;
    padding-left: 15px;
  }
  ```

- 1.1.5 `推荐` `>`、`+`、`~` 、`||` 等组合器前后各保留一个空格。stylelint: [selector-combinator-space-before](https://stylelint.io/user-guide/rules/selector-combinator-space-before) [selector-combinator-space-after](https://stylelint.io/user-guide/rules/selector-combinator-space-after)

  ```css
  /* bad */
  .selector>.children {
    padding-left: 15px;
  }
  .selector+.brother {
    padding-left: 15px;
  }

  /* good */
  .selector > .children {
    padding-left: 15px;
  }
  .selector + .brother {
    padding-left: 15px;
  }
  ```

- 1.1.6 `推荐` 在使用 `,` 分隔的属性值中，`,` 之后保留一个空格。stylelint: [value-list-comma-space-after](https://stylelint.io/user-guide/rules/value-list-comma-space-after)

  ```css
  /* bad */
  .selector {
    background-color: rgba(0,0,0,0.5);
    box-shadow: 0px 1px 2px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.5);
  }

  /* good */
  .selector {
    background-color: rgba(0, 0, 0, 0.5);
    box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.5);
  }
  ```

- 1.1.7 `推荐` 注释内容和注释符之间留有一个空格。stylelint: [comment-whitespace-inside](https://stylelint.io/user-guide/rules/comment-whitespace-inside)

  ```css
  /* bad */
  .selector {
    /*comment*/
    /*  comment  */
    /**
     *comment
     */
    padding-left: 15px;
  }

  /* good */
  .selector {
    /* comment */
    /**
     * comment
     */
    padding-left: 15px;
  }
  ```

- 1.1.8 `推荐` 声明块的右大括号 `}` 应单独成行。

  ```css
  /* bad */
  .selector {
    padding-left: 15px;}

  /* good */
  .selector {
    padding-left: 15px;
  }
  ```

- 1.1.9 `推荐` 属性声明应单独成行。stylelint: [declaration-block-single-line-max-declarations](https://stylelint.io/user-guide/rules/declaration-block-single-line-max-declarations)

  ```css
  /* bad */
  .selector {
    padding-left: 15px;  margin-left: 10px;
  }

  /* good */
  .selector {
    padding-left: 15px;
    margin-left: 10px;
  }
  ```


- 1.1.10 `推荐` 单行代码最多不要超过 100 个字符。 stylelint: [max-line-length](https://stylelint.io/user-guide/rules/max-line-length) 除了以下两种情况：

  - 使用 [`url()`](https://developer.mozilla.org/en-US/docs/Web/CSS/url) 函数时
  - CSS 属性值本身无法换行时，即属性值内无空格或逗号时

  ```css
  /* bad */
  background-image: -webkit-gradient(linear, left bottom, left top, color-stop(0.04, rgb(88, 94, 124)), color-stop(0.52, rgb(115, 123, 162)));

  /* good */
  background-image: -webkit-gradient(
    linear,
    left bottom,
    left top,
    color-stop(0.04, rgb(88, 94, 124)),
    color-stop(0.52, rgb(115, 123, 162))
  );
  ```

- 1.1.11 `参考` 使用多个选择器时，每个选择器应该单独成行。stylelint: [selector-list-comma-newline-after](https://stylelint.io/user-guide/rules/selector-list-comma-newline-after)

  ```css
  /* bad */
  .selector, .selector-secondary, .selector-third {
    padding: 15px;
    margin-bottom: 15px;
  }

  /* good */
  .selector,
  .selector-secondary,
  .selector-third {
    padding: 15px;
    margin-bottom: 15px;
  }
  ```

- 1.1.12 `参考` 声明块内只有一条语句时，也应该写成多行。

  ```css
  /* bad */
  .selector { padding-left: 15px; }

  /* good */
  .selector {
    padding-left: 15px;
  }
  ```

- 1.1.13 `参考` 注释行上方需留有一行空行，除非上一行是注释或块的顶部。stylelint: [comment-empty-line-before](https://stylelint.io/user-guide/rules/comment-empty-line-before)

  ```css
  /* bad */
  .selector {

    /* comment */
    padding-left: 15px;
    /* comment */
    padding-right: 15px;
  }

  /* good */
  .selector {
    /* comment */
    padding-left: 15px;

    /* comment */
    padding-right: 15px;
  }
  ```

### 1.2 选择器

- 1.2.1 `参考` 不要使用 id 选择器。stylelint: [selector-max-id](https://stylelint.io/user-guide/rules/selector-max-id)

  id 会带来过高的[选择器优先级](https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity)，使得后续很难进行样式覆盖（继而引发使用 `!important` 覆盖样式的恶性循环）。

  ```css
  /* bad */
  .normal {
    padding: 10px;
  }
  #special {
    padding: 15px;
  }

  /* good */
  .normal {
    padding: 10px;
  }
  .normal.special {
    padding: 15px;
  }
  ```

- 1.2.2 `参考` 属性选择器的值始终用双引号包裹。stylelint: [selector-attribute-quotes](https://stylelint.io/user-guide/rules/selector-attribute-quotes)

  属性选择器的值的引号只有在[某些情况下](https://mathiasbynens.be/notes/unquoted-attribute-values#css)可以省略。

  ```css
  /* bad */
  input[type=text] {
    height: 20px;
  }

  /* good */
  input[type="text"] {
    height: 20px;
  }
  ```

- 1.2.3 `参考` 使用 CSS 选择器时，应注意以下性能问题：

  - 使用 class 而不是原生元素标签
  - 减少在经常出现的组件中使用个别属性选择器（如 `[class^="..."]`）
  - 控制选择器的长度，每个组合选择器内的条目尽量不超过 3 个

  > 只从效率的角度来看，CSS 选择器从高（高效率）到低（低效率）的顺序是：
  >
  > - ID 选择器， 比如 `#header`
  > - 类选择器，比如 `.header`
  > - 标签（元素）选择器，比如 `div`
  > - 相邻兄弟选择器，比如 `h2 + p`
  > - 子选择器，比如 `ul > li`
  > - 后代选择器，比如 `ul a`
  > - 通配符选择器，比如 `*`
  > - 属性选择器，比如 `[class^="grid-"]`
  > - 伪类（伪元素）选择器，比如 `a:hover`、`a::before`
