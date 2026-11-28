# 03-语言特性-Props-State-Refs（2 语言特性（2.3～2.5））

> 来源：alibaba/f2e-spec《阿里巴巴前端规约之 React 编码规约》coding/react.zh.md（MPL-2.0），本文件为其「2 语言特性（2.3～2.5）」章节切片，原文零删减。
> 本文件含规则条目 16 条；等级图例：强制＝必须遵循，推荐＝强烈建议，参考＝视情况。规则编号沿用源文档（如 1.2.1）。

## 本文件目录

- 2.3 Props（13 条）
- 2.4 State（2 条）
- 2.5 Refs（1 条）

---
### 2.3 Props

- 2.3.1 `强制` 采用小驼峰风格命名 prop 。eslint: [react/no-unknown-property](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/no-unknown-property.md)

  ```jsx static
  // bad
  <Foo
    UserName="hello"
    phone_number={12345678}
  />

  // good
  <Foo
    userName="hello"
    phoneNumber={12345678}
  />
  ```

- 2.3.2 `强制` 声明的 prop 必须被使用。eslint: [react/no-unused-prop-types](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/no-unused-prop-types.md)

  声明而未使用的 prop 可能带来潜在的问题，也会给维护者造成困扰，应将它们删除。

  ```jsx static
  // bad
  var Hello = createReactClass({
    propTypes: {
      name: PropTypes.string
    },
    render: function() {
      return <div>Hello Bob</div>;
    }
  });

  var Hello = createReactClass({
    propTypes: {
      firstname: PropTypes.string.isRequired,
      middlename: PropTypes.string.isRequired, // middlename is never used below
      lastname: PropTypes.string.isRequired
    },
    render: function() {
      return <div>Hello {this.props.firstname} {this.props.lastname}</div>;
    }
  });

  // good
  var Hello = createReactClass({
    propTypes: {
      name: PropTypes.string
    },
    render: function() {
      return <div>Hello {this.props.name}</div>;
    }
  });
  ```

- 2.3.3 `参考`  props，state 优先使用解构赋值。eslint: [react/destructuring-assignment](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/destructuring-assignment.md)

  ```jsx static
  // bad
  const MyComponent = (props) => {
    return (<div id={props.id} />)
  };

  // good
  const MyComponent = ({id}) => {
    return (<div id={id} />)
  };

  const MyComponent = (props, context) => {
    const { id } = props;
    return (<div id={id} />)
  };
  ```

- 2.3.4 `强制` prop 值为 true 时，可以省略它的值。eslint: [react/jsx-boolean-value](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/jsx-boolean-value.md)

  ```jsx static
  // bad
  <Foo
    hidden={true}
  />

  // good
  <Foo
    hidden
  />
  ```

- 2.3.5 `推荐` prop 需要 propTypes 验证。eslint: [react/prop-types](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/prop-types.md)

  PropTypes 验证接收到的数据从而提高组件的可重用性。如果其他开发传入了不正确数据类型，可以及时警告。

  ```jsx static
  // bad
  class Greeting extends React.Component {
    render() {
      return (
        <h1>Hello, {this.props.name}</h1>
      );
    }
  }

  // good
  class Greeting extends React.Component {
    render() {
      return (
        <h1>Hello, {this.props.name}</h1>
      );
    }
  }

  Greeting.propTypes = {
    name: PropTypes.string
  };
  ```

- 2.3.6 `推荐` 不要使用模糊的类型检查器。eslint: [react/forbid-prop-types](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/forbid-prop-types.md)

  不要使用模糊的类型验证，比如 any, array, object。它们可以用其他明确的类型代替。any可以替换为任意类型，array 和 object 可以分别替换为 arrayOf 和 shape。

  ```jsx static
  // bad
  class MyComponent extends React.Component {
    ...
  }

  MyComponent.propTypes = {
    // 任意类型的数据
    optionalAny: PropTypes.any,
    // 一个未指定元素类型的数组
    optionalArray: PropTypes.array,
    // 一个未指定属性类型的对象
    optionalObject: PropTypes.object
  };

  // good
  class MyComponent extends React.Component {
    ...
  }

  MyComponent.propTypes = {
    // 指明待验证数据的特性类型，确保接收的数据是有效的
    optionalAny: PropTypes.string,
    requiredAny: PropTypes.any.isRequired,
    // 一个指定了元素类型的数组
    optionalArray: PropTypes.arrayOf(PropTypes.number),
    // 一个指定了属性类型的对象
    optionalObject: PropTypes.shape({
      color: PropTypes.string,
      fontSize: PropTypes.number
    }),
  };
  ```

- 2.3.7 `参考` 属性需要指定 defaultProps，除了 isRequired 的属性。eslint: [react/require-default-props](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/require-default-props.md)

  ```jsx static
  // bad
  function MyStatelessComponent({ foo, bar }) {
    return <div>{foo}{bar}</div>;
  }
  MyStatelessComponent.propTypes = {
    foo: PropTypes.number.isRequired,
    bar: PropTypes.string,
  };

  // good
  function MyStatelessComponent({ foo, bar }) {
    return <div>{foo}{bar}</div>;
  }
  MyStatelessComponent.propTypes = {
    foo: PropTypes.number.isRequired,
    bar: PropTypes.string,
  };
  MyStatelessComponent.defaultProps = {
    bar: '',
  };
  ```

- 2.3.8 `强制` 如果属性有 isRequired 类型检查，不要在 defaultProps 内对其赋值。eslint: [react/default-props-match-prop-types](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/default-props-match-prop-types.md)

  propTypes 类型检查发生在 defaultProps 解析之后，如果在 defaultProps 赋值，isRequired 类型检查没有实际意义。

  ```jsx static
  // bad
  MyStatelessComponent.propTypes = {
    foo: React.PropTypes.string.isRequired,
    bar: React.PropTypes.string
  };

  MyStatelessComponent.defaultProps = {
    foo: "foo"
  };

  // good
  MyStatelessComponent.propTypes = {
    foo: React.PropTypes.string.isRequired,
    bar: React.PropTypes.string
  };

  MyStatelessComponent.defaultProps = {
      bar: 'some default'
  };
  ```

- 2.3.9 `推荐` 不要用数组的索引值作为 map 生成元素的 key。eslint: [react/no-array-index-key](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/no-array-index-key.md)

  为什么？React 使用 key 来标识哪些项已更改，已添加或已删除， [key 应该始终稳定](https://reactjs.org/docs/lists-and-keys.html#keys)。使用不稳定的 ID 是一种[反模式](https://medium.com/@robinpokorny/index-as-a-key-is-an-anti-pattern-e0349aece318)，因为它不能唯一标识元素。如果数组重新排序或将元素添加到数组的开头，可能会更改索引导致不必要的渲染，对性能产生负面影响。

  如果数组的顺序可能发生变化，我们不建议使用索引值作为 key。

  ```jsx static
  // bad
  {todos.map((todo, index) =>
    <Todo
      {...todo}
      key={index}
    />
  )}

  // good
  {todos.map(todo => (
    <Todo
      {...todo}
      key={todo.id}
    />
  ))}
  ```

- 2.3.10 `强制` 禁止将 children 作为属性名。eslint: [react/no-children-prop](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/no-children-prop.md)

  使用 JSX 时，`children` 应嵌套在开始和结束标签之间。不使用JSX时，应将 `children` 作为附加参数传递给 `React.createElement`。

  ```jsx static
  // bad
  <div children='Children' />

  <MyComponent children={<AnotherComponent />} />
  <MyComponent children={['Child 1', 'Child 2']} />

  React.createElement("div", { children: 'Children' })

  // good
  <div>Children</div>

  <MyComponent>Children</MyComponent>

  <MyComponent>
    <span>Child 1</span>
    <span>Child 2</span>
  </MyComponent>

  React.createElement("div", {}, 'Children')
  React.createElement("div", 'Child 1', 'Child 2')
  ```

- 2.3.11 `强制` 不要声明重复的属性名。eslint: [react/jsx-no-duplicate-props](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/jsx-no-duplicate-props.md)

  ```jsx static
  // bad
  <Hello name="John" name="John" />;

  // good
  <Hello firstname="John" lastname="Doe" />;
  ```

- 2.3.12 `强制` style 的属性值必须是一个对象。eslint: [react/style-prop-object](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/style-prop-object.md)

  ```jsx static
  // bad
  <div style="color: 'red'" />
  <div style={true} />
  <Hello style={true} />

  const styles = true;
  <div style={styles} />

  React.createElement("div", { style: "color: 'red'" });
  React.createElement("div", { style: true });
  React.createElement("Hello", { style: true });

  const styles = true;
  React.createElement("div", { style: styles });

  // good
  <div style={{ color: "red" }} />
  <Hello style={{ color: "red" }} />

  const styles = { color: "red" };
  <div style={styles} />

  React.createElement("div", { style: { color: 'red' }});
  React.createElement("Hello", { style: { color: 'red' }});

  const styles = { height: '100px' };
  React.createElement("div", { style: styles });
  ```

- 2.3.13 `推荐` 不要单独使用 target='_blank'。eslint: [react/jsx-no-target-blank](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/jsx-no-target-blank.md)

  `target='_blank'` 常用于在新标签页打开。使用这个属性可能造成严重的安全问题。建议和 `rel='noreferrer noopener'` 一起使用。[详见](https://mathiasbynens.github.io/rel-noopener/)
  ```jsx static
  // bad
  const Hello = <a target='_blank' href="http://example.com/"></a>
  const Hello = <a target='_blank' href={ dynamicLink }></a>

  // good
  const Hello = <p target='_blank'></p>
  const Hello = <a target='_blank' rel='noopener noreferrer' href="http://example.com"></a>
  const Hello = <a target='_blank' href="relative/path/in/the/host"></a>
  const Hello = <a target='_blank' href="/absolute/path/in/the/host"></a>
  const Hello = <a></a>
  ```

### 2.4 State

- 2.4.1 `强制` 不要在 setState 中使用 this.state。eslint: [react/no-access-state-in-setstate](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/no-access-state-in-setstate.md)

  在 setState 中使用 this.state 可能导致错误，当两个 state 在同一个批处理中时，引用的是旧状态而不是新状态。
  为避免这种情况，请在回调中使用 preState 作为第一个参数。
  ```jsx static
  // bad
  function increment() {
    this.setState({ value: this.state.value + 1 });
  }

  // good
  function increment() {
    this.setState(prevState => ({ value: prevState.value + 1 }));
  }
  ```

  bad case 中假设 value 为1，有两个 setState 操作在同一个批处理中执行，实际执行的是：
  ```
  setState({ value: 1 + 1 })
  setState({ value: 1 + 1 })
  ```
  good case 中 react 会以正确的更新后的状态调用参数。实际执行的是：
  ```
  setState({ value: 1 + 1 })
  setState({ value: 2 + 1 })
  ```

- 2.4.2 `强制` 声明的 state 必须被使用。eslint: [react/no-unused-state](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/no-unused-state.md)

  声明而未使用的 state 可能带来潜在的问题，也会给维护者造成困扰，应将它们删除。

  ```jsx static
  // bad
  class MyComponent extends React.Component {
    state = { foo: 0 };

    render() {
      return <SomeComponent />;
    }
  }

  var UnusedGetInitialStateTest = createReactClass({
    getInitialState: function() {
      return { foo: 0 };
    },
    render: function() {
      return <SomeComponent />;
    }
  })

  // good
  class MyComponent extends React.Component {
    state = { foo: 0 };

    render() {
      return <SomeComponent foo={this.state.foo} />;
    }
  }

  var UnusedGetInitialStateTest = createReactClass({
    getInitialState: function() {
      return { foo: 0 };
    },
    render: function() {
      return <SomeComponent foo={this.state.foo} />;
    }
  })
  ```

### 2.5 Refs

- 2.5.1 `强制` 使用 ref 回调函数或 React.createRef()，不要使用字符串。eslint: [react/no-string-refs](https://github.com/yannickcr/eslint-plugin-react/blob/master/docs/rules/no-string-refs.md)

  ```jsx static
  // bad - 使用字符串
  class MyComponent extends React.Component {
    componentDidMount() {
      this.refs.inputRef.focus();
    }

    render() {
      return <input type="text" ref="inputRef" />;
    }
  }

  // good - 使用回调函数
  class MyComponent extends React.Component {
    componentDidMount() {
      this.inputRef.focus();
    }

    render() {
      return <input type="text" ref={(ele) => { this.inputRef = ele; }} />;
    }
  }

  // good - 使用 React.createRef()，React V16 后版本支持
  class MyComponent extends React.Component {
    constructor(props) {
      super(props);

      this.inputRef = React.createRef();
    }

    componentDidMount() {
      this.inputRef.current.focus();
    }

    render() {
      return <input type="text" ref={this.inputRef} />;
    }
  }
  ```
