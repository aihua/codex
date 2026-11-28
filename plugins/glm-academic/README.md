# glm-academic — glm-academic Codex 插件

学术研究插件（v2 多技能合并）：一次安装覆盖「检索 → 日报 → 深度收集 → 综述 → 选题」完整学术工作流。纯 Skills 型 Codex 插件（Agent Plugins 1.0.0 + `.codex-plugin` 兼容清单，身份字段同步），供本地模型调用。六个技能自六个 v1 单技能插件迁移（技能文件按附录 D 完成合规修订，触发行为与分别安装旧插件时一致）；四个 AMiner 技能构成同插件内的分档路由（免费 → 付费 → 日报 → 深度收集），四个 AMiner 技能均需 AMINER_API_KEY。

## 技能目录（6 个）

| 技能 | 触发场景 | 依赖 |
|---|---|---|
| aminer-academic-search | 付费深度学术检索 / 学者画像 / 论文深挖 / 机构与专利分析 | AMINER_API_KEY（28 付费 API） |
| aminer-daily-paper | 推荐论文 / 每日论文 / 按方向或学者画像推荐 | AMINER_API_KEY（rec5） |
| aminer-deep-search | 综述文献收集 / 多轮深挖几百篇候选论文 | AMINER_API_KEY |
| aminer-free-academic | 免费学术检索 / 先筛论文 / 学者识别 / 期刊判别 | AMINER_API_KEY（7 免费 API） |
| glm-literature-survey | 生成 6-20 页文献综述 PDF（60+ 真实引用） | 纯本地渲染 |
| glm-research-explorer | 模糊方向 → 具体研究选题 | 零依赖 |

## 目录结构

```
glm-academic/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 6 个技能目录（四个 aminer 技能目录已按规范改名为与 name 一致）
    ├── aminer-academic-search/
    ├── aminer-daily-paper/
    ├── aminer-deep-search/
    ├── aminer-free-academic/
    ├── glm-literature-survey/
    └── glm-research-explorer/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-academic.tar.gz -C ~/.codex/plugins/   # 解出 glm-academic/（含 6 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-academic ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 6 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

