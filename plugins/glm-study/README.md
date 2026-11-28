# glm-study — glm-study Codex 插件

学习与测验插件（v2 多技能合并）：督学、出题、练习页、速查卡四技能构成学习闭环。督学技能的搜索与抓取依赖 glm-web 插件技能（若已安装，未装自动降级为用户粘贴资料）。

## 技能目录（4 个）

| 技能 | 触发场景 |
|---|---|
| glm-study-buddy | 长期学习项目督学 / 复习计划 / 进度追踪 |
| glm-quiz-mastery | 从资料出题 / 掌握度追踪 |
| glm-quiz-html | 题目数组 → 单文件网页练习页 |
| glm-cheat-sheet | 学习材料 → 双栏速查 PDF 卡 |

## 目录结构

```
glm-study/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 4 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-study-buddy/
    ├── glm-quiz-mastery/
    ├── glm-quiz-html/
    └── glm-cheat-sheet/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-study.tar.gz -C ~/.codex/plugins/   # 解出 glm-study/（含 4 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-study ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 4 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

