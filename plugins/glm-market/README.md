# glm-market — glm-market Codex 插件

营销与市场研究插件（v2 多技能合并）：八步内容营销体系、23 域营销知识库、咨询级市场研究报告。零 SDK、零网络出口，交付物落在用户输出目录。

## 技能目录（3 个）

| 技能 | 触发场景 |
|---|---|
| glm-content-strategy | 内容营销策略 / 选题日历 / 分发与复用 |
| glm-marketing-mode | 营销模式知识库 / 文案框架 / 转化优化 |
| glm-market-research-reports | 咨询级市场研究报告（50+ 页） |

## 目录结构

```
glm-market/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 3 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-content-strategy/
    ├── glm-marketing-mode/
    └── glm-market-research-reports/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-market.tar.gz -C ~/.codex/plugins/   # 解出 glm-market/（含 3 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-market ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 3 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

