# 检索等效与维度查询样例

## 等效矩阵（源宿主组件 → 本地实现）

| 源组件 | 本地等效 | 输出 |
|---|---|---|
| 结构化学术检索（源宿主组件·论文检索形态） | `scripts/s2_search.py --query "..." --limit 10` | title/authors/year/venue/citations/url |
| 学者发现（源宿主组件·学者检索形态） | s2_search 结果的 `authors` 字段扫描 top-cited 命中 | 作者名 + 代表作 |
| 通用 web 检索 | glm-web-search 插件 `glmws.py search "..." --num 8` | url/name/snippet/host/rank |
| 页面全文抓取 | glm-web-search 插件 `glmws.py fetch "URL" --max-chars 4000` | 纯文本 |

s2_search.py 匿名端点限流 ~1 req/s：连续调用之间 `sleep 1`；HTTP 429 时脚本
自动等 2 秒重试一次，再失败 exit 2 并给降级建议。

## 七维度查询样例（direction = "federated learning" 时）

| 维度 | s2_search 查询 | glmws.py 补充查询 |
|---|---|---|
| 1 热点 | `federated learning recent advances` `--since-year 2024` | `federated learning hot topics 2025` |
| 2 开放问题 | `federated learning open problems challenges` | `federated learning open problems` |
| 3 综述 | `federated learning survey` `--min-citations 100` | `federated learning survey 2024 filetype:pdf` |
| 4 基准 | `federated learning benchmark evaluation` | `federated learning benchmark leaderboard` |
| 5 应用 | `federated learning applications industry` | `federated learning industry use cases` |
| 6 交叉 | `federated learning differential privacy`（选 1-2 邻域） | 同左 |
| 7 突破 | `federated learning` `--since-year 2025 --min-citations 5` | `federated learning breakthrough 2025` |

执行顺序纪律：每个维度**先 s2_search**，结果单薄（<3 条或维度偏工程/社区）
再补 glmws.py search；每个问题最多 fetch 2 个 URL；每完成一个维度立刻把
中间笔记追加进 `$RUN/search_notes.md`。

## 降级路径（沙箱禁网）

1. s2_search.py exit 2 / glmws.py exit 2 → 沙箱禁网或出口被防火墙拦截。
2. 转纯模型知识模式：三份交付物照常产出，但 `literature_pre_survey.md`
   每条文献标注 `NOT web-verified this session`，并在交付物开头写明
   "本次为离线模式，文献信息未经联网核实，投稿/开题前必须人工复核"。
3. 绝不在离线模式下伪装"已核实"。
