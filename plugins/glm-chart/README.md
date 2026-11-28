# glm-chart — glm-chart Codex 插件

数据可视化插件（v2 更名合并）：按评审决策点 D6 由 glmcharts 更名为 glm-chart（技能名 glmcharts 原样保留），统一 glm- 前缀命名。已实测可用的基线插件：matplotlib / ECharts / D3 / Mermaid 场景化路由，专业配色与防重叠规则。

## 技能目录（1 个）

| 技能 | 触发场景 |
|---|---|
| glmcharts | 画图表 / 画架构图 / 做数据看板（任何数据可视化请求） |

## 目录结构

```
glm-chart/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 1 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    └── glmcharts/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-chart.tar.gz -C ~/.codex/plugins/   # 解出 glm-chart/（含 1 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-chart ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 1 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

