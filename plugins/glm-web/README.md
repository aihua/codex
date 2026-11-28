# glm-web — glm-web Codex 插件

网页检索与内容获取插件（v2 多技能合并）：整个 GLM 技能体系的通用底座——20 多个技能的文档引用本插件内的搜索与阅读 CLI。建议优先安装。五个技能自五个 v1 单技能插件原样迁移（措辞按 §5.6 审计更新为同插件/跨插件表述，触发行为不变）。

## 技能目录（5 个）

| 技能 | 触发场景 | 入口 |
|---|---|---|
| glm-web-search | 搜索网页 / 联网检索 | `glmws.py`（零依赖 CLI） |
| glm-web-reader | 读取网页正文 / 抓取文章 | `glmwr.py`（零依赖 CLI） |
| glm-multi-search-engine | 多引擎聚合检索 / 高级算子 | `mse.py`（八引擎） |
| glm-agent-browser | 无头浏览器操作 / 截图 / 快照 | 纯标准库自动化 |
| glm-contentanalysis | 视频播客文章的内容萃取 | 路由型 SKILL.md |

## 目录结构

```
glm-web/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 5 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-web-search/
    ├── glm-web-reader/
    ├── glm-multi-search-engine/
    ├── glm-agent-browser/
    └── glm-contentanalysis/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-web.tar.gz -C ~/.codex/plugins/   # 解出 glm-web/（含 5 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-web ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 5 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

