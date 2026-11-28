# glm-finance — glm-finance Codex 插件

金融投资插件（v2 多技能合并）：行情与综合分析 + 个股决策看板。行情新闻检索路由 glm-web 插件技能、制图路由 glm-chart 插件技能（均为若已安装）。

## 技能目录（2 个）

| 技能 | 触发场景 |
|---|---|
| glm-finance | 行情 / 财报 / 资讯综合分析 |
| glm-stock-analysis-skill | 个股决策看板 / 股息评分 / 自选股管理 |

## 目录结构

```
glm-finance/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 2 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-finance/
    └── glm-stock-analysis-skill/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-finance.tar.gz -C ~/.codex/plugins/   # 解出 glm-finance/（含 2 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-finance ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 2 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

