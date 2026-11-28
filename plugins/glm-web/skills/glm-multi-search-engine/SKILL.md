---
name: glm-multi-search-engine
description: "Multi search engine integration with 8 domestic (CN) search engines. Supports advanced search operators, time filters, site search, and WeChat article search. No API keys required. 国内多引擎检索：当用户要\"搜一下 / 联网查 / 查最新 / 用百度 / 用搜狗 / 搜微信公众号 / 头条搜 / 集思录查 / 360 搜\"或需要国内引擎面（微信文章站内搜、头条热点、集思录金融数据、必应CN/INT 切换）时触发；通用高质量检索先走 glm-web-search（Bing 主引擎），需要国内引擎时用本技能的 mse.py（8 引擎无 key，启发式解析）。"
metadata:
  version: "1.0.0"
---

# GLM Multi Search Engine（国内多引擎检索）

8 个国内搜索引擎的无 key 集成，供本地部署 Codex agent 做国内信息面检索。

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-web/`
- 本技能目录：`~/.codex/plugins/glm-web/skills/glm-multi-search-engine/`
- 下文 `scripts/`、`references/` 均指该技能目录内的子目录。
- **宿主工具等效替换**：源 skill 的全部抓取调用（宿主页面抓取组件，
  78 处调用样例）统一替换为本技能自带的 `scripts/mse.py`：
  - 引擎检索 → `mse.py search --engine <id> --query "..."`（构造 URL + 伪装
    UA 抓取 + 启发式提取结果链接）
  - 直接抓 URL → `mse.py fetch "<URL>"`（纯文本化输出，`--raw` 看原始 HTML）
  - 引擎注册表 → `mse.py engines`
- 通用高质量检索（无需国内引擎面时）优先 glm-web-search 插件的
  `glmws.py search`（Bing 主引擎 + DDG 降级，解析质量更高）；本插件补齐
  国内引擎面（微信/头条/集思录/360/搜狗/必应CN/INT）。
- **网络出口声明**：功能性联网（用户显式发起的检索），经 Codex 命令沙箱
  网络授权执行；无 SDK、无 API key、无后台遥测。沙箱禁网时 mse.py
  exit 2 明确报错。
- 解析为**启发式**（各引擎页面结构差异大）：返回标题+链接；快照正文用
  `fetch` 逐条取。反爬视目标站点而定（微信/搜狗常带验证码页），命中时
  exit 2 并建议换引擎。

## Search Engines (Domestic - CN Only)

| 引擎 | id | URL 模板 |
|---|---|---|
| Baidu | `baidu` | `https://www.baidu.com/s?wd={keyword}` |
| Bing CN | `bingcn` | `https://cn.bing.com/search?q={keyword}&ensearch=0` |
| Bing INT | `bingint` | `https://cn.bing.com/search?q={keyword}&ensearch=1` |
| 360 | `so360` | `https://www.so.com/s?q={keyword}` |
| Sogou | `sogou` | `https://sogou.com/web?query={keyword}` |
| WeChat | `wechat` | `https://wx.sogou.com/weixin?type=2&query={keyword}` |
| Toutiao | `toutiao` | `https://so.toutiao.com/search?keyword={keyword}` |
| Jisilu | `jisilu` | `https://www.jisilu.cn/explore/?keyword={keyword}` |

## Quick Examples

```bash
# 引擎注册表
python3 ~/.codex/plugins/glm-web/skills/glm-multi-search-engine/scripts/mse.py engines

# Basic search (Baidu)
python3 ~/.codex/plugins/glm-web/skills/glm-multi-search-engine/scripts/mse.py \
    search --engine baidu --query "python 教程"

# Site-specific (Bing CN)
python3 ~/.codex/plugins/glm-web/skills/glm-multi-search-engine/scripts/mse.py \
    search --engine bingcn --query "site:github.com react"

# WeChat article search
python3 ~/.codex/plugins/glm-web/skills/glm-multi-search-engine/scripts/mse.py \
    search --engine wechat --query "人工智能 最新进展"

# Jisilu financial data
python3 ~/.codex/plugins/glm-web/skills/glm-multi-search-engine/scripts/mse.py \
    search --engine jisilu --query "REITs"

# Fetch any URL as plain text (直接抓取任意页面)
python3 ~/.codex/plugins/glm-web/skills/glm-multi-search-engine/scripts/mse.py \
    fetch "https://www.baidu.com/s?wd=python+tutorial" --max-chars 4000
```

## Advanced Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `site:` | `site:github.com python` | Search within site |
| `filetype:` | `filetype:pdf report` | Specific file type |
| `""` | `"machine learning"` | Exact match |
| `-` | `python -snake` | Exclude term |
| `OR` | `cat OR dog` | Either term |

## Time Filters

| Parameter | Description |
|-----------|-------------|
| `tbs=qdr:h` | Past hour |
| `tbs=qdr:d` | Past day |
| `tbs=qdr:w` | Past week |
| `tbs=qdr:m` | Past month |
| `tbs=qdr:y` | Past year |

注：`tbs` 参数族源自 Google 系语法；国内引擎对时间过滤支持不一（百度
`gpc=stf=…`、360 `sn=…`），模型可先 `fetch` 引擎首页确认当前参数形态，
或直接把时间词写进查询（"2026 最新 / 近一周"）。

## Search Engine Notes

- **WeChat Search**: Best for searching WeChat public articles and content
- **Toutiao**: Good for trending topics and news aggregation
- **Jisilu**: Focused on financial and investment data
- **Bing INT**: International search results via Bing interface
- **Bing CN**: Localized Chinese search results

## 引擎选择策略（给模型的路由规则）

1. 通用检索 / 需要高质量解析 → 先 glm-web-search 的 `glmws.py search`。
2. 要**微信公众号**内容 → 本插件 `mse.py search --engine wechat`。
3. 要**头条热点/新闻聚合** → `--engine toutiao`。
4. 要**集思录金融数据**（REITs/可转债/基金） → `--engine jisilu`。
5. 要**国内引擎面**（百度权重中文内容、360、搜狗） → 对应引擎 id。
6. Bing 国际/国内结果切换 → `bingint` / `bingcn`。
7. 单引擎失败（exit 2：反爬/验证码/网络）→ 换引擎重试一次；再失败改
   glm-web-search。
8. 国际引擎（Google/DDG/Bang 等 17 引擎扩展面） → 见
   `references/international-search.md`（17 引擎操作符与 Bangs 速查）。

## Documentation

- `references/international-search.md` — 9 国际引擎 + Google 高级语法 +
  DuckDuckGo Bangs 速查（本地调用形态已等效替换为 mse.py fetch）
- `references/CHANGELOG.md` — 版本历史（v1.0.0 八引擎 → v2.0.x 国际扩展 →
  本地插件化 v1.0.0）

## License

MIT
