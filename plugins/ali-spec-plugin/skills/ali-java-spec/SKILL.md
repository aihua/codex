---
name: ali-java-spec
description: 《阿里巴巴 Java 开发手册（终极版 1.3.0）》除 MySQL 建表/索引/SQL 外的全部规约：编程规约（命名、常量、格式、OOP、集合、并发、控制、注释）、异常日志、单元测试、安全规约、ORM 映射、工程结构与附录。凡编写、修改、评审 Java 代码或设计工程结构、单元测试时使用。
---

# 阿里巴巴 Java 开发规约

《阿里巴巴 Java 开发手册（终极版 1.3.0）》除 MySQL 建表/索引/SQL（见 ali-sql-spec）外的全部规约，共 182 条（强制 106 / 推荐 52 / 参考 24），另含前言、附录与专有名词。规则原文与正反例零删减存放于 references。

## 何时使用

编写、修改或评审 Java 代码；设计类与工程结构；处理异常与日志；编写单元测试；安全防护；ORM（iBATIS/MyBatis）映射；二方库与服务器配置。

## 规约等级图例

- 【强制】：违反即生产事故高危项，必须整改。
- 【推荐】：强烈建议遵循。
- 【参考】：视具体情况选择。

规则编号沿用手册小节序号（如 命名-1、并发-7、异常-12），可溯源至原文。

## 规则速查索引

| 编号 | 等级 | 规则摘要（原文首句） | 全文位置 |
| --- | --- | --- | --- |
| 命名-1 | 强制 | 代码中的命名均不能以下划线或美元符号开始，也不能以下划线或美元符号结束 | references/01-命名风格.md |
| 命名-2 | 强制 | 代码中的命名严禁使用拼音与英文混合的方式，更不允许直接使用中文的方式 | references/01-命名风格.md |
| 命名-3 | 强制 | 类名使用UpperCamelCase风格，必须遵从驼峰形式，但以下情形例外：DO / BO / DTO / VO / AO | references/01-命名风格.md |
| 命名-4 | 强制 | 方法名、参数名、成员变量、局部变量都统一使用 lowerCamelCase风格，必须遵从驼峰形式 | references/01-命名风格.md |
| 命名-5 | 强制 | 常量命名全部大写，单词间用下划线隔开，力求语义表达完整清楚，不要嫌名字长 | references/01-命名风格.md |
| 命名-6 | 强制 | 抽象类命名使用 Abstract或Base开头；异常类命名使用 Exception结尾；测试类命名以它要测试的类的名称开始…… | references/01-命名风格.md |
| 命名-7 | 强制 | 中括号是数组类型的一部分，数组定义如下：String[] args; | references/01-命名风格.md |
| 命名-8 | 强制 | POJO类中布尔类型的变量，都不要加 is，否则部分框架解析会引起序列化错误 | references/01-命名风格.md |
| 命名-9 | 强制 | 包名统一使用小写，点分隔符之间有且仅有一个自然语义的英语单词 | references/01-命名风格.md |
| 命名-10 | 强制 | 杜绝完全不规范的缩写，避免望文不知义 | references/01-命名风格.md |
| 命名-11 | 推荐 | 为了达到代码自解释的目标，任何自定义编程元素在命名时，使用尽量完整的单词组合来表达其意 | references/01-命名风格.md |
| 命名-12 | 推荐 | 如果使用到了设计模式，建议在类名中体现出具体模式 | references/01-命名风格.md |
| 命名-13 | 推荐 | 接口类中的方法和属性不要加任何修饰符号（public 也不要加），保持代码的简洁性，并加上有效的Javadoc注释 | references/01-命名风格.md |
| 命名-14-1 | 强制 | 对于 Service和DAO类，基于 SOA的理念，暴露出来的服务一定是接口，内部的实现类用Impl的后缀与接口区别 | references/01-命名风格.md |
| 命名-14-2 | 推荐 | 如果是形容能力的接口名称，取对应的形容词做接口名 | references/01-命名风格.md |
| 命名-15 | 参考 | 枚举类名建议带上 Enum后缀，枚举成员名称需要全大写，单词间用下划线隔开 | references/01-命名风格.md |
| 命名-16 | 参考 | 各层命名规约： | references/01-命名风格.md |
| 常量-1 | 强制 | 不允许任何魔法值（即未经定义的常量）直接出现在代码中 | references/02-常量定义.md |
| 常量-2 | 强制 | long或者Long初始赋值时，必须使用大写的 L，不能是小写的 l，小写容易跟数字 1混淆，造成误解 | references/02-常量定义.md |
| 常量-3 | 推荐 | 不要使用一个常量类维护所有常量，应该按常量功能进行归类，分开维护 | references/02-常量定义.md |
| 常量-4 | 推荐 | 常量的复用层次有五层：跨应用共享常量、应用内共享常量、子工程内共享常量、包内共享常量、类内共享常量 | references/02-常量定义.md |
| 常量-5 | 推荐 | 如果变量值仅在一个范围内变化，且带有名称之外的延伸属性，定义为枚举类 | references/02-常量定义.md |
| 格式-1 | 强制 | 大括号的使用约定 | references/03-代码格式.md |
| 格式-2 | 强制 | 左小括号和字符之间不出现空格；同样，右小括号和字符之间也不出现空格 | references/03-代码格式.md |
| 格式-3 | 强制 | if/for/while/switch/do等保留字与括号之间都必须加空格 | references/03-代码格式.md |
| 格式-4 | 强制 | 任何二目、三目运算符的左右两边都需要加一个空格 | references/03-代码格式.md |
| 格式-5 | 强制 | 缩进采用4 个空格，禁止使用tab字符 | references/03-代码格式.md |
| 格式-6 | 强制 | 注释的双斜线与注释内容之间有且仅有一个空格 | references/03-代码格式.md |
| 格式-7 | 强制 | 单行字符数限制不超过 120 个，超出需要换行，换行时遵循如下原则： | references/03-代码格式.md |
| 格式-8 | 强制 | 方法参数在定义和传入时，多个参数逗号后边必须加空格 | references/03-代码格式.md |
| 格式-9 | 强制 | IDE的text file encoding设置为 UTF-8; IDE中文件的换行符使用 Unix格式…… | references/03-代码格式.md |
| 格式-10 | 推荐 | 没有必要增加若干空格来使某一行的字符与上一行对应位置的字符对齐 | references/03-代码格式.md |
| 格式-11 | 推荐 | 方法体内的执行语句组、变量的定义语句组、不同的业务逻辑之间或者不同的语义之间插入一个空行 | references/03-代码格式.md |
| OOP-1 | 强制 | 避免通过一个类的对象引用访问此类的静态变量或静态方法，无谓增加编译器解析成本，直接用类名来访问即可 | references/04-OOP规约.md |
| OOP-2 | 强制 | 所有的覆写方法，必须加@Override注解 | references/04-OOP规约.md |
| OOP-3 | 强制 | 相同参数类型，相同业务含义，才可以使用 Java的可变参数，避免使用 Object | references/04-OOP规约.md |
| OOP-4 | 强制 | 外部正在调用或者二方库依赖的接口，不允许修改方法签名，避免对接口调用方产生影响 | references/04-OOP规约.md |
| OOP-5 | 强制 | 不能使用过时的类或方法 | references/04-OOP规约.md |
| OOP-6 | 强制 | Object的equals方法容易抛空指针异常，应使用常量或确定有值的对象来调用 equals | references/04-OOP规约.md |
| OOP-7 | 强制 | 所有的相同类型的包装类对象之间值的比较，全部使用equals方法比较 | references/04-OOP规约.md |
| OOP-8-1 | 强制 | 所有的 POJO类属性必须使用包装数据类型 | references/04-OOP规约.md |
| OOP-8-2 | 强制 | RPC方法的返回值和参数必须使用包装数据类型 | references/04-OOP规约.md |
| OOP-8-3 | 推荐 | 所有的局部变量使用基本数据类型 | references/04-OOP规约.md |
| OOP-9 | 强制 | 定义DO/DTO/VO等POJO类时，不要设定任何属性默认值 | references/04-OOP规约.md |
| OOP-10 | 强制 | 序列化类新增属性时，请不要修改 serialVersionUID字段，避免反序列失败；如果完全不兼容升级，避免反序列化混乱…… | references/04-OOP规约.md |
| OOP-11 | 强制 | 构造方法里面禁止加入任何业务逻辑，如果有初始化逻辑，请放在 init方法中 | references/04-OOP规约.md |
| OOP-12 | 强制 | POJO类必须写 toString方法 | references/04-OOP规约.md |
| OOP-13 | 推荐 | 使用索引访问用 String的split方法得到的数组时，需做最后一个分隔符后有无内容的检查…… | references/04-OOP规约.md |
| OOP-14 | 推荐 | 当一个类有多个构造方法，或者多个同名方法，这些方法应该按顺序放置在一起，便于阅读 | references/04-OOP规约.md |
| OOP-15 | 推荐 | 类内方法定义顺序依次是：公有方法或保护方法 > 私有方法 > getter/setter 方法 | references/04-OOP规约.md |
| OOP-16 | 推荐 | setter方法中，参数名称与类成员变量名称一致，this.成员名 = 参数名 | references/04-OOP规约.md |
| OOP-17 | 推荐 | 循环体内，字符串的连接方式，使用 StringBuilder的 append方法进行扩展 | references/04-OOP规约.md |
| OOP-18 | 推荐 | final可以声明类、成员变量、方法、以及本地变量，下列情况使用 final关键字： | references/04-OOP规约.md |
| OOP-19 | 推荐 | 慎用Object的clone方法来拷贝对象 | references/04-OOP规约.md |
| OOP-20 | 推荐 | 类成员与方法访问控制从严： | references/04-OOP规约.md |
| 集合-1 | 强制 | 关于hashCode和equals的处理，遵循如下规则： | references/05-集合处理.md |
| 集合-2 | 强制 | ArrayList的subList结果不可强转成ArrayList，否则会抛出ClassCastException 异常…… | references/05-集合处理.md |
| 集合-3 | 强制 | 在subList场景中，高度注意对原集合元素个数的修改，会导致子列表的遍历、增加…… | references/05-集合处理.md |
| 集合-4 | 强制 | 使用集合转数组的方法，必须使用集合的 toArray(T[] array)，传入的是类型完全一样的数组…… | references/05-集合处理.md |
| 集合-5 | 强制 | 使用工具类 Arrays.asList()把数组转换成集合时，不能使用其修改集合相关的方法…… | references/05-集合处理.md |
| 集合-6 | 强制 | 泛型通配符<? extends T>来接收返回的数据，此写法的泛型集合不能使用 add方法…… | references/05-集合处理.md |
| 集合-7 | 强制 | 不要在foreach循环里进行元素的remove/add操作 | references/05-集合处理.md |
| 集合-8 | 强制 | 在JDK7版本及以上，Comparator要满足如下三个条件，不然Arrays.sort…… | references/05-集合处理.md |
| 集合-9 | 推荐 | 集合初始化时，指定集合初始值大小 | references/05-集合处理.md |
| 集合-10 | 推荐 | 使用entrySet遍历Map类集合KV，而不是 keySet方式进行遍历 | references/05-集合处理.md |
| 集合-11 | 推荐 | 高度注意 Map类集合K/V能不能存储 null值的情况，如下表格：集合类 Key Value Super 说明…… | references/05-集合处理.md |
| 集合-12 | 参考 | 合理利用好集合的有序性(sort)和稳定性(order)，避免集合的无序性(unsort)和不稳定性(unorder)带来的…… | references/05-集合处理.md |
| 集合-13 | 参考 | 利用Set元素唯一的特性，可以快速对一个集合进行去重操作，避免使用 List的 contains方法进行遍历、对比、去重操作 | references/05-集合处理.md |
| 并发-1 | 强制 | 获取单例对象需要保证线程安全，其中的方法也要保证线程安全 | references/06-并发处理.md |
| 并发-2 | 强制 | 创建线程或线程池时请指定有意义的线程名称，方便出错时回溯 | references/06-并发处理.md |
| 并发-3 | 强制 | 线程资源必须通过线程池提供，不允许在应用中自行显式创建线程 | references/06-并发处理.md |
| 并发-4 | 强制 | 线程池不允许使用 Executors去创建，而是通过 ThreadPoolExecutor的方式…… | references/06-并发处理.md |
| 并发-5 | 强制 | SimpleDateFormat 是线程不安全的类，一般不要定义为 static变量，如果定义为 static，必须加锁…… | references/06-并发处理.md |
| 并发-6 | 强制 | 高并发时，同步调用应该去考量锁的性能损耗 | references/06-并发处理.md |
| 并发-7 | 强制 | 对多个资源、数据库表、对象同时加锁时，需要保持一致的加锁顺序，否则可能会造成死锁 | references/06-并发处理.md |
| 并发-8 | 强制 | 并发修改同一记录时，避免更新丢失，需要加锁 | references/06-并发处理.md |
| 并发-9 | 强制 | 多线程并行处理定时任务时，Timer运行多个TimeTask时，只要其中之一没有捕获抛出的异常，其它任务便会自动终止运行…… | references/06-并发处理.md |
| 并发-10 | 推荐 | 使用CountDownLatch进行异步转同步操作，每个线程退出前必须调用 countDown 方法…… | references/06-并发处理.md |
| 并发-11 | 推荐 | 避免Random实例被多线程使用，虽然共享该实例是线程安全的，但会因竞争同一 seed 导致的性能下降 | references/06-并发处理.md |
| 并发-12 | 推荐 | 在并发场景下，通过双重检查锁（double-checked locking）实现延迟初始化的优化问题隐患(可参考 The…… | references/06-并发处理.md |
| 并发-13 | 参考 | volatile解决多线程内存不可见问题 | references/06-并发处理.md |
| 并发-14 | 参考 | HashMap在容量不够进行resize时由于高并发可能出现死链，导致CPU飙升…… | references/06-并发处理.md |
| 并发-15 | 参考 | ThreadLocal无法解决共享对象的更新问题，ThreadLocal对象建议使用static 修饰 | references/06-并发处理.md |
| 控制-1 | 强制 | 在一个switch块内，每个case要么通过 break/return等来终止…… | references/07-控制语句.md |
| 控制-2 | 强制 | 在if/else/for/while/do语句中必须使用大括号 | references/07-控制语句.md |
| 控制-3 | 推荐 | 表达异常的分支时，少用if-else方式，这种方式可以改写成： if (condition) { ... return…… | references/07-控制语句.md |
| 控制-4 | 推荐 | 除常用方法（如 getXxx/isXxx）等外，不要在条件判断中执行其它复杂的语句…… | references/07-控制语句.md |
| 控制-5 | 推荐 | 循环体中的语句要考量性能，以下操作尽量移至循环体外处理，如定义对象、变量、获取数据库连接…… | references/07-控制语句.md |
| 控制-6 | 推荐 | 接口入参保护，这种场景常见的是用于做批量操作的接口 | references/07-控制语句.md |
| 控制-7 | 参考 | 下列情形，需要进行参数校验： | references/07-控制语句.md |
| 控制-8 | 参考 | 下列情形，不需要进行参数校验： | references/07-控制语句.md |
| 注释-1 | 强制 | 类、类属性、类方法的注释必须使用 Javadoc规范，使用/**内容*/格式，不得使用 // xxx方式 | references/08-注释规约.md |
| 注释-2 | 强制 | 所有的抽象方法（包括接口中的方法）必须要用 Javadoc注释、除了返回值、参数、异常说明外，还必须指出该方法做什么事情…… | references/08-注释规约.md |
| 注释-3 | 强制 | 所有的类都必须添加创建者和创建日期 | references/08-注释规约.md |
| 注释-4 | 强制 | 方法内部单行注释，在被注释语句上方另起一行，使用//注释 | references/08-注释规约.md |
| 注释-5 | 强制 | 所有的枚举类型字段必须要有注释，说明每个数据项的用途 | references/08-注释规约.md |
| 注释-6 | 推荐 | 与其“半吊子”英文来注释，不如用中文注释把问题说清楚 | references/08-注释规约.md |
| 注释-7 | 推荐 | 代码修改的同时，注释也要进行相应的修改，尤其是参数、返回值、异常、核心逻辑等的修改 | references/08-注释规约.md |
| 注释-8 | 参考 | 合理处理注释掉的代码 | references/08-注释规约.md |
| 注释-9 | 参考 | 对于注释的要求：第一、能够准确反应设计思想和代码逻辑；第二、能够描述业务含义，使别的程序员能够迅速了解到代码背后的信息 | references/08-注释规约.md |
| 注释-10 | 参考 | 好的命名、代码结构是自解释的，注释力求精简准确、表达到位 | references/08-注释规约.md |
| 注释-11 | 参考 | 特殊注释标记，请注明标记人与标记时间 | references/08-注释规约.md |
| 其它-1 | 强制 | 在使用正则表达式时，利用好其预编译功能，可以有效加快正则匹配速度 | references/09-其它.md |
| 其它-2 | 强制 | velocity调用 POJO类的属性时，建议直接使用属性名取值即可，模板引擎会自动按规范调用POJO的getXxx()…… | references/09-其它.md |
| 其它-3 | 强制 | 后台输送给页面的变量必须加$!{var}——中间的感叹号 | references/09-其它.md |
| 其它-4 | 强制 | 注意 Math.random() 这个方法返回是 double类型，注意取值的范围 0≤x<1（能够取到零值…… | references/09-其它.md |
| 其它-5 | 强制 | 获取当前毫秒数 System.currentTimeMillis(); 而不是new Date().getTime(); | references/09-其它.md |
| 其它-6 | 推荐 | 不要在视图模板中加入任何复杂的逻辑 | references/09-其它.md |
| 其它-7 | 推荐 | 任何数据结构的构造或初始化，都应指定大小，避免数据结构无限增长吃光内存 | references/09-其它.md |
| 其它-8 | 推荐 | 及时清理不再使用的代码段或配置信息 | references/09-其它.md |
| 异常-1 | 强制 | Java 类库中定义的一类 RuntimeException可以通过预先检查进行规避，而不应该通过catch 来处理…… | references/10-异常处理.md |
| 异常-2 | 强制 | 异常不要用来做流程控制，条件控制，因为异常的处理效率比条件分支低 | references/10-异常处理.md |
| 异常-3 | 强制 | 对大段代码进行 try-catch，这是不负责任的表现 | references/10-异常处理.md |
| 异常-4 | 强制 | 捕获异常是为了处理它，不要捕获了却什么都不处理而抛弃之，如果不想处理它，请将该异常抛给它的调用者 | references/10-异常处理.md |
| 异常-5 | 强制 | 有try块放到了事务代码中，catch异常后，如果需要回滚事务，一定要注意手动回滚事务 | references/10-异常处理.md |
| 异常-6 | 强制 | finally块必须对资源对象、流对象进行关闭，有异常也要做 try-catch | references/10-异常处理.md |
| 异常-7 | 强制 | 不能在finally块中使用return，finally块中的return返回后方法结束执行…… | references/10-异常处理.md |
| 异常-8 | 强制 | 捕获异常与抛异常，必须是完全匹配，或者捕获异常是抛异常的父类 | references/10-异常处理.md |
| 异常-9 | 推荐 | 方法的返回值可以为 null，不强制返回空集合，或者空对象等，必须添加注释充分说明什么情况下会返回 null值 | references/10-异常处理.md |
| 异常-10 | 推荐 | 防止NPE，是程序员的基本修养，注意 NPE产生的场景： | references/10-异常处理.md |
| 异常-11 | 推荐 | 定义时区分 unchecked / checked 异常，避免直接抛出new RuntimeException()…… | references/10-异常处理.md |
| 异常-12 | 参考 | 在代码中使用“抛异常”还是“返回错误码”，对于公司外的 http/api开放接口必须使用“错误码”；而应用内部推荐异常抛出…… | references/10-异常处理.md |
| 异常-13 | 参考 | 避免出现重复的代码（Don’t Repeat Yourself），即 DRY原则 | references/10-异常处理.md |
| 日志-1 | 强制 | 应用中不可直接使用日志系统（Log4j、Logback）中的API，而应依赖使用日志框架 SLF4J中的API…… | references/11-日志规约.md |
| 日志-2 | 强制 | 日志文件推荐至少保存 15天，因为有些异常具备以“周”为频次发生的特点 | references/11-日志规约.md |
| 日志-3 | 强制 | 应用中的扩展日志（如打点、临时监控、访问日志等）命名方式： appName_logType_logName.log | references/11-日志规约.md |
| 日志-4 | 强制 | 对trace/debug/info级别的日志输出，必须使用条件输出形式或者使用占位符的方式 | references/11-日志规约.md |
| 日志-5 | 强制 | 避免重复打印日志，浪费磁盘空间，务必在 log4j.xml中设置 additivity=false | references/11-日志规约.md |
| 日志-6 | 强制 | 异常信息应该包括两类信息：案发现场信息和异常堆栈信息 | references/11-日志规约.md |
| 日志-7 | 推荐 | 谨慎地记录日志 | references/11-日志规约.md |
| 日志-8 | 参考 | 可以使用warn日志级别来记录用户输入参数错误的情况，避免用户投诉时，无所适从 | references/11-日志规约.md |
| 单测-1 | 强制 | 好的单元测试必须遵守 AIR原则 | references/12-单元测试.md |
| 单测-2 | 强制 | 单元测试应该是全自动执行的，并且非交互式的 | references/12-单元测试.md |
| 单测-3 | 强制 | 保持单元测试的独立性 | references/12-单元测试.md |
| 单测-4 | 强制 | 单元测试是可以重复执行的，不能受到外界环境的影响 | references/12-单元测试.md |
| 单测-5 | 强制 | 对于单元测试，要保证测试粒度足够小，有助于精确定位问题 | references/12-单元测试.md |
| 单测-6 | 强制 | 核心业务、核心应用、核心模块的增量代码确保单元测试通过 | references/12-单元测试.md |
| 单测-7 | 强制 | 单元测试代码必须写在如下工程目录：src/test/java，不允许写在业务代码目录下 | references/12-单元测试.md |
| 单测-8 | 推荐 | 单元测试的基本目标：语句覆盖率达到 70%；核心模块的语句覆盖率和分支覆盖率都要达到100% | references/12-单元测试.md |
| 单测-9 | 推荐 | 编写单元测试代码遵守 BCDE原则，以保证被测试模块的交付质量 | references/12-单元测试.md |
| 单测-10 | 推荐 | 对于数据库相关的查询，更新，删除等操作，不能假设数据库里的数据是存在的，或者直接操作数据库把数据插入进去…… | references/12-单元测试.md |
| 单测-11 | 推荐 | 和数据库相关的单元测试，可以设定自动回滚机制，不给数据库造成脏数据 | references/12-单元测试.md |
| 单测-12 | 推荐 | 对于不可测的代码建议做必要的重构，使代码变得可测，避免为了达到测试要求而书写不规范测试代码 | references/12-单元测试.md |
| 单测-13 | 推荐 | 在设计评审阶段，开发人员需要和测试人员一起确定单元测试范围，单元测试最好覆盖所有测试用例 | references/12-单元测试.md |
| 单测-14 | 推荐 | 单元测试作为一种质量保障手段，不建议项目发布后补充单元测试用例，建议在项目提测前完成单元测试 | references/12-单元测试.md |
| 单测-15 | 参考 | 为了更方便地进行单元测试，业务代码应避免以下情况：  构造方法中做的事情过多 | references/12-单元测试.md |
| 单测-16 | 参考 | 不要对单元测试存在如下误解：  那是测试同学干的事情 | references/12-单元测试.md |
| 安全-1 | 强制 | 隶属于用户个人的页面或者功能必须进行权限控制校验 | references/13-安全规约.md |
| 安全-2 | 强制 | 用户敏感数据禁止直接展示，必须对展示数据进行脱敏 | references/13-安全规约.md |
| 安全-3 | 强制 | 用户输入的 SQL参数严格使用参数绑定或者 METADATA字段值限定，防止 SQL注入，禁止字符串拼接SQL访问数据库 | references/13-安全规约.md |
| 安全-4 | 强制 | 用户请求传入的任何参数必须做有效性验证 | references/13-安全规约.md |
| 安全-5 | 强制 | 禁止向HTML页面输出未经安全过滤或未正确转义的用户数据 | references/13-安全规约.md |
| 安全-6 | 强制 | 表单、AJAX提交必须执行CSRF安全过滤 | references/13-安全规约.md |
| 安全-7 | 强制 | 在使用平台资源，譬如短信、邮件、电话、下单、支付，必须实现正确的防重放限制，如数量限制、疲劳度控制、验证码校验…… | references/13-安全规约.md |
| 安全-8 | 推荐 | 发贴、评论、发送即时消息等用户生成内容的场景必须实现防刷、文本内容违禁词过滤等风控策略 | references/13-安全规约.md |
| ORM-1 | 强制 | 在表查询中，一律不要使用 * 作为查询的字段列表，需要哪些字段必须明确写明 | references/14-ORM映射.md |
| ORM-2 | 强制 | POJO类的布尔属性不能加is，而数据库字段必须加 is_，要求在 resultMap中进行字段与属性之间的映射 | references/14-ORM映射.md |
| ORM-3 | 强制 | 不要用resultClass当返回参数，即使所有类属性名与数据库字段一一对应，也需要定义；反过来…… | references/14-ORM映射.md |
| ORM-4 | 强制 | sql.xml配置参数使用：#{}，#param# 不要使用${} 此种方式容易出现 SQL注入 | references/14-ORM映射.md |
| ORM-5 | 强制 | iBATIS自带的 queryForList(String statementName,int start,int…… | references/14-ORM映射.md |
| ORM-6 | 强制 | 不允许直接拿 HashMap与Hashtable作为查询结果集的输出 | references/14-ORM映射.md |
| ORM-7 | 强制 | 更新数据表记录时，必须同时更新记录对应的 gmt_modified字段值为当前时间 | references/14-ORM映射.md |
| ORM-8 | 推荐 | 不要写一个大而全的数据更新接口，传入为 POJO类，不管是不是自己的目标更新字段…… | references/14-ORM映射.md |
| ORM-9 | 参考 | @Transactional事务不要滥用 | references/14-ORM映射.md |
| ORM-10 | 参考 | <isEqual>中的compareValue是与属性值对比的常量，一般是数字…… | references/14-ORM映射.md |
| 分层-1 | 推荐 | 图中默认上层依赖于下层，箭头关系表示可直接依赖，如：开放接口层可以依赖于 Web层，也可以直接依赖于 Service层…… | references/15-应用分层.md |
| 分层-2 | 参考 | （分层异常处理规约）在DAO层，产生的异常类型有很多，无法用细粒度的异常进行catch…… | references/15-应用分层.md |
| 分层-3 | 参考 | 分层领域模型规约：  DO（Data Object）：与数据库表结构一一对应，通过 DAO层向上传输数据源对象 | references/15-应用分层.md |
| 二方库-1 | 强制 | 定义GAV遵从以下规则： | references/16-二方库依赖.md |
| 二方库-2 | 强制 | 二方库版本号命名方式：主版本号.次版本号.修订号 | references/16-二方库依赖.md |
| 二方库-3 | 强制 | 线上应用不要依赖 SNAPSHOT版本 | references/16-二方库依赖.md |
| 二方库-4 | 强制 | 二方库的新增或升级，保持除功能点之外的其它 jar包仲裁结果不变 | references/16-二方库依赖.md |
| 二方库-5 | 强制 | 二方库里可以定义枚举类型，参数可以使用枚举类型，但是接口返回值不允许使用枚举类型或者包含枚举类型的 POJO对象 | references/16-二方库依赖.md |
| 二方库-6 | 强制 | 依赖于一个二方库群时，必须定义一个统一的版本变量，避免版本号不一致 | references/16-二方库依赖.md |
| 二方库-7 | 强制 | 禁止在子项目的 pom依赖中出现相同的 GroupId，相同的ArtifactId，但是不同的 Version | references/16-二方库依赖.md |
| 二方库-8 | 推荐 | 所有pom文件中的依赖声明放在<dependencies>语句块中…… | references/16-二方库依赖.md |
| 二方库-9 | 推荐 | 二方库不要有配置项，最低限度不要再增加配置项 | references/16-二方库依赖.md |
| 二方库-10 | 参考 | 为避免应用二方库的依赖冲突问题，二方库发布者应当遵循以下原则： | references/16-二方库依赖.md |
| 服务器-1 | 推荐 | 高并发服务器建议调小 TCP协议的 time_wait超时时间 | references/17-服务器.md |
| 服务器-2 | 推荐 | 调大服务器所支持的最大文件句柄数 | references/17-服务器.md |
| 服务器-3 | 推荐 | 给JVM设置-XX:+HeapDumpOnOutOfMemoryError参数，让 JVM碰到OOM场景时输出 dump信息 | references/17-服务器.md |
| 服务器-4 | 参考 | 服务器内部重定向使用 forward；外部重定向地址使用URL拼装工具类来生成…… | references/17-服务器.md |

## references 导航

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| references/01-命名风格.md | 命名风格 17 条规则全文（含说明、正反例） | 类/方法/变量命名、包名、领域模型命名时 |
| references/02-常量定义.md | 常量定义 5 条规则全文（含说明、正反例） | 定义常量、魔法值排查、long 赋值时 |
| references/03-代码格式.md | 代码格式 11 条规则全文（含说明、正反例） | 缩进、空格、行宽、括号与换行风格时 |
| references/04-OOP规约.md | OOP 规约 22 条规则全文（含说明、正反例） | 类设计、继承组合、序列化、equals/hashCode 时 |
| references/05-集合处理.md | 集合处理 13 条规则全文（含说明、正反例） | 集合初始化、遍历、toArray、并发容器时 |
| references/06-并发处理.md | 并发处理 15 条规则全文（含说明、正反例） | 线程池、锁、ThreadLocal、并发工具类时 |
| references/07-控制语句.md | 控制语句 8 条规则全文（含说明、正反例） | switch/判断/循环/卫语句设计时 |
| references/08-注释规约.md | 注释规约 11 条规则全文（含说明、正反例） | 编写 Javadoc 与注释时 |
| references/09-其它.md | 其它 8 条规则全文（含说明、正反例） | 正则、上下文加载、序列化等杂项时 |
| references/10-异常处理.md | 异常处理 13 条规则全文（含说明、正反例） | try-catch-finally、NPE 防护、异常设计时 |
| references/11-日志规约.md | 日志规约 8 条规则全文（含说明、正反例） | 日志级别选择、占位符与拼接、日志输出时 |
| references/12-单元测试.md | 单元测试 16 条规则全文（含说明、正反例） | 编写或评审单元测试（AIR/BCDE 原则、断言、覆盖率）时 |
| references/13-安全规约.md | 安全规约 8 条规则全文（含说明、正反例） | 权限校验、用户输入验证、SQL 注入与越权防护时 |
| references/14-ORM映射.md | ORM 映射 10 条规则全文（含说明、正反例） | iBATIS/MyBatis 的 XML 与注解 SQL、动态 SQL 时 |
| references/15-应用分层.md | 应用分层 3 条规则全文（含说明、正反例） | 设计或检查工程分层（Web/Service/Manager/DAO）时 |
| references/16-二方库依赖.md | 二方库依赖 10 条规则全文（含说明、正反例） | 二方库发布、GAV 坐标、pom 与依赖治理时 |
| references/17-服务器.md | 服务器 4 条规则全文（含说明、正反例） | 服务器与中间件配置（超时、重试、线程数）时 |
| references/00-前言.md | 手册体例与规约等级体系说明 | 了解等级含义与说明/正例/反例体例时 |
| references/19-附录-版本历史.md | 手册版本历史（1.0.0 → 1.3.0） | 核对规约版本差异时 |
| references/18-附录-专有名词.md | 专有名词解释（POJO/DO/AO/BO/GAV/NPE 等 12 项） | 查阅术语时 |

## 共享参考

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| ../../shared-references/http-json-api.md | HTTP JSON API 规范：响应信封与分页接口协议 | 设计开放接口（错误码、Result 封装）时，与异常-12、分层-2 条款联动阅读 |

## 使用方式

1. 编码前：按当前任务读取对应 references 文件全文，再动手。
2. 编码中：拿不准时回到速查索引定位规则编号，再读对应原文（含说明、正例、反例）。
3. 引用规则时给出编号（如 并发-7（创建线程或线程池时指定有意义的线程名）），便于团队溯源与评审对齐。
4. 评审场景请改用 ali-review-java；MySQL 建表/索引/SQL 场景请配合 ali-sql-spec。
