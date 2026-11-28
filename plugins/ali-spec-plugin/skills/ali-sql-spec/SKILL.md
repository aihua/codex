---
name: ali-sql-spec
description: 《阿里巴巴 Java 开发手册》MySQL 数据库规约（建表规约、索引规约、SQL 语句）。凡编写或评审 MySQL 建表 DDL、字段类型、主键与索引设计、SQL 查询与优化、count/join/in 写法、数据订正时必须使用本技能，即使用户没有提到规约二字。
---

# 阿里巴巴 MySQL 数据库规约

《阿里巴巴 Java 开发手册（终极版 1.3.0）》第五章 MySQL 数据库之（一）建表规约、（二）索引规约、（三）SQL 语句，共 37 条（强制 21 / 推荐 12 / 参考 4）。规则原文与正反例零删减存放于 references。

## 何时使用

编写或评审 MySQL 建表 DDL、字段类型选择、主键与索引设计、SQL 查询与优化（count/join/in 写法）、数据订正语句时；跨表查询与深分页场景同样适用。

## 规约等级图例

- 【强制】：违反即生产事故高危项，必须整改。
- 【推荐】：强烈建议遵循。
- 【参考】：视具体情况选择。

规则编号沿用手册小节序号（如 建表-1、索引-4、SQL-5），可溯源至原文。

## 规则速查索引

| 编号 | 等级 | 规则摘要（原文首句） | 全文位置 |
| --- | --- | --- | --- |
| 建表-1 | 强制 | 表达是与否概念的字段，必须使用 is_xxx的方式命名，数据类型是 unsigned tinyint | references/01-建表规约.md |
| 建表-2 | 强制 | 表名、字段名必须使用小写字母或数字，禁止出现数字开头，禁止两个下划线中间只出现数字 | references/01-建表规约.md |
| 建表-3 | 强制 | 表名不使用复数名词 | references/01-建表规约.md |
| 建表-4 | 强制 | 禁用保留字，如 desc、range、match、delayed等，请参考MySQL官方保留字 | references/01-建表规约.md |
| 建表-5 | 强制 | 主键索引名为 pk_字段名；唯一索引名为 uk_字段名；普通索引名则为 idx_字段名 | references/01-建表规约.md |
| 建表-6 | 强制 | 小数类型为 decimal，禁止使用float和double | references/01-建表规约.md |
| 建表-7 | 强制 | 如果存储的字符串长度几乎相等，使用 char定长字符串类型 | references/01-建表规约.md |
| 建表-8 | 强制 | varchar是可变长字符串，不预先分配存储空间，长度不要超过 5000，如果存储长度大于此值，定义字段类型为 text…… | references/01-建表规约.md |
| 建表-9 | 强制 | 表必备三字段：id, gmt_create, gmt_modified | references/01-建表规约.md |
| 建表-10 | 推荐 | 表的命名最好是加上“业务名称_表的作用” | references/01-建表规约.md |
| 建表-11 | 推荐 | 库名与应用名称尽量一致 | references/01-建表规约.md |
| 建表-12 | 推荐 | 如果修改字段含义或对字段表示的状态追加时，需要及时更新字段注释 | references/01-建表规约.md |
| 建表-13 | 推荐 | 字段允许适当冗余，以提高查询性能，但必须考虑数据一致 | references/01-建表规约.md |
| 建表-14 | 推荐 | 单表行数超过 500万行或者单表容量超过 2GB，才推荐进行分库分表 | references/01-建表规约.md |
| 建表-15 | 参考 | 合适的字符存储长度，不但节约数据库表空间、节约索引存储，更重要的是提升检索速度 | references/01-建表规约.md |
| 索引-1 | 强制 | 业务上具有唯一特性的字段，即使是多个字段的组合，也必须建成唯一索引 | references/02-索引规约.md |
| 索引-2 | 强制 | 超过三个表禁止 join | references/02-索引规约.md |
| 索引-3 | 强制 | 在varchar字段上建立索引时，必须指定索引长度，没必要对全字段建立索引，根据实际文本区分度决定索引长度即可 | references/02-索引规约.md |
| 索引-4 | 强制 | 页面搜索严禁左模糊或者全模糊，如果需要请走搜索引擎来解决 | references/02-索引规约.md |
| 索引-5 | 推荐 | 如果有order by的场景，请注意利用索引的有序性 | references/02-索引规约.md |
| 索引-6 | 推荐 | 利用覆盖索引来进行查询操作，避免回表 | references/02-索引规约.md |
| 索引-7 | 推荐 | 利用延迟关联或者子查询优化超多分页场景 | references/02-索引规约.md |
| 索引-8 | 推荐 | SQL性能优化的目标：至少要达到 range 级别，要求是ref级别，如果可以是consts 最好 | references/02-索引规约.md |
| 索引-9 | 推荐 | 建组合索引的时候，区分度最高的在最左边 | references/02-索引规约.md |
| 索引-10 | 推荐 | 防止因字段类型不同造成的隐式转换，导致索引失效 | references/02-索引规约.md |
| 索引-11 | 参考 | 创建索引时避免有如下极端误解： | references/02-索引规约.md |
| SQL-1 | 强制 | 不要使用count(列名)或count(常量)来替代count(*)，count(*)是SQL92定义的标准统计行数的语法…… | references/03-SQL语句.md |
| SQL-2 | 强制 | count(distinct col) 计算该列除NULL之外的不重复行数…… | references/03-SQL语句.md |
| SQL-3 | 强制 | 当某一列的值全是 NULL时，count(col)的返回结果为0，但 sum(col)的返回结果为 NULL…… | references/03-SQL语句.md |
| SQL-4 | 强制 | 使用ISNULL()来判断是否为 NULL值 | references/03-SQL语句.md |
| SQL-5 | 强制 | 在代码中写分页查询逻辑时，若 count为0 应直接返回，避免执行后面的分页语句 | references/03-SQL语句.md |
| SQL-6 | 强制 | 不得使用外键与级联，一切外键概念必须在应用层解决 | references/03-SQL语句.md |
| SQL-7 | 强制 | 禁止使用存储过程，存储过程难以调试和扩展，更没有移植性 | references/03-SQL语句.md |
| SQL-8 | 强制 | 数据订正时，删除和修改记录时，要先 select，避免出现误删除，确认无误才能执行更新语句 | references/03-SQL语句.md |
| SQL-9 | 推荐 | in操作能避免则避免，若实在避免不了，需要仔细评估 in后边的集合元素数量，控制在1000个之内 | references/03-SQL语句.md |
| SQL-10 | 参考 | 如果有全球化需要，所有的字符存储与表示，均以 utf-8编码，注意字符统计函数的区别 | references/03-SQL语句.md |
| SQL-11 | 参考 | TRUNCATE TABLE 比 DELETE 速度快，且使用的系统和事务日志资源少…… | references/03-SQL语句.md |

## references 导航

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| references/01-建表规约.md | 建表规约 15 条规则全文（含说明、正反例） | 建表、改表、审核建表 DDL 时 |
| references/02-索引规约.md | 索引规约 11 条规则全文（含说明、正反例） | 索引设计、慢查询优化时 |
| references/03-SQL语句.md | SQL 语句 11 条规则全文（含说明、正反例） | 编写或评审 SQL、数据订正时 |

## 共享参考

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| ../../shared-references/http-json-api.md | HTTP JSON API 规范：响应信封（success/code/message）与分页接口协议（currentPage/pageSize/orderBy） | 设计涉及前后端交互的分页查询接口时，与安全规约 pageSize/order 校验联动阅读 |

## 使用方式

1. 编码前：按当前任务读取对应 references 文件全文，再动手。
2. 编码中：拿不准时回到速查索引定位规则编号，再读对应原文（含说明、正例、反例）。
3. 引用规则时给出编号（如 建表-6（小数类型用 decimal）），便于团队溯源与评审对齐。
4. 评审场景请改用 ali-review-sql，它按本技能的规则全文逐条走查并输出带严重级的违规清单。
